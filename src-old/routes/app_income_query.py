from flask import Blueprint, request, jsonify
from datetime import datetime, date, timedelta
from models.exchange_models import ExchangeTransaction, Currency, Branch, Operator
from services.db_service import DatabaseService
from services.auth_service import token_required, has_permission
from utils.multilingual_log_service import multilingual_logger
from sqlalchemy import func, and_
import logging

logger = logging.getLogger(__name__)

income_query_bp = Blueprint('income_query', __name__, url_prefix='/api/income_query')

@income_query_bp.route('/daily', methods=['GET'])
@token_required
@has_permission('view_transactions')
def query_daily_income(current_user):
    """查询日收入统计"""
    try:
        # 记录日志
        from utils.language_utils import get_current_language
        current_language = get_current_language()
        multilingual_logger.log_income_query(
            operator_id=current_user['id'],
            branch_id=current_user['branch_id'],
            query_type="日收入统计",
            ip_address=request.remote_addr,
            language=current_language
        )
        
        # 获取查询参数
        query_date = request.args.get('date', date.today().isoformat())
        
        # 基本响应框架
        return jsonify({
            'success': True,
            'message': '动态收入查询 - 日收入统计',
            'data': {
                'query_date': query_date,
                'query_type': 'daily',
                'query_time': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Daily income query error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@income_query_bp.route('/monthly', methods=['GET'])
@token_required
@has_permission('view_transactions')
def query_monthly_income(current_user):
    """查询月收入统计"""
    try:
        # 记录日志
        from utils.language_utils import get_current_language
        current_language = get_current_language()
        multilingual_logger.log_income_query(
            operator_id=current_user['id'],
            branch_id=current_user['branch_id'],
            query_type="月收入统计",
            ip_address=request.remote_addr,
            language=current_language
        )
        
        # 获取查询参数
        query_month = request.args.get('month', date.today().strftime('%Y-%m'))
        
        # 基本响应框架
        return jsonify({
            'success': True,
            'message': '动态收入查询 - 月收入统计',
            'data': {
                'query_month': query_month,
                'query_type': 'monthly',
                'query_time': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Monthly income query error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@income_query_bp.route('/profit', methods=['GET'])
@token_required
@has_permission('view_transactions')
def query_exchange_profit(current_user):
    """查询兑换利润"""
    try:
        # 获取查询参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        date_range = f"{start_date} 至 {end_date}" if start_date and end_date else "默认范围"
        
        # 记录日志
        from utils.language_utils import get_current_language
        current_language = get_current_language()
        multilingual_logger.log_income_query(
            operator_id=current_user['id'],
            branch_id=current_user['branch_id'],
            query_type="兑换利润查询",
            date_range=date_range,
            ip_address=request.remote_addr,
            language=current_language
        )
        
        # 基本响应框架
        return jsonify({
            'success': True,
            'message': '动态收入查询 - 兑换利润',
            'data': {
                'start_date': start_date,
                'end_date': end_date,
                'query_type': 'profit',
                'query_time': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Exchange profit query error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500 