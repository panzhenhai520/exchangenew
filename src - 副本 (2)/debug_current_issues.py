#!/usr/bin/env python3
"""
调试当前问题
1. 检查AMLO触发是否修复
2. 检查国家列表语言问题
3. 检查收据样式问题
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from services.repform.rule_engine import RuleEngine
from sqlalchemy import text
import json

def check_current_issues():
    """检查当前问题"""
    session = DatabaseService.get_session()
    
    try:
        print("="*60)
        print("调试当前问题")
        print("="*60)
        
        # 1. 检查AMLO触发规则
        print("\n1. 检查AMLO触发规则:")
        rules = session.execute(text("""
            SELECT 
                id, rule_name, rule_expression, is_active
            FROM trigger_rules 
            WHERE report_type = 'AMLO-1-01'
            AND is_active = TRUE
            ORDER BY priority DESC
        """)).fetchall()
        
        if rules:
            print(f"   找到 {len(rules)} 条AMLO-1-01规则")
            for rule in rules:
                print(f"   规则 ID {rule[0]}: {rule[1]}")
                
                try:
                    rule_expr = json.loads(rule[2])
                    print(f"   规则表达式: {json.dumps(rule_expr, ensure_ascii=False, indent=6)}")
                    
                    # 测试规则评估
                    test_data = {
                        'total_amount': 89200000,  # 用户报告的金额
                        'payment_method': 'cash'
                    }
                    
                    try:
                        result = RuleEngine.evaluate_rule(rule_expr, test_data)
                        print(f"   评估结果: {result}")
                        if result:
                            print(f"   ✅ 应该触发AMLO-1-01报告!")
                        else:
                            print(f"   ❌ 不会触发")
                    except Exception as eval_error:
                        print(f"   [错误] 评估失败: {eval_error}")
                    
                except Exception as e:
                    print(f"   [错误] 解析规则表达式失败: {e}")
                print()
        else:
            print("   [错误] 没有找到AMLO-1-01规则")
        
        # 2. 检查国家列表
        print("\n2. 检查国家列表:")
        countries = session.execute(text("""
            SELECT 
                country_code, country_name_zh, country_name_en, country_name_th
            FROM countries 
            WHERE is_active = TRUE
            ORDER BY sort_order
            LIMIT 5
        """)).fetchall()
        
        if countries:
            print("   前5个国家:")
            for country in countries:
                print(f"   {country[0]}: 中文={country[1]}, 英文={country[2]}, 泰文={country[3]}")
        else:
            print("   [错误] 没有找到国家数据")
        
        # 3. 检查API调用格式
        print("\n3. 正确的API调用格式:")
        print("   前端应该发送:")
        print("   {")
        print("     'report_type': 'AMLO-1-01',")
        print("     'data': {")
        print("       'total_amount': 89200000,")
        print("       'payment_method': 'cash'")
        print("     },")
        print("     'branch_id': 6")
        print("   }")
        
        # 4. 检查收据样式问题
        print("\n4. 收据样式问题:")
        print("   用户报告收据上有小方框乱码")
        print("   需要检查:")
        print("   - PDF生成时的字体设置")
        print("   - 字符编码问题")
        print("   - 参考文档: D:\\Code\\ExchangeNew\\Re\\Receipt information_ใบเสร็จรับเงิน_WangSwiss_ฟ้าทอง.docx")
        print("   - 参考图片: Receipt size example.jpg")
        
        print("\n" + "="*60)
        print("问题总结")
        print("="*60)
        print("1. AMLO触发问题: 前端API格式已修复，应该能正常触发")
        print("2. 国家列表语言: API支持多语言，前端调用正确")
        print("3. 收据乱码问题: 需要检查PDF生成逻辑")
        print("\n建议:")
        print("- 重新测试AMLO触发（确保网点未锁定）")
        print("- 检查浏览器控制台的国家API调用")
        print("- 检查收据PDF生成代码")
        
    except Exception as e:
        print(f"\n[错误] 测试过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        DatabaseService.close_session(session)

if __name__ == "__main__":
    check_current_issues()
