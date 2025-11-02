# -*- coding: utf-8 -*-
"""
测试AMLO报告填写规则，输出到文件
"""
import os
import sys

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.pdf.amlo_data_mapper import AMLODataMapper

mapper = AMLODataMapper()

output = []
output.append("=" * 80)
output.append("AMLO填写规则验证测试")
output.append("=" * 80)

# 测试场景1: 现金买入外币
output.append("\n【测试1】现金买入外币 (Cash Buy FX)")
output.append("-" * 80)

transaction_data = {
    'direction': 'buy',
    'currency_code': 'USD',
    'amount': 160000,
    'amount_thb': 5600000,
    'local_amount': 5600000,
    'payment_method': 'cash'
}

form_data = {
    'payment_method': 'cash',
    'foreign_amount': 160000,
    'currency_code': 'USD',
}

result = mapper.map_reservation_to_pdf_fields('AMLO-1-01', transaction_data, form_data)

output.append(f"fill_42 (买入外币描述): {result.get('fill_42')}")
output.append(f"  期望包含: USD 160,000 (ธนบัตร)")
output.append(f"  包含现金标注: {'ธนบัตร' in result.get('fill_42', '')}")

output.append(f"\nfill_48 (账号行金额): '{result.get('fill_48')}'")
output.append(f"  期望: 空字符串")
output.append(f"  正确: {result.get('fill_48') == ''}")

output.append(f"\nfill_48_5 (买入外币金额行): {result.get('fill_48_5')}")
output.append(f"  期望: 5600000.00")
output.append(f"  正确: {result.get('fill_48_5') == '5600000.00'}")

output.append(f"\ncomb_3 (账号): '{result.get('comb_3')}'")
output.append(f"  期望: 空字符串 (现金交易)")
output.append(f"  正确: {result.get('comb_3') == ''}")

# 测试场景2: 转账买入外币
output.append("\n\n【测试2】转账买入外币 (Transfer Buy FX)")
output.append("-" * 80)

transaction_data['payment_method'] = 'transfer'
form_data['payment_method'] = 'transfer'
form_data['account_number'] = '88888888'
form_data['related_account'] = '1234567890'

result = mapper.map_reservation_to_pdf_fields('AMLO-1-01', transaction_data, form_data)

output.append(f"fill_42 (买入外币描述): {result.get('fill_42')}")
output.append(f"  期望包含: USD 160,000 (โอน)")
output.append(f"  包含转账标注: {'โอน' in result.get('fill_42', '')}")

output.append(f"\ncomb_3 (机构账号): {result.get('comb_3')}")
output.append(f"  期望: 88888888")
output.append(f"  正确: {result.get('comb_3') == '88888888'}")

output.append(f"\ncomb_5 (客户支付账号): {result.get('comb_5')}")
output.append(f"  期望: 1234567890")
output.append(f"  正确: {result.get('comb_5') == '1234567890'}")

# 测试场景3: 现金卖出外币
output.append("\n\n【测试3】现金卖出外币 (Cash Sell FX)")
output.append("-" * 80)

transaction_data['direction'] = 'sell'
transaction_data['payment_method'] = 'cash'
transaction_data['amount'] = 150000
transaction_data['local_amount'] = 5250000
form_data['payment_method'] = 'cash'
form_data['foreign_amount'] = 150000
form_data.pop('account_number', None)
form_data.pop('related_account', None)

result = mapper.map_reservation_to_pdf_fields('AMLO-1-01', transaction_data, form_data)

output.append(f"fill_43 (卖出外币描述): {result.get('fill_43')}")
output.append(f"  期望包含: USD 150,000 (ธนบัตร)")
output.append(f"  包含现金标注: {'ธนบัตร' in result.get('fill_43', '')}")

output.append(f"\nfill_49 (账号行金额): '{result.get('fill_49')}'")
output.append(f"  期望: 空字符串")
output.append(f"  正确: {result.get('fill_49') == ''}")

output.append(f"\nfill_49_5 (卖出外币金额行): {result.get('fill_49_5')}")
output.append(f"  期望: 5250000.00")
output.append(f"  正确: {result.get('fill_49_5') == '5250000.00'}")

output.append(f"\ncomb_4 (账号): '{result.get('comb_4')}'")
output.append(f"  期望: 空字符串 (现金交易)")
output.append(f"  正确: {result.get('comb_4') == ''}")

# 测试场景4: 转账卖出外币
output.append("\n\n【测试4】转账卖出外币 (Transfer Sell FX)")
output.append("-" * 80)

transaction_data['payment_method'] = 'transfer'
form_data['payment_method'] = 'transfer'
form_data['payout_account_number'] = '99999999'
form_data['payout_related_account'] = '0987654321'

result = mapper.map_reservation_to_pdf_fields('AMLO-1-01', transaction_data, form_data)

output.append(f"fill_43 (卖出外币描述): {result.get('fill_43')}")
output.append(f"  期望包含: USD 150,000 (โอน)")
output.append(f"  包含转账标注: {'โอน' in result.get('fill_43', '')}")

output.append(f"\ncomb_4 (机构账号): {result.get('comb_4')}")
output.append(f"  期望: 99999999")
output.append(f"  正确: {result.get('comb_4') == '99999999'}")

output.append(f"\ncomb_6 (客户收款账号): {result.get('comb_6')}")
output.append(f"  期望: 0987654321")
output.append(f"  正确: {result.get('comb_6') == '0987654321'}")

output.append("\n" + "=" * 80)
output.append("测试完成!")
output.append("=" * 80)

# 写入文件
with open('test_amlo_results.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print("测试结果已保存到: test_amlo_results.txt")
