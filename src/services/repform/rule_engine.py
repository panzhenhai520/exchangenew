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
    def evaluate_rule_with_details(rule_expression: Dict[str, Any], data: Dict[str, Any]) -> tuple:
        """
        评估规则表达式并返回详细的条件匹配信息
        
        Args:
            rule_expression: 规则表达式字典
            data: 待评估的数据字典
            
        Returns:
            (是否匹配, 条件详情字典)
            条件详情 = {
                'matched': [满足的条件列表],
                'unmatched': [未满足的条件列表]
            }
        """
        if not rule_expression or not isinstance(rule_expression, dict):
            return False, {'matched': [], 'unmatched': []}
        
        logic = rule_expression.get('logic', 'AND').upper()
        conditions = rule_expression.get('conditions', [])
        
        if not conditions:
            return False, {'matched': [], 'unmatched': []}
        
        matched_conditions = []
        unmatched_conditions = []
        results = []  # 用于逻辑判断的结果列表

        for condition in conditions:
            try:
                # 检查是否是嵌套条件（有logic字段）
                if 'logic' in condition and 'conditions' in condition:
                    # 递归处理嵌套条件
                    nested_result, nested_details = RuleEngine.evaluate_rule_with_details(condition, data)

                    # 不要扁平化嵌套条件，只记录嵌套条件的最终结果
                    condition_detail = {
                        'nested_logic': condition.get('logic'),
                        'nested_result': nested_result,
                        'nested_details': nested_details,  # 保留详细信息
                        'matched': nested_result
                    }

                    results.append(nested_result)  # 用于逻辑判断
                    if nested_result:
                        matched_conditions.append(condition_detail)
                    else:
                        unmatched_conditions.append(condition_detail)
                else:
                    # 处理简单条件
                    field_name = condition.get('field')
                    operator = condition.get('operator')
                    expected_value = condition.get('value')
                    actual_value = data.get(field_name)

                    result = RuleEngine._compare_values(actual_value, operator, expected_value)

                    condition_detail = {
                        'field': field_name,
                        'operator': operator,
                        'expected_value': expected_value,
                        'actual_value': actual_value,
                        'matched': result
                    }

                    results.append(result)  # 用于逻辑判断
                    if result:
                        matched_conditions.append(condition_detail)
                    else:
                        unmatched_conditions.append(condition_detail)

            except Exception as e:
                print(f"Error evaluating condition {condition}: {str(e)}")
                unmatched_conditions.append({
                    'field': condition.get('field', 'unknown'),
                    'operator': condition.get('operator', '='),
                    'expected_value': condition.get('value'),
                    'actual_value': None,
                    'matched': False,
                    'error': str(e)
                })
        
        # 根据逻辑操作符返回结果
        if logic == 'AND':
            is_triggered = all(results) and len(results) > 0
        elif logic == 'OR':
            is_triggered = any(results) and len(results) > 0
        else:  # NOT
            is_triggered = not any(results)
        
        return is_triggered, {
            'matched': matched_conditions,
            'unmatched': unmatched_conditions,
            'logic': logic
        }
    
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
                # 检查是否是嵌套条件（有logic字段）
                if 'logic' in condition and 'conditions' in condition:
                    # 递归处理嵌套条件
                    nested_result = RuleEngine.evaluate_rule(condition, data)
                    results.append(nested_result)
                else:
                    # 处理简单条件
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
            print(f"\n[RuleEngine.check_triggers] ========== 开始检查触发条件 ==========", flush=True)
            print(f"[RuleEngine.check_triggers] 报告类型: {report_type}", flush=True)
            print(f"[RuleEngine.check_triggers] 网点ID: {branch_id}", flush=True)
            print(f"[RuleEngine.check_triggers] 交易数据: {data}", flush=True)

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

            all_rules = list(result)
            print(f"[RuleEngine.check_triggers] 查询到 {len(all_rules)} 条启用的规则", flush=True)

            matched_rules = []

            for row in all_rules:
                rule_dict = dict(row._mapping)
                rule_id = rule_dict['id']
                rule_name = rule_dict['rule_name']
                priority = rule_dict['priority']

                print(f"\n[RuleEngine.check_triggers] --- 评估规则 {rule_id}: {rule_name} (优先级: {priority}) ---", flush=True)

                # 解析rule_expression
                try:
                    rule_expression = json.loads(rule_dict['rule_expression'])
                    print(f"[RuleEngine.check_triggers] 规则表达式: {rule_expression}", flush=True)
                except Exception as parse_error:
                    print(f"[RuleEngine.check_triggers] [ERROR] 规则表达式解析失败: {str(parse_error)}", flush=True)
                    continue

                # 评估规则，并收集条件匹配详情
                is_matched, condition_details = RuleEngine.evaluate_rule_with_details(rule_expression, data)

                match_result = 'MATCHED' if is_matched else 'NOT_MATCHED'
                print(f"[RuleEngine.check_triggers] 规则匹配结果: {match_result}", flush=True)
                print(f"[RuleEngine.check_triggers] 匹配的条件: {condition_details.get('matched', [])}", flush=True)
                print(f"[RuleEngine.check_triggers] 未匹配的条件: {condition_details.get('unmatched', [])}", flush=True)

                if is_matched:
                    print(f"[RuleEngine.check_triggers] [OK] 规则 {rule_id} 匹配成功，添加到结果列表", flush=True)
                    rule_dict['condition_details'] = condition_details  # 添加条件详情
                    rule_dict['rule_expression_parsed'] = rule_expression  # 添加解析后的表达式
                    matched_rules.append(rule_dict)

            # 构建返回结果
            print(f"\n[RuleEngine.check_triggers] ========== 评估完成 ==========", flush=True)
            print(f"[RuleEngine.check_triggers] 共匹配 {len(matched_rules)} 条规则", flush=True)

            if matched_rules:
                highest_priority_rule = matched_rules[0]
                print(f"[RuleEngine.check_triggers] 最高优先级规则: {highest_priority_rule['rule_name']} (ID: {highest_priority_rule['id']})", flush=True)

                result_dict = {
                    'triggered': True,
                    'trigger_rules': matched_rules,
                    'highest_priority_rule': highest_priority_rule,
                    'allow_continue': highest_priority_rule.get('allow_continue', False),
                    'message_cn': highest_priority_rule.get('warning_message_cn', ''),
                    'message_en': highest_priority_rule.get('warning_message_en', ''),
                    'message_th': highest_priority_rule.get('warning_message_th', ''),
                    'matched_conditions': highest_priority_rule.get('condition_details', {}).get('matched', []),  # 新增
                    'unmatched_conditions': highest_priority_rule.get('condition_details', {}).get('unmatched', []),  # 新增
                    'rule_expression': highest_priority_rule.get('rule_expression_parsed')  # 新增
                }

                print(f"[RuleEngine.check_triggers] 返回结果: triggered=True", flush=True)
                return result_dict
            else:
                print(f"[RuleEngine.check_triggers] 返回结果: triggered=False (无匹配规则)", flush=True)
                return {
                    'triggered': False,
                    'trigger_rules': [],
                    'highest_priority_rule': None,
                    'allow_continue': True
                }

        except Exception as e:
            print(f"[RuleEngine.check_triggers] [EXCEPTION] 异常: {str(e)}", flush=True)
            import traceback
            traceback.print_exc()
            raise

    @staticmethod
    def get_customer_stats(
        db_session: Session,
        customer_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取客户累计交易统计（跨网点）

        Args:
            db_session: 数据库会话
            customer_id: 客户证件号
            days: 统计天数（默认30天）

        Returns:
            统计结果字典:
            {
                "cumulative_amount_30d": 累计金额（跨网点）,
                "transaction_count_30d": 交易次数（跨网点）,
                "last_transaction_date": 最后交易日期,
                "branch_breakdown": 按网点分解统计
            }
        """
        try:
            start_date = (datetime.now() - timedelta(days=days)).date()

            # 总体统计（跨网点）
            sql = text("""
                SELECT
                    COUNT(*) as transaction_count,
                    COALESCE(SUM(ABS(local_amount)), 0) as cumulative_amount,
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
            
            # 按网点分解统计
            branch_sql = text("""
                SELECT
                    branch_id,
                    COUNT(*) as count,
                    COALESCE(SUM(ABS(local_amount)), 0) as amount
                FROM exchange_transactions
                WHERE customer_id = :customer_id
                    AND transaction_date >= :start_date
                    AND status = 'completed'
                GROUP BY branch_id
                ORDER BY branch_id
            """)
            
            branch_result = db_session.execute(
                branch_sql,
                {'customer_id': customer_id, 'start_date': start_date}
            )
            
            branch_breakdown = []
            for branch_row in branch_result:
                branch_breakdown.append({
                    'branch_id': branch_row[0],
                    'count': int(branch_row[1]),
                    'amount': float(branch_row[2])
                })
            
            if row:
                stats = {
                    'cumulative_amount_30d': float(row[1] or 0),
                    'transaction_count_30d': int(row[0] or 0),
                    'last_transaction_date': str(row[2]) if row[2] else None,
                    'branch_breakdown': branch_breakdown,
                    # 保持向后兼容
                    'cumulative_amount_1month': float(row[1] or 0),
                    'transaction_count_1month': int(row[0] or 0)
                }
                return stats

            return {
                'cumulative_amount_30d': 0.0,
                'transaction_count_30d': 0,
                'last_transaction_date': None,
                'branch_breakdown': [],
                'cumulative_amount_1month': 0.0,
                'transaction_count_1month': 0
            }

        except Exception as e:
            print(f"Error getting customer stats for {customer_id}: {str(e)}")
            return {
                'cumulative_amount_30d': 0.0,
                'transaction_count_30d': 0,
                'last_transaction_date': None,
                'branch_breakdown': [],
                'cumulative_amount_1month': 0.0,
                'transaction_count_1month': 0
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
