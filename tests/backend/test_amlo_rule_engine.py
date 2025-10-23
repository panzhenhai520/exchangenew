import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.repform.rule_engine import RuleEngine


@pytest.mark.parametrize(
    "data,expected",
    [
        ({"total_amount": 5200000, "customer_country_code": "US"}, True),
        ({"total_amount": 4800000, "customer_country_code": "US"}, False),
        ({"total_amount": 6000000, "customer_country_code": "TH"}, False),
    ],
)
def test_ctr_rule_triggers_on_amount_and_country(data, expected):
    rule_expression = {
        "logic": "AND",
        "conditions": [
            {"field": "total_amount", "operator": ">=", "value": 5000000},
            {"field": "customer_country_code", "operator": "=", "value": "US"},
        ],
    }
    assert RuleEngine.evaluate_rule(rule_expression, data) is expected


def test_atr_rule_requires_asset_and_threshold():
    rule_expression = {
        "logic": "AND",
        "conditions": [
            {"field": "exchange_type", "operator": "=", "value": "asset_mortgage"},
            {"field": "asset_value", "operator": ">=", "value": 2000000},
        ],
    }

    data = {
        "exchange_type": "asset_mortgage",
        "asset_value": 2500000,
    }
    assert RuleEngine.evaluate_rule(rule_expression, data) is True

    data["asset_value"] = 1500000
    assert RuleEngine.evaluate_rule(rule_expression, data) is False


def test_str_rule_supports_nested_conditions():
    rule_expression = {
        "logic": "OR",
        "conditions": [
            {"field": "is_manual_flag", "operator": "=", "value": True},
            {
                "logic": "AND",
                "conditions": [
                    {"field": "cumulative_amount_30d", "operator": ">=", "value": 8000000},
                    {"field": "transaction_count_30d", "operator": ">=", "value": 10},
                ],
            },
        ],
    }

    # Manual flag should trigger regardless of totals
    data = {
        "is_manual_flag": True,
        "cumulative_amount_30d": 0,
        "transaction_count_30d": 0,
    }
    assert RuleEngine.evaluate_rule(rule_expression, data) is True

    # Automatic threshold trigger
    data = {
        "is_manual_flag": False,
        "cumulative_amount_30d": 9000000,
        "transaction_count_30d": 12,
    }
    assert RuleEngine.evaluate_rule(rule_expression, data) is True

    # No condition satisfied
    data = {
        "is_manual_flag": False,
        "cumulative_amount_30d": 4000000,
        "transaction_count_30d": 4,
    }
    assert RuleEngine.evaluate_rule(rule_expression, data) is False
