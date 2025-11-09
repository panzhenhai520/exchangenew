#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查触发规则配置"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Windows UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from services.db_service import DatabaseService
from sqlalchemy import text

session = DatabaseService.get_session()

try:
    print("="*80)
    print("检查AMLO触发规则配置")
    print("="*80)
    
    # 查询AMLO规则
    result = session.execute(text("""
        SELECT 
            id, report_type, rule_name, 
            rule_expression, is_active, priority,
            allow_continue
        FROM trigger_rules
        WHERE report_type IN ('AMLO-1-01', 'AMLO-1-02', 'AMLO-1-03')
        ORDER BY report_type, priority
    """))
    
    rules = result.fetchall()
    
    if not rules:
        print("\n[WARN] 未找到AMLO触发规则！")
        print("\n需要先配置触发规则。")
    else:
        print(f"\n找到 {len(rules)} 条AMLO规则:\n")
        
        for rule in rules:
            print(f"[规则 {rule[0]}] {rule[1]}")
            print(f"  名称: {rule[2]}")
            print(f"  表达式: {rule[3]}")
            print(f"  启用: {'是' if rule[4] else '否'}")
            print(f"  优先级: {rule[5]}")
            print(f"  允许继续: {'是' if rule[6] else '否'}")
            print()
    
    print("="*80)
    
except Exception as e:
    print(f"[ERROR] 查询失败: {e}")
    import traceback
    traceback.print_exc()
finally:
    DatabaseService.close_session(session)

