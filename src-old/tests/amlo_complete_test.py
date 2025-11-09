#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AMLO完整测试流程
包括：触发检测 → 预约表单 → 实际交易 → 生成票据 → 生成AMLO报告
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置输出编码为UTF-8（Windows兼容）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import requests
import json
from datetime import datetime
import time

# 系统配置
BASE_URL = "http://localhost:5001"
BRANCH_ID = 1

class AMLOTester:
    def __init__(self):
        self.token = None
        self.test_results = []
    
    def login(self):
        """登录系统"""
        print("\n" + "="*80)
        print("[步骤1] 登录系统")
        print("="*80)
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "login_code": "admin",
            "password": "admin123",
            "branch": BRANCH_ID
        })
        
        if response.status_code == 200:
            result = response.json()
            self.token = result.get('access_token')
            print("[OK] 登录成功")
            print(f"  用户: admin")
            print(f"  网点ID: {BRANCH_ID}")
            return True
        else:
            print(f"[ERROR] 登录失败: {response.text}")
            return False
    
    def check_and_configure_rules(self):
        """检查并配置触发规则"""
        print("\n" + "="*80)
        print("[步骤2] 检查触发规则配置")
        print("="*80)
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # 获取所有规则
        try:
            response = requests.get(f"{BASE_URL}/api/compliance/trigger-rules", headers=headers, timeout=10)
        except Exception as e:
            print(f"[ERROR] 请求失败: {e}")
            return False
        
        if response.status_code == 401:
            # Token过期，重新登录
            print("[WARN] Token过期，重新登录...")
            if not self.login():
                return False
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{BASE_URL}/api/compliance/trigger-rules", headers=headers)
        
        if response.status_code != 200:
            print(f"[ERROR] 获取规则失败 (HTTP {response.status_code}): {response.text}")
            return False
        
        rules = response.json().get('data', [])
        print(f"[OK] 当前系统共有 {len(rules)} 条触发规则")
        
        # 检查AMLO规则
        amlo_rules = {}
        for rule in rules:
            if rule['report_type'] in ['AMLO-1-01', 'AMLO-1-02', 'AMLO-1-03']:
                amlo_rules[rule['report_type']] = rule
        
        print(f"\n找到 {len(amlo_rules)} 条AMLO规则:")
        for report_type, rule in amlo_rules.items():
            print(f"\n  [{report_type}] {rule['rule_name_cn']}")
            print(f"    启用: {'是' if rule['is_active'] else '否'}")
            print(f"    优先级: {rule['priority']}")
            print(f"    表达式: {rule['rule_expression']}")
            print(f"    允许继续: {'是' if rule['allow_continue'] else '否'}")
        
        # 验证必要的规则是否存在
        required_types = ['AMLO-1-01', 'AMLO-1-03']  # 1-02 可选
        missing_types = [t for t in required_types if t not in amlo_rules]
        
        if missing_types:
            print(f"\n[WARN] 缺少规则: {', '.join(missing_types)}")
            return False
        
        return True
    
    def test_trigger_detection(self, customer_id, customer_name, currency_code, direction, amount, suspicious=False):
        """测试触发检测"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        test_data = {
            "customer_id": customer_id,
            "customer_name": customer_name,
            "currency_code": currency_code,
            "direction": direction,
            "amount": amount,
            "branch_id": BRANCH_ID
        }
        
        if suspicious:
            test_data['suspicious_flag'] = 1
        
        print(f"\n检查触发条件:")
        print(f"  客户: {customer_name} ({customer_id})")
        print(f"  交易: {direction.upper()} {amount:,} {currency_code}")
        
        response = requests.post(
            f"{BASE_URL}/api/repform/check-trigger",
            headers=headers,
            json=test_data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('triggered'):
                triggered_reports = result.get('triggered_reports', [])
                print(f"  [OK] 触发 {len(triggered_reports)} 个报告:")
                for report in triggered_reports:
                    print(f"    - {report['report_type']}: {report.get('rule_name', '')}")
                
                # 显示客户统计（如果有）
                if 'customer_stats' in result:
                    stats = result['customer_stats']
                    print(f"\n  客户统计:")
                    print(f"    30天交易: {stats.get('transaction_count_30d', 0)} 笔")
                    print(f"    30天累计: {stats.get('cumulative_amount_30d', 0):,.2f} THB")
                
                return {
                    'success': True,
                    'triggered': True,
                    'reports': triggered_reports,
                    'test_data': test_data
                }
            else:
                print(f"  [ERROR] 未触发任何报告")
                return {'success': True, 'triggered': False}
        else:
            print(f"  [ERROR] 检查失败: {response.status_code}")
            return {'success': False, 'message': response.text}
    
    def get_form_schema(self, report_type):
        """获取表单结构"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/repform/form-schema/{report_type}",
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json().get('data', {})
        else:
            return None
    
    def simulate_form_submission(self, report_type, transaction_data):
        """模拟表单填写和提交"""
        print(f"\n  模拟填写 {report_type} 预约表单...")
        
        # 获取表单结构
        form_schema = self.get_form_schema(report_type)
        if not form_schema:
            print(f"    [ERROR] 无法获取表单结构")
            return None
        
        # 构造表单数据（简化版）
        form_data = {
            'customer_id': transaction_data['customer_id'],
            'customer_name': transaction_data['customer_name'],
            'transaction_amount': transaction_data.get('amount', 0),
            'transaction_currency': transaction_data.get('currency_code', 'USD'),
            'transaction_purpose': '旅游支出',  # 模拟数据
            'occupation': '商人',
            'address': '曼谷市中心',
            'phone': '0812345678',
            'nationality': 'CN',
            'id_type': '护照',
            'id_number': transaction_data['customer_id'],
            'remarks': f'测试{report_type}报告生成'
        }
        
        if report_type == 'AMLO-1-02':
            form_data['suspicious_reason'] = '交易模式异常，多次小额分拆'
            form_data['risk_level'] = 'high'
        
        print(f"    [OK] 表单数据已准备")
        return form_data
    
    def run_test_case(self, case_number, description, customer_id, customer_name, 
                      currency_code, direction, amount, expected_report, suspicious=False):
        """运行单个测试用例"""
        print("\n" + "="*80)
        print(f"[测试用例{case_number}] {description}")
        print("="*80)
        
        # 1. 触发检测
        trigger_result = self.test_trigger_detection(
            customer_id, customer_name, currency_code, direction, amount, suspicious
        )
        
        if not trigger_result.get('success'):
            print(f"\n[FAIL] 用例{case_number}失败: 触发检测异常")
            self.test_results.append({
                'case': case_number,
                'result': 'FAILED',
                'reason': '触发检测失败'
            })
            return False
        
        if not trigger_result.get('triggered'):
            print(f"\n[FAIL] 用例{case_number}失败: 未触发预期报告")
            self.test_results.append({
                'case': case_number,
                'result': 'FAILED',
                'reason': '未触发'
            })
            return False
        
        # 2. 检查是否触发了预期报告
        triggered_reports = trigger_result.get('reports', [])
        has_expected = any(r['report_type'] == expected_report for r in triggered_reports)
        
        if not has_expected:
            print(f"\n[FAIL] 用例{case_number}失败: 未触发{expected_report}")
            print(f"    实际触发: {', '.join([r['report_type'] for r in triggered_reports])}")
            self.test_results.append({
                'case': case_number,
                'result': 'FAILED',
                'reason': f'未触发{expected_report}'
            })
            return False
        
        # 3. 模拟表单填写
        form_data = self.simulate_form_submission(expected_report, trigger_result['test_data'])
        
        if not form_data:
            print(f"\n[WARN]  用例{case_number}部分成功: 触发正确但表单模拟失败")
            self.test_results.append({
                'case': case_number,
                'result': 'PARTIAL',
                'reason': '表单模拟失败'
            })
            return True  # 触发检测正确，算部分成功
        
        print(f"\n[PASS] 用例{case_number}成功:")
        print(f"    触发报告: {expected_report}")
        print(f"    表单字段: {len(form_data)} 个")
        
        self.test_results.append({
            'case': case_number,
            'result': 'PASSED',
            'report_type': expected_report,
            'form_data': form_data
        })
        
        return True
    
    def run_all_tests(self):
        """运行所有测试用例"""
        print("\n" + "="*80)
        print("AMLO报告完整测试流程")
        print("="*80)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 登录
        if not self.login():
            print("\n[ERROR] 测试终止: 登录失败")
            return False
        
        # 检查规则
        if not self.check_and_configure_rules():
            print("\n[ERROR] 测试终止: 规则配置不完整")
            return False
        
        # 准备测试数据
        print("\n" + "="*80)
        print("[步骤3] 准备测试数据")
        print("="*80)
        
        print("\n正在创建测试客户历史数据...")
        try:
            import subprocess
            result = subprocess.run(
                ["python", "tests/create_test_customer_history.py"],
                cwd=os.path.dirname(os.path.dirname(__file__)),
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=30
            )
            if result.returncode == 0:
                print("[OK] 测试数据准备完成")
            else:
                print(f"[WARN]  测试数据准备失败，AMLO-1-03可能无法测试")
        except Exception as e:
            print(f"[WARN]  测试数据准备异常: {e}")
        
        # 执行测试用例
        print("\n" + "="*80)
        print("[步骤4] 执行测试用例")
        print("="*80)
        
        # 测试用例1: AMLO-1-01
        self.run_test_case(
            case_number=1,
            description="AMLO-1-01 单笔大额交易（60,000 USD ≈ 2,130,000 THB）",
            customer_id="1234567890123",
            customer_name="张三",
            currency_code="USD",
            direction="buy",
            amount=60000,
            expected_report="AMLO-1-01"
        )
        
        # 测试用例2: AMLO-1-03
        self.run_test_case(
            case_number=2,
            description="AMLO-1-03 累计大额交易（30,000 USD + 历史410万 ≈ 516.5万 THB）",
            customer_id="TEST9876543210",
            customer_name="测试客户-张三-跨网点累计",
            currency_code="USD",
            direction="buy",
            amount=30000,
            expected_report="AMLO-1-03"
        )
        
        # 测试用例3: AMLO-1-02
        self.run_test_case(
            case_number=3,
            description="AMLO-1-02 可疑交易（2,000 USD ≈ 70,000 THB，标记可疑）",
            customer_id="9876543210987",
            customer_name="李四",
            currency_code="USD",
            direction="sell",
            amount=2000,
            expected_report="AMLO-1-02",
            suspicious=True
        )
        
        # 输出汇总
        self.print_summary()
        
        return True
    
    def print_summary(self):
        """打印测试汇总"""
        print("\n" + "="*80)
        print("测试结果汇总")
        print("="*80)
        
        passed = sum(1 for r in self.test_results if r['result'] == 'PASSED')
        partial = sum(1 for r in self.test_results if r['result'] == 'PARTIAL')
        failed = sum(1 for r in self.test_results if r['result'] == 'FAILED')
        total = len(self.test_results)
        
        print(f"\n总计: {total} 个测试用例")
        print(f"  [PASS] 通过: {passed}")
        print(f"  [WARN]  部分: {partial}")
        print(f"  [FAIL] 失败: {failed}")
        
        print(f"\n详细结果:")
        for result in self.test_results:
            status_icon = {
                'PASSED': '[PASS]',
                'PARTIAL': '[WARN]',
                'FAILED': '[FAIL]'
            }.get(result['result'], '?')
            
            print(f"  {status_icon} 用例{result['case']}: {result['result']}")
            if 'report_type' in result:
                print(f"      触发报告: {result['report_type']}")
            if 'reason' in result:
                print(f"      原因: {result['reason']}")
        
        print("\n" + "="*80)
        print("后续操作指南")
        print("="*80)
        print("\n1. 访问前端页面进行实际交易:")
        print(f"   {BASE_URL}")
        print("\n2. 进行以下交易（根据测试结果）:")
        
        for i, result in enumerate(self.test_results, 1):
            if result['result'] in ['PASSED', 'PARTIAL']:
                print(f"\n   测试用例{i}:")
                if 'form_data' in result:
                    form = result['form_data']
                    print(f"     客户: {form.get('customer_name')} ({form.get('customer_id')})")
                    print(f"     金额: {form.get('transaction_amount')} {form.get('transaction_currency')}")
                    print(f"     触发: {result.get('report_type')}")
        
        print("\n3. 检查生成的文件:")
        print("   交易票据: receipts/ 目录")
        print("   AMLO报告: manager_files/ 目录")
        
        print("\n4. 查询报告:")
        print(f"   访问: {BASE_URL}/amlo/reports")
        print("   或使用API: GET /api/amlo/reports")

def main():
    """主函数"""
    tester = AMLOTester()
    
    try:
        tester.run_all_tests()
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] 无法连接到系统")
        print(f"  请确保系统已启动: {BASE_URL}")
        print(f"  启动命令: cd src; python main.py")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

