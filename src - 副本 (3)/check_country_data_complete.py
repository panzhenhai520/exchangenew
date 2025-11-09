#!/usr/bin/env python3
"""
检查国家数据的完整性
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from sqlalchemy import text

def check_country_data_complete():
    session = DatabaseService.get_session()
    try:
        print("检查国家数据完整性:")
        
        # 检查总国家数
        total_countries = session.execute(text("""
            SELECT COUNT(*) FROM countries WHERE is_active = TRUE
        """)).fetchone()
        print(f"总国家数: {total_countries[0]}")
        
        # 检查缺少英文名称的国家
        missing_en = session.execute(text("""
            SELECT country_code, country_name_zh 
            FROM countries 
            WHERE is_active = TRUE 
            AND (country_name_en IS NULL OR country_name_en = '')
            ORDER BY country_name_zh
        """)).fetchall()
        
        print(f"\n缺少英文名称的国家数: {len(missing_en)}")
        if missing_en:
            print("前10个缺少英文名称的国家:")
            for i, country in enumerate(missing_en[:10]):
                print(f"  {i+1}. {country[0]}: {country[1]}")
        
        # 检查缺少泰文名称的国家
        missing_th = session.execute(text("""
            SELECT country_code, country_name_zh 
            FROM countries 
            WHERE is_active = TRUE 
            AND (country_name_th IS NULL OR country_name_th = '')
            ORDER BY country_name_zh
        """)).fetchall()
        
        print(f"\n缺少泰文名称的国家数: {len(missing_th)}")
        if missing_th:
            print("前10个缺少泰文名称的国家:")
            for i, country in enumerate(missing_th[:10]):
                print(f"  {i+1}. {country[0]}: {country[1]}")
        
        # 检查完整数据的国家
        complete_countries = session.execute(text("""
            SELECT COUNT(*) FROM countries 
            WHERE is_active = TRUE 
            AND country_name_zh IS NOT NULL AND country_name_zh != ''
            AND country_name_en IS NOT NULL AND country_name_en != ''
            AND country_name_th IS NOT NULL AND country_name_th != ''
        """)).fetchone()
        
        print(f"\n完整数据的国家数: {complete_countries[0]}")
        print(f"完整率: {complete_countries[0] / total_countries[0] * 100:.1f}%")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    check_country_data_complete()
