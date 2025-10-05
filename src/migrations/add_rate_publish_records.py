"""
添加汇率发布记录表
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

def upgrade():
    """添加汇率发布记录表"""
    session = DatabaseService.get_session()
    
    try:
        # 创建汇率发布记录表
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS rate_publish_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                branch_id INTEGER NOT NULL,
                publish_date DATE NOT NULL,
                publish_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                publisher_id INTEGER NOT NULL,
                publisher_name VARCHAR(100) NOT NULL,
                total_currencies INTEGER NOT NULL DEFAULT 0,
                publish_theme VARCHAR(20) DEFAULT 'light',
                access_token VARCHAR(100),
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (branch_id) REFERENCES branches (id),
                FOREIGN KEY (publisher_id) REFERENCES operators (id)
            )
        """))
        
        # 创建汇率发布详情表
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS rate_publish_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                publish_record_id INTEGER NOT NULL,
                currency_id INTEGER NOT NULL,
                currency_code VARCHAR(3) NOT NULL,
                currency_name VARCHAR(50) NOT NULL,
                buy_rate DECIMAL(10, 4) NOT NULL,
                sell_rate DECIMAL(10, 4) NOT NULL,
                sort_order INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (publish_record_id) REFERENCES rate_publish_records (id) ON DELETE CASCADE,
                FOREIGN KEY (currency_id) REFERENCES currencies (id)
            )
        """))
        
        # 创建索引
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_rate_publish_records_branch_date
            ON rate_publish_records (branch_id, publish_date)
        """))
        
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_rate_publish_details_record_id
            ON rate_publish_details (publish_record_id)
        """))
        
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_rate_publish_details_currency
            ON rate_publish_details (currency_id)
        """))
        
        DatabaseService.commit_session(session)
        print("✅ Rate publish records tables created successfully")
        
    except Exception as e:
        DatabaseService.rollback_session(session)
        print(f"❌ Error creating rate publish records tables: {e}")
        raise e
    finally:
        DatabaseService.close_session(session)

def downgrade():
    """删除汇率发布记录表"""
    session = DatabaseService.get_session()
    
    try:
        session.execute(text("DROP TABLE IF EXISTS rate_publish_details"))
        session.execute(text("DROP TABLE IF EXISTS rate_publish_records"))
        DatabaseService.commit_session(session)
        print("✅ Rate publish records tables dropped successfully")
        
    except Exception as e:
        DatabaseService.rollback_session(session)
        print(f"❌ Error dropping rate publish records tables: {e}")
        raise e
    finally:
        DatabaseService.close_session(session)

if __name__ == "__main__":
    print("Running rate publish records migration...")
    upgrade()
    print("Migration completed!") 