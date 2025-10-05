from flask import Blueprint, request, jsonify
from datetime import datetime, date
from models.exchange_models import ExchangeTransaction, Currency, CurrencyBalance, ExchangeRate, Branch, SystemLog, Operator
from services.db_service import DatabaseService
from services.auth_service import token_required, has_permission, check_business_lock_for_transactions
from services.transaction_split_service import TransactionSplitService
from sqlalchemy import and_, or_, func
import logging
import random
import string
from decimal import Decimal, ROUND_HALF_UP
from services.balance_service import BalanceService
from utils.transaction_utils import generate_transaction_no
from utils.multilingual_log_service import multilingual_logger
from services.unified_log_service import log_exchange_transaction
import os
from utils.language_utils import get_current_language
from utils.backend_i18n import t, get_request_language

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add constant for rate precision
RATE_PRECISION = Decimal('0.0001')

exchange_bp = Blueprint('exchange', __name__, url_prefix='/api/exchange')

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
            print(f"兑换交易日志记录失败: {log_error}")
        
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
            }
        })
    except Exception as e:
        logger.error(f"Exchange transaction failed: {str(e)}")
        session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

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
    logger.info(f"🔍 验证API收到请求: {data}")
    logger.info(f"🔍 当前用户: {current_user}")
    
    if not data or not all(k in data for k in ['type', 'currency_id', 'amount']):
        logger.error(f"❌ 缺少必要参数: {data}")
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
                logger.info(f"🔍 创建新的外币余额记录，初始余额为0")
            else:
                # 卖出外币时，必须有余额记录
                language = get_request_language(request)
                return jsonify({'success': False, 'message': t('validation.no_balance_record', language)}), 400

        amount = float(data['amount'])
        exchange_type = data['type']  # 'buy' or 'sell'

        # 检查余额是否充足
        logger.info(f"🔍 开始检查余额 - exchange_type: {exchange_type}, amount: {amount}")
        
        if exchange_type == 'buy':
            logger.info(f"🔍 买入外币模式 - 需要检查本币余额")
            try:
                # 网点买入外币时，需要支付本币给客户，应该检查本币余额
                # 计算需要支付的本币金额
                local_amount_needed = amount * float(exchange_rate.buy_rate)
                logger.info(f"🔍 计算本币需求: {amount} * {float(exchange_rate.buy_rate)} = {local_amount_needed}")
                
                # 获取网点信息以确定本币ID
                branch = session.query(Branch).filter_by(id=current_user['branch_id']).first()
                logger.info(f"🔍 查询网点信息: {branch}")
                
                if not branch or not branch.base_currency_id:
                    logger.error(f"❌ 网点信息不完整: branch={branch}, base_currency_id={branch.base_currency_id if branch else None}")
                    language = get_request_language(request)
                    return jsonify({
                        'success': False,
                        'message': t('validation.branch_info_incomplete', language)
                    }), 400
                
                logger.info(f"🔍 本币ID: {branch.base_currency_id}")
                
                # 获取本币余额
                base_currency_balance = session.query(CurrencyBalance).filter_by(
                    branch_id=current_user['branch_id'],
                    currency_id=branch.base_currency_id
                ).first()
                
                logger.info(f"🔍 本币余额记录: {base_currency_balance}")
                
                if not base_currency_balance:
                    logger.error(f"❌ 本币余额记录不存在")
                    language = get_request_language(request)
                    return jsonify({
                        'success': False,
                        'message': t('validation.base_currency_balance_not_exist', language),
                        'available_amount': 0
                    }), 400
                
                logger.info(f"🔍 当前本币余额: {base_currency_balance.balance}, 需要: {local_amount_needed}")
                    
                if float(base_currency_balance.balance) < local_amount_needed:
                    # 获取本币信息以显示准确的货币名称
                    base_currency = session.query(Currency).filter_by(id=branch.base_currency_id).first()
                    base_currency_name = base_currency.currency_name if base_currency else '本币'
                    base_currency_code = base_currency.currency_code if base_currency else ''
                    
                    current_balance = float(base_currency_balance.balance)
                    shortfall = local_amount_needed - current_balance
                    
                    logger.info(f"🔍 详细计算:")
                    logger.info(f"🔍 - 需要金额: {local_amount_needed}")
                    logger.info(f"🔍 - 当前余额: {current_balance}")  
                    logger.info(f"🔍 - 计算差额: {local_amount_needed} - {current_balance} = {shortfall}")
                    
                    # 使用后端国际化系统
                    language = get_request_language(request)
                    error_msg = t('balance.foreign_currency_insufficient', language,
                                currency_name=base_currency_name,
                                required_amount=local_amount_needed,
                                currency_code=base_currency_code,
                                current_balance=current_balance,
                                shortfall=shortfall)
                    
                    logger.info(f"❌ 本币余额不足: {error_msg}")
                    
                    return jsonify({
                        'success': False,
                        'message': error_msg,
                        'available_amount': current_balance,
                        'required_amount': local_amount_needed,
                        'shortfall': shortfall
                    }), 400
                else:
                    logger.info(f"✅ 本币余额充足")
                    
            except Exception as e:
                logger.error(f"❌ 检查本币余额时出错: {str(e)}")
                language = get_request_language(request)
                return jsonify({
                    'success': False,
                    'message': t('balance.balance_check_error', language, error=str(e))
                }), 500
                
        else:
            logger.info(f"🔍 卖出外币模式 - 需要检查外币库存")
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
                logger.info(f"❌ 外币库存不足: {error_msg}")
                
                return jsonify({
                    'success': False,
                    'message': error_msg,
                    'available_amount': float(balance.balance)
                }), 400
            else:
                logger.info(f"✅ 外币库存充足")

        # 返回验证结果和当前汇率
        language = get_request_language(request)
        return jsonify({
            'success': True,
            'message': t('validation.validation_passed', language),
            'buy_rate': float(exchange_rate.buy_rate),
            'sell_rate': float(exchange_rate.sell_rate),
            'available_amount': float(balance.balance)
        })

    except Exception as e:
        logger.error(f"Exchange validation failed: {str(e)}")
        language = get_request_language(request)
        return jsonify({'success': False, 'message': t('system.system_error', language, error=str(e))}), 500
    finally:
        DatabaseService.close_session(session)

@exchange_bp.route('/transactions/today', methods=['GET'])
@token_required
@has_permission('transaction_execute')
def get_today_transactions(*args):
    """获取今日交易列表"""
    current_user = args[0]
    session = DatabaseService.get_session()
    try:
        today = date.today()
        
        # 查询今日所有交易
        transactions = session.query(
            ExchangeTransaction,
            Currency.currency_code,
            Currency.currency_name,
            func.concat(Operator.name, ' (', Operator.login_code, ')').label('operator_name')
        ).join(
            Currency, ExchangeTransaction.currency_id == Currency.id
        ).join(
            Operator, ExchangeTransaction.operator_id == Operator.id
        ).filter(
            ExchangeTransaction.branch_id == current_user['branch_id'],
            ExchangeTransaction.transaction_date == today,
            # 只显示买入、卖出和冲减类型的交易
            ExchangeTransaction.type.in_(['buy', 'sell', 'reversal'])
        ).order_by(
            ExchangeTransaction.created_at.desc()
        ).all()

        result = []
        for tx, currency_code, currency_name, operator_name in transactions:
            # 检查是否已被冲减
            is_reversed = session.query(ExchangeTransaction).filter(
                ExchangeTransaction.type == 'reversal',
                ExchangeTransaction.original_transaction_no == tx.transaction_no
            ).first() is not None

            result.append({
                'id': tx.id,
                'transaction_no': tx.transaction_no,
                'type': tx.type,
                'currency_code': currency_code,
                'currency_name': currency_name,
                'amount': float(tx.amount),
                'rate': float(tx.rate),
                'local_amount': float(tx.local_amount),
                'customer_name': tx.customer_name,
                'operator_name': operator_name,
                'transaction_time': tx.transaction_time,
                'is_reversed': is_reversed,
                'original_transaction_no': tx.original_transaction_no
            })

        return jsonify({
            'success': True,
            'transactions': result
        })

    except Exception as e:
        logger.error(f"Error in get_today_transactions: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

# 新增：PDF票据生成和打印API
@exchange_bp.route('/transactions/<int:transaction_id>/print-receipt', methods=['POST'])
@token_required
@has_permission('transaction_execute')
def print_receipt(*args, **kwargs):
    """生成并打印交易票据PDF"""
    # 修复参数顺序问题：从装饰器获取current_user，从路径获取transaction_id
    current_user = args[0] if len(args) > 0 else kwargs.get('current_user')
    transaction_id = args[1] if len(args) > 1 else kwargs.get('transaction_id')
    
    logger.info(f"=== 开始打印票据 ===")
    logger.info(f"transaction_id: {transaction_id}")
    logger.info(f"current_user: {current_user}")
    
    if not current_user:
        logger.error("用户信息获取失败")
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
    
    if not transaction_id:
        logger.error("交易ID参数缺失")
        return jsonify({'success': False, 'message': '交易ID参数缺失'}), 400
    
    # 获取请求数据，包括语言参数
    request_data = request.get_json() or {}
    language = request_data.get('language', 'zh')  # 默认中文
    logger.info(f"请求语言: {language}")
    
    session = DatabaseService.get_session()
    
    try:
        logger.info("=== 步骤1：获取交易记录 ===")
        # 获取交易记录
        transaction = session.query(ExchangeTransaction).filter_by(
            id=transaction_id,
            branch_id=current_user['branch_id']
        ).first()
        
        if not transaction:
            logger.error(f"交易记录不存在: transaction_id={transaction_id}, branch_id={current_user['branch_id']}")
            return jsonify({'success': False, 'message': '交易记录不存在'}), 404
        
        logger.info(f"找到交易记录: {transaction.transaction_no}")
        
        logger.info("=== 步骤2：获取相关信息 ===")
        # 获取相关信息
        currency = session.query(Currency).filter_by(id=transaction.currency_id).first()
        branch = session.query(Branch).filter_by(id=transaction.branch_id).first()
        base_currency = session.query(Currency).filter_by(id=branch.base_currency_id).first()
        
        logger.info(f"货币: {currency.currency_code if currency else 'None'}")
        logger.info(f"网点: {branch.branch_name if branch else 'None'}")
        logger.info(f"基础货币: {base_currency.currency_code if base_currency else 'None'}")
        
        # 准备PDF数据
        logger.info("=== 步骤3：导入PDF服务 ===")
        try:
            # 已改用SimplePDFService，无需PDFReceiptService
            logger.info("PDF服务导入成功")
        except ImportError as e:
            logger.error(f"PDF服务导入失败: {e}")
            return jsonify({'success': False, 'message': 'PDF服务不可用'}), 500
        
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
        
        logger.info("=== 步骤4：准备PDF数据 ===")
        # 确定交易类型描述
        if transaction.type == 'buy':
            transaction_type_desc = '买入'
        elif transaction.type == 'sell':
            transaction_type_desc = '卖出'
        else:
            transaction_type_desc = transaction.type
        
        # 确定金额显示
        if transaction.type == 'buy':
            # 银行买入外币，客户卖出外币
            from_amount = abs(float(transaction.amount))
            from_currency = currency.currency_code
            to_amount = abs(float(transaction.local_amount))
            to_currency = base_currency.currency_code
        else:
            # 银行卖出外币，客户买入外币
            from_amount = abs(float(transaction.local_amount))
            from_currency = base_currency.currency_code
            to_amount = abs(float(transaction.amount))
            to_currency = currency.currency_code
        
        pdf_data = {
            'transaction_no': transaction.transaction_no,
            'branch_name': branch.branch_name,
            'branch_code': branch.branch_code,
            'transaction_type_desc': transaction_type_desc,
            'currency_code': currency.currency_code,
            'formatted_datetime': format_transaction_time(transaction.transaction_date, transaction.transaction_time),
            'from_amount': from_amount,
            'from_currency': from_currency,
            'to_amount': to_amount,
            'to_currency': to_currency,
            'rate': float(transaction.rate),
            'foreign_currency': currency.currency_code,
            'base_currency': base_currency.currency_code,
            'customer_name': transaction.customer_name or '',
            'customer_id': transaction.customer_id or '',
            'purpose': transaction.purpose or '',
            'remarks': transaction.remarks or ''
        }
        
        logger.info(f"PDF数据准备完成: {pdf_data}")
        
        logger.info("=== 步骤5：生成PDF文件路径 ===")
        # 生成PDF文件路径（使用SimplePDFService保持硬编码格式）
        from services.simple_pdf_service import SimplePDFService
        file_path = SimplePDFService.get_receipt_file_path(
            transaction.transaction_no, 
            transaction.transaction_date
        )
        logger.info(f"PDF文件路径: {file_path}")
        
        logger.info("=== 步骤6：生成PDF ===")
        # 使用SimplePDFService的硬编码格式（保持原有格式）
        try:
            # 使用SimplePDFService生成PDF（返回base64内容），传递语言参数
            # 设置重新打印时间（如果是重新打印）
            reprint_time = datetime.now() if transaction.print_count and transaction.print_count > 0 else None
            pdf_content = SimplePDFService.generate_exchange_receipt(transaction, session, reprint_time, language)
            
            # 将base64内容保存到文件系统（用于下载）
            import base64
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'wb') as f:
                f.write(base64.b64decode(pdf_content))
            
            logger.info(f"PDF文件已保存到: {file_path}")
            success = True
            
        except Exception as pdf_error:
            logger.error(f"PDF生成过程中发生异常: {str(pdf_error)}")
            import traceback
            logger.error(f"PDF生成异常详情: {traceback.format_exc()}")
            return jsonify({'success': False, 'message': f'PDF生成异常: {str(pdf_error)}'}), 500
        
        if not success:
            logger.error("PDF生成失败")
            return jsonify({'success': False, 'message': 'PDF生成失败'}), 500
        
        logger.info("=== 步骤7：更新数据库记录 ===")
        # 更新交易记录的票据信息
        if not transaction.receipt_filename:
            # 只有第一次打印时才设置文件名
            transaction.receipt_filename = os.path.basename(file_path)
        
        # 增加打印次数
        transaction.print_count = (transaction.print_count or 0) + 1
        
        # 记录系统日志
        log = SystemLog(
            operation='PRINT_RECEIPT',
            operator_id=current_user['id'],
            log_type='exchange',
            action=f"打印票据 {transaction.transaction_no}",
            details=f"第{transaction.print_count}次打印，文件: {transaction.receipt_filename}",
            ip_address=request.remote_addr,
            created_at=datetime.now()
        )
        session.add(log)
        
        session.commit()
        
        logger.info("=== 票据生成成功 ===")
        
        # 根据语言返回不同的成功消息
        messages = {
            'zh': f'外币兑换票据生成成功，第{transaction.print_count}次打印',
            'en': f'Exchange receipt generated successfully, print #{transaction.print_count}',
            'th': f'สร้างใบเสร็จแลกเปลี่ยนสำเร็จ ครั้งที่ {transaction.print_count}'
        }
        success_message = messages.get(language, messages['zh'])
        
        return jsonify({
            'success': True,
            'message': success_message,
            'receipt_filename': transaction.receipt_filename,
            'print_count': transaction.print_count,
            'file_path': file_path
        })
        
    except Exception as e:
        logger.error(f"Print receipt failed: {str(e)}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@exchange_bp.route('/transactions/<transaction_no>/download-receipt', methods=['GET'])
@token_required
@has_permission('transaction_execute')
def download_receipt(*args, **kwargs):
    """下载交易票据PDF"""
    # 修复参数顺序问题：从装饰器获取current_user，从路径获取transaction_no
    current_user = args[0] if len(args) > 0 else kwargs.get('current_user')
    transaction_no = args[1] if len(args) > 1 else kwargs.get('transaction_no')
    
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
        
        if not transaction.receipt_filename:
            return jsonify({'success': False, 'message': '该交易尚未生成票据'}), 404
        
        # 构建文件路径（使用SimplePDFService保持一致）
        from services.simple_pdf_service import SimplePDFService
        file_path = SimplePDFService.get_receipt_file_path(
            transaction.transaction_no, 
            transaction.transaction_date
        )
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'message': '票据文件不存在'}), 404
        
        # 返回文件
        from flask import send_file
        return send_file(
            file_path,
            as_attachment=True,
            download_name=transaction.receipt_filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Download receipt failed: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@exchange_bp.route('/business-group/<business_group_id>/print-receipt', methods=['POST'])
@token_required
@has_permission('transaction_execute')
def print_dual_direction_receipt(*args, **kwargs):
    """生成并打印双向交易业务组PDF票据"""
    # 修复参数顺序问题：从装饰器获取current_user，从路径获取business_group_id
    current_user = args[0] if len(args) > 0 else kwargs.get('current_user')
    business_group_id = args[1] if len(args) > 1 else kwargs.get('business_group_id')

    logger.info(f"=== 开始打印双向交易票据 ===")
    logger.info(f"business_group_id: {business_group_id}")
    logger.info(f"current_user: {current_user}")

    if not current_user:
        logger.error("用户信息获取失败")
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401

    if not business_group_id:
        logger.error("业务组ID参数缺失")
        return jsonify({'success': False, 'message': '业务组ID参数缺失'}), 400

    # 获取请求数据，包括语言参数
    request_data = request.get_json() or {}
    language = request_data.get('language', 'zh')  # 默认中文
    logger.info(f"请求语言: {language}")

    session = DatabaseService.get_session()

    try:
        logger.info("=== 步骤1：获取业务组交易记录 ===")
        # 获取业务组的所有交易记录
        transactions = session.query(ExchangeTransaction).filter_by(
            business_group_id=business_group_id,
            branch_id=current_user['branch_id']
        ).order_by(ExchangeTransaction.group_sequence).all()

        if not transactions:
            logger.error(f"业务组交易记录不存在: business_group_id={business_group_id}, branch_id={current_user['branch_id']}")
            return jsonify({'success': False, 'message': '业务组交易记录不存在'}), 404

        logger.info(f"找到 {len(transactions)} 条交易记录")

        logger.info("=== 步骤2：获取相关信息 ===")
        # 获取第一条交易的相关信息（所有交易共享客户和网点信息）
        first_transaction = transactions[0]

        # 获取相关数据
        currencies = {}
        for tx in transactions:
            if tx.currency_id not in currencies:
                currency = session.query(Currency).filter_by(id=tx.currency_id).first()
                if currency:
                    currencies[tx.currency_id] = currency

        branch = session.query(Branch).filter_by(id=first_transaction.branch_id).first()
        operator = session.query(Operator).filter_by(id=first_transaction.operator_id).first()

        logger.info(f"涉及币种数量: {len(currencies)}")
        logger.info(f"网点: {branch.branch_name if branch else 'None'}")
        logger.info(f"操作员: {operator.name if operator else 'None'}")

        logger.info("=== 步骤3：构建业务组数据 ===")
        # 构建业务组数据
        business_group_data = {
            'business_group_id': business_group_id,
            'branch_id': current_user['branch_id'],
            'operator_id': first_transaction.operator_id,
            'transaction_date': first_transaction.transaction_date,
            'transaction_time': first_transaction.transaction_time,
            'customer_info': {
                'name': first_transaction.customer_name or '',
                'id_number': first_transaction.customer_id or '',
                'country_code': getattr(first_transaction, 'customer_country_code', '') or '',
                'address': getattr(first_transaction, 'customer_address', '') or '',
                'remarks': first_transaction.remarks or ''
            },
            # 新增字段
            'payment_method': getattr(first_transaction, 'payment_method', 'cash') or 'cash',
            'payment_method_note': getattr(first_transaction, 'payment_method_note', '') or '',
            'transactions': [],
            'denomination_details': []
        }

        # 添加交易记录详情
        for tx in transactions:
            currency = currencies.get(tx.currency_id)
            currency_code = currency.currency_code if currency else 'UNKNOWN'

            business_group_data['transactions'].append({
                'id': tx.id,
                'transaction_no': tx.transaction_no,
                'currency_id': tx.currency_id,
                'currency_code': currency_code,
                'direction': getattr(tx, 'transaction_direction', 'sell') or 'sell',
                'amount': tx.amount,
                'local_amount': tx.local_amount,
                'rate': tx.rate,
                'type': tx.type
            })

        # 由于面值详情信息在当前数据结构中不直接可用，
        # 我们从交易记录中推断面值信息（这是一个简化方案）
        for tx in transactions:
            currency = currencies.get(tx.currency_id)
            if currency:
                business_group_data['denomination_details'].append({
                    'denomination_value': abs(float(tx.amount)),
                    'denomination_type': 'bill',  # 默认纸币类型
                    'quantity': 1,  # 简化为1张
                    'direction': getattr(tx, 'transaction_direction', 'sell') or 'sell',
                    'currency_code': currency.currency_code,
                    'subtotal': abs(float(tx.amount))
                })

        logger.info(f"业务组数据准备完成: {len(business_group_data['transactions'])} 条交易, {len(business_group_data['denomination_details'])} 个面值详情")

        logger.info("=== 步骤4：生成PDF ===")
        # 使用DualDirectionPDFGenerator生成PDF
        try:
            from services.simple_pdf_service import SimplePDFService
            pdf_content = SimplePDFService.generate_dual_direction_receipt(business_group_data, session, language)

            logger.info("双向交易PDF生成成功")
            success = True

        except Exception as pdf_error:
            logger.error(f"PDF生成过程中发生异常: {str(pdf_error)}")
            import traceback
            logger.error(f"PDF生成异常详情: {traceback.format_exc()}")
            return jsonify({'success': False, 'message': f'PDF生成异常: {str(pdf_error)}'}), 500

        if not success:
            logger.error("PDF生成失败")
            return jsonify({'success': False, 'message': 'PDF生成失败'}), 500

        logger.info("=== 步骤5：生成文件路径 ===")
        # 生成文件路径 - 使用第一条交易的流水号_MULTI格式
        from services.simple_pdf_service import SimplePDFService
        file_path = SimplePDFService.get_receipt_file_path(
            f"{first_transaction.transaction_no}_MULTI",
            first_transaction.transaction_date
        )

        # 将base64内容保存到文件系统（用于下载）
        import base64
        import os
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'wb') as f:
            f.write(base64.b64decode(pdf_content))

        logger.info(f"PDF文件已保存到: {file_path}")

        logger.info("=== 步骤6：记录系统日志 ===")
        # 记录系统日志
        log = SystemLog(
            operation='PRINT_DUAL_RECEIPT',
            operator_id=current_user['id'],
            log_type='exchange',
            action=f"打印双向交易票据 {business_group_id}",
            details=f"业务组包含 {len(transactions)} 条交易记录，文件: {os.path.basename(file_path)}",
            ip_address=request.remote_addr,
            created_at=datetime.now()
        )
        session.add(log)

        session.commit()

        logger.info("=== 双向交易票据生成成功 ===")

        # 根据语言返回不同的成功消息
        messages = {
            'zh': f'双向交易票据生成成功，业务组: {business_group_id}',
            'en': f'Dual-direction transaction receipt generated successfully, Group: {business_group_id}',
            'th': f'สร้างใบเสร็จธุรกรรมสองทิศทางสำเร็จ กลุ่ม: {business_group_id}'
        }
        success_message = messages.get(language, messages['zh'])

        return jsonify({
            'success': True,
            'message': success_message,
            'business_group_id': business_group_id,
            'transaction_count': len(transactions),
            'file_path': file_path,
            'pdf_base64': pdf_content  # 添加PDF的base64内容，供前端打印使用
        })

    except Exception as e:
        logger.error(f"Print dual direction receipt failed: {str(e)}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

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
        logger.info(f"[validate_dual_direction] 收到验证请求: {data}")

        # 验证必要字段
        language = get_request_language(request)
        required_fields = ['denomination_data', 'customer_info']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': t('validation.missing_required_field', language, field=field)}), 400

        # 验证客户姓名
        if not data['customer_info'].get('name', '').strip():
            return jsonify({'success': False, 'message': t('customer.name_required', language)}), 400

        # 验证面值组合数据
        denomination_data = data['denomination_data']
        if not denomination_data.get('combinations') or len(denomination_data['combinations']) == 0:
            return jsonify({'success': False, 'message': t('transaction.no_combinations_provided', language)}), 400

        # 获取用户网点信息
        session = DatabaseService.get_session()
        try:
            branch = session.query(Branch).filter_by(id=current_user['branch_id']).first()
            if not branch:
                return jsonify({'success': False, 'message': t('validation.branch_not_found', language)}), 400

            if not branch.base_currency_id:
                return jsonify({'success': False, 'message': t('validation.branch_no_base_currency', language)}), 400

            logger.info(f"[validate_dual_direction] 开始验证，网点ID: {current_user['branch_id']}, 本币ID: {branch.base_currency_id}")

            # 使用TransactionSplitService分析面值组合
            transaction_groups = TransactionSplitService.analyze_denomination_combinations(
                denomination_data, branch.base_currency_id
            )

            if not transaction_groups:
                return jsonify({
                    'success': False,
                    'message': t('transaction.no_valid_combinations', language)
                }), 400

            logger.info(f"[validate_dual_direction] 分析得到 {len(transaction_groups)} 个交易分组")

            # 生成虚拟交易记录用于验证（不实际保存）
            virtual_transaction_records = TransactionSplitService.create_transaction_records(
                business_group_id="VALIDATION_TEMP",
                transaction_groups=transaction_groups,
                branch_id=current_user['branch_id'],
                operator_id=current_user['id'],
                customer_info=data['customer_info'],
                purpose_id=data.get('purpose_id')
            )

            logger.info(f"[validate_dual_direction] 生成 {len(virtual_transaction_records)} 条虚拟交易记录用于验证")

            # 验证余额充足性
            validation_result = TransactionSplitService.validate_balance_sufficiency(
                session, virtual_transaction_records, current_user['branch_id'], language
            )

            if not validation_result['success']:
                logger.info(f"[validate_dual_direction] 余额验证失败: {validation_result['message']}")
                return jsonify({
                    'success': False,
                    'message': validation_result['message']
                }), 400

            # 检查余额阈值报警
            logger.info(f"[validate_dual_direction] 开始检查余额阈值报警")
            threshold_warnings = []

            # 导入余额报警服务
            from services.balance_alert_service import BalanceAlertService

            for record in virtual_transaction_records:
                currency_id = record['currency_id']
                transaction_amount = abs(float(record['amount']))  # 取绝对值作为交易量
                transaction_type = 'buy' if record['amount'] > 0 else 'sell'  # 正数为买入，负数为卖出

                try:
                    # 检查交易对余额的影响
                    impact_result = BalanceAlertService.check_transaction_impact(
                        currency_id, current_user['branch_id'], transaction_amount, transaction_type
                    )

                    # 如果会触发报警，收集警告信息
                    if impact_result.get('will_trigger_alert', False):
                        new_status = impact_result.get('new_status', {})
                        impact_analysis = impact_result.get('impact_analysis', '')

                        # 获取币种信息
                        currency = session.query(Currency).filter_by(id=currency_id).first()
                        currency_name = currency.currency_name if currency else t('system.unknown_currency', language)
                        currency_code = currency.currency_code if currency else 'UNKNOWN'

                        warning_msg = t('balance.threshold_warning', language,
                                      currency_name=currency_name,
                                      currency_code=currency_code,
                                      current_balance=impact_result.get('current_balance', 0),
                                      new_balance=impact_result.get('new_balance', 0),
                                      impact_analysis=impact_analysis)

                        threshold_warnings.append({
                            'currency_id': currency_id,
                            'currency_code': currency_code,
                            'currency_name': currency_name,
                            'warning_message': warning_msg,
                            'warning_level': new_status.get('level', 'warning'),
                            'current_balance': impact_result.get('current_balance', 0),
                            'new_balance': impact_result.get('new_balance', 0)
                        })

                except Exception as e:
                    # 尝试获取币种代码用于日志记录
                    try:
                        currency = session.query(Currency).filter_by(id=currency_id).first()
                        currency_code = currency.currency_code if currency else 'UNKNOWN'
                        logger.error(f"检查币种 {currency_code} (ID: {currency_id}) 的阈值报警时出错: {str(e)}")
                    except:
                        logger.error(f"检查币种 ID {currency_id} 的阈值报警时出错: {str(e)}")
                    continue

            logger.info(f"[validate_dual_direction] 检查到 {len(threshold_warnings)} 个阈值报警")
            logger.info(f"[validate_dual_direction] 验证通过")

            # 返回验证成功结果，包含汇总信息和阈值报警
            response_data = {
                'success': True,
                'message': t('validation.validation_passed_can_execute', language),
                'validation_details': {
                    'transaction_groups': len(transaction_groups),
                    'total_records': len(virtual_transaction_records),
                    'currencies_involved': len(set(record['currency_id'] for record in virtual_transaction_records))
                }
            }

            # 如果有阈值报警，添加到响应中
            if threshold_warnings:
                response_data['threshold_warnings'] = threshold_warnings
                # 如果有严重报警，可以考虑修改消息
                critical_warnings = [w for w in threshold_warnings if w['warning_level'] == 'critical']
                if critical_warnings:
                    response_data['message'] = t('validation.validation_passed_with_critical_warnings', language)
                else:
                    response_data['message'] = t('validation.validation_passed_with_warnings', language)

            return jsonify(response_data)

        finally:
            DatabaseService.close_session(session)

    except Exception as e:
        logger.error(f"双向交易验证失败: {str(e)}")
        language = get_request_language(request)
        return jsonify({
            'success': False,
            'message': t('transaction.validation_error', language) + f': {str(e)}'
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

        # 验证必要字段
        required_fields = ['denomination_data', 'customer_info']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'缺少必要字段: {field}'}), 400

        # 获取用户网点信息
        session = DatabaseService.get_session()
        try:
            branch = session.query(Branch).filter_by(id=current_user['branch_id']).first()
            if not branch:
                return jsonify({'success': False, 'message': '网点信息不存在'}), 400

            # 执行拆分交易
            result = TransactionSplitService.execute_split_transaction(
                denomination_data=data['denomination_data'],
                branch_id=current_user['branch_id'],
                base_currency_id=branch.base_currency_id,
                operator_id=current_user['id'],
                customer_info=data['customer_info'],
                purpose_id=data.get('purpose_id')
            )

            if result['success']:
                # 记录系统日志
                multilingual_logger.log_system_operation(
                    'dual_direction_transaction',
                    operator_id=current_user['id'],
                    branch_id=current_user['branch_id'],
                    details=f"双向交易执行成功 - 业务组ID: {result['data']['business_group_id']}, 拆分为 {result['data']['transaction_count']} 条交易记录",
                    language='zh-CN'
                )

                return jsonify({
                    'success': True,
                    'message': '双向交易执行成功',
                    'data': result['data']
                })
            else:
                return jsonify({
                    'success': False,
                    'message': result['message']
                }), 400

        finally:
            DatabaseService.close_session(session)

    except Exception as e:
        logger.error(f"双向交易执行失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'交易执行失败: {str(e)}'
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

    except Exception as e:
        logger.error(f"获取业务组交易记录失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取失败: {str(e)}'
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
            # 记录系统日志
            multilingual_logger.log_system_operation(
                'business_group_reversal',
                operator_id=current_user['id'],
                branch_id=current_user['branch_id'],
                details=f"原业务组ID: {business_group_id}, 反结算业务组ID: {result['data']['reversal_group_id']}, 原因: {reason}",
                language='zh-CN'
            )

            return jsonify({
                'success': True,
                'message': '业务组反结算成功',
                'data': result['data']
            })
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 400

    except Exception as e:
        logger.error(f"业务组反结算失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'反结算失败: {str(e)}'
        }), 500