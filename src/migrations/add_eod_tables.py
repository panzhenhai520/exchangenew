from datetime import datetime
from sqlalchemy import create_engine, MetaData
from models.exchange_models import Base, EODStatus, EODHistory, EODBalanceSnapshot
from services.db_service import DatabaseService

def upgrade():
    """添加日结相关表"""
    engine = DatabaseService.get_engine()
    metadata = MetaData()
    
    # 创建表
    EODStatus.__table__.create(engine, checkfirst=True)
    EODHistory.__table__.create(engine, checkfirst=True)
    EODBalanceSnapshot.__table__.create(engine, checkfirst=True)
    
    print("Created EOD tables successfully")

def downgrade():
    """删除日结相关表"""
    engine = DatabaseService.get_engine()
    
    # 按依赖关系反向删除表
    EODBalanceSnapshot.__table__.drop(engine, checkfirst=True)
    EODHistory.__table__.drop(engine, checkfirst=True)
    EODStatus.__table__.drop(engine, checkfirst=True)
    
    print("Dropped EOD tables successfully")

if __name__ == '__main__':
    upgrade() 