# -*- coding: utf-8 -*-
"""
AMLO Report Service

Handles AMLO report management including:
- Listing reports with filters
- Marking reports as submitted to AMLO
- Batch operations
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import text
from datetime import datetime

from .db_helpers import AMLODatabaseHelper
from .validators import ReservationValidator

logger = logging.getLogger(__name__)


class ReportService:
    """Service layer for AMLO report management"""

    @staticmethod
    def list_reports(
        session,
        branch_id: int,
        filters: Dict[str, Any],
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        List AMLO reports with pagination and filtering

        Args:
            session: SQLAlchemy session
            branch_id: Branch ID to filter by
            filters: Dict with filter criteria (is_reported, start_date, end_date, report_type, customer_id)
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Dict with success, data (list of reports), and pagination info
        """
        try:
            # Validate pagination
            valid, error = ReservationValidator.validate_pagination(page, page_size)
            if not valid:
                return {'success': False, 'message': error, 'data': [], 'pagination': {}}

            # Build WHERE clauses
            where_clauses = ['r.branch_id = :branch_id']
            params = {'branch_id': branch_id}

            # is_reported filter
            if filters.get('is_reported') is not None:
                where_clauses.append('r.is_reported = :is_reported')
                params['is_reported'] = 1 if filters['is_reported'] else 0

            # Report type filter
            if filters.get('report_type'):
                where_clauses.append('r.report_type = :report_type')
                params['report_type'] = filters['report_type']

            # Customer ID filter
            if filters.get('customer_id'):
                where_clauses.append('r.customer_id = :customer_id')
                params['customer_id'] = filters['customer_id']

            # Reservation ID filter (for PDF viewing)
            # Note: AMLOReport table uses 'reserved_id', not 'reservation_id'
            if filters.get('reservation_id'):
                where_clauses.append('r.reserved_id = :reservation_id')
                params['reservation_id'] = filters['reservation_id']

            # Date filters
            AMLODatabaseHelper.apply_date_filters(
                where_clauses,
                params,
                filters.get('start_date'),
                filters.get('end_date'),
                date_field='r.created_at'
            )

            where_sql = ' AND '.join(where_clauses)

            # Count total
            count_sql = text(f"""
                SELECT COUNT(*) FROM AMLOReport r
                WHERE {where_sql}
            """)
            total = session.execute(count_sql, params).scalar() or 0

            # Get paginated results
            offset = (page - 1) * page_size
            params['limit'] = page_size
            params['offset'] = offset

            data_sql = text(f"""
                SELECT
                    r.id, r.reserved_id, r.report_no, r.report_type,
                    r.customer_name, r.customer_id,
                    r.branch_id, r.transaction_amount,
                    r.is_reported, r.report_time,
                    r.created_at, r.operator_id, r.updated_at,
                    res.status as reservation_status
                FROM AMLOReport r
                LEFT JOIN Reserved_Transaction res ON r.reserved_id = res.id
                WHERE {where_sql}
                ORDER BY r.created_at DESC
                LIMIT :limit OFFSET :offset
            """)

            results = session.execute(data_sql, params).fetchall()

            # Serialize results
            items = []
            for row in results:
                item = {
                    'id': row[0],
                    'reservation_id': row[1],  # This is reserved_id from database
                    'report_no': row[2],
                    'report_type': row[3],
                    'customer_name': row[4],
                    'customer_id': row[5],
                    'branch_id': row[6],
                    'amount': float(row[7]) if row[7] else None,  # transaction_amount
                    'is_reported': bool(row[8]),
                    'report_time': row[9].isoformat() if row[9] else None,
                    'created_at': row[10].isoformat() if row[10] else None,
                    'created_by': row[11],  # operator_id
                    'updated_at': row[12].isoformat() if row[12] else None,
                    'reservation_status': row[13]
                }
                items.append(item)

            return AMLODatabaseHelper.build_pagination_response(items, total, page, page_size)

        except Exception as e:
            logger.error(f"[ReportService] Error listing reports: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'Failed to list reports: {str(e)}',
                'data': [],
                'pagination': {}
            }

    @staticmethod
    def mark_reports_as_submitted(
        session,
        report_ids: List[int],
        reporter_id: int
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Mark multiple reports as submitted to AMLO

        Args:
            session: SQLAlchemy session
            report_ids: List of report IDs
            reporter_id: ID of user submitting reports

        Returns:
            Tuple of (success, result_data, error_message)
        """
        try:
            if not report_ids:
                return False, None, "No report IDs provided"

            # Validate all report IDs exist
            check_sql = text("""
                SELECT id, is_reported, report_no
                FROM AMLOReport
                WHERE id IN :report_ids
            """)

            results = session.execute(check_sql, {'report_ids': tuple(report_ids)}).fetchall()

            if len(results) != len(report_ids):
                return False, None, "Some report IDs not found"

            # Check if any already reported
            already_reported = [row[2] for row in results if row[1]]
            if already_reported:
                return False, None, f"Reports already submitted: {', '.join(already_reported)}"

            # Update reports
            update_sql = text("""
                UPDATE AMLOReport
                SET is_reported = 1,
                    report_time = :report_time,
                    updated_at = :updated_at
                WHERE id IN :report_ids
            """)

            report_time = datetime.now()

            session.execute(update_sql, {
                'report_ids': tuple(report_ids),
                'report_time': report_time,
                'updated_at': report_time
            })

            session.commit()

            result_data = {
                'updated_count': len(report_ids),
                'report_ids': report_ids,
                'report_time': report_time.isoformat()
            }

            logger.info(f"[ReportService] Marked {len(report_ids)} reports as submitted by user {reporter_id}")
            return True, result_data, None

        except Exception as e:
            session.rollback()
            logger.error(f"[ReportService] Error marking reports as submitted: {e}", exc_info=True)
            return False, None, f"Failed to mark reports as submitted: {str(e)}"

    @staticmethod
    def get_report_by_id(
        session,
        report_id: int
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Get report details by ID

        Args:
            session: SQLAlchemy session
            report_id: Report ID

        Returns:
            Tuple of (success, report_data, error_message)
        """
        try:
            sql = text("""
                SELECT
                    r.id, r.reserved_id, r.report_no, r.report_type,
                    r.customer_name, r.customer_id,
                    r.branch_id, r.transaction_amount,
                    r.is_reported, r.report_time,
                    r.created_at, r.operator_id, r.updated_at,
                    res.status as reservation_status, res.form_data
                FROM AMLOReport r
                LEFT JOIN Reserved_Transaction res ON r.reserved_id = res.id
                WHERE r.id = :report_id
            """)

            result = session.execute(sql, {'report_id': report_id}).fetchone()

            if not result:
                return False, None, "Report not found"

            report_data = {
                'id': result[0],
                'reservation_id': result[1],  # reserved_id from database
                'report_no': result[2],
                'report_type': result[3],
                'customer_name': result[4],
                'customer_id': result[5],
                'branch_id': result[6],
                'amount': float(result[7]) if result[7] else None,  # transaction_amount
                'is_reported': bool(result[8]),
                'report_time': result[9].isoformat() if result[9] else None,
                'created_at': result[10].isoformat() if result[10] else None,
                'created_by': result[11],  # operator_id
                'updated_at': result[12].isoformat() if result[12] else None,
                'reservation': {
                    'id': result[1],
                    'status': result[13],
                    'form_data': AMLODatabaseHelper.parse_form_data(result[14])
                }
            }

            return True, report_data, None

        except Exception as e:
            logger.error(f"[ReportService] Error getting report {report_id}: {e}", exc_info=True)
            return False, None, f"Failed to get report: {str(e)}"

    @staticmethod
    def batch_submit_reports(
        session,
        report_ids: List[int],
        reporter_id: int
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Batch submit multiple reports (validates each before submitting)

        Args:
            session: SQLAlchemy session
            report_ids: List of report IDs
            reporter_id: ID of user submitting

        Returns:
            Tuple of (success, result_data, error_message)
        """
        try:
            if not report_ids:
                return False, None, "No report IDs provided"

            # Validate each report
            validation_errors = []
            valid_report_ids = []

            for report_id in report_ids:
                check_sql = text("""
                    SELECT id, is_reported, report_no, report_type
                    FROM AMLOReport
                    WHERE id = :report_id
                """)
                result = session.execute(check_sql, {'report_id': report_id}).fetchone()

                if not result:
                    validation_errors.append(f"Report {report_id} not found")
                    continue

                if result[1]:  # is_reported
                    validation_errors.append(f"Report {result[2]} already submitted")
                    continue

                valid_report_ids.append(report_id)

            # If any validation errors, return them
            if validation_errors:
                return False, None, '; '.join(validation_errors)

            # Mark all valid reports as submitted
            if valid_report_ids:
                success, result_data, error = ReportService.mark_reports_as_submitted(
                    session, valid_report_ids, reporter_id
                )
                return success, result_data, error

            return False, None, "No valid reports to submit"

        except Exception as e:
            logger.error(f"[ReportService] Error batch submitting reports: {e}", exc_info=True)
            return False, None, f"Failed to batch submit reports: {str(e)}"
