#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
检查分支数据
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

def check_branches():
    """检查分支数据"""
    print("检查分支数据...")

    session = DatabaseService.get_session()
    try:
        branches = session.query(Branch).all()
        print(f"\n当前数据库中有 {len(branches)} 个分支:")

        for branch in branches:
            base_currency = session.query(Currency).filter_by(id=branch.base_currency_id).first()
            base_currency_code = base_currency.currency_code if base_currency else "None"
            print(f"  - ID={branch.id}, Name={branch.branch_name}, Code={branch.branch_code}, Base Currency={base_currency_code}")

        # 检查Branch 2
        branch2 = session.query(Branch).filter_by(id=2).first()
        if branch2:
            print(f"\n✅ Branch 2已存在: {branch2.branch_name}")
        else:
            print(f"\n❌ Branch 2不存在")

    except Exception as e:
        print(f"❌ 检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        DatabaseService.close_session(session)

if __name__ == '__main__':
    check_branches()
