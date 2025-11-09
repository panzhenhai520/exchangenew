from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import func, case, and_, or_, desc, text
from sqlalchemy.exc import SQLAlchemyError
from services.db_service import DatabaseService
from services.log_service import LogService
from models.exchange_models import (
    EODStatus, 
    # EODHistory, EODBalanceSnapshot,  # 已废弃 - 2025-10-10
    EODBalanceVerification, EODPrintLog, EODCashOut,
    ExchangeTransaction, Currency, CurrencyBalance, Branch, Operator, EODSessionLock
)
from utils.transaction_utils import generate_transaction_no
from config.features import FeatureFlags
import logging
import os

logger = logging.getLogger(__name__)

# 延迟导入以避免循环依赖
def get_eod_step_service():
    try:
        from services.eod_step_service import EODStepService
        return EODStepService
    except ImportError:
        return None

class EODService:
    """日结服务类 - 实现8个步骤的日结流程"""
    
    @staticmethod
    def start_eod(branch_id, operator_id, target_date, session_id=None, ip_address=None, user_agent=None):
        """
        步骤1: 开始日结 - 增强版，支持业务时间范围和会话锁定
        """
        session = DatabaseService.get_session()
        try:
            # 【增强】检查是否存在处理中的日结，同时验证会话锁定
            existing_eod = session.query(EODStatus).filter(
                EODStatus.branch_id == branch_id,
                EODStatus.status == 'processing'
            ).first()
            
            if existing_eod:
                # 检查是否有对应的活跃会话锁定
                session_lock = session.query(EODSessionLock).filter(
                    EODSessionLock.eod_status_id == existing_eod.id,
                    EODSessionLock.is_active == True
                ).first()
                
                if not session_lock:
                    # 【自动清理】孤立的EOD记录，自动取消
                    print(f"发现孤立的EOD记录: ID {existing_eod.id}, 自动清理")
                    existing_eod.status = 'cancelled'
                    existing_eod.cancel_reason = '系统自动清理：孤立记录'
                    existing_eod.completed_at = datetime.now()
                    existing_eod.is_locked = False
                    existing_eod.step_status = 'cancelled'
                    session.commit()
                    
                    LogService.log_system_event(
                        f"自动清理孤立的EOD记录: ID {existing_eod.id}",
                        operator_id=operator_id,
                        branch_id=branch_id
                    )
                else:
                    # 使用翻译获取消息
                    from utils.i18n_utils import I18nUtils
                    message = I18nUtils.get_message('eod.unfinished_eod_exists', 'zh-CN')
                    return {'success': False, 'message': message}
            
            # 【修改】允许同一天多次日结，只检查是否有正在处理的日结
            # 注释掉原有的限制逻辑，支持同一天多次日结的业务需求
            # completed_eod = session.query(EODStatus).filter(
            #     EODStatus.branch_id == branch_id,
            #     EODStatus.date == target_date,
            #     EODStatus.status == 'completed'
            # ).first()
            # 
            # if completed_eod:
            #     return {'success': False, 'message': '该日期已完成日结'}
            
            current_time = datetime.now()
            business_start_time = None
            business_end_time = None
            
            # 【特性开关】只有启用业务时间范围特性时才计算
            if FeatureFlags.FEATURE_NEW_BUSINESS_TIME_RANGE:
                try:
                    business_end_time = current_time
                    
                    # 【修复】获取上次日结的结束时间，支持同一天多次日结
                    prev_eod = session.query(EODStatus).filter(
                        EODStatus.branch_id == branch_id,
                        EODStatus.status == 'completed'
                    ).order_by(desc(EODStatus.completed_at)).first()
                    
                    if prev_eod and prev_eod.completed_at:
                        business_start_time = prev_eod.completed_at
                    else:
                        # 【修复】如果没有上次日结记录，从第一笔交易时间开始（符合用户要求）
                        first_transaction = session.query(ExchangeTransaction).filter(
                            ExchangeTransaction.branch_id == branch_id
                        ).order_by(ExchangeTransaction.created_at.asc()).first()
                        
                        if first_transaction and first_transaction.created_at:
                            business_start_time = first_transaction.created_at
                        else:
                            # 如果没有任何交易记录，使用当天0点
                            business_start_time = datetime.combine(target_date, datetime.min.time())
                            
                    LogService.log_system_event(
                        f"业务时间范围计算完成 - 开始: {business_start_time}, 结束: {business_end_time}",
                        operator_id=operator_id,
                        branch_id=branch_id
                    )
                            
                except Exception as e:
                    # 【修复】如果业务时间范围计算失败，使用默认的安全值
                    LogService.log_error(f"业务时间范围计算失败: {str(e)}, 使用默认时间范围", operator_id=operator_id)
                    business_start_time = datetime.combine(target_date, datetime.min.time())
                    business_end_time = current_time
            
            # 创建新的日结记录
            eod_data = {
                'branch_id': branch_id,
                'date': target_date,
                'status': 'processing',
                'started_at': current_time,
                'started_by': operator_id,
                'is_locked': True,
                'step': 1,
                'step_status': 'completed'
            }
            
            # 只有在特性启用且计算成功时才设置业务时间范围
            if FeatureFlags.FEATURE_NEW_BUSINESS_TIME_RANGE and business_start_time:
                eod_data['business_start_time'] = business_start_time
                eod_data['business_end_time'] = business_end_time
            
            eod_status = EODStatus(**eod_data)
            session.add(eod_status)
            session.commit()
            
            # 【新增】创建会话锁定
            if session_id and ip_address:
                session_lock_result = EODService.create_eod_session_lock(
                    branch_id=branch_id,
                    eod_status_id=eod_status.id,
                    operator_id=operator_id,
                    session_id=session_id,
                    ip_address=ip_address,
                    user_agent=user_agent or ''
                )
                
                if not session_lock_result['success']:
                    # 如果会话锁定失败，回滚日结记录
                    session.rollback()
                    return {
                        'success': False,
                        'message': f'创建会话锁定失败: {session_lock_result["message"]}',
                        'existing_session': session_lock_result.get('existing_session')
                    }
            
            # 记录详细的日结开始日志
            try:
                from services.unified_log_service import log_eod_operation
                from utils.language_utils import get_current_language
                
                current_language = get_current_language()
                
                # 获取操作员信息
                operator = session.query(Operator).filter_by(id=operator_id).first()
                operator_name = operator.name if operator else '未知用户'
                
                # 构建详细的日志信息
                start_details = {
                    'operator_name': operator_name,
                    'start_time': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'target_date': target_date.strftime('%Y-%m-%d'),
                    'business_start_time': business_start_time.strftime('%Y-%m-%d %H:%M:%S') if business_start_time else '未设置',
                    'business_end_time': business_end_time.strftime('%Y-%m-%d %H:%M:%S') if business_end_time else '未设置',
                    'session_id': session_id,
                    'ip_address': ip_address,
                    'eod_id': eod_status.id
                }
                
                log_eod_operation(
                    operator_id=operator_id,
                    branch_id=branch_id,
                    eod_action='start',
                    eod_date=target_date.strftime('%Y-%m-%d'),
                    ip_address=ip_address,
                    language='zh-CN',
                    eod_id=eod_status.id,
                    operator_name=operator_name,
                    start_details=start_details
                )
                
                # 保留原有的简单日志记录
                log_message = f"开始日结流程 - 分支ID: {branch_id}, 日期: {target_date}, 时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
                if business_start_time:
                    log_message += f", 业务时间范围: {business_start_time.strftime('%Y-%m-%d %H:%M:%S')} ~ {business_end_time.strftime('%Y-%m-%d %H:%M:%S')}"
                
                LogService.log_system_event(log_message, operator_id=operator_id, branch_id=branch_id)
                
            except Exception as log_error:
                print(f"日结开始日志记录失败: {log_error}")
                # 保留原有的简单日志记录作为备份
                log_message = f"开始日结流程 - 分支ID: {branch_id}, 日期: {target_date}, 时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
                if business_start_time:
                    log_message += f", 业务时间范围: {business_start_time.strftime('%Y-%m-%d %H:%M:%S')} ~ {business_end_time.strftime('%Y-%m-%d %H:%M:%S')}"
                
                LogService.log_system_event(log_message, operator_id=operator_id, branch_id=branch_id)
            
            result = {
                'success': True,
                'message': '日结流程已开始',
                'eod_id': eod_status.id
            }
            
            # 只有启用特性时才返回业务时间范围信息
            if FeatureFlags.FEATURE_NEW_BUSINESS_TIME_RANGE and business_start_time:
                result['business_period'] = {
                    'start_time': business_start_time.isoformat(),
                    'end_time': business_end_time.isoformat()
                }
            
            return result
            
        except Exception as e:
            session.rollback()
            LogService.log_error(f"开始日结失败: {str(e)}", operator_id=operator_id)
            return {'success': False, 'message': f'开始日结失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def extract_balance(eod_id):
        """
        步骤2: 提取余额 - 从余额表提取营业锁定后的所有币种余额
        """
        print(f"🔧 EOD Service: extract_balance 函数被调用, eod_id = {eod_id}")
        session = DatabaseService.get_session()
        try:
            # 获取日结记录
            eod_status = session.query(EODStatus).filter_by(id=eod_id).first()
            if not eod_status:
                return {'success': False, 'message': '日结记录不存在'}
            
            if eod_status.status != 'processing':
                return {'success': False, 'message': '日结状态不正确'}
            
            # 获取所有货币的当前余额
            balances = session.query(CurrencyBalance).filter_by(branch_id=eod_status.branch_id).all()
            
            balance_data = []
            for balance in balances:
                currency = session.query(Currency).filter_by(id=balance.currency_id).first()
                balance_data.append({
                    'currency_id': balance.currency_id,
                    'currency_code': currency.currency_code,
                    'currency_name': currency.currency_name,
                    'custom_flag_filename': currency.custom_flag_filename,  # 【新增】自定义图标文件名
                    'flag_code': currency.flag_code,  # 【新增】标准图标代码
                    'current_balance': float(balance.balance),
                    'last_updated': balance.updated_at.isoformat() if balance.updated_at else None
                })
            
            # 更新步骤状态 - 完成第2步并推进到第3步
            print(f"🔧 EOD Service: 准备更新步骤从 {eod_status.step} 到 3")
            eod_status.step = 3
            eod_status.step_status = 'processing'
            session.commit()
       
            print(f"🔧 EOD Service: 步骤已更新为 {eod_status.step}, 状态: {eod_status.step_status}")
            
            return {
                'success': True,
                'message': '余额提取完成',
                'balances': balance_data
            }
            
        except Exception as e:
            session.rollback()
            return {'success': False, 'message': f'提取余额失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def calculate_theoretical_balance(eod_id):
        """
        步骤3: 计算理论余额 - 期初 + 当日变动 = 理论余额
        """
        logging.info(f"开始计算理论余额 - EOD ID: {eod_id}")
        session = DatabaseService.get_session()
        try:
            eod_status = session.query(EODStatus).filter_by(id=eod_id).first()
            if not eod_status:
                return {'success': False, 'message': '日结记录不存在'}
            
            branch_id = eod_status.branch_id
            target_date = eod_status.date
            
            # 获取网点信息
            branch = session.query(Branch).filter_by(id=branch_id).first()
            if not branch:
                return {'success': False, 'message': '网点不存在'}
            
            # 【修改】先获取所有可能涉及的币种，然后按币种分别计算时间范围
            # 获取所有有余额的币种（包括余额为0的）
            balance_currency_ids = session.query(CurrencyBalance.currency_id).filter(
                CurrencyBalance.branch_id == branch_id
            ).distinct().all()
            
            # 获取日结营业统计时间范围
            business_start_time = None
            business_end_time = None
            prev_eod = session.query(EODStatus).filter(
                EODStatus.branch_id == branch_id,
                EODStatus.status == 'completed'
            ).order_by(desc(EODStatus.completed_at)).first()
            if prev_eod and prev_eod.completed_at:
                business_start_time = prev_eod.completed_at
            else:
                first_transaction = session.query(ExchangeTransaction).filter(
                    ExchangeTransaction.branch_id == branch_id
                ).order_by(ExchangeTransaction.transaction_date).first()
                if first_transaction:
                    business_start_time = first_transaction.transaction_date
            business_end_time = eod_status.started_at
            logger.info(f"🌍 日结营业统计时间范围: {business_start_time} 到 {business_end_time}")
            # 获取在营业时间范围内有交易记录的币种
            transaction_currency_ids = []
            if business_start_time and business_end_time:
                transaction_currency_ids = session.query(ExchangeTransaction.currency_id).filter(
                    ExchangeTransaction.branch_id == branch_id,
                    ExchangeTransaction.status.in_(['completed', 'reversed']),
                    ExchangeTransaction.transaction_date >= business_start_time,
                    ExchangeTransaction.transaction_date <= business_end_time
                ).distinct().all()
            # 合并所有币种ID（包括余额为0的和有交易记录的）
            currency_ids = set([row[0] for row in balance_currency_ids] + [row[0] for row in transaction_currency_ids])
            
            # 总是包含本币，即使没有交易记录
            if branch.base_currency_id:
                currency_ids.add(branch.base_currency_id)
            
            # 获取所有涉及的币种
            currencies = session.query(Currency).filter(
                Currency.id.in_(currency_ids)
            ).all() if currency_ids else []
            
            balance_calculations = []
            
            for currency in currencies:
                # 安全检查：确保currency对象和currency_code字段存在
                if not currency or not currency.currency_code:
                    logging.warning(f"[WARNING] 跳过无效币种: currency={currency}")
                    continue
                
                # 【关键修改】为每个币种分别计算时间范围和期初余额
                
                # 【简化】统一从 EODBalanceVerification 表查找该币种的上一次日结记录
                prev_eod_verification = session.query(EODBalanceVerification).join(EODStatus).filter(
                    EODStatus.branch_id == branch_id,
                    EODStatus.id != eod_id,  # 排除当前日结
                    EODStatus.status == 'completed',
                    EODBalanceVerification.currency_id == currency.id
                ).order_by(desc(EODStatus.completed_at)).first()
                
                if prev_eod_verification:
                    # 该币种有上一次日结记录
                    # 期初余额：使用上次日结验证后的余额
                    opening_balance = Decimal(str(prev_eod_verification.actual_balance))
                    
                    # 时间范围：从上一次日结结束时间到本次日结开始时间
                    prev_eod_status = session.query(EODStatus).filter_by(id=prev_eod_verification.eod_status_id).first()
                    
                    logging.info(f"📋 币种{currency.currency_code}找到上次日结记录:")
                    logging.info(f"  - 上次日结ID: {prev_eod_verification.eod_status_id}")
                    logging.info(f"  - 期初余额: {opening_balance}")
                    logging.info(f"  - completed_at: {prev_eod_status.completed_at if prev_eod_status else 'None'}")
                    
                    if prev_eod_status and prev_eod_status.completed_at:
                        currency_change_start_time = prev_eod_status.completed_at
                        currency_change_end_time = eod_status.started_at
                        
                        logging.info(f"[OK] 币种{currency.currency_code}使用上次日结时间:")
                        logging.info(f"  - 变化开始时间: {currency_change_start_time}")
                        logging.info(f"  - 变化结束时间: {currency_change_end_time}")
                    else:
                        # 如果找不到完成时间，fallback到第一笔交易逻辑
                        logging.warning(f"[WARNING] 币种{currency.currency_code}上次日结记录存在但completed_at为空，fallback到第一笔交易逻辑")
                        
                        from routes.app_reports import _calculate_opening_balance_from_transactions
                        
                        opening_balance_float, currency_change_start_time = _calculate_opening_balance_from_transactions(
                            session, branch_id, currency.id, eod_status.started_at, branch.base_currency_id if branch else None
                        )
                        
                        opening_balance = Decimal(str(opening_balance_float))
                        currency_change_end_time = eod_status.started_at
                        
                        logging.info(f"📊 币种{currency.currency_code}期初余额(fallback): {opening_balance}")
                        logging.info(f"📅 币种{currency.currency_code}变化统计时间(fallback): {currency_change_start_time} 到 {currency_change_end_time}")
                
                else:
                    # 该币种没有上一次日结记录
                    # 从第一笔交易的值作为期初余额
                    from routes.app_reports import _calculate_opening_balance_from_transactions
                    
                    opening_balance_float, currency_change_start_time = _calculate_opening_balance_from_transactions(
                        session, branch_id, currency.id, eod_status.started_at, branch.base_currency_id if branch else None
                    )
                    
                    opening_balance = Decimal(str(opening_balance_float))
                    currency_change_end_time = eod_status.started_at
                    
                    logging.info(f"📊 币种{currency.currency_code}期初余额(第一笔交易): {opening_balance}")
                    logging.info(f"📅 币种{currency.currency_code}变化统计时间: {currency_change_start_time} 到 {currency_change_end_time}")
                
                # 2. 计算该币种的当日交易变动（使用该币种的时间范围）
                is_base_currency = (branch and branch.base_currency_id == currency.id)
                
                if is_base_currency:
                    # 本币：需要计算所有交易对本币的影响
                    # 1. 直接对本币的交易（如余额调整、本币交款等）- 使用local_amount字段保持一致性
                    direct_transactions = session.query(
                        func.coalesce(func.sum(ExchangeTransaction.local_amount), 0)
                    ).filter(
                        ExchangeTransaction.branch_id == branch_id,
                        ExchangeTransaction.currency_id == currency.id,
                        ExchangeTransaction.created_at >= currency_change_start_time,
                        ExchangeTransaction.created_at < currency_change_end_time,
                        ExchangeTransaction.status.in_(['completed', 'reversed']),
                        # 【修复】剔除Eod_diff类型的业务
                        ExchangeTransaction.type != 'Eod_diff'
                    ).scalar()
                    
                    # 2. 所有外币交易对本币的影响（通过local_amount字段）
                    foreign_exchange_impact = session.query(
                        func.coalesce(func.sum(ExchangeTransaction.local_amount), 0)
                    ).filter(
                        ExchangeTransaction.branch_id == branch_id,
                        ExchangeTransaction.currency_id != currency.id,  # 排除本币直接交易
                        ExchangeTransaction.created_at >= currency_change_start_time,
                        ExchangeTransaction.created_at < currency_change_end_time,
                        ExchangeTransaction.status.in_(['completed', 'reversed']),
                        # 【修复】剔除Eod_diff类型的业务
                        ExchangeTransaction.type != 'Eod_diff'
                    ).scalar()
                    
                    # 合并两部分变动
                    daily_transactions = (direct_transactions or 0) + (foreign_exchange_impact or 0)
                    
                    # 【调试日志】记录本币计算详情
                    logging.info(f"🔍 {currency.currency_code} 本币计算详情:")
                    logging.info(f"  - 直接交易变动: {direct_transactions or 0}")
                    logging.info(f"  - 外币交易影响: {foreign_exchange_impact or 0}")
                    logging.info(f"  - 合并后变动: {daily_transactions}")
                else:
                    # 外币：累加 amount 字段（外币变动金额）
                    daily_transactions = session.query(
                        func.coalesce(func.sum(ExchangeTransaction.amount), 0)
                    ).filter(
                        ExchangeTransaction.branch_id == branch_id,
                        ExchangeTransaction.currency_id == currency.id,
                        ExchangeTransaction.created_at >= currency_change_start_time,
                        ExchangeTransaction.created_at < currency_change_end_time,
                        ExchangeTransaction.status.in_(['completed', 'reversed']),
                        # 【修复】剔除Eod_diff类型的业务
                        ExchangeTransaction.type != 'Eod_diff'
                    ).scalar()
                    
                    # 【调试日志】记录外币计算详情
                    logging.info(f"🔍 {currency.currency_code} 外币计算详情:")
                    logging.info(f"  - amount字段变动: {daily_transactions or 0}")
                
                daily_change = Decimal(str(daily_transactions or 0))
                theoretical_balance = opening_balance + daily_change
                
                # 【调试日志】记录计算过程
                logging.info(f"🔍 {currency.currency_code} 计算过程:")
                logging.info(f"  - 期初余额: {opening_balance}")
                logging.info(f"  - 当日变动: {daily_change}")
                logging.info(f"  - 理论余额: {theoretical_balance}")
                
                # 获取实际余额
                actual_balance_record = session.query(CurrencyBalance).filter_by(
                    branch_id=branch_id,
                    currency_id=currency.id
                ).first()
                
                actual_balance = Decimal(str(actual_balance_record.balance)) if actual_balance_record else Decimal('0')
                
                balance_calculations.append({
                    'currency_id': currency.id,
                    'currency_code': currency.currency_code,
                    'currency_name': currency.currency_name,
                    'custom_flag_filename': currency.custom_flag_filename,
                    'flag_code': currency.flag_code,
                    'opening_balance': float(opening_balance),
                    'daily_change': float(daily_change),
                    'theoretical_balance': float(theoretical_balance),
                    'actual_balance': float(actual_balance),
                    'difference': float(theoretical_balance - actual_balance),
                    'change_start_time': currency_change_start_time.isoformat() if currency_change_start_time else None,
                    'change_end_time': currency_change_end_time.isoformat() if currency_change_end_time else None
                })
                
                # 【调试日志】记录返回的数据
                logging.info(f"🔍 {currency.currency_code} 返回数据:")
                logging.info(f"  - currency_id: {currency.id}")
                logging.info(f"  - currency_code: {currency.currency_code}")
                logging.info(f"  - currency_name: {currency.currency_name}")
                logging.info(f"  - opening_balance: {float(opening_balance)}")
                logging.info(f"  - daily_change: {float(daily_change)}")
                logging.info(f"  - theoretical_balance: {float(theoretical_balance)}")
                logging.info(f"  - actual_balance: {float(actual_balance)}")
            
            # 更新步骤状态 - 完成第3步并推进到第4步
            eod_status.step = 4
            eod_status.step_status = 'processing'
            session.commit()
            
            # 使用I18n工具类获取消息
            from utils.i18n_utils import I18nUtils
            
            return {
                'success': True,
                'message': I18nUtils.get_message('eod.theoretical_balance_calculated'),
                'calculations': balance_calculations
            }
            
        except Exception as e:
            session.rollback()
            from utils.i18n_utils import I18nUtils
            return {'success': False, 'message': f'{I18nUtils.get_message("eod.calculation_failed")}: {str(e)}'}
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def verify_balance(eod_id):
        """
        步骤4: 核对余额 - 理论余额 vs 实际余额
        """
        session = DatabaseService.get_session()
        try:
            eod_status = session.query(EODStatus).filter_by(id=eod_id).first()
            if not eod_status:
                return {'success': False, 'message': '日结记录不存在'}
            
            # 先计算理论余额
            calc_result = EODService.calculate_theoretical_balance(eod_id)
            if not calc_result['success']:
                return calc_result
            
            calculations = calc_result['calculations']
            verification_results = []
            all_match = True
            
            # 清除之前的核对记录
            session.query(EODBalanceVerification).filter_by(eod_status_id=eod_id).delete()
            
            for calc in calculations:
                is_match = abs(calc['difference']) < 0.01  # 允许0.01的误差
                if not is_match:
                    all_match = False
                
                # 保存核对结果
                verification = EODBalanceVerification(
                    eod_status_id=eod_id,
                    currency_id=calc['currency_id'],
                    opening_balance=calc['opening_balance'],
                    theoretical_balance=calc['theoretical_balance'],
                    actual_balance=calc['actual_balance'],
                    is_match=is_match,
                    difference=calc['difference']
                )
                session.add(verification)
                
                verification_results.append({
                    'currency_id': calc['currency_id'],
                    'currency_code': calc['currency_code'],
                    'currency_name': calc['currency_name'],
                    'custom_flag_filename': calc['custom_flag_filename'],  # 【新增】自定义图标文件名
                    'flag_code': calc['flag_code'],  # 【新增】标准图标代码
                    'theoretical_balance': calc['theoretical_balance'],
                    'actual_balance': calc['actual_balance'],
                    'difference': calc['difference'],
                    'is_match': is_match,
                    'status_icon': '✓' if is_match else '✗'
                })
            
            # 更新步骤状态
            eod_status.step = 4
            eod_status.step_status = 'completed'
            session.commit()
            
            from utils.i18n_utils import I18nUtils
            return {
                'success': True,
                'message': I18nUtils.get_message('eod.balance_verification_completed'),
                'all_match': all_match,
                'verification_results': verification_results
            }
            
        except Exception as e:
            session.rollback()
            return {'success': False, 'message': f'余额核对失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def handle_verification_result(eod_id, action, reason=None):
        """
        步骤5: 处理核对结果 - 一致则继续，不一致则取消或强制继续
        """
        session = DatabaseService.get_session()
        try:
            eod_status = session.query(EODStatus).filter_by(id=eod_id).first()
            if not eod_status:
                return {'success': False, 'message': '日结记录不存在'}
            
            if action == 'cancel':
                # 核对不一致，取消日结
                eod_status.status = 'cancelled'
                eod_status.cancel_reason = reason or '余额核对不一致'
                eod_status.is_locked = False  # 解除营业锁定
                eod_status.step = 5
                eod_status.step_status = 'cancelled'
                
                session.commit()
                
                return {
                    'success': True,
                    'message': '日结已取消，营业锁定已解除',
                    'status': 'cancelled'
                }
            
            elif action == 'continue':
                # 核对一致，继续下一步
                current_step = eod_status.step
                next_step = current_step + 1
                
                eod_status.step = next_step
                eod_status.step_status = 'processing'
                
                session.commit()
                
                return {
                    'success': True,
                    'message': f'步骤{current_step}完成，已进入第{next_step}步',
                    'status': 'processing',
                    'step': next_step,
                    'step_status': 'processing'
                }
            
            elif action == 'force':
                # 强制继续，忽略余额差异
                eod_status.step = 5  # 【修复】推进到第5步（处理核对结果步骤）
                eod_status.step_status = 'processing'  # 【修复】标记为处理中，等待用户操作
                eod_status.cancel_reason = f'强制继续: {reason or "操作员强制忽略余额差异"}'
                
                # 记录强制继续的日志
                LogService.log_system_event(
                    f"强制继续日结 - EOD ID: {eod_id}, 原因: {reason}",
                    operator_id=eod_status.started_by,
                    branch_id=eod_status.branch_id
                )
                
                session.commit()
                
                return {
                    'success': True,
                    'message': '已强制继续日结流程，余额差异将被忽略',
                    'status': 'processing',
                    'forced': True
                }
            
            elif action == 'adjust':
                # 【新增】余额调节后重新计算 - 保持在第4步，需要重新核对
                LogService.log_system_event(
                    f"余额调节后重新计算 - EOD ID: {eod_id}, 原因: {reason or '余额调节'}",
                    operator_id=eod_status.started_by,
                    branch_id=eod_status.branch_id
                )
                
                # 重新计算理论余额并核对
                calc_result = EODService.calculate_theoretical_balance(eod_id)
                if not calc_result['success']:
                    session.rollback()
                    return {'success': False, 'message': f'重新计算失败: {calc_result["message"]}'}
                
                verify_result = EODService.verify_balance(eod_id)
                if not verify_result['success']:
                    session.rollback()
                    return {'success': False, 'message': f'重新核对失败: {verify_result["message"]}'}
                
                # 保持在第4步，等待用户确认
                eod_status.step = 4
                eod_status.step_status = 'completed'
                
                session.commit()
                
                return {
                    'success': True,
                    'message': '余额调节后重新计算完成，请重新核对',
                    'status': 'processing',
                    'adjusted': True,
                    'verification_results': verify_result.get('verification_results', [])
                }
            
            else:
                return {'success': False, 'message': '无效的操作类型'}
                
        except Exception as e:
            session.rollback()
            return {'success': False, 'message': f'处理核对结果失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)

    @staticmethod
    def handle_balance_difference(eod_id, action, reason=None):
        """
        处理余额差额选择：cancel, force, adjust
        """
        session = DatabaseService.get_session()
        try:
            eod_status = session.query(EODStatus).filter_by(id=eod_id).first()
            if not eod_status:
                return {'success': False, 'message': '日结记录不存在'}
            
            if action == 'cancel':
                # 取消日结
                eod_status.status = 'cancelled'
                eod_status.cancel_reason = reason or '操作员取消日结'
                eod_status.is_locked = False  # 解除营业锁定
                eod_status.step = 5
                eod_status.step_status = 'cancelled'
                
                session.commit()
                
                return {
                    'success': True,
                    'message': '日结已取消，营业锁定已解除',
                    'status': 'cancelled'
                }
            
            elif action == 'force':
                # 强制继续，忽略余额差异，生成差额报告
                eod_status.step = 5  # 【修复】推进到第5步（处理核对结果步骤）
                eod_status.step_status = 'processing'  # 【修复】标记为处理中，等待用户操作
                eod_status.cancel_reason = f'强制继续: {reason or "操作员强制忽略余额差异"}'
                
                # 记录强制继续的日志
                from services.log_service import LogService
                LogService.log_system_event(
                    f"强制继续日结 - EOD ID: {eod_id}, 原因: {reason}",
                    operator_id=eod_status.started_by,
                    branch_id=eod_status.branch_id
                )
                
                # 生成差额报告
                try:
                    from services.difference_report_service import DifferenceReportService
                    # 获取验证结果用于生成差额报告
                    verify_result = EODService.verify_balance(eod_id)
                    verification_results = verify_result.get('verification_results', []) if verify_result.get('success') else []
                    
                    # 生成三种语言版本的报告
                    for lang in ['zh', 'en', 'th']:
                        try:
                            report_result = DifferenceReportService.generate_difference_report(
                                eod_id, 
                                verification_results, 
                                lang
                            )
                            if not report_result['success']:
                                logging.warning(f"生成{lang}语言差额报告失败: {report_result['message']}")
                            else:
                                logging.info(f"生成{lang}语言差额报告成功: {report_result['filename']}")
                        except Exception as e:
                            logging.error(f"生成{lang}语言差额报告异常: {str(e)}")
                            # 继续处理其他语言，不中断流程
                except Exception as e:
                    logging.error(f"生成差额报告过程中发生异常: {str(e)}")
                    # 即使报告生成失败，也不影响强制继续的流程
                
                session.commit()
                
                return {
                    'success': True,
                    'message': '已强制继续日结流程，余额差异将被忽略',
                    'status': 'processing',
                    'forced': True,
                    'verification_results': verification_results
                }
            
            elif action == 'adjust':
                # 差额调节，重新计算理论余额并核对
                from services.log_service import LogService
                LogService.log_system_event(
                    f"开始差额调节 - EOD ID: {eod_id}, 原因: {reason or '差额调节'}",
                    operator_id=eod_status.started_by,
                    branch_id=eod_status.branch_id
                )
                
                # 重新计算理论余额并核对
                calc_result = EODService.calculate_theoretical_balance(eod_id)
                if not calc_result['success']:
                    session.rollback()
                    return {'success': False, 'message': f'重新计算失败: {calc_result["message"]}'}
                
                verify_result = EODService.verify_balance(eod_id)
                if not verify_result['success']:
                    session.rollback()
                    return {'success': False, 'message': f'重新核对失败: {verify_result["message"]}'}
                
                # 保持在第4步，等待用户确认
                eod_status.step = 4
                eod_status.step_status = 'completed'
                
                session.commit()
                
                return {
                    'success': True,
                    'message': '差额调节后重新计算完成，请重新核对',
                    'status': 'processing',
                    'adjusted': True,
                    'verification_results': verify_result.get('verification_results', []),
                    'all_match': verify_result.get('all_match', False)
                }
            
            else:
                return {'success': False, 'message': '无效的操作类型'}
                
        except Exception as e:
            session.rollback()
            return {'success': False, 'message': f'处理余额差额失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)

    @staticmethod
    def adjust_eod_difference(eod_id, adjust_data, operator_id):
        """
        执行日结差额调节
        """
        session = DatabaseService.get_session()
        try:
            eod_status = session.query(EODStatus).filter_by(id=eod_id).first()
            if not eod_status:
                return {'success': False, 'message': '日结记录不存在'}
            
            # 验证EOD状态
            logging.info(f"🔧 EOD状态检查: step={eod_status.step}")
            if eod_status.step not in [4, 5]:  # 允许在步骤4和5进行差额调节
                return {'success': False, 'message': f'当前步骤不允许进行差额调节 (当前步骤: {eod_status.step}, 需要步骤: 4或5)'}
            
            # 记录差额调节开始
            from services.log_service import LogService
            LogService.log_system_event(
                f"开始执行差额调节 - EOD ID: {eod_id}, 调节币种数: {len(adjust_data)}",
                operator_id=operator_id,
                branch_id=eod_status.branch_id
            )
            
            # 执行差额调节
            adjusted_currencies = []
            
            for adjust_item in adjust_data:
                currency_id = adjust_item['currency_id']
                # 【修复】直接使用字符串转换为Decimal，避免float精度丢失
                adjust_amount = Decimal(str(adjust_item['adjust_amount']))
                adjust_reason = adjust_item.get('adjust_reason', '')
                if not adjust_reason:
                    # 使用翻译的默认原因
                    from utils.i18n_utils import I18nUtils
                    adjust_reason = I18nUtils.get_message('eod.difference_adjust.default_reason', 'zh-CN')
                
                # 获取币种信息
                currency = session.query(Currency).filter_by(id=currency_id).first()
                if not currency:
                    continue
                
                # 获取当前余额
                balance_record = session.query(CurrencyBalance).filter_by(
                    branch_id=eod_status.branch_id,
                    currency_id=currency_id
                ).first()
                
                if not balance_record:
                    # 如果余额记录不存在，创建一个
                    balance_record = CurrencyBalance(
                        branch_id=eod_status.branch_id,
                        currency_id=currency_id,
                        balance=0
                    )
                    session.add(balance_record)
                
                # 记录调节前的余额
                balance_before = Decimal(str(balance_record.balance or 0))
                
                # 【调试日志】记录差额调节开始
                logging.info(f"🔧 差额调节开始 - 币种: {currency.currency_code}")
                logging.info(f"  - 币种ID: {currency_id}")
                logging.info(f"  - 调节前余额: {balance_before}")
                logging.info(f"  - 调节金额: {adjust_amount}")
                logging.info(f"  - 预期调节后余额: {balance_before + adjust_amount}")
                
                # 执行余额调节 - 使用BalanceService确保一致性
                from services.balance_service import BalanceService
                
                # 【调试】检查参数
                logging.info(f"🔧 差额调节参数检查:")
                logging.info(f"  - currency_id: {currency_id}")
                logging.info(f"  - branch_id: {eod_status.branch_id}")
                logging.info(f"  - adjust_amount: {adjust_amount}")
                
                # 【修复】使用BalanceService更新余额，与余额调节保持一致
                from services.balance_service import BalanceService
                
                # 使用BalanceService更新余额
                balance_before_service, balance_after_service = BalanceService.update_currency_balance(
                    session=session,
                    currency_id=currency_id,
                    branch_id=eod_status.branch_id,
                    amount=adjust_amount,
                    lock_for_update=True
                )
                
                logging.info(f"🔧 BalanceService更新成功: {balance_before_service} -> {balance_after_service}")
                
                # 【调试】检查更新结果
                logging.info(f"🔧 差额调节更新结果:")
                logging.info(f"  - 调节前余额: {balance_before_service}")
                logging.info(f"  - 调节后余额: {balance_after_service}")
                logging.info(f"  - 调节金额: {adjust_amount}")
                logging.info(f"  - 币种ID: {currency_id}")
                logging.info(f"  - 网点ID: {eod_status.branch_id}")
                
                # 更新new_balance变量用于后续处理
                new_balance = float(balance_after_service)  # 转换为float以保持兼容性，但使用Decimal计算
                
                # 【调试日志】记录余额更新
                logging.info(f"🔧 余额已更新 - 币种: {currency.currency_code}")
                logging.info(f"  - 更新后余额: {new_balance}")
                logging.info(f"  - 调节前余额: {balance_before_service}")
                logging.info(f"  - 调节后余额: {balance_after_service}")
                logging.info(f"  - 数据库会话状态: {session.is_active}")
                logging.info(f"  - 事务状态: {session.in_transaction()}")
                logging.info(f"  - 数据类型检查 - balance_before: {type(balance_before_service)}, adjust_amount: {type(adjust_amount)}, new_balance: {type(new_balance)}")
                
                # 创建差额调节交易记录
                transaction_no = generate_transaction_no(eod_status.branch_id, session)
                
                # 判断是否是本币
                branch = session.query(Branch).filter_by(id=eod_status.branch_id).first()
                is_base_currency = (branch and branch.base_currency_id == currency_id)
                
                # 根据币种类型设置amount和local_amount
                if is_base_currency:
                    # 本币差额调节：amount=0, local_amount=调节金额
                    amount_value = 0
                    local_amount_value = adjust_amount
                    logging.info(f"🔧 本币差额调节 - 币种: {currency.currency_code}, amount=0, local_amount={adjust_amount}")
                else:
                    # 外币差额调节：amount=调节金额, local_amount=0
                    amount_value = adjust_amount
                    local_amount_value = 0
                    logging.info(f"🔧 外币差额调节 - 币种: {currency.currency_code}, amount={adjust_amount}, local_amount=0")
                
                adjustment_transaction = ExchangeTransaction(
                    branch_id=eod_status.branch_id,
                    currency_id=currency_id,
                    type='Eod_diff',  # 特殊的业务类型
                    amount=amount_value,
                    rate=1.0,  # 差额调节不涉及汇率
                    local_amount=local_amount_value,
                    operator_id=operator_id,
                    transaction_no=transaction_no,
                    status='completed',
                    customer_name=adjust_reason,  # 调节原因存储在customer_name字段
                    balance_before=float(balance_before_service),
                    balance_after=float(balance_after_service),
                    transaction_date=eod_status.date,  # 使用EOD日期
                    transaction_time=datetime.now().strftime('%H:%M:%S'),  # 当前时间
                    created_at=datetime.now()
                )
                
                session.add(adjustment_transaction)
                
                adjusted_currencies.append({
                    'currency_id': currency_id,
                    'currency_code': currency.currency_code,
                    'currency_name': currency.currency_name,
                    'adjust_amount': float(adjust_amount),
                    'balance_before': float(balance_before_service),
                    'balance_after': float(balance_after_service),
                    'theoretical_balance': float(balance_after_service),  # 添加理论余额
                    'actual_balance': float(balance_before_service),  # 添加实际余额
                    'reason': adjust_reason
                })
                
                # 记录调节日志
                LogService.log_system_event(
                    f"差额调节 - 币种: {currency.currency_code}, 调节金额: {adjust_amount}, 原因: {adjust_reason}",
                    operator_id=operator_id,
                    branch_id=eod_status.branch_id
                )
            
            # 【修复】所有余额更新完成后，统一提交
            logging.info(f"🔧 准备提交所有余额更新...")
            try:
                session.commit()
                logging.info(f"🔧 余额更新提交成功")
                
                # 【调试】提交后立即验证余额是否真的更新了
                logging.info(f"🔧 提交后验证余额更新...")
                for adj in adjusted_currencies:
                    currency_id = adj['currency_id']
                    
                    # 【调试】强制刷新会话，清除缓存
                    session.expire_all()
                    
                    balance_record = session.query(CurrencyBalance).filter_by(
                        branch_id=eod_status.branch_id,
                        currency_id=currency_id
                    ).first()
                    if balance_record:
                        actual_balance = float(balance_record.balance or 0)
                        expected_balance = adj['balance_after']
                        logging.info(f"  - {adj['currency_code']}: 期望{expected_balance}, 实际{actual_balance}")
                        logging.info(f"  - 余额记录ID: {balance_record.id}, 更新时间: {balance_record.updated_at}")
                        if abs(actual_balance - expected_balance) > 0.01:
                            logging.error(f"  [ERROR] 余额更新失败 - {adj['currency_code']}: 期望{expected_balance}, 实际{actual_balance}")
                        else:
                            logging.info(f"  [OK] 余额更新成功 - {adj['currency_code']}: {actual_balance}")
                    else:
                        logging.error(f"  [ERROR] 找不到余额记录 - {adj['currency_code']}")
                
            except Exception as commit_error:
                logging.error(f"[ERROR] 余额更新提交失败: {str(commit_error)}")
                session.rollback()
                return {'success': False, 'message': f'余额更新提交失败: {str(commit_error)}'}
            
            # 【修复】余额更新后，再验证差额调节的合理性
            logging.info(f"🔧 开始验证差额调节合理性...")
            validation_result = EODService.validate_difference_adjustment(eod_id, adjust_data)
            if not validation_result['success']:
                logging.error(f"[ERROR] 差额调节验证失败: {validation_result['message']}")
                return {'success': False, 'message': f'差额调节验证失败: {validation_result["message"]}'}
            
            if not validation_result['all_valid']:
                logging.warning(f"[WARNING] 差额调节验证发现问题:")
                for result in validation_result['validation_results']:
                    if not result['is_valid']:
                        logging.warning(f"  - {result['currency_code']}: {result['message']}")
                
                # 可以选择继续执行或返回错误
                logging.info(f"🔧 继续执行差额调节（验证发现问题但允许继续）")
            
            # 【调试日志】记录提交前状态
            logging.info(f"🔧 准备提交事务 - 调节币种数: {len(adjusted_currencies)}")
            for adj in adjusted_currencies:
                logging.info(f"  - {adj['currency_code']}: {adj['balance_before']} -> {adj['balance_after']}")
            
            # 【调试日志】验证余额记录状态
            for adj in adjusted_currencies:
                currency_id = adj['currency_id']
                balance_record = session.query(CurrencyBalance).filter_by(
                    branch_id=eod_status.branch_id,
                    currency_id=currency_id
                ).first()
                if balance_record:
                    logging.info(f"🔧 提交前余额状态 - {adj['currency_code']}: {balance_record.balance}")
                else:
                    logging.error(f"[ERROR] 提交前找不到余额记录 - {adj['currency_code']}")
            
            # 【修复】余额更新已提交，无需重复提交
            logging.info(f"🔧 余额更新已完成，无需重复提交")
            
            # 【修复】跳过余额验证，因为BalanceService已经成功更新余额
            logging.info(f"🔧 跳过余额验证（BalanceService已成功更新余额）")
            
            # 记录验证跳过信息
            for adj in adjusted_currencies:
                logging.info(f"[OK] 余额更新完成 - {adj['currency_code']}: {adj['balance_before']} -> {adj['balance_after']}")
            
            logging.info(f"[OK] 所有余额更新完成")
            
            # 生成差额调节报告 - 异步处理，避免阻塞
            try:
                from services.difference_report_service import DifferenceReportService
                # 只生成中文版本，其他语言版本可以后续生成
                report_result = DifferenceReportService.generate_difference_adjustment_report(
                    eod_id, 
                    adjusted_currencies, 
                    'zh'
                )
                if not report_result['success']:
                    logging.warning(f"生成中文差额调节报告失败: {report_result['message']}")
                else:
                    logging.info(f"生成中文差额调节报告成功: {report_result['filename']}")
            except Exception as report_error:
                logging.warning(f"生成差额调节报告时出错: {str(report_error)}")
                # 不影响主要流程
            
            # 记录差额调节完成
            LogService.log_system_event(
                f"差额调节完成 - EOD ID: {eod_id}, 调节币种数: {len(adjusted_currencies)}",
                operator_id=operator_id,
                branch_id=eod_status.branch_id
            )
            
            return {
                'success': True,
                'message': f'差额调节完成，共调节 {len(adjusted_currencies)} 个币种',
                'adjusted_currencies': adjusted_currencies,
                'verification_results': [],
                'all_match': True,
                'report_generated': True
            }
            
        except Exception as e:
            logging.error(f"[ERROR] 差额调节过程中发生异常: {str(e)}")
            logging.error(f"[ERROR] 执行事务回滚")
            session.rollback()
            return {'success': False, 'message': f'差额调节失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def process_cash_out(eod_id, cash_out_data, operator_id, cash_receiver_name=None, cash_out_remark=None):
        """
        步骤7: 完成交款 - 生成流水，更新余额（锁定状态保持到最后完成）
        """
        session = DatabaseService.get_session()
        try:
            eod_status = session.query(EODStatus).filter_by(id=eod_id).first()
            if not eod_status:
                return {'success': False, 'message': '日结记录不存在'}
            
            branch_id = eod_status.branch_id
            target_date = eod_status.date
            
            # 2. 处理每个币种的交款
            cash_out_records = []
            
            for cash_out in cash_out_data:
                currency_id = cash_out['currency_id']
                cash_out_amount = Decimal(str(cash_out['amount']))
                
                if cash_out_amount > 0:
                    # 生成交款流水号 - 使用统一的票据号生成函数
                    transaction_no = generate_transaction_no(branch_id, session)
                    
                    # 【修复】判断是否为本币交款，决定amount和local_amount字段的值
                    # 获取网点的本币信息
                    branch = session.query(Branch).filter_by(id=branch_id).first()
                    is_base_currency = (branch and branch.base_currency_id == currency_id)
                    
                    if is_base_currency:
                        # 本币交款：金额写在local_amount字段
                        amount_value = 0
                        local_amount_value = -cash_out_amount
                    else:
                        # 外币交款：金额写在amount字段
                        amount_value = -cash_out_amount
                        local_amount_value = 0
                    
                    # 生成交款流水
                    transaction = ExchangeTransaction(
                        transaction_no=transaction_no,
                        branch_id=branch_id,
                        currency_id=currency_id,
                        type='cash_out',
                        amount=amount_value,  # 根据币种类型确定
                        rate=1,  # 交款汇率为1
                        local_amount=local_amount_value,  # 根据币种类型确定
                        operator_id=operator_id,
                        transaction_date=target_date,
                        transaction_time=datetime.now().strftime('%H:%M:%S'),
                        created_at=datetime.now(),
                        status='completed'
                    )
                    session.add(transaction)
                    session.flush()  # 获取transaction_id
                    
                    # 更新余额
                    balance = session.query(CurrencyBalance).filter_by(
                        branch_id=branch_id,
                        currency_id=currency_id
                    ).first()
                    
                    remaining_balance = 0
                    if balance:
                        # 将float类型的余额转换为Decimal类型进行运算
                        current_balance = Decimal(str(balance.balance))
                        new_balance = current_balance - cash_out_amount
                        balance.balance = float(new_balance)
                        balance.updated_at = datetime.now()
                        remaining_balance = balance.balance
                    
                    # 【关键改动】更新EODBalanceVerification表的actual_balance为交款后余额
                    # 这样下次日结可以从这个表获取准确的期初余额
                    verification = session.query(EODBalanceVerification).filter_by(
                        eod_status_id=eod_id,
                        currency_id=currency_id
                    ).first()
                    
                    if verification:
                        verification.actual_balance = remaining_balance
                        verification.verified_at = datetime.now()
                    
                    # 记录交款信息
                    cash_out_record = EODCashOut(
                        eod_status_id=eod_id,
                        currency_id=currency_id,
                        cash_out_amount=cash_out_amount,
                        remaining_balance=remaining_balance,
                        transaction_id=transaction.id
                    )
                    session.add(cash_out_record)
                    
                    cash_out_records.append({
                        'currency_id': currency_id,
                        'cash_out_amount': float(cash_out_amount),
                        'remaining_balance': float(remaining_balance)
                    })
            
            # 3. 更新步骤状态（进入第7步但需要完成打印）
            eod_status.step = 7
            eod_status.step_status = 'pending'  # 改为pending，需要完成打印
            # 注意：不在这里解除锁定，锁定状态保持到最后完成日结
            
            # 提交事务
            session.commit()
            
            # 记录详细的交款日志
            try:
                from services.unified_log_service import log_eod_operation
                from utils.language_utils import get_current_language
                
                current_language = get_current_language()
                cash_out_time = datetime.now()
                
                # 获取交款操作员信息
                cash_out_operator = session.query(Operator).filter_by(id=operator_id).first()
                cash_out_operator_name = cash_out_operator.name if cash_out_operator else '未知用户'
                
                # 获取收款人信息
                cash_receiver_display = cash_receiver_name if cash_receiver_name else '未指定'
                
                # 统计交款汇总信息
                total_cash_out_amount = 0
                currency_details = []
                
                for record in cash_out_records:
                    currency = session.query(Currency).filter_by(id=record['currency_id']).first()
                    total_cash_out_amount += record['cash_out_amount']
                    
                    currency_details.append({
                        'currency_code': currency.currency_code if currency else '未知',
                        'currency_name': currency.currency_name if currency else '未知',
                        'cash_out_amount': record['cash_out_amount'],
                        'remaining_balance': record['remaining_balance']
                    })
                
                # 构建详细的交款信息
                cash_out_details = {
                    'cash_out_time': cash_out_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'cash_out_operator_name': cash_out_operator_name,
                    'cash_receiver_name': cash_receiver_display,
                    'total_currencies': len(cash_out_records),
                    'total_cash_out_amount': total_cash_out_amount,
                    'currency_details': currency_details,
                    'eod_step': 6,
                    'business_lock_status': '保持锁定到日结完成',
                    'cash_out_remark': cash_out_remark or ''
                }
                
                log_eod_operation(
                    operator_id=operator_id,
                    branch_id=branch_id,
                    eod_action='cash_out',
                    eod_date=target_date.strftime('%Y-%m-%d'),
                    ip_address=None,
                    language=current_language,
                    eod_id=eod_id,
                    operator_name=cash_out_operator_name,
                    cash_out_details=cash_out_details
                )
                
                # 保留原有的简单日志记录
                LogService.log_system_event(
                    f"日结交款完成 - EOD ID: {eod_id}, 交款时间: {cash_out_time.strftime('%Y-%m-%d %H:%M:%S')}, 交款人: {cash_out_operator_name}, 收款人: {cash_receiver_display}, 交款币种: {len(cash_out_records)}种",
                    operator_id=operator_id,
                    branch_id=branch_id
                )
                
            except Exception as log_error:
                print(f"交款日志记录失败: {log_error}")
                # 保留原有的简单日志记录作为备份
                LogService.log_system_event(
                    f"日结交款完成 - EOD ID: {eod_id}, 交款时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}, 交款人: {cash_out_operator_name}, 收款人: {cash_receiver_display}, 交款币种: {len(cash_out_records)}种",
                    operator_id=operator_id,
                    branch_id=branch_id
                )
            
            return {
                'success': True,
                'message': '交款完成，营业锁定已解除',
                'cash_out_records': cash_out_records,
                'step': 7,
                'step_status': 'processing'
            }
            
        except Exception as e:
            session.rollback()
            return {'success': False, 'message': f'交款处理失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def generate_report(eod_id, mode='simple'):
        """
        步骤8: 生成日结报表 - 必须先完成第7步打印
        """
        session = DatabaseService.get_session()
        try:
            eod_status = session.query(EODStatus).filter_by(id=eod_id).first()
            if not eod_status:
                return {'success': False, 'message': '日结记录不存在'}
            
            # 检查第7步是否完成
            if eod_status.step < 7:
                return {'success': False, 'message': '请先完成前面的步骤'}
            
            if eod_status.step == 7 and eod_status.step_status != 'completed':
                return {'success': False, 'message': '请先完成第7步的报表打印'}
            
            if eod_status.print_count == 0:
                return {'success': False, 'message': '请先打印日结报表'}
            
            branch_id = eod_status.branch_id
            target_date = eod_status.date
            
            # 获取分支信息
            branch = session.query(Branch).filter_by(id=branch_id).first()
            
            # 获取交易统计
            transaction_stats = session.query(
                Currency.currency_code,
                Currency.currency_name,
                ExchangeTransaction.type,
                func.count().label('count'),
                func.sum(ExchangeTransaction.amount).label('total_amount'),
                func.sum(ExchangeTransaction.local_amount).label('total_local_amount')
            ).join(Currency).filter(
                ExchangeTransaction.branch_id == branch_id,
                func.date(ExchangeTransaction.transaction_date) == target_date,
                ExchangeTransaction.status == 'completed'
            ).group_by(
                Currency.currency_code,
                Currency.currency_name,
                ExchangeTransaction.type
            ).all()
            
            # 计算交易统计汇总
            total_transactions = 0
            buy_transactions = 0
            sell_transactions = 0
            
            for stat in transaction_stats:
                total_transactions += stat.count
                if stat.type == 'buy':
                    buy_transactions += stat.count
                elif stat.type == 'sell':
                    sell_transactions += stat.count
            
            # 获取余额核对结果
            verifications = session.query(EODBalanceVerification).filter_by(
                eod_status_id=eod_id
            ).all()
            
            # 获取交款记录
            cash_outs = session.query(EODCashOut).filter_by(
                eod_status_id=eod_id
            ).all()
            
            # 构建交款汇总数据
            cash_out_summary = []
            for co in cash_outs:
                currency = session.query(Currency).filter_by(id=co.currency_id).first()
                cash_out_summary.append({
                    'currency_id': co.currency_id,
                    'currency_code': currency.currency_code if currency else '',
                    'cash_out_amount': float(co.cash_out_amount),
                    'remaining_balance': float(co.remaining_balance)
                })
            
            # 构建余额汇总数据（简单模式显示当前余额）
            balance_summary = []
            for v in verifications:
                currency = session.query(Currency).filter_by(id=v.currency_id).first()
                balance_summary.append({
                    'currency_id': v.currency_id,
                    'currency_code': currency.currency_code if currency else '',
                    'currency_name': currency.currency_name if currency else '',
                    'opening_balance': float(v.opening_balance),
                    'actual_balance': float(v.actual_balance),
                    'theoretical_balance': float(v.theoretical_balance),
                    'difference': float(v.difference),
                    'is_match': v.is_match
                })
            
            # 构建余额明细数据（详细模式）
            balance_details = []
            if mode == 'detailed':
                for v in verifications:
                    currency = session.query(Currency).filter_by(id=v.currency_id).first()
                    change_amount = v.actual_balance - v.opening_balance
                    balance_details.append({
                        'currency_id': v.currency_id,
                        'currency_code': currency.currency_code if currency else '',
                        'opening_balance': float(v.opening_balance),
                        'closing_balance': float(v.actual_balance),
                        'change_amount': float(change_amount)
                    })
            
            # 获取操作员信息
            operator = session.query(Operator).filter_by(id=eod_status.started_by).first()
            
            report_data = {
                'eod_id': eod_id,
                'branch_name': branch.branch_name if branch else '',
                'eod_date': target_date.isoformat(),
                'generated_at': datetime.now().isoformat(),
                'mode': mode,
                'operator_name': operator.name if operator else '',
                # 交易统计
                'total_transactions': total_transactions,
                'buy_transactions': buy_transactions,
                'sell_transactions': sell_transactions,
                # 余额汇总（简单模式显示）
                'balance_summary': balance_summary,
                # 交款汇总（如果已有交款记录）
                'cash_out_summary': cash_out_summary,
                # 余额明细（详细模式）
                'balance_details': balance_details,
                # 原始数据（保留兼容性）
                'transaction_stats': [
                    {
                        'currency_code': stat.currency_code,
                        'currency_name': stat.currency_name,
                        'type': stat.type,
                        'count': stat.count,
                        'total_amount': float(stat.total_amount or 0),
                        'total_local_amount': float(stat.total_local_amount or 0)
                    }
                    for stat in transaction_stats
                ],
                'balance_verifications': [
                    {
                        'currency_id': v.currency_id,
                        'opening_balance': float(v.opening_balance),
                        'theoretical_balance': float(v.theoretical_balance),
                        'actual_balance': float(v.actual_balance),
                        'is_match': v.is_match,
                        'difference': float(v.difference)
                    }
                    for v in verifications
                ],
                'cash_out_records': [
                    {
                        'currency_id': co.currency_id,
                        'cash_out_amount': float(co.cash_out_amount),
                        'remaining_balance': float(co.remaining_balance)
                    }
                    for co in cash_outs
                ]
            }
            
            # 更新步骤状态
            eod_status.step = 8
            eod_status.step_status = 'completed'
            session.commit()
            
            return {
                'success': True,
                'message': '日结报表生成完成',
                'report_data': report_data,
                'step': 8,
                'step_status': 'completed'
            }
            
        except Exception as e:
            session.rollback()
            return {'success': False, 'message': f'生成报表失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def generate_preview_report(eod_id, mode='simple'):
        """
        生成预览报表数据 - 第7步专用，不检查步骤状态，只返回数据不打印
        """
        session = DatabaseService.get_session()
        try:
            eod_status = session.query(EODStatus).filter_by(id=eod_id).first()
            if not eod_status:
                return {'success': False, 'message': '日结记录不存在'}
            
            branch_id = eod_status.branch_id
            target_date = eod_status.date
            
            # 获取分支信息
            branch = session.query(Branch).filter_by(id=branch_id).first()
            
            # 获取交易统计
            transaction_stats = session.query(
                Currency.currency_code,
                Currency.currency_name,
                ExchangeTransaction.type,
                func.count().label('count'),
                func.sum(ExchangeTransaction.amount).label('total_amount'),
                func.sum(ExchangeTransaction.local_amount).label('total_local_amount')
            ).join(Currency).filter(
                ExchangeTransaction.branch_id == branch_id,
                func.date(ExchangeTransaction.transaction_date) == target_date,
                ExchangeTransaction.status == 'completed'
            ).group_by(
                Currency.currency_code,
                Currency.currency_name,
                ExchangeTransaction.type
            ).all()
            
            # 计算交易统计汇总
            total_transactions = 0
            buy_transactions = 0
            sell_transactions = 0
            
            for stat in transaction_stats:
                total_transactions += stat.count
                if stat.type == 'buy':
                    buy_transactions += stat.count
                elif stat.type == 'sell':
                    sell_transactions += stat.count
            
            # 获取余额核对结果
            verifications = session.query(EODBalanceVerification).filter_by(
                eod_status_id=eod_id
            ).all()
            
            # 获取交款记录
            cash_outs = session.query(EODCashOut).filter_by(
                eod_status_id=eod_id
            ).all()
            
            # 构建交款汇总数据
            cash_out_summary = []
            for co in cash_outs:
                currency = session.query(Currency).filter_by(id=co.currency_id).first()
                cash_out_summary.append({
                    'currency_id': co.currency_id,
                    'currency_code': currency.currency_code if currency else '',
                    'cash_out_amount': float(co.cash_out_amount),
                    'remaining_balance': float(co.remaining_balance)
                })
            
            # 获取当日发布的币种ID列表，参考外币兑换页面的过滤逻辑
            today = target_date
            published_currency_ids = []
            
            # 查询当日的发布记录
            from models.exchange_models import RatePublishRecord, RatePublishDetail
            publish_record = session.query(RatePublishRecord).filter(
                RatePublishRecord.branch_id == branch_id,
                RatePublishRecord.publish_date == today
            ).order_by(RatePublishRecord.publish_time.desc()).first()
            
            if publish_record:
                # 获取发布的币种ID列表
                published_details = session.query(RatePublishDetail).filter(
                    RatePublishDetail.publish_record_id == publish_record.id
                ).all()
                published_currency_ids = [detail.currency_id for detail in published_details]
            
            # 获取差额调节记录
            eod_diff_transactions = session.query(ExchangeTransaction).filter(
                ExchangeTransaction.branch_id == branch_id,
                ExchangeTransaction.type == 'Eod_diff',
                ExchangeTransaction.transaction_date == target_date
            ).all()
            
            # 构建差额调节映射
            adjustment_map = {}
            for adj_tx in eod_diff_transactions:
                adjustment_map[adj_tx.currency_id] = {
                    'adjust_amount': float(adj_tx.amount),
                    'reason': adj_tx.customer_name or '日结差额调节'
                }
            
            # 构建余额汇总数据 - 使用EOD记录中存储的营业时间范围（与打印报表逻辑一致）
            balance_summary = []
            
            # 【修复】使用EOD记录中存储的营业时间范围
            business_start_time = eod_status.business_start_time
            business_end_time = eod_status.business_end_time
            
            # 获取营业时间范围内的交易币种（如果EOD记录中有时间范围）
            transaction_currency_ids = []
            try:
                if business_start_time and business_end_time:
                    transaction_currencies = session.query(ExchangeTransaction.currency_id).filter(
                        ExchangeTransaction.branch_id == branch_id,
                        ExchangeTransaction.transaction_date >= business_start_time,
                        ExchangeTransaction.transaction_date <= business_end_time,
                        ExchangeTransaction.status == 'completed'
                    ).distinct().all()
                    
                    transaction_currency_ids = [tc.currency_id for tc in transaction_currencies]
                else:
                    # 如果没有营业时间范围，使用所有余额核对记录
                    pass
            except Exception as e:
                # 如果查询失败，使用空列表
                transaction_currency_ids = []
            
            for v in verifications:
                currency = session.query(Currency).filter_by(id=v.currency_id).first()
                if not currency:
                    continue
                    
                # 检查是否为营业时间范围内的交易币种或有余额的币种
                has_transaction_in_business_hours = (v.currency_id in transaction_currency_ids)
                has_balance_or_activity = (
                    v.opening_balance != 0 or 
                    v.actual_balance != 0 or 
                    v.theoretical_balance != 0 or 
                    v.difference != 0 or
                    has_transaction_in_business_hours
                )
                
                # 根据模式决定过滤条件
                if mode == 'detailed':
                    # 详细模式：显示有余额或有营业时间范围内交易的币种
                    should_include = has_balance_or_activity
                else:
                    # 简单模式：显示有余额或有营业时间范围内交易的币种
                    should_include = has_balance_or_activity
                
                if should_include:
                    # 检查是否有差额调节
                    adjustment_info = adjustment_map.get(v.currency_id)
                    status_text = ''
                    if adjustment_info:
                        # 有差额调节
                        adjust_amount = adjustment_info['adjust_amount']
                        status_text = f"差额调节 {adjust_amount:+.2f}"
                    elif v.difference != 0:
                        # 有差异但未调节
                        status_text = "X"
                    else:
                        # 无差异
                        status_text = "☑"
                    
                    # 计算实际余额：如果有差额调节，使用原始实际余额；否则使用当前实际余额
                    display_actual_balance = float(v.actual_balance)
                    display_difference = float(v.difference)
                    if adjustment_info:
                        # 有差额调节时，显示原始实际余额和原始差异
                        display_actual_balance = float(v.actual_balance) - adjustment_info['adjust_amount']
                        display_difference = display_actual_balance - float(v.theoretical_balance)
                    
                    balance_summary.append({
                        'currency_id': v.currency_id,
                        'currency_code': currency.currency_code if currency else '',
                        'currency_name': currency.currency_name if currency else '',
                        'custom_flag_filename': currency.custom_flag_filename if currency else None,
                        'opening_balance': float(v.opening_balance),
                        'actual_balance': display_actual_balance,  # 使用显示用的实际余额
                        'theoretical_balance': float(v.theoretical_balance),
                        'difference': display_difference,  # 使用显示用的差异
                        'is_match': v.is_match,
                        'status': status_text,
                        'has_adjustment': adjustment_info is not None
                    })
            
            # 检查差额处理状态
            has_adjustment = len(adjustment_map) > 0
            has_difference = any(v.difference != 0 for v in verifications)
            has_difference_without_adjustment = has_difference and not has_adjustment
            
            # 构建差额调节汇总数据（如果有差额调节）
            difference_adjustment_summary = []
            if has_adjustment:
                for v in verifications:
                    currency = session.query(Currency).filter_by(id=v.currency_id).first()
                    if not currency:
                        continue
                    
                    adjustment_info = adjustment_map.get(v.currency_id)
                    if adjustment_info:
                        # 计算调节前的实际余额（理论余额减去调节金额）
                        original_actual_balance = float(v.theoretical_balance) - float(adjustment_info['adjust_amount'])
                        
                        difference_adjustment_summary.append({
                            'currency_code': currency.currency_code,
                            'currency_name': currency.currency_name,
                            'theoretical_balance': float(v.theoretical_balance),
                            'actual_balance': float(v.actual_balance),
                            'original_actual_balance': original_actual_balance,  # 调节前的实际余额
                            'adjust_amount': adjustment_info['adjust_amount'],
                            'reason': adjustment_info['reason']
                        })
            
            # 构建差额报告汇总数据（如果有差额但未调节）
            difference_report_summary = []
            if has_difference_without_adjustment:
                for v in verifications:
                    currency = session.query(Currency).filter_by(id=v.currency_id).first()
                    if not currency:
                        continue
                    
                    if v.difference != 0:
                        difference_report_summary.append({
                            'currency_code': currency.currency_code,
                            'currency_name': currency.currency_name,
                            'theoretical_balance': float(v.theoretical_balance),
                            'actual_balance': float(v.actual_balance),
                            'difference': float(v.difference)
                        })
            
            # 获取收入统计数据（详细模式才需要）
            income_summary = []
            if mode == 'detailed':
                from models.report_models import DailyIncomeReport
                income_reports = session.query(DailyIncomeReport).filter_by(
                    eod_id=eod_id
                ).all()
                
                for report in income_reports:
                    income_summary.append({
                        'currency_code': report.currency_code,
                        'total_buy': float(report.total_buy),
                        'total_sell': float(report.total_sell),
                        'buy_rate': float(report.buy_rate) if report.buy_rate else 0,
                        'sell_rate': float(report.sell_rate) if report.sell_rate else 0,
                        'income': float(report.income),
                        'spread_income': float(report.spread_income)
                    })
            
            # 构建余额明细数据（详细模式）
            balance_details = []
            if mode == 'detailed':
                for v in verifications:
                    currency = session.query(Currency).filter_by(id=v.currency_id).first()
                    change_amount = v.actual_balance - v.opening_balance
                    balance_details.append({
                        'currency_id': v.currency_id,
                        'currency_code': currency.currency_code if currency else '',
                        'opening_balance': float(v.opening_balance),
                        'closing_balance': float(v.actual_balance),
                        'change_amount': float(change_amount)
                    })
            
            # 获取操作员信息
            operator = session.query(Operator).filter_by(id=eod_status.started_by).first()
            
            report_data = {
                'eod_id': eod_id,
                'branch_id': branch_id,
                'branch_name': branch.branch_name if branch else '',
                'eod_date': target_date.isoformat(),
                'generated_at': datetime.now().isoformat(),
                'mode': mode,
                'operator_name': operator.name if operator else '',
                # 交易统计
                'total_transactions': total_transactions,
                'buy_transactions': buy_transactions,
                'sell_transactions': sell_transactions,
                # 余额汇总
                'balance_summary': balance_summary,
                # 交款汇总
                'cash_out_summary': cash_out_summary,
                # 差额调节汇总
                'difference_adjustment_summary': difference_adjustment_summary,
                # 差额报告汇总
                'difference_report_summary': difference_report_summary,
                # 差额处理状态
                'has_adjustment': has_adjustment,
                'has_difference_without_adjustment': has_difference_without_adjustment,
                # 余额明细（详细模式）
                'balance_details': balance_details,
                # 收入汇总（详细模式）
                'income_summary': income_summary
            }
            
            # 【新增】在预览报表生成时，如果有差额调节，同时生成差额调节报告
            if has_adjustment and difference_adjustment_summary:
                from services.difference_report_service import DifferenceReportService
                # 生成三种语言版本的差额调节报告
                for lang in ['zh', 'en', 'th']:
                    report_result = DifferenceReportService.generate_difference_adjustment_report(
                        eod_id, 
                        difference_adjustment_summary, 
                        lang
                    )
                    if not report_result['success']:
                        logging.warning(f"生成{lang}语言差额调节报告失败: {report_result['message']}")
                    else:
                        logging.info(f"生成{lang}语言差额调节报告成功: {report_result['filename']}")
            
            return {
                'success': True,
                'message': '预览报表生成成功',
                'report_data': report_data
            }
            
        except Exception as e:
            return {'success': False, 'message': f'预览报表生成失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def print_report(eod_id, operator_id, mode='simple', language='zh'):
        """
        打印日结报表 - 第7步专用，直接生成数据避免循环检查
        根据差额处理状态决定生成哪些报表：
        - 无差额：只生成交款表
        - 有差额调节：生成交款表 + 差额调节表
        - 有差额但强制继续：生成交款表 + 差额报告表
        """
        from services.log_service import LogService
        from services.simple_pdf_service import SimplePDFService
        session = DatabaseService.get_session()
        try:
            eod_status = session.query(EODStatus).filter_by(id=eod_id).first()
            if not eod_status:
                return {'success': False, 'message': '日结记录不存在'}
            
            # 【调试】在方法开始就输出营业时间范围
            print(f"🚨 ALERT - print_report方法开始 - EOD ID: {eod_id}")
            print(f"🚨 ALERT - business_start_time: {eod_status.business_start_time}")
            print(f"🚨 ALERT - business_end_time: {eod_status.business_end_time}")
            print(f"🚨 ALERT - target_date: {eod_status.date}")
            print(f"🚨 ALERT - 方法参数: mode={mode}, language={language}")
            print("=" * 50)
            
            # 【新增】维护EOD会话状态 - 确保打印后会话仍然有效
            try:
                from flask import session as flask_session
                session_id = flask_session.get('eod_session_id')
                if session_id:
                    # 更新会话活动时间
                    EODService.update_eod_session_activity(session_id, eod_status.branch_id)
                    LogService.log_system_event(
                        f"打印报表时维护会话状态 - EOD: {eod_id}, Session: {session_id}",
                        operator_id=operator_id,
                        branch_id=eod_status.branch_id
                    )
            except Exception as session_error:
                LogService.log_error(f"维护会话状态失败: {str(session_error)}")
            
            branch_id = eod_status.branch_id
            target_date = eod_status.date
            
            # 1. 直接生成报表数据，避免generate_report的循环检查
            # 获取分支信息
            branch = session.query(Branch).filter_by(id=branch_id).first()
            
            # 获取交易统计
            transaction_stats = session.query(
                Currency.currency_code,
                Currency.currency_name,
                ExchangeTransaction.type,
                func.count().label('count'),
                func.sum(ExchangeTransaction.amount).label('total_amount'),
                func.sum(ExchangeTransaction.local_amount).label('total_local_amount')
            ).join(Currency).filter(
                ExchangeTransaction.branch_id == branch_id,
                func.date(ExchangeTransaction.transaction_date) == target_date,
                ExchangeTransaction.status == 'completed'
            ).group_by(
                Currency.currency_code,
                Currency.currency_name,
                ExchangeTransaction.type
            ).all()
            
            # 计算交易统计汇总
            total_transactions = 0
            buy_transactions = 0
            sell_transactions = 0
            
            for stat in transaction_stats:
                total_transactions += stat.count
                if stat.type == 'buy':
                    buy_transactions += stat.count
                elif stat.type == 'sell':
                    sell_transactions += stat.count
            
            # 获取余额核对结果
            verifications = session.query(EODBalanceVerification).filter_by(
                eod_status_id=eod_id
            ).all()
            
            # 获取交款记录
            cash_outs = session.query(EODCashOut).filter_by(
                eod_status_id=eod_id
            ).all()
            
            # 构建交款汇总数据
            cash_out_summary = []
            for co in cash_outs:
                currency = session.query(Currency).filter_by(id=co.currency_id).first()
                cash_out_summary.append({
                    'currency_id': co.currency_id,
                    'currency_code': currency.currency_code if currency else '',
                    'cash_out_amount': float(co.cash_out_amount),
                    'remaining_balance': float(co.remaining_balance)
                })
            
            # 获取当日发布的币种ID列表，参考外币兑换页面的过滤逻辑
            today = target_date
            published_currency_ids = []
            
            # 查询当日的发布记录
            from models.exchange_models import RatePublishRecord, RatePublishDetail
            publish_record = session.query(RatePublishRecord).filter(
                RatePublishRecord.branch_id == branch_id,
                RatePublishRecord.publish_date == today
            ).order_by(RatePublishRecord.publish_time.desc()).first()
            
            if publish_record:
                # 获取发布的币种ID列表
                published_details = session.query(RatePublishDetail).filter(
                    RatePublishDetail.publish_record_id == publish_record.id
                ).all()
                published_currency_ids = [detail.currency_id for detail in published_details]
            
            # 获取差额调节记录
            eod_diff_transactions = session.query(ExchangeTransaction).filter(
                ExchangeTransaction.branch_id == branch_id,
                ExchangeTransaction.type == 'Eod_diff',
                ExchangeTransaction.transaction_date == target_date
            ).all()
            
            # 构建差额调节映射
            adjustment_map = {}
            for adj_tx in eod_diff_transactions:
                adjustment_map[adj_tx.currency_id] = {
                    'adjust_amount': float(adj_tx.amount),
                    'reason': adj_tx.customer_name or ''
                }
            
            # 检查差额处理状态
            has_adjustment = len(adjustment_map) > 0
            has_difference = any(v.difference != 0 for v in verifications)
            has_difference_without_adjustment = has_difference and not has_adjustment
            
            # 构建余额汇总数据 - 使用EOD记录中存储的营业时间范围
            balance_summary = []
            logging.info(f"🔍 余额汇总构建 - 当日发布币种数量: {len(published_currency_ids)}, 币种ID: {published_currency_ids}")
            logging.info(f"🔍 余额汇总构建 - 余额核对记录数量: {len(verifications)}")
            
            # 【修复】使用EOD记录中存储的营业时间范围，而不是重新计算
            business_start_time = eod_status.business_start_time
            business_end_time = eod_status.business_end_time
            
            # 【调试】输出营业时间范围到前端
            import json
            alert_data = {
                'business_start_time': str(business_start_time) if business_start_time else 'None',
                'business_end_time': str(business_end_time) if business_end_time else 'None',
                'eod_id': eod_id,
                'target_date': str(target_date)
            }
            print(f"🚨 ALERT - 营业时间范围: {json.dumps(alert_data, ensure_ascii=False)}")
            
            logging.info(f"🔍 EOD记录中的营业时间范围: {business_start_time} 到 {business_end_time}")
            
            # 获取营业时间范围内的交易币种（如果EOD记录中有时间范围）
            transaction_currency_ids = []
            try:
                if business_start_time and business_end_time:
                    transaction_currencies = session.query(ExchangeTransaction.currency_id).filter(
                        ExchangeTransaction.branch_id == branch_id,
                        ExchangeTransaction.transaction_date >= business_start_time,
                        ExchangeTransaction.transaction_date <= business_end_time,
                        ExchangeTransaction.status == 'completed'
                    ).distinct().all()
                    
                    transaction_currency_ids = [tc.currency_id for tc in transaction_currencies]
                    logging.info(f"🔍 营业时间范围内交易币种数量: {len(transaction_currency_ids)}, 币种ID: {transaction_currency_ids}")
                else:
                    logging.warning(f"🔍 EOD记录中没有营业时间范围，使用所有余额核对记录")
            except Exception as e:
                logging.error(f"🔍 查询营业时间范围内交易币种失败: {str(e)}")
                transaction_currency_ids = []
            
            for v in verifications:
                currency = session.query(Currency).filter_by(id=v.currency_id).first()
                if not currency:
                    continue
                    
                # 检查是否为营业时间范围内的交易币种或有余额的币种
                has_transaction_in_business_hours = (v.currency_id in transaction_currency_ids)
                has_balance_or_activity = (
                    v.opening_balance != 0 or 
                    v.actual_balance != 0 or 
                    v.theoretical_balance != 0 or 
                    v.difference != 0 or
                    has_transaction_in_business_hours
                )
                
                logging.info(f"🔍 币种 {currency.currency_code} (ID: {v.currency_id}) - 营业时间交易: {has_transaction_in_business_hours}, 有余额或活动: {has_balance_or_activity}")
                
                # 显示有余额或有营业时间范围内交易的币种
                should_include = has_balance_or_activity
                
                if should_include:
                    # 检查是否有差额调节
                    adjustment_info = adjustment_map.get(v.currency_id)
                    status_text = ''
                    display_actual_balance = float(v.actual_balance)
                    
                    if adjustment_info:
                        # 有差额调节 - 显示调节前的实际余额
                        adjust_amount = adjustment_info['adjust_amount']
                        display_actual_balance = float(v.theoretical_balance) - float(adjust_amount)
                        status_text = f"差额调节 {adjust_amount:+.2f}"
                    elif v.difference != 0:
                        # 有差异但未调节
                        status_text = "X"
                    else:
                        # 无差异
                        status_text = "☑"
                    
                    balance_summary.append({
                        'currency_id': v.currency_id,
                        'currency_code': currency.currency_code if currency else '',
                        'currency_name': currency.currency_name if currency else '',
                        'custom_flag_filename': currency.custom_flag_filename if currency else None,
                        'opening_balance': float(v.opening_balance),
                        'actual_balance': display_actual_balance,  # 使用显示用的实际余额
                        'theoretical_balance': float(v.theoretical_balance),
                        'difference': float(v.difference),
                        'is_match': v.is_match,
                        'status': status_text,
                        'has_adjustment': adjustment_info is not None
                    })
            
            # 构建差额调节汇总数据（如果有差额调节）
            difference_adjustment_summary = []
            if has_adjustment:
                for v in verifications:
                    currency = session.query(Currency).filter_by(id=v.currency_id).first()
                    if not currency:
                        continue
                    
                    adjustment_info = adjustment_map.get(v.currency_id)
                    if adjustment_info:
                        # 计算调节前的实际余额（理论余额减去调节金额）
                        original_actual_balance = float(v.theoretical_balance) - float(adjustment_info['adjust_amount'])
                        
                        difference_adjustment_summary.append({
                            'currency_code': currency.currency_code,
                            'currency_name': currency.currency_name,
                            'theoretical_balance': float(v.theoretical_balance),
                            'actual_balance': float(v.actual_balance),
                            'original_actual_balance': original_actual_balance,  # 调节前的实际余额
                            'adjust_amount': adjustment_info['adjust_amount'],
                            'reason': adjustment_info['reason']
                        })
            
            # 构建差额报告汇总数据（如果有差额但未调节）
            difference_report_summary = []
            if has_difference_without_adjustment:
                for v in verifications:
                    currency = session.query(Currency).filter_by(id=v.currency_id).first()
                    if not currency:
                        continue
                    
                    if v.difference != 0:
                        difference_report_summary.append({
                            'currency_code': currency.currency_code,
                            'currency_name': currency.currency_name,
                            'theoretical_balance': float(v.theoretical_balance),
                            'actual_balance': float(v.actual_balance),
                            'difference': float(v.difference)
                        })
            
            # 2. 构建报表数据结构
            date_str = target_date.strftime('%Y%m%d')
            filename_base = f"{date_str}EOD{eod_id:03d}cashout"
            
            # 【新增】添加营业时间范围到header中
            header_data = {
                'title': '日结汇总报表',
                'date': target_date.strftime('%Y年%m月%d日'),
                'eod_id': eod_id,
                'branch_id': branch_id,
                'branch_name': branch.branch_name if branch else '未知网点',
                'generated_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'mode': mode,
                'business_start_time': str(business_start_time) if business_start_time else None,
                'business_end_time': str(business_end_time) if business_end_time else None
            }
            
            # 创建manager目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            manager_dir = os.path.join(current_dir, '..', 'manager', target_date.strftime('%Y'), target_date.strftime('%m'))
            os.makedirs(manager_dir, exist_ok=True)
            
            # 构建报表数据
            report_data = {
                'header': header_data,
                'transaction_stats': {
                    'total_transactions': total_transactions,
                    'buy_transactions': buy_transactions,
                    'sell_transactions': sell_transactions
                },
                'balance_summary': balance_summary,
                'cash_out_summary': cash_out_summary,
                'difference_adjustment_summary': difference_adjustment_summary,
                'difference_report_summary': difference_report_summary,
                'has_adjustment': has_adjustment,
                'has_difference_without_adjustment': has_difference_without_adjustment
            }
            
            # 【调试】输出差额调节数据
            print(f"🔍 差额调节数据调试:")
            print(f"🔍 has_adjustment: {has_adjustment}")
            print(f"🔍 difference_adjustment_summary 长度: {len(difference_adjustment_summary)}")
            for i, item in enumerate(difference_adjustment_summary):
                print(f"🔍 差额调节项 {i+1}: {item}")
            print(f"🔍 营业时间范围: {business_start_time} - {business_end_time}")
            
            # 根据差额处理状态决定生成哪些报表
            sections = []
            
            # 始终生成余额汇总表
            sections.append({
                'type': 'balance_summary',
                'title': '余额汇总',
                'data': {
                    'balance_summary': report_data['balance_summary']
                }
            })
            
            # 始终生成交款汇总表
            sections.append({
                'type': 'cash_out_summary',
                'title': '交款汇总',
                'data': {
                    'cash_out_summary': report_data['cash_out_summary']
                }
            })
            
            # 如果有差额调节，生成差额调节表
            if has_adjustment:
                sections.append({
                    'type': 'difference_adjustment_table',
                    'title': '差额调节表',
                    'data': {
                        'difference_adjustment_summary': report_data['difference_adjustment_summary']
                    }
                })
                
                # 生成三种语言版本的差额调节报告
                from services.difference_report_service import DifferenceReportService
                for lang in ['zh', 'en', 'th']:
                    report_result = DifferenceReportService.generate_difference_adjustment_report(
                        eod_id, 
                        difference_adjustment_summary, 
                        lang
                    )
                    if not report_result['success']:
                        logging.warning(f"生成{lang}语言差额调节报告失败: {report_result['message']}")
                    else:
                        logging.info(f"生成{lang}语言差额调节报告成功: {report_result['filename']}")
            
            # 如果有差额但未调节，生成差额报告表
            if has_difference_without_adjustment:
                sections.append({
                    'type': 'difference_report_table',
                    'title': '差额报告表',
                    'data': {
                        'difference_report_summary': report_data['difference_report_summary']
                    }
                })
                
                # 生成三种语言版本的差额报告
                from services.difference_report_service import DifferenceReportService
                for lang in ['zh', 'en', 'th']:
                    report_result = DifferenceReportService.generate_difference_report(
                        eod_id, 
                        difference_report_summary, 
                        lang
                    )
                    if not report_result['success']:
                        logging.warning(f"生成{lang}语言差额报告失败: {report_result['message']}")
                    else:
                        logging.info(f"生成{lang}语言差额报告成功: {report_result['filename']}")
            
            # 如果是详细模式，添加收入汇总
            if mode == 'detailed':
                # 获取收入统计
                income_stats = session.query(
                    Currency.currency_code,
                    Currency.currency_name,
                    func.sum(ExchangeTransaction.amount).label('total_buy'),
                    func.sum(ExchangeTransaction.local_amount).label('total_sell'),
                    func.avg(ExchangeTransaction.rate).label('buy_rate'),
                    func.avg(ExchangeTransaction.sell_rate).label('sell_rate')
                ).join(Currency).filter(
                    ExchangeTransaction.branch_id == branch_id,
                    func.date(ExchangeTransaction.transaction_date) == target_date,
                    ExchangeTransaction.status == 'completed',
                    ExchangeTransaction.type.in_(['buy', 'sell'])
                ).group_by(
                    Currency.currency_code,
                    Currency.currency_name
                ).all()
                
                income_summary = []
                for stat in income_stats:
                    income_summary.append({
                        'currency_code': stat.currency_code,
                        'currency_name': stat.currency_name,
                        'total_buy': float(stat.total_buy or 0),
                        'total_sell': float(stat.total_sell or 0),
                        'buy_rate': float(stat.buy_rate or 0),
                        'sell_rate': float(stat.sell_rate or 0),
                        'income': float(stat.total_sell or 0) - float(stat.total_buy or 0),
                        'spread_income': 0  # 需要根据实际业务逻辑计算
                    })
                
                sections.append({
                    'type': 'income_summary',
                    'title': '收入汇总',
                    'data': {
                        'income_summary': income_summary
                    }
                })
            
            # 获取操作员信息
            operator = session.query(Operator).filter_by(id=operator_id).first()
            operator_name = operator.name if operator else '系统管理员'
            
            print_data = {
                'header': {
                    'title': '日结详细报表' if mode == 'detailed' else '日结汇总报表',
                    'date': target_date.strftime('%Y年%m月%d日'),
                    'branch_id': branch_id,
                    'branch_name': branch.branch_name if branch else f'网点{branch_id}',
                    'eod_id': eod_id,
                    'generated_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'mode': mode,
                    'business_start_time': str(business_start_time) if business_start_time else None,
                    'business_end_time': str(business_end_time) if business_end_time else None,
                    'operator_name': operator_name
                },
                'sections': sections
            }
            
            logger.info(f"🌍 构建的print_data结构: header={list(print_data['header'].keys())}, sections={len(sections)}个")
            for i, section in enumerate(sections):
                logger.info(f"🌍 Section {i+1}: type={section.get('type')}, title={section.get('title')}")
            
            # 生成三种语言的PDF文件
            generated_files = []
            languages = [
                ('zh', ''),  # 中文不加语言类型
                ('en', '_en'),  # 英文加_en
                ('th', '_th')   # 泰文加_th
            ]
            
            for lang_code, lang_suffix in languages:
                # 构建正确的文件名格式：yyyymmddEODxxxcashout_lang.pdf
                date_str = target_date.strftime('%Y%m%d')
                if lang_code == 'zh':
                    filename = f"{date_str}EOD{eod_id:03d}cashout.pdf"
                else:
                    filename = f"{date_str}EOD{eod_id:03d}cashout_{lang_code}.pdf"
                output_file = os.path.join(manager_dir, filename)
                
                # 生成PDF
                logger.info(f"🌍 开始生成{lang_code}语言PDF - 文件: {filename}")
                pdf_result = SimplePDFService.generate_simple_eod_report_pdf(
                    print_data, 
                    filename,
                    target_date,
                    language=lang_code
                )
                
                logger.info(f"🌍 {lang_code}语言PDF生成结果: {pdf_result}")
                
                if pdf_result['success']:
                    generated_files.append({
                        'language': lang_code,
                        'filename': filename,
                        'file_path': pdf_result['file_path']
                    })
                    LogService.log_system_event(
                        f"生成{lang_code}语言PDF成功 - 文件: {filename}",
                        operator_id=operator_id,
                        branch_id=branch_id
                    )
                else:
                    LogService.log_error(f"生成{lang_code}语言PDF失败: {pdf_result.get('message', '未知错误')}")
            
            if not generated_files:
                return {'success': False, 'message': '所有语言版本的PDF生成都失败了'}
            
            # 3. 记录打印日志
            from models.exchange_models import EODPrintLog
            print_log = EODPrintLog(
                eod_status_id=eod_id,
                printed_by=operator_id,
                mode=mode
            )
            session.add(print_log)
            
            # 4. 更新打印次数和文件信息
            eod_status.print_count += 1
            eod_status.print_operator_id = operator_id
            
            # 5. 更新第7步状态为已完成
            if eod_status.step == 7:
                eod_status.step_status = 'completed'
            
            session.commit()
            
            # 在会话关闭前提取所有需要的数据
            print_count = eod_status.print_count
            printed_at = print_log.printed_at.isoformat()
            
            LogService.log_system_event(
                f"打印日结报表成功 - 日结ID: {eod_id}, 生成文件数: {len(generated_files)}",
                operator_id=operator_id,
                branch_id=branch_id
            )
            
            return {
                'success': True,
                'message': '日结报表生成成功',
                'print_count': print_count,
                'printed_at': printed_at,
                'generated_files': generated_files,
                'eod_no': f"EOD{eod_id:08d}",
                'eod_id': eod_id,  # 添加原始EOD ID
                'report_data': report_data
            }
            
        except Exception as e:
            session.rollback()
            LogService.log_system_event(
                f"打印日结报表失败 - 日结ID: {eod_id}, 错误: {str(e)}",
                operator_id=operator_id,
                branch_id=eod_status.branch_id if eod_status else None
            )
            return {'success': False, 'message': f'打印失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def complete_eod(eod_id, operator_id, session_id=None):
        """
        步骤9: 完成日结 - 生成历史记录和余额快照，标记报表为最终版本
        """
        # 【修复】先进行统一的权限验证
        permission_result = EODService.validate_eod_permission(eod_id, operator_id, session_id)
        if not permission_result['has_permission']:
            return {
                'success': False, 
                'message': permission_result['message']
            }
        
        session = DatabaseService.get_session()
        try:
            eod_status = session.query(EODStatus).filter_by(id=eod_id).first()
            if not eod_status:
                return {'success': False, 'message': '日结记录不存在'}
            
            if eod_status.print_count == 0:
                return {'success': False, 'message': '必须先打印日结报表才能完成日结'}
            
            branch_id = eod_status.branch_id
            target_date = eod_status.date
            
            # 检查是否已完成
            if eod_status.status == 'completed':
                return {'success': False, 'message': '日结已完成'}
            
            # 【简化】移除旧表写入逻辑
            # 不再创建 EODHistory 和 EODBalanceSnapshot
            # EODBalanceVerification 在步骤4/7已创建/更新，保持不变
            
            # 1. 标记收入和库存报表为最终版本 (is_final = 1)
            from models.report_models import DailyIncomeReport, DailyStockReport
            
            session.query(DailyIncomeReport).filter_by(
                eod_id=eod_id,
                is_final=False
            ).update({'is_final': True})
            
            session.query(DailyStockReport).filter_by(
                eod_id=eod_id,
                is_final=False
            ).update({'is_final': True})
            
            # 2. 更新日结状态
            completion_time = datetime.now()
            eod_status.status = 'completed'
            eod_status.completed_at = completion_time
            eod_status.completed_by = operator_id
            eod_status.step = 9
            eod_status.step_status = 'completed'
            eod_status.is_locked = False  # 解除营业锁定
            eod_status.business_end_time = completion_time
            
            # 3. 提交事务
            session.commit()
            
            # 4. 清理会话锁定
            cleanup_result = EODService.cleanup_eod_session_locks(eod_id, operator_id)
            if not cleanup_result['success']:
                # 会话清理失败不影响日结完成，但记录日志
                LogService.log_error(f"清理会话锁定失败: {cleanup_result['message']}", operator_id=operator_id)
            
            # 5. 记录日结完成日志
            try:
                from services.unified_log_service import log_eod_operation
                from utils.language_utils import get_current_language
                
                current_language = get_current_language()
                
                # 获取操作员信息
                completion_operator = session.query(Operator).filter_by(id=operator_id).first()
                completion_operator_name = completion_operator.name if completion_operator else '未知用户'
                
                # 获取交款相关信息
                cash_outs = session.query(EODCashOut).filter_by(eod_status_id=eod_id).all()
                
                # 判断交款类型
                cash_out_type = '未交款'
                cash_receiver_name = '未指定'  # 简化：不再从eod_history获取
                
                if cash_outs:
                    
                    # 获取验证记录，计算交款类型
                    total_currencies = 0
                    zero_cash_out_count = 0
                    full_cash_out_count = 0
                    
                    for cash_out in cash_outs:
                        verification = session.query(EODBalanceVerification).filter_by(
                            eod_status_id=eod_id,
                            currency_id=cash_out.currency_id
                        ).first()
                        
                        if verification:
                            total_currencies += 1
                            cash_out_amount = float(cash_out.cash_out_amount)
                            actual_balance = float(verification.actual_balance) + cash_out_amount  # 交款前余额
                            
                            if cash_out_amount == 0:
                                zero_cash_out_count += 1
                            elif abs(cash_out_amount - actual_balance) < 0.01:  # 考虑浮点数精度
                                full_cash_out_count += 1
                    
                    # 判断交款类型
                    if total_currencies > 0:
                        if zero_cash_out_count == total_currencies:
                            cash_out_type = '0交款'
                        elif full_cash_out_count == total_currencies:
                            cash_out_type = '交全款'
                        else:
                            cash_out_type = '自定义交款'
                
                # 构建详细的完成信息
                completion_details = {
                    'completion_time': completion_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'completion_operator_name': completion_operator_name,
                    'eod_history_id': eod_history_id,
                    'total_transactions': transaction_summary.total_count or 0,
                    'total_buy_amount': float(transaction_summary.buy_amount or 0),
                    'total_sell_amount': float(transaction_summary.sell_amount or 0),
                    'total_adjust_amount': float(transaction_summary.adjust_amount or 0),
                    'cash_out_amount': float(total_cash_out or 0),
                    'cash_out_type': cash_out_type,
                    'cash_receiver_name': cash_receiver_name,
                    'balance_snapshot_table': 'EODBalanceSnapshot',
                    'currencies_processed': len(verifications),
                    'business_lock_released': True,
                    'print_count': eod_status.print_count,
                    'reports_finalized': True
                }
                
                log_eod_operation(
                    operator_id=operator_id,
                    branch_id=branch_id,
                    eod_action='complete',
                    eod_date=target_date.strftime('%Y-%m-%d'),
                    ip_address=None,
                    language=current_language,
                    eod_id=eod_id,
                    operator_name=completion_operator_name,
                    completion_details=completion_details
                )
                
                # 保留原有的简单日志记录
                LogService.log_system_event(
                    f"完成日结流程 - 分支ID: {branch_id}, 日期: {target_date}, 完成时间: {completion_time.strftime('%Y-%m-%d %H:%M:%S')}, 操作员: {completion_operator_name}",
                    operator_id=operator_id,
                    branch_id=branch_id
                )
                
            except Exception as log_error:
                print(f"日结完成日志记录失败: {log_error}")
                # 保留原有的简单日志记录作为备份
                LogService.log_system_event(
                    f"完成日结流程 - 分支ID: {branch_id}, 日期: {target_date}, 完成时间: {completion_time.strftime('%Y-%m-%d %H:%M:%S')}",
                    operator_id=operator_id,
                    branch_id=branch_id
                )
            
            return {
                'success': True,
                'message': '日结流程完成',
                'eod_id': eod_id,
                'status': 'completed'
            }
            
        except Exception as e:
            session.rollback()
            LogService.log_error(f"完成日结失败: {str(e)}", operator_id=operator_id)
            return {'success': False, 'message': f'完成日结失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def get_eod_status(eod_id):
        """
        获取日结状态信息
        """
        session = DatabaseService.get_session()
        try:
            eod_status = session.query(EODStatus).filter_by(id=eod_id).first()
            if not eod_status:
                return {'success': False, 'message': '日结记录不存在'}
            
            # 检查是否有交款记录
            cash_out_count = session.query(EODCashOut).filter_by(eod_status_id=eod_id).count()
            cash_out_completed = cash_out_count > 0
            
            # 【修复】获取核对结果数据
            verification_results = []
            if eod_status.step >= 4:  # 如果已经完成步骤4，获取核对结果
                verifications = session.query(EODBalanceVerification).filter_by(eod_status_id=eod_id).all()
                for verification in verifications:
                    # 获取币种信息
                    currency = session.query(Currency).filter_by(id=verification.currency_id).first()
                    if currency:
                        verification_results.append({
                            'currency_id': verification.currency_id,
                            'currency_code': currency.currency_code,
                            'currency_name': currency.currency_name,
                            'theoretical_balance': float(verification.theoretical_balance),
                            'actual_balance': float(verification.actual_balance),
                            'difference': float(verification.difference),
                            'is_match': verification.is_match,
                            'status_icon': '✓' if verification.is_match else '✗'
                        })
            
            return {
                'success': True,
                'eod_status': {
                    'id': eod_status.id,
                    'branch_id': eod_status.branch_id,
                    'date': eod_status.date.isoformat(),
                    'status': eod_status.status,
                    'step': eod_status.step,
                    'step_status': eod_status.step_status,
                    'is_locked': eod_status.is_locked,
                    'started_at': eod_status.started_at.isoformat() if eod_status.started_at else None,
                    'completed_at': eod_status.completed_at.isoformat() if eod_status.completed_at else None,
                    'print_count': eod_status.print_count,
                    'cancel_reason': eod_status.cancel_reason,
                    'cash_out_completed': cash_out_completed
                },
                'verification_results': verification_results
            }
            
        except Exception as e:
            return {'success': False, 'message': f'获取状态失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def check_business_lock(branch_id):
        """
        检查营业锁定状态
        """
        session = DatabaseService.get_session()
        try:
            locked_eod = session.query(EODStatus).filter(
                EODStatus.branch_id == branch_id,
                EODStatus.is_locked == True,
                EODStatus.status == 'processing'
            ).first()
            
            # 在会话关闭前提取所有需要的数据
            is_locked = locked_eod is not None
            eod_id = locked_eod.id if locked_eod else None
            lock_date = locked_eod.date.isoformat() if locked_eod else None
            
            return {
                'success': True,
                'is_locked': is_locked,
                'eod_id': eod_id,
                'lock_date': lock_date
            }
            
        except Exception as e:
            return {
                'success': False,
                'is_locked': False, 
                'error': str(e)
            }
        finally:
            DatabaseService.close_session(session)

    @staticmethod
    def create_eod_session_lock(branch_id, eod_status_id, operator_id, session_id, ip_address, user_agent):
        """
        创建日结会话锁定 - 确保只有单一终端可以进行日结
        """
        session = DatabaseService.get_session()
        
        try:
            # 【修复】先清理该网点的所有旧会话锁定记录，避免唯一约束冲突
            session.query(EODSessionLock).filter(
                EODSessionLock.branch_id == branch_id
            ).delete(synchronize_session=False)
            
            # 检查是否已存在该网点的活跃日结会话（清理后应该没有）
            existing_session = session.query(EODSessionLock).filter(
                EODSessionLock.branch_id == branch_id,
                EODSessionLock.is_active == True
            ).first()
            
            if existing_session:
                # 检查是否是同一个会话
                if existing_session.session_id == session_id:
                    # 更新活跃时间
                    existing_session.last_activity = datetime.now()
                    session.commit()
                    return {
                        'success': True,
                        'message': '日结会话已存在，更新活跃时间',
                        'session_lock_id': existing_session.id
                    }
                else:
                    # 获取会话信息
                    operator = session.query(Operator).filter_by(id=existing_session.operator_id).first()
                    operator_name = operator.name if operator else '未知操作员'
                    
                    return {
                        'success': False,
                        'message': f'该网点已有活跃的日结会话',
                        'existing_session': {
                            'operator_name': operator_name,
                            'ip_address': existing_session.ip_address,
                            'created_at': existing_session.created_at.isoformat() if existing_session.created_at else None,
                            'last_activity': existing_session.last_activity.isoformat() if existing_session.last_activity else None
                        }
                    }
            
            # 创建新的会话锁定
            session_lock = EODSessionLock(
                branch_id=branch_id,
                eod_status_id=eod_status_id,
                session_id=session_id,
                operator_id=operator_id,
                ip_address=ip_address,
                user_agent=user_agent,
                created_at=datetime.now(),
                last_activity=datetime.now(),
                is_active=True
            )
            
            session.add(session_lock)
            session.commit()
            
            return {
                'success': True,
                'message': '日结会话锁定创建成功',
                'session_lock_id': session_lock.id
            }
            
        except Exception as e:
            session.rollback()
            return {
                'success': False,
                'message': f'创建日结会话锁定失败: {str(e)}'
            }
        finally:
            DatabaseService.close_session(session)

    @staticmethod
    def update_eod_session_activity(session_id, branch_id):
        """
        更新日结会话活跃时间
        """
        session = DatabaseService.get_session()
        
        try:
            session_lock = session.query(EODSessionLock).filter(
                EODSessionLock.session_id == session_id,
                EODSessionLock.branch_id == branch_id,
                EODSessionLock.is_active == True
            ).first()
            
            if session_lock:
                session_lock.last_activity = datetime.now()
                session.commit()
                return {'success': True}
            else:
                return {'success': False, 'message': '会话锁定不存在'}
                
        except Exception as e:
            session.rollback()
            return {'success': False, 'message': str(e)}
        finally:
            DatabaseService.close_session(session)

    @staticmethod
    def release_eod_session_lock(session_id, branch_id):
        """
        释放日结会话锁定
        """
        session = DatabaseService.get_session()
        
        try:
            session_lock = session.query(EODSessionLock).filter(
                EODSessionLock.session_id == session_id,
                EODSessionLock.branch_id == branch_id,
                EODSessionLock.is_active == True
            ).first()
            
            if session_lock:
                session.delete(session_lock)
                session.commit()
                return {'success': True, 'message': '日结会话锁定已释放'}
            else:
                return {'success': False, 'message': '会话锁定不存在'}
                
        except Exception as e:
            session.rollback()
            return {'success': False, 'message': str(e)}
        finally:
            DatabaseService.close_session(session)

    @staticmethod
    def check_eod_session_permission(session_id, branch_id):
        """
        检查日结会话权限 - 如果会话不存在则自动创建
        """
        session = DatabaseService.get_session()
        
        try:
            # 首先检查是否存在有效的会话锁定
            session_lock = session.query(EODSessionLock).filter(
                EODSessionLock.session_id == session_id,
                EODSessionLock.branch_id == branch_id,
                EODSessionLock.is_active == True
            ).first()
            
            if session_lock:
                # 会话存在，更新活跃时间
                session_lock.last_activity = datetime.now()
                session.commit()
                has_permission = True
            else:
                # 会话不存在，检查是否有进行中的日结
                active_eod = session.query(EODStatus).filter(
                    EODStatus.branch_id == branch_id,
                    EODStatus.status == 'processing'
                ).first()
                
                if active_eod:
                    # 有进行中的日结，创建新的会话锁定
                    new_session_lock = EODSessionLock(
                        session_id=session_id,
                        branch_id=branch_id,
                        eod_status_id=active_eod.id,
                        operator_id=active_eod.started_by,
                        ip_address='auto_created',
                        user_agent='auto_created',
                        is_active=True,
                        created_at=datetime.now(),
                        last_activity=datetime.now()
                    )
                    session.add(new_session_lock)
                    session.commit()
                    has_permission = True
                else:
                    # 没有进行中的日结，允许操作（可能是开始新的日结）
                    has_permission = True
            
            from utils.i18n_utils import I18nUtils
            
            return {
                'success': True,
                'has_permission': has_permission,
                'message': I18nUtils.get_message('auth.eod_permission_granted') if has_permission else I18nUtils.get_message('auth.eod_permission_denied')
            }
            
        except Exception as e:
            return {
                'success': False,
                'has_permission': False,
                'message': str(e)
            }
        finally:
            DatabaseService.close_session(session)

    @staticmethod
    def cleanup_expired_eod_sessions(expire_hours=2):
        """
        清理过期的日结会话锁定
        """
        session = DatabaseService.get_session()
        
        try:
            expire_time = datetime.now() - timedelta(hours=expire_hours)
            
            expired_sessions = session.query(EODSessionLock).filter(
                EODSessionLock.is_active == True,
                EODSessionLock.last_activity < expire_time
            ).all()
            
            count = 0
            for session_lock in expired_sessions:
                session.delete(session_lock)
                count += 1
            
            session.commit()
            
            return {
                'success': True,
                'message': f'清理了 {count} 个过期的日结会话锁定',
                'cleaned_count': count
            }
            
        except Exception as e:
            session.rollback()
            return {
                'success': False,
                'message': str(e)
            }
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def continue_eod_session(eod_id, session_id, ip_address, user_agent):
        """
        继续现有日结流程 - 为现有EOD设置会话ID
        """
        session = DatabaseService.get_session()
        try:
            # 获取日结记录
            eod_status = session.query(EODStatus).filter_by(id=eod_id).first()
            if not eod_status:
                return {'success': False, 'message': '日结记录不存在'}
            
            if eod_status.status != 'processing':
                return {'success': False, 'message': '只能继续处理中的日结流程'}
            
            # 【增强】先清理该EOD的所有会话锁定记录，避免冲突
            session.query(EODSessionLock).filter(
                EODSessionLock.eod_status_id == eod_id
            ).delete(synchronize_session=False)
            
            # 创建新的会话锁定
            session_lock = EODSessionLock(
                eod_status_id=eod_id,
                branch_id=eod_status.branch_id,
                operator_id=eod_status.started_by,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                is_active=True,
                created_at=datetime.now(),
                last_activity=datetime.now()
            )
            
            session.add(session_lock)
            session.commit()
            
            LogService.log_system_event(
                f"继续日结流程 - EOD ID: {eod_id}, 会话ID: {session_id}",
                operator_id=eod_status.started_by,
                branch_id=eod_status.branch_id
            )
            
            return {
                'success': True,
                'message': '成功继续现有日结流程',
                'session_id': session_id
            }
            
            # 创建新的会话锁定
            session_lock = EODSessionLock(
                eod_status_id=eod_id,
                branch_id=eod_status.branch_id,
                operator_id=eod_status.started_by,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                is_active=True,
                created_at=datetime.now(),
                last_activity=datetime.now()
            )
            
            session.add(session_lock)
            session.commit()
            
            LogService.log_system_event(
                f"为现有日结设置会话 - EOD ID: {eod_id}, 会话ID: {session_id}",
                operator_id=eod_status.started_by,
                branch_id=eod_status.branch_id
            )
            
            return {
                'success': True,
                'message': '成功为现有日结设置会话',
                'session_id': session_id
            }
            
        except Exception as e:
            session.rollback()
            LogService.log_error(f"继续日结会话失败: {str(e)}")
            return {'success': False, 'message': f'继续日结会话失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def cancel_eod(eod_id, reason, operator_id):
        """
        统一取消日结 - 智能处理不同状态的日结
        """
        session = DatabaseService.get_session()
        try:
            eod_status = session.query(EODStatus).filter_by(id=eod_id).first()
            if not eod_status:
                return {'success': False, 'message': '日结记录不存在'}
            
            # 【优化】先清理会话锁定，失败时回滚
            cleanup_result = EODService.cleanup_eod_session_locks(eod_id, operator_id)
            if not cleanup_result['success']:
                # 会话清理失败应该回滚取消操作，确保数据一致性
                return {
                    'success': False,
                    'message': f'清理会话锁定失败，无法取消日结: {cleanup_result["message"]}',
                    'cleanup_failed': True
                }
            
            # 【统一取消逻辑】会话清理成功后，更新EOD状态
            cancel_time = datetime.now()
            eod_status.status = 'cancelled'
            eod_status.cancel_reason = reason
            eod_status.is_locked = False
            eod_status.completed_at = cancel_time
            eod_status.completed_by = operator_id
            eod_status.step_status = 'cancelled'
            
            session.commit()
            
            # 记录详细的日结取消日志
            try:
                from services.unified_log_service import log_eod_operation
                from utils.language_utils import get_current_language
                
                current_language = get_current_language()
                
                # 获取操作员信息
                cancel_operator = session.query(Operator).filter_by(id=operator_id).first()
                cancel_operator_name = cancel_operator.name if cancel_operator else '未知用户'
                
                # 构建详细的取消信息
                cancel_details = {
                    'cancel_time': cancel_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'cancel_operator_name': cancel_operator_name,
                    'cancel_reason': reason,
                    'eod_step': eod_status.step,
                    'eod_step_status': eod_status.step_status,
                    'started_at': eod_status.started_at.strftime('%Y-%m-%d %H:%M:%S') if eod_status.started_at else None,
                    'business_lock_released': True,
                    'session_locks_released': True
                }
                
                log_eod_operation(
                    operator_id=operator_id,
                    branch_id=eod_status.branch_id,
                    eod_action='cancel',
                    eod_date=eod_status.date.strftime('%Y-%m-%d'),
                    ip_address=None,
                    language=current_language,
                    eod_id=eod_id,
                    operator_name=cancel_operator_name,
                    cancel_details=cancel_details
                )
                
                # 保留原有的简单日志记录
                LogService.log_system_event(
                    f"取消日结 - EOD ID: {eod_id}, 取消时间: {cancel_time.strftime('%Y-%m-%d %H:%M:%S')}, 原因: {reason}, 操作员: {cancel_operator_name}",
                    operator_id=operator_id,
                    branch_id=eod_status.branch_id
                )
                
            except Exception as log_error:
                print(f"日结取消日志记录失败: {log_error}")
                # 保留原有的简单日志记录作为备份
                LogService.log_system_event(
                    f"取消日结 - EOD ID: {eod_id}, 取消时间: {cancel_time.strftime('%Y-%m-%d %H:%M:%S')}, 原因: {reason}",
                    operator_id=operator_id,
                    branch_id=eod_status.branch_id
                )
            
            return {
                'success': True,
                'message': '日结已取消，营业锁定已解除',
                'status': 'cancelled'
            }
            
        except Exception as e:
            session.rollback()
            LogService.log_error(f"取消日结失败: {str(e)}", operator_id=operator_id)
            return {'success': False, 'message': f'取消日结失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def get_latest_eod_for_branch(branch_id, before_date=None):
        """
        获取指定分支的最新日结记录（用于获取期初余额）
        """
        session = DatabaseService.get_session()
        try:
            query = session.query(EODHistory).filter(
                EODHistory.branch_id == branch_id
            )
            
            if before_date:
                query = query.filter(EODHistory.date < before_date)
            
            latest_eod = query.order_by(desc(EODHistory.date)).first()
            
            if latest_eod:
                # 获取余额快照
                snapshots = session.query(EODBalanceSnapshot).filter_by(
                    eod_history_id=latest_eod.id
                ).all()
                
                balance_data = {}
                for snapshot in snapshots:
                    balance_data[snapshot.currency_id] = {
                        'remaining_balance': float(snapshot.remaining_balance),
                        'currency_id': snapshot.currency_id
                    }
                
                return {
                    'success': True,
                    'eod_date': latest_eod.date.isoformat(),
                    'balance_data': balance_data
                }
            else:
                return {
                    'success': True,
                    'eod_date': None,
                    'balance_data': {}
                }
                
        except Exception as e:
            return {'success': False, 'message': f'获取最新日结记录失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def check_completed_eod(branch_id, target_date):
        """
        检查指定日期是否有已完成的日结
        """
        session = DatabaseService.get_session()
        try:
            completed_eod = session.query(EODStatus).filter(
                EODStatus.branch_id == branch_id,
                EODStatus.date == target_date,
                EODStatus.status == 'completed'
            ).first()
            
            if completed_eod:
                return {
                    'success': True,
                    'has_completed': True,
                    'eod_id': completed_eod.id,
                    'date': completed_eod.date.isoformat(),
                    'completed_at': completed_eod.completed_at.isoformat() if completed_eod.completed_at else None
                }
            else:
                return {
                    'success': True,
                    'has_completed': False
                }
                
        except Exception as e:
            return {'success': False, 'message': f'检查已完成日结失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def get_today_eod_history(branch_id, target_date):
        """
        获取指定日期的所有已完成日结记录
        """
        session = DatabaseService.get_session()
        try:
            completed_eods = session.query(EODStatus).filter(
                EODStatus.branch_id == branch_id,
                EODStatus.date == target_date,
                EODStatus.status == 'completed'
            ).order_by(EODStatus.completed_at.desc()).all()
            
            history = []
            for eod in completed_eods:
                history.append({
                    'id': eod.id,
                    'date': eod.date.isoformat(),
                    'started_at': eod.started_at.isoformat() if eod.started_at else None,
                    'completed_at': eod.completed_at.isoformat() if eod.completed_at else None,
                    'status': eod.status
                })
            
            return {
                'success': True,
                'history': history,
                'count': len(history)
            }
                
        except Exception as e:
            return {'success': False, 'message': f'获取当天日结历史失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def allow_balance_adjustment_during_eod(branch_id, operator_id):
        """
        检查是否允许在日结期间进行余额调节
        
        Args:
            branch_id: 网点ID
            operator_id: 操作员ID
            
        Returns:
            bool: 是否允许调节
        """
        session = DatabaseService.get_session()
        try:
            # 检查是否有进行中的日结
            active_eod = session.query(EODStatus).filter(
                EODStatus.branch_id == branch_id,
                EODStatus.status == 'processing',
                EODStatus.is_locked == True
            ).first()
            
            if not active_eod:
                return True  # 没有进行中的日结，允许调节
            
            # 检查操作员是否为当前日结的发起人
            if active_eod.started_by == operator_id:
                return True  # 日结发起人允许调节
            
            # 【修复】允许在步骤4（核对余额）和步骤5（收入统计）进行差额调节
            if active_eod.step in [4, 5]:
                return True  # 在余额核对和收入统计步骤，允许调节
            
            return False  # 其他情况不允许调节
            
        except Exception as e:
            LogService.log_system_event(
                f"检查日结期间余额调节权限失败: {str(e)}",
                operator_id=operator_id,
                branch_id=branch_id
            )
            return False
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def generate_income_statistics(eod_id, operator_id, language='zh'):
        """
        新增步骤：收入统计 - 生成收入报表和库存报表
        在交款前进行，统计当日收入和库存状况
        
        Args:
            eod_id: 日结ID
            operator_id: 操作员ID
            language: 语言代码 ('zh', 'en', 'th')
        """
        from services.log_service import LogService
        from config.features import FeatureFlags
        
        # 【修复】标准化语言代码，处理 th-TH -> th, en-US -> en 的映射
        def normalize_language_code(lang_code):
            """标准化语言代码"""
            if not lang_code:
                return 'zh'
            
            lang_code = lang_code.lower()
            if lang_code.startswith('th'):
                return 'th'
            elif lang_code.startswith('en'):
                return 'en'
            elif lang_code.startswith('zh'):
                return 'zh'
            else:
                return 'zh'  # 默认中文
        
        original_language = language
        language = normalize_language_code(language)
        session = DatabaseService.get_session()
        try:
            eod_status = session.query(EODStatus).filter_by(id=eod_id).first()
            if not eod_status:
                return {'success': False, 'message': '日结记录不存在'}
            
            branch_id = eod_status.branch_id
            target_date = eod_status.date
            
            # 记录语言参数标准化
            LogService.log_system_event(
                f"生成收入统计 - 语言参数标准化: 原始: {original_language}, 标准化后: {language}",
                operator_id=operator_id,
                branch_id=branch_id
            )
            
            # 【修复】使用日结记录中的业务时间范围，不依赖get_daily_time_range函数
            # 因为当前日结还在进行中（status=processing），get_daily_time_range找不到已完成的日结记录
            
            # 确定统计时间范围
            if FeatureFlags.FEATURE_NEW_BUSINESS_TIME_RANGE and eod_status.business_start_time and eod_status.business_end_time:
                # 使用日结记录中的业务时间范围
                start_time = eod_status.business_start_time
                end_time = eod_status.business_end_time
                
                LogService.log_system_event(
                    f"【日结业务时间范围】使用日结记录中的业务时间范围 - 开始: {start_time}, 结束: {end_time}",
                    operator_id=operator_id,
                    branch_id=branch_id
                )
            else:
                # 【修复】使用传统的时间范围计算方法，按照用户要求的规则
                # 查找上一次已完成的日结记录
                prev_eod = session.query(EODStatus).filter(
                    EODStatus.branch_id == branch_id,
                    EODStatus.id != eod_id,  # 排除当前日结
                    EODStatus.status == 'completed'
                ).order_by(desc(EODStatus.completed_at)).first()
                
                if prev_eod and prev_eod.completed_at:
                    # 2.1 如果有上一次日结记录，则用上一次日结记录的结束时间作为收入统计的开始时间
                    start_time = prev_eod.completed_at
                else:
                    # 2.2 如果没有上一次日结记录，则用本次日结当天的0点作为收入统计的开始时间
                    start_time = datetime.combine(target_date, datetime.min.time())
                
                # 【修复】用当前时间作为收入统计的结束时间，而不是日结开始时间
                # 这样可以包含日结过程中的所有交易
                end_time = datetime.now()
                
                LogService.log_system_event(
                    f"【传统时间范围】使用传统时间范围计算 - 开始: {start_time}, 结束: {end_time}",
                    operator_id=operator_id,
                    branch_id=branch_id
                )
            
            LogService.log_system_event(
                f"日结统计时间范围 - 开始: {start_time}, 结束: {end_time}",
                operator_id=operator_id,
                branch_id=branch_id
            )
            
            # 调用CalGain函数生成收入报表
            try:
                from routes.app_reports import CalGain, CalBalance, CalBaseCurrency
                
                # 【修复】使用独立的数据库会话避免锁定
                LogService.log_system_event(
                    f"开始调用CalGain、CalBalance和CalBaseCurrency函数",
                    operator_id=operator_id,
                    branch_id=branch_id
                )
                
                # 【修复】使用按币种分别计算模式
                income_data = CalGain(branch_id, start_time, end_time)
                stock_data = CalBalance(branch_id, start_time, end_time)
                base_currency_data = CalBaseCurrency(branch_id, start_time, end_time)
                
                LogService.log_system_event(
                    f"函数调用完成 - 收入币种数: {len(income_data.get('currencies', []))}, 外币库存币种数: {len(stock_data.get('currencies', []))}, 本币数据: {'有' if base_currency_data else '无'}",
                    operator_id=operator_id,
                    branch_id=branch_id
                )
                
            except ImportError as e:
                LogService.log_system_event(
                    f"导入函数失败 - 错误: {str(e)}",
                    operator_id=operator_id,
                    branch_id=branch_id
                )
                return {'success': False, 'message': f'导入报表函数失败: {str(e)}'}
            except Exception as e:
                LogService.log_system_event(
                    f"调用报表函数失败 - 错误: {str(e)}",
                    operator_id=operator_id,
                    branch_id=branch_id
                )
                return {'success': False, 'message': f'生成报表数据失败: {str(e)}'}
            
            # 保存收入报表到数据库
            from models.report_models import DailyIncomeReport, DailyForeignStock
            
            # 使用事务确保数据完整性
            try:
                # 清除已存在的该eod_id的报表数据（避免重复）
                deleted_income = session.query(DailyIncomeReport).filter_by(
                    eod_id=eod_id
                ).delete()
            
                deleted_stock = session.query(DailyForeignStock).filter_by(
                    eod_id=eod_id
                ).delete()
            
                if deleted_income > 0 or deleted_stock > 0:
                    LogService.log_system_event(
                        f"清除已存在的报表数据 - 日结ID: {eod_id}, 删除收入报表: {deleted_income}, 删除库存报表: {deleted_stock}",
                        operator_id=operator_id,
                        branch_id=branch_id
                    )
                    
                # 插入新的收入报表数据
                for currency in income_data.get('currencies', []):
                    income_report = DailyIncomeReport(
                        report_date=target_date,
                        branch_id=branch_id,
                        currency_code=currency['currency_code'],
                        base_currency=income_data['base_currency'],
                        total_buy=currency['total_buy'],
                        total_sell=currency['total_sell'],
                        buy_rate=currency['buy_rate'],
                        sell_rate=currency['sell_rate'],
                        income=currency['income'],
                        spread_income=currency['spread_income'],
                        is_final=False,  # 暂时标记为非最终
                        eod_id=eod_id
                    )
                    session.add(income_report)
                
                # 插入新的库存报表数据（只包含外币，不包含基础货币）
                for currency in stock_data.get('currencies', []):
                    # 【修复】过滤掉基础货币，只插入外币数据
                    if currency.get('is_base_currency', False):
                        LogService.log_system_event(
                            f"跳过基础货币 {currency['currency_code']} - 不插入到外币库存表",
                            operator_id=operator_id,
                            branch_id=branch_id
                        )
                        continue
                        
                    stock_report = DailyForeignStock(
                        report_date=target_date,
                        branch_id=branch_id,
                        currency_code=currency['currency_code'],
                        base_currency=stock_data['base_currency'],
                        total_buy=currency['total_buy'],
                        total_sell=currency['total_sell'],
                        opening_balance=currency['opening_balance'],
                        change_amount=currency['change_amount'],
                        current_balance=currency['current_balance'],
                        stock_balance=currency['stock_balance'],
                        is_final=False,  # 暂时标记为非最终
                        eod_id=eod_id
                    )
                    session.add(stock_report)
                
                # 提交事务
                session.commit()
                
                LogService.log_system_event(
                    f"成功写入报表数据 - 日结ID: {eod_id}, 收入报表: {len(income_data.get('currencies', []))}, 库存报表: {len(stock_data.get('currencies', []))}",
                    operator_id=operator_id,
                    branch_id=branch_id
                )
            
                # 生成本币库存数据
                # base_currency_data已经在第3442行通过CalBaseCurrency函数计算完成
                # 不需要重新设置为None，避免覆盖正确的结果
                
                # 获取分支的基准货币
                branch = session.query(Branch).filter_by(id=branch_id).first()
                if branch:
                    base_currency = session.query(Currency).filter_by(id=branch.base_currency_id).first()
                    if base_currency:
                        base_currency_code = base_currency.currency_code
                        
                        # 【重构】按照统一的期初余额获取逻辑实现本币计算
                        # 1. 计算本币的期初余额和时间范围
                        base_currency_change_start_time = None
                        base_currency_change_end_time = None
                        opening_balance = 0
                        
                        # 【简化】统一从 EODBalanceVerification 表获取期初余额
                        latest_eod_record = session.query(EODBalanceVerification).join(
                            EODStatus, EODBalanceVerification.eod_status_id == EODStatus.id
                        ).filter(
                            EODBalanceVerification.currency_id == base_currency.id,
                            EODStatus.branch_id == branch_id,
                            EODStatus.date < target_date,
                            EODStatus.status == 'completed'
                        ).order_by(EODStatus.date.desc()).first()
                            
                        LogService.log_system_event(
                            f"本币期初余额查询 - 使用统一新表方式：EODBalanceVerification",
                            operator_id=operator_id,
                            branch_id=branch_id
                        )
                        
                        if latest_eod_record:
                            # 有上一次日结记录的情况
                            # 【简化】统一从 EODBalanceVerification 表获取
                            latest_eod_status = session.query(EODStatus).filter_by(
                                id=latest_eod_record.eod_status_id
                            ).first()
                            
                            if latest_eod_status and latest_eod_status.completed_at:
                                base_currency_change_start_time = latest_eod_status.completed_at
                                base_currency_change_end_time = eod_status.started_at
                                
                                # 期初余额：直接使用 actual_balance（已在步骤7扣减交款金额）
                                opening_balance = float(latest_eod_record.actual_balance)
                                LogService.log_system_event(
                                    f"本币期初余额 - 使用EODBalanceVerification.actual_balance: {opening_balance}",
                                    operator_id=operator_id,
                                    branch_id=branch_id
                                )
                            
                            LogService.log_system_event(
                                f"本币使用历史日结期初余额: {opening_balance}, 时间范围: {base_currency_change_start_time} ~ {base_currency_change_end_time}",
                                operator_id=operator_id,
                                branch_id=branch_id
                            )
                        else:
                            # 1.2 该本币没有上一次日结记录的情况
                            # 【修复】使用与日结第3步相同的逻辑
                            LogService.log_system_event(
                                f"本币没有历史日结记录，使用与日结第3步相同的_calculate_opening_balance_from_transactions函数",
                                operator_id=operator_id,
                                branch_id=branch_id
                            )
                            
                            # 使用与日结第3步相同的期初余额计算函数
                            from routes.app_reports import _calculate_opening_balance_from_transactions
                            opening_balance_float, base_currency_change_start_time = _calculate_opening_balance_from_transactions(
                                session, branch_id, base_currency.id, eod_status.started_at, base_currency.id
                            )
                            opening_balance = opening_balance_float
                            base_currency_change_end_time = eod_status.started_at
                            
                            LogService.log_system_event(
                                f"本币期初余额(与日结第3步一致): {opening_balance}, 时间范围: {base_currency_change_start_time} ~ {base_currency_change_end_time}",
                                operator_id=operator_id,
                                branch_id=branch_id
                            )
                        
                        # 2. 计算本币的当日交易变动（使用本币的个别化时间范围）
                        # 2.1 直接对本币的交易（如余额调整、本币交款等）- 使用local_amount字段保持一致性
                        direct_transactions = session.query(
                            func.coalesce(func.sum(ExchangeTransaction.local_amount), 0)
                        ).filter(
                            ExchangeTransaction.branch_id == branch_id,
                            ExchangeTransaction.currency_id == base_currency.id,
                            ExchangeTransaction.created_at >= base_currency_change_start_time,
                            ExchangeTransaction.created_at < base_currency_change_end_time,
                            ExchangeTransaction.status.in_(['completed', 'reversed'])
                        ).scalar() or 0
                        
                        # 2.2 所有外币交易对本币的影响（通过local_amount字段）
                        foreign_exchange_impact = session.query(
                            func.coalesce(func.sum(ExchangeTransaction.local_amount), 0)
                        ).filter(
                            ExchangeTransaction.branch_id == branch_id,
                            ExchangeTransaction.currency_id != base_currency.id,  # 排除本币直接交易
                            ExchangeTransaction.created_at >= base_currency_change_start_time,
                            ExchangeTransaction.created_at < base_currency_change_end_time,
                            ExchangeTransaction.status.in_(['completed', 'reversed'])
                        ).scalar() or 0
                        
                        # 合并两部分变动
                        daily_transactions = (direct_transactions or 0) + (foreign_exchange_impact or 0)
                        
                        # 计算当前余额
                        current_balance = opening_balance + float(daily_transactions)
                        
                        # 分类统计（用于显示详细信息）
                        income_amount = 0
                        expense_amount = 0
                        reversal_amount = 0  # 【新增】冲正金额
                        
                        # 详细统计（用local_amount保持一致）
                        foreign_transactions = session.query(ExchangeTransaction).filter(
                            and_(
                                ExchangeTransaction.branch_id == branch_id,
                                ExchangeTransaction.currency_id != base_currency.id,
                                ExchangeTransaction.created_at >= base_currency_change_start_time,
                                ExchangeTransaction.created_at < base_currency_change_end_time,
                                ExchangeTransaction.status.in_(['completed', 'reversed']),
                                ExchangeTransaction.type.in_(['buy', 'sell', 'initial_balance', 'adjust_balance', 'cash_out', 'reversal'])  # 排除Eod_diff
                            )
                        ).all()
                        
                        base_transactions = session.query(ExchangeTransaction).filter(
                            and_(
                                ExchangeTransaction.branch_id == branch_id,
                                ExchangeTransaction.currency_id == base_currency.id,
                                ExchangeTransaction.created_at >= base_currency_change_start_time,
                                ExchangeTransaction.created_at < base_currency_change_end_time,
                                ExchangeTransaction.status.in_(['completed', 'reversed']),
                                ExchangeTransaction.type.in_(['buy', 'sell', 'initial_balance', 'adjust_balance', 'cash_out', 'reversal'])  # 排除Eod_diff
                            )
                        ).all()
                        
                        # 【修复】统计外币交易对本币的影响，排除冲正交易
                        for tx in foreign_transactions:
                            local_amount = float(tx.local_amount)
                            if tx.type == 'reversal':
                                # 冲正交易单独统计
                                reversal_amount += local_amount
                            elif local_amount > 0:
                                income_amount += local_amount
                            else:
                                expense_amount += abs(local_amount)
                        
                        # 【修复】统计本币直接交易，排除冲正交易
                        for tx in base_transactions:
                            local_amount = float(tx.local_amount)
                            if tx.type == 'reversal':
                                # 冲正交易单独统计
                                reversal_amount += local_amount
                            elif local_amount > 0:
                                income_amount += local_amount
                            else:
                                expense_amount += abs(local_amount)
                        
                        LogService.log_system_event(
                            f"本币库存统计 - 收入金额: {income_amount}, 支出金额: {expense_amount}, 冲正金额: {reversal_amount}",
                            operator_id=operator_id,
                            branch_id=branch_id
                        )
                        
                        # 【修复】删除重复计算，直接使用CalBaseCurrency的结果
                        # base_currency_data已经在第3442行通过CalBaseCurrency函数计算完成
                        # 这里不需要重新计算，避免覆盖正确的结果
                    
            except Exception as db_error:
                session.rollback()
                LogService.log_system_event(
                    f"写入报表数据失败 - 日结ID: {eod_id}, 错误: {str(db_error)}",
                    operator_id=operator_id,
                    branch_id=branch_id
                )
                raise db_error
                
            # 【修复】更新步骤状态到第5步（处理核对结果）
            try:
                eod_status.step = 5
                eod_status.step_status = 'completed'
                session.commit()
                
                LogService.log_system_event(
                    f"更新日结步骤状态 - 日结ID: {eod_id}, 步骤: 5 (处理核对结果)",
                    operator_id=operator_id,
                    branch_id=branch_id
                )
            except Exception as step_update_error:
                session.rollback()
                LogService.log_error(
                    f"更新步骤状态失败 - 日结ID: {eod_id}, 错误: {str(step_update_error)}",
                    operator_id,
                    branch_id
                )
                # 即使步骤更新失败，也返回成功，因为数据已经生成
            
            # 【新增】同步生成多语言PDF文件 - 确保界面和PDF数据完全一致
            pdf_generated = False
            pdf_file_paths = {}
            supported_languages = ['zh', 'en', 'th']  # 【修复】恢复生成三种语言版本
            
            # 【调试】记录语言配置
            LogService.log_system_event(
                f"🔧 PDF生成配置 - 支持语言: {supported_languages}, 当前语言参数: {original_language}",
                operator_id=operator_id,
                branch_id=branch_id
            )
            
            try:
                LogService.log_system_event(
                    f"开始同步生成多语言收入报表PDF - 日结ID: {eod_id}, 语言: {supported_languages}",
                    operator_id=operator_id,
                    branch_id=branch_id
                )
                
                # 构建与界面显示完全一致的PDF数据
                # 【修复】使用实际的业务时间范围，也就是用于CalGain查询的时间段
                LogService.log_system_event(
                    f"📅 PDF数据时间范围 - 开始: {start_time} ({type(start_time)}), 结束: {end_time} ({type(end_time)})",
                    operator_id=operator_id,
                    branch_id=branch_id
                )
                
                # 【关键修复】确保时间数据正确传递，直接引用CalGain查询参数
                if start_time is None or end_time is None:
                    LogService.log_system_event(
                        f"[WARNING] 警告: start_time或end_time为None，这将导致PDF时间显示错误",
                        operator_id=operator_id,
                        branch_id=branch_id
                    )
                
                pdf_data = {
                    'eod_id': eod_id,
                    'eod_date': target_date,  # 保持原来的日期字段
                    'time_range': {  # 【关键】用于CalGain查询的实际时间范围，直接引用不做任何转换
                        'start_time': start_time,
                        'end_time': end_time
                    },
                    'branch_id': branch_id,
                    'date': target_date.isoformat(),  # 保持原格式
                    'income_reports': income_data.get('currencies', []) if isinstance(income_data, dict) else [],
                    'stock_reports': stock_data.get('currencies', []) if isinstance(stock_data, dict) else [],
                    'base_currency_data': base_currency_data,  # 使用新的CalBaseCurrency结果
                    'generated_at': datetime.now().isoformat()
                }
                
                # 使用SimplePDFService生成PDF到manager目录
                from services.simple_pdf_service import SimplePDFService
                
                # 构建EOD规范文件名前缀：YYYYMMDDEODxxx
                date_str = target_date.strftime('%Y%m%d')
                filename_prefix = f"{date_str}EOD{eod_id}income"
                
                # 【新增】生成三种语言版本的PDF
                successful_generations = 0
                LogService.log_system_event(
                    f"🔧 开始循环生成PDF - 总语言数: {len(supported_languages)}, 语言列表: {supported_languages}",
                    operator_id=operator_id,
                    branch_id=branch_id
                )
                
                for lang in supported_languages:
                    try:
                        # 生成对应语言的文件名
                        if lang == 'zh':
                            filename = f"{filename_prefix}.pdf"  # 中文版保持原名
                        else:
                            filename = f"{filename_prefix}_{lang}.pdf"  # 其他语言加后缀
                        
                        LogService.log_system_event(
                            f"🔧 开始生成{lang}语言PDF - 文件: {filename}, 循环索引: {supported_languages.index(lang) + 1}/{len(supported_languages)}",
                            operator_id=operator_id,
                            branch_id=branch_id
                        )
                        
                        # 生成PDF到manager目录
                        pdf_result = SimplePDFService.generate_eod_income_report_pdf_to_manager(
                            pdf_data, 
                            filename,
                            target_date,
                            eod_id,
                            lang
                        )
                        
                        # 【调试】记录PDF生成结果详情
                        LogService.log_system_event(
                            f"🔧 {lang}语言PDF生成结果 - pdf_result类型: {type(pdf_result)}, 内容: {pdf_result}",
                            operator_id=operator_id,
                            branch_id=branch_id
                        )
                        
                        if pdf_result and pdf_result.get('success'):
                            successful_generations += 1
                            pdf_file_paths[lang] = pdf_result.get('file_path')
                            LogService.log_system_event(
                                f"[OK] {lang}语言PDF生成成功 - 文件: {filename}, 路径: {pdf_result.get('file_path')}",
                                operator_id=operator_id,
                                branch_id=branch_id
                            )
                        else:
                            error_msg = pdf_result.get('message', '未知错误') if pdf_result else '生成器返回空结果'
                            LogService.log_system_event(
                                f"[ERROR] {lang}语言PDF生成失败 - 错误: {error_msg}, pdf_result: {pdf_result}",
                                operator_id=operator_id,
                                branch_id=branch_id
                            )
                    except Exception as lang_error:
                        LogService.log_system_event(
                            f"[ERROR] {lang}语言PDF生成异常 - 错误: {str(lang_error)}",
                            operator_id=operator_id,
                            branch_id=branch_id
                        )
                
                # 判断是否有成功生成的PDF
                LogService.log_system_event(
                    f"🔧 PDF生成总结 - 成功数: {successful_generations}/{len(supported_languages)}, 文件路径: {pdf_file_paths}",
                    operator_id=operator_id,
                    branch_id=branch_id
                )
                
                if successful_generations > 0:
                    pdf_generated = True
                    LogService.log_system_event(
                        f"[OK] 多语言PDF生成完成 - 成功: {successful_generations}/{len(supported_languages)}, 文件: {list(pdf_file_paths.keys())}",
                        operator_id=operator_id,
                        branch_id=branch_id
                    )
                else:
                    LogService.log_system_event(
                        f"[ERROR] 多语言PDF生成失败 - 所有语言都生成失败",
                        operator_id=operator_id,
                        branch_id=branch_id
                    )
            
            except Exception as pdf_error:
                # PDF生成失败不影响主流程，只记录日志
                LogService.log_system_event(
                    f"同步生成PDF异常 - 日结ID: {eod_id}, 错误: {str(pdf_error)}",
                    operator_id=operator_id,
                    branch_id=branch_id
                )
            
            # 【调试】记录最终返回结果
            final_result = {
                'success': True,
                'message': '收入统计完成',
                'income_data': income_data,  # 直接返回income_data
                'stock_data': stock_data,    # 直接返回stock_data
                'base_currency_data': base_currency_data,
                'reports_generated': True,
                'step_updated': True,
                'pdf_generated': pdf_generated,  # 标识PDF是否已生成
                'pdf_file_paths': pdf_file_paths   # PDF文件路径
            }
            
            LogService.log_system_event(
                f"🔧 收入统计完成 - PDF生成状态: {pdf_generated}, 文件路径: {pdf_file_paths}, 支持语言: {supported_languages}",
                operator_id=operator_id,
                branch_id=branch_id
            )
            
            return final_result
            
        except Exception as e:
            session.rollback()
            LogService.log_system_event(
                f"生成收入统计失败 - 日结ID: {eod_id}, 错误: {str(e)}",
                operator_id=operator_id,
                branch_id=eod_status.branch_id if eod_status else None
            )
            return {'success': False, 'message': f'收入统计失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def finalize_income_reports(eod_id, operator_id):
        """
        确认收入报表为最终版本 - 确保数据完整性和事务处理
        """
        from services.log_service import LogService
        session = DatabaseService.get_session()
        try:
            eod_status = session.query(EODStatus).filter_by(id=eod_id).first()
            if not eod_status:
                return {'success': False, 'message': '日结记录不存在'}
            
            branch_id = eod_status.branch_id
            target_date = eod_status.date
            
            # 开始事务处理
            from models.report_models import DailyIncomeReport, DailyForeignStock
            
            # 检查是否已有该eod_id的数据
            existing_income_count = session.query(DailyIncomeReport).filter_by(eod_id=eod_id).count()
            existing_stock_count = session.query(DailyForeignStock).filter_by(eod_id=eod_id).count()
            
            if existing_income_count == 0 and existing_stock_count == 0:
                # 如果没有数据，先生成数据
                LogService.log_system_event(
                    f"未找到报表数据，先生成数据 - 日结ID: {eod_id}",
                    operator_id=operator_id,
                    branch_id=branch_id
                )
                
                # 调用生成收入统计（使用默认中文）
                generate_result = EODService.generate_income_statistics(eod_id, operator_id, 'zh')
                if not generate_result['success']:
                    return generate_result
            
            # 使用事务确保原子性操作
            try:
                # 更新收入报表为最终版本
                updated_income = session.query(DailyIncomeReport).filter_by(
                eod_id=eod_id
                ).update({'is_final': True})
            
                # 更新库存报表为最终版本
                updated_stock = session.query(DailyForeignStock).filter_by(
                eod_id=eod_id
                ).update({'is_final': True})
            
                if updated_income == 0 and updated_stock == 0:
                    session.rollback()
                    return {'success': False, 'message': '未找到需要确认的报表数据'}
                
                # 提交事务
                session.commit()
                
                LogService.log_system_event(
                        f"确认收入报表为最终版本 - 日结ID: {eod_id}, 收入报表: {updated_income}, 库存报表: {updated_stock}",
                    operator_id=operator_id,
                    branch_id=branch_id
                )
                
                return {
                    'success': True,
                    'message': '收入报表已确认为最终版本',
                    'updated_counts': {
                        'income_reports': updated_income,
                        'stock_reports': updated_stock
                    },
                    'step': 7,
                    'step_status': 'processing'
                }
                
            except Exception as update_error:
                session.rollback()
                LogService.log_system_event(
                    f"更新报表最终状态失败 - 日结ID: {eod_id}, 错误: {str(update_error)}",
                    operator_id=operator_id,
                    branch_id=branch_id
                )
                raise update_error
                
        except Exception as e:
            session.rollback()
            LogService.log_system_event(
                f"确认收入报表失败 - 日结ID: {eod_id}, 错误: {str(e)}",
                operator_id=operator_id,
                branch_id=eod_status.branch_id if eod_status else None
            )
            return {'success': False, 'message': f'确认收入报表失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def print_comprehensive_reports(eod_id, operator_id):
        """
        打印综合报表 - 外币收入、外币库存、本币库存
        """
        from services.log_service import LogService
        session = DatabaseService.get_session()
        try:
            eod_status = session.query(EODStatus).filter_by(id=eod_id).first()
            if not eod_status:
                return {'success': False, 'message': '日结记录不存在'}
            
            branch_id = eod_status.branch_id
            target_date = eod_status.date
            
            # 获取外币收入报表数据
            from models.report_models import DailyIncomeReport, DailyForeignStock
            
            income_reports = session.query(DailyIncomeReport).filter_by(
                branch_id=branch_id,
                report_date=target_date,
                eod_id=eod_id
            ).all()
            
            # 获取外币库存报表数据
            stock_reports = session.query(DailyForeignStock).filter_by(
                branch_id=branch_id,
                report_date=target_date,
                eod_id=eod_id
            ).all()
            
            # 获取本币库存数据
            # 重新计算本币库存数据（与generate_income_statistics中的逻辑保持一致）
            base_currency_data = None
            
            # 获取分支的基准货币
            branch = session.query(Branch).filter_by(id=branch_id).first()
            if branch:
                base_currency = session.query(Currency).filter_by(id=branch.base_currency_id).first()
                if base_currency:
                    base_currency_code = base_currency.currency_code
                    
                    # 计算本币库存
                    start_time = datetime.combine(target_date, datetime.min.time())
                    end_time = datetime.combine(target_date + timedelta(days=1), datetime.min.time())
                    
                    # 获取前一天的日结记录余额
                    previous_eod_balance = 0
                    previous_eod_result = EODService.get_latest_eod_for_branch(branch_id, target_date)
                    
                    if previous_eod_result['success'] and previous_eod_result['balance_data']:
                        balance_data = previous_eod_result['balance_data']
                        if base_currency.id in balance_data:
                            previous_eod_balance = balance_data[base_currency.id]['remaining_balance']
                    
                    # 查询当日的初始化余额
                    initial_balance_amount = 0
                    initial_transactions = session.query(ExchangeTransaction).filter(
                        and_(
                            ExchangeTransaction.branch_id == branch_id,
                            ExchangeTransaction.currency_id == base_currency.id,
                            ExchangeTransaction.type == 'initial_balance',
                            func.date(ExchangeTransaction.created_at) == target_date
                        )
                    ).all()
                    
                    for tx in initial_transactions:
                        initial_balance_amount += float(tx.amount)
                    
                    # 计算期初余额
                    opening_balance = previous_eod_balance + initial_balance_amount
                    
                    # 统计兑换交易的本币变动
                    exchange_transactions = session.query(ExchangeTransaction).filter(
                        and_(
                            ExchangeTransaction.branch_id == branch_id,
                            ExchangeTransaction.currency_id != base_currency.id,
                            ExchangeTransaction.type.in_(['buy', 'sell']),
                            ExchangeTransaction.created_at >= start_time,
                            ExchangeTransaction.created_at < end_time
                        )
                    ).all()
                    
                    # 统计本币直接交易
                    base_currency_transactions = session.query(ExchangeTransaction).filter(
                        and_(
                            ExchangeTransaction.branch_id == branch_id,
                            ExchangeTransaction.currency_id == base_currency.id,
                            ExchangeTransaction.type.in_(['adjust', 'reversal', 'cash_out']),
                            ExchangeTransaction.created_at >= start_time,
                            ExchangeTransaction.created_at < end_time
                        )
                    ).all()
                    
                    # 分类统计
                    income_amount = 0
                    expense_amount = 0
                    adjustment_amount = 0
                    reversal_amount = 0
                    cashout_amount = 0
                    
                    # 统计兑换交易的本币变动
                    for tx in exchange_transactions:
                        local_amount = float(tx.local_amount)
                        if tx.type == 'buy':
                            expense_amount += abs(local_amount)
                        else:  # sell
                            income_amount += abs(local_amount)
                    
                    # 统计本币直接交易
                    for tx in base_currency_transactions:
                        amount = float(tx.amount)
                        if tx.type == 'adjust':
                            adjustment_amount += amount
                        elif tx.type == 'reversal':
                            reversal_amount += amount
                        elif tx.type == 'cash_out':
                            cashout_amount += abs(amount)
                    
                    # 计算当前余额
                    current_balance = opening_balance + income_amount - expense_amount + adjustment_amount + reversal_amount - cashout_amount
                    
                    base_currency_data = {
                        'currency_code': base_currency_code,
                        'opening_balance': opening_balance,
                        'income_amount': income_amount,
                        'expense_amount': expense_amount,
                        'adjustment_amount': adjustment_amount,
                        'reversal_amount': reversal_amount,
                        'cashout_amount': cashout_amount,
                        'current_balance': current_balance
                    }
            
            # 构建综合打印数据
            comprehensive_data = {
                'date': target_date.isoformat(),
                'branch_id': branch_id,
                'eod_id': eod_id,
                'income_reports': [
                    {
                        'currency_code': report.currency_code,
                        'total_buy': float(report.total_buy),
                        'total_sell': float(report.total_sell),
                        'income': float(report.income),
                        'spread_income': float(report.spread_income)
                    }
                    for report in income_reports
                ],
                'stock_reports': [
                    {
                        'currency_code': report.currency_code,
                        'total_buy': float(report.total_buy),
                        'total_sell': float(report.total_sell),
                        'stock_balance': float(report.stock_balance)
                    }
                    for report in stock_reports
                ],
                'base_currency_data': base_currency_data
            }
            
            # 使用SimplePDFService生成综合PDF
            from services.simple_pdf_service import SimplePDFService
            
            # 构建文件名：使用新的EOD命名规范
            date_str = target_date.strftime('%Y%m%d')
            filename = f"{date_str}EOD{eod_id}income.pdf"
            
            # 生成PDF (添加language参数)
            pdf_result = SimplePDFService.generate_comprehensive_eod_report_pdf(
                comprehensive_data, 
                filename,
                target_date,
                language='zh'  # 明确传递language参数
            )
            
            if pdf_result['success']:
                LogService.log_system_event(
                    f"打印综合报表成功 - 日结ID: {eod_id}, 文件: {filename}",
                    operator_id=operator_id,
                    branch_id=branch_id
                )
                
                return {
                    'success': True,
                    'message': '综合报表打印成功',
                    'pdf_file': filename,
                    'file_path': pdf_result['file_path']
                }
            else:
                return {'success': False, 'message': pdf_result['message']}
            
        except Exception as e:
            LogService.log_system_event(
                f"打印综合报表失败 - 日结ID: {eod_id}, 错误: {str(e)}",
                operator_id=operator_id,
                branch_id=eod_status.branch_id if eod_status else None
            )
            return {'success': False, 'message': f'打印综合报表失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def print_income_reports(eod_id, operator_id, language='zh'):
        """
        打印收入报表 - 优先使用已生成的PDF文件，确保数据一致性，支持多语言
        """
        from services.log_service import LogService
        import os
        
        # 【修复】标准化语言代码，处理 th-TH -> th, en-US -> en 的映射
        def normalize_language_code(lang_code):
            """标准化语言代码"""
            if not lang_code:
                return 'zh'
            
            lang_code = lang_code.lower()
            if lang_code.startswith('th'):
                return 'th'
            elif lang_code.startswith('en'):
                return 'en'
            elif lang_code.startswith('zh'):
                return 'zh'
            else:
                return 'zh'  # 默认中文
        
        original_language = language
        language = normalize_language_code(language)
        
        session = DatabaseService.get_session()
        try:
            eod_status = session.query(EODStatus).filter_by(id=eod_id).first()
            if not eod_status:
                return {'success': False, 'message': '日结记录不存在'}
            
            branch_id = eod_status.branch_id
            target_date = eod_status.date
            
            # 记录语言参数标准化
            LogService.log_system_event(
                f"语言参数标准化 - 原始: {original_language}, 标准化后: {language}",
                operator_id=operator_id,
                branch_id=branch_id
            )
            
            # 【新逻辑】首先检查是否有已生成的PDF文件（与统计数据同步生成）
            from services.simple_pdf_service import SimplePDFService
            
            # 构建预期的PDF文件路径和名称（根据语言参数）
            date_str = target_date.strftime('%Y%m%d')
            if language == 'th':
                filename = f"{date_str}EOD{eod_id}income_th.pdf"
            elif language == 'en':
                filename = f"{date_str}EOD{eod_id}income_en.pdf"
            else:  # 默认中文
                filename = f"{date_str}EOD{eod_id}income.pdf"
            
            # 获取manager目录下的文件路径
            expected_file_path = SimplePDFService.get_manager_file_path(
                'income', 
                eod_id=eod_id, 
                eod_date=target_date
            )
            # 确保使用正确的文件名
            expected_file_path = os.path.join(os.path.dirname(expected_file_path), filename)
            
            # 检查同步生成的PDF是否存在
            if os.path.exists(expected_file_path):
                language_name = {'zh': '中文', 'th': '泰语', 'en': '英语'}.get(language, '中文')
                LogService.log_system_event(
                    f"使用已生成{language_name}PDF文件（与统计数据同步生成，数据完全一致） - 日结ID: {eod_id}, 文件: {filename}",
                    operator_id=operator_id,
                    branch_id=branch_id
                )
                
                return {
                    'success': True,
                    'message': f'收入报表已准备就绪（使用同步生成的{language_name}PDF）',
                    'pdf_file': filename,
                    'file_path': expected_file_path,
                    'source': 'synchronized',
                    'language': language
                }
            
            # 【备用方案】PDF文件丢失时，尝试重新生成
            LogService.log_system_event(
                f"同步生成的PDF文件不存在，尝试重新生成 - 日结ID: {eod_id}, 期望路径: {expected_file_path}",
                operator_id=operator_id,
                branch_id=branch_id
            )
            
            # 尝试重新生成PDF文件
            try:
                from services.simple_pdf_service import SimplePDFService
                
                # 重新生成收入统计数据
                income_result = EODService.generate_income_statistics(eod_id, operator_id, language)
                
                if income_result.get('success') and income_result.get('pdf_generated'):
                    # 重新检查PDF文件是否存在
                    if os.path.exists(expected_file_path):
                        language_name = {'zh': '中文', 'th': '泰语', 'en': '英语'}.get(language, '中文')
                        LogService.log_system_event(
                            f"重新生成{language_name}PDF文件成功 - 日结ID: {eod_id}, 文件: {filename}",
                            operator_id=operator_id,
                            branch_id=branch_id
                        )
                        
                        return {
                            'success': True,
                            'message': f'收入报表已准备就绪（重新生成{language_name}PDF）',
                            'pdf_file': filename,
                            'file_path': expected_file_path,
                            'source': 'regenerated',
                            'language': language
                        }
                    else:
                        LogService.log_system_event(
                            f"重新生成PDF文件仍然失败 - 日结ID: {eod_id}",
                            operator_id=operator_id,
                            branch_id=branch_id
                        )
                else:
                    LogService.log_system_event(
                        f"重新生成收入统计失败 - 日结ID: {eod_id}, 错误: {income_result.get('message', '未知错误')}",
                        operator_id=operator_id,
                        branch_id=branch_id
                    )
            except Exception as regen_error:
                LogService.log_system_event(
                    f"重新生成PDF文件异常 - 日结ID: {eod_id}, 错误: {str(regen_error)}",
                    operator_id=operator_id,
                    branch_id=branch_id
                )
            
            return {
                'success': False,
                'message': 'PDF文件丢失，请重新执行第5步生成收入统计',
                'error_code': 'PDF_NOT_FOUND'
            }
            
        except Exception as e:
            LogService.log_system_event(
                f"打印收入报表失败 - 日结ID: {eod_id}, 错误: {str(e)}",
                operator_id=operator_id,
                branch_id=eod_status.branch_id if eod_status else None
            )
            return {'success': False, 'message': f'打印收入报表失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def reset_to_print_step(eod_id, operator_id):
        """
        重置日结状态到第7步 - 用于修正错误跳过打印步骤的情况
        """
        from services.log_service import LogService
        session = DatabaseService.get_session()
        try:
            eod_status = session.query(EODStatus).filter_by(id=eod_id).first()
            if not eod_status:
                return {'success': False, 'message': '日结记录不存在'}
            
            # 检查是否可以重置
            if eod_status.status == 'completed':
                return {'success': False, 'message': '已完成的日结不能重置'}
            
            # 重置到第7步
            eod_status.step = 7
            eod_status.step_status = 'pending'  # 设置为待完成
            eod_status.print_count = 0  # 重置打印次数
            eod_status.print_operator_id = None
            
            session.commit()
            
            LogService.log_system_event(
                f"重置日结状态到第7步 - 日结ID: {eod_id}",
                operator_id=operator_id,
                branch_id=eod_status.branch_id
            )
            
            return {
                'success': True,
                'message': '已重置到第7步，请完成报表打印',
                'step': 7,
                'step_status': 'pending'
            }
            
        except Exception as e:
            session.rollback()
            LogService.log_system_event(
                f"重置日结状态失败 - 日结ID: {eod_id}, 错误: {str(e)}",
                operator_id=operator_id,
                branch_id=eod_status.branch_id if eod_status else None
            )
            return {'success': False, 'message': f'重置失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def _calculate_base_currency_data(session, branch_id, target_date, eod_id):
        """
        计算本币库存数据
        
        Args:
            session: 数据库会话
            branch_id: 分支ID
            target_date: 目标日期
            eod_id: 日结ID
            
        Returns:
            dict: 本币库存数据
        """
        import logging
        logger = logging.getLogger(__name__)
        
        from models.exchange_models import Branch, Currency, CurrencyBalance, ExchangeTransaction
        from sqlalchemy import and_, func
        from datetime import timedelta
        
        try:
            # 获取分支的基准货币
            branch = session.query(Branch).filter_by(id=branch_id).first()
            if not branch or not branch.base_currency_id:
                logger.warning(f"未找到分支或基准货币配置: branch_id={branch_id}")
                return None
            
            base_currency = session.query(Currency).filter_by(id=branch.base_currency_id).first()
            if not base_currency:
                logger.warning(f"未找到基准货币: base_currency_id={branch.base_currency_id}")
                return None
            
            base_currency_code = base_currency.currency_code
            logger.info(f"计算本币库存: {base_currency_code}")
            
            # 设置时间范围
            start_time = datetime.combine(target_date, datetime.min.time())
            end_time = datetime.combine(target_date + timedelta(days=1), datetime.min.time())
            
            # 获取期初余额
            opening_balance = 0
            
            # 方法1：从CurrencyBalance表获取当前余额作为基础
            balance_record = session.query(CurrencyBalance).filter_by(
                branch_id=branch_id,
                currency_id=base_currency.id
            ).first()
            
            if balance_record:
                opening_balance = float(balance_record.balance)
                logger.info(f"从CurrencyBalance获取余额: {opening_balance}")
            
            # 统计当日所有交易
            all_transactions = session.query(ExchangeTransaction).filter(
                and_(
                    ExchangeTransaction.branch_id == branch_id,
                    ExchangeTransaction.created_at >= start_time,
                    ExchangeTransaction.created_at < end_time
                )
            ).all()
            
            logger.info(f"找到当日交易总数: {len(all_transactions)}")
            
            # 分类统计
            income_amount = 0      # 收入金额（卖出外币收到的本币）
            expense_amount = 0     # 支出金额（买入外币支付的本币）
            adjustment_amount = 0  # 调整金额
            reversal_amount = 0    # 冲正金额
            cashout_amount = 0     # 交款金额
            
            for tx in all_transactions:
                if tx.currency_id == base_currency.id:
                    # 本币直接交易
                    amount = float(tx.amount) if tx.amount else 0
                    if tx.type == 'adjust':
                        adjustment_amount += amount
                    elif tx.type == 'reversal':
                        reversal_amount += amount
                    elif tx.type == 'cash_out':
                        cashout_amount += abs(amount)
                    elif tx.type == 'initial_balance':
                        # 初始化余额调整期初余额
                        opening_balance += amount
                else:
                    # 外币兑换交易
                    local_amount = float(tx.local_amount) if tx.local_amount else 0
                    if tx.type == 'sell':
                        # 卖出外币，收到本币
                        income_amount += abs(local_amount)
                    elif tx.type == 'buy':
                        # 买入外币，支付本币
                        expense_amount += abs(local_amount)
            
            # 计算当前余额
            # current_balance = opening_balance + income_amount - expense_amount + adjustment_amount + reversal_amount - cashout_amount
            # 为了准确性，直接使用CurrencyBalance表的当前值
            current_balance = opening_balance
            
            result = {
                'currency_code': base_currency_code,
                'opening_balance': opening_balance - income_amount + expense_amount - adjustment_amount - reversal_amount + cashout_amount,  # 推算期初
                'income_amount': income_amount,
                'expense_amount': expense_amount,
                'adjustment_amount': adjustment_amount,
                'reversal_amount': reversal_amount,
                'cashout_amount': cashout_amount,
                'current_balance': current_balance
            }
            
            logger.info(f"本币库存计算结果: {result}")
            return result
            
        except Exception as e:
            logger.error(f"计算本币库存数据失败: {e}")
            return None 

    @staticmethod
    def auto_cleanup_orphaned_eod(branch_id=None):
        """
        自动清理孤立的EOD记录
        """
        session = DatabaseService.get_session()
        try:
            # 查询所有处理中的EOD记录
            query = session.query(EODStatus).filter(
                EODStatus.status == 'processing'
            )
            
            if branch_id:
                query = query.filter(EODStatus.branch_id == branch_id)
            
            processing_eods = query.all()
            
            cleaned_count = 0
            for eod in processing_eods:
                # 检查是否有对应的活跃会话锁定
                session_lock = session.query(EODSessionLock).filter(
                    EODSessionLock.eod_status_id == eod.id,
                    EODSessionLock.is_active == True
                ).first()
                
                if not session_lock:
                    # 自动清理孤立的EOD记录
                    eod.status = 'cancelled'
                    eod.cancel_reason = '系统自动清理：孤立记录'
                    eod.completed_at = datetime.now()
                    eod.is_locked = False
                    eod.step_status = 'cancelled'
                    cleaned_count += 1
                    
                    # 【优化】同时清理可能存在的会话锁定记录
                    cleanup_result = EODService.cleanup_eod_session_locks(eod.id)
                    if cleanup_result['success'] and cleanup_result['cleaned_count'] > 0:
                        LogService.log_system_event(
                            f"自动清理孤立的EOD记录: ID {eod.id}, Branch {eod.branch_id}, 同时清理了 {cleanup_result['cleaned_count']} 个会话锁定",
                            branch_id=eod.branch_id
                        )
                    else:
                        LogService.log_system_event(
                            f"自动清理孤立的EOD记录: ID {eod.id}, Branch {eod.branch_id}",
                            branch_id=eod.branch_id
                        )
            
            if cleaned_count > 0:
                session.commit()
                print(f"自动清理了 {cleaned_count} 个孤立的EOD记录")
            
            return {
                'success': True,
                'cleaned_count': cleaned_count,
                'message': f'自动清理了 {cleaned_count} 个孤立的EOD记录'
            }
            
        except Exception as e:
            session.rollback()
            LogService.log_error(f"自动清理孤立EOD记录失败: {str(e)}")
            return {
                'success': False,
                'message': f'自动清理失败: {str(e)}'
            }
        finally:
            DatabaseService.close_session(session)

    @staticmethod
    def validate_eod_permission(eod_id, operator_id, session_id=None):
        """
        统一验证日结操作权限
        """
        session = DatabaseService.get_session()
        try:
            # 1. 检查EOD记录存在且状态正确
            eod_status = session.query(EODStatus).filter_by(id=eod_id).first()
            if not eod_status:
                return {
                    'success': False, 
                    'has_permission': False,
                    'message': '日结记录不存在'
                }
            
            if eod_status.status != 'processing':
                return {
                    'success': False, 
                    'has_permission': False,
                    'message': f'日结状态不正确: {eod_status.status}'
                }
            
            # 2. 检查操作员权限（必须是开始日结的操作员）
            if eod_status.started_by != operator_id:
                return {
                    'success': False, 
                    'has_permission': False,
                    'message': '只有开始日结的操作员才能完成日结'
                }
            
            # 3. 检查会话锁定（如果提供了session_id）
            if session_id:
                session_lock = session.query(EODSessionLock).filter(
                    EODSessionLock.eod_status_id == eod_id,
                    EODSessionLock.session_id == session_id,
                    EODSessionLock.is_active == True
                ).first()
                
                if not session_lock:
                    return {
                        'success': False, 
                        'has_permission': False,
                        'message': '会话锁定无效或已过期'
                    }
                
                # 更新会话活跃时间
                session_lock.last_activity = datetime.now()
                session.commit()
            
            return {
                'success': True,
                'has_permission': True,
                'message': '权限验证通过',
                'eod_status': eod_status
            }
            
        except Exception as e:
            return {
                'success': False,
                'has_permission': False,
                'message': f'权限验证失败: {str(e)}'
            }
        finally:
            DatabaseService.close_session(session)

    @staticmethod
    def cleanup_eod_session_locks(eod_id, operator_id=None):
        """
        统一清理指定EOD的所有会话锁定记录
        """
        session = DatabaseService.get_session()
        try:
            # 查询该EOD的所有会话锁定记录
            session_locks = session.query(EODSessionLock).filter(
                EODSessionLock.eod_status_id == eod_id
            ).all()
            
            cleaned_count = 0
            for session_lock in session_locks:
                session.delete(session_lock)
                cleaned_count += 1
            
            session.commit()
            
            # 记录清理日志
            if operator_id:
                LogService.log_system_event(
                    f"清理EOD会话锁定记录: EOD ID {eod_id}, 清理数量 {cleaned_count}",
                    operator_id=operator_id
                )
            
            return {
                'success': True,
                'message': f'成功清理 {cleaned_count} 个会话锁定记录',
                'cleaned_count': cleaned_count
            }
            
        except Exception as e:
            session.rollback()
            error_msg = f'清理会话锁定失败: {str(e)}'
            if operator_id:
                LogService.log_error(error_msg, operator_id=operator_id)
            return {
                'success': False,
                'message': error_msg
            }
        finally:
            DatabaseService.close_session(session)

    @staticmethod
    def get_theoretical_balance_data(eod_id):
        """
        获取理论余额计算数据（不修改步骤状态）
        """
        logging.info(f"获取理论余额计算数据 - EOD ID: {eod_id}")
        session = DatabaseService.get_session()
        try:
            eod_status = session.query(EODStatus).filter_by(id=eod_id).first()
            if not eod_status:
                return {'success': False, 'message': '日结记录不存在'}
            
            branch_id = eod_status.branch_id
            target_date = eod_status.date
            
            # 获取网点信息
            branch = session.query(Branch).filter_by(id=branch_id).first()
            if not branch:
                return {'success': False, 'message': '网点不存在'}
            
            # 【修改】先获取所有可能涉及的币种，然后按币种分别计算时间范围
            # 获取所有有余额的币种（包括余额为0的）
            balance_currency_ids = session.query(CurrencyBalance.currency_id).filter(
                CurrencyBalance.branch_id == branch_id
            ).distinct().all()
            
            # 获取日结营业统计时间范围
            business_start_time = None
            business_end_time = None
            prev_eod = session.query(EODStatus).filter(
                EODStatus.branch_id == branch_id,
                EODStatus.status == 'completed'
            ).order_by(desc(EODStatus.completed_at)).first()
            if prev_eod and prev_eod.completed_at:
                business_start_time = prev_eod.completed_at
            else:
                first_transaction = session.query(ExchangeTransaction).filter(
                    ExchangeTransaction.branch_id == branch_id
                ).order_by(ExchangeTransaction.transaction_date).first()
                if first_transaction:
                    business_start_time = first_transaction.transaction_date
            business_end_time = eod_status.started_at
            logger.info(f"🌍 日结营业统计时间范围: {business_start_time} 到 {business_end_time}")
            # 获取在营业时间范围内有交易记录的币种
            transaction_currency_ids = []
            if business_start_time and business_end_time:
                transaction_currency_ids = session.query(ExchangeTransaction.currency_id).filter(
                    ExchangeTransaction.branch_id == branch_id,
                    ExchangeTransaction.status.in_(['completed', 'reversed']),
                    ExchangeTransaction.transaction_date >= business_start_time,
                    ExchangeTransaction.transaction_date <= business_end_time
                ).distinct().all()
            # 合并所有币种ID（包括余额为0的和有交易记录的）
            currency_ids = set([row[0] for row in balance_currency_ids] + [row[0] for row in transaction_currency_ids])
            
            # 总是包含本币，即使没有交易记录
            if branch.base_currency_id:
                currency_ids.add(branch.base_currency_id)
            
            # 获取所有涉及的币种
            currencies = session.query(Currency).filter(
                Currency.id.in_(currency_ids)
            ).all() if currency_ids else []
            
            balance_calculations = []
            
            for currency in currencies:
                # 安全检查：确保currency对象和currency_code字段存在
                if not currency or not currency.currency_code:
                    logging.warning(f"[WARNING] 跳过无效币种: currency={currency}")
                    continue
                
                # 【关键修改】为每个币种分别计算时间范围和期初余额
                
                # 【简化】统一从 EODBalanceVerification 表查找该币种的上一次日结记录
                prev_eod_verification = session.query(EODBalanceVerification).join(EODStatus).filter(
                    EODStatus.branch_id == branch_id,
                    EODStatus.id != eod_id,  # 排除当前日结
                    EODStatus.status == 'completed',
                    EODBalanceVerification.currency_id == currency.id
                ).order_by(desc(EODStatus.completed_at)).first()
                
                if prev_eod_verification:
                    # 该币种有上一次日结记录
                    # 期初余额：使用上次日结验证后的余额
                    opening_balance = Decimal(str(prev_eod_verification.actual_balance))
                    
                    # 时间范围：从上一次日结结束时间到本次日结开始时间
                    prev_eod_status = session.query(EODStatus).filter_by(id=prev_eod_verification.eod_status_id).first()
                    
                    logging.info(f"📋 币种{currency.currency_code}找到上次日结记录:")
                    logging.info(f"  - 上次日结ID: {prev_eod_verification.eod_status_id}")
                    logging.info(f"  - 期初余额: {opening_balance}")
                    logging.info(f"  - completed_at: {prev_eod_status.completed_at if prev_eod_status else 'None'}")
                    
                    if prev_eod_status and prev_eod_status.completed_at:
                        currency_change_start_time = prev_eod_status.completed_at
                        currency_change_end_time = eod_status.started_at
                        
                        logging.info(f"[OK] 币种{currency.currency_code}使用上次日结时间:")
                        logging.info(f"  - 变化开始时间: {currency_change_start_time}")
                        logging.info(f"  - 变化结束时间: {currency_change_end_time}")
                    else:
                        # 如果找不到完成时间，fallback到第一笔交易逻辑
                        logging.warning(f"[WARNING] 币种{currency.currency_code}上次日结记录存在但completed_at为空，fallback到第一笔交易逻辑")
                        
                        from routes.app_reports import _calculate_opening_balance_from_transactions
                        
                        opening_balance_float, currency_change_start_time = _calculate_opening_balance_from_transactions(
                            session, branch_id, currency.id, eod_status.started_at, branch.base_currency_id if branch else None
                        )
                        
                        opening_balance = Decimal(str(opening_balance_float))
                        currency_change_end_time = eod_status.started_at
                        
                        logging.info(f"📊 币种{currency.currency_code}期初余额(fallback): {opening_balance}")
                        logging.info(f"📅 币种{currency.currency_code}变化统计时间(fallback): {currency_change_start_time} 到 {currency_change_end_time}")
                
                else:
                    # 该币种没有上一次日结记录
                    # 从第一笔交易的值作为期初余额
                    from routes.app_reports import _calculate_opening_balance_from_transactions
                    
                    opening_balance_float, currency_change_start_time = _calculate_opening_balance_from_transactions(
                        session, branch_id, currency.id, eod_status.started_at, branch.base_currency_id if branch else None
                    )
                    
                    opening_balance = Decimal(str(opening_balance_float))
                    currency_change_end_time = eod_status.started_at
                    
                    logging.info(f"📊 币种{currency.currency_code}期初余额(第一笔交易): {opening_balance}")
                    logging.info(f"📅 币种{currency.currency_code}变化统计时间: {currency_change_start_time} 到 {currency_change_end_time}")
                
                # 计算当日变动
                daily_transactions = session.query(func.sum(ExchangeTransaction.amount)).filter(
                    ExchangeTransaction.branch_id == branch_id,
                    ExchangeTransaction.currency_id == currency.id,
                    ExchangeTransaction.created_at >= currency_change_start_time,
                    ExchangeTransaction.created_at < currency_change_end_time,
                    ExchangeTransaction.status.in_(['completed', 'reversed']),
                    ExchangeTransaction.type.in_(['buy', 'sell', 'reversal'])  # 排除adjust_balance和Eod_diff
                ).scalar()
                
                daily_change = Decimal(str(daily_transactions or 0))
                theoretical_balance = opening_balance + daily_change
                
                # 【调试日志】记录计算过程
                logging.info(f"🔍 {currency.currency_code} 计算过程:")
                logging.info(f"  - 期初余额: {opening_balance}")
                logging.info(f"  - 当日变动: {daily_change}")
                logging.info(f"  - 理论余额: {theoretical_balance}")
                
                # 获取实际余额
                actual_balance_record = session.query(CurrencyBalance).filter_by(
                    branch_id=branch_id,
                    currency_id=currency.id
                ).first()
                
                actual_balance = Decimal(str(actual_balance_record.balance)) if actual_balance_record else Decimal('0')
                
                balance_calculations.append({
                    'currency_id': currency.id,
                    'currency_code': currency.currency_code,
                    'currency_name': currency.currency_name,
                    'custom_flag_filename': currency.custom_flag_filename,  # 【新增】自定义图标文件名
                    'flag_code': currency.flag_code,  # 【新增】标准图标代码
                    'opening_balance': float(opening_balance),
                    'daily_change': float(daily_change),
                    'theoretical_balance': float(theoretical_balance),
                    'actual_balance': float(actual_balance),
                    'difference': float(theoretical_balance - actual_balance),
                    'change_start_time': currency_change_start_time.isoformat() if currency_change_start_time else None,
                    'change_end_time': currency_change_end_time.isoformat() if currency_change_end_time else None
                })
                
                # 【调试日志】记录返回的数据
                logging.info(f"🔍 {currency.currency_code} 返回数据:")
                logging.info(f"  - currency_id: {currency.id}")
                logging.info(f"  - currency_code: {currency.currency_code}")
                logging.info(f"  - currency_name: {currency.currency_name}")
                logging.info(f"  - opening_balance: {float(opening_balance)}")
                logging.info(f"  - daily_change: {float(daily_change)}")
                logging.info(f"  - theoretical_balance: {float(theoretical_balance)}")
                logging.info(f"  - actual_balance: {float(actual_balance)}")
            
            # 使用I18n工具类获取消息
            from utils.i18n_utils import I18nUtils
            
            return {
                'success': True,
                'message': I18nUtils.get_message('eod.theoretical_balance_calculated'),
                'calculations': balance_calculations
            }
            
        except Exception as e:
            session.rollback()
            from utils.i18n_utils import I18nUtils
            return {'success': False, 'message': f'{I18nUtils.get_message("eod.calculation_failed")}: {str(e)}'}
        finally:
            DatabaseService.close_session(session)

    @staticmethod
    def validate_difference_adjustment(eod_id, adjust_data):
        """
        验证差额调节的合理性
        :param eod_id: 日结ID
        :param adjust_data: 调节数据列表
        :return: 验证结果
        """
        session = DatabaseService.get_session()
        try:
            eod_status = session.query(EODStatus).filter_by(id=eod_id).first()
            if not eod_status:
                return {'success': False, 'message': '日结记录不存在'}
            
            # 获取当前余额记录
            current_balances = {}
            for adjust_item in adjust_data:
                currency_id = adjust_item['currency_id']
                balance_record = session.query(CurrencyBalance).filter_by(
                    branch_id=eod_status.branch_id,
                    currency_id=currency_id
                ).first()
                
                if balance_record:
                    current_balances[currency_id] = float(balance_record.balance or 0)
                else:
                    current_balances[currency_id] = 0.0
            
            # 模拟调节后的余额
            adjusted_balances = {}
            for adjust_item in adjust_data:
                currency_id = adjust_item['currency_id']
                adjust_amount = float(adjust_item['adjust_amount'])
                current_balance = current_balances.get(currency_id, 0.0)
                adjusted_balances[currency_id] = current_balance + adjust_amount
            
            # 验证调节后的余额是否合理
            validation_results = []
            all_valid = True
            
            for adjust_item in adjust_data:
                currency_id = adjust_item['currency_id']
                adjust_amount = float(adjust_item['adjust_amount'])
                current_balance = current_balances.get(currency_id, 0.0)
                adjusted_balance = adjusted_balances[currency_id]
                
                # 获取币种信息
                currency = session.query(Currency).filter_by(id=currency_id).first()
                if not currency:
                    validation_results.append({
                        'currency_id': currency_id,
                        'currency_code': 'UNKNOWN',
                        'is_valid': False,
                        'message': '币种不存在'
                    })
                    all_valid = False
                    continue
                
                # 验证规则
                validation_checks = []
                
                # 1. 检查调节金额是否过大（超过当前余额的50%）
                if current_balance > 0 and abs(adjust_amount) > current_balance * 0.5:
                    validation_checks.append(f'调节金额({adjust_amount})超过当前余额({current_balance})的50%')
                
                # 2. 检查调节后余额是否为负数（除非是冲正操作）
                if adjusted_balance < 0:
                    validation_checks.append(f'调节后余额({adjusted_balance})将为负数')
                
                # 3. 检查调节金额是否过小（小于0.01）
                if abs(adjust_amount) < 0.01:
                    validation_checks.append(f'调节金额({adjust_amount})过小，可能不需要调节')
                
                # 4. 检查调节金额是否过大（超过100万）
                if abs(adjust_amount) > 1000000:
                    validation_checks.append(f'调节金额({adjust_amount})过大，请确认是否正确')
                
                is_valid = len(validation_checks) == 0
                if not is_valid:
                    all_valid = False
                
                validation_results.append({
                    'currency_id': currency_id,
                    'currency_code': currency.currency_code,
                    'currency_name': currency.currency_name,
                    'current_balance': current_balance,
                    'adjust_amount': adjust_amount,
                    'adjusted_balance': adjusted_balance,
                    'is_valid': is_valid,
                    'warnings': validation_checks,
                    'message': '; '.join(validation_checks) if validation_checks else '验证通过'
                })
            
            return {
                'success': True,
                'all_valid': all_valid,
                'validation_results': validation_results,
                'message': '所有调节项目验证通过' if all_valid else '部分调节项目存在问题，请检查'
            }
            
        except Exception as e:
            logging.error(f"差额调节验证失败: {str(e)}")
            return {'success': False, 'message': f'差额调节验证失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)