# -*- coding: utf-8 -*-
"""
验证PDF中的复选框状态
"""
import fitz

pdf_path = r"D:\code\exchangenew\amlo_pdfs\test_checkbox.pdf"

doc = fitz.open(pdf_path)
page = doc[0]

print("Checkbox Status Verification")
print("=" * 80)

# 检查所有复选框
widgets = list(page.widgets()) if page.widgets() else []

checked_boxes = []
unchecked_boxes = []

for widget in widgets:
    if widget.field_type == fitz.PDF_WIDGET_TYPE_CHECKBOX:
        field_name = widget.field_name
        field_value = widget.field_value

        if field_value:
            checked_boxes.append(field_name)
        else:
            unchecked_boxes.append(field_name)

doc.close()

# 保存结果
with open('checkbox_status.txt', 'w', encoding='utf-8') as f:
    f.write("PDF Checkbox Status Report\n")
    f.write("=" * 80 + "\n\n")

    f.write(f"Checked Boxes ({len(checked_boxes)}):\n")
    f.write("-" * 80 + "\n")
    for box in checked_boxes:
        f.write(f"  [X] {box}\n")

    f.write(f"\nUnchecked Boxes ({len(unchecked_boxes)}):\n")
    f.write("-" * 80 + "\n")
    for box in unchecked_boxes:
        f.write(f"  [ ] {box}\n")

    f.write("\n" + "=" * 80 + "\n")
    f.write(f"Total checkboxes: {len(checked_boxes) + len(unchecked_boxes)}\n")
    f.write(f"Checked: {len(checked_boxes)}\n")
    f.write(f"Unchecked: {len(unchecked_boxes)}\n")

print(f"Checked: {len(checked_boxes)}")
print(f"Unchecked: {len(unchecked_boxes)}")
print("\nDetails saved to: checkbox_status.txt")
print("Please manually open the PDF to verify the checkmarks are visible.")
