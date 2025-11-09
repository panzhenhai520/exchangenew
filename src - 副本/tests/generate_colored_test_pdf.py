#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成带颜色标注的测试PDF
所有填充的数据用红色显示，方便对比
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime

# 注册泰文字体
font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'services', 'pdf', 'fonts', 'Sarabun-Regular.ttf')
pdfmetrics.registerFont(TTFont('Sarabun', font_path))

def generate_colored_test_pdf():
    """生成带颜色标注的测试PDF"""
    
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'manager', '2025', '10')
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, 'AMLO-1-01_COLORED_TEST.pdf')
    
    # 创建PDF
    c = canvas.Canvas(output_file, pagesize=A4)
    width, height = A4
    
    # 测试数据
    test_data = {
        'report_no': 'TEST-2025-1011-999',
        'report_date': '11/10/2025',
        'customer_name': '测试客户张三',
        'customer_id': 'TEST123456789',
        'occupation': 'นักธุรกิจ (Businessman)',
        'address': '曼谷素坤逸路123号',
        'phone': '0861234567890',
        'nationality': 'CHN',
        'transaction_date': '10/10/2025',
        'currency': 'USD',
        'foreign_amount': 75000.00,
        'exchange_rate': 35.50,
        'thb_amount': 2662500.00,
        'purpose': 'เดินทาง/ท่องเที่ยว (Travel)',
        'funding_source': 'เงินเดือน (Salary)',
        'remarks': '测试字段映射'
    }
    
    # 标题（黑色）
    c.setFont('Sarabun', 16)
    c.setFillColorRGB(0, 0, 0)
    c.drawCentredString(width/2, height - 40*mm, 'รายงาน ปปง. ๑-๐๑')
    c.drawCentredString(width/2, height - 50*mm, 'AMLO-1-01 测试报告（红色=填充数据）')
    
    # 说明
    c.setFont('Sarabun', 10)
    c.drawCentredString(width/2, height - 60*mm, '黑色=标签，红色=填充的数据')
    
    y_pos = height - 80*mm
    x_left = 30*mm
    
    # ส่วนที่ ๑ - 客户信息
    c.setFont('Sarabun', 14)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(x_left, y_pos, 'ส่วนที่ ๑ - ข้อมูลลูกค้า (客户信息)')
    y_pos -= 10*mm
    
    # 绘制字段（标签黑色，数据红色）
    fields_section1 = [
        ('ชื่อ (Name):', test_data['customer_name']),
        ('เลขประจำตัว (ID):', test_data['customer_id']),
        ('อาชีพ (Occupation):', test_data['occupation']),
        ('ที่อยู่ (Address):', test_data['address']),
        ('โทรศัพท์ (Phone):', test_data['phone']),
        ('สัญชาติ (Nationality):', test_data['nationality'])
    ]
    
    c.setFont('Sarabun', 11)
    for label, value in fields_section1:
        # 标签（黑色）
        c.setFillColorRGB(0, 0, 0)
        c.drawString(x_left, y_pos, label)
        
        # 数据（红色）
        c.setFillColorRGB(1, 0, 0)  # 红色
        c.drawString(x_left + 60*mm, y_pos, str(value))
        
        y_pos -= 7*mm
    
    # ส่วนที่ ๒ - 交易信息
    y_pos -= 5*mm
    c.setFont('Sarabun', 14)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(x_left, y_pos, 'ส่วนที่ ๒ - ข้อมูลธุรกรรม (交易信息)')
    y_pos -= 10*mm
    
    fields_section2 = [
        ('วันที่ (Date):', test_data['transaction_date']),
        ('สกุลเงิน (Currency):', test_data['currency']),
        ('จำนวนเงินตราต่างประเทศ (Foreign Amount):', f"{test_data['foreign_amount']:,.2f}"),
        ('อัตราแลกเปลี่ยน (Exchange Rate):', f"{test_data['exchange_rate']:.4f}"),
        ('จำนวนเงินบาท (THB Amount):', f"{test_data['thb_amount']:,.2f}")
    ]
    
    c.setFont('Sarabun', 11)
    for label, value in fields_section2:
        c.setFillColorRGB(0, 0, 0)
        c.drawString(x_left, y_pos, label)
        
        c.setFillColorRGB(1, 0, 0)  # 红色
        c.drawString(x_left + 80*mm, y_pos, str(value))
        
        y_pos -= 7*mm
    
    # ส่วนที่ ๓ - 用途和资金来源
    y_pos -= 5*mm
    c.setFont('Sarabun', 14)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(x_left, y_pos, 'ส่วนที่ ๓ - วัตถุประสงค์และแหล่งเงิน (用途和资金)')
    y_pos -= 10*mm
    
    fields_section3 = [
        ('วัตถุประสงค์ (Purpose):', test_data['purpose']),
        ('แหล่งที่มาของเงิน (Funding Source):', test_data['funding_source']),
        ('หมายเหตุ (Remarks):', test_data['remarks'])
    ]
    
    c.setFont('Sarabun', 11)
    for label, value in fields_section3:
        c.setFillColorRGB(0, 0, 0)
        c.drawString(x_left, y_pos, label)
        
        c.setFillColorRGB(1, 0, 0)  # 红色
        c.drawString(x_left + 80*mm, y_pos, str(value))
        
        y_pos -= 7*mm
    
    # 页脚说明
    c.setFont('Sarabun', 10)
    c.setFillColorRGB(0, 0, 1)  # 蓝色
    c.drawCentredString(width/2, 30*mm, '此PDF用于测试字段映射，红色文字为填充的数据')
    c.drawCentredString(width/2, 25*mm, '请对比样本PDF，检查数据是否在正确位置显示')
    
    # 保存
    c.save()
    
    print("="*80)
    print("带颜色标注的测试PDF生成完成")
    print("="*80)
    
    print(f"\n文件位置: {os.path.abspath(output_file)}")
    print(f"文件大小: {os.path.getsize(output_file) / 1024:.2f} KB")
    
    print(f"\n颜色说明:")
    print(f"  - 黑色: 字段标签（泰文+中文）")
    print(f"  - 红色: 填充的数据 ← 这些是表单输入的内容")
    print(f"  - 蓝色: 说明文字")
    
    print(f"\n请打开此文件，您将清楚看到:")
    print(f"  1. 哪些数据被填充了（红色）")
    print(f"  2. 数据的位置和布局")
    print(f"  3. 与样本PDF的差异")
    
    return output_file

if __name__ == "__main__":
    output = generate_colored_test_pdf()
    
    print("\n" + "="*80)
    print("下一步")
    print("="*80)
    print(f"\n1. 打开生成的PDF: {output}")
    print(f"2. 对比样本PDF")
    print(f"3. 告诉我您看到的差异")
    print(f"4. 我将实现1:1复刻")

