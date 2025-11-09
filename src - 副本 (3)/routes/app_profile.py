from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from services.db_service import DatabaseService
from services.auth_service import token_required
from services.log_service import record_system_log
from services.activity_service import ActivityService
from models.exchange_models import Operator, Branch, Role
from datetime import datetime
import hashlib
import re

profile_bp = Blueprint('profile', __name__, url_prefix='/api/user')

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
    # 允许输入任何字符，不进行格式校验
    return True

@profile_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """获取当前用户的个人信息"""
    session = DatabaseService.get_session()
    try:
        # 获取当前用户ID
        user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
        
        # 查询用户信息，包含关联的角色和分支信息
        user = session.query(Operator).filter_by(id=user_id).first()
        
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        # 获取角色信息
        role_name = None
        if user.role_id:
            role = session.query(Role).filter_by(id=user.role_id).first()
            role_name = role.role_name if role else None
        
        # 获取分支信息
        branch_name = None
        if user.branch_id:
            branch = session.query(Branch).filter_by(id=user.branch_id).first()
            branch_name = branch.branch_name if branch else None
        
        result = {
            'id': user.id,
            'login_code': user.login_code,
            'name': user.name,
            'email': getattr(user, 'email', None),
            'mobile_number': getattr(user, 'mobile_number', None),
            'phone_number': getattr(user, 'phone_number', None),
            'id_card_number': getattr(user, 'id_card_number', None),
            'address': getattr(user, 'address', None),
            'role_id': user.role_id,
            'role_name': role_name,
            'branch_id': user.branch_id,
            'branch_name': branch_name,
            'status': getattr(user, 'status', 'active'),
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'created_at': user.created_at.isoformat() if user.created_at else None
        }
        
        # 记录活动日志
        try:
            current_user_branch_id = current_user.branch_id if hasattr(current_user, 'branch_id') else current_user.get('branch_id')
            ActivityService.log_activity(
                user_id, 
                'profile_view', 
                'View personal profile',
                request.remote_addr,
                request.headers.get('User-Agent'),
                branch_id=current_user_branch_id
            )
        except Exception as log_error:
            print(f"记录活动日志失败: {str(log_error)}")
        
        return jsonify({'success': True, 'user': result})
    except Exception as e:
        print(f"获取个人信息失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@profile_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    """更新当前用户的个人信息"""
    data = request.json
    
    if not data:
        return jsonify({'success': False, 'message': '缺少更新数据'}), 400
    
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
        # 获取当前用户ID
        user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
        
        # 查询用户
        user = session.query(Operator).filter_by(id=user_id).first()
        
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        # 更新允许修改的字段
        updatable_fields = ['name', 'email', 'mobile_number', 'phone_number', 'id_card_number', 'address']
        updated_fields = []
        
        for field in updatable_fields:
            if field in data:
                old_value = getattr(user, field, None)
                new_value = data[field]
                
                if old_value != new_value:
                    setattr(user, field, new_value)
                    updated_fields.append(f"{field}: {old_value} -> {new_value}")
        
        if updated_fields:
            # 提交更改
            session.commit()
            
            # 记录系统日志
            try:
                record_system_log(
                    user_id=user_id,
                    action='profile_update',
                    description=f'Updated profile fields: {", ".join(updated_fields)}',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
            except Exception as log_error:
                print(f"记录系统日志失败: {str(log_error)}")
            
            # 记录活动日志
            try:
                current_user_branch_id = current_user.branch_id if hasattr(current_user, 'branch_id') else current_user.get('branch_id')
                ActivityService.log_activity(
                    user_id, 
                    'profile_update', 
                    f'Updated profile: {", ".join([field.split(":")[0] for field in updated_fields])}',
                    request.remote_addr,
                    request.headers.get('User-Agent'),
                    branch_id=current_user_branch_id
                )
            except Exception as log_error:
                print(f"记录活动日志失败: {str(log_error)}")
            
            return jsonify({'success': True, 'message': '个人信息更新成功'})
        else:
            return jsonify({'success': True, 'message': '没有需要更新的信息'})
            
    except Exception as e:
        session.rollback()
        print(f"更新个人信息失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@profile_bp.route('/change-password', methods=['PUT'])
@token_required
def change_password(current_user):
    """修改当前用户的密码"""
    data = request.json
    
    if not data:
        return jsonify({'success': False, 'message': 'Missing password data'}), 400
    
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({'success': False, 'message': 'Current password and new password cannot be empty'}), 400
    
    if len(new_password) < 8:
        return jsonify({'success': False, 'message': 'New password must be at least 8 characters'}), 400
    
    session = DatabaseService.get_session()
    try:
        # 获取当前用户ID
        user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
        
        # 查询用户
        user = session.query(Operator).filter_by(id=user_id).first()
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # 验证当前密码
        # 支持多种密码验证方式
        current_password_valid = False
        
        # 方式1: 检查MD5哈希
        if user.password_hash == hashlib.md5(current_password.encode()).hexdigest():
            current_password_valid = True
        # 方式2: 检查Werkzeug密码哈希
        elif user.password_hash and user.password_hash.startswith('pbkdf2:'):
            try:
                current_password_valid = check_password_hash(user.password_hash, current_password)
            except:
                pass
        # 方式3: 直接比较（不安全，但可能存在）
        elif user.password_hash == current_password:
            current_password_valid = True
        
        if not current_password_valid:
            # 记录密码修改失败的尝试
            try:
                record_system_log(
                    user_id=user_id,
                    action='password_change_failed',
                    description='Invalid current password provided',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
            except Exception as log_error:
                print(f"记录系统日志失败: {str(log_error)}")
            
            return jsonify({'success': False, 'message': 'Current password is incorrect'}), 400
        
        # 生成新密码的哈希
        # 使用MD5保持与登录验证的一致性
        new_password_hash = hashlib.md5(new_password.encode()).hexdigest()
        
        # 更新密码
        user.password_hash = new_password_hash
        session.commit()
        
        # 记录系统日志
        try:
            record_system_log(
                user_id=user_id,
                action='password_change',
                description='Password changed successfully',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
        except Exception as log_error:
            print(f"记录系统日志失败: {str(log_error)}")
        
        # 记录活动日志
        try:
            current_user_branch_id = current_user.branch_id if hasattr(current_user, 'branch_id') else current_user.get('branch_id')
            ActivityService.log_activity(
                user_id, 
                'password_change', 
                'Password changed successfully',
                request.remote_addr,
                request.headers.get('User-Agent'),
                branch_id=current_user_branch_id
            )
        except Exception as log_error:
            print(f"记录活动日志失败: {str(log_error)}")
        
        return jsonify({'success': True, 'message': 'Password changed successfully'})
        
    except Exception as e:
        session.rollback()
        print(f"Password change failed: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session) 