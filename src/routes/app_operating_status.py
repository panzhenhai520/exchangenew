#!/usr/bin/env python3
"""
营业状态管理API路由
包含：
- 清空营业数据功能
- 营业状态查询功能
- 状态控制功能
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, date
from services.auth_service import token_required, has_permission
from services.db_service import DatabaseService
from services.unified_log_service import UnifiedLogService
from models.exchange_models import (
    BranchOperatingStatus, Branch, Operator, ExchangeTransaction,
    EODStatus, 
    # EODHistory, EODBalanceSnapshot,  # 已废弃 - 2025-10-10
    EODBalanceVerification, EODPrintLog, EODCashOut, SystemLog,
    CurrencyBalance, OperatorActivityLog, TransactionAlert, 
    RatePublishRecord, RatePublishDetail, ReceiptSequence, ExchangeRate,
    EndOfDayReport, EODStepAction, EODSessionLock, Role
)

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_, text
import logging

# Get logger instance - DO NOT call basicConfig() here as it will override
# the logging configuration already set in main.py
logger = logging.getLogger('app_operating_status')

# Create blueprint for operating status operations
operating_status_bp = Blueprint('operating_status', __name__, url_prefix='/api/operating-status')

def clear_test_users_and_roles(session, current_user):
    """清理测试用户和角色"""
    try:
        # 保护的角色名称（不删除）
        protected_roles = ['系统管理员', '分行管理员', '窗口操作员']
        
        # 1. 删除除了admin之外的所有用户
        # 先删除用户相关的日志记录
        users_to_delete = session.query(Operator).filter(
            Operator.login_code != 'admin'
        ).all()
        
        deleted_users_count = 0
        for user in users_to_delete:
            # 删除用户的活动日志
            session.query(OperatorActivityLog).filter_by(operator_id=user.id).delete()
            # 删除用户的系统日志
            session.query(SystemLog).filter_by(operator_id=user.id).delete()
            # 删除用户创建的汇率记录
            session.query(ExchangeRate).filter_by(created_by=user.id).delete()
            # 删除用户相关的交易记录
            session.query(ExchangeTransaction).filter_by(operator_id=user.id).delete()
            # 删除用户相关的EOD状态记录
            session.query(EODStatus).filter_by(started_by=user.id).delete()
            session.query(EODStatus).filter_by(completed_by=user.id).delete()
            # 删除用户相关的EOD打印记录
            session.query(EODPrintLog).filter_by(printed_by=user.id).delete()
            # 删除用户相关的EOD现金记录
            session.query(EODCashOut).filter_by(cash_out_operator_id=user.id).delete()
            session.query(EODCashOut).filter_by(cash_receiver_id=user.id).delete()
            # 删除用户相关的汇率发布记录
            session.query(RatePublishRecord).filter_by(publisher_id=user.id).delete()
            # 删除用户相关的交易提醒
            session.query(TransactionAlert).filter_by(operator_id=user.id).delete()
            session.query(TransactionAlert).filter_by(resolved_by=user.id).delete()
            # 删除用户相关的营业状态记录
            session.query(BranchOperatingStatus).filter_by(initial_setup_by=user.id).delete()
            session.query(BranchOperatingStatus).filter_by(last_data_reset_by=user.id).delete()
            # 删除用户相关的EOD历史记录
            session.query(EODHistory).filter_by(operator_id=user.id).delete()
            # 删除用户相关的EOD会话锁
            session.query(EODSessionLock).filter_by(operator_id=user.id).delete()
            # 删除用户
            session.delete(user)
            deleted_users_count += 1
        
        # 2. 删除除了保护角色之外的所有角色
        roles_to_delete = session.query(Role).filter(
            ~Role.role_name.in_(protected_roles)
        ).all()
        
        deleted_roles_count = 0
        for role in roles_to_delete:
            # 删除角色权限关联
            session.execute(text("DELETE FROM role_permissions WHERE role_id = :role_id"), 
                          {'role_id': role.id})
            # 删除角色
            session.delete(role)
            deleted_roles_count += 1
        
        # 提交事务
        session.commit()
        
        # 记录清理日志
        log = SystemLog(
            operation='CLEAR_TEST_USERS_ROLES',
            operator_id=current_user['id'],
            log_type='system',
            action='清理测试用户和角色',
            details=f'删除用户: {deleted_users_count} 个, 删除角色: {deleted_roles_count} 个',
            ip_address=request.remote_addr
        )
        session.add(log)
        session.commit()
        
        logger.info(f"清理测试用户和角色完成: 删除用户 {deleted_users_count} 个, 删除角色 {deleted_roles_count} 个")
        
        return {
            'deleted_users': deleted_users_count,
            'deleted_roles': deleted_roles_count
        }
        
    except Exception as e:
        logger.error(f"清理测试用户和角色失败: {str(e)}")
        session.rollback()
        raise e

@operating_status_bp.route('/status/<int:branch_id>', methods=['GET'])
@token_required
@has_permission('system_manage')
def get_branch_operating_status(current_user, branch_id):
    """获取网点营业状态"""
    session = DatabaseService.get_session()
    try:
        # 检查权限：只有管理员或本网点用户可以查看
        if current_user['branch_id'] != branch_id and not current_user.get('is_admin', False):
            return jsonify({'success': False, 'message': '无权查看其他网点状态'}), 403
        
        # 获取营业状态
        branch_status = session.query(BranchOperatingStatus).filter_by(
            branch_id=branch_id
        ).first()
        
        if not branch_status:
            return jsonify({'success': False, 'message': '网点状态未找到'}), 404
        
        # 获取网点信息
        branch = session.query(Branch).filter_by(id=branch_id).first()
        if not branch:
            return jsonify({'success': False, 'message': '网点不存在'}), 404
        
        # 获取初始化操作员信息
        initial_operator = None
        if branch_status.initial_setup_by:
            initial_operator = session.query(Operator).filter_by(
                id=branch_status.initial_setup_by
            ).first()
        
        # 获取最后重置操作员信息
        last_reset_operator = None
        if branch_status.last_data_reset_by:
            last_reset_operator = session.query(Operator).filter_by(
                id=branch_status.last_data_reset_by
            ).first()
        
        # 统计营业数据
        total_transactions = session.query(ExchangeTransaction).filter(
            ExchangeTransaction.branch_id == branch_id,
            ExchangeTransaction.type.in_(['buy', 'sell'])
        ).count()
        
        # 余额调节记录已迁移到交易表
        total_adjustments = session.query(ExchangeTransaction).filter_by(
            branch_id=branch_id, type='adjust_balance'
        ).count()
        
        total_eod_reports = session.query(EODHistory).filter_by(
            branch_id=branch_id
        ).count()
        
        result = {
            'branch_id': branch_id,
            'branch_name': branch.branch_name,
            'branch_code': branch.branch_code,
            'status': branch_status.to_dict(),
            'initial_operator': initial_operator.name if initial_operator else None,
            'last_reset_operator': last_reset_operator.name if last_reset_operator else None,
            'statistics': {
                'total_transactions': total_transactions,
                'total_adjustments': total_adjustments,
                'total_eod_reports': total_eod_reports
            }
        }
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        logger.error(f"获取网点营业状态失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@operating_status_bp.route('/clear-data/<int:branch_id>', methods=['POST'])
@token_required
@has_permission('system_manage')
def clear_branch_operating_data(current_user, branch_id):
    """清空网点营业数据 - 危险操作，需要系统管理权限"""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': '缺少必要的参数'}), 400
    
    # 验证确认参数
    confirm_code = data.get('confirm_code')
    reason = data.get('reason', '')
    clear_test_users_roles = data.get('clear_test_users_roles', False)
    
    if confirm_code != 'www.59697.com':
        return jsonify({'success': False, 'message': '安全密码不正确'}), 400
    
    if not reason or len(reason.strip()) < 10:
        return jsonify({'success': False, 'message': '请提供详细的清空原因（至少10个字符）'}), 400
    
    session = DatabaseService.get_session()
    try:
        # 检查网点是否存在
        branch = session.query(Branch).filter_by(id=branch_id).first()
        if not branch:
            return jsonify({'success': False, 'message': '网点不存在'}), 404
        
        # 获取营业状态
        branch_status = session.query(BranchOperatingStatus).filter_by(
            branch_id=branch_id
        ).first()
        
        if not branch_status:
            return jsonify({'success': False, 'message': '网点状态未找到'}), 404
        
        # 检查是否有进行中的日结
        active_eod = session.query(EODStatus).filter(
            EODStatus.branch_id == branch_id,
            EODStatus.status.in_(['pending', 'processing']),
            EODStatus.is_locked == True
        ).first()
        
        if active_eod:
            return jsonify({
                'success': False, 
                'message': '当前有进行中的日结流程，无法清空数据'
            }), 400
        
        # 记录清空前的数据统计
        stats_before = {
            'transactions': session.query(ExchangeTransaction).filter_by(branch_id=branch_id).count(),
            'adjustments': session.query(ExchangeTransaction).filter_by(branch_id=branch_id, type='adjust_balance').count(),
            'currency_balances': session.query(CurrencyBalance).filter_by(branch_id=branch_id).count(),
            'eod_histories': session.query(EODHistory).filter_by(branch_id=branch_id).count(),
            'eod_statuses': session.query(EODStatus).filter_by(branch_id=branch_id).count(),
            'eod_reports': session.query(EndOfDayReport).filter_by(branch_id=branch_id).count(),
            'system_logs': session.query(SystemLog).join(Operator).filter(Operator.branch_id == branch_id).count(),
            'activity_logs': session.query(OperatorActivityLog).filter_by(branch_id=branch_id).count(),
            'transaction_alerts': session.query(TransactionAlert).filter_by(branch_id=branch_id).count(),
            'rate_publish_records': session.query(RatePublishRecord).filter_by(branch_id=branch_id).count(),
            'receipt_sequences': session.query(ReceiptSequence).filter_by(branch_id=branch_id).count()
        }
        
        # 展示访问日志表已删除
        stats_before['display_access_logs'] = 0
        
        # 尝试统计报表数据（如果表存在）
        try:
            from models.report_models import DailyIncomeReport, DailyForeignStock, DailyStockReport
            stats_before['daily_income_reports'] = session.query(DailyIncomeReport).filter_by(branch_id=branch_id).count()
            stats_before['daily_foreign_stock'] = session.query(DailyForeignStock).filter_by(branch_id=branch_id).count()
            stats_before['daily_stock_reports'] = session.query(DailyStockReport).filter_by(branch_id=branch_id).count()
        except Exception:
            stats_before['daily_income_reports'] = 0
            stats_before['daily_foreign_stock'] = 0
            stats_before['daily_stock_reports'] = 0
            logger.warning("报表模型不存在，跳过统计")
        
        logger.info(f"开始清空网点 {branch_id} 的营业数据，操作员: {current_user['id']}")
        logger.info(f"清空前统计: {stats_before}")
        
        # 开始清空数据（按依赖关系顺序）
        
        # 1. 删除日结相关数据 - 先获取ID再删除（SQLite兼容）
        
        # 获取该网点的EODStatus ID列表
        eod_status_ids = [row[0] for row in session.query(EODStatus.id).filter_by(branch_id=branch_id).all()]
        if eod_status_ids:
            # 删除EODPrintLog
            session.query(EODPrintLog).filter(EODPrintLog.eod_status_id.in_(eod_status_ids)).delete(synchronize_session=False)
            # 删除EODCashOut
            session.query(EODCashOut).filter(EODCashOut.eod_status_id.in_(eod_status_ids)).delete(synchronize_session=False)
            # 删除EODBalanceVerification
            session.query(EODBalanceVerification).filter(EODBalanceVerification.eod_status_id.in_(eod_status_ids)).delete(synchronize_session=False)
            # 删除EODStepAction
            session.query(EODStepAction).filter(EODStepAction.eod_status_id.in_(eod_status_ids)).delete(synchronize_session=False)
            # 删除EODSessionLock
            session.query(EODSessionLock).filter(EODSessionLock.eod_status_id.in_(eod_status_ids)).delete(synchronize_session=False)
        
        # 获取该网点的EODHistory ID列表
        eod_history_ids = [row[0] for row in session.query(EODHistory.id).filter_by(branch_id=branch_id).all()]
        if eod_history_ids:
            # 删除EODBalanceSnapshot
            session.query(EODBalanceSnapshot).filter(EODBalanceSnapshot.eod_history_id.in_(eod_history_ids)).delete(synchronize_session=False)
        
        # 删除EODHistory和EODStatus
        session.query(EODHistory).filter_by(branch_id=branch_id).delete()
        session.query(EODStatus).filter_by(branch_id=branch_id).delete()
        
        # 删除旧版日结报表
        session.query(EndOfDayReport).filter_by(branch_id=branch_id).delete()
        
        # 2. 删除交易记录
        session.query(ExchangeTransaction).filter_by(branch_id=branch_id).delete()
        
        # 3. 余额调节记录已迁移到交易表，不需要单独删除
        
        # 4. 删除汇率发布记录
        # 获取该网点的汇率发布记录ID列表
        rate_publish_ids = [row[0] for row in session.query(RatePublishRecord.id).filter_by(branch_id=branch_id).all()]
        if rate_publish_ids:
            # 删除汇率发布详情
            session.query(RatePublishDetail).filter(RatePublishDetail.publish_record_id.in_(rate_publish_ids)).delete(synchronize_session=False)
        # 删除汇率发布记录
        session.query(RatePublishRecord).filter_by(branch_id=branch_id).delete()
        
        # 5. 删除余额信息
        session.query(CurrencyBalance).filter_by(branch_id=branch_id).delete()
        
        # 6. 删除操作员活动日志
        session.query(OperatorActivityLog).filter_by(branch_id=branch_id).delete()
        
        # 7. 删除系统日志（仅删除该网点操作员的日志）
        operator_ids = [row[0] for row in session.query(Operator.id).filter_by(branch_id=branch_id).all()]
        if operator_ids:
            session.query(SystemLog).filter(SystemLog.operator_id.in_(operator_ids)).delete(synchronize_session=False)
        
        # 8. 删除交易报警
        session.query(TransactionAlert).filter_by(branch_id=branch_id).delete()
        
        # 9. 展示访问日志表已删除，跳过
        
        # 10. 重置票据序列
        session.query(ReceiptSequence).filter_by(branch_id=branch_id).delete()
        
        # 11. 删除报表数据（如果表存在）
        try:
            from models.report_models import DailyIncomeReport, DailyForeignStock, DailyStockReport
            session.query(DailyIncomeReport).filter_by(branch_id=branch_id).delete()
            session.query(DailyForeignStock).filter_by(branch_id=branch_id).delete()
            session.query(DailyStockReport).filter_by(branch_id=branch_id).delete()
            logger.info("成功删除报表数据")
        except Exception as e:
            logger.warning(f"跳过删除报表数据: {str(e)}")
        
        # 12. 重置汇率批量保存状态
        session.query(ExchangeRate).filter_by(branch_id=branch_id).update({
            'batch_saved': 0,
            'batch_saved_time': None,
            'batch_saved_by': None
        })
        
        # 13. 重置营业状态
        now = datetime.now()
        branch_status.is_initial_setup_completed = False
        branch_status.initial_setup_date = None
        branch_status.initial_setup_by = None
        branch_status.last_data_reset_date = now
        branch_status.last_data_reset_by = current_user['id']
        branch_status.data_reset_count += 1
        branch_status.operating_start_date = None
        branch_status.updated_at = now
        
        # 5. 记录系统日志
        log = SystemLog(
            operation='CLEAR_OPERATING_DATA',
            operator_id=current_user['id'],
            log_type='system',
            action='清空营业数据',
            details=f'网点ID: {branch_id}, 网点名称: {branch.branch_name}, 原因: {reason}, 清空前统计: {stats_before}',
            ip_address=request.remote_addr
        )
        session.add(log)
        
        session.commit()
        
        logger.info(f"成功清空网点 {branch_id} 的营业数据")
        
        # 清理测试用户和角色（如果选择）
        test_users_roles_cleared = None
        if clear_test_users_roles:
            test_users_roles_cleared = clear_test_users_and_roles(session, current_user)
            logger.info(f"清理测试用户和角色完成: {test_users_roles_cleared}")
        
        # 记录营业数据清理日志
        try:
            log_service = UnifiedLogService()
            log_service.log_business_data_cleanup(
                operator_id=current_user['operator_id'],
                operator_name=current_user.get('name', '未知用户'),
                cleanup_reason=reason,
                affected_records=sum(stats_before.values()),
                ip_address=request.remote_addr,
                branch_id=current_user['branch_id']
            )
        except Exception as log_error:
            # 日志记录失败不应该影响数据清理流程
            logger.info(f"营业数据清理日志记录失败: {log_error}")
        
        return jsonify({
            'success': True,
            'message': '营业数据清空成功',
            'cleared_data': stats_before,
            'reset_count': branch_status.data_reset_count,
            'test_users_roles_cleared': test_users_roles_cleared
        })
        
    except Exception as e:
        logger.error(f"清空营业数据失败: {str(e)}")
        session.rollback()
        return jsonify({'success': False, 'message': f'清空失败: {str(e)}'}), 500
    finally:
        DatabaseService.close_session(session)

@operating_status_bp.route('/reset-history/<int:branch_id>', methods=['GET'])
@token_required
@has_permission('system_manage')
def get_branch_reset_history(current_user, branch_id):
    """获取网点数据重置历史"""
    session = DatabaseService.get_session()
    try:
        # 检查权限
        if current_user['branch_id'] != branch_id and not current_user.get('is_admin', False):
            return jsonify({'success': False, 'message': '无权查看其他网点历史'}), 403
        
        # 获取重置历史（从系统日志中查询）
        reset_logs = session.query(SystemLog).join(
            Operator, SystemLog.operator_id == Operator.id
        ).filter(
            SystemLog.operation == 'CLEAR_OPERATING_DATA',
            SystemLog.details.like(f'网点ID: {branch_id},%')
        ).order_by(SystemLog.created_at.desc()).all()
        
        result = []
        for log in reset_logs:
            result.append({
                'id': log.id,
                'reset_date': log.created_at.isoformat(),
                'operator_name': log.operator.name,
                'operator_id': log.operator_id,
                'details': log.details,
                'ip_address': log.ip_address
            })
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        logger.error(f"获取重置历史失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@operating_status_bp.route('/check-clear-permission/<int:branch_id>', methods=['GET'])
@token_required
@has_permission('system_manage')
def check_clear_permission(current_user, branch_id):
    """检查清空数据权限和前置条件"""
    session = DatabaseService.get_session()
    try:
        # 检查网点是否存在
        branch = session.query(Branch).filter_by(id=branch_id).first()
        if not branch:
            return jsonify({'success': False, 'message': '网点不存在'}), 404
        
        # 检查或创建营业状态记录
        branch_status = session.query(BranchOperatingStatus).filter_by(
            branch_id=branch_id
        ).first()
        
        if not branch_status:
            # 如果不存在状态记录，自动创建一个
            logger.info(f"为网点 {branch_id} 创建营业状态记录")
            branch_status = BranchOperatingStatus(
                branch_id=branch_id,
                is_initial_setup_completed=False,
                data_reset_count=0
            )
            session.add(branch_status)
            session.commit()
            logger.info(f"网点 {branch_id} 营业状态记录创建成功")
        
        # 检查是否有进行中的日结
        active_eod = session.query(EODStatus).filter(
            EODStatus.branch_id == branch_id,
            EODStatus.status.in_(['pending', 'processing']),
            EODStatus.is_locked == True
        ).first()
        
        can_clear = not bool(active_eod)
        
        # 统计将要清空的数据
        data_stats = {
            'transactions': session.query(ExchangeTransaction).filter_by(branch_id=branch_id).count(),
            'adjustments': session.query(ExchangeTransaction).filter_by(branch_id=branch_id, type='adjust_balance').count(),
            'eod_reports': session.query(EODHistory).filter_by(branch_id=branch_id).count()
        }
        
        return jsonify({
            'success': True,
            'can_clear': can_clear,
            'blocking_reason': '存在进行中的日结流程' if active_eod else None,
            'data_stats': data_stats,
            'branch_name': branch.branch_name
        })
        
    except Exception as e:
        logger.error(f"检查清空权限失败: {str(e)}")
        logger.error(f"错误堆栈: ", exc_info=True)
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500
    finally:
        DatabaseService.close_session(session) 