#!/usr/bin/env python3
"""
检查AMLO/BOT触发条件
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from sqlalchemy import text

def check_trigger_conditions():
    session = DatabaseService.get_session()
    try:
        print("检查AMLO/BOT触发条件:")
        
        # 检查AMLO-1-01的触发规则
        amlo_rules = session.execute(text("""
            SELECT id, rule_name, rule_expression, description_cn, is_active
            FROM trigger_rules 
            WHERE report_type = 'AMLO-1-01' AND is_active = TRUE
            ORDER BY id
        """)).fetchall()
        
        print(f"\nAMLO-1-01触发规则数量: {len(amlo_rules)}")
        for rule in amlo_rules:
            print(f"规则 {rule[0]}: {rule[1]}")
            print(f"  表达式: {rule[2]}")
            print(f"  描述: {rule[3]}")
            print(f"  状态: {'启用' if rule[4] else '禁用'}")
        
        # 检查BOT触发规则
        bot_rules = session.execute(text("""
            SELECT DISTINCT report_type, COUNT(*) as rule_count
            FROM trigger_rules 
            WHERE report_type LIKE 'BOT%' AND is_active = TRUE
            GROUP BY report_type
            ORDER BY report_type
        """)).fetchall()
        
        print(f"\nBOT触发规则:")
        for rule in bot_rules:
            print(f"  {rule[0]}: {rule[1]} 条规则")
        
        # 检查用户交易金额是否满足触发条件
        transaction_amount = 161650000  # 用户交易金额 (THB)
        print(f"\n用户交易金额: {transaction_amount:,} THB")
        
        # 分析规则表达式中的阈值
        print("\n分析触发条件:")
        for rule in amlo_rules:
            print(f"规则 {rule[0]}: {rule[1]}")
            print(f"  表达式: {rule[2]}")
            
            # 尝试从表达式中提取阈值
            import re
            # 查找数字（可能是阈值）
            numbers = re.findall(r'\d+', rule[2])
            if numbers:
                print(f"  表达式中的数字: {numbers}")
                # 通常阈值是较大的数字
                large_numbers = [int(n) for n in numbers if int(n) > 1000]
                if large_numbers:
                    max_number = max(large_numbers)
                    print(f"  可能的阈值: {max_number:,}")
                    if transaction_amount >= max_number:
                        print(f"  ✅ 交易金额 {transaction_amount:,} >= 可能阈值 {max_number:,}，应该触发")
                    else:
                        print(f"  ❌ 交易金额 {transaction_amount:,} < 可能阈值 {max_number:,}，不会触发")
            print()
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    check_trigger_conditions()
