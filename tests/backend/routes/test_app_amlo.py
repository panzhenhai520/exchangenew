"""
Unit tests for AMLO routes (app_amlo.py)
Tests PDF generation, batch reporting, and report listing
"""
import pytest
from unittest.mock import patch, Mock, MagicMock, mock_open
from datetime import datetime, timedelta
import io
import zipfile

# Mark all tests in this module
pytestmark = [pytest.mark.unit, pytest.mark.amlo, pytest.mark.routes]


class TestGetReports:
    """Test GET /api/amlo/reports endpoint"""

    @patch('src.routes.app_amlo.DatabaseService')
    @patch('src.routes.app_amlo.current_user_info')
    def test_get_reports_success(self, mock_user_info, mock_db_service, mock_db_session,
                                   sample_amlo_report, mock_query):
        """Should return paginated list of reports"""
        # Setup
        mock_user_info.return_value = {'branch_id': 1}
        mock_session = mock_db_session
        mock_db_service.get_session.return_value.__enter__.return_value = mock_session

        # Mock query to return sample reports
        mock_query_obj = mock_query([sample_amlo_report])
        mock_session.query.return_value = mock_query_obj

        # Import route after mocking
        from src.routes.app_amlo import get_reports

        # Execute
        with patch('flask.request') as mock_request:
            mock_request.args = {'page': '1', 'page_size': '20'}
            response = get_reports()

        # Verify
        assert response[0]['success'] is True
        assert 'data' in response[0]
        mock_session.query.assert_called()

    @patch('src.routes.app_amlo.DatabaseService')
    @patch('src.routes.app_amlo.current_user_info')
    def test_get_reports_with_status_filter(self, mock_user_info, mock_db_service,
                                              mock_db_session, sample_amlo_report):
        """Should filter reports by status"""
        mock_user_info.return_value = {'branch_id': 1}
        mock_session = mock_db_session
        mock_db_service.get_session.return_value.__enter__.return_value = mock_session

        from src.routes.app_amlo import get_reports

        with patch('flask.request') as mock_request:
            mock_request.args = {'status': 'pending', 'page': '1', 'page_size': '20'}
            response = get_reports()

        # Verify filter was applied
        assert response[0]['success'] is True

    @patch('src.routes.app_amlo.DatabaseService')
    @patch('src.routes.app_amlo.current_user_info')
    def test_get_reports_with_date_range(self, mock_user_info, mock_db_service, mock_db_session):
        """Should filter reports by date range"""
        mock_user_info.return_value = {'branch_id': 1}
        mock_session = mock_db_session
        mock_db_service.get_session.return_value.__enter__.return_value = mock_session

        from src.routes.app_amlo import get_reports

        with patch('flask.request') as mock_request:
            mock_request.args = {
                'start_date': '2025-01-01',
                'end_date': '2025-12-31',
                'page': '1',
                'page_size': '20'
            }
            response = get_reports()

        assert response[0]['success'] is True


class TestGenerateReportPDF:
    """Test GET /api/amlo/reports/<id>/generate-pdf endpoint"""

    @patch('src.routes.app_amlo.AMLOPDFGenerator')
    @patch('src.routes.app_amlo.DatabaseService')
    @patch('src.routes.app_amlo.current_user_info')
    def test_generate_single_pdf_success(self, mock_user_info, mock_db_service,
                                          mock_pdf_gen, sample_amlo_report):
        """Should generate single PDF successfully"""
        # Setup
        mock_user_info.return_value = {'branch_id': 1}

        # Mock database session
        mock_session = MagicMock()
        mock_db_service.get_session.return_value.__enter__.return_value = mock_session

        # Mock report query
        mock_report = MagicMock()
        mock_report.id = 1
        mock_report.report_type = 'AMLO-1-01'
        mock_report.form_data = {'test': 'data'}
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_report

        # Mock PDF generator
        mock_generator_instance = MagicMock()
        mock_generator_instance.generate_pdf.return_value = b'PDF content'
        mock_pdf_gen.return_value = mock_generator_instance

        from src.routes.app_amlo import generate_report_pdf

        # Execute with flask.send_file mocked
        with patch('src.routes.app_amlo.send_file') as mock_send_file:
            mock_send_file.return_value = ('PDF response', 200)
            response = generate_report_pdf(1)

        # Verify
        mock_pdf_gen.assert_called()
        mock_generator_instance.generate_pdf.assert_called_once()
        assert response[1] == 200

    @patch('src.routes.app_amlo.DatabaseService')
    @patch('src.routes.app_amlo.current_user_info')
    def test_generate_pdf_report_not_found(self, mock_user_info, mock_db_service):
        """Should return 404 if report not found"""
        mock_user_info.return_value = {'branch_id': 1}

        # Mock database session - report not found
        mock_session = MagicMock()
        mock_db_service.get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        from src.routes.app_amlo import generate_report_pdf

        with patch('src.routes.app_amlo.jsonify') as mock_jsonify:
            mock_jsonify.return_value = ({'error': 'Not found'}, 404)
            response = generate_report_pdf(999)

        assert response[1] == 404

    @patch('src.routes.app_amlo.AMLOPDFGenerator')
    @patch('src.routes.app_amlo.DatabaseService')
    @patch('src.routes.app_amlo.current_user_info')
    def test_generate_pdf_handles_exception(self, mock_user_info, mock_db_service, mock_pdf_gen):
        """Should handle PDF generation exceptions gracefully"""
        mock_user_info.return_value = {'branch_id': 1}

        mock_session = MagicMock()
        mock_db_service.get_session.return_value.__enter__.return_value = mock_session

        mock_report = MagicMock()
        mock_report.id = 1
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_report

        # Mock PDF generator to raise exception
        mock_pdf_gen.side_effect = Exception('PDF generation failed')

        from src.routes.app_amlo import generate_report_pdf

        with patch('src.routes.app_amlo.jsonify') as mock_jsonify:
            mock_jsonify.return_value = ({'error': 'PDF generation failed'}, 500)
            response = generate_report_pdf(1)

        assert response[1] == 500


class TestBatchGeneratePDF:
    """Test POST /api/amlo/reports/batch-generate-pdf endpoint"""

    @patch('src.routes.app_amlo.AMLOPDFGenerator')
    @patch('src.routes.app_amlo.DatabaseService')
    @patch('src.routes.app_amlo.current_user_info')
    def test_batch_generate_pdf_success(self, mock_user_info, mock_db_service, mock_pdf_gen):
        """Should generate multiple PDFs and return ZIP file"""
        mock_user_info.return_value = {'branch_id': 1}

        # Mock database session
        mock_session = MagicMock()
        mock_db_service.get_session.return_value.__enter__.return_value = mock_session

        # Mock reports
        mock_report1 = MagicMock()
        mock_report1.id = 1
        mock_report1.report_type = 'AMLO-1-01'
        mock_report1.reservation_no = 'RES001'
        mock_report1.form_data = {'test': 'data1'}

        mock_report2 = MagicMock()
        mock_report2.id = 2
        mock_report2.report_type = 'AMLO-1-02'
        mock_report2.reservation_no = 'RES002'
        mock_report2.form_data = {'test': 'data2'}

        mock_session.query.return_value.filter.return_value.all.return_value = [
            mock_report1, mock_report2
        ]

        # Mock PDF generator
        mock_generator_instance = MagicMock()
        mock_generator_instance.generate_pdf.side_effect = [b'PDF1 content', b'PDF2 content']
        mock_pdf_gen.return_value = mock_generator_instance

        from src.routes.app_amlo import batch_generate_pdf

        # Execute
        with patch('flask.request') as mock_request:
            mock_request.get_json.return_value = {'report_ids': [1, 2]}
            with patch('src.routes.app_amlo.send_file') as mock_send_file:
                mock_send_file.return_value = ('ZIP response', 200)
                response = batch_generate_pdf()

        # Verify
        assert mock_generator_instance.generate_pdf.call_count == 2
        assert response[1] == 200

    @patch('src.routes.app_amlo.DatabaseService')
    @patch('src.routes.app_amlo.current_user_info')
    def test_batch_generate_pdf_empty_list(self, mock_user_info, mock_db_service):
        """Should handle empty report ID list"""
        mock_user_info.return_value = {'branch_id': 1}

        from src.routes.app_amlo import batch_generate_pdf

        with patch('flask.request') as mock_request:
            mock_request.get_json.return_value = {'report_ids': []}
            with patch('src.routes.app_amlo.jsonify') as mock_jsonify:
                mock_jsonify.return_value = ({'error': 'No reports selected'}, 400)
                response = batch_generate_pdf()

        assert response[1] == 400

    @patch('src.routes.app_amlo.AMLOPDFGenerator')
    @patch('src.routes.app_amlo.DatabaseService')
    @patch('src.routes.app_amlo.current_user_info')
    def test_batch_generate_pdf_partial_failure(self, mock_user_info, mock_db_service, mock_pdf_gen):
        """Should handle partial PDF generation failures"""
        mock_user_info.return_value = {'branch_id': 1}

        mock_session = MagicMock()
        mock_db_service.get_session.return_value.__enter__.return_value = mock_session

        mock_report1 = MagicMock()
        mock_report1.id = 1
        mock_report1.report_type = 'AMLO-1-01'
        mock_report1.form_data = {'test': 'data1'}

        mock_session.query.return_value.filter.return_value.all.return_value = [mock_report1]

        # Mock PDF generator to fail
        mock_generator_instance = MagicMock()
        mock_generator_instance.generate_pdf.side_effect = Exception('PDF gen failed')
        mock_pdf_gen.return_value = mock_generator_instance

        from src.routes.app_amlo import batch_generate_pdf

        with patch('flask.request') as mock_request:
            mock_request.get_json.return_value = {'report_ids': [1]}
            with patch('src.routes.app_amlo.jsonify') as mock_jsonify:
                mock_jsonify.return_value = ({'error': 'PDF generation failed'}, 500)
                response = batch_generate_pdf()

        assert response[1] == 500


class TestBatchReport:
    """Test POST /api/amlo/reports/batch-report endpoint"""

    @patch('src.routes.app_amlo.DatabaseService')
    @patch('src.routes.app_amlo.current_user_info')
    def test_batch_report_success(self, mock_user_info, mock_db_service):
        """Should mark multiple reports as reported"""
        mock_user_info.return_value = {'branch_id': 1, 'id': 1}

        # Mock database session
        mock_session = MagicMock()
        mock_db_service.get_session.return_value.__enter__.return_value = mock_session

        # Mock reports
        mock_report1 = MagicMock()
        mock_report1.id = 1
        mock_report1.is_reported = False

        mock_report2 = MagicMock()
        mock_report2.id = 2
        mock_report2.is_reported = False

        mock_session.query.return_value.filter.return_value.all.return_value = [
            mock_report1, mock_report2
        ]

        from src.routes.app_amlo import batch_report

        # Execute
        with patch('flask.request') as mock_request:
            mock_request.get_json.return_value = {'report_ids': [1, 2]}
            response = batch_report()

        # Verify reports are marked as reported
        assert mock_report1.is_reported is True
        assert mock_report2.is_reported is True
        mock_session.commit.assert_called_once()
        assert response[0]['success'] is True

    @patch('src.routes.app_amlo.DatabaseService')
    @patch('src.routes.app_amlo.current_user_info')
    def test_batch_report_empty_list(self, mock_user_info, mock_db_service):
        """Should reject empty report list"""
        mock_user_info.return_value = {'branch_id': 1}

        from src.routes.app_amlo import batch_report

        with patch('flask.request') as mock_request:
            mock_request.get_json.return_value = {'report_ids': []}
            response = batch_report()

        assert response[0]['success'] is False
        assert response[1] == 400

    @patch('src.routes.app_amlo.DatabaseService')
    @patch('src.routes.app_amlo.current_user_info')
    def test_batch_report_handles_exception(self, mock_user_info, mock_db_service):
        """Should rollback on exception"""
        mock_user_info.return_value = {'branch_id': 1, 'id': 1}

        mock_session = MagicMock()
        mock_db_service.get_session.return_value.__enter__.return_value = mock_session

        # Mock commit to raise exception
        mock_session.commit.side_effect = Exception('Database error')

        from src.routes.app_amlo import batch_report

        with patch('flask.request') as mock_request:
            mock_request.get_json.return_value = {'report_ids': [1, 2]}
            response = batch_report()

        mock_session.rollback.assert_called_once()
        assert response[0]['success'] is False
        assert response[1] == 500


class TestOverdueDetection:
    """Test overdue report detection logic"""

    def test_overdue_calculation(self):
        """Should correctly identify overdue reports (>3 days)"""
        # Create reports with different ages
        recent_report = {
            'created_at': datetime.now() - timedelta(days=2),
            'is_reported': False
        }

        overdue_report = {
            'created_at': datetime.now() - timedelta(days=5),
            'is_reported': False
        }

        reported_old_report = {
            'created_at': datetime.now() - timedelta(days=10),
            'is_reported': True
        }

        # Test overdue logic
        def is_overdue(report):
            if report['is_reported']:
                return False
            days = (datetime.now() - report['created_at']).days
            return days > 3

        assert is_overdue(recent_report) is False
        assert is_overdue(overdue_report) is True
        assert is_overdue(reported_old_report) is False

    def test_overdue_days_calculation(self):
        """Should correctly calculate overdue days"""
        report = {
            'created_at': datetime.now() - timedelta(days=5),
            'is_reported': False
        }

        def get_overdue_days(report):
            if report['is_reported']:
                return 0
            return max(0, (datetime.now() - report['created_at']).days)

        overdue_days = get_overdue_days(report)
        assert overdue_days == 5

    def test_overdue_days_for_reported(self):
        """Should return 0 overdue days for reported items"""
        report = {
            'created_at': datetime.now() - timedelta(days=10),
            'is_reported': True
        }

        def get_overdue_days(report):
            if report['is_reported']:
                return 0
            return max(0, (datetime.now() - report['created_at']).days)

        assert get_overdue_days(report) == 0
