#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AMLO直接测试（绕过API，直接调用服务层）
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Windows UTF-8 输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from services.db_service import DatabaseService
from services.repform.rule_engine import RuleEngine
from models.exchange_models import Currency
from datetime import datetime

def test_trigger_conditions():
    """测试触发条件"""
    print("="*80)
    print("AMLO触发条件测试（直接调用服务层）")
    print("="*80)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    session = DatabaseService.get_session()
    
    try:
        # 获取USD币种ID
        usd = session.query(Currency).filter_by(currency_code='USD').first()
        if not usd:
            print("[ERROR] USD币种不存在")
            return
        
        print(f"[OK] USD币种ID: {usd.id}\n")
        
        # 测试用例1: AMLO-1-01 (60,000 USD @ 35.50 = 2,130,000 THB)
        print("="*80)
        print("[测试用例1] AMLO-1-01 单笔大额交易")
        print("="*80)
        
        test_data_1 = {
            'customer_id': '1234567890123',
            'customer_name': '张三',
            'currency_code': 'USD',
            'direction': 'buy',
            'total_amount': 2130000,  # 本币金额
            'amount': 60000,  # 外币金额
            'branch_id': 1
        }
        
        print(f"交易信息:")
        print(f"  客户: {test_data_1['customer_name']} ({test_data_1['customer_id']})")
        print(f"  交易: 买入 {test_data_1['amount']:,} USD")
        print(f"  本币: {test_data_1['total_amount']:,} THB")
        
        result_1 = RuleEngine.check_triggers(session, None, test_data_1, 1)
        
        if result_1.get('triggered'):
            print(f"\n[OK] 触发检测成功")
            for report in result_1.get('triggered_reports', []):
                print(f"  - {report['report_type']}: {report.get('rule_name', '')}")
                if report['report_type'] == 'AMLO-1-01':
                    print(f"    [PASS] AMLO-1-01 触发成功!")
        else:
            print(f"\n[ERROR] 未触发任何报告")
        
        # 测试用例2: AMLO-1-03 (30,000 USD + 历史410万 = 516.5万 THB)
        print("\n" + "="*80)
        print("[测试用例2] AMLO-1-03 累计大额交易")
        print("="*80)
        
        test_data_2 = {
            'customer_id': 'TEST9876543210',
            'customer_name': '测试客户-张三-跨网点累计',
            'currency_code': 'USD',
            'direction': 'buy',
            'total_amount': 1065000,
            'amount': 30000,
            'branch_id': 1
        }
        
        print(f"交易信息:")
        print(f"  客户: {test_data_2['customer_name']} ({test_data_2['customer_id']})")
        print(f"  交易: 买入 {test_data_2['amount']:,} USD")
        print(f"  本币: {test_data_2['total_amount']:,} THB")
        
        # 获取客户历史
        customer_stats = RuleEngine.get_customer_stats(session, test_data_2['customer_id'], days=30)
        
        print(f"\n客户历史统计:")
        print(f"  30天交易: {customer_stats['transaction_count_30d']} 笔")
        print(f"  30天累计: {customer_stats['cumulative_amount_30d']:,.2f} THB")
        
        if 'branch_breakdown' in customer_stats:
            print(f"  网点分布:")
            for branch_data in customer_stats['branch_breakdown']:
                print(f"    Branch {branch_data['branch_id']}: {branch_data['count']}笔, {branch_data['amount']:,.2f} THB")
        
        # 检查触发
        result_2 = RuleEngine.check_triggers(session, None, test_data_2, 1)
        
        if result_2.get('triggered'):
            print(f"\n[OK] 触发检测成功")
            for report in result_2.get('triggered_reports', []):
                print(f"  - {report['report_type']}: {report.get('rule_name', '')}")
                if report['report_type'] == 'AMLO-1-03':
                    print(f"    [PASS] AMLO-1-03 触发成功!")
        else:
            print(f"\n[ERROR] 未触发任何报告")
        
        # 测试用例3: AMLO-1-02 (2,000 USD @ 35.00 = 70,000 THB + 可疑标记)
        print("\n" + "="*80)
        print("[测试用例3] AMLO-1-02 可疑交易")
        print("="*80)
        
        test_data_3 = {
            'customer_id': '9876543210987',
            'customer_name': '李四',
            'currency_code': 'USD',
            'direction': 'sell',
            'total_amount': 70000,
            'amount': 2000,
            'suspicious_flag': 1,
            'branch_id': 1
        }
        
        print(f"交易信息:")
        print(f"  客户: {test_data_3['customer_name']} ({test_data_3['customer_id']})")
        print(f"  交易: 卖出 {test_data_3['amount']:,} USD")
        print(f"  本币: {test_data_3['total_amount']:,} THB")
        print(f"  可疑标记: 是")
        
        result_3 = RuleEngine.check_triggers(session, None, test_data_3, 1)
        
        if result_3.get('triggered'):
            print(f"\n[OK] 触发检测成功")
            for report in result_3.get('triggered_reports', []):
                print(f"  - {report['report_type']}: {report.get('rule_name', '')}")
                if report['report_type'] == 'AMLO-1-02':
                    print(f"    [PASS] AMLO-1-02 触发成功!")
        else:
            print(f"\n[ERROR] 未触发任何报告")
        
        # 汇总
        print("\n" + "="*80)
        print("测试结果汇总")
        print("="*80)
        
        results = []
        for i, result in enumerate([result_1, result_2, result_3], 1):
            report_types = {
                1: 'AMLO-1-01',
                2: 'AMLO-1-03',
                3: 'AMLO-1-02'
            }
            expected = report_types[i]
            
            if result.get('triggered'):
                triggered = [r['report_type'] for r in result.get('triggered_reports', [])]
                if expected in triggered:
                    print(f"[PASS] 用例{i} ({expected}): 触发成功")
                    results.append(True)
                else:
                    print(f"[FAIL] 用例{i} ({expected}): 未触发预期报告")
                    print(f"        实际触发: {', '.join(triggered)}")
                    results.append(False)
            else:
                print(f"[FAIL] 用例{i} ({expected}): 未触发任何报告")
                results.append(False)
        
        print(f"\n通过率: {sum(results)}/3")
        
        print("\n" + "="*80)
        print("下一步操作")
        print("="*80)
        print("\n由于直接测试绕过了完整的交易流程，")
        print("请通过浏览器访问前端页面进行完整测试：")
        print("\n1. 访问: http://localhost:8080")
        print("2. 登录: admin / admin123")
        print("3. 进入兑换页面")
        print("4. 按照 AMLO_MANUAL_TEST_GUIDE.md 执行测试")
        print("5. 收集生成的PDF文件进行核对")
        print("\n生成的文件位置:")
        print("  交易票据: src/receipts/")
        print("  AMLO报告: src/manager_files/")
        
    except Exception as e:
        print(f"\n[ERROR] 测试异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        DatabaseService.close_session(session)

if __name__ == "__main__":
    test_trigger_conditions()

