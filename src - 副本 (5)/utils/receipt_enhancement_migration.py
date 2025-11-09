"""Utility helpers for running the receipt enhancement migration scripts.

The original file shipped with a large amount of non-UTF8 text and became
corrupted in the repository.  This module restores the required logic using
ASCII strings only so the backend can import it safely.
"""

from datetime import datetime
from typing import Dict, List

from sqlalchemy import text

from services.db_service import DatabaseService
import logging

logger = logging.getLogger(__name__)


class ReceiptEnhancementMigration:
    """Collection of ad-hoc migration helpers used by the receipt service."""

    # ------------------------------------------------------------------
    # Country table helpers
    # ------------------------------------------------------------------
    @staticmethod
    def create_country_table() -> Dict[str, object]:
        """Create the `countries` table when it does not exist."""
        session = DatabaseService.get_session()
        try:
            result = session.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_SCHEMA = DATABASE()
                      AND TABLE_NAME = 'countries'
                    """
                )
            )
            table_exists = result.scalar() > 0

            if not table_exists:
                session.execute(
                    text(
                        """
                        CREATE TABLE countries (
                            id INT PRIMARY KEY AUTO_INCREMENT,
                            country_code VARCHAR(2) UNIQUE NOT NULL COMMENT 'ISO 3166-1 alpha-2 code',
                            country_name_zh VARCHAR(100) NOT NULL COMMENT 'Chinese name',
                            country_name_en VARCHAR(100) NOT NULL COMMENT 'English name',
                            country_name_th VARCHAR(100) NULL COMMENT 'Thai name',
                            phone_code VARCHAR(10) NULL COMMENT 'Telephone code',
                            currency_code VARCHAR(3) NULL COMMENT 'Primary currency',
                            is_active BOOLEAN NOT NULL DEFAULT TRUE,
                            sort_order INT DEFAULT 0,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                                ON UPDATE CURRENT_TIMESTAMP
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                          COLLATE=utf8mb4_unicode_ci
                          COMMENT='countries master data'
                        """
                    )
                )
                session.commit()
                logger.info("Created countries table")
                return {"success": True, "message": "countries table created"}

            logger.info("countries table already exists; skipping creation")
            return {"success": True, "message": "countries table already exists"}

        except Exception as exc:  # noqa: BLE001 - migration helper
            session.rollback()
            logger.error("Failed to create countries table: %s", exc)
            return {"success": False, "message": f"create countries failed: {exc}"}
        finally:
            DatabaseService.close_session(session)

    # ------------------------------------------------------------------
    # Branch receipt fields
    # ------------------------------------------------------------------
    @staticmethod
    def add_branch_receipt_fields() -> Dict[str, object]:
        """Ensure receipt related columns exist on the `branches` table."""
        session = DatabaseService.get_session()
        try:
            result = session.execute(
                text(
                    """
                    SELECT COLUMN_NAME
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                      AND TABLE_NAME = 'branches'
                    """
                )
            )
            columns = {row[0] for row in result.fetchall()}
            fields_added: List[str] = []

            if "company_full_name" not in columns:
                session.execute(
                    text(
                        """
                        ALTER TABLE branches
                          ADD COLUMN company_full_name VARCHAR(255) NULL
                            COMMENT 'Full company name for receipts'
                        """
                    )
                )
                fields_added.append("company_full_name")
                logger.info("Added company_full_name column to branches")

            if "tax_registration_number" not in columns:
                session.execute(
                    text(
                        """
                        ALTER TABLE branches
                          ADD COLUMN tax_registration_number VARCHAR(100) NULL
                            COMMENT 'Tax registration number'
                        """
                    )
                )
                fields_added.append("tax_registration_number")
                logger.info("Added tax_registration_number column to branches")

            session.commit()
            if fields_added:
                return {
                    "success": True,
                    "message": "Added branch fields: " + ", ".join(fields_added),
                }
            return {"success": True, "message": "All branch fields already exist"}

        except Exception as exc:  # noqa: BLE001 - migration helper
            session.rollback()
            logger.error("Failed to add branch receipt fields: %s", exc)
            return {"success": False, "message": f"add branch fields failed: {exc}"}
        finally:
            DatabaseService.close_session(session)

    # ------------------------------------------------------------------
    # Transaction receipt fields
    # ------------------------------------------------------------------
    @staticmethod
    def add_transaction_payment_fields() -> Dict[str, object]:
        """Add missing receipt/payment columns to `exchange_transactions`."""
        session = DatabaseService.get_session()
        try:
            result = session.execute(
                text(
                    """
                    SELECT COLUMN_NAME
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                      AND TABLE_NAME = 'exchange_transactions'
                    """
                )
            )
            columns = {row[0] for row in result.fetchall()}
            fields_added: List[str] = []

            if "payment_method" not in columns:
                session.execute(
                    text(
                        """
                        ALTER TABLE exchange_transactions
                          ADD COLUMN payment_method VARCHAR(50) DEFAULT 'cash'
                            COMMENT 'Payment method: cash, instrument_cheque, instrument_draft, instrument_other, other'
                        """
                    )
                )
                fields_added.append("payment_method")
                logger.info("Added payment_method column to exchange_transactions")

            if "payment_method_note" not in columns:
                session.execute(
                    text(
                        """
                        ALTER TABLE exchange_transactions
                          ADD COLUMN payment_method_note VARCHAR(200) NULL
                            COMMENT 'Additional note for payment method'
                        """
                    )
                )
                fields_added.append("payment_method_note")
                logger.info("Added payment_method_note column to exchange_transactions")

            if "receipt_language" not in columns:
                session.execute(
                    text(
                        """
                        ALTER TABLE exchange_transactions
                          ADD COLUMN receipt_language VARCHAR(5) DEFAULT 'zh'
                            COMMENT 'Receipt print language: zh, en, th'
                        """
                    )
                )
                fields_added.append("receipt_language")
                logger.info("Added receipt_language column to exchange_transactions")

            if "issuing_country_code" not in columns:
                session.execute(
                    text(
                        """
                        ALTER TABLE exchange_transactions
                          ADD COLUMN issuing_country_code VARCHAR(2) NULL
                            COMMENT 'ID issuing country code'
                        """
                    )
                )
                fields_added.append("issuing_country_code")
                logger.info("Added issuing_country_code column to exchange_transactions")

            session.commit()
            if fields_added:
                return {
                    "success": True,
                    "message": "Added transaction fields: " + ", ".join(fields_added),
                }
            return {
                "success": True,
                "message": "All transaction payment fields already exist",
            }

        except Exception as exc:  # noqa: BLE001 - migration helper
            session.rollback()
            logger.error("Failed to add transaction payment fields: %s", exc)
            return {
                "success": False,
                "message": f"add transaction fields failed: {exc}",
            }
        finally:
            DatabaseService.close_session(session)

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------
    @staticmethod
    def run_all_migrations() -> Dict[str, object]:
        """Execute all receipt enhancement migrations in order."""
        results = [
            ReceiptEnhancementMigration.create_country_table(),
            ReceiptEnhancementMigration.add_branch_receipt_fields(),
            ReceiptEnhancementMigration.add_transaction_payment_fields(),
        ]

        success = all(result.get("success") for result in results)
        messages = [result.get("message", "") for result in results]

        return {
            "success": success,
            "message": "\n".join(messages),
            "details": results,
            "executed_at": datetime.utcnow().isoformat(),
        }

