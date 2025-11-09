from sqlalchemy import text
#!/usr/bin/env python3
"""
数据库迁移脚本：创建票据编号序列表
确保每个网点的票据编号连续性
"""

import sqlite3
import os
import sys
from datetime import datetime, date

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DATABASE_PATH, DatabaseService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_receipt_sequence_table():
    """创建票据编号序列表"""
    
    # 检查数据库文件是否存在
    if not os.path.exists(DATABASE_PATH):
        logger.error(f"数据库文件不存在: {DATABASE_PATH}")
        return False
    
    try:
        # 直接使用SQLite连接执行创建表语句
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        logger.info("开始创建receipt_sequences表...")
        
        # 创建票据编号序列表
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS receipt_sequences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            branch_id INTEGER NOT NULL UNIQUE,
            current_sequence INTEGER NOT NULL DEFAULT 0,
            last_date DATE NOT NULL DEFAULT (date('now')),
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (branch_id) REFERENCES branches(id)
        );
        """
        
        cursor.execute(create_table_sql)
        logger.info("✅ receipt_sequences表创建成功")
        
        # 创建索引
        index_sql = """
        CREATE INDEX IF NOT EXISTS idx_receipt_sequences_branch_id 
        ON receipt_sequences (branch_id);
        """
        
        cursor.execute(index_sql)
        logger.info("✅ 索引创建成功")
        
        # 为所有现有网点初始化序列记录
        cursor.execute("SELECT id, branch_code FROM branches WHERE is_active = 1")
        branches = cursor.fetchall()
        
        today = date.today().isoformat()
        
        for branch_id, branch_code in branches:
            # 检查是否已存在记录
            cursor.execute("SELECT COUNT(*) FROM receipt_sequences WHERE branch_id = ?", (branch_id,))
            exists = cursor.fetchone()[0]
            
            if not exists:
                # 初始化网点的票据序列
                cursor.execute("""
                    INSERT INTO receipt_sequences (branch_id, current_sequence, last_date, updated_at)
                    VALUES (?, 0, ?, ?)
                """, (branch_id, today, datetime.now().isoformat()))
                logger.info(f"✅ 为网点 {branch_code} (ID: {branch_id}) 初始化票据序列")
        
        # 提交更改
        conn.commit()
        logger.info("✅ 票据序列表创建并初始化完成")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 创建票据序列表失败: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

def verify_receipt_sequence_table():
    """验证票据序列表创建结果"""
    try:
        session = DatabaseService.get_session()
        
        # 测试查询
        result = session.execute(text(\"SELECT COUNT(*) FROM receipt_sequences\"))
        count = result.fetchone()[0]
        logger.info(f"✅ receipt_sequences表查询成功，当前记录数: {count}")
        
        # 查看表结构
        result = session.execute(text(\"PRAGMA table_info(receipt_sequences)\"))
        columns = result.fetchall()
        logger.info("receipt_sequences表结构:")
        for col in columns:
            logger.info(f"  {col[1]} {col[2]} {'NOT NULL' if col[3] else 'NULL'}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 验证票据序列表失败: {str(e)}")
        return False
        
    finally:
        if 'session' in locals():
            DatabaseService.close_session(session)

if __name__ == "__main__":
    logger.info("🚀 开始创建票据编号序列表...")
    logger.info(f"数据库路径: {DATABASE_PATH}")
    
    if create_receipt_sequence_table():
        logger.info("✅ 票据序列表创建成功，开始验证...")
        if verify_receipt_sequence_table():
            logger.info("🎉 票据编号序列系统创建并验证成功！")
        else:
            logger.error("❌ 票据序列表验证失败")
    else:
        logger.error("❌ 票据序列表创建失败") 