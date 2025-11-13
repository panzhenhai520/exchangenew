import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from difflib import SequenceMatcher
import pymysql

CSV_MAP = {
    'AMLO-1-01': Path('Re/1-01-field-map.csv'),
    'AMLO-1-02': Path('Re/1-02-field-map.csv'),
    'AMLO-1-03': Path('Re/1-03-field-map.csv'),
}


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


def load_report_fields():
    env = load_env()
    conn = pymysql.connect(host=env.get('MYSQL_HOST', 'localhost'),
                           user=env.get('MYSQL_USER'),
                           password=env.get('MYSQL_PASSWORD'),
                           database=env.get('MYSQL_DATABASE'),
                           port=int(env.get('MYSQL_PORT', 3306)),
                           charset='utf8mb4')
    rows = defaultdict(list)
    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT report_type, field_name, field_th_name, field_en_name,
                       field_cn_name, field_type, fillpos, fill_order, field_group
                FROM report_fields
                WHERE report_type IN ('AMLO-1-01','AMLO-1-02','AMLO-1-03')
                ORDER BY report_type, fill_order
            """)
            for row in cur.fetchall():
                report_type, field_name, th, en, cn, ftype, fillpos, order, group = row
                rows[report_type].append({
                    'field_name': field_name,
                    'field_th_name': th or '',
                    'field_en_name': en,
                    'field_cn_name': cn,
                    'field_type': ftype,
                    'fillpos': fillpos,
                    'fill_order': order,
                    'field_group': group,
                })
    return rows


def load_csv(report_type):
    path = CSV_MAP[report_type]
    entries = []
    with path.open('r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = row['nearby_th_label'].strip()
            entries.append({
                'pdf_field': row['field_name'].strip(),
                'label': label,
                'type': row['type'].strip()
            })
    return entries


def normalize(text):
    if not text:
        return ''
    text = text.lower()
    text = re.sub(r'[\d\s\u0e50-\u0e59\.\-_/\\,()\[\]{}]', '', text)
    text = text.replace('?', '').replace('?', '')
    return text


def best_matches(field_label, entries, topn=5):
    norm_target = normalize(field_label)
    scored = []
    for entry in entries:
        candidate = entry['label']
        norm_candidate = normalize(candidate)
        if not norm_candidate and not norm_target:
            score = 0
        else:
            score = SequenceMatcher(None, norm_target, norm_candidate).ratio()
            if norm_target and norm_candidate:
                if norm_target in norm_candidate or norm_candidate in norm_target:
                    score += 0.2
        scored.append((score, entry))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:topn]


def main():
    report_fields = load_report_fields()
    output = {}
    for report_type, fields in report_fields.items():
        csv_entries = load_csv(report_type)
        output_rows = []
        for field in fields:
            matches = best_matches(field['field_th_name'], csv_entries)
            output_rows.append({
                'field_name': field['field_name'],
                'field_th_name': field['field_th_name'],
                'field_en_name': field['field_en_name'],
                'field_type': field['field_type'],
                'field_group': field['field_group'],
                'existing_fillpos': field['fillpos'],
                'candidates': [
                    {
                        'pdf_field': m[1]['pdf_field'],
                        'label': m[1]['label'],
                        'score': round(m[0], 3)
                    }
                    for m in matches
                ]
            })
        output[report_type] = output_rows
    Path('tmp_fillpos_candidates.json').write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Generated tmp_fillpos_candidates.json')


if __name__ == '__main__':
    main()
