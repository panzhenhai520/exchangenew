#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AMLO & BOT 合规功能全面验证脚本
检查所有关键功能的实现状态
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from services.db_service import DatabaseService
import json
from datetime import datetime, timedelta

class ComplianceChecker:
    def __init__(self):
        self.db = DatabaseService()
        self.session = self.db.get_session()
        self.results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }
    
    def log_pass(self, test_name, message=""):
        self.results['passed'].append((test_name, message))
        print(f"✓ PASS: {test_name}")
        if message:
            print(f"       {message}")
    
    def log_fail(self, test_name, message=""):
        self.results['failed'].append((test_name, message))
        print(f"✗ FAIL: {test_name}")
        if message:
            print(f"       {message}")
    
    def log_warning(self, test_name, message=""):
        self.results['warnings'].append((test_name, message))
        print(f"⚠ WARN: {test_name}")
        if message:
            print(f"       {message}")
    
    def check_database_structure(self):
        """检查数据库结构完整性"""
        print("\n" + "="*80)
        print("1. 数据库结构检查")
        print("="*80)
        
        # 检查必需的表
        required_tables = [
            'report_fields',
            'trigger_rules',
            'Reserved_Transaction',
            'AMLOReport',
            'BOT_BuyFX',
            'BOT_SellFX',
            'BOT_Provider',
            'BOT_FCD',
            'exchange_transactions'
        ]
        
        for table in required_tables:
            result = self.session.execute(f"SHOW TABLES LIKE '{table}'")
            if result.fetchone():
                self.log_pass(f"表存在: {table}")
            else:
                self.log_fail(f"表不存在: {table}")
        
        # 检查exchange_transactions表的字段
        result = self.session.execute("DESCRIBE exchange_transactions")
        columns = {row[0] for row in result}
        
        required_fields = ['bot_flag', 'fcd_flag', 'use_fcd', 'branch_id', 'seqno']
        for field in required_fields:
            if field in columns:
                self.log_pass(f"exchange_transactions.{field} 存在")
            else:
                self.log_fail(f"exchange_transactions.{field} 不存在")
    
    def check_trigger_rules(self):
        """检查触发规则配置"""
        print("\n" + "="*80)
        print("2. 触发规则配置检查")
        print("="*80)
        
        # 检查各报告类型的触发规则
        report_types = ['AMLO-1-01', 'AMLO-1-02', 'AMLO-1-03', 
                       'BOT_BuyFX', 'BOT_SellFX', 'BOT_FCD', 'BOT_Provider']
        
        for report_type in report_types:
            result = self.session.execute(
                "SELECT COUNT(*), SUM(is_active) FROM trigger_rules WHERE report_type = %s",
                (report_type,)
            )
            row = result.fetchone()
            total = row[0] if row else 0
            active = row[1] if row and row[1] else 0
            
            if total > 0:
                if active > 0:
                    self.log_pass(f"{report_type} 触发规则: {active}条激活（共{total}条）")
                else:
                    self.log_warning(f"{report_type} 触发规则: {total}条存在但未激活")
            else:
                self.log_fail(f"{report_type} 触发规则: 未配置")
    
    def check_field_definitions(self):
        """检查字段定义"""
        print("\n" + "="*80)
        print("3. 字段定义检查")
        print("="*80)
        
        report_types = ['AMLO-1-01', 'AMLO-1-02', 'AMLO-1-03', 
                       'BOT_BuyFX', 'BOT_SellFX', 'BOT_FCD', 'BOT_Provider']
        
        for report_type in report_types:
            result = self.session.execute(
                "SELECT COUNT(*) FROM report_fields WHERE report_type = %s",
                (report_type,)
            )
            count = result.fetchone()[0]
            
            if count > 0:
                self.log_pass(f"{report_type} 字段定义: {count}个字段")
            else:
                self.log_fail(f"{report_type} 字段定义: 未配置")
        
        # 检查多语言支持
        result = self.session.execute("""
            SELECT report_type, 
                   SUM(CASE WHEN field_cn_name IS NOT NULL THEN 1 ELSE 0 END) as cn_count,
                   SUM(CASE WHEN field_en_name IS NOT NULL THEN 1 ELSE 0 END) as en_count,
                   SUM(CASE WHEN field_th_name IS NOT NULL THEN 1 ELSE 0 END) as th_count,
                   COUNT(*) as total
            FROM report_fields
            GROUP BY report_type
        """)
        
        print("\n  多语言字段覆盖率:")
        for row in result:
            report_type, cn, en, th, total = row
            if cn == total and en == total and th == total:
                print(f"  ✓ {report_type}: 100% (中{cn}/英{en}/泰{th} / 总{total})")
            else:
                print(f"  ⚠ {report_type}: 不完整 (中{cn}/英{en}/泰{th} / 总{total})")
    
    def check_bot_integration(self):
        """检查BOT集成"""
        print("\n" + "="*80)
        print("4. BOT报告集成检查")
        print("="*80)
        
        # 检查BOT报告服务
        try:
            from services.bot_report_service import BOTReportService
            self.log_pass("BOT报告服务: 已导入")
            
            # 检查各方法是否存在
            methods = ['generate_bot_buyfx', 'generate_bot_sellfx', 
                      'generate_bot_fcd', 'generate_bot_provider']
            for method in methods:
                if hasattr(BOTReportService, method):
                    self.log_pass(f"BOTReportService.{method}: 存在")
                else:
                    self.log_fail(f"BOTReportService.{method}: 不存在")
        except Exception as e:
            self.log_fail(f"BOT报告服务: 导入失败 - {str(e)}")
    
    def check_amlo_integration(self):
        """检查AMLO集成"""
        print("\n" + "="*80)
        print("5. AMLO流程集成检查")
        print("="*80)
        
        # 检查预约表
        result = self.session.execute("SELECT COUNT(*) FROM Reserved_Transaction")
        count = result.fetchone()[0]
        self.log_pass(f"Reserved_Transaction表: {count}条记录")
        
        # 检查AMLO报告表
        result = self.session.execute("SELECT COUNT(*) FROM AMLOReport")
        count = result.fetchone()[0]
        self.log_pass(f"AMLOReport表: {count}条记录")
        
        # 检查状态字段
        result = self.session.execute("DESCRIBE Reserved_Transaction")
        columns = {row[0] for row in result}
        
        required_fields = ['status', 'audit_time', 'reject_time', 'transaction_time', 'report_time']
        for field in required_fields:
            if field in columns:
                self.log_pass(f"Reserved_Transaction.{field}: 存在")
            else:
                self.log_warning(f"Reserved_Transaction.{field}: 可能缺失")
    
    def check_rule_engine(self):
        """检查规则引擎"""
        print("\n" + "="*80)
        print("6. 规则引擎功能检查")
        print("="*80)
        
        try:
            from services.repform.rule_engine import RuleEngine
            self.log_pass("规则引擎: 已导入")
            
            # 测试简单规则评估
            test_rule = {
                "logic": "AND",
                "conditions": [
                    {"field": "amount", "operator": ">", "value": 1000},
                    {"field": "currency", "operator": "=", "value": "USD"}
                ]
            }
            
            test_data = {"amount": 2000, "currency": "USD"}
            result = RuleEngine.evaluate_rule(test_rule, test_data)
            
            if result:
                self.log_pass("规则引擎: 评估功能正常")
            else:
                self.log_fail("规则引擎: 评估结果错误")
                
        except Exception as e:
            self.log_fail(f"规则引擎: 测试失败 - {str(e)}")
    
    def check_api_endpoints(self):
        """检查API端点"""
        print("\n" + "="*80)
        print("7. API端点检查")
        print("="*80)
        
        # 检查关键文件是否存在
        api_files = [
            ('src/routes/app_amlo.py', 'AMLO审计API'),
            ('src/routes/app_bot.py', 'BOT报告API'),
            ('src/routes/app_repform.py', '动态表单API'),
            ('src/routes/app_compliance.py', '合规配置API'),
            ('src/routes/app_balance.py', '余额调节API')
        ]
        
        for filepath, description in api_files:
            full_path = os.path.join(os.path.dirname(__file__), '..', filepath)
            if os.path.exists(full_path):
                self.log_pass(f"{description}: 文件存在")
                
                # 检查BOT_Provider集成（仅对余额调节API）
                if 'app_balance.py' in filepath:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'BOT_Provider' in content and 'check_triggers' in content:
                            self.log_pass("余额调节API: BOT_Provider集成已完成")
                        else:
                            self.log_fail("余额调节API: BOT_Provider集成缺失")
            else:
                self.log_fail(f"{description}: 文件不存在")
    
    def check_frontend_components(self):
        """检查前端组件"""
        print("\n" + "="*80)
        print("8. 前端组件检查")
        print("="*80)
        
        components = [
            ('src/views/amlo/ReservationAuditView.vue', 'AMLO预约审核页面'),
            ('src/views/amlo/ReportListView.vue', 'AMLO报告列表页面'),
            ('src/views/bot/BOTReportView.vue', 'BOT报告查询页面'),
            ('src/views/StandardsManagementView.vue', '规范管理页面'),
            ('src/components/exchange/ReservationModal.vue', '预约模态框'),
            ('src/views/ExchangeView.vue', '兑换页面')
        ]
        
        for filepath, description in components:
            full_path = os.path.join(os.path.dirname(__file__), '..', filepath)
            if os.path.exists(full_path):
                self.log_pass(f"{description}: 文件存在")
            else:
                self.log_warning(f"{description}: 文件不存在")
    
    def generate_summary(self):
        """生成测试总结"""
        print("\n" + "="*80)
        print("测试总结")
        print("="*80)
        
        total = len(self.results['passed']) + len(self.results['failed']) + len(self.results['warnings'])
        passed = len(self.results['passed'])
        failed = len(self.results['failed'])
        warnings = len(self.results['warnings'])
        
        print(f"\n总计: {total} 项检查")
        print(f"✓ 通过: {passed} 项 ({passed/total*100:.1f}%)")
        print(f"✗ 失败: {failed} 项 ({failed/total*100:.1f}%)")
        print(f"⚠ 警告: {warnings} 项 ({warnings/total*100:.1f}%)")
        
        if failed > 0:
            print("\n失败项详情:")
            for test, msg in self.results['failed']:
                print(f"  ✗ {test}")
                if msg:
                    print(f"    {msg}")
        
        if warnings > 0:
            print("\n警告项详情:")
            for test, msg in self.results['warnings']:
                print(f"  ⚠ {test}")
                if msg:
                    print(f"    {msg}")
        
        # 计算完成度
        completion_rate = (passed / total * 100) if total > 0 else 0
        print(f"\n整体合规完成度: {completion_rate:.1f}%")
        
        if completion_rate >= 90:
            print("状态: ✓ 优秀 - 系统基本符合监管要求")
        elif completion_rate >= 75:
            print("状态: ⚠ 良好 - 大部分功能已实现，部分需要完善")
        elif completion_rate >= 60:
            print("状态: ⚠ 一般 - 核心功能已实现，需要补充完善")
        else:
            print("状态: ✗ 不足 - 需要大量开发工作")
        
        return completion_rate >= 75
    
    def run_all_checks(self):
        """运行所有检查"""
        print("="*80)
        print("AMLO & BOT 合规功能全面验证")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        try:
            self.check_database_structure()
            self.check_trigger_rules()
            self.check_field_definitions()
            self.check_bot_integration()
            self.check_amlo_integration()
            self.check_rule_engine()
            self.check_api_endpoints()
            self.check_frontend_components()
            
            success = self.generate_summary()
            
            return 0 if success else 1
            
        except Exception as e:
            print(f"\n✗ 检查过程中发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return 2
        finally:
            self.session.close()

def main():
    checker = ComplianceChecker()
    return checker.run_all_checks()

if __name__ == "__main__":
    sys.exit(main())

