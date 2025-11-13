import csv
for encoding in ('utf-8-sig', 'utf-8', 'gbk'):
    try:
        with open('Re/fillpos1-01.csv', 'r', encoding=encoding) as f:
            rows = list(csv.reader(f))
        break
    except UnicodeDecodeError:
        continue
else:
    raise RuntimeError('Failed to decode CSV')

for row in rows[2:12]:
    print(row[1].strip("'"), row[23].strip("'"), row[27].strip("'"))
