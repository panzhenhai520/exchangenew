# -*- coding: utf-8 -*-
"""
触发服务统一化测试
验证 AMLOTriggerService 和 BOTTriggerService 使用 RuleEngine 后的功能

运行方式：
    pytest tests/backend/services/test_trigger_services_unified.py -v
"""

import pytest
from decimal import Decimal
from datetime import datetime, date
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy import text

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..', 'src'))

from services.amlo_trigger_service import AMLOTriggerService
from services.bot_trigger_service import BOTTriggerService
from services.repform.rule_engine import RuleEngine


class TestAMLOTriggerServiceUnified:
    """测试AMLO触发服务使用统一规则引擎"""

    def test_prepare_transaction_data(self):
        """测试交易数据准备"""
        # 创建模拟对象
        session = MagicMock()
        transaction = Mock()
        transaction.transaction_no = 'T20251021001'
        transaction.local_amount = Decimal('5500000.00')
        transaction.amount = Decimal('150000.00')
        transaction.type = 'buy'
        transaction.payment_method = 'cash'
        transaction.customer_country_code = 'US'
        transaction.transaction_date = date.today()
        transaction.customer_id = '1234567890123'
        transaction.customer_name = 'John Doe'

        currency = Mock()
        currency.currency_code = 'USD'

        # 模拟客户统计查询
        with patch.object(RuleEngine, 'get_customer_stats', return_value={
            'cumulative_amount_30d': 10000000,
            'transaction_count_30d': 5
        }):
            data = AMLOTriggerService._prepare_transaction_data(
                session, transaction, currency
            )

        # 验证数据格式
        assert data['total_amount'] == 5500000.00
        assert data['amount'] == 150000.00
        assert data['currency_code'] == 'USD'
        assert data['transaction_type'] == 'buy'
        assert data['direction'] == 'buy'
        assert data['payment_method'] == 'cash'
        assert data['customer_country_code'] == 'US'
        assert data['customer_id'] == '1234567890123'
        assert data['cumulative_amount_30d'] == 10000000
        assert data['transaction_count_30d'] == 5

    def test_check_and_create_uses_rule_engine(self):
        """测试触发检查使用RuleEngine"""
        session = MagicMock()
        transaction = Mock()
        transaction.transaction_no = 'T20251021002'
        transaction.local_amount = Decimal('6000000.00')
        transaction.amount = Decimal('180000.00')
        transaction.type = 'buy'
        transaction.payment_method = 'cash'
        transaction.customer_id = '9876543210123'
        transaction.customer_name = 'Jane Smith'

        currency = Mock()
        currency.currency_code = 'USD'

        # 模拟RuleEngine返回触发AMLO-1-01
        with patch.object(RuleEngine, 'check_triggers') as mock_check_triggers, \
             patch.object(RuleEngine, 'get_customer_stats', return_value={}), \
             patch.object(AMLOTriggerService, '_create_amlo_101_record') as mock_create, \
             patch.object(AMLOTriggerService, '_mark_transaction_amlo_flag'):

            # 第一次调用（AMLO-1-01）返回触发
            # 第二、三次调用返回未触发
            mock_check_triggers.side_effect = [
                {
                    'triggered': True,
                    'highest_priority_rule': {
                        'rule_name': 'CTR大额现金交易',
                        'id': 1
                    }
                },
                {'triggered': False},
                {'triggered': False}
            ]

            results = AMLOTriggerService.check_and_create_amlo_records(
                session, transaction, currency, 1, 1
            )

        # 验证RuleEngine被调用3次（检查3种AMLO类型）
        assert mock_check_triggers.call_count == 3

        # 验证AMLO-1-01记录被创建
        assert results['amlo_101_created'] is True
        assert results['amlo_102_created'] is False
        assert results['amlo_103_created'] is False
        assert mock_create.called


class TestBOTTriggerServiceUnified:
    """测试BOT触发服务使用统一规则引擎"""

    def test_prepare_transaction_data(self):
        """测试BOT交易数据准备"""
        session = MagicMock()
        transaction = Mock()
        transaction.amount = Decimal('25000.00')
        transaction.local_amount = Decimal('875000.00')
        transaction.type = 'buy'
        transaction.payment_method = 'cash'
        transaction.use_fcd = False  # 明确设置
        transaction.customer_country_code = 'JP'
        transaction.transaction_date = date.today()
        transaction.customer_id = 'P123456'
        transaction.customer_name = 'Tanaka'

        currency = Mock()
        currency.currency_code = 'USD'

        usd_equivalent = Decimal('25000.00')

        data = BOTTriggerService._prepare_transaction_data(
            session, transaction, currency, usd_equivalent
        )

        # 验证数据格式
        assert data['amount'] == 25000.00
        assert data['local_amount'] == 875000.00
        assert data['total_amount'] == 875000.00  # 兼容字段
        assert data['usd_equivalent'] == 25000.00
        assert data['verification_amount'] == 25000.00  # 兼容字段
        assert data['currency_code'] == 'USD'
        assert data['direction'] == 'buy'
        assert data['use_fcd'] is False

    def test_check_and_create_uses_rule_engine(self):
        """测试BOT触发检查使用RuleEngine"""
        session = MagicMock()
        transaction = Mock()
        transaction.transaction_no = 'T20251021003'
        transaction.amount = Decimal('30000.00')
        transaction.local_amount = Decimal('1050000.00')
        transaction.rate = Decimal('35.00')
        transaction.type = 'buy'
        transaction.payment_method = 'cash'
        transaction.customer_id = 'P654321'
        transaction.customer_name = 'Sato'

        currency = Mock()
        currency.currency_code = 'USD'

        # 模拟RuleEngine返回触发BOT_BuyFX
        with patch.object(RuleEngine, 'check_triggers') as mock_check_triggers, \
             patch.object(BOTTriggerService, '_calculate_usd_equivalent', return_value=Decimal('30000')), \
             patch.object(BOTTriggerService, '_create_bot_buyfx_record') as mock_create, \
             patch.object(BOTTriggerService, '_mark_transaction_bot_flags'):

            # 第一次调用（BOT_BuyFX）返回触发
            # 第二、三次调用返回未触发
            mock_check_triggers.side_effect = [
                {
                    'triggered': True,
                    'highest_priority_rule': {
                        'rule_name': 'Buy FX $20K+',
                        'id': 10
                    }
                },
                {'triggered': False},
                {'triggered': False}
            ]

            results = BOTTriggerService.check_and_create_bot_records(
                session, transaction, currency, 1, 1
            )

        # 验证RuleEngine被调用3次（检查3种BOT类型）
        assert mock_check_triggers.call_count == 3

        # 验证BOT_BuyFX记录被创建
        assert results['bot_buyfx_created'] is True
        assert results['bot_sellfx_created'] is False
        assert results['bot_fcd_created'] is False
        assert mock_create.called


class TestRuleEngineIntegration:
    """测试RuleEngine集成"""

    def test_rule_engine_evaluate_simple_condition(self):
        """测试RuleEngine评估简单条件"""
        rule_expression = {
            'logic': 'AND',
            'conditions': [
                {'field': 'total_amount', 'operator': '>=', 'value': 5000000},
                {'field': 'currency_code', 'operator': '!=', 'value': 'THB'}
            ]
        }

        # 满足条件的数据
        data = {
            'total_amount': 6000000,
            'currency_code': 'USD'
        }

        result = RuleEngine.evaluate_rule(rule_expression, data)
        assert result is True

        # 不满足条件的数据
        data2 = {
            'total_amount': 3000000,
            'currency_code': 'USD'
        }

        result2 = RuleEngine.evaluate_rule(rule_expression, data2)
        assert result2 is False

    def test_rule_engine_evaluate_with_details(self):
        """测试RuleEngine带详情的评估"""
        rule_expression = {
            'logic': 'AND',
            'conditions': [
                {'field': 'usd_equivalent', 'operator': '>=', 'value': 20000},
                {'field': 'use_fcd', 'operator': '=', 'value': True}
            ]
        }

        data = {
            'usd_equivalent': 25000,
            'use_fcd': True
        }

        is_matched, details = RuleEngine.evaluate_rule_with_details(rule_expression, data)

        assert is_matched is True
        assert len(details['matched']) == 2
        assert len(details['unmatched']) == 0
        assert details['logic'] == 'AND'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
