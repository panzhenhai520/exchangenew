# -*- coding: utf-8 -*-
"""
测试复选框显示
"""
import os
import sys

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.pdf.amlo_pdf_filler_overlay import AMLOPDFFillerOverlay

# 测试数据 - 包含多个复选框
test_data = {
    'fill_52': '001-001-68-110050USD',

    # 头部复选框
    'Check Box2': True,  # รายงานฉบับหลัก (原报告)
    'Check Box3': False,  # รายงานฉบับแกไข (修订报告)

    # 办理方式
    'Check Box4': True,  # ทำธุรกรรมด้วยตนเอง (本人办理)
    'Check Box5': False,  # ทำธุรกรรมแทนผู้อื่น (代理办理)

    # 证件类型
    'Check Box6': True,  # บัตรประจำตัวประชาชน (身份证)
    'Check Box7': False,  # หนังสือเดินทาง (护照)
    'Check Box8': False,  # ใบสำคัญประจำตัวคนต่างด้าว (外国人证)
    'Check Box9': False,  # อื่นๆ (其他)

    # 左栏交易类型
    'Check Box18': False,  # ฝากเงิน (存款)
    'Check Box19': False,  # ซื้อตราสารการเงิน (买票据)
    'Check Box20': False,  # เช็ค (支票)
    'Check Box21': False,  # ดราฟต์ (汇票)
    'Check Box22': False,  # อื่นๆ (其他票据)
    'Check Box23': True,   # ซื้อเงินตราต่างประเทศ (买入外币) ✓
    'Check Box24': False,  # อื่นๆ (其他)

    # 右栏交易类型
    'Check Box25': False,  # ถอนเงิน (取款)
    'Check Box26': False,  # ขายตราสารการเงิน (卖票据)
    'Check Box27': False,  # เช็ค (支票)
    'Check Box28': False,  # ดราฟต์ (汇票)
    'Check Box29': False,  # อื่นๆ (其他票据)
    'Check Box30': False,  # ขายเงินตราต่างประเทศ (卖出外币)
    'Check Box31': False,  # อื่นๆ (其他)

    # 底部复选框
    'Check Box32': False,  # สถาบันการเงินเป็นผู้บันทึกข้อเท็จจริง
    'Check Box33': False,  # ลูกค้าไม่ลงลายมือชื่อ

    # 一些文本字段用于参考定位
    'fill_4': '测试姓名',
    'fill_42': 'USD 155,500 (ธนบัตร)',
    'fill_48_5': '5027315.00',
    'fill_50': '5027315.00',
    'left_amount': 'ห้าล้านสองหมื่นเจ็ดพันสามร้อยสิบห้าบาทถ้วน',
}

print("=" * 80)
print("测试复选框显示")
print("=" * 80)

# 初始化填充器
filler = AMLOPDFFillerOverlay()

# 生成PDF
output_path = os.path.join(os.path.dirname(__file__), 'amlo_pdfs', 'test_checkbox.pdf')
try:
    result = filler.fill_form('AMLO-1-01', test_data, output_path)
    print(f"\n[SUCCESS] PDF generated: {result}")
    print("\n应该勾选的复选框:")
    print("  ✓ Check Box2 (รายงานฉบับหลัก - 原报告)")
    print("  ✓ Check Box4 (ทำธุรกรรมด้วยตนเอง - 本人办理)")
    print("  ✓ Check Box6 (บัตรประจำตัวประชาชน - 身份证)")
    print("  ✓ Check Box23 (ซื้อเงินตราต่างประเทศ - 买入外币)")
    print("\n请打开PDF检查这些复选框是否显示勾选标记。")
except Exception as e:
    print(f"\n[ERROR] Generation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("测试完成!")
print("=" * 80)
print(f"\nPDF位置: {output_path}")
