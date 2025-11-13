import os
from pathlib import Path
import json
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
data = {}
with conn:
    with conn.cursor() as cur:
        cur.execute("SELECT report_type, field_name, field_th_name, fill_order FROM report_fields ORDER BY report_type, fill_order")
        for report_type, field_name, field_th_name, fill_order in cur.fetchall():
            data.setdefault(report_type, []).append({
                'field_name': field_name,
                'field_th_name': field_th_name,
                'fill_order': fill_order
            })
Path('tmp_report_fields.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print('Exported to tmp_report_fields.json')
