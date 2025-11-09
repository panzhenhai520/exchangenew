#!/usr/bin/env python3
"""
调试当前问题
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from sqlalchemy import text
import json

def check_issues():
    session = DatabaseService.get_session()
    try:
        print("="*60)
        print("调试当前问题")
        print("="*60)
        
        # 1. 检查国家数据
        print("\n1. 检查国家数据:")
        countries = session.execute(text("""
            SELECT country_code, country_name_zh, country_name_en, country_name_th 
            FROM countries 
            WHERE is_active = TRUE 
            LIMIT 10
        """)).fetchall()
        
        for c in countries:
            print(f"{c[0]}: 中文={c[1]}, 英文={c[2]}, 泰文={c[3] or 'NULL'}")
        
        # 2. 检查AMLO触发规则
        print("\n2. 检查AMLO触发规则:")
        rules = session.execute(text("""
            SELECT id, rule_name, rule_expression 
            FROM trigger_rules 
            WHERE report_type = 'AMLO-1-01' AND is_active = TRUE
        """)).fetchall()
        
        for r in rules:
            print(f"规则 {r[0]}: {r[1]}")
            try:
                expr = json.loads(r[2])
                print(f"表达式: {json.dumps(expr, ensure_ascii=False, indent=2)}")
            except:
                print(f"表达式: {r[2]}")
        
        # 3. 检查库存余额
        print("\n3. 检查库存余额:")
        balances = session.execute(text("""
            SELECT b.branch_name, c.currency_code, cb.balance
            FROM currency_balances cb
            JOIN branches b ON cb.branch_id = b.id
            JOIN currencies c ON cb.currency_id = c.id
            WHERE cb.balance < 0
        """)).fetchall()
        
        for b in balances:
            print(f"网点: {b[0]}, 币种: {b[1]}, 余额: {b[2]}")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    check_issues()
