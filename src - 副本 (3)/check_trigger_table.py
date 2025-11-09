#!/usr/bin/env python3
"""检查trigger_rules表结构"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from sqlalchemy import text

session = DatabaseService.get_session()
try:
    result = session.execute(text("SHOW COLUMNS FROM trigger_rules")).fetchall()
    print("trigger_rules表结构:")
    for row in result:
        print(f"  {row[0]}: {row[1]}")
finally:
    DatabaseService.close_session(session)

