# -*- coding: utf-8 -*-
"""
FormValidator - 表单验证器
负责验证用户提交的表单数据
版本: v1.0
创建日期: 2025-10-02
"""

import re
import json
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from .field_manager import FieldManager


class FormValidator:
    """表单验证器类"""

    @staticmethod
    def validate_form_data(
        db_session: Session,
        report_type: str,
        form_data: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        验证表单数据

        Args:
            db_session: 数据库会话
            report_type: 报告类型
            form_data: 表单数据

        Returns:
            (是否验证通过, 错误信息列表)
        """
        errors = []

        try:
            # 获取字段定义
            fields = FieldManager.get_fields_by_report_type(
                db_session,
                report_type,
                language='zh'
            )

            for field in fields:
                field_name = field.get('field_name')
                field_label = field.get('label', field_name)
                field_type = field.get('field_type')
                is_required = field.get('is_required', False)
                validation_rule = field.get('validation_rule') or {}  # 确保不是None

                # 获取实际值
                actual_value = form_data.get(field_name)

                # 必填校验
                if is_required:
                    if actual_value is None or actual_value == '':
                        errors.append(f"{field_label}为必填项")
                        continue

                # 如果值为空且非必填，跳过后续验证
                if actual_value is None or actual_value == '':
                    continue

                # 类型校验
                type_valid, type_error = FormValidator._validate_type(
                    actual_value,
                    field_type,
                    field_label
                )
                if not type_valid:
                    errors.append(type_error)
                    continue

                # 长度校验（VARCHAR, TEXT）
                if field_type in ['VARCHAR', 'TEXT'] and validation_rule:
                    length_valid, length_error = FormValidator._validate_length(
                        actual_value,
                        field_label,
                        validation_rule,
                        field.get('field_length')
                    )
                    if not length_valid:
                        errors.append(length_error)

                # 数值范围校验（INT, DECIMAL）
                if field_type in ['INT', 'DECIMAL'] and validation_rule:
                    range_valid, range_error = FormValidator._validate_range(
                        actual_value,
                        field_label,
                        validation_rule
                    )
                    if not range_valid:
                        errors.append(range_error)

                # 正则校验
                if validation_rule and 'pattern' in validation_rule:
                    pattern_valid, pattern_error = FormValidator._validate_pattern(
                        actual_value,
                        field_label,
                        validation_rule['pattern']
                    )
                    if not pattern_valid:
                        errors.append(pattern_error)

            return (len(errors) == 0, errors)

        except Exception as e:
            print(f"Error validating form data: {str(e)}")
            return (False, [f"验证过程发生错误: {str(e)}"])

    @staticmethod
    def _validate_type(
        value: Any,
        field_type: str,
        field_label: str
    ) -> Tuple[bool, str]:
        """
        验证值类型

        Args:
            value: 实际值
            field_type: 字段类型
            field_label: 字段标签

        Returns:
            (是否有效, 错误信息)
        """
        try:
            if field_type == 'INT':
                int(value)
            elif field_type == 'DECIMAL':
                float(value)
            elif field_type == 'DATE':
                # 简单的日期格式检查
                if not re.match(r'^\d{4}-\d{2}-\d{2}$', str(value)):
                    return (False, f"{field_label}日期格式不正确，应为YYYY-MM-DD")
            elif field_type == 'DATETIME':
                if not re.match(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}$', str(value)):
                    return (False, f"{field_label}日期时间格式不正确")
            elif field_type == 'BOOLEAN':
                if not isinstance(value, bool):
                    if str(value).lower() not in ['true', 'false', '1', '0']:
                        return (False, f"{field_label}必须是布尔值")

            return (True, '')

        except:
            return (False, f"{field_label}类型不正确")

    @staticmethod
    def _validate_length(
        value: Any,
        field_label: str,
        validation_rule: Dict[str, Any],
        max_length: int = None
    ) -> Tuple[bool, str]:
        """
        验证长度

        Args:
            value: 实际值
            field_label: 字段标签
            validation_rule: 验证规则
            max_length: 最大长度（字段定义）

        Returns:
            (是否有效, 错误信息)
        """
        value_str = str(value)
        length = len(value_str)

        # 最小长度
        if 'min_length' in validation_rule:
            min_length = validation_rule['min_length']
            if length < min_length:
                return (False, f"{field_label}最少{min_length}个字符")

        # 最大长度
        if 'max_length' in validation_rule:
            max_len = validation_rule['max_length']
            if length > max_len:
                return (False, f"{field_label}最多{max_len}个字符")
        elif max_length:
            if length > max_length:
                return (False, f"{field_label}最多{max_length}个字符")

        return (True, '')

    @staticmethod
    def _validate_range(
        value: Any,
        field_label: str,
        validation_rule: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        验证数值范围

        Args:
            value: 实际值
            field_label: 字段标签
            validation_rule: 验证规则

        Returns:
            (是否有效, 错误信息)
        """
        try:
            numeric_value = float(value)

            # 最小值
            if 'min' in validation_rule:
                min_value = float(validation_rule['min'])
                if numeric_value < min_value:
                    return (False, f"{field_label}不能小于{min_value}")

            # 最大值
            if 'max' in validation_rule:
                max_value = float(validation_rule['max'])
                if numeric_value > max_value:
                    return (False, f"{field_label}不能大于{max_value}")

            return (True, '')

        except:
            return (False, f"{field_label}必须是有效的数值")

    @staticmethod
    def _validate_pattern(
        value: Any,
        field_label: str,
        pattern: str
    ) -> Tuple[bool, str]:
        """
        验证正则表达式

        Args:
            value: 实际值
            field_label: 字段标签
            pattern: 正则表达式

        Returns:
            (是否有效, 错误信息)
        """
        try:
            value_str = str(value)
            if not re.match(pattern, value_str):
                return (False, f"{field_label}格式不正确")

            return (True, '')

        except:
            return (False, f"{field_label}格式验证失败")

    @staticmethod
    def validate_enum_option(
        db_session: Session,
        report_type: str,
        field_name: str,
        value: str
    ) -> bool:
        """
        验证枚举选项是否有效

        Args:
            db_session: 数据库会话
            report_type: 报告类型
            field_name: 字段名
            value: 值

        Returns:
            是否有效
        """
        try:
            field = FieldManager.get_field_by_name(
                db_session,
                report_type,
                field_name
            )

            if not field or field.get('field_type') != 'ENUM':
                return True  # 非枚举字段

            validation_rule = field.get('validation_rule') or {}
            options = validation_rule.get('options', [])

            return value in options

        except:
            return False
