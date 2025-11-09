#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AMLO完整测试 - 基于A005网点
生成测试数据并验证报告
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Windows UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from services.db_service import DatabaseService
from sqlalchemy import text
from datetime import datetime, timedelta
import json

def get_a005_branch_id():
    """获取A005网点ID"""
    session = DatabaseService.get_session()
    try:
        result = session.execute(text("""
            SELECT id, branch_code, branch_name 
            FROM branches 
            WHERE branch_code = 'A005'
        """))
        branch = result.fetchone()
        
        if branch:
            print(f"[OK] 找到A005网点")
            print(f"  ID: {branch[0]}")
            print(f"  代码: {branch[1]}")
            print(f"  名称: {branch[2]}")
            return branch[0]
        else:
            print("[WARN] A005网点不存在，使用Branch 1")
            return 1
    finally:
        DatabaseService.close_session(session)

def create_test_transactions_a005(branch_id):
    """为A005创建测试交易"""
    session = DatabaseService.get_session()
    
    print("\n[1] 创建测试交易数据...")
    
    try:
        # 获取USD币种ID
        usd_result = session.execute(text("SELECT id FROM currencies WHERE currency_code = 'USD'"))
        usd_id = usd_result.scalar()
        
        if not usd_id:
            print("[ERROR] USD币种不存在")
            return False
        
        print(f"  USD币种ID: {usd_id}")
        
        # 清理旧测试数据
        session.execute(text("""
            DELETE FROM exchange_transactions 
            WHERE customer_id IN ('TEST_AMLO_101', 'TEST_AMLO_103_HIST', 'TEST_AMLO_102')
            AND branch_id = :branch_id
        """), {'branch_id': branch_id})
        session.commit()
        
        # 创建测试交易
        test_transactions = []
        
        # 用例1: AMLO-1-01 - 单笔大额
        test_transactions.append({
            'transaction_no': f'TEST_AMLO101_{datetime.now().strftime("%Y%m%d%H%M%S")}',
            'branch_id': branch_id,
            'currency_id': usd_id,
            'type': 'buy',
            'amount': 60000,
            'rate': 35.50,
            'local_amount': 2130000,
            'customer_name': '张三-测试AMLO101',
            'customer_id': 'TEST_AMLO_101',
            'transaction_date': datetime.now().date(),
            'transaction_time': datetime.now().time(),
            'status': 'completed',
            'created_at': datetime.now(),
            'operator_id': 1,
            'seqno': 1
        })
        
        # 用例2: AMLO-1-03 - 创建历史累计数据（4笔，共410万）
        base_time = datetime.now() - timedelta(days=15)
        historical_txs = [
            {'days_ago': 25, 'amount_usd': 40000, 'rate': 35.5, 'thb': 1420000},
            {'days_ago': 20, 'amount_usd': 35000, 'rate': 35.6, 'thb': 1246000},
            {'days_ago': 15, 'amount_usd': 28000, 'rate': 35.3, 'thb': 988400},
            {'days_ago': 10, 'amount_usd': 30000, 'rate': 35.4, 'thb': 1062000}
        ]
        
        for i, tx in enumerate(historical_txs):
            tx_time = datetime.now() - timedelta(days=tx['days_ago'])
            test_transactions.append({
                'transaction_no': f'TEST_HIST_{i+1}_{datetime.now().strftime("%m%d")}',
                'branch_id': branch_id,
                'currency_id': usd_id,
                'type': 'buy' if i % 2 == 0 else 'sell',
                'amount': tx['amount_usd'],
                'rate': tx['rate'],
                'local_amount': tx['thb'],
                'customer_name': '李明-测试AMLO103',
                'customer_id': 'TEST_AMLO_103_HIST',
                'transaction_date': tx_time.date(),
                'transaction_time': tx_time.time(),
                'status': 'completed',
                'created_at': tx_time,
                'operator_id': 1,
                'seqno': i + 2
            })
        
        # 插入测试交易
        for tx in test_transactions:
            insert_sql = text("""
                INSERT INTO exchange_transactions (
                    transaction_no, branch_id, currency_id, type,
                    amount, rate, local_amount,
                    customer_name, customer_id,
                    transaction_date, transaction_time,
                    status, created_at, operator_id, seqno
                ) VALUES (
                    :transaction_no, :branch_id, :currency_id, :type,
                    :amount, :rate, :local_amount,
                    :customer_name, :customer_id,
                    :transaction_date, :transaction_time,
                    :status, :created_at, :operator_id, :seqno
                )
            """)
            
            session.execute(insert_sql, tx)
        
        session.commit()
        
        print(f"\n  [OK] 已创建 {len(test_transactions)} 笔测试交易")
        print(f"  - AMLO-1-01: 1笔 (213万THB)")
        print(f"  - AMLO-1-03历史: 4笔 (471.6万THB累计)")
        
        return True
        
    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] 创建测试交易失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        DatabaseService.close_session(session)

def verify_triggers_a005(branch_id):
    """验证A005网点的触发逻辑"""
    session = DatabaseService.get_session()
    
    print("\n[2] 验证触发逻辑...")
    
    try:
        from services.repform.rule_engine import RuleEngine
        
        # 测试AMLO-1-01
        test1_data = {
            'customer_id': 'TEST_AMLO_101',
            'customer_name': '张三-测试AMLO101',
            'total_amount': 2130000,
            'amount': 60000,
            'currency_code': 'USD',
            'direction': 'buy',
            'branch_id': branch_id
        }
        
        result1 = RuleEngine.check_triggers(session, 'AMLO-1-01', test1_data, branch_id)
        
        print(f"\n  测试1 (AMLO-1-01):")
        print(f"    金额: 2,130,000 THB")
        if result1.get('triggered'):
            print(f"    结果: [PASS] 触发成功")
        else:
            print(f"    结果: [FAIL] 未触发")
        
        # 测试AMLO-1-03
        stats = RuleEngine.get_customer_stats(session, 'TEST_AMLO_103_HIST', days=30)
        
        test2_data = {
            'customer_id': 'TEST_AMLO_103_HIST',
            'customer_name': '李明-测试AMLO103',
            'total_amount': 1100000,  # 新交易110万
            'amount': 30000,
            'currency_code': 'USD',
            'direction': 'buy',
            'branch_id': branch_id,
            'cumulative_amount_30d': stats['cumulative_amount_30d'] + 1100000
        }
        
        result2 = RuleEngine.check_triggers(session, 'AMLO-1-03', test2_data, branch_id)
        
        print(f"\n  测试2 (AMLO-1-03):")
        print(f"    历史累计: {stats['cumulative_amount_30d']:,.2f} THB")
        print(f"    新交易: 1,100,000 THB")
        print(f"    总累计: {test2_data['cumulative_amount_30d']:,.2f} THB")
        if result2.get('triggered'):
            print(f"    结果: [PASS] 触发成功")
        else:
            print(f"    结果: [FAIL] 未触发")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        DatabaseService.close_session(session)

def show_next_steps(branch_id):
    """显示后续操作步骤"""
    print("\n" + "="*80)
    print("测试数据准备完成")
    print("="*80)
    
    print(f"\n目标网点: A005 (ID: {branch_id})")
    print("\n下一步操作:")
    print("\n1. 使用A005网点的账号登录:")
    print("   访问: http://localhost:8080")
    print("   用户: (A005网点的操作员账号)")
    print("   网点: A005")
    
    print("\n2. 进行测试交易:")
    print("\n   测试用例1 (AMLO-1-01):")
    print("   - 客户: 张三-测试AMLO101")
    print("   - 证件号: TEST_AMLO_101")
    print("   - 交易: 买入 60,000 USD")
    print("   - 预期: 触发AMLO-1-01")
    
    print("\n   测试用例2 (AMLO-1-03):")
    print("   - 客户: 李明-测试AMLO103")
    print("   - 证件号: TEST_AMLO_103_HIST")
    print("   - 交易: 买入 30,000 USD")
    print("   - 预期: 触发AMLO-1-03 (已有471.6万历史)")
    
    print("\n3. 查看报告:")
    print("   - AMLO预约审核: http://localhost:8080/amlo/reservations")
    print("   - AMLO报告管理: http://localhost:8080/amlo/reports")
    print("   - BOT报告查询: http://localhost:8080/bot/reports")
    
    print("\n4. 查找PDF文件:")
    print(f"   $today = Get-Date -Format 'yyyyMMdd'")
    print(f"   explorer \"D:\\Code\\ExchangeNew\\src\\receipts\\$today\"")
    print(f"   explorer \"D:\\Code\\ExchangeNew\\src\\manager_files\\$today\"")

def main():
    print("="*80)
    print("AMLO测试数据准备 - A005网点")
    print("="*80)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 获取A005网点ID
    branch_id = get_a005_branch_id()
    
    # 创建测试交易
    if not create_test_transactions_a005(branch_id):
        return
    
    # 验证触发逻辑
    if not verify_triggers_a005(branch_id):
        return
    
    # 显示后续步骤
    show_next_steps(branch_id)

if __name__ == "__main__":
    main()

