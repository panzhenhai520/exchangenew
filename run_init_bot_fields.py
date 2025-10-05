# -*- coding: utf-8 -*-
"""
执行BOT报表字段初始化
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.db_service import SessionLocal
from sqlalchemy import text

print("Initializing BOT Report Fields...")

# 读取SQL文件
with open('init_bot_fields.sql', 'r', encoding='utf-8') as f:
    sql_content = f.read()

# 分割语句
statements = []
for stmt in sql_content.split(';'):
    stmt = stmt.strip()
    if stmt and not stmt.startswith('--'):
        statements.append(stmt)

session = SessionLocal()

try:
    for i, stmt in enumerate(statements, 1):
        try:
            session.execute(text(stmt))
            print(f"  [OK] Statement {i}/{len(statements)}")
        except Exception as e:
            print(f"  [WARNING] Statement {i} failed: {str(e)[:80]}")

    session.commit()
    print("\n[OK] BOT fields initialization complete")

    # 验证
    result = session.execute(text("""
        SELECT report_type, COUNT(*) as field_count
        FROM report_fields
        WHERE report_type LIKE 'BOT%'
        GROUP BY report_type
        ORDER BY report_type
    """))

    print("\nBOT Report Fields:")
    for row in result:
        print(f"  {row.report_type}: {row.field_count} fields")

except Exception as e:
    session.rollback()
    print(f"\n[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

finally:
    session.close()
