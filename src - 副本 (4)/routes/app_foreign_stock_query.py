from flask import Blueprint, request, jsonify
from services.db_service import DatabaseService
from services.auth_service import token_required, has_permission
from models.exchange_models import ExchangeTransaction, Branch, Currency, EODBalanceVerification, EODStatus  # EODBalanceSnapshot, EODHistory 已废弃
from sqlalchemy import and_, or_, func, desc
from datetime import datetime, timedelta
from utils.multilingual_log_service import multilingual_logger
import logging

logger = logging.getLogger(__name__)
foreign_stock_query_bp = Blueprint('foreign_stock_query', __name__)

@foreign_stock_query_bp.route('/current', methods=['GET'])
@token_required
@has_permission('view_balances')
def query_current_stock(current_user):
    """查询当前库存"""
    try:
        # 记录日志
        from utils.language_utils import get_current_language
        current_language = get_current_language()
        multilingual_logger.log_stock_query(
            operator_id=current_user['id'],
            branch_id=current_user['branch_id'],
            query_type="当前库存查询",
            ip_address=request.remote_addr,
            language=current_language
        )
        
        # 获取查询参数
        currency_code = request.args.get('currency_code')
        
        # 基本响应框架
        return jsonify({
            'success': True,
            'message': '库存外币查询 - 当前库存',
            'data': {
                'currency_code': currency_code,
                'query_type': 'current',
                'query_time': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Current stock query error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@foreign_stock_query_bp.route('/history', methods=['GET'])
@token_required
@has_permission('view_balances')
def query_stock_history(current_user):
    """查询库存历史"""
    try:
        # 获取查询参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        currency_code = request.args.get('currency_code')
        date_range = f"{start_date} 至 {end_date}" if start_date and end_date else "默认范围"
        
        # 记录日志
        from utils.language_utils import get_current_language
        current_language = get_current_language()
        multilingual_logger.log_stock_query(
            operator_id=current_user['id'],
            branch_id=current_user['branch_id'],
            query_type="库存历史查询",
            currency_code=currency_code,
            date_range=date_range,
            ip_address=request.remote_addr,
            language=current_language
        )
        
        # 基本响应框架
        return jsonify({
            'success': True,
            'message': '库存外币查询 - 库存历史',
            'data': {
                'start_date': start_date,
                'end_date': end_date,
                'currency_code': currency_code,
                'query_type': 'history',
                'query_time': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Stock history query error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@foreign_stock_query_bp.route('/low_balance', methods=['GET'])
@token_required
@has_permission('view_balances')
def query_low_balance(current_user):
    """查询低库存警告"""
    try:
        # 记录日志
        from utils.language_utils import get_current_language
        current_language = get_current_language()
        multilingual_logger.log_stock_query(
            operator_id=current_user['id'],
            branch_id=current_user['branch_id'],
            query_type="低库存警告查询",
            ip_address=request.remote_addr,
            language=current_language
        )
        
        # 获取查询参数
        threshold = request.args.get('threshold', '1000')  # 默认警告阈值
        
        # 基本响应框架
        return jsonify({
            'success': True,
            'message': '库存外币查询 - 低库存警告',
            'data': {
                'threshold': threshold,
                'query_type': 'low_balance',
                'query_time': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Low balance query error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@foreign_stock_query_bp.route('/summary', methods=['GET'])
@token_required
@has_permission('view_balances')
def query_stock_summary(current_user):
    """查询库存汇总"""
    try:
        # 记录日志
        multilingual_logger.log_stock_query(
            operator_id=current_user['id'],
            branch_id=current_user['branch_id'],
            query_type="库存汇总查询",
            ip_address=request.remote_addr,
            language='zh-CN'
        )
        
        # 基本响应框架
        return jsonify({
            'success': True,
            'message': '库存外币查询 - 库存汇总',
            'data': {
                'query_type': 'summary',
                'query_time': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Stock summary query error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@foreign_stock_query_bp.route('/foreign-stock', methods=['GET'])
@token_required
def get_foreign_stock_query(current_user):
    """
    库存外币查询API
    
    按照用户要求的统一算法实现：
    1. 基于网点和币种进行查询
    2. 期初余额：有日结记录从相应表获取，无日结记录取第一笔交易值
    3. 变动统计：从上次日结结束时间+1秒开始，到查询时间结束
    4. 外币使用amount字段统计
    """
    try:
        # 获取查询参数
        branch_id = request.args.get('branch_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date') 
        
        if not branch_id:
            return jsonify({'error': '缺少必要的参数：branch_id'}), 400
        
        # 转换时间格式
        if start_date:
            start_time = datetime.strptime(start_date, '%Y-%m-%d')
        else:
            start_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        if end_date:
            end_time = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        else:
            end_time = datetime.now()
        
        # 调用统一的库存计算函数
        from routes.app_reports import CalBalance
        stock_data = CalBalance(branch_id, start_time, end_time)
        
        # 过滤只显示外币（非基础货币）
        foreign_currencies = [
            currency for currency in stock_data.get('currencies', [])
            if not currency.get('is_base_currency', False)
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'currencies': foreign_currencies,
                'query_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_currencies': len(foreign_currencies)
            }
        })
        
    except Exception as e:
        logging.error(f"库存外币查询异常: {str(e)}")
        return jsonify({'error': f'查询失败: {str(e)}'}), 500

@foreign_stock_query_bp.route('/foreign-stock/currency/<currency_code>', methods=['GET'])
@token_required
def get_foreign_stock_detail(current_user, currency_code):
    """
    获取指定外币的详细库存信息
    """
    try:
        # 获取查询参数
        branch_id = request.args.get('branch_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not branch_id:
            return jsonify({'error': '缺少必要的参数：branch_id'}), 400
        
        # 转换时间格式
        if start_date:
            start_time = datetime.strptime(start_date, '%Y-%m-%d')
        else:
            start_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        if end_date:
            end_time = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        else:
            end_time = datetime.now()
        
        session = DatabaseService.get_session()
        
        # 获取指定币种信息
        currency = session.query(Currency).filter_by(currency_code=currency_code).first()
        if not currency:
            return jsonify({'error': f'币种 {currency_code} 不存在'}), 404
        
        # 获取网点信息
        branch = session.query(Branch).filter_by(id=branch_id).first()
        if not branch:
            return jsonify({'error': f'网点 {branch_id} 不存在'}), 404
        
        # 确保不是基础货币
        if currency.id == branch.base_currency_id:
            return jsonify({'error': f'{currency_code} 是基础货币，请使用本币库存查询'}), 400
        
        # 获取该币种的库存信息
        stock_data = CalBalance(branch_id, start_time, end_time)
        
        # 找到指定币种的数据
        currency_data = None
        for curr in stock_data.get('currencies', []):
            if curr.get('currency_code') == currency_code:
                currency_data = curr
                break
        
        if not currency_data:
            # 如果没有找到数据，说明该币种在查询时间范围内没有交易
            currency_data = {
                'currency_code': currency_code,
                'currency_name': currency.currency_name,
                'opening_balance': 0,
                'current_balance': 0,
                'change_amount': 0,
                'total_buy': 0,
                'total_sell': 0,
                'is_base_currency': False
            }
        
        # 获取该币种的交易明细
        transactions = session.query(ExchangeTransaction).filter(
            and_(
                ExchangeTransaction.branch_id == branch_id,
                ExchangeTransaction.currency_id == currency.id,
                ExchangeTransaction.created_at >= start_time,
                ExchangeTransaction.created_at < end_time,
                ExchangeTransaction.type.in_(['buy', 'sell', 'initial_balance', 'adjust_balance', 'cash_out', 'reversal'])
            )
        ).order_by(ExchangeTransaction.created_at.desc()).all()
        
        transaction_details = []
        for tx in transactions:
            transaction_details.append({
                'id': tx.id,
                'type': tx.type,
                'amount': float(tx.amount),
                'local_amount': float(tx.local_amount),
                'exchange_rate': float(tx.exchange_rate) if tx.exchange_rate else 0,
                'created_at': tx.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'memo': tx.remarks or ''
            })
        
        return jsonify({
            'success': True,
            'data': {
                'currency_info': currency_data,
                'transactions': transaction_details,
                'query_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_transactions': len(transaction_details)
            }
        })
        
    except Exception as e:
        logging.error(f"外币库存明细查询异常: {str(e)}")
        return jsonify({'error': f'查询失败: {str(e)}'}), 500
        
    finally:
        DatabaseService.close_session() 