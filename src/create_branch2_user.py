#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
创建Branch 2测试用户
"""

import sys
import os
import io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure stdout/stderr encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from services.db_service import DatabaseService
from models.exchange_models import Operator, Branch, Role
import hashlib

def create_branch2_user():
    """创建Branch 2测试用户"""
    print("开始创建Branch 2测试用户...")

    session = DatabaseService.get_session()
    try:
        # 检查Branch 2是否存在
        branch2 = session.query(Branch).filter_by(id=2).first()
        if not branch2:
            print("❌ Branch 2不存在，请先创建Branch 2")
            return False

        print(f"✅ Branch 2找到: {branch2.branch_name}")

        # 检查用户是否已存在
        existing_user = session.query(Operator).filter_by(login_code='branch2_user').first()
        if existing_user:
            print(f"✅ 用户 'branch2_user' 已存在 (ID={existing_user.id})")
            return True

        # 获取默认角色 (使用系统管理员角色)
        role = session.query(Role).filter_by(role_name='系统管理员').first()
        if not role:
            # 使用第一个找到的角色
            role = session.query(Role).first()

        if not role:
            print("❌ 没有找到可用的角色")
            return False

        print(f"✅ 使用角色: {role.role_name} (ID={role.id})")

        # 创建用户
        password_hash = hashlib.md5('branch2_pass'.encode()).hexdigest()

        new_user = Operator(
            name='Branch 2 Test User',
            login_code='branch2_user',
            password_hash=password_hash,
            role_id=role.id,
            branch_id=2,
            is_active=True
        )

        session.add(new_user)
        session.commit()

        print(f"✅ 成功创建用户:")
        print(f"   - ID: {new_user.id}")
        print(f"   - Name: {new_user.name}")
        print(f"   - Login Code: {new_user.login_code}")
        print(f"   - Password: branch2_pass")
        print(f"   - Branch: {branch2.branch_name} (ID=2)")
        print(f"   - Role: {role.role_name}")

        return True

    except Exception as e:
        session.rollback()
        print(f"❌ 创建用户失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        DatabaseService.close_session(session)

if __name__ == '__main__':
    result = create_branch2_user()
    sys.exit(0 if result else 1)
