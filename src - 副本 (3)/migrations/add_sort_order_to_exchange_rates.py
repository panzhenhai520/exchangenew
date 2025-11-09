"""
添加sort_order字段到exchange_rates表
创建时间: 2025-01-03
"""

import sqlite3
import os
from datetime import datetime

def upgrade():
    """升级数据库：添加sort_order字段到exchange_rates表"""
    try:
        # 数据库文件路径
        db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'exchange_system.db')
        
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"[{datetime.now()}] 开始为exchange_rates表添加sort_order字段...")
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(exchange_rates)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'sort_order' in columns:
            print(f"[{datetime.now()}] sort_order字段已存在，跳过迁移")
            return True
            
        # 添加sort_order字段
        cursor.execute("""
            ALTER TABLE exchange_rates 
            ADD COLUMN sort_order INTEGER DEFAULT 0
        """)
        
        # 为现有数据设置默认排序值（按currency_id排序）
        cursor.execute("""
            UPDATE exchange_rates 
            SET sort_order = currency_id 
            WHERE sort_order = 0 OR sort_order IS NULL
        """)
        
        conn.commit()
        print(f"[{datetime.now()}] 成功添加sort_order字段到exchange_rates表")
        
        return True
        
    except Exception as e:
        print(f"[{datetime.now()}] 迁移失败: {str(e)}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()

def downgrade():
    """降级数据库：移除sort_order字段（SQLite不支持直接删除列）"""
    print("SQLite不支持直接删除列，请手动处理降级操作")
    return False

if __name__ == "__main__":
    print("正在执行数据库迁移...")
    success = upgrade()
    if success:
        print("✅ 迁移成功完成")
    else:
        print("❌ 迁移失败") 