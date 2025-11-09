from flask import Blueprint, jsonify, request
from datetime import datetime
from services.db_service import DatabaseService
from models.exchange_models import Permission, PermissionTranslation, Role, RolePermission
from flask import g
from services.auth_service import token_required, has_permission
from sqlalchemy.orm import joinedload

roles_bp = Blueprint('roles', __name__, url_prefix='/api')

def get_language_code():
    """获取当前语言代码，优先URL参数，其次请求头，统一只取前2位"""
    lang = request.args.get('lang')
    if not lang:
        lang = request.headers.get('Accept-Language', 'zh')
    lang = lang.lower()[:2]  # 只取前2位，兼容en-US、zh-CN等
    if lang == 'en':
        return 'en'
    elif lang == 'th':
        return 'th'
    else:
        return 'zh'

def get_permissions_with_translations(language_code):
    """获取权限列表，包含对应语言的翻译"""
    print(f"DEBUG: Getting permissions for language: {language_code}")
    session = DatabaseService.get_session()
    
    try:
        # 获取所有权限
        permissions = session.query(Permission).all()
        print(f"DEBUG: Found {len(permissions)} permissions")
        
        # 获取指定语言的翻译
        translations = session.query(PermissionTranslation).filter(
            PermissionTranslation.language_code == language_code
        ).all()
        print(f"DEBUG: Found {len(translations)} translations for language {language_code}")
        
        # 创建翻译映射
        translation_map = {t.permission_id: t.description for t in translations}
        print(f"DEBUG: Translation map: {translation_map}")
        
        # 构建权限列表
        result = []
        for permission in permissions:
            # 获取翻译后的描述
            translated_description = translation_map.get(permission.id, permission.description)
            print(f"DEBUG: Permission {permission.id} - Original: {permission.description}, Translated: {translated_description}")
            
            permission_dict = {
                'id': str(permission.id),
                'permission_name': permission.permission_name,  # 保持英文代码不变
                'description': translated_description  # 使用翻译后的描述
            }
            result.append(permission_dict)
        
        return result
    except Exception as e:
        print(f"Error getting permissions: {e}")
        return []
    finally:
        DatabaseService.close_session(session)

@roles_bp.route('/roles', methods=['GET'])
@token_required
def get_roles(current_user):
    """获取所有角色"""
    session = DatabaseService.get_session()
    try:
        roles = session.query(Role).options(
            joinedload(Role.permissions).joinedload(RolePermission.permission)
        ).all()

        result = []
        for role in roles:
            result.append({
                'id': role.id,
                'name': role.role_name,
                'description': role.description,
                'permissions': [
                    {
                        'id': rp.permission.id,
                        'name': rp.permission.permission_name,
                        'description': rp.permission.description
                    } for rp in role.permissions
                ]
            })
        return jsonify({'success': True, 'roles': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@roles_bp.route('/roles/<int:role_id>', methods=['GET'])
@token_required
def get_role(current_user, role_id):
    """获取单个角色详情"""
    session = DatabaseService.get_session()
    try:
        role = session.query(Role).options(
            joinedload(Role.permissions).joinedload(RolePermission.permission)
        ).filter_by(id=role_id).first()
        
        if not role:
            return jsonify({'success': False, 'message': '角色不存在'}), 404
            
        result = {
            'id': role.id,
            'name': role.role_name,
            'description': role.description,
            'permissions': [
                {
                    'id': rp.permission.id,
                    'name': rp.permission.permission_name,
                    'description': rp.permission.description
                } for rp in role.permissions
            ]
        }
        return jsonify({'success': True, 'role': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@roles_bp.route('/roles', methods=['POST'])
@token_required
def create_role(current_user):
    """创建新角色"""
    data = request.json
    
    if not data or not data.get('role_name'):
        return jsonify({'success': False, 'message': '角色名称不能为空'}), 400
    
    session = DatabaseService.get_session()
    try:
        # 检查角色名称是否已存在
        existing_role = session.query(Role).filter_by(role_name=data['role_name']).first()
        if existing_role:
            return jsonify({'success': False, 'message': '角色名称已存在'}), 400
        
        # 创建新角色
        new_role = Role(
            role_name=data['role_name'],
            description=data.get('description', '')
        )
        session.add(new_role)
        session.flush()  # 获取角色ID
        
        # 添加权限
        if data.get('permissions'):
            for permission_id in data['permissions']:
                role_permission = RolePermission(
                    role_id=new_role.id,
                    permission_id=permission_id
                )
                session.add(role_permission)
        
        session.commit()
        
        return jsonify({
            'success': True,
            'message': '角色创建成功',
            'role': {
                'id': new_role.id,
                'name': new_role.role_name,
                'description': new_role.description
            }
        })
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@roles_bp.route('/roles/<int:role_id>', methods=['PUT'])
@token_required
def update_role(current_user, role_id):
    """更新角色"""
    data = request.json
    
    if not data:
        return jsonify({'success': False, 'message': '没有提供数据'}), 400
    
    session = DatabaseService.get_session()
    try:
        role = session.query(Role).filter_by(id=role_id).first()
        if not role:
            return jsonify({'success': False, 'message': '角色不存在'}), 404
        
        # 检查角色名称是否已存在（如果更改了名称）
        if 'role_name' in data and data['role_name'] != role.role_name:
            existing_role = session.query(Role).filter_by(role_name=data['role_name']).first()
            if existing_role:
                return jsonify({'success': False, 'message': '角色名称已存在'}), 400
        
        # 更新角色信息
        if 'role_name' in data:
            role.role_name = data['role_name']
        if 'description' in data:
            role.description = data['description']
        
        # 更新权限
        if 'permissions' in data:
            # 删除现有权限
            session.query(RolePermission).filter_by(role_id=role_id).delete()
            
            # 添加新权限
            for permission_id in data['permissions']:
                role_permission = RolePermission(
                    role_id=role_id,
                    permission_id=permission_id
                )
                session.add(role_permission)
        
        session.commit()
        
        return jsonify({
            'success': True,
            'message': '角色更新成功',
            'role': {
                'id': role.id,
                'name': role.role_name,
                'description': role.description
            }
        })
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@roles_bp.route('/roles/<int:role_id>', methods=['DELETE'])
@token_required
def delete_role(current_user, role_id):
    """删除角色"""
    session = DatabaseService.get_session()
    try:
        role = session.query(Role).filter_by(id=role_id).first()
        if not role:
            return jsonify({'success': False, 'message': '角色不存在'}), 404
        
        # 检查是否为移动端专用内置角色
        if role.role_name in ['App', 'APP']:
            return jsonify({
                'success': False,
                'message': f'无法删除角色 "{role.role_name}"，这是移动端专用内置角色'
            }), 400
        
        # 检查是否有用户使用此角色
        from models.exchange_models import Operator
        operators_using_role = session.query(Operator).filter_by(role_id=role_id).all()
        if operators_using_role:
            operator_names = [op.name for op in operators_using_role]
            return jsonify({
                'success': False,
                'message': f'无法删除角色，以下用户正在使用：{", ".join(operator_names)}'
            }), 400
        
        # 删除角色权限关联
        session.query(RolePermission).filter_by(role_id=role_id).delete()
        
        # 删除角色
        session.delete(role)
        session.commit()
        
        return jsonify({
            'success': True,
            'message': f'角色 "{role.role_name}" 删除成功'
        })
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@roles_bp.route('/permissions', methods=['GET'])
def get_permissions():
    """获取权限列表，支持多语言"""
    print(f"DEBUG: get_permissions called")
    language_code = get_language_code()
    print(f"DEBUG: language_code: {language_code}")
    permissions = get_permissions_with_translations(language_code)
    print(f"DEBUG: permissions count: {len(permissions)}")
    return jsonify({'success': True, 'permissions': permissions})

@roles_bp.route('/roles/<int:role_id>/permissions', methods=['GET'])
@token_required
def get_role_permissions(current_user, role_id):
    """获取角色的权限列表"""
    session = DatabaseService.get_session()
    try:
        role = session.query(Role).options(
            joinedload(Role.permissions).joinedload(RolePermission.permission)
        ).filter_by(id=role_id).first()
        
        if not role:
            return jsonify({'success': False, 'message': '角色不存在'}), 404
        
        permissions = [
            {
                'id': rp.permission.id,
                'name': rp.permission.permission_name,
                'description': rp.permission.description
            } for rp in role.permissions
        ]
        
        return jsonify({'success': True, 'permissions': permissions})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)
