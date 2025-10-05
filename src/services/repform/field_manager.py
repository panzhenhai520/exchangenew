# -*- coding: utf-8 -*-
"""
FieldManager - 字段管理服务
负责管理report_fields表的CRUD操作和字段查询
版本: v1.0
创建日期: 2025-10-02
"""

import json
from typing import List, Dict, Optional, Any
from sqlalchemy import text
from sqlalchemy.orm import Session


class FieldManager:
    """字段管理服务类"""

    @staticmethod
    def get_fields_by_report_type(
        db_session: Session,
        report_type: str,
        language: str = 'zh',
        is_active: bool = True
    ) -> List[Dict[str, Any]]:
        """
        获取指定报告类型的字段定义

        Args:
            db_session: 数据库会话
            report_type: 报告类型 (AMLO-1-01, AMLO-1-02, AMLO-1-03, BOT_BuyFX, etc.)
            language: 语言 ('zh', 'en', 'th')
            is_active: 是否只查询启用的字段

        Returns:
            字段列表，按fill_order排序
        """
        try:
            # 构建SQL查询
            sql = text("""
                SELECT
                    id,
                    field_name,
                    field_type,
                    field_length,
                    field_precision,
                    field_scale,
                    CASE :language
                        WHEN 'zh' THEN field_cn_name
                        WHEN 'en' THEN field_en_name
                        WHEN 'th' THEN field_th_name
                        ELSE field_cn_name
                    END as label,
                    field_cn_name,
                    field_en_name,
                    field_th_name,
                    fill_order,
                    is_required,
                    default_value,
                    validation_rule,
                    CASE :language
                        WHEN 'zh' THEN placeholder_cn
                        WHEN 'en' THEN placeholder_en
                        WHEN 'th' THEN placeholder_th
                        ELSE placeholder_cn
                    END as placeholder,
                    CASE :language
                        WHEN 'zh' THEN help_text_cn
                        WHEN 'en' THEN help_text_en
                        WHEN 'th' THEN help_text_th
                        ELSE help_text_cn
                    END as help_text,
                    field_group,
                    report_type,
                    is_active
                FROM report_fields
                WHERE report_type = :report_type
                    AND (:is_active = FALSE OR is_active = TRUE)
                ORDER BY fill_order ASC
            """)

            result = db_session.execute(
                sql,
                {
                    'report_type': report_type,
                    'language': language,
                    'is_active': is_active
                }
            )

            fields = []
            for row in result:
                field_dict = dict(row._mapping)

                # 解析validation_rule (JSON字符串转字典)
                if field_dict.get('validation_rule'):
                    try:
                        field_dict['validation_rule'] = json.loads(field_dict['validation_rule'])
                    except:
                        field_dict['validation_rule'] = {}

                fields.append(field_dict)

            return fields

        except Exception as e:
            print(f"Error getting fields for report type {report_type}: {str(e)}")
            raise

    @staticmethod
    def get_form_definition(
        db_session: Session,
        report_type: str,
        language: str = 'zh'
    ) -> Dict[str, Any]:
        """
        获取表单定义（分组、排序后的字段）

        Args:
            db_session: 数据库会话
            report_type: 报告类型
            language: 语言

        Returns:
            表单定义字典，包含field_groups等信息
        """
        try:
            # 获取所有字段
            fields = FieldManager.get_fields_by_report_type(
                db_session,
                report_type,
                language
            )

            if not fields:
                return {
                    'report_type': report_type,
                    'report_name': '',
                    'field_groups': []
                }

            # 获取报告名称（使用第一个字段的report_type作为参考）
            report_names = {
                'AMLO-1-01': {
                    'zh': '现金交易报告',
                    'en': 'Cash Transaction Report',
                    'th': 'รายงานธุรกรรมเงินสด'
                },
                'AMLO-1-02': {
                    'zh': '资产交易报告',
                    'en': 'Asset Transaction Report',
                    'th': 'รายงานธุรกรรมทรัพย์สิน'
                },
                'AMLO-1-03': {
                    'zh': '可疑交易报告',
                    'en': 'Suspicious Transaction Report',
                    'th': 'รายงานธุรกรรมที่น่าสงสัย'
                },
                'BOT_BuyFX': {
                    'zh': '买入外币报告',
                    'en': 'Buy Foreign Currency Report',
                    'th': 'รายงานการซื้อเงินตราต่างประเทศ'
                },
                'BOT_SellFX': {
                    'zh': '卖出外币报告',
                    'en': 'Sell Foreign Currency Report',
                    'th': 'รายงานการขายเงินตราต่างประเทศ'
                },
                'BOT_Provider': {
                    'zh': '外币提供方信息',
                    'en': 'Foreign Currency Provider Information',
                    'th': 'ข้อมูลผู้ให้บริการเงินตราต่างประเทศ'
                },
                'BOT_FCD': {
                    'zh': 'FCD账户交易报告',
                    'en': 'FCD Account Transaction Report',
                    'th': 'รายงานธุรกรรมบัญชี FCD'
                }
            }

            report_name = report_names.get(report_type, {}).get(language, report_type)

            # 按field_group分组
            grouped_fields = {}
            for field in fields:
                group_name = field.get('field_group', '其他')
                if group_name not in grouped_fields:
                    grouped_fields[group_name] = []
                grouped_fields[group_name].append(field)

            # 构建field_groups列表
            field_groups = []
            for group_name, group_fields in grouped_fields.items():
                field_groups.append({
                    'group_name': group_name,
                    'fields': group_fields
                })

            return {
                'report_type': report_type,
                'report_name_cn': report_names.get(report_type, {}).get('zh', ''),
                'report_name_en': report_names.get(report_type, {}).get('en', ''),
                'report_name_th': report_names.get(report_type, {}).get('th', ''),
                'report_name': report_name,
                'field_groups': field_groups,
                'total_fields': len(fields)
            }

        except Exception as e:
            print(f"Error getting form definition for {report_type}: {str(e)}")
            raise

    @staticmethod
    def get_field_by_name(
        db_session: Session,
        report_type: str,
        field_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        根据字段名获取字段定义

        Args:
            db_session: 数据库会话
            report_type: 报告类型
            field_name: 字段名

        Returns:
            字段定义字典，如果不存在返回None
        """
        try:
            sql = text("""
                SELECT *
                FROM report_fields
                WHERE report_type = :report_type
                    AND field_name = :field_name
                    AND is_active = TRUE
                LIMIT 1
            """)

            result = db_session.execute(
                sql,
                {'report_type': report_type, 'field_name': field_name}
            )

            row = result.first()
            if row:
                field_dict = dict(row._mapping)

                # 解析validation_rule
                if field_dict.get('validation_rule'):
                    try:
                        field_dict['validation_rule'] = json.loads(field_dict['validation_rule'])
                    except:
                        field_dict['validation_rule'] = {}

                return field_dict

            return None

        except Exception as e:
            print(f"Error getting field {field_name} for report type {report_type}: {str(e)}")
            raise

    @staticmethod
    def get_required_fields(
        db_session: Session,
        report_type: str
    ) -> List[str]:
        """
        获取必填字段名称列表

        Args:
            db_session: 数据库会话
            report_type: 报告类型

        Returns:
            必填字段名称列表
        """
        try:
            sql = text("""
                SELECT field_name
                FROM report_fields
                WHERE report_type = :report_type
                    AND is_required = TRUE
                    AND is_active = TRUE
                ORDER BY fill_order ASC
            """)

            result = db_session.execute(sql, {'report_type': report_type})

            return [row[0] for row in result]

        except Exception as e:
            print(f"Error getting required fields for {report_type}: {str(e)}")
            raise

    @staticmethod
    def get_all_report_types(db_session: Session) -> List[Dict[str, Any]]:
        """
        获取所有报告类型列表

        Args:
            db_session: 数据库会话

        Returns:
            报告类型列表，包含统计信息
        """
        try:
            sql = text("""
                SELECT
                    report_type,
                    COUNT(*) as field_count,
                    SUM(CASE WHEN is_required = TRUE THEN 1 ELSE 0 END) as required_count
                FROM report_fields
                WHERE is_active = TRUE
                GROUP BY report_type
                ORDER BY report_type
            """)

            result = db_session.execute(sql)

            report_names = {
                'AMLO-1-01': '现金交易报告',
                'AMLO-1-02': '资产交易报告',
                'AMLO-1-03': '可疑交易报告',
                'BOT_BuyFX': '买入外币报告',
                'BOT_SellFX': '卖出外币报告',
                'BOT_Provider': '外币提供方信息',
                'BOT_FCD': 'FCD账户交易报告'
            }

            report_types = []
            for row in result:
                report_types.append({
                    'report_type': row[0],
                    'report_name': report_names.get(row[0], row[0]),
                    'field_count': row[1],
                    'required_count': row[2]
                })

            return report_types

        except Exception as e:
            print(f"Error getting all report types: {str(e)}")
            raise
