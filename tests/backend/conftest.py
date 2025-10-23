"""
Pytest configuration and fixtures for backend testing
"""
import pytest
import sys
import os
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta

# Add src directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

@pytest.fixture
def mock_app():
    """Create a mock Flask app for testing"""
    app = MagicMock()
    app.config = {
        'SECRET_KEY': 'test_secret_key',
        'JWT_SECRET_KEY': 'test_jwt_secret',
        'TESTING': True
    }
    return app

@pytest.fixture
def mock_db_session():
    """Create a mock database session"""
    session = MagicMock()
    session.add = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    session.query = Mock()
    session.close = Mock()
    return session

@pytest.fixture
def mock_current_user():
    """Create a mock current user object"""
    return {
        'id': 1,
        'username': 'test_user',
        'branch_id': 1,
        'role': 'System',
        'permissions': ['amlo.view', 'amlo.report', 'bot.view', 'bot.export']
    }

@pytest.fixture
def sample_amlo_report():
    """Create a sample AMLO report object"""
    return {
        'id': 1,
        'reservation_no': 'RES001',
        'report_type': 'AMLO-1-01',
        'customer_name': 'John Doe',
        'customer_id': '1234567890123',
        'amount': 500000.00,
        'currency_code': 'THB',
        'direction': 'buy',
        'created_at': datetime.now() - timedelta(days=2),
        'is_reported': False,
        'form_data': {
            'section_a': {
                'field1': 'value1',
                'field2': 'value2'
            }
        },
        'branch_id': 1,
        'created_by': 1
    }

@pytest.fixture
def sample_overdue_report():
    """Create a sample overdue AMLO report (>3 days old)"""
    return {
        'id': 2,
        'reservation_no': 'RES002',
        'report_type': 'AMLO-1-02',
        'customer_name': 'Jane Smith',
        'customer_id': '9876543210987',
        'amount': 750000.00,
        'currency_code': 'THB',
        'direction': 'sell',
        'created_at': datetime.now() - timedelta(days=5),  # 5 days old (overdue)
        'is_reported': False,
        'form_data': {
            'section_a': {
                'field1': 'value1'
            }
        },
        'branch_id': 1,
        'created_by': 1
    }

@pytest.fixture
def sample_bot_transaction():
    """Create a sample BOT transaction"""
    return {
        'id': 1,
        'transaction_no': 'TXN001',
        'customer_id': '1234567890123',
        'currency_code': 'USD',
        'foreign_amount': 1000.00,
        'local_amount': 35000.00,
        'exchange_rate': 35.00,
        'direction': 'buy',
        'transaction_date': datetime.now().date(),
        'transaction_time': datetime.now().time(),
        'branch_id': 1,
        'operator_id': 1
    }

@pytest.fixture
def sample_bot_buy_data():
    """Create sample BOT Buy FX report data"""
    return {
        'items': [
            {
                'transaction_no': 'TXN001',
                'transaction_time': '10:30:00',
                'customer_id': '1234567890123',
                'currency': 'USD',
                'foreign_amount': 1000.00,
                'local_amount': 35000.00,
                'rate': 35.00
            },
            {
                'transaction_no': 'TXN002',
                'transaction_time': '14:45:00',
                'customer_id': '9876543210987',
                'currency': 'EUR',
                'foreign_amount': 500.00,
                'local_amount': 19000.00,
                'rate': 38.00
            }
        ],
        'total': 2,
        'total_amount_thb': 54000.00
    }

@pytest.fixture
def sample_bot_sell_data():
    """Create sample BOT Sell FX report data"""
    return {
        'items': [
            {
                'transaction_no': 'TXN003',
                'transaction_time': '11:15:00',
                'customer_id': '5555555555555',
                'currency': 'JPY',
                'foreign_amount': 100000.00,
                'local_amount': 25000.00,
                'rate': 0.25
            }
        ],
        'total': 1,
        'total_amount_thb': 25000.00
    }

@pytest.fixture
def mock_pdf_generator():
    """Create a mock PDF generator"""
    generator = MagicMock()
    generator.generate_pdf = Mock(return_value=b'Mock PDF Content')
    return generator

@pytest.fixture
def mock_excel_generator():
    """Create a mock Excel generator"""
    generator = MagicMock()
    generator.generate_excel = Mock(return_value=b'Mock Excel Content')
    return generator

@pytest.fixture
def mock_request():
    """Create a mock Flask request object"""
    request = MagicMock()
    request.args = {}
    request.json = {}
    request.method = 'GET'
    request.headers = {
        'Authorization': 'Bearer test_token'
    }
    return request

@pytest.fixture
def mock_token():
    """Create a mock JWT token"""
    return {
        'sub': 1,
        'username': 'test_user',
        'branch_id': 1,
        'role': 'System',
        'exp': datetime.now() + timedelta(hours=1)
    }

class MockQuery:
    """Mock SQLAlchemy query object"""
    def __init__(self, data=None):
        self.data = data or []
        self._filter_called = False

    def filter(self, *args, **kwargs):
        self._filter_called = True
        return self

    def filter_by(self, **kwargs):
        return self

    def order_by(self, *args):
        return self

    def limit(self, n):
        self.data = self.data[:n]
        return self

    def offset(self, n):
        self.data = self.data[n:]
        return self

    def first(self):
        return self.data[0] if self.data else None

    def all(self):
        return self.data

    def count(self):
        return len(self.data)

@pytest.fixture
def mock_query():
    """Create a mock query object"""
    return MockQuery

@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all mocks before each test"""
    yield
    # Cleanup can be added here if needed
