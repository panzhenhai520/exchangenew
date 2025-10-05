from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta, date
from sqlalchemy import func, case, distinct, literal, text
import logging
from models.exchange_models import Branch, Currency, Permission, RolePermission, SystemLog, ExchangeTransaction, Operator, CurrencyBalance, OperatorActivityLog, Country
from services.db_service import DatabaseService
from services.auth_service import token_required, has_permission, has_any_permission
import traceback
from sqlalchemy import desc
from sqlalchemy.orm import joinedload
from utils.safe_error_handler import safe_error_response, handle_database_error, get_safe_error_message

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

system_bp = Blueprint('system', __name__, url_prefix='/api/system')

@system_bp.route('/branches', methods=['GET'], strict_slashes=False)
@token_required
def get_branches(*args, **kwargs):
    """获取所有营业网点"""
    logger.info("开始获取营业网点列表")
    
    # 从装饰器传递的参数中获取current_user
    current_user = kwargs.get('current_user') or args[0]
    logger.debug(f"当前用户信息: {current_user}")
    
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
    
    session = DatabaseService.get_session()
    try:
        # 移除 is_active 过滤，返回所有网点
        branches = session.query(Branch).all()
        logger.debug(f"查询到 {len(branches)} 个网点")
        
        result = []
        for branch in branches:
            try:
                base_currency_code = None
                if branch.base_currency_id:
                    currency = session.query(Currency).get(branch.base_currency_id)
                    if currency:
                        base_currency_code = currency.currency_code
                        logger.debug(f"网点 {branch.branch_code} 的本币: {base_currency_code}")

                result.append({
                    'id': branch.id,
                    'branch_name': branch.branch_name,
                    'branch_code': branch.branch_code,
                    'address': branch.address,
                    'manager_name': branch.manager_name,
                    'phone_number': branch.phone_number,
                    'base_currency_id': branch.base_currency_id,
                    'base_currency': base_currency_code,
                    'is_active': branch.is_active,
                    'company_full_name': branch.company_full_name,
                    'tax_registration_number': branch.tax_registration_number
                })
            except Exception as e:
                logger.error(f"处理网点 {branch.branch_code} 时出错: {str(e)}")
                logger.error(traceback.format_exc())
                continue
        
        logger.info("成功获取营业网点列表")
        return jsonify({'success': True, 'branches': result})
    except Exception as e:
        error_msg = f"获取网点列表时出错: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return safe_error_response(e, "获取网点列表失败", 500)
    finally:
        DatabaseService.close_session(session)

@system_bp.route('/branches', methods=['POST'], strict_slashes=False)
@token_required
@has_permission('system_manage')
def add_branch(*args, **kwargs):
    """添加新的营业网点"""
    current_user = kwargs.get('current_user') or args[0]
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
    data = request.json
    if not data or not all(k in data for k in ['branch_name', 'branch_code', 'base_currency_id']):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    session = DatabaseService.get_session()
    try:
        # 检查网点代码是否已存在
        existing = session.query(Branch).filter_by(branch_code=data['branch_code']).first()
        if existing:
            return safe_error_response(None, '网点代码已存在', 400)
        
        # 检查本币是否存在
        currency = session.query(Currency).filter_by(id=data['base_currency_id']).first()
        if not currency:
            return safe_error_response(None, '指定的本币不存在', 404)
        
        # 创建新网点
        branch = Branch(
            branch_name=data['branch_name'],
            branch_code=data['branch_code'],
            address=data.get('address'),
            manager_name=data.get('manager_name'),
            phone_number=data.get('phone_number'),
            base_currency_id=data['base_currency_id'],
            is_active=True
        )
        session.add(branch)
        session.commit()
        
        # 记录网点新增日志
        log = SystemLog(
            operator_id=current_user['id'],
            operation='CREATE_BRANCH',
            log_type='branch_management',
            action=f"Created branch: {branch.branch_name}",
            details=f"Branch ID: {branch.id}, Branch code: {branch.branch_code}, Base currency: {currency.currency_code}",
            ip_address=request.remote_addr
        )
        session.add(log)
        session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Branch added successfully',
            'branch': {
                'id': branch.id,
                'branch_name': branch.branch_name,
                'branch_code': branch.branch_code,
                'address': branch.address,
                'manager_name': branch.manager_name,
                'phone_number': branch.phone_number,
                'base_currency_id': branch.base_currency_id,
                'base_currency': currency.currency_code
            }
        })
    except Exception as e:
        session.rollback()
        return safe_error_response(e, "添加网点失败", 500)
    finally:
        DatabaseService.close_session(session)

@system_bp.route('/branches/<int:branch_id>', methods=['PUT'])
@token_required
@has_any_permission(['system_manage', 'branch_manage'])
def update_branch(*args, **kwargs):
    """更新营业网点信息"""
    # 从Flask路由参数中获取branch_id
    branch_id = request.view_args.get('branch_id')
    
    current_user = kwargs.get('current_user') or args[0]
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
    data = request.json
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'}), 400
    
    session = DatabaseService.get_session()
    try:
        branch = session.query(Branch).filter_by(id=branch_id).first()
        if not branch:
            return jsonify({'success': False, 'message': 'Branch not found'}), 404
        
        # 如果要更新网点代码，检查是否已存在
        if 'branch_code' in data and data['branch_code'] != branch.branch_code:
            existing = session.query(Branch).filter_by(branch_code=data['branch_code']).first()
            if existing:
                return safe_error_response(None, '网点代码已存在', 400)
        
        # 如果要更新本币，检查是否存在
        if 'base_currency_id' in data:
            currency = session.query(Currency).filter_by(id=data['base_currency_id']).first()
            if not currency:
                return safe_error_response(None, '指定的本币不存在', 404)
        
        # 更新字段
        current_app.logger.info(f"[API] 更新网点 {branch_id} - 接收到的数据: {data}")
        
        for key in ['branch_name', 'branch_code', 'address', 'manager_name', 'phone_number', 'base_currency_id']:
            if key in data:
                old_value = getattr(branch, key)
                new_value = data[key]
                current_app.logger.info(f"[API] 准备更新字段 {key}: {old_value} -> {new_value}")
                
                # 检查值是否为空字符串，转换为None
                if new_value == '':
                    new_value = None
                    current_app.logger.info(f"[API] 空字符串转换为None: {key}")
                
                setattr(branch, key, new_value)
                current_app.logger.info(f"[API] 已更新字段 {key}: {getattr(branch, key)}")
        
        current_app.logger.info(f"[API] 更新后的网点信息: manager_name={branch.manager_name}, phone_number={branch.phone_number}")
        
        # 强制刷新对象状态
        session.flush()
        current_app.logger.info(f"[API] 数据库刷新完成")
        
        # 提交事务
        session.commit()
        current_app.logger.info(f"[API] 数据库提交成功")
        
        # 记录网点修改日志
        log = SystemLog(
            operator_id=current_user['id'],
            operation='UPDATE_BRANCH',
            log_type='branch_management',
            action=f"Updated branch: {branch.branch_name}",
            details=f"Branch ID: {branch.id}, Branch code: {branch.branch_code}",
            ip_address=request.remote_addr
        )
        session.add(log)
        session.commit()
        
        # 验证更新结果
        session.refresh(branch)
        current_app.logger.info(f"[API] 验证更新结果: manager_name={branch.manager_name}, phone_number={branch.phone_number}")
        
        # 构建返回数据
        response_data = {
            'id': branch.id,
            'branch_name': branch.branch_name,
            'branch_code': branch.branch_code,
            'address': branch.address,
            'manager_name': branch.manager_name,
            'phone_number': branch.phone_number,
            'base_currency_id': branch.base_currency_id,
            'base_currency': branch.base_currency.currency_code if branch.base_currency else None
        }
        
        current_app.logger.info(f"[API] 返回数据: {response_data}")
        
        return jsonify({
            'success': True,
            'message': 'Branch updated successfully',
            'branch': response_data
        })
    except Exception as e:
        session.rollback()
        return safe_error_response(e, "更新网点失败", 500)
    finally:
        DatabaseService.close_session(session)

@system_bp.route('/branches/<int:branch_id>/check-delete', methods=['GET'])
@token_required
@has_permission('system_manage')
def check_branch_can_delete(*args, **kwargs):
    """检查网点是否可以删除"""
    branch_id = request.view_args.get('branch_id')
    current_user = kwargs.get('current_user') or args[0]
    
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
    session = DatabaseService.get_session()
    try:
        branch = session.query(Branch).filter_by(id=branch_id).first()
        if not branch:
            return safe_error_response(None, '网点不存在', 404)
        
        reasons = []
        can_delete = True
        
        # 检查是否有操作员
        operators_count = session.query(Operator).filter_by(branch_id=branch_id).count()
        if operators_count > 0:
            can_delete = False
            reasons.append(f'该网点下有 {operators_count} 个操作员')
        
        # 检查是否有交易记录
        transactions_count = session.query(ExchangeTransaction).filter_by(branch_id=branch_id).count()
        if transactions_count > 0:
            can_delete = False
            reasons.append(f'该网点有 {transactions_count} 条交易记录')
        
        # 检查是否有余额记录
        balances_count = session.query(CurrencyBalance).filter_by(branch_id=branch_id).count()
        if balances_count > 0:
            can_delete = False
            reasons.append(f'该网点有 {balances_count} 条余额记录')
        
        # 检查是否有系统日志
        logs_count = session.query(SystemLog).join(Operator).filter(Operator.branch_id == branch_id).count()
        if logs_count > 0:
            can_delete = False
            reasons.append(f'该网点相关操作员有 {logs_count} 条系统日志')
        
        return jsonify({
            'success': True,
            'can_delete': can_delete,
            'reasons': reasons,
            'branch_name': branch.branch_name
        })
        
    except Exception as e:
        return safe_error_response(e, "检查网点数据失败", 500)
    finally:
        DatabaseService.close_session(session)

@system_bp.route('/branches/<int:branch_id>', methods=['DELETE'])
@token_required
@has_permission('system_manage')
def delete_branch(*args, **kwargs):
    """删除营业网点"""
    branch_id = request.view_args.get('branch_id')
    current_user = kwargs.get('current_user') or args[0]
    
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
    session = DatabaseService.get_session()
    try:
        branch = session.query(Branch).filter_by(id=branch_id).first()
        if not branch:
            return jsonify({'success': False, 'message': '网点不存在'}), 404
        
        # 再次检查是否可以删除（双重保险）
        reasons = []
        
        # 检查是否有操作员
        operators_count = session.query(Operator).filter_by(branch_id=branch_id).count()
        if operators_count > 0:
            reasons.append(f'该网点下有 {operators_count} 个操作员')
        
        # 检查是否有交易记录
        transactions_count = session.query(ExchangeTransaction).filter_by(branch_id=branch_id).count()
        if transactions_count > 0:
            reasons.append(f'该网点有 {transactions_count} 条交易记录')
        
        # 检查是否有余额记录
        balances_count = session.query(CurrencyBalance).filter_by(branch_id=branch_id).count()
        if balances_count > 0:
            reasons.append(f'该网点有 {balances_count} 条余额记录')
        
        if reasons:
            return jsonify({
                'success': False, 
                'message': f'无法删除网点 "{branch.branch_name}"，原因：' + '；'.join(reasons)
            }), 400
        
        # 记录删除操作
        log = SystemLog(
            operator_id=current_user['id'],
            operation='DELETE_BRANCH',
            log_type='branch_management',
            action=f"Deleted branch: {branch.branch_name}",
            details=f"Branch ID: {branch.id}, Branch code: {branch.branch_code}",
            ip_address=request.remote_addr
        )
        session.add(log)
        
        # 执行删除
        session.delete(branch)
        session.commit()
        
        return jsonify({
            'success': True,
            'message': f'网点 "{branch.branch_name}" 删除成功'
        })
        
    except Exception as e:
        session.rollback()
        return safe_error_response(e, "删除网点失败", 500)
    finally:
        DatabaseService.close_session(session)

@system_bp.route('/currencies', methods=['GET'])
@token_required
@has_permission('system_manage')
def get_currencies(*args, **kwargs):
    """获取所有币种（用于系统管理）"""
    current_user = kwargs.get('current_user') or args[0]
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
    session = DatabaseService.get_session()
    try:
        currencies = session.query(Currency).all()
        result = [{
            'id': currency.id,
            'currency_code': currency.currency_code,
            'currency_name': currency.currency_name,
            'country': currency.country,
            'flag_code': currency.flag_code,
            'symbol': currency.symbol
        } for currency in currencies]
        return jsonify({'success': True, 'currencies': result})
    except Exception as e:
        return safe_error_response(e, "获取币种列表失败", 500)
    finally:
        DatabaseService.close_session(session)

@system_bp.route('/logs', methods=['GET'], strict_slashes=False)
@token_required
@has_any_permission(['end_of_day', 'system_manage'])
def get_system_logs(*args, **kwargs):
    """获取系统日志"""
    # 从装饰器传递的参数中获取current_user
    current_user = kwargs.get('current_user') or args[0]
    
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
    
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    log_type = request.args.get('log_type')
    operator_name = request.args.get('operator_name')
    
    # 添加调试信息
    logger.info(f"系统日志查询参数: page={page}, per_page={per_page}, start_date={start_date}, end_date={end_date}, log_type={log_type}, operator_name={operator_name}")
    
    session = DatabaseService.get_session()
    try:
        # 添加调试信息
        logger.info(f"系统日志查询参数: page={page}, per_page={per_page}, start_date={start_date}, end_date={end_date}, log_type={log_type}, operator_name={operator_name}")
        
        # 检查数据库中是否有系统日志数据
        total_logs = session.query(SystemLog).count()
        logger.info(f"数据库中总共有 {total_logs} 条系统日志记录")
        
        # 检查数据库中的日志类型分布
        log_types = session.query(SystemLog.operation).distinct().all()
        logger.info(f"数据库中的日志类型: {[lt[0] for lt in log_types]}")
        
        if total_logs == 0:
            logger.warning("数据库中没有系统日志记录")
            return jsonify({
                'success': True,
                'logs': [],
                'total': 0,
                'page': page,
                'per_page': per_page
            })
        
        # 日志类型映射 - 将前端类型映射到实际的数据库字段
        log_type_mapping = {
            'login': 'login',
            'logout': 'logout',
            'user_login': 'login',
            'user_logout': 'logout',
            'exchange': 'exchange',
            'rate': 'rate_update',
            'rate_update': 'rate_update',
            'balance': 'balance_adjustment',
            'balance_adjustment': 'balance_adjustment',
            'end_of_day': 'eod_operation',
            'branch_management': 'branch',
            'system': 'system',
            'system_manage': 'system'
        }
        
        # 查询系统日志 - 使用原生SQL避免标签问题
        
        # 构建基础SQL
        base_sql = """
        SELECT 
            sl.id,
            sl.operator_id,
            sl.operation,
            sl.action,
            sl.details,
            sl.ip_address,
            sl.created_at,
            o.name as operator_name
        FROM system_logs sl
        JOIN operators o ON sl.operator_id = o.id
        """
        
        # 构建WHERE条件
        where_conditions = []
        params = {}
        
        if start_date:
            where_conditions.append("sl.created_at >= :start_date")
            params['start_date'] = datetime.strptime(start_date, '%Y-%m-%d')
        
        if end_date:
            where_conditions.append("sl.created_at <= :end_date")
            params['end_date'] = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        
        if log_type and log_type != 'all':
            if log_type in log_type_mapping:
                db_log_type = log_type_mapping[log_type]
                if log_type == 'system_manage':
                    where_conditions.append("sl.operation IN ('user_management', 'role_configuration', 'branch_management', 'system_configuration')")
                elif log_type == 'branch_management':
                    where_conditions.append("sl.operation IN ('CREATE_BRANCH', 'UPDATE_BRANCH', 'DELETE_BRANCH')")
                else:
                    where_conditions.append("sl.operation = :log_type")
                    params['log_type'] = db_log_type
        
        if operator_name:
            where_conditions.append("o.name LIKE :operator_name")
            params['operator_name'] = f'%{operator_name}%'
        
        # 组合SQL
        if where_conditions:
            base_sql += " WHERE " + " AND ".join(where_conditions)
        
        # 添加排序和分页
        base_sql += " ORDER BY sl.created_at DESC LIMIT :limit OFFSET :offset"
        params['limit'] = per_page
        params['offset'] = (page - 1) * per_page
        
        # 执行查询
        result = session.execute(text(base_sql), params)
        logs = result.fetchall()
        
        # 获取总记录数
        count_sql = """
        SELECT COUNT(*) as total
        FROM system_logs sl
        JOIN operators o ON sl.operator_id = o.id
        """
        if where_conditions:
            count_sql += " WHERE " + " AND ".join(where_conditions)
        
        # 移除分页参数
        count_params = {k: v for k, v in params.items() if k not in ['limit', 'offset']}
        total_result = session.execute(text(count_sql), count_params)
        total = total_result.scalar()
        
        # 格式化结果
        result = []
        for log in logs:
            # 确定日志类型显示名称
            display_log_type = log.operation
            if log.operation == 'eod_operation':
                    display_log_type = 'end_of_day'
            elif log.operation in ['user_management', 'role_configuration', 'branch_management', 'system_configuration']:
                    display_log_type = 'system_manage'
            elif log.operation in ['CREATE_BRANCH', 'UPDATE_BRANCH', 'DELETE_BRANCH']:
                    display_log_type = 'branch_management'
            
            result.append({
                'id': log.id,
                'operator_id': log.operator_id,
                'operator_name': log.operator_name,
                'operation': display_log_type,
                'log_type': display_log_type,
                'action': log.action,
                'details': log.details,
                'ip_address': log.ip_address,
                'created_at': log.created_at.isoformat(),
                'source_table': 'system_log'
            })
        
        return jsonify({
            'success': True,
            'logs': result,
            'total': total,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        logger.error(f"获取系统日志失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@system_bp.route('/statistics/daily', methods=['GET'])
@token_required
@has_permission('system_statistics_view')
def get_daily_statistics(*args, **kwargs):
    """获取每日统计数据"""
    # 从装饰器传递的参数中获取current_user
    current_user = kwargs.get('current_user') or args[0]
    
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
    
    session = DatabaseService.get_session()
    try:
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        # 获取今日交易统计
        today_stats = session.query(
            func.count().label('total_transactions'),
            func.sum(ExchangeTransaction.local_amount).label('total_amount')
        ).filter(
            ExchangeTransaction.transaction_date == today
        ).first()
        
        # 获取昨日交易统计
        yesterday_stats = session.query(
            func.count().label('total_transactions'),
            func.sum(ExchangeTransaction.local_amount).label('total_amount')
        ).filter(
            ExchangeTransaction.transaction_date == yesterday
        ).first()
        
        # 获取活跃用户数
        active_users = session.query(func.count(distinct(Operator.id))).filter(
            Operator.last_login >= today
        ).scalar()
        
        # 获取活跃网点数
        active_branches = session.query(func.count(distinct(Branch.id))).filter(
            Branch.is_active == True
        ).scalar()
        
        return jsonify({
            'success': True,
            'statistics': {
                'today': {
                    'total_transactions': today_stats.total_transactions or 0,
                    'total_amount': float(today_stats.total_amount or 0),
                    'active_users': active_users,
                    'active_branches': active_branches
                },
                'yesterday': {
                    'total_transactions': yesterday_stats.total_transactions or 0,
                    'total_amount': float(yesterday_stats.total_amount or 0)
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@system_bp.route('/statistics/monthly', methods=['GET'])
@token_required
@has_permission('system_statistics_view')
def get_monthly_statistics(*args, **kwargs):
    """获取月度统计数据"""
    # 从装饰器传递的参数中获取current_user
    current_user = kwargs.get('current_user') or args[0]
    
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
    
    session = DatabaseService.get_session()
    try:
        today = datetime.now().date()
        first_day = today.replace(day=1)
        last_month = (first_day - timedelta(days=1)).replace(day=1)
        
        # 获取本月交易统计
        this_month_stats = session.query(
            func.count().label('total_transactions'),
            func.sum(ExchangeTransaction.local_amount).label('total_amount')
        ).filter(
            ExchangeTransaction.transaction_date >= first_day
        ).first()
        
        # 获取上月交易统计
        last_month_stats = session.query(
            func.count().label('total_transactions'),
            func.sum(ExchangeTransaction.local_amount).label('total_amount')
        ).filter(
            ExchangeTransaction.transaction_date >= last_month,
            ExchangeTransaction.transaction_date < first_day
        ).first()
        
        # 获取本月活跃用户数
        active_users = session.query(func.count(distinct(Operator.id))).filter(
            Operator.last_login >= first_day
        ).scalar()
        
        # 获取本月活跃网点数
        active_branches = session.query(func.count(distinct(Branch.id))).filter(
            Branch.is_active == True
        ).scalar()
        
        return jsonify({
            'success': True,
            'statistics': {
                'this_month': {
                    'total_transactions': this_month_stats.total_transactions or 0,
                    'total_amount': float(this_month_stats.total_amount or 0),
                    'active_users': active_users,
                    'active_branches': active_branches
                },
                'last_month': {
                    'total_transactions': last_month_stats.total_transactions or 0,
                    'total_amount': float(last_month_stats.total_amount or 0)
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@system_bp.route('/statistics/yearly', methods=['GET'])
@token_required
@has_permission('system_statistics_view')
def get_yearly_statistics(*args, **kwargs):
    """获取年度统计数据"""
    # 从装饰器传递的参数中获取current_user
    current_user = kwargs.get('current_user') or args[0]
    
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
    
    session = DatabaseService.get_session()
    try:
        today = datetime.now().date()
        first_day = today.replace(month=1, day=1)
        last_year = first_day.replace(year=first_day.year-1)
        
        # 获取本年交易统计
        this_year_stats = session.query(
            func.count().label('total_transactions'),
            func.sum(ExchangeTransaction.local_amount).label('total_amount')
        ).filter(
            ExchangeTransaction.transaction_date >= first_day
        ).first()
        
        # 获取去年交易统计
        last_year_stats = session.query(
            func.count().label('total_transactions'),
            func.sum(ExchangeTransaction.local_amount).label('total_amount')
        ).filter(
            ExchangeTransaction.transaction_date >= last_year,
            ExchangeTransaction.transaction_date < first_day
        ).first()
        
        # 获取本年活跃用户数
        active_users = session.query(func.count(distinct(Operator.id))).filter(
            Operator.last_login >= first_day
        ).scalar()
        
        # 获取本年活跃网点数
        active_branches = session.query(func.count(distinct(Branch.id))).filter(
            Branch.is_active == True
        ).scalar()
        
        return jsonify({
            'success': True,
            'statistics': {
                'this_year': {
                    'total_transactions': this_year_stats.total_transactions or 0,
                    'total_amount': float(this_year_stats.total_amount or 0),
                    'active_users': active_users,
                    'active_branches': active_branches
                },
                'last_year': {
                    'total_transactions': last_year_stats.total_transactions or 0,
                    'total_amount': float(last_year_stats.total_amount or 0)
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@system_bp.route('/branches/current', methods=['GET'])
@token_required
def get_current_branch(*args, **kwargs):
    """获取当前用户的网点信息"""
    current_user = kwargs.get('current_user') or args[0]
    
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
    
    session = DatabaseService.get_session()
    try:
        # 获取网点信息，包括本币信息
        branch = session.query(Branch).options(
            joinedload(Branch.base_currency)
        ).filter_by(id=current_user.get('branch_id')).first()
        
        if not branch:
            return jsonify({'success': False, 'message': '网点不存在'}), 404
        
        return jsonify({
            'success': True,
            'branch': {
                'id': branch.id,
                'name': branch.branch_name,
                'code': branch.branch_code,
                'base_currency_id': branch.base_currency_id,
                'base_currency': {
                    'id': branch.base_currency.id,
                    'code': branch.base_currency.currency_code,
                    'name': branch.base_currency.currency_name,
                    'flag_code': branch.base_currency.flag_code
                } if branch.base_currency else None
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

# 新增：根据币种代码获取币种信息
@system_bp.route('/currencies/by-code/<currency_code>', methods=['GET'])
@token_required
def get_currency_by_code(currency_code):
    """根据币种代码获取币种信息"""
    try:
        db_service = DatabaseService()
        session = db_service.get_session()
        
        # 查询币种信息
        currency = session.query(Currency).filter_by(currency_code=currency_code).first()
        
        if currency:
            return jsonify({
                'success': True,
                'currency': {
                    'id': currency.id,
                    'currency_code': currency.currency_code,
                    'currency_name': currency.currency_name,
                    'is_active': currency.is_active
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': f'未找到币种代码为 {currency_code} 的币种'
            }), 404
            
    except Exception as e:
        logger.error(f"获取币种信息失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '获取币种信息失败'
        }), 500
    finally:
        if 'session' in locals():
            db_service.close_session(session) 

@system_bp.route('/currency-translations', methods=['GET'])
@token_required
@has_permission('view_system')
def get_currency_translations(current_user):
    """
    获取币种翻译配置 - 供前端动态加载使用
    """
    try:
        from services.currency_translation_service import CurrencyTranslationService
        
        # 重新加载配置以确保最新数据
        translations = CurrencyTranslationService.reload_config()
        
        if translations:
            return jsonify({
                'success': True,
                'translations': translations,
                'count': len(translations)
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '无法加载币种翻译配置'
            }), 500
            
    except Exception as e:
        logger.error(f'获取币种翻译失败: {e}')
        return jsonify({
            'success': False,
            'message': f'获取币种翻译失败: {str(e)}'
        }), 500

@system_bp.route('/currency-translations', methods=['POST'])
@token_required
@has_permission('manage_system')
def add_currency_translation(current_user):
    """
    添加币种翻译配置
    """
    try:
        data = request.get_json()
        currency_code = data.get('currency_code')
        translations = data.get('translations')
        
        if not currency_code or not translations:
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            }), 400
        
        from services.currency_translation_service import CurrencyTranslationService
        
        success = CurrencyTranslationService.add_translation(currency_code, translations)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'成功添加币种翻译: {currency_code}'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '添加币种翻译失败'
            }), 500
            
    except Exception as e:
        logger.error(f'添加币种翻译失败: {e}')
        return jsonify({
            'success': False,
            'message': f'添加币种翻译失败: {str(e)}'
        }), 500

@system_bp.route('/countries', methods=['GET'])
@token_required
def get_countries(*args, **kwargs):
    """
    获取国家列表
    支持参数:
    - language: zh/en/th (返回指定语言的国家名称)
    - search: 搜索关键词 (按国家名称或代码搜索)
    - active_only: true/false (只返回启用的国家)
    """
    current_user = kwargs.get('current_user') or args[0]
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401

    # 获取查询参数
    language = request.args.get('language', 'zh')  # 默认中文
    search = request.args.get('search', '').strip()
    active_only = request.args.get('active_only', 'true').lower() == 'true'

    session = DatabaseService.get_session()
    try:
        # 构建查询
        query = session.query(Country)

        # 过滤条件：只返回启用的国家
        if active_only:
            query = query.filter(Country.is_active == True)

        # 搜索条件：支持按国家代码或名称搜索
        if search:
            search_pattern = f'%{search}%'
            query = query.filter(
                (Country.country_code.like(search_pattern)) |
                (Country.country_name_zh.like(search_pattern)) |
                (Country.country_name_en.like(search_pattern)) |
                (Country.country_name_th.like(search_pattern))
            )

        # 按排序顺序排序
        query = query.order_by(Country.sort_order)

        countries = query.all()

        # 根据语言参数返回对应的国家名称
        result = []
        for country in countries:
            country_data = {
                'id': country.id,
                'country_code': country.country_code,
                'phone_code': country.phone_code,
                'currency_code': country.currency_code,
                'is_active': country.is_active,
                'sort_order': country.sort_order
            }

            # 根据语言参数添加对应的国家名称字段
            if language == 'en':
                country_data['country_name'] = country.country_name_en
            elif language == 'th':
                country_data['country_name'] = country.country_name_th or country.country_name_en
            else:  # 默认中文
                country_data['country_name'] = country.country_name_zh

            # 同时返回所有语言版本（可选）
            country_data['country_name_zh'] = country.country_name_zh
            country_data['country_name_en'] = country.country_name_en
            country_data['country_name_th'] = country.country_name_th

            result.append(country_data)

        logger.info(f"成功获取国家列表，共 {len(result)} 个国家，语言: {language}")
        return jsonify({
            'success': True,
            'countries': result,
            'total': len(result),
            'language': language
        })

    except Exception as e:
        logger.error(f"获取国家列表失败: {str(e)}")
        logger.error(traceback.format_exc())
        return safe_error_response(e, "获取国家列表失败", 500)
    finally:
        DatabaseService.close_session(session)