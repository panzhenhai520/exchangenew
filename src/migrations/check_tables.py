#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import get_db_url
from sqlalchemy import create_engine, text

def check_tables():
    """检查面值相关表是否创建成功"""
    try:
        database_url = get_db_url()
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # 检查表是否存在
            result = conn.execute(text("SHOW TABLES LIKE '%denomination%'"))
            tables = [row[0] for row in result]
            
            print("✅ 面值相关表:")
            for table in tables:
                print(f"  - {table}")
            
            if not tables:
                print("❌ 没有找到面值相关表")
                return False
            
            # 检查表结构
            for table in tables:
                print(f"\n📋 {table} 表结构:")
                result = conn.execute(text(f"DESCRIBE {table}"))
                for row in result:
                    print(f"  - {row[0]}: {row[1]} {row[2] if row[2] else ''}")
            
            return True
            
    except Exception as e:
        print(f"❌ 检查失败: {str(e)}")
        return False

if __name__ == '__main__':
    check_tables()