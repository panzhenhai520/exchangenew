#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：添加业务时间字段到EODStatus表
执行时间：2025-01-07
作者：系统自动生成
"""

import sqlite3
import os
from datetime import datetime

def add_business_time_fields():
    """添加业务时间字段到EODStatus表"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'exchange_system.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(eod_status)")
        columns = [column[1] for column in cursor.fetchall()]
        
        changes_made = False
        
        # 添加business_start_time字段
        if 'business_start_time' not in columns:
            cursor.execute('''
                ALTER TABLE eod_status 
                ADD COLUMN business_start_time DATETIME NULL
            ''')
            print("✅ 已添加 business_start_time 字段")
            changes_made = True
        else:
            print("ℹ️  business_start_time 字段已存在")
        
        # 添加business_end_time字段
        if 'business_end_time' not in columns:
            cursor.execute('''
                ALTER TABLE eod_status 
                ADD COLUMN business_end_time DATETIME NULL
            ''')
            print("✅ 已添加 business_end_time 字段")
            changes_made = True
        else:
            print("ℹ️  business_end_time 字段已存在")
        
        if changes_made:
            conn.commit()
            print("✅ 数据库迁移完成")
        else:
            print("ℹ️  数据库已是最新状态，无需迁移")
            
    except sqlite3.Error as e:
        print(f"❌ 数据库迁移失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def rollback_business_time_fields():
    """回滚业务时间字段（SQLite不支持DROP COLUMN，需要重建表）"""
    print("⚠️  警告：SQLite不支持删除列，回滚需要重建表结构")
    print("⚠️  建议使用备份文件进行回滚")
    
if __name__ == "__main__":
    print("🔄 开始数据库迁移...")
    add_business_time_fields()
    print("🎉 迁移完成！") 