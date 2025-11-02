# -*- coding: utf-8 -*-
"""
验证AMLO问题修复
"""
import os
import sys

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.pdf.amlo_data_mapper import AMLODataMapper

mapper = AMLODataMapper()

output = []
output.append("=" * 80)
output.append("AMLO问题修复验证测试")
output.append("=" * 80)

# 测试场景1: 现金买入外币 - 验证问题修复
output.append("\n【测试1】现金买入外币 - 验证问题修复")
output.append("-" * 80)

transaction_data = {
    'direction': 'buy',
    'currency_code': 'USD',
    'amount': 155500,
    'amount_thb': 5027315,
    'local_amount': 5027315,
    'payment_method': 'cash'
}

form_data = {
    'payment_method': 'cash',
    'foreign_amount': 155500,
    'currency_code': 'USD',
}

result = mapper.map_reservation_to_pdf_fields('AMLO-1-01', transaction_data, form_data)

output.append("\n【问题1】Check Box2 (รายงานฉบับหลัก) 应该勾选")
output.append(f"  Check Box2: {result.get('Check Box2')}")
output.append(f"  ✓ 期望: True")
output.append(f"  {'✓ PASS' if result.get('Check Box2') == True else '✗ FAIL'}")

output.append("\n【问题2】Check Box18 (ฝากเงิน) 不应该勾选")
output.append(f"  Check Box18: {result.get('Check Box18')}")
output.append(f"  ✓ 期望: False")
output.append(f"  {'✓ PASS' if result.get('Check Box18') == False else '✗ FAIL'}")

output.append("\n【问题3】fill_45 (右栏อื่นๆ) 不应该填写金额")
output.append(f"  fill_45: '{result.get('fill_45')}'")
output.append(f"  ✓ 期望: 空字符串")
output.append(f"  {'✓ PASS' if result.get('fill_45') == '' else '✗ FAIL'}")

output.append("\n【问题4】右栏所有明细项应该为空")
output.append(f"  fill_49 (账号行): '{result.get('fill_49')}'")
output.append(f"    ✓ 期望: 空字符串")
output.append(f"    {'✓ PASS' if result.get('fill_49') == '' else '✗ FAIL'}")

output.append(f"  fill_49_1 (取款): '{result.get('fill_49_1')}'")
output.append(f"    ✓ 期望: 空字符串")
output.append(f"    {'✓ PASS' if result.get('fill_49_1') == '' else '✗ FAIL'}")

output.append(f"  fill_49_5 (卖外币): '{result.get('fill_49_5')}'")
output.append(f"    ✓ 期望: 空字符串")
output.append(f"    {'✓ PASS' if result.get('fill_49_5') == '' else '✗ FAIL'}")

output.append(f"  fill_51 (右栏合计): '{result.get('fill_51')}'")
output.append(f"    ✓ 期望: 0.00")
output.append(f"    {'✓ PASS' if result.get('fill_51') == '0.00' else '✗ FAIL'}")

output.append("\n【问题5】左栏应该正确填写")
output.append(f"  fill_48 (账号行): '{result.get('fill_48')}'")
output.append(f"    ✓ 期望: 空字符串")
output.append(f"    {'✓ PASS' if result.get('fill_48') == '' else '✗ FAIL'}")

output.append(f"  fill_48_5 (买外币): '{result.get('fill_48_5')}'")
output.append(f"    ✓ 期望: 5027315.00")
output.append(f"    {'✓ PASS' if result.get('fill_48_5') == '5027315.00' else '✗ FAIL'}")

output.append(f"  fill_50 (左栏合计): '{result.get('fill_50')}'")
output.append(f"    ✓ 期望: 5027315.00")
output.append(f"    {'✓ PASS' if result.get('fill_50') == '5027315.00' else '✗ FAIL'}")

output.append(f"  Check Box23 (ซื้อเงินตราต่างประเทศ): {result.get('Check Box23')}")
output.append(f"    ✓ 期望: True")
output.append(f"    {'✓ PASS' if result.get('Check Box23') == True else '✗ FAIL'}")

output.append(f"  fill_42 (币种描述): '{result.get('fill_42')}'")
output.append(f"    ✓ 期望包含: USD 155,500 (ธนบัตร)")
output.append(f"    {'✓ PASS' if 'USD' in result.get('fill_42', '') and 'ธนบัตร' in result.get('fill_42', '') else '✗ FAIL'}")

# 测试场景2: 现金卖出外币 - 验证对称逻辑
output.append("\n\n【测试2】现金卖出外币 - 验证对称逻辑")
output.append("-" * 80)

transaction_data['direction'] = 'sell'
transaction_data['amount'] = 150000
transaction_data['local_amount'] = 5250000
form_data['foreign_amount'] = 150000

result = mapper.map_reservation_to_pdf_fields('AMLO-1-01', transaction_data, form_data)

output.append("\n【对称性】左栏所有明细项应该为空")
output.append(f"  fill_48 (账号行): '{result.get('fill_48')}'")
output.append(f"    ✓ 期望: 空字符串")
output.append(f"    {'✓ PASS' if result.get('fill_48') == '' else '✗ FAIL'}")

output.append(f"  fill_48_1 (存款): '{result.get('fill_48_1')}'")
output.append(f"    ✓ 期望: 空字符串")
output.append(f"    {'✓ PASS' if result.get('fill_48_1') == '' else '✗ FAIL'}")

output.append(f"  fill_48_5 (买外币): '{result.get('fill_48_5')}'")
output.append(f"    ✓ 期望: 空字符串")
output.append(f"    {'✓ PASS' if result.get('fill_48_5') == '' else '✗ FAIL'}")

output.append(f"  fill_50 (左栏合计): '{result.get('fill_50')}'")
output.append(f"    ✓ 期望: 0.00")
output.append(f"    {'✓ PASS' if result.get('fill_50') == '0.00' else '✗ FAIL'}")

output.append("\n【对称性】右栏应该正确填写")
output.append(f"  fill_49 (账号行): '{result.get('fill_49')}'")
output.append(f"    ✓ 期望: 空字符串")
output.append(f"    {'✓ PASS' if result.get('fill_49') == '' else '✗ FAIL'}")

output.append(f"  fill_49_5 (卖外币): '{result.get('fill_49_5')}'")
output.append(f"    ✓ 期望: 5250000.00")
output.append(f"    {'✓ PASS' if result.get('fill_49_5') == '5250000.00' else '✗ FAIL'}")

output.append(f"  fill_51 (右栏合计): '{result.get('fill_51')}'")
output.append(f"    ✓ 期望: 5250000.00")
output.append(f"    {'✓ PASS' if result.get('fill_51') == '5250000.00' else '✗ FAIL'}")

output.append(f"  Check Box30 (ขายเงินตราต่างประเทศ): {result.get('Check Box30')}")
output.append(f"    ✓ 期望: True")
output.append(f"    {'✓ PASS' if result.get('Check Box30') == True else '✗ FAIL'}")

output.append(f"  fill_43 (币种描述): '{result.get('fill_43')}'")
output.append(f"    ✓ 期望包含: USD 150,000 (ธนบัตร)")
output.append(f"    {'✓ PASS' if 'USD' in result.get('fill_43', '') and 'ธนบัตร' in result.get('fill_43', '') else '✗ FAIL'}")

output.append("\n" + "=" * 80)
output.append("所有验证测试完成!")
output.append("=" * 80)

# 写入文件
with open('test_amlo_fix_results.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print("验证结果已保存到: test_amlo_fix_results.txt")
