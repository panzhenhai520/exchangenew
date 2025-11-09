# -*- coding: utf-8 -*-
"""
修正AMLO触发规则阈值，使其符合监管要求
根据 D:\Code\ExchangeNew\Re\AMLO和BOT监管要求.txt 文档
"""

from services.db_service import SessionLocal
from sqlalchemy import text
import json

def fix_amlo_trigger_thresholds():
    """
    修正AMLO触发规则阈值

    监管要求:
    - AMLO-1-01 (CTR): 金额 >= 5,000,000 THB
    - AMLO-1-02 (ATR): 金额 >= 8,000,000 THB + 涉及资产抵押兑换
    - AMLO-1-03 (STR): 可疑交易（基于历史、频率、资金来源等）
    """
    session = SessionLocal()

    try:
        print("=" * 80)
        print("修正AMLO触发规则阈值")
        print("=" * 80)

        # 1. 更新AMLO-1-01规则13 - 标准大额现金交易
        print("\n[1/4] 更新AMLO-1-01规则13（标准大额现金交易）")
        print("  从: total_amount >= 2,000,000")
        print("  到: total_amount >= 5,000,000")

        new_expression_13 = json.dumps({
            "logic": "AND",
            "conditions": [
                {
                    "field": "total_amount",
                    "operator": ">=",
                    "value": 5000000
                }
            ]
        })

        sql_13 = text("""
            UPDATE trigger_rules
            SET rule_expression = :expression,
                updated_at = NOW()
            WHERE id = 13
        """)
        session.execute(sql_13, {'expression': new_expression_13})
        print("  [OK] 已更新规则13")

        # 2. 更新AMLO-1-01规则16 - 高风险条件（保持不变，这是附加风险规则）
        print("\n[2/4] 检查AMLO-1-01规则16（高风险条件）")
        print("  规则16是附加高风险规则，保持当前配置:")
        print("  - 金额 >= 1,000,000 且 客户年龄 >= 65")
        print("  - 金额 >= 1,500,000 且 现金支付")
        print("  [OK] 规则16不需要修改")

        # 3. 更新AMLO-1-02规则14 - 资产交易报告
        print("\n[3/4] 更新AMLO-1-02规则14（资产交易报告）")
        print("  从: total_amount >= 50,000 AND suspicious_flag == 1")
        print("  到: total_amount >= 8,000,000 AND exchange_type == 'asset_mortgage'")

        new_expression_14 = json.dumps({
            "logic": "AND",
            "conditions": [
                {
                    "field": "total_amount",
                    "operator": ">=",
                    "value": 8000000
                },
                {
                    "field": "exchange_type",
                    "operator": "==",
                    "value": "asset_mortgage"
                }
            ]
        })

        sql_14 = text("""
            UPDATE trigger_rules
            SET rule_expression = :expression,
                updated_at = NOW()
            WHERE id = 14
        """)
        session.execute(sql_14, {'expression': new_expression_14})
        print("  [OK] 已更新规则14")

        # 4. AMLO-1-03规则15 - 可疑交易（保持不变）
        print("\n[4/4] 检查AMLO-1-03规则15（可疑交易）")
        print("  当前配置: cumulative_amount_30d >= 5,000,000")
        print("  这是累计金额触发，符合可疑交易监测要求")
        print("  [OK] 规则15不需要修改")

        # 提交更改
        session.commit()

        print("\n" + "=" * 80)
        print("更新完成！")
        print("=" * 80)

        # 验证更新结果
        print("\n验证更新后的规则:")
        print("-" * 80)

        verify_sql = text("""
            SELECT id, rule_name, report_type, rule_expression, priority
            FROM trigger_rules
            WHERE id IN (13, 14, 15, 16)
            ORDER BY report_type, priority DESC
        """)

        results = session.execute(verify_sql).fetchall()
        for row in results:
            print(f"\n规则ID: {row[0]}")
            print(f"名称: {row[1]}")
            print(f"类型: {row[2]}")
            print(f"优先级: {row[4]}")
            expr = json.loads(row[3])
            print(f"表达式: {json.dumps(expr, indent=2, ensure_ascii=False)}")

        return True

    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] 更新失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        session.close()


if __name__ == '__main__':
    success = fix_amlo_trigger_thresholds()
    if success:
        print("\n[SUCCESS] AMLO触发规则阈值已成功更新")
        print("[SUCCESS] 现在测试: 6,494,000 THB应该会触发AMLO-1-01")
    else:
        print("\n[FAILED] 更新失败，请检查错误信息")
