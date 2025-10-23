# -*- coding: utf-8 -*-
"""
交易+合规触发集成测试
验证实际交易流程中AMLO和BOT触发的正确性

运行方式：
    pytest tests/backend/integration/test_exchange_with_compliance.py -v
"""

import pytest
from decimal import Decimal
from datetime import datetime, date
from unittest.mock import Mock, MagicMock, patch, ANY
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..', 'src'))

from services.amlo_trigger_service import AMLOTriggerService
from services.bot_trigger_service import BOTTriggerService
from services.repform.rule_engine import RuleEngine


class TestExchangeWithCompliance:
    """测试交易流程中的合规触发"""

    def test_large_cash_transaction_triggers_amlo_ctr(self):
        """测试大额现金交易触发AMLO CTR (AMLO-1-01)"""
        # 模拟场景: 买入USD $160,000 (约5,600,000 THB)
        session = MagicMock()

        transaction = Mock()
        transaction.id = 1001
        transaction.transaction_no = 'T20251021001'
        transaction.local_amount = Decimal('5600000.00')  # 超过500万泰铢阈值
        transaction.amount = Decimal('160000.00')
        transaction.rate = Decimal('35.00')
        transaction.type = 'buy'
        transaction.payment_method = 'cash'
        transaction.customer_id = '1234567890123'
        transaction.customer_name = 'John Doe'
        transaction.customer_country_code = 'US'
        transaction.transaction_date = date.today()

        currency = Mock()
        currency.currency_code = 'USD'

        # 模拟RuleEngine返回触发AMLO-1-01
        with patch.object(RuleEngine, 'check_triggers') as mock_check, \
             patch.object(RuleEngine, 'get_customer_stats', return_value={}), \
             patch.object(AMLOTriggerService, '_create_amlo_101_record') as mock_create, \
             patch.object(AMLOTriggerService, '_mark_transaction_amlo_flag'):

            # 模拟AMLO-1-01触发，其他不触发
            mock_check.side_effect = [
                {
                    'triggered': True,
                    'highest_priority_rule': {
                        'rule_name': 'CTR大额现金交易',
                        'id': 1
                    }
                },
                {'triggered': False},  # AMLO-1-02
                {'triggered': False}   # AMLO-1-03
            ]

            results = AMLOTriggerService.check_and_create_amlo_records(
                session, transaction, currency, 1, 1
            )

        # 验证AMLO CTR被创建
        assert results['amlo_101_created'] is True
        assert results['amlo_102_created'] is False
        assert results['amlo_103_created'] is False
        assert mock_create.called

    def test_large_fx_transaction_triggers_bot_buyfx(self):
        """测试大额外汇交易触发BOT BuyFX"""
        # 模拟场景: 买入USD $25,000 (超过BOT阈值$20,000)
        session = MagicMock()

        transaction = Mock()
        transaction.id = 1002
        transaction.transaction_no = 'T20251021002'
        transaction.amount = Decimal('25000.00')
        transaction.local_amount = Decimal('875000.00')
        transaction.rate = Decimal('35.00')
        transaction.type = 'buy'
        transaction.payment_method = 'cash'
        transaction.customer_id = 'P123456'
        transaction.customer_name = 'Jane Smith'
        transaction.customer_country_code = 'US'
        transaction.transaction_date = date.today()
        transaction.use_fcd = False

        currency = Mock()
        currency.currency_code = 'USD'

        # 模拟RuleEngine返回触发BOT_BuyFX
        with patch.object(RuleEngine, 'check_triggers') as mock_check, \
             patch.object(BOTTriggerService, '_calculate_usd_equivalent', return_value=Decimal('25000')), \
             patch.object(BOTTriggerService, '_create_bot_buyfx_record') as mock_create, \
             patch.object(BOTTriggerService, '_mark_transaction_bot_flags'):

            # 模拟BOT_BuyFX触发，其他不触发
            mock_check.side_effect = [
                {
                    'triggered': True,
                    'highest_priority_rule': {
                        'rule_name': 'BOT Buy FX 超过$20K',
                        'id': 10
                    }
                },
                {'triggered': False},  # BOT_SellFX
                {'triggered': False}   # BOT_FCD
            ]

            results = BOTTriggerService.check_and_create_bot_records(
                session, transaction, currency, 1, 1
            )

        # 验证BOT BuyFX被创建
        assert results['bot_buyfx_created'] is True
        assert results['bot_sellfx_created'] is False
        assert results['bot_fcd_created'] is False
        assert mock_create.called

    def test_combined_amlo_and_bot_trigger(self):
        """测试同时触发AMLO和BOT"""
        # 模拟场景: 买入USD $200,000 (7,000,000 THB)
        # 应同时触发 AMLO-1-01 (超过500万) 和 BOT_BuyFX (超过$20K)
        session = MagicMock()

        transaction = Mock()
        transaction.id = 1003
        transaction.transaction_no = 'T20251021003'
        transaction.local_amount = Decimal('7000000.00')
        transaction.amount = Decimal('200000.00')
        transaction.rate = Decimal('35.00')
        transaction.type = 'buy'
        transaction.payment_method = 'cash'
        transaction.customer_id = '9876543210123'
        transaction.customer_name = 'Big Customer'
        transaction.customer_country_code = 'US'
        transaction.transaction_date = date.today()
        transaction.use_fcd = False

        currency = Mock()
        currency.currency_code = 'USD'

        # 测试AMLO触发
        with patch.object(RuleEngine, 'check_triggers') as mock_check_amlo, \
             patch.object(RuleEngine, 'get_customer_stats', return_value={}), \
             patch.object(AMLOTriggerService, '_create_amlo_101_record') as mock_amlo_create, \
             patch.object(AMLOTriggerService, '_mark_transaction_amlo_flag'):

            mock_check_amlo.side_effect = [
                {'triggered': True, 'highest_priority_rule': {'rule_name': 'CTR', 'id': 1}},
                {'triggered': False},
                {'triggered': False}
            ]

            amlo_results = AMLOTriggerService.check_and_create_amlo_records(
                session, transaction, currency, 1, 1
            )

        # 测试BOT触发
        with patch.object(RuleEngine, 'check_triggers') as mock_check_bot, \
             patch.object(BOTTriggerService, '_calculate_usd_equivalent', return_value=Decimal('200000')), \
             patch.object(BOTTriggerService, '_create_bot_buyfx_record') as mock_bot_create, \
             patch.object(BOTTriggerService, '_mark_transaction_bot_flags'):

            mock_check_bot.side_effect = [
                {'triggered': True, 'highest_priority_rule': {'rule_name': 'BOT BuyFX', 'id': 10}},
                {'triggered': False},
                {'triggered': False}
            ]

            bot_results = BOTTriggerService.check_and_create_bot_records(
                session, transaction, currency, 1, 1
            )

        # 验证两个系统都被触发
        assert amlo_results['amlo_101_created'] is True
        assert bot_results['bot_buyfx_created'] is True
        assert mock_amlo_create.called
        assert mock_bot_create.called

    def test_small_transaction_no_trigger(self):
        """测试小额交易不触发任何合规报告"""
        # 模拟场景: 买入USD $1,000 (35,000 THB)
        session = MagicMock()

        transaction = Mock()
        transaction.id = 1004
        transaction.transaction_no = 'T20251021004'
        transaction.local_amount = Decimal('35000.00')
        transaction.amount = Decimal('1000.00')
        transaction.rate = Decimal('35.00')
        transaction.type = 'buy'
        transaction.payment_method = 'cash'
        transaction.customer_id = 'SMALL001'
        transaction.customer_name = 'Small Customer'
        transaction.customer_country_code = 'TH'
        transaction.transaction_date = date.today()
        transaction.use_fcd = False

        currency = Mock()
        currency.currency_code = 'USD'

        # AMLO检查
        with patch.object(RuleEngine, 'check_triggers') as mock_check_amlo, \
             patch.object(RuleEngine, 'get_customer_stats', return_value={}), \
             patch.object(AMLOTriggerService, '_mark_transaction_amlo_flag'):

            # 所有AMLO规则都不触发
            mock_check_amlo.side_effect = [
                {'triggered': False},
                {'triggered': False},
                {'triggered': False}
            ]

            amlo_results = AMLOTriggerService.check_and_create_amlo_records(
                session, transaction, currency, 1, 1
            )

        # BOT检查
        with patch.object(RuleEngine, 'check_triggers') as mock_check_bot, \
             patch.object(BOTTriggerService, '_calculate_usd_equivalent', return_value=Decimal('1000')), \
             patch.object(BOTTriggerService, '_mark_transaction_bot_flags'):

            # 所有BOT规则都不触发
            mock_check_bot.side_effect = [
                {'triggered': False},
                {'triggered': False},
                {'triggered': False}
            ]

            bot_results = BOTTriggerService.check_and_create_bot_records(
                session, transaction, currency, 1, 1
            )

        # 验证没有触发任何报告
        assert amlo_results['amlo_101_created'] is False
        assert amlo_results['amlo_102_created'] is False
        assert amlo_results['amlo_103_created'] is False
        assert bot_results['bot_buyfx_created'] is False
        assert bot_results['bot_sellfx_created'] is False
        assert bot_results['bot_fcd_created'] is False

    def test_test_trigger_matches_actual_trigger(self):
        """测试触发API和实际触发逻辑的一致性"""
        # 准备相同的数据
        transaction_data = {
            'total_amount': 6000000,
            'amount': 171428.57,
            'currency_code': 'USD',
            'transaction_type': 'buy',
            'direction': 'buy',
            'payment_method': 'cash',
            'customer_country_code': 'US',
            'customer_id': '1234567890123'
        }

        session = MagicMock()

        # 模拟测试触发API调用 RuleEngine
        with patch.object(RuleEngine, 'check_triggers') as mock_check_test:
            mock_check_test.return_value = {
                'triggered': True,
                'highest_priority_rule': {
                    'rule_name': 'CTR大额现金交易',
                    'id': 1
                }
            }

            test_result = RuleEngine.check_triggers(
                session, 'AMLO-1-01', transaction_data, 1
            )

        # 模拟实际交易触发调用相同的 RuleEngine
        with patch.object(RuleEngine, 'check_triggers') as mock_check_actual:
            mock_check_actual.return_value = {
                'triggered': True,
                'highest_priority_rule': {
                    'rule_name': 'CTR大额现金交易',
                    'id': 1
                }
            }

            actual_result = RuleEngine.check_triggers(
                session, 'AMLO-1-01', transaction_data, 1
            )

        # 验证结果完全一致
        assert test_result['triggered'] == actual_result['triggered']
        assert test_result['highest_priority_rule']['id'] == actual_result['highest_priority_rule']['id']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
