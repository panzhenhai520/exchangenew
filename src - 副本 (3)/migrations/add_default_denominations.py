#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import get_db_url
from sqlalchemy import create_engine, text

def add_default_denominations():
    """为现有币种添加默认面值"""
    
    # 常见币种的默认面值
    default_denominations = {
        'USD': [
            (1, 'bill'), (5, 'bill'), (10, 'bill'), (20, 'bill'), (50, 'bill'), (100, 'bill'),
            (0.01, 'coin'), (0.05, 'coin'), (0.10, 'coin'), (0.25, 'coin'), (0.50, 'coin'), (1, 'coin')
        ],
        'EUR': [
            (5, 'bill'), (10, 'bill'), (20, 'bill'), (50, 'bill'), (100, 'bill'), (200, 'bill'), (500, 'bill'),
            (0.01, 'coin'), (0.02, 'coin'), (0.05, 'coin'), (0.10, 'coin'), (0.20, 'coin'), (0.50, 'coin'), (1, 'coin'), (2, 'coin')
        ],
        'GBP': [
            (5, 'bill'), (10, 'bill'), (20, 'bill'), (50, 'bill'),
            (0.01, 'coin'), (0.02, 'coin'), (0.05, 'coin'), (0.10, 'coin'), (0.20, 'coin'), (0.50, 'coin'), (1, 'coin'), (2, 'coin')
        ],
        'JPY': [
            (1000, 'bill'), (2000, 'bill'), (5000, 'bill'), (10000, 'bill'),
            (1, 'coin'), (5, 'coin'), (10, 'coin'), (50, 'coin'), (100, 'coin'), (500, 'coin')
        ],
        'CNY': [
            (1, 'bill'), (5, 'bill'), (10, 'bill'), (20, 'bill'), (50, 'bill'), (100, 'bill'),
            (0.01, 'coin'), (0.02, 'coin'), (0.05, 'coin'), (0.1, 'coin'), (0.2, 'coin'), (0.5, 'coin'), (1, 'coin')
        ],
        'HKD': [
            (10, 'bill'), (20, 'bill'), (50, 'bill'), (100, 'bill'), (500, 'bill'), (1000, 'bill'),
            (0.10, 'coin'), (0.20, 'coin'), (0.50, 'coin'), (1, 'coin'), (2, 'coin'), (5, 'coin'), (10, 'coin')
        ]
    }
    
    try:
        database_url = get_db_url()
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            trans = conn.begin()
            
            try:
                # 获取所有币种（排除本币）
                result = conn.execute(text("""
                    SELECT c.id, c.currency_code 
                    FROM currencies c 
                    LEFT JOIN branches b ON c.id = b.base_currency_id 
                    WHERE b.base_currency_id IS NULL
                """))
                currencies = {row[1]: row[0] for row in result}
                
                print(f"找到 {len(currencies)} 个币种")
                
                # 为每个币种添加默认面值
                for currency_code, currency_id in currencies.items():
                    if currency_code in default_denominations:
                        denominations = default_denominations[currency_code]
                        print(f"为 {currency_code} 添加 {len(denominations)} 个面值...")
                        
                        for i, (value, type_) in enumerate(denominations):
                            # 检查面值是否已存在
                            check_result = conn.execute(text("""
                                SELECT COUNT(*) FROM currency_denominations 
                                WHERE currency_id = :currency_id 
                                AND denomination_value = :value 
                                AND denomination_type = :type
                            """), {
                                'currency_id': currency_id,
                                'value': value,
                                'type': type_
                            })
                            
                            if check_result.scalar() == 0:
                                conn.execute(text("""
                                    INSERT INTO currency_denominations 
                                    (currency_id, denomination_value, denomination_type, sort_order, is_active)
                                    VALUES (:currency_id, :value, :type, :sort_order, 1)
                                """), {
                                    'currency_id': currency_id,
                                    'value': value,
                                    'type': type_,
                                    'sort_order': i
                                })
                                print(f"  ✅ 添加面值: {value} {type_}")
                            else:
                                print(f"  ⚠️  面值已存在: {value} {type_}")
                
                trans.commit()
                print("✅ 默认面值添加成功！")
                
            except Exception as e:
                trans.rollback()
                print(f"❌ 添加默认面值失败: {str(e)}")
                raise
                
    except Exception as e:
        print(f"❌ 添加默认面值失败: {str(e)}")
        raise

if __name__ == '__main__':
    add_default_denominations()