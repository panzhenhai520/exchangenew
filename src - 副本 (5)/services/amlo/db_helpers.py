# -*- coding: utf-8 -*-
"""
AMLO Database Helper Utilities

Provides common database query patterns and helper methods used across
AMLO service modules.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import text
from datetime import datetime

logger = logging.getLogger(__name__)


class AMLODatabaseHelper:
    """Shared database query helpers for AMLO services"""

    @staticmethod
    def get_reservation_or_none(session, reservation_id: int, branch_id: Optional[int] = None) -> Optional[Any]:
        """
        Get reservation by ID, optionally filtered by branch

        Args:
            session: SQLAlchemy session
            reservation_id: Reservation ID
            branch_id: Optional branch ID for filtering

        Returns:
            Reservation row or None if not found
        """
        try:
            sql = text("""
                SELECT
                    id, reservation_no, report_type, direction, status,
                    customer_name, customer_id, customer_country_code,
                    branch_id, currency_id, amount,
                    form_data, created_at, audit_time,
                    operator_id, auditor_id, rejection_reason
                FROM Reserved_Transaction
                WHERE id = :reservation_id
            """)

            params = {'reservation_id': reservation_id}

            if branch_id is not None:
                sql = text("""
                    SELECT
                        id, reservation_no, report_type, direction, status,
                        customer_name, customer_id, customer_country_code,
                        branch_id, currency_id, amount,
                        form_data, created_at, audit_time,
                        operator_id, auditor_id, rejection_reason
                    FROM Reserved_Transaction
                    WHERE id = :reservation_id AND branch_id = :branch_id
                """)
                params['branch_id'] = branch_id

            result = session.execute(sql, params).fetchone()
            return result

        except Exception as e:
            logger.error(f"[AMLODatabaseHelper] Error getting reservation {reservation_id}: {e}")
            return None

    @staticmethod
    def parse_form_data(form_data_json: Optional[str]) -> Dict[str, Any]:
        """
        Parse form_data JSON safely

        Args:
            form_data_json: JSON string from database

        Returns:
            Parsed dictionary or empty dict on error
        """
        if not form_data_json:
            return {}

        try:
            if isinstance(form_data_json, dict):
                return form_data_json
            return json.loads(form_data_json)
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"[AMLODatabaseHelper] Failed to parse form_data: {e}")
            return {}

    @staticmethod
    def build_pagination_response(items: List[Dict], total: int, page: int, page_size: int) -> Dict[str, Any]:
        """
        Build standard pagination response

        Args:
            items: List of items for current page
            total: Total count of items
            page: Current page number (1-indexed)
            page_size: Items per page

        Returns:
            Pagination response dictionary
        """
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

        return {
            'success': True,
            'data': {
                'items': items,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages
            }
        }

    @staticmethod
    def apply_date_filters(
        where_clauses: List[str],
        params: Dict[str, Any],
        start_date: Optional[str],
        end_date: Optional[str],
        date_field: str = 'created_at'
    ) -> None:
        """
        Apply date range filters to query

        Args:
            where_clauses: List to append WHERE conditions to
            params: Dict to add query parameters to
            start_date: Start date string (YYYY-MM-DD)
            end_date: End date string (YYYY-MM-DD)
            date_field: Database field name to filter on
        """
        if start_date:
            where_clauses.append(f'{date_field} >= :start_date')
            params['start_date'] = start_date

        if end_date:
            where_clauses.append(f'{date_field} <= :end_date')
            params['end_date'] = end_date

    @staticmethod
    def serialize_reservation_row(row: Any, include_form_data: bool = True) -> Dict[str, Any]:
        """
        Convert database row to dictionary

        Args:
            row: SQLAlchemy result row
            include_form_data: Whether to parse and include form_data

        Returns:
            Serialized dictionary
        """
        if not row:
            return {}

        result = {
            'id': row[0],
            'reservation_no': row[1],
            'report_type': row[2],
            'direction': row[3],
            'status': row[4],
            'customer_name': row[5],
            'customer_id': row[6],
            'customer_address': row[7],
            'branch_id': row[8],
            'currency_id': row[9],
            'amount': float(row[10]) if row[10] else None,
            'created_at': row[12].isoformat() if row[12] else None,
            'updated_at': row[13].isoformat() if row[13] else None,
            'created_by': row[14],
            'audited_by': row[15],
            'audited_at': row[16].isoformat() if row[16] else None
        }

        if include_form_data and len(row) > 11:
            result['form_data'] = AMLODatabaseHelper.parse_form_data(row[11])

        return result

    @staticmethod
    def get_user_info(session, user_id: Optional[int]) -> Dict[str, Any]:
        """
        Get basic user information

        Args:
            session: SQLAlchemy session
            user_id: User ID

        Returns:
            Dict with user info (id, username, name)
        """
        if not user_id:
            return {'id': None, 'username': None, 'name': None}

        try:
            sql = text("""
                SELECT id, username, full_name
                FROM operators
                WHERE id = :user_id
            """)
            result = session.execute(sql, {'user_id': user_id}).fetchone()

            if result:
                return {
                    'id': result[0],
                    'username': result[1],
                    'name': result[2] or result[1]
                }
        except Exception as e:
            logger.error(f"[AMLODatabaseHelper] Error getting user info for {user_id}: {e}")

        return {'id': user_id, 'username': None, 'name': None}

    @staticmethod
    def validate_branch_access(session, reservation_id: int, user_branch_id: int) -> bool:
        """
        Check if user's branch matches reservation's branch

        Args:
            session: SQLAlchemy session
            reservation_id: Reservation ID
            user_branch_id: User's branch ID

        Returns:
            True if branch matches, False otherwise
        """
        try:
            sql = text("SELECT branch_id FROM Reserved_Transaction WHERE id = :reservation_id")
            result = session.execute(sql, {'reservation_id': reservation_id}).fetchone()

            if not result:
                return False

            return result[0] == user_branch_id

        except Exception as e:
            logger.error(f"[AMLODatabaseHelper] Error validating branch access: {e}")
            return False
