# -*- coding: utf-8 -*-
"""
AMLO Validation Utilities

Provides validation functions for AMLO business logic
"""

import logging
from typing import Tuple, Optional, Dict, Any

logger = logging.getLogger(__name__)


class ReservationValidator:
    """Validation utilities for AMLO reservations"""

    # Valid status values
    VALID_STATUSES = ['pending', 'approved', 'rejected', 'completed']

    # Valid audit actions
    VALID_AUDIT_ACTIONS = ['approve', 'reject']

    # Valid signature types
    VALID_SIGNATURE_TYPES = ['reporter', 'customer', 'auditor']

    # Valid report types
    VALID_REPORT_TYPES = ['AMLO-1-01', 'AMLO-1-02', 'AMLO-1-03']

    @staticmethod
    def validate_status(status: str) -> Tuple[bool, Optional[str]]:
        """
        Validate reservation status

        Args:
            status: Status string to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not status:
            return False, "Status cannot be empty"

        if status not in ReservationValidator.VALID_STATUSES:
            return False, f"Invalid status: {status}. Must be one of {ReservationValidator.VALID_STATUSES}"

        return True, None

    @staticmethod
    def validate_audit_action(action: str) -> Tuple[bool, Optional[str]]:
        """
        Validate audit action

        Args:
            action: Action string (approve/reject)

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not action:
            return False, "Action cannot be empty"

        if action not in ReservationValidator.VALID_AUDIT_ACTIONS:
            return False, f"Invalid action: {action}. Must be 'approve' or 'reject'"

        return True, None

    @staticmethod
    def validate_status_transition(current_status: str, target_status: str, action: str = None) -> Tuple[bool, Optional[str]]:
        """
        Validate status state machine transitions

        State machine:
        - pending -> approved (audit with approve)
        - pending -> rejected (audit with reject)
        - approved -> completed (complete transaction)
        - approved -> pending (reverse audit)
        - rejected -> pending (reverse audit)

        Args:
            current_status: Current reservation status
            target_status: Target status
            action: Optional audit action

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate both statuses
        valid, error = ReservationValidator.validate_status(current_status)
        if not valid:
            return False, f"Current status invalid: {error}"

        valid, error = ReservationValidator.validate_status(target_status)
        if not valid:
            return False, f"Target status invalid: {error}"

        # Define valid transitions
        valid_transitions = {
            'pending': ['approved', 'rejected'],
            'approved': ['completed', 'pending'],
            'rejected': ['pending'],
            'completed': []  # No transitions from completed
        }

        if target_status not in valid_transitions.get(current_status, []):
            return False, f"Cannot transition from '{current_status}' to '{target_status}'"

        # Additional validation for audit actions
        if action:
            if current_status == 'pending':
                if action == 'approve' and target_status != 'approved':
                    return False, "Approve action must result in 'approved' status"
                if action == 'reject' and target_status != 'rejected':
                    return False, "Reject action must result in 'rejected' status"

        return True, None

    @staticmethod
    def validate_rejection_reason(action: str, rejection_reason: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate rejection reason is provided when rejecting

        Args:
            action: Audit action
            rejection_reason: Rejection reason text

        Returns:
            Tuple of (is_valid, error_message)
        """
        if action == 'reject':
            if not rejection_reason or not rejection_reason.strip():
                return False, "Rejection reason is required when rejecting"

        return True, None

    @staticmethod
    def validate_signature_type(signature_type: str) -> Tuple[bool, Optional[str]]:
        """
        Validate signature type

        Args:
            signature_type: Signature type string

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not signature_type:
            return False, "Signature type cannot be empty"

        if signature_type not in ReservationValidator.VALID_SIGNATURE_TYPES:
            return False, f"Invalid signature type: {signature_type}. Must be one of {ReservationValidator.VALID_SIGNATURE_TYPES}"

        return True, None

    @staticmethod
    def validate_signature_data(signature_data: str, max_size: int = 500 * 1024) -> Tuple[bool, Optional[str], int]:
        """
        Validate signature data format and size

        Args:
            signature_data: Base64 signature data
            max_size: Maximum size in bytes (default 500KB)

        Returns:
            Tuple of (is_valid, error_message, data_size)
        """
        if not signature_data:
            return False, "Signature data cannot be empty", 0

        data_size = len(signature_data)

        # Check format
        if not signature_data.startswith('data:image/png;base64,'):
            return False, "Signature must be in format 'data:image/png;base64,...'", data_size

        # Check size
        if data_size > max_size:
            return False, f"Signature too large: {data_size / 1024:.2f}KB (max {max_size / 1024:.0f}KB)", data_size

        return True, None, data_size

    @staticmethod
    def validate_report_type(report_type: str) -> Tuple[bool, Optional[str]]:
        """
        Validate AMLO report type

        Args:
            report_type: Report type string

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not report_type:
            return False, "Report type cannot be empty"

        if report_type not in ReservationValidator.VALID_REPORT_TYPES:
            return False, f"Invalid report type: {report_type}. Must be one of {ReservationValidator.VALID_REPORT_TYPES}"

        return True, None

    @staticmethod
    def validate_pagination(page: int, page_size: int, max_page_size: int = 100) -> Tuple[bool, Optional[str]]:
        """
        Validate pagination parameters

        Args:
            page: Page number (1-indexed)
            page_size: Items per page
            max_page_size: Maximum allowed page size

        Returns:
            Tuple of (is_valid, error_message)
        """
        if page < 1:
            return False, "Page number must be >= 1"

        if page_size < 1:
            return False, "Page size must be >= 1"

        if page_size > max_page_size:
            return False, f"Page size too large (max {max_page_size})"

        return True, None

    @staticmethod
    def validate_form_data(form_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate form data structure

        Args:
            form_data: Form data dictionary

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(form_data, dict):
            return False, "Form data must be a dictionary"

        # Add specific validation rules as needed
        # For now, just check it's a valid dict

        return True, None
