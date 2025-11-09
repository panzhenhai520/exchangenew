#!/usr/bin/env python3
"""
检查国家数据
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from sqlalchemy import text

def check_country_data():
    session = DatabaseService.get_session()
    try:
        print("检查国家数据:")
        
        # 检查前5个国家的数据
        countries = session.execute(text("""
            SELECT country_code, country_name_zh, country_name_en, country_name_th 
            FROM countries 
            WHERE is_active = TRUE 
            ORDER BY sort_order
            LIMIT 5
        """)).fetchall()
        
        for c in countries:
            zh_name = c[1] if c[1] else 'NULL'
            en_name = c[2] if c[2] else 'NULL'
            th_name = c[3] if c[3] else 'NULL'
            print(f"{c[0]}: 中文={zh_name}, 英文={en_name}, 泰文={th_name}")
        
        # 检查是否有英文名称为空的国家
        empty_en = session.execute(text("""
            SELECT COUNT(*) FROM countries 
            WHERE is_active = TRUE AND (country_name_en IS NULL OR country_name_en = '')
        """)).fetchone()
        
        print(f"\n英文名称为空的国家数量: {empty_en[0]}")
        
        # 检查是否有泰文名称为空的国家
        empty_th = session.execute(text("""
            SELECT COUNT(*) FROM countries 
            WHERE is_active = TRUE AND (country_name_th IS NULL OR country_name_th = '')
        """)).fetchone()
        
        print(f"泰文名称为空的国家数量: {empty_th[0]}")
        
    except Exception as e:
        print(f"错误: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_country_data()
