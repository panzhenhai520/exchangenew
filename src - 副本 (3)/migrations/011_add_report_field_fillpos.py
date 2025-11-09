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
    # The mappings below capture fill positions that have been manually
    # verified against the annotated PDFs.  (Fields that still need
    # confirmation remain unmapped for now to avoid polluting data.)
    "AMLO-1-01": {
        "report_number": "fill_52",
        "total_amount": "fill_45",
        "transaction_date_day": "fill_37",
        "transaction_date_month": "fill_38",
        "transaction_date_year": "fill_39",
        "transaction_purpose": "fill_47",
        "maker_id_number": "comb_1",
        "maker_phone": "fill_7",
        "maker_occupation_type": "fill_9",
        "maker_occupation_employer": "fill_10",
        "maker_occupation_business_type": "fill_28",
        "joint_party_firstname": "fill_20",
        "joint_party_lastname": "fill_20",
        "joint_party_address": "fill_22",
        "joint_party_phone": "fill_23",
    },
    "AMLO-1-02": {
        "report_number": "fill_52",
    },
    "AMLO-1-03": {
        "transaction_date_day": "fill_37",
        "transaction_date_month": "fill_38",
        "transaction_date_year": "fill_39",
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
    # Attempt to place the new column after ``is_readonly`` when the column exists,
    # otherwise fall back to appending the column to avoid OperationalError (1054).
    inspector_sql = text(
        """
        SELECT COUNT(*) FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'report_fields'
          AND COLUMN_NAME = 'is_readonly'
        """
    )
    has_is_readonly = session.execute(inspector_sql).scalar()

    if has_is_readonly:
        add_column_sql = """
            ALTER TABLE report_fields
            ADD COLUMN fillpos VARCHAR(64) NULL COMMENT 'Target PDF field identifier'
            AFTER is_readonly
        """
    else:
        add_column_sql = """
            ALTER TABLE report_fields
            ADD COLUMN fillpos VARCHAR(64) NULL COMMENT 'Target PDF field identifier'
        """

    session.execute(text(add_column_sql))
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
