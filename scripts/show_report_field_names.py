#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from pathlib import Path

data = json.loads(Path("report_fields_dump.json").read_text(encoding="utf-8"))

for report_type, items in data.items():
    print(f"== {report_type} ==")
    for item in items:
        print(f"{item['field_name']:<35} {item['field_en_name']}")
    print()
