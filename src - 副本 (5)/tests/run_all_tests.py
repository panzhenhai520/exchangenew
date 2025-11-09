#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
综合测试运行器
Comprehensive Test Runner for Exchange System

运行所有测试场景：
- AMLO完整场景测试（预约、审核、交易、超期提醒）
- BOT Provider触发测试（USD和EUR场景）
- 集成所有测试结果报告

Usage:
    python src/tests/run_all_tests.py
    python src/tests/run_all_tests.py --suite amlo    # 仅运行AMLO测试
    python src/tests/run_all_tests.py --suite bot     # 仅运行BOT测试
    python src/tests/run_all_tests.py --verbose       # 详细输出
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
from datetime import datetime
import traceback
import io

# Configure stdout/stderr encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 导入测试模块
from tests.test_amlo_complete_scenarios import AMLOScenarioTester
from tests.test_amlo_audit_features import AMLOAuditFeaturesTest
from tests.test_branch_isolation import BranchIsolationTest
from tests.test_bot_provider_eur_adjustment import test_bot_provider_trigger_eur_adjustment
from tests.test_all_bot_reports import AllBOTReportsTest


class ComprehensiveTestRunner:
    """综合测试运行器"""

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.results = {
            'amlo': {},
            'amlo_audit': {},
            'branch_isolation': {},
            'bot': {},
            'total_passed': 0,
            'total_failed': 0,
            'total_skipped': 0
        }
        self.start_time = None
        self.end_time = None

    def print_header(self):
        """打印测试套件标题"""
        print("\n" + "="*100)
        print("Currency Exchange System - Comprehensive Test Suite".center(100))
        print("外汇管理系统 - 综合测试套件".center(100))
        print("="*100)
        print(f"\n⏰ Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📍 Working Directory: {os.getcwd()}")
        print(f"🐍 Python Version: {sys.version.split()[0]}")
        print("="*100 + "\n")

    def print_section_header(self, title, subtitle=""):
        """打印测试章节标题"""
        print("\n" + "="*100)
        print(f"  {title}")
        if subtitle:
            print(f"  {subtitle}")
        print("="*100 + "\n")

    def run_amlo_tests(self):
        """运行AMLO测试场景"""
        self.print_section_header(
            "🔐 AMLO Compliance Tests",
            "AMLO合规性测试 - 预约、审核、交易、超期提醒"
        )

        try:
            tester = AMLOScenarioTester()

            # 登录
            if not tester.login():
                print("❌ AMLO测试套件失败: 无法登录")
                self.results['amlo']['login'] = False
                self.results['total_failed'] += 3
                return False

            self.results['amlo']['login'] = True

            # 场景A: 完整预约到交易流程
            try:
                result_a = tester.scenario_a_reservation_to_transaction()
                self.results['amlo']['scenario_a'] = result_a
                if result_a:
                    self.results['total_passed'] += 1
                else:
                    self.results['total_failed'] += 1
            except Exception as e:
                print(f"❌ Scenario A failed with exception: {str(e)}")
                if self.verbose:
                    traceback.print_exc()
                self.results['amlo']['scenario_a'] = False
                self.results['total_failed'] += 1

            # 场景B: 反审核流程
            try:
                result_b = tester.scenario_b_reverse_audit()
                self.results['amlo']['scenario_b'] = result_b
                if result_b:
                    self.results['total_passed'] += 1
                else:
                    self.results['total_failed'] += 1
            except Exception as e:
                print(f"❌ Scenario B failed with exception: {str(e)}")
                if self.verbose:
                    traceback.print_exc()
                self.results['amlo']['scenario_b'] = False
                self.results['total_failed'] += 1

            # 场景C: 超期提醒
            try:
                result_c = tester.scenario_c_overdue_alert()
                self.results['amlo']['scenario_c'] = result_c
                if result_c:
                    self.results['total_passed'] += 1
                else:
                    self.results['total_failed'] += 1
            except Exception as e:
                print(f"❌ Scenario C failed with exception: {str(e)}")
                if self.verbose:
                    traceback.print_exc()
                self.results['amlo']['scenario_c'] = False
                self.results['total_failed'] += 1

            return all([
                self.results['amlo'].get('scenario_a', False),
                self.results['amlo'].get('scenario_b', False),
                self.results['amlo'].get('scenario_c', False)
            ])

        except Exception as e:
            print(f"❌ AMLO测试套件发生严重错误: {str(e)}")
            if self.verbose:
                traceback.print_exc()
            self.results['total_failed'] += 3
            return False

    def run_amlo_audit_tests(self):
        """运行AMLO审计功能测试"""
        self.print_section_header(
            "🔍 AMLO Audit Features Tests",
            "AMLO审计功能测试 - 预约审核、报告查询、状态流转"
        )

        try:
            tester = AMLOAuditFeaturesTest()

            # 登录
            if not tester.login():
                print("❌ AMLO审计测试套件失败: 无法登录")
                self.results['amlo_audit']['login'] = False
                self.results['total_failed'] += 19  # Total AMLO audit tests
                return False

            self.results['amlo_audit']['login'] = True

            # 设置测试数据
            if not tester.setup_test_data():
                print("❌ AMLO审计测试套件失败: 无法设置测试数据")
                self.results['total_failed'] += 19
                return False

            # Part 1: Reservation Audit Page Tests (7 tests)
            part1_tests = [
                ('reservation_query', tester.test_reservation_query),
                ('time_range_filter', tester.test_time_range_filter),
                ('status_filter', tester.test_status_filter),
                ('approve_function', tester.test_approve_function),
                ('reject_function', tester.test_reject_function),
                ('reverse_audit_function', tester.test_reverse_audit_function),
                ('history_query', tester.test_history_query)
            ]

            for test_key, test_method in part1_tests:
                try:
                    result = test_method()
                    self.results['amlo_audit'][test_key] = result
                    if result:
                        self.results['total_passed'] += 1
                    else:
                        self.results['total_failed'] += 1
                except Exception as e:
                    print(f"❌ {test_key} failed with exception: {str(e)}")
                    if self.verbose:
                        traceback.print_exc()
                    self.results['amlo_audit'][test_key] = False
                    self.results['total_failed'] += 1

            # Part 2: AMLO Report Query Page Tests (7 tests)
            part2_tests = [
                ('report_list_display', tester.test_report_list_display),
                ('time_diff_calculation', tester.test_time_diff_calculation),
                ('unreported_blue_display', tester.test_unreported_blue_display),
                ('overdue_red_display', tester.test_overdue_red_display),
                ('immediate_report_prompt', tester.test_immediate_report_prompt),
                ('mark_reported_function', tester.test_mark_reported_function),
                ('pdf_download_function', tester.test_pdf_download_function)
            ]

            for test_key, test_method in part2_tests:
                try:
                    result = test_method()
                    self.results['amlo_audit'][test_key] = result
                    if result:
                        self.results['total_passed'] += 1
                    else:
                        self.results['total_failed'] += 1
                except Exception as e:
                    print(f"❌ {test_key} failed with exception: {str(e)}")
                    if self.verbose:
                        traceback.print_exc()
                    self.results['amlo_audit'][test_key] = False
                    self.results['total_failed'] += 1

            # Part 3: Status Transition Tests (5 tests)
            try:
                tester.test_status_transitions()
                for test_key in ['pending_to_approved', 'pending_to_rejected', 'approved_to_pending',
                                 'approved_to_completed', 'completed_to_reported']:
                    result = tester.test_results.get(test_key, False)
                    self.results['amlo_audit'][test_key] = result
                    if result:
                        self.results['total_passed'] += 1
                    else:
                        self.results['total_failed'] += 1
            except Exception as e:
                print(f"❌ Status transition tests failed with exception: {str(e)}")
                if self.verbose:
                    traceback.print_exc()
                for test_key in ['pending_to_approved', 'pending_to_rejected', 'approved_to_pending',
                                 'approved_to_completed', 'completed_to_reported']:
                    self.results['amlo_audit'][test_key] = False
                    self.results['total_failed'] += 1

            # Check overall success
            all_passed = all(self.results['amlo_audit'].get(key, False)
                           for key in tester.test_results.keys() if key != 'login')
            return all_passed

        except Exception as e:
            print(f"❌ AMLO审计测试套件发生严重错误: {str(e)}")
            if self.verbose:
                traceback.print_exc()
            self.results['total_failed'] += 19
            return False

    def run_branch_isolation_tests(self):
        """运行网点数据隔离测试"""
        self.print_section_header(
            "🏢 Branch Data Isolation Tests",
            "网点数据隔离测试 - Branch 1/2数据完全隔离验证"
        )

        try:
            tester = BranchIsolationTest()

            # 运行所有测试
            exit_code = tester.run_all_tests()

            # 提取结果
            test_keys = [
                'branch1_login',
                'branch2_login',
                'reservation_isolation',
                'report_isolation',
                'transaction_isolation',
                'trigger_rule_isolation',
                'branch_id_correctness',
                'cross_branch_access_denied'
            ]

            for key in test_keys:
                result = tester.test_results.get(key, False)
                self.results['branch_isolation'][key] = result
                if result:
                    self.results['total_passed'] += 1
                else:
                    self.results['total_failed'] += 1

            return exit_code == 0

        except Exception as e:
            print(f"❌ 网点隔离测试套件发生严重错误: {str(e)}")
            if self.verbose:
                traceback.print_exc()
            self.results['total_failed'] += 8
            return False

    def run_bot_tests(self):
        """运行所有BOT报告测试"""
        self.print_section_header(
            "🏦 BOT Reports Tests",
            "BOT报告测试 - BuyFX, SellFX, FCD, Provider"
        )

        all_passed = True

        # Test 1: 完整BOT报告测试（4种报告类型）
        try:
            print("\n[BOT Suite 1] All BOT Reports Test (BuyFX, SellFX, FCD, Provider)...")
            bot_tester = AllBOTReportsTest()
            result = bot_tester.run_all_tests()

            # 从bot_tester提取结果
            self.results['bot']['bot_buyfx'] = bot_tester.test_results.get('bot_buyfx', False)
            self.results['bot']['bot_sellfx'] = bot_tester.test_results.get('bot_sellfx', False)
            self.results['bot']['bot_fcd'] = bot_tester.test_results.get('bot_fcd', False)
            self.results['bot']['bot_provider'] = bot_tester.test_results.get('bot_provider', False)

            # 统计结果
            for key in ['bot_buyfx', 'bot_sellfx', 'bot_fcd', 'bot_provider']:
                if self.results['bot'].get(key):
                    self.results['total_passed'] += 1
                else:
                    self.results['total_failed'] += 1
                    all_passed = False

        except Exception as e:
            print(f"❌ 完整BOT报告测试发生错误: {str(e)}")
            if self.verbose:
                traceback.print_exc()
            # Mark all as failed
            for key in ['bot_buyfx', 'bot_sellfx', 'bot_fcd', 'bot_provider']:
                self.results['bot'][key] = False
                self.results['total_failed'] += 1
            all_passed = False

        # Test 2: BOT Provider EUR调节专项测试
        try:
            print("\n[BOT Suite 2] BOT Provider EUR Adjustment Test...")
            result = test_bot_provider_trigger_eur_adjustment()
            self.results['bot']['eur_adjustment'] = result

            if result:
                self.results['total_passed'] += 1
            else:
                self.results['total_failed'] += 1
                all_passed = False

        except Exception as e:
            print(f"❌ EUR调节测试发生错误: {str(e)}")
            if self.verbose:
                traceback.print_exc()
            self.results['bot']['eur_adjustment'] = False
            self.results['total_failed'] += 1
            all_passed = False

        return all_passed

    def print_summary(self):
        """打印测试总结报告"""
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()

        print("\n" + "="*100)
        print("📊 Test Results Summary".center(100))
        print("测试结果汇总".center(100))
        print("="*100 + "\n")

        # AMLO测试结果
        print("🔐 AMLO Compliance Tests:")
        if 'login' in self.results['amlo']:
            status = "✅ PASS" if self.results['amlo']['login'] else "❌ FAIL"
            print(f"  {status} - Login Authentication")

        for scenario in ['scenario_a', 'scenario_b', 'scenario_c']:
            if scenario in self.results['amlo']:
                status = "✅ PASS" if self.results['amlo'][scenario] else "❌ FAIL"
                scenario_name = {
                    'scenario_a': 'Scenario A: Reservation to Transaction (20 steps)',
                    'scenario_b': 'Scenario B: Reverse Audit (4 steps)',
                    'scenario_c': 'Scenario C: Overdue Alert (5 steps)'
                }[scenario]
                print(f"  {status} - {scenario_name}")

        # AMLO审计功能测试结果
        print("\n🔍 AMLO Audit Features Tests:")
        amlo_audit_tests = [
            ('reservation_query', 'Reservation Query Function'),
            ('time_range_filter', 'Time Range Filter'),
            ('status_filter', 'Status Filter'),
            ('approve_function', 'Approve Function'),
            ('reject_function', 'Reject Function'),
            ('reverse_audit_function', 'Reverse Audit Function'),
            ('history_query', 'History Query Function'),
            ('report_list_display', 'Report List Display'),
            ('time_diff_calculation', 'Time Difference Calculation'),
            ('unreported_blue_display', 'Unreported Records (Blue)'),
            ('overdue_red_display', 'Overdue Records (Red)'),
            ('immediate_report_prompt', 'Immediate Report Prompt'),
            ('mark_reported_function', 'Mark Reported Function'),
            ('pdf_download_function', 'PDF Download Function'),
            ('pending_to_approved', 'Status: pending → approved'),
            ('pending_to_rejected', 'Status: pending → rejected'),
            ('approved_to_pending', 'Status: approved → pending (reverse)'),
            ('approved_to_completed', 'Status: approved → completed'),
            ('completed_to_reported', 'Status: completed → reported')
        ]

        for test_key, test_name in amlo_audit_tests:
            if test_key in self.results['amlo_audit']:
                result = self.results['amlo_audit'][test_key]
                if result is True:
                    status = "✅ PASS"
                elif result is False:
                    status = "❌ FAIL"
                else:
                    status = "⏭️  SKIP"
                print(f"  {status} - {test_name}")

        # 网点隔离测试结果
        print("\n🏢 Branch Data Isolation Tests:")
        branch_isolation_tests = [
            ('branch1_login', 'Branch 1 Login'),
            ('branch2_login', 'Branch 2 Login'),
            ('reservation_isolation', 'Reservation Data Isolation'),
            ('report_isolation', 'Report Data Isolation'),
            ('transaction_isolation', 'Transaction Data Isolation'),
            ('trigger_rule_isolation', 'Trigger Rule Branch Isolation'),
            ('branch_id_correctness', 'Branch ID Correctness'),
            ('cross_branch_access_denied', 'Cross-Branch Access Denied')
        ]

        for test_key, test_name in branch_isolation_tests:
            if test_key in self.results['branch_isolation']:
                result = self.results['branch_isolation'][test_key]
                if result is True:
                    status = "✅ PASS"
                elif result is False:
                    status = "❌ FAIL"
                else:
                    status = "⏭️  SKIP"
                print(f"  {status} - {test_name}")

        # BOT测试结果
        print("\n🏦 BOT Reports Tests:")
        bot_tests = [
            ('bot_buyfx', 'BOT_BuyFX: 买入外币 > 20,000 USD'),
            ('bot_sellfx', 'BOT_SellFX: 卖出外币 > 20,000 USD'),
            ('bot_fcd', 'BOT_FCD: FCD账户 > 50,000 USD'),
            ('bot_provider', 'BOT_Provider: 余额调节 > 20,000 USD'),
            ('eur_adjustment', 'BOT_Provider: EUR转USD等值测试')
        ]

        for test_key, test_name in bot_tests:
            if test_key in self.results['bot']:
                result = self.results['bot'][test_key]
                if result is True:
                    status = "✅ PASS"
                elif result is False:
                    status = "❌ FAIL"
                else:
                    status = "⏭️  SKIP"
                print(f"  {status} - {test_name}")

        # 总体统计
        print("\n" + "-"*100)
        total_tests = self.results['total_passed'] + self.results['total_failed']
        pass_rate = (self.results['total_passed'] / total_tests * 100) if total_tests > 0 else 0

        print(f"\n📈 Overall Statistics:")
        print(f"  Total Tests Run:    {total_tests}")
        print(f"  Tests Passed:       {self.results['total_passed']} ✅")
        print(f"  Tests Failed:       {self.results['total_failed']} ❌")
        print(f"  Tests Skipped:      {self.results['total_skipped']} ⏭️")
        print(f"  Pass Rate:          {pass_rate:.1f}%")
        print(f"  Duration:           {duration:.2f} seconds")

        print("\n" + "="*100)

        if self.results['total_failed'] == 0:
            print("✅ ALL TESTS PASSED! 所有测试通过！".center(100))
            print("="*100 + "\n")
            return 0
        else:
            print(f"❌ {self.results['total_failed']} TEST(S) FAILED! {self.results['total_failed']}个测试失败！".center(100))
            print("="*100 + "\n")
            return 1

    def run_all(self):
        """运行所有测试"""
        self.start_time = datetime.now()
        self.print_header()

        # 运行AMLO场景测试
        amlo_result = self.run_amlo_tests()

        # 运行AMLO审计功能测试
        amlo_audit_result = self.run_amlo_audit_tests()

        # 运行网点数据隔离测试
        branch_isolation_result = self.run_branch_isolation_tests()

        # 运行BOT测试
        bot_result = self.run_bot_tests()

        # 打印总结
        return self.print_summary()

    def run_suite(self, suite_name):
        """运行指定的测试套件"""
        self.start_time = datetime.now()
        self.print_header()

        if suite_name == 'amlo':
            self.run_amlo_tests()
        elif suite_name == 'amlo_audit':
            self.run_amlo_audit_tests()
        elif suite_name == 'branch_isolation':
            self.run_branch_isolation_tests()
        elif suite_name == 'bot':
            self.run_bot_tests()
        else:
            print(f"❌ Unknown test suite: {suite_name}")
            print("   Available suites: amlo, amlo_audit, branch_isolation, bot")
            return 1

        return self.print_summary()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='外汇管理系统综合测试运行器 - Exchange System Comprehensive Test Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_all_tests.py                            # 运行所有测试
  python run_all_tests.py --suite amlo               # 仅运行AMLO场景测试
  python run_all_tests.py --suite amlo_audit         # 仅运行AMLO审计功能测试
  python run_all_tests.py --suite branch_isolation   # 仅运行网点数据隔离测试
  python run_all_tests.py --suite bot                # 仅运行BOT测试
  python run_all_tests.py --verbose                  # 详细输出模式
        """
    )

    parser.add_argument(
        '--suite',
        choices=['amlo', 'amlo_audit', 'branch_isolation', 'bot', 'all'],
        default='all',
        help='指定要运行的测试套件 (default: all)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='启用详细输出模式'
    )

    args = parser.parse_args()

    runner = ComprehensiveTestRunner(verbose=args.verbose)

    try:
        if args.suite == 'all':
            return runner.run_all()
        else:
            return runner.run_suite(args.suite)
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        return 130
    except Exception as e:
        print(f"\n\n❌ 测试运行器发生严重错误: {str(e)}")
        if args.verbose:
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
