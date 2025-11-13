import pymysql
from pathlib import Path

def load_env():
    env = {}
    for file in (Path('.env'), Path('.env.local')):
        if file.exists():
            for line in file.read_text(encoding='utf-8').splitlines():
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
        cur.execute("SELECT login_code, password_hash FROM operators WHERE login_code='admin'")
        for row in cur.fetchall():
            print(row)
