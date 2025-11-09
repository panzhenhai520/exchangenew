# 完全替代基于 sqlite3 的旧逻辑，采用 SQLAlchemy ORM 重写

from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from services.db_service import DatabaseService
from services.auth_service import token_required, has_permission
from services.log_service import record_system_log
from services.activity_service import ActivityService
from services.unified_log_service import log_user_management
from models.exchange_models import Operator, Branch, Role, Permission, RolePermission, PermissionTranslation
from sqlalchemy.orm import joinedload
from datetime import datetime
import hashlib
import re
from utils.language_utils import get_current_language

user_bp = Blueprint('user', __name__, url_prefix='/api/users')
perm_bp = Blueprint('permission', __name__, url_prefix='/api/permissions')

# 数据验证函数
def validate_email(email):
    """验证邮箱格式"""
    if not email:
        return True  # 邮箱是可选的
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """验证电话号码格式"""
    if not phone:
        return True  # 电话是可选的
    # 支持中国大陆、香港、台湾、泰国等地区的电话号码格式
    pattern = r'^[\+]?[0-9\-\s\(\)]{7,20}$'
    return re.match(pattern, phone) is not None

def validate_id_card(id_card):
    """验证身份证号码格式"""
    if not id_card:
        return True  # 身份证是可选的
    # 支持中国身份证、护照等格式
    pattern = r'^[A-Za-z0-9]{6,20}$'
    return re.match(pattern, id_card) is not None

# ----------------------------- 用户接口 -----------------------------

@user_bp.route('/', methods=['GET'])
@token_required
@has_permission('user_manage')
def get_users(current_user):
    """获取用户列表"""
    session = DatabaseService.get_session()
    try:
        print("开始获取用户列表...")
        
        # 简化查询，不使用 joinedload，只获取活跃用户
        users = session.query(Operator).filter_by(is_active=True).all()
        print(f"查询到 {len(users)} 个活跃用户")
        
        result = []
        for user in users:
            try:
                # 安全地获取关联数据
                role_name = None
                branch_name = None
                
                if user.role_id:
                    role = session.query(Role).filter_by(id=user.role_id).first()
                    role_name = role.role_name if role else None
                
                if user.branch_id:
                    branch = session.query(Branch).filter_by(id=user.branch_id).first()
                    branch_name = branch.branch_name if branch else None
                
                user_data = {
                'id': user.id,
                'login_code': user.login_code,
                'name': user.name,
                'role_id': user.role_id,
                    'role_name': role_name,
                'branch_id': user.branch_id,
                    'branch_name': branch_name,
                'is_active': user.is_active,
                    'status': getattr(user, 'status', 'active'),
                'last_login': user.last_login.isoformat() if user.last_login else None,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    # 新增字段（安全获取）
                    'id_card_number': getattr(user, 'id_card_number', None),
                    'phone_number': getattr(user, 'phone_number', None),
                    'mobile_number': getattr(user, 'mobile_number', None),
                    'address': getattr(user, 'address', None),
                    'email': getattr(user, 'email', None)
                }
                result.append(user_data)
                print(f"处理用户: {user.login_code}")
            except Exception as user_error:
                print(f"处理用户 {user.login_code} 时出错: {str(user_error)}")
                continue
        
        print(f"成功处理 {len(result)} 个用户")
        return jsonify({'success': True, 'users': result})
    except Exception as e:
        print(f"获取用户列表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@user_bp.route('/<int:user_id>', methods=['GET'])
@token_required
@has_permission('user_manage')
def get_user(current_user, user_id):
    """获取单个用户信息"""
    session = DatabaseService.get_session()
    try:
        # 安全地记录活动
        try:
            current_user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
            current_user_branch_id = current_user.branch_id if hasattr(current_user, 'branch_id') else current_user.get('branch_id')
            
            if current_user_id:
                ActivityService.log_activity(
                    current_user_id, 
                    'action', 
                    f'View user details: {user_id}',
                    request.remote_addr,
                    request.headers.get('User-Agent'),
                    branch_id=current_user_branch_id
                )
        except Exception as log_error:
            print(f"记录活动日志失败: {str(log_error)}")
            # 继续执行，不影响用户查询
        
        # 使用 joinedload 预加载关联数据
        user = session.query(Operator).options(
            joinedload(Operator.role),
            joinedload(Operator.branch)
        ).filter_by(id=user_id).first()
        
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        result = {
            'id': user.id,
            'login_code': user.login_code,
            'name': user.name,
            'role_id': user.role_id,
            'role_name': user.role.role_name if user.role else None,
            'branch_id': user.branch_id,
            'branch_name': user.branch.branch_name if user.branch else None,
            'is_active': user.is_active,
            'status': user.status,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            # 新增字段
            'id_card_number': user.id_card_number,
            'phone_number': user.phone_number,
            'mobile_number': user.mobile_number,
            'address': user.address,
            'email': user.email
        }
        
        return jsonify({'success': True, 'user': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@user_bp.route('/', methods=['POST'])
@token_required
@has_permission('user_manage')
def create_user(current_user):
    """创建新用户"""
    data = request.json
    
    # 验证必填字段
    required_fields = ['login_code', 'name', 'password', 'role_id', 'branch_id']
    if not data or not all(field in data for field in required_fields):
        return jsonify({'success': False, 'message': '缺少必要的用户信息'}), 400
    
    # 数据验证
    if data.get('email') and not validate_email(data['email']):
        return jsonify({'success': False, 'message': '邮箱格式不正确'}), 400
    
    if data.get('phone_number') and not validate_phone(data['phone_number']):
        return jsonify({'success': False, 'message': '电话号码格式不正确'}), 400
    
    if data.get('mobile_number') and not validate_phone(data['mobile_number']):
        return jsonify({'success': False, 'message': '手机号码格式不正确'}), 400
    
    if data.get('id_card_number') and not validate_id_card(data['id_card_number']):
        return jsonify({'success': False, 'message': '身份证号码格式不正确'}), 400
    
    session = DatabaseService.get_session()
    try:
        # 检查同一网点内登录代码是否已存在
        existing_user = session.query(Operator).filter_by(
            login_code=data['login_code'], 
            branch_id=data['branch_id']
        ).first()
        if existing_user:
            return jsonify({'success': False, 'message': '该网点内登录代码已存在'}), 400
        
        # 检查角色是否存在
        role = session.query(Role).filter_by(id=data['role_id']).first()
        if not role:
            return jsonify({'success': False, 'message': '角色不存在'}), 400
        
        # 检查网点是否存在
        branch = session.query(Branch).filter_by(id=data['branch_id']).first()
        if not branch:
            return jsonify({'success': False, 'message': '网点不存在'}), 400
        
        # 创建新用户
        password_hash = hashlib.md5(data['password'].encode()).hexdigest()
        new_user = Operator(
            login_code=data['login_code'],
            name=data['name'],
            password_hash=password_hash,
            role_id=data['role_id'],
            branch_id=data['branch_id'],
            is_active=True,
            status=data.get('status', 'active'),
            created_at=datetime.utcnow(),
            # 新增字段
            id_card_number=data.get('id_card_number'),
            phone_number=data.get('phone_number'),
            mobile_number=data.get('mobile_number'),
            address=data.get('address'),
            email=data.get('email')
        )
        
        session.add(new_user)
        DatabaseService.commit_session(session)
        
        # 安全地获取current_user的属性
        try:
            current_user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
            current_user_branch_id = current_user.branch_id if hasattr(current_user, 'branch_id') else current_user.get('branch_id')
            
            # 记录活动和系统日志
            if current_user_id:
                ActivityService.log_activity(
                    current_user_id, 
                    'action', 
                    f'Created user: {new_user.login_code}',
                    request.remote_addr,
                    request.headers.get('User-Agent'),
                    branch_id=current_user_branch_id
                )
                
                # 使用统一日志服务记录系统日志
                from services.unified_log_service import log_user_management
                from utils.language_utils import get_current_language
                
                current_language = get_current_language()
                log_user_management(
                    operator_id=current_user_id,
                    branch_id=current_user_branch_id,
                    action_type='create',
                    target_user=f"{new_user.login_code} ({new_user.name})",
                    ip_address=request.remote_addr,
                    language=current_language
                )
        except Exception as log_error:
            print(f"记录日志失败: {str(log_error)}")
            # 继续执行，不影响用户创建
        

        
        return jsonify({
            'success': True,
            'message': '用户创建成功',
            'user': {
                'id': new_user.id,
                'login_code': new_user.login_code,
                'name': new_user.name,
                'role_id': new_user.role_id,
                'branch_id': new_user.branch_id,
                'is_active': new_user.is_active,
                'status': new_user.status,
                'created_at': new_user.created_at.isoformat()
            }
        })
    except Exception as e:
        DatabaseService.rollback_session(session)
        print(f"创建用户失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@user_bp.route('/<int:user_id>', methods=['PUT'])
@token_required
@has_permission('user_manage')
def update_user(current_user, user_id):
    """更新用户信息"""
    data = request.json
    
    if not data:
        return jsonify({'success': False, 'message': '没有提供更新数据'}), 400
    
    # 数据验证
    if data.get('email') and not validate_email(data['email']):
        return jsonify({'success': False, 'message': '邮箱格式不正确'}), 400
    
    if data.get('phone_number') and not validate_phone(data['phone_number']):
        return jsonify({'success': False, 'message': '电话号码格式不正确'}), 400
    
    if data.get('mobile_number') and not validate_phone(data['mobile_number']):
        return jsonify({'success': False, 'message': '手机号码格式不正确'}), 400
    
    if data.get('id_card_number') and not validate_id_card(data['id_card_number']):
        return jsonify({'success': False, 'message': '身份证号码格式不正确'}), 400
    
    session = DatabaseService.get_session()
    try:
        user = session.query(Operator).filter_by(id=user_id).first()
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        # 更新基本信息
        if 'name' in data:
            user.name = data['name']
        
        if 'role_id' in data:
            # 检查角色是否存在
            role = session.query(Role).filter_by(id=data['role_id']).first()
            if not role:
                return jsonify({'success': False, 'message': '角色不存在'}), 400
            user.role_id = data['role_id']
        
        if 'branch_id' in data:
            # 检查网点是否存在
            branch = session.query(Branch).filter_by(id=data['branch_id']).first()
            if not branch:
                return jsonify({'success': False, 'message': '网点不存在'}), 400
            user.branch_id = data['branch_id']
        
        if 'is_active' in data:
            user.is_active = data['is_active']
        
        if 'status' in data:
            user.status = data['status']
        
        if 'password' in data:
            # 更新密码
            user.password_hash = hashlib.md5(data['password'].encode()).hexdigest()
        
        # 更新新增字段
        if 'id_card_number' in data:
            user.id_card_number = data['id_card_number']
        
        if 'phone_number' in data:
            user.phone_number = data['phone_number']
        
        if 'mobile_number' in data:
            user.mobile_number = data['mobile_number']
        
        if 'address' in data:
            user.address = data['address']
        
        if 'email' in data:
            user.email = data['email']
        
        DatabaseService.commit_session(session)
        
        # 安全地获取current_user的属性并记录活动和系统日志
        try:
            current_user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
            current_user_branch_id = current_user.branch_id if hasattr(current_user, 'branch_id') else current_user.get('branch_id')
            
            if current_user_id:
                ActivityService.log_activity(
                    current_user_id, 
                    'action', 
                    f'Updated user: {user_id}',
                    request.remote_addr,
                    request.headers.get('User-Agent'),
                    branch_id=current_user_branch_id
                )
                
                # 使用统一日志服务记录系统日志
                from services.unified_log_service import log_user_management
                from utils.language_utils import get_current_language
                
                current_language = get_current_language()
                log_user_management(
                    operator_id=current_user_id,
                    branch_id=current_user_branch_id,
                    action_type='update',
                    target_user=f"{user.login_code} ({user.name})",
                    ip_address=request.remote_addr,
                    language=current_language
                )
        except Exception as log_error:
            print(f"记录日志失败: {str(log_error)}")
            # 继续执行，不影响用户更新
        
        return jsonify({
            'success': True,
            'message': '用户信息更新成功',
            'user': {
                'id': user.id,
                'login_code': user.login_code,
                'name': user.name,
                'role_id': user.role_id,
                'branch_id': user.branch_id,
                'is_active': user.is_active,
                'status': user.status,
                'id_card_number': user.id_card_number,
                'phone_number': user.phone_number,
                'mobile_number': user.mobile_number,
                'address': user.address,
                'email': user.email
            }
        })
    except Exception as e:
        DatabaseService.rollback_session(session)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@user_bp.route('/<int:user_id>', methods=['DELETE'])
@token_required
@has_permission('user_manage')
def delete_user(current_user, user_id):
    session = DatabaseService.get_session()
    try:
        user = session.query(Operator).get(user_id)
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # 检查用户是否有业务流水
        from models.exchange_models import ExchangeTransaction
        
        # 检查兑换业务
        exchange_count = session.query(ExchangeTransaction).filter_by(
            operator_id=user_id,
            type='buy'
        ).count()
        exchange_count += session.query(ExchangeTransaction).filter_by(
            operator_id=user_id,
            type='sell'
        ).count()
        
        # 检查冲正业务
        reversal_count = session.query(ExchangeTransaction).filter_by(
            operator_id=user_id,
            type='reversal'
        ).count()
        
        # 检查余额调节业务
        balance_adjust_count = session.query(ExchangeTransaction).filter_by(
            operator_id=user_id,
            type='adjust_balance'
        ).count()
        
        # 检查余额初始化业务
        initial_balance_count = session.query(ExchangeTransaction).filter_by(
            operator_id=user_id,
            type='initial_balance'
        ).count()
        
        # 如果有任何业务流水，不允许删除，只能停用
        total_business_count = exchange_count + reversal_count + balance_adjust_count + initial_balance_count
        
        if total_business_count > 0:
            business_details = []
            if exchange_count > 0:
                business_details.append(f"兑换业务: {exchange_count}笔")
            if reversal_count > 0:
                business_details.append(f"冲正业务: {reversal_count}笔")
            if balance_adjust_count > 0:
                business_details.append(f"余额调节: {balance_adjust_count}笔")
            if initial_balance_count > 0:
                business_details.append(f"余额初始化: {initial_balance_count}笔")
            
            return jsonify({
                'success': False, 
                'message': f'该用户有业务流水记录，不能删除。业务详情: {", ".join(business_details)}。建议停用该用户。',
                'business_count': total_business_count,
                'business_details': business_details
            }), 400
        
        # 没有业务流水，可以删除
        user.is_active = False
        user.status = 'inactive'  # 同时更新状态字段
        DatabaseService.commit_session(session)
        
        # 记录系统日志
        try:
            current_user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
            current_user_branch_id = current_user.branch_id if hasattr(current_user, 'branch_id') else current_user.get('branch_id')
            
            if current_user_id:
                # 使用统一日志服务记录系统日志
                from services.unified_log_service import log_user_management
                from utils.language_utils import get_current_language
                
                current_language = get_current_language()
                log_user_management(
                    operator_id=current_user_id,
                    branch_id=current_user_branch_id,
                    action_type='delete',
                    target_user=f"{user.login_code} ({user.name})",
                    ip_address=request.remote_addr,
                    language=current_language
                )
        except Exception as log_error:
            print(f"记录系统日志失败: {str(log_error)}")
            # 继续执行，不影响用户删除
            
        return jsonify({'success': True, 'message': 'User deactivated'})
    except Exception as e:
        DatabaseService.rollback_session(session)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@user_bp.route('/<int:user_id>/check-business', methods=['GET'])
@token_required
@has_permission('user_manage')
def check_user_business(current_user, user_id):
    """检查用户是否有业务流水"""
    session = DatabaseService.get_session()
    try:
        user = session.query(Operator).get(user_id)
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # 检查用户是否有业务流水
        from models.exchange_models import ExchangeTransaction
        
        # 检查兑换业务
        exchange_count = session.query(ExchangeTransaction).filter_by(
            operator_id=user_id,
            type='buy'
        ).count()
        exchange_count += session.query(ExchangeTransaction).filter_by(
            operator_id=user_id,
            type='sell'
        ).count()
        
        # 检查冲正业务
        reversal_count = session.query(ExchangeTransaction).filter_by(
            operator_id=user_id,
            type='reversal'
        ).count()
        
        # 检查余额调节业务
        balance_adjust_count = session.query(ExchangeTransaction).filter_by(
            operator_id=user_id,
            type='adjust_balance'
        ).count()
        
        # 检查余额初始化业务
        initial_balance_count = session.query(ExchangeTransaction).filter_by(
            operator_id=user_id,
            type='initial_balance'
        ).count()
        
        total_business_count = exchange_count + reversal_count + balance_adjust_count + initial_balance_count
        
        business_details = []
        if exchange_count > 0:
            business_details.append(f"兑换业务: {exchange_count}笔")
        if reversal_count > 0:
            business_details.append(f"冲正业务: {reversal_count}笔")
        if balance_adjust_count > 0:
            business_details.append(f"余额调节: {balance_adjust_count}笔")
        if initial_balance_count > 0:
            business_details.append(f"余额初始化: {initial_balance_count}笔")
        
        return jsonify({
            'success': True,
            'can_delete': total_business_count == 0,
            'business_count': total_business_count,
            'business_details': business_details,
            'exchange_count': exchange_count,
            'reversal_count': reversal_count,
            'balance_adjust_count': balance_adjust_count,
            'initial_balance_count': initial_balance_count
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

# 新增活跃状态相关接口
@user_bp.route('/<int:user_id>/activities', methods=['GET'])
@token_required
@has_permission('user_manage')
def get_user_activities(current_user, user_id):
    """获取用户活跃状态记录"""
    try:
        limit = request.args.get('limit', 50, type=int)
        activity_type = request.args.get('activity_type')
        
        activities = ActivityService.get_operator_activities(
            user_id, 
            limit=limit, 
            activity_type=activity_type
        )
        
        return jsonify({
            'success': True,
            'activities': activities
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@user_bp.route('/activities/summary', methods=['GET'])
@token_required
@has_permission('user_manage')
def get_activities_summary(current_user):
    """获取活跃状态统计摘要"""
    try:
        branch_id = request.args.get('branch_id', type=int)
        days = request.args.get('days', 7, type=int)
        
        summary = ActivityService.get_activities_summary(
            branch_id=branch_id,
            days=days
        )
        
        return jsonify({
            'success': True,
            'summary': summary
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@user_bp.route('/online', methods=['GET'])
@token_required
@has_permission('user_manage')
def get_online_users(current_user):
    """获取在线用户列表"""
    try:
        branch_id = request.args.get('branch_id', type=int)
        minutes = request.args.get('minutes', 30, type=int)
        
        online_operators = ActivityService.get_online_operators(
            branch_id=branch_id,
            minutes=minutes
        )
        
        return jsonify({
            'success': True,
            'online_operators': online_operators
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ----------------------------- 权限接口 -----------------------------

@perm_bp.route('/', methods=['GET'])
@token_required
def get_permissions(current_user):
    session = DatabaseService.get_session()
    try:
        perms = session.query(Permission).order_by(Permission.id).all()
        return jsonify({'success': True, 'permissions': [
            {'id': p.id, 'name': p.permission_name, 'description': p.description} for p in perms
        ]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

# 角色管理功能已移至 app_roles.py，避免重复
# 此处的角色API已被移除，请使用 /api/roles

# 角色创建功能已移至 app_roles.py，避免重复
# 此处的角色创建API已被移除，请使用 /api/roles

# 角色管理功能已移至 app_roles.py，避免重复
# 此处的角色更新和删除API已被移除，请使用 /api/roles

# 扩展权限国际化API
@perm_bp.route('/translations', methods=['GET'])
@token_required
@has_permission('user_manage')
def get_permission_translations(current_user):
    """获取权限国际化描述"""
    session = DatabaseService.get_session()
    try:
        language = request.args.get('language', 'zh')
        
        # 获取所有权限及其翻译
        permissions = session.query(Permission).options(
            joinedload(Permission.translations)
        ).all()
        
        result = []
        for permission in permissions:
            translation = None
            for trans in permission.translations:
                if trans.language_code == language:
                    translation = trans.description
                    break
            
            result.append({
                'id': permission.id,
                'permission_name': permission.permission_name,
                'description': translation or permission.description,
                'original_description': permission.description
            })
        
        return jsonify({
            'success': True,
            'permissions': result,
            'language': language
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@perm_bp.route('/translations', methods=['POST'])
@token_required
@has_permission('role_manage')
def create_permission_translation(current_user):
    """创建权限国际化描述"""
    data = request.json
    
    required_fields = ['permission_id', 'language_code', 'description']
    if not data or not all(field in data for field in required_fields):
        return jsonify({'success': False, 'message': '缺少必要的翻译信息'}), 400
    
    session = DatabaseService.get_session()
    try:
        # 检查权限是否存在
        permission = session.query(Permission).filter_by(id=data['permission_id']).first()
        if not permission:
            return jsonify({'success': False, 'message': '权限不存在'}), 400
        
        # 检查翻译是否已存在
        existing_translation = session.query(PermissionTranslation).filter_by(
            permission_id=data['permission_id'],
            language_code=data['language_code']
        ).first()
        
        if existing_translation:
            # 更新现有翻译
            existing_translation.description = data['description']
            message = '权限翻译更新成功'
        else:
            # 创建新翻译
            new_translation = PermissionTranslation(
                permission_id=data['permission_id'],
                language_code=data['language_code'],
                description=data['description'],
                created_at=datetime.utcnow()
            )
            session.add(new_translation)
            message = '权限翻译创建成功'
        
        DatabaseService.commit_session(session)
        
        # 安全地记录活动
        try:
            current_user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
            current_user_branch_id = current_user.branch_id if hasattr(current_user, 'branch_id') else current_user.get('branch_id')
            
            if current_user_id:
                ActivityService.log_activity(
                    current_user_id, 
                    'action', 
                    f'Created/Updated permission translation: {data["permission_id"]} - {data["language_code"]}',
                    request.remote_addr,
                    request.headers.get('User-Agent'),
                    branch_id=current_user_branch_id
                )
        except Exception as log_error:
            print(f"记录活动日志失败: {str(log_error)}")
            # 继续执行，不影响翻译创建
        
        return jsonify({
            'success': True,
            'message': message
        })
    except Exception as e:
        DatabaseService.rollback_session(session)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@user_bp.route('/<int:user_id>/activate', methods=['PUT'])
@token_required
@has_permission('user_manage')
def activate_user(current_user, user_id):
    """激活用户"""
    session = DatabaseService.get_session()
    try:
        user = session.query(Operator).filter_by(id=user_id).first()
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        user.is_active = True
        user.status = 'active'
        DatabaseService.commit_session(session)
        
        # 记录活动日志
        try:
            current_user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
            current_user_branch_id = current_user.branch_id if hasattr(current_user, 'branch_id') else current_user.get('branch_id')
            
            if current_user_id:
                from services.unified_log_service import log_user_management
                from utils.language_utils import get_current_language
                
                current_language = get_current_language()
                log_user_management(
                    operator_id=current_user_id,
                    branch_id=current_user_branch_id,
                    action_type='activate',
                    target_user=f"{user.login_code} ({user.name})",
                    ip_address=request.remote_addr,
                    language=current_language
                )
        except Exception as log_error:
            print(f"记录活动日志失败: {str(log_error)}")
        
        return jsonify({'success': True, 'message': '用户已激活'})
    except Exception as e:
        DatabaseService.rollback_session(session)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@user_bp.route('/<int:user_id>/deactivate', methods=['PUT'])
@token_required
@has_permission('user_manage')
def deactivate_user(current_user, user_id):
    """停用用户"""
    session = DatabaseService.get_session()
    try:
        user = session.query(Operator).filter_by(id=user_id).first()
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        user.is_active = False
        user.status = 'inactive'
        DatabaseService.commit_session(session)
        
        # 记录活动日志
        try:
            current_user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
            current_user_branch_id = current_user.branch_id if hasattr(current_user, 'branch_id') else current_user.get('branch_id')
            
            if current_user_id:
                from services.unified_log_service import log_user_management
                from utils.language_utils import get_current_language
                
                current_language = get_current_language()
                log_user_management(
                    operator_id=current_user_id,
                    branch_id=current_user_branch_id,
                    action_type='deactivate',
                    target_user=f"{user.login_code} ({user.name})",
                    ip_address=request.remote_addr,
                    language=current_language
                )
        except Exception as log_error:
            print(f"记录活动日志失败: {str(log_error)}")
        
        return jsonify({'success': True, 'message': '用户已停用'})
    except Exception as e:
        DatabaseService.rollback_session(session)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)
