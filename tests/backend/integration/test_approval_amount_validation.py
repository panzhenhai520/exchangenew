# -*- coding: utf-8 -*-
"""
AMLO审核金额验证集成测试
测试交易执行时的审核金额验证逻辑

运行方式：
    pytest tests/backend/integration/test_approval_amount_validation.py -v
"""

import pytest
from decimal import Decimal
from datetime import datetime, date
from unittest.mock import Mock, MagicMock, patch, ANY
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..', 'src'))

# 创建Flask应用上下文
from flask import Flask, request
from flask.testing import FlaskClient
from sqlalchemy import text

@pytest.fixture
def app():
    """创建测试用Flask应用"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()

@pytest.fixture
def app_context(app):
    """创建应用上下文"""
    with app.app_context():
        yield app


class TestApprovalAmountValidation:
    """测试AMLO审核金额验证逻辑"""

    def test_transaction_blocked_when_amount_exceeds_approval(self, app_context):
        """测试：交易金额超过审核金额时应被阻止"""
        from routes.exchange.perform import perform_exchange

        # 模拟场景: 审核金额600万，实际交易800万（超额）
        with patch('routes.exchange.perform.DatabaseService.get_session') as mock_get_session, \
             patch('routes.exchange.perform.request') as mock_request:

            # 模拟数据库会话
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session

            # 模拟查询审核记录（审核金额600万）
            mock_reservation = (
                1,  # id
                'RS202510210001',  # reservation_no
                'AMLO-1-01',  # report_type
                'approved',  # status
                Decimal('6000000.00'),  # local_amount (审核金额)
                '审核通过'  # audit_notes
            )

            mock_session.execute.return_value.fetchone.return_value = mock_reservation

            # 模拟请求数据（实际交易800万）
            mock_request.get_json.return_value = {
                'currency_id': 2,
                'type': 'buy',
                'amount': 228571.43,  # USD金额
                'local_amount': 8000000.00,  # 本币金额（超过审核的600万）
                'exchange_rate': 35.0,
                'customer_name': '张三',
                'customer_id': '1234567890123',
                'purpose': '旅游'
            }

            # 模拟当前用户
            current_user = {
                'id': 1,
                'branch_id': 1,
                'username': 'operator'
            }

            # 模拟币种和网点查询
            mock_currency = Mock()
            mock_currency.currency_code = 'USD'

            mock_branch = Mock()
            mock_branch.base_currency_id = 1

            mock_session.query.return_value.filter_by.return_value.first.side_effect = [
                mock_currency,  # 第一次查询：币种
                mock_branch      # 第二次查询：网点
            ]

            # 执行交易
            response = perform_exchange(current_user)
            response_data = response[0].get_json()

            # 验证交易被阻止
            assert response_data['success'] is False
            assert 'error_type' in response_data
            assert response_data['error_type'] == 'amount_exceeded'
            assert response_data['approved_amount'] == 6000000.00
            assert response_data['actual_amount'] == 8000000.00
            assert '超过审核金额' in response_data['message']

            # 验证HTTP状态码为403（禁止）
            assert response[1] == 403

            # 验证会话被回滚
            mock_session.rollback.assert_called()

    def test_transaction_allowed_when_amount_equals_approval(self, app_context):
        """测试：交易金额等于审核金额时应允许"""
        from routes.exchange.perform import perform_exchange

        # 模拟场景: 审核金额600万，实际交易600万（相等）
        with patch('routes.exchange.perform.DatabaseService.get_session') as mock_get_session, \
             patch('routes.exchange.perform.request') as mock_request, \
             patch('routes.exchange.perform.BalanceService') as mock_balance_service, \
             patch('routes.exchange.perform.multilingual_logger'), \
             patch('routes.exchange.perform.log_exchange_transaction'), \
             patch('routes.exchange.perform.get_current_language', return_value='zh-CN'), \
             patch('services.amlo_trigger_service.AMLOTriggerService.check_and_create_amlo_records', return_value={}), \
             patch('services.bot_trigger_service.BOTTriggerService.check_and_create_bot_records', return_value={}):

            # 模拟数据库会话
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session

            # 模拟查询审核记录（审核金额600万）
            mock_reservation = (
                1,  # id
                'RS202510210001',  # reservation_no
                'AMLO-1-01',  # report_type
                'approved',  # status
                Decimal('6000000.00'),  # local_amount (审核金额)
                '审核通过'  # audit_notes
            )

            # 设置execute的返回值：第一次返回审核记录，后续调用返回None
            execute_return = MagicMock()
            execute_return.fetchone.side_effect = [mock_reservation, None]  # 第二次返回None (状态更新查询)
            execute_return.rowcount = 1
            mock_session.execute.return_value = execute_return

            # 模拟请求数据（实际交易600万，等于审核金额）
            mock_request.get_json.return_value = {
                'currency_id': 2,
                'type': 'buy',
                'amount': 171428.57,  # USD金额
                'local_amount': 6000000.00,  # 本币金额（等于审核金额）
                'exchange_rate': 35.0,
                'customer_name': '张三',
                'customer_id': '1234567890123',
                'purpose': '旅游'
            }
            mock_request.remote_addr = '127.0.0.1'

            # 模拟当前用户
            current_user = {
                'id': 1,
                'branch_id': 1,
                'username': 'operator'
            }

            # 模拟币种和网点查询
            mock_currency = Mock()
            mock_currency.currency_code = 'USD'

            mock_branch = Mock()
            mock_branch.base_currency_id = 1

            mock_session.query.return_value.filter_by.return_value.first.side_effect = [
                mock_currency,  # 第一次查询：币种
                mock_branch      # 第二次查询：网点
            ]

            # 模拟余额服务返回值
            mock_balance_service.update_currency_balance.return_value = (
                Decimal('1000000.00'),  # balance_before
                Decimal('1171428.57')   # balance_after
            )

            # 模拟交易创建
            mock_transaction = Mock()
            mock_transaction.id = 1001
            mock_transaction.transaction_no = 'T20251021001'
            mock_transaction.type = 'buy'
            mock_transaction.rate = Decimal('35.0')
            mock_transaction.customer_name = '张三'
            mock_transaction.customer_id = '1234567890123'
            mock_transaction.purpose = '旅游'
            mock_transaction.remarks = ''
            mock_transaction.transaction_date = date.today()
            mock_transaction.transaction_time = '10:30:00'

            mock_balance_service.create_exchange_transaction.return_value = mock_transaction

            # 执行交易
            response = perform_exchange(current_user)
            response_data = response.get_json()

            # 验证交易成功
            assert response_data['success'] is True
            assert response_data['message'] == '交易成功'
            assert 'transaction' in response_data
            assert response_data['transaction']['id'] == 1001

            # 验证会话被提交（不是回滚）
            assert mock_session.commit.called
            assert not mock_session.rollback.called

    def test_transaction_allowed_when_amount_below_approval(self, app_context):
        """测试：交易金额低于审核金额时应允许"""
        from routes.exchange.perform import perform_exchange

        # 模拟场景: 审核金额600万，实际交易400万（低于）
        with patch('routes.exchange.perform.DatabaseService.get_session') as mock_get_session, \
             patch('routes.exchange.perform.request') as mock_request, \
             patch('routes.exchange.perform.BalanceService') as mock_balance_service, \
             patch('routes.exchange.perform.multilingual_logger'), \
             patch('routes.exchange.perform.log_exchange_transaction'), \
             patch('routes.exchange.perform.get_current_language', return_value='zh-CN'), \
             patch('services.amlo_trigger_service.AMLOTriggerService.check_and_create_amlo_records', return_value={}), \
             patch('services.bot_trigger_service.BOTTriggerService.check_and_create_bot_records', return_value={}):

            # 模拟数据库会话
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session

            # 模拟查询审核记录（审核金额600万）
            mock_reservation = (
                1,  # id
                'RS202510210001',  # reservation_no
                'AMLO-1-01',  # report_type
                'approved',  # status
                Decimal('6000000.00'),  # local_amount (审核金额)
                '审核通过'  # audit_notes
            )

            execute_return = MagicMock()
            execute_return.fetchone.side_effect = [mock_reservation, None]
            execute_return.rowcount = 1
            mock_session.execute.return_value = execute_return

            # 模拟请求数据（实际交易400万，低于审核金额）
            mock_request.get_json.return_value = {
                'currency_id': 2,
                'type': 'buy',
                'amount': 114285.71,  # USD金额
                'local_amount': 4000000.00,  # 本币金额（低于审核的600万）
                'exchange_rate': 35.0,
                'customer_name': '张三',
                'customer_id': '1234567890123',
                'purpose': '旅游'
            }
            mock_request.remote_addr = '127.0.0.1'

            # 模拟当前用户
            current_user = {
                'id': 1,
                'branch_id': 1,
                'username': 'operator'
            }

            # 模拟币种和网点查询
            mock_currency = Mock()
            mock_currency.currency_code = 'USD'

            mock_branch = Mock()
            mock_branch.base_currency_id = 1

            mock_session.query.return_value.filter_by.return_value.first.side_effect = [
                mock_currency,
                mock_branch
            ]

            # 模拟余额服务返回值
            mock_balance_service.update_currency_balance.return_value = (
                Decimal('1000000.00'),
                Decimal('1114285.71')
            )

            # 模拟交易创建
            mock_transaction = Mock()
            mock_transaction.id = 1002
            mock_transaction.transaction_no = 'T20251021002'
            mock_transaction.type = 'buy'
            mock_transaction.rate = Decimal('35.0')
            mock_transaction.customer_name = '张三'
            mock_transaction.customer_id = '1234567890123'
            mock_transaction.purpose = '旅游'
            mock_transaction.remarks = ''
            mock_transaction.transaction_date = date.today()
            mock_transaction.transaction_time = '10:30:00'

            mock_balance_service.create_exchange_transaction.return_value = mock_transaction

            # 执行交易
            response = perform_exchange(current_user)
            response_data = response.get_json()

            # 验证交易成功
            assert response_data['success'] is True
            assert response_data['message'] == '交易成功'

    def test_transaction_allowed_when_no_reservation_exists(self, app_context):
        """测试：无预约记录时应正常允许交易"""
        from routes.exchange.perform import perform_exchange

        # 模拟场景: 无审核记录，小额交易（不触发AMLO）
        with patch('routes.exchange.perform.DatabaseService.get_session') as mock_get_session, \
             patch('routes.exchange.perform.request') as mock_request, \
             patch('routes.exchange.perform.BalanceService') as mock_balance_service, \
             patch('routes.exchange.perform.multilingual_logger'), \
             patch('routes.exchange.perform.log_exchange_transaction'), \
             patch('routes.exchange.perform.get_current_language', return_value='zh-CN'), \
             patch('services.amlo_trigger_service.AMLOTriggerService.check_and_create_amlo_records', return_value={}), \
             patch('services.bot_trigger_service.BOTTriggerService.check_and_create_bot_records', return_value={}):

            # 模拟数据库会话
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session

            # 模拟查询：无审核记录
            execute_return = MagicMock()
            execute_return.fetchone.return_value = None
            execute_return.rowcount = 0
            mock_session.execute.return_value = execute_return

            # 模拟请求数据（小额交易）
            mock_request.get_json.return_value = {
                'currency_id': 2,
                'type': 'buy',
                'amount': 1000.00,  # USD金额
                'local_amount': 35000.00,  # 本币金额
                'exchange_rate': 35.0,
                'customer_name': '李四',
                'customer_id': '9876543210123',
                'purpose': '旅游'
            }
            mock_request.remote_addr = '127.0.0.1'

            # 模拟当前用户
            current_user = {
                'id': 1,
                'branch_id': 1,
                'username': 'operator'
            }

            # 模拟币种和网点查询
            mock_currency = Mock()
            mock_currency.currency_code = 'USD'

            mock_branch = Mock()
            mock_branch.base_currency_id = 1

            mock_session.query.return_value.filter_by.return_value.first.side_effect = [
                mock_currency,
                mock_branch
            ]

            # 模拟余额服务返回值
            mock_balance_service.update_currency_balance.return_value = (
                Decimal('1000000.00'),
                Decimal('1001000.00')
            )

            # 模拟交易创建
            mock_transaction = Mock()
            mock_transaction.id = 1003
            mock_transaction.transaction_no = 'T20251021003'
            mock_transaction.type = 'buy'
            mock_transaction.rate = Decimal('35.0')
            mock_transaction.customer_name = '李四'
            mock_transaction.customer_id = '9876543210123'
            mock_transaction.purpose = '旅游'
            mock_transaction.remarks = ''
            mock_transaction.transaction_date = date.today()
            mock_transaction.transaction_time = '10:30:00'

            mock_balance_service.create_exchange_transaction.return_value = mock_transaction

            # 执行交易
            response = perform_exchange(current_user)
            response_data = response.get_json()

            # 验证交易成功
            assert response_data['success'] is True
            assert response_data['message'] == '交易成功'

    def test_reservation_status_updated_to_completed_after_transaction(self, app_context):
        """测试：交易成功后预约状态应更新为completed"""
        from routes.exchange.perform import perform_exchange

        # 模拟场景: 有审核记录，交易成功后应更新状态
        with patch('routes.exchange.perform.DatabaseService.get_session') as mock_get_session, \
             patch('routes.exchange.perform.request') as mock_request, \
             patch('routes.exchange.perform.BalanceService') as mock_balance_service, \
             patch('routes.exchange.perform.multilingual_logger'), \
             patch('routes.exchange.perform.log_exchange_transaction'), \
             patch('routes.exchange.perform.get_current_language', return_value='zh-CN'), \
             patch('services.amlo_trigger_service.AMLOTriggerService.check_and_create_amlo_records', return_value={}), \
             patch('services.bot_trigger_service.BOTTriggerService.check_and_create_bot_records', return_value={}):

            # 模拟数据库会话
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session

            # 模拟查询和更新
            mock_reservation = (
                1,
                'RS202510210001',
                'AMLO-1-01',
                'approved',
                Decimal('6000000.00'),
                '审核通过'
            )

            # 创建多个返回值实例
            check_result = MagicMock()
            check_result.fetchone.return_value = mock_reservation

            update_result = MagicMock()
            update_result.rowcount = 1  # 表示更新成功
            update_result.fetchone.return_value = None

            # 设置execute的返回值顺序
            mock_session.execute.side_effect = [check_result, update_result]

            # 模拟请求数据
            mock_request.get_json.return_value = {
                'currency_id': 2,
                'type': 'buy',
                'amount': 171428.57,
                'local_amount': 6000000.00,
                'exchange_rate': 35.0,
                'customer_name': '张三',
                'customer_id': '1234567890123',
                'purpose': '旅游'
            }
            mock_request.remote_addr = '127.0.0.1'

            # 模拟当前用户
            current_user = {
                'id': 1,
                'branch_id': 1,
                'username': 'operator'
            }

            # 模拟币种和网点查询
            mock_currency = Mock()
            mock_currency.currency_code = 'USD'

            mock_branch = Mock()
            mock_branch.base_currency_id = 1

            mock_session.query.return_value.filter_by.return_value.first.side_effect = [
                mock_currency,
                mock_branch
            ]

            # 模拟余额服务
            mock_balance_service.update_currency_balance.return_value = (
                Decimal('1000000.00'),
                Decimal('1171428.57')
            )

            # 模拟交易创建
            mock_transaction = Mock()
            mock_transaction.id = 1001
            mock_transaction.transaction_no = 'T20251021001'
            mock_transaction.type = 'buy'
            mock_transaction.rate = Decimal('35.0')
            mock_transaction.customer_name = '张三'
            mock_transaction.customer_id = '1234567890123'
            mock_transaction.purpose = '旅游'
            mock_transaction.remarks = ''
            mock_transaction.transaction_date = date.today()
            mock_transaction.transaction_time = '10:30:00'

            mock_balance_service.create_exchange_transaction.return_value = mock_transaction

            # 执行交易
            response = perform_exchange(current_user)
            response_data = response.get_json()

            # 验证交易成功
            assert response_data['success'] is True

            # 验证UPDATE语句被调用（第二次execute调用）
            assert mock_session.execute.call_count == 2

            # 验证commit被调用（至少一次用于更新状态）
            assert mock_session.commit.called


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
