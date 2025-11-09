"""
Add AMLO/BOT related branch fields and the AMLO report sequence table.

Usage:
    python src/migrations/add_amlo_bot_branch_fields_and_sequences.py
"""

import os
import sys
from datetime import datetime

from sqlalchemy import inspect, text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService  # noqa: E402  pylint: disable=C0413


def add_branch_columns(session):
    """Ensure branches table contains all AMLO/BOT required columns."""
    inspector = inspect(session.bind)
    columns = {col['name'] for col in inspector.get_columns('branches')}

    alter_statements = []

    if 'amlo_institution_code' not in columns:
        alter_statements.append(
            "ADD COLUMN amlo_institution_code VARCHAR(10) NULL COMMENT 'AMLO institution code (3 digits)'"
        )
    if 'amlo_branch_code' not in columns:
        alter_statements.append(
            "ADD COLUMN amlo_branch_code VARCHAR(10) NULL COMMENT 'AMLO branch code (3 digits)'"
        )
    if 'bot_sender_code' not in columns:
        alter_statements.append(
            "ADD COLUMN bot_sender_code VARCHAR(20) NULL COMMENT 'BOT data sender code'"
        )
    if 'bot_branch_area_code' not in columns:
        alter_statements.append(
            "ADD COLUMN bot_branch_area_code VARCHAR(20) NULL COMMENT 'BOT branch area code'"
        )
    if 'bot_license_number' not in columns:
        alter_statements.append(
            "ADD COLUMN bot_license_number VARCHAR(20) NULL COMMENT 'BOT dedicated license number'"
        )

    if alter_statements:
        alter_sql = f"""
            ALTER TABLE branches
            {', '.join(alter_statements)}
        """
        session.execute(text(alter_sql))
        session.commit()
        print("[OK] Added AMLO/BOT columns to branches table")
    else:
        print("[SKIP] branches table already has AMLO/BOT columns")


def create_sequence_table(session):
    """Create AMLO report sequence table to guarantee unique numbers."""
    inspector = inspect(session.bind)
    if 'amlo_report_sequences' in inspector.get_table_names():
        print("[SKIP] amlo_report_sequences 表已存在")
        return

    create_sql = """
        CREATE TABLE IF NOT EXISTS amlo_report_sequences (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sequence_date DATE NOT NULL,
            report_type VARCHAR(20) NOT NULL,
            branch_id INT NOT NULL,
            last_sequence INT NOT NULL DEFAULT 0,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uq_amlo_report_sequences (sequence_date, report_type, branch_id),
            CONSTRAINT fk_amlo_report_sequences_branch
                FOREIGN KEY (branch_id) REFERENCES branches(id)
                ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AMLO报告流水号序列表';
    """
    session.execute(text(create_sql))
    session.commit()
    print("[OK] amlo_report_sequences table created")


def main():
    session = DatabaseService.get_session()
    try:
        add_branch_columns(session)
        create_sequence_table(session)
    except Exception as exc:  # pylint: disable=broad-except
        session.rollback()
        print(f"[ERROR] Migration failed: {exc}")
        raise
    finally:
        DatabaseService.close_session(session)
        print(f"[DONE] {datetime.utcnow().isoformat()} migration finished")


if __name__ == '__main__':
    main()
