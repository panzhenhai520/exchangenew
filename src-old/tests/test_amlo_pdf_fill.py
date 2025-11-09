# -*- coding: utf-8 -*-
"""
AMLO PDF表单填充测试脚本
测试 AMLO-1-01, AMLO-1-02, AMLO-1-03 PDF自动填充功能

运行方式:
    python src/tests/test_amlo_pdf_fill.py
"""

import os
import sys
from datetime import datetime

# Windows console encoding fix
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'ignore')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'ignore')

# 添加src目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(src_dir)
sys.path.insert(0, src_dir)

# 导入AMLO PDF填充服务
from services.pdf.amlo_form_filler import AMLOFormFiller, generate_amlo_pdf


def test_amlo_101_fill():
    """测试AMLO-1-01表单填充"""
    print("\n" + "=" * 60)
    print("测试AMLO-1-01表单填充")
    print("=" * 60)

    # 准备测试数据
    test_data = {
        # 客户信息
        'customer_id': '1234567890123',
        'customer_name': 'นายสมชาย ใจดี',  # Mr. Somchai Jaidee
        'customer_address': '123 ถ.สุขุมวิท แขวงคลองเตย เขตคลองเตย กรุงเทพฯ 10110',
        'customer_phone': '02-1234567',
        'customer_occupation': 'พนักงานบริษัท',  # Company employee

        # 交易信息
        'transaction_date': datetime(2025, 10, 18),
        'transaction_type': 'buy',  # buy = 买入外币(客户卖外币给机构)
        'foreign_amount': 75000.00,  # USD amount
        'transaction_purpose': 'ท่องเที่ยว',  # Tourism

        # 其他信息
        'beneficiary_name': 'ตนเอง',  # Self
        'reservation_no': 'AMLO20251018001',
        'is_original': True,
        'is_on_behalf': False,

        # 分支信息
        'branch': {
            'institution_code': '001',
            'branch_code': '005'
        }
    }

    # 输出路径
    output_dir = os.path.join(project_root, 'test_output')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'test_AMLO_101.pdf')

    try:
        print(f"\n生成测试PDF: {output_file}")
        print("\n测试数据:")
        print(f"  - 客户姓名: {test_data['customer_name']}")
        print(f"  - 身份证号: {test_data['customer_id']}")
        print(f"  - 交易日期: {test_data['transaction_date'].strftime('%Y-%m-%d')}")
        print(f"  - 交易类型: {test_data['transaction_type']}")
        print(f"  - 外币金额: ${test_data['foreign_amount']:,.2f}")

        # 生成PDF
        result_path = generate_amlo_pdf('AMLO-1-01', test_data, output_file)

        print(f"\n✅ 成功生成PDF: {result_path}")
        print("\n请打开PDF文件验证以下内容:")
        print("  1. 报告编号 (右上角): 001-005-68-AMLO20251018001")
        print("  2. 身份证号 (13位方框): 1234567890123")
        print("  3. 客户姓名: นายสมชาย ใจดี")
        print("  4. 交易日期: 18/10/2568 (佛历)")
        print("  5. 买入外币勾选框: ✓")
        print("  6. 交易金额: 75,000.00")

        return True

    except FileNotFoundError as e:
        print(f"\n❌ 模板文件未找到: {e}")
        print("\n请确保以下模板文件存在:")
        print("  D:\\code\\exchangenew\\src\\static\\amlo_forms\\AMLO-1-01.pdf")
        return False

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_field_extraction():
    """测试字段提取功能"""
    print("\n" + "=" * 60)
    print("测试字段提取和映射")
    print("=" * 60)

    from services.pdf.amlo_field_mappings import DB_TO_PDF_MAPPING_101
    from services.pdf.amlo_form_filler import AMLOFormFiller

    test_data = {
        'customer_id': '1234567890123',
        'customer_name': 'Test Customer',
        'transaction_date': datetime(2025, 10, 18),
        'transaction_type': 'buy',
        'foreign_amount': 75000.00,
        'branch': {
            'institution_code': '001',
            'branch_code': '005'
        }
    }

    try:
        filler = AMLOFormFiller()
        field_values = filler._extract_field_values(
            test_data,
            DB_TO_PDF_MAPPING_101,
            {}
        )

        print(f"\n成功提取 {len(field_values)} 个字段值:")
        for field_name, field_value in sorted(field_values.items())[:10]:
            print(f"  - {field_name}: {field_value}")

        print("\n✅ 字段提取测试通过")
        return True

    except Exception as e:
        print(f"\n❌ 字段提取测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_template_existence():
    """测试模板文件是否存在"""
    print("\n" + "=" * 60)
    print("检查AMLO模板文件")
    print("=" * 60)

    template_dir = os.path.join(project_root, 'src', 'static', 'amlo_forms')
    templates = ['AMLO-1-01.pdf', 'AMLO-1-02.pdf', 'AMLO-1-03.pdf']

    all_exist = True
    for template in templates:
        template_path = os.path.join(template_dir, template)
        exists = os.path.exists(template_path)
        status = "✅ 存在" if exists else "❌ 不存在"
        print(f"  {template}: {status}")

        if exists:
            size = os.path.getsize(template_path)
            print(f"    大小: {size / 1024:.2f} KB")
        else:
            all_exist = False

    return all_exist


def test_font_availability():
    """测试泰文字体是否可用"""
    print("\n" + "=" * 60)
    print("检查泰文字体")
    print("=" * 60)

    font_dir = os.path.join(project_root, 'src', 'fonts')
    thai_fonts = ['Sarabun-Regular.ttf', 'Sarabun-Bold.ttf']

    any_found = False
    for font in thai_fonts:
        font_path = os.path.join(font_dir, font)
        exists = os.path.exists(font_path)
        status = "✅ 存在" if exists else "❌ 不存在"
        print(f"  {font}: {status}")

        if exists:
            any_found = True
            size = os.path.getsize(font_path)
            print(f"    大小: {size / 1024:.2f} KB")

    if not any_found:
        print("\n⚠️ 警告: 未找到泰文字体，将使用Helvetica替代")
        print("  泰文可能无法正常显示")

    return any_found


def main():
    """运行所有测试"""
    print("=" * 60)
    print("AMLO PDF 表单填充测试套件")
    print("=" * 60)

    results = {}

    # 测试1: 模板文件存在性
    results['templates'] = test_template_existence()

    # 测试2: 字体可用性
    results['fonts'] = test_font_availability()

    # 测试3: 字段提取
    results['field_extraction'] = test_field_extraction()

    # 测试4: AMLO-1-01表单填充
    results['amlo_101'] = test_amlo_101_fill()

    # 总结
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name}: {status}")

    all_passed = all(results.values())
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败，请检查上述错误信息")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
