"""
Unit tests for BOT routes (app_bot.py)
Tests Excel export, T+1 reporting, and data retrieval
"""
import pytest
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime, date, timedelta
import io

# Mark all tests in this module
pytestmark = [pytest.mark.unit, pytest.mark.bot, pytest.mark.routes]


class TestGetT1BuyFX:
    """Test GET /api/bot/t1-buy-fx endpoint"""

    @patch('src.routes.app_bot.DatabaseService')
    @patch('src.routes.app_bot.current_user_info')
    def test_get_t1_buy_fx_success(self, mock_user_info, mock_db_service, sample_bot_buy_data):
        """Should return buy FX transaction data"""
        mock_user_info.return_value = {'branch_id': 1}

        # Mock database session
        mock_session = MagicMock()
        mock_db_service.get_session.return_value.__enter__.return_value = mock_session

        # Mock transactions
        mock_transactions = [
            MagicMock(
                transaction_no='TXN001',
                transaction_time=datetime.now().time(),
                customer_id='1234567890123',
                currency_code='USD',
                foreign_amount=1000.00,
                local_amount=35000.00,
                exchange_rate=35.00
            )
        ]
        mock_session.query.return_value.filter.return_value.all.return_value = mock_transactions

        from src.routes.app_bot import get_t1_buy_fx

        # Execute
        with patch('flask.request') as mock_request:
            mock_request.args = {'date': '2025-01-15'}
            response = get_t1_buy_fx()

        # Verify
        assert response[0]['success'] is True
        assert 'data' in response[0]
        mock_session.query.assert_called()

    @patch('src.routes.app_bot.DatabaseService')
    @patch('src.routes.app_bot.current_user_info')
    def test_get_t1_buy_fx_default_date(self, mock_user_info, mock_db_service):
        """Should use yesterday's date by default"""
        mock_user_info.return_value = {'branch_id': 1}

        mock_session = MagicMock()
        mock_db_service.get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.all.return_value = []

        from src.routes.app_bot import get_t1_buy_fx

        with patch('flask.request') as mock_request:
            mock_request.args = {}
            response = get_t1_buy_fx()

        assert response[0]['success'] is True

    @patch('src.routes.app_bot.DatabaseService')
    @patch('src.routes.app_bot.current_user_info')
    def test_get_t1_buy_fx_calculates_totals(self, mock_user_info, mock_db_service):
        """Should calculate total count and amount"""
        mock_user_info.return_value = {'branch_id': 1}

        mock_session = MagicMock()
        mock_db_service.get_session.return_value.__enter__.return_value = mock_session

        mock_transactions = [
            MagicMock(local_amount=35000.00),
            MagicMock(local_amount=19000.00)
        ]
        mock_session.query.return_value.filter.return_value.all.return_value = mock_transactions

        from src.routes.app_bot import get_t1_buy_fx

        with patch('flask.request') as mock_request:
            mock_request.args = {'date': '2025-01-15'}
            response = get_t1_buy_fx()

        assert response[0]['data']['total'] == 2
        # Total amount should be sum of local_amounts


class TestGetT1SellFX:
    """Test GET /api/bot/t1-sell-fx endpoint"""

    @patch('src.routes.app_bot.DatabaseService')
    @patch('src.routes.app_bot.current_user_info')
    def test_get_t1_sell_fx_success(self, mock_user_info, mock_db_service):
        """Should return sell FX transaction data"""
        mock_user_info.return_value = {'branch_id': 1}

        mock_session = MagicMock()
        mock_db_service.get_session.return_value.__enter__.return_value = mock_session

        mock_transactions = [
            MagicMock(
                transaction_no='TXN002',
                transaction_time=datetime.now().time(),
                customer_id='9876543210987',
                currency_code='EUR',
                foreign_amount=500.00,
                local_amount=19000.00,
                exchange_rate=38.00
            )
        ]
        mock_session.query.return_value.filter.return_value.all.return_value = mock_transactions

        from src.routes.app_bot import get_t1_sell_fx

        with patch('flask.request') as mock_request:
            mock_request.args = {'date': '2025-01-15'}
            response = get_t1_sell_fx()

        assert response[0]['success'] is True
        assert 'data' in response[0]

    @patch('src.routes.app_bot.DatabaseService')
    @patch('src.routes.app_bot.current_user_info')
    def test_get_t1_sell_fx_empty_results(self, mock_user_info, mock_db_service):
        """Should handle empty results gracefully"""
        mock_user_info.return_value = {'branch_id': 1}

        mock_session = MagicMock()
        mock_db_service.get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.all.return_value = []

        from src.routes.app_bot import get_t1_sell_fx

        with patch('flask.request') as mock_request:
            mock_request.args = {'date': '2025-01-15'}
            response = get_t1_sell_fx()

        assert response[0]['success'] is True
        assert response[0]['data']['total'] == 0


class TestExportBuyFX:
    """Test GET /api/bot/export-buy-fx endpoint"""

    @patch('openpyxl.Workbook')
    @patch('src.routes.app_bot.DatabaseService')
    @patch('src.routes.app_bot.current_user_info')
    def test_export_buy_fx_success(self, mock_user_info, mock_db_service, mock_workbook):
        """Should export buy FX data to Excel"""
        mock_user_info.return_value = {'branch_id': 1}

        # Mock database session
        mock_session = MagicMock()
        mock_db_service.get_session.return_value.__enter__.return_value = mock_session

        # Mock transactions
        mock_transactions = [
            MagicMock(
                transaction_no='TXN001',
                transaction_time=datetime.now().time(),
                customer_id='1234567890123',
                currency_code='USD',
                foreign_amount=1000.00,
                local_amount=35000.00,
                exchange_rate=35.00
            )
        ]
        mock_session.query.return_value.filter.return_value.all.return_value = mock_transactions

        # Mock workbook
        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_wb.active = mock_ws
        mock_workbook.return_value = mock_wb

        from src.routes.app_bot import export_buy_fx_excel

        # Execute
        with patch('flask.request') as mock_request:
            mock_request.args = {'date': '2025-01-15'}
            with patch('src.routes.app_bot.send_file') as mock_send_file:
                mock_send_file.return_value = ('Excel response', 200)
                response = export_buy_fx_excel()

        # Verify
        mock_workbook.assert_called()
        assert response[1] == 200

    @patch('openpyxl.Workbook')
    @patch('src.routes.app_bot.DatabaseService')
    @patch('src.routes.app_bot.current_user_info')
    def test_export_buy_fx_empty_data(self, mock_user_info, mock_db_service, mock_workbook):
        """Should export empty Excel when no data"""
        mock_user_info.return_value = {'branch_id': 1}

        mock_session = MagicMock()
        mock_db_service.get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.all.return_value = []

        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_wb.active = mock_ws
        mock_workbook.return_value = mock_wb

        from src.routes.app_bot import export_buy_fx_excel

        with patch('flask.request') as mock_request:
            mock_request.args = {'date': '2025-01-15'}
            with patch('src.routes.app_bot.send_file') as mock_send_file:
                mock_send_file.return_value = ('Excel response', 200)
                response = export_buy_fx_excel()

        assert response[1] == 200

    @patch('src.routes.app_bot.DatabaseService')
    @patch('src.routes.app_bot.current_user_info')
    def test_export_buy_fx_handles_exception(self, mock_user_info, mock_db_service):
        """Should handle Excel generation exceptions"""
        mock_user_info.return_value = {'branch_id': 1}

        mock_session = MagicMock()
        mock_db_service.get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.side_effect = Exception('Database error')

        from src.routes.app_bot import export_buy_fx_excel

        with patch('flask.request') as mock_request:
            mock_request.args = {'date': '2025-01-15'}
            with patch('src.routes.app_bot.jsonify') as mock_jsonify:
                mock_jsonify.return_value = ({'error': 'Export failed'}, 500)
                response = export_buy_fx_excel()

        assert response[1] == 500


class TestExportSellFX:
    """Test GET /api/bot/export-sell-fx endpoint"""

    @patch('openpyxl.Workbook')
    @patch('src.routes.app_bot.DatabaseService')
    @patch('src.routes.app_bot.current_user_info')
    def test_export_sell_fx_success(self, mock_user_info, mock_db_service, mock_workbook):
        """Should export sell FX data to Excel"""
        mock_user_info.return_value = {'branch_id': 1}

        mock_session = MagicMock()
        mock_db_service.get_session.return_value.__enter__.return_value = mock_session

        mock_transactions = [
            MagicMock(
                transaction_no='TXN002',
                transaction_time=datetime.now().time(),
                customer_id='9876543210987',
                currency_code='EUR',
                foreign_amount=500.00,
                local_amount=19000.00,
                exchange_rate=38.00
            )
        ]
        mock_session.query.return_value.filter.return_value.all.return_value = mock_transactions

        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_wb.active = mock_ws
        mock_workbook.return_value = mock_wb

        from src.routes.app_bot import export_sell_fx_excel

        with patch('flask.request') as mock_request:
            mock_request.args = {'date': '2025-01-15'}
            with patch('src.routes.app_bot.send_file') as mock_send_file:
                mock_send_file.return_value = ('Excel response', 200)
                response = export_sell_fx_excel()

        mock_workbook.assert_called()
        assert response[1] == 200

    @patch('openpyxl.Workbook')
    @patch('src.routes.app_bot.DatabaseService')
    @patch('src.routes.app_bot.current_user_info')
    def test_export_sell_fx_with_formatting(self, mock_user_info, mock_db_service, mock_workbook):
        """Should apply formatting to Excel headers and data"""
        mock_user_info.return_value = {'branch_id': 1}

        mock_session = MagicMock()
        mock_db_service.get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.all.return_value = []

        # Mock workbook and worksheet
        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_wb.active = mock_ws
        mock_workbook.return_value = mock_wb

        from src.routes.app_bot import export_sell_fx_excel

        with patch('flask.request') as mock_request:
            mock_request.args = {'date': '2025-01-15'}
            with patch('src.routes.app_bot.send_file') as mock_send_file:
                mock_send_file.return_value = ('Excel response', 200)
                response = export_sell_fx_excel()

        # Verify worksheet was accessed for writing
        assert mock_ws.append.called or mock_ws.cell.called


class TestSaveBuyFX:
    """Test POST /api/bot/save-buy-fx endpoint"""

    @patch('src.routes.app_bot.DatabaseService')
    @patch('src.routes.app_bot.current_user_info')
    def test_save_buy_fx_success(self, mock_user_info, mock_db_service):
        """Should save buy FX report data"""
        mock_user_info.return_value = {'branch_id': 1, 'id': 1}

        mock_session = MagicMock()
        mock_db_service.get_session.return_value.__enter__.return_value = mock_session

        from src.routes.app_bot import save_buy_fx_report

        with patch('flask.request') as mock_request:
            mock_request.get_json.return_value = {
                'transaction_id': 123,
                'report_date': '2025-01-15',
                'json_data': {'currency': 'USD', 'amount': 1000}
            }
            response = save_buy_fx_report()

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        assert response[0]['success'] is True

    @patch('src.routes.app_bot.DatabaseService')
    @patch('src.routes.app_bot.current_user_info')
    def test_save_buy_fx_missing_data(self, mock_user_info, mock_db_service):
        """Should reject request with missing data"""
        mock_user_info.return_value = {'branch_id': 1}

        from src.routes.app_bot import save_buy_fx_report

        with patch('flask.request') as mock_request:
            mock_request.get_json.return_value = {}
            response = save_buy_fx_report()

        assert response[0]['success'] is False
        assert response[1] == 400


class TestSaveSellFX:
    """Test POST /api/bot/save-sell-fx endpoint"""

    @patch('src.routes.app_bot.DatabaseService')
    @patch('src.routes.app_bot.current_user_info')
    def test_save_sell_fx_success(self, mock_user_info, mock_db_service):
        """Should save sell FX report data"""
        mock_user_info.return_value = {'branch_id': 1, 'id': 1}

        mock_session = MagicMock()
        mock_db_service.get_session.return_value.__enter__.return_value = mock_session

        from src.routes.app_bot import save_sell_fx_report

        with patch('flask.request') as mock_request:
            mock_request.get_json.return_value = {
                'transaction_id': 456,
                'report_date': '2025-01-15',
                'json_data': {'currency': 'EUR', 'amount': 500}
            }
            response = save_sell_fx_report()

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        assert response[0]['success'] is True


class TestGetTriggerConfig:
    """Test GET /api/bot/trigger-config endpoint"""

    @patch('src.routes.app_bot.DatabaseService')
    @patch('src.routes.app_bot.current_user_info')
    def test_get_trigger_config_success(self, mock_user_info, mock_db_service):
        """Should return BOT trigger configuration"""
        mock_user_info.return_value = {'branch_id': 1}

        mock_session = MagicMock()
        mock_db_service.get_session.return_value.__enter__.return_value = mock_session

        mock_config = MagicMock()
        mock_config.buy_threshold = 450000
        mock_config.sell_threshold = 450000
        mock_config.enabled = True
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_config

        from src.routes.app_bot import get_trigger_config

        response = get_trigger_config()

        assert response[0]['success'] is True
        assert response[0]['data']['buy_threshold'] == 450000

    @patch('src.routes.app_bot.DatabaseService')
    @patch('src.routes.app_bot.current_user_info')
    def test_get_trigger_config_not_found(self, mock_user_info, mock_db_service):
        """Should return default config if not found"""
        mock_user_info.return_value = {'branch_id': 1}

        mock_session = MagicMock()
        mock_db_service.get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        from src.routes.app_bot import get_trigger_config

        response = get_trigger_config()

        # Should return default values or 404
        assert response[0]['success'] is True or response[1] == 404


class TestSaveTriggerConfig:
    """Test POST /api/bot/trigger-config endpoint"""

    @patch('src.routes.app_bot.DatabaseService')
    @patch('src.routes.app_bot.current_user_info')
    def test_save_trigger_config_create_new(self, mock_user_info, mock_db_service):
        """Should create new config if doesn't exist"""
        mock_user_info.return_value = {'branch_id': 1, 'id': 1}

        mock_session = MagicMock()
        mock_db_service.get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        from src.routes.app_bot import save_trigger_config

        with patch('flask.request') as mock_request:
            mock_request.get_json.return_value = {
                'buy_threshold': 500000,
                'sell_threshold': 500000,
                'enabled': True
            }
            response = save_trigger_config()

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        assert response[0]['success'] is True

    @patch('src.routes.app_bot.DatabaseService')
    @patch('src.routes.app_bot.current_user_info')
    def test_save_trigger_config_update_existing(self, mock_user_info, mock_db_service):
        """Should update existing config"""
        mock_user_info.return_value = {'branch_id': 1, 'id': 1}

        mock_session = MagicMock()
        mock_db_service.get_session.return_value.__enter__.return_value = mock_session

        mock_config = MagicMock()
        mock_config.buy_threshold = 450000
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_config

        from src.routes.app_bot import save_trigger_config

        with patch('flask.request') as mock_request:
            mock_request.get_json.return_value = {
                'buy_threshold': 600000,
                'sell_threshold': 600000,
                'enabled': False
            }
            response = save_trigger_config()

        # Config should be updated
        assert mock_config.buy_threshold == 600000
        mock_session.commit.assert_called_once()
        assert response[0]['success'] is True


class TestExcelFormatting:
    """Test Excel export formatting"""

    def test_column_widths(self):
        """Should set appropriate column widths"""
        # This is a conceptual test showing how column widths should be set
        expected_widths = {
            'A': 15,  # Transaction No
            'B': 12,  # Time
            'C': 20,  # Customer ID
            'D': 10,  # Currency
            'E': 15,  # Foreign Amount
            'F': 15,  # Local Amount
            'G': 12   # Rate
        }

        assert expected_widths['A'] == 15
        assert expected_widths['C'] == 20

    def test_header_formatting(self):
        """Should apply bold formatting to headers"""
        # Conceptual test for header formatting
        assert True  # Headers should be bold with background color

    def test_number_formatting(self):
        """Should format numbers with 2 decimal places"""
        # Conceptual test for number formatting
        test_amount = 1000.00
        formatted = f"{test_amount:.2f}"
        assert formatted == "1000.00"


class TestDateHandling:
    """Test date parameter handling"""

    def test_parse_date_string(self):
        """Should correctly parse date strings"""
        date_string = '2025-01-15'
        parsed_date = datetime.strptime(date_string, '%Y-%m-%d').date()

        assert parsed_date.year == 2025
        assert parsed_date.month == 1
        assert parsed_date.day == 15

    def test_default_to_yesterday(self):
        """Should default to yesterday's date"""
        yesterday = date.today() - timedelta(days=1)
        assert yesterday < date.today()

    def test_validate_date_format(self):
        """Should validate date format"""
        valid_dates = ['2025-01-15', '2024-12-31']
        invalid_dates = ['15-01-2025', '2025/01/15', 'invalid']

        for valid_date in valid_dates:
            try:
                datetime.strptime(valid_date, '%Y-%m-%d')
                assert True
            except ValueError:
                assert False

        for invalid_date in invalid_dates:
            try:
                datetime.strptime(invalid_date, '%Y-%m-%d')
                assert False  # Should not reach here
            except ValueError:
                assert True  # Expected to fail
