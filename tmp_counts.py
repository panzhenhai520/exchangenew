import os
from pathlib import Path
import pymysql

def load_env():
    env = {}
    for path in (Path('.env'), Path('.env.local')):
        if not path.exists():
            continue
        for line in path.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip()
    return env

env = load_env()
conn = pymysql.connect(host=env.get('MYSQL_HOST', 'localhost'),
                       user=env.get('MYSQL_USER'),
                       password=env.get('MYSQL_PASSWORD'),
                       database=env.get('MYSQL_DATABASE'),
                       port=int(env.get('MYSQL_PORT', 3306)),
                       charset='utf8mb4')
with conn:
    with conn.cursor() as cur:
        cur.execute("SELECT report_type, COUNT(*) FROM report_fields GROUP BY report_type")
        for row in cur.fetchall():
            print(row)
