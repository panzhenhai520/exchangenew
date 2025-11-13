import json
from pprint import pprint
with open('tmp_fillpos_candidates.json','r',encoding='utf-8') as f:
    data=json.load(f)
pprint(data['AMLO-1-01'][:5])
