"""
清理卡住的日结状态脚本
用于清理异常的日结状态和会话锁定
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from models.exchange_models import EODStatus, EODSessionLock
from datetime import datetime

def cleanup_stuck_eod(eod_id=None, branch_id=None, force=False):
    """
    清理卡住的日结状态
    
    Args:
        eod_id: 指定的EOD ID，如果None则清理所有processing状态的EOD
        branch_id: 指定的网点ID，如果None则清理所有网点
        force: 是否强制清理
    """
    session = DatabaseService.get_session()
    
    try:
        # 构建查询条件
        query = session.query(EODStatus).filter(
            EODStatus.status == 'processing'
        )
        
        if eod_id:
            query = query.filter(EODStatus.id == eod_id)
        
        if branch_id:
            query = query.filter(EODStatus.branch_id == branch_id)
        
        stuck_eods = query.all()
        
        if not stuck_eods:
            print("没有发现卡住的日结状态")
            return
        
        print(f"发现 {len(stuck_eods)} 个卡住的日结状态:")
        for eod in stuck_eods:
            print(f"  - EOD ID: {eod.id}, 网点: {eod.branch_id}, 日期: {eod.date}, 开始时间: {eod.started_at}")
        
        if not force:
            confirm = input("\n是否确认清理这些日结状态? (y/N): ").strip().lower()
            if confirm != 'y':
                print("取消清理操作")
                return
        
        # 清理操作
        cleaned_count = 0
        for eod in stuck_eods:
            try:
                print(f"\n清理 EOD ID: {eod.id}")
                
                # 1. 清理相关的会话锁定
                session_locks = session.query(EODSessionLock).filter(
                    EODSessionLock.eod_status_id == eod.id,
                    EODSessionLock.is_active == True
                ).all()
                
                for lock in session_locks:
                    # 删除会话锁定记录，避免唯一约束冲突
                    session.delete(lock)
                    print(f"  - 删除会话锁定: {lock.session_id}")
                
                # 2. 更新EOD状态
                eod.status = 'cancelled'
                eod.cancel_reason = '系统清理 - 卡住状态'
                eod.is_locked = False
                eod.completed_at = datetime.now()
                eod.completed_by = 0  # 系统操作
                
                print(f"  - 更新EOD状态为已取消")
                
                cleaned_count += 1
                
            except Exception as e:
                print(f"  - 清理 EOD ID {eod.id} 失败: {str(e)}")
                continue
        
        session.commit()
        print(f"\n✅ 成功清理了 {cleaned_count} 个日结状态")
        
    except Exception as e:
        session.rollback()
        print(f"❌ 清理失败: {str(e)}")
        raise
    finally:
        DatabaseService.close_session(session)

def cleanup_expired_sessions(expire_hours=2):
    """清理过期的会话锁定"""
    session = DatabaseService.get_session()
    
    try:
        from datetime import timedelta
        expire_time = datetime.now() - timedelta(hours=expire_hours)
        
        expired_sessions = session.query(EODSessionLock).filter(
            EODSessionLock.is_active == True,
            EODSessionLock.last_activity < expire_time
        ).all()
        
        if not expired_sessions:
            print("没有发现过期的会话锁定")
            return
        
        print(f"发现 {len(expired_sessions)} 个过期的会话锁定:")
        for session_lock in expired_sessions:
            print(f"  - 会话ID: {session_lock.session_id}, 网点: {session_lock.branch_id}, 最后活跃: {session_lock.last_activity}")
            # 删除过期会话锁定记录，避免唯一约束冲突
            session.delete(session_lock)
        
        session.commit()
        print(f"✅ 成功清理了 {len(expired_sessions)} 个过期会话锁定")
        
    except Exception as e:
        session.rollback()
        print(f"❌ 清理失败: {str(e)}")
        raise
    finally:
        DatabaseService.close_session(session)

def show_current_status():
    """显示当前日结和会话状态"""
    session = DatabaseService.get_session()
    
    try:
        # 查询进行中的日结
        processing_eods = session.query(EODStatus).filter(
            EODStatus.status == 'processing'
        ).all()
        
        print("📊 当前系统状态:")
        print(f"进行中的日结: {len(processing_eods)}")
        
        for eod in processing_eods:
            print(f"  - EOD ID: {eod.id}, 网点: {eod.branch_id}, 日期: {eod.date}")
            print(f"    开始时间: {eod.started_at}, 步骤: {eod.step}, 锁定: {eod.is_locked}")
        
        # 查询活跃的会话锁定
        active_sessions = session.query(EODSessionLock).filter(
            EODSessionLock.is_active == True
        ).all()
        
        print(f"\n活跃的会话锁定: {len(active_sessions)}")
        for session_lock in active_sessions:
            print(f"  - 会话ID: {session_lock.session_id}, 网点: {session_lock.branch_id}")
            print(f"    操作员: {session_lock.operator_id}, IP: {session_lock.ip_address}")
            print(f"    最后活跃: {session_lock.last_activity}")
        
    except Exception as e:
        print(f"❌ 查询状态失败: {str(e)}")
    finally:
        DatabaseService.close_session(session)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='清理卡住的日结状态')
    parser.add_argument('--eod-id', type=int, help='指定EOD ID')
    parser.add_argument('--branch-id', type=int, help='指定网点ID')
    parser.add_argument('--force', action='store_true', help='强制清理，不询问确认')
    parser.add_argument('--status', action='store_true', help='只显示当前状态，不清理')
    parser.add_argument('--cleanup-sessions', action='store_true', help='清理过期会话')
    parser.add_argument('--expire-hours', type=int, default=2, help='会话过期时间（小时）')
    
    args = parser.parse_args()
    
    if args.status:
        show_current_status()
    elif args.cleanup_sessions:
        cleanup_expired_sessions(args.expire_hours)
    else:
        cleanup_stuck_eod(args.eod_id, args.branch_id, args.force) 