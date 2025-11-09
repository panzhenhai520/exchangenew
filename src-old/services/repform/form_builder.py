# -*- coding: utf-8 -*-
"""
FormBuilder - 表单构建器
负责根据字段定义动态构建前端表单Schema
版本: v1.0
创建日期: 2025-10-02
"""

import json
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from .field_manager import FieldManager


class FormBuilder:
    """表单构建器类"""

    @staticmethod
    def build_form_schema(
        db_session: Session,
        report_type: str,
        language: str = 'zh',
        initial_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        构建表单Schema（JSON格式，供前端渲染）

        Args:
            db_session: 数据库会话
            report_type: 报告类型
            language: 语言
            initial_data: 初始数据（用于预填充表单）

        Returns:
            表单Schema字典，包含字段定义、验证规则、分组等
        """
        try:
            # 获取表单定义
            form_def = FieldManager.get_form_definition(
                db_session,
                report_type,
                language
            )

            # 构建表单项
            form_items = []
            validation_rules = {}

            for group in form_def.get('field_groups', []):
                group_items = []

                for field in group.get('fields', []):
                    field_name = field.get('field_name')
                    field_type = field.get('field_type')

                    # 构建表单项
                    form_item = {
                        'name': field_name,
                        'label': field.get('label', ''),
                        'type': FormBuilder._map_field_type(field_type),
                        'required': field.get('is_required', False),
                        'placeholder': field.get('placeholder', ''),
                        'help_text': field.get('help_text', ''),
                        'default_value': field.get('default_value'),
                        'group': group.get('group_name', '')
                    }

                    # 添加字段类型特定的属性
                    if field_type == 'ENUM':
                        validation_rule = field.get('validation_rule', {})
                        options = validation_rule.get('options', [])
                        form_item['options'] = FormBuilder._build_enum_options(
                            options,
                            language
                        )

                    elif field_type == 'VARCHAR' or field_type == 'TEXT':
                        validation_rule = field.get('validation_rule', {})
                        form_item['min_length'] = validation_rule.get('min_length')
                        form_item['max_length'] = validation_rule.get('max_length') or field.get('field_length')
                        form_item['pattern'] = validation_rule.get('pattern')

                    elif field_type == 'DECIMAL':
                        form_item['precision'] = field.get('field_precision', 15)
                        form_item['scale'] = field.get('field_scale', 2)
                        validation_rule = field.get('validation_rule', {})
                        form_item['min'] = validation_rule.get('min', 0)
                        form_item['max'] = validation_rule.get('max')

                    elif field_type == 'INT':
                        validation_rule = field.get('validation_rule', {})
                        form_item['min'] = validation_rule.get('min')
                        form_item['max'] = validation_rule.get('max')

                    # 预填充初始值
                    if initial_data and field_name in initial_data:
                        form_item['value'] = initial_data[field_name]

                    group_items.append(form_item)

                    # 构建验证规则
                    if field.get('is_required'):
                        validation_rules[field_name] = validation_rules.get(field_name, [])
                        validation_rules[field_name].append({
                            'required': True,
                            'message': f"请输入{field.get('label', field_name)}"
                        })

                    # 添加其他验证规则
                    validation_rule = field.get('validation_rule', {})
                    if validation_rule:
                        FormBuilder._add_validation_rules(
                            validation_rules,
                            field_name,
                            field.get('label', field_name),
                            field_type,
                            validation_rule
                        )

                # 添加分组项
                if group_items:
                    form_items.append({
                        'group_name': group.get('group_name', ''),
                        'items': group_items
                    })

            return {
                'report_type': report_type,
                'report_name': form_def.get('report_name', ''),
                'language': language,
                'form_items': form_items,
                'validation_rules': validation_rules,
                'total_fields': form_def.get('total_fields', 0)
            }

        except Exception as e:
            print(f"Error building form schema for {report_type}: {str(e)}")
            raise

    @staticmethod
    def _map_field_type(field_type: str) -> str:
        """
        将数据库字段类型映射为前端表单控件类型

        Args:
            field_type: 数据库字段类型

        Returns:
            前端控件类型
        """
        type_mapping = {
            'VARCHAR': 'input',
            'TEXT': 'textarea',
            'INT': 'number',
            'DECIMAL': 'number',
            'DATE': 'date',
            'DATETIME': 'datetime',
            'BOOLEAN': 'checkbox',
            'ENUM': 'select'
        }

        return type_mapping.get(field_type, 'input')

    @staticmethod
    def _build_enum_options(
        options: List[str],
        language: str = 'zh'
    ) -> List[Dict[str, str]]:
        """
        构建枚举选项列表

        Args:
            options: 选项值列表
            language: 语言

        Returns:
            选项字典列表，格式: [{"value": "...", "label": "..."}]
        """
        # 预定义的枚举翻译
        translations = {
            'self': {'zh': '本人办理', 'en': 'Self', 'th': 'ด้วยตนเอง'},
            'agent': {'zh': '代理办理', 'en': 'Agent', 'th': 'ตัวแทน'},
            'national_id': {'zh': '身份证', 'en': 'National ID', 'th': 'บัตรประชาชน'},
            'passport': {'zh': '护照', 'en': 'Passport', 'th': 'หนังสือเดินทาง'},
            'foreigner_cert': {'zh': '外国人证件', 'en': 'Foreigner Certificate', 'th': 'ใบสำคัญคนต่างด้าว'},
            'other': {'zh': '其他', 'en': 'Other', 'th': 'อื่นๆ'},
            'mortgage': {'zh': '抵押', 'en': 'Mortgage', 'th': 'จำนอง'},
            'sale': {'zh': '出售转让', 'en': 'Sale', 'th': 'ขาย'},
            'transfer': {'zh': '转账', 'en': 'Transfer', 'th': 'โอน'},
            'land': {'zh': '土地', 'en': 'Land', 'th': 'ที่ดิน'},
            'land_building': {'zh': '土地和建筑物', 'en': 'Land and Building', 'th': 'ที่ดินและอาคาร'},
            'building': {'zh': '建筑物', 'en': 'Building', 'th': 'อาคาร'}
        }

        enum_options = []
        for option_value in options:
            label = translations.get(option_value, {}).get(language, option_value)
            enum_options.append({
                'value': option_value,
                'label': label
            })

        return enum_options

    @staticmethod
    def _add_validation_rules(
        validation_rules: Dict[str, List],
        field_name: str,
        field_label: str,
        field_type: str,
        rule_config: Dict[str, Any]
    ):
        """
        添加验证规则

        Args:
            validation_rules: 验证规则字典
            field_name: 字段名
            field_label: 字段标签
            field_type: 字段类型
            rule_config: 规则配置
        """
        if field_name not in validation_rules:
            validation_rules[field_name] = []

        # 最小长度
        if 'min_length' in rule_config:
            validation_rules[field_name].append({
                'min': rule_config['min_length'],
                'message': f"{field_label}最少{rule_config['min_length']}个字符"
            })

        # 最大长度
        if 'max_length' in rule_config:
            validation_rules[field_name].append({
                'max': rule_config['max_length'],
                'message': f"{field_label}最多{rule_config['max_length']}个字符"
            })

        # 正则表达式
        if 'pattern' in rule_config:
            validation_rules[field_name].append({
                'pattern': rule_config['pattern'],
                'message': f"{field_label}格式不正确"
            })

        # 数值范围
        if field_type in ['INT', 'DECIMAL']:
            if 'min' in rule_config:
                validation_rules[field_name].append({
                    'type': 'number',
                    'min': rule_config['min'],
                    'message': f"{field_label}不能小于{rule_config['min']}"
                })

            if 'max' in rule_config:
                validation_rules[field_name].append({
                    'type': 'number',
                    'max': rule_config['max'],
                    'message': f"{field_label}不能大于{rule_config['max']}"
                })

    @staticmethod
    def prefill_from_transaction(
        transaction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        从交易数据预填充表单数据

        Args:
            transaction_data: 交易数据

        Returns:
            预填充的表单数据
        """
        # 字段映射（交易字段 -> 报告字段）
        field_mapping = {
            'customer_name': 'customer_name',
            'customer_id': 'id_number',
            'customer_address': 'customer_address',
            'customer_phone': 'customer_phone',
            'customer_occupation': 'customer_occupation',
            'customer_workplace': 'customer_workplace',
            'customer_work_phone': 'customer_work_phone',
            'local_amount': 'total_amount',
            'currency_code': 'buy_currency_code',
            'amount': 'buy_currency_amount',
            'purpose': 'transaction_purpose',
            'transaction_date': 'transaction_date'
        }

        prefilled_data = {}
        for trans_field, report_field in field_mapping.items():
            if trans_field in transaction_data:
                prefilled_data[report_field] = transaction_data[trans_field]

        # 设置默认值
        prefilled_data['transaction_method'] = 'self'
        prefilled_data['buy_foreign_currency'] = True

        return prefilled_data
