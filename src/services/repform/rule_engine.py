# -*- coding: utf-8 -*-
"""
RuleEngine - 规则引擎
负责解析和评估trigger_rules表中的规则表达式
版本: v1.0
创建日期: 2025-10-02
"""

import json
from typing import Dict, Any, List, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime, timedelta


class RuleEngine:
    """规则引擎类"""

    @staticmethod
    def evaluate_rule(rule_expression: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """
        评估规则表达式

        Args:
            rule_expression: 规则表达式字典，例如:
                {
                    "logic": "AND",
                    "conditions": [
                        {"field": "total_amount", "operator": ">=", "value": 5000000},
                        {"field": "currency_code", "operator": "!=", "value": "THB"}
                    ]
                }
            data: 待评估的数据字典

        Returns:
            布尔值，表示是否满足规则
        """
        if not rule_expression or not isinstance(rule_expression, dict):
            return False

        logic = rule_expression.get('logic', 'AND').upper()
        conditions = rule_expression.get('conditions', [])

        if not conditions:
            return False

        results = []
        for condition in conditions:
            try:
                field_name = condition.get('field')
                operator = condition.get('operator')
                expected_value = condition.get('value')

                actual_value = data.get(field_name)

                result = RuleEngine._compare_values(
                    actual_value,
                    operator,
                    expected_value
                )
                results.append(result)

            except Exception as e:
                print(f"Error evaluating condition {condition}: {str(e)}")
                results.append(False)

        # 根据逻辑操作符返回结果
        if logic == 'AND':
            return all(results)
        elif logic == 'OR':
            return any(results)
        elif logic == 'NOT':
            return not all(results)
        else:
            return False

    @staticmethod
    def _compare_values(actual: Any, operator: str, expected: Any) -> bool:
        """
        比较两个值

        Args:
            actual: 实际值
            operator: 操作符 (>, >=, <, <=, =, !=, IN, NOT IN, LIKE)
            expected: 期望值

        Returns:
            布尔值比较结果
        """
        # 处理None值
        if actual is None:
            return operator in ['!=', 'NOT IN']

        try:
            # 数值比较
            if operator == '>':
                return float(actual) > float(expected)
            elif operator == '>=':
                return float(actual) >= float(expected)
            elif operator == '<':
                return float(actual) < float(expected)
            elif operator == '<=':
                return float(actual) <= float(expected)

            # 等值比较
            elif operator == '=' or operator == '==':
                # 布尔值比较
                if isinstance(expected, bool):
                    return bool(actual) == expected
                # 数值比较
                try:
                    return float(actual) == float(expected)
                except:
                    return str(actual) == str(expected)

            elif operator == '!=' or operator == '<>':
                try:
                    return float(actual) != float(expected)
                except:
                    return str(actual) != str(expected)

            # 列表/集合操作
            elif operator == 'IN':
                if isinstance(expected, (list, tuple, set)):
                    return actual in expected
                return actual == expected

            elif operator == 'NOT IN':
                if isinstance(expected, (list, tuple, set)):
                    return actual not in expected
                return actual != expected

            # 字符串操作
            elif operator == 'LIKE':
                return str(expected).lower() in str(actual).lower()

            elif operator == 'NOT LIKE':
                return str(expected).lower() not in str(actual).lower()

            else:
                print(f"Unsupported operator: {operator}")
                return False

        except Exception as e:
            print(f"Error comparing values: actual={actual}, operator={operator}, expected={expected}, error={str(e)}")
            return False

    @staticmethod
    def check_triggers(
        db_session: Session,
        report_type: str,
        data: Dict[str, Any],
        branch_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        检查是否触发报告

        Args:
            db_session: 数据库会话
            report_type: 报告类型
            data: 交易数据
            branch_id: 网点ID（可选，如果提供则优先匹配该网点的规则）

        Returns:
            检查结果字典:
            {
                "triggered": True/False,
                "trigger_rules": [匹配的规则列表],
                "highest_priority_rule": 最高优先级规则,
                "allow_continue": 是否允许继续交易
            }
        """
        try:
            # 查询该报告类型的启用规则
            sql = text("""
                SELECT
                    id,
                    rule_name,
                    report_type,
                    rule_expression,
                    description_cn,
                    description_en,
                    description_th,
                    priority,
                    allow_continue,
                    warning_message_cn,
                    warning_message_en,
                    warning_message_th,
                    branch_id
                FROM trigger_rules
                WHERE report_type = :report_type
                    AND is_active = TRUE
                    AND (branch_id IS NULL OR branch_id = :branch_id)
                ORDER BY priority DESC, id ASC
            """)

            result = db_session.execute(
                sql,
                {'report_type': report_type, 'branch_id': branch_id or 0}
            )

            matched_rules = []

            for row in result:
                rule_dict = dict(row._mapping)

                # 解析rule_expression
                try:
                    rule_expression = json.loads(rule_dict['rule_expression'])
                except:
                    print(f"Invalid rule expression for rule {rule_dict['id']}")
                    continue

                # 评估规则
                if RuleEngine.evaluate_rule(rule_expression, data):
                    matched_rules.append(rule_dict)

            # 构建返回结果
            if matched_rules:
                highest_priority_rule = matched_rules[0]

                return {
                    'triggered': True,
                    'trigger_rules': matched_rules,
                    'highest_priority_rule': highest_priority_rule,
                    'allow_continue': highest_priority_rule.get('allow_continue', False),
                    'message_cn': highest_priority_rule.get('warning_message_cn', ''),
                    'message_en': highest_priority_rule.get('warning_message_en', ''),
                    'message_th': highest_priority_rule.get('warning_message_th', '')
                }
            else:
                return {
                    'triggered': False,
                    'trigger_rules': [],
                    'highest_priority_rule': None,
                    'allow_continue': True
                }

        except Exception as e:
            print(f"Error checking triggers for report type {report_type}: {str(e)}")
            raise

    @staticmethod
    def get_customer_stats(
        db_session: Session,
        customer_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取客户累计交易统计

        Args:
            db_session: 数据库会话
            customer_id: 客户证件号
            days: 统计天数（默认30天）

        Returns:
            统计结果字典:
            {
                "cumulative_amount_1month": 累计金额,
                "transaction_count_1month": 交易次数,
                "last_transaction_date": 最后交易日期
            }
        """
        try:
            start_date = (datetime.now() - timedelta(days=days)).date()

            sql = text("""
                SELECT
                    COUNT(*) as transaction_count,
                    COALESCE(SUM(local_amount), 0) as cumulative_amount,
                    MAX(transaction_date) as last_transaction_date
                FROM exchange_transactions
                WHERE customer_id = :customer_id
                    AND transaction_date >= :start_date
                    AND status = 'completed'
            """)

            result = db_session.execute(
                sql,
                {'customer_id': customer_id, 'start_date': start_date}
            )

            row = result.first()
            if row:
                return {
                    'cumulative_amount_1month': float(row[1] or 0),
                    'transaction_count_1month': int(row[0] or 0),
                    'last_transaction_date': str(row[2]) if row[2] else None
                }

            return {
                'cumulative_amount_1month': 0.0,
                'transaction_count_1month': 0,
                'last_transaction_date': None
            }

        except Exception as e:
            print(f"Error getting customer stats for {customer_id}: {str(e)}")
            return {
                'cumulative_amount_1month': 0.0,
                'transaction_count_1month': 0,
                'last_transaction_date': None
            }

    @staticmethod
    def parse_condition(condition_str: str) -> Dict[str, Any]:
        """
        解析条件表达式字符串（用于从前端接收的文本条件）

        Args:
            condition_str: 条件字符串，例如 "total_amount >= 5000000"

        Returns:
            条件字典
        """
        try:
            # 简单的条件解析（可扩展为更复杂的解析器）
            operators = ['>=', '<=', '>', '<', '!=', '=', 'IN', 'NOT IN', 'LIKE']

            for operator in operators:
                if operator in condition_str:
                    parts = condition_str.split(operator, 1)
                    if len(parts) == 2:
                        field = parts[0].strip()
                        value_str = parts[1].strip()

                        # 尝试转换值类型
                        try:
                            value = json.loads(value_str)
                        except:
                            value = value_str.strip('"\'')

                        return {
                            'field': field,
                            'operator': operator,
                            'value': value
                        }

            return {}

        except Exception as e:
            print(f"Error parsing condition string '{condition_str}': {str(e)}")
            return {}
