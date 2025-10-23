from flask import Blueprint, request, jsonify, send_file
from sqlalchemy import func, desc
from datetime import datetime, date
from decimal import Decimal
from models.exchange_models import ExchangeTransaction, Currency, Branch, Operator, CurrencyBalance, SystemLog
from services.db_service import DatabaseService
from services.auth_service import token_required, has_permission, check_business_lock_for_transactions
import logging
from utils.transaction_utils import generate_transaction_no
from services.log_service import LogService
from services.unified_log_service import log_reversal_transaction
from utils.language_utils import get_current_language
# PDFReceiptService已迁移至SimplePDFService
import os
import base64
from services.simple_pdf_service import SimplePDFService

# Get logger instance - DO NOT call basicConfig() here as it will override
# the logging configuration already set in main.py
logger = logging.getLogger('app_query_transactions')

def decimal_to_str(value):
    """Convert Decimal to string with proper precision"""
    if isinstance(value, Decimal):
        return str(value.normalize())
    return value

transactions_bp = Blueprint('transactions', __name__, url_prefix='/api/transactions')

@transactions_bp.route('/query', methods=['GET'])
@token_required
@has_permission('view_transactions')
def query_transactions(current_user, *args):
    logger.info(f"Query parameters: {request.args}")
    
    try:
        # Parse query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        customer_name = request.args.get('customer_name')
        transaction_no = request.args.get('transaction_no')
        operator_name = request.args.get('operator_name')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        min_amount = request.args.get('min_amount', type=float)
        max_amount = request.args.get('max_amount', type=float)
        currency_code = request.args.get('currency_code')
        
        # Limit per_page to prevent excessive queries
        if per_page > 100:
            per_page = 100
        
        # Calculate offset for pagination
        offset = (page - 1) * per_page
        
        session = DatabaseService.get_session()
        try:
            # Base query with joins
            query = session.query(
                ExchangeTransaction,
                Currency.currency_code,
                Currency.currency_name,
                Currency.custom_flag_filename,  # 添加自定义图标文件名
                Currency.flag_code,
                Operator.name.label('operator_name')
            ).join(
                Currency, ExchangeTransaction.currency_id == Currency.id
            ).join(
                Operator, ExchangeTransaction.operator_id == Operator.id
            ).filter(
                ExchangeTransaction.type != 'Eod_diff'  # 排除日结差额调节交易
            )
            
            # Apply filters
            if customer_name:
                query = query.filter(ExchangeTransaction.customer_name.ilike(f'%{customer_name}%'))
            
            if transaction_no:
                query = query.filter(ExchangeTransaction.transaction_no.ilike(f'%{transaction_no}%'))
            
            if operator_name:
                query = query.filter(Operator.name.ilike(f'%{operator_name}%'))
            
            if min_amount is not None:
                query = query.filter(ExchangeTransaction.amount >= min_amount)
            
            if max_amount is not None:
                query = query.filter(ExchangeTransaction.amount <= max_amount)
            
            if currency_code:
                query = query.filter(Currency.currency_code == currency_code)
            
            # Date range filters
            if start_date:
                try:
                    start = datetime.strptime(start_date, '%Y-%m-%d').date()
                    query = query.filter(ExchangeTransaction.transaction_date >= start)
                except ValueError:
                    return jsonify({'success': False, 'message': 'Invalid start date format'}), 400
            
            if end_date:
                try:
                    end = datetime.strptime(end_date, '%Y-%m-%d').date()
                    query = query.filter(ExchangeTransaction.transaction_date <= end)
                except ValueError:
                    return jsonify({'success': False, 'message': 'Invalid end date format'}), 400
            
            # Count total records
            total_count = query.count()
            
            # Apply sorting and pagination
            query = query.order_by(
                desc(ExchangeTransaction.transaction_date),
                desc(ExchangeTransaction.transaction_time)
            ).offset(offset).limit(per_page)
            
            # Execute query and format results
            transactions = []
            for tx, currency_code, currency_name, custom_flag_filename, flag_code, operator_name in query.all():
                transactions.append({
                    'id': tx.id,
                    'transaction_no': tx.transaction_no,
                    'type': tx.type,
                    'amount': str(tx.amount),
                    'rate': str(tx.rate),
                    'local_amount': str(tx.local_amount),
                    'transaction_time': f"{tx.transaction_date} {tx.transaction_time}",
                    'customer_name': tx.customer_name,
                    'operator_name': operator_name,
                    'currency_code': currency_code,
                    'currency_name': currency_name,
                    'custom_flag_filename': custom_flag_filename,  # 添加自定义图标文件名
                    'flag_code': flag_code,
                    'status': tx.status or 'active',  # 【修复】添加status字段
                    'original_transaction_no': tx.original_transaction_no  # 【修复】添加原交易号字段
                })
            
            return jsonify({
                'success': True,
                'transactions': transactions,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total_count': total_count,
                    'total_pages': (total_count + per_page - 1) // per_page
                }
            })
        
        except Exception as e:
            logger.error(f"Error in query_transactions: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
        finally:
            DatabaseService.close_session(session)

    except Exception as e:
        logger.error(f"Error in query_transactions: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@transactions_bp.route('/<int:transaction_id>', methods=['GET'])
@token_required
@has_permission('view_transactions')
def get_transaction_detail(current_user, transaction_id):
    session = DatabaseService.get_session()
    try:
        # Query the transaction with related information
        transaction = session.query(ExchangeTransaction).filter_by(id=transaction_id).first()
        
        if not transaction:
            return jsonify({'success': False, 'message': 'Transaction not found'}), 404
        
        # Check if user has permission to view this branch's transactions
        if transaction.branch_id != current_user.branch_id and not has_permission('manage_all_branches')(lambda: True):
            return jsonify({'success': False, 'message': 'You do not have permission to view this transaction'}), 403
        
        # Get related information
        branch = session.query(Branch).filter_by(id=transaction.branch_id).first()
        operator = session.query(Operator).filter_by(id=transaction.operator_id).first()
        buy_currency = session.query(Currency).filter_by(id=transaction.buy_currency_id).first()
        sell_currency = session.query(Currency).filter_by(id=transaction.sell_currency_id).first()
        
        return jsonify({
            'success': True,
            'transaction': {
                'id': transaction.id,
                'transaction_number': transaction.transaction_number,
                'customer_name': transaction.customer_name,
                'customer_id': transaction.customer_id,
                'buy_amount': transaction.buy_amount,
                'sell_amount': transaction.sell_amount,
                'exchange_rate': transaction.exchange_rate,
                'transaction_date': transaction.transaction_date.isoformat(),
                'status': transaction.status,
                'branch': {
                    'id': branch.id,
                    'name': branch.branch_name,
                    'code': branch.branch_code
                } if branch else None,
                'operator': {
                    'id': operator.id,
                    'name': operator.name,
                    'login_code': operator.login_code
                } if operator else None,
                'buy_currency': {
                    'id': buy_currency.id,
                    'code': buy_currency.currency_code,
                    'name': buy_currency.currency_name,
                    'flag_code': buy_currency.flag_code
                } if buy_currency else None,
                'sell_currency': {
                    'id': sell_currency.id,
                    'code': sell_currency.currency_code,
                    'name': sell_currency.currency_name,
                    'flag_code': sell_currency.flag_code
                } if sell_currency else None
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@transactions_bp.route('/reverse', methods=['POST'])
@token_required
@has_permission('reverse_transaction')
@check_business_lock_for_transactions
def reverse_transaction(current_user, *args):
    logger.info(f"Reversal request: {request.json}")
    
    try:
        data = request.json
        if not data or 'transaction_no' not in data or 'reason' not in data:
            return jsonify({
                'success': False,
                'message': '缺少必要的参数'
            }), 400
        
        transaction_no = data['transaction_no']
        reason = data['reason']
        
        session = DatabaseService.get_session()
        try:
            # 查找原始交易
            transaction = session.query(ExchangeTransaction).filter_by(
                transaction_no=transaction_no
            ).first()
            
            if not transaction:
                return jsonify({
                    'success': False,
                    'message': '交易不存在'
                }), 404
            
            # 检查交易是否已经被作废
            existing_reversal = session.query(ExchangeTransaction).filter_by(
                type='reversal',
                original_transaction_no=transaction_no
            ).first()
            
            if existing_reversal:
                return jsonify({
                    'success': False,
                    'message': '该交易已被作废'
                }), 400
            
            # 【关键检查】检查交易是否在日结业务时间范围内，如果是则不允许作废
            from models.exchange_models import EODStatus  # EODHistory 已废弃
            from sqlalchemy import and_
            
            # 构建交易的完整时间（精确到时分秒）
            transaction_datetime = datetime.combine(
                transaction.transaction_date,
                datetime.strptime(transaction.transaction_time, '%H:%M:%S').time()
            )
            
            logger.info(f"🔍 冲正检查 - 交易时间: {transaction_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"🔍 冲正检查 - 交易号: {transaction_no}")
            logger.info(f"🔍 冲正检查 - 网点ID: {transaction.branch_id}")
            
            # 查找该交易时间是否在某个已完成的日结的业务时间范围内
            # 使用EODStatus的business_end_time进行精确比较
            completed_eod_status = session.query(EODStatus).filter(
                and_(
                    EODStatus.branch_id == transaction.branch_id,
                    EODStatus.status == 'completed',
                    EODStatus.business_end_time.isnot(None),  # 确保有结束时间
                    EODStatus.business_end_time >= transaction_datetime  # 交易时间在日结结束时间之前或等于
                )
            ).order_by(EODStatus.business_end_time.desc()).first()
            
            if completed_eod_status:
                logger.info(f"🔍 冲正检查 - 找到已完成的日结: ID={completed_eod_status.id}, 业务时间范围: {completed_eod_status.business_start_time.strftime('%Y-%m-%d %H:%M:%S') if completed_eod_status.business_start_time else 'None'} - {completed_eod_status.business_end_time.strftime('%Y-%m-%d %H:%M:%S') if completed_eod_status.business_end_time else 'None'}")
                
                # 检查交易是否在该日结的业务时间范围内
                if (completed_eod_status.business_start_time and 
                    completed_eod_status.business_end_time and
                    completed_eod_status.business_start_time <= transaction_datetime <= completed_eod_status.business_end_time):
                    logger.warning(f"❌ 冲正被拒绝 - 交易在日结业务时间范围内")
                    return jsonify({
                        'success': False,
                        'message': f'该交易发生在 {transaction_datetime.strftime("%Y-%m-%d %H:%M:%S")}，在日结业务时间范围内（{completed_eod_status.business_start_time.strftime("%Y-%m-%d %H:%M:%S")} - {completed_eod_status.business_end_time.strftime("%Y-%m-%d %H:%M:%S")}），不允许作废'
                    }), 400
                else:
                    logger.info(f"✅ 冲正检查通过 - 交易不在日结业务时间范围内")
            else:
                logger.info(f"✅ 冲正检查通过 - 没有找到相关的已完成日结")
            
            # 获取币种余额
            balance = session.query(CurrencyBalance).filter_by(
                branch_id=transaction.branch_id,
                currency_id=transaction.currency_id
            ).first()

            if not balance:
                return jsonify({'success': False, 'message': '未找到币种余额记录'}), 404
            
            # 计算冲减金额
            reversal_amount = -Decimal(str(transaction.amount))
            reversal_local_amount = -Decimal(str(transaction.local_amount))
            
            # 记录冲减前的余额
            balance_before = Decimal(str(balance.balance))
            balance_after = balance_before + reversal_amount
            
            # 生成作废交易号 - 使用统一的票据号生成函数
            reversal_tx_no = generate_transaction_no(transaction.branch_id, session)
            
            # 创建作废交易记录
            now = datetime.now()
            reversal_tx = ExchangeTransaction(
                transaction_no=reversal_tx_no,
                branch_id=transaction.branch_id,
                currency_id=transaction.currency_id,
                type='reversal',  # 作废类型
                amount=str(reversal_amount),  # 金额取反
                rate=transaction.rate,
                local_amount=str(reversal_local_amount),  # 本币金额取反
                customer_name=reason,  # 使用作废原因
                customer_id=transaction.customer_id,
                operator_id=current_user['id'],  # 使用当前操作员
                transaction_date=now.date(),
                transaction_time=now.strftime('%H:%M:%S'),
                created_at=now,
                original_transaction_no=transaction_no,  # 记录原始交易号
                balance_before=str(balance_before),
                balance_after=str(balance_after)
            )
            
            # 【关键修复】更新外币余额
            balance.balance = str(balance_after)
            balance.updated_at = now
            
            # 【关键修复】获取网点的本币信息并更新本币余额
            branch = session.query(Branch).filter_by(id=transaction.branch_id).first()
            if branch and branch.base_currency_id:
                base_currency_balance = session.query(CurrencyBalance).filter_by(
                    branch_id=transaction.branch_id,
                    currency_id=branch.base_currency_id
                ).first()
                
                if base_currency_balance:
                    # 冲正：本币余额需要减去原交易的本币金额
                    base_balance_before = Decimal(str(base_currency_balance.balance))
                    base_balance_after = base_balance_before + reversal_local_amount
                    
                    base_currency_balance.balance = str(base_balance_after)
                    base_currency_balance.updated_at = now
                    
                    logger.info(f"🔄 本币余额更新: {base_balance_before} → {base_balance_after}")
                else:
                    logger.warning(f"⚠️ 未找到本币余额记录: branch_id={transaction.branch_id}, currency_id={branch.base_currency_id}")
            
            # 【关键修复】将原交易标记为已冲正状态
            transaction.status = 'reversed'
            logger.info(f"✅ 原交易 {transaction_no} 已标记为已冲正状态")
            
            session.add(reversal_tx)
            session.commit()
            
            # 记录冲正交易日志
            try:
                current_language = get_current_language()
                log_reversal_transaction(
                    operator_id=current_user['id'],
                    branch_id=current_user['branch_id'],
                    original_transaction_no=transaction_no,
                    currency_code=transaction.currency.currency_code,
                    amount=abs(float(reversal_tx.amount)),
                    rate=float(reversal_tx.rate) if reversal_tx.rate else 1.0,
                    reversal_transaction_no=reversal_tx_no,
                    ip_address=request.remote_addr,
                    language=current_language  # 使用当前用户的语言设置
                )
            except Exception as log_error:
                # 日志记录失败不应该影响冲正流程
                logger.warning(f"冲正交易日志记录失败: {log_error}")
            
            return jsonify({
                'success': True,
                'message': '交易已成功作废',
                'reversal_transaction_no': reversal_tx_no,
                'reversal_transaction_id': reversal_tx.id
            })
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error in reverse_transaction: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'作废交易失败: {str(e)}'
            }), 500
        finally:
            DatabaseService.close_session(session)
            
    except Exception as e:
        logger.error(f"Error in reverse_transaction: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 新增：PDF票据生成和打印API for 冲正业务
@transactions_bp.route('/reversal/<int:transaction_id>/print-receipt', methods=['POST'])
@token_required
@has_permission('reverse_transaction')
def print_reversal_receipt(*args, **kwargs):
    """生成并打印冲正票据PDF"""
    # 修复参数顺序问题：从装饰器获取current_user，从路径获取transaction_id
    current_user = args[0] if len(args) > 0 else kwargs.get('current_user')
    transaction_id = args[1] if len(args) > 1 else kwargs.get('transaction_id')
    
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
    
    if not transaction_id:
        return jsonify({'success': False, 'message': '交易ID参数缺失'}), 400
    
    # 获取请求数据，包括语言参数
    request_data = request.get_json() or {}
    language = request_data.get('language', 'zh')  # 默认中文
    logger.info(f"冲正打印请求语言: {language}")
    
    session = DatabaseService.get_session()
    
    try:
        # 获取冲正交易记录
        reversal_tx = session.query(ExchangeTransaction).filter_by(
            id=transaction_id,
            branch_id=current_user['branch_id'],
            type='reversal'  # 只查找冲正类型的交易
        ).first()
        
        if not reversal_tx:
            return jsonify({'success': False, 'message': '冲正交易记录不存在'}), 404
        
        # 获取原始交易记录
        original_tx = session.query(ExchangeTransaction).filter_by(
            transaction_no=reversal_tx.original_transaction_no
        ).first()
        
        if not original_tx:
            return jsonify({'success': False, 'message': '原始交易记录不存在'}), 404
        
        # 获取相关信息
        currency = session.query(Currency).filter_by(id=reversal_tx.currency_id).first()
        branch = session.query(Branch).filter_by(id=reversal_tx.branch_id).first()
        operator = session.query(Operator).filter_by(id=reversal_tx.operator_id).first()
        
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
        
        # 准备冲正单据的PDF数据
        reversal_amount = abs(float(reversal_tx.amount))
        original_amount = abs(float(original_tx.amount))
        pdf_data = {
            'transaction_no': reversal_tx.transaction_no,
            'branch_name': branch.branch_name,
            'branch_code': branch.branch_code,
            'transaction_type_desc': '交易冲正',
            'currency_code': currency.currency_code,
            'formatted_datetime': format_transaction_time(reversal_tx.transaction_date, reversal_tx.transaction_time),
            'from_amount': original_amount,
            'from_currency': f'原交易{currency.currency_code}',
            'to_amount': reversal_amount,
            'to_currency': f'冲正{currency.currency_code}',
            'rate': reversal_tx.rate or '1.0000',
            'foreign_currency': currency.currency_code,
            'base_currency': currency.currency_code,
            'customer_name': f'操作员：{operator.name}' if operator else '系统操作',
            'customer_id': 'REVERSAL_TRANSACTION',
            'purpose': '交易冲正',
            'remarks': f'冲正原因：{reversal_tx.customer_name or "无"} | 原单据号：{original_tx.transaction_no}'
        }
        
        # 生成PDF文件路径（使用SimplePDFService保持硬编码格式）
        file_path = SimplePDFService.get_receipt_file_path(
            reversal_tx.transaction_no, 
            reversal_tx.transaction_date
        )
        
        # 使用SimplePDFService生成冲正PDF，传递语言参数
        try:
            pdf_content = SimplePDFService.generate_reversal_receipt(reversal_tx, session, language=language)
            
            # 将base64内容保存到文件系统（用于下载）
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'wb') as f:
                f.write(base64.b64decode(pdf_content))
            
            logger.info(f"冲正PDF文件已保存到: {file_path}")
            success = True
            
        except Exception as e:
            logger.error(f"生成冲正PDF失败: {str(e)}")
            success = False
        
        if not success:
            return jsonify({'success': False, 'message': 'PDF生成失败'}), 500
        
        # 更新交易记录的票据信息
        if not reversal_tx.receipt_filename:
            # 只有第一次打印时才设置文件名
            reversal_tx.receipt_filename = os.path.basename(file_path)
        
        # 增加打印次数
        reversal_tx.print_count = (reversal_tx.print_count or 0) + 1
        
        # 记录系统日志
        log = SystemLog(
            operation='PRINT_REVERSAL_RECEIPT',
            operator_id=current_user['id'],
            log_type='transaction',
            action=f"打印冲正单据 {reversal_tx.transaction_no}",
            details=f"第{reversal_tx.print_count}次打印，文件: {reversal_tx.receipt_filename}，原单据号: {original_tx.transaction_no}",
            ip_address=request.remote_addr,
            created_at=datetime.now()
        )
        session.add(log)
        
        session.commit()
        
        # 根据语言返回不同的成功消息
        messages = {
            'zh': f'交易冲正单据生成成功，第{reversal_tx.print_count}次打印',
            'en': f'Transaction reversal receipt generated successfully, print #{reversal_tx.print_count}',
            'th': f'สร้างใบเสร็จการกลับรายการสำเร็จ ครั้งที่ {reversal_tx.print_count}'
        }
        success_message = messages.get(language, messages['zh'])
        
        return jsonify({
            'success': True,
            'message': success_message,
            'receipt_filename': reversal_tx.receipt_filename,
            'print_count': reversal_tx.print_count,
            'file_path': file_path
        })
        
    except Exception as e:
        logger.error(f"Print reversal receipt failed: {str(e)}")
        session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@transactions_bp.route('/reversal/<transaction_no>/download-receipt', methods=['GET'])
@token_required
@has_permission('reverse_transaction')
def download_reversal_receipt(*args, **kwargs):
    """下载冲正票据PDF"""
    # 修复参数顺序问题：从装饰器获取current_user，从路径获取transaction_no
    current_user = args[0] if len(args) > 0 else kwargs.get('current_user')
    transaction_no = args[1] if len(args) > 1 else kwargs.get('transaction_no')
    
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
    
    if not transaction_no:
        return jsonify({'success': False, 'message': '交易号参数缺失'}), 400
    
    session = DatabaseService.get_session()
    
    try:
        # 获取冲正交易记录
        reversal_tx = session.query(ExchangeTransaction).filter_by(
            transaction_no=transaction_no,
            branch_id=current_user['branch_id'],
            type='reversal'
        ).first()
        
        if not reversal_tx:
            return jsonify({'success': False, 'message': '冲正交易记录不存在'}), 404
        
        if not reversal_tx.receipt_filename:
            return jsonify({'success': False, 'message': '该交易尚未生成票据'}), 404
        
        # 构建文件路径（使用SimplePDFService保持一致）
        file_path = SimplePDFService.get_receipt_file_path(
            reversal_tx.transaction_no, 
            reversal_tx.transaction_date
        )
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'message': '票据文件不存在'}), 404
        
        # 返回文件
        return send_file(
            file_path,
            as_attachment=True,
            download_name=reversal_tx.receipt_filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Download reversal receipt failed: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@transactions_bp.route('/<int:transaction_id>/reprint-receipt', methods=['POST'])
@token_required
@has_permission('view_transactions')
def reprint_receipt(current_user, transaction_id):
    """重新打印交易收据"""
    session = DatabaseService.get_session()
    try:
        # 查找交易记录
        transaction = session.query(ExchangeTransaction).filter_by(id=transaction_id).first()
        
        if not transaction:
            return jsonify({'success': False, 'message': '交易记录不存在'}), 404
        
        # 检查权限：只能查看自己网点的交易
        if transaction.branch_id != current_user['branch_id']:
            return jsonify({'success': False, 'message': '您没有权限访问该交易记录'}), 403
        
        # 1. 首先尝试从文件系统中找到已存在的PDF文件
        pdf_content = None
        pdf_file_path = None
        
        if transaction.receipt_filename:
            # 从交易记录中获取文件名
            receipt_filename = transaction.receipt_filename
            
            # 构建完整的文件路径
            transaction_date = transaction.transaction_date
            year = str(transaction_date.year)
            month = str(transaction_date.month).zfill(2)
            
            pdf_file_path = os.path.join(
                'src', 'receipts', year, month, receipt_filename
            )
            
            # 检查文件是否存在
            if os.path.exists(pdf_file_path):
                try:
                    with open(pdf_file_path, 'rb') as file:
                        pdf_content = file.read()
                    logger.info(f"Successfully loaded existing PDF: {pdf_file_path}")
                except Exception as e:
                    logger.error(f"Failed to read existing PDF {pdf_file_path}: {str(e)}")
                    pdf_content = None
        
        # 2. 如果没有找到文件，重新生成PDF
        if pdf_content is None:
            logger.info(f"PDF file not found or failed to read, regenerating for transaction {transaction_id}")
            
            # 根据交易类型重新生成PDF
            try:
                # 标记为重新打印
                reprint_time = datetime.now()
                
                # 生成新的PDF（返回base64字符串）
                pdf_base64 = SimplePDFService.generate_exchange_receipt(
                    transaction, 
                    session, 
                    reprint_time=reprint_time
                )
                
                # 更新打印次数
                transaction.print_count = (transaction.print_count or 0) + 1
                session.commit()
                
                logger.info(f"Successfully regenerated PDF for transaction {transaction_id}")
                
            except Exception as e:
                logger.error(f"Failed to regenerate PDF for transaction {transaction_id}: {str(e)}")
                return jsonify({
                    'success': False, 
                    'message': f'PDF生成失败: {str(e)}'
                }), 500
        else:
            # 使用现有文件也要更新打印次数
            transaction.print_count = (transaction.print_count or 0) + 1
            session.commit()
            
            # 将二进制内容转为base64
            pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        
        # 3. 返回PDF内容
        if pdf_base64:
            
            # 记录重新打印日志
            LogService.log_business_operation(
                operation_type='REPRINT_RECEIPT',
                message=f'重新打印交易收据 - 交易号: {transaction.transaction_no}, 交易类型: {transaction.type}, '
                       f'打印次数: {transaction.print_count}, '
                       f'文件来源: {"现有文件" if pdf_file_path and os.path.exists(pdf_file_path) else "重新生成"}',
                operator_id=current_user['id'],
                branch_id=current_user.get('branch_id'),
                transaction_id=transaction.id
            )
            
            return jsonify({
                'success': True,
                'pdf_content': pdf_base64,
                'message': '收据重新打印成功',
                'print_count': transaction.print_count
            })
        else:
            return jsonify({
                'success': False,
                'message': '无法获取PDF内容'
            }), 500
            
    except Exception as e:
        logger.error(f"Reprint receipt failed: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'重新打印失败：{str(e)}'
        }), 500
    finally:
        DatabaseService.close_session(session)

@transactions_bp.route('/export-csv', methods=['GET'])
@token_required
@has_permission('view_transactions')
def export_transactions_csv(current_user, *args):
    """导出交易记录为CSV文件"""
    logger.info(f"Export CSV parameters: {request.args}")
    
    try:
        # Parse query parameters
        customer_name = request.args.get('customer_name')
        transaction_no = request.args.get('transaction_no')
        operator_name = request.args.get('operator_name')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        min_amount = request.args.get('min_amount', type=float)
        max_amount = request.args.get('max_amount', type=float)
        currency_code = request.args.get('currency_code')
        
        session = DatabaseService.get_session()
        try:
            # Base query with joins
            query = session.query(
                ExchangeTransaction,
                Currency.currency_code,
                Operator.name.label('operator_name')
            ).join(
                Currency, ExchangeTransaction.currency_id == Currency.id
            ).join(
                Operator, ExchangeTransaction.operator_id == Operator.id
            ).filter(
                ExchangeTransaction.type != 'Eod_diff'  # 排除日结差额调节交易
            )
            
            # Apply filters
            if customer_name:
                query = query.filter(ExchangeTransaction.customer_name.ilike(f'%{customer_name}%'))
            
            if transaction_no:
                query = query.filter(ExchangeTransaction.transaction_no.ilike(f'%{transaction_no}%'))
            
            if operator_name:
                query = query.filter(Operator.name.ilike(f'%{operator_name}%'))
            
            if min_amount is not None:
                query = query.filter(ExchangeTransaction.amount >= min_amount)
            
            if max_amount is not None:
                query = query.filter(ExchangeTransaction.amount <= max_amount)
            
            if currency_code:
                query = query.filter(Currency.currency_code == currency_code)
            
            # Date range filters
            if start_date:
                try:
                    start = datetime.strptime(start_date, '%Y-%m-%d').date()
                    query = query.filter(ExchangeTransaction.transaction_date >= start)
                except ValueError:
                    return jsonify({'success': False, 'message': 'Invalid start date format'}), 400
            
            if end_date:
                try:
                    end = datetime.strptime(end_date, '%Y-%m-%d').date()
                    query = query.filter(ExchangeTransaction.transaction_date <= end)
                except ValueError:
                    return jsonify({'success': False, 'message': 'Invalid end date format'}), 400
            
            # Get all results (no pagination for export)
            results = query.order_by(desc(ExchangeTransaction.transaction_date), desc(ExchangeTransaction.transaction_time)).all()
            
            # Format data for CSV
            transactions = []
            for result in results:
                transaction, currency_code, operator_name = result
                
                # Format transaction time
                def format_transaction_time(transaction_date, transaction_time):
                    if transaction_time:
                        return f"{transaction_date.strftime('%Y-%m-%d')} {transaction_time.strftime('%H:%M:%S')}"
                    else:
                        return transaction_date.strftime('%Y-%m-%d')
                
                transactions.append({
                    'transaction_time': format_transaction_time(transaction.transaction_date, transaction.transaction_time),
                    'transaction_no': transaction.transaction_no,
                    'type': transaction.type,
                    'currency_code': currency_code,
                    'amount': decimal_to_str(transaction.amount),
                    'rate': decimal_to_str(transaction.rate),
                    'local_amount': decimal_to_str(transaction.local_amount),
                    'customer_name': transaction.customer_name or '',
                    'operator_name': operator_name or ''
                })
            
            # Generate CSV content
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output, lineterminator='\n')
            
            # Write CSV headers
            headers = ['交易时间', '交易号', '类型', '币种', '金额', '汇率', '本币金额', '客户姓名', '操作员']
            writer.writerow(headers)
            
            # Write data
            for tx in transactions:
                writer.writerow([
                    tx['transaction_time'],
                    tx['transaction_no'],
                    tx['type'],
                    tx['currency_code'],
                    tx['amount'],
                    tx['rate'],
                    tx['local_amount'],
                    tx['customer_name'],
                    tx['operator_name']
                ])
            
            # Get CSV content
            csv_content = output.getvalue()
            output.close()
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'transaction_query_{timestamp}.csv'
            
            # Create export directory
            import os
            export_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'exports')
            if not os.path.exists(export_dir):
                os.makedirs(export_dir, exist_ok=True)
            
            # Save file
            file_path = os.path.join(export_dir, filename)
            with open(file_path, 'w', encoding='utf-8-sig') as f:  # Use utf-8-sig to support Chinese
                f.write(csv_content)
            
            # Return download link
            download_url = f'/api/transactions/download-csv/{filename}'
            
            return jsonify({
                'success': True,
                'message': '导出成功',
                'file_path': file_path,
                'download_url': download_url,
                'filename': filename,
                'transactions': transactions  # Also return data for frontend processing
            })
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error in export_transactions_csv: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
        finally:
            DatabaseService.close_session(session)
            
    except Exception as e:
        logger.error(f"Export CSV failed: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'导出失败：{str(e)}'
        }), 500

@transactions_bp.route('/download-csv/<filename>', methods=['GET'])
def download_transactions_csv(filename):
    """下载交易查询导出文件"""
    try:
        import os
        from flask import send_file
        
        # Security check: ensure filename doesn't contain path
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({'success': False, 'message': '无效的文件名'}), 400
        
        # Build file path
        export_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'exports')
        file_path = os.path.join(export_dir, filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'message': '文件不存在'}), 404
        
        # Return file
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv'
        )
        
    except Exception as e:
        logger.error(f"Download CSV failed: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'下载失败：{str(e)}'
        }), 500
