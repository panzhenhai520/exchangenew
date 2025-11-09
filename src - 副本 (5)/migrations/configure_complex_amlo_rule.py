#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置复杂组合条件的AMLO触发规则（用于测试）
测试多字段AND/OR组合逻辑
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
import json

def configure_complex_rule():
    """配置复杂组合条件规则"""
    session = DatabaseService.get_session()
    
    print("="*80)
    print("配置复杂组合条件AMLO触发规则")
    print("="*80)
    
    try:
        # 复杂规则：AMLO-1-01高风险组合
        # 条件：(金额 >= 100万 AND 年龄 >= 65) OR (金额 >= 150万 AND 现金交易)
        
        complex_rule = {
            'report_type': 'AMLO-1-01',
            'rule_name': 'AMLO-1-01高风险组合',
            'rule_name_en': 'AMLO-1-01 High Risk Combination',
            'rule_name_th': 'AMLO-1-01 รายการเสี่ยงสูง',
            'rule_expression': json.dumps({
                "logic": "OR",
                "conditions": [
                    {
                        "logic": "AND",
                        "conditions": [
                            {"field": "total_amount", "operator": ">=", "value": 1000000},
                            {"field": "customer_age", "operator": ">=", "value": 65}
                        ]
                    },
                    {
                        "logic": "AND",
                        "conditions": [
                            {"field": "total_amount", "operator": ">=", "value": 1500000},
                            {"field": "payment_method", "operator": "==", "value": "cash"}
                        ]
                    }
                ]
            }),
            'priority': 110,  # 高于标准规则
            'is_active': True,
            'allow_continue': False,
            'warning_message_cn': '高风险交易组合：老年客户大额交易或超大额现金交易',
            'warning_message_en': 'High risk combination: Elderly customer large transaction or very large cash transaction',
            'warning_message_th': 'รายการเสี่ยงสูง: ผู้สูงอายุทำรายการใหญ่หรือเงินสดจำนวนมาก'
        }
        
        print("\n[1] 插入复杂组合条件规则...")
        print(f"\n规则详情:")
        print(f"  名称: {complex_rule['rule_name']}")
        print(f"  类型: {complex_rule['report_type']}")
        print(f"  优先级: {complex_rule['priority']}")
        print(f"\n组合逻辑:")
        print(f"  外层逻辑: OR")
        print(f"  分支1: (金额 >= 100万 AND 年龄 >= 65)")
        print(f"  分支2: (金额 >= 150万 AND 支付方式 = 现金)")
        
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
        
        session.execute(sql, complex_rule)
        session.commit()
        
        print(f"\n  [OK] 规则插入成功")
        
        # 添加测试所需的字段定义
        print("\n[2] 添加测试字段定义...")
        
        test_fields = [
            {
                'report_type': 'AMLO-1-01',
                'field_name': 'customer_age',
                'field_cn_name': '客户年龄',
                'field_en_name': 'Customer Age',
                'field_th_name': 'อายุลูกค้า',
                'field_type': 'INT',
                'is_required': False,
                'fill_order': 10,
                'field_group': '客户信息'
            },
            {
                'report_type': 'AMLO-1-01',
                'field_name': 'payment_method',
                'field_cn_name': '支付方式',
                'field_en_name': 'Payment Method',
                'field_th_name': 'วิธีชำระเงิน',
                'field_type': 'ENUM',
                'field_options': json.dumps(['cash', 'transfer', 'card']),
                'is_required': False,
                'fill_order': 11,
                'field_group': '交易信息'
            }
        ]
        
        for field in test_fields:
            # 检查字段是否已存在
            check_sql = text("""
                SELECT id FROM report_fields
                WHERE report_type = :report_type
                AND field_name = :field_name
            """)
            
            exists = session.execute(check_sql, {
                'report_type': field['report_type'],
                'field_name': field['field_name']
            }).fetchone()
            
            if exists:
                print(f"  字段 {field['field_name']} 已存在，跳过")
                continue
            
            # 插入字段
            field_sql = text("""
                INSERT INTO report_fields (
                    report_type, field_name, 
                    field_cn_name, field_en_name, field_th_name,
                    field_type, field_options, is_required, fill_order, field_group,
                    created_at
                ) VALUES (
                    :report_type, :field_name,
                    :field_cn_name, :field_en_name, :field_th_name,
                    :field_type, :field_options, :is_required, :fill_order, :field_group,
                    NOW()
                )
            """)
            
            params = field.copy()
            if 'field_options' not in params:
                params['field_options'] = None
            
            session.execute(field_sql, params)
            print(f"  [OK] 字段 {field['field_name']} 已添加")
        
        session.commit()
        
        print("\n" + "="*80)
        print("[OK] 复杂组合条件配置完成!")
        print("="*80)
        
        print("\n测试用例:")
        print("\n  用例A: 触发分支1（老年客户大额）")
        print("    客户年龄: 70岁")
        print("    交易金额: 110万THB")
        print("    预期: 触发 AMLO-1-01高风险组合")
        
        print("\n  用例B: 触发分支2（超大额现金）")
        print("    支付方式: 现金")
        print("    交易金额: 160万THB")
        print("    预期: 触发 AMLO-1-01高风险组合")
        
        print("\n  用例C: 不触发")
        print("    客户年龄: 30岁")
        print("    交易金额: 110万THB")
        print("    支付方式: 转账")
        print("    预期: 不触发（两个分支条件都不满足）")
        
        print("\n运行测试:")
        print("  python tests/test_complex_rule.py")
        
    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] 配置失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        DatabaseService.close_session(session)

if __name__ == "__main__":
    configure_complex_rule()

