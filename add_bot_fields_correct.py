# -*- coding: utf-8 -*-
"""
使用正确的ENUM值添加BOT报表字段
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.db_service import SessionLocal
from sqlalchemy import text

print("Adding BOT Report Fields...")

session = SessionLocal()

try:
    # BOT_BuyFX fields
    bot_buy_fields = [
        ('report_date', 'DATE', 50, '报告日期', 'Report Date', 'วันที่รายงาน', 'BOT报告', 1, 1),
        ('transaction_no', 'VARCHAR', 50, '交易编号', 'Transaction No', 'เลขที่ธุรกรรม', 'BOT交易', 10, 1),
        ('transaction_date', 'DATE', 50, '交易日期', 'Transaction Date', 'วันที่ทำธุรกรรม', 'BOT交易', 11, 1),
        ('customer_id', 'VARCHAR', 20, '客户证件号', 'Customer ID', 'เลขประจำตัว', 'BOT客户', 20, 1),
        ('customer_name', 'VARCHAR', 200, '客户姓名', 'Customer Name', 'ชื่อลูกค้า', 'BOT客户', 21, 1),
        ('currency_code', 'VARCHAR', 10, '货币代码', 'Currency Code', 'สกุลเงิน', 'BOT货币', 30, 1),
        ('foreign_amount', 'DECIMAL', None, '外币金额', 'Foreign Amount', 'จำนวนเงินต่างประเทศ', 'BOT货币', 31, 1),
        ('exchange_rate', 'DECIMAL', None, '汇率', 'Exchange Rate', 'อัตราแลกเปลี่ยน', 'BOT货币', 32, 1),
        ('thb_amount', 'DECIMAL', None, '泰铢金额', 'THB Amount', 'จำนวนเงินบาท', 'BOT货币', 33, 1),
        ('funding_source', 'VARCHAR', 200, '资金来源', 'Funding Source', 'ที่มาของเงิน', 'BOT交易', 40, 0),
    ]

    # Delete existing BOT fields
    session.execute(text("DELETE FROM report_fields WHERE report_type IN ('BOT_BuyFX', 'BOT_SellFX')"))

    # Add BOT_BuyFX fields
    for field in bot_buy_fields:
        session.execute(text('''
            INSERT INTO report_fields
            (field_name, field_type, field_length, field_cn_name, field_en_name, field_th_name,
             report_type, field_group, fill_order, is_required, is_active, created_at)
            VALUES
            (:name, :type, :length, :cn, :en, :th, 'BOT_BuyFX', :group, :order, :required, 1, NOW())
        '''), {
            'name': field[0],
            'type': field[1],
            'length': field[2],
            'cn': field[3],
            'en': field[4],
            'th': field[5],
            'group': field[6],
            'order': field[7],
            'required': field[8]
        })

    print(f"  [OK] Added {len(bot_buy_fields)} fields to BOT_BuyFX")

    # Add BOT_SellFX fields (similar to BuyFX but with different purpose)
    bot_sell_fields = [
        ('report_date', 'DATE', 50, '报告日期', 'Report Date', 'วันที่รายงาน', 'BOT报告', 1, 1),
        ('transaction_no', 'VARCHAR', 50, '交易编号', 'Transaction No', 'เลขที่ธุรกรรม', 'BOT交易', 10, 1),
        ('transaction_date', 'DATE', 50, '交易日期', 'Transaction Date', 'วันที่ทำธุรกรรม', 'BOT交易', 11, 1),
        ('customer_id', 'VARCHAR', 20, '客户证件号', 'Customer ID', 'เลขประจำตัว', 'BOT客户', 20, 1),
        ('customer_name', 'VARCHAR', 200, '客户姓名', 'Customer Name', 'ชื่อลูกค้า', 'BOT客户', 21, 1),
        ('currency_code', 'VARCHAR', 10, '货币代码', 'Currency Code', 'สกุลเงิน', 'BOT货币', 30, 1),
        ('foreign_amount', 'DECIMAL', None, '外币金额', 'Foreign Amount', 'จำนวนเงินต่างประเทศ', 'BOT货币', 31, 1),
        ('exchange_rate', 'DECIMAL', None, '汇率', 'Exchange Rate', 'อัตราแลกเปลี่ยน', 'BOT货币', 32, 1),
        ('thb_amount', 'DECIMAL', None, '泰铢金额', 'THB Amount', 'จำนวนเงินบาท', 'BOT货币', 33, 1),
        ('payment_purpose', 'VARCHAR', 200, '付款目的', 'Payment Purpose', 'จุดหมายปลายทาง', 'BOT交易', 40, 0),
    ]

    for field in bot_sell_fields:
        session.execute(text('''
            INSERT INTO report_fields
            (field_name, field_type, field_length, field_cn_name, field_en_name, field_th_name,
             report_type, field_group, fill_order, is_required, is_active, created_at)
            VALUES
            (:name, :type, :length, :cn, :en, :th, 'BOT_SellFX', :group, :order, :required, 1, NOW())
        '''), {
            'name': field[0],
            'type': field[1],
            'length': field[2],
            'cn': field[3],
            'en': field[4],
            'th': field[5],
            'group': field[6],
            'order': field[7],
            'required': field[8]
        })

    print(f"  [OK] Added {len(bot_sell_fields)} fields to BOT_SellFX")

    session.commit()

    # Verify
    print("\nVerification:")
    for rt in ['BOT_BuyFX', 'BOT_SellFX']:
        result = session.execute(text('''
            SELECT COUNT(*) as cnt FROM report_fields WHERE report_type = :rt
        '''), {'rt': rt})
        count = result.scalar()
        print(f"  {rt}: {count} fields")

    print("\n[OK] BOT report fields added successfully!")

except Exception as e:
    session.rollback()
    print(f"\n[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

finally:
    session.close()
