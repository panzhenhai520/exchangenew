#!/usr/bin/env python3
"""
数据库迁移：为exchange_rates表添加批量保存相关字段
创建时间：2025-07-05
目的：支持今日汇率管理页面的绿色小勾显示逻辑
"""

import sqlite3
import os
from datetime import datetime

def migrate():
    """执行数据库迁移"""
    # 数据库文件路径
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'exchange_system.db')
    
    print(f"开始迁移数据库：{db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(exchange_rates)")
        columns = [column[1] for column in cursor.fetchall()]
        
        fields_to_add = [
            ('batch_saved', 'INTEGER DEFAULT 0'),
            ('batch_saved_time', 'DATETIME'),
            ('batch_saved_by', 'VARCHAR(100)')
        ]
        
        # 添加缺失的字段
        for field_name, field_type in fields_to_add:
            if field_name not in columns:
                sql = f"ALTER TABLE exchange_rates ADD COLUMN {field_name} {field_type}"
                print(f"执行SQL: {sql}")
                cursor.execute(sql)
                print(f"✓ 成功添加字段: {field_name}")
            else:
                print(f"⚠ 字段已存在: {field_name}")
        
        # 提交更改
        conn.commit()
        print("✓ 数据库迁移成功完成")
        
        # 验证字段添加结果
        cursor.execute("PRAGMA table_info(exchange_rates)")
        all_columns = [column[1] for column in cursor.fetchall()]
        print(f"当前exchange_rates表的所有字段: {all_columns}")
        
    except Exception as e:
        print(f"❌ 数据库迁移失败: {str(e)}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def rollback():
    """回滚迁移（删除添加的字段）"""
    # SQLite不支持DROP COLUMN，需要重建表来删除字段
    print("警告：SQLite不支持删除字段，回滚操作需要重建表，这可能导致数据丢失")
    print("如需回滚，请手动处理或重新初始化数据库")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
        rollback()
    else:
        migrate() 