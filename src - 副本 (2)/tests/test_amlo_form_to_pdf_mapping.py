#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AMLO预约表单字段到PDF的映射
验证表单填写的内容是否正确显示在PDF上
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from services.db_service import DatabaseService
from services.pdf.amlo_pdf_generator import AMLOPDFGenerator
from sqlalchemy import text
from datetime import datetime, date
import json

def test_form_to_pdf_mapping():
    """测试表单字段到PDF的映射"""
    
    print("="*80)
    print("AMLO表单字段→PDF映射测试")
    print("="*80)
    
    # 准备完整的测试数据
    test_data = {
        # PDF基本信息
        'report_no': 'TEST-2025-1011-999',
        'report_date': '11/10/2025',
        
        # ส่วนที่ ๑ - 客户信息（来自预约表单）
        'customer_name': '测试客户张三 (Test Customer Zhang San)',
        'customer_id': 'TEST123456789',
        'customer_id_type': 'Passport',
        'nationality': 'CHN',
        'occupation': 'นักธุรกิจ / Businessman / 商人',
        'address': '曼谷素坤逸路123号 / 123 Sukhumvit Rd, Bangkok',
        'phone': '0861234567890',
        
        # ส่วนที่ ๒ - 交易信息
        'transaction_date': '10/10/2025',
        'transaction_type': '买入外币 / Buy Foreign Currency',
        'currency': 'USD',
        'foreign_amount': 75000.00,
        'exchange_rate': 35.50,
        'thb_amount': 2662500.00,
        
        # ส่วนที่ ๓ - 用途和资金来源（来自预约表单）
        'purpose': 'เดินทาง/ท่องเที่ยว / Travel / 旅游支出',
        'funding_source': 'เงินเดือน / Salary / 工资收入',
        'remarks': '测试AMLO-1-01报告字段映射 / Test field mapping'
    }
    
    print("\n[1] 测试数据准备:")
    print("-"*80)
    print("表单字段及其值:")
    print(json.dumps(test_data, indent=2, ensure_ascii=False))
    
    # 生成测试PDF
    print("\n[2] 生成测试PDF:")
    print("-"*80)
    
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'manager', '2025', '10')
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, 'AMLO-1-01_FIELD_MAPPING_TEST.pdf')
    
    try:
        generator = AMLOPDFGenerator()
        result_path = generator.generate_pdf('AMLO-1-01', test_data, output_file)
        
        file_size = os.path.getsize(result_path)
        
        print(f"[OK] PDF生成成功!")
        print(f"  文件: {os.path.basename(result_path)}")
        print(f"  路径: {os.path.abspath(result_path)}")
        print(f"  大小: {file_size / 1024:.2f} KB")
        
    except Exception as e:
        print(f"[ERROR] PDF生成失败: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # 字段映射检查清单
    print("\n[3] 字段映射检查清单:")
    print("-"*80)
    print("""
请打开生成的PDF，逐一检查以下字段是否正确显示：

ส่วนที่ ๑ (客户信息部分):
  [ ] 客户姓名: "测试客户张三 (Test Customer Zhang San)"
  [ ] 证件号码: "TEST123456789"
  [ ] 证件类型: "Passport" 或对应的泰文
  [ ] 国籍: "CHN" 或 "中国"
  [ ] 职业: "นักธุรกิจ / Businessman / 商人"
  [ ] 地址: "曼谷素坤逸路123号 / 123 Sukhumvit Rd, Bangkok"
  [ ] 电话: "0861234567890"

ส่วนที่ ๒ (交易信息部分):
  [ ] 交易日期: "10/10/2025"
  [ ] 交易类型: "买入外币" 对应的复选框是否勾选
  [ ] 币种: "USD"
  [ ] 外币金额: "75,000.00"
  [ ] 汇率: "35.50"
  [ ] 泰铢金额: "2,662,500.00"

ส่วนที่ ๓ (用途和资金来源):
  [ ] 用途: "เดินทาง/ท่องเที่ยว / Travel / 旅游支出"
  [ ] 资金来源: "เงินเดือน / Salary / 工资收入"
  [ ] 备注: "测试AMLO-1-01报告字段映射 / Test field mapping"

其他:
  [ ] 报告编号: "TEST-2025-1011-999" 是否显示
  [ ] 报告日期: "11/10/2025" 是否显示
  [ ] 表单编号: "แบบ ปปง. ๑-๐๑" 是否显示
  [ ] 泰文标题是否正确
  [ ] 页面布局是否与样本一致
    """)
    
    # 对比大小
    print("\n[4] 文件大小对比:")
    print("-"*80)
    
    sample_file = os.path.join(
        r"D:\Code\ExchangeNew\Re",
        "รายงาน ปปง 1-01 ซื้อขายเกิน 500,000 บาท ยกเว้นเงินบาทแลก.pdf"
    )
    
    if os.path.exists(sample_file):
        sample_size = os.path.getsize(sample_file) / 1024
        generated_size = file_size / 1024
        
        print(f"  样本PDF: {sample_size:.2f} KB")
        print(f"  生成PDF: {generated_size:.2f} KB")
        print(f"  大小差异: {sample_size - generated_size:.2f} KB ({(1 - generated_size/sample_size)*100:.1f}% 更小)")
        
        if generated_size < sample_size * 0.5:
            print(f"\n  [WARN] 生成的PDF比样本小很多，可能缺少内容或格式元素")
            print(f"  [建议] 检查是否缺少：")
            print(f"    - 表格边框")
            print(f"    - 背景图案")
            print(f"    - 说明文字")
            print(f"    - 页眉页脚")
    
    # 打开文件对比
    print("\n[5] 打开文件进行对比:")
    print("-"*80)
    print(f"\n  样本PDF: {sample_file}")
    print(f"  生成PDF: {result_path}")
    print(f"\n  执行以下命令打开文件:")
    print(f'  explorer "{os.path.dirname(result_path)}"')
    
    return result_path

if __name__ == "__main__":
    result = test_form_to_pdf_mapping()
    
    if result:
        print("\n" + "="*80)
        print("测试完成")
        print("="*80)
        print(f"\n请人工打开PDF文件核对字段映射")
        print(f"记录缺失或位置错误的字段")
        print(f"然后决定使用哪个方案实现1:1复刻")

