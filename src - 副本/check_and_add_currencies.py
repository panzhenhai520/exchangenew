#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
检查并添加测试所需的货币
"""

import sys
import os
import io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure stdout/stderr encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from services.db_service import DatabaseService
from models.exchange_models import Currency, Country

def check_and_add_currencies():
    """检查并添加USD和EUR货币"""
    print("正在检查货币数据...")

    with DatabaseService.get_session() as session:
        # 检查现有货币
        currencies = session.query(Currency).all()
        print(f"\n当前数据库中有 {len(currencies)} 种货币")

        # 检查USD
        usd = session.query(Currency).filter_by(currency_code='USD').first()
        if usd:
            print(f"✅ USD已存在: ID={usd.id}, Name={usd.currency_name}")
        else:
            print("❌ USD不存在，正在添加...")
            # 获取美国
            usa = session.query(Country).filter_by(country_code='US').first()
            if not usa:
                print("  添加美国...")
                usa = Country(
                    country_code='US',
                    country_name='United States',
                    country_name_cn='美国',
                    country_name_th='สหรัฐอเมริกา'
                )
                session.add(usa)
                session.flush()

            usd = Currency(
                currency_code='USD',
                currency_name='US Dollar',
                currency_name_cn='美元',
                currency_name_th='ดอลลาร์สหรัฐ',
                currency_symbol='$',
                country_id=usa.id,
                is_active=True
            )
            session.add(usd)
            session.commit()
            print(f"✅ USD已添加: ID={usd.id}")

        # 检查EUR
        eur = session.query(Currency).filter_by(currency_code='EUR').first()
        if eur:
            print(f"✅ EUR已存在: ID={eur.id}, Name={eur.currency_name}")
        else:
            print("❌ EUR不存在，正在添加...")
            # 获取德国作为EUR的代表国家
            germany = session.query(Country).filter_by(country_code='DE').first()
            if not germany:
                print("  添加德国...")
                germany = Country(
                    country_code='DE',
                    country_name='Germany',
                    country_name_cn='德国',
                    country_name_th='เยอรมนี'
                )
                session.add(germany)
                session.flush()

            eur = Currency(
                currency_code='EUR',
                currency_name='Euro',
                currency_name_cn='欧元',
                currency_name_th='ยูโร',
                currency_symbol='€',
                country_id=germany.id,
                is_active=True
            )
            session.add(eur)
            session.commit()
            print(f"✅ EUR已添加: ID={eur.id}")

        # 检查THB
        thb = session.query(Currency).filter_by(currency_code='THB').first()
        if thb:
            print(f"✅ THB已存在: ID={thb.id}, Name={thb.currency_name}")
        else:
            print("❌ THB不存在，正在添加...")
            thailand = session.query(Country).filter_by(country_code='TH').first()
            if not thailand:
                print("  添加泰国...")
                thailand = Country(
                    country_code='TH',
                    country_name='Thailand',
                    country_name_cn='泰国',
                    country_name_th='ประเทศไทย'
                )
                session.add(thailand)
                session.flush()

            thb = Currency(
                currency_code='THB',
                currency_name='Thai Baht',
                currency_name_cn='泰铢',
                currency_name_th='บาทไทย',
                currency_symbol='฿',
                country_id=thailand.id,
                is_active=True
            )
            session.add(thb)
            session.commit()
            print(f"✅ THB已添加: ID={thb.id}")

        print("\n✅ 货币检查完成！")

        # 列出所有货币
        currencies = session.query(Currency).filter(
            Currency.currency_code.in_(['USD', 'EUR', 'THB'])
        ).all()
        print(f"\n测试所需货币:")
        for c in currencies:
            print(f"  - {c.currency_code}: {c.currency_name} (ID={c.id})")

if __name__ == '__main__':
    check_and_add_currencies()
