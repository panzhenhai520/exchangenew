#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移脚本：更新已有币种的自定义图标信息
从 currency_templates 表获取自定义图标信息，更新到 currencies 表
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import get_db_url
from sqlalchemy import create_engine, text

def update_existing_currencies_custom_flags():
    """更新已有币种的自定义图标信息"""
    
    # 获取数据库连接
    database_url = get_db_url()
    engine = create_engine(database_url)
    
    try:
        with engine.begin() as connection:
            # 查询需要更新的币种
            # 查找在 currencies 表中存在但在 currency_templates 表中有自定义图标的币种
            update_sql = """
            UPDATE currencies c
            INNER JOIN currency_templates ct ON c.currency_code = ct.currency_code
            SET c.custom_flag_filename = ct.custom_flag_filename
            WHERE ct.custom_flag_filename IS NOT NULL 
            AND ct.custom_flag_filename != ''
            AND (c.custom_flag_filename IS NULL OR c.custom_flag_filename = '')
            """
            
            result = connection.execute(text(update_sql))
            updated_count = result.rowcount
            
            print(f"✅ 成功更新 {updated_count} 个币种的自定义图标信息")
            
            # 显示更新详情
            detail_sql = """
            SELECT c.currency_code, c.currency_name, c.custom_flag_filename
            FROM currencies c
            INNER JOIN currency_templates ct ON c.currency_code = ct.currency_code
            WHERE ct.custom_flag_filename IS NOT NULL 
            AND ct.custom_flag_filename != ''
            """
            
            detail_result = connection.execute(text(detail_sql))
            updated_currencies = detail_result.fetchall()
            
            if updated_currencies:
                print("\n📋 已更新的币种列表：")
                for currency in updated_currencies:
                    print(f"  - {currency[0]} ({currency[1]}): {currency[2]}")
            else:
                print("\nℹ️  没有找到需要更新的币种")
                
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("开始迁移：更新已有币种的自定义图标信息...")
    success = update_existing_currencies_custom_flags()
    if success:
        print("✅ 迁移完成")
    else:
        print("❌ 迁移失败")
        sys.exit(1) 