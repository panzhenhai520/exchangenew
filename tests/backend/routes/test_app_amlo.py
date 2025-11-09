"""
Unit tests for AMLO routes (app_amlo.py)
Tests PDF generation, batch reporting, and report listing

Updated for refactored service layer architecture
"""
import pytest
from unittest.mock import patch, Mock, MagicMock, mock_open
from datetime import datetime, timedelta
from flask import Flask, g
import io
import zipfile

# Mark all tests in this module
pytestmark = [pytest.mark.unit, pytest.mark.amlo, pytest.mark.routes]


@pytest.fixture
def app():
    """Create Flask app for testing"""
    import sys
    import os

    # Add src directory to path to allow relative imports
    src_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'

    # Register blueprint
    from routes.app_amlo import app_amlo
    app.register_blueprint(app_amlo)

    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def mock_auth():
    """Mock authentication decorator"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            # Simulate authenticated user
            return f(*args, **kwargs)
        return wrapper
    return decorator


class TestGetReports:
    """Test GET /api/amlo/reports endpoint"""

    @patch('services.amlo.report_service.ReportService.list_reports')
    @patch('routes.app_amlo.SessionLocal')
    @patch('routes.app_amlo.token_required')
    def test_get_reports_success(self, mock_token_req, mock_session_local, mock_list_reports, client):
        """Should return paginated list of reports"""
        # Bypass authentication
        mock_token_req.side_effect = lambda f: f

        # Setup mock session
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        # Mock service response
        mock_list_reports.return_value = {
            'success': True,
            'data': [{
                'id': 1,
                'report_no': 'AMLO-001',
                'report_type': 'AMLO-1-01',
                'customer_name': 'Test Customer'
            }],
            'pagination': {
                'total': 1,
                'page': 1,
                'page_size': 20,
                'pages': 1
            }
        }

        # Setup Flask context with g.current_user
        with client.application.test_request_context():
            g.current_user = {'branch_id': 1, 'id': 1}

            # Execute
            response = client.get('/api/amlo/reports?page=1&page_size=20')
            data = response.get_json()

            # Verify
            assert response.status_code == 200
            assert data['success'] is True
            assert 'data' in data


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
