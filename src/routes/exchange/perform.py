from decimal import Decimal

from flask import jsonify, request

from models.exchange_models import Branch, Currency
from services.auth_service import (
    check_business_lock_for_transactions,
    has_permission,
    token_required,
)
from services.balance_service import BalanceService
from services.db_service import DatabaseService
from services.unified_log_service import log_exchange_transaction
from utils.language_utils import get_current_language
from utils.multilingual_log_service import multilingual_logger

from . import exchange_bp, logger


@exchange_bp.route('/perform', methods=['POST'])
@token_required
@has_permission('transaction_execute')
@check_business_lock_for_transactions
def perform_exchange(*args):
    """执行货币兑换操作"""
    current_user = args[0] if args else None
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401

    session = DatabaseService.get_session()

    try:
        data = request.get_json()

        # 验证必要字段
        required_fields = ['currency_id', 'type', 'amount', 'customer_name', 'exchange_rate']
        for field in required_fields:
            if field not in data:
                raise ValueError(f'缺少必要字段: {field}')

        # 获取当前汇率
        currency = session.query(Currency).filter_by(id=data['currency_id']).first()
        if not currency:
            raise ValueError('币种不存在')

        # 获取网点信息和本币ID
        branch = session.query(Branch).filter_by(id=current_user['branch_id']).first()
        if not branch or not branch.base_currency_id:
            raise ValueError('网点信息不完整或未设置本币')

        base_currency_id = branch.base_currency_id

        # 直接使用前端发送的金额（已经包含正负号）
        foreign_amount_change = Decimal(str(data['amount']))  # 外币变动金额（前端已处理正负号）
        base_amount_change = Decimal(str(data['local_amount']))  # 本币变动金额（前端已处理正负号）

        # ⭐ AMLO审核金额验证：检查客户是否有已审核的预约记录
        customer_id = data.get('customer_id', '')
        if customer_id:
            try:
                from sqlalchemy import text

                # 查询最近的已审核预约记录
                reservation_query = text("""
                    SELECT
                        id,
                        reservation_no,
                        report_type,
                        status,
                        local_amount,
                        audit_notes
                    FROM Reserved_Transaction
                    WHERE customer_id = :customer_id
                      AND status = 'approved'
                    ORDER BY created_at DESC
                    LIMIT 1
                """)

                reservation = session.execute(reservation_query, {'customer_id': customer_id}).fetchone()

                if reservation:
                    approved_amount = Decimal(str(reservation[4])) if reservation[4] else Decimal('0')
                    actual_amount = abs(base_amount_change)  # 使用本币金额（绝对值）

                    # 检查实际金额是否超过审核金额
                    if actual_amount > approved_amount:
                        session.rollback()
                        logger.warning(
                            f"交易金额({actual_amount})超过审核金额({approved_amount})，"
                            f"客户: {customer_id}, 预约单号: {reservation[1]}"
                        )
                        return jsonify({
                            'success': False,
                            'message': f'交易金额({float(actual_amount):,.2f})超过审核金额({float(approved_amount):,.2f})，请重新提交审核或降低交易金额',
                            'error_type': 'amount_exceeded',
                            'approved_amount': float(approved_amount),
                            'actual_amount': float(actual_amount),
                            'reservation_id': reservation[0],
                            'reservation_no': reservation[1],
                            'report_type': reservation[2]
                        }), 403

                    # 记录验证成功日志
                    logger.info(
                        f"AMLO审核金额验证通过: 实际金额({actual_amount}) <= 审核金额({approved_amount}), "
                        f"客户: {customer_id}, 预约单号: {reservation[1]}"
                    )

            except Exception as validation_error:
                logger.error(f"AMLO审核金额验证失败: {str(validation_error)}")
                # 验证失败不应阻止交易，只记录错误
                import traceback
                traceback.print_exc()

        # 更新外币余额（加行锁）
        foreign_balance_before, foreign_balance_after = BalanceService.update_currency_balance(
            session=session,
            currency_id=data['currency_id'],
            branch_id=current_user['branch_id'],
            amount=foreign_amount_change,
            lock_for_update=True
        )

        # 更新本币余额（加行锁）
        base_balance_before, base_balance_after = BalanceService.update_currency_balance(
            session=session,
            currency_id=base_currency_id,
            branch_id=current_user['branch_id'],
            amount=base_amount_change,
            lock_for_update=True
        )

        # 创建交易记录（保持原来的设计：一笔交易一条记录）
        transaction = BalanceService.create_exchange_transaction(
            session=session,
            branch_id=current_user['branch_id'],
            currency_id=data['currency_id'],
            transaction_type=data['type'],
            amount=foreign_amount_change,  # 外币变动金额（带正负号）
            rate=Decimal(str(data['exchange_rate'])),
            local_amount=base_amount_change,  # 本币变动金额（带正负号）
            customer_name=data['customer_name'],
            customer_id=data.get('customer_id', ''),
            operator_id=current_user['id'],
            balance_before=foreign_balance_before,
            balance_after=foreign_balance_after,
            purpose=data.get('purpose', ''),
            remarks=data.get('remarks', '')
        )

        # 记录系统日志（多语言）
        multilingual_logger.log_exchange_transaction(
            operator_id=current_user['id'],
            branch_id=current_user['branch_id'],
            currency_code=currency.currency_code,
            amount=float(foreign_amount_change),
            transaction_type='购入' if data['type'] == 'buy' else '售出',
            customer_name=data['customer_name'],
            ip_address=request.remote_addr,
            language='zh-CN'
        )

        # 提交事务
        session.commit()

        # ⭐ 合规检查: 检查AMLO和BOT报告触发条件（使用统一的RuleEngine）
        compliance_results = {
            'amlo': {'triggered': False, 'reports': []},
            'bot': {'triggered': False, 'reports': []}
        }

        # 1️⃣ 检查AMLO报告触发条件
        try:
            from services.amlo_trigger_service import AMLOTriggerService

            amlo_results = AMLOTriggerService.check_and_create_amlo_records(
                session=session,
                transaction=transaction,
                currency=currency,
                branch_id=current_user['branch_id'],
                operator_id=current_user['id']
            )

            # 如果创建了AMLO记录，记录结果并提交
            if any(amlo_results.values()):
                session.commit()
                logger.info(
                    "AMLO记录创建结果: CTR(101)=%s, ATR(102)=%s, STR(103)=%s",
                    amlo_results['amlo_101_created'],
                    amlo_results['amlo_102_created'],
                    amlo_results['amlo_103_created'],
                )
                compliance_results['amlo']['triggered'] = True
                if amlo_results['amlo_101_created']:
                    compliance_results['amlo']['reports'].append('AMLO-1-01')
                if amlo_results['amlo_102_created']:
                    compliance_results['amlo']['reports'].append('AMLO-1-02')
                if amlo_results['amlo_103_created']:
                    compliance_results['amlo']['reports'].append('AMLO-1-03')
        except Exception as amlo_error:
            # AMLO触发失败不应影响主交易流程，只记录错误
            logger.error(f"AMLO触发检查失败: {str(amlo_error)}")
            import traceback
            traceback.print_exc()

        # 2️⃣ 检查BOT报告触发条件
        try:
            from services.bot_trigger_service import BOTTriggerService

            bot_results = BOTTriggerService.check_and_create_bot_records(
                session=session,
                transaction=transaction,
                currency=currency,
                branch_id=current_user['branch_id'],
                operator_id=current_user['id']
            )

            # 如果创建了BOT记录，记录结果并提交
            if any(bot_results.values()):
                session.commit()
                logger.info(
                    "BOT记录创建结果: BuyFX=%s, SellFX=%s, FCD=%s",
                    bot_results['bot_buyfx_created'],
                    bot_results['bot_sellfx_created'],
                    bot_results['bot_fcd_created'],
                )
                compliance_results['bot']['triggered'] = True
                if bot_results['bot_buyfx_created']:
                    compliance_results['bot']['reports'].append('BOT_BuyFX')
                if bot_results['bot_sellfx_created']:
                    compliance_results['bot']['reports'].append('BOT_SellFX')
                if bot_results['bot_fcd_created']:
                    compliance_results['bot']['reports'].append('BOT_FCD')
        except Exception as bot_error:
            # BOT触发失败不应影响主交易流程，只记录错误
            logger.error(f"BOT触发检查失败: {str(bot_error)}")
            import traceback
            traceback.print_exc()

        # 记录兑换交易日志
        try:
            current_language = get_current_language()
            log_exchange_transaction(
                operator_id=current_user['id'],
                branch_id=current_user['branch_id'],
                currency_code=currency.currency_code,
                amount=float(data['amount']),
                transaction_type=transaction.type,
                customer_name=data['customer_name'],
                transaction_no=transaction.transaction_no,
                rate=float(transaction.rate),
                ip_address=request.remote_addr,
                language=current_language
            )
        except Exception as log_error:
            # 日志记录失败不应该影响交易流程
            logger.warning(f"兑换交易日志记录失败: {log_error}")

        # ⭐ 更新预约状态为completed（如果有已审核的预约记录）
        if customer_id:
            try:
                update_query = text("""
                    UPDATE Reserved_Transaction
                    SET status = 'completed',
                        actual_transaction_id = :transaction_id,
                        completed_at = NOW()
                    WHERE customer_id = :customer_id
                      AND status = 'approved'
                      AND id = (
                          SELECT id FROM (
                              SELECT id FROM Reserved_Transaction
                              WHERE customer_id = :customer_id
                                AND status = 'approved'
                              ORDER BY created_at DESC
                              LIMIT 1
                          ) AS subquery
                      )
                """)

                result = session.execute(update_query, {
                    'transaction_id': transaction.id,
                    'customer_id': customer_id
                })

                if result.rowcount > 0:
                    session.commit()
                    logger.info(
                        f"预约记录状态已更新为completed: 客户={customer_id}, "
                        f"交易ID={transaction.id}, 交易单号={transaction.transaction_no}"
                    )
                else:
                    logger.info(f"无需更新预约状态: 客户={customer_id}没有approved状态的预约记录")
            except Exception as update_error:
                logger.error(f"更新预约状态失败: {str(update_error)}")
                # 更新失败不应影响交易流程，只记录错误
                import traceback
                traceback.print_exc()

        return jsonify({
            'success': True,
            'message': '交易成功',
            'transaction': {
                'id': transaction.id,
                'transaction_no': transaction.transaction_no,
                'transaction_date': transaction.transaction_date.isoformat() if transaction.transaction_date else None,
                'transaction_time': transaction.transaction_time,
                'amount': float(foreign_amount_change),
                'local_amount': float(base_amount_change),
                'foreign_balance_before': float(foreign_balance_before),
                'foreign_balance_after': float(foreign_balance_after),
                'base_balance_before': float(base_balance_before),
                'base_balance_after': float(base_balance_after),
                'customer_name': transaction.customer_name,
                'customer_id': transaction.customer_id,
                'purpose': transaction.purpose,
                'remarks': transaction.remarks,
                'type': transaction.type,
                'rate': float(transaction.rate)
            },
            'compliance': compliance_results  # 新增：返回合规检查结果
        })
    except Exception as exc:
        logger.error(f"Exchange transaction failed: {str(exc)}")
        session.rollback()
        return jsonify({'success': False, 'message': str(exc)}), 500
    finally:
        DatabaseService.close_session(session)
