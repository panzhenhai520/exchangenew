# -*- coding: utf-8 -*-
"""
执行report_fields初始化脚本
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.db_service import SessionLocal
from sqlalchemy import text

print("="*70)
print("Initializing Complete Report Fields")
print("="*70)

# 读取SQL文件
with open('init_complete_report_fields.sql', 'r', encoding='utf-8') as f:
    sql_content = f.read()

# 分割成多个语句
statements = []
current_statement = []

for line in sql_content.split('\n'):
    stripped = line.strip()
    # 跳过注释和空行
    if not stripped or stripped.startswith('--'):
        continue

    current_statement.append(line)

    # 检查是否语句结束
    if stripped.endswith(';'):
        statements.append('\n'.join(current_statement))
        current_statement = []

print(f"\nFound {len(statements)} SQL statements to execute\n")

session = SessionLocal()

try:
    executed = 0
    for i, stmt in enumerate(statements, 1):
        try:
            session.execute(text(stmt))
            executed += 1
            if i % 10 == 0:
                print(f"  Executed {i}/{len(statements)} statements...")
        except Exception as e:
            print(f"  [WARNING] Statement {i} failed: {str(e)[:100]}")

    session.commit()

    print(f"\n[OK] Successfully executed {executed}/{len(statements)} statements")

    # 验证结果
    print("\nVerifying field counts:")
    print("-"*70)

    result = session.execute(text("""
        SELECT report_type, COUNT(*) as field_count
        FROM report_fields
        GROUP BY report_type
        ORDER BY report_type
    """))

    for row in result:
        print(f"  {row.report_type}: {row.field_count} fields")

    print("\n" + "="*70)
    print("Report Fields Initialization Complete!")
    print("="*70)

except Exception as e:
    session.rollback()
    print(f"\n[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

finally:
    session.close()
