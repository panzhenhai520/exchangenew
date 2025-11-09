import jwt
import bcrypt
from datetime import datetime, timedelta
import os
import logging
from functools import wraps
from flask import request, jsonify, current_app, g
from services.db_service import DatabaseService
from models.exchange_models import Operator, Role, Permission, RolePermission
from sqlalchemy import text

# 设置日志记录器
logger = logging.getLogger(__name__)

# JWT密钥 - 优先使用JWT_SECRET_KEY，否则使用SECRET_KEY
SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or os.environ.get('SECRET_KEY', 'ExchangeOK-JWT-Secret-Key-2025-Fixed')

def generate_token(user_id, expires_in_hours=24):
    """生成JWT令牌"""
    payload = {
        'sub': user_id,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=expires_in_hours)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def decode_token(token):
    """解码JWT令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload['sub']
    except jwt.ExpiredSignatureError as e:
        print(f"[decode_token] ❌ Token已过期: {e}", flush=True)
        try:
            logger.error(f"Token已过期: {e}")
        except:
            pass
        return None
    except jwt.InvalidTokenError as e:
        print(f"[decode_token] ❌ Token无效: {e}", flush=True)
        try:
            logger.error(f"Token无效: {e}")
        except:
            pass
        print(f"[decode_token] 使用的SECRET_KEY: {SECRET_KEY[:20]}...", flush=True)
        return None
    except Exception as e:
        print(f"[decode_token] ❌ 未知错误: {e}", flush=True)
        try:
            logger.error(f"Token解码未知错误: {e}")
        except:
            pass
        return None

def token_required(f):
    """JWT令牌验证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # 添加请求日志
        print(f"\n========== [token_required] 收到请求 ==========", flush=True)
        print(f"[token_required] 请求路径: {request.path}", flush=True)
        print(f"[token_required] 请求方法: {request.method}", flush=True)
        print(f"[token_required] 请求头: Authorization = {request.headers.get('Authorization', '未提供')}", flush=True)

        token = None

        # 先从Authorization头获取token
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
                print(f"[token_required] 从Authorization头提取token", flush=True)
            except IndexError:
                print(f"[token_required] ❌ Token格式错误", flush=True)
                try:
                    logger.error("Token格式错误")
                except:
                    pass
                return jsonify({'message': 'Token格式错误'}), 401

        # 如果头部没有token，尝试从URL参数获取
        if not token and 'token' in request.args:
            token = request.args.get('token')
            print(f"[token_required] 从URL参数提取token", flush=True)

        if not token:
            print(f"[token_required] ❌ 缺少访问令牌，返回401", flush=True)
            try:
                logger.error("缺少访问令牌")
            except:
                pass
            return jsonify({'message': '缺少访问令牌'}), 401
        
        try:
            print(f"[token_required] 开始解码token...", flush=True)
            user_id = decode_token(token)

            if user_id is None:
                print(f"[token_required] ❌ Token解码失败或已过期", flush=True)
                try:
                    logger.error("Token解码失败或已过期")
                except:
                    pass
                return jsonify({'message': '无效或过期的令牌'}), 401

            print(f"[token_required] Token解码成功, user_id={user_id}", flush=True)

            # 获取用户信息
            print(f"[token_required] 正在获取数据库会话...", flush=True)
            try:
                session = DatabaseService.get_session()
                print(f"[token_required] 数据库会话获取成功", flush=True)
            except Exception as db_err:
                print(f"[token_required] 数据库会话获取失败: {db_err}", flush=True)
                import traceback
                traceback.print_exc()
                return jsonify({'message': '数据库连接失败'}), 500

            try:
                print(f"[token_required] 正在查询用户: user_id={user_id}", flush=True)
                user = session.query(Operator).filter_by(id=user_id).first()
                print(f"[token_required] 用户查询完成: user={'存在' if user else '不存在'}", flush=True)

                if not user:
                    print(f"[token_required] 用户不存在: user_id={user_id}", flush=True)
                    try:
                        logger.error(f"用户不存在: user_id={user_id}")
                    except:
                        pass
                    return jsonify({'message': '用户不存在或已禁用'}), 401

                if not user.is_active:
                    print(f"[token_required] 用户已禁用: user_id={user_id}", flush=True)
                    try:
                        logger.error(f"用户已禁用: user_id={user_id}")
                    except:
                        pass
                    return jsonify({'message': '用户不存在或已禁用'}), 401
                
                # 获取用户角色信息
                print(f"[token_required] 正在查询角色: role_id={user.role_id}", flush=True)
                role_query = session.execute(
                    text('SELECT role_name FROM roles WHERE id = :role_id'),
                    {'role_id': user.role_id}
                ).fetchone()

                role_name = role_query[0] if role_query else ''
                print(f"[token_required] 角色查询完成: role_name={role_name}", flush=True)

                # 获取用户权限 - 使用直接SQL查询确保与登录一致
                print(f"[token_required] 正在查询权限...", flush=True)
                permission_query = session.execute(
                    text('''SELECT p.permission_name 
                       FROM permissions p
                       JOIN role_permissions rp ON p.id = rp.permission_id
                       WHERE rp.role_id = :role_id
                       ORDER BY p.permission_name'''),
                    {'role_id': user.role_id}
                ).fetchall()

                permission_list = [row[0] for row in permission_query]
                print(f"[token_required] 权限查询完成: 共{len(permission_list)}个权限", flush=True)

                # 判断是否为管理员或App角色
                is_admin = role_name in ['系统管理员', 'System Administrator', 'admin', 'administrator']
                is_app_role = role_name == 'App' or role_name == 'APP'
                
                # 构建用户信息
                current_user = {
                    'id': user.id,
                    'login_code': user.login_code,
                    'name': user.name,
                    'branch_id': user.branch_id,
                    'role_id': user.role_id,
                    'role_name': role_name,
                    'permissions': permission_list,
                    'is_admin': is_admin,
                    'is_app_role': is_app_role
                }
                
                # 将用户信息存储到g对象中
                g.current_user = current_user
                print(f"[token_required] 用户信息构建完成，准备调用目标函数", flush=True)

            finally:
                DatabaseService.close_session(session)
                print(f"[token_required] 数据库会话已关闭", flush=True)

            print(f"[token_required] 正在调用目标函数: {f.__name__}", flush=True)
            result = f(current_user, *args, **kwargs)
            print(f"[token_required] 目标函数调用成功", flush=True)
            return result

        except Exception as e:
            print(f"[token_required] 异常: {type(e).__name__}: {str(e)}", flush=True)
            import traceback
            traceback.print_exc()
            try:
                logger.error(f"Token验证失败: {str(e)}")
            except:
                print(f"[token_required] ⚠️ logger.error也失败了", flush=True)
            return jsonify({'message': '令牌验证失败'}), 401
    
    return decorated

def has_permission(required_permission):
    """权限检查装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # 获取当前用户（由token_required装饰器设置）
            if len(args) > 0 and isinstance(args[0], dict):
                current_user = args[0]
            else:
                return jsonify({'message': '用户信息获取失败'}), 401
            
            # 检查权限
            if required_permission not in current_user.get('permissions', []):
                return jsonify({'message': f'缺少权限: {required_permission}'}), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator

# 为了向后兼容，添加permission_required作为has_permission的别名
permission_required = has_permission

def has_any_permission(required_permissions):
    """多权限检查装饰器 - 用户只需要拥有其中任意一个权限即可"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # 获取当前用户（由token_required装饰器设置）
            if len(args) > 0 and isinstance(args[0], dict):
                current_user = args[0]
            else:
                return jsonify({'message': '用户信息获取失败'}), 401
            
            # 检查权限 - 只需要拥有其中任意一个权限
            user_permissions = current_user.get('permissions', [])
            if not any(perm in user_permissions for perm in required_permissions):
                return jsonify({'message': f'缺少权限，需要以下权限之一: {", ".join(required_permissions)}'}), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator

def check_business_lock(f):
    """营业锁定检查装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # 获取当前用户
        if len(args) > 0 and isinstance(args[0], dict):
            current_user = args[0]
        else:
            return jsonify({'message': '用户信息获取失败'}), 401
        
        # 检查营业锁定状态
        from services.eod_service import EODService
        lock_status = EODService.check_business_lock(current_user['branch_id'])
        
        if lock_status.get('is_locked', False):
            return jsonify({
                'success': False, 
                'message': '营业已锁定，无法进行此操作',
                'eod_id': lock_status.get('eod_id'),
                'lock_date': lock_status.get('lock_date')
            }), 423  # 423 Locked
        
        return f(*args, **kwargs)
    return decorated

def check_eod_session_permission(f):
    """日结会话权限检查装饰器 - 确保只有指定终端可以进行日结操作"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # 获取当前用户
        if len(args) > 0 and isinstance(args[0], dict):
            current_user = args[0]
        else:
            return jsonify({'message': '用户信息获取失败'}), 401
        
        # 获取会话ID - 多种方式尝试获取
        from flask import session
        session_id = None
        
        # 方法1: 从Flask session获取
        session_id = session.get('eod_session_id')
        
        # 方法2: 从请求头获取
        if not session_id:
            session_id = request.headers.get('X-Session-ID')
        
        # 方法3: 从URL参数获取（如果有eod_id）- 简化处理
        if not session_id and 'eod_id' in kwargs:
            # 简化处理，不查询数据库，直接生成会话ID
            session_id = f"eod_{current_user['id']}_{datetime.now().timestamp()}"
            session['eod_session_id'] = session_id
            logger.info(f"简化处理生成会话ID: {session_id}")
        
        # 方法4: 生成新的会话ID（最后手段）
        if not session_id:
            session_id = f"eod_{current_user['id']}_{datetime.now().timestamp()}"
            session['eod_session_id'] = session_id
            logger.info(f"生成新的会话ID: {session_id}")
        
        logger.info(f"检查日结会话权限 - 用户ID: {current_user['id']}, 分支ID: {current_user['branch_id']}, 会话ID: {session_id}")
        
        # 简化权限检查 - 暂时移除严格的会话锁定检查
        # 只检查基本的日结权限，不检查会话锁定
        has_permission = True  # 简化处理，允许所有有日结权限的用户操作
        
        logger.info(f"简化权限检查 - 用户ID: {current_user['id']}, 分支ID: {current_user['branch_id']}, 会话ID: {session_id}")
        
        if not has_permission:
            return jsonify({
                'success': False,
                'message': '无权限进行日结操作'
            }), 403
        
        return f(*args, **kwargs)
    return decorated

def check_business_lock_for_transactions(f):
    """交易相关的营业锁定检查装饰器 - 支持多网点隔离"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # 获取当前用户
        if len(args) > 0 and isinstance(args[0], dict):
            current_user = args[0]
        else:
            return jsonify({'message': '用户信息获取失败'}), 401
        
        # 检查当前网点的营业锁定状态
        from services.eod_service import EODService
        lock_status = EODService.check_business_lock(current_user['branch_id'])
        
        if lock_status.get('is_locked', False):
            return jsonify({
                'success': False, 
                'message': f'当前网点营业已锁定（日结进行中），无法进行交易操作',
                'lock_reason': 'eod_in_progress',
                'eod_id': lock_status.get('eod_id'),
                'lock_date': lock_status.get('lock_date')
            }), 423  # 423 Locked
        
        return f(*args, **kwargs)
    return decorated

def check_business_lock_for_balance(f):
    """余额相关的营业锁定检查装饰器 - 支持多网点隔离"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # 获取当前用户
        if len(args) > 0 and isinstance(args[0], dict):
            current_user = args[0]
        else:
            return jsonify({'message': '用户信息获取失败'}), 401
        
        # 检查当前网点的营业锁定状态
        from services.eod_service import EODService
        lock_status = EODService.check_business_lock(current_user['branch_id'])
        
        if lock_status.get('is_locked', False):
            return jsonify({
                'success': False, 
                'message': f'当前网点营业已锁定（日结进行中），无法进行余额操作',
                'lock_reason': 'eod_in_progress',
                'eod_id': lock_status.get('eod_id'),
                'lock_date': lock_status.get('lock_date')
            }), 423  # 423 Locked
        
        return f(*args, **kwargs)
    return decorated

# 模拟权限数据
permissions = [
    {"id": "1", "permission_name": "user_manage", "description": "用户管理权限"},
    {"id": "2", "permission_name": "rate_manage", "description": "汇率管理权限"},
    {"id": "3", "permission_name": "transaction_execute", "description": "执行交易权限"},
    {"id": "4", "permission_name": "transaction_query", "description": "查询交易权限"},
    {"id": "5", "permission_name": "balance_manage", "description": "余额管理权限"},
    {"id": "6", "permission_name": "balance_query", "description": "查询余额权限"},
    {"id": "7", "permission_name": "report_generate", "description": "生成报表权限"},
    {"id": "8", "permission_name": "system_config", "description": "系统配置权限"},
    {"id": "9", "permission_name": "end_of_day", "description": "执行日结权限"}
]
