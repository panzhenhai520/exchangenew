# -*- coding: utf-8 -*-
"""检查PDF模板的表单字段"""
import sys
import os

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from PyPDF2 import PdfReader
import csv

def inspect_pdf_fields(pdf_path, csv_path=None):
    """检查PDF表单字段"""
    print("="*80)
    print(f"检查PDF模板: {pdf_path}")
    print("="*80)

    if not os.path.exists(pdf_path):
        print(f"❌ 文件不存在: {pdf_path}")
        return

    try:
        reader = PdfReader(pdf_path)
        fields = reader.get_fields()

        if not fields:
            print("\n⚠️  警告: PDF没有表单字段！")
            print("   这可能是一个静态PDF，不是可填写的表单")
            print("   需要使用Adobe Acrobat创建表单字段")
            return

        print(f"\n✅ 找到 {len(fields)} 个表单字段\n")

        # 按字段名排序
        sorted_fields = sorted(fields.items(), key=lambda x: x[0])

        # 显示字段列表
        print("PDF表单字段列表:")
        print("-" * 80)
        print(f"{'字段名':<30} {'字段类型':<15} {'默认值':<20}")
        print("-" * 80)

        for field_name, field_obj in sorted_fields:
            field_type = field_obj.get('/FT', 'Unknown')
            default_value = field_obj.get('/DV', field_obj.get('/V', ''))

            # 格式化字段类型
            if field_type == '/Tx':
                type_str = 'Text (文本)'
            elif field_type == '/Btn':
                type_str = 'Button (按钮/复选框)'
            elif field_type == '/Ch':
                type_str = 'Choice (选择框)'
            else:
                type_str = str(field_type)

            print(f"{field_name:<30} {type_str:<15} {str(default_value):<20}")

        # 如果提供了CSV文件，进行对比
        if csv_path and os.path.exists(csv_path):
            print("\n" + "="*80)
            print("对比CSV映射文件")
            print("="*80)

            with open(csv_path, 'r', encoding='utf-8') as f:
                reader_csv = csv.DictReader(f)
                csv_fields = {row['field_name']: row for row in reader_csv}

            print(f"\nCSV中定义的字段: {len(csv_fields)} 个")
            print(f"PDF中实际的字段: {len(fields)} 个\n")

            # 检查匹配情况
            matched = []
            csv_only = []
            pdf_only = []

            for field_name in csv_fields.keys():
                if field_name in fields:
                    matched.append(field_name)
                else:
                    csv_only.append(field_name)

            for field_name in fields.keys():
                if field_name not in csv_fields:
                    pdf_only.append(field_name)

            print(f"✅ 匹配的字段: {len(matched)} 个")
            print(f"⚠️  仅在CSV中: {len(csv_only)} 个")
            print(f"⚠️  仅在PDF中: {len(pdf_only)} 个")

            if csv_only:
                print("\n仅在CSV中存在的字段 (可能无法填充):")
                for fn in csv_only[:10]:  # 只显示前10个
                    print(f"  - {fn}")
                if len(csv_only) > 10:
                    print(f"  ... 还有 {len(csv_only) - 10} 个")

            if pdf_only:
                print("\n仅在PDF中存在的字段 (未在CSV中映射):")
                for fn in pdf_only[:10]:
                    print(f"  - {fn}")
                if len(pdf_only) > 10:
                    print(f"  ... 还有 {len(pdf_only) - 10} 个")

        print("\n" + "="*80)

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 检查3个模板
    templates = [
        ('AMLO-1-01', 'Re/1-01-fill.pdf', 'Re/1-01-field-map.csv'),
        ('AMLO-1-02', 'Re/1-02-fill.pdf', 'Re/1-02-field-map.csv'),
        ('AMLO-1-03', 'Re/1-03-fill.pdf', 'Re/1-03-field-map.csv'),
    ]

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    for report_type, pdf_file, csv_file in templates:
        pdf_path = os.path.join(project_root, pdf_file)
        csv_path = os.path.join(project_root, csv_file)

        print(f"\n\n{'#'*80}")
        print(f"# {report_type}")
        print(f"{'#'*80}\n")

        inspect_pdf_fields(pdf_path, csv_path)
        print("\n")
