#!/usr/bin/env python3
"""
添加汇率展示发布记录表
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from services.db_service import DatabaseService
import logging

logger = logging.getLogger(__name__)

def upgrade():
    """添加dashboard_publish_records表"""
    session = DatabaseService.get_session()
    try:
        # 创建dashboard_publish_records表
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS dashboard_publish_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                branch_id INTEGER NOT NULL,
                publish_date DATE NOT NULL,
                publisher_id INTEGER NOT NULL,
                encrypted_url VARCHAR(500) NOT NULL,
                access_token VARCHAR(255) NOT NULL UNIQUE,
                currency_order TEXT,
                theme VARCHAR(20) NOT NULL DEFAULT 'light',
                is_active BOOLEAN NOT NULL DEFAULT 1,
                expires_at DATETIME,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (branch_id) REFERENCES branches (id),
                FOREIGN KEY (publisher_id) REFERENCES operators (id),
                UNIQUE(branch_id, publish_date, is_active)
            )
        """))
        
        # 创建索引
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
        
        DatabaseService.commit_session(session)
        print("✅ Dashboard publish records table created successfully")
        
    except Exception as e:
        DatabaseService.rollback_session(session)
        print(f"❌ Error creating dashboard publish records table: {e}")
        raise
    finally:
        DatabaseService.close_session(session)

def downgrade():
    """删除dashboard_publish_records表"""
    session = DatabaseService.get_session()
    try:
        session.execute(text("DROP TABLE IF EXISTS dashboard_publish_records"))
        DatabaseService.commit_session(session)
        print("✅ Dashboard publish records table dropped successfully")
        
    except Exception as e:
        DatabaseService.rollback_session(session)
        print(f"❌ Error dropping dashboard publish records table: {e}")
        raise
    finally:
        DatabaseService.close_session(session)

if __name__ == "__main__":
    print("Running dashboard publish records migration...")
    upgrade()
    print("Migration completed!")
