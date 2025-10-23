# -*- coding: utf-8 -*-
"""
完整AMLO流程测试
测试：预约→审核→交易完整流程
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from services.db_service import DatabaseService
from sqlalchemy import text
from datetime import datetime, date

def test_flow():
    """测试完整流程"""
    session = DatabaseService.get_session()
    
    try:
        print("="*80)
        print("AMLO完整流程测试")
        print("="*80)
        
        # 场景1: 检查有已通过预约的客户
        print("\n[场景1] 检查有已通过预约的客户")
        print("-"*80)
        
        # 查找状态为approved的预约
        sql = text("""
            SELECT customer_id, customer_name, status, local_amount, report_type
            FROM Reserved_Transaction
            WHERE status = 'approved'
            LIMIT 1
        """)
        
        result = session.execute(sql).fetchone()
        if result:
            print(f"[OK] 找到已通过预约:")
            print(f"  客户: {result[1]}")
            print(f"  证件号: {result[0]}")
            print(f"  状态: {result[2]}")
            print(f"  批准金额: {result[3]} THB")
            print(f"  报告类型: {result[4]}")
            print(f"\n  → 该客户输入证件号时应显示'审核已通过，可继续交易'")
        else:
            print("[INFO] 暂无已通过的预约")
        
        # 场景2: 检查待审核的预约
        print("\n[场景2] 检查待审核的预约")
        print("-"*80)
        
        sql = text("""
            SELECT customer_id, customer_name, status, local_amount, report_type
            FROM Reserved_Transaction
            WHERE status = 'pending'
            LIMIT 1
        """)
        
        result = session.execute(sql).fetchone()
        if result:
            print(f"[OK] 找到待审核预约:")
            print(f"  客户: {result[1]}")
            print(f"  证件号: {result[0]}")
            print(f"  状态: {result[2]}")
            print(f"  金额: {result[3]} THB")
            print(f"\n  → 该客户输入证件号时应显示'待审核，无法交易'")
        else:
            print("[INFO] 暂无待审核的预约")
        
        # 场景3: 检查被拒绝的预约
        print("\n[场景3] 检查被拒绝的预约")
        print("-"*80)
        
        sql = text("""
            SELECT customer_id, customer_name, status, rejection_reason
            FROM Reserved_Transaction
            WHERE status = 'rejected'
            LIMIT 1
        """)
        
        result = session.execute(sql).fetchone()
        if result:
            print(f"[OK] 找到被拒绝预约:")
            print(f"  客户: {result[1]}")
            print(f"  证件号: {result[0]}")
            print(f"  状态: {result[2]}")
            print(f"  拒绝理由: {result[3]}")
            print(f"\n  → 该客户输入证件号时应显示'审核未通过：{result[3]}'")
        else:
            print("[INFO] 暂无被拒绝的预约")
        
        # 场景4: 测试新客户（无预约）
        print("\n[场景4] 测试新客户（无预约）")
        print("-"*80)
        
        test_customer_id = "TEST_NEW_CUSTOMER_001"
        sql = text("""
            SELECT COUNT(*) FROM Reserved_Transaction
            WHERE customer_id = :customer_id
        """)
        
        count = session.execute(sql, {'customer_id': test_customer_id}).scalar()
        
        if count == 0:
            print(f"[OK] 客户 {test_customer_id} 无预约记录")
            print(f"\n  → 输入证件号时应调用触发规则检查")
            print(f"  → 如触发规则，弹出预约表单")
            print(f"  → 如不触发，直接继续交易")
        else:
            print(f"[INFO] 客户已有{count}条预约")
        
        # 检查PDF文件
        print("\n[场景5] 检查已生成的PDF文件")
        print("-"*80)
        
        import glob
        pdf_pattern = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..', 'manager', '2025', '10', 'AMLO*.pdf'
        )
        
        pdfs = glob.glob(pdf_pattern)
        print(f"[OK] 找到 {len(pdfs)} 个AMLO PDF文件")
        
        if pdfs:
            print("\n示例文件:")
            for pdf in pdfs[:3]:
                print(f"  - {os.path.basename(pdf)}")
            print(f"\n  → 在预约审核页面应该可以点击查看这些PDF")
        
        # 最终总结
        print("\n" + "="*80)
        print("流程检查总结")
        print("="*80)
        
        print("\n✅ 数据库中已有的状态:")
        sql = text("""
            SELECT status, COUNT(*) as count
            FROM Reserved_Transaction
            GROUP BY status
        """)
        
        results = session.execute(sql).fetchall()
        for row in results:
            print(f"  - {row[0]}: {row[1]} 条")
        
        print("\n📋 需要验证的前端功能:")
        print("  1. 预约审核页面 - PDF查看按钮")
        print("  2. 兑换页面 - 输入证件号后检查预约状态")
        print("  3. 状态提示 - 已通过/待审核/被拒绝")
        print("  4. 交易继续 - 已通过预约可继续交易")
        
        print("\n🌐 测试页面:")
        print("  - 预约审核: http://localhost:8080/amlo/reservations")
        print("  - 兑换页面: http://localhost:8080/exchange")
        
    finally:
        DatabaseService.close_session(session)

if __name__ == "__main__":
    test_flow()

