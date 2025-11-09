from flask import Blueprint, request, jsonify
from sqlalchemy import desc
from datetime import datetime
import logging
from models.exchange_models import ExchangeTransaction, Currency, Operator
from services.db_service import DatabaseService
from services.auth_service import token_required, has_permission
# 已移除不需要的导入：BalanceService 和 generate_transaction_no

# 设置日志记录器
logger = logging.getLogger(__name__)

balance_adjust_query_bp = Blueprint('balance_adjust_query', __name__, url_prefix='/api/balance-adjustments')

# 注意：余额调整功能已移至 app_query_balances.py 中的 adjust_balance 函数
# 此文件专注于余额调整的查询功能

@balance_adjust_query_bp.route('/adjustment-query', methods=['GET'])
@token_required
@has_permission('log_view')
def query_balance_adjustment_logs(*args, **kwargs):
    """查询余额调节日志"""
    current_user = kwargs.get('current_user') or args[0]
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    min_amount = request.args.get('min_amount', type=float)
    max_amount = request.args.get('max_amount', type=float)
    operator_name = request.args.get('operator_name')
    reason = request.args.get('reason')

    session = DatabaseService.get_session()
    try:
        query = session.query(ExchangeTransaction, Currency, Operator) \
            .join(Currency, ExchangeTransaction.currency_id == Currency.id) \
            .join(Operator, ExchangeTransaction.operator_id == Operator.id) \
            .filter(ExchangeTransaction.type.in_(['adjust_balance', 'Eod_diff']))  # 余额调节类型和日结差额调节
            
        if start_date:
            query = query.filter(ExchangeTransaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(ExchangeTransaction.transaction_date <= end_date)
        if min_amount is not None:
            query = query.filter(ExchangeTransaction.amount >= min_amount)
        if max_amount is not None:
            query = query.filter(ExchangeTransaction.amount <= max_amount)
        if operator_name:
            query = query.filter(Operator.name.ilike(f'%{operator_name}%'))
        if reason:
            query = query.filter(ExchangeTransaction.customer_name.ilike(f'%{reason}%'))  # 调节原因存在customer_name字段
            
        total_count = query.count()
        query = query.order_by(desc(ExchangeTransaction.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        records = []
        for tx, currency, operator in query.all():
            records.append({
                'id': tx.id,
                'adjust_time': tx.created_at.isoformat() if tx.created_at else None,
                'adjust_no': tx.transaction_no,
                'currency_code': currency.currency_code,
                'currency_name': currency.currency_name,
                'custom_flag_filename': currency.custom_flag_filename,
                'flag_code': currency.flag_code,
                'adjust_amount': float(tx.amount),
                'balance_before': float(tx.balance_before) if tx.balance_before is not None else None,
                'balance_after': float(tx.balance_after) if tx.balance_after is not None else None,
                'operator_name': operator.name,
                'reason': tx.customer_name  # 调节原因存在customer_name字段
            })
            
        return jsonify({
            'success': True,
            'records': records,
            'pagination': {
                'total_count': total_count,
                'page': page,
                'page_size': page_size
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@balance_adjust_query_bp.route('/query', methods=['GET'])
@token_required
@has_permission('balance_manage')
def query_balance_adjustments(*args, **kwargs):
    """查询余额调节记录"""
    current_user = kwargs.get('current_user') or args[0]
    
    # 解析查询参数
    branch_id = request.args.get('branch_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    currency_id = request.args.get('currency_id')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    session = DatabaseService.get_session()
    try:
        # 构建查询
        query = session.query(ExchangeTransaction, Currency, Operator) \
            .join(Currency, ExchangeTransaction.currency_id == Currency.id) \
            .join(Operator, ExchangeTransaction.operator_id == Operator.id) \
            .filter(ExchangeTransaction.type == 'adjust_balance')  # 统一使用adjust_balance作为类型条件
            
        # 应用过滤条件
        if branch_id:
            query = query.filter(ExchangeTransaction.branch_id == branch_id)
        if start_date:
            query = query.filter(ExchangeTransaction.created_at >= start_date)
        if end_date:
            query = query.filter(ExchangeTransaction.created_at <= end_date)
        if currency_id:
            query = query.filter(ExchangeTransaction.currency_id == currency_id)
            
        # 计算总记录数
        total_count = query.count()
        
        # 应用分页
        query = query.order_by(desc(ExchangeTransaction.created_at))
        query = query.offset((page - 1) * per_page).limit(per_page)
        
        # 格式化结果
        records = []
        for tx, currency, operator in query.all():
            records.append({
                'id': tx.id,
                'transaction_no': tx.transaction_no,
                'currency_code': currency.currency_code,
                'currency_name': currency.currency_name,
                'amount': float(tx.amount),
                'balance_before': float(tx.balance_before) if tx.balance_before else None,
                'balance_after': float(tx.balance_after) if tx.balance_after else None,
                'operator_name': operator.name,
                'created_at': tx.created_at.isoformat() if tx.created_at else None,
                'reason': tx.customer_name  # 调节原因存储在customer_name字段
            })
            
        return jsonify({
            'success': True,
            'data': {
                'records': records,
                'total': total_count,
                'page': page,
                'per_page': per_page
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)