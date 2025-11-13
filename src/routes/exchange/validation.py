from datetime import date, datetime

from flask import jsonify, request
from sqlalchemy import and_

from models.exchange_models import Branch, Currency, CurrencyBalance, ExchangeRate
from services.auth_service import has_permission, token_required
from services.db_service import DatabaseService
from utils.backend_i18n import get_request_language, t

from . import exchange_bp, logger


@exchange_bp.route('/validate', methods=['POST'])
@token_required
@has_permission('transaction_execute')
def validate_exchange(*args):
    """验证兑换操作的可行性"""
    current_user = args[0] if args else None
    if not current_user:
        language = get_request_language(request)
        return jsonify({'success': False, 'message': t('auth.user_info_failed', language)}), 401

    data = request.json
    logger.info("🔍 验证API收到请求: %s", data)
    logger.info("🔍 当前用户: %s", current_user)

    if not data or not all(k in data for k in ['type', 'currency_id', 'amount']):
        logger.error("❌ 缺少必要参数: %s", data)
        language = get_request_language(request)
        return jsonify({'success': False, 'message': t('validation.missing_required_params', language)}), 400

    session = DatabaseService.get_session()
    try:
        # 获取当前汇率
        today = date.today()
        currency_with_rate = session.query(Currency, ExchangeRate).join(
            ExchangeRate,
            and_(
                Currency.id == ExchangeRate.currency_id,
                ExchangeRate.branch_id == current_user['branch_id'],
                ExchangeRate.rate_date == today
            )
        ).filter(Currency.id == data['currency_id']).first()

        if not currency_with_rate:
            language = get_request_language(request)
            return jsonify({'success': False, 'message': t('validation.currency_no_rate', language)}), 404

        currency, exchange_rate = currency_with_rate

        # 获取外币余额记录
        balance = session.query(CurrencyBalance).filter_by(
            branch_id=current_user['branch_id'],
            currency_id=data['currency_id']
        ).first()

        # 如果外币余额记录不存在，根据交易类型决定处理方式
        if not balance:
            if data['type'] == 'buy':
                # 买入外币时，如果没有余额记录，创建一个初始余额为0的记录
                balance = CurrencyBalance(
                    branch_id=current_user['branch_id'],
                    currency_id=data['currency_id'],
                    balance=0.0,
                    updated_at=datetime.now()
                )
                session.add(balance)
                session.flush()  # 确保可以获取到这个新记录
                logger.info("🔍 创建新的外币余额记录，初始余额为0")
            else:
                # 卖出外币时，必须有余额记录
                language = get_request_language(request)
                return jsonify({'success': False, 'message': t('validation.no_balance_record', language)}), 400

        amount = float(data['amount'])
        exchange_type = data['type']  # 'buy' or 'sell'

        # 检查余额是否充足
        logger.info("🔍 开始检查余额 - exchange_type: %s, amount: %s", exchange_type, amount)

        if exchange_type == 'buy':
            logger.info("🔍 买入外币模式 - 需要检查本币余额")
            try:
                # 网点买入外币时，需要支付本币给客户，应该检查本币余额
                # 计算需要支付的本币金额
                local_amount_needed = amount * float(exchange_rate.buy_rate)
                logger.info("🔍 计算本币需求: %s * %s = %s", amount, float(exchange_rate.buy_rate), local_amount_needed)

                # 获取网点信息以确定本币ID
                branch = session.query(Branch).filter_by(id=current_user['branch_id']).first()
                logger.info("🔍 查询网点信息: %s", branch)

                if not branch or not branch.base_currency_id:
                    logger.error("❌ 网点信息不完整: branch=%s, base_currency_id=%s", branch, branch.base_currency_id if branch else None)
                    language = get_request_language(request)
                    return jsonify({
                        'success': False,
                        'message': t('validation.branch_info_incomplete', language)
                    }), 400

                logger.info("🔍 本币ID: %s", branch.base_currency_id)

                # 获取本币余额
                base_currency_balance = session.query(CurrencyBalance).filter_by(
                    branch_id=current_user['branch_id'],
                    currency_id=branch.base_currency_id
                ).first()

                logger.info("🔍 本币余额记录: %s", base_currency_balance)

                if not base_currency_balance:
                    logger.error("❌ 本币余额记录不存在")
                    language = get_request_language(request)
                    return jsonify({
                        'success': False,
                        'message': t('validation.base_currency_balance_not_exist', language),
                        'available_amount': 0
                    }), 400

                logger.info("🔍 当前本币余额: %s, 需要: %s", base_currency_balance.balance, local_amount_needed)

                if float(base_currency_balance.balance) < local_amount_needed:
                    # 获取本币信息以显示准确的货币名称
                    base_currency = session.query(Currency).filter_by(id=branch.base_currency_id).first()
                    base_currency_name = base_currency.currency_name if base_currency else '本币'
                    base_currency_code = base_currency.currency_code if base_currency else ''

                    current_balance = float(base_currency_balance.balance)
                    shortfall = local_amount_needed - current_balance

                    logger.info("🔍 详细计算:")
                    logger.info("🔍 - 需要金额: %s", local_amount_needed)
                    logger.info("🔍 - 当前余额: %s", current_balance)
                    logger.info("🔍 - 计算差额: %s - %s = %s", local_amount_needed, current_balance, shortfall)

                    # 使用后端国际化系统
                    language = get_request_language(request)
                    error_msg = t('balance.foreign_currency_insufficient', language,
                                  currency_name=base_currency_name,
                                  required_amount=local_amount_needed,
                                  currency_code=base_currency_code,
                                  current_balance=current_balance,
                                  shortfall=shortfall)

                    logger.info("❌ 本币余额不足: %s", error_msg)

                    return jsonify({
                        'success': False,
                        'message': error_msg,
                        'available_amount': current_balance,
                        'required_amount': local_amount_needed,
                        'shortfall': shortfall
                    }), 400
                logger.info("✅ 本币余额充足")

            except Exception as exc:
                logger.error("❌ 检查本币余额时出错: %s", str(exc))
                language = get_request_language(request)
                return jsonify({
                    'success': False,
                    'message': t('balance.balance_check_error', language, error=str(exc))
                }), 500

        else:
            logger.info("🔍 卖出外币模式 - 需要检查外币库存")
            # 网点卖出外币时，检查外币库存是否充足
            if float(balance.balance) < amount:
                # 使用后端国际化系统
                language = get_request_language(request)
                error_msg = t('balance.foreign_stock_insufficient', language,
                              currency_name=currency.currency_name,
                              required_amount=amount,
                              currency_code=currency.currency_code,
                              current_stock=float(balance.balance),
                              missing_amount=amount - float(balance.balance))
                logger.info("❌ 外币库存不足: %s", error_msg)

                return jsonify({
                    'success': False,
                    'message': error_msg,
                    'available_amount': float(balance.balance)
                }), 400
            logger.info("✅ 外币库存充足")

        # ⭐ 新增：检查AMLO/BOT触发条件
        amlo_triggered = False
        bot_triggered = False
        trigger_details = {}
        has_approved_reservation = False
        reservation_info = None

        try:
            from services.repform.rule_engine import RuleEngine
            from decimal import Decimal

            # 构建检查数据
            customer_id = data.get('customer_id', '')
            customer_name = data.get('customer_name', '')

            # 计算交易金额（本币）
            if exchange_type == 'buy':
                transaction_amount_thb = amount * float(exchange_rate.buy_rate)
            else:
                transaction_amount_thb = amount * float(exchange_rate.sell_rate)

            # ⭐⭐⭐ 重点1：先检查是否有已审核通过的预约
            if customer_id:
                logger.info(f"🔍 检查客户 {customer_id} 是否有已审核通过的预约")

                reservation_query = text("""
                    SELECT id, reservation_no, report_type, status, local_amount,
                           audit_notes, created_at, audited_at
                    FROM reserved_transaction
                    WHERE customer_id = :customer_id
                      AND status = 'approved'
                    ORDER BY created_at DESC
                    LIMIT 1
                """)

                reservation_result = session.execute(
                    reservation_query,
                    {'customer_id': customer_id}
                ).fetchone()

                if reservation_result:
                    has_approved_reservation = True
                    approved_amount = float(reservation_result[4])  # local_amount

                    reservation_info = {
                        'id': reservation_result[0],
                        'reservation_no': reservation_result[1],
                        'report_type': reservation_result[2],
                        'status': reservation_result[3],
                        'approved_amount': approved_amount,
                        'audit_notes': reservation_result[5],
                        'created_at': str(reservation_result[6]),
                        'audited_at': str(reservation_result[7]) if reservation_result[7] else None
                    }

                    logger.info(f"✅ 找到已审核通过的预约: {reservation_info['reservation_no']}, 审核金额: {approved_amount}")

                    # 检查当前交易金额是否在审核金额范围内
                    if transaction_amount_thb <= approved_amount:
                        logger.info(f"✅ 交易金额 {transaction_amount_thb} <= 审核金额 {approved_amount}，允许交易，无需重新触发AMLO")
                        # 直接允许交易，不触发AMLO检查
                        language = get_request_language(request)
                        response_data = {
                            'success': True,
                            'message': t('validation.validation_passed', language),
                            'buy_rate': float(exchange_rate.buy_rate),
                            'sell_rate': float(exchange_rate.sell_rate),
                            'available_amount': float(balance.balance),
                            'amlo_triggered': False,
                            'bot_triggered': False,
                            'triggered': False,
                            'has_approved_reservation': True,
                            'reservation_info': reservation_info
                        }
                        return jsonify(response_data)
                    else:
                        logger.warning(f"⚠️ 交易金额 {transaction_amount_thb} > 审核金额 {approved_amount}，需要阻止交易")
                        # 金额超过审核额度，阻止交易
                        language = get_request_language(request)
                        return jsonify({
                            'success': False,
                            'message': t('validation.amount_exceeds_approved', language),
                            'error_type': 'amount_exceeded',
                            'approved_amount': approved_amount,
                            'actual_amount': transaction_amount_thb,
                            'exceed_amount': transaction_amount_thb - approved_amount,
                            'reservation_info': reservation_info
                        }), 403
                else:
                    logger.info(f"ℹ️ 客户 {customer_id} 没有已审核通过的预约，需要检查是否触发AMLO")

            # ⭐⭐⭐ 重点2：如果没有已审核预约，才检查AMLO触发条件
            check_data = {
                'customer_id': customer_id,
                'customer_name': customer_name,
                'transaction_type': 'exchange',
                'direction': exchange_type,
                'currency_code': currency.currency_code,
                'amount': Decimal(str(amount)),
                'transaction_amount_thb': Decimal(str(transaction_amount_thb)),
                'total_amount': Decimal(str(transaction_amount_thb)),
                'payment_method': data.get('payment_method', 'cash'),
                'branch_id': current_user['branch_id']
            }

            logger.info("🔍 检查AMLO触发条件，数据: %s", check_data)

            # 检查AMLO-1-01触发
            amlo_result = RuleEngine.check_triggers(
                db_session=session,
                report_type='AMLO-1-01',
                data=check_data,
                branch_id=current_user['branch_id']
            )

            if amlo_result.get('triggered'):
                amlo_triggered = True
                trigger_details['amlo'] = {
                    'report_type': 'AMLO-1-01',
                    'triggered': True,
                    'allow_continue': amlo_result.get('allow_continue', False),
                    'message_cn': amlo_result.get('message_cn', ''),
                    'message_en': amlo_result.get('message_en', ''),
                    'message_th': amlo_result.get('message_th', ''),
                    'trigger_rules': amlo_result.get('trigger_rules', [])
                }
                logger.info("✅ AMLO-1-01 触发!")
            else:
                logger.info("ℹ️ AMLO-1-01 未触发")

            # TODO: 检查BOT触发条件（如需要）
            # bot_result = check_bot_triggers(...)

        except Exception as trigger_error:
            # 触发检查失败不应阻止库存验证，只记录警告
            logger.warning(f"⚠️ AMLO/BOT触发检查失败: {str(trigger_error)}")
            import traceback
            traceback.print_exc()

        # 返回验证结果和当前汇率
        language = get_request_language(request)
        response_data = {
            'success': True,
            'message': t('validation.validation_passed', language),
            'buy_rate': float(exchange_rate.buy_rate),
            'sell_rate': float(exchange_rate.sell_rate),
            'available_amount': float(balance.balance),
            # ⭐ 新增：返回触发状态
            'amlo_triggered': amlo_triggered,
            'bot_triggered': bot_triggered,
            'trigger_details': trigger_details
        }

        if amlo_triggered or bot_triggered:
            response_data['triggered'] = True
            logger.info("⚠️ 触发AMLO/BOT规则，返回triggered=True")
        else:
            response_data['triggered'] = False
            logger.info("✅ 未触发AMLO/BOT规则，返回triggered=False")

        return jsonify(response_data)

    except Exception as exc:
        logger.error("Exchange validation failed: %s", str(exc))
        language = get_request_language(request)
        return jsonify({'success': False, 'message': t('system.system_error', language, error=str(exc))}), 500
    finally:
        DatabaseService.close_session(session)
