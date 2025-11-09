#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
创建Branch 2
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
from models.exchange_models import Branch, Currency

def create_branch2():
    """创建Branch 2"""
    print("开始创建Branch 2...")

    session = DatabaseService.get_session()
    try:
        # 检查Branch 2是否已存在
        existing_branch = session.query(Branch).filter_by(id=2).first()
        if existing_branch:
            print(f"✅ Branch 2已存在: {existing_branch.branch_name}")
            return True

        # 获取THB作为本币
        thb = session.query(Currency).filter_by(currency_code='THB').first()
        if not thb:
            print("❌ THB货币不存在，无法创建分支")
            return False

        print(f"✅ 找到THB货币: ID={thb.id}")

        # 创建Branch 2
        branch2 = Branch(
            id=2,
            branch_name='Branch 2 Test',
            branch_code='BR002',
            address='Test Address 2',
            manager_name='Test Manager 2',
            phone_number='123-456-7890',
            base_currency_id=thb.id,
            is_active=True
        )

        session.add(branch2)
        session.commit()

        print(f"✅ 成功创建Branch 2:")
        print(f"   - ID: {branch2.id}")
        print(f"   - Name: {branch2.branch_name}")
        print(f"   - Code: {branch2.branch_code}")
        print(f"   - Base Currency: THB (ID={thb.id})")

        return True

    except Exception as e:
        session.rollback()
        print(f"❌ 创建失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        DatabaseService.close_session(session)

if __name__ == '__main__':
    result = create_branch2()
    sys.exit(0 if result else 1)
