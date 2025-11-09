"""
日结步骤操作记录表 - 用于支持步骤回滚和取消日结功能
"""

from datetime import datetime
from sqlalchemy import create_engine, text, text
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService

def upgrade():
    """添加EOD步骤操作记录表"""
    
    session = DatabaseService.get_session()
    
    try:
        # 创建eod_step_actions表
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS eod_step_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                eod_status_id INTEGER NOT NULL,
                step_number INTEGER NOT NULL,
                action_type VARCHAR(50) NOT NULL,
                action_data TEXT,
                rollback_data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER NOT NULL,
                FOREIGN KEY (eod_status_id) REFERENCES eod_status(id),
                FOREIGN KEY (created_by) REFERENCES operators(id)
            )
        """))
        
        session.commit()
        print("✅ 已创建 eod_step_actions 表")
        
    except Exception as e:
        session.rollback()
        print(f"❌ 创建表失败: {e}")
        raise
    finally:
        DatabaseService.close_session(session)

def downgrade():
    """删除EOD步骤操作记录表"""
    
    session = DatabaseService.get_session()
    
    try:
        session.execute(text("DROP TABLE IF EXISTS eod_step_actions"))
        session.commit()
        print("✅ 已删除 eod_step_actions 表")
        
    except Exception as e:
        session.rollback()
        print(f"❌ 删除表失败: {e}")
        raise
    finally:
        DatabaseService.close_session(session)

if __name__ == "__main__":
    print("正在创建日结步骤操作记录表...")
    upgrade()
    print("迁移完成！")