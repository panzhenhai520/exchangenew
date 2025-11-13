import csv
import json
from pathlib import Path

rows = []
with open('Re/1-01-field-map.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

Path('tmp_101_csv.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
print('ok')
