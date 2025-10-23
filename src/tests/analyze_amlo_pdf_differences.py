#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析AMLO PDF样本 vs 当前生成的PDF
找出格式差异，提供1:1复刻方案
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("="*80)
print("AMLO PDF格式分析和1:1复刻方案")
print("="*80)

# 样本文件位置
sample_dir = r"D:\Code\ExchangeNew\Re"
samples = [
    "รายงาน ปปง 1-01 ซื้อขายเกิน 500,000 บาท ยกเว้นเงินบาทแลก.pdf",
    "รายงาน ปปง 1-02 ซื้อขายเกิน 800,000 บาท ยกเว้นเงินบาทแลก.pdf",
    "รายงาน ปปง 1-03  ซื้อขายระหว่างนิติบุคลล.pdf"
]

print("\n[1] 样本文件位置:")
print("-"*80)
for sample in samples:
    filepath = os.path.join(sample_dir, sample)
    if os.path.exists(filepath):
        size = os.path.getsize(filepath) / 1024
        print(f"  [OK] {sample}")
        print(f"       大小: {size:.2f} KB")
    else:
        print(f"  [ERROR] 文件不存在: {sample}")

# 当前生成的文件
print("\n[2] 当前生成的PDF文件:")
print("-"*80)

import glob
generated_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'manager', '2025', '10')
generated_pdfs = glob.glob(os.path.join(generated_dir, "AMLO*.pdf"))

if generated_pdfs:
    print(f"  找到 {len(generated_pdfs)} 个生成的AMLO PDF:")
    for pdf in generated_pdfs[:5]:
        size = os.path.getsize(pdf) / 1024
        print(f"  - {os.path.basename(pdf)} ({size:.2f} KB)")
    if len(generated_pdfs) > 5:
        print(f"  ... 还有 {len(generated_pdfs) - 5} 个文件")
else:
    print("  [ERROR] 未找到生成的PDF")

print("\n[3] PDF生成器代码位置:")
print("-"*80)

generators = [
    "src/services/pdf/amlo_pdf_generator.py",
    "src/services/pdf/amlo_pdf_generator_v2.py",
    "src/services/pdf/amlo_pdf_generator_precise.py",
    "src/services/pdf/amlo_101_final.py",
    "src/services/pdf/amlo_101_from_config.py"
]

for gen in generators:
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', gen)
    if os.path.exists(filepath):
        size = os.path.getsize(filepath) / 1024
        print(f"  [OK] {os.path.basename(gen)} ({size:.2f} KB)")
    else:
        print(f"  [SKIP] {os.path.basename(gen)} (不存在)")

print("\n[4] PDF 1:1复刻方案评估:")
print("-"*80)

print("""
方案A: 基于PDF模板 (类似BOT Excel)
  原理: 使用PyPDF2/pypdf打开样本PDF，填充文本字段
  优点: 
    - [OK] 格式100%一致
    - [OK] 无需手动绘制布局
    - [OK] 样本更新时自动同步
  缺点:
    - [WARN] 需要样本PDF有可填充字段（Form Fields）
    - [WARN] 泰文PDF可能没有表单字段
  可行性: ⚠️ 需要检查样本PDF是否有表单字段

方案B: 精确ReportLab绘制
  原理: 使用ReportLab，精确测量样本PDF的每个元素位置
  优点:
    - [OK] 完全可控
    - [OK] 不依赖样本结构
    - [OK] 可以精确复刻
  缺点:
    - [WARN] 需要大量测量和调整
    - [WARN] 维护成本高
  可行性: ✅ 可行，需要时间

方案C: HTML转PDF (推荐)
  原理: 创建HTML模板，使用weasyprint或pdfkit转为PDF
  优点:
    - [OK] 样式用CSS控制，易于调整
    - [OK] 可以精确复刻布局
    - [OK] 维护简单
    - [OK] 支持多语言
  缺点:
    - [INFO] 需要安装额外依赖
  可行性: ✅ 推荐方案

方案D: 使用现有PDF作为背景 + 填充数据
  原理: 将样本PDF作为背景图，在上面绘制文本
  优点:
    - [OK] 格式100%匹配
    - [OK] 只需要定位数据位置
  缺点:
    - [WARN] 每次都需要加载背景PDF
    - [INFO] 文件体积较大
  可行性: ✅ 可行，简单有效
""")

print("\n[5] 推荐实施方案:")
print("-"*80)
print("""
最佳方案: 方案D（PDF背景 + 数据填充）

实施步骤:
1. 将样本PDF转换为背景图片或直接使用
2. 使用PyPDF2或reportlab在样本PDF上叠加文本
3. 只需要精确定位每个数据字段的坐标
4. 保持样本的所有格式、样式、泰文字体

优势:
- 最快实现（1-2小时）
- 格式100%一致
- 维护简单
- 不影响现有功能
""")

print("\n[6] 表单字段映射测试准备:")
print("-"*80)
print("""
需要验证的映射:

预约表单字段 → PDF显示位置
├─ customer_name (客户姓名) → PDF ส่วนที่ ๑ / 姓名栏
├─ customer_id (证件号) → PDF ส่วนที่ ๑ / 证件号栏
├─ occupation (职业) → PDF ส่วนที่ ๑ / 职业栏
├─ address (地址) → PDF ส่วนที่ ๑ / 地址栏
├─ phone (电话) → PDF ส่วนที่ ๑ / 电话栏
├─ nationality (国籍) → PDF ส่วนที่ ๑ / 国籍栏
├─ transaction_date (交易日期) → PDF ส่วนที่ ๒ / 日期栏
├─ transaction_type (交易类型) → PDF ส่วนที่ ๒ / 存款/提款复选框
├─ currency (币种) → PDF ส่วนที่ ๒ / 币种栏
├─ foreign_amount (外币金额) → PDF ส่วนที่ ๒ / 金额栏
├─ exchange_rate (汇率) → PDF ส่วนที่ ๒ / 汇率栏
├─ thb_amount (泰铢金额) → PDF ส่วนที่ ๒ / 泰铢金额栏
├─ purpose (用途) → PDF ส่วนที่ ๓ / 用途栏
├─ funding_source (资金来源) → PDF ส่วนที่ ๓ / 资金来源栏
└─ remarks (备注) → PDF ส่วนที่ ๓ / 备注栏

测试方法:
1. 使用测试数据填写预约表单
2. 生成PDF
3. 打开PDF人工核对每个字段
4. 记录缺失或位置错误的字段
""")

print("\n" + "="*80)
print("分析完成")
print("="*80)
print("\n下一步:")
print("  1. 人工打开样本PDF和生成的PDF对比")
print("  2. 记录具体差异点")
print("  3. 选择实施方案")
print("  4. 实现1:1复刻")

