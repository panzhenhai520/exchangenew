#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证EOD数据完整性 - 确保所有已完成的日结都有验证记录"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from sqlalchemy import text

def verify_data():
    """验证数据完整性"""
    session = DatabaseService.get_session()
    try:
        print("="*80)
        print("EOD数据完整性验证")
        print("="*80)
        
        # 查询所有已完成的日结
        completed_eods = session.execute(text("""
            SELECT id, branch_id, date, completed_at
            FROM eod_status
            WHERE status = 'completed'
            ORDER BY completed_at DESC
        """)).fetchall()
        
        print(f"\n已完成的日结记录: {len(completed_eods)} 条")
        print("-"*80)
        
        all_complete = True
        missing_verifications = []
        
        for eod in completed_eods:
            eod_id = eod[0]
            branch_id = eod[1]
            eod_date = eod[2]
            completed_at = eod[3]
            
            # 检查是否有对应的 EODBalanceVerification 记录
            verification_count = session.execute(text("""
                SELECT COUNT(*) 
                FROM eod_balance_verification
                WHERE eod_status_id = :eod_id
            """), {'eod_id': eod_id}).scalar()
            
            if verification_count == 0:
                missing_verifications.append({
                    'eod_id': eod_id,
                    'branch_id': branch_id,
                    'date': eod_date,
                    'completed_at': completed_at
                })
                print(f"  ⚠️ EOD {eod_id} (网点{branch_id}, 日期: {eod_date}) 缺少验证记录")
                all_complete = False
            else:
                print(f"  ✓ EOD {eod_id} (网点{branch_id}, 日期: {eod_date}) 有 {verification_count} 条验证记录")
        
        print("\n" + "="*80)
        if all_complete:
            print("✅ 数据验证通过！")
            print("="*80)
            print("\n所有已完成的日结都有完整的验证记录")
            print("可以安全地移除旧表逻辑")
            print("\n下次期初余额来源: EODBalanceVerification.actual_balance")
            return True
        else:
            print("⚠️ 数据验证失败！")
            print("="*80)
            print(f"\n发现 {len(missing_verifications)} 个日结缺少验证记录：")
            for missing in missing_verifications:
                print(f"  - EOD {missing['eod_id']} (网点{missing['branch_id']}, {missing['date']})")
            print("\n建议：")
            print("1. 检查这些日结是否正常完成")
            print("2. 如果异常，可以忽略（标记为已取消）")
            print("3. 如果正常，需要补充验证记录")
            return False
            
    except Exception as e:
        print(f"\n❌ 验证过程出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()

if __name__ == "__main__":
    success = verify_data()
    sys.exit(0 if success else 1)

