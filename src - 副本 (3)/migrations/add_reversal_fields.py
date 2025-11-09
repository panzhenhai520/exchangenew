from sqlalchemy import create_engine
from services.db_service import DatabaseService

def upgrade():
    """添加冲减关联字段"""
    engine = DatabaseService.get_engine()
    
    # 添加原交易号字段
    with engine.connect() as connection:
        connection.execute("""
            ALTER TABLE exchange_transactions
            ADD COLUMN IF NOT EXISTS original_transaction_no VARCHAR(20) NULL;
        """)
        
def downgrade():
    """移除冲减关联字段"""
    engine = DatabaseService.get_engine()
    
    # 移除原交易号字段
    with engine.connect() as connection:
        connection.execute("""
            ALTER TABLE exchange_transactions
            DROP COLUMN IF EXISTS original_transaction_no;
        """)

if __name__ == '__main__':
    upgrade() 