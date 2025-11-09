#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移脚本：为 currencies 表添加 custom_flag_filename 字段
用于存储自定义币种图标的文件名
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import get_db_url
from sqlalchemy import create_engine, text

def add_custom_flag_to_currencies():
    """为 currencies 表添加 custom_flag_filename 字段"""
    
    # 获取数据库连接
    database_url = get_db_url()
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as connection:
            # 检查字段是否已存在
            check_sql = """
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name = 'currencies' 
            AND column_name = 'custom_flag_filename'
            """
            
            result = connection.execute(text(check_sql))
            column_exists = result.scalar() > 0
            
            if not column_exists:
                # 添加字段
                add_column_sql = """
                ALTER TABLE currencies 
                ADD COLUMN custom_flag_filename VARCHAR(255)
                """
                
                connection.execute(text(add_column_sql))
                connection.commit()
                print("✅ 成功添加 custom_flag_filename 字段到 currencies 表")
            else:
                print("ℹ️  custom_flag_filename 字段已存在，跳过迁移")
                
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("开始迁移：为 currencies 表添加 custom_flag_filename 字段...")
    success = add_custom_flag_to_currencies()
    if success:
        print("✅ 迁移完成")
    else:
        print("❌ 迁移失败")
        sys.exit(1) 