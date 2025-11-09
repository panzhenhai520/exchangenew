#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""备份旧EOD表数据"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from datetime import datetime
from services.db_service import DatabaseService
from sqlalchemy import text

def backup_old_tables():
    """备份 EODHistory 和 EODBalanceSnapshot 表的数据"""
    session = DatabaseService.get_session()
    
    backup_data = {
        'backup_time': datetime.now().isoformat(),
        'backup_reason': '简化日结功能前的数据备份',
        'eod_history': [],
        'eod_balance_snapshot': []
    }
    
    try:
        print("="*80)
        print("备份旧EOD表数据")
        print("="*80)
        
        # 备份 EODHistory
        print("\n[1] 备份 eod_history 表...")
        history_records = session.execute(text("""
            SELECT * FROM eod_history ORDER BY id
        """)).fetchall()
        
        for record in history_records:
            backup_data['eod_history'].append(dict(record._mapping))
        
        print(f"  ✓ 备份 {len(history_records)} 条记录")
        
        # 备份 EODBalanceSnapshot
        print("\n[2] 备份 eod_balance_snapshot 表...")
        snapshot_records = session.execute(text("""
            SELECT * FROM eod_balance_snapshot ORDER BY id
        """)).fetchall()
        
        for record in snapshot_records:
            backup_data['eod_balance_snapshot'].append(dict(record._mapping))
        
        print(f"  ✓ 备份 {len(snapshot_records)} 条记录")
        
        # 保存到JSON文件
        backup_dir = os.path.join(os.path.dirname(__file__), '..', 'backup')
        os.makedirs(backup_dir, exist_ok=True)
        
        backup_filename = f'eod_old_tables_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        backup_file = os.path.join(backup_dir, backup_filename)
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n[3] 保存备份文件...")
        print(f"  ✓ 文件: {backup_file}")
        print(f"  ✓ 大小: {os.path.getsize(backup_file)} 字节")
        
        print("\n" + "="*80)
        print("✅ 备份完成！")
        print("="*80)
        print(f"\n备份文件: {backup_filename}")
        print(f"EODHistory: {len(backup_data['eod_history'])} 条")
        print(f"EODBalanceSnapshot: {len(backup_data['eod_balance_snapshot'])} 条")
        print(f"\n如需恢复数据，请参考此JSON文件")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 备份失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()

if __name__ == "__main__":
    success = backup_old_tables()
    sys.exit(0 if success else 1)

