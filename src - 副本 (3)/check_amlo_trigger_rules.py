#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
查询AMLO触发规则
"""

import sys
import os
import io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure stdout/stderr encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from services.db_service import DatabaseService
from sqlalchemy import text

def check_amlo_trigger_rules():
    """查询AMLO触发规则"""
    print("=" * 80)
    print("AMLO触发规则查询")
    print("=" * 80)

    session = DatabaseService.get_session()
    try:
        # 查询所有AMLO触发规则
        query = text("""
            SELECT
                id,
                rule_name,
                report_type,
                condition_type,
                threshold_amount,
                threshold_currency,
                is_active,
                description
            FROM amlo_trigger_rules
            WHERE is_active = 1
            ORDER BY report_type, id
        """)

        rules = session.execute(query).fetchall()

        if not rules:
            print("\n❌ 数据库中没有AMLO触发规则")
            return

        print(f"\n找到 {len(rules)} 条激活的AMLO触发规则:\n")

        # 按report_type分组显示
        current_report_type = None

        for rule in rules:
            rule_id, rule_name, report_type, condition_type, threshold_amount, threshold_currency, is_active, description = rule

            if report_type != current_report_type:
                current_report_type = report_type
                print(f"\n{'='*80}")
                print(f"📋 {report_type}")
                print(f"{'='*80}")

            print(f"\n规则ID: {rule_id}")
            print(f"规则名称: {rule_name}")
            print(f"条件类型: {condition_type}")
            print(f"触发金额: {threshold_amount:,.2f} {threshold_currency}")
            print(f"说明: {description if description else '无'}")
            print(f"-" * 80)

        # 打印测试指南
        print("\n" + "="*80)
        print("🧪 测试指南")
        print("="*80)

        for rule in rules:
            rule_id, rule_name, report_type, condition_type, threshold_amount, threshold_currency, is_active, description = rule

            print(f"\n测试 {report_type}:")
            print(f"  条件: {condition_type}")
            print(f"  金额阈值: >= {threshold_amount:,.2f} {threshold_currency}")

            if condition_type == 'single_transaction':
                print(f"  测试方法: 执行单笔买入或卖出交易，金额 >= {threshold_amount:,.2f} {threshold_currency}")
            elif condition_type == 'daily_cumulative_buy':
                print(f"  测试方法: 当日累计买入金额 >= {threshold_amount:,.2f} {threshold_currency}")
            elif condition_type == 'daily_cumulative_sell':
                print(f"  测试方法: 当日累计卖出金额 >= {threshold_amount:,.2f} {threshold_currency}")
            elif condition_type == 'daily_cumulative_both':
                print(f"  测试方法: 当日累计买入+卖出金额 >= {threshold_amount:,.2f} {threshold_currency}")

            # 计算建议测试金额
            test_amount = threshold_amount * 1.1  # 超出阈值10%
            print(f"  建议测试金额: {test_amount:,.2f} {threshold_currency}")

            # 如果是THB，给出外币等值
            if threshold_currency == 'THB':
                # 假设汇率
                usd_rate = 34.0
                eur_rate = 38.0
                jpy_rate = 0.23

                print(f"  等值外币金额示例:")
                print(f"    USD: {test_amount / usd_rate:,.2f} (汇率 {usd_rate})")
                print(f"    EUR: {test_amount / eur_rate:,.2f} (汇率 {eur_rate})")
                print(f"    JPY: {test_amount / jpy_rate:,.0f} (汇率 {jpy_rate})")

    except Exception as e:
        print(f"\n❌ 查询失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        DatabaseService.close_session(session)

if __name__ == '__main__':
    check_amlo_trigger_rules()
