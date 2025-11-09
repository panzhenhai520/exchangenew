from flask import Blueprint, request, jsonify
from datetime import datetime, date
from services.auth_service import token_required, has_permission, check_business_lock_for_balance
from services.db_service import DatabaseService
from models.exchange_models import Currency, CurrencyBalance, ExchangeRate, SystemLog, Branch, Operator, ExchangeTransaction, EODStatus, BranchOperatingStatus, CurrencyTemplate
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_
import logging
from sqlalchemy.orm import joinedload
from utils.transaction_utils import generate_transaction_no  # 修复：使用正确的导入
from decimal import Decimal
from services.balance_service import BalanceService
from services.log_service import LogService
from services.unified_log_service import UnifiedLogService, log_balance_adjustment
import os
import base64
# PDFReceiptService已迁移至SimplePDFService
from services.simple_pdf_service import SimplePDFService
from utils.language_utils import get_current_language
from utils.i18n_utils import I18nUtils

# Configure logging
# logging.basicConfig() - REMOVED: Do not override logging config from main.py
logger = logging.getLogger('app_balance')

# Create blueprint for balance operations
balance_bp = Blueprint('balance', __name__, url_prefix='/api/balance-management')

@balance_bp.route('/available-currencies', methods=['GET'])
@token_required
@has_permission('balance_manage')
def get_available_currencies(*args, **kwargs):
    """获取当前网点可兑换的币种及余额信息"""
    # 从装饰器中获取current_user
    current_user = kwargs.get('current_user') or args[0]
    
    if not current_user or not current_user.get('id'):
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
    # 获取是否需要检查汇率的参数
    require_rate = request.args.get('require_rate', 'false').lower() == 'true'
    # 获取是否包含本币的参数
    include_base = request.args.get('include_base', 'true').lower() == 'true'
        
    session = DatabaseService.get_session()
    try:
        # 获取操作员所属网点信息（包括本币信息）
        operator = session.query(Operator).filter_by(id=current_user['id']).first()
        if not operator:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
            
        branch = session.query(Branch).options(
            joinedload(Branch.base_currency)
        ).filter_by(id=operator.branch_id).first()
        
        if not branch:
            return jsonify({'success': False, 'message': '网点不存在'}), 404
            
        if not branch.base_currency:
            return jsonify({'success': False, 'message': '网点未设置本币'}), 400
            
        # 获取当前日期
        today = date.today()
        
        # 查询所有币种（包括本币）及其余额信息
        currencies_query = session.query(
            Currency,
            CurrencyBalance
        ).outerjoin(
            CurrencyBalance,
            and_(
                Currency.id == CurrencyBalance.currency_id,
                CurrencyBalance.branch_id == operator.branch_id
            )
        )
        
        # 获取结果
        currencies_result = currencies_query.all()
        
        result = []
        for currency, balance in currencies_result:
            # 检查是否是本币
            is_base = currency.id == branch.base_currency_id
            
            # 如果不包含本币且当前是本币，则跳过
            if not include_base and is_base:
                continue
                
            currency_data = {
                'currency_id': currency.id,
                'currency_code': currency.currency_code,
                'currency_name': currency.currency_name,
                'flag_code': currency.flag_code,
                'custom_flag_filename': currency.custom_flag_filename,
                'current_balance': float(balance.balance) if balance else 0.0,
                'is_base': is_base
            }
            
            # 添加余额更新信息
            if balance:
                currency_data['balance_updated_at'] = balance.updated_at.isoformat() if balance.updated_at else None
                
                # 查找最近一次初始余额设置的操作员信息
                latest_initial_transaction = session.query(ExchangeTransaction).join(
                    Operator, ExchangeTransaction.operator_id == Operator.id
                ).filter(
                    ExchangeTransaction.branch_id == operator.branch_id,
                    ExchangeTransaction.currency_id == currency.id,
                    ExchangeTransaction.type == 'initial_balance'
                ).order_by(ExchangeTransaction.created_at.desc()).first()
                
                if latest_initial_transaction:
                    currency_data['last_initial_operator'] = latest_initial_transaction.operator.name
                    currency_data['last_initial_time'] = latest_initial_transaction.created_at.isoformat()
                else:
                    currency_data['last_initial_operator'] = None
                    currency_data['last_initial_time'] = None
            else:
                currency_data['balance_updated_at'] = None
                currency_data['last_initial_operator'] = None
                currency_data['last_initial_time'] = None
            
            # 如果不是本币，检查汇率
            if not is_base:
                rate = session.query(ExchangeRate).filter(
                    and_(
                        ExchangeRate.currency_id == currency.id,
                        ExchangeRate.branch_id == operator.branch_id,
                        ExchangeRate.rate_date == today
                    )
                ).first()
                
                # 如果需要检查汇率且没有汇率，则跳过该币种
                if require_rate and not rate:
                    continue
                    
                if rate:
                    currency_data.update({
                        'buy_rate': float(rate.buy_rate),
                        'sell_rate': float(rate.sell_rate)
                    })
            
            result.append(currency_data)
            
        # 确保本币在列表最前面
        result.sort(key=lambda x: (0 if x['is_base'] else 1, x['currency_code']))

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        logger.error(f"Failed to get available currencies: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@balance_bp.route('/update', methods=['POST'])
@token_required
@has_permission('balance_manage')
@check_business_lock_for_balance
def update_balance(*args, **kwargs):
    """更新币种余额"""
    # 从装饰器中获取current_user
    current_user = kwargs.get('current_user') or args[0]
    data = request.json
    if not data or not all(k in data for k in ['currency_id', 'amount']):
        return jsonify({'success': False, 'message': '缺少必要的参数'}), 400

    session = DatabaseService.get_session()
    try:
        currency_id = data['currency_id']
        amount = float(data['amount'])

        # 获取币种信息
        currency = session.query(Currency).get(currency_id)
        if not currency:
            return jsonify({'success': False, 'message': '币种不存在'}), 404

        # 查找或创建余额记录
        balance = session.query(CurrencyBalance).filter_by(
            branch_id=current_user['branch_id'],
            currency_id=currency_id
        ).first()

        if balance:
            # 更新现有余额
            balance.balance = amount
            balance.updated_at = datetime.now()
        else:
            # 创建新的余额记录
            balance = CurrencyBalance(
                branch_id=current_user['branch_id'],
                currency_id=currency_id,
                balance=amount,
                updated_at=datetime.now()
            )
            session.add(balance)

        # 记录系统日志
        log = SystemLog(
            operation='UPDATE_BALANCE',
            operator_id=current_user['id'],
            log_type='balance',
            action=f"更新{currency.currency_name}余额为{amount}",
            details=f"币种: {currency.currency_code}, 金额: {amount}",
            ip_address=request.remote_addr
        )
        session.add(log)

        DatabaseService.commit_session(session)

        return jsonify({
            'success': True,
            'message': '余额更新成功',
            'data': {
                'currency_id': currency_id,
                'currency_code': currency.currency_code,
                'currency_name': currency.currency_name,
                'current_balance': float(amount)
            }
        })

    except Exception as e:
        logger.error(f"Failed to update balance: {str(e)}")
        DatabaseService.rollback_session(session)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@balance_bp.route('/adjust', methods=['POST'])
@token_required
@has_permission('balance_manage')
@check_business_lock_for_balance
def adjust_balance(*args, **kwargs):
    """调整币种余额，同时记录流水"""
    current_user = args[0]
    data = request.get_json()
    session = DatabaseService.get_session()
    
    try:
        # 检查日结期间余额调节权限
        from services.eod_service import EODService
        if not EODService.allow_balance_adjustment_during_eod(current_user['branch_id'], current_user['id']):
            return jsonify({
                'success': False, 
                'message': '当前营业锁定期间，您无权进行余额调节'
            }), 403
        
        # 获取参数
        currency_id = data.get('currency_id')
        adjustment_amount = data.get('adjustment_amount', data.get('amount', 0))
        adjustment_type = data.get('adjustment_type', 'increase')
        reason = data.get('reason', '')
        
        # 计算调整金额
        if adjustment_type == 'decrease':
            amount = -Decimal(str(abs(float(adjustment_amount))))
        else:
            amount = Decimal(str(abs(float(adjustment_amount))))
        
        if not currency_id or adjustment_amount == 0:
            return jsonify({'success': False, 'message': '无效的输入参数'}), 400
            
        # 获取币种信息
        currency = session.query(Currency).filter_by(id=currency_id).first()
        if not currency:
            return jsonify({'success': False, 'message': '币种不存在'}), 404
        
        # 获取网点信息，用于判断是否是本币
        branch = session.query(Branch).options(
            joinedload(Branch.base_currency)
        ).filter_by(id=current_user['branch_id']).first()
        
        if not branch:
            return jsonify({'success': False, 'message': '网点不存在'}), 404
        
        # 判断是否是本币
        is_base_currency = currency.id == branch.base_currency_id
        
        # 更新余额
        balance_before, balance_after = BalanceService.update_currency_balance(
            session=session,
            currency_id=currency_id,
            branch_id=current_user['branch_id'],
            amount=amount,
            lock_for_update=True
        )
        
        # 创建流水记录 - 根据币种类型写入不同字段
        now = datetime.now()
        if is_base_currency:
            # 本币调节：写入local_amount字段，amount字段为0
            transaction = ExchangeTransaction(
                transaction_no=generate_transaction_no(branch_id=current_user['branch_id'], session=session),
                branch_id=current_user['branch_id'],
                currency_id=currency_id,
                type='adjust_balance',
                amount='0.0',
                rate='1.0',
                local_amount=str(amount),
                operator_id=current_user['id'],
                transaction_date=now.date(),
                transaction_time=now.strftime('%H:%M:%S'),
                created_at=now,
                customer_name=reason,
                balance_before=str(balance_before),
                balance_after=str(balance_after)
            )
        else:
            # 外币调节：写入amount字段，local_amount字段为0
            transaction = ExchangeTransaction(
                transaction_no=generate_transaction_no(branch_id=current_user['branch_id'], session=session),
                branch_id=current_user['branch_id'],
                currency_id=currency_id,
                type='adjust_balance',
                amount=str(amount),
                rate='1.0',
                local_amount='0.0',
                operator_id=current_user['id'],
                transaction_date=now.date(),
                transaction_time=now.strftime('%H:%M:%S'),
                created_at=now,
                customer_name=reason,
                balance_before=str(balance_before),
                balance_after=str(balance_after)
            )
        
        session.add(transaction)
        
        # 记录系统日志
        log = SystemLog(
            operation='ADJUST_BALANCE',
            operator_id=current_user['id'],
            log_type='balance',
            action=f"{'增加' if amount > 0 else '减少'}{currency.currency_name}余额{abs(amount)}",
            details=f"币种: {currency.currency_code}, 调整前余额: {balance_before}, 调整金额: {amount}, 调整后余额: {balance_after}, 原因: {reason}",
            ip_address=request.remote_addr,
            created_at=now
        )
        session.add(log)
        
        # 检查BOT_Provider触发条件（仅针对外币增加的情况）
        bot_report_generated = False
        if adjustment_type == 'increase' and not is_base_currency and amount > 0:
            try:
                # 计算USD等值
                # 获取USD对本币的汇率
                usd_rate = session.query(ExchangeRate).filter(
                    ExchangeRate.branch_id == current_user['branch_id'],
                    ExchangeRate.currency_code == 'USD',
                    ExchangeRate.is_active == True
                ).order_by(ExchangeRate.updated_at.desc()).first()
                
                if usd_rate:
                    # 获取调节币种对本币的汇率
                    adj_currency_rate = session.query(ExchangeRate).filter(
                        ExchangeRate.branch_id == current_user['branch_id'],
                        ExchangeRate.currency_code == currency.currency_code,
                        ExchangeRate.is_active == True
                    ).order_by(ExchangeRate.updated_at.desc()).first()
                    
                    usd_equivalent = 0
                    if currency.currency_code == 'USD':
                        # 直接是USD
                        usd_equivalent = float(amount)
                    elif adj_currency_rate and usd_rate:
                        # 转换为USD等值：外币金额 * 外币买入汇率 / USD卖出汇率
                        usd_equivalent = float(amount) * float(adj_currency_rate.buy_rate) / float(usd_rate.sell_rate)
                    
                    logger.info(f"余额调节USD等值计算: {currency.currency_code} {amount} = {usd_equivalent} USD")
                    
                    # 检查BOT_Provider触发条件
                    from services.repform.rule_engine import RuleEngine
                    trigger_result = RuleEngine.check_triggers(
                        session, 'BOT_Provider',
                        {
                            'adjustment_type': 'increase',
                            'usd_equivalent': usd_equivalent,
                            'currency_code': currency.currency_code,
                            'adjustment_amount': float(amount)
                        },
                        current_user['branch_id']
                    )
                    
                    if trigger_result.get('triggered'):
                        logger.info(f"BOT_Provider触发条件满足，准备生成报告")
                        
                        # 生成BOT_Provider报告
                        from services.bot_report_service import BOTReportService
                        report_id = BOTReportService.generate_bot_provider(
                            session,
                            transaction.id,
                            {
                                'branch_id': current_user['branch_id'],
                                'operator_id': current_user['id'],
                                'currency_code': currency.currency_code,
                                'adjustment_amount': float(amount),
                                'usd_equivalent': usd_equivalent,
                                'adjustment_reason': reason,
                                'transaction_no': transaction.transaction_no
                            }
                        )
                        
                        if report_id:
                            bot_report_generated = True
                            logger.info(f"BOT_Provider报告生成成功: report_id={report_id}")
                        else:
                            logger.warning("BOT_Provider报告生成返回None")
                    else:
                        logger.info(f"BOT_Provider触发条件未满足: usd_equivalent={usd_equivalent}, 阈值=20000")
                else:
                    logger.warning("未找到USD汇率，无法计算USD等值")
                    
            except Exception as e:
                logger.error(f"BOT_Provider触发检查失败: {str(e)}")
                import traceback
                traceback.print_exc()
                # 不影响主流程，继续执行
        
        # 提交事务
        session.commit()
        
        # 记录余额调整日志
        try:
            current_language = get_current_language()
            log_balance_adjustment(
                operator_id=current_user['id'],
                branch_id=current_user['branch_id'],
                currency_code=currency.currency_code,
                adjustment_type=transaction.type,
                amount=float(adjustment_amount),
                reason=data.get('reason', ''),
                balance_before=float(balance_before),
                balance_after=float(balance_after),
                ip_address=request.remote_addr,
                adjustment_no=transaction.transaction_no,  # 添加调整单据号
                language=current_language  # 使用当前用户的语言设置
            )
        except Exception as log_error:
            # 日志记录失败不应该影响余额调整流程
            logger.warning(f"余额调整日志记录失败: {log_error}")
        
        # 构建响应消息
        response_message = '余额调整成功'
        if bot_report_generated:
            response_message += '，已自动生成BOT Provider报告'
        
        return jsonify({
            'success': True,
            'message': response_message,
            'bot_report_generated': bot_report_generated,
            'transaction': {
                'id': transaction.id,
                'transaction_id': transaction.id,
                'transaction_no': transaction.transaction_no,
                'currency_code': currency.currency_code,
                'amount': str(amount),
                'balance_before': str(balance_before),
                'balance_after': str(balance_after),
                'transaction_date': transaction.transaction_date.isoformat() if transaction.transaction_date else None,
                'transaction_time': transaction.transaction_time,
                'customer_name': transaction.customer_name,
                'operator_id': transaction.operator_id,
                'type': transaction.type
            }
        })
        
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'message': f'余额调整失败: {str(e)}'}), 500
    finally:
        session.close()

@balance_bp.route('/currency-templates', methods=['GET'])
@token_required
@has_permission('view_balances')
def get_currency_templates_for_balance(*args):
    """获取余额查询可用的币种模板列表（返回Currency表的id，确保与余额查询接口一致）"""
    current_user = args[0] if args else None
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401

    session = DatabaseService.get_session()
    try:
        # 查询所有活跃的币种模板，并关联Currency表获取正确的id
        templates = session.query(
            CurrencyTemplate,
            Currency.id.label('currency_id')
        ).join(
            Currency, CurrencyTemplate.currency_code == Currency.currency_code
        ).filter(
            CurrencyTemplate.is_active == True
        ).order_by(CurrencyTemplate.currency_code).all()
        
        # 格式化结果
        result = []
        for template, currency_id in templates:
            result.append({
                'id': currency_id,  # 使用Currency表的id，确保与余额查询接口一致
                'currency_code': template.currency_code,
                'currency_name': template.currency_name,
                'flag_code': template.flag_code,
                'symbol': template.symbol,
                'country': template.country,
                'is_active': template.is_active
            })

        return jsonify({
            'success': True,
            'templates': result,
            'total': len(result)
        })

    except Exception as e:
        session.rollback()
        logger.error(f"Error in get_currency_templates_for_balance: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@balance_bp.route('/query-currencies', methods=['GET'])
@token_required
@has_permission('view_balances')
def get_query_currencies(*args):
    """获取余额查询可用的币种列表（包括本币和所有在汇率表中出现过的币种）"""
    current_user = args[0] if args else None
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401

    session = DatabaseService.get_session()
    try:
        # 确定查询的网点ID
        branch_id = request.args.get('branch_id', type=int)
        target_branch_id = branch_id if branch_id else current_user['branch_id']
        
        logger.info(f"查询币种列表 - 用户ID: {current_user.get('id')}, 目标网点ID: {target_branch_id}")
        
        # 获取网点信息
        branch = session.query(Branch).filter_by(id=target_branch_id).first()
        if not branch:
            logger.error(f"网点不存在: {target_branch_id}")
            return jsonify({'success': False, 'message': '网点不存在'}), 404

        # 构建基础查询：获取所有在汇率表中出现过的币种
        rates_subquery = session.query(
            ExchangeRate.currency_id.distinct().label('currency_id')
        ).filter(
            ExchangeRate.branch_id == target_branch_id
        ).subquery()

        # 主查询：获取所有币种信息
        query = session.query(
            Currency.id.label('currency_id'),
            Currency.currency_name.label('currency_name'),
            Currency.currency_code.label('currency_code'),
            Currency.flag_code.label('flag_code')
        ).select_from(
            Currency
        ).join(
            rates_subquery, Currency.id == rates_subquery.c.currency_id
        )

        # 添加本币到查询中（如果本币不在汇率表中）
        if branch.base_currency_id:
            base_currency_query = session.query(
                Currency.id.label('currency_id'),
                Currency.currency_name.label('currency_name'),
                Currency.currency_code.label('currency_code'),
                Currency.flag_code.label('flag_code')
            ).select_from(
                Currency
            ).filter(
                Currency.id == branch.base_currency_id
            )
            
            # 合并查询结果
            query = query.union(base_currency_query)

        # 执行查询并排序
        currencies = query.order_by(Currency.currency_code).all()

        # 格式化结果
        result = []
        for currency in currencies:
            # 检查是否是本币
            is_base = currency.currency_id == branch.base_currency_id
            
            result.append({
                'id': currency.currency_id,
                'currency_code': currency.currency_code,
                'currency_name': currency.currency_name,
                'flag_code': currency.flag_code,
                'is_base': is_base
            })

        return jsonify({
            'success': True,
            'currencies': result
        })

    except Exception as e:
        session.rollback()
        logger.error(f"Error in get_query_currencies: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@balance_bp.route('/query', methods=['GET'])
@token_required
@has_permission('view_balances')
def query_balances(*args):
    """查询余额 - 显示所有在汇率表中出现过的币种"""
    current_user = args[0] if args else None
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401

    session = DatabaseService.get_session()
    try:
        # 获取查询参数
        query_date = request.args.get('date', date.today().isoformat())
        branch_id = request.args.get('branch_id', type=int)
        currency_id = request.args.get('currency_id', type=int)

        # 确定查询的网点ID
        target_branch_id = branch_id if branch_id else current_user['branch_id']
        
        # 获取网点信息
        branch = session.query(Branch).filter_by(id=target_branch_id).first()
        if not branch:
            return jsonify({'success': False, 'message': '网点不存在'}), 404

        # 如果指定了币种ID，直接查询该币种
        if currency_id:
            logger.info(f"查询指定币种ID: {currency_id}")
            query = session.query(
                Currency.id.label('currency_id'),
                Currency.currency_name.label('currency_name'),
                Currency.currency_code.label('currency_code'),
                Currency.custom_flag_filename.label('custom_flag_filename'),
                Currency.flag_code.label('flag_code'),
                Branch.branch_name.label('branch_name'),
                CurrencyBalance.balance.label('balance'),
                CurrencyBalance.updated_at.label('updated_at'),
                CurrencyBalance.id.label('balance_id')
            ).select_from(
                Currency
            ).join(
                Branch, Branch.id == target_branch_id
            ).outerjoin(
                CurrencyBalance, 
                and_(
                    CurrencyBalance.currency_id == Currency.id,
                    CurrencyBalance.branch_id == target_branch_id
                )
            ).filter(
                Currency.id == currency_id
            )
        else:
            # 构建基础查询：获取所有在汇率表中出现过的币种（包括本币）
            # 使用子查询获取该网点所有设置过汇率的币种
            rates_subquery = session.query(
                ExchangeRate.currency_id.distinct().label('currency_id')
            ).filter(
                ExchangeRate.branch_id == target_branch_id
            ).subquery()

            # 主查询：获取所有币种信息，左连接余额表
            query = session.query(
                Currency.id.label('currency_id'),
                Currency.currency_name.label('currency_name'),
                Currency.currency_code.label('currency_code'),
                Currency.custom_flag_filename.label('custom_flag_filename'),
                Currency.flag_code.label('flag_code'),
                Branch.branch_name.label('branch_name'),
                CurrencyBalance.balance.label('balance'),
                CurrencyBalance.updated_at.label('updated_at'),
                CurrencyBalance.id.label('balance_id')
            ).select_from(
                Currency
            ).join(
                rates_subquery, Currency.id == rates_subquery.c.currency_id
            ).join(
                Branch, Branch.id == target_branch_id
            ).outerjoin(
                CurrencyBalance, 
                and_(
                    CurrencyBalance.currency_id == Currency.id,
                    CurrencyBalance.branch_id == target_branch_id
                )
            )

            # 添加本币到查询中（如果本币不在汇率表中）
            if branch.base_currency_id:
                base_currency_query = session.query(
                    Currency.id.label('currency_id'),
                    Currency.currency_name.label('currency_name'),
                    Currency.currency_code.label('currency_code'),
                    Currency.custom_flag_filename.label('custom_flag_filename'),
                    Currency.flag_code.label('flag_code'),
                    Branch.branch_name.label('branch_name'),
                    CurrencyBalance.balance.label('balance'),
                    CurrencyBalance.updated_at.label('updated_at'),
                    CurrencyBalance.id.label('balance_id')
                ).select_from(
                    Currency
                ).join(
                    Branch, Branch.id == target_branch_id
                ).outerjoin(
                    CurrencyBalance,
                    and_(
                        CurrencyBalance.currency_id == Currency.id,
                        CurrencyBalance.branch_id == target_branch_id
                    )
                ).filter(
                    Currency.id == branch.base_currency_id
                )
                
                # 合并查询结果
                query = query.union(base_currency_query)

        # 添加过滤条件 - 管理员和App角色可以查看所有网点余额
        if not (current_user.get('is_admin', False) or current_user.get('is_app_role', False)):
            # 普通用户只能查看自己网点的余额
            if target_branch_id != current_user['branch_id']:
                return jsonify({'success': False, 'message': 'no_permission_view_other_branch_balance'}), 403

        # 执行查询
        balances = query.order_by(Currency.currency_code).all()
        
        logger.info(f"查询结果数量: {len(balances)}")
        if currency_id:
            logger.info(f"指定币种ID {currency_id} 的查询结果:")
            for balance in balances:
                logger.info(f"  - 币种ID: {balance.currency_id}, 币种代码: {balance.currency_code}, 币种名称: {balance.currency_name}")

        # 格式化结果
        result = []
        for balance in balances:
            result.append({
                'id': balance.balance_id or 0,  # 如果没有余额记录，使用0作为ID
                'branchId': target_branch_id,
                'branchName': balance.branch_name,
                'currencyId': balance.currency_id,
                'currencyName': balance.currency_name,
                'currencyCode': balance.currency_code,
                'custom_flag_filename': balance.custom_flag_filename,
                'flag_code': balance.flag_code,
                'balance': float(balance.balance or 0),  # 如果没有余额记录，显示0
                'updatedAt': balance.updated_at.strftime('%Y-%m-%d %H:%M:%S') if balance.updated_at else None
            })

        return jsonify({
            'success': True,
            'balances': result
        })

    except Exception as e:
        session.rollback()
        logger.error(f"Error in query_balances: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@balance_bp.route('/export', methods=['GET'])
@token_required
@has_permission('view_balances')
def export_balances(*args):
    """导出余额查询结果"""
    current_user = args[0] if args else None
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401

    session = DatabaseService.get_session()
    try:
        # 获取查询参数
        query_date = request.args.get('date', date.today().isoformat())
        branch_id = request.args.get('branch_id', type=int)
        currency_id = request.args.get('currency_id', type=int)

        # 确定查询的网点ID
        target_branch_id = branch_id if branch_id else current_user['branch_id']
        
        # 获取网点信息
        branch = session.query(Branch).filter_by(id=target_branch_id).first()
        if not branch:
            return jsonify({'success': False, 'message': '网点不存在'}), 404

        # 构建查询：根据是否指定币种来决定查询策略
        if currency_id:
            # 如果指定了币种，直接查询该币种
            query = session.query(
                Currency.id.label('currency_id'),
                Currency.currency_name.label('currency_name'),
                Currency.currency_code.label('currency_code'),
                Branch.branch_name.label('branch_name'),
                CurrencyBalance.balance.label('balance'),
                CurrencyBalance.updated_at.label('updated_at'),
                CurrencyBalance.id.label('balance_id')
            ).select_from(
                Currency
            ).join(
                Branch, Branch.id == target_branch_id
            ).outerjoin(
                CurrencyBalance, 
                and_(
                    CurrencyBalance.currency_id == Currency.id,
                    CurrencyBalance.branch_id == target_branch_id
                )
            ).filter(
                Currency.id == currency_id
            )
        else:
            # 如果没有指定币种，查询所有在汇率表中出现过的币种（包括本币）
            rates_subquery = session.query(
                ExchangeRate.currency_id.distinct().label('currency_id')
            ).filter(
                ExchangeRate.branch_id == target_branch_id
            ).subquery()

            # 主查询：获取所有币种信息，左连接余额表
            query = session.query(
                Currency.id.label('currency_id'),
                Currency.currency_name.label('currency_name'),
                Currency.currency_code.label('currency_code'),
                Branch.branch_name.label('branch_name'),
                CurrencyBalance.balance.label('balance'),
                CurrencyBalance.updated_at.label('updated_at'),
                CurrencyBalance.id.label('balance_id')
            ).select_from(
                Currency
            ).join(
                rates_subquery, Currency.id == rates_subquery.c.currency_id
            ).join(
                Branch, Branch.id == target_branch_id
            ).outerjoin(
                CurrencyBalance, 
                and_(
                    CurrencyBalance.currency_id == Currency.id,
                    CurrencyBalance.branch_id == target_branch_id
                )
            )

            # 添加本币到查询中（如果本币不在汇率表中）
            if branch.base_currency_id:
                base_currency_query = session.query(
                    Currency.id.label('currency_id'),
                    Currency.currency_name.label('currency_name'),
                    Currency.currency_code.label('currency_code'),
                    Branch.branch_name.label('branch_name'),
                    CurrencyBalance.balance.label('balance'),
                    CurrencyBalance.updated_at.label('updated_at'),
                    CurrencyBalance.id.label('balance_id')
                ).select_from(
                    Currency
                ).join(
                    Branch, Branch.id == target_branch_id
                ).outerjoin(
                    CurrencyBalance,
                    and_(
                        CurrencyBalance.currency_id == Currency.id,
                        CurrencyBalance.branch_id == target_branch_id
                    )
                ).filter(
                    Currency.id == branch.base_currency_id
                )
                
                # 合并查询结果
                query = query.union(base_currency_query)

        # 添加权限过滤条件
        if not current_user.get('is_admin', False):
            # 非管理员只能查看自己网点的余额
            if target_branch_id != current_user['branch_id']:
                return jsonify({'success': False, 'message': '无权查看其他网点的余额'}), 403

        # 执行查询并排序
        balances = query.order_by(Currency.currency_code).all()

        # 去重处理：使用字典确保每个币种只出现一次
        unique_balances = {}
        for balance in balances:
            currency_code = balance.currency_code
            if currency_code not in unique_balances:
                unique_balances[currency_code] = balance

        # 生成CSV内容
        import csv
        import io
        
        # 创建CSV文件
        output = io.StringIO()
        writer = csv.writer(output, lineterminator='\n')
        
        # 写入CSV头部
        writer.writerow(['网点', '币种代码', '币种名称', '余额', '最后更新时间', '是否本币'])
        
        # 写入数据（按币种代码排序）
        for currency_code in sorted(unique_balances.keys()):
            balance = unique_balances[currency_code]
            # 检查是否是本币
            is_base = balance.currency_id == branch.base_currency_id
            
            writer.writerow([
                balance.branch_name,
                balance.currency_code,
                balance.currency_name,
                float(balance.balance or 0),
                balance.updated_at.strftime('%Y-%m-%d %H:%M:%S') if balance.updated_at else '',
                '是' if is_base else '否'
            ])
        
        # 获取CSV内容并清理多余的空行
        csv_content = output.getvalue()
        output.close()
        
        # 清理多余的空行
        lines = csv_content.split('\n')
        cleaned_lines = []
        for line in lines:
            if line.strip():  # 只保留非空行
                cleaned_lines.append(line)
        
        csv_content = '\n'.join(cleaned_lines)
        
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        branch_code = getattr(branch, 'branch_code', f'branch_{branch.id}')
        filename = f'balance_query_{branch_code}_{timestamp}.csv'
        
        # 创建导出目录
        import os
        export_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'exports')
        if not os.path.exists(export_dir):
            os.makedirs(export_dir, exist_ok=True)
        
        # 保存文件
        file_path = os.path.join(export_dir, filename)
        with open(file_path, 'w', encoding='utf-8-sig') as f:  # 使用utf-8-sig支持中文
            f.write(csv_content)
        
        # 返回下载链接
        download_url = f'/api/balance-management/download/{filename}'
        
        return jsonify({
            'success': True,
            'message': '导出成功',
            'file_path': file_path,
            'download_url': download_url,
            'filename': filename
        })

    except Exception as e:
        session.rollback()
        logger.error(f"Error in export_balances: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@balance_bp.route('/download/<filename>', methods=['GET'])
def download_balance_export(filename):
    """下载余额查询导出文件"""
    try:
        import os
        from flask import send_file
        
        # 安全检查：确保文件名不包含路径
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({'success': False, 'message': '无效的文件名'}), 400
        
        # 构建文件路径
        export_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'exports')
        file_path = os.path.join(export_dir, filename)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'message': '文件不存在'}), 404
        
        # 返回文件
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv'
        )
        
    except Exception as e:
        logger.error(f"Error in download_balance_export: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@balance_bp.route('/initial', methods=['POST'])
@token_required
@has_permission('balance_manage')
@check_business_lock_for_balance
def set_initial_balance(*args, **kwargs):
    """设置期初余额"""
    current_user = kwargs.get('current_user') or args[0]
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': '缺少必要的参数'}), 400
        
    branch_id = data.get('branch_id')
    balances = data.get('balances', [])
    
    if not branch_id or not balances:
        return jsonify({'success': False, 'message': '缺少必要的参数'}), 400
        
    session = DatabaseService.get_session()
    try:
        # 获取操作员所属网点信息
        operator = session.query(Operator).filter_by(id=current_user['id']).first()
        if not operator:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
            
        # 验证网点权限
        if str(operator.branch_id) != str(branch_id):
            return jsonify({'success': False, 'message': '无权操作其他网点的余额'}), 403
        
        # 检查网点营业状态 - 为清空营业数据功能保留
        branch_status = session.query(BranchOperatingStatus).filter_by(
            branch_id=branch_id
        ).first()
        
        if not branch_status:
            # 为新网点创建状态记录
            branch_status = BranchOperatingStatus(
                branch_id=branch_id,
                is_initial_setup_completed=False,
                data_reset_count=0
            )
            session.add(branch_status)
        
        # 币种级别的期初设置控制 - 智能过滤已期初的币种
        valid_balances = []  # 可以期初的币种
        skipped_currencies = []  # 跳过的已期初币种
        invalid_currencies = []  # 无效的币种数据
        
        for balance_data in balances:
            currency_id = balance_data.get('currency_id')
            new_balance = balance_data.get('balance')
            
            if not currency_id or new_balance is None:
                invalid_currencies.append(balance_data)
                continue
                
            # 检查该币种是否已经有期初余额记录
            existing_initial = session.query(ExchangeTransaction).filter_by(
                branch_id=branch_id,
                currency_id=currency_id,
                type='initial_balance'
            ).first()
            
            if existing_initial:
                # 获取币种信息用于日志
                currency = session.query(Currency).filter_by(id=currency_id).first()
                currency_name = currency.currency_name if currency else f"币种ID:{currency_id}"
                skipped_currencies.append({
                    'currency_id': currency_id,
                    'currency_name': currency_name,
                    'initial_date': existing_initial.transaction_date.isoformat(),
                    'initial_operator': existing_initial.operator.name if existing_initial.operator else '未知',
                    'current_balance': float(existing_initial.balance_after) if existing_initial.balance_after else 0
                })
                logger.info(f"跳过已期初币种: {currency_name} (ID: {currency_id})")
            else:
                # 这是可以期初的币种
                valid_balances.append(balance_data)
        
        # 如果没有任何可期初的币种
        if not valid_balances:
            if skipped_currencies:
                return jsonify({
                    'success': False, 
                    'message': '所有提交的币种都已完成期初设置，无需重复操作',
                    'skipped_currencies': skipped_currencies,
                    'suggestion': '如需重新设置，请使用"清空营业数据"功能。'
                }), 400
            else:
                return jsonify({
                    'success': False, 
                    'message': '没有有效的币种数据可以处理',
                    'invalid_data': invalid_currencies
                }), 400
        
        # 检查是否有进行中的日结
        active_eod = session.query(EODStatus).filter(
            EODStatus.branch_id == branch_id,
            EODStatus.status.in_(['pending', 'processing']),
            EODStatus.is_locked == True
        ).first()
        
        if active_eod:
            return jsonify({
                'success': False, 
                'message': '当前有进行中的日结流程，无法进行余额初始化操作'
            }), 400
            
        # 获取当前日期和时间
        now = datetime.now()
        today = now.date()
        
        # 检查是否为网点首次期初设置
        is_first_initial_setup = not branch_status.is_initial_setup_completed and session.query(ExchangeTransaction).filter_by(
            branch_id=branch_id,
            type='initial_balance'
        ).count() == 0
        
        transaction_records = []
        
        # 只处理有效的币种（未期初的币种）
        logger.info(f"开始处理 {len(valid_balances)} 个未期初币种，跳过 {len(skipped_currencies)} 个已期初币种")
        
        # 更新每个币种的余额
        for balance_data in valid_balances:
            currency_id = balance_data.get('currency_id')
            new_balance = balance_data.get('balance')
            
            if not currency_id or new_balance is None:
                continue
            
            # 获取币种信息
            currency = session.query(Currency).filter_by(id=currency_id).first()
            if not currency:
                continue
                
            # 查找现有余额记录
            balance = session.query(CurrencyBalance).filter_by(
                branch_id=branch_id,
                currency_id=currency_id
            ).first()
            
            
            # 计算余额变动
            old_balance = Decimal(str(balance.balance)) if balance else Decimal('0')
            new_balance_decimal = Decimal(str(new_balance))
            balance_change = new_balance_decimal - old_balance
            
            # 注释掉余额变动检查 - 按用户要求，只要勾选就要创建期初记录
            # 即使金额没有变化或为0，也要产生期初单据
            # if balance_change == 0:
            #     continue
            
            # 更新或创建余额记录
            if balance:
                balance.balance = new_balance
                balance.updated_at = now
            else:
                balance = CurrencyBalance(
                    branch_id=branch_id,
                    currency_id=currency_id,
                    balance=new_balance,
                    updated_at=now
                )
                session.add(balance)
            
            # 创建交易流水记录（用于日结计算）
            transaction_no = generate_transaction_no(branch_id=current_user['branch_id'], session=session)
            
            # 获取网点的本币信息
            branch = session.query(Branch).filter_by(id=current_user['branch_id']).first()
            base_currency_id = branch.base_currency_id if branch else None
            
            # 【修正】确定amount和local_amount的写入逻辑：
            # - 外币期初：amount写入期初金额，local_amount写入0
            # - 本币期初：amount写入0，local_amount写入期初金额
            if currency_id == base_currency_id:
                # 本币期初：amount = 0, local_amount = 期初金额
                amount_value = Decimal('0')
                local_amount_value = new_balance_decimal
            else:
                # 外币期初：amount = 期初金额, local_amount = 0
                amount_value = new_balance_decimal
                local_amount_value = Decimal('0')
            
            transaction = ExchangeTransaction(
                transaction_no=transaction_no,
                branch_id=current_user['branch_id'],
                currency_id=currency_id,
                type='initial_balance',  # 新增交易类型：期初余额设置
                amount=str(amount_value),  # 【修正】外币期初写入期初金额，本币期初写入0
                rate=str(Decimal('1.0')),  # 汇率设为1 - 修复：转换为字符串
                local_amount=str(local_amount_value),  # 【修正】外币期初写入0，本币期初写入期初金额
                customer_name='系统期初余额设置',
                customer_id='SYSTEM',
                operator_id=current_user['id'],
                transaction_date=today,
                transaction_time=now.strftime('%H:%M:%S'),
                created_at=now,
                balance_before=str(old_balance),  # 修复：转换为字符串
                balance_after=str(new_balance_decimal),  # 修复：转换为字符串
                status='completed'
            )
            session.add(transaction)
            transaction_records.append({
                'currency_code': currency.currency_code,
                'old_balance': float(old_balance),
                'new_balance': float(new_balance_decimal),
                'change': float(balance_change),
                'transaction_no': transaction_no
            })
                
        # 记录系统日志
        log = SystemLog(
            operation='SET_INITIAL_BALANCE',
            operator_id=current_user['id'],
            log_type='balance',
            action='设置期初余额',
            details=f'网点ID: {branch_id}, 更新币种数: {len(transaction_records)}, 交易记录: {[r["transaction_no"] for r in transaction_records]}',
            ip_address=request.remote_addr
        )
        session.add(log)
        
        # 更新营业状态 - 如果是网点第一次期初设置，标记营业开始
        if len(transaction_records) > 0:
            if is_first_initial_setup:  # 如果这是网点的第一次期初设置
                branch_status.is_initial_setup_completed = True
                branch_status.initial_setup_date = now
                branch_status.initial_setup_by = current_user['id']
                branch_status.operating_start_date = today
                branch_status.updated_at = now
                
                logger.info(f"网点 {branch_id} 开始营业，首次期初设置 {len(transaction_records)} 个币种，操作员: {current_user['id']}")
            else:
                logger.info(f"网点 {branch_id} 追加期初设置 {len(transaction_records)} 个币种，操作员: {current_user['id']}")
        
        session.commit()
        
        # 记录余额初始化日志
        try:
            log_service = UnifiedLogService()
            for record in transaction_records:
                log_service.log_balance_initialization(
                    operator_id=current_user['operator_id'],
                    operator_name=current_user.get('name', '未知用户'),
                    currency_code=record['currency_code'],
                    initial_amount=record['new_balance'],
                    transaction_no=record['transaction_no'],
                    ip_address=request.remote_addr,
                    branch_id=current_user['branch_id']
                )
        except Exception as log_error:
            # 日志记录失败不应该影响余额初始化流程
            logger.warning(f"余额初始化日志记录失败: {log_error}")
        
        # 构建成功返回信息
        response_message = f'成功设置 {len(transaction_records)} 个币种的期初余额'
        if skipped_currencies:
            response_message += f'，跳过 {len(skipped_currencies)} 个已期初币种'
        
        return jsonify({
            'success': True,
            'message': response_message,
            'processed_currencies': len(transaction_records),
            'skipped_currencies_count': len(skipped_currencies),
            'skipped_currencies': skipped_currencies,
            'transaction_records': transaction_records
        })
        
    except Exception as e:
        logger.error(f"Failed to set initial balances: {str(e)}")
        session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        session.close()

# 新增：查询初始化余额交易记录的API
@balance_bp.route('/initial/transactions', methods=['GET'])
@token_required
@has_permission('balance_manage')
def get_initial_balance_transactions(current_user):
    """获取初始化余额的交易记录列表"""
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
    
    session = DatabaseService.get_session()
    
    try:
        # 获取查询参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        currency_code = request.args.get('currency_code')
        
        # 构建查询
        query = session.query(
            ExchangeTransaction,
            Currency.currency_code,
            Currency.currency_name
        ).join(
            Currency, ExchangeTransaction.currency_id == Currency.id
        ).filter(
            ExchangeTransaction.branch_id == current_user['branch_id'],
            ExchangeTransaction.type == 'initial_balance'
        )
        
        # 添加筛选条件
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(ExchangeTransaction.transaction_date >= start)
            except ValueError:
                return jsonify({'success': False, 'message': '开始日期格式错误'}), 400
        
        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(ExchangeTransaction.transaction_date <= end)
            except ValueError:
                return jsonify({'success': False, 'message': '结束日期格式错误'}), 400
        
        if currency_code:
            query = query.filter(Currency.currency_code == currency_code)
        
        # 按时间倒序排列
        transactions = query.order_by(
            ExchangeTransaction.transaction_date.desc(),
            ExchangeTransaction.transaction_time.desc()
        ).all()
        
        # 格式化结果
        result = []
        for tx, currency_code, currency_name in transactions:
            result.append({
                'id': tx.id,
                'transaction_no': tx.transaction_no,
                'currency_code': currency_code,
                'currency_name': currency_name,
                'amount': str(tx.amount),
                'balance_before': str(tx.balance_before) if tx.balance_before else '0',
                'balance_after': str(tx.balance_after) if tx.balance_after else '0',
                'transaction_date': tx.transaction_date.isoformat() if tx.transaction_date else None,
                'transaction_time': tx.transaction_time,
                'created_at': tx.created_at.isoformat() if tx.created_at else None,
                'receipt_filename': tx.receipt_filename,
                'print_count': tx.print_count or 0,
                'has_receipt': bool(tx.receipt_filename)
            })
        
        return jsonify({
            'success': True,
            'transactions': result,
            'total_count': len(result)
        })
        
    except Exception as e:
        logger.error(f"Get initial balance transactions failed: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

# 新增：PDF票据生成和打印API for 初始化余额
@balance_bp.route('/initial/transactions/<int:transaction_id>/print-receipt', methods=['POST'])
@token_required
@has_permission('balance_manage')
def print_initial_balance_receipt(current_user, transaction_id):
    """生成并打印初始化余额票据PDF"""
    
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
    
    if not transaction_id:
        return jsonify({'success': False, 'message': '交易ID参数缺失'}), 400
    
    session = DatabaseService.get_session()
    
    try:
        # 获取交易记录
        transaction = session.query(ExchangeTransaction).filter_by(
            id=transaction_id,
            branch_id=current_user['branch_id'],
            type='initial_balance'  # 只查找初始化余额类型的交易
        ).first()
        
        if not transaction:
            return jsonify({'success': False, 'message': '初始化余额交易记录不存在'}), 404
        
        # 获取相关信息
        currency = session.query(Currency).filter_by(id=transaction.currency_id).first()
        branch = session.query(Branch).filter_by(id=transaction.branch_id).first()
        operator = session.query(Operator).filter_by(id=transaction.operator_id).first()
        
        # 格式化交易时间
        def format_transaction_time(transaction_date, transaction_time):
            """格式化交易时间显示"""
            try:
                if isinstance(transaction_date, date):
                    date_str = transaction_date.strftime('%Y-%m-%d')
                else:
                    date_str = str(transaction_date)
                
                if transaction_time:
                    return f"{date_str} {transaction_time}"
                else:
                    return date_str
            except Exception as e:
                logger.error(f"格式化交易时间失败: {e}")
                return f"{transaction_date} {transaction_time or ''}"
        
        # 准备初始化余额单据的PDF数据
        pdf_data = {
            'transaction_no': transaction.transaction_no,
            'branch_name': branch.branch_name,
            'branch_code': branch.branch_code,
            'transaction_type_desc': '期初余额设置',
            'currency_code': currency.currency_code,
            'formatted_datetime': format_transaction_time(transaction.transaction_date, transaction.transaction_time),
            'from_amount': abs(float(transaction.balance_before or 0)),
            'from_currency': '调整前余额',
            'to_amount': abs(float(transaction.balance_after or 0)),
            'to_currency': currency.currency_code,
            'rate': '1.0000',
            'foreign_currency': currency.currency_code,
            'base_currency': currency.currency_code,
            'customer_name': f'操作员：{operator.name}' if operator else '系统操作',
            'customer_id': 'INITIAL_BALANCE',
            'purpose': '期初余额设置',
            'remarks': f'调整金额：{transaction.amount}',
            'branch_code': branch.branch_code if branch else '',
            'branch_name': branch.branch_name if branch else '',
            'branch_display': f"{branch.branch_name if branch else '未知网点'}({branch.branch_code if branch else ''})" if branch else '未知网点'
        }
        
        # 获取语言参数
        language = request.json.get('language', 'zh')
        
        # 添加调试信息
        logger.info(f"单个打印接收到的语言参数: {language}")
        logger.info(f"单个打印完整的请求数据: {request.json}")
        
        # 生成PDF文件路径
        file_path = SimplePDFService.get_receipt_file_path(
            transaction.transaction_no, 
            transaction.transaction_date,
            language
        )
        
        # 生成PDF - 使用SimplePDFService统一硬编码格式
        from services.balance_service import BalanceService
        # 设置重新打印时间（如果是重新打印）
        reprint_time = datetime.now() if transaction.print_count and transaction.print_count > 0 else None
        
        pdf_content = BalanceService.generate_initial_balance_receipt(transaction, session, reprint_time, language)
        
        # 保存PDF到文件
        pdf_bytes = base64.b64decode(pdf_content)
        with open(file_path, 'wb') as f:
            f.write(pdf_bytes)
        success = True
        
        if not success:
            return jsonify({'success': False, 'message': 'PDF生成失败'}), 500
        
        # 更新交易记录的票据信息
        if not transaction.receipt_filename:
            # 只有第一次打印时才设置文件名
            transaction.receipt_filename = os.path.basename(file_path)
        
        # 增加打印次数
        transaction.print_count = (transaction.print_count or 0) + 1
        
        # 记录系统日志
        log = SystemLog(
            operation='PRINT_INITIAL_BALANCE_RECEIPT',
            operator_id=current_user['id'],
            log_type='balance',
            action=f"打印期初余额单据 {transaction.transaction_no}",
            details=f"第{transaction.print_count}次打印，文件: {transaction.receipt_filename}",
            ip_address=request.remote_addr,
            created_at=datetime.now()
        )
        session.add(log)
        
        session.commit()
        
        # 根据语言返回对应的成功消息，包含打印次数
        success_messages = {
            'zh': f'期初余额单据生成成功，第{transaction.print_count}次打印',
            'en': f'Initial balance document generated successfully, print #{transaction.print_count}',
            'th': f'สร้างเอกสารยอดเริ่มต้นสำเร็จ ครั้งที่ {transaction.print_count}'
        }
        success_message = success_messages.get(language, success_messages['zh'])
        
        return jsonify({
            'success': True,
            'message': success_message,
            'receipt_filename': transaction.receipt_filename,
            'print_count': transaction.print_count,
            'file_path': file_path
        })
        
    except Exception as e:
        logger.error(f"Print initial balance receipt failed: {str(e)}")
        session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@balance_bp.route('/initial/transactions/<transaction_no>/download-receipt', methods=['GET'])
@token_required
@has_permission('balance_manage')
def download_initial_balance_receipt(current_user, transaction_no):
    """下载初始化余额票据PDF"""
    
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
    
    if not transaction_no:
        return jsonify({'success': False, 'message': '交易号参数缺失'}), 400
    
    # 获取语言参数
    language = request.args.get('language', 'zh')
    logger.info(f"下载初始余额票据 - 交易号: {transaction_no}, 语言: {language}")
    
    session = DatabaseService.get_session()
    
    try:
        # 获取交易记录
        transaction = session.query(ExchangeTransaction).filter_by(
            transaction_no=transaction_no,
            branch_id=current_user['branch_id'],
            type='initial_balance'
        ).first()
        
        if not transaction:
            return jsonify({'success': False, 'message': '初始化余额交易记录不存在'}), 404
        
        if not transaction.receipt_filename:
            return jsonify({'success': False, 'message': '该交易尚未生成票据'}), 404
        
        # 构建文件路径 - 添加语言参数
        file_path = SimplePDFService.get_receipt_file_path(
            transaction.transaction_no, 
            transaction.transaction_date,
            language
        )
        
        logger.info(f"尝试下载文件: {file_path}")
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'message': f'票据文件不存在: {file_path}'}), 404
        
        # 记录下载日志
        log = SystemLog(
            operation='DOWNLOAD_INITIAL_BALANCE_RECEIPT',
            operator_id=current_user['id'],
            log_type='balance',
            action=f"下载期初余额单据 {transaction_no}",
            details=f"文件: {transaction.receipt_filename}",
            ip_address=request.remote_addr,
            created_at=datetime.now()
        )
        session.add(log)
        session.commit()
        
        # 返回文件
        from flask import send_file
        return send_file(
            file_path,
            as_attachment=True,
            download_name=transaction.receipt_filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Download initial balance receipt failed: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@balance_bp.route('/adjust/transactions/<transaction_no>/download-receipt', methods=['GET'])
@token_required
@has_permission('balance_manage')
def download_adjust_balance_receipt(current_user, transaction_no):
    """下载余额调整票据PDF"""
    
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
    
    if not transaction_no:
        return jsonify({'success': False, 'message': '交易号参数缺失'}), 400
    
    # 获取语言参数
    language = request.args.get('language', 'zh')
    logger.info(f"下载余额调整票据 - 交易号: {transaction_no}, 语言: {language}")
    
    session = DatabaseService.get_session()
    
    try:
        # 获取交易记录
        transaction = session.query(ExchangeTransaction).filter_by(
            transaction_no=transaction_no,
            branch_id=current_user['branch_id'],
            type='adjust_balance'
        ).first()
        
        if not transaction:
            return jsonify({'success': False, 'message': '余额调整交易记录不存在'}), 404
        
        if not transaction.receipt_filename:
            return jsonify({'success': False, 'message': '该交易尚未生成票据'}), 404
        
        # 构建文件路径 - 添加语言参数
        file_path = SimplePDFService.get_receipt_file_path(
            transaction.transaction_no, 
            transaction.transaction_date,
            language
        )
        
        logger.info(f"尝试下载文件: {file_path}")
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'message': f'票据文件不存在: {file_path}'}), 404
        
        # 返回文件
        from flask import send_file
        return send_file(
            file_path,
            as_attachment=True,
            download_name=transaction.receipt_filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Download adjust balance receipt failed: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

# 新增：根据交易号获取交易信息的API
@balance_bp.route('/transactions/by-no/<transaction_no>', methods=['GET'])
@token_required
@has_permission('balance_manage')
def get_transaction_by_no(current_user, transaction_no):
    """根据交易号获取交易信息"""
    
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
    
    if not transaction_no:
        return jsonify({'success': False, 'message': '交易号参数缺失'}), 400
    
    session = DatabaseService.get_session()
    
    try:
        # 获取交易记录
        transaction = session.query(ExchangeTransaction).filter_by(
            transaction_no=transaction_no,
            branch_id=current_user['branch_id']
        ).first()
        
        if not transaction:
            return jsonify({'success': False, 'message': '交易记录不存在'}), 404
        
        # 获取相关信息
        currency = session.query(Currency).filter_by(id=transaction.currency_id).first()
        
        transaction_data = {
            'id': transaction.id,
            'transaction_no': transaction.transaction_no,
            'type': transaction.type,
            'currency_code': currency.currency_code if currency else None,
            'currency_name': currency.currency_name if currency else None,
            'amount': float(transaction.amount),
            'balance_before': float(transaction.balance_before) if transaction.balance_before else None,
            'balance_after': float(transaction.balance_after) if transaction.balance_after else None,
            'transaction_date': transaction.transaction_date.isoformat() if transaction.transaction_date else None,
            'transaction_time': transaction.transaction_time,
            'created_at': transaction.created_at.isoformat() if transaction.created_at else None,
            'customer_name': transaction.customer_name,
            'receipt_filename': transaction.receipt_filename,
            'print_count': transaction.print_count or 0,
            'has_receipt': bool(transaction.receipt_filename)
        }
        
        return jsonify({
            'success': True,
            'transaction': transaction_data
        })
        
    except Exception as e:
        logger.error(f"Get transaction by no failed: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

# 新增：查询余额调整交易记录的API
@balance_bp.route('/adjust/transactions', methods=['GET'])
@token_required
@has_permission('balance_manage')
def get_adjust_balance_transactions(current_user):
    """获取余额调整的交易记录列表"""
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
    
    session = DatabaseService.get_session()
    
    try:
        # 获取查询参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        currency_code = request.args.get('currency_code')
        
        # 构建查询
        query = session.query(
            ExchangeTransaction,
            Currency.currency_code,
            Currency.currency_name
        ).join(
            Currency, ExchangeTransaction.currency_id == Currency.id
        ).filter(
            ExchangeTransaction.branch_id == current_user['branch_id'],
            ExchangeTransaction.type == 'adjust_balance'
        )

        # 添加筛选条件
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(ExchangeTransaction.transaction_date >= start)
            except ValueError:
                return jsonify({'success': False, 'message': '开始日期格式错误'}), 400
        
        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(ExchangeTransaction.transaction_date <= end)
            except ValueError:
                return jsonify({'success': False, 'message': '结束日期格式错误'}), 400
        
        if currency_code:
            query = query.filter(Currency.currency_code == currency_code)
        
        # 执行查询
        transactions = query.all()

        # 格式化结果
        result = []
        for tx, currency_code, currency_name in transactions:
            result.append({
                'id': tx.id,
                'transaction_no': tx.transaction_no,
                'currency_code': currency_code,
                'currency_name': currency_name,
                'amount': str(tx.amount),
                'balance_before': str(tx.balance_before) if tx.balance_before else '0',
                'balance_after': str(tx.balance_after) if tx.balance_after else '0',
                'transaction_date': tx.transaction_date.isoformat() if tx.transaction_date else None,
                'transaction_time': tx.transaction_time,
                'created_at': tx.created_at.isoformat() if tx.created_at else None,
                'reason': tx.customer_name,  # 调整原因存储在customer_name字段
                'receipt_filename': tx.receipt_filename,
                'print_count': tx.print_count or 0,
                'has_receipt': bool(tx.receipt_filename)
            })
        
        return jsonify({
            'success': True,
            'transactions': result,
            'total_count': len(result)
        })
        
    except Exception as e:
        logger.error(f"Get adjust balance transactions failed: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

# 新增：PDF票据生成和打印API for 余额调整（支持HTML转PDF）
@balance_bp.route('/adjust/transactions/<int:transaction_id>/print-receipt', methods=['POST'])
@token_required
@has_permission('balance_manage')
def print_adjust_balance_receipt(current_user, transaction_id):
    """生成并打印余额调整票据PDF（支持从HTML内容生成）"""
    
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
    
    if not transaction_id:
        return jsonify({'success': False, 'message': '交易ID参数缺失'}), 400
    
    session = DatabaseService.get_session()
    data = request.get_json() or {}
    
    try:
        # 获取交易记录
        transaction = session.query(ExchangeTransaction).filter_by(
            id=transaction_id,
            branch_id=current_user['branch_id'],
            type='adjust_balance'  # 修复：与创建时使用相同的类型
        ).first()
        
        if not transaction:
            return jsonify({'success': False, 'message': '余额调整交易记录不存在'}), 404
        
        # 获取语言参数，默认为中文
        language = data.get('language', 'zh')
        
        # 生成PDF文件路径
        file_path = SimplePDFService.get_receipt_file_path(
            transaction.transaction_no, 
            transaction.transaction_date,
            language
        )
        
        # 直接使用SimplePDFService统一硬编码格式生成PDF
        from services.balance_service import BalanceService
        # 设置重新打印时间（如果是重新打印）
        reprint_time = datetime.now() if transaction.print_count and transaction.print_count > 0 else None
        pdf_content = BalanceService.generate_adjustment_receipt(transaction, session, reprint_time, language)
        
        # 保存PDF到文件
        pdf_bytes = base64.b64decode(pdf_content)
        with open(file_path, 'wb') as f:
            f.write(pdf_bytes)
        success = True
        
        if not success:
            return jsonify({'success': False, 'message': 'PDF生成失败'}), 500
        
        # 更新交易记录的票据信息
        if not transaction.receipt_filename:
            # 只有第一次打印时才设置文件名
            transaction.receipt_filename = os.path.basename(file_path)
        
        # 增加打印次数
        transaction.print_count = (transaction.print_count or 0) + 1
        
        # 记录系统日志
        log = SystemLog(
            operation='PRINT_ADJUST_BALANCE_RECEIPT',
            operator_id=current_user['id'],
            log_type='balance',
            action=f"打印余额调整单据 {transaction.transaction_no}",
            details=f"第{transaction.print_count}次打印，文件: {transaction.receipt_filename}，方法: SimplePDFService硬编码格式，语言: {language}",
            ip_address=request.remote_addr,
            created_at=datetime.now()
        )
        session.add(log)
        
        session.commit()
        
        # 【修复】根据语言返回相应的成功消息，包含打印次数
        success_messages = {
            'zh': f'余额调整单据生成成功，第{transaction.print_count}次打印',
            'en': f'Balance adjustment receipt generated successfully, print #{transaction.print_count}',
            'th': f'ใบเสร็จการปรับยอดคงเหลือสร้างสำเร็จ ครั้งที่ {transaction.print_count}'
        }
        success_message = success_messages.get(language, success_messages['zh'])
        
        return jsonify({
            'success': True,
            'message': success_message,
            'receipt_filename': transaction.receipt_filename,
            'print_count': transaction.print_count,
            'file_path': file_path
        })
        
    except Exception as e:
        logger.error(f"Print adjust balance receipt failed: {str(e)}")
        session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@balance_bp.route('/initial/print-summary', methods=['POST'])
@token_required
@has_permission('balance_manage')
def print_initial_balance_summary(current_user):
    """生成并打印初始化余额汇总PDF（从前端HTML内容生成）"""
    data = request.get_json()
    
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
    
    session = DatabaseService.get_session()
    
    try:
        # 获取前端传递的HTML内容或数据
        html_content = data.get('html_content')
        transaction_records = data.get('transaction_records', [])
        
        # 生成汇总单据编号
        now = datetime.now()
        summary_no = f"INIT{now.strftime('%Y%m%d%H%M%S')}"
        
        # 获取语言参数
        language = data.get('language', 'zh')
        
        # 添加调试信息
        logger.info(f"接收到的语言参数: {language}")
        logger.info(f"完整的请求数据: {data}")
        
        # 生成PDF文件路径
        file_path = SimplePDFService.get_receipt_file_path(
            summary_no, 
            now.date(),
            language
        )
        
        success = False
        
        # 强制使用后端ReportLab生成PDF（确保签名标签正确）
        if transaction_records:
            # 获取网点和操作员信息
            operator = session.query(Operator).filter_by(id=current_user['id']).first()
            branch = session.query(Branch).filter_by(id=operator.branch_id if operator else current_user['branch_id']).first()
            
            fallback_data = {
                'transaction_no': summary_no,
                'branch_name': branch.branch_name if branch else '未知网点',
                'formatted_datetime': now.strftime('%Y-%m-%d %H:%M:%S'),
                'operator_name': operator.name if operator else '未知操作员',
                'total_currencies': len(transaction_records),
                'transaction_records': transaction_records
            }
            
            # 使用SimplePDFService统一硬编码格式
            pdf_content = SimplePDFService.generate_summary_receipt(fallback_data, language)
            
            # 保存PDF到文件
            pdf_bytes = base64.b64decode(pdf_content)
            with open(file_path, 'wb') as f:
                f.write(pdf_bytes)
            success = True
        
        if not success:
            return jsonify({'success': False, 'message': 'PDF生成失败，请检查数据格式'}), 500
        
        # 记录系统日志
        log = SystemLog(
            operation='PRINT_INITIAL_BALANCE_SUMMARY',
            operator_id=current_user['id'],
            log_type='balance',
            action=f"打印期初余额汇总单据 {summary_no}",
            details=f"生成方式: ReportLab后端生成PDF，文件: {os.path.basename(file_path)}",
            ip_address=request.remote_addr,
            created_at=now
        )
        session.add(log)
        
        session.commit()
        
        # 根据语言返回对应的成功消息
        success_messages = {
            'zh': '期初余额汇总单据生成成功',
            'en': 'Initial balance summary document generated successfully',
            'th': 'สร้างเอกสารสรุปยอดเริ่มต้นสำเร็จ'
        }
        success_message = success_messages.get(language, success_messages['zh'])
        
        return jsonify({
            'success': True,
            'message': success_message,
            'summary_no': summary_no,
            'receipt_filename': os.path.basename(file_path),
            'file_path': file_path
        })
        
    except Exception as e:
        logger.error(f"Print initial balance summary failed: {str(e)}")
        session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@balance_bp.route('/initial/download-summary/<summary_no>', methods=['GET'])
@token_required
@has_permission('balance_manage')
def download_initial_balance_summary(current_user, summary_no):
    """下载初始化余额汇总PDF"""
    
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
    
    if not summary_no:
        return jsonify({'success': False, 'message': '汇总单号参数缺失'}), 400
    
    try:
        # 获取语言参数
        language = request.args.get('language', 'zh')
        logger.info(f"下载汇总PDF - 语言参数: {language}, 汇总单号: {summary_no}")
        
        # 根据语言构建正确的文件名
        if language == 'en':
            filename = f"{summary_no}_en.pdf"
        elif language == 'th':
            filename = f"{summary_no}_th.pdf"
        else:  # zh或其他语言
            filename = f"{summary_no}.pdf"
        
        logger.info(f"构建的文件名: {filename}")
        
        # 构建文件路径 - 尝试多种语言版本
        possible_paths = []
        
        # 尝试指定语言版本
        possible_paths.append(SimplePDFService.get_receipt_file_path(
            summary_no, 
            datetime.now().date(),
            language
        ))
        
        # 如果指定语言不是中文，也尝试中文版本作为备用
        if language != 'zh':
            possible_paths.append(SimplePDFService.get_receipt_file_path(
                summary_no, 
                datetime.now().date(),
                'zh'
            ))
        
        # 查找存在的文件
        file_path = None
        for i, path in enumerate(possible_paths):
            logger.info(f"检查文件路径 {i+1}: {path} - 存在: {os.path.exists(path)}")
            if os.path.exists(path):
                file_path = path
                logger.info(f"找到文件: {file_path}")
                break
        
        if not file_path:
            logger.error(f"所有可能的文件路径都不存在: {possible_paths}")
            return jsonify({'success': False, 'message': '汇总单据文件不存在'}), 404
        
        # 记录下载日志
        session = DatabaseService.get_session()
        try:
            log = SystemLog(
                operation='DOWNLOAD_INITIAL_BALANCE_SUMMARY',
                operator_id=current_user['id'],
                log_type='balance',
                action=f"下载期初余额汇总单据 {summary_no}",
                details=f"文件: 期初余额汇总_{summary_no}.pdf",
                ip_address=request.remote_addr,
                created_at=datetime.now()
            )
            session.add(log)
            session.commit()
        except Exception as log_e:
            logger.error(f"Failed to log download action: {str(log_e)}")
        finally:
            DatabaseService.close_session(session)
        
        # 返回文件
        from flask import send_file
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Download initial balance summary failed: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 新增：历史单据查询和重新打印API
@balance_bp.route('/historical/transactions/<transaction_no>/reprint', methods=['POST'])
@token_required
@has_permission('balance_manage')
def reprint_historical_balance_receipt(current_user, transaction_no):
    """重新打印历史余额调整单据"""
    
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
    
    if not transaction_no:
        return jsonify({'success': False, 'message': '交易号参数缺失'}), 400
    
    session = DatabaseService.get_session()
    
    try:
        # 查询历史交易记录（不限制网点，但需要管理员权限）
        transaction = session.query(ExchangeTransaction).filter_by(
            transaction_no=transaction_no,
            type='adjust_balance'
        ).first()
        
        if not transaction:
            return jsonify({'success': False, 'message': '历史交易记录不存在'}), 404
        
        # 检查权限：如果不是同网点，需要管理员权限
        if transaction.branch_id != current_user['branch_id']:
            if not has_permission('manage_all_branches')(lambda: True):
                return jsonify({'success': False, 'message': '无权限访问其他网点的历史记录'}), 403
        
        # 获取相关信息
        currency = session.query(Currency).filter_by(id=transaction.currency_id).first()
        operator = session.query(Operator).filter_by(id=transaction.operator_id).first()
        
        if not currency:
            return jsonify({'success': False, 'message': '币种信息不存在'}), 404
        
        # 检查PDF文件是否存在
        file_path = SimplePDFService.get_receipt_file_path(
            transaction.transaction_no, 
            transaction.transaction_date
        )
        
        pdf_exists = os.path.exists(file_path)
        
        if not pdf_exists:
            # 重新生成PDF
            pdf_data = {
                'transaction_no': transaction.transaction_no,
                'adjustment_date': transaction.transaction_date.strftime('%Y/%m/%d') if transaction.transaction_date else '',
                'adjustment_time': transaction.transaction_time or '',
                'currency_code': currency.currency_code,
                'currency_name': currency.currency_name,
                'before_balance': float(transaction.balance_before or 0),
                'adjustment_amount': abs(float(transaction.amount or 0)),
                'adjustment_type': 'increase' if float(transaction.amount or 0) >= 0 else 'decrease',
                'after_balance': float(transaction.balance_after or 0),
                'reason': transaction.customer_name or '历史调整',
                'operator_name': operator.name if operator else '系统操作'
            }
            
            # 使用SimplePDFService统一硬编码格式
            from services.balance_service import BalanceService
            # 历史单据重新打印，设置重新打印时间
            reprint_time = datetime.now()
            # 【修复】传递语言参数，默认为中文
            language = data.get('language', 'zh')
            pdf_content = BalanceService.generate_adjustment_receipt(transaction, session, reprint_time, language)
            
            # 保存PDF到文件
            pdf_bytes = base64.b64decode(pdf_content)
            with open(file_path, 'wb') as f:
                f.write(pdf_bytes)
            success = True
            
            if not success:
                return jsonify({'success': False, 'message': 'PDF重新生成失败'}), 500
        
        # 更新打印次数
        transaction.print_count = (transaction.print_count or 0) + 1
        
        # 如果没有票据文件名，设置一个
        if not transaction.receipt_filename:
            transaction.receipt_filename = os.path.basename(file_path)
        
        # 记录系统日志
        log = SystemLog(
            operation='REPRINT_HISTORICAL_BALANCE_RECEIPT',
            operator_id=current_user['id'],
            log_type='balance',
            action=f"重新打印历史余额调整单据 {transaction.transaction_no}",
            details=f"第{transaction.print_count}次打印（历史单据），文件: {transaction.receipt_filename}",
            ip_address=request.remote_addr,
            created_at=datetime.now()
        )
        session.add(log)
        
        session.commit()
        
        # 【修复】根据语言返回相应的成功消息
        success_messages = {
            'zh': '历史单据重新打印成功',
            'en': 'Historical receipt reprinted successfully',
            'th': 'พิมพ์ใบเสร็จประวัติซ้ำสำเร็จ'
        }
        success_message = success_messages.get(language, success_messages['zh'])
        
        return jsonify({
            'success': True,
            'message': success_message,
            'receipt_filename': transaction.receipt_filename,
            'print_count': transaction.print_count,
            'file_path': file_path,
            'is_historical': True,
            'original_date': transaction.transaction_date.isoformat() if transaction.transaction_date else None
        })
        
    except Exception as e:
        logger.error(f"Reprint historical balance receipt failed: {str(e)}")
        session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@balance_bp.route('/alert-status/<int:currency_id>', methods=['GET'])
@token_required
@has_permission('balance_manage')
def get_balance_alert_status(current_user, currency_id):
    """获取余额报警状态"""
    try:
        from services.balance_alert_service import BalanceAlertService
        
        branch_id = current_user['branch_id']
        alert_info = BalanceAlertService.get_balance_alert_info(currency_id, branch_id)
        
        return jsonify({
            'success': True,
            'alert_info': alert_info
        })
    except Exception as e:
        logger.error(f"获取余额报警状态失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@balance_bp.route('/current/<int:currency_id>', methods=['GET'])
@token_required
@has_permission('balance_manage')
def get_current_balance(current_user, currency_id):
    """获取当前余额"""
    try:
        branch_id = current_user['branch_id']
        session = DatabaseService.get_session()
        try:
            # 获取当前余额
            balance_record = session.query(CurrencyBalance).filter(
                CurrencyBalance.branch_id == branch_id,
                CurrencyBalance.currency_id == currency_id
            ).first()
            
            current_balance = float(balance_record.balance) if balance_record and balance_record.balance else 0.0
            
            return jsonify({
                'success': True,
                'balance': current_balance,
                'last_updated': balance_record.updated_at.isoformat() if balance_record and balance_record.updated_at else None
            })
        finally:
            DatabaseService.close_session(session)
            
    except Exception as e:
        logger.error(f"获取当前余额失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@balance_bp.route('/check-transaction-impact', methods=['POST'])
@token_required
@has_permission('exchange_manage')
def check_transaction_impact(current_user):
    """检查交易对余额的影响"""
    try:
        from services.balance_alert_service import BalanceAlertService
        from decimal import Decimal
        
        data = request.get_json()
        currency_id = data.get('currency_id')
        transaction_amount = Decimal(str(data.get('transaction_amount', 0)))
        transaction_type = data.get('transaction_type')  # 'buy' 或 'sell'
        
        if not currency_id or not transaction_amount or not transaction_type:
            return jsonify({'success': False, 'message': '参数不完整'}), 400
        
        branch_id = current_user['branch_id']
        impact_analysis = BalanceAlertService.check_transaction_impact(
            currency_id, branch_id, transaction_amount, transaction_type
        )
        
        return jsonify({
            'success': True,
            'impact_analysis': impact_analysis
        })
        
    except Exception as e:
        logger.error(f"检查交易影响失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@balance_bp.route('/initial/currencies-status', methods=['GET'])
@token_required
@has_permission('balance_manage')
def get_currencies_initial_status(*args, **kwargs):
    """获取币种期初设置状态 - 用于前端显示哪些币种可以期初"""
    current_user = kwargs.get('current_user') or args[0]
    
    session = DatabaseService.get_session()
    try:
        # 获取所有币种
        currencies = session.query(Currency).all()
        
        result = []
        for currency in currencies:
            # 检查该币种是否已经期初过
            has_initial = session.query(ExchangeTransaction).filter_by(
                branch_id=current_user['branch_id'],
                currency_id=currency.id,
                type='initial_balance'
            ).first()
            
            # 获取当前余额
            balance = session.query(CurrencyBalance).filter_by(
                branch_id=current_user['branch_id'],
                currency_id=currency.id
            ).first()
            
            currency_status = {
                'currency_id': currency.id,
                'currency_code': currency.currency_code,
                'currency_name': currency.currency_name,
                'flag_code': currency.flag_code,
                'custom_flag_filename': currency.custom_flag_filename,  # 添加自定义图标文件名
                'current_balance': float(balance.balance) if balance else 0.0,
                'has_initial': bool(has_initial),
                'can_initial': not bool(has_initial)  # 只有未期初的币种才能期初
            }
            
            # 如果已经期初过，添加期初信息
            if has_initial:
                # 【修复】根据币种类型正确返回期初金额
                # 获取网点信息确定本币
                operator = session.query(Operator).filter_by(id=current_user['id']).first()
                branch = session.query(Branch).filter_by(id=operator.branch_id).first() if operator else None
                
                # 判断是否为本币
                is_base_currency = (branch and branch.base_currency_id == currency.id)
                
                if is_base_currency:
                    # 本币：期初金额使用local_amount字段
                    initial_amount = float(has_initial.local_amount)
                else:
                    # 外币：期初金额使用amount字段
                    initial_amount = float(has_initial.amount)
                
                currency_status.update({
                    'initial_date': has_initial.transaction_date.isoformat(),
                    'initial_time': has_initial.transaction_time,
                    'initial_operator': has_initial.operator.name if has_initial.operator else '未知',
                    'initial_amount': initial_amount,
                    'is_base': is_base_currency  # 添加是否为本币的标识
                })
            else:
                # 未期初的币种也需要判断是否为本币
                operator = session.query(Operator).filter_by(id=current_user['id']).first()
                branch = session.query(Branch).filter_by(id=operator.branch_id).first() if operator else None
                is_base_currency = (branch and branch.base_currency_id == currency.id)
                currency_status['is_base'] = is_base_currency
            
            result.append(currency_status)
        
        # 统计信息
        total_currencies = len(result)
        initialized_count = sum(1 for c in result if c['has_initial'])
        pending_count = total_currencies - initialized_count
        
        return jsonify({
            'success': True,
            'data': result,
            'summary': {
                'total_currencies': total_currencies,
                'initialized_count': initialized_count,
                'pending_count': pending_count,
                'can_add_more': pending_count > 0
            }
        })
        
    except Exception as e:
        logger.error(f"获取币种期初状态失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@balance_bp.route('/set-to-zero', methods=['POST'])
@token_required
@has_permission('balance_manage')
@check_business_lock_for_balance
def set_currencies_to_zero(*args, **kwargs):
    """批量设置币种余额为0 - 不是期初操作"""
    current_user = kwargs.get('current_user') or args[0]
    data = request.get_json()
    
    if not data or 'currencies' not in data:
        return jsonify({'success': False, 'message': '缺少必要的参数'}), 400
    
    currencies_to_set = data['currencies']
    branch_id = data.get('branch_id', current_user['branch_id'])
    
    # 验证权限：只能操作自己的网点
    if branch_id != current_user['branch_id'] and not current_user.get('is_admin', False):
        return jsonify({'success': False, 'message': '只能操作自己的网点'}), 403
    
    if not currencies_to_set:
        return jsonify({'success': False, 'message': '没有要设置的币种'}), 400
    
    session = DatabaseService.get_session()
    try:
        updated_currencies = []
        
        for currency_data in currencies_to_set:
            currency_id = currency_data.get('currency_id')
            currency_code = currency_data.get('currency_code')
            
            if not currency_id:
                continue
            
            # 检查币种是否存在
            currency = session.query(Currency).get(currency_id)
            if not currency:
                logger.warning(f"币种 {currency_id} 不存在，跳过")
                continue
            
            # 检查是否已经期初过（已期初的币种不能设置为0）
            has_initial = session.query(ExchangeTransaction).filter_by(
                branch_id=branch_id,
                currency_id=currency_id,
                type='initial_balance'
            ).first()
            
            if has_initial:
                logger.warning(f"币种 {currency_code} 已期初，跳过设置为0")
                continue
            
            # 查找或创建余额记录
            balance = session.query(CurrencyBalance).filter_by(
                branch_id=branch_id,
                currency_id=currency_id
            ).first()
            
            old_balance = float(balance.balance) if balance else 0.0
            
            if balance:
                # 更新现有余额
                balance.balance = 0.0
                balance.updated_at = datetime.now()
            else:
                # 创建新的余额记录
                balance = CurrencyBalance(
                    branch_id=branch_id,
                    currency_id=currency_id,
                    balance=0.0,
                    updated_at=datetime.now()
                )
                session.add(balance)
            
            updated_currencies.append({
                'currency_id': currency_id,
                'currency_code': currency_code,
                'old_balance': old_balance,
                'new_balance': 0.0,
                'change': -old_balance
            })
        
        if not updated_currencies:
            return jsonify({'success': False, 'message': '没有可设置的币种'}), 400
        
        # 记录系统日志
        currency_codes = [c['currency_code'] for c in updated_currencies]
        log = SystemLog(
            operation='SET_BALANCE_TO_ZERO',
            operator_id=current_user['id'],
            log_type='balance',
            action=f"批量设置币种余额为0",
            details=f"网点ID: {branch_id}, 币种: {', '.join(currency_codes)}, 共 {len(updated_currencies)} 个币种",
            ip_address=request.remote_addr,
            created_at=datetime.now()
        )
        session.add(log)
        
        session.commit()
        
        logger.info(f"成功设置 {len(updated_currencies)} 个币种余额为0")
        
        return jsonify({
            'success': True,
            'message': f'成功设置 {len(updated_currencies)} 个币种余额为0',
            'updated_currencies': updated_currencies
        })
        
    except Exception as e:
        logger.error(f"设置币种余额为0失败: {str(e)}")
        session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)
