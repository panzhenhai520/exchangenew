# EOD改进的数据迁移和验证工具
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import func, text
from services.db_service import DatabaseService
from models.exchange_models import EODStatus, ExchangeTransaction, EODBalanceVerification, CurrencyBalance
import logging

logger = logging.getLogger(__name__)

class EODMigrationTools:
    """日结改进的数据迁移和验证工具"""
    
    @staticmethod
    def add_business_time_fields():
        """为eod_status表添加业务时间字段"""
        session = DatabaseService.get_session()
        try:
            # 检查字段是否已存在
            result = session.execute(text("PRAGMA table_info(eod_status)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'business_start_time' not in columns:
                session.execute(text("ALTER TABLE eod_status ADD COLUMN business_start_time DATETIME NULL"))
                logger.info("已添加business_start_time字段")
            
            if 'business_end_time' not in columns:
                session.execute(text("ALTER TABLE eod_status ADD COLUMN business_end_time DATETIME NULL"))
                logger.info("已添加business_end_time字段")
            
            session.commit()
            return {'success': True, 'message': '数据库结构更新完成'}
            
        except Exception as e:
            session.rollback()
            logger.error(f"添加业务时间字段失败: {str(e)}")
            return {'success': False, 'message': f'添加字段失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def backfill_business_time_data():
        """为现有EOD记录补填业务时间字段"""
        session = DatabaseService.get_session()
        try:
            updated_count = 0
            
            # 获取所有缺少业务时间的EOD记录
            eod_records = session.query(EODStatus).filter(
                EODStatus.business_start_time.is_(None)
            ).order_by(EODStatus.branch_id, EODStatus.date).all()
            
            for eod in eod_records:
                try:
                    # 计算业务开始时间
                    prev_eod = session.query(EODStatus).filter(
                        EODStatus.branch_id == eod.branch_id,
                        EODStatus.date < eod.date,
                        EODStatus.status == 'completed'
                    ).order_by(EODStatus.completed_at.desc()).first()
                    
                    if prev_eod and prev_eod.completed_at:
                        business_start_time = prev_eod.completed_at
                    else:
                        # 取当天第一条交易时间往前推3秒
                        first_tx = session.query(ExchangeTransaction).filter(
                            ExchangeTransaction.branch_id == eod.branch_id,
                            func.date(ExchangeTransaction.created_at) == eod.date
                        ).order_by(ExchangeTransaction.created_at).first()
                        
                        if first_tx:
                            business_start_time = first_tx.created_at - timedelta(seconds=3)
                        else:
                            business_start_time = datetime.combine(eod.date, datetime.min.time())
                    
                    # 设置业务结束时间
                    business_end_time = eod.completed_at if eod.completed_at else eod.started_at
                    
                    # 更新记录
                    eod.business_start_time = business_start_time
                    eod.business_end_time = business_end_time
                    updated_count += 1
                    
                    logger.info(f"已更新EOD {eod.id} 的业务时间范围: {business_start_time} ~ {business_end_time}")
                    
                except Exception as e:
                    logger.error(f"更新EOD {eod.id} 失败: {str(e)}")
                    continue
            
            session.commit()
            return {
                'success': True, 
                'message': f'成功更新{updated_count}条EOD记录的业务时间',
                'updated_count': updated_count
            }
            
        except Exception as e:
            session.rollback()
            logger.error(f"补填业务时间字段失败: {str(e)}")
            return {'success': False, 'message': f'补填失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def validate_data_consistency(eod_id=None):
        """验证EOD数据一致性"""
        session = DatabaseService.get_session()
        try:
            issues = []
            
            # 查询范围
            if eod_id:
                eod_records = session.query(EODStatus).filter_by(id=eod_id).all()
            else:
                # 检查最近10条EOD记录
                eod_records = session.query(EODStatus).filter(
                    EODStatus.status == 'completed'
                ).order_by(EODStatus.completed_at.desc()).limit(10).all()
            
            for eod in eod_records:
                try:
                    # 1. 检查业务时间范围的合理性
                    if eod.business_start_time and eod.business_end_time:
                        if eod.business_start_time >= eod.business_end_time:
                            issues.append({
                                'eod_id': eod.id,
                                'type': 'business_time_range',
                                'message': '业务开始时间不能晚于结束时间',
                                'start_time': eod.business_start_time.isoformat(),
                                'end_time': eod.business_end_time.isoformat()
                            })
                    
                    # 2. 检查EODBalanceVerification与CurrencyBalance的一致性
                    verifications = session.query(EODBalanceVerification).filter_by(
                        eod_status_id=eod.id
                    ).all()
                    
                    for verification in verifications:
                        currency_balance = session.query(CurrencyBalance).filter_by(
                            branch_id=eod.branch_id,
                            currency_id=verification.currency_id
                        ).first()
                        
                        if currency_balance:
                            # 检查余额差异（考虑可能的后续交款）
                            diff = abs(verification.actual_balance - float(currency_balance.balance))
                            if diff > 0.01:  # 允许1分钱的误差
                                issues.append({
                                    'eod_id': eod.id,
                                    'type': 'balance_inconsistency',
                                    'currency_id': verification.currency_id,
                                    'verification_balance': verification.actual_balance,
                                    'current_balance': float(currency_balance.balance),
                                    'difference': diff
                                })
                    
                except Exception as e:
                    logger.error(f"验证EOD {eod.id} 时出错: {str(e)}")
                    issues.append({
                        'eod_id': eod.id,
                        'type': 'validation_error',
                        'message': f'验证过程出错: {str(e)}'
                    })
            
            return {
                'success': True,
                'issues_count': len(issues),
                'issues': issues
            }
            
        except Exception as e:
            logger.error(f"数据一致性验证失败: {str(e)}")
            return {'success': False, 'message': f'验证失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def create_rollback_script():
        """创建回滚脚本"""
        rollback_script = '''
# EOD改进回滚脚本
# 执行此脚本可以回滚到改进前的状态

from config.features import FeatureFlags

# 1. 关闭所有新特性
FeatureFlags.ENABLE_BUSINESS_TIME_RANGE = False
FeatureFlags.ENABLE_ENHANCED_BALANCE_CALCULATION = False
FeatureFlags.ENABLE_COMPREHENSIVE_STATISTICS = False
FeatureFlags.ENABLE_BALANCE_CONSISTENCY_CHECK = False

print("已关闭所有新特性，系统恢复到传统模式")

# 2. 可选：删除新增的数据库字段（谨慎操作）
# ALTER TABLE eod_status DROP COLUMN business_start_time;
# ALTER TABLE eod_status DROP COLUMN business_end_time;
'''
        
        with open('src/scripts/eod_rollback.py', 'w', encoding='utf-8') as f:
            f.write(rollback_script)
        
        return {'success': True, 'message': '回滚脚本已生成: src/scripts/eod_rollback.py'}
    
    @staticmethod
    def get_migration_status():
        """获取迁移状态"""
        session = DatabaseService.get_session()
        try:
            # 检查字段是否存在
            result = session.execute(text("PRAGMA table_info(eod_status)"))
            columns = [row[1] for row in result.fetchall()]
            
            has_business_start_time = 'business_start_time' in columns
            has_business_end_time = 'business_end_time' in columns
            
            # 统计有业务时间的记录数
            business_time_count = 0
            total_eod_count = 0
            
            if has_business_start_time:
                business_time_count = session.query(EODStatus).filter(
                    EODStatus.business_start_time.isnot(None)
                ).count()
            
            total_eod_count = session.query(EODStatus).count()
            
            from config.features import FeatureFlags
            
            return {
                'success': True,
                'database_structure': {
                    'has_business_start_time': has_business_start_time,
                    'has_business_end_time': has_business_end_time
                },
                'data_migration': {
                    'total_eod_records': total_eod_count,
                    'records_with_business_time': business_time_count,
                    'migration_percentage': (business_time_count / total_eod_count * 100) if total_eod_count > 0 else 0
                },
                'feature_flags': FeatureFlags.get_all_features()
            }
            
        except Exception as e:
            logger.error(f"获取迁移状态失败: {str(e)}")
            return {'success': False, 'message': f'获取状态失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session) 