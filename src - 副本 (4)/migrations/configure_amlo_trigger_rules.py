#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置标准的AMLO触发规则
按照泰国AMLO监管要求设置
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Windows UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from services.db_service import DatabaseService
from sqlalchemy import text
from datetime import datetime
import json

def configure_amlo_rules():
    """配置标准AMLO触发规则"""
    session = DatabaseService.get_session()
    
    print("="*80)
    print("配置AMLO标准触发规则")
    print("="*80)
    
    try:
        # 标准AMLO规则配置
        amlo_rules = [
            {
                'report_type': 'AMLO-1-01',
                'rule_name': 'AMLO-1-01单笔大额',
                'rule_name_en': 'AMLO-1-01 Large Single Transaction',
                'rule_name_th': 'AMLO-1-01 รายการขนาดใหญ่ครั้งเดียว',
                'rule_expression': json.dumps({
                    "logic": "AND",
                    "conditions": [{
                        "field": "total_amount",
                        "operator": ">=",
                        "value": 2000000  # 200万THB
                    }]
                }),
                'priority': 100,
                'is_active': True,
                'allow_continue': False,
                'warning_message_cn': '单笔交易金额超过200万泰铢，需要填写AMLO-1-01报告',
                'warning_message_en': 'Single transaction exceeds 2,000,000 THB, AMLO-1-01 report required',
                'warning_message_th': 'ธุรกรรมเดียวเกิน 2,000,000 บาท ต้องกรอกรายงาน AMLO-1-01'
            },
            {
                'report_type': 'AMLO-1-02',
                'rule_name': 'AMLO-1-02资产交易',
                'rule_name_en': 'AMLO-1-02 Asset Transaction',
                'rule_name_th': 'AMLO-1-02 รายการทรัพย์สิน',
                'rule_expression': json.dumps({
                    "logic": "AND",
                    "conditions": [
                        {
                            "field": "total_amount",
                            "operator": ">=",
                            "value": 8000000  # 800万THB
                        },
                        {
                            "field": "exchange_type",
                            "operator": "==",
                            "value": "asset_backed"  # 资产抵押兑换
                        }
                    ]
                }),
                'priority': 100,
                'is_active': True,
                'allow_continue': False,
                'warning_message_cn': '资产抵押兑换且金额超过800万泰铢，需要填写AMLO-1-02报告',
                'warning_message_en': 'Asset-backed exchange exceeding 8,000,000 THB, AMLO-1-02 report required',
                'warning_message_th': 'การแลกเปลี่ยนที่มีหลักประกันทรัพย์สินเกิน 8,000,000 บาท ต้องกรอกรายงาน AMLO-1-02'
            },
            {
                'report_type': 'AMLO-1-03',
                'rule_name': 'AMLO-1-03累计大额',
                'rule_name_en': 'AMLO-1-03 Cumulative Large Amount',
                'rule_name_th': 'AMLO-1-03 ยอดรวมขนาดใหญ่',
                'rule_expression': json.dumps({
                    "logic": "AND",
                    "conditions": [{
                        "field": "cumulative_amount_30d",
                        "operator": ">=",
                        "value": 5000000  # 500万THB
                    }]
                }),
                'priority': 100,
                'is_active': True,
                'allow_continue': False,
                'warning_message_cn': '30天累计交易金额超过500万泰铢，需要填写AMLO-1-03报告',
                'warning_message_en': '30-day cumulative exceeds 5,000,000 THB, AMLO-1-03 report required',
                'warning_message_th': 'ยอดรวม 30 วันเกิน 5,000,000 บาท ต้องกรอกรายงาน AMLO-1-03'
            }
        ]
        
        # 先删除旧的AMLO规则
        print("\n[1] 删除旧的AMLO规则...")
        deleted = session.execute(text("""
            DELETE FROM trigger_rules 
            WHERE report_type IN ('AMLO-1-01', 'AMLO-1-02', 'AMLO-1-03')
        """))
        session.commit()
        print(f"  [OK] 已删除 {deleted.rowcount} 条旧规则")
        
        # 插入新规则
        print("\n[2] 插入新的标准AMLO规则...")
        
        for i, rule in enumerate(amlo_rules, 1):
            sql = text("""
                INSERT INTO trigger_rules (
                    report_type, rule_name, rule_name_en, rule_name_th,
                    rule_expression, priority, is_active, allow_continue,
                    warning_message_cn, warning_message_en, warning_message_th,
                    created_at
                ) VALUES (
                    :report_type, :rule_name, :rule_name_en, :rule_name_th,
                    :rule_expression, :priority, :is_active, :allow_continue,
                    :warning_message_cn, :warning_message_en, :warning_message_th,
                    NOW()
                )
            """)
            
            session.execute(sql, rule)
            print(f"  [{i}] {rule['rule_name']} - [OK]")
        
        session.commit()
        
        print("\n" + "="*80)
        print("[OK] AMLO触发规则配置完成!")
        print("="*80)
        print("\n配置的规则:")
        print("  1. AMLO-1-01 (CTR-现金交易报告): 单笔 >= 200万THB")
        print("  2. AMLO-1-02 (ATR-资产交易报告): 金额 >= 800万THB AND 兑换类型 = 资产抵押")
        print("  3. AMLO-1-03 (STR-可疑交易报告): 30天累计 >= 500万THB")
        print("\n现在可以运行测试：")
        print("  python tests/amlo_direct_test.py")
        
    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] 配置失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        DatabaseService.close_session(session)

if __name__ == "__main__":
    configure_amlo_rules()

