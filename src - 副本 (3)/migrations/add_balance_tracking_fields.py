from yoyo import step

__depends__ = {}

steps = [
    step("""
        ALTER TABLE exchange_transactions
        ADD COLUMN balance_before DECIMAL(15, 2),
        ADD COLUMN balance_after DECIMAL(15, 2)
    """,
    """
        ALTER TABLE exchange_transactions
        DROP COLUMN balance_before,
        DROP COLUMN balance_after
    """)
] 