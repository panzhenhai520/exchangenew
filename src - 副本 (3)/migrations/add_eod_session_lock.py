"""
添加EODSessionLock表 - 确保只有单一终端可以进行日结
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from services.db_service import DatabaseService
from datetime import datetime

def run_migration():
    """执行迁移"""
    session = DatabaseService.get_session()
    
    try:
        # 检查表是否已存在
        result = session.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='eod_session_locks'
        """)).fetchone()
        
        if result:
            print("EODSessionLock表已存在，跳过迁移")
            return
        
        # 创建eod_session_locks表
        session.execute(text("""
            CREATE TABLE eod_session_locks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                branch_id INTEGER NOT NULL,
                eod_status_id INTEGER NOT NULL,
                session_id VARCHAR(100) NOT NULL,
                operator_id INTEGER NOT NULL,
                ip_address VARCHAR(50) NOT NULL,
                user_agent TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (branch_id) REFERENCES branches(id),
                FOREIGN KEY (eod_status_id) REFERENCES eod_status(id),
                FOREIGN KEY (operator_id) REFERENCES operators(id)
            )
        """))
        
        # 创建索引
        session.execute(text("""
            CREATE INDEX idx_eod_session_locks_branch_id ON eod_session_locks(branch_id)
        """))
        
        session.execute(text("""
            CREATE INDEX idx_eod_session_locks_eod_status_id ON eod_session_locks(eod_status_id)
        """))
        
        session.execute(text("""
            CREATE INDEX idx_eod_session_locks_session_id ON eod_session_locks(session_id)
        """))
        
        session.execute(text("""
            CREATE INDEX idx_eod_session_locks_active ON eod_session_locks(branch_id, is_active)
        """))
        
        session.commit()
        print("EODSessionLock表创建成功")
        
    except Exception as e:
        session.rollback()
        print(f"迁移失败: {e}")
        raise
    finally:
        DatabaseService.close_session(session)

if __name__ == "__main__":
    run_migration() 