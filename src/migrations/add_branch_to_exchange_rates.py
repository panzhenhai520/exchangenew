import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text

# Add src directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import get_db_url

def column_exists(conn, table, column):
    """Check if a column exists in a table"""
    result = conn.execute(text(f"""
        SELECT COUNT(*) 
        FROM pragma_table_info('{table}') 
        WHERE name='{column}';
    """))
    return result.scalar() > 0

def upgrade():
    """Add branch_id to exchange_rates table and migrate existing data"""
    engine = create_engine(get_db_url())
    
    with engine.begin() as conn:
        # 1. 检查并添加 branch_id 列
        if not column_exists(conn, 'exchange_rates', 'branch_id'):
            conn.execute(text("""
                ALTER TABLE exchange_rates 
                ADD COLUMN branch_id INTEGER 
                REFERENCES branches(id);
            """))
        
        # 2. 获取默认网点（总行）的 ID
        result = conn.execute(text("""
            SELECT id FROM branches 
            WHERE branch_code = 'HQ' 
            OR branch_name LIKE '%总行%' 
            LIMIT 1;
        """))
        default_branch_id = result.scalar()
        
        if not default_branch_id:
            # 如果没有找到总行，创建一个
            conn.execute(text("""
                INSERT INTO branches (branch_name, branch_code, is_active, created_at)
                VALUES ('总行营业部', 'HQ', 1, :created_at);
            """), {"created_at": datetime.utcnow()})
            
            result = conn.execute(text("SELECT last_insert_rowid();"))
            default_branch_id = result.scalar()
        
        # 3. 更新现有记录，设置默认网点
        conn.execute(text("""
            UPDATE exchange_rates 
            SET branch_id = :branch_id 
            WHERE branch_id IS NULL;
        """), {"branch_id": default_branch_id})
        
        # 4. 将 branch_id 设置为非空
        # SQLite不支持ALTER COLUMN，需要通过创建新表来实现
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS exchange_rates_new (
                id INTEGER PRIMARY KEY,
                currency_id INTEGER NOT NULL,
                branch_id INTEGER NOT NULL,
                rate_date DATE NOT NULL,
                buy_rate FLOAT NOT NULL,
                sell_rate FLOAT NOT NULL,
                created_by INTEGER NOT NULL,
                created_at DATETIME,
                updated_at DATETIME,
                FOREIGN KEY(currency_id) REFERENCES currencies(id),
                FOREIGN KEY(branch_id) REFERENCES branches(id),
                FOREIGN KEY(created_by) REFERENCES operators(id)
            );
        """))
        
        # 复制数据到新表
        conn.execute(text("""
            INSERT INTO exchange_rates_new 
            SELECT * FROM exchange_rates;
        """))
        
        # 删除旧表并重命名新表
        conn.execute(text("DROP TABLE exchange_rates;"))
        conn.execute(text("ALTER TABLE exchange_rates_new RENAME TO exchange_rates;"))
        
        # 5. 添加唯一索引
        conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_branch_currency_date 
            ON exchange_rates (branch_id, currency_id, rate_date);
        """))

def downgrade():
    """Remove branch_id from exchange_rates table"""
    engine = create_engine(get_db_url())
    
    with engine.begin() as conn:
        # 1. 删除唯一索引
        conn.execute(text("DROP INDEX IF EXISTS idx_unique_branch_currency_date;"))
        
        # 2. 创建新表（不包含branch_id）
        conn.execute(text("""
            CREATE TABLE exchange_rates_new (
                id INTEGER PRIMARY KEY,
                currency_id INTEGER NOT NULL,
                rate_date DATE NOT NULL,
                buy_rate FLOAT NOT NULL,
                sell_rate FLOAT NOT NULL,
                created_by INTEGER NOT NULL,
                created_at DATETIME,
                updated_at DATETIME,
                FOREIGN KEY(currency_id) REFERENCES currencies(id),
                FOREIGN KEY(created_by) REFERENCES operators(id)
            );
        """))
        
        # 复制数据到新表（忽略branch_id）
        conn.execute(text("""
            INSERT INTO exchange_rates_new 
            SELECT id, currency_id, rate_date, buy_rate, sell_rate, 
                   created_by, created_at, updated_at 
            FROM exchange_rates;
        """))
        
        # 删除旧表并重命名新表
        conn.execute(text("DROP TABLE exchange_rates;"))
        conn.execute(text("ALTER TABLE exchange_rates_new RENAME TO exchange_rates;")) 