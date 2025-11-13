import fitz
import sys
pdf_path = 'Re/1-01-fill.pdf'
doc = fitz.open(pdf_path)
page = doc[0]
pix = page.get_pixmap(matrix=fitz.Matrix(2,2))
pix.save('amlo_101_page1.png')
print('Saved amlo_101_page1.png')
