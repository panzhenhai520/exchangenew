"""
清理日结会话的工具函数
"""

from services.db_service import DatabaseService
from models.exchange_models import EODSessionLock, EODStatus
from datetime import datetime, timedelta
from services.log_service import LogService


def cleanup_current_branch_session(current_user):
    """
    清理当前网点的日结会话锁定
    """
    session = DatabaseService.get_session()
    
    try:
        branch_id = current_user.get('branch_id')
        if not branch_id:
            return {
                'success': False,
                'message': '无法获取网点信息'
            }
        
        # 查找当前网点的活跃会话锁定
        active_sessions = session.query(EODSessionLock).filter(
            EODSessionLock.branch_id == branch_id,
            EODSessionLock.is_active == True
        ).all()
        
        if not active_sessions:
            return {
                'success': True,
                'message': '当前网点没有活跃的日结会话锁定',
                'cleaned_count': 0
            }
        
        # 清理会话锁定
        cleaned_count = 0
        for session_lock in active_sessions:
            # 删除会话锁定记录，避免唯一约束冲突
            session.delete(session_lock)
            cleaned_count += 1
            
            # 记录日志
            LogService.log_system_event(
                f"清理日结会话锁定 - 会话ID: {session_lock.session_id}, 网点: {branch_id}",
                operator_id=current_user.get('id'),
                branch_id=branch_id
            )
        
        # 查找相关的processing状态的EOD并设置为cancelled
        processing_eods = session.query(EODStatus).filter(
            EODStatus.branch_id == branch_id,
            EODStatus.status == 'processing'
        ).all()
        
        cancelled_eods = 0
        for eod in processing_eods:
            eod.status = 'cancelled'
            eod.cancel_reason = '用户清理会话锁定'
            eod.is_locked = False
            eod.completed_at = datetime.now()
            eod.completed_by = current_user.get('id')
            cancelled_eods += 1
            
            # 记录日志
            LogService.log_system_event(
                f"清理时自动取消日结 - EOD ID: {eod.id}, 网点: {branch_id}",
                operator_id=current_user.get('id'),
                branch_id=branch_id
            )
        
        session.commit()
        
        message = f"成功清理了 {cleaned_count} 个会话锁定"
        if cancelled_eods > 0:
            message += f"，取消了 {cancelled_eods} 个进行中的日结"
        
        return {
            'success': True,
            'message': message,
            'cleaned_count': cleaned_count,
            'cancelled_eods': cancelled_eods
        }
        
    except Exception as e:
        session.rollback()
        LogService.log_error(f"清理日结会话失败: {str(e)}", operator_id=current_user.get('id'))
        return {
            'success': False,
            'message': f'清理日结会话失败: {str(e)}'
        }
    finally:
        DatabaseService.close_session(session)


def cleanup_expired_sessions_for_branch(branch_id, expire_hours=2):
    """
    清理指定网点的过期会话
    """
    session = DatabaseService.get_session()
    
    try:
        expire_time = datetime.now() - timedelta(hours=expire_hours)
        
        expired_sessions = session.query(EODSessionLock).filter(
            EODSessionLock.branch_id == branch_id,
            EODSessionLock.is_active == True,
            EODSessionLock.last_activity < expire_time
        ).all()
        
        count = 0
        for session_lock in expired_sessions:
            # 删除过期会话锁定记录，避免唯一约束冲突
            session.delete(session_lock)
            count += 1
        
        session.commit()
        
        return {
            'success': True,
            'message': f'清理了 {count} 个过期的会话锁定',
            'cleaned_count': count
        }
        
    except Exception as e:
        session.rollback()
        return {
            'success': False,
            'message': f'清理过期会话失败: {str(e)}'
        }
    finally:
        DatabaseService.close_session(session) 