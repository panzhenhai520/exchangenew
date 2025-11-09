# -*- coding: utf-8 -*-
"""
BOT报告自动生成服务
负责根据触发条件自动生成BOT相关报告
版本: v1.0
创建日期: 2025-10-08
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class BOTReportService:
    """BOT报告自动生成服务类"""

    @staticmethod
    def generate_bot_buyfx(
        db_session: Session,
        transaction_id: int,
        transaction_data: Dict[str, Any]
    ) -> Optional[int]:
        """
        生成BOT买入外币报告

        Args:
            db_session: 数据库会话
            transaction_id: 交易ID
            transaction_data: 交易数据
                - transaction_no: 交易流水号
                - customer_id: 客户证件号
                - customer_name: 客户姓名
                - currency_code: 货币代码
                - currency_name: 货币名称
                - foreign_amount: 外币金额
                - local_amount: 本币金额
                - exchange_rate: 汇率
                - transaction_time: 交易时间
                - exchange_type: 兑换类型
                - funding_source: 资金来源
                - branch_id: 网点ID
                - operator_id: 操作员ID

        Returns:
            报告ID，失败返回None
        """
        try:
            # 准备报告数据
            report_data = {
                'transaction_no': transaction_data.get('transaction_no'),
                'customer_id': transaction_data.get('customer_id'),
                'customer_name': transaction_data.get('customer_name'),
                'currency_code': transaction_data.get('currency_code'),
                'currency_name': transaction_data.get('currency_name'),
                'foreign_amount': transaction_data.get('foreign_amount'),
                'local_amount': transaction_data.get('local_amount'),
                'exchange_rate': transaction_data.get('exchange_rate'),
                'transaction_time': transaction_data.get('transaction_time'),
                'exchange_type': transaction_data.get('exchange_type'),
                'funding_source': transaction_data.get('funding_source')
            }

            # 插入BOT_BuyFX表
            sql = text("""
                INSERT INTO BOT_BuyFX (
                    transaction_id,
                    transaction_no,
                    customer_id,
                    customer_name,
                    currency_code,
                    currency_name,
                    foreign_amount,
                    local_amount_thb,
                    exchange_rate,
                    transaction_date,
                    exchange_type,
                    funding_source,
                    json_data,
                    branch_id,
                    operator_id,
                    is_reported,
                    created_at
                ) VALUES (
                    :transaction_id,
                    :transaction_no,
                    :customer_id,
                    :customer_name,
                    :currency_code,
                    :currency_name,
                    :foreign_amount,
                    :local_amount,
                    :exchange_rate,
                    :transaction_date,
                    :exchange_type,
                    :funding_source,
                    :json_data,
                    :branch_id,
                    :operator_id,
                    FALSE,
                    NOW()
                )
            """)

            params = {
                'transaction_id': transaction_id,
                'transaction_no': report_data['transaction_no'],
                'customer_id': report_data['customer_id'],
                'customer_name': report_data['customer_name'],
                'currency_code': report_data['currency_code'],
                'currency_name': report_data['currency_name'],
                'foreign_amount': report_data['foreign_amount'],
                'local_amount': report_data['local_amount'],
                'exchange_rate': report_data['exchange_rate'],
                'transaction_date': report_data['transaction_time'],
                'exchange_type': report_data['exchange_type'],
                'funding_source': report_data['funding_source'],
                'json_data': json.dumps(report_data, ensure_ascii=False),
                'branch_id': transaction_data.get('branch_id'),
                'operator_id': transaction_data.get('operator_id')
            }

            result = db_session.execute(sql, params)
            db_session.commit()

            report_id = result.lastrowid
            logger.info(f"成功生成BOT_BuyFX报告，报告ID: {report_id}, 交易ID: {transaction_id}")
            return report_id

        except Exception as e:
            db_session.rollback()
            logger.error(f"生成BOT_BuyFX报告失败: {str(e)}, 交易ID: {transaction_id}")
            return None

    @staticmethod
    def generate_bot_sellfx(
        db_session: Session,
        transaction_id: int,
        transaction_data: Dict[str, Any]
    ) -> Optional[int]:
        """
        生成BOT卖出外币报告

        Args:
            db_session: 数据库会话
            transaction_id: 交易ID
            transaction_data: 交易数据（同generate_bot_buyfx）

        Returns:
            报告ID，失败返回None
        """
        try:
            # 准备报告数据
            report_data = {
                'transaction_no': transaction_data.get('transaction_no'),
                'customer_id': transaction_data.get('customer_id'),
                'customer_name': transaction_data.get('customer_name'),
                'currency_code': transaction_data.get('currency_code'),
                'currency_name': transaction_data.get('currency_name'),
                'foreign_amount': transaction_data.get('foreign_amount'),
                'local_amount': transaction_data.get('local_amount'),
                'exchange_rate': transaction_data.get('exchange_rate'),
                'transaction_time': transaction_data.get('transaction_time'),
                'exchange_type': transaction_data.get('exchange_type')
            }

            # 插入BOT_SellFX表
            sql = text("""
                INSERT INTO BOT_SellFX (
                    transaction_id,
                    transaction_no,
                    customer_id,
                    customer_name,
                    currency_code,
                    currency_name,
                    foreign_amount,
                    local_amount_thb,
                    exchange_rate,
                    transaction_date,
                    exchange_type,
                    json_data,
                    branch_id,
                    operator_id,
                    is_reported,
                    created_at
                ) VALUES (
                    :transaction_id,
                    :transaction_no,
                    :customer_id,
                    :customer_name,
                    :currency_code,
                    :currency_name,
                    :foreign_amount,
                    :local_amount,
                    :exchange_rate,
                    :transaction_date,
                    :exchange_type,
                    :json_data,
                    :branch_id,
                    :operator_id,
                    FALSE,
                    NOW()
                )
            """)

            params = {
                'transaction_id': transaction_id,
                'transaction_no': report_data['transaction_no'],
                'customer_id': report_data['customer_id'],
                'customer_name': report_data['customer_name'],
                'currency_code': report_data['currency_code'],
                'currency_name': report_data['currency_name'],
                'foreign_amount': report_data['foreign_amount'],
                'local_amount': report_data['local_amount'],
                'exchange_rate': report_data['exchange_rate'],
                'transaction_date': report_data['transaction_time'],
                'exchange_type': report_data['exchange_type'],
                'json_data': json.dumps(report_data, ensure_ascii=False),
                'branch_id': transaction_data.get('branch_id'),
                'operator_id': transaction_data.get('operator_id')
            }

            result = db_session.execute(sql, params)
            db_session.commit()

            report_id = result.lastrowid
            logger.info(f"成功生成BOT_SellFX报告，报告ID: {report_id}, 交易ID: {transaction_id}")
            return report_id

        except Exception as e:
            db_session.rollback()
            logger.error(f"生成BOT_SellFX报告失败: {str(e)}, 交易ID: {transaction_id}")
            return None

    @staticmethod
    def generate_bot_fcd(
        db_session: Session,
        transaction_id: int,
        transaction_data: Dict[str, Any]
    ) -> Optional[int]:
        """
        生成BOT FCD账户报告

        Args:
            db_session: 数据库会话
            transaction_id: 交易ID
            transaction_data: 交易数据（包含FCD账户信息）

        Returns:
            报告ID，失败返回None
        """
        try:
            # 准备报告数据
            report_data = {
                'transaction_no': transaction_data.get('transaction_no'),
                'customer_id': transaction_data.get('customer_id'),
                'customer_name': transaction_data.get('customer_name'),
                'currency_code': transaction_data.get('currency_code'),
                'currency_name': transaction_data.get('currency_name'),
                'foreign_amount': transaction_data.get('foreign_amount'),
                'local_amount': transaction_data.get('local_amount'),
                'exchange_rate': transaction_data.get('exchange_rate'),
                'transaction_time': transaction_data.get('transaction_time'),
                'direction': transaction_data.get('direction'),
                'use_fcd': True
            }

            # 插入BOT_FCD表
            sql = text("""
                INSERT INTO BOT_FCD (
                    transaction_id,
                    transaction_no,
                    customer_id,
                    customer_name,
                    currency_code,
                    currency_name,
                    foreign_amount,
                    local_amount_thb,
                    exchange_rate,
                    transaction_date,
                    transaction_direction,
                    json_data,
                    branch_id,
                    operator_id,
                    is_reported,
                    created_at
                ) VALUES (
                    :transaction_id,
                    :transaction_no,
                    :customer_id,
                    :customer_name,
                    :currency_code,
                    :currency_name,
                    :foreign_amount,
                    :local_amount,
                    :exchange_rate,
                    :transaction_date,
                    :direction,
                    :json_data,
                    :branch_id,
                    :operator_id,
                    FALSE,
                    NOW()
                )
            """)

            params = {
                'transaction_id': transaction_id,
                'transaction_no': report_data['transaction_no'],
                'customer_id': report_data['customer_id'],
                'customer_name': report_data['customer_name'],
                'currency_code': report_data['currency_code'],
                'currency_name': report_data['currency_name'],
                'foreign_amount': report_data['foreign_amount'],
                'local_amount': report_data['local_amount'],
                'exchange_rate': report_data['exchange_rate'],
                'transaction_date': report_data['transaction_time'],
                'direction': report_data['direction'],
                'json_data': json.dumps(report_data, ensure_ascii=False),
                'branch_id': transaction_data.get('branch_id'),
                'operator_id': transaction_data.get('operator_id')
            }

            result = db_session.execute(sql, params)
            db_session.commit()

            report_id = result.lastrowid
            logger.info(f"成功生成BOT_FCD报告，报告ID: {report_id}, 交易ID: {transaction_id}")
            return report_id

        except Exception as e:
            db_session.rollback()
            logger.error(f"生成BOT_FCD报告失败: {str(e)}, 交易ID: {transaction_id}")
            return None

    @staticmethod
    def generate_bot_provider(
        db_session: Session,
        adjustment_id: int,
        adjustment_data: Dict[str, Any]
    ) -> Optional[int]:
        """
        生成BOT Provider报告（余额调节触发）

        Args:
            db_session: 数据库会话
            adjustment_id: 余额调节ID
            adjustment_data: 调节数据
                - currency_code: 货币代码
                - currency_name: 货币名称
                - adjustment_amount: 调节金额
                - local_amount: 本币金额
                - reason: 调节原因
                - branch_id: 网点ID
                - operator_id: 操作员ID

        Returns:
            报告ID，失败返回None
        """
        try:
            # 准备报告数据
            report_data = {
                'currency_code': adjustment_data.get('currency_code'),
                'currency_name': adjustment_data.get('currency_name'),
                'adjustment_amount': adjustment_data.get('adjustment_amount'),
                'local_amount': adjustment_data.get('local_amount'),
                'reason': adjustment_data.get('reason'),
                'adjustment_time': adjustment_data.get('adjustment_time', datetime.now())
            }

            # 插入BOT_Provider表
            sql = text("""
                INSERT INTO BOT_Provider (
                    adjustment_id,
                    currency_code,
                    currency_name,
                    provider_amount,
                    local_amount_thb,
                    adjustment_reason,
                    adjustment_date,
                    json_data,
                    branch_id,
                    operator_id,
                    is_reported,
                    created_at
                ) VALUES (
                    :adjustment_id,
                    :currency_code,
                    :currency_name,
                    :provider_amount,
                    :local_amount,
                    :reason,
                    :adjustment_date,
                    :json_data,
                    :branch_id,
                    :operator_id,
                    FALSE,
                    NOW()
                )
            """)

            params = {
                'adjustment_id': adjustment_id,
                'currency_code': report_data['currency_code'],
                'currency_name': report_data['currency_name'],
                'provider_amount': report_data['adjustment_amount'],
                'local_amount': report_data['local_amount'],
                'reason': report_data['reason'],
                'adjustment_date': report_data['adjustment_time'],
                'json_data': json.dumps(report_data, ensure_ascii=False),
                'branch_id': adjustment_data.get('branch_id'),
                'operator_id': adjustment_data.get('operator_id')
            }

            result = db_session.execute(sql, params)
            db_session.commit()

            report_id = result.lastrowid
            logger.info(f"成功生成BOT_Provider报告，报告ID: {report_id}, 调节ID: {adjustment_id}")
            return report_id

        except Exception as e:
            db_session.rollback()
            logger.error(f"生成BOT_Provider报告失败: {str(e)}, 调节ID: {adjustment_id}")
            return None

    @staticmethod
    def auto_generate_bot_reports(
        db_session: Session,
        transaction_id: int,
        transaction_data: Dict[str, Any],
        bot_flag: int = 0,
        fcd_flag: int = 0,
        bot_report_type: Optional[str] = None,
        fcd_report_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        自动生成BOT报告（根据标记）

        Args:
            db_session: 数据库会话
            transaction_id: 交易ID
            transaction_data: 交易数据
            bot_flag: BOT标记 (0或1)
            fcd_flag: FCD标记 (0或1)
            bot_report_type: BOT报告类型 (BOT_BuyFX/BOT_SellFX)
            fcd_report_type: FCD报告类型 (BOT_FCD)

        Returns:
            生成结果字典
            {
                'bot_report_generated': True/False,
                'bot_report_id': 报告ID或None,
                'fcd_report_generated': True/False,
                'fcd_report_id': 报告ID或None
            }
        """
        result = {
            'bot_report_generated': False,
            'bot_report_id': None,
            'fcd_report_generated': False,
            'fcd_report_id': None
        }

        try:
            # 1. 生成BOT买入/卖出报告
            if bot_flag == 1 and bot_report_type:
                if bot_report_type == 'BOT_BuyFX':
                    report_id = BOTReportService.generate_bot_buyfx(
                        db_session,
                        transaction_id,
                        transaction_data
                    )
                    if report_id:
                        result['bot_report_generated'] = True
                        result['bot_report_id'] = report_id

                elif bot_report_type == 'BOT_SellFX':
                    report_id = BOTReportService.generate_bot_sellfx(
                        db_session,
                        transaction_id,
                        transaction_data
                    )
                    if report_id:
                        result['bot_report_generated'] = True
                        result['bot_report_id'] = report_id

            # 2. 生成FCD报告
            if fcd_flag == 1 and fcd_report_type == 'BOT_FCD':
                report_id = BOTReportService.generate_bot_fcd(
                    db_session,
                    transaction_id,
                    transaction_data
                )
                if report_id:
                    result['fcd_report_generated'] = True
                    result['fcd_report_id'] = report_id

            return result

        except Exception as e:
            logger.error(f"自动生成BOT报告失败: {str(e)}")
            return result
