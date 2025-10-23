from flask import Blueprint, request, jsonify
from datetime import datetime
from models.exchange_models import CurrencyBalance, Currency, Branch, ExchangeTransaction
from services.db_service import DatabaseService
from services.auth_service import token_required, has_permission
from sqlalchemy.orm import joinedload
import logging
import random
import string
from utils.transaction_utils import generate_transaction_no

# Get logger instance - DO NOT call basicConfig() here as it will override
# the logging configuration already set in main.py
logger = logging.getLogger(__name__)

cash_bp = Blueprint('cash', __name__, url_prefix='/api/cash')

@cash_bp.route('/cash_out', methods=['POST'])
@token_required
@has_permission('manage_cash')
def cash_out(current_user):
    """
    处理交款操作
    """
    data = request.json
    if not data or not all(k in data for k in ['currency_id', 'amount', 'reason']):
        return jsonify({'success': False, 'message': '缺少必要字段'}), 400
    
    try:
        currency_id = int(data['currency_id'])
        amount = float(data['amount'])
        reason = data['reason']
        
        if amount <= 0:
            return jsonify({'success': False, 'message': '交款金额必须大于0'}), 400
            
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': '无效的数据类型'}), 400
    
    session = DatabaseService.get_session()
    try:
        # 获取币种信息
        currency = session.query(Currency).filter_by(id=currency_id).first()
        if not currency:
            return jsonify({'success': False, 'message': '币种不存在'}), 404

        # 获取网点信息
        branch = session.query(Branch).options(
            joinedload(Branch.base_currency)
        ).filter_by(id=current_user['branch_id']).first()
        
        if not branch:
            return jsonify({'success': False, 'message': '网点不存在'}), 404
        
        # 获取当前余额
        balance = session.query(CurrencyBalance).filter_by(
            branch_id=current_user['branch_id'],
            currency_id=currency_id
        ).first()
        
        if not balance:
            return jsonify({'success': False, 'message': '未找到余额记录'}), 404
            
        # 检查余额是否足够
        if balance.balance < amount:
            return jsonify({'success': False, 'message': '余额不足'}), 400
        
        # 更新余额
        previous_balance = balance.balance
        balance.balance -= amount
        balance.updated_at = datetime.utcnow()
        
        # 创建流水记录
        now = datetime.now()
        transaction = ExchangeTransaction(
            transaction_no=generate_transaction_no(current_user['branch_id'], session),
            branch_id=current_user['branch_id'],
            currency_id=currency_id,
            type='cash_out',
            amount=-amount,  # 负数表示减少
            rate=1.0,  # 交款不涉及汇率
            local_amount=0.0,  # 交款不涉及本币金额
            operator_id=current_user['id'],
            transaction_date=now.date(),
            transaction_time=now.strftime('%H:%M:%S'),
            created_at=now,
            customer_name=reason  # 使用reason字段记录交款原因
        )
        session.add(transaction)
        
        # 提交事务
        DatabaseService.commit_session(session)
        
        return jsonify({
            'success': True,
            'message': '交款成功',
            'transaction': {
                'currency_code': currency.currency_code,
                'currency_name': currency.currency_name,
                'previous_balance': previous_balance,
                'amount': amount,
                'new_balance': balance.balance,
                'updated_at': balance.updated_at.isoformat(),
                'transaction_no': transaction.transaction_no
            }
        })
    
    except Exception as e:
        logger.error(f"Error in cash_out: {str(e)}")
        DatabaseService.rollback_session(session)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session) 