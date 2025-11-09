# -*- coding: utf-8 -*-
"""
BOT报告触发服务
在交易完成后自动判断是否需要生成BOT记录
版本: v2.0 - 重构使用统一的RuleEngine
创建日期: 2025-10-08
最后更新: 2025-10-21
"""

from sqlalchemy import text
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime
from typing import Dict, Any, Optional
import logging

# 导入统一的规则引擎
from services.repform.rule_engine import RuleEngine

logger = logging.getLogger(__name__)


class BOTTriggerService:
    """BOT报告触发服务 - 使用动态规则评估"""

    # 默认触发阈值配置 (当没有配置规则时使用)
    DEFAULT_THRESHOLDS = {
        'buy_fx_usd_equivalent': Decimal('20000'),   # Buy FX触发阈值 (USD等值)
        'sell_fx_usd_equivalent': Decimal('20000'),  # Sell FX触发阈值
        'fcd_usd_equivalent': Decimal('50000'),      # FCD触发阈值
        'provider_usd_equivalent': Decimal('20000')  # Provider触发阈值
    }

    @classmethod
    def check_and_create_bot_records(
        cls,
        session: Session,
        transaction: Any,
        currency: Any,
        branch_id: int,
        operator_id: int
    ) -> Dict[str, bool]:
        """
        检查交易是否需要创建BOT记录（使用统一的RuleEngine）

        Args:
            session: 数据库会话
            transaction: 交易记录对象
            currency: 货币对象
            branch_id: 网点ID
            operator_id: 操作员ID

        Returns:
            {
                'bot_buyfx_created': True/False,
                'bot_sellfx_created': True/False,
                'bot_fcd_created': True/False
            }
        """
        results = {
            'bot_buyfx_created': False,
            'bot_sellfx_created': False,
            'bot_fcd_created': False
        }

        try:
            # 计算USD等值金额
            usd_equivalent = cls._calculate_usd_equivalent(
                session=session,
                amount=abs(Decimal(str(transaction.amount))),
                currency_code=currency.currency_code,
                exchange_rate=Decimal(str(transaction.rate))
            )

            logger.info(f"检查BOT触发条件 - 交易: {transaction.transaction_no}, USD等值: ${usd_equivalent:,.2f}")

            # 准备交易数据用于规则匹配
            transaction_data = cls._prepare_transaction_data(
                session, transaction, currency, usd_equivalent
            )

            # 使用RuleEngine检查各个BOT报告类型的触发条件
            report_types = ['BOT_BuyFX', 'BOT_SellFX', 'BOT_FCD']

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

                        # 根据报告类型创建相应的BOT记录
                        if report_type == 'BOT_BuyFX' and not results['bot_buyfx_created']:
                            cls._create_bot_buyfx_record(
                                session, transaction, currency,
                                branch_id, operator_id, usd_equivalent
                            )
                            results['bot_buyfx_created'] = True
                            logger.info(f"✓ 已创建BOT_BuyFX记录")

                        elif report_type == 'BOT_SellFX' and not results['bot_sellfx_created']:
                            cls._create_bot_sellfx_record(
                                session, transaction, currency,
                                branch_id, operator_id, usd_equivalent
                            )
                            results['bot_sellfx_created'] = True
                            logger.info(f"✓ 已创建BOT_SellFX记录")

                        elif report_type == 'BOT_FCD' and not results['bot_fcd_created']:
                            direction = 'buy' if transaction.type == 'buy' else 'sell'
                            cls._create_bot_fcd_record(
                                session, transaction, currency,
                                branch_id, operator_id, usd_equivalent, direction
                            )
                            results['bot_fcd_created'] = True
                            logger.info(f"✓ 已创建BOT_FCD记录")

                except Exception as rule_error:
                    logger.error(f"检查 {report_type} 触发失败: {str(rule_error)}")
                    import traceback
                    traceback.print_exc()
                    continue

            # 标记原始交易记录
            if any(results.values()):
                cls._mark_transaction_bot_flags(session, transaction, results)

            return results

        except Exception as e:
            logger.error(f"BOT记录创建失败: {str(e)}")
            import traceback
            traceback.print_exc()
            # 不抛出异常，避免影响主交易流程
            return results

    @classmethod
    def _prepare_transaction_data(
        cls,
        session: Session,
        transaction: Any,
        currency: Any,
        usd_equivalent: Decimal
    ) -> Dict[str, Any]:
        """
        准备交易数据用于规则评估

        Args:
            session: 数据库会话
            transaction: 交易记录对象
            currency: 货币对象
            usd_equivalent: USD等值金额

        Returns:
            格式化的交易数据字典
        """
        # 判断是否使用FCD账户
        payment_foreign_flag = getattr(transaction, 'payment_is_foreign_account', False)
        if isinstance(payment_foreign_flag, str):
            payment_foreign_flag = payment_foreign_flag.strip().lower() in ('1', 'true', 'yes', 'y')
        elif isinstance(payment_foreign_flag, (int, float)):
            payment_foreign_flag = payment_foreign_flag != 0
        elif not isinstance(payment_foreign_flag, bool):
            payment_foreign_flag = False

        use_fcd = bool(getattr(transaction, 'use_fcd', False)) or payment_foreign_flag

        # 基础交易数据
        data = {
            'amount': abs(float(transaction.amount)),  # 外币金额
            'local_amount': abs(float(transaction.local_amount)),  # 本币金额
            'total_amount': abs(float(transaction.local_amount)),  # 兼容AMLO字段
            'usd_equivalent': float(usd_equivalent),  # USD等值
            'verification_amount': float(usd_equivalent),  # 兼容AMLO字段
            'currency_code': currency.currency_code,
            'transaction_type': transaction.type,
            'direction': transaction.type,  # 兼容字段
            'payment_method': getattr(transaction, 'payment_method', 'cash'),
            'use_fcd': use_fcd,
            'customer_country_code': getattr(transaction, 'customer_country_code', 'TH'),
            'transaction_date': transaction.transaction_date,
            'customer_id': transaction.customer_id or '',
            'customer_name': transaction.customer_name or '',
        }

        return data

    @classmethod
    def _calculate_usd_equivalent(
        cls,
        session: Session,
        amount: Decimal,
        currency_code: str,
        exchange_rate: Decimal
    ) -> Decimal:
        """
        计算USD等值金额

        Args:
            session: 数据库会话
            amount: 外币金额
            currency_code: 货币代码
            exchange_rate: 当前交易汇率

        Returns:
            USD等值金额
        """
        if currency_code == 'USD':
            return amount

        try:
            # 查询当前USD对THB汇率
            sql = text("""
                SELECT buy_rate
                FROM exchange_rates er
                JOIN currencies c ON er.currency_id = c.id
                WHERE c.currency_code = 'USD'
                AND er.rate_date = CURDATE()
                ORDER BY er.created_at DESC
                LIMIT 1
            """)

            usd_rate_result = session.execute(sql).fetchone()

            if not usd_rate_result:
                # 如果没有当天USD汇率，使用默认值35
                usd_rate = Decimal('35.0')
                logger.warning(f"未找到USD汇率，使用默认值: {usd_rate}")
            else:
                usd_rate = Decimal(str(usd_rate_result[0]))

            # 计算: 外币金额 * 外币汇率 / USD汇率
            thb_amount = amount * exchange_rate
            usd_equivalent = thb_amount / usd_rate

            logger.debug(f"USD等值计算: {amount} {currency_code} * {exchange_rate} / {usd_rate} = ${usd_equivalent:,.2f}")

            return usd_equivalent

        except Exception as e:
            logger.error(f"USD等值计算失败: {str(e)}")
            return Decimal('0')

    @classmethod
    def _create_bot_buyfx_record(
        cls,
        session: Session,
        transaction: Any,
        currency: Any,
        branch_id: int,
        operator_id: int,
        usd_equivalent: Decimal
    ):
        """创建BOT_BuyFX记录"""
        sql = text("""
            INSERT INTO bot_buyfx (
                transaction_id, transaction_date, transaction_no,
                customer_id_type, customer_id_number, customer_name,
                customer_country_code, buy_currency_code, buy_amount,
                local_amount, exchange_rate, usd_equivalent, remarks,
                branch_id, operator_id, created_at
            ) VALUES (
                :transaction_id, :transaction_date, :transaction_no,
                :customer_id_type, :customer_id_number, :customer_name,
                :customer_country_code, :buy_currency_code, :buy_amount,
                :local_amount, :exchange_rate, :usd_equivalent, :remarks,
                :branch_id, :operator_id, NOW()
            )
        """)

        # 推断证件类型
        customer_id = transaction.customer_id or ''
        customer_id_type = cls._infer_id_type(customer_id)

        session.execute(sql, {
            'transaction_id': transaction.id,
            'transaction_date': transaction.transaction_date,
            'transaction_no': transaction.transaction_no,
            'customer_id_type': customer_id_type,
            'customer_id_number': customer_id,
            'customer_name': transaction.customer_name or '',
            'customer_country_code': getattr(transaction, 'customer_country_code', None) or 'TH',
            'buy_currency_code': currency.currency_code,
            'buy_amount': abs(transaction.amount),
            'local_amount': abs(transaction.local_amount),
            'exchange_rate': transaction.rate,
            'usd_equivalent': usd_equivalent,
            'remarks': transaction.remarks or '',
            'branch_id': branch_id,
            'operator_id': operator_id
        })

    @classmethod
    def _create_bot_sellfx_record(
        cls,
        session: Session,
        transaction: Any,
        currency: Any,
        branch_id: int,
        operator_id: int,
        usd_equivalent: Decimal
    ):
        """创建BOT_SellFX记录"""
        sql = text("""
            INSERT INTO bot_sellfx (
                transaction_id, transaction_date, transaction_no,
                customer_id_type, customer_id_number, customer_name,
                customer_country_code, sell_currency_code, sell_amount,
                local_amount, exchange_rate, usd_equivalent, remarks,
                branch_id, operator_id, created_at
            ) VALUES (
                :transaction_id, :transaction_date, :transaction_no,
                :customer_id_type, :customer_id_number, :customer_name,
                :customer_country_code, :sell_currency_code, :sell_amount,
                :local_amount, :exchange_rate, :usd_equivalent, :remarks,
                :branch_id, :operator_id, NOW()
            )
        """)

        customer_id = transaction.customer_id or ''
        customer_id_type = cls._infer_id_type(customer_id)

        session.execute(sql, {
            'transaction_id': transaction.id,
            'transaction_date': transaction.transaction_date,
            'transaction_no': transaction.transaction_no,
            'customer_id_type': customer_id_type,
            'customer_id_number': customer_id,
            'customer_name': transaction.customer_name or '',
            'customer_country_code': getattr(transaction, 'customer_country_code', None) or 'TH',
            'sell_currency_code': currency.currency_code,
            'sell_amount': abs(transaction.amount),
            'local_amount': abs(transaction.local_amount),
            'exchange_rate': transaction.rate,
            'usd_equivalent': usd_equivalent,
            'remarks': transaction.remarks or '',
            'branch_id': branch_id,
            'operator_id': operator_id
        })

    @classmethod
    def _create_bot_fcd_record(
        cls,
        session: Session,
        transaction: Any,
        currency: Any,
        branch_id: int,
        operator_id: int,
        usd_equivalent: Decimal,
        direction: str
    ):
        """创建BOT_FCD记录"""
        sql = text("""
            INSERT INTO bot_fcd (
                transaction_id, account_open_date, bank_name, account_number,
                currency_code, balance, transaction_amount, usd_equivalent,
                remarks, branch_id, operator_id, fcd_flag, created_at
            ) VALUES (
                :transaction_id, :account_open_date, :bank_name, :account_number,
                :currency_code, :balance, :transaction_amount, :usd_equivalent,
                :remarks, :branch_id, :operator_id, 1, NOW()
            )
        """)

        # 尝试从payment_method_note获取银行信息，否则使用默认值
        bank_name = getattr(transaction, 'payment_method_note', None) or 'FCD Account'
        account_number = transaction.customer_id or f'FCD-{transaction.transaction_no}'

        session.execute(sql, {
            'transaction_id': transaction.id,
            'account_open_date': transaction.transaction_date,
            'bank_name': bank_name,
            'account_number': account_number,
            'currency_code': currency.currency_code,
            'balance': 0,  # 可以后续从FCD余额表查询
            'transaction_amount': abs(transaction.amount),
            'usd_equivalent': usd_equivalent,
            'remarks': f"{direction.upper()} FCD - {transaction.remarks or ''}".strip(),
            'branch_id': branch_id,
            'operator_id': operator_id
        })

    @classmethod
    def _mark_transaction_bot_flags(
        cls,
        session: Session,
        transaction: Any,
        results: Dict[str, bool]
    ):
        """标记交易记录的BOT标志"""
        bot_flag = 1 if (results['bot_buyfx_created'] or results['bot_sellfx_created']) else 0
        fcd_flag = 1 if results['bot_fcd_created'] else 0

        sql = text("""
            UPDATE exchange_transactions
            SET bot_flag = :bot_flag,
                fcd_flag = :fcd_flag
            WHERE id = :transaction_id
        """)

        session.execute(sql, {
            'bot_flag': bot_flag,
            'fcd_flag': fcd_flag,
            'transaction_id': transaction.id
        })

    @classmethod
    def _check_with_default_thresholds(
        cls,
        session: Session,
        transaction: Any,
        currency: Any,
        branch_id: int,
        operator_id: int,
        usd_equivalent: Decimal,
        use_fcd: bool
    ) -> Dict[str, bool]:
        """使用默认阈值判断（向后兼容）"""
        results = {
            'bot_buyfx_created': False,
            'bot_sellfx_created': False,
            'bot_fcd_created': False
        }

        # 检查Buy FX触发
        if transaction.type == 'buy':
            if use_fcd and usd_equivalent >= cls.DEFAULT_THRESHOLDS['fcd_usd_equivalent']:
                cls._create_bot_fcd_record(
                    session, transaction, currency,
                    branch_id, operator_id, usd_equivalent, 'buy'
                )
                results['bot_fcd_created'] = True
                logger.info(f"✓ 已创建BOT_FCD记录 (买入, 金额: ${usd_equivalent:,.2f})")
            elif usd_equivalent >= cls.DEFAULT_THRESHOLDS['buy_fx_usd_equivalent']:
                cls._create_bot_buyfx_record(
                    session, transaction, currency,
                    branch_id, operator_id, usd_equivalent
                )
                results['bot_buyfx_created'] = True
                logger.info(f"✓ 已创建BOT_BuyFX记录 (金额: ${usd_equivalent:,.2f})")

        # 检查Sell FX触发
        elif transaction.type == 'sell':
            if use_fcd and usd_equivalent >= cls.DEFAULT_THRESHOLDS['fcd_usd_equivalent']:
                cls._create_bot_fcd_record(
                    session, transaction, currency,
                    branch_id, operator_id, usd_equivalent, 'sell'
                )
                results['bot_fcd_created'] = True
                logger.info(f"✓ 已创建BOT_FCD记录 (卖出, 金额: ${usd_equivalent:,.2f})")
            elif usd_equivalent >= cls.DEFAULT_THRESHOLDS['sell_fx_usd_equivalent']:
                cls._create_bot_sellfx_record(
                    session, transaction, currency,
                    branch_id, operator_id, usd_equivalent
                )
                results['bot_sellfx_created'] = True
                logger.info(f"✓ 已创建BOT_SellFX记录 (金额: ${usd_equivalent:,.2f})")

        if any(results.values()):
            cls._mark_transaction_bot_flags(session, transaction, results)

        return results


    @staticmethod
    def _to_bool(value: Any) -> bool:
        """转换为布尔值"""
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)

    @staticmethod
    def _infer_id_type(customer_id: str) -> str:
        """
        根据证件号码推断证件类型

        泰国身份证: 13位数字
        护照: 通常6-9位字母+数字组合
        """
        if not customer_id:
            return 'Unknown'

        customer_id = customer_id.strip()

        # 13位纯数字 -> 泰国身份证
        if len(customer_id) == 13 and customer_id.isdigit():
            return 'Thai ID'

        # 包含字母 -> 护照
        if any(c.isalpha() for c in customer_id):
            return 'Passport'

        # 其他情况
        return 'ID Card'
