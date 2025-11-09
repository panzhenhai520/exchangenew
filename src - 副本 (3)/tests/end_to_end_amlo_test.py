#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端AMLO测试 - 真实生成PDF文件
直接调用后端服务生成交易、预约和PDF报告
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
from services.repform.report_data_service import ReportDataService
from services.pdf.amlo_pdf_generator import AMLOPDFGenerator
from models.exchange_models import ExchangeTransaction, Currency, Branch
from sqlalchemy import text
from datetime import datetime, date
import json
import glob

def create_real_transaction(branch_id, customer_id, customer_name, amount_usd, rate):
    """创建真实的交易记录"""
    session = DatabaseService.get_session()
    
    try:
        # 获取USD币种
        usd = session.query(Currency).filter_by(currency_code='USD').first()
        if not usd:
            print("[ERROR] USD币种不存在")
            return None
        
        # 生成交易号
        from utils.transaction_utils import generate_transaction_no
        tx_no = generate_transaction_no(branch_id, session)
        
        # 计算本币金额
        local_amount = amount_usd * rate
        
        # 创建交易记录
        now = datetime.now()
        transaction = ExchangeTransaction(
            transaction_no=tx_no,
            branch_id=branch_id,
            currency_id=usd.id,
            type='buy',
            amount=amount_usd,
            rate=rate,
            local_amount=local_amount,
            customer_name=customer_name,
            customer_id=customer_id,
            transaction_date=date.today(),
            transaction_time=now.strftime('%H:%M:%S'),  # 只存储时分秒，避免微秒过长
            status='completed',
            created_at=now,
            operator_id=1,
            seqno=1
        )
        
        session.add(transaction)
        session.flush()
        
        tx_id = transaction.id
        session.commit()
        
        print(f"[OK] 交易创建成功")
        print(f"  交易号: {tx_no}")
        print(f"  交易ID: {tx_id}")
        print(f"  金额: {amount_usd:,} USD = {local_amount:,} THB")
        
        return {
            'id': tx_id,
            'transaction_no': tx_no,
            'currency_id': usd.id,
            'amount': amount_usd,
            'local_amount': local_amount,
            'rate': rate
        }
        
    except Exception as e:
        session.rollback()
        print(f"[ERROR] 创建交易失败: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        DatabaseService.close_session(session)

def create_reservation_and_report(branch_id, transaction_data, customer_id, customer_name):
    """创建预约和AMLO报告"""
    session = DatabaseService.get_session()
    
    try:
        # 准备预约数据
        reservation_data = {
            'report_type': 'AMLO-1-01',
            'customer_id': customer_id,
            'customer_name': customer_name,
            'currency_id': transaction_data['currency_id'],
            'direction': 'buy',
            'amount': transaction_data['amount'],
            'local_amount': transaction_data['local_amount'],
            'rate': transaction_data['rate'],
            'trigger_type': '1',
            'transaction_id': transaction_data['id'],
            'branch_id': branch_id,
            'operator_id': 1,
            'form_data': {
                'occupation': '商人',
                'address': '曼谷市中心测试路100号',
                'phone': '0812345678',
                'purpose': '旅游支出',
                'funding_source': '个人储蓄',
                'remarks': '端到端测试AMLO-1-01报告生成'
            },
            'exchange_type': 'normal'
        }
        
        # 保存预约记录
        reservation_id = ReportDataService.save_reservation(session, reservation_data)
        
        print(f"\n[OK] 预约记录创建成功")
        print(f"  预约ID: {reservation_id}")
        
        # 准备报告数据
        # report_type是ENUM('CTR','ATR','STR')，report_format是具体格式
        report_data = {
            'report_type': 'CTR',  # Cash Transaction Report
            'report_format': 'AMLO-1-01',
            'branch_id': branch_id,
            'reserved_id': reservation_id,
            'transaction_id': transaction_data['id'],
            'customer_id': customer_id,
            'customer_name': customer_name,
            'transaction_amount': transaction_data['local_amount'],
            'transaction_date': date.today(),
            'operator_id': 1,
            'language': 'zh',
            'pdf_filename': '',
            'pdf_path': ''
        }
        
        # 保存AMLO报告记录
        report_id = ReportDataService.save_amlo_report(session, report_data)
        
        print(f"\n[OK] AMLO报告记录创建成功")
        print(f"  报告ID: {report_id}")
        
        # 获取报告详情（用于生成PDF）
        report_record = session.execute(text("""
            SELECT * FROM AMLOReport WHERE id = :id
        """), {'id': report_id}).fetchone()
        
        # 生成PDF
        print(f"\n[3] 生成PDF文件...")
        
        # 构建PDF数据
        pdf_data = {
            'report_no': report_record.report_no,
            'report_date': datetime.now().strftime('%Y-%m-%d'),
            'customer_name': customer_name,
            'customer_id': customer_id,
            'occupation': '商人',
            'address': '曼谷市中心测试路100号',
            'phone': '0812345678',
            'transaction_date': date.today().strftime('%Y-%m-%d'),
            'transaction_type': '买入',
            'currency': 'USD',
            'foreign_amount': transaction_data['amount'],
            'exchange_rate': transaction_data['rate'],
            'thb_amount': transaction_data['local_amount'],
            'purpose': '旅游支出',
            'funding_source': '个人储蓄',
            'remarks': '端到端测试AMLO-1-01报告生成'
        }
        
        # 确定输出路径（使用manager目录结构）
        current_dir = os.path.dirname(os.path.abspath(__file__))
        year = date.today().year
        month = date.today().month
        
        manager_dir = os.path.join(current_dir, '..', 'manager', str(year), f"{month:02d}")
        os.makedirs(manager_dir, exist_ok=True)
        
        pdf_filename = f"AMLO-1-01_R{report_record.report_no}.pdf"
        pdf_path = os.path.join(manager_dir, pdf_filename)
        
        print(f"  PDF路径: {pdf_path}")
        
        # 生成PDF
        generator = AMLOPDFGenerator()
        result_path = generator.generate_pdf('AMLO-1-01', pdf_data, pdf_path)
        
        # 更新数据库中的PDF路径
        session.execute(text("""
            UPDATE AMLOReport 
            SET pdf_filename = :filename, pdf_path = :path
            WHERE id = :id
        """), {
            'filename': pdf_filename,
            'path': pdf_path,
            'id': report_id
        })
        
        session.commit()
        
        print(f"\n[OK] PDF生成成功!")
        print(f"  文件名: {pdf_filename}")
        print(f"  完整路径: {os.path.abspath(pdf_path)}")
        print(f"  文件大小: {os.path.getsize(pdf_path)} 字节")
        
        return {
            'reservation_id': reservation_id,
            'report_id': report_id,
            'pdf_path': pdf_path,
            'pdf_filename': pdf_filename
        }
        
    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] 创建预约和报告失败: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        DatabaseService.close_session(session)

def verify_files_exist(transaction_data, report_data):
    """验证文件确实存在"""
    print("\n" + "="*80)
    print("[4] 验证文件存在性")
    print("="*80)
    
    # 验证PDF报告
    if os.path.exists(report_data['pdf_path']):
        print(f"\n[OK] AMLO报告PDF存在")
        print(f"  路径: {os.path.abspath(report_data['pdf_path'])}")
        print(f"  大小: {os.path.getsize(report_data['pdf_path']) / 1024:.2f} KB")
    else:
        print(f"\n[ERROR] AMLO报告PDF不存在: {report_data['pdf_path']}")
    
    # 查找交易票据（如果生成了）
    year = date.today().year
    month = date.today().month
    receipt_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'receipts', str(year), f"{month:02d}")
    
    if os.path.exists(receipt_dir):
        receipts = glob.glob(os.path.join(receipt_dir, f"*{transaction_data['transaction_no']}*.pdf"))
        if receipts:
            print(f"\n[OK] 找到交易票据:")
            for receipt in receipts:
                print(f"  {os.path.basename(receipt)}")
                print(f"  路径: {os.path.abspath(receipt)}")
                print(f"  大小: {os.path.getsize(receipt) / 1024:.2f} KB")
        else:
            print(f"\n[INFO] 交易票据未找到（可能需要通过前端交易生成）")
    else:
        print(f"\n[INFO] 票据目录不存在: {receipt_dir}")

def list_all_files():
    """列出所有生成的文件"""
    print("\n" + "="*80)
    print("[5] 列出所有PDF文件")
    print("="*80)
    
    year = date.today().year
    month = date.today().month
    
    # 列出AMLO报告
    manager_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'manager', str(year), f"{month:02d}")
    
    print(f"\nAMLO报告目录: {os.path.abspath(manager_dir)}")
    
    if os.path.exists(manager_dir):
        amlo_files = glob.glob(os.path.join(manager_dir, "AMLO*.pdf"))
        if amlo_files:
            print(f"找到 {len(amlo_files)} 个AMLO报告:")
            for f in amlo_files:
                print(f"  - {os.path.basename(f)}")
        else:
            print("  暂无AMLO报告")
    else:
        print("  [INFO] 目录不存在")
    
    # 列出交易票据
    receipt_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'receipts', str(year), f"{month:02d}")
    
    print(f"\n交易票据目录: {os.path.abspath(receipt_dir)}")
    
    if os.path.exists(receipt_dir):
        receipt_files = glob.glob(os.path.join(receipt_dir, "*.pdf"))
        if receipt_files:
            print(f"找到 {len(receipt_files)} 个交易票据:")
            for f in receipt_files[:5]:  # 只显示前5个
                print(f"  - {os.path.basename(f)}")
            if len(receipt_files) > 5:
                print(f"  ... 还有 {len(receipt_files) - 5} 个文件")
        else:
            print("  暂无票据")
    else:
        print("  [INFO] 目录不存在")

def main():
    print("="*80)
    print("端到端AMLO测试 - 真实生成PDF文件")
    print("="*80)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 获取A005网点
    session = DatabaseService.get_session()
    try:
        branch = session.query(Branch).filter_by(branch_code='A005').first()
        if not branch:
            print("[WARN] A005网点不存在，使用Branch 1")
            branch = session.query(Branch).filter_by(id=1).first()
        
        branch_id = branch.id
        print(f"[OK] 使用网点: {branch.branch_name} (ID: {branch_id}, Code: {branch.branch_code})")
    finally:
        DatabaseService.close_session(session)
    
    # 步骤1: 创建交易
    print("\n" + "="*80)
    print("[1] 创建测试交易")
    print("="*80)
    
    transaction_data = create_real_transaction(
        branch_id=branch_id,
        customer_id='TEST_E2E_AMLO',
        customer_name='端到端测试客户',
        amount_usd=60000,
        rate=35.50
    )
    
    if not transaction_data:
        print("\n[ERROR] 测试终止: 交易创建失败")
        return
    
    # 步骤2: 创建预约和报告
    print("\n" + "="*80)
    print("[2] 创建预约和AMLO报告")
    print("="*80)
    
    report_data = create_reservation_and_report(
        branch_id=branch_id,
        transaction_data=transaction_data,
        customer_id='TEST_E2E_AMLO',
        customer_name='端到端测试客户'
    )
    
    if not report_data:
        print("\n[ERROR] 测试终止: 报告创建失败")
        return
    
    # 步骤3: 验证文件存在
    verify_files_exist(transaction_data, report_data)
    
    # 步骤4: 列出所有文件
    list_all_files()
    
    # 最终总结
    print("\n" + "="*80)
    print("测试完成总结")
    print("="*80)
    
    print(f"\n生成的文件:")
    print(f"  1. AMLO报告: {os.path.abspath(report_data['pdf_path'])}")
    print(f"     (可用PDF阅读器打开)")
    
    print(f"\n数据库记录:")
    print(f"  - 交易ID: {transaction_data['id']}")
    print(f"  - 预约ID: {report_data['reservation_id']}")
    print(f"  - 报告ID: {report_data['report_id']}")
    
    print(f"\n查看报告的方式:")
    print(f"  1. 直接打开PDF: {os.path.abspath(report_data['pdf_path'])}")
    print(f"  2. 访问报告列表: http://localhost:8080/amlo/reports")
    print(f"  3. 访问预约列表: http://localhost:8080/amlo/reservations")
    
    print(f"\n打开文件目录:")
    print(f"  explorer \"{os.path.dirname(os.path.abspath(report_data['pdf_path']))}\"")

if __name__ == "__main__":
    main()

