#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Export AMLO report_fields definitions to a JSON file for analysis.
"""

import json
import os
from pathlib import Path

try:
    import pymysql
except ImportError as exc:
    raise SystemExit("Please install pymysql first (pip install pymysql)") from exc


def load_env(values: dict, path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values.setdefault(key.strip(), value.strip())


env = dict(os.environ)
for candidate in (Path(".env"), Path(".env.local")):
    load_env(env, candidate)

conn = pymysql.connect(
    host=env.get("MYSQL_HOST") or env.get("DB_HOST") or "localhost",
    user=env.get("MYSQL_USER") or env.get("DB_USER"),
    password=env.get("MYSQL_PASSWORD") or env.get("DB_PASSWORD"),
    database=env.get("MYSQL_DATABASE") or env.get("DB_NAME"),
    port=int(env.get("MYSQL_PORT") or env.get("DB_PORT") or 3306),
    charset="utf8mb4",
)

output = {}

with conn:
    with conn.cursor() as cur:
        for report_type in ("AMLO-1-01", "AMLO-1-02", "AMLO-1-03"):
            cur.execute(
                """
                SELECT
                    field_name,
                    field_en_name,
                    field_cn_name,
                    field_th_name,
                    fillpos
                FROM report_fields
                WHERE report_type = %s
                ORDER BY fill_order
                """,
                (report_type,),
            )
            output[report_type] = [
                {
                    "field_name": row[0],
                    "field_en_name": row[1],
                    "field_cn_name": row[2],
                    "field_th_name": row[3],
                    "fillpos": row[4],
                }
                for row in cur.fetchall()
            ]

Path("report_fields_dump.json").write_text(
    json.dumps(output, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print("Exported report field definitions to report_fields_dump.json")
