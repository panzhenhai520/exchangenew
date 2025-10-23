# -*- coding: utf-8 -*-
"""
Migration 011: Add fillpos column to report_fields and backfill AMLO mappings.
Created: 2025-10-22
Purpose: Record PDF form field identifiers so AMLO reports can map dynamic inputs
         to interactive PDF controls (e.g., fill_XX / Check BoxYY).
"""

import os
import sys
from sqlalchemy import text

# Ensure project root is on sys.path to reuse existing services
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.db_service import DatabaseService  # noqa: E402


AMLO_FILLPOS_MAPPINGS = {
    "AMLO-1-01": {
        "customer_id": "comb_1",
        "customer_name": "fill_13",
        "customer_address": "fill_13",
        "customer_phone": "fill_57",
        "customer_occupation": "fill_13",
        "transaction_purpose": "fill_42",
        "beneficiary_name": "fill_50",
    },
    "AMLO-1-02": {
        "customer_id": "fill_7",
        "customer_name": "fill_11",
        "customer_address": "fill_11",
        "customer_phone": "fill_68",
        "customer_occupation": "fill_11",
        "transaction_purpose": "fill_44",
        "beneficiary_name": "fill_44",
    },
    "AMLO-1-03": {
        "customer_id": "comb_1",
        "customer_name": "fill_7",
        "customer_address": "fill_11",
        "customer_phone": "fill_56",
        "customer_occupation": "fill_11",
        "transaction_purpose": "fill_42",
        "beneficiary_name": "comb_4",
    },
}


def ensure_fillpos_column(session):
    """Add fillpos column if it does not already exist."""
    check_sql = text(
        """
        SELECT COUNT(*) AS count
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'report_fields'
          AND COLUMN_NAME = 'fillpos'
        """
    )
    exists = session.execute(check_sql).scalar()

    if exists:
        print("[Migration 011] Column report_fields.fillpos already exists.")
        return

    print("[Migration 011] Adding fillpos column to report_fields...")
    session.execute(
        text(
            """
            ALTER TABLE report_fields
            ADD COLUMN fillpos VARCHAR(64) NULL COMMENT 'Target PDF field identifier'
            AFTER is_readonly
            """
        )
    )
    session.commit()
    print("[Migration 011] Column fillpos added successfully.")


def backfill_amlo_fillpos(session):
    """Populate fillpos values for key AMLO report fields."""
    print("[Migration 011] Backfilling AMLO fillpos mappings...")

    update_sql = text(
        """
        UPDATE report_fields
        SET fillpos = :fillpos,
            updated_at = NOW()
        WHERE report_type = :report_type
          AND field_name = :field_name
        """
    )

    for report_type, mapping in AMLO_FILLPOS_MAPPINGS.items():
        for field_name, fillpos in mapping.items():
            result = session.execute(
                update_sql,
                {
                    "fillpos": fillpos,
                    "report_type": report_type,
                    "field_name": field_name,
                },
            )
            if result.rowcount:
                print(
                    f"  -> {report_type}.{field_name} mapped to fillpos '{fillpos}'"
                )
        session.commit()


def main():
    session = DatabaseService.get_session()
    try:
        ensure_fillpos_column(session)
        backfill_amlo_fillpos(session)
    finally:
        DatabaseService.close_session(session)


if __name__ == "__main__":
    main()
