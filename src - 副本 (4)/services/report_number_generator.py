#!/usr/bin/env python3
"""
报告编号生成服务
支持AMLO和BOT报告的唯一编号生成
"""

import re
from datetime import datetime, date
from typing import Optional, Dict, Any
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from models.report_number_models import AMLOReportSequence, BOTReportSequence, ReportNumberLog
from services.db_service import DatabaseService


class ReportNumberGenerator:
    """报告编号生成器"""
    
    @staticmethod
    def get_buddhist_year_suffix() -> str:
        """获取佛历年份的后两位数字"""
        current_year = datetime.now().year
        buddhist_year = current_year + 543  # 公历转佛历
        return str(buddhist_year)[-2:]  # 取最后两位
    
    @staticmethod
    def get_current_year_month() -> str:
        """获取当前年月字符串 (YYYY-MM)"""
        return datetime.now().strftime('%Y-%m')
    
    @staticmethod
    def get_branch_codes(session: Session, branch_id: int) -> Dict[str, str]:
        """获取网点的AMLO机构代码和支行代码"""
        try:
            print(f"[get_branch_codes] [START] Getting AMLO codes for branch {branch_id}")

            # 检查branches表是否存在
            sql = text("SHOW TABLES LIKE 'branches'")
            result = session.execute(sql).fetchone()

            if not result:
                print("[get_branch_codes] [ERROR] Branches table does not exist, using default codes")
                return {
                    'institution_code': '001',
                    'branch_code': '001'
                }

            print("[get_branch_codes] [OK] Branches table exists")

            sql = text("""
                SELECT id, amlo_institution_code, amlo_branch_code
                FROM branches
                WHERE id = :branch_id
            """)
            result = session.execute(sql, {'branch_id': branch_id}).fetchone()

            if not result:
                print(f"[get_branch_codes] [ERROR] Branch ID {branch_id} not found, using default codes")
                return {
                    'institution_code': '001',
                    'branch_code': '001'
                }

            print(f"[get_branch_codes] [QUERY] id={result.id}, amlo_institution_code={result.amlo_institution_code}, amlo_branch_code={result.amlo_branch_code}")

            # 确保代码格式正确（3位数字）
            institution_code = str(result.amlo_institution_code or '001').zfill(3)
            branch_code = str(result.amlo_branch_code or '001').zfill(3)

            print(f"[get_branch_codes] [SUCCESS] Final codes: institution_code={institution_code}, branch_code={branch_code}")

            return {
                'institution_code': institution_code,
                'branch_code': branch_code
            }
        except Exception as e:
            print(f"[get_branch_codes] [ERROR] Failed to get branch codes: {e}, using default codes")
            import traceback
            traceback.print_exc()
            return {
                'institution_code': '001',
                'branch_code': '001'
            }
    
    @staticmethod
    def generate_amlo_report_number(
        session: Session,
        branch_id: int,
        currency_code: str,
        operator_id: int,
        transaction_id: Optional[int] = None
    ) -> str:
        """
        生成AMLO报告编号
        格式: XXX-XXX-XX-XXXXXXCCC
        - 前3位: AMLO机构代码
        - 第4-6位: 支行代码  
        - 第7-8位: 佛历年份后两位
        - 第9-14位: 月内序列号(6位，每月重置)
        - 第15-17位: 币种代码(ISO 4217)
        
        Args:
            session: 数据库会话
            branch_id: 网点ID
            currency_code: 币种代码 (如 USD, EUR, JPY)
            operator_id: 操作员ID
            transaction_id: 关联交易ID(可选)
            
        Returns:
            生成的报告编号
        """
        try:
            # 1. 获取网点代码
            branch_codes = ReportNumberGenerator.get_branch_codes(session, branch_id)
            
            # 2. 获取佛历年份后缀
            year_suffix = ReportNumberGenerator.get_buddhist_year_suffix()
            
            # 3. 获取当前年月
            year_month = ReportNumberGenerator.get_current_year_month()
            
            # 4. 确保币种代码格式正确
            currency_code = currency_code.upper().strip()
            if len(currency_code) != 3:
                raise ValueError(f"币种代码必须为3位: {currency_code}")
            
            # 5. 获取或创建序列记录 (使用 SELECT FOR UPDATE 悲观锁)
            sequence_record = session.query(AMLOReportSequence).filter(
                AMLOReportSequence.branch_id == branch_id,
                AMLOReportSequence.currency_code == currency_code,
                AMLOReportSequence.year_month == year_month
            ).with_for_update().first()  # 行级锁，防止并发冲突

            if not sequence_record:
                # 创建新的序列记录 (需要处理并发创建)
                try:
                    sequence_record = AMLOReportSequence(
                        branch_id=branch_id,
                        currency_code=currency_code,
                        year_month=year_month,
                        current_sequence=0
                    )
                    session.add(sequence_record)
                    session.flush()  # 确保ID生成
                except IntegrityError:
                    # 如果另一个事务已创建，重新查询
                    session.rollback()
                    sequence_record = session.query(AMLOReportSequence).filter(
                        AMLOReportSequence.branch_id == branch_id,
                        AMLOReportSequence.currency_code == currency_code,
                        AMLOReportSequence.year_month == year_month
                    ).with_for_update().first()

                    if not sequence_record:
                        raise Exception("并发创建序列记录失败")

            # 6. 原子性增加序列号 (已通过SELECT FOR UPDATE锁定)
            sequence_record.current_sequence += 1
            sequence_record.last_used_at = datetime.now()
            
            # 7. 生成报告编号
            # 序列号格式：月份(2位) + 月内序列号(4位)
            current_month = datetime.now().month
            month_str = str(current_month).zfill(2)
            sequence_str = str(sequence_record.current_sequence).zfill(4)
            full_sequence = f"{month_str}{sequence_str}"
            
            report_number = f"{branch_codes['institution_code']}-{branch_codes['branch_code']}-{year_suffix}-{full_sequence}{currency_code}"
            
            # 8. 记录使用日志
            log_record = ReportNumberLog(
                report_number=report_number,
                report_type='AMLO',
                branch_id=branch_id,
                currency_code=currency_code,
                sequence_id=sequence_record.id,
                transaction_id=transaction_id,
                operator_id=operator_id
            )
            session.add(log_record)

            # 🔧 注意：不在这里commit，由调用方统一commit，避免序列号消耗但报告创建失败
            session.flush()  # 只刷新到数据库，但不提交事务

            print(f"[AMLO编号生成] 成功生成报告编号: {report_number} (未提交事务)")
            return report_number
            
        except IntegrityError as e:
            session.rollback()
            # 如果是并发冲突，重试一次
            if "uk_branch_currency_month" in str(e):
                print(f"[AMLO编号生成] 检测到并发冲突，重试生成...")
                return ReportNumberGenerator.generate_amlo_report_number(
                    session, branch_id, currency_code, operator_id, transaction_id
                )
            else:
                raise e
        except Exception as e:
            session.rollback()
            print(f"[AMLO编号生成] 生成失败: {e}")
            raise e
    
    @staticmethod
    def generate_bot_report_number(
        session: Session,
        branch_id: int,
        report_type: str,
        operator_id: int,
        transaction_id: Optional[int] = None
    ) -> str:
        """
        生成BOT报告编号
        格式: XXX-XXX-XX-XXXXXX
        
        Args:
            session: 数据库会话
            branch_id: 网点ID
            report_type: 报告类型 (BuyFX/SellFX/FCD)
            operator_id: 操作员ID
            transaction_id: 关联交易ID(可选)
            
        Returns:
            生成的报告编号
        """
        try:
            # 1. 获取网点代码
            branch_codes = ReportNumberGenerator.get_branch_codes(session, branch_id)
            
            # 2. 获取佛历年份后缀
            year_suffix = ReportNumberGenerator.get_buddhist_year_suffix()
            
            # 3. 获取当前年月
            year_month = ReportNumberGenerator.get_current_year_month()
            
            # 4. 获取或创建序列记录 (使用 SELECT FOR UPDATE 悲观锁)
            sequence_record = session.query(BOTReportSequence).filter(
                BOTReportSequence.branch_id == branch_id,
                BOTReportSequence.report_type == report_type,
                BOTReportSequence.year_month == year_month
            ).with_for_update().first()  # 行级锁，防止并发冲突

            if not sequence_record:
                # 创建新的序列记录 (需要处理并发创建)
                try:
                    sequence_record = BOTReportSequence(
                        branch_id=branch_id,
                        report_type=report_type,
                        year_month=year_month,
                        current_sequence=0
                    )
                    session.add(sequence_record)
                    session.flush()
                except IntegrityError:
                    # 如果另一个事务已创建，重新查询
                    session.rollback()
                    sequence_record = session.query(BOTReportSequence).filter(
                        BOTReportSequence.branch_id == branch_id,
                        BOTReportSequence.report_type == report_type,
                        BOTReportSequence.year_month == year_month
                    ).with_for_update().first()

                    if not sequence_record:
                        raise Exception("并发创建序列记录失败")

            # 5. 原子性增加序列号 (已通过SELECT FOR UPDATE锁定)
            sequence_record.current_sequence += 1
            sequence_record.last_used_at = datetime.now()
            
            # 6. 生成报告编号
            # 序列号格式：月份(2位) + 月内序列号(4位)
            current_month = datetime.now().month
            month_str = str(current_month).zfill(2)
            sequence_str = str(sequence_record.current_sequence).zfill(4)
            full_sequence = f"{month_str}{sequence_str}"
            
            report_number = f"{branch_codes['institution_code']}-{branch_codes['branch_code']}-{year_suffix}-{full_sequence}"
            
            # 7. 记录使用日志
            log_record = ReportNumberLog(
                report_number=report_number,
                report_type='BOT',
                branch_id=branch_id,
                currency_code=None,  # BOT报告不使用币种代码
                sequence_id=sequence_record.id,
                transaction_id=transaction_id,
                operator_id=operator_id
            )
            session.add(log_record)
            
            session.commit()
            
            print(f"[BOT编号生成] 成功生成报告编号: {report_number}")
            return report_number
            
        except IntegrityError as e:
            session.rollback()
            # 如果是并发冲突，重试一次
            if "uk_branch_type_month" in str(e):
                print(f"[BOT编号生成] 检测到并发冲突，重试生成...")
                return ReportNumberGenerator.generate_bot_report_number(
                    session, branch_id, report_type, operator_id, transaction_id
                )
            else:
                raise e
        except Exception as e:
            session.rollback()
            print(f"[BOT编号生成] 生成失败: {e}")
            raise e
    
    @staticmethod
    def validate_report_number(report_number: str, report_type: str = 'AMLO') -> bool:
        """
        验证报告编号格式是否正确
        
        Args:
            report_number: 报告编号
            report_type: 报告类型 (AMLO/BOT)
            
        Returns:
            是否有效
        """
        try:
            if report_type == 'AMLO':
                # AMLO格式: XXX-XXX-XX-XXXXXXCCC (序列号是月份2位+月内序列4位)
                pattern = r'^\d{3}-\d{3}-\d{2}-\d{6}[A-Z]{3}$'
                if not re.match(pattern, report_number):
                    return False
                
                # 验证币种代码是否为有效的ISO 4217代码
                currency_code = report_number[-3:]
                valid_currencies = ['USD', 'EUR', 'JPY', 'GBP', 'CHF', 'AUD', 'CAD', 'SGD', 'HKD', 'CNY', 'KRW', 'THB']
                return currency_code in valid_currencies
                
            elif report_type == 'BOT':
                # BOT格式: XXX-XXX-XX-XXXXXX (序列号是月份2位+月内序列4位)
                pattern = r'^\d{3}-\d{3}-\d{2}-\d{6}$'
                return bool(re.match(pattern, report_number))
            
            return False
        except Exception:
            return False
    
    @staticmethod
    def parse_report_number(report_number: str) -> Dict[str, Any]:
        """
        解析报告编号，提取各部分信息
        
        Args:
            report_number: 报告编号
            
        Returns:
            解析后的信息字典
        """
        try:
            parts = report_number.split('-')
            if len(parts) != 4:
                raise ValueError("报告编号格式不正确")
            
            institution_code = parts[0]
            branch_code = parts[1]
            year_suffix = parts[2]
            sequence_part = parts[3]
            
            if len(sequence_part) >= 9:  # AMLO报告 (6位序列号+3位币种代码)
                sequence_number = sequence_part[:-3]
                currency_code = sequence_part[-3:]
                report_type = 'AMLO'
            else:  # BOT报告 (6位序列号)
                sequence_number = sequence_part
                currency_code = None
                report_type = 'BOT'
            
            return {
                'report_type': report_type,
                'institution_code': institution_code,
                'branch_code': branch_code,
                'year_suffix': year_suffix,
                'sequence_number': sequence_number,
                'currency_code': currency_code,
                'full_number': report_number
            }
        except Exception as e:
            raise ValueError(f"解析报告编号失败: {e}")
    
    @staticmethod
    def get_sequence_statistics(session: Session, branch_id: int, year_month: Optional[str] = None) -> Dict[str, Any]:
        """
        获取序列号使用统计
        
        Args:
            session: 数据库会话
            branch_id: 网点ID
            year_month: 年月(可选，默认当前月)
            
        Returns:
            统计信息
        """
        try:
            if not year_month:
                year_month = ReportNumberGenerator.get_current_year_month()
            
            # AMLO统计
            amlo_sequences = session.query(AMLOReportSequence).filter(
                AMLOReportSequence.branch_id == branch_id,
                AMLOReportSequence.year_month == year_month
            ).all()
            
            # BOT统计
            bot_sequences = session.query(BOTReportSequence).filter(
                BOTReportSequence.branch_id == branch_id,
                BOTReportSequence.year_month == year_month
            ).all()
            
            return {
                'year_month': year_month,
                'amlo_sequences': [
                    {
                        'currency_code': seq.currency_code,
                        'current_sequence': seq.current_sequence,
                        'last_used_at': seq.last_used_at
                    } for seq in amlo_sequences
                ],
                'bot_sequences': [
                    {
                        'report_type': seq.report_type,
                        'current_sequence': seq.current_sequence,
                        'last_used_at': seq.last_used_at
                    } for seq in bot_sequences
                ]
            }
        except Exception as e:
            print(f"获取统计信息失败: {e}")
            return {'error': str(e)}
