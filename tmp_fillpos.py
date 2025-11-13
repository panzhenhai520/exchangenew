import os
from pathlib import Path
import pymysql

env = {}
for path in (Path('.env'), Path('.env.local')):
    if path.exists():
        for line in path.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip()

conn = pymysql.connect(
    host=env.get('MYSQL_HOST', 'localhost'),
    user=env.get('MYSQL_USER'),
    password=env.get('MYSQL_PASSWORD'),
    database=env.get('MYSQL_DATABASE'),
    port=int(env.get('MYSQL_PORT', 3306)),
    charset='utf8mb4'
)
with conn:
    with conn.cursor() as cur:
        cur.execute("SELECT report_type, field_name, field_th_name, fillpos FROM report_fields WHERE fillpos IS NOT NULL ORDER BY report_type, fill_order")
        for row in cur.fetchall():
            print(row)
