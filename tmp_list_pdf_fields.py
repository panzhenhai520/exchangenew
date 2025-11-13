from PyPDF2 import PdfReader
reader = PdfReader('Re/1-01-fill.pdf')
fields = reader.get_fields()
for name, data in fields.items():
    print(name, data.get('/FT'))
