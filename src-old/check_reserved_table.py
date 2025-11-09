# -*- coding: utf-8 -*-
from services.db_service import DatabaseService
from sqlalchemy import text

s = DatabaseService.get_session()
result = s.execute(text('DESCRIBE Reserved_Transaction'))
print('Reserved_Transaction表结构:')
print(f"{'字段名':<30} {'类型':<30} {'允许NULL':<10}")
print("-"*80)
for row in result:
    print(f'{row[0]:<30} {row[1]:<30} {row[2]:<10}')
DatabaseService.close_session(s)

