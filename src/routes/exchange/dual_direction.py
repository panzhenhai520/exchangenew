from flask import jsonify, request

from models.exchange_models import Branch, Currency
from services.auth_service import (
    check_business_lock_for_transactions,
    has_permission,
    token_required,
)
from services.db_service import DatabaseService
from services.transaction_split_service import TransactionSplitService
from utils.backend_i18n import get_request_language, t
from utils.multilingual_log_service import multilingual_logger

from . import exchange_bp, logger


@exchange_bp.route('/validate-dual-direction', methods=['POST'])
@token_required
@has_permission('transaction_execute')
def validate_dual_direction_exchange(*args):
    """验证双向交易的可行性（检查余额充足性等约束条件）"""
    current_user = args[0] if args else None
    if not current_user:
        language = get_request_language(request)
        return jsonify({'success': False, 'message': t('auth.user_info_failed', language)}), 401

    try:
        data = request.get_json()
        logger.info("[validate_dual_direction] 收到验证请求: %s", data)

        # 验证必要字段
        language = get_request_language(request)
        required_fields = ['denomination_data', 'customer_info']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': t('validation.missing_required_field', language, field=field)
                }), 400

        # 验证客户姓名
        if not data['customer_info'].get('name', '').strip():
            return jsonify({'success': False, 'message': t('customer.name_required', language)}), 400

        # 验证面值组合数据
        denomination_data = data['denomination_data']
        if not denomination_data.get('combinations') or len(denomination_data['combinations']) == 0:
            return jsonify({'success': False, 'message': t('transaction.no_combinations_provided', language)}), 400

        session = DatabaseService.get_session()
        try:
            branch = session.query(Branch).filter_by(id=current_user['branch_id']).first()
            if not branch:
                return jsonify({'success': False, 'message': t('validation.branch_not_found', language)}), 400

            if not branch.base_currency_id:
                return jsonify({'success': False, 'message': t('validation.branch_no_base_currency', language)}), 400

            logger.info(
                "[validate_dual_direction] 开始验证，网点ID: %s, 本币ID: %s",
                current_user['branch_id'],
                branch.base_currency_id,
            )

            transaction_groups = TransactionSplitService.analyze_denomination_combinations(
                denomination_data,
                branch.base_currency_id,
                data.get('exchange_mode')  # 传递交易方向
            )

            if not transaction_groups:
                return jsonify({
                    'success': False,
                    'message': t('transaction.no_valid_combinations', language)
                }), 400

            logger.info("[validate_dual_direction] 分析得到 %s 个交易分组", len(transaction_groups))

            virtual_transaction_records = TransactionSplitService.create_transaction_records(
                business_group_id="VALIDATION_TEMP",
                transaction_groups=transaction_groups,
                branch_id=current_user['branch_id'],
                operator_id=current_user['id'],
                customer_info=data['customer_info'],
                purpose_id=data.get('purpose_id')
            )

            logger.info("[validate_dual_direction] 生成 %s 条虚拟交易记录用于验证", len(virtual_transaction_records))

            validation_result = TransactionSplitService.validate_balance_sufficiency(
                session,
                virtual_transaction_records,
                current_user['branch_id'],
                language
            )

            if not validation_result['success']:
                logger.info("[validate_dual_direction] 余额验证失败: %s", validation_result['message'])
                return jsonify({
                    'success': False,
                    'message': validation_result['message']
                }), 400

            logger.info("[validate_dual_direction] 开始检查余额阈值报警")
            threshold_warnings = []

            from services.balance_alert_service import BalanceAlertService

            for record in virtual_transaction_records:
                currency_id = record['currency_id']
                transaction_amount = abs(float(record['amount']))
                transaction_type = 'buy' if record['amount'] > 0 else 'sell'

                try:
                    impact_result = BalanceAlertService.check_transaction_impact(
                        currency_id,
                        current_user['branch_id'],
                        transaction_amount,
                        transaction_type
                    )

                    if impact_result.get('will_trigger_alert', False):
                        new_status = impact_result.get('new_status', {})
                        impact_analysis = impact_result.get('impact_analysis', '')

                        currency = session.query(Currency).filter_by(id=currency_id).first()
                        currency_name = currency.currency_name if currency else t('system.unknown_currency', language)
                        currency_code = currency.currency_code if currency else 'UNKNOWN'

                        warning_msg = t(
                            'balance.threshold_warning',
                            language,
                            currency_name=currency_name,
                            currency_code=currency_code,
                            current_balance=impact_result.get('current_balance', 0),
                            new_balance=impact_result.get('new_balance', 0),
                            impact_analysis=impact_analysis
                        )

                        threshold_warnings.append({
                            'currency_id': currency_id,
                            'currency_code': currency_code,
                            'currency_name': currency_name,
                            'warning_message': warning_msg,
                            'warning_level': new_status.get('level', 'warning'),
                            'current_balance': impact_result.get('current_balance', 0),
                            'new_balance': impact_result.get('new_balance', 0)
                        })

                except Exception as err:
                    try:
                        currency = session.query(Currency).filter_by(id=currency_id).first()
                        currency_code = currency.currency_code if currency else 'UNKNOWN'
                        logger.error("检查币种 %s (ID: %s) 的阈值报警时出错: %s", currency_code, currency_id, str(err))
                    except Exception:
                        logger.error("检查币种 ID %s 的阈值报警时出错: %s", currency_id, str(err))
                    continue

            logger.info("[validate_dual_direction] 检查到 %s 个阈值报警", len(threshold_warnings))
            logger.info("[validate_dual_direction] 验证通过")

            response_data = {
                'success': True,
                'message': t('validation.validation_passed_can_execute', language),
                'validation_details': {
                    'transaction_groups': len(transaction_groups),
                    'total_records': len(virtual_transaction_records),
                    'currencies_involved': len(set(record['currency_id'] for record in virtual_transaction_records))
                }
            }

            if threshold_warnings:
                response_data['threshold_warnings'] = threshold_warnings
                critical_warnings = [w for w in threshold_warnings if w['warning_level'] == 'critical']
                if critical_warnings:
                    response_data['message'] = t('validation.validation_passed_with_critical_warnings', language)
                else:
                    response_data['message'] = t('validation.validation_passed_with_warnings', language)

            return jsonify(response_data)

        finally:
            DatabaseService.close_session(session)

    except Exception as exc:
        logger.error("双向交易验证失败: %s", str(exc))
        language = get_request_language(request)
        return jsonify({
            'success': False,
            'message': t('transaction.validation_error', language) + f': {str(exc)}'
        }), 500


@exchange_bp.route('/perform-dual-direction', methods=['POST'])
@token_required
@has_permission('transaction_execute')
@check_business_lock_for_transactions
def perform_dual_direction_exchange(*args):
    """执行双向交易（支持面值组合的不同买卖方向）"""
    current_user = args[0] if args else None
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401

    try:
        data = request.get_json()

        required_fields = ['denomination_data', 'customer_info']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'缺少必要字段: {field}'}), 400

        session = DatabaseService.get_session()
        try:
            branch = session.query(Branch).filter_by(id=current_user['branch_id']).first()
            if not branch:
                return jsonify({'success': False, 'message': '网点信息不存在'}), 400

            result = TransactionSplitService.execute_split_transaction(
                denomination_data=data['denomination_data'],
                branch_id=current_user['branch_id'],
                base_currency_id=branch.base_currency_id,
                operator_id=current_user['id'],
                customer_info=data['customer_info'],
                purpose_id=data.get('purpose_id'),
                exchange_mode=data.get('exchange_mode')  # 传递交易方向
            )

            if result['success']:
                multilingual_logger.log_system_operation(
                    'dual_direction_transaction',
                    operator_id=current_user['id'],
                    branch_id=current_user['branch_id'],
                    details=(
                        f"双向交易执行成功 - 业务组ID: {result['data']['business_group_id']}, "
                        f"拆分为 {result['data']['transaction_count']} 条交易记录"
                    ),
                    language='zh-CN'
                )

                return jsonify({
                    'success': True,
                    'message': '双向交易执行成功',
                    'data': result['data']
                })

            return jsonify({
                'success': False,
                'message': result['message']
            }), 400

        finally:
            DatabaseService.close_session(session)

    except Exception as exc:
        logger.error("双向交易执行失败: %s", str(exc))
        return jsonify({
            'success': False,
            'message': f'交易执行失败: {str(exc)}'
        }), 500


@exchange_bp.route('/business-group/<business_group_id>', methods=['GET'])
@token_required
@has_permission('transaction_execute')
def get_business_group_transactions(*args, business_group_id):
    """获取业务组的所有交易记录"""
    current_user = args[0] if args else None
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401

    try:
        transactions = TransactionSplitService.get_business_group_transactions(business_group_id)

        return jsonify({
            'success': True,
            'message': '获取业务组交易记录成功',
            'data': {
                'business_group_id': business_group_id,
                'transactions': transactions,
                'transaction_count': len(transactions)
            }
        })

    except Exception as exc:
        logger.error("获取业务组交易记录失败: %s", str(exc))
        return jsonify({
            'success': False,
            'message': f'获取失败: {str(exc)}'
        }), 500


@exchange_bp.route('/business-group/<business_group_id>/reverse', methods=['POST'])
@token_required
@has_permission('transaction_execute')
def reverse_business_group(*args, business_group_id):
    """反结算整个业务组"""
    current_user = args[0] if args else None
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401

    try:
        data = request.get_json()
        reason = data.get('reason', '') if data else ''

        result = TransactionSplitService.reverse_business_group(
            business_group_id=business_group_id,
            operator_id=current_user['id'],
            reason=reason
        )

        if result['success']:
            multilingual_logger.log_system_operation(
                'business_group_reversal',
                operator_id=current_user['id'],
                branch_id=current_user['branch_id'],
                details=(
                    f"原业务组ID: {business_group_id}, "
                    f"反结算业务组ID: {result['data']['reversal_group_id']}, 原因: {reason}"
                ),
                language='zh-CN'
            )

            return jsonify({
                'success': True,
                'message': '业务组反结算成功',
                'data': result['data']
            })

        return jsonify({
            'success': False,
            'message': result['message']
        }), 400

    except Exception as exc:
        logger.error("业务组反结算失败: %s", str(exc))
        return jsonify({
            'success': False,
            'message': f'反结算失败: {str(exc)}'
        }), 500
