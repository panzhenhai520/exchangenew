#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
检查角色数据
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
from models.exchange_models import Role

def check_roles():
    """检查角色数据"""
    print("检查角色数据...")

    session = DatabaseService.get_session()
    try:
        roles = session.query(Role).all()
        print(f"\n当前数据库中有 {len(roles)} 个角色:")

        for role in roles:
            print(f"  - ID={role.id}, Name={role.role_name}, Description={role.description}")

    except Exception as e:
        print(f"❌ 检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        DatabaseService.close_session(session)

if __name__ == '__main__':
    check_roles()
