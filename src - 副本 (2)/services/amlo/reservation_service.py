# -*- coding: utf-8 -*-
"""
AMLO Reservation Service

Handles all business logic for AMLO reservation management including:
- Checking customer reservations
- Listing reservations with filters
- Getting reservation details
- Updating reservation data
- Completing reservations
"""

import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import text
from datetime import datetime

from .db_helpers import AMLODatabaseHelper
from .validators import ReservationValidator

logger = logging.getLogger(__name__)


class ReservationService:
    """Service layer for AMLO reservation management"""

    @staticmethod
    def check_customer_has_reservation(
        session,
        customer_id: str,
        branch_id: int
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if customer has existing AMLO reservation

        Args:
            session: SQLAlchemy session
            customer_id: Customer ID number
            branch_id: Branch ID to filter by

        Returns:
            Tuple of (has_reservation, reservation_data)
        """
        try:
            sql = text("""
                SELECT
                    id, reservation_no, report_type, direction, status,
                    customer_name, customer_id, customer_address,
                    branch_id, currency_id, amount, form_data,
                    created_at, updated_at
                FROM Reserved_Transaction
                WHERE customer_id = :customer_id
                  AND branch_id = :branch_id
                  AND status IN ('pending', 'approved')
                ORDER BY created_at DESC
                LIMIT 1
            """)

            result = session.execute(sql, {
                'customer_id': customer_id,
                'branch_id': branch_id
            }).fetchone()

            if not result:
                return False, None

            # Parse reservation data
            reservation_data = {
                'id': result[0],
                'reservation_no': result[1],
                'report_type': result[2],
                'direction': result[3],
                'status': result[4],
                'customer_name': result[5],
                'customer_id': result[6],
                'customer_address': result[7],
                'branch_id': result[8],
                'currency_id': result[9],
                'amount': float(result[10]) if result[10] else None,
                'form_data': AMLODatabaseHelper.parse_form_data(result[11]),
                'created_at': result[12].isoformat() if result[12] else None,
                'updated_at': result[13].isoformat() if result[13] else None
            }

            return True, reservation_data

        except Exception as e:
            logger.error(f"[ReservationService] Error checking customer reservation: {e}", exc_info=True)
            return False, None

    @staticmethod
    def list_reservations(
        session,
        branch_id: int,
        filters: Dict[str, Any],
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        List reservations with pagination and filtering

        Args:
            session: SQLAlchemy session
            branch_id: Branch ID to filter by
            filters: Dict with filter criteria (status, start_date, end_date, customer_id, report_type)
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Dict with success, data (list of reservations), and pagination info
        """
        try:
            # Validate pagination
            valid, error = ReservationValidator.validate_pagination(page, page_size)
            if not valid:
                return {'success': False, 'message': error, 'data': [], 'pagination': {}}

            # Build WHERE clauses (no table alias, direct field names)
            where_clauses = ['branch_id = :branch_id']
            params = {'branch_id': branch_id}

            # Status filter
            if filters.get('status'):
                where_clauses.append('status = :status')
                params['status'] = filters['status']

            # Customer ID filter
            if filters.get('customer_id'):
                where_clauses.append('customer_id = :customer_id')
                params['customer_id'] = filters['customer_id']

            # Report type filter
            if filters.get('report_type'):
                where_clauses.append('report_type = :report_type')
                params['report_type'] = filters['report_type']

            # Date filters (no prefix)
            AMLODatabaseHelper.apply_date_filters(
                where_clauses,
                params,
                filters.get('start_date'),
                filters.get('end_date'),
                date_field='created_at'
            )

            where_sql = ' AND '.join(where_clauses)

            # Count total
            count_sql = text(f"""
                SELECT COUNT(*) FROM Reserved_Transaction
                WHERE {where_sql}
            """)
            total = session.execute(count_sql, params).scalar() or 0

            # Get paginated results
            offset = (page - 1) * page_size
            params['limit'] = page_size
            params['offset'] = offset

            data_sql = text(f"""
                SELECT
                    id, reservation_no, customer_id, customer_name,
                    customer_country_code, currency_id, direction,
                    amount, local_amount, rate, trigger_type,
                    report_type, status, branch_id, operator_id,
                    auditor_id, created_at, audit_time,
                    rejection_reason, exchange_type, funding_source,
                    form_data
                FROM Reserved_Transaction
                WHERE {where_sql}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """)

            data_result = session.execute(data_sql, params)
            items = [dict(row._mapping) for row in data_result]

            # Convert dates to ISO format
            for item in items:
                if item.get('created_at'):
                    item['created_at'] = item['created_at'].isoformat()
                if item.get('audit_time'):
                    item['audit_time'] = item['audit_time'].isoformat()
                # Parse form_data JSON if present
                if item.get('form_data'):
                    item['form_data'] = AMLODatabaseHelper.parse_form_data(item['form_data'])

            return AMLODatabaseHelper.build_pagination_response(items, total, page, page_size)

        except Exception as e:
            logger.error(f"[ReservationService] Error listing reservations: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'Failed to list reservations: {str(e)}',
                'data': [],
                'pagination': {}
            }

    @staticmethod
    def get_reservation_by_id(
        session,
        reservation_id: int,
        branch_id: Optional[int] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Get reservation details by ID

        Args:
            session: SQLAlchemy session
            reservation_id: Reservation ID
            branch_id: Optional branch ID for access control

        Returns:
            Tuple of (success, reservation_data, error_message)
        """
        try:
            # Get reservation with related data
            # Simplified query - only get fields that exist
            sql = text("""
                SELECT
                    id, reservation_no, report_type, direction, status,
                    customer_name, customer_id, customer_country_code,
                    branch_id, currency_id, amount, local_amount, rate,
                    form_data, created_at, audit_time,
                    operator_id, auditor_id, rejection_reason
                FROM Reserved_Transaction
                WHERE id = :reservation_id
            """)

            params = {'reservation_id': reservation_id}

            # Add branch filter if provided
            if branch_id is not None:
                sql = text("""
                    SELECT
                        id, reservation_no, report_type, direction, status,
                        customer_name, customer_id, customer_country_code,
                        branch_id, currency_id, amount, local_amount, rate,
                        form_data, created_at, audit_time,
                        operator_id, auditor_id, rejection_reason
                    FROM Reserved_Transaction
                    WHERE id = :reservation_id AND branch_id = :branch_id
                """)
                params['branch_id'] = branch_id

            result = session.execute(sql, params).fetchone()

            if not result:
                return False, None, "Reservation not found"

            # Build reservation data with correct field mapping
            reservation_data = {
                'id': result[0],
                'reservation_no': result[1],
                'report_type': result[2],
                'direction': result[3],
                'status': result[4],
                'customer_name': result[5],
                'customer_id': result[6],
                'customer_country_code': result[7],
                'branch_id': result[8],
                'currency_id': result[9],
                'amount': float(result[10]) if result[10] else None,
                'local_amount': float(result[11]) if result[11] else None,
                'rate': float(result[12]) if result[12] else None,
                'form_data': AMLODatabaseHelper.parse_form_data(result[13]),
                'created_at': result[14].isoformat() if result[14] else None,
                'audit_time': result[15].isoformat() if result[15] else None,
                'operator_id': result[16],
                'auditor_id': result[17],
                'rejection_reason': result[18]
            }

            return True, reservation_data, None

        except Exception as e:
            logger.error(f"[ReservationService] Error getting reservation {reservation_id}: {e}", exc_info=True)
            return False, None, f"Failed to get reservation: {str(e)}"

    @staticmethod
    def update_reservation_form_data(
        session,
        reservation_id: int,
        form_data: Dict[str, Any],
        user_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Update reservation form data

        Args:
            session: SQLAlchemy session
            reservation_id: Reservation ID
            form_data: New form data dictionary
            user_id: User performing the update

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Validate form data
            valid, error = ReservationValidator.validate_form_data(form_data)
            if not valid:
                return False, error

            # Check reservation exists
            reservation = AMLODatabaseHelper.get_reservation_or_none(session, reservation_id)
            if not reservation:
                return False, "Reservation not found"

            # Update form_data
            form_data_json = json.dumps(form_data, ensure_ascii=False)

            update_sql = text("""
                UPDATE Reserved_Transaction
                SET form_data = :form_data
                WHERE id = :reservation_id
            """)

            session.execute(update_sql, {
                'reservation_id': reservation_id,
                'form_data': form_data_json
            })
            session.commit()

            logger.info(f"[ReservationService] Updated form_data for reservation {reservation_id} by user {user_id}")
            return True, None

        except Exception as e:
            session.rollback()
            logger.error(f"[ReservationService] Error updating reservation {reservation_id}: {e}", exc_info=True)
            return False, f"Failed to update reservation: {str(e)}"

    @staticmethod
    def complete_reservation(
        session,
        reservation_id: int,
        transaction_id: Optional[int] = None,
        actual_amount: Optional[float] = None,
        user_id: Optional[int] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Mark reservation as completed after transaction

        Args:
            session: SQLAlchemy session
            reservation_id: Reservation ID
            transaction_id: Linked transaction ID
            actual_amount: Actual transaction amount
            user_id: User completing the reservation

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Get reservation
            reservation = AMLODatabaseHelper.get_reservation_or_none(session, reservation_id)
            if not reservation:
                return False, "Reservation not found"

            # Check current status
            current_status = reservation[4]  # status field
            if current_status != 'approved':
                return False, f"Cannot complete reservation with status '{current_status}'. Must be 'approved'."

            # Validate status transition
            valid, error = ReservationValidator.validate_status_transition(current_status, 'completed')
            if not valid:
                return False, error

            # Update status
            update_sql = text("""
                UPDATE Reserved_Transaction
                SET status = 'completed',
                    linked_transaction_id = :transaction_id,
                    actual_amount = :actual_amount,
                    completed_at = :completed_at
                WHERE id = :reservation_id
            """)

            session.execute(update_sql, {
                'reservation_id': reservation_id,
                'transaction_id': transaction_id,
                'actual_amount': actual_amount,
                'completed_at': datetime.now()
            })
            session.commit()

            logger.info(f"[ReservationService] Completed reservation {reservation_id} with transaction {transaction_id} by user {user_id}")
            return True, None

        except Exception as e:
            session.rollback()
            logger.error(f"[ReservationService] Error completing reservation {reservation_id}: {e}", exc_info=True)
            return False, f"Failed to complete reservation: {str(e)}"
