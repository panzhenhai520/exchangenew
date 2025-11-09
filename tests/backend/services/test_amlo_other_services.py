"""
Unit tests for other AMLO services (ReportService, SignatureService, PDFGenerationService)

Tests the business logic in services/amlo/
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from src.services.amlo.report_service import ReportService
from src.services.amlo.signature_service import SignatureService
from src.services.amlo.pdf_generation_service import PDFGenerationService

# Mark all tests in this module
pytestmark = [pytest.mark.unit, pytest.mark.amlo, pytest.mark.services]


# ==============================================================================
# ReportService Tests
# ==============================================================================

class TestReportServiceListReports:
    """Test ReportService.list_reports"""

    def test_lists_reports_with_pagination(self):
        """Should return paginated report list"""
        mock_session = Mock()
        mock_session.execute.return_value.scalar.return_value = 5
        mock_session.execute.return_value.fetchall.return_value = []

        result = ReportService.list_reports(
            mock_session,
            branch_id=1,
            filters={},
            page=1,
            page_size=20
        )

        assert result['success'] is True
        assert result['pagination']['total'] == 5

    def test_applies_is_reported_filter(self):
        """Should filter by is_reported status"""
        mock_session = Mock()
        mock_session.execute.return_value.scalar.return_value = 0
        mock_session.execute.return_value.fetchall.return_value = []

        result = ReportService.list_reports(
            mock_session,
            branch_id=1,
            filters={'is_reported': True},
            page=1,
            page_size=20
        )

        assert result['success'] is True
        # Verify is_reported=1 was in params
        call_args = mock_session.execute.call_args_list[0]
        assert call_args[0][1].get('is_reported') == 1


class TestReportServiceMarkAsSubmitted:
    """Test ReportService.mark_reports_as_submitted"""

    def test_marks_multiple_reports(self):
        """Should mark multiple reports as submitted"""
        mock_session = Mock()

        # Mock check query - all reports exist and not reported
        mock_session.execute.return_value.fetchall.return_value = [
            (1, 0, 'RPT-001'),
            (2, 0, 'RPT-002')
        ]

        success, result, error = ReportService.mark_reports_as_submitted(
            mock_session,
            report_ids=[1, 2],
            reporter_id=1
        )

        assert success is True
        assert result['updated_count'] == 2
        mock_session.commit.assert_called_once()

    def test_rejects_already_reported(self):
        """Should reject if any report already submitted"""
        mock_session = Mock()

        # Mock one report already reported
        mock_session.execute.return_value.fetchall.return_value = [
            (1, 1, 'RPT-001')  # is_reported=1
        ]

        success, result, error = ReportService.mark_reports_as_submitted(
            mock_session,
            report_ids=[1],
            reporter_id=1
        )

        assert success is False
        assert 'already' in error.lower()


class TestReportServiceGetById:
    """Test ReportService.get_report_by_id"""

    def test_returns_complete_report_data(self):
        """Should return report with all related data"""
        mock_session = Mock()

        # Mock result
        mock_result = (
            1, 1, 'RPT-001', 'AMLO-1-01',
            'John Doe', 'ID123',
            1, 1, 5000.0,
            0, None,
            datetime.now(), 1, datetime.now(),
            'USD', 'US Dollar',
            'BR001', 'Branch 1',
            'admin', 'Admin User',
            'pending', '{}'
        )
        mock_session.execute.return_value.fetchone.return_value = mock_result

        success, data, error = ReportService.get_report_by_id(mock_session, 1)

        assert success is True
        assert data['id'] == 1
        assert 'currency' in data
        assert 'branch' in data


# ==============================================================================
# SignatureService Tests
# ==============================================================================

class TestSignatureServiceSave:
    """Test SignatureService.save_reservation_signatures"""

    def test_saves_valid_signatures(self):
        """Should save valid signature data"""
        mock_session = Mock()

        with patch('src.services.amlo.signature_service.AMLODatabaseHelper.get_reservation_or_none') as mock_get:
            mock_get.return_value = Mock()  # Reservation exists

            signatures = {
                'reporter_signature': 'data:image/png;base64,iVBORw0KGgo=',
                'customer_signature': 'data:image/png;base64,iVBORw0KGgo='
            }

            success, result, error = SignatureService.save_reservation_signatures(
                mock_session,
                reservation_id=1,
                signatures=signatures
            )

            assert success is True
            assert len(result['signatures_saved']) == 2
            mock_session.commit.assert_called_once()

    def test_validates_signature_format(self):
        """Should reject invalid signature format"""
        mock_session = Mock()

        with patch('src.services.amlo.signature_service.AMLODatabaseHelper.get_reservation_or_none') as mock_get:
            mock_get.return_value = Mock()

            signatures = {
                'reporter_signature': 'invalid_format'  # Wrong format
            }

            success, result, error = SignatureService.save_reservation_signatures(
                mock_session,
                reservation_id=1,
                signatures=signatures
            )

            assert success is False
            assert 'format' in error.lower()

    def test_requires_at_least_one_signature(self):
        """Should reject if no signatures provided"""
        mock_session = Mock()

        with patch('src.services.amlo.signature_service.AMLODatabaseHelper.get_reservation_or_none') as mock_get:
            mock_get.return_value = Mock()

            success, result, error = SignatureService.save_reservation_signatures(
                mock_session,
                reservation_id=1,
                signatures={}  # Empty
            )

            assert success is False
            assert 'at least one' in error.lower()


class TestSignatureServiceGet:
    """Test SignatureService.get_reservation_signatures"""

    def test_returns_all_signatures(self):
        """Should return all signature data"""
        mock_session = Mock()

        mock_result = (
            'data:image/png;base64,AAA=',  # reporter
            'data:image/png;base64,BBB=',  # customer
            None,  # auditor
            'base64',
            '{"reporter_signature_at": "2025-11-03T10:00:00"}'
        )
        mock_session.execute.return_value.fetchone.return_value = mock_result

        success, data, error = SignatureService.get_reservation_signatures(
            mock_session,
            reservation_id=1
        )

        assert success is True
        assert data['reporter_signature'] is not None
        assert data['customer_signature'] is not None
        assert data['auditor_signature'] is None
        assert data['has_signatures'] is True


class TestSignatureServiceDelete:
    """Test SignatureService.delete_signature"""

    def test_deletes_specific_signature(self):
        """Should delete specified signature type"""
        mock_session = Mock()

        # Mock existing timestamps
        mock_session.execute.return_value.fetchone.return_value = (
            '{"reporter_signature_at": "2025-11-03T10:00:00"}',
        )

        with patch('src.services.amlo.signature_service.AMLODatabaseHelper.get_reservation_or_none') as mock_get:
            mock_get.return_value = Mock()

            success, error = SignatureService.delete_signature(
                mock_session,
                reservation_id=1,
                signature_type='reporter'
            )

            assert success is True
            mock_session.commit.assert_called_once()

    def test_validates_signature_type(self):
        """Should reject invalid signature type"""
        mock_session = Mock()

        success, error = SignatureService.delete_signature(
            mock_session,
            reservation_id=1,
            signature_type='invalid_type'
        )

        assert success is False
        assert 'invalid' in error.lower()


# ==============================================================================
# PDFGenerationService Tests
# ==============================================================================

class TestPDFGenerationNormalizeBool:
    """Test PDFGenerationService.normalize_bool"""

    def test_normalizes_various_types(self):
        """Should normalize different value types to boolean"""
        assert PDFGenerationService.normalize_bool(True) is True
        assert PDFGenerationService.normalize_bool(False) is False
        assert PDFGenerationService.normalize_bool('true') is True
        assert PDFGenerationService.normalize_bool('1') is True
        assert PDFGenerationService.normalize_bool('yes') is True
        assert PDFGenerationService.normalize_bool('false') is False
        assert PDFGenerationService.normalize_bool('0') is False
        assert PDFGenerationService.normalize_bool(1) is True
        assert PDFGenerationService.normalize_bool(0) is False
        assert PDFGenerationService.normalize_bool(None) is False


class TestPDFGenerationCombineFields:
    """Test PDFGenerationService field combination methods"""

    def test_combines_name_fields(self):
        """Should combine name components correctly"""
        form_data = {
            'person_title': 'Mr.',
            'person_firstname': 'John',
            'person_lastname': 'Doe'
        }

        result = PDFGenerationService.combine_name_fields(form_data, 'person')

        assert 'Mr.' in result
        assert 'John' in result
        assert 'Doe' in result

    def test_uses_full_name_if_provided(self):
        """Should prefer full_name over components"""
        form_data = {
            'person_full_name': 'John Doe',
            'person_firstname': 'Jane',
            'person_lastname': 'Smith'
        }

        result = PDFGenerationService.combine_name_fields(form_data, 'person')

        assert result == 'John Doe'

    def test_combines_address_fields(self):
        """Should combine address components in order"""
        form_data = {
            'addr_number': '123',
            'addr_road': 'Main St',
            'addr_district': 'Downtown',
            'addr_province': 'Bangkok'
        }

        result = PDFGenerationService.combine_address_fields(form_data, 'addr')

        assert '123' in result
        assert 'Main St' in result
        assert 'Downtown' in result


class TestPDFGenerationParseDateFromComponents:
    """Test PDFGenerationService.parse_date_from_components"""

    def test_parses_valid_date(self):
        """Should parse date from day/month/year fields"""
        form_data = {
            'date_day': '15',
            'date_month': '10',
            'date_year': '2025'
        }

        result = PDFGenerationService.parse_date_from_components(
            form_data, 'date_day', 'date_month', 'date_year'
        )

        assert result is not None
        assert result.year == 2025
        assert result.month == 10
        assert result.day == 15

    def test_handles_two_digit_year(self):
        """Should convert 2-digit year to 4-digit"""
        form_data = {
            'date_day': '15',
            'date_month': '10',
            'date_year': '25'
        }

        result = PDFGenerationService.parse_date_from_components(
            form_data, 'date_day', 'date_month', 'date_year'
        )

        assert result.year == 2025

    def test_returns_none_for_missing_fields(self):
        """Should return None if any field missing"""
        form_data = {'date_day': '15'}

        result = PDFGenerationService.parse_date_from_components(
            form_data, 'date_day', 'date_month', 'date_year'
        )

        assert result is None


class TestPDFGenerationGetBlankForm:
    """Test PDFGenerationService.get_blank_form_path"""

    def test_returns_path_for_valid_type(self):
        """Should return file path for valid report type"""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True

            success, path, error = PDFGenerationService.get_blank_form_path('AMLO-1-01')

            assert success is True
            assert 'AMLO-1-01.pdf' in path

    def test_rejects_invalid_type(self):
        """Should reject invalid report type"""
        success, path, error = PDFGenerationService.get_blank_form_path('INVALID')

        assert success is False
        assert 'invalid' in error.lower()

    def test_returns_error_if_file_not_exists(self):
        """Should return error if file doesn't exist"""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False

            success, path, error = PDFGenerationService.get_blank_form_path('AMLO-1-01')

            assert success is False
            assert 'not found' in error.lower()
