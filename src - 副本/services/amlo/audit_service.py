# -*- coding: utf-8 -*-
"""
AMLO Audit Service

Handles audit and approval workflow for AMLO reservations including:
- Approving reservations
- Rejecting reservations
- Reverse auditing (un-approving)
- Auto-creating AMLO reports on approval
"""

import logging
from typing import Dict, Any, Optional, Tuple, List
from sqlalchemy import text
from datetime import datetime

from .db_helpers import AMLODatabaseHelper
from .validators import ReservationValidator
# Note: ReportDataService import removed - not actually used in this module

logger = logging.getLogger(__name__)


class AuditService:
    """Service layer for AMLO audit and approval workflow"""

    @staticmethod
    def audit_reservation(
        session,
        reservation_id: int,
        action: str,
        auditor_id: int,
        rejection_reason: Optional[str] = None,
        remarks: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Audit a reservation (approve or reject)

        Args:
            session: SQLAlchemy session
            reservation_id: Reservation ID
            action: 'approve' or 'reject'
            auditor_id: ID of user performing audit
            rejection_reason: Required if action is 'reject'
            remarks: Optional audit remarks

        Returns:
            Tuple of (success, result_data, error_message)
        """
        try:
            # Validate action
            valid, error = ReservationValidator.validate_audit_action(action)
            if not valid:
                return False, None, error

            # Validate rejection reason
            valid, error = ReservationValidator.validate_rejection_reason(action, rejection_reason)
            if not valid:
                return False, None, error

            # Get reservation
            reservation = AMLODatabaseHelper.get_reservation_or_none(session, reservation_id)
            if not reservation:
                return False, None, "Reservation not found"

            # Check current status
            current_status = reservation[4]  # status field
            if current_status != 'pending':
                return False, None, f"Cannot audit reservation with status '{current_status}'. Must be 'pending'."

            # Determine target status
            target_status = 'approved' if action == 'approve' else 'rejected'

            # Validate status transition
            valid, error = ReservationValidator.validate_status_transition(
                current_status, target_status, action
            )
            if not valid:
                return False, None, error

            # Update reservation status
            update_sql = text("""
                UPDATE Reserved_Transaction
                SET status = :status,
                    auditor_id = :auditor_id,
                    audit_time = :audit_time,
                    rejection_reason = :rejection_reason,
                    remarks = :remarks
                WHERE id = :reservation_id
            """)

            session.execute(update_sql, {
                'reservation_id': reservation_id,
                'status': target_status,
                'auditor_id': auditor_id,
                'audit_time': datetime.now(),
                'rejection_reason': rejection_reason if action == 'reject' else None,
                'remarks': remarks
            })

            result_data = {
                'reservation_id': reservation_id,
                'action': action,
                'new_status': target_status,
                'audited_by': auditor_id,
                'audited_at': datetime.now().isoformat()
            }

            # If approved, auto-create AMLO report
            if action == 'approve':
                try:
                    report_result = AuditService._create_amlo_report_on_approval(
                        session, reservation, auditor_id
                    )
                    if report_result:
                        result_data['amlo_report_id'] = report_result.get('report_id')
                        result_data['amlo_report_no'] = report_result.get('report_no')
                except Exception as report_error:
                    logger.error(f"[AuditService] Failed to create AMLO report after approval: {report_error}")
                    # Don't fail the audit, but log the error
                    result_data['report_creation_error'] = str(report_error)

            session.commit()

            logger.info(f"[AuditService] {action.capitalize()}d reservation {reservation_id} by user {auditor_id}")
            return True, result_data, None

        except Exception as e:
            session.rollback()
            logger.error(f"[AuditService] Error auditing reservation {reservation_id}: {e}", exc_info=True)
            return False, None, f"Failed to audit reservation: {str(e)}"

    @staticmethod
    def _create_amlo_report_on_approval(
        session,
        reservation_row,
        auditor_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Auto-create AMLO report when reservation is approved

        Args:
            session: SQLAlchemy session
            reservation_row: Reservation database row
            auditor_id: ID of auditor who approved

        Returns:
            Dict with report_id and report_no, or None on failure
        """
        try:
            reservation_id = reservation_row[0]
            report_type = reservation_row[2]
            customer_name = reservation_row[5]
            customer_id = reservation_row[6]
            branch_id = reservation_row[8]
            currency_id = reservation_row[9]
            amount = reservation_row[10]

            # Generate report number
            report_no_sql = text("""
                SELECT CONCAT(
                    :report_type, '_',
                    :branch_code, '-',
                    LPAD(IFNULL(MAX(CAST(SUBSTRING_INDEX(report_no, '-', -1) AS UNSIGNED)), 0) + 1, 6, '0')
                )
                FROM AMLOReport
                WHERE report_type = :report_type
                  AND branch_id = :branch_id
                  AND YEAR(created_at) = YEAR(NOW())
            """)

            # Get branch code
            branch_sql = text("SELECT branch_code FROM branches WHERE id = :branch_id")
            branch_result = session.execute(branch_sql, {'branch_id': branch_id}).fetchone()
            branch_code = branch_result[0] if branch_result else '000'

            report_no_result = session.execute(report_no_sql, {
                'report_type': report_type,
                'branch_code': branch_code,
                'branch_id': branch_id
            }).fetchone()

            report_no = report_no_result[0] if report_no_result else f"{report_type}_{branch_code}-000001"

            # Insert AMLO report
            # Note: Use 'reserved_id' not 'reservation_id', 'operator_id' not 'created_by'
            # Also need to add required fields for AMLOReport
            insert_sql = text("""
                INSERT INTO AMLOReport (
                    reserved_id, report_no, report_type, report_format,
                    customer_name, customer_id,
                    branch_id, transaction_amount, transaction_date,
                    pdf_filename, pdf_path,
                    is_reported, operator_id, created_at
                ) VALUES (
                    :reserved_id, :report_no, :report_type, :report_format,
                    :customer_name, :customer_id,
                    :branch_id, :transaction_amount, NOW(),
                    :pdf_filename, :pdf_path,
                    0, :operator_id, NOW()
                )
            """)

            # Map report_type to report_format (e.g., 'AMLO-1-01' -> 'AMLO-1-01')
            report_format = report_type if report_type in ('AMLO-1-01', 'AMLO-1-02', 'AMLO-1-03') else 'AMLO-1-01'

            result = session.execute(insert_sql, {
                'reserved_id': reservation_id,
                'report_no': report_no,
                'report_type': 'CTR',  # Default to CTR, could be derived from report_format
                'report_format': report_format,
                'customer_name': customer_name,
                'customer_id': customer_id,
                'branch_id': branch_id,
                'transaction_amount': amount,
                'pdf_filename': f'{report_no}.pdf',
                'pdf_path': f'amlo_pdfs/{report_no}.pdf',
                'operator_id': auditor_id
            })

            report_id = result.lastrowid

            logger.info(f"[AuditService] Auto-created AMLO report {report_no} (ID: {report_id}) for reservation {reservation_id}")

            return {
                'report_id': report_id,
                'report_no': report_no
            }

        except Exception as e:
            logger.error(f"[AuditService] Error creating AMLO report: {e}", exc_info=True)
            return None

    @staticmethod
    def reverse_audit(
        session,
        reservation_id: int,
        auditor_id: int,
        remarks: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Reverse audit (revert approved/rejected back to pending)

        Args:
            session: SQLAlchemy session
            reservation_id: Reservation ID
            auditor_id: ID of user performing reverse audit
            remarks: Optional remarks

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
            if current_status not in ['approved', 'rejected']:
                return False, f"Cannot reverse audit reservation with status '{current_status}'. Must be 'approved' or 'rejected'."

            # Validate status transition
            valid, error = ReservationValidator.validate_status_transition(current_status, 'pending')
            if not valid:
                return False, error

            # Update reservation status back to pending
            update_sql = text("""
                UPDATE Reserved_Transaction
                SET status = 'pending',
                    audited_by = NULL,
                    audited_at = NULL,
                    rejection_reason = NULL,
                    audit_remarks = :remarks,
                    updated_at = :updated_at
                WHERE id = :reservation_id
            """)

            session.execute(update_sql, {
                'reservation_id': reservation_id,
                'remarks': remarks,
                'updated_at': datetime.now()
            })

            session.commit()

            logger.info(f"[AuditService] Reversed audit for reservation {reservation_id} by user {auditor_id}")
            return True, None

        except Exception as e:
            session.rollback()
            logger.error(f"[AuditService] Error reversing audit for reservation {reservation_id}: {e}", exc_info=True)
            return False, f"Failed to reverse audit: {str(e)}"

    @staticmethod
    def get_audit_history(
        session,
        reservation_id: int
    ) -> Tuple[bool, Optional[List[Dict[str, Any]]], Optional[str]]:
        """
        Get audit history for a reservation

        Args:
            session: SQLAlchemy session
            reservation_id: Reservation ID

        Returns:
            Tuple of (success, audit_history, error_message)
        """
        try:
            # In the current schema, we don't have a separate audit history table
            # We can only return the latest audit information
            reservation = AMLODatabaseHelper.get_reservation_or_none(session, reservation_id)
            if not reservation:
                return False, None, "Reservation not found"

            audit_history = []

            # If there's an auditor, add the audit record
            if reservation[15]:  # audited_by field
                auditor_info = AMLODatabaseHelper.get_user_info(session, reservation[15])

                audit_record = {
                    'audited_at': reservation[16].isoformat() if reservation[16] else None,
                    'auditor_id': reservation[15],
                    'auditor_username': auditor_info['username'],
                    'auditor_name': auditor_info['name'],
                    'status': reservation[4],  # current status
                    'remarks': None  # We don't have this in current schema
                }
                audit_history.append(audit_record)

            return True, audit_history, None

        except Exception as e:
            logger.error(f"[AuditService] Error getting audit history for reservation {reservation_id}: {e}", exc_info=True)
            return False, None, f"Failed to get audit history: {str(e)}"
