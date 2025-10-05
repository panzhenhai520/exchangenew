#!/usr/bin/env python3
"""
简单调试脚本
"""

from services.db_service import create_db_engine
from sqlalchemy import text

def simple_debug():
    """简单调试"""
    try:
        engine = create_db_engine()
        with engine.connect() as conn:
            print("=== 简单调试信息 ===")
            
            # 检查BranchCurrency表是否存在数据
            print("\n1. BranchCurrency表数据:")
            result = conn.execute(text("SELECT COUNT(*) FROM branch_currencies"))
            count = result.fetchone()[0]
            print(f"  总记录数: {count}")
            
            if count > 0:
                result = conn.execute(text("""
                    SELECT branch_id, currency_id, is_enabled 
                    FROM branch_currencies 
                    ORDER BY branch_id, currency_id
                """))
                
                for row in result.fetchall():
                    branch_id, currency_id, is_enabled = row
                    print(f"  网点{branch_id} 币种{currency_id}: {'启用' if is_enabled else '禁用'}")
            
            # 检查禁用的币种
            print("\n2. 禁用的币种:")
            result = conn.execute(text("""
                SELECT branch_id, currency_id 
                FROM branch_currencies 
                WHERE is_enabled = 0
            """))
            
            disabled = result.fetchall()
            if disabled:
                for row in disabled:
                    branch_id, currency_id = row
                    print(f"  网点{branch_id} 币种{currency_id}: 禁用")
            else:
                print("  没有禁用的币种")
            
            # 检查今日汇率
            print("\n3. 今日汇率记录:")
            result = conn.execute(text("""
                SELECT branch_id, currency_id 
                FROM exchange_rates 
                WHERE rate_date = CURDATE()
                ORDER BY branch_id, currency_id
            """))
            
            today_rates = result.fetchall()
            if today_rates:
                for row in today_rates:
                    branch_id, currency_id = row
                    print(f"  网点{branch_id} 币种{currency_id}")
            else:
                print("  今日没有汇率记录")
                
    except Exception as e:
        print(f"调试过程中出现错误: {str(e)}")

if __name__ == "__main__":
    simple_debug() 