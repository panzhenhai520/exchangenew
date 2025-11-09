#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整的7笔交易测试
生成: 3个AMLO PDF + 4个BOT报表
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Windows UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from services.db_service import DatabaseService
from services.bot_template_based_generator import BOTTemplateBasedGenerator
from models.exchange_models import ExchangeTransaction, Currency, Branch
from sqlalchemy import text
from datetime import datetime, date
import calendar

def clear_today_data():
    """清理今天的测试数据"""
    session = DatabaseService.get_session()
    
    try:
        # 删除今天的数据
        session.execute(text("DELETE FROM AMLOReport WHERE DATE(created_at) = CURDATE()"))
        session.execute(text("DELETE FROM Reserved_Transaction WHERE DATE(created_at) = CURDATE()"))
        session.execute(text("DELETE FROM BOT_BuyFX WHERE DATE(created_at) = CURDATE()"))
        session.execute(text("DELETE FROM BOT_SellFX WHERE DATE(created_at) = CURDATE()"))
        session.execute(text("DELETE FROM BOT_FCD WHERE DATE(created_at) = CURDATE()"))
        
        session.commit()
        print("[OK] 已清理今天的测试数据\n")
        
    except Exception as e:
        session.rollback()
        print(f"[ERROR] 清理数据失败: {e}\n")
    finally:
        DatabaseService.close_session(session)

def create_transaction_with_bot_records(branch_id, test_case):
    """创建交易并同时创建BOT记录"""
    session = DatabaseService.get_session()
    
    try:
        # 获取币种
        currency = session.query(Currency).filter_by(currency_code=test_case['currency']).first()
        if not currency:
            print(f"[ERROR] 币种不存在: {test_case['currency']}")
            return None
        
        # 生成交易号
        from utils.transaction_utils import generate_transaction_no
        tx_no = generate_transaction_no(branch_id, session)
        
        # 计算本币金额
        amount = test_case['amount']
        rate = test_case['rate']
        local_amount = amount * rate
        
        # 创建交易记录
        now = datetime.now()
        transaction = ExchangeTransaction(
            transaction_no=tx_no,
            branch_id=branch_id,
            currency_id=currency.id,
            type=test_case['type'],
            amount=amount,
            rate=rate,
            local_amount=local_amount,
            customer_name=test_case['customer_name'],
            customer_id=test_case['customer_id'],
            customer_country_code=test_case.get('country_code', 'TH'),
            customer_address=test_case.get('address'),
            occupation=test_case.get('occupation'),
            transaction_date=date.today(),
            transaction_time=now.strftime('%H:%M:%S'),
            status='completed',
            created_at=now,
            operator_id=1,
            seqno=1,
            use_fcd=test_case.get('use_fcd', False)
        )
        
        session.add(transaction)
        session.flush()
        
        tx_id = transaction.id
        
        # 创建BOT记录
        if test_case['type'] == 'buy':
            # 创建Buy FX记录
            sql = text("""
                INSERT INTO BOT_BuyFX (
                    transaction_id, transaction_no, transaction_date,
                    customer_id_type, customer_id_number, customer_name,
                    customer_country_code, rate_type, buy_currency_code,
                    buy_amount, local_currency_code, local_amount,
                    exchange_rate, usd_equivalent, remarks,
                    branch_id, operator_id, created_at
                ) VALUES (
                    :tx_id, :tx_no, :tx_date,
                    :id_type, :id_number, :name,
                    :country_code, 'CASH', :currency,
                    :amount, 'THB', :local_amount,
                    :rate, :usd_equiv, :remarks,
                    :branch_id, :operator_id, NOW()
                )
            """)
            
            usd_equiv = amount if test_case['currency'] == 'USD' else (amount * rate / 35.5)
            
            session.execute(sql, {
                'tx_id': tx_id,
                'tx_no': tx_no,
                'tx_date': date.today(),
                'id_type': test_case.get('id_type', 'Passport'),
                'id_number': test_case['customer_id'],
                'name': test_case['customer_name'],
                'country_code': test_case.get('country_code', 'TH'),
                'currency': test_case['currency'],
                'amount': amount,
                'local_amount': local_amount,
                'rate': rate,
                'usd_equiv': usd_equiv,
                'remarks': test_case.get('remarks', ''),
                'branch_id': branch_id,
                'operator_id': 1
            })
            
        elif test_case['type'] == 'sell':
            # 创建Sell FX记录
            sql = text("""
                INSERT INTO BOT_SellFX (
                    transaction_id, transaction_no, transaction_date,
                    customer_id_type, customer_id_number, customer_name,
                    customer_country_code, rate_type, sell_currency_code,
                    sell_amount, local_currency_code, local_amount,
                    exchange_rate, usd_equivalent, remarks,
                    branch_id, operator_id, created_at
                ) VALUES (
                    :tx_id, :tx_no, :tx_date,
                    :id_type, :id_number, :name,
                    :country_code, 'CASH', :currency,
                    :amount, 'THB', :local_amount,
                    :rate, :usd_equiv, :remarks,
                    :branch_id, :operator_id, NOW()
                )
            """)
            
            usd_equiv = amount if test_case['currency'] == 'USD' else (amount * rate / 35.5)
            
            session.execute(sql, {
                'tx_id': tx_id,
                'tx_no': tx_no,
                'tx_date': date.today(),
                'id_type': test_case.get('id_type', 'Passport'),
                'id_number': test_case['customer_id'],
                'name': test_case['customer_name'],
                'country_code': test_case.get('country_code', 'TH'),
                'currency': test_case['currency'],
                'amount': amount,
                'local_amount': local_amount,
                'rate': rate,
                'usd_equiv': usd_equiv,
                'remarks': test_case.get('remarks', ''),
                'branch_id': branch_id,
                'operator_id': 1
            })
        
        # 如果使用FCD，创建FCD记录
        if test_case.get('use_fcd'):
            sql = text("""
                INSERT INTO BOT_FCD (
                    transaction_id, account_open_date, bank_name,
                    account_number, currency_code, balance,
                    transaction_amount, usd_equivalent, remarks,
                    branch_id, operator_id, created_at
                ) VALUES (
                    :tx_id, :open_date, :bank_name,
                    :account_no, :currency, :balance,
                    :amount, :usd_equiv, :remarks,
                    :branch_id, :operator_id, NOW()
                )
            """)
            
            usd_equiv = amount if test_case['currency'] == 'USD' else (amount * rate / 35.5)
            
            session.execute(sql, {
                'tx_id': tx_id,
                'open_date': date.today(),
                'bank_name': test_case.get('bank_name', 'Bangkok Bank'),
                'account_no': test_case.get('account_no', 'FCD001'),
                'currency': test_case['currency'],
                'balance': test_case.get('fcd_balance', amount),
                'amount': amount,
                'usd_equiv': usd_equiv,
                'remarks': f"FCD Account Transaction - {test_case.get('remarks', '')}",
                'branch_id': branch_id,
                'operator_id': 1
            })
        
        session.commit()
        
        print(f"[OK] 交易创建成功: {tx_no}")
        print(f"  客户: {test_case['customer_name']}")
        print(f"  类型: {'买入' if test_case['type'] == 'buy' else '卖出'}")
        print(f"  金额: {amount:,} {test_case['currency']} @ {rate} = {local_amount:,} THB")
        if test_case.get('use_fcd'):
            print(f"  [FCD] 使用FCD账户")
        print()
        
        return {
            'id': tx_id,
            'transaction_no': tx_no,
            'currency_id': currency.id,
            'amount': amount,
            'local_amount': local_amount,
            'rate': rate,
            'type': test_case['type']
        }
        
    except Exception as e:
        session.rollback()
        print(f"[ERROR] 创建交易失败: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        DatabaseService.close_session(session)

def generate_amlo_reports_for_transactions(branch_id, transactions):
    """为符合条件的交易生成AMLO报告"""
    from services.repform.report_data_service import ReportDataService
    from services.pdf.amlo_pdf_generator import AMLOPDFGenerator
    import json
    
    session = DatabaseService.get_session()
    amlo_count = 0
    
    try:
        for tx_data, test_case in transactions:
            if not tx_data:
                continue
            
            # 判断是否需要生成AMLO报告
            report_format = None
            
            if tx_data['local_amount'] >= 500000 and tx_data['local_amount'] < 8000000:
                report_format = 'AMLO-1-01'
            elif tx_data['local_amount'] >= 8000000:
                if test_case.get('is_asset', False):
                    report_format = 'AMLO-1-02'
                else:
                    report_format = 'AMLO-1-01'
            elif test_case.get('is_suspicious', False):
                report_format = 'AMLO-1-03'
            
            if not report_format:
                continue
            
            print(f"[AMLO] 生成{report_format}报告: {test_case['customer_name']}")
            
            # 准备预约数据
            reservation_data = {
                'report_type': report_format,
                'customer_id': test_case['customer_id'],
                'customer_name': test_case['customer_name'],
                'currency_id': tx_data['currency_id'],
                'direction': tx_data['type'],
                'amount': tx_data['amount'],
                'local_amount': tx_data['local_amount'],
                'rate': tx_data['rate'],
                'trigger_type': '1',
                'transaction_id': tx_data['id'],
                'branch_id': branch_id,
                'operator_id': 1,
                'form_data': {
                    'occupation': test_case.get('occupation', ''),
                    'address': test_case.get('address', ''),
                    'phone': test_case.get('phone', ''),
                    'purpose': test_case.get('purpose', ''),
                    'funding_source': test_case.get('funding_source', ''),
                    'remarks': test_case.get('remarks', '')
                },
                'exchange_type': 'normal'
            }
            
            # 保存预约
            reservation_id = ReportDataService.save_reservation(session, reservation_data)
            
            # 映射report_type
            report_type_map = {
                'AMLO-1-01': 'CTR',
                'AMLO-1-02': 'ATR',
                'AMLO-1-03': 'STR'
            }
            
            # 保存报告
            report_data = {
                'report_type': report_type_map.get(report_format, 'CTR'),
                'report_format': report_format,
                'branch_id': branch_id,
                'reserved_id': reservation_id,
                'transaction_id': tx_data['id'],
                'customer_id': test_case['customer_id'],
                'customer_name': test_case['customer_name'],
                'transaction_amount': tx_data['local_amount'],
                'transaction_date': date.today(),
                'operator_id': 1,
                'language': 'zh',
                'pdf_filename': '',
                'pdf_path': ''
            }
            
            report_id = ReportDataService.save_amlo_report(session, report_data)
            
            # 获取报告记录
            report_record = session.execute(text("SELECT * FROM AMLOReport WHERE id = :id"), {'id': report_id}).fetchone()
            
            # 准备PDF数据
            form_data = reservation_data['form_data']
            pdf_data = {
                'report_no': report_record.report_no,
                'report_date': datetime.now().strftime('%d/%m/%Y'),
                'customer_name': test_case['customer_name'],
                'customer_id': test_case['customer_id'],
                'customer_id_type': test_case.get('id_type', 'Passport'),
                'occupation': form_data.get('occupation', ''),
                'address': form_data.get('address', ''),
                'phone': form_data.get('phone', ''),
                'nationality': test_case.get('country_code', 'TH'),
                'transaction_date': date.today().strftime('%d/%m/%Y'),
                'transaction_type': '买入外币' if tx_data['type'] == 'buy' else '卖出外币',
                'currency': test_case['currency'],
                'foreign_amount': float(tx_data['amount']),
                'exchange_rate': float(tx_data['rate']),
                'thb_amount': float(tx_data['local_amount']),
                'purpose': form_data.get('purpose', ''),
                'funding_source': form_data.get('funding_source', ''),
                'remarks': form_data.get('remarks', '')
            }
            
            # 确定输出路径
            year = date.today().year
            month = date.today().month
            manager_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'manager', str(year), f"{month:02d}")
            os.makedirs(manager_dir, exist_ok=True)
            
            pdf_filename = f"{report_format}_R{report_record.report_no}.pdf"
            pdf_path = os.path.join(manager_dir, pdf_filename)
            
            # 生成PDF
            generator = AMLOPDFGenerator()
            generator.generate_pdf(report_format, pdf_data, pdf_path)
            
            # 更新PDF路径
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
            
            file_size = os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 0
            print(f"  [OK] {pdf_filename} ({file_size/1024:.2f} KB)")
            
            amlo_count += 1
        
        return amlo_count
        
    except Exception as e:
        session.rollback()
        print(f"[ERROR] 生成AMLO报告失败: {e}")
        import traceback
        traceback.print_exc()
        return amlo_count
    finally:
        DatabaseService.close_session(session)

def generate_bot_excel_report(branch_id):
    """使用模板生成BOT Excel报表（保存到manager目录）"""
    session = DatabaseService.get_session()
    
    try:
        print("="*80)
        print("[BOT Excel] 生成BOT合规报表（保存到manager目录）")
        print("="*80)
        
        # 获取当前月份（佛历）
        today = date.today()
        report_month = today.month
        report_year = today.year + 543  # 转换为佛历
        
        print(f"\n报告期间: {report_year}/{report_month} (佛历)")
        print(f"公历: {today.year}/{today.month}")
        
        # 使用模板生成器（自动保存到manager目录）
        output_path = BOTTemplateBasedGenerator.generate_report(
            db_session=session,
            branch_id=branch_id,
            report_month=report_month,
            report_year=report_year
        )
        
        file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
        
        print(f"\n[OK] BOT Excel报表生成成功!")
        print(f"  文件: {os.path.basename(output_path)}")
        print(f"  大小: {file_size / 1024:.2f} KB")
        print(f"  路径: {os.path.abspath(output_path)}")
        
        return output_path
        
    except Exception as e:
        print(f"[ERROR] 生成BOT Excel失败: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        DatabaseService.close_session(session)

def main():
    print("="*80)
    print("完整的7笔交易测试 + AMLO & BOT报表生成")
    print("="*80)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 清理旧数据
    clear_today_data()
    
    # 获取A005网点
    session = DatabaseService.get_session()
    try:
        branch = session.query(Branch).filter_by(branch_code='A005').first()
        if not branch:
            branch = session.query(Branch).filter_by(id=1).first()
        branch_id = branch.id
        print(f"[OK] 测试网点: {branch.branch_name} (Code: {branch.branch_code})\n")
    finally:
        DatabaseService.close_session(session)
    
    # 定义7笔测试交易
    test_cases = [
        {
            'name': '交易1: AMLO 1-01 + BOT Buy FX',
            'customer_name': 'Somchai Suksai',
            'customer_id': 'TH1234567890123',
            'id_type': 'Thai ID',
            'country_code': 'TH',
            'currency': 'USD',
            'amount': 70000,
            'rate': 35.50,
            'type': 'buy',
            'occupation': 'นักธุรกิจ (Businessman)',
            'address': 'Bangkok, Thailand',
            'purpose': 'เดินทาง/ท่องเที่ยว (Travel)',
            'funding_source': 'เงินเดือน (Salary)',
            'remarks': 'Test AMLO-1-01 + BOT Buy FX'
        },
        {
            'name': '交易2: AMLO 1-02 + BOT Buy FX (资产)',
            'customer_name': 'ABC Company Limited',
            'customer_id': 'TAX1234567890',
            'id_type': 'Corporate',
            'country_code': 'TH',
            'currency': 'USD',
            'amount': 300000,
            'rate': 35.60,
            'type': 'buy',
            'occupation': 'บริษัท (Company)',
            'address': 'Sukhumvit Road, Bangkok',
            'purpose': 'ลงทุน/ซื้ออสังหาริมทรัพย์ (Real Estate Investment)',
            'funding_source': 'สินทรัพย์หลักประกัน (Collateral Assets)',
            'remarks': 'Test AMLO-1-02 Asset Transaction',
            'is_asset': True
        },
        {
            'name': '交易3: AMLO 1-03 (可疑) + BOT Buy FX',
            'customer_name': 'John Smith',
            'customer_id': 'PASS123456789',
            'id_type': 'Passport',
            'country_code': 'US',
            'currency': 'USD',
            'amount': 50000,
            'rate': 35.45,
            'type': 'buy',
            'occupation': 'ไม่ทราบ (Unknown)',
            'address': 'New York, USA',
            'purpose': 'ไม่ระบุ (Unspecified)',
            'funding_source': 'เงินสด (Cash)',
            'remarks': 'Suspicious - Multiple large transactions in short period',
            'is_suspicious': True
        },
        {
            'name': '交易4: BOT Sell FX',
            'customer_name': 'Nittaya Phongphan',
            'customer_id': 'TH9876543210987',
            'id_type': 'Thai ID',
            'country_code': 'TH',
            'currency': 'EUR',
            'amount': 40000,
            'rate': 38.20,
            'type': 'sell',
            'occupation': 'พนักงานบริษัท (Employee)',
            'address': 'Chiang Mai, Thailand',
            'purpose': 'กลับจากการเดินทาง (Return from travel)',
            'funding_source': 'เงินเหลือจากการเดินทาง (Travel funds)',
            'remarks': 'Test BOT Sell FX'
        },
        {
            'name': '交易5: BOT Buy FX (大额)',
            'customer_name': 'David Lee',
            'customer_id': 'PASS987654321',
            'id_type': 'Passport',
            'country_code': 'SG',
            'currency': 'USD',
            'amount': 150000,
            'rate': 35.55,
            'type': 'buy',
            'occupation': 'นักลงทุน (Investor)',
            'address': 'Singapore',
            'purpose': 'ธุรกิจ (Business)',
            'funding_source': 'รายได้จากธุรกิจ (Business income)',
            'remarks': 'Test Large BOT Buy FX + AMLO-1-01'
        },
        {
            'name': '交易6: BOT FCD + BOT Buy FX',
            'customer_name': 'XYZ Trading Company',
            'customer_id': 'TAX9876543210',
            'id_type': 'Corporate',
            'country_code': 'TH',
            'currency': 'USD',
            'amount': 80000,
            'rate': 35.50,
            'type': 'buy',
            'occupation': 'บริษัทนำเข้า-ส่งออก (Import-Export)',
            'address': 'Samut Prakan, Thailand',
            'purpose': 'นำเข้าสินค้า (Import goods)',
            'funding_source': 'บัญชี FCD (FCD Account)',
            'remarks': 'Test BOT FCD + Buy FX',
            'use_fcd': True,
            'bank_name': 'Bangkok Bank',
            'account_no': 'FCD123456789',
            'fcd_balance': 100000
        },
        {
            'name': '交易7: AMLO 1-01 + BOT Buy FX (小额)',
            'customer_name': 'Maria Garcia',
            'customer_id': 'PASS456789123',
            'id_type': 'Passport',
            'country_code': 'ES',
            'currency': 'EUR',
            'amount': 15000,
            'rate': 38.00,
            'type': 'buy',
            'occupation': 'นักท่องเที่ยว (Tourist)',
            'address': 'Madrid, Spain',
            'purpose': 'ท่องเที่ยว (Tourism)',
            'funding_source': 'เงินออม (Savings)',
            'remarks': 'Test small amount + AMLO-1-01'
        }
    ]
    
    print("="*80)
    print("[第1步] 创建7笔测试交易")
    print("="*80)
    print()
    
    transactions = []
    for idx, test_case in enumerate(test_cases, 1):
        print(f"[{idx}/7] {test_case['name']}")
        print("-"*80)
        
        tx_data = create_transaction_with_bot_records(branch_id, test_case)
        transactions.append((tx_data, test_case))
    
    # 生成AMLO报告
    print("="*80)
    print("[第2步] 生成AMLO报告")
    print("="*80)
    print()
    
    amlo_count = generate_amlo_reports_for_transactions(branch_id, transactions)
    
    print(f"\n[OK] 生成了 {amlo_count} 个AMLO报告\n")
    
    # 生成BOT Excel报表
    bot_excel_path = generate_bot_excel_report(branch_id)
    
    # 最终总结
    print("\n" + "="*80)
    print("测试完成总结")
    print("="*80)
    
    print(f"\n✅ 交易记录: 创建了 {len([t for t, _ in transactions if t])} 笔交易")
    print(f"✅ AMLO报告: 生成了 {amlo_count} 个PDF")
    print(f"✅ BOT报表: 生成了 1 个Excel（包含多个sheet）")
    
    print(f"\n📂 查看文件:")
    print(f"  AMLO: explorer \"D:\\Code\\ExchangeNew\\src\\manager\\2025\\10\"")
    if bot_excel_path:
        print(f"  BOT:  explorer \"{os.path.dirname(os.path.abspath(bot_excel_path))}\"")
    
    print(f"\n🌐 在线查看:")
    print(f"  - AMLO报告: http://localhost:8080/amlo/reports")
    print(f"  - BOT查询:  http://localhost:8080/bot/reports")

if __name__ == "__main__":
    main()

