import json
fields=json.load(open('tmp_report_fields.json','r',encoding='utf-8'))['AMLO-1-01']
for field in fields:
    print(f"{field['fill_order']:3} {field['field_name']:35} {field['field_th_name']}")
