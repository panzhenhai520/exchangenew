import json
with open('tmp_101_csv.json','r',encoding='utf-8') as f:
    rows=json.load(f)
for row in rows:
    print(f"{row['field_name']:15} {row['type']:8} {row['nearby_th_label']}")
