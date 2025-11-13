import json
from pprint import pprint
rows = json.load(open('tmp_101_csv.json','r',encoding='utf-8'))
print('rows:', len(rows))
pprint(rows[-10:])
