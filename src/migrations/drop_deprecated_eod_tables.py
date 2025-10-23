#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
删除已废弃的EOD旧表
执行前提：确保已备份数据到 backup/ 目录
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

def drop_deprecated_tables():
    """
    删除已废弃的EOD旧表
    
    删除表：
    - eod_history
    - eod_balance_snapshot
    
    前提条件：
    1. 系统已稳定运行1-2个月
    2. 数据已备份到 backup/eod_old_tables_backup_*.json
    3. 所有功能使用新表（EODBalanceVerification）正常运行
    """
    session = DatabaseService.get_session()
    
    print("="*80)
    print("删除已废弃的EOD旧表")
    print("="*80)
    print()
    print("⚠️  警告：此操作将永久删除以下表及其数据：")
    print("  - eod_history")
    print("  - eod_balance_snapshot")
    print()
    print("前提条件检查：")
    print("  [?] 系统已稳定运行1-2个月？")
    print("  [?] 数据已备份到 backup/ 目录？")
    print("  [?] 所有功能使用新表正常运行？")
    print()
    
    # 确认操作
    confirm = input("确认删除旧表？请输入 'YES' 继续: ")
    if confirm != 'YES':
        print("\n操作已取消")
        return {'success': False, 'message': '用户取消操作'}
    
    try:
        print("\n开始删除旧表...")
        
        # 1. 检查表是否存在
        print("\n[1] 检查表是否存在...")
        result = session.execute(text("SHOW TABLES LIKE 'eod_balance_snapshot'"))
        snapshot_exists = result.fetchone() is not None
        
        result = session.execute(text("SHOW TABLES LIKE 'eod_history'"))
        history_exists = result.fetchone() is not None
        
        if not snapshot_exists and not history_exists:
            print("  ✓ 旧表不存在，无需删除")
            return {'success': True, 'message': '旧表不存在'}
        
        # 2. 统计数据量
        print("\n[2] 统计数据量...")
        if snapshot_exists:
            result = session.execute(text("SELECT COUNT(*) FROM eod_balance_snapshot"))
            snapshot_count = result.scalar()
            print(f"  - eod_balance_snapshot: {snapshot_count} 条记录")
        
        if history_exists:
            result = session.execute(text("SELECT COUNT(*) FROM eod_history"))
            history_count = result.scalar()
            print(f"  - eod_history: {history_count} 条记录")
        
        # 3. 删除表（先删除子表，后删除父表）
        print("\n[3] 删除表...")
        
        if snapshot_exists:
            print("  - 删除 eod_balance_snapshot...")
            session.execute(text("DROP TABLE IF EXISTS eod_balance_snapshot"))
            print("    ✓ 已删除")
        
        if history_exists:
            print("  - 删除 eod_history...")
            session.execute(text("DROP TABLE IF EXISTS eod_history"))
            print("    ✓ 已删除")
        
        session.commit()
        
        print("\n" + "="*80)
        print("✅ 旧表删除成功！")
        print("="*80)
        print("\n后续建议：")
        print("  1. 验证系统功能正常运行")
        print("  2. 检查日志是否有异常")
        print("  3. 保留备份文件至少3个月")
        print()
        
        return {
            'success': True,
            'message': '旧表删除成功',
            'deleted_tables': ['eod_balance_snapshot', 'eod_history'] if snapshot_exists and history_exists else []
        }
        
    except Exception as e:
        session.rollback()
        print(f"\n✗ 错误：{e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'message': str(e)
        }
    finally:
        DatabaseService.close_session(session)

if __name__ == "__main__":
    result = drop_deprecated_tables()
    
    if not result['success']:
        sys.exit(1)

