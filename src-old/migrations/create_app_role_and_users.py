"""
创建App角色和用户的数据库迁移脚本
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import hashlib
from datetime import datetime
from sqlalchemy import text
from services.db_service import DatabaseService
from models.exchange_models import Role, Operator, Branch

def create_app_role_and_users():
    """创建App角色和用户"""
    session = DatabaseService.get_session()
    try:
        print("开始创建App角色和用户...")
        
        # 1. 创建App角色
        existing_role = session.query(Role).filter_by(role_name="App").first()
        if existing_role:
            print(f"App角色已存在，ID: {existing_role.id}")
            app_role = existing_role
        else:
            app_role = Role(
                role_name="App",
                description="移动端专用角色，支持汇率发布、查询、日结等功能",
                created_at=datetime.utcnow()
            )
            session.add(app_role)
            session.flush()  # 获取角色ID
            print(f"创建App角色成功，ID: {app_role.id}")
        
        # 2. 为每个网点创建App用户
        branches = session.query(Branch).all()
        created_users = []
        
        for branch in branches:
            # 检查是否已存在App用户
            existing_user = session.query(Operator).filter_by(
                login_code=f"app_{branch.branch_code}",
                role_id=app_role.id
            ).first()
            
            if existing_user:
                print(f"网点 {branch.branch_name} 的App用户已存在: {existing_user.login_code}")
                continue
            
            # 创建App用户
            app_user = Operator(
                login_code=f"app_{branch.branch_code}",
                password_hash=hashlib.md5("123456".encode()).hexdigest(),
                name=f"App用户-{branch.branch_name}",
                branch_id=branch.id,
                role_id=app_role.id,
                is_active=True,
                status='active',
                created_at=datetime.utcnow()
            )
            session.add(app_user)
            created_users.append(app_user)
            print(f"创建App用户: {app_user.login_code} (网点: {branch.branch_name})")
        
        session.commit()
        print(f"成功创建 {len(created_users)} 个App用户")
        
        return {
            'role_id': app_role.id,
            'created_users': len(created_users),
            'total_branches': len(branches)
        }
        
    except Exception as e:
        session.rollback()
        print(f"创建App角色和用户失败: {str(e)}")
        raise
    finally:
        DatabaseService.close_session(session)

def add_app_permissions():
    """为App角色添加必要的权限"""
    session = DatabaseService.get_session()
    try:
        print("开始为App角色添加权限...")
        
        # 获取App角色
        app_role = session.query(Role).filter_by(role_name="App").first()
        if not app_role:
            print("App角色不存在，请先创建App角色")
            return
        
        # 定义App角色需要的权限
        app_permissions = [
            'dashboard_view',           # 首页查看
            'rates_manage',             # 汇率管理
            'rates_publish',            # 汇率发布
            'balance_query',            # 余额查询
            'balance_adjust_query',     # 余额调节查询
            'income_query',             # 动态收入查询
            'foreign_stock_query',      # 库存外币查询
            'eod_history_view',         # 日结历史查看
            'user_manage',              # 用户管理
            'role_manage',              # 角色管理
            'profile_view',             # 个人信息查看
            'profile_edit',             # 个人信息编辑
            'password_change'           # 密码修改
        ]
        
        # 检查并添加权限
        added_permissions = 0
        for permission_name in app_permissions:
            # 查找权限 - 使用正确的SQL语法
            permission_result = session.execute(text('''
                SELECT id FROM permissions WHERE permission_name = :permission_name
            '''), {'permission_name': permission_name}).first()
            
            if not permission_result:
                print(f"权限 {permission_name} 不存在，跳过")
                continue
            
            permission_id = permission_result[0]
            
            # 检查是否已分配
            existing_role_permission = session.execute(text('''
                SELECT id FROM role_permissions 
                WHERE role_id = :role_id AND permission_id = :permission_id
            '''), {
                'role_id': app_role.id,
                'permission_id': permission_id
            }).first()
            
            if existing_role_permission:
                print(f"权限 {permission_name} 已分配给App角色")
                continue
            
            # 添加权限分配
            session.execute(text('''
                INSERT INTO role_permissions (role_id, permission_id, created_at)
                VALUES (:role_id, :permission_id, :created_at)
            '''), {
                'role_id': app_role.id,
                'permission_id': permission_id,
                'created_at': datetime.utcnow()
            })
            added_permissions += 1
            print(f"为App角色添加权限: {permission_name}")
        
        session.commit()
        print(f"成功为App角色添加 {added_permissions} 个权限")
        
    except Exception as e:
        session.rollback()
        print(f"为App角色添加权限失败: {str(e)}")
        raise
    finally:
        DatabaseService.close_session(session)

if __name__ == "__main__":
    print("=== 创建App角色和用户 ===")
    result = create_app_role_and_users()
    print(f"角色ID: {result['role_id']}")
    print(f"创建用户数: {result['created_users']}")
    print(f"总网点数: {result['total_branches']}")
    
    print("\n=== 为App角色添加权限 ===")
    add_app_permissions()
    
    print("\n=== 完成 ===") 