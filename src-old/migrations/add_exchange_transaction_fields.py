from sqlalchemy import text
#!/usr/bin/env python3
"""
数据库迁移脚本：为exchange_transactions表添加新字段
添加字段：purpose, remarks, receipt_filename, print_count
"""

import sqlite3
import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DATABASE_PATH, DatabaseService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_exchange_transaction_fields():
    """为exchange_transactions表添加新字段"""
    
    # 检查数据库文件是否存在
    if not os.path.exists(DATABASE_PATH):
        logger.error(f"数据库文件不存在: {DATABASE_PATH}")
        return False
    
    try:
        # 直接使用SQLite连接执行ALTER TABLE语句
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        logger.info("开始为exchange_transactions表添加新字段...")
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(exchange_transactions)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        
        # 要添加的字段列表
        new_fields = [
            ("purpose", "VARCHAR(100)"),
            ("remarks", "TEXT"),
            ("receipt_filename", "VARCHAR(255)"),
            ("print_count", "INTEGER DEFAULT 0")
        ]
        
        # 逐个添加字段（如果不存在）
        for field_name, field_type in new_fields:
            if field_name not in existing_columns:
                sql = f"ALTER TABLE exchange_transactions ADD COLUMN {field_name} {field_type}"
                logger.info(f"执行SQL: {sql}")
                cursor.execute(sql)
                logger.info(f"✅ 成功添加字段: {field_name}")
            else:
                logger.info(f"⚠️ 字段已存在，跳过: {field_name}")
        
        # 提交更改
        conn.commit()
        logger.info("✅ 所有字段添加完成")
        
        # 验证字段是否成功添加
        cursor.execute("PRAGMA table_info(exchange_transactions)")
        all_columns = [column[1] for column in cursor.fetchall()]
        logger.info(f"当前exchange_transactions表的所有字段: {all_columns}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 添加字段失败: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

def verify_migration():
    """验证迁移结果"""
    try:
        session = DatabaseService.get_session()
        
        # 导入模型以验证
        from models.exchange_models import ExchangeTransaction, TransactionPurposeLimit
        
        # 测试查询exchange_transactions表
        result = session.execute(text(\"SELECT purpose, remarks, receipt_filename, print_count FROM exchange_transactions LIMIT 1\"))
        logger.info("✅ 新字段查询测试成功")
        
        # 测试TransactionPurposeLimit模型
        purpose_limits = session.query(TransactionPurposeLimit).limit(5).all()
        logger.info(f"✅ TransactionPurposeLimit模型测试成功，查询到 {len(purpose_limits)} 条记录")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 验证迁移失败: {str(e)}")
        return False
        
    finally:
        if 'session' in locals():
            DatabaseService.close_session(session)

if __name__ == "__main__":
    logger.info("🚀 开始数据库迁移...")
    logger.info(f"数据库路径: {DATABASE_PATH}")
    
    if add_exchange_transaction_fields():
        logger.info("✅ 字段添加成功，开始验证...")
        if verify_migration():
            logger.info("🎉 数据库迁移完成并验证成功！")
        else:
            logger.error("❌ 迁移验证失败")
    else:
        logger.error("❌ 数据库迁移失败") 