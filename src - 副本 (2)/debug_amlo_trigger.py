#!/usr/bin/env python3
"""
AMLO触发问题调试脚本
用于检查为什么大额交易没有触发AMLO预约表单
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from services.repform.rule_engine import RuleEngine
from models.report_models import TriggerRule
from sqlalchemy import text
import json

def check_amlo_trigger_rules():
    """检查AMLO触发规则配置"""
    session = DatabaseService.get_session()
    
    try:
        print("=== AMLO触发规则检查 ===")
        
        # 1. 检查AMLO触发规则
        print("\n1. 检查AMLO触发规则:")
        rules = session.execute(text("""
            SELECT 
                id,
                rule_name,
                report_type,
                rule_expression,
                description_cn,
                priority,
                allow_continue,
                warning_message_cn,
                is_active,
                branch_id
            FROM trigger_rules 
            WHERE report_type LIKE 'AMLO%' 
            AND is_active = TRUE
            ORDER BY report_type, priority DESC
        """)).fetchall()
        
        if rules:
            for rule in rules:
                print(f"\n  规则ID: {rule[0]}")
                print(f"  规则名称: {rule[1]}")
                print(f"  报告类型: {rule[2]}")
                print(f"  描述: {rule[4]}")
                print(f"  优先级: {rule[5]}")
                print(f"  允许继续: {rule[6]}")
                print(f"  警告消息: {rule[7]}")
                print(f"  是否启用: {rule[8]}")
                print(f"  网点ID: {rule[9]}")
                
                # 解析规则表达式
                try:
                    rule_expr = json.loads(rule[3])
                    print(f"  规则表达式: {json.dumps(rule_expr, indent=2, ensure_ascii=False)}")
                except Exception as e:
                    print(f"  规则表达式解析失败: {e}")
                    print(f"  原始表达式: {rule[3]}")
        else:
            print("  ❌ 没有找到启用的AMLO触发规则")
        
        # 2. 测试触发条件
        print("\n2. 测试触发条件:")
        
        # 模拟大额交易数据
        test_data = {
            'total_amount': 8926244.00,  # 用户提到的大额交易
            'currency_code': 'THB',
            'customer_id': 'TEST1234567890123'
        }
        
        print(f"  测试数据: {test_data}")
        
        # 测试AMLO-1-01触发
        for rule in rules:
            if rule[2] == 'AMLO-1-01':
                print(f"\n  测试规则: {rule[1]} (ID: {rule[0]})")
                try:
                    rule_expr = json.loads(rule[3])
                    triggered = RuleEngine.evaluate_rule(rule_expr, test_data)
                    print(f"  触发结果: {'✅ 触发' if triggered else '❌ 未触发'}")
                    
                    if triggered:
                        print(f"  允许继续: {rule[6]}")
                        print(f"  警告消息: {rule[7]}")
                except Exception as e:
                    print(f"  测试失败: {e}")
        
        # 3. 检查字段定义
        print("\n3. 检查报告字段定义:")
        fields = session.execute(text("""
            SELECT 
                field_name,
                field_label_zh,
                field_label_en,
                field_type,
                is_required,
                report_type
            FROM report_fields 
            WHERE report_type LIKE 'AMLO%'
            ORDER BY report_type, sort_order
        """)).fetchall()
        
        if fields:
            for field in fields:
                print(f"  {field[5]}: {field[0]} ({field[1]}) - {field[3]}")
        else:
            print("  ❌ 没有找到AMLO报告字段定义")
        
        # 4. 检查数据库连接
        print("\n4. 检查数据库连接:")
        try:
            result = session.execute(text("SELECT COUNT(*) FROM trigger_rules")).scalar()
            print(f"  ✅ 数据库连接正常，trigger_rules表有 {result} 条记录")
        except Exception as e:
            print(f"  ❌ 数据库连接失败: {e}")
        
    except Exception as e:
        print(f"检查过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        DatabaseService.close_session(session)

def create_test_amlo_rule():
    """创建测试AMLO规则"""
    session = DatabaseService.get_session()
    
    try:
        print("=== 创建测试AMLO规则 ===")
        
        # 检查是否已存在测试规则
        existing = session.execute(text("""
            SELECT COUNT(*) FROM trigger_rules 
            WHERE rule_name = '测试大额交易触发规则'
        """)).scalar()
        
        if existing > 0:
            print("测试规则已存在，跳过创建")
            return
        
        # 创建测试规则
        test_rule = {
            "logic": "AND",
            "conditions": [
                {
                    "field": "total_amount",
                    "operator": ">=",
                    "value": 2000000  # 200万泰铢
                },
                {
                    "field": "currency_code",
                    "operator": "=",
                    "value": "THB"
                }
            ]
        }
        
        session.execute(text("""
            INSERT INTO trigger_rules (
                rule_name,
                report_type,
                rule_expression,
                description_cn,
                description_en,
                description_th,
                priority,
                allow_continue,
                warning_message_cn,
                warning_message_en,
                warning_message_th,
                is_active,
                branch_id,
                created_at,
                updated_at
            ) VALUES (
                :rule_name,
                :report_type,
                :rule_expression,
                :description_cn,
                :description_en,
                :description_th,
                :priority,
                :allow_continue,
                :warning_message_cn,
                :warning_message_en,
                :warning_message_th,
                :is_active,
                :branch_id,
                NOW(),
                NOW()
            )
        """), {
            'rule_name': '测试大额交易触发规则',
            'report_type': 'AMLO-1-01',
            'rule_expression': json.dumps(test_rule),
            'description_cn': '测试规则：交易金额>=200万THB时触发AMLO-1-01报告',
            'description_en': 'Test rule: Trigger AMLO-1-01 when transaction amount >= 2M THB',
            'description_th': 'กฎทดสอบ: เรียก AMLO-1-01 เมื่อจำนวนเงิน >= 2M THB',
            'priority': 100,
            'allow_continue': False,
            'warning_message_cn': '交易金额超过200万泰铢，需要填写AMLO-1-01报告',
            'warning_message_en': 'Transaction amount exceeds 2M THB, AMLO-1-01 report required',
            'warning_message_th': 'จำนวนเงินเกิน 2M THB ต้องกรอกรายงาน AMLO-1-01',
            'is_active': True,
            'branch_id': None  # 全局规则
        })
        
        session.commit()
        print("✅ 测试AMLO规则创建成功")
        
    except Exception as e:
        session.rollback()
        print(f"创建测试规则失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        DatabaseService.close_session(session)

def test_trigger_api():
    """测试触发API"""
    import requests
    
    print("=== 测试触发API ===")
    
    # 模拟API调用
    test_data = {
        "report_type": "AMLO-1-01",
        "data": {
            "total_amount": 8926244.00,
            "currency_code": "THB",
            "customer_id": "TEST1234567890123"
        },
        "branch_id": 1
    }
    
    try:
        # 这里需要实际的token，暂时跳过
        print("API测试需要有效的认证token，请手动测试")
        print(f"测试数据: {json.dumps(test_data, indent=2)}")
        print("API端点: POST /api/repform/check-trigger")
        
    except Exception as e:
        print(f"API测试失败: {str(e)}")

if __name__ == "__main__":
    print("AMLO触发问题调试工具")
    print("1. 检查AMLO触发规则")
    print("2. 创建测试AMLO规则")
    print("3. 测试触发API")
    
    choice = input("请选择操作 (1/2/3): ")
    
    if choice == "1":
        check_amlo_trigger_rules()
    elif choice == "2":
        create_test_amlo_rule()
    elif choice == "3":
        test_trigger_api()
    else:
        print("无效选择")
