"""
Unit tests for AMLO AuditService

Tests the audit workflow logic in services/amlo/audit_service.py
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from src.services.amlo.audit_service import AuditService

# Mark all tests in this module
pytestmark = [pytest.mark.unit, pytest.mark.amlo, pytest.mark.services]


class TestAuditReservation:
    """Test audit_reservation method"""

    def test_approves_pending_reservation(self):
        """Should approve pending reservation and create AMLO report"""
        mock_session = Mock()

        # Mock get_reservation_or_none to return pending reservation
        mock_reservation = Mock()
        mock_reservation.__getitem__ = lambda self, key: {
            0: 1,  # id
            2: 'AMLO-1-01',  # report_type
            4: 'pending',  # status
            5: 'John Doe',  # customer_name
            6: 'ID123',  # customer_id
            8: 1,  # branch_id
            9: 1,  # currency_id
            10: 5000.0  # amount
        }[key]

        with patch('src.services.amlo.audit_service.AMLODatabaseHelper.get_reservation_or_none') as mock_get:
            mock_get.return_value = mock_reservation

            # Mock report creation
            with patch.object(AuditService, '_create_amlo_report_on_approval') as mock_create_report:
                mock_create_report.return_value = {'report_id': 1, 'report_no': 'RPT-001'}

                # Execute
                success, result_data, error = AuditService.audit_reservation(
                    mock_session,
                    reservation_id=1,
                    action='approve',
                    auditor_id=2,
                    rejection_reason=None,
                    remarks='Looks good'
                )

                # Assert
                assert success is True
                assert error is None
                assert result_data is not None
                assert result_data['action'] == 'approve'
                assert result_data['new_status'] == 'approved'
                assert 'amlo_report_id' in result_data
                mock_session.commit.assert_called_once()

    def test_rejects_pending_reservation(self):
        """Should reject pending reservation with reason"""
        mock_session = Mock()

        mock_reservation = Mock()
        mock_reservation.__getitem__ = lambda self, key: {4: 'pending'}[key]

        with patch('src.services.amlo.audit_service.AMLODatabaseHelper.get_reservation_or_none') as mock_get:
            mock_get.return_value = mock_reservation

            # Execute
            success, result_data, error = AuditService.audit_reservation(
                mock_session,
                reservation_id=1,
                action='reject',
                auditor_id=2,
                rejection_reason='Insufficient documentation'
            )

            # Assert
            assert success is True
            assert error is None
            assert result_data['action'] == 'reject'
            assert result_data['new_status'] == 'rejected'

    def test_requires_rejection_reason_when_rejecting(self):
        """Should return error if rejection reason is missing"""
        mock_session = Mock()

        mock_reservation = Mock()
        mock_reservation.__getitem__ = lambda self, key: {4: 'pending'}[key]

        with patch('src.services.amlo.audit_service.AMLODatabaseHelper.get_reservation_or_none') as mock_get:
            mock_get.return_value = mock_reservation

            # Execute without rejection reason
            success, result_data, error = AuditService.audit_reservation(
                mock_session,
                reservation_id=1,
                action='reject',
                auditor_id=2,
                rejection_reason=None  # Missing!
            )

            # Assert
            assert success is False
            assert 'reason' in error.lower()

    def test_validates_audit_action(self):
        """Should return error for invalid action"""
        mock_session = Mock()

        # Execute with invalid action
        success, result_data, error = AuditService.audit_reservation(
            mock_session,
            reservation_id=1,
            action='invalid_action',
            auditor_id=2
        )

        # Assert
        assert success is False
        assert error is not None

    def test_rejects_non_pending_status(self):
        """Should not allow auditing non-pending reservations"""
        mock_session = Mock()

        # Mock reservation with 'completed' status
        mock_reservation = Mock()
        mock_reservation.__getitem__ = lambda self, key: {4: 'completed'}[key]

        with patch('src.services.amlo.audit_service.AMLODatabaseHelper.get_reservation_or_none') as mock_get:
            mock_get.return_value = mock_reservation

            # Execute
            success, result_data, error = AuditService.audit_reservation(
                mock_session,
                reservation_id=1,
                action='approve',
                auditor_id=2
            )

            # Assert
            assert success is False
            assert 'pending' in error.lower()

    def test_returns_error_when_reservation_not_found(self):
        """Should return error when reservation doesn't exist"""
        mock_session = Mock()

        with patch('src.services.amlo.audit_service.AMLODatabaseHelper.get_reservation_or_none') as mock_get:
            mock_get.return_value = None

            # Execute
            success, result_data, error = AuditService.audit_reservation(
                mock_session,
                reservation_id=999,
                action='approve',
                auditor_id=2
            )

            # Assert
            assert success is False
            assert error == "Reservation not found"

    def test_rolls_back_on_error(self):
        """Should rollback transaction on error"""
        mock_session = Mock()
        mock_session.execute.side_effect = Exception("Database error")

        mock_reservation = Mock()
        mock_reservation.__getitem__ = lambda self, key: {4: 'pending'}[key]

        with patch('src.services.amlo.audit_service.AMLODatabaseHelper.get_reservation_or_none') as mock_get:
            mock_get.return_value = mock_reservation

            # Execute
            success, result_data, error = AuditService.audit_reservation(
                mock_session,
                reservation_id=1,
                action='approve',
                auditor_id=2
            )

            # Assert
            assert success is False
            mock_session.rollback.assert_called_once()


class TestReverseAudit:
    """Test reverse_audit method"""

    def test_reverses_approved_to_pending(self):
        """Should revert approved reservation to pending"""
        mock_session = Mock()

        # Mock approved reservation
        mock_reservation = Mock()
        mock_reservation.__getitem__ = lambda self, key: {4: 'approved'}[key]

        with patch('src.services.amlo.audit_service.AMLODatabaseHelper.get_reservation_or_none') as mock_get:
            mock_get.return_value = mock_reservation

            # Execute
            success, error = AuditService.reverse_audit(
                mock_session,
                reservation_id=1,
                auditor_id=2,
                remarks='Need more review'
            )

            # Assert
            assert success is True
            assert error is None
            mock_session.execute.assert_called_once()
            mock_session.commit.assert_called_once()

    def test_reverses_rejected_to_pending(self):
        """Should revert rejected reservation to pending"""
        mock_session = Mock()

        mock_reservation = Mock()
        mock_reservation.__getitem__ = lambda self, key: {4: 'rejected'}[key]

        with patch('src.services.amlo.audit_service.AMLODatabaseHelper.get_reservation_or_none') as mock_get:
            mock_get.return_value = mock_reservation

            # Execute
            success, error = AuditService.reverse_audit(
                mock_session,
                reservation_id=1,
                auditor_id=2
            )

            # Assert
            assert success is True
            assert error is None

    def test_rejects_invalid_status_for_reverse(self):
        """Should not reverse audit on pending or completed status"""
        mock_session = Mock()

        # Mock pending reservation
        mock_reservation = Mock()
        mock_reservation.__getitem__ = lambda self, key: {4: 'pending'}[key]

        with patch('src.services.amlo.audit_service.AMLODatabaseHelper.get_reservation_or_none') as mock_get:
            mock_get.return_value = mock_reservation

            # Execute
            success, error = AuditService.reverse_audit(
                mock_session,
                reservation_id=1,
                auditor_id=2
            )

            # Assert
            assert success is False
            assert 'approved' in error.lower() or 'rejected' in error.lower()

    def test_returns_error_when_not_found(self):
        """Should return error when reservation doesn't exist"""
        mock_session = Mock()

        with patch('src.services.amlo.audit_service.AMLODatabaseHelper.get_reservation_or_none') as mock_get:
            mock_get.return_value = None

            # Execute
            success, error = AuditService.reverse_audit(
                mock_session,
                reservation_id=999,
                auditor_id=2
            )

            # Assert
            assert success is False
            assert error == "Reservation not found"


class TestCreateAMLOReportOnApproval:
    """Test _create_amlo_report_on_approval method"""

    def test_creates_report_with_generated_number(self):
        """Should create AMLO report with auto-generated report number"""
        mock_session = Mock()

        # Mock reservation row
        mock_reservation = (
            1, None, 'AMLO-1-01', None, None,
            'John Doe', 'ID123', None,
            1, 1, 5000.0
        )

        # Mock branch code query
        mock_session.execute.return_value.fetchone.side_effect = [
            ('BR001',),  # branch code
            ('AMLO-1-01_BR001-000001',)  # generated report number
        ]

        # Mock insert result
        mock_session.execute.return_value.lastrowid = 1

        # Execute
        result = AuditService._create_amlo_report_on_approval(
            mock_session,
            mock_reservation,
            auditor_id=2
        )

        # Assert
        assert result is not None
        assert 'report_id' in result
        assert 'report_no' in result
        assert result['report_id'] == 1

    def test_returns_none_on_error(self):
        """Should return None and log error on failure"""
        mock_session = Mock()
        mock_session.execute.side_effect = Exception("Database error")

        mock_reservation = (1, None, 'AMLO-1-01', None, None, 'John', 'ID', None, 1, 1, 5000.0)

        # Execute
        result = AuditService._create_amlo_report_on_approval(
            mock_session,
            mock_reservation,
            auditor_id=2
        )

        # Assert
        assert result is None


class TestGetAuditHistory:
    """Test get_audit_history method"""

    def test_returns_audit_info_when_available(self):
        """Should return audit history for audited reservation"""
        mock_session = Mock()

        # Mock reservation with audit info
        mock_reservation = (
            1, None, None, None, 'approved',  # status
            None, None, None, None, None, None, None, None, None,
            None, 2, datetime.now(),  # audited_by, audited_at
            None, None, None
        )

        with patch('src.services.amlo.audit_service.AMLODatabaseHelper.get_reservation_or_none') as mock_get:
            mock_get.return_value = mock_reservation

            with patch('services.amlo.audit_service.AMLODatabaseHelper.get_user_info') as mock_user:
                mock_user.return_value = {
                    'id': 2,
                    'username': 'auditor',
                    'name': 'Auditor User'
                }

                # Execute
                success, history, error = AuditService.get_audit_history(
                    mock_session,
                    reservation_id=1
                )

                # Assert
                assert success is True
                assert error is None
                assert len(history) == 1
                assert history[0]['auditor_id'] == 2

    def test_returns_empty_when_not_audited(self):
        """Should return empty history when not audited yet"""
        mock_session = Mock()

        # Mock reservation without audit info
        mock_reservation = (
            1, None, None, None, 'pending',
            None, None, None, None, None, None, None, None, None,
            None, None, None,  # No auditor
            None, None, None
        )

        with patch('src.services.amlo.audit_service.AMLODatabaseHelper.get_reservation_or_none') as mock_get:
            mock_get.return_value = mock_reservation

            # Execute
            success, history, error = AuditService.get_audit_history(
                mock_session,
                reservation_id=1
            )

            # Assert
            assert success is True
            assert history == []

    def test_returns_error_when_not_found(self):
        """Should return error when reservation doesn't exist"""
        mock_session = Mock()

        with patch('src.services.amlo.audit_service.AMLODatabaseHelper.get_reservation_or_none') as mock_get:
            mock_get.return_value = None

            # Execute
            success, history, error = AuditService.get_audit_history(
                mock_session,
                reservation_id=999
            )

            # Assert
            assert success is False
            assert error == "Reservation not found"
