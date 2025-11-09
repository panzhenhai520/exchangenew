#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时清理孤立的EOD会话锁定
建议：每小时执行一次
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from services.db_service import DatabaseService
from services.log_service import LogService
from models.exchange_models import EODSessionLock, EODStatus
from sqlalchemy import and_
import logging

logger = logging.getLogger(__name__)

def cleanup_stale_sessions():
    """
    清理过期的会话锁定记录
    
    规则：
    1. last_activity 超过2小时
    2. 且对应的 EOD 状态不是 processing
    3. 或者 EOD 仍在 processing 但会话超时 → 自动取消EOD
    
    返回：清理的记录数量
    """
    session = DatabaseService.get_session()
    try:
        stale_time = datetime.now() - timedelta(hours=2)
        
        # 查询过期的会话锁定（超过2小时无活动）
        stale_locks = session.query(EODSessionLock).filter(
            and_(
                EODSessionLock.is_active == True,
                EODSessionLock.last_activity < stale_time
            )
        ).all()
        
        cleaned_count = 0
        cancelled_eod_count = 0
        
        for lock in stale_locks:
            # 检查对应的EOD状态
            eod_status = session.query(EODStatus).filter_by(id=lock.eod_status_id).first()
            
            if not eod_status:
                # EOD记录不存在，删除孤立会话
                session.delete(lock)
                cleaned_count += 1
                logger.info(f"清理孤立会话锁定: session_id={lock.session_id}, EOD不存在")
                
            elif eod_status.status != 'processing':
                # EOD已完成或已取消，删除残留会话
                session.delete(lock)
                cleaned_count += 1
                logger.info(f"清理残留会话锁定: session_id={lock.session_id}, EOD状态={eod_status.status}")
                
            elif eod_status.status == 'processing':
                # EOD仍在处理中，但会话超时 → 自动取消EOD
                eod_status.status = 'cancelled'
                eod_status.cancel_reason = f'系统自动取消：会话超时（超过2小时无活动）'
                eod_status.is_locked = False
                eod_status.step_status = 'cancelled'
                eod_status.completed_at = datetime.now()
                
                session.delete(lock)
                cleaned_count += 1
                cancelled_eod_count += 1
                
                logger.warning(f"自动取消超时EOD: eod_id={eod_status.id}, branch_id={eod_status.branch_id}")
                
                LogService.log_system_event(
                    f"自动取消超时日结: EOD ID {eod_status.id}, 会话ID {lock.session_id}, 最后活动 {lock.last_activity}",
                    operator_id=lock.operator_id,
                    branch_id=eod_status.branch_id
                )
        
        session.commit()
        
        if cleaned_count > 0:
            logger.info(f"定时清理完成: 清理 {cleaned_count} 个孤立会话, 自动取消 {cancelled_eod_count} 个超时日结")
        
        return {
            'success': True,
            'cleaned_count': cleaned_count,
            'cancelled_eod_count': cancelled_eod_count,
            'message': f'清理完成: {cleaned_count}个会话, {cancelled_eod_count}个日结'
        }
        
    except Exception as e:
        session.rollback()
        logger.error(f"定时清理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'message': str(e),
            'cleaned_count': 0,
            'cancelled_eod_count': 0
        }
    finally:
        DatabaseService.close_session(session)

if __name__ == "__main__":
    print("="*80)
    print("清理孤立EOD会话锁定任务")
    print("="*80)
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"超时阈值: 2小时")
    print()
    
    result = cleanup_stale_sessions()
    
    if result['success']:
        print(f"✓ 清理完成")
        print(f"  清理会话数: {result['cleaned_count']}")
        print(f"  取消日结数: {result['cancelled_eod_count']}")
    else:
        print(f"✗ 清理失败: {result['message']}")
        sys.exit(1)

