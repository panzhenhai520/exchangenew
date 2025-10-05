"""
日结步骤管理 API
"""

from flask import Blueprint, request, jsonify
from services.auth_service import token_required, has_permission
from services.log_service import LogService
from services.db_service import DatabaseService
from services.eod_service import EODService
from datetime import datetime, timedelta
import os
import glob
from sqlalchemy import and_, func
from sqlalchemy.orm import joinedload
from models.exchange_models import EODStatus, Currency, Branch, ExchangeTransaction, CurrencyBalance, EODCashOut, EODBalanceVerification, EODSessionLock
from models.report_models import DailyIncomeReport, DailyStockReport
from utils.language_utils import get_current_language
import logging

eod_step_bp = Blueprint('eod_step', __name__, url_prefix='/api/eod-step')

@eod_step_bp.route('/<int:eod_id>/cancel-complete', methods=['POST'])
@token_required
@has_permission('end_of_day')
def cancel_complete_eod(current_user, eod_id):
    """智能取消日结 - 根据当前步骤进行不同的处理"""
    try:
        data = request.get_json()
        reason = data.get('reason', '用户取消日结')
        
        db_service = DatabaseService()
        eod_service = EODService()
        
        # 获取日结记录
        eod_status = db_service.get_session().query(EODStatus).filter_by(id=eod_id).first()
        if not eod_status:
            return jsonify({'success': False, 'message': '日结记录不存在'}), 404
        
        if eod_status.status == 'completed':
            return jsonify({'success': False, 'message': '已完成的日结不能取消'}), 400
        
        # 记录取消操作
        LogService.log_business_operation(
            'eod_cancel',
            f'取消日结: {eod_id}, 当前步骤: {eod_status.step}, 原因: {reason}',
            current_user.get('id'),
            eod_status.branch_id
        )
        
        session = db_service.get_session()
        try:
            # 根据当前步骤进行不同的处理
            if eod_status.step >= 7:
                # 第7步后：智能取消，恢复交款前状态
                result = _smart_cancel_after_cash_out(session, eod_status, current_user, reason)
            else:
                # 第7步前：简单取消
                result = _simple_cancel_before_cash_out(session, eod_status, current_user, reason)
            
            if result['success']:
                db_service.commit_session(session)
                
                # 记录日结取消操作日志
                try:
                    current_language = get_current_language()
                    from services.unified_log_service import log_eod_operation
                    log_eod_operation(
                        operator_id=current_user['id'],
                        branch_id=current_user['branch_id'],
                        eod_action='cancel',
                        eod_date=str(eod_status.date),
                        ip_address=request.remote_addr,
                        eod_id=str(eod_id),
                        language=current_language
                    )
                except Exception as log_error:
                    print(f"日结取消操作日志记录失败: {log_error}")
                
                return jsonify(result), 200
            else:
                return jsonify(result), 400
                
        except Exception as e:
            db_service.rollback_session(session)
            raise e
        finally:
            db_service.close_session(session)
            
    except Exception as e:
        LogService.log_error(
            f'取消日结失败: {str(e)}',
            current_user.get('id'),
            eod_status.branch_id if 'eod_status' in locals() else None
        )
        return jsonify({'success': False, 'message': f'取消日结失败: {str(e)}'}), 500


def _simple_cancel_before_cash_out(session, eod_status, current_user, reason):
    """第7步前的简单取消"""
    try:
        # 1. 删除PDF文件
        _delete_eod_pdf_files(eod_status, current_user)
        
        # 2. 删除相关数据记录
        _delete_eod_data_records(session, eod_status.id, eod_status)
        
        # 3. 更新日结状态
        eod_status.status = 'cancelled'
        eod_status.completed_at = datetime.now()
        eod_status.completed_by = current_user.get('id')
        eod_status.step = 1
        eod_status.step_status = 'cancelled'
        
        # 4. 解除营业锁定
        _unlock_business(session, eod_status.branch_id)
        
        # 5. 删除会话锁定记录，避免唯一约束冲突
        session.query(EODSessionLock).filter(
            EODSessionLock.eod_status_id == eod_status.id
        ).delete(synchronize_session=False)
        
        return {
            'success': True, 
            'message': '日结已完全取消，营业锁定已解除',
            'eod_id': eod_status.id,
            'new_status': 'cancelled',
            'cancel_type': 'simple'
        }
        
    except Exception as e:
        raise e


def _smart_cancel_after_cash_out(session, eod_status, current_user, reason):
    """第7步后的智能取消 - 恢复交款前状态"""
    try:
        # 1. 恢复交款前的余额状态
        cash_out_records = session.query(EODCashOut).filter_by(eod_status_id=eod_status.id).all()
        
        for cash_out_record in cash_out_records:
            # 获取交款流水记录
            transaction = session.query(ExchangeTransaction).filter_by(id=cash_out_record.transaction_id).first()
            if transaction:
                # 恢复余额：将交款金额加回余额表
                balance = session.query(CurrencyBalance).filter_by(
                    branch_id=eod_status.branch_id,
                    currency_id=cash_out_record.currency_id
                ).first()
                
                if balance:
                    # 恢复交款前的余额
                    restored_balance = float(balance.balance) + float(cash_out_record.cash_out_amount)
                    balance.balance = restored_balance
                    balance.updated_at = datetime.now()
                    
                    # 记录余额恢复操作
                    LogService.log_business_operation(
                        'balance_restore',
                        f'恢复交款前余额: 币种ID {cash_out_record.currency_id}, 恢复金额 {cash_out_record.cash_out_amount}, 新余额 {restored_balance}',
                        current_user.get('id'),
                        eod_status.branch_id
                    )
                
                # 删除交款流水记录
                session.delete(transaction)
                
                # 记录删除操作
                LogService.log_business_operation(
                    'transaction_delete',
                    f'删除交款流水记录: {transaction.transaction_no}',
                    current_user.get('id'),
                    eod_status.branch_id
                )
            
            # 删除交款记录
            session.delete(cash_out_record)
        
        # 2. 恢复EODBalanceVerification表的actual_balance为交款前状态
        # 获取交款前的余额快照（从EODBalanceVerification表）
        verifications = session.query(EODBalanceVerification).filter_by(eod_status_id=eod_status.id).all()
        
        # 先保存交款记录信息，因为后面会删除
        cash_out_info = {}
        for cash_out_record in cash_out_records:
            cash_out_info[cash_out_record.currency_id] = float(cash_out_record.cash_out_amount)
        
        for verification in verifications:
            # 检查是否有对应的交款记录
            if verification.currency_id in cash_out_info:
                # 恢复交款前的实际余额
                verification.actual_balance = float(verification.actual_balance) + cash_out_info[verification.currency_id]
                verification.verified_at = datetime.now()
        
        # 3. 删除PDF文件
        _delete_eod_pdf_files(eod_status, current_user)
        
        # 4. 删除相关数据记录
        _delete_eod_data_records(session, eod_status.id, eod_status)
        
        # 5. 更新日结状态 - 回滚到第6步（交款前）
        eod_status.status = 'processing'  # 保持处理中状态
        eod_status.step = 6  # 回滚到第6步
        eod_status.step_status = 'pending'  # 重置步骤状态
        eod_status.completed_at = None
        eod_status.completed_by = None
        
        # 6. 保持营业锁定（因为还在日结流程中）
        # 不解除锁定，因为用户可能要继续日结
        
        return {
            'success': True, 
            'message': '日结已智能取消，交款状态已恢复，可重新进行交款操作',
            'eod_id': eod_status.id,
            'new_status': 'processing',
            'current_step': 6,
            'cancel_type': 'smart',
            'restored_cash_out_count': len(cash_out_records)
        }
        
    except Exception as e:
        raise e


def _delete_eod_pdf_files(eod_status, current_user):
    """删除日结PDF文件"""
    try:
        pdf_files = glob.glob(f"receipts/**/A{eod_status.branch_id:03d}{eod_status.date.strftime('%Y%m%d')}*.pdf", recursive=True)
        for pdf_file in pdf_files:
            if os.path.exists(pdf_file):
                os.remove(pdf_file)
                LogService.log_business_operation(
                    'file_delete',
                    f'删除日结PDF文件: {pdf_file}',
                    current_user.get('id'),
                    eod_status.branch_id
                )
    except Exception as e:
        LogService.log_error(
            f'删除PDF文件失败: {str(e)}',
            current_user.get('id'),
            eod_status.branch_id
        )


def _delete_eod_data_records(session, eod_id, eod_status):
    """删除日结相关数据记录"""
    # 删除日结报表
    session.query(DailyIncomeReport).filter_by(eod_id=eod_id).delete()
    session.query(DailyStockReport).filter_by(eod_id=eod_id).delete()
    
    # 删除余额调整记录（如果是本次日结产生的）
    session.query(ExchangeTransaction).filter(
        ExchangeTransaction.created_at >= eod_status.started_at,
        ExchangeTransaction.type == 'adjust_balance',
        ExchangeTransaction.remarks.like(f'%日结%{eod_id}%')
    ).delete(synchronize_session=False)


def _unlock_business(session, branch_id):
    """解除营业锁定"""
    branch = session.query(Branch).filter_by(id=branch_id).first()
    if branch:
        branch.is_locked = False
        branch.lock_reason = None
        branch.locked_at = None
        branch.locked_by = None

@eod_step_bp.route('/<int:eod_id>/rollback/<int:step_number>', methods=['POST'])
@token_required
@has_permission('end_of_day')
def rollback_step(current_user, eod_id, step_number):
    """回滚指定步骤 - 超级简化版，直接允许上一步"""
    try:
        data = request.get_json()
        reason = data.get('reason', '用户回滚步骤')
        
        # 【调试】记录接收到的参数
        logging.info(f"🔍 回退请求调试信息:")
        logging.info(f"  - EOD ID: {eod_id}")
        logging.info(f"  - 请求回退到步骤: {step_number}")
        logging.info(f"  - 原因: {reason}")
        
        db_service = DatabaseService()
        session = db_service.get_session()
        
        try:
            # 获取日结记录
            eod_status = session.query(EODStatus).filter_by(id=eod_id).first()
            if not eod_status:
                return jsonify({'success': False, 'message': '日结记录不存在'}), 404
            
            # 【调试】记录当前EOD状态
            logging.info(f"  - 当前EOD步骤: {eod_status.step}")
            logging.info(f"  - 当前EOD状态: {eod_status.status}")
            logging.info(f"  - 当前步骤状态: {eod_status.step_status}")
            
            # 检查网点权限
            if eod_status.branch_id != current_user['branch_id']:
                return jsonify({'success': False, 'message': '无权限回滚其他网点的日结'}), 403
            
            # 【统一回退规则】明确区分回退和取消的概念
            # 第7步后不允许步骤回退，因为已经完成交款操作
            # 如果需要修改，应该使用"智能取消"功能
            if eod_status.step >= 7:
                return jsonify({
                    'success': False, 
                    'message': '第7步后不允许步骤回退，因为已经完成交款操作。如需修改，请使用"取消日结"功能进行智能取消。',
                    'suggestion': 'use_cancel_instead'
                }), 400
            
            # 验证步骤号范围：只能回退到1-6步
            if step_number < 1 or step_number > 6:
                return jsonify({
                    'success': False, 
                    'message': f'无效的步骤号: {step_number}。步骤回退只能到1-6步。'
                }), 400
            
            # 验证回退方向：只能回退到当前步骤之前的步骤
            if step_number >= eod_status.step:
                logging.error(f"❌ 回退验证失败: 请求回退到步骤{step_number}，当前步骤为{eod_status.step}")
                return jsonify({
                    'success': False, 
                    'message': f'无法回退到步骤 {step_number}，当前步骤为 {eod_status.step}。只能回退到更早的步骤（1-{eod_status.step-1}）。'
                }), 400
            
            # 记录回滚操作
            LogService.log_business_operation(
                'eod_rollback',
                f'用户回滚日结步骤: {eod_id}, 从步骤{eod_status.step}回滚到步骤{step_number}, 原因: {reason}',
                current_user.get('id'),
                eod_status.branch_id
            )
            
            # 直接更新日结状态 - 不做任何复杂的清理
            eod_status.step = step_number
            eod_status.step_status = 'pending'
            
            db_service.commit_session(session)
            
            # 记录日结回滚操作日志
            try:
                current_language = get_current_language()
                from services.unified_log_service import log_eod_operation
                log_eod_operation(
                    operator_id=current_user['id'],
                    branch_id=current_user['branch_id'],
                    eod_action='rollback',
                    eod_date=str(eod_status.date),
                    ip_address=request.remote_addr,
                    eod_id=str(eod_id),  # 添加日结批次号
                    details=f'从步骤{eod_status.step}回滚到步骤{step_number}，原因: {reason}',
                    language=current_language  # 使用当前用户的语言设置
                )
            except Exception as log_error:
                # 日志记录失败不应该影响日结回滚流程
                print(f"日结回滚操作日志记录失败: {log_error}")
            
            # 【修复】获取当前语言并翻译消息
            current_language = get_current_language()
            try:
                from utils.i18n_utils import I18nUtils
                translated_message = I18nUtils.get_message('eod.step_rollback_success', current_language, {'step': step_number})
            except Exception as translate_error:
                # 如果翻译失败，使用默认消息
                logging.warning(f"翻译失败: {translate_error}")
                translated_message = f'已成功回退到步骤 {step_number}'
            
            return jsonify(
                {
                    'success': True,
                    'message': translated_message,
                    'current_step': step_number,
                    'new_step': step_number,
                    'eod_id': eod_id
                }
            ), 200
            
        except Exception as e:
            db_service.rollback_session(session)
            logging.error(f"回滚步骤失败: {str(e)}")
            return jsonify({'success': False, 'message': f'回滚步骤失败: {str(e)}'}), 500
        finally:
            db_service.close_session(session)
            
    except Exception as e:
        logging.error(f"回滚步骤异常: {str(e)}")
        return jsonify({'success': False, 'message': f'回滚步骤异常: {str(e)}'}), 500

@eod_step_bp.route('/<int:eod_id>/income/currency/<currency_code>/transactions', methods=['GET'])
@token_required
@has_permission('end_of_day')
def get_eod_currency_transactions(current_user, eod_id, currency_code):
    """获取日结收入统计中特定币种的交易明细"""
    try:
        db_service = DatabaseService()
        session = db_service.get_session()
        
        try:
            # 获取日结记录
            eod_status = session.query(EODStatus).filter_by(id=eod_id).first()
            if not eod_status:
                return jsonify({'success': False, 'message': '日结记录不存在'}), 404
            
            # 权限检查：只能查看自己网点的日结
            if eod_status.branch_id != current_user.get('branch_id'):
                return jsonify({'success': False, 'message': '无权访问其他网点的日结数据'}), 403
            
            # 【修复】使用与收入统计相同的时间范围
            from config.features import FeatureFlags
            
            # 获取日结使用的业务时间范围
            if FeatureFlags.FEATURE_NEW_BUSINESS_TIME_RANGE:
                if eod_status.business_start_time and eod_status.business_end_time:
                    start_time = eod_status.business_start_time
                    end_time = eod_status.business_end_time
                else:
                    # 如果新字段为空，回退到旧逻辑
                    start_time = datetime.combine(eod_status.date, datetime.min.time())
                    end_time = datetime.now()
            else:
                # 使用旧的时间范围逻辑
                completed_eod_today = session.query(EODStatus).filter(
                    EODStatus.branch_id == eod_status.branch_id,
                    EODStatus.date == eod_status.date,
                    EODStatus.status == 'completed'
                ).order_by(EODStatus.completed_at.desc()).first()
                
                if completed_eod_today:
                    start_time = completed_eod_today.completed_at
                else:
                    start_time = datetime.combine(eod_status.date, datetime.min.time())
                
                end_time = datetime.now()
            
            # 获取币种信息
            currency = session.query(Currency).filter(
                Currency.currency_code == currency_code
            ).first()
            
            if not currency:
                return jsonify({'success': False, 'message': f'币种代码 {currency_code} 不存在'}), 404
            
            # 【修复】查询特定币种的交易明细 - 使用与CalGain相同的查询条件
            transactions = session.query(ExchangeTransaction).filter(
                ExchangeTransaction.branch_id == eod_status.branch_id,
                ExchangeTransaction.currency_id == currency.id,
                ExchangeTransaction.type.in_(['buy', 'sell', 'adjust_balance', 'reversal']),  # 【修复】包含adjust_balance
                ExchangeTransaction.status != 'reversed',  # 【修复】排除被冲正的交易
                ExchangeTransaction.created_at >= start_time,
                ExchangeTransaction.created_at < end_time  # 【修复】使用小于而不是小于等于
            ).order_by(ExchangeTransaction.created_at.desc()).all()
            
            # 转换为字典格式
            transaction_list = []
            for tx in transactions:
                transaction_list.append({
                    'transaction_no': tx.transaction_no,
                    'type': tx.type,
                    'currency_code': currency_code,
                    'amount': float(tx.amount),
                    'rate': float(tx.rate),
                    'local_amount': float(tx.local_amount),
                    'customer_name': tx.customer_name,
                    'created_at': tx.created_at.isoformat(),
                    'operator': tx.operator.name if tx.operator else '未知操作员'
                })
            
            return jsonify({
                'success': True,
                'data': {
                    'eod_id': eod_id,
                    'currency_code': currency_code,
                    'transactions': transaction_list,
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'total_count': len(transaction_list)
                }
            })
            
        finally:
            db_service.close_session(session)
            
    except Exception as e:
        LogService.log_error(
            f'获取日结币种交易明细失败: {str(e)}',
            current_user.get('id'),
            current_user.get('branch_id')
        )
        return jsonify({'success': False, 'message': f'获取交易明细失败: {str(e)}'}), 500
