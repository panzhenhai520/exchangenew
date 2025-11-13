from flask import Blueprint, request, jsonify
from services.auth_service import (
    generate_token,
    decode_token,
    token_required,
    has_permission
)
from models.exchange_models import Branch, Role, Permission, RolePermission, Operator
from services.db_service import DatabaseService
from datetime import datetime
from utils.multilingual_log_service import multilingual_logger
from services.unified_log_service import log_user_login, log_user_logout
from utils.language_utils import get_current_language
import logging

# Get logger instance - DO NOT call basicConfig() here
logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/branches', methods=['GET'])
def get_active_branches():
    """获取所有网点列表（用于登录选择）"""
    session = DatabaseService.get_session()
    try:
        # 使用 joinedload 预加载 base_currency 关系
        from sqlalchemy.orm import joinedload
        branches = session.query(Branch).options(
            joinedload(Branch.base_currency)
        ).all()  # 获取所有网点，不限制is_active
        
        result = [{
            'id': branch.id,
            'branch_name': branch.branch_name,
            'branch_code': branch.branch_code,
            'is_active': branch.is_active,  # 添加活跃状态
            'company_name': branch.company_name,  # 公司名称
            'institution_type': branch.institution_type if hasattr(branch, 'institution_type') else 'money_changer',  # 机构类型
            'base_currency': {
                'id': branch.base_currency.id,
                'code': branch.base_currency.currency_code,
                'name': branch.base_currency.currency_name
            } if branch.base_currency else None
        } for branch in branches]
        
        # 按活跃状态排序：活跃的在前
        result.sort(key=lambda x: (not x['is_active'], x['branch_name']))
        
        return jsonify({'success': True, 'branches': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    login_code = data.get('login_code')
    password = data.get('password')
    branch_id = data.get('branch_id') or data.get('branch')  # 兼容 branch_id 和 branch 两种字段名

    logger.debug(f"=== 登录调试信息 ===")
    logger.debug(f"接收到的数据: {data}")
    logger.debug(f"login_code: {login_code}")
    logger.debug(f"password: {password}")
    logger.debug(f"branch_id: {branch_id}")

    if not login_code or not password or not branch_id:
        logger.error(f"ERROR: Missing required info: login_code={login_code}, password={password}, branch_id={branch_id}")
        return jsonify({'success': False, 'message': '缺少必要的登录信息'}), 400

    # 模拟密码加密后的MD5值比对（实际项目中建议使用 werkzeug）
    import hashlib
    password_md5 = hashlib.md5(password.encode()).hexdigest()
    logger.debug(f"密码MD5: {password_md5}")

    session = DatabaseService.get_session()
    try:
        # 查找用户
        from sqlalchemy.orm import joinedload
        
        user = session.query(Operator).options(
            joinedload(Operator.role)
        ).filter_by(
            login_code=login_code,
            password_hash=password_md5
        ).first()

        logger.debug(f"查询用户结果: {user}")
        if user:
            logger.debug(f"找到用户: ID={user.id}, login_code={user.login_code}, is_active={user.is_active}")

        if not user:
            logger.warning(f"❌ 用户验证失败: login_code={login_code}, password_md5={password_md5}")
            # 记录登录失败日志 - 使用请求头中的语言设置
            current_language = get_current_language()
            multilingual_logger.log_system_operation(
                'login_failed',
                details=f"登录失败: 用户名={login_code}, IP={request.remote_addr}",
                ip_address=request.remote_addr,
                language=current_language
            )
            return jsonify({'success': False, 'message': '用户名或密码错误'}), 401

        if not user.is_active:
            logger.warning(f"❌ 用户已停用: {user.login_code}")
            return jsonify({'success': False, 'message': '用户已停用'}), 403

        # 获取网点信息，包括本币信息
        branch = session.query(Branch).options(
            joinedload(Branch.base_currency)
        ).filter_by(id=branch_id).first()

        if not branch:
            return jsonify({'success': False, 'message': '网点不存在'}), 404

        if not branch.is_active:
            return jsonify({'success': False, 'message': '该网点已停用'}), 403

        # 检查网点切换权限：只有系统管理员可以切换到其他网点
        if user.branch_id != branch_id:
            # 检查是否是系统管理员（role_id = 1）
            if not user.role or user.role.id != 1:
                return jsonify({
                    'success': False, 
                    'message': '只有系统管理员可以切换网点'
                }), 403
            # 更新用户的 branch_id
            user.branch_id = branch_id
            DatabaseService.commit_session(session)

        # 生成token
        token = generate_token(user.id)
        
        # 获取用户角色和权限
        role = user.role
        permissions = []
        if role:
            # 使用直接SQL查询确保权限加载可靠
            from sqlalchemy import text
            permission_query = session.execute(
                text('''SELECT p.permission_name 
                   FROM permissions p
                   JOIN role_permissions rp ON p.id = rp.permission_id
                   WHERE rp.role_id = :role_id
                   ORDER BY p.permission_name'''),
                {'role_id': role.id}
            ).fetchall()
            
            permissions = [row[0] for row in permission_query]

            logger.debug(f"[权限] 用户 {user.name} 的权限列表: {permissions}")
            logger.debug(f"[检查] 是否有transaction_execute权限: {'transaction_execute' in permissions}")

        # 构建网点本币信息
        branch_currency = None
        if branch.base_currency:
            branch_currency = {
                'id': branch.base_currency.id,
                'code': branch.base_currency.currency_code,
                'name': branch.base_currency.currency_name
            }

        # 检查App角色是否需要强制修改密码
        require_password_change = False
        if role and (role.role_name == "App" or role.role_name == "APP"):
            # 检查是否是初始密码
            import hashlib
            if user.password_hash == hashlib.md5("123456".encode()).hexdigest():
                require_password_change = True

        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        DatabaseService.commit_session(session)

        # 记录用户登录日志 - 使用统一日志服务
        try:
            current_language = get_current_language()
            log_user_login(
                operator_id=user.id,
                branch_id=branch.id,
                username=user.name,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', ''),
                language=current_language
            )
        except Exception as log_error:
            # 日志记录失败不应该影响登录流程
            logger.warning(f"用户登录日志记录失败: {log_error}")

        branch_payload = {
            'id': branch.id,
            'branch_name': branch.branch_name,
            'branch_code': branch.branch_code,
            'address': branch.address,
            'manager_name': branch.manager_name,
            'phone_number': branch.phone_number,
            'institution_type': getattr(branch, 'institution_type', None),
            'company_full_name': getattr(branch, 'company_full_name', None),
            'tax_registration_number': getattr(branch, 'tax_registration_number', None),
            'license_number': getattr(branch, 'license_number', None),
            'amlo_institution_code': getattr(branch, 'amlo_institution_code', None),
            'amlo_branch_code': getattr(branch, 'amlo_branch_code', None),
            'bot_sender_code': getattr(branch, 'bot_sender_code', None),
            'bot_branch_area_code': getattr(branch, 'bot_branch_area_code', None),
            'bot_license_number': getattr(branch, 'bot_license_number', None)
        }

        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': user.id,
                'name': user.name,
                'branch_id': branch.id,
                'branch_name': branch.branch_name,
                'branch_code': branch.branch_code,
                'role_id': user.role_id,
                'role_name': role.role_name if role else None,
            'branch_currency': branch_currency,
            'branch_currency_id': branch.base_currency.id if branch.base_currency else None,
            'company_full_name': getattr(branch, 'company_full_name', None),
            'tax_registration_number': getattr(branch, 'tax_registration_number', None),
            'license_number': getattr(branch, 'license_number', None),
            'amlo_institution_code': getattr(branch, 'amlo_institution_code', None),
            'amlo_branch_code': getattr(branch, 'amlo_branch_code', None),
                'bot_sender_code': getattr(branch, 'bot_sender_code', None),
                'bot_branch_area_code': getattr(branch, 'bot_branch_area_code', None),
                'bot_license_number': getattr(branch, 'bot_license_number', None),
                'branch': branch_payload
            },
            'permissions': permissions,
            'require_password_change': require_password_change
        })
    except Exception as e:
        DatabaseService.rollback_session(session)
        logger.error(f"Login error: {str(e)}")
        return jsonify({'success': False, 'message': '登录失败，请稍后重试'}), 500
    finally:
        DatabaseService.close_session(session)

@auth_bp.route('/refresh', methods=['POST'])
@token_required
def refresh_token(current_user):
    """刷新token"""
    try:
        # 生成新的token
        new_token = generate_token(current_user['id'])
        
        return jsonify({
            'success': True,
            'token': new_token,
            'message': 'Token刷新成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Token刷新失败: {str(e)}'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    """用户退出登录"""
    try:
        # 记录用户退出日志
        try:
            current_language = get_current_language()
            log_user_logout(
                operator_id=current_user['id'],
                branch_id=current_user.get('branch_id'),
                username=current_user.get('name', '未知用户'),
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', ''),
                language=current_language
            )
        except Exception as log_error:
            # 日志记录失败不应该影响退出流程
            logger.warning(f"用户退出日志记录失败: {log_error}")
        
        return jsonify({
            'success': True,
            'message': '退出登录成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'退出登录失败: {str(e)}'
        }), 500

@auth_bp.route('/validate-token', methods=['GET'])
@token_required
def validate_token(current_user):
    """验证token并返回用户权限信息"""
    session = None
    try:
        session = DatabaseService.get_session()

        # 从数据库重新获取用户角色和权限
        from sqlalchemy import text
        from models.exchange_models import Operator

        user = session.query(Operator).filter_by(id=current_user['id']).first()
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404

        # 获取用户权限
        role = user.role
        permissions = []
        if role:
            permission_query = session.execute(
                text('''SELECT p.permission_name
                   FROM permissions p
                   JOIN role_permissions rp ON p.id = rp.permission_id
                   WHERE rp.role_id = :role_id
                   ORDER BY p.permission_name'''),
                {'role_id': role.id}
            ).fetchall()

            permissions = [row[0] for row in permission_query]

        logger.debug(f"[Token验证] 用户 {user.name} 的权限: {permissions}")

        return jsonify({
            'success': True,
            'permissions': permissions,
            'user': {
                'id': user.id,
                'name': user.name,
                'login_code': user.login_code,
                'role_name': role.role_name if role else None,
                'branch_id': user.branch_id
            }
        })
    except Exception as e:
        logger.error(f"Token验证失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Token验证失败: {str(e)}'
        }), 500
    finally:
        if session:
            DatabaseService.close_session(session)
