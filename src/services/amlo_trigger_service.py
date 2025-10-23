# -*- coding: utf-8 -*-
"""
AMLO报告触发服务
在交易完成后自动判断是否需要生成AMLO记录
版本: v2.0 - 重构使用统一的RuleEngine
创建日期: 2025-10-08
最后更新: 2025-10-21
"""

from sqlalchemy import text
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List
import logging

# 导入统一的规则引擎
from services.repform.rule_engine import RuleEngine

logger = logging.getLogger(__name__)


class AMLOTriggerService:
    """AMLO报告触发服务"""

    @classmethod
    def check_and_create_amlo_records(
        cls,
        session: Session,
        transaction: Any,
        currency: Any,
        branch_id: int,
        operator_id: int
    ) -> Dict[str, bool]:
        """
        检查交易是否需要创建AMLO记录（使用统一的RuleEngine）

        Args:
            session: 数据库会话
            transaction: 交易记录对象
            currency: 货币对象
            branch_id: 网点ID
            operator_id: 操作员ID

        Returns:
            {
                'amlo_101_created': True/False,  # CTR
                'amlo_102_created': True/False,  # ATR
                'amlo_103_created': True/False   # STR
            }
        """
        results = {
            'amlo_101_created': False,
            'amlo_102_created': False,
            'amlo_103_created': False
        }

        try:
            # 准备交易数据用于规则匹配
            transaction_data = cls._prepare_transaction_data(
                session, transaction, currency
            )

            logger.info(f"检查AMLO触发条件 - 交易: {transaction.transaction_no}")

            # 使用RuleEngine检查各个AMLO报告类型的触发条件
            report_types = ['AMLO-1-01', 'AMLO-1-02', 'AMLO-1-03']

            for report_type in report_types:
                try:
                    # 调用统一的规则引擎
                    trigger_result = RuleEngine.check_triggers(
                        db_session=session,
                        report_type=report_type,
                        data=transaction_data,
                        branch_id=branch_id
                    )

                    if trigger_result['triggered']:
                        logger.info(f"触发 {report_type} - 规则: {trigger_result['highest_priority_rule']['rule_name']}")

                        # 根据报告类型创建相应的AMLO记录
                        if report_type == 'AMLO-1-01' and not results['amlo_101_created']:
                            cls._create_amlo_101_record(
                                session, transaction, currency,
                                branch_id, operator_id, transaction_data['total_amount']
                            )
                            results['amlo_101_created'] = True
                            logger.info(f"✓ 已创建AMLO-1-01 (CTR) 记录")

                        elif report_type == 'AMLO-1-02' and not results['amlo_102_created']:
                            cls._create_amlo_102_record(
                                session, transaction, currency,
                                branch_id, operator_id, transaction_data['total_amount']
                            )
                            results['amlo_102_created'] = True
                            logger.info(f"✓ 已创建AMLO-1-02 (ATR) 记录")

                        elif report_type == 'AMLO-1-03' and not results['amlo_103_created']:
                            cls._create_amlo_103_record(
                                session, transaction, currency,
                                branch_id, operator_id, transaction_data['total_amount']
                            )
                            results['amlo_103_created'] = True
                            logger.info(f"✓ 已创建AMLO-1-03 (STR) 记录")

                except Exception as rule_error:
                    logger.error(f"检查 {report_type} 触发失败: {str(rule_error)}")
                    import traceback
                    traceback.print_exc()
                    continue

            # 标记原始交易记录
            if any(results.values()):
                cls._mark_transaction_amlo_flag(session, transaction, results)

            return results

        except Exception as e:
            logger.error(f"AMLO记录创建失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return results

    @classmethod
    def _prepare_transaction_data(
        cls,
        session: Session,
        transaction: Any,
        currency: Any
    ) -> Dict[str, Any]:
        """
        准备交易数据用于规则评估

        Args:
            session: 数据库会话
            transaction: 交易记录对象
            currency: 货币对象

        Returns:
            格式化的交易数据字典
        """
        # 基础交易数据
        data = {
            'total_amount': abs(float(transaction.local_amount)),  # AMLO使用本币金额
            'amount': abs(float(transaction.amount)),  # 外币金额
            'currency_code': currency.currency_code,
            'transaction_type': transaction.type,
            'direction': transaction.type,  # 兼容字段
            'payment_method': getattr(transaction, 'payment_method', 'cash'),
            'customer_country_code': getattr(transaction, 'customer_country_code', 'TH'),
            'transaction_date': transaction.transaction_date,
            'customer_id': transaction.customer_id or '',
            'customer_name': transaction.customer_name or '',
        }

        # 如果有客户ID，获取客户累计交易统计
        if transaction.customer_id:
            try:
                customer_stats = RuleEngine.get_customer_stats(
                    session,
                    transaction.customer_id,
                    days=30
                )
                # 添加客户统计字段，供累计金额规则使用
                data['cumulative_amount_30d'] = float(customer_stats.get('cumulative_amount_30d', 0))
                data['transaction_count_30d'] = customer_stats.get('transaction_count_30d', 0)
            except Exception as e:
                logger.warning(f"获取客户统计失败: {str(e)}")
                data['cumulative_amount_30d'] = 0
                data['transaction_count_30d'] = 0

        return data


    @classmethod
    def _create_amlo_101_record(
        cls,
        session: Session,
        transaction: Any,
        currency: Any,
        branch_id: int,
        operator_id: int,
        thb_amount: float
    ):
        """创建AMLO-1-01 (CTR - 现金交易报告) 记录"""
        sql = text("""
            INSERT INTO amlo_reports (
                reservation_no, report_type, transaction_id,
                customer_name, customer_id_number, customer_country_code,
                transaction_date, transaction_amount, currency_code,
                thb_amount, branch_id, operator_id,
                is_reported, created_at
            ) VALUES (
                :reservation_no, 'AMLO-1-01', :transaction_id,
                :customer_name, :customer_id_number, :customer_country_code,
                :transaction_date, :transaction_amount, :currency_code,
                :thb_amount, :branch_id, :operator_id,
                0, NOW()
            )
        """)

        session.execute(sql, {
            'reservation_no': f'AMLO-{transaction.transaction_no}',
            'transaction_id': transaction.id,
            'customer_name': transaction.customer_name or '',
            'customer_id_number': transaction.customer_id or '',
            'customer_country_code': getattr(transaction, 'customer_country_code', 'TH'),
            'transaction_date': transaction.transaction_date,
            'transaction_amount': abs(float(transaction.amount)),
            'currency_code': currency.currency_code,
            'thb_amount': thb_amount,
            'branch_id': branch_id,
            'operator_id': operator_id
        })

    @classmethod
    def _create_amlo_102_record(
        cls,
        session: Session,
        transaction: Any,
        currency: Any,
        branch_id: int,
        operator_id: int,
        thb_amount: float
    ):
        """创建AMLO-1-02 (ATR - 累计交易报告) 记录"""
        sql = text("""
            INSERT INTO amlo_reports (
                reservation_no, report_type, transaction_id,
                customer_name, customer_id_number, customer_country_code,
                transaction_date, transaction_amount, currency_code,
                thb_amount, branch_id, operator_id,
                is_reported, created_at
            ) VALUES (
                :reservation_no, 'AMLO-1-02', :transaction_id,
                :customer_name, :customer_id_number, :customer_country_code,
                :transaction_date, :transaction_amount, :currency_code,
                :thb_amount, :branch_id, :operator_id,
                0, NOW()
            )
        """)

        session.execute(sql, {
            'reservation_no': f'AMLO-{transaction.transaction_no}',
            'transaction_id': transaction.id,
            'customer_name': transaction.customer_name or '',
            'customer_id_number': transaction.customer_id or '',
            'customer_country_code': getattr(transaction, 'customer_country_code', 'TH'),
            'transaction_date': transaction.transaction_date,
            'transaction_amount': abs(float(transaction.amount)),
            'currency_code': currency.currency_code,
            'thb_amount': thb_amount,
            'branch_id': branch_id,
            'operator_id': operator_id
        })

    @classmethod
    def _create_amlo_103_record(
        cls,
        session: Session,
        transaction: Any,
        currency: Any,
        branch_id: int,
        operator_id: int,
        thb_amount: float
    ):
        """创建AMLO-1-03 (STR - 可疑交易报告) 记录"""
        sql = text("""
            INSERT INTO amlo_reports (
                reservation_no, report_type, transaction_id,
                customer_name, customer_id_number, customer_country_code,
                transaction_date, transaction_amount, currency_code,
                thb_amount, branch_id, operator_id,
                is_reported, suspicious_reason, created_at
            ) VALUES (
                :reservation_no, 'AMLO-1-03', :transaction_id,
                :customer_name, :customer_id_number, :customer_country_code,
                :transaction_date, :transaction_amount, :currency_code,
                :thb_amount, :branch_id, :operator_id,
                0, :suspicious_reason, NOW()
            )
        """)

        session.execute(sql, {
            'reservation_no': f'AMLO-{transaction.transaction_no}',
            'transaction_id': transaction.id,
            'customer_name': transaction.customer_name or '',
            'customer_id_number': transaction.customer_id or '',
            'customer_country_code': getattr(transaction, 'customer_country_code', 'TH'),
            'transaction_date': transaction.transaction_date,
            'transaction_amount': abs(float(transaction.amount)),
            'currency_code': currency.currency_code,
            'thb_amount': thb_amount,
            'branch_id': branch_id,
            'operator_id': operator_id,
            'suspicious_reason': '自动触发：符合可疑交易规则'
        })

    @classmethod
    def _mark_transaction_amlo_flag(
        cls,
        session: Session,
        transaction: Any,
        results: Dict[str, bool]
    ):
        """标记交易记录的AMLO标志"""
        amlo_flag = 1 if any(results.values()) else 0

        sql = text("""
            UPDATE exchange_transactions
            SET amlo_flag = :amlo_flag
            WHERE id = :transaction_id
        """)

        session.execute(sql, {
            'amlo_flag': amlo_flag,
            'transaction_id': transaction.id
        })
