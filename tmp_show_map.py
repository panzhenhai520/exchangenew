import json
from operator import itemgetter

with open('tmp_fillpos_candidates.json','r',encoding='utf-8') as f:
    data=json.load(f)

for field in data['AMLO-1-01'][:20]:
    cand=field['candidates'][0] if field['candidates'] else None
    pdf_field = cand['pdf_field'] if cand else 'None'
    score = cand['score'] if cand else 0
    print(f"{field['field_name']:30} -> {pdf_field:15} ({score})")
