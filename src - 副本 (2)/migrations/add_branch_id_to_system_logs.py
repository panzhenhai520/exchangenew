#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库迁移脚本：为system_logs表添加branch_id字段
创建时间：2025-07-03
迁移目的：支持多语言日志服务中的网点关联功能
"""

import sqlite3
import os
import sys
from datetime import datetime

def add_branch_id_to_system_logs():
    """为system_logs表添加branch_id字段"""
    
    # 获取数据库路径
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'exchange_system.db')
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查branch_id字段是否已存在
        cursor.execute("PRAGMA table_info(system_logs)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'branch_id' in columns:
            print("branch_id字段已存在于system_logs表中，无需迁移")
            return True
        
        # 备份原表数据
        print("正在备份system_logs表数据...")
        cursor.execute("CREATE TABLE system_logs_backup AS SELECT * FROM system_logs")
        
        # 添加branch_id字段
        print("正在添加branch_id字段...")
        cursor.execute("""
            ALTER TABLE system_logs 
            ADD COLUMN branch_id INTEGER REFERENCES branches(id)
        """)
        
        # 提交更改
        conn.commit()
        print("迁移完成：已成功为system_logs表添加branch_id字段")
        
        # 显示表结构
        cursor.execute("PRAGMA table_info(system_logs)")
        columns = cursor.fetchall()
        print("\n更新后的system_logs表结构:")
        for column in columns:
            print(f"  {column[1]} {column[2]} {'NOT NULL' if column[3] else 'NULL'}")
        
        return True
        
    except Exception as e:
        print(f"迁移失败: {e}")
        # 尝试恢复备份
        try:
            cursor.execute("DROP TABLE IF EXISTS system_logs")
            cursor.execute("ALTER TABLE system_logs_backup RENAME TO system_logs")
            conn.commit()
            print("已恢复到迁移前状态")
        except:
            print("恢复备份失败，请手动检查数据库")
        return False
    
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """主函数"""
    print("开始执行system_logs表迁移...")
    print(f"迁移时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    success = add_branch_id_to_system_logs()
    
    print("-" * 50)
    if success:
        print("迁移成功完成！")
        return 0
    else:
        print("迁移失败！")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 