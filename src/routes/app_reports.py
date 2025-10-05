#!/usr/bin/env python3
"""
报表查询API路由
包含：
- 动态收入查询
- 库存外币查询
- PDF导出功能
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, date, timedelta
from services.auth_service import token_required, has_permission
from services.db_service import DatabaseService
from models.exchange_models import ExchangeTransaction, Currency, Branch, Operator, EODStatus, CurrencyBalance
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, func, or_, desc
from sqlalchemy.orm import joinedload
from decimal import Decimal
import logging
from utils.multilingual_log_service import multilingual_logger
from utils.currency_utils import get_base_currency_id_from_branch, is_base_currency
from models.exchange_models import EODBalanceVerification, EODBalanceSnapshot, EODHistory
from config.features import FeatureFlags

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('app_reports')

# Create blueprint for report operations
reports_bp = Blueprint('reports', __name__, url_prefix='/api/reports')

def CalGain(branch_id, start_time, end_time):
    """
    计算收入统计报表
    
    Args:
        branch_id: 网点ID
        start_time: 开始时间
        end_time: 结束时间
    
    Returns:
        dict: 收入统计数据
    """
    session = DatabaseService.get_session()
    
    try:
        # 【日志】记录CalGain函数的调用参数
        logging.info(f"💰 CalGain函数被调用 - 网点ID: {branch_id}")
        logging.info(f"📅 CalGain查询时间范围: {start_time.strftime('%Y-%m-%d %H:%M:%S')} 到 {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info(f"⏰ CalGain时间跨度: {(end_time - start_time).total_seconds() / 3600:.2f} 小时")
        
        # 获取网点信息
        branch = session.query(Branch).options(
            joinedload(Branch.base_currency)
        ).filter_by(id=branch_id).first()
        
        if not branch:
            raise ValueError(f"网点ID {branch_id} 不存在")
        
        base_currency_code = branch.base_currency.currency_code if branch.base_currency else 'USD'
        base_currency_id = branch.base_currency_id if branch else None
        
        # 【改进】查询指定时间范围内的所有相关交易
        # 包含买卖交易、余额调节、冲正交易，以及被冲正的交易（显示完整业务流程）
        # 【日志】记录SQL查询条件
        logging.info(f"🔍 【汇总查询】CalGain查询条件:")
        logging.info(f"  - 网点ID: {branch_id}")
        logging.info(f"  - 交易类型: ['buy', 'sell', 'adjust_balance', 'reversal', 'initial_balance']")
        logging.info(f"  - 包含状态: 所有状态（包括被冲正的交易）")
        logging.info(f"  - 时间范围: {start_time.strftime('%Y-%m-%d %H:%M:%S')} 到 {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info(f"  - 时间条件SQL: created_at >= '{start_time}' AND created_at < '{end_time}'")
        
        transactions = session.query(
            ExchangeTransaction.currency_id,
            ExchangeTransaction.type,
            ExchangeTransaction.amount,
            ExchangeTransaction.rate,
            ExchangeTransaction.local_amount
        ).filter(
            and_(
                ExchangeTransaction.branch_id == branch_id,
                ExchangeTransaction.type.in_(['buy', 'sell', 'adjust_balance', 'reversal', 'initial_balance']),  # 【新增】包含期初余额
                # 【修复】移除 status != 'reversed' 条件，显示所有交易包括被冲正的交易
                ExchangeTransaction.created_at >= start_time,
                ExchangeTransaction.created_at < end_time
            )
        ).all()
        
        # 【日志】记录查询结果
        logging.info(f"📊 【汇总查询】CalGain查询到 {len(transactions)} 笔交易记录")
        
        # 【调试】详细记录查询到的交易
        type_counts = {}
        for tx in transactions:
            type_counts[tx.type] = type_counts.get(tx.type, 0) + 1
            logging.info(f"  交易: 币种ID={tx.currency_id}, 类型={tx.type}, 金额={tx.amount}, 本币金额={tx.local_amount}")
        
        # 【日志】记录汇总查询的交易类型分布
        logging.info(f"📊 【汇总查询】交易类型分布: {type_counts}")
        
        # 【日志】记录每种币种的交易数量
        currency_counts = {}
        for tx in transactions:
            currency_counts[tx.currency_id] = currency_counts.get(tx.currency_id, 0) + 1
        logging.info(f"📊 【汇总查询】各币种交易数量: {currency_counts}")
        
        # 按币种分组统计
        currency_stats = {}
        
        for tx in transactions:
            currency_id = tx.currency_id
            if currency_id not in currency_stats:
                currency_stats[currency_id] = {
                    'total_buy': 0,
                    'total_sell': 0,
                    'buy_rate': 0,
                    'sell_rate': 0,
                    'buy_local_amount': 0,
                    'sell_local_amount': 0,
                    'total_adjust': 0,           # 【新增】余额调节统计
                    'total_reversal': 0,         # 【新增】冲正交易统计
                    'reversal_local_amount': 0,  # 【新增】冲正交易本币金额
                    'has_income_impact': False   # 【新增】标记是否有收入影响
                }
            
            amount = float(tx.amount)
            local_amount = float(tx.local_amount)
            
            if tx.type == 'buy':
                # 买入交易：银行买入外币，amount为正值
                currency_stats[currency_id]['total_buy'] += abs(amount)
                currency_stats[currency_id]['buy_rate'] = float(tx.rate)
                currency_stats[currency_id]['buy_local_amount'] += abs(local_amount)
                currency_stats[currency_id]['has_income_impact'] = True  # 标记有收入影响
            elif tx.type == 'sell':
                # 卖出交易：银行卖出外币，amount为负值，使用绝对值
                currency_stats[currency_id]['total_sell'] += abs(amount)
                currency_stats[currency_id]['sell_rate'] = float(tx.rate)
                currency_stats[currency_id]['sell_local_amount'] += abs(local_amount)
                currency_stats[currency_id]['has_income_impact'] = True  # 标记有收入影响
            elif tx.type == 'adjust_balance':
                # 【新增】余额调节：记录调节金额，不影响收入计算
                currency_stats[currency_id]['total_adjust'] += amount
                # 余额调节不影响收入，不标记has_income_impact
            elif tx.type == 'reversal':
                # 【修复】冲正交易：记录冲正金额和本币金额，直接使用local_amount
                currency_stats[currency_id]['total_reversal'] += amount
                currency_stats[currency_id]['reversal_local_amount'] += local_amount
                currency_stats[currency_id]['has_income_impact'] = True  # 标记有收入影响
            elif tx.type == 'initial_balance':
                # 【新增】期初余额：只记录但不计入收入计算（仅影响库存）
                pass  # 期初余额不参与收入统计，也不标记has_income_impact
        
        # 【修复】添加基础货币统计逻辑
        # 基础货币的变动通过其他货币交易的local_amount体现
        base_currency_id = branch.base_currency_id
        if base_currency_id:
            # 初始化基础货币统计
            if base_currency_id not in currency_stats:
                currency_stats[base_currency_id] = {
                    'total_buy': 0,
                    'total_sell': 0,
                    'buy_rate': 1.0,  # 基础货币汇率为1
                    'sell_rate': 1.0,
                    'buy_local_amount': 0,
                    'sell_local_amount': 0,
                    'total_adjust': 0,
                    'total_reversal': 0,
                    'reversal_local_amount': 0,
                    'has_income_impact': False
                }
            
            # 统计基础货币的变动（通过所有交易的local_amount）
            base_currency_income = 0
            for tx in transactions:
                local_amount = float(tx.local_amount)
                if tx.type == 'buy':
                    # 买入外币，本币支出（负值）
                    base_currency_income -= abs(local_amount)
                    currency_stats[base_currency_id]['buy_local_amount'] += abs(local_amount)
                elif tx.type == 'sell':
                    # 卖出外币，本币收入（正值）
                    base_currency_income += abs(local_amount)
                    currency_stats[base_currency_id]['sell_local_amount'] += abs(local_amount)
                elif tx.type == 'reversal':
                    # 冲正交易，直接使用local_amount
                    base_currency_income += local_amount
                    currency_stats[base_currency_id]['reversal_local_amount'] += local_amount
                elif tx.type == 'initial_balance' and tx.currency_id == base_currency_id:
                    # 基础货币的期初余额，使用local_amount
                    currency_stats[base_currency_id]['total_adjust'] += local_amount
            
            # 如果基础货币有变动，标记为有收入影响
            if (currency_stats[base_currency_id]['buy_local_amount'] != 0 or 
                currency_stats[base_currency_id]['sell_local_amount'] != 0 or
                currency_stats[base_currency_id]['reversal_local_amount'] != 0 or
                currency_stats[base_currency_id]['total_adjust'] != 0):
                currency_stats[base_currency_id]['has_income_impact'] = True
                
                logging.info(f"💰 基础货币({base_currency_id})统计: 买入本币支出={currency_stats[base_currency_id]['buy_local_amount']}, 卖出本币收入={currency_stats[base_currency_id]['sell_local_amount']}, 冲正本币={currency_stats[base_currency_id]['reversal_local_amount']}, 调节={currency_stats[base_currency_id]['total_adjust']}")

        # 【修复】显示所有有交易的币种（包括买入、卖出或冲正交易）
        all_currency_ids = set()
        for currency_id, stats in currency_stats.items():
            # 只要有买卖交易或冲正交易就包含
            if (stats['total_buy'] > 0 or stats['total_sell'] > 0 or 
                stats['total_reversal'] != 0 or stats['has_income_impact']):
                all_currency_ids.add(currency_id)
        
        # 【日志】记录筛选结果
        logging.info(f"📊 CalGain筛选结果: 总币种数 {len(currency_stats)}, 包含在结果中的币种数 {len(all_currency_ids)}")
        for currency_id in currency_stats:
            stats = currency_stats[currency_id]
            if currency_id not in all_currency_ids:
                logging.info(f"🚫 已过滤币种ID {currency_id}：买入={stats['total_buy']}, 卖出={stats['total_sell']}, 冲正={stats['total_reversal']}")
            else:
                logging.info(f"✅ 包含币种ID {currency_id}：买入={stats['total_buy']}, 卖出={stats['total_sell']}, 冲正={stats['total_reversal']}")
        
        # 获取币种信息并计算收入
        currencies = session.query(Currency).filter(
            Currency.id.in_(all_currency_ids)
        ).all()
        
        currency_map = {c.id: c for c in currencies}
        
        result_currencies = []
        total_income = 0
        total_spread_income = 0
        
        for currency_id, stats in currency_stats.items():
            currency = currency_map.get(currency_id)
            if not currency:
                continue
            
            # 检查是否是基础货币
            is_base_currency = (currency_id == base_currency_id)
            
            # 【修复】动态收入查询不显示本币
            if is_base_currency:
                continue
            
            # 外币的统计逻辑（已过滤掉基础货币）
            total_buy = stats['total_buy']
            total_sell = stats['total_sell']
            buy_local_amount = stats['buy_local_amount']
            sell_local_amount = stats['sell_local_amount']
            total_reversal = stats['total_reversal']  # 冲正交易金额
            reversal_local_amount = stats['reversal_local_amount']  # 冲正交易本币金额
            
            # 【修复】计算实际净收益，包含冲正交易的影响
            # 冲正交易直接使用其local_amount，确保冲正后净收入为0
            income = sell_local_amount - buy_local_amount + reversal_local_amount
            
            # 计算点差估算收入
            min_volume = min(total_buy, total_sell)
            buy_rate = stats['buy_rate']
            sell_rate = stats['sell_rate']
            spread_income = min_volume * (sell_rate - buy_rate)
            
            result_currencies.append({
                'currency_code': currency.currency_code,
                'currency_name': currency.currency_name,
                'custom_flag_filename': currency.custom_flag_filename,  # 【新增】自定义图标文件名
                'flag_code': currency.flag_code,  # 【新增】标准图标代码
                'buy_amount': total_buy,        # 前端使用的字段名
                'sell_amount': total_sell,      # 前端使用的字段名
                'total_buy': total_buy,         # 保持兼容性
                'total_sell': total_sell,       # 保持兼容性
                'reversal_amount': total_reversal,  # 【新增】冲正金额
                'reversal_local_amount': reversal_local_amount,  # 【新增】冲正本币金额
                'buy_rate': stats['buy_rate'],
                'sell_rate': stats['sell_rate'],
                'income': income,
                'spread_income': spread_income
            })
            
            total_income += income
            total_spread_income += spread_income
        
        return {
            'branch_id': branch_id,
            'branch_name': branch.branch_name,
            'base_currency': base_currency_code,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'total_income': total_income,
            'total_spread_income': total_spread_income,
            'currencies': result_currencies
        }
        
    finally:
        DatabaseService.close_session(session)

def get_currency_period_info(session, branch_id, currency_id, base_currency_id, eod_start_time):
    """
    获取币种的期初余额和时间范围信息
    
    按用户要求的规则：
    1. 基于网点统计，其次按币种
    2. 如果该币种没有上一次的日结记录，取该币种第一笔交易作为期初
    3. 如果该币种有上一次的日结记录，根据FEATURE_NEW_PERIOD_BALANCE从相应表获取期初余额
    4. 确定库存变动统计的开始时间和结束时间
    
    Args:
        session: 数据库会话
        branch_id: 网点ID
        currency_id: 币种ID
        base_currency_id: 基础货币ID
        eod_start_time: 本次日结开始时间
    
    Returns:
        tuple: (期初余额, 变化统计开始时间, 变化统计结束时间)
    """
    from datetime import timedelta
    
    is_base_currency = (currency_id == base_currency_id)
    
    # 根据特性开关决定从哪个表获取上次日结记录
    if FeatureFlags.FEATURE_NEW_PERIOD_BALANCE:
        # 从EODStatus表获取上次日结记录
        last_eod = session.query(EODStatus).filter(
            and_(
                EODStatus.branch_id == branch_id,
                EODStatus.status == 'completed',
                EODStatus.completed_at.isnot(None),
                EODStatus.completed_at < eod_start_time
            )
        ).order_by(EODStatus.completed_at.desc()).first()
        
        if last_eod:
            # 从EODBalanceVerification表获取期初余额
            balance_record = session.query(EODBalanceVerification).filter(
                and_(
                    EODBalanceVerification.eod_status_id == last_eod.id,
                    EODBalanceVerification.currency_id == currency_id
                )
            ).first()
            
            if balance_record:
                opening_balance = float(balance_record.actual_balance or 0)
                # 变化统计开始时间：上次日结结束时间+1秒
                change_start_time = last_eod.completed_at + timedelta(seconds=1)
                logging.info(f"📊 币种{currency_id}从EODBalanceVerification获取期初余额: {opening_balance}")
                logging.info(f"📊 币种{currency_id}变化统计开始时间: {change_start_time}")
                return opening_balance, change_start_time, eod_start_time
    else:
        # 从EODHistory表获取上次日结记录
        last_eod = session.query(EODHistory).filter(
            and_(
                EODHistory.branch_id == branch_id,
                EODHistory.created_at < eod_start_time
            )
        ).order_by(EODHistory.created_at.desc()).first()
        
        if last_eod:
            # 从EODBalanceSnapshot表获取期初余额
            balance_record = session.query(EODBalanceSnapshot).filter(
                and_(
                    EODBalanceSnapshot.eod_history_id == last_eod.id,
                    EODBalanceSnapshot.currency_id == currency_id
                )
            ).first()
            
            if balance_record:
                opening_balance = float(balance_record.remaining_balance or 0)
                # 变化统计开始时间：上次日结结束时间+1秒
                change_start_time = last_eod.created_at + timedelta(seconds=1)
                logging.info(f"📊 币种{currency_id}从EODBalanceSnapshot获取期初余额: {opening_balance}")
                logging.info(f"📊 币种{currency_id}变化统计开始时间: {change_start_time}")
                return opening_balance, change_start_time, eod_start_time
    
    # 如果没有找到日结记录，使用第一笔交易作为期初
    logging.info(f"📊 币种{currency_id}无上次日结记录，使用第一笔交易作为期初")
    
    # 查询该币种在日结开始时间前的第一笔交易（按时间正序）
    first_transaction = session.query(ExchangeTransaction).filter(
        and_(
            ExchangeTransaction.branch_id == branch_id,
            ExchangeTransaction.currency_id == currency_id,
            ExchangeTransaction.created_at < eod_start_time,
            ExchangeTransaction.type.in_(['initial_balance', 'adjust_balance', 'buy', 'sell', 'reversal', 'cash_out'])
        )
    ).order_by(ExchangeTransaction.created_at.asc()).first()
    
    if not first_transaction:
        logging.info(f"📊 币种{currency_id}无历史交易记录，期初余额为0")
        return 0.0, eod_start_time, eod_start_time
    
    # 取第一笔交易的值作为期初余额
    if is_base_currency:
        # 本币使用local_amount字段
        opening_balance = float(first_transaction.local_amount)
    else:
        # 外币使用amount字段
        opening_balance = float(first_transaction.amount)
    
    # 变化统计从第一笔交易时间之后开始（+1秒）
    change_start_time = first_transaction.created_at + timedelta(seconds=1)
    
    logging.info(f"📊 币种{currency_id}期初余额计算：第一笔交易ID={first_transaction.id}, 时间={first_transaction.created_at}, 期初余额={opening_balance}")
    logging.info(f"📊 币种{currency_id}变化统计开始时间：{change_start_time}")
    
    return opening_balance, change_start_time, eod_start_time

def _calculate_opening_balance_from_transactions(session, branch_id, currency_id, eod_start_time, base_currency_id):
    """
    当没有上次日结记录时，按照用户要求的逻辑计算期初余额
    
    规则：
    1. 查找该币种在日结开始时间之前的第一笔交易
    2. 第一笔交易的amount/local_amount值直接作为期初余额（不考虑交易类型）
    3. 外币使用amount字段，本币使用local_amount字段
    
    Args:
        session: 数据库会话
        branch_id: 网点ID
        currency_id: 币种ID
        eod_start_time: 日结开始时间
        base_currency_id: 基础货币ID
    
    Returns:
        tuple: (期初余额, 变化统计开始时间)
    """
    is_base_currency = (currency_id == base_currency_id)
    
    # 查询该币种在日结开始时间前的第一笔交易（按时间正序）
    first_transaction = session.query(ExchangeTransaction).filter(
        and_(
            ExchangeTransaction.branch_id == branch_id,
            ExchangeTransaction.currency_id == currency_id,
            ExchangeTransaction.created_at < eod_start_time,
            ExchangeTransaction.type.in_(['initial_balance', 'adjust_balance', 'buy', 'sell', 'reversal', 'cash_out'])
        )
    ).order_by(ExchangeTransaction.created_at.asc()).first()
    
    if not first_transaction:
        logging.info(f"📊 币种{currency_id}无历史交易记录，期初余额为0")
        return 0.0, eod_start_time
    
    # 取第一笔交易的值作为期初余额
    if is_base_currency:
        # 本币使用local_amount字段
        opening_balance = float(first_transaction.local_amount)
    else:
        # 外币使用amount字段
        opening_balance = float(first_transaction.amount)
    
    # 变化统计从第一笔交易时间之后开始（+1秒）
    from datetime import timedelta
    change_start_time = first_transaction.created_at + timedelta(seconds=1)
    
    logging.info(f"📊 币种{currency_id}期初余额计算：第一笔交易ID={first_transaction.id}, 时间={first_transaction.created_at}, 期初余额={opening_balance}")
    logging.info(f"📊 币种{currency_id}变化统计开始时间：{change_start_time}")
    
    return opening_balance, change_start_time

def CalBalance(branch_id, start_time, end_time):
    """
    计算库存外币报表
    
    Args:
        branch_id: 网点ID
        start_time: 开始时间
        end_time: 结束时间
    
    Returns:
        dict: 库存统计数据
    """
    session = DatabaseService.get_session()
    
    try:
        # 【日志】记录CalBalance函数的调用参数
        logging.info(f"💳 CalBalance函数被调用 - 网点ID: {branch_id}")
        logging.info(f"📅 CalBalance查询时间范围: {start_time.strftime('%Y-%m-%d %H:%M:%S')} 到 {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info(f"⏰ CalBalance时间跨度: {(end_time - start_time).total_seconds() / 3600:.2f} 小时")
        
        # 获取网点信息
        branch = session.query(Branch).options(
            joinedload(Branch.base_currency)
        ).filter_by(id=branch_id).first()
        
        if not branch:
            raise ValueError(f"网点ID {branch_id} 不存在")
        
        base_currency_code = branch.base_currency.currency_code if branch.base_currency else 'USD'
        base_currency_id = branch.base_currency_id if branch else None
        
        # 获取当前正在处理的日结记录，用于确定统计时间范围
        current_eod = session.query(EODStatus).filter(
            EODStatus.branch_id == branch_id,
            EODStatus.status.in_(['processing', 'completed'])
        ).order_by(desc(EODStatus.started_at)).first()
        
        eod_start_time = current_eod.started_at if current_eod else datetime.now()
        
        # 获取所有可能存在余额的币种
        active_currencies = session.query(Currency).all()
        currency_map = {c.id: c for c in active_currencies}
        
        # 【优化】只获取有实际交易或余额的货币，避免处理所有22种货币
        # 先查询有交易记录的货币
        currencies_with_transactions = session.query(ExchangeTransaction.currency_id).filter(
            ExchangeTransaction.branch_id == branch_id
        ).distinct().all()
        
        # 查询有余额记录的货币
        currencies_with_balance = session.query(CurrencyBalance.currency_id).filter(
            CurrencyBalance.branch_id == branch_id,
            CurrencyBalance.balance != 0
        ).distinct().all()
        
        # 合并有交易或有余额的货币
        relevant_currency_ids = set()
        for (currency_id,) in currencies_with_transactions:
            relevant_currency_ids.add(currency_id)
        for (currency_id,) in currencies_with_balance:
            relevant_currency_ids.add(currency_id)
            
        # 【重要】确保基础货币始终包含在内
        if base_currency_id:
            relevant_currency_ids.add(base_currency_id)
            
        # 过滤出相关的货币
        relevant_currencies = [c for c in active_currencies if c.id in relevant_currency_ids]
        
        logging.info(f"💡 性能优化: 总币种数 {len(active_currencies)}, 相关币种数 {len(relevant_currencies)}")
        
        # 使用优化后的货币列表
        active_currencies = relevant_currencies
        
        # 【使用与日结相同的期初余额获取逻辑】
        from datetime import timedelta
        
        # 【修复】为每个币种单独计算变化统计时间范围和期初余额
        opening_balances = {}
        currency_change_periods = {}  # 存储每个币种的变化统计时间范围
        
        if FeatureFlags.FEATURE_NEW_PERIOD_BALANCE:
            # 【新方式】从EODBalanceVerification表获取上次日结的actual_balance
            logging.info("🔧 使用新方式：从EODBalanceVerification表获取期初余额")
            
            for currency in active_currencies:
                # 查找上次已完成日结的余额验证记录
                prev_eod_verification = session.query(EODBalanceVerification).join(EODStatus).filter(
                    EODStatus.branch_id == branch_id,
                    EODStatus.status == 'completed',
                    EODBalanceVerification.currency_id == currency.id
                ).order_by(desc(EODStatus.completed_at)).first()
                
                if prev_eod_verification:
                    # 1.1 有上次日结记录：使用上次日结验证后的实际余额作为期初
                    opening_balances[currency.id] = float(prev_eod_verification.actual_balance)
                    # 变化统计从上次日结结束时间+1秒开始
                    prev_eod_status = session.query(EODStatus).filter_by(
                        id=prev_eod_verification.eod_status_id
                    ).first()
                    if prev_eod_status and prev_eod_status.completed_at:
                        change_start = prev_eod_status.completed_at + timedelta(seconds=1)
                        change_end = end_time  # 使用查询的结束时间，而不是日结开始时间
                        currency_change_periods[currency.id] = (change_start, change_end)
                        logging.info(f"📊 {currency.currency_code} 期初余额: {opening_balances[currency.id]} (来自EODBalanceVerification)")
                        logging.info(f"📅 {currency.currency_code} 变化统计时间: {change_start} 到 {change_end}")
                    else:
                        # 如果没有完成时间，使用默认时间范围
                        currency_change_periods[currency.id] = (start_time, end_time)
                else:
                    # 1.2 没有上次日结记录：按照用户要求的逻辑计算期初余额和变化统计时间范围
                    opening_balance, change_start = _calculate_opening_balance_from_transactions(
                        session, branch_id, currency.id, eod_start_time, base_currency_id
                    )
                    opening_balances[currency.id] = opening_balance
                    change_end = end_time  # 使用查询的结束时间，而不是日结开始时间
                    currency_change_periods[currency.id] = (change_start, change_end)
                    logging.info(f"📊 {currency.currency_code} 期初余额: {opening_balances[currency.id]} (第一笔交易值)")
                    logging.info(f"📅 {currency.currency_code} 变化统计时间: {change_start} 到 {change_end}")
        else:
            # 【传统方式】从EODBalanceSnapshot表获取remaining_balance
            logging.info("🔧 使用传统方式：从EODBalanceSnapshot表获取期初余额")
            
            for currency in active_currencies:
                # 查找上次日结的余额快照记录
                prev_snapshot = session.query(EODBalanceSnapshot).join(EODHistory).filter(
                    EODHistory.branch_id == branch_id,
                    EODBalanceSnapshot.currency_id == currency.id
                ).order_by(desc(EODHistory.created_at)).first()
                
                if prev_snapshot:
                    # 1.1 有上次日结记录：使用上次日结的剩余余额作为期初
                    opening_balances[currency.id] = float(prev_snapshot.remaining_balance)
                    # 变化统计从上次日结结束时间+1秒开始
                    prev_eod_history = session.query(EODHistory).filter_by(
                        id=prev_snapshot.eod_history_id
                    ).first()
                    if prev_eod_history and prev_eod_history.created_at:
                        change_start = prev_eod_history.created_at + timedelta(seconds=1)
                        change_end = end_time  # 使用查询的结束时间，而不是日结开始时间
                        currency_change_periods[currency.id] = (change_start, change_end)
                        logging.info(f"📊 {currency.currency_code} 期初余额: {opening_balances[currency.id]} (来自EODBalanceSnapshot)")
                        logging.info(f"📅 {currency.currency_code} 变化统计时间: {change_start} 到 {change_end}")
                    else:
                        # 如果没有完成时间，使用默认时间范围
                        currency_change_periods[currency.id] = (start_time, end_time)
                else:
                    # 1.2 没有上次日结记录：按照用户要求的逻辑计算期初余额和变化统计时间范围
                    opening_balance, change_start = _calculate_opening_balance_from_transactions(
                        session, branch_id, currency.id, eod_start_time, base_currency_id
                    )
                    opening_balances[currency.id] = opening_balance
                    change_end = end_time  # 使用查询的结束时间，而不是日结开始时间
                    currency_change_periods[currency.id] = (change_start, change_end)
                    logging.info(f"📊 {currency.currency_code} 期初余额: {opening_balances[currency.id]} (第一笔交易值)")
                    logging.info(f"📅 {currency.currency_code} 变化统计时间: {change_start} 到 {change_end}")

        # 【修复】计算全局的变化统计时间范围
        # 从所有币种的时间范围中计算最早开始时间和最晚结束时间
        all_start_times = []
        all_end_times = []
        
        for currency_id, (period_start, period_end) in currency_change_periods.items():
            all_start_times.append(period_start)
            all_end_times.append(period_end)
        
        # 如果有币种的时间范围，使用最早的开始时间和最晚的结束时间
        if all_start_times and all_end_times:
            change_start_time = min(all_start_times)
            change_end_time = max(all_end_times)
        else:
            # 如果没有币种数据，使用传入的时间范围
            change_start_time = start_time
            change_end_time = end_time
        
        logging.info(f"📅 全局变化统计时间范围: {change_start_time} 到 {change_end_time}")

        # 【修复】按币种分别查询变动期间的交易，使用各自的时间范围
        currency_changes = {}
        
        for currency in active_currencies:
            currency_id = currency.id
            change_start, change_end = currency_change_periods.get(currency_id, (start_time, end_time))
            
            # 查询该币种在其特定时间范围内的交易
            change_filter_conditions = [
                ExchangeTransaction.branch_id == branch_id,
                ExchangeTransaction.currency_id == currency_id,
                ExchangeTransaction.created_at >= change_start,
                ExchangeTransaction.created_at < change_end,
                ExchangeTransaction.type.in_(['buy', 'sell', 'initial_balance', 'adjust_balance', 'cash_out', 'reversal'])
            ]
            
            # 根据特性开关决定是否排除冲正交易
            if FeatureFlags.FEATURE_NEW_BUSINESS_TIME_RANGE:
                change_filter_conditions.append(ExchangeTransaction.status != 'reversed')
            
            change_transactions = session.query(
                ExchangeTransaction.type,
                ExchangeTransaction.amount,
                ExchangeTransaction.local_amount
            ).filter(and_(*change_filter_conditions)).all()
            
            logging.info(f"📊 {currency.currency_code} 变动计算: 查询到 {len(change_transactions)} 笔变动交易 (时间范围: {change_start} 到 {change_end})")
            
            # 初始化币种变动统计
            currency_changes[currency_id] = {
                'total_buy': 0,
                'total_sell': 0,
                'total_initial': 0,
                'total_adjust': 0,
                'total_cash_out': 0
            }
            
            # 统计该币种的变动
            for tx in change_transactions:
                amount = float(tx.amount)
                local_amount = float(tx.local_amount)
                
                if tx.type == 'buy':
                    currency_changes[currency_id]['total_buy'] += abs(amount)
                elif tx.type == 'sell':
                    currency_changes[currency_id]['total_sell'] += abs(amount)
                elif tx.type == 'initial_balance':
                    currency_changes[currency_id]['total_initial'] += amount
                elif tx.type == 'adjust_balance':
                    currency_changes[currency_id]['total_adjust'] += amount
                elif tx.type == 'cash_out':
                    currency_changes[currency_id]['total_cash_out'] += abs(amount)
        
        # 【修复】为基础货币单独处理本币变动
        if base_currency_id:
            if base_currency_id not in currency_changes:
                currency_changes[base_currency_id] = {
                    'total_buy': 0,
                    'total_sell': 0,
                    'total_initial': 0,
                    'total_adjust': 0,
                    'total_cash_out': 0
                }
                logging.info(f"🏦 初始化基础货币变动数据: {base_currency_id}")
            
            # 统计基础货币的变动（通过所有交易的local_amount）
            change_start, change_end = currency_change_periods.get(base_currency_id, (start_time, end_time))
            
            all_transactions = session.query(
                ExchangeTransaction.type,
                ExchangeTransaction.local_amount,
                ExchangeTransaction.currency_id
            ).filter(
                and_(
                    ExchangeTransaction.branch_id == branch_id,
                    ExchangeTransaction.created_at >= change_start,
                    ExchangeTransaction.created_at < change_end,
                    ExchangeTransaction.type.in_(['buy', 'sell', 'initial_balance', 'adjust_balance', 'cash_out', 'reversal'])
                )
            ).all()
            
            # 【修复】基础货币的计算逻辑：直接累加所有交易的local_amount（带正负号）
            for tx in all_transactions:
                local_amount = float(tx.local_amount)
                # 对于基础货币，所有交易的local_amount都直接累加（正负抵消）
                currency_changes[base_currency_id]['total_adjust'] += local_amount
            
            logging.info(f"🏦 基础货币变动统计完成: {currency_changes[base_currency_id]}")
        
        # 【修复】确保基础货币在opening_balances中有记录
        if base_currency_id and base_currency_id not in opening_balances:
            opening_balances[base_currency_id] = 0
            logging.info(f"🏦 初始化基础货币期初余额: {base_currency_id} = 0")
        
        # 获取所有涉及的币种（期初余额 + 变动交易涉及的币种）
        all_currency_ids = set(opening_balances.keys()) | set(currency_changes.keys())
        
        logging.info(f"🏦 所有币种ID: {all_currency_ids}")
        logging.info(f"🏦 基础货币ID: {base_currency_id}")
        
        result_currencies = []
        
        for currency_id in all_currency_ids:
            currency = currency_map.get(currency_id)
            if not currency:
                logging.warning(f"🏦 币种ID {currency_id} 在currency_map中未找到")
                continue
            
            # 【修复】为基础货币添加专门的统计逻辑
            is_base_currency = (currency_id == base_currency_id)
            
            # 获取期初余额（从日结快照获取）
            opening_balance = opening_balances.get(currency_id, 0)
            
            # 获取变动数据
            changes = currency_changes.get(currency_id, {
                'total_buy': 0,
                'total_sell': 0,
                'total_initial': 0,
                'total_adjust': 0,
                'total_cash_out': 0
            })
            
            # 【修复】基础货币和外币的变动计算逻辑不同
            if is_base_currency:
                # 【简化】基础货币的变动计算：直接使用所有交易local_amount的累加（带正负号）
                change_amount = changes['total_adjust']
                
                logging.info(f"💰 基础货币({currency.currency_code})变动计算: 直接累加所有交易local_amount = {change_amount}")
            else:
                # 外币的变动计算（原逻辑）
                change_amount = (
                    changes['total_buy'] -
                    changes['total_sell'] +
                    changes['total_initial'] +
                    changes['total_adjust'] -
                    changes['total_cash_out']
                )
            
            # 当前余额 = 期初余额 + 变动金额
            current_balance = opening_balance + change_amount
            
            # 只有存在余额或变动的币种才加入结果，但基础货币始终包含
            if opening_balance != 0 or change_amount != 0 or current_balance != 0 or is_base_currency:
                result_currencies.append({
                    'currency_code': currency.currency_code,
                    'currency_name': currency.currency_name,
                    'custom_flag_filename': currency.custom_flag_filename,  # 【新增】自定义图标文件名
                    'flag_code': currency.flag_code,  # 【新增】标准图标代码
                    'total_buy': changes['total_buy'],
                    'total_sell': changes['total_sell'],
                    'opening_balance': opening_balance,
                    'change_amount': change_amount,
                    'current_balance': current_balance,
                    'stock_balance': current_balance,  # 保留原字段以兼容
                    'is_base_currency': is_base_currency  # 【新增】标记是否为基础货币
                })
                
                logging.info(f"📊 {currency.currency_code}: 期初={opening_balance}, 变动={change_amount}, 当前={current_balance}, 是否本币={is_base_currency}")
            else:
                logging.info(f"📊 {currency.currency_code}: 跳过（无余额且非本币）")
        
        logging.info(f"📋 CalBalance计算完成: 共 {len(result_currencies)} 种外币")
        
        # 【调试】检查基础货币是否在结果中
        base_currency_in_result = any(c.get('is_base_currency', False) for c in result_currencies)
        logging.info(f"🏦 基础货币是否在结果中: {base_currency_in_result}")
        if not base_currency_in_result and base_currency_id:
            logging.error(f"🏦 警告：基础货币 {base_currency_id} 未包含在结果中！")
        
        return {
            'branch_id': branch_id,
            'branch_name': branch.branch_name,
            'base_currency': base_currency_code,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'actual_change_start_time': change_start_time.isoformat(),
            'actual_change_end_time': change_end_time.isoformat(),
            'period_balance_method': 'EODBalanceVerification' if FeatureFlags.FEATURE_NEW_PERIOD_BALANCE else 'EODBalanceSnapshot',
            'business_time_range_enabled': FeatureFlags.FEATURE_NEW_BUSINESS_TIME_RANGE,
            'currencies': result_currencies
        }
        
    finally:
        DatabaseService.close_session(session)

def get_daily_time_range(branch_id):
    """
    获取当前业务周期的时间范围
    规则：
    1. 起始时间 = 上一次日结的结束时间+1秒（如果有）
    2. 如果没有上次日结，则从当天0点开始（符合用户要求）
    3. 结束时间 = 当前查询时间（对于查询接口）或本次日结开始时间（对于日结过程）
    4. 根据特性开关 FEATURE_NEW_PERIOD_BALANCE 确定从哪个表获取上次日结结束时间
    
    Args:
        branch_id: 网点ID
    Returns:
        tuple: (start_time, end_time)
    """
    session = DatabaseService.get_session()
    try:
        # 【日志】记录时间范围计算开始
        logging.info(f"⏰ 开始计算业务时间范围 - 网点ID: {branch_id}")
        logging.info(f"🔧 特性开关FEATURE_NEW_PERIOD_BALANCE: {FeatureFlags.FEATURE_NEW_PERIOD_BALANCE}")
        
        # 【修复】结束时间逻辑：如果有正在进行的日结，使用其开始时间；否则使用当前时间
        current_eod = session.query(EODStatus).filter(
            and_(
                EODStatus.branch_id == branch_id,
                EODStatus.status == 'processing'
            )
        ).order_by(EODStatus.started_at.desc()).first()
        
        if current_eod and current_eod.started_at:
            # 如果有正在进行的日结，使用其开始时间作为结束时间
            end_time = current_eod.started_at
            logging.info(f"📅 结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')} (本次日结开始时间)")
            logging.info(f"📝 当前日结ID: {current_eod.id}, 开始时间: {current_eod.started_at}")
        else:
            # 如果没有正在进行的日结，使用当前时间作为结束时间
            end_time = datetime.now()
            logging.info(f"📅 结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')} (当前查询时间)")
            logging.info(f"📝 无正在进行的日结")
        
        # 根据特性开关决定从哪个表获取上次日结结束时间
        if FeatureFlags.FEATURE_NEW_PERIOD_BALANCE:
            # 从EODStatus表获取
            logging.info(f"🔍 从EODStatus表获取上次日结结束时间")
            last_completed_eod = session.query(EODStatus).filter(
                and_(
                    EODStatus.branch_id == branch_id,
                    EODStatus.status == 'completed',
                    EODStatus.completed_at.isnot(None)
                )
            ).order_by(EODStatus.completed_at.desc()).first()
            
            if last_completed_eod:
                # 【修复】如果有上一次日结，从其结束时间+1秒开始
                from datetime import timedelta
                start_time = last_completed_eod.completed_at + timedelta(seconds=1)
                logging.info(f"✅ 找到上一次日结记录(EODStatus)，开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')} (+1秒)")
                logging.info(f"📝 上一次日结ID: {last_completed_eod.id}, 完成时间: {last_completed_eod.completed_at}")
            else:
                # 如果没有上一次日结，从第一笔交易时间开始
                first_transaction = session.query(ExchangeTransaction).filter(
                    ExchangeTransaction.branch_id == branch_id
                ).order_by(ExchangeTransaction.created_at.asc()).first()
                
                if first_transaction:
                    start_time = first_transaction.created_at
                    logging.info(f"✅ 找到第一笔交易，开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    logging.info(f"📝 第一笔交易ID: {first_transaction.id}, 币种: {first_transaction.currency_id}")
                else:
                    # 如果没有任何交易，从当天0点开始
                    today = date.today()
                    start_time = datetime.combine(today, datetime.min.time())
                    logging.info(f"⚠️ 未找到任何交易记录，从当天0点开始: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    logging.info(f"📅 当天日期: {today}")
        else:
            # 从EODHistory表获取
            logging.info(f"🔍 从EODHistory表获取上次日结结束时间")
            last_completed_eod = session.query(EODHistory).filter(
                EODHistory.branch_id == branch_id
            ).order_by(EODHistory.created_at.desc()).first()
            
            if last_completed_eod:
                # 【修复】如果有上一次日结，从其结束时间+1秒开始
                from datetime import timedelta
                start_time = last_completed_eod.created_at + timedelta(seconds=1)
                logging.info(f"✅ 找到上一次日结记录(EODHistory)，开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')} (+1秒)")
                logging.info(f"📝 上一次日结ID: {last_completed_eod.id}, 完成时间: {last_completed_eod.created_at}")
            else:
                # 如果没有上一次日结，从第一笔交易时间开始
                first_transaction = session.query(ExchangeTransaction).filter(
                    ExchangeTransaction.branch_id == branch_id
                ).order_by(ExchangeTransaction.created_at.asc()).first()
                
                if first_transaction:
                    start_time = first_transaction.created_at
                    logging.info(f"✅ 找到第一笔交易，开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    logging.info(f"📝 第一笔交易ID: {first_transaction.id}, 币种: {first_transaction.currency_id}")
                else:
                    # 如果没有任何交易，从当天0点开始
                    today = date.today()
                    start_time = datetime.combine(today, datetime.min.time())
                    logging.info(f"⚠️ 未找到任何交易记录，从当天0点开始: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    logging.info(f"📅 当天日期: {today}")
        
        # 【日志】记录最终的时间范围
        logging.info(f"📊 最终业务时间范围: {start_time.strftime('%Y-%m-%d %H:%M:%S')} 到 {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info(f"⏰ 业务时间跨度: {(end_time - start_time).total_seconds() / 3600:.2f} 小时")
        
        return start_time, end_time
        
    finally:
        DatabaseService.close_session(session)

@reports_bp.route('/income', methods=['GET'])
@token_required
def get_income_report(current_user):
    """获取动态收入统计报表"""
    try:
        # 检查权限
        user_permissions = current_user.get('permissions', [])
        if 'view_transactions' not in user_permissions:
            return jsonify({
                'success': False,
                'message': '权限不足，需要view_transactions权限'
            }), 403
        
        branch_id = current_user.get('branch_id')
        if not branch_id:
            return jsonify({
                'success': False,
                'message': '网点信息不存在'
            }), 400
        
        # 【修复】使用统一的业务时间范围获取逻辑
        start_time, now = get_daily_time_range(branch_id)
        
        # 【日志】记录动态收入查询的时间条件
        import logging
        logging.info(f"🔍 动态收入查询 - 网点ID: {branch_id}")
        logging.info(f"📅 查询时间范围: {start_time.strftime('%Y-%m-%d %H:%M:%S')} 到 {now.strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info(f"⏰ 时间跨度: {(now - start_time).total_seconds() / 3600:.2f} 小时")
        logging.info(f"🏪 时间范围类型: 业务周期时间范围（从上次日结结束时间开始）")
        
        # 【修复】调用CalGain函数计算收入，启用按币种分别计算模式
        report_data = CalGain(branch_id, start_time, now)
        
        # 【日志】记录汇总结果
        logging.info(f"📊 动态收入汇总结果: 总收入={report_data.get('total_income', 0)}, 币种数量={len(report_data.get('currencies', []))}")
        
        return jsonify({
            'success': True,
            'data': report_data
        })
        
    except Exception as e:
        multilingual_logger.log_system_error(
            'income_report_error',
            details=f"获取收入报表失败: {str(e)}",
            language='zh-CN'
        )
        return jsonify({
            'success': False,
            'message': f'获取收入报表失败: {str(e)}'
        }), 500

@reports_bp.route('/stock', methods=['GET'])
@token_required
def get_stock_report(current_user):
    """获取库存外币统计报表"""
    try:
        # 检查权限
        user_permissions = current_user.get('permissions', [])
        if 'view_balances' not in user_permissions:
            return jsonify({
                'success': False,
                'message': '权限不足，需要view_balances权限'
            }), 403
        
        branch_id = current_user.get('branch_id')
        if not branch_id:
            return jsonify({
                'success': False,
                'message': '网点信息不存在'
            }), 400
        
        # 【修复】使用统一的业务时间范围获取逻辑
        start_time, now = get_daily_time_range(branch_id)
        
        # 【日志】记录动态库存查询的时间条件
        import logging
        logging.info(f"🔍 动态库存查询 - 网点ID: {branch_id}")
        logging.info(f"📅 查询时间范围: {start_time.strftime('%Y-%m-%d %H:%M:%S')} 到 {now.strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info(f"⏰ 时间跨度: {(now - start_time).total_seconds() / 3600:.2f} 小时")
        logging.info(f"🏪 时间范围类型: 业务周期时间范围（从上次日结结束时间开始）")
        
        # 【修复】调用CalBalance函数计算库存，启用按币种分别计算模式
        report_data = CalBalance(branch_id, start_time, now)
        
        # 【修复】使用CalBalance函数返回的is_base_currency字段过滤本币
        if 'currencies' in report_data:
            original_count = len(report_data['currencies'])
            report_data['currencies'] = [
                currency for currency in report_data['currencies']
                if not currency.get('is_base_currency', False)
            ]
            filtered_count = len(report_data['currencies'])
            logging.info(f"🚫 过滤本币: 原始币种数={original_count}, 过滤后币种数={filtered_count}")
        else:
            logging.info(f"ℹ️ 未进行本币过滤: 无currencies数据")
        
        # 【日志】记录汇总结果
        logging.info(f"📊 动态库存汇总结果: 币种数量={len(report_data.get('currencies', []))}")
        
        return jsonify({
            'success': True,
            'data': report_data
        })
        
    except Exception as e:
        multilingual_logger.log_system_error(
            'stock_report_error',
            details=f"获取库存报表失败: {str(e)}",
            language='zh-CN'
        )
        return jsonify({
            'success': False,
            'message': f'获取库存报表失败: {str(e)}'
        }), 500

@reports_bp.route('/income/export', methods=['POST'])
@token_required
def export_income_report(current_user):
    """导出收入报表PDF"""
    try:
        from services.simple_pdf_service import SimplePDFService
        
        # 获取语言参数
        data = request.get_json() or {}
        language = data.get('language', 'zh')
        
        # 检查权限
        user_permissions = current_user.get('permissions', [])
        if 'branch_manage' not in user_permissions and 'system_manage' not in user_permissions:
            permission_messages = {
                'zh': '权限不足',
                'en': 'Insufficient permissions',
                'th': 'สิทธิ์ไม่เพียงพอ'
            }
            return jsonify({
                'success': False,
                'message': permission_messages.get(language, permission_messages['zh'])
            }), 403
        
        # 获取当前收入报表数据
        branch_id = current_user.get('branch_id')
        if not branch_id:
            branch_messages = {
                'zh': '网点信息不存在',
                'en': 'Branch information not found',
                'th': 'ไม่พบข้อมูลสาขา'
            }
            return jsonify({
                'success': False,
                'message': branch_messages.get(language, branch_messages['zh'])
            }), 400
        
        # 获取今日时间范围
        start_time, end_time = get_daily_time_range(branch_id)
        
        # 获取收入统计数据
        income_data = CalGain(branch_id, start_time, end_time)
        
        # 直接传递收入数据给PDF生成器
        pdf_content = SimplePDFService.generate_income_report_pdf(income_data, language)
        
        # 根据语言设置成功消息
        success_messages = {
            'zh': 'PDF导出成功',
            'en': 'PDF export successful',
            'th': 'ส่งออก PDF สำเร็จ'
        }
        
        return jsonify({
            'success': True,
            'message': success_messages.get(language, success_messages['zh']),
            'pdf_content': pdf_content
        })
        
    except Exception as e:
        # 根据语言设置错误消息
        error_messages = {
            'zh': f'导出失败: {str(e)}',
            'en': f'Export failed: {str(e)}',
            'th': f'การส่งออกล้มเหลว: {str(e)}'
        }
        
        return jsonify({
            'success': False,
            'message': error_messages.get(language, f'导出失败: {str(e)}')
        }), 500

@reports_bp.route('/stock/export', methods=['POST'])
@token_required
def export_stock_report(current_user):
    """导出库存报表PDF"""
    try:
        from services.simple_pdf_service import SimplePDFService
        
        # 获取语言参数
        data = request.get_json() or {}
        language = data.get('language', 'zh')
        
        # 检查权限
        user_permissions = current_user.get('permissions', [])
        if 'branch_manage' not in user_permissions and 'system_manage' not in user_permissions:
            permission_messages = {
                'zh': '权限不足',
                'en': 'Insufficient permissions',
                'th': 'สิทธิ์ไม่เพียงพอ'
            }
            return jsonify({
                'success': False,
                'message': permission_messages.get(language, permission_messages['zh'])
            }), 403
        
        # 获取当前库存报表数据
        branch_id = current_user.get('branch_id')
        if not branch_id:
            branch_messages = {
                'zh': '网点信息不存在',
                'en': 'Branch information not found',
                'th': 'ไม่พบข้อมูลสาขา'
            }
            return jsonify({
                'success': False,
                'message': branch_messages.get(language, branch_messages['zh'])
            }), 400
        
        # 获取今日时间范围
        start_time, end_time = get_daily_time_range(branch_id)
        
        # 获取库存统计数据
        stock_data = CalBalance(branch_id, start_time, end_time)
        
        # 直接传递库存数据给PDF生成器
        pdf_content = SimplePDFService.generate_stock_report_pdf(stock_data, language)
        
        # 根据语言设置成功消息
        success_messages = {
            'zh': 'PDF导出成功',
            'en': 'PDF export successful',
            'th': 'ส่งออก PDF สำเร็จ'
        }
        
        return jsonify({
            'success': True,
            'message': success_messages.get(language, success_messages['zh']),
            'pdf_content': pdf_content
        })
        
    except Exception as e:
        # 根据语言设置错误消息
        error_messages = {
            'zh': f'导出失败: {str(e)}',
            'en': f'Export failed: {str(e)}',
            'th': f'การส่งออกล้มเหลว: {str(e)}'
        }
        
        return jsonify({
            'success': False,
            'message': error_messages.get(language, f'导出失败: {str(e)}')
        }), 500

@reports_bp.route('/check-permissions', methods=['GET'])
@token_required
def check_report_permissions(current_user):
    """检查用户报表权限"""
    try:
        user_permissions = current_user.get('permissions', [])
        branch_id = current_user.get('branch_id')
        
        return jsonify({
            'success': True,
            'data': {
                'user_id': current_user.get('user_id'),
                'username': current_user.get('name', '未知用户'),
                'branch_id': branch_id,
                'permissions': user_permissions,
                'has_branch_manage': 'branch_manage' in user_permissions,
                'has_system_manage': 'system_manage' in user_permissions,
                'can_view_reports': 'branch_manage' in user_permissions or 'system_manage' in user_permissions
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'检查权限失败: {str(e)}'
        }), 500

@reports_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查API"""
    return jsonify({
        'success': True,
        'message': 'Reports API is healthy',
        'timestamp': datetime.now().isoformat()
    })

@reports_bp.route('/test-auth', methods=['GET'])
@token_required
def test_auth(current_user):
    """测试token验证API"""
    logger.info(f"🧪 测试API被调用，用户信息: {current_user}")
    return jsonify({
        'success': True,
        'message': 'Token验证成功',
        'user_info': {
            'id': current_user.get('id'),
            'name': current_user.get('name'),
            'login_code': current_user.get('login_code'),
            'branch_id': current_user.get('branch_id'),
            'permissions': current_user.get('permissions', [])
        }
    })

@reports_bp.route('/test-income', methods=['GET'])
@token_required
def test_income_simple(current_user):
    """简化版收入报表测试API"""
    logger.info(f"🧪 简化收入测试API被调用")
    logger.info(f"👤 用户: {current_user.get('name')} (ID: {current_user.get('id')})")
    logger.info(f"🔑 权限: {current_user.get('permissions', [])}")
    
    # 检查权限
    user_permissions = current_user.get('permissions', [])
    has_branch_manage = 'branch_manage' in user_permissions
    has_system_manage = 'system_manage' in user_permissions
    
    logger.info(f"🔍 branch_manage权限: {has_branch_manage}")
    logger.info(f"🔍 system_manage权限: {has_system_manage}")
    
    if not has_branch_manage and not has_system_manage:
        logger.warning(f"❌ 权限不足")
        return jsonify({
            'success': False,
            'message': '权限不足，需要branch_manage或system_manage权限',
            'user_permissions': user_permissions,
            'required_permissions': ['branch_manage', 'system_manage']
        }), 403
    
    logger.info(f"✅ 权限检查通过，返回简单数据")
    return jsonify({
        'success': True,
        'message': '权限检查通过',
        'user_info': {
            'name': current_user.get('name'),
            'permissions': user_permissions,
            'has_required_permission': True
        }
    })

@reports_bp.route('/test-currency/<currency_code>', methods=['GET'])
@token_required
def test_currency_simple(current_user, currency_code):
    """简化版币种测试API"""
    logger.info(f"🧪 简化币种测试API被调用")
    logger.info(f"👤 用户: {current_user.get('name')} (ID: {current_user.get('id')})")
    logger.info(f"💰 币种: {currency_code}")
    logger.info(f"🔑 权限: {current_user.get('permissions', [])}")
    
    return jsonify({
        'success': True,
        'message': f'币种{currency_code}测试成功',
        'currency_code': currency_code,
        'user_name': current_user.get('name')
    })

@reports_bp.route('/income/currency/<currency_code>/transactions', methods=['GET'])
@token_required
def get_currency_transactions(current_user, currency_code):
    """获取特定币种的交易明细"""
    logger.info(f"🔍 币种交易明细API被调用")
    logger.info(f"📋 请求路径: {request.path}")
    logger.info(f"👤 用户信息: {current_user.get('name', '未知')} (ID: {current_user.get('id')})")
    logger.info(f"🏪 网点ID: {current_user.get('branch_id')}")
    logger.info(f"💰 查询币种: {currency_code}")
    logger.info(f"🔑 用户权限: {current_user.get('permissions', [])}")
    
    # 【修复】在函数开始时初始化session变量，避免作用域问题
    session = None
    
    try:
        # 记录用户信息
        user_permissions = current_user.get('permissions', [])
        logger.info(f"👤 用户权限: {user_permissions}")
        
        # 检查权限
        if 'branch_manage' not in user_permissions and 'system_manage' not in user_permissions:
            logger.warning(f"❌ 权限不足: 需要branch_manage或system_manage，当前有: {user_permissions}")
            return jsonify({
                'success': False,
                'message': '权限不足，需要branch_manage或system_manage权限'
            }), 403
        
        branch_id = current_user.get('branch_id')
        if not branch_id:
            logger.error("❌ 网点信息不存在")
            return jsonify({
                'success': False,
                'message': '网点信息不存在'
            }), 400
        
        # 【修复】使用正在处理的日结记录的实际时间范围，而不是get_daily_time_range
        # 首先查找正在处理的日结记录
        session = DatabaseService.get_session()  # 【修复】在这里创建session
        
        current_eod = session.query(EODStatus).filter(
            EODStatus.branch_id == branch_id,
            EODStatus.status == 'processing'
        ).first()
        
        if current_eod and current_eod.business_start_time and current_eod.business_end_time:
            # 使用正在处理的日结记录的实际时间范围
            start_time = current_eod.business_start_time
            end_time = current_eod.business_end_time
            time_range_source = "正在处理的日结记录"
        else:
            # 回退到通用的时间范围计算
            start_time, end_time = get_daily_time_range(branch_id)
            time_range_source = "通用时间范围计算"
        
        # 【日志】记录交易明细查询的时间条件
        logger.info(f"🔍 交易明细查询 - 网点ID: {branch_id}, 币种: {currency_code}")
        logger.info(f"📅 明细查询时间范围: {start_time.strftime('%Y-%m-%d %H:%M:%S')} 到 {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"⏰ 明细查询时间跨度: {(end_time - start_time).total_seconds() / 3600:.2f} 小时")
        logger.info(f"🏪 时间范围来源: {time_range_source}")
        logger.info(f"📊 当前日结记录: {current_eod.id if current_eod else '无'}")
        
        # 首先获取币种ID
        currency = session.query(Currency).filter(
            Currency.currency_code == currency_code
        ).first()
        
        if not currency:
            logger.error(f"❌ 币种代码 {currency_code} 不存在")
            return jsonify({
                'success': False,
                'message': f'币种代码 {currency_code} 不存在'
            }), 404
        
        logger.info(f"🔍 查询币种: {currency_code} (ID: {currency.id})")
        
        # 【新增】计算期初余额 - 使用与日结相同的逻辑
        opening_balance = 0
        opening_balance_source = ""
        
        if FeatureFlags.FEATURE_NEW_PERIOD_BALANCE:
            # 【新方式】从EODBalanceVerification表获取上次日结的actual_balance
            logger.info("🔧 使用新方式：从EODBalanceVerification表获取期初余额")
            
            prev_eod_verification = session.query(EODBalanceVerification).join(EODStatus).filter(
                EODStatus.branch_id == branch_id,
                EODStatus.status == 'completed',
                EODBalanceVerification.currency_id == currency.id
            ).order_by(desc(EODStatus.completed_at)).first()
            
            if prev_eod_verification:
                opening_balance = float(prev_eod_verification.actual_balance)
                opening_balance_source = f"EODBalanceVerification (日结ID: {prev_eod_verification.eod_status_id})"
                logger.info(f"📊 {currency_code} 期初余额: {opening_balance} (来自{opening_balance_source})")
            else:
                opening_balance = 0
                opening_balance_source = "无验证记录，默认为0"
                logger.info(f"📊 {currency_code} 期初余额: 0 (无验证记录)")
        else:
            # 【传统方式】从EODBalanceSnapshot表获取remaining_balance
            logger.info("🔧 使用传统方式：从EODBalanceSnapshot表获取期初余额")
            
            prev_snapshot = session.query(EODBalanceSnapshot).join(EODHistory).filter(
                EODHistory.branch_id == branch_id,
                EODBalanceSnapshot.currency_id == currency.id
            ).order_by(desc(EODHistory.created_at)).first()
            
            if prev_snapshot:
                opening_balance = float(prev_snapshot.remaining_balance)
                opening_balance_source = f"EODBalanceSnapshot (历史ID: {prev_snapshot.eod_history_id})"
                logger.info(f"📊 {currency_code} 期初余额: {opening_balance} (来自{opening_balance_source})")
            else:
                opening_balance = 0
                opening_balance_source = "无快照记录，默认为0"
                logger.info(f"📊 {currency_code} 期初余额: 0 (无快照记录)")
        
        # 【修复】查询特定币种的交易明细 - 使用与CalGain相同的查询条件
        # 【日志】记录SQL查询条件
        logger.info(f"🔍 【明细查询】get_currency_transactions查询条件:")
        logger.info(f"  - 网点ID: {branch_id}")
        logger.info(f"  - 币种ID: {currency.id} ({currency_code})")
        logger.info(f"  - 交易类型: ['buy', 'sell', 'adjust_balance', 'reversal', 'initial_balance']")
        logger.info(f"  - 包含状态: 所有状态（包括被冲正的交易）")
        logger.info(f"  - 时间范围: {start_time.strftime('%Y-%m-%d %H:%M:%S')} 到 {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"  - 时间条件SQL: created_at >= '{start_time}' AND created_at < '{end_time}'")
        
        transactions = session.query(ExchangeTransaction).filter(
            and_(
                ExchangeTransaction.branch_id == branch_id,
                ExchangeTransaction.currency_id == currency.id,
                ExchangeTransaction.type.in_(['buy', 'sell', 'adjust_balance', 'reversal', 'initial_balance']),  # 【修复】添加initial_balance，与CalGain完全一致
                # 【修复】移除 status != 'reversed' 条件，显示所有交易包括被冲正的交易
                ExchangeTransaction.created_at >= start_time,
                ExchangeTransaction.created_at < end_time  # 【修复】使用小于而不是小于等于
            )
        ).order_by(ExchangeTransaction.created_at.desc()).all()
        
        # 【日志】记录查询结果
        logger.info(f"📊 【明细查询】get_currency_transactions查询到 {len(transactions)} 笔交易记录")
        
        # 【日志】记录交易类型分布
        type_counts = {}
        for tx in transactions:
            type_counts[tx.type] = type_counts.get(tx.type, 0) + 1
        logger.info(f"📊 【明细查询】交易类型分布: {type_counts}")
        
        # 【日志】记录详细交易信息
        for tx in transactions:
            logger.info(f"  交易: 币种ID={tx.currency_id}, 类型={tx.type}, 金额={tx.amount}, 本币金额={tx.local_amount}, 时间={tx.created_at}")
        
        # 【新增】计算变动金额
        total_buy = 0
        total_sell = 0
        total_adjust = 0
        total_reversal = 0
        
        for tx in transactions:
            amount = float(tx.amount)
            if tx.type == 'buy':
                total_buy += abs(amount)
            elif tx.type == 'sell':
                total_sell += abs(amount)
            elif tx.type == 'adjust_balance':
                total_adjust += amount
            elif tx.type == 'reversal':
                total_reversal += amount
        
        # 计算净变动和当前余额
        net_change = total_buy - total_sell + total_adjust + total_reversal
        current_balance = opening_balance + net_change
        
        logger.info(f"📊 {currency_code} 余额统计: 期初={opening_balance}, 变动={net_change}, 当前={current_balance}")
        
        # 【日志】输出查询条件对比总结
        logger.info("="*80)
        logger.info(f"📋 【查询条件对比总结】币种: {currency_code}")
        logger.info(f"🔍 【汇总查询】CalGain条件: type IN ['buy', 'sell', 'adjust_balance', 'reversal', 'initial_balance']")
        logger.info(f"🔍 【明细查询】get_currency_transactions条件: type IN ['buy', 'sell', 'adjust_balance', 'reversal', 'initial_balance']")
        logger.info(f"⏰ 【时间条件】两个查询均使用: created_at >= '{start_time}' AND created_at < '{end_time}'")
        logger.info(f"📊 【明细查询结果】{currency_code} 查询到 {len(transactions)} 笔交易记录")
        logger.info("="*80)
        
        # 转换为字典格式
        transaction_list = []
        for tx in transactions:
            transaction_list.append({
                'transaction_no': tx.transaction_no,
                'type': tx.type,
                'currency_code': currency_code,  # 使用传入的currency_code
                'amount': float(tx.amount),
                'rate': float(tx.rate),
                'local_amount': float(tx.local_amount),
                'customer_name': tx.customer_name,
                'created_at': tx.created_at.isoformat(),
                'operator': tx.operator.name if tx.operator else '未知操作员'
            })
        
        return jsonify({
            'success': True,
            'data': {
                'transactions': transaction_list,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'currency_code': currency_code,
                'currency_name': currency.currency_name,
                'total_count': len(transaction_list),
                'time_range_type': 'business_cycle',  # 标识使用业务周期时间范围
                # 【新增】期初余额和统计信息
                'opening_balance': opening_balance,
                'opening_balance_source': opening_balance_source,
                'period_balance_method': 'EODBalanceVerification' if FeatureFlags.FEATURE_NEW_PERIOD_BALANCE else 'EODBalanceSnapshot',
                'balance_summary': {
                    'opening_balance': opening_balance,
                    'total_buy': total_buy,
                    'total_sell': total_sell,
                    'total_adjust': total_adjust,
                    'total_reversal': total_reversal,
                    'net_change': net_change,
                    'current_balance': current_balance
                }
            }
        })
        
    except Exception as e:
        logger.error(f"❌ 获取币种交易明细失败: {str(e)}")
        logger.error(f"异常详情: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"堆栈跟踪: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': f'获取币种交易明细失败: {str(e)}'
        }), 500
        
    finally:
        # 【修复】只有当session不为None时才关闭
        if session is not None:
            DatabaseService.close_session(session) 

def CalBaseCurrency(branch_id, start_time, end_time):
    """
    计算本币库存统计（重写版本：基于CalBalance算法分解）
    
    Args:
        branch_id: 网点ID
        start_time: 开始时间
        end_time: 结束时间
    
    Returns:
        dict: 本币库存统计数据
    """
    session = DatabaseService.get_session()
    
    try:
        # 【日志】记录CalBaseCurrency函数的调用参数
        logging.info(f"CalBaseCurrency函数被调用 - 网点ID: {branch_id}")
        logging.info(f"CalBaseCurrency查询时间范围: {start_time.strftime('%Y-%m-%d %H:%M:%S')} 到 {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 获取网点信息
        branch = session.query(Branch).options(
            joinedload(Branch.base_currency)
        ).filter_by(id=branch_id).first()
        
        if not branch:
            raise ValueError(f"网点ID {branch_id} 不存在")
        
        # 获取本币信息
        base_currency_id = get_base_currency_id_from_branch(branch_id)
        if not base_currency_id:
            raise ValueError(f"无法获取网点 {branch_id} 的本币ID")
        
        base_currency_code = branch.base_currency.currency_code if branch.base_currency else 'THB'
        
        logging.info(f"🏦 本币信息: ID={base_currency_id}, 代码={base_currency_code}")
        
        # 【核心】调用CalBalance函数获取本币的理论余额
        balance_result = CalBalance(branch_id, start_time, end_time)
        
        # 【调试】记录CalBalance返回的结果
        logging.info(f"🏦 CalBalance返回结果: {len(balance_result.get('currencies', []))} 种货币")
        for i, currency_data in enumerate(balance_result.get('currencies', [])):
            logging.info(f"🏦 货币{i+1}: {currency_data.get('currency_code')} - 期初:{currency_data.get('opening_balance')}, 当前:{currency_data.get('current_balance')}, 是否本币:{currency_data.get('is_base_currency', False)}")
        
        # 从CalBalance结果中找到本币的数据
        base_currency_balance_data = None
        for currency_data in balance_result.get('currencies', []):
            if currency_data.get('currency_code') == base_currency_code:
                base_currency_balance_data = currency_data
                logging.info(f"🏦 找到本币数据: {base_currency_code}")
                break
        
        if not base_currency_balance_data:
            logging.error(f"🏦 未找到本币数据: {base_currency_code}")
            logging.error(f"🏦 可用的货币代码: {[c.get('currency_code') for c in balance_result.get('currencies', [])]}")
            
            # 【修复】如果CalBalance中没有找到本币数据，尝试通过is_base_currency标志查找
            for currency_data in balance_result.get('currencies', []):
                if currency_data.get('is_base_currency', False):
                    base_currency_balance_data = currency_data
                    logging.info(f"🏦 通过is_base_currency标志找到本币数据: {currency_data.get('currency_code')}")
                    break
        
        if not base_currency_balance_data:
            logging.error(f"🏦 仍然未找到本币数据，将使用默认值")
            # 【修复】如果仍然找不到，创建一个默认的本币数据结构
            base_currency_balance_data = {
                'currency_code': base_currency_code,
                'opening_balance': 0,
                'current_balance': 0,
                'is_base_currency': True
            }
        
        # 从CalBalance结果中提取关键数据
        opening_balance = base_currency_balance_data.get('opening_balance', 0)
        theoretical_balance = base_currency_balance_data.get('current_balance', 0)  # 使用current_balance作为理论余额
        
        # 【核心算法】基于CalBalance的相同查询条件，分解出买入、卖出、冲正
        # 获取本币变化统计时间范围（与CalBalance保持一致）
        from config.features import FeatureFlags
        
        if FeatureFlags.FEATURE_NEW_PERIOD_BALANCE:
            # 查找上次已完成日结的余额验证记录
            prev_eod_verification = session.query(EODBalanceVerification).join(EODStatus).filter(
                EODStatus.branch_id == branch_id,
                EODStatus.status == 'completed',
                EODBalanceVerification.currency_id == base_currency_id
            ).order_by(desc(EODStatus.completed_at)).first()
            
            if prev_eod_verification:
                # 变化统计从上次日结结束时间+1秒开始
                prev_eod_status = session.query(EODStatus).filter_by(
                    id=prev_eod_verification.eod_status_id
                ).first()
                change_start = prev_eod_status.completed_at + timedelta(seconds=1) if prev_eod_status else start_time
            else:
                change_start = start_time
        else:
            # 传统方式：从快照表获取
            latest_snapshot = session.query(EODBalanceSnapshot).join(EODHistory).filter(
                EODHistory.branch_id == branch_id,
                EODBalanceSnapshot.currency_id == base_currency_id,
                EODHistory.date < start_time.date()
            ).order_by(desc(EODHistory.date)).first()
            
            if latest_snapshot:
                change_start = latest_snapshot.created_at + timedelta(seconds=1)
            else:
                change_start = start_time
        
        change_end = end_time
        
        # 【与CalBalance完全相同的查询条件】查询本币相关交易
        # 【修改】为了正确分解收入、支出、冲正，需要包含所有交易（包括被冲正的）
        # 收入金额要统计所有sell流水，支出要统计所有buy流水，冲正只统计reversal类型
        change_filter_conditions = [
            ExchangeTransaction.branch_id == branch_id,
            ExchangeTransaction.created_at >= change_start,
            ExchangeTransaction.created_at < change_end,
            ExchangeTransaction.type.in_(['buy', 'sell', 'initial_balance', 'adjust_balance', 'cash_out', 'reversal']),
            # 【重要】移除 status != 'reversed' 条件，确保收入支出统计包含所有交易
            # 冲正金额会单独统计reversal类型，不会重复计算
        ]
        
        # 【重要】排除Eod_diff类型的交易（与CalBalance保持一致）
        change_filter_conditions.append(ExchangeTransaction.type != 'Eod_diff')
        
        # 【新增】为了保持与CalBalance的一致性，需要根据特性开关决定是否排除冲正交易
        # 但是为了正确分解显示，我们需要两个查询：
        # 1. 与CalBalance一致的查询（用于验证理论余额）
        # 2. 包含所有交易的查询（用于分解显示）
        
        # 查询1：与CalBalance一致的交易（用于验证）
        balance_filter_conditions = change_filter_conditions.copy()
        if FeatureFlags.FEATURE_NEW_BUSINESS_TIME_RANGE:
            balance_filter_conditions.append(ExchangeTransaction.status != 'reversed')
        
        balance_transactions = session.query(
            ExchangeTransaction.type,
            ExchangeTransaction.local_amount,
            ExchangeTransaction.amount
        ).filter(and_(*balance_filter_conditions)).all()
        
        # 查询2：包含所有交易的查询（用于分解显示）
        change_transactions = session.query(
            ExchangeTransaction.type,
            ExchangeTransaction.local_amount,
            ExchangeTransaction.amount
        ).filter(and_(*change_filter_conditions)).all()
        
        logging.info(f"本币统计: 查询到 {len(change_transactions)} 笔变动交易 (时间范围: {change_start} 到 {change_end})")
        logging.info(f"本币验证: 查询到 {len(balance_transactions)} 笔余额验证交易")
        
        # 【改进】分解算法：严格按照交易类型分类
        # 使用包含所有交易的change_transactions进行分解显示
        income_amount = 0.0      # 收入金额（只包含sell类型）
        expense_amount = 0.0     # 支出金额（只包含buy类型）
        reversal_amount = 0.0    # 冲正金额（只包含reversal类型，带符号）
        adjust_balance_amount = 0.0  # 余额调节金额（带符号）
        initial_balance_amount = 0.0  # 期初余额金额（带符号）
        cash_out_amount = 0.0    # 交款金额（带符号）
        
        for tx in change_transactions:
            local_amount = float(tx.local_amount)
            amount = float(tx.amount)
            
            if tx.type == 'buy':
                # 买入外币：本币支出（只统计buy类型）
                expense_amount += abs(local_amount)  # 记录为正数
            elif tx.type == 'sell':
                # 卖出外币：本币收入（只统计sell类型）
                income_amount += abs(local_amount)  # 记录为正数
            elif tx.type == 'reversal':
                # 冲正交易：只包含reversal类型（带符号）
                reversal_amount += local_amount
            elif tx.type == 'adjust_balance':
                # 余额调节：单独统计（带符号）
                adjust_balance_amount += local_amount
            elif tx.type == 'initial_balance':
                # 期初余额：单独统计（带符号）
                initial_balance_amount += local_amount
            elif tx.type == 'cash_out':
                # 交款：单独统计（带符号）
                cash_out_amount += local_amount
        
        # 【验证】使用与CalBalance一致的交易计算验证余额
        verification_balance = opening_balance
        for tx in balance_transactions:
            local_amount = float(tx.local_amount)
            if tx.type in ['buy', 'sell', 'initial_balance', 'adjust_balance', 'cash_out', 'reversal']:
                verification_balance += local_amount
        
        # 【验证】确保验证余额与CalBalance的理论余额一致
        if abs(verification_balance - theoretical_balance) > 0.01:  # 允许0.01的误差
            logging.warning(f"本币余额验证不一致: 理论余额={theoretical_balance}, 验证余额={verification_balance}, 差异={verification_balance - theoretical_balance}")
        
        # 【显示】使用包含所有交易的change_transactions计算显示余额
        calculated_balance = opening_balance + income_amount - expense_amount + reversal_amount + adjust_balance_amount + initial_balance_amount + cash_out_amount
        
        # 【日志】记录本币统计详情
        logging.info(f"本币({base_currency_code})统计详情:")
        logging.info(f"  期初余额: {opening_balance}")
        logging.info(f"  收入金额: +{income_amount} (仅sell类型，包含所有sell交易)")
        logging.info(f"  支出金额: -{expense_amount} (仅buy类型，包含所有buy交易)")
        logging.info(f"  冲正金额: {reversal_amount:+.2f} (仅reversal类型)")
        logging.info(f"  余额调节: {adjust_balance_amount:+.2f}")
        logging.info(f"  期初余额调整: {initial_balance_amount:+.2f}")
        logging.info(f"  交款金额: {cash_out_amount:+.2f}")
        logging.info(f"  理论余额: {theoretical_balance} (来自CalBalance)")
        logging.info(f"  验证余额: {verification_balance} (与CalBalance一致)")
        logging.info(f"  显示余额: {calculated_balance} (包含所有交易)")
        
        return {
            'currency_code': base_currency_code,
            'currency_name': branch.base_currency.currency_name if branch.base_currency else '泰铢',
            'opening_balance': opening_balance,
            'income_amount': income_amount,        # 收入（仅sell类型，包含所有sell交易）
            'expense_amount': expense_amount,      # 支出（仅buy类型，包含所有buy交易）
            'reversal_amount': reversal_amount,    # 冲正（仅reversal类型，带符号）
            'adjust_balance_amount': adjust_balance_amount,  # 余额调节（带符号）
            'initial_balance_amount': initial_balance_amount,  # 期初余额调整（带符号）
            'cash_out_amount': cash_out_amount,    # 交款金额（带符号）
            'current_balance': theoretical_balance, # 当前余额（使用CalBalance的理论余额）
            'theoretical_balance': theoretical_balance,  # 理论余额（来自CalBalance，前端显示用）
            'verification_balance': verification_balance,  # 验证余额（与CalBalance一致）
            'display_balance': calculated_balance,  # 显示余额（包含所有交易）
            'branch_id': branch_id,
            'branch_name': branch.branch_name,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        }
        
    finally:
        DatabaseService.close_session(session)