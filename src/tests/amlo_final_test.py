#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AMLO最终测试 - 使用正确的API调用方式
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Windows UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from services.db_service import DatabaseService
from services.repform.rule_engine import RuleEngine
from datetime import datetime

def main():
    print("="*80)
    print("AMLO触发测试（修复版）")
    print("="*80)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    session = DatabaseService.get_session()
    
    try:
        # 测试用例1: AMLO-1-01
        print("="*80)
        print("[用例1] AMLO-1-01 单笔大额交易 (60,000 USD = 2,130,000 THB)")
        print("="*80)
        
        test1_data = {
            'customer_id': '1234567890123',
            'customer_name': '张三',
            'total_amount': 2130000,  # 本币金额
            'amount': 60000,
            'currency_code': 'USD',
            'direction': 'buy',
            'branch_id': 1
        }
        
        print(f"测试数据: 买入 {test1_data['amount']:,} USD = {test1_data['total_amount']:,} THB")
        
        # 不指定report_type，让引擎检查所有类型
        from sqlalchemy import text
        
        # 手动查询并测试每个AMLO规则
        amlo_types = ['AMLO-1-01', 'AMLO-1-02', 'AMLO-1-03']
        
        for report_type in amlo_types:
            result = RuleEngine.check_triggers(session, report_type, test1_data, 1)
            
            if result.get('triggered'):
                print(f"\n[PASS] 触发 {report_type}:")
                for rule in result.get('triggered_reports', []):
                    print(f"  - 规则: {rule.get('rule_name', '')}")
                    print(f"    优先级: {rule.get('priority')}")
                    print(f"    允许继续: {'是' if rule.get('allow_continue') else '否'}")
        
        # 测试用例2: AMLO-1-03
        print("\n" + "="*80)
        print("[用例2] AMLO-1-03 累计大额交易 (30,000 USD + 历史410万 = 516.5万 THB)")
        print("="*80)
        
        test2_data = {
            'customer_id': 'TEST9876543210',
            'customer_name': '测试客户-张三-跨网点累计',
            'total_amount': 1065000,
            'amount': 30000,
            'currency_code': 'USD',
            'direction': 'buy',
            'branch_id': 1
        }
        
        # 获取客户统计
        stats = RuleEngine.get_customer_stats(session, test2_data['customer_id'], days=30)
        
        # 添加累计金额到测试数据
        test2_data['cumulative_amount_30d'] = stats['cumulative_amount_30d'] + test2_data['total_amount']
        test2_data['transaction_count_30d'] = stats['transaction_count_30d'] + 1
        
        print(f"测试数据: 买入 {test2_data['amount']:,} USD = {test2_data['total_amount']:,} THB")
        print(f"客户历史: {stats['transaction_count_30d']}笔, {stats['cumulative_amount_30d']:,.2f} THB")
        print(f"累计金额: {test2_data['cumulative_amount_30d']:,.2f} THB")
        
        for report_type in amlo_types:
            result = RuleEngine.check_triggers(session, report_type, test2_data, 1)
            
            if result.get('triggered'):
                print(f"\n[PASS] 触发 {report_type}:")
                for rule in result.get('triggered_reports', []):
                    print(f"  - 规则: {rule.get('rule_name', '')}")
        
        # 测试用例3: AMLO-1-02
        print("\n" + "="*80)
        print("[用例3] AMLO-1-02 可疑交易 (2,000 USD = 70,000 THB + 可疑标记)")
        print("="*80)
        
        test3_data = {
            'customer_id': '9876543210987',
            'customer_name': '李四',
            'total_amount': 70000,
            'amount': 2000,
            'currency_code': 'USD',
            'direction': 'sell',
            'suspicious_flag': 1,  # 可疑标记
            'branch_id': 1
        }
        
        print(f"测试数据: 卖出 {test3_data['amount']:,} USD = {test3_data['total_amount']:,} THB")
        print(f"可疑标记: 是")
        
        for report_type in amlo_types:
            result = RuleEngine.check_triggers(session, report_type, test3_data, 1)
            
            if result.get('triggered'):
                print(f"\n[PASS] 触发 {report_type}:")
                for rule in result.get('triggered_reports', []):
                    print(f"  - 规则: {rule.get('rule_name', '')}")
        
        # 汇总结果
        print("\n" + "="*80)
        print("测试总结")
        print("="*80)
        print("\n[OK] 触发条件测试完成")
        print("\n下一步操作:")
        print("  1. 访问前端页面: http://localhost:8080")
        print("  2. 登录: admin / admin123")
        print("  3. 进入兑换页面")
        print("  4. 按以下数据进行实际交易:")
        print("\n     用例1: 买入 60,000 USD (客户: 张三, 1234567890123)")
        print("     用例2: 买入 30,000 USD (客户: TEST9876543210)")
        print("     用例3: 卖出 2,000 USD (客户: 李四, 勾选可疑标记)")
        print("\n  5. 收集生成的PDF文件:")
        print("     - 交易票据: src/receipts/")
        print("     - AMLO报告: src/manager_files/")
        
    except Exception as e:
        print(f"\n[ERROR] 测试异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        DatabaseService.close_session(session)

if __name__ == "__main__":
    main()

