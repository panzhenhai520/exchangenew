"""
Unit tests for AMLO ReservationService

Tests the business logic in services/amlo/reservation_service.py
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from src.services.amlo.reservation_service import ReservationService

# Mark all tests in this module
pytestmark = [pytest.mark.unit, pytest.mark.amlo, pytest.mark.services]


class TestCheckCustomerHasReservation:
    """Test check_customer_has_reservation method"""

    def test_returns_true_when_reservation_exists(self):
        """Should return True and reservation data when customer has pending reservation"""
        # Setup mock session
        mock_session = Mock()
        mock_result = Mock()
        mock_result.__getitem__ = lambda self, key: {
            0: 1,  # id
            1: 'AMLO-001',  # reservation_no
            2: 'AMLO-1-01',  # report_type
            3: 'buy',  # direction
            4: 'pending',  # status
            5: 'John Doe',  # customer_name
            6: 'ID123456',  # customer_id
            7: '123 Main St',  # customer_address
            8: 1,  # branch_id
            9: 1,  # currency_id
            10: 5000.0,  # amount
            11: '{}',  # form_data
            12: datetime.now(),  # created_at
            13: datetime.now()  # updated_at
        }[key]

        mock_session.execute.return_value.fetchone.return_value = mock_result

        # Execute
        has_reservation, data = ReservationService.check_customer_has_reservation(
            mock_session, 'ID123456', 1
        )

        # Assert
        assert has_reservation is True
        assert data is not None
        assert data['id'] == 1
        assert data['customer_id'] == 'ID123456'
        assert data['status'] == 'pending'

        # Verify SQL was called with correct params
        mock_session.execute.assert_called_once()
        call_args = mock_session.execute.call_args
        assert 'ID123456' in str(call_args) or call_args[0][1]['customer_id'] == 'ID123456'

    def test_returns_false_when_no_reservation(self):
        """Should return False when customer has no reservation"""
        # Setup mock session
        mock_session = Mock()
        mock_session.execute.return_value.fetchone.return_value = None

        # Execute
        has_reservation, data = ReservationService.check_customer_has_reservation(
            mock_session, 'ID999999', 1
        )

        # Assert
        assert has_reservation is False
        assert data is None

    def test_handles_exception_gracefully(self):
        """Should return False on database error"""
        # Setup mock session that raises exception
        mock_session = Mock()
        mock_session.execute.side_effect = Exception("Database error")

        # Execute
        has_reservation, data = ReservationService.check_customer_has_reservation(
            mock_session, 'ID123456', 1
        )

        # Assert
        assert has_reservation is False
        assert data is None


class TestListReservations:
    """Test list_reservations method"""

    def test_returns_paginated_results(self):
        """Should return paginated list with correct structure"""
        # Setup mock session
        mock_session = Mock()

        # Mock count query
        mock_session.execute.return_value.scalar.return_value = 10

        # Mock data query
        mock_row = (
            1, 'AMLO-001', 'AMLO-1-01', 'buy', 'pending',
            'John Doe', 'ID123', '123 Main St',
            1, 1, 5000.0,
            '{}', datetime.now(), datetime.now(),
            1, None, None,
            'USD', 'US Dollar',
            'admin', None
        )
        mock_session.execute.return_value.fetchall.return_value = [mock_row]

        # Execute
        result = ReservationService.list_reservations(
            mock_session,
            branch_id=1,
            filters={},
            page=1,
            page_size=20
        )

        # Assert
        assert result['success'] is True
        assert 'data' in result
        assert 'pagination' in result
        assert len(result['data']) == 1
        assert result['pagination']['total'] == 10
        assert result['pagination']['page'] == 1
        assert result['pagination']['page_size'] == 20

    def test_applies_status_filter(self):
        """Should filter by status when provided"""
        mock_session = Mock()
        mock_session.execute.return_value.scalar.return_value = 0
        mock_session.execute.return_value.fetchall.return_value = []

        # Execute with status filter
        result = ReservationService.list_reservations(
            mock_session,
            branch_id=1,
            filters={'status': 'approved'},
            page=1,
            page_size=20
        )

        # Assert SQL contains status filter
        assert result['success'] is True
        call_args = mock_session.execute.call_args_list
        # Should have 2 calls: count and data
        assert len(call_args) >= 2
        # Check that 'approved' was passed as parameter
        count_call = call_args[0]
        assert 'approved' in str(count_call) or count_call[0][1].get('status') == 'approved'

    def test_applies_date_filters(self):
        """Should filter by date range when provided"""
        mock_session = Mock()
        mock_session.execute.return_value.scalar.return_value = 0
        mock_session.execute.return_value.fetchall.return_value = []

        # Execute with date filters
        result = ReservationService.list_reservations(
            mock_session,
            branch_id=1,
            filters={
                'start_date': '2025-01-01',
                'end_date': '2025-01-31'
            },
            page=1,
            page_size=20
        )

        # Assert
        assert result['success'] is True
        call_args = mock_session.execute.call_args_list
        assert len(call_args) >= 2

    def test_validates_pagination_params(self):
        """Should return error for invalid pagination"""
        mock_session = Mock()

        # Execute with invalid page
        result = ReservationService.list_reservations(
            mock_session,
            branch_id=1,
            filters={},
            page=0,  # Invalid
            page_size=20
        )

        # Assert
        assert result['success'] is False
        assert 'message' in result
        assert result['data'] == []

    def test_handles_database_error(self):
        """Should handle database errors gracefully"""
        mock_session = Mock()
        mock_session.execute.side_effect = Exception("Database error")

        # Execute
        result = ReservationService.list_reservations(
            mock_session,
            branch_id=1,
            filters={},
            page=1,
            page_size=20
        )

        # Assert
        assert result['success'] is False
        assert 'message' in result


class TestGetReservationById:
    """Test get_reservation_by_id method"""

    def test_returns_reservation_with_full_details(self):
        """Should return complete reservation with related data"""
        mock_session = Mock()

        # Mock result with all fields
        mock_result = (
            1, 'AMLO-001', 'AMLO-1-01', 'buy', 'pending',
            'John Doe', 'ID123', '123 Main St',
            1, 1, 5000.0,
            '{}', datetime.now(), datetime.now(),
            1, 2, datetime.now(),
            None, None, None,  # signatures
            'USD', 'US Dollar',
            'BR001', 'Branch 1',
            'admin', 'Admin User',
            'auditor', 'Auditor User'
        )
        mock_session.execute.return_value.fetchone.return_value = mock_result

        # Execute
        success, data, error = ReservationService.get_reservation_by_id(
            mock_session, 1
        )

        # Assert
        assert success is True
        assert error is None
        assert data is not None
        assert data['id'] == 1
        assert data['reservation_no'] == 'AMLO-001'
        assert 'currency' in data
        assert 'branch' in data
        assert 'creator' in data

    def test_returns_error_when_not_found(self):
        """Should return error when reservation doesn't exist"""
        mock_session = Mock()
        mock_session.execute.return_value.fetchone.return_value = None

        # Execute
        success, data, error = ReservationService.get_reservation_by_id(
            mock_session, 999
        )

        # Assert
        assert success is False
        assert data is None
        assert error == "Reservation not found"

    def test_filters_by_branch_when_provided(self):
        """Should apply branch filter when branch_id is provided"""
        mock_session = Mock()
        mock_session.execute.return_value.fetchone.return_value = None

        # Execute with branch filter
        success, data, error = ReservationService.get_reservation_by_id(
            mock_session, 1, branch_id=1
        )

        # Assert
        assert success is False
        # Verify branch_id was in the query
        call_args = mock_session.execute.call_args
        assert 'branch_id' in str(call_args) or call_args[0][1].get('branch_id') == 1


class TestUpdateReservationFormData:
    """Test update_reservation_form_data method"""

    def test_updates_form_data_successfully(self):
        """Should update form data and return success"""
        mock_session = Mock()

        # Mock get_reservation_or_none to return a reservation
        with patch('src.services.amlo.reservation_service.AMLODatabaseHelper.get_reservation_or_none') as mock_get:
            mock_get.return_value = Mock()  # Reservation exists

            # Execute
            success, error = ReservationService.update_reservation_form_data(
                mock_session,
                reservation_id=1,
                form_data={'field1': 'value1'},
                user_id=1
            )

            # Assert
            assert success is True
            assert error is None
            mock_session.execute.assert_called_once()
            mock_session.commit.assert_called_once()

    def test_returns_error_when_reservation_not_found(self):
        """Should return error when reservation doesn't exist"""
        mock_session = Mock()

        with patch('src.services.amlo.reservation_service.AMLODatabaseHelper.get_reservation_or_none') as mock_get:
            mock_get.return_value = None

            # Execute
            success, error = ReservationService.update_reservation_form_data(
                mock_session,
                reservation_id=999,
                form_data={'field1': 'value1'},
                user_id=1
            )

            # Assert
            assert success is False
            assert error == "Reservation not found"

    def test_rolls_back_on_error(self):
        """Should rollback transaction on error"""
        mock_session = Mock()
        mock_session.execute.side_effect = Exception("Database error")

        with patch('src.services.amlo.reservation_service.AMLODatabaseHelper.get_reservation_or_none') as mock_get:
            mock_get.return_value = Mock()

            # Execute
            success, error = ReservationService.update_reservation_form_data(
                mock_session,
                reservation_id=1,
                form_data={'field1': 'value1'},
                user_id=1
            )

            # Assert
            assert success is False
            assert error is not None
            mock_session.rollback.assert_called_once()


class TestCompleteReservation:
    """Test complete_reservation method"""

    def test_completes_approved_reservation(self):
        """Should mark approved reservation as completed"""
        mock_session = Mock()

        # Mock reservation with 'approved' status
        mock_reservation = Mock()
        mock_reservation.__getitem__ = lambda self, key: {
            4: 'approved'  # status field
        }[key]

        with patch('src.services.amlo.reservation_service.AMLODatabaseHelper.get_reservation_or_none') as mock_get:
            mock_get.return_value = mock_reservation

            # Execute
            success, error = ReservationService.complete_reservation(
                mock_session,
                reservation_id=1,
                transaction_id=100,
                actual_amount=5000.0,
                user_id=1
            )

            # Assert
            assert success is True
            assert error is None
            mock_session.execute.assert_called_once()
            mock_session.commit.assert_called_once()

    def test_rejects_non_approved_status(self):
        """Should reject completion if status is not 'approved'"""
        mock_session = Mock()

        # Mock reservation with 'pending' status
        mock_reservation = Mock()
        mock_reservation.__getitem__ = lambda self, key: {
            4: 'pending'  # status field
        }[key]

        with patch('src.services.amlo.reservation_service.AMLODatabaseHelper.get_reservation_or_none') as mock_get:
            mock_get.return_value = mock_reservation

            # Execute
            success, error = ReservationService.complete_reservation(
                mock_session,
                reservation_id=1,
                transaction_id=100
            )

            # Assert
            assert success is False
            assert 'pending' in error.lower() or 'approved' in error.lower()

    def test_returns_error_when_not_found(self):
        """Should return error when reservation doesn't exist"""
        mock_session = Mock()

        with patch('src.services.amlo.reservation_service.AMLODatabaseHelper.get_reservation_or_none') as mock_get:
            mock_get.return_value = None

            # Execute
            success, error = ReservationService.complete_reservation(
                mock_session,
                reservation_id=999
            )

            # Assert
            assert success is False
            assert error == "Reservation not found"
