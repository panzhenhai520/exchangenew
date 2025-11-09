# -*- coding: utf-8 -*-
"""
AMLO Signature Service

Handles signature management for AMLO reservations including:
- Saving signatures (reporter, customer, auditor)
- Retrieving signatures
- Deleting signatures
- Validation
"""

import logging
import json
from typing import Dict, Any, Optional, Tuple, List
from sqlalchemy import text
from datetime import datetime

from .db_helpers import AMLODatabaseHelper
from .validators import ReservationValidator

logger = logging.getLogger(__name__)


class SignatureService:
    """Service layer for AMLO signature management"""

    # Maximum signature size (500KB)
    MAX_SIGNATURE_SIZE = 500 * 1024

    @staticmethod
    def save_reservation_signatures(
        session,
        reservation_id: int,
        signatures: Dict[str, str],
        storage_type: str = 'base64'
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Save signatures for a reservation

        Args:
            session: SQLAlchemy session
            reservation_id: Reservation ID
            signatures: Dict with keys 'reporter_signature', 'customer_signature', 'auditor_signature'
            storage_type: Storage type ('base64' or 'file')

        Returns:
            Tuple of (success, result_data, error_message)
        """
        try:
            # Check reservation exists
            reservation = AMLODatabaseHelper.get_reservation_or_none(session, reservation_id)
            if not reservation:
                return False, None, "Reservation not found"

            # Extract signatures
            reporter_sig = signatures.get('reporter_signature')
            customer_sig = signatures.get('customer_signature')
            auditor_sig = signatures.get('auditor_signature')

            # Validate at least one signature provided
            if not any([reporter_sig, customer_sig, auditor_sig]):
                return False, None, "At least one signature must be provided"

            # Validate each signature
            signatures_to_save = []
            validation_errors = []

            if reporter_sig:
                valid, error, size = ReservationValidator.validate_signature_data(
                    reporter_sig, SignatureService.MAX_SIGNATURE_SIZE
                )
                if not valid:
                    validation_errors.append(f"Reporter signature: {error}")
                else:
                    signatures_to_save.append('reporter')

            if customer_sig:
                valid, error, size = ReservationValidator.validate_signature_data(
                    customer_sig, SignatureService.MAX_SIGNATURE_SIZE
                )
                if not valid:
                    validation_errors.append(f"Customer signature: {error}")
                else:
                    signatures_to_save.append('customer')

            if auditor_sig:
                valid, error, size = ReservationValidator.validate_signature_data(
                    auditor_sig, SignatureService.MAX_SIGNATURE_SIZE
                )
                if not valid:
                    validation_errors.append(f"Auditor signature: {error}")
                else:
                    signatures_to_save.append('auditor')

            if validation_errors:
                return False, None, '; '.join(validation_errors)

            # Build update statement
            update_parts = []
            params = {
                'reservation_id': reservation_id,
                'storage_type': storage_type
            }

            if reporter_sig:
                update_parts.append('reporter_signature = :reporter_signature')
                params['reporter_signature'] = reporter_sig

            if customer_sig:
                update_parts.append('customer_signature = :customer_signature')
                params['customer_signature'] = customer_sig

            if auditor_sig:
                update_parts.append('auditor_signature = :auditor_signature')
                params['auditor_signature'] = auditor_sig

            # Update timestamps
            timestamps = SignatureService._update_signature_timestamps(
                session, reservation_id, signatures_to_save
            )

            update_parts.append('signature_storage_type = :storage_type')
            update_parts.append('signature_timestamps = :timestamps')
            update_parts.append('updated_at = :updated_at')

            params['timestamps'] = json.dumps(timestamps, ensure_ascii=False)
            params['updated_at'] = datetime.now()

            # Execute update
            update_sql = text(f"""
                UPDATE Reserved_Transaction
                SET {', '.join(update_parts)}
                WHERE id = :reservation_id
            """)

            session.execute(update_sql, params)
            session.commit()

            result_data = {
                'reservation_id': reservation_id,
                'signatures_saved': signatures_to_save,
                'timestamps': timestamps,
                'storage_type': storage_type
            }

            logger.info(f"[SignatureService] Saved {len(signatures_to_save)} signatures for reservation {reservation_id}")
            return True, result_data, None

        except Exception as e:
            session.rollback()
            logger.error(f"[SignatureService] Error saving signatures for reservation {reservation_id}: {e}", exc_info=True)
            return False, None, f"Failed to save signatures: {str(e)}"

    @staticmethod
    def _update_signature_timestamps(
        session,
        reservation_id: int,
        signature_types: List[str]
    ) -> Dict[str, str]:
        """
        Update signature timestamps

        Args:
            session: SQLAlchemy session
            reservation_id: Reservation ID
            signature_types: List of signature types being updated

        Returns:
            Dict of timestamps
        """
        # Get existing timestamps
        sql = text("SELECT signature_timestamps FROM Reserved_Transaction WHERE id = :reservation_id")
        result = session.execute(sql, {'reservation_id': reservation_id}).fetchone()

        existing_timestamps = {}
        if result and result[0]:
            try:
                existing_timestamps = json.loads(result[0])
            except (json.JSONDecodeError, TypeError):
                existing_timestamps = {}

        # Update timestamps for provided signatures
        current_time = datetime.now().isoformat()
        for sig_type in signature_types:
            existing_timestamps[f'{sig_type}_signature_at'] = current_time

        return existing_timestamps

    @staticmethod
    def get_reservation_signatures(
        session,
        reservation_id: int
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Get all signatures for a reservation

        Args:
            session: SQLAlchemy session
            reservation_id: Reservation ID

        Returns:
            Tuple of (success, signatures_data, error_message)
        """
        try:
            sql = text("""
                SELECT
                    reporter_signature,
                    customer_signature,
                    auditor_signature,
                    signature_storage_type,
                    signature_timestamps
                FROM Reserved_Transaction
                WHERE id = :reservation_id
            """)

            result = session.execute(sql, {'reservation_id': reservation_id}).fetchone()

            if not result:
                return False, None, "Reservation not found"

            # Parse timestamps
            timestamps = {}
            if result[4]:
                try:
                    timestamps = json.loads(result[4])
                except (json.JSONDecodeError, TypeError):
                    timestamps = {}

            signatures_data = {
                'reservation_id': reservation_id,
                'reporter_signature': result[0],
                'customer_signature': result[1],
                'auditor_signature': result[2],
                'storage_type': result[3] or 'base64',
                'timestamps': timestamps,
                'has_signatures': any([result[0], result[1], result[2]])
            }

            return True, signatures_data, None

        except Exception as e:
            logger.error(f"[SignatureService] Error getting signatures for reservation {reservation_id}: {e}", exc_info=True)
            return False, None, f"Failed to get signatures: {str(e)}"

    @staticmethod
    def delete_signature(
        session,
        reservation_id: int,
        signature_type: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Delete a specific signature

        Args:
            session: SQLAlchemy session
            reservation_id: Reservation ID
            signature_type: 'reporter', 'customer', or 'auditor'

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Validate signature type
            valid, error = ReservationValidator.validate_signature_type(signature_type)
            if not valid:
                return False, error

            # Check reservation exists
            reservation = AMLODatabaseHelper.get_reservation_or_none(session, reservation_id)
            if not reservation:
                return False, "Reservation not found"

            # Get existing timestamps
            sql = text("SELECT signature_timestamps FROM Reserved_Transaction WHERE id = :reservation_id")
            result = session.execute(sql, {'reservation_id': reservation_id}).fetchone()

            timestamps = {}
            if result and result[0]:
                try:
                    timestamps = json.loads(result[0])
                except (json.JSONDecodeError, TypeError):
                    timestamps = {}

            # Remove timestamp for this signature
            timestamp_key = f'{signature_type}_signature_at'
            if timestamp_key in timestamps:
                del timestamps[timestamp_key]

            # Update database
            field_name = f'{signature_type}_signature'
            update_sql = text(f"""
                UPDATE Reserved_Transaction
                SET {field_name} = NULL,
                    signature_timestamps = :timestamps,
                    updated_at = :updated_at
                WHERE id = :reservation_id
            """)

            session.execute(update_sql, {
                'reservation_id': reservation_id,
                'timestamps': json.dumps(timestamps, ensure_ascii=False),
                'updated_at': datetime.now()
            })
            session.commit()

            logger.info(f"[SignatureService] Deleted {signature_type} signature for reservation {reservation_id}")
            return True, None

        except Exception as e:
            session.rollback()
            logger.error(f"[SignatureService] Error deleting signature for reservation {reservation_id}: {e}", exc_info=True)
            return False, f"Failed to delete signature: {str(e)}"

    @staticmethod
    def validate_multiple_signatures(
        signatures: Dict[str, str]
    ) -> Tuple[bool, List[str]]:
        """
        Validate multiple signatures at once

        Args:
            signatures: Dict with signature data

        Returns:
            Tuple of (all_valid, error_messages)
        """
        errors = []

        for sig_type in ['reporter', 'customer', 'auditor']:
            sig_key = f'{sig_type}_signature'
            if sig_key in signatures and signatures[sig_key]:
                valid, error, size = ReservationValidator.validate_signature_data(
                    signatures[sig_key],
                    SignatureService.MAX_SIGNATURE_SIZE
                )
                if not valid:
                    errors.append(f"{sig_type.capitalize()}: {error}")

        return len(errors) == 0, errors
