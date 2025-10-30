#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path

try:
    import pymysql
except ImportError as exc:
    raise SystemExit("Please install pymysql first (pip install pymysql)") from exc

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def load_env_file(path: Path):
    values = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


env = dict(os.environ)
for candidate in (Path(".env"), Path(".env.local")):
    env.update(load_env_file(candidate))

conn = pymysql.connect(
    host=env.get("MYSQL_HOST") or env.get("DB_HOST") or "localhost",
    user=env.get("MYSQL_USER") or env.get("DB_USER"),
    password=env.get("MYSQL_PASSWORD") or env.get("DB_PASSWORD"),
    database=env.get("MYSQL_DATABASE") or env.get("DB_NAME"),
    port=int(env.get("MYSQL_PORT") or env.get("DB_PORT") or 3306),
    charset="utf8mb4",
)

with conn:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT field_name, field_en_name, field_cn_name, field_th_name
            FROM report_fields
            WHERE report_type IN ('AMLO-1-01','AMLO-1-02','AMLO-1-03')
            ORDER BY report_type, fill_order
            """
        )
        rows = cur.fetchall()
        for row in rows:
            print(row)
