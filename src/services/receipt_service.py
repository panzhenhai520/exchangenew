"""
票据编号生成服务
确保每个网点的票据编号包含网点信息并严格保持连续性
"""

from datetime import datetime, date
from sqlalchemy import and_
from models.exchange_models import ReceiptSequence, Branch
from services.db_service import DatabaseService
import logging

logger = logging.getLogger(__name__)

class ReceiptService:
    
    @staticmethod
    def generate_receipt_number(branch_id, session=None):
        """
        生成包含网点信息的连续票据编号
        格式：{网点代码}{日期YYYYMMDD}{4位序列号}
        例如：HO001202412150001, A003202412150002
        
        Args:
            branch_id: 网点ID
            session: 数据库会话（可选，如果不提供则自动创建）
            
        Returns:
            str: 生成的票据编号
        """
        
        # 如果没有提供session，则创建一个
        should_close_session = False
        if session is None:
            session = DatabaseService.get_session()
            should_close_session = True
            
        try:
            # 获取网点信息
            branch = session.query(Branch).filter_by(id=branch_id).first()
            if not branch:
                raise ValueError(f"网点ID {branch_id} 不存在")
            
            # 当前日期
            today = date.today()
            date_str = today.strftime('%Y%m%d')
            
            # 使用数据库行锁确保线程安全
            sequence_record = session.query(ReceiptSequence).filter_by(
                branch_id=branch_id
            ).with_for_update().first()
            
            if not sequence_record:
                # 如果没有序列记录，创建一个
                sequence_record = ReceiptSequence(
                    branch_id=branch_id,
                    current_sequence=0,
                    last_date=today,
                    updated_at=datetime.utcnow()
                )
                session.add(sequence_record)
                session.flush()  # 确保记录已插入
            
            # 检查日期是否变更，如果是新的一天，重置序列号
            # SQLAlchemy会自动处理DATE类型的转换
            if sequence_record.last_date != today:
                sequence_record.current_sequence = 0
                sequence_record.last_date = today
            
            # 递增序列号
            sequence_record.current_sequence += 1
            sequence_record.updated_at = datetime.utcnow()
            
            # 生成票据编号：网点代码 + 日期 + 4位序列号
            receipt_number = f"{branch.branch_code}{date_str}{sequence_record.current_sequence:04d}"
            
            # 提交更改（如果是外部传入的session，由调用方决定是否提交）
            if should_close_session:
                session.commit()
            
            logger.info(f"生成票据编号: {receipt_number} (网点: {branch.branch_code}, 日期: {date_str}, 序列: {sequence_record.current_sequence})")
            
            return receipt_number
            
        except Exception as e:
            logger.error(f"生成票据编号失败: {str(e)}")
            if should_close_session:
                session.rollback()
            raise
            
        finally:
            if should_close_session:
                DatabaseService.close_session(session)
    
    @staticmethod
    def get_current_sequence(branch_id):
        """
        获取指定网点的当前序列号信息
        
        Args:
            branch_id: 网点ID
            
        Returns:
            dict: 包含当前序列号信息的字典
        """
        session = DatabaseService.get_session()
        try:
            sequence_record = session.query(ReceiptSequence).filter_by(
                branch_id=branch_id
            ).first()
            
            if not sequence_record:
                return {
                    'branch_id': branch_id,
                    'current_sequence': 0,
                    'last_date': None,
                    'next_number': None
                }
            
            # 获取网点信息
            branch = session.query(Branch).filter_by(id=branch_id).first()
            today = date.today()
            
            # 预测下一个编号
            # SQLAlchemy会自动处理DATE类型的转换
            next_sequence = sequence_record.current_sequence + 1
            if sequence_record.last_date != today:
                next_sequence = 1  # 新的一天从1开始
            
            next_number = f"{branch.branch_code}{today.strftime('%Y%m%d')}{next_sequence:04d}"
            
            return {
                'branch_id': branch_id,
                'branch_code': branch.branch_code,
                'current_sequence': sequence_record.current_sequence,
                'last_date': str(sequence_record.last_date) if sequence_record.last_date else None,
                'next_number': next_number,
                'updated_at': str(sequence_record.updated_at) if sequence_record.updated_at else None
            }
            
        except Exception as e:
            logger.error(f"获取序列号信息失败: {str(e)}")
            raise
            
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def reset_daily_sequence(branch_id=None):
        """
        重置日序列号（通常用于日终处理或系统维护）
        
        Args:
            branch_id: 网点ID，如果为None则重置所有网点
        """
        session = DatabaseService.get_session()
        try:
            today = date.today()
            
            if branch_id:
                # 重置指定网点
                sequence_record = session.query(ReceiptSequence).filter_by(
                    branch_id=branch_id
                ).first()
                
                if sequence_record:
                    sequence_record.current_sequence = 0
                    sequence_record.last_date = today
                    sequence_record.updated_at = datetime.utcnow()
                    logger.info(f"重置网点 {branch_id} 的票据序列号")
            else:
                # 重置所有网点
                session.query(ReceiptSequence).update({
                    'current_sequence': 0,
                    'last_date': today,
                    'updated_at': datetime.utcnow()
                })
                logger.info("重置所有网点的票据序列号")
            
            session.commit()
            
        except Exception as e:
            logger.error(f"重置序列号失败: {str(e)}")
            session.rollback()
            raise
            
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def validate_receipt_number(receipt_number):
        """
        验证票据编号格式是否正确
        
        Args:
            receipt_number: 票据编号
            
        Returns:
            dict: 验证结果和解析信息
        """
        try:
            if len(receipt_number) < 13:  # 最小长度：网点代码(3) + 日期(8) + 序列(4)
                return {
                    'valid': False,
                    'error': '票据编号长度不足'
                }
            
            # 尝试解析格式
            # 假设网点代码为3-5位字符
            possible_branch_codes = []
            for i in range(3, min(6, len(receipt_number) - 11)):  # 至少保留8位日期+4位序列
                branch_code = receipt_number[:i]
                remainder = receipt_number[i:]
                
                if len(remainder) == 12:  # 8位日期 + 4位序列
                    date_part = remainder[:8]
                    sequence_part = remainder[8:]
                    
                    # 验证日期格式
                    try:
                        datetime.strptime(date_part, '%Y%m%d')
                        # 验证序列号是数字
                        int(sequence_part)
                        
                        possible_branch_codes.append({
                            'branch_code': branch_code,
                            'date': date_part,
                            'sequence': int(sequence_part)
                        })
                    except ValueError:
                        continue
            
            if possible_branch_codes:
                # 返回第一个有效的解析结果
                parsed = possible_branch_codes[0]
                return {
                    'valid': True,
                    'branch_code': parsed['branch_code'],
                    'date': parsed['date'],
                    'sequence': parsed['sequence']
                }
            else:
                return {
                    'valid': False,
                    'error': '票据编号格式不正确'
                }
                
        except Exception as e:
            return {
                'valid': False,
                'error': f'验证过程出错: {str(e)}'
            } 