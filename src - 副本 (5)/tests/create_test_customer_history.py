#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
创建测试客户的历史交易数据
用于测试跨网点累计金额触发AMLO报告
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from sqlalchemy import text
from datetime import datetime, timedelta
from decimal import Decimal

def create_test_customer_data():
    """
    创建测试客户：TEST9876543210
    在多个网点创建接近阈值的历史交易
    累计金额：4,100,000 THB（距离500万阈值还差900,000）
    """
    
    db = DatabaseService()
    session = db.get_session()
    
    try:
        # 测试客户信息
        customer_id = 'TEST9876543210'
        customer_name = '测试客户-张三-跨网点累计'
        
        print("="*80)
        print(f"创建测试客户历史交易数据")
        print("="*80)
        print(f"客户证件号: {customer_id}")
        print(f"客户姓名: {customer_name}")
        print(f"目的: 测试跨网点累计金额触发AMLO-1-03\n")
        
        # 先检查并删除已存在的测试数据
        print("[1] 清理已存在的测试数据...")
        session.execute(
            text("DELETE FROM exchange_transactions WHERE customer_id = :customer_id"),
            {'customer_id': customer_id}
        )
        session.commit()
        print("  [OK] 已清理旧数据\n")
        
        # 获取币种ID映射
        print("[2] 获取币种ID...")
        result = session.execute(text("SELECT id, currency_code FROM currencies WHERE currency_code IN ('USD', 'EUR', 'GBP')"))
        currency_map = {row[1]: row[0] for row in result}
        print(f"  [OK] 找到{len(currency_map)}个币种: {', '.join(currency_map.keys())}\n")
        
        # 交易记录配置（使用现有网点：1, 3, 4）
        test_transactions = [
            {
                'branch_id': 1,
                'days_ago': 30,
                'currency_code': 'USD',
                'direction': 'buy',
                'foreign_amount': Decimal('42000'),
                'rate': Decimal('35.7'),
                'local_amount': Decimal('1500000'),
                'description': '第1笔-Branch1'
            },
            {
                'branch_id': 3,
                'days_ago': 25,
                'currency_code': 'EUR',
                'direction': 'sell',
                'foreign_amount': Decimal('30000'),
                'rate': Decimal('40.0'),
                'local_amount': Decimal('1200000'),
                'description': '第2笔-Branch3'
            },
            {
                'branch_id': 1,
                'days_ago': 20,
                'currency_code': 'USD',
                'direction': 'buy',
                'foreign_amount': Decimal('22400'),
                'rate': Decimal('35.7'),
                'local_amount': Decimal('800000'),
                'description': '第3笔-Branch1'
            },
            {
                'branch_id': 4,
                'days_ago': 15,
                'currency_code': 'USD',
                'direction': 'sell',
                'foreign_amount': Decimal('17000'),
                'rate': Decimal('35.3'),
                'local_amount': Decimal('600000'),
                'description': '第4笔-Branch4'
            }
        ]
        
        print("[3] 插入历史交易记录...")
        
        total_amount = Decimal('0')
        operator_id = 1  # 使用默认操作员ID
        
        for i, trans in enumerate(test_transactions, 1):
            # 计算交易日期
            trans_date = datetime.now() - timedelta(days=trans['days_ago'])
            
            # 检查币种是否存在
            if trans['currency_code'] not in currency_map:
                print(f"  [WARN] 跳过：币种 {trans['currency_code']} 不存在")
                continue
            
            currency_id = currency_map[trans['currency_code']]
            
            # 生成交易流水号
            transaction_no = f"TEST{trans['branch_id']:02d}{trans_date.strftime('%Y%m%d')}{i:04d}"
            
            # 插入交易记录
            sql = text("""
                INSERT INTO exchange_transactions (
                    transaction_no, branch_id, currency_id, type,
                    amount, rate, local_amount,
                    customer_name, customer_id,
                    operator_id, transaction_date, transaction_time,
                    status, created_at, seqno
                ) VALUES (
                    :transaction_no, :branch_id, :currency_id, :type,
                    :amount, :rate, :local_amount,
                    :customer_name, :customer_id,
                    :operator_id, :transaction_date, :transaction_time,
                    'completed', :created_at, :seqno
                )
            """)
            
            session.execute(sql, {
                'transaction_no': transaction_no,
                'branch_id': trans['branch_id'],
                'currency_id': currency_id,
                'type': trans['direction'],
                'amount': float(trans['foreign_amount']),
                'rate': float(trans['rate']),
                'local_amount': float(trans['local_amount']),
                'customer_name': customer_name,
                'customer_id': customer_id,
                'operator_id': operator_id,
                'transaction_date': trans_date.date(),
                'transaction_time': trans_date.strftime('%H:%M:%S'),
                'created_at': trans_date,
                'seqno': i
            })
            
            total_amount += trans['local_amount']
            
            print(f"  [{i}] {trans['description']}")
            print(f"      网点: Branch {trans['branch_id']} | {trans['days_ago']}天前")
            print(f"      交易: {trans['direction'].upper()} {trans['foreign_amount']:,.0f} {trans['currency_code']}")
            print(f"      本币: {trans['local_amount']:,.0f} THB")
        
        session.commit()
        
        # 验证数据
        print(f"\n[4] 验证插入的数据...")
        verify_sql = text("""
            SELECT COUNT(*), COALESCE(SUM(ABS(local_amount)), 0)
            FROM exchange_transactions
            WHERE customer_id = :customer_id
                AND transaction_date >= :start_date
                AND status = 'completed'
        """)
        
        start_date = (datetime.now() - timedelta(days=30)).date()
        verify_result = session.execute(verify_sql, {'customer_id': customer_id, 'start_date': start_date})
        verify_row = verify_result.first()
        
        print("="*80)
        print("✓ 测试数据创建成功！")
        print("="*80)
        print(f"客户证件号: {customer_id}")
        print(f"客户姓名: {customer_name}")
        print(f"历史交易次数: {verify_row[0]}")
        print(f"30天累计金额: {verify_row[1]:,.0f} THB")
        print(f"距离500万阈值: {5000000 - verify_row[1]:,.0f} THB")
        print()
        print("="*80)
        print("测试用例说明")
        print("="*80)
        print(f"1. 在测试触发页面输入证件号：{customer_id}")
        print(f"2. 输入新交易：买入 30,000 USD")
        print(f"3. 按汇率35.5计算，本币约：1,065,000 THB")
        print(f"4. 累计金额：{verify_row[1]:,.0f} + 1,065,000 = {verify_row[1] + 1065000:,.0f} THB")
        print(f"5. 预期结果：✓ 触发AMLO-1-03（累计超过500万THB）")
        print()
        print("="*80)
        print("跨网点统计验证")
        print("="*80)
        
        # 按网点统计
        branch_sql = text("""
            SELECT branch_id, COUNT(*), COALESCE(SUM(ABS(local_amount)), 0)
            FROM exchange_transactions
            WHERE customer_id = :customer_id
                AND transaction_date >= :start_date
            GROUP BY branch_id
            ORDER BY branch_id
        """)
        
        branch_result = session.execute(branch_sql, {'customer_id': customer_id, 'start_date': start_date})
        
        for row in branch_result:
            print(f"  Branch {row[0]}: {row[1]}笔交易, {row[2]:,.0f} THB")
        
        print()
        print("="*80)
        print("提示：这个客户的数据可以用来测试跨网点累计触发功能")
        print("="*80)
        
    except Exception as e:
        session.rollback()
        print(f"\n✗ 错误：{str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        session.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(create_test_customer_data())

