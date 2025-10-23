#!/usr/bin/env python3
"""
AMLO触发问题自动检查工具
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
        print("=== AMLO触发规则诊断报告 ===\n")
        
        # 1. 检查AMLO触发规则
        print("1. 检查AMLO触发规则:")
        rules = session.execute(text("""
            SELECT 
                id, rule_name, report_type, rule_expression, description_cn,
                priority, allow_continue, warning_message_cn, is_active, branch_id
            FROM trigger_rules 
            WHERE report_type LIKE 'AMLO%'
            AND is_active = TRUE
            ORDER BY report_type, priority DESC
        """)).fetchall()
        
        if rules:
            print(f"  找到 {len(rules)} 条启用的AMLO触发规则:\n")
            for rule in rules:
                print(f"  规则ID: {rule[0]}")
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
                print()
        else:
            print("  ❌ 没有找到启用的AMLO触发规则\n")
        
        # 2. 测试触发条件
        print("\n2. 测试触发条件:")
        
        # 模拟大额交易数据 - 用户提到的交易金额
        test_data = {
            'transaction_amount_thb': 8926244.00,  # 用户提到的大额交易
            'total_amount': 8926244.00,
            'currency_code': 'THB',
            'customer_id': 'TEST1234567890123',
            'transaction_type': 'exchange'
        }
        
        print(f"  测试数据: {json.dumps(test_data, indent=2, ensure_ascii=False)}\n")
        
        # 测试每个规则
        triggered_count = 0
        for rule in rules:
            print(f"  测试规则: {rule[1]} (ID: {rule[0]}, 类型: {rule[2]})")
            try:
                rule_expr = json.loads(rule[3])
                triggered = RuleEngine.evaluate_rule(rule_expr, test_data)
                print(f"  触发结果: {'[触发]' if triggered else '[未触发]'}")
                
                if triggered:
                    triggered_count += 1
                    print(f"  允许继续: {rule[6]}")
                    print(f"  警告消息: {rule[7]}")
            except Exception as e:
                print(f"  测试失败: {e}")
                import traceback
                traceback.print_exc()
            print()
        
        if triggered_count == 0:
            print("  [警告] 大额交易(8,926,244.00 THB)没有触发任何AMLO规则!")
            print("  可能的原因:")
            print("    1. 规则表达式中的字段名称不匹配（如使用了'total_amount'但实际应该是'transaction_amount_thb'）")
            print("    2. 阈值设置太高")
            print("    3. 规则条件不完整或有误")
        else:
            print(f"  [成功] 大额交易触发了 {triggered_count} 条AMLO规则")
        
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
            AND is_active = TRUE
            ORDER BY report_type, sort_order
        """)).fetchall()
        
        if fields:
            field_counts = {}
            for field in fields:
                report_type = field[5]
                field_counts[report_type] = field_counts.get(report_type, 0) + 1
            
            print(f"  找到 {len(fields)} 个AMLO报告字段:\n")
            for report_type, count in field_counts.items():
                print(f"    {report_type}: {count} 个字段")
            
            print("\n  前10个字段示例:")
            for field in fields[:10]:
                print(f"    {field[5]}: {field[0]} ({field[1]}) - {field[3]}, 必填: {field[4]}")
        else:
            print("  [错误] 没有找到AMLO报告字段定义")
        
        # 4. 检查数据库统计
        print("\n4. 数据库统计:")
        try:
            trigger_count = session.execute(text("SELECT COUNT(*) FROM trigger_rules")).scalar()
            field_count = session.execute(text("SELECT COUNT(*) FROM report_fields")).scalar()
            reservation_count = session.execute(text("SELECT COUNT(*) FROM Reserved_Transaction")).scalar()
            report_count = session.execute(text("SELECT COUNT(*) FROM AMLOReport")).scalar()
            
            print(f"  [正常] 数据库连接正常")
            print(f"    - trigger_rules表: {trigger_count} 条记录")
            print(f"    - report_fields表: {field_count} 条记录")
            print(f"    - Reserved_Transaction表: {reservation_count} 条记录")
            print(f"    - AMLOReport表: {report_count} 条记录")
        except Exception as e:
            print(f"  [错误] 数据库连接失败: {e}")
        
        # 5. 检查ExchangeView.vue中的触发逻辑
        print("\n5. 建议检查的前端代码:")
        print("  文件: src/views/ExchangeView.vue")
        print("  检查点:")
        print("    - handleConfirm() 方法中是否调用了 /api/repform/check-trigger")
        print("    - 传递给API的数据格式是否正确")
        print("    - 是否正确处理了API返回的触发结果")
        print("    - 是否显示了AMLO预约模态框")
        
        print("\n6. 建议检查的后端API:")
        print("  文件: src/routes/app_repform.py")
        print("  检查点:")
        print("    - /api/repform/check-trigger 端点是否正常工作")
        print("    - 是否正确调用了RuleEngine.check_triggers()")
        print("    - 是否返回了正确的触发结果")
        
        print("\n" + "="*50)
        print("诊断完成!")
        print("="*50)
        
    except Exception as e:
        print(f"检查过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        DatabaseService.close_session(session)

if __name__ == "__main__":
    check_amlo_trigger_rules()

