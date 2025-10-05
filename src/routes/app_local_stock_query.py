from flask import Blueprint, request, jsonify
from sqlalchemy import func, desc, and_, or_
from datetime import datetime, date, timedelta
from decimal import Decimal
from models.exchange_models import (
    ExchangeTransaction, Currency, Branch, Operator, CurrencyBalance, EODBalanceSnapshot, EODHistory, EODBalanceVerification, EODStatus
)
from services.db_service import DatabaseService
from services.auth_service import token_required, has_permission
from config.features import FeatureFlags
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('app_local_stock_query')

local_stock_bp = Blueprint('local_stock', __name__, url_prefix='/api/reports')

@local_stock_bp.route('/local-stock', methods=['GET'])
@token_required
@has_permission('view_balances')
def get_local_stock_query(current_user):
    """获取本币库存查询数据"""
    try:
        session = DatabaseService.get_session()
        
        # 获取当前用户的网点信息
        branch_id = current_user['branch_id']
        branch = session.query(Branch).filter_by(id=branch_id).first()
        
        if not branch:
            return jsonify({'success': False, 'message': '网点信息不存在'}), 404
        
        # 获取网点的本币信息
        base_currency = None
        if branch.base_currency_id:
            base_currency = session.query(Currency).filter_by(id=branch.base_currency_id).first()
        
        if not base_currency:
            return jsonify({'success': False, 'message': '未设置网点本币'}), 400
        
        # 获取时间范围，如果没有传入参数，使用统一的业务时间范围
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date and end_date:
            # 使用传入的时间范围
            start_time = datetime.strptime(start_date, '%Y-%m-%d')
            end_time = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        else:
            # 使用统一的业务时间范围
            from routes.app_reports import get_daily_time_range
            start_time, end_time = get_daily_time_range(branch_id)
        
        # 【简化】使用统一的CalBalance函数计算库存
        from routes.app_reports import CalBalance
        balance_data = CalBalance(branch_id, start_time, end_time)
        
        # 过滤只显示基础货币
        base_currency_data = None
        for currency in balance_data.get('currencies', []):
            if currency.get('is_base_currency', False):
                base_currency_data = currency
                break
        
        if not base_currency_data:
            # 如果没有找到基础货币数据，创建默认数据
            base_currency_data = {
                'currency_code': base_currency.currency_code,
                'currency_name': base_currency.currency_name,
                'opening_balance': 0,
                'current_balance': 0,
                'change_amount': 0,
                'total_buy': 0,
                'total_sell': 0,
                'is_base_currency': True
            }
        
        # 获取当前余额（从余额表）
        current_balance = 0
        current_balance_record = session.query(CurrencyBalance).filter_by(
            branch_id=branch_id,
            currency_id=base_currency.id
        ).first()
        
        if current_balance_record:
            current_balance = float(current_balance_record.balance or 0)
        
        # 【修复】获取本币相关的交易明细（用于显示）
        # 使用CalBalance函数返回的实际变化统计时间范围
        actual_change_start_time = balance_data.get('actual_change_start_time')
        actual_change_end_time = balance_data.get('actual_change_end_time')
        
        # 如果没有实际变化时间，使用传入的时间范围
        if actual_change_start_time and actual_change_end_time:
            transaction_start_time = datetime.fromisoformat(actual_change_start_time.replace('Z', '+00:00')).replace(tzinfo=None) if isinstance(actual_change_start_time, str) else actual_change_start_time
            transaction_end_time = datetime.fromisoformat(actual_change_end_time.replace('Z', '+00:00')).replace(tzinfo=None) if isinstance(actual_change_end_time, str) else actual_change_end_time
        else:
            transaction_start_time = start_time
            transaction_end_time = end_time
        
        logger.info(f"📅 本币库存查询 - 交易显示时间范围: {transaction_start_time} 到 {transaction_end_time}")
        
        transactions = session.query(ExchangeTransaction).filter(
            ExchangeTransaction.branch_id == branch_id,
            ExchangeTransaction.created_at >= transaction_start_time,
            ExchangeTransaction.created_at < transaction_end_time,
            ExchangeTransaction.type != 'Eod_diff'  # 排除日结差额调节交易
        ).order_by(ExchangeTransaction.created_at.desc()).all()
        
        # 构建交易列表
        transaction_list = []
        for tx in transactions:
            # 获取外币信息
            foreign_currency = None
            if tx.currency_id != base_currency.id:
                foreign_currency = session.query(Currency).filter_by(id=tx.currency_id).first()
            
            # 只包含对本币有影响的交易
            if tx.local_amount and tx.local_amount != 0:
                transaction_list.append({
                    'id': tx.id,
                    'transaction_time': tx.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'type': tx.type,
                    'transaction_no': tx.transaction_no,
                    'original_transaction_no': tx.original_transaction_no,
                    'foreign_currency_code': foreign_currency.currency_code if foreign_currency else base_currency.currency_code,
                    'amount': float(tx.amount or 0),
                    'rate': float(tx.rate or 0),
                    'local_amount_change': float(tx.local_amount),
                    'description': f"{tx.type} - {foreign_currency.currency_code if foreign_currency else base_currency.currency_code}"
                })
        
        # 构建响应数据
        response_data = {
            'branch_name': branch.branch_name,
            'base_currency_code': base_currency.currency_code,
            'base_currency_name': base_currency.currency_name,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'opening_balance': base_currency_data['opening_balance'],
            'current_balance': current_balance,
            'change_amount': base_currency_data['change_amount'],
            'total_buy': base_currency_data['total_buy'],
            'total_sell': base_currency_data['total_sell'],
            'transactions': transaction_list,
            'period_balance_method': 'EODBalanceVerification' if FeatureFlags.FEATURE_NEW_PERIOD_BALANCE else 'EODBalanceSnapshot',
            'actual_change_start_time': balance_data.get('actual_change_start_time'),
            'actual_change_end_time': balance_data.get('actual_change_end_time'),
        }
        
        logger.info(f"本币库存查询成功: 网点={branch.branch_name}, 本币={base_currency.currency_code}, 交易数={len(transaction_list)}")
        
        return jsonify({
            'success': True,
            'data': response_data
        })
        
    except Exception as e:
        logger.error(f"获取本币库存查询数据失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取数据失败: {str(e)}'}), 500
    
    finally:
        DatabaseService.close_session(session)

@local_stock_bp.route('/local-stock/export', methods=['GET'])
@token_required
@has_permission('view_balances')
def export_local_stock_query(current_user):
    """导出本币库存查询报表"""
    try:
        # 获取数据
        # 这里可以调用上面的查询逻辑，然后导出为Excel格式
        return jsonify({
            'success': True,
            'message': '导出功能待实现'
        })
    except Exception as e:
        logger.error(f"导出本币库存查询报表失败: {str(e)}")
        return jsonify({'success': False, 'message': f'导出失败: {str(e)}'}), 500 