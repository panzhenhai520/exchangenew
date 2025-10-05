# -*- coding: utf-8 -*-
"""
AMLO PDF生成器测试脚本
测试三种AMLO报告的PDF生成功能
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import codecs

# Windows UTF-8编码处理
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from services.pdf import AMLOPDFGenerator

def test_amlo_101():
    """测试AMLO-1-01现金交易报告生成"""
    print("=" * 70)
    print("测试 AMLO-1-01 现金交易报告生成")
    print("=" * 70)

    generator = AMLOPDFGenerator()

    data = {
        'report_number': 'A001-2025-001',
        'is_amendment': False,
        'maker_type': 'person',
        'maker_name': 'นายทดสอบ ระบบ',
        'maker_id': '1234567890123',
        'maker_address': '123 ถนนสุขุมวิท แขวงคลองเตย เขตคลองเตย กรุงเทพฯ 10110',
        'joint_party_name': '',
        'transaction_date': '01/10/2025',
        'transaction_type': 'exchange',
        'currency_code': 'USD',
        'amount_thb': 520000.00,
        'remarks': 'แลกเปลี่ยนเงินดอลลาร์สหรัฐ',
        'reporter_name': 'นางสาวพนักงาน ทดสอบ',
        'reporter_position': 'เจ้าหน้าที่แลกเปลี่ยนเงิน',
        'report_date': datetime.now().strftime('%d/%m/%Y')
    }

    output_path = os.path.join(project_root, 'test_output', 'AMLO-1-01_test.pdf')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        result = generator.generate_amlo_101(data, output_path)
        print(f"✓ AMLO-1-01 PDF生成成功")
        print(f"  输出文件: {result}")
        print(f"  文件大小: {os.path.getsize(result):,} bytes")
        return True
    except Exception as e:
        print(f"✗ AMLO-1-01 PDF生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_amlo_102():
    """测试AMLO-1-02资产交易报告生成"""
    print("\n" + "=" * 70)
    print("测试 AMLO-1-02 资产交易报告生成")
    print("=" * 70)

    generator = AMLOPDFGenerator()

    data = {
        'report_number': 'A001-2025-002',
        'is_amendment': False,
        'maker_type': 'company',
        'maker_name': 'บริษัท ทดสอบ จำกัด',
        'maker_id': '0123456789012',
        'asset_transaction_type': 'transfer',
        'asset_type': 'building',
        'asset_value_thb': 8500000.00,
        'reporter_name': 'นางสาวพนักงาน ทดสอบ',
        'reporter_position': 'เจ้าหน้าที่แลกเปลี่ยนเงิน',
        'report_date': datetime.now().strftime('%d/%m/%Y')
    }

    output_path = os.path.join(project_root, 'test_output', 'AMLO-1-02_test.pdf')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        result = generator.generate_amlo_102(data, output_path)
        print(f"✓ AMLO-1-02 PDF生成成功")
        print(f"  输出文件: {result}")
        print(f"  文件大小: {os.path.getsize(result):,} bytes")
        return True
    except Exception as e:
        print(f"✗ AMLO-1-02 PDF生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_amlo_103():
    """测试AMLO-1-03可疑交易报告生成"""
    print("\n" + "=" * 70)
    print("测试 AMLO-1-03 可疑交易报告生成")
    print("=" * 70)

    generator = AMLOPDFGenerator()

    data = {
        'report_number': 'A001-2025-003',
        'is_amendment': False,
        'has_filed_ctr_atr': True,
        'previous_report_number': 'A001-2025-001',
        'maker_name': 'นายทดสอบ ระบบ',
        'suspicion_reasons': '''1. ลูกค้าทำธุรกรรมแลกเปลี่ยนเงินตราจำนวนมาก
2. ไม่สามารถให้ข้อมูลแหล่งที่มาของเงินได้ชัดเจน
3. พฤติกรรมการทำธุรกรรมผิดปกติจากลูกค้าทั่วไป
4. ธุรกรรมไม่สอดคล้องกับประวัติการทำงานและรายได้
5. มีความพยายามหลีกเลี่ยงการให้ข้อมูล
6. มีเหตุอันควรสงสัยว่าเกี่ยวข้องกับการฟอกเงิน''',
        'reporter_name': 'นางสาวพนักงาน ทดสอบ',
        'report_date': datetime.now().strftime('%d/%m/%Y')
    }

    output_path = os.path.join(project_root, 'test_output', 'AMLO-1-03_test.pdf')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        result = generator.generate_amlo_103(data, output_path)
        print(f"✓ AMLO-1-03 PDF生成成功")
        print(f"  输出文件: {result}")
        print(f"  文件大小: {os.path.getsize(result):,} bytes")
        return True
    except Exception as e:
        print(f"✗ AMLO-1-03 PDF生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_unified_api():
    """测试统一的PDF生成API"""
    print("\n" + "=" * 70)
    print("测试统一PDF生成API (generate_pdf)")
    print("=" * 70)

    generator = AMLOPDFGenerator()

    # 测试数据
    test_cases = [
        {
            'type': 'AMLO-1-01',
            'data': {
                'report_number': 'A001-2025-004',
                'maker_name': 'นายทดสอบ API',
                'transaction_date': '02/10/2025',
                'amount_thb': 600000.00,
                'reporter_name': 'นางสาวพนักงาน ทดสอบ'
            }
        },
        {
            'type': 'AMLO-1-02',
            'data': {
                'report_number': 'A001-2025-005',
                'maker_name': 'บริษัท ทดสอบ API จำกัด',
                'asset_value_thb': 9000000.00,
                'reporter_name': 'นางสาวพนักงาน ทดสอบ'
            }
        },
        {
            'type': 'AMLO-1-03',
            'data': {
                'report_number': 'A001-2025-006',
                'maker_name': 'นายทดสอบ API',
                'suspicion_reasons': 'ทดสอบระบบ API',
                'reporter_name': 'นางสาวพนักงาน ทดสอบ'
            }
        }
    ]

    success_count = 0
    for test_case in test_cases:
        report_type = test_case['type']
        data = test_case['data']
        output_path = os.path.join(
            project_root, 'test_output',
            f"{report_type.replace('-', '_')}_api_test.pdf"
        )

        try:
            result = generator.generate_pdf(report_type, data, output_path)
            print(f"  ✓ {report_type}: {result}")
            success_count += 1
        except Exception as e:
            print(f"  ✗ {report_type}: {str(e)}")

    print(f"\n统一API测试结果: {success_count}/{len(test_cases)} 成功")
    return success_count == len(test_cases)

def main():
    """主测试函数"""
    print("\n" + "=" * 70)
    print("AMLO PDF生成器完整测试")
    print("=" * 70)
    print()

    # 执行所有测试
    results = []

    results.append(("AMLO-1-01", test_amlo_101()))
    results.append(("AMLO-1-02", test_amlo_102()))
    results.append(("AMLO-1-03", test_amlo_103()))
    results.append(("统一API", test_unified_api()))

    # 汇总结果
    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)

    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {test_name:<20} {status}")

    # 总体结果
    total = len(results)
    passed = sum(1 for _, r in results if r)
    print()
    print(f"总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n✓ 所有PDF生成器测试通过！")
        print("\n生成的PDF文件位于: src/test_output/")
        print("请手动对比生成的PDF与re目录下的样本PDF，确保格式一致。")
        return 0
    else:
        print("\n✗ 部分测试失败，请检查错误信息")
        return 1

if __name__ == '__main__':
    exit_code = main()

    print("\n按任意键退出...")
    try:
        input()
    except:
        pass

    sys.exit(exit_code)
