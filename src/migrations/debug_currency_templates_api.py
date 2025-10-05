#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试currency_templates API返回的数据
"""

import sys
import os
import requests
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def debug_currency_templates_api():
    """调试currency_templates API返回的数据"""
    
    try:
        # 模拟API调用
        url = "http://localhost:5001/api/rates/currency_templates"
        
        # 获取测试用的token（这里需要先登录获取token）
        print("🔍 正在调试currency_templates API...")
        print(f"📡 API地址: {url}")
        
        # 由于需要认证，我们直接查询数据库来模拟API返回的数据
        from services.db_service import get_db_url
        from sqlalchemy import create_engine, text
        
        database_url = get_db_url()
        engine = create_engine(database_url)
        
        with engine.connect() as connection:
            # 查询currency_templates表中的AS币种
            sql = """
            SELECT id, currency_code, currency_name, country, flag_code, custom_flag_filename
            FROM currency_templates 
            WHERE currency_code = 'AS'
            """
            
            result = connection.execute(text(sql))
            templates = result.fetchall()
            
            print("\n📋 API应该返回的AS币种数据：")
            for template in templates:
                template_dict = {
                    'id': template[0],
                    'currency_code': template[1],
                    'currency_name': template[2],
                    'country': template[3],
                    'flag_code': template[4],
                    'custom_flag_filename': template[5]
                }
                print(f"  - {json.dumps(template_dict, ensure_ascii=False, indent=2)}")
                
            # 检查是否有其他AS币种记录
            all_as_sql = """
            SELECT id, currency_code, currency_name, country, flag_code, custom_flag_filename
            FROM currency_templates 
            WHERE currency_code LIKE '%AS%' OR currency_name LIKE '%AS%'
            """
            
            all_result = connection.execute(text(all_as_sql))
            all_templates = all_result.fetchall()
            
            print(f"\n📋 所有包含AS的币种模板（共{len(all_templates)}个）：")
            for template in all_templates:
                print(f"  - ID: {template[0]}, 代码: {template[1]}, 名称: {template[2]}, 国家: {template[3]}")
                
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("开始调试currency_templates API...")
    success = debug_currency_templates_api()
    if success:
        print("✅ 调试完成")
    else:
        print("❌ 调试失败")
        sys.exit(1) 