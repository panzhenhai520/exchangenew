"""
更新 exchange_transactions 表的金额字段类型
将 FLOAT 类型改为 DECIMAL 类型以确保精确计算
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Column, Numeric

def upgrade():
    # 创建临时表
    op.create_table(
        'exchange_transactions_new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('transaction_no', sa.String(20), nullable=False),
        sa.Column('branch_id', sa.Integer(), nullable=False),
        sa.Column('currency_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('rate', sa.Numeric(10, 4), nullable=False),
        sa.Column('local_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('customer_name', sa.String(100)),
        sa.Column('customer_id', sa.String(50)),
        sa.Column('operator_id', sa.Integer(), nullable=False),
        sa.Column('transaction_date', sa.Date(), nullable=False),
        sa.Column('transaction_time', sa.String(10), nullable=False),
        sa.Column('created_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('transaction_no'),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id']),
        sa.ForeignKeyConstraint(['currency_id'], ['currencies.id']),
        sa.ForeignKeyConstraint(['operator_id'], ['operators.id'])
    )

    # 复制数据
    op.execute("""
        INSERT INTO exchange_transactions_new 
        SELECT id, transaction_no, branch_id, currency_id, type,
               CAST(amount AS DECIMAL(15,2)),
               CAST(rate AS DECIMAL(10,4)),
               CAST(local_amount AS DECIMAL(15,2)),
               customer_name, customer_id, operator_id,
               transaction_date, transaction_time, created_at
        FROM exchange_transactions
    """)

    # 删除旧表
    op.drop_table('exchange_transactions')

    # 重命名新表
    op.rename_table('exchange_transactions_new', 'exchange_transactions')

def downgrade():
    # 创建临时表（使用旧的结构）
    op.create_table(
        'exchange_transactions_old',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('transaction_no', sa.String(20), nullable=False),
        sa.Column('branch_id', sa.Integer(), nullable=False),
        sa.Column('currency_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('rate', sa.Float(), nullable=False),
        sa.Column('local_amount', sa.Float(), nullable=False),
        sa.Column('customer_name', sa.String(100)),
        sa.Column('customer_id', sa.String(50)),
        sa.Column('operator_id', sa.Integer(), nullable=False),
        sa.Column('transaction_date', sa.Date(), nullable=False),
        sa.Column('transaction_time', sa.String(10), nullable=False),
        sa.Column('created_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('transaction_no'),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id']),
        sa.ForeignKeyConstraint(['currency_id'], ['currencies.id']),
        sa.ForeignKeyConstraint(['operator_id'], ['operators.id'])
    )

    # 复制数据回旧结构
    op.execute("""
        INSERT INTO exchange_transactions_old 
        SELECT id, transaction_no, branch_id, currency_id, type,
               CAST(amount AS FLOAT),
               CAST(rate AS FLOAT),
               CAST(local_amount AS FLOAT),
               customer_name, customer_id, operator_id,
               transaction_date, transaction_time, created_at
        FROM exchange_transactions
    """)

    # 删除新表
    op.drop_table('exchange_transactions')

    # 重命名回旧表
    op.rename_table('exchange_transactions_old', 'exchange_transactions') 