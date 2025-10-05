#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复DashboardPublishRecord表的唯一约束问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    """执行数据库迁移"""
    session = DatabaseService.get_session()
    
    try:
        logger.info("开始修复DashboardPublishRecord表的唯一约束...")
        
        # 1. 先备份数据到临时表
        session.execute(text("""
            CREATE TEMPORARY TABLE dashboard_publish_records_backup AS 
            SELECT * FROM dashboard_publish_records
        """))
        logger.info("备份数据完成")
        
        # 2. 删除原表
        session.execute(text("DROP TABLE dashboard_publish_records"))
        logger.info("删除原表完成")
        
        # 3. 重新创建表（去掉UNIQUE约束）
        session.execute(text("""
            CREATE TABLE dashboard_publish_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                branch_id INTEGER NOT NULL,
                publish_date DATE NOT NULL,
                publish_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                rate_date DATE NOT NULL,
                publisher_id INTEGER NOT NULL,
                encrypted_url VARCHAR(500) NOT NULL,
                access_token VARCHAR(255) NOT NULL UNIQUE,
                currency_order TEXT,
                theme VARCHAR(20) NOT NULL DEFAULT 'light',
                description VARCHAR(255),
                is_active BOOLEAN NOT NULL DEFAULT 1,
                expires_at DATETIME,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (branch_id) REFERENCES branches (id),
                FOREIGN KEY (publisher_id) REFERENCES operators (id)
            )
        """))
        logger.info("重新创建表完成")
        
        # 4. 恢复数据
        session.execute(text("""
            INSERT INTO dashboard_publish_records 
            SELECT * FROM dashboard_publish_records_backup
        """))
        logger.info("恢复数据完成")
        
        # 5. 创建新的索引
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_dashboard_publish_branch_date 
            ON dashboard_publish_records (branch_id, publish_date)
        """))
        
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_dashboard_publish_token 
            ON dashboard_publish_records (access_token)
        """))
        
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_dashboard_publish_active 
            ON dashboard_publish_records (is_active, publish_date)
        """))
        
        logger.info("创建索引完成")
        
        # 提交事务
        DatabaseService.commit_session(session)
        logger.info("数据库迁移完成！")
        
    except Exception as e:
        logger.error(f"数据库迁移失败: {e}")
        DatabaseService.rollback_session(session)
        raise
    finally:
        DatabaseService.close_session(session)

if __name__ == "__main__":
    print("开始修复DashboardPublishRecord表的唯一约束...")
    migrate()
    print("修复完成！") 