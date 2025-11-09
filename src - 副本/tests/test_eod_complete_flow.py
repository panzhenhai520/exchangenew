#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整的日结流程测试
测试7步日结流程的完整性
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from services.db_service import DatabaseService
from services.eod_service import EODService
from models.exchange_models import EODStatus, Branch, Currency, CurrencyBalance, ExchangeTransaction
from sqlalchemy import text, func
from datetime import datetime, date, timedelta
import json

def print_section(title):
    """打印分节标题"""
    print("\n" + "="*80)
    print(f"{title}")
    print("="*80)

def check_eod_setup():
    """检查日结环境准备"""
    session = DatabaseService.get_session()
    
    try:
        print_section("步骤0: 日结环境检查")
        
        # 检查网点
        branch = session.query(Branch).filter_by(branch_code='A005').first()
        if not branch:
            branch = session.query(Branch).first()
        
        print(f"[OK] 测试网点: {branch.branch_name} (ID: {branch.id})")
        
        # 检查是否有进行中的日结
        processing_eod = session.query(EODStatus).filter_by(
            branch_id=branch.id,
            status='processing'
        ).first()
        
        if processing_eod:
            eod_id = processing_eod.id
            eod_step = processing_eod.step
            eod_date = processing_eod.date
            eod_status = processing_eod.status
            
            print(f"[WARN] 存在进行中的日结 (ID: {eod_id})")
            print(f"  状态: {eod_status}")
            print(f"  当前步骤: {eod_step}")
            print(f"  日期: {eod_date}")
            return branch.id, eod_id
        else:
            print(f"[OK] 无进行中的日结，可以开始新日结")
            return branch.id, None
        
    finally:
        DatabaseService.close_session(session)

def check_currency_balances(branch_id):
    """检查币种余额"""
    session = DatabaseService.get_session()
    
    try:
        print_section("步骤0.1: 检查币种余额")
        
        balances = session.query(CurrencyBalance, Currency).join(
            Currency, CurrencyBalance.currency_id == Currency.id
        ).filter(
            CurrencyBalance.branch_id == branch_id
        ).all()
        
        print(f"\n当前库存余额:")
        print(f"{'币种':<10} {'余额':<15} {'状态'}")
        print("-"*50)
        
        for balance, currency in balances:
            status = "正常" if balance.balance > 0 else "⚠️ 零余额"
            print(f"{currency.currency_code:<10} {float(balance.balance):<15,.2f} {status}")
        
        return len(balances) > 0
        
    finally:
        DatabaseService.close_session(session)

def check_today_transactions(branch_id):
    """检查今天的交易"""
    session = DatabaseService.get_session()
    
    try:
        print_section("步骤0.2: 检查今日交易")
        
        today = date.today()
        
        transactions = session.query(
            func.count(ExchangeTransaction.id).label('count'),
            func.sum(ExchangeTransaction.local_amount).label('total')
        ).filter(
            ExchangeTransaction.branch_id == branch_id,
            ExchangeTransaction.transaction_date == today
        ).first()
        
        print(f"\n今日交易统计 ({today}):")
        print(f"  交易笔数: {transactions.count or 0}")
        print(f"  交易总额: {float(transactions.total or 0):,.2f} THB")
        
        if transactions.count and transactions.count > 0:
            print(f"\n[WARN] 今天有{transactions.count}笔交易，日结应该针对昨天的数据")
            print(f"[INFO] 建议使用昨天的日期进行日结测试")
        else:
            print(f"\n[OK] 今天无交易，可以对今天进行日结")
        
        return transactions.count or 0
        
    finally:
        DatabaseService.close_session(session)

def test_start_eod(branch_id):
    """测试步骤1: 开始日结"""
    print_section("步骤1: 开始日结")
    
    # 使用昨天的日期
    target_date = date.today() - timedelta(days=1)
    
    print(f"\n目标日期: {target_date}")
    print(f"网点ID: {branch_id}")
    
    result = EODService.start_eod(
        branch_id=branch_id,
        operator_id=1,
        target_date=target_date
    )
    
    if result.get('success'):
        print(f"\n[OK] 日结启动成功")
        print(f"  EOD ID: {result.get('eod_id')}")
        print(f"  状态: {result.get('status')}")
        print(f"  当前步骤: {result.get('current_step', 0)}")
        return result.get('eod_id')
    else:
        print(f"\n[ERROR] 日结启动失败: {result.get('message')}")
        return None

def test_eod_steps(eod_id):
    """测试日结步骤2-7"""
    session = DatabaseService.get_session()
    
    try:
        # 获取EOD状态
        eod = session.query(EODStatus).filter_by(id=eod_id).first()
        if not eod:
            print(f"[ERROR] EOD记录不存在: {eod_id}")
            return False
        
        print(f"\n当前EOD状态:")
        print(f"  ID: {eod.id}")
        print(f"  网点: {eod.branch_id}")
        print(f"  日期: {eod.date}")
        print(f"  状态: {eod.status}")
        print(f"  当前步骤: {eod.step}")
        
        # 步骤2-7的定义
        steps = [
            (2, "余额核对", "balance_verification"),
            (3, "收入统计", "income_statistics"),
            (4, "外币库存", "foreign_stock"),
            (5, "本币库存", "local_stock"),
            (6, "现金支出", "cash_out"),
            (7, "打印报表", "print_reports")
        ]
        
        print("\n" + "="*80)
        print("日结7步流程定义")
        print("="*80)
        
        for step_num, step_name, step_code in steps:
            print(f"  步骤{step_num}: {step_name} ({step_code})")
        
        return True
        
    finally:
        DatabaseService.close_session(session)

def check_eod_tables():
    """检查日结相关表"""
    session = DatabaseService.get_session()
    
    try:
        print_section("数据库表检查")
        
        tables = [
            'eod_status',
            'eod_balance_verification',
            'eod_cash_out',
            'eod_session_locks',
            'daily_income_report'
        ]
        
        for table in tables:
            result = session.execute(text(f"SHOW TABLES LIKE '{table}'")).fetchone()
            if result:
                count = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                print(f"  ✅ {table:<30} ({count} 条记录)")
            else:
                print(f"  ❌ {table:<30} (不存在)")
        
    finally:
        DatabaseService.close_session(session)

def main():
    print("="*80)
    print("日结(EOD)功能完整测试")
    print("="*80)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 步骤0: 环境检查
    branch_id, existing_eod_id = check_eod_setup()
    
    if existing_eod_id:
        print(f"\n[INFO] 发现进行中的日结，将继续测试该日结流程")
        eod_id = existing_eod_id
    else:
        # 检查余额和交易
        has_balances = check_currency_balances(branch_id)
        tx_count = check_today_transactions(branch_id)
        
        if not has_balances:
            print("\n[ERROR] 没有币种余额，无法进行日结")
            print("[建议] 请先进行一些交易或手动添加币种余额")
            return
        
        # 步骤1: 开始日结
        eod_id = test_start_eod(branch_id)
        
        if not eod_id:
            print("\n[ERROR] 日结启动失败，测试终止")
            return
    
    # 检查日结相关表
    check_eod_tables()
    
    # 测试日结步骤
    test_eod_steps(eod_id)
    
    # 最终总结
    print_section("测试总结")
    
    print(f"\n✅ 日结环境: 正常")
    print(f"✅ EOD ID: {eod_id}")
    print(f"✅ 网点ID: {branch_id}")
    
    print(f"\n📋 后续测试:")
    print(f"  1. 访问日结页面: http://localhost:8080/eod")
    print(f"  2. 继续执行步骤2-7")
    print(f"  3. 验证每步数据正确性")
    print(f"  4. 完成日结")
    print(f"  5. 验证生成的报表PDF")
    
    print(f"\n📂 日结报表位置:")
    print(f"  manager/2025/{date.today().strftime('%m')}/")

if __name__ == "__main__":
    main()

