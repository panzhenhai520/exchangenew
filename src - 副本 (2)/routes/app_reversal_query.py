from flask import Blueprint, request, jsonify
from sqlalchemy import desc
from datetime import datetime
from models.exchange_models import ExchangeTransaction, Currency, Operator
from services.db_service import DatabaseService
from services.auth_service import token_required, has_permission

reversal_query_bp = Blueprint('reversal_query', __name__, url_prefix='/api/transactions')

@reversal_query_bp.route('/reversal-query', methods=['GET'])
@token_required
@has_permission('log_view')
def query_reversals(*args):
    current_user = args[0]
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    min_amount = request.args.get('min_amount', type=float)
    max_amount = request.args.get('max_amount', type=float)
    operator_name = request.args.get('operator_name')
    reversal_no = request.args.get('reversal_no')
    original_no = request.args.get('original_no')
    reason = request.args.get('reason')

    session = DatabaseService.get_session()
    try:
        query = session.query(ExchangeTransaction, Currency, Operator) \
            .join(Currency, ExchangeTransaction.currency_id == Currency.id) \
            .join(Operator, ExchangeTransaction.operator_id == Operator.id) \
            .filter(ExchangeTransaction.type == 'reversal')  # 只查询作废交易
            
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
        if reversal_no:
            query = query.filter(ExchangeTransaction.transaction_no.ilike(f'%{reversal_no}%'))
        if original_no:
            query = query.filter(ExchangeTransaction.original_transaction_no.ilike(f'%{original_no}%'))
        if reason:
            query = query.filter(ExchangeTransaction.customer_name.ilike(f'%{reason}%'))  # 作废原因存在customer_name字段
            
        total_count = query.count()
        query = query.order_by(desc(ExchangeTransaction.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        records = []
        for tx, currency, operator in query.all():
            records.append({
                'id': tx.id,
                'reversal_time': tx.created_at.isoformat() if tx.created_at else None,
                'reversal_no': tx.transaction_no,
                'original_no': tx.original_transaction_no,
                'currency_code': currency.currency_code,
                'currency_name': currency.currency_name,
                'custom_flag_filename': currency.custom_flag_filename,  # 添加自定义图标文件名
                'flag_code': currency.flag_code,
                'amount': float(tx.amount),
                'operator_name': operator.name,
                'reason': tx.customer_name  # 作废原因存在customer_name字段
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