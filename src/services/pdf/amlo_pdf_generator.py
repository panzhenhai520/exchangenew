# -*- coding: utf-8 -*-
"""
AMLO PDF生成器
用于生成符合泰国反洗钱办公室(AMLO)要求的PDF报告
严格按照re目录下的PDF样本格式生成

支持的报告类型:
- AMLO-1-01: 现金交易报告 (≥500,000泰铢)
- AMLO-1-02: 资产交易报告 (≥8,000,000泰铢)
- AMLO-1-03: 可疑交易报告
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import black
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from datetime import datetime
import os
from typing import Dict, List, Optional, Tuple

# A4页面尺寸 (宽 x 高)
PAGE_WIDTH, PAGE_HEIGHT = A4  # 210mm x 297mm

# 字体配置
FONT_NAME_TH = 'Sarabun'  # 泰语字体
FONT_NAME_EN = 'Helvetica'  # 英文字体
FONT_SIZE_TITLE = 14
FONT_SIZE_SECTION = 12
FONT_SIZE_NORMAL = 10
FONT_SIZE_SMALL = 8

# 边距设置 (单位: mm)
MARGIN_LEFT = 20
MARGIN_RIGHT = 20
MARGIN_TOP = 20
MARGIN_BOTTOM = 20

# 复选框样式
CHECKBOX_SIZE = 3 * mm
CHECKBOX_CHAR = '□'
CHECKBOX_CHECKED = '☑'

class AMLOPDFGenerator:
    """AMLO PDF报告生成器基类"""

    def __init__(self):
        """初始化PDF生成器"""
        self.thai_font_available = self._register_fonts()

        # 如果泰语字体不可用，使用Helvetica作为后备
        if not self.thai_font_available:
            global FONT_NAME_TH
            FONT_NAME_TH = 'Helvetica'

    def _register_fonts(self):
        """注册泰语字体

        Returns:
            bool: 字体注册成功返回True，否则返回False
        """
        try:
            # 尝试注册Sarabun字体（如果存在）
            font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'Sarabun-Regular.ttf')
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('Sarabun', font_path))

                # 注册粗体版本
                font_bold_path = os.path.join(os.path.dirname(__file__), 'fonts', 'Sarabun-Bold.ttf')
                if os.path.exists(font_bold_path):
                    pdfmetrics.registerFont(TTFont('Sarabun-Bold', font_bold_path))

                print("[OK] Thai font registered successfully")
                return True
            else:
                print("WARNING: Thai font file not found, using default Helvetica font")
                print(f"  Expected path: {font_path}")
                print("  Thai text may not display correctly")
                return False
        except Exception as e:
            print(f"WARNING: Thai font registration failed - {str(e)}")
            print("Using default Helvetica font, Thai text may not display correctly")
            return False

    def _draw_triple_border(self, c: canvas.Canvas):
        """绘制三层边框（外细-中粗-内细）

        标准报告的边框结构:
        - 外层: 1磅细线
        - 中层: 3磅粗线 (主边框)
        - 内层: 0.5磅细线
        """
        # 定义边距
        outer_margin = 5*mm
        middle_margin = 7*mm
        inner_margin = 9*mm

        # 外层细边框 (1磅)
        c.saveState()
        c.setLineWidth(1)
        c.setStrokeColorRGB(0, 0, 0)
        c.rect(outer_margin, outer_margin,
               PAGE_WIDTH - 2*outer_margin,
               PAGE_HEIGHT - 2*outer_margin)

        # 中层粗边框 (3磅) - 主边框
        c.setLineWidth(3)
        c.rect(middle_margin, middle_margin,
               PAGE_WIDTH - 2*middle_margin,
               PAGE_HEIGHT - 2*middle_margin)

        # 内层细边框 (0.5磅)
        c.setLineWidth(0.5)
        c.rect(inner_margin, inner_margin,
               PAGE_WIDTH - 2*inner_margin,
               PAGE_HEIGHT - 2*inner_margin)

        c.restoreState()

    def _draw_checkbox(self, c: canvas.Canvas, x: float, y: float, checked: bool = False,
                      label: str = '', label_offset: float = 5*mm):
        """绘制复选框

        Args:
            c: Canvas对象
            x: X坐标
            y: Y坐标
            checked: 是否选中
            label: 标签文本
            label_offset: 标签偏移量
        """
        # 绘制方框
        c.rect(x, y, CHECKBOX_SIZE, CHECKBOX_SIZE)

        # 如果选中，绘制勾选标记
        if checked:
            c.setFont(FONT_NAME_EN, FONT_SIZE_NORMAL)
            c.drawString(x + 0.5*mm, y + 0.5*mm, '✓')

        # 绘制标签
        if label:
            c.setFont(FONT_NAME_TH, FONT_SIZE_NORMAL)
            c.drawString(x + label_offset, y, label)

    def _draw_underline(self, c: canvas.Canvas, x: float, y: float, width: float,
                       text: str = '', text_offset: float = 2*mm):
        """绘制下划线填空字段

        Args:
            c: Canvas对象
            x: X坐标
            y: Y坐标
            width: 下划线宽度
            text: 填充文本
            text_offset: 文本垂直偏移
        """
        # 绘制下划线
        c.line(x, y, x + width, y)

        # 绘制文本
        if text:
            c.setFont(FONT_NAME_TH, FONT_SIZE_NORMAL)
            c.drawString(x + 2*mm, y + text_offset, text)

    def _draw_id_boxes(self, c: canvas.Canvas, x: float, y: float, id_number: str = '',
                      box_count: int = 13):
        """绘制身份证号码格式的方框

        Args:
            c: Canvas对象
            x: X坐标
            y: Y坐标
            id_number: 身份证号码
            box_count: 方框数量（默认13位）
        """
        box_size = 6 * mm  # 增大方格尺寸
        box_gap = 1 * mm

        # 保存当前颜色状态
        c.saveState()

        for i in range(box_count):
            # 绘制方框
            c.setStrokeColorRGB(0, 0, 0)  # 黑色边框
            c.setFillColorRGB(1, 1, 1)    # 白色填充
            c.rect(x + i * (box_size + box_gap), y, box_size, box_size, stroke=1, fill=1)

            # 填充数字（如果有）
            if id_number and i < len(id_number):
                c.setFillColorRGB(0, 0, 0)  # 黑色文字
                c.setFont(FONT_NAME_EN, 9)  # 使用固定大小
                # 居中绘制数字
                c.drawCentredString(
                    x + i * (box_size + box_gap) + box_size/2,
                    y + 1.5*mm,
                    str(id_number[i])  # 确保转换为字符串
                )

        c.restoreState()

    def _draw_table(self, c: canvas.Canvas, data: List[List[str]], x: float, y: float,
                   col_widths: List[float], row_height: float = 8*mm):
        """绘制表格

        Args:
            c: Canvas对象
            data: 表格数据（二维列表）
            x: X坐标
            y: Y坐标（左上角）
            col_widths: 列宽列表
            row_height: 行高
        """
        current_y = y

        for row_idx, row_data in enumerate(data):
            current_x = x

            for col_idx, cell_text in enumerate(row_data):
                # 绘制单元格边框
                c.rect(current_x, current_y - row_height, col_widths[col_idx], row_height)

                # 绘制单元格文本（居中）
                c.setFont(FONT_NAME_TH, FONT_SIZE_SMALL)
                c.drawCentredString(
                    current_x + col_widths[col_idx]/2,
                    current_y - row_height/2 - 1*mm,
                    cell_text
                )

                current_x += col_widths[col_idx]

            current_y -= row_height

    def _draw_report_number_box(self, c: canvas.Canvas, report_number: str = ''):
        """绘制右上角报告编号框

        Args:
            c: Canvas对象
            report_number: 报告编号
        """
        box_x = PAGE_WIDTH - MARGIN_RIGHT*mm - 50*mm
        box_y = PAGE_HEIGHT - MARGIN_TOP*mm - 20*mm
        box_width = 50*mm
        box_height = 15*mm

        # 绘制外框
        c.rect(box_x, box_y, box_width, box_height)

        # 绘制标题
        c.setFont(FONT_NAME_TH, FONT_SIZE_SMALL)
        c.drawCentredString(box_x + box_width/2, box_y + box_height - 5*mm, 'เลขที่รายงาน')

        # 绘制编号
        c.setFont(FONT_NAME_EN, FONT_SIZE_NORMAL)
        c.drawCentredString(box_x + box_width/2, box_y + 5*mm, report_number)

    def _draw_footer_disclaimer(self, c: canvas.Canvas, page_num: int = 2):
        """绘制第2页的法律声明

        Args:
            c: Canvas对象
            page_num: 页码
        """
        if page_num != 2:
            return

        disclaimer_text = [
            "หมายเหตุ:",
            "๑. ให้กรอกข้อความในแบบรายงานให้ครบถ้วนและชัดเจน",
            "๒. ให้ส่งแบบรายงานภายในเวลาที่กฎหมายกำหนด",
            "๓. การรายงานข้อมูลเท็จอาจมีความผิดตามกฎหมาย"
        ]

        c.setFont(FONT_NAME_TH, FONT_SIZE_SMALL)
        y_position = MARGIN_BOTTOM*mm + 20*mm

        for text in disclaimer_text:
            c.drawString(MARGIN_LEFT*mm, y_position, text)
            y_position -= 5*mm

    def generate_amlo_101(self, data: Dict, output_path: str) -> str:
        """生成AMLO-1-01现金交易报告

        Args:
            data: 报告数据字典
            output_path: 输出文件路径

        Returns:
            生成的PDF文件路径
        """
        c = canvas.Canvas(output_path, pagesize=A4)

        # ========== 第1页 ==========

        # 绘制三层边框
        self._draw_triple_border(c)

        # 绘制报告编号框
        self._draw_report_number_box(c, data.get('report_number', ''))

        # 标题
        c.setFont(FONT_NAME_TH, FONT_SIZE_TITLE)
        c.drawCentredString(PAGE_WIDTH/2, PAGE_HEIGHT - 30*mm,
                           'แบบรายงานการทำธุรกรรมที่ใช้เงินสด')

        # 副标题
        c.setFont(FONT_NAME_TH, FONT_SIZE_NORMAL)
        c.drawCentredString(PAGE_WIDTH/2, PAGE_HEIGHT - 38*mm,
                           'ตามมาตรา ๑๓ แห่งพระราชบัญญัติป้องกันและปราบปรามการฟอกเงิน พ.ศ. ๒๕๔๒')

        # 报告类型复选框
        y_pos = PAGE_HEIGHT - 48*mm
        self._draw_checkbox(c, MARGIN_LEFT*mm, y_pos,
                           checked=data.get('is_amendment', False) == False,
                           label='รายงานฉบับแรก', label_offset=6*mm)
        self._draw_checkbox(c, MARGIN_LEFT*mm + 50*mm, y_pos,
                           checked=data.get('is_amendment', False) == True,
                           label='รายงานฉบับแก้ไข', label_offset=6*mm)

        # ส่วนที่ 1: ผู้ทำธุรกรรม
        y_pos -= 10*mm
        c.setFont(FONT_NAME_TH, FONT_SIZE_SECTION)
        c.drawString(MARGIN_LEFT*mm, y_pos, 'ส่วนที่ ๑ ผู้ทำธุรกรรม')

        # 交易者类型
        y_pos -= 8*mm
        self._draw_checkbox(c, MARGIN_LEFT*mm, y_pos,
                           checked=data.get('maker_type') == 'person',
                           label='บุคคลธรรมดา', label_offset=6*mm)
        self._draw_checkbox(c, MARGIN_LEFT*mm + 50*mm, y_pos,
                           checked=data.get('maker_type') == 'company',
                           label='นิติบุคคล', label_offset=6*mm)

        # 姓名字段
        y_pos -= 10*mm
        c.setFont(FONT_NAME_TH, FONT_SIZE_NORMAL)
        c.drawString(MARGIN_LEFT*mm, y_pos, 'ชื่อ-นามสกุล/ชื่อนิติบุคคล')
        self._draw_underline(c, MARGIN_LEFT*mm + 50*mm, y_pos - 2*mm, 100*mm,
                            text=data.get('maker_name', ''))

        # 身份证号码
        y_pos -= 10*mm
        c.drawString(MARGIN_LEFT*mm, y_pos, 'เลขประจำตัวประชาชน/เลขทะเบียนนิติบุคคล')
        self._draw_id_boxes(c, MARGIN_LEFT*mm + 70*mm, y_pos - 2*mm,
                           id_number=data.get('maker_id', ''))

        # 地址
        y_pos -= 10*mm
        c.drawString(MARGIN_LEFT*mm, y_pos, 'ที่อยู่')
        self._draw_underline(c, MARGIN_LEFT*mm + 20*mm, y_pos - 2*mm, 130*mm,
                            text=data.get('maker_address', ''))

        # ส่วนที่ 2: ผู้ร่วมทำธุรกรรม/ผู้รับมอบอำนาจ
        y_pos -= 15*mm
        c.setFont(FONT_NAME_TH, FONT_SIZE_SECTION)
        c.drawString(MARGIN_LEFT*mm, y_pos, 'ส่วนที่ ๒ ผู้ร่วมทำธุรกรรม/ผู้รับมอบอำนาจ (ถ้ามี)')

        # 关联方姓名
        y_pos -= 10*mm
        c.setFont(FONT_NAME_TH, FONT_SIZE_NORMAL)
        c.drawString(MARGIN_LEFT*mm, y_pos, 'ชื่อ-นามสกุล')
        self._draw_underline(c, MARGIN_LEFT*mm + 30*mm, y_pos - 2*mm, 120*mm,
                            text=data.get('joint_party_name', ''))

        # ส่วนที่ 3: ข้อเท็จจริงเกี่ยวกับธุรกรรม
        y_pos -= 15*mm
        c.setFont(FONT_NAME_TH, FONT_SIZE_SECTION)
        c.drawString(MARGIN_LEFT*mm, y_pos, 'ส่วนที่ ๓ ข้อเท็จจริงเกี่ยวกับธุรกรรม')

        # 交易日期
        y_pos -= 10*mm
        c.setFont(FONT_NAME_TH, FONT_SIZE_NORMAL)
        c.drawString(MARGIN_LEFT*mm, y_pos, 'วันที่ทำธุรกรรม')
        transaction_date = data.get('transaction_date', '')
        if isinstance(transaction_date, datetime):
            transaction_date = transaction_date.strftime('%d/%m/%Y')
        self._draw_underline(c, MARGIN_LEFT*mm + 35*mm, y_pos - 2*mm, 40*mm,
                            text=transaction_date)

        # 交易类型
        y_pos -= 10*mm
        c.drawString(MARGIN_LEFT*mm, y_pos, 'ประเภทธุรกรรม')

        y_pos -= 8*mm
        self._draw_checkbox(c, MARGIN_LEFT*mm + 10*mm, y_pos,
                           checked=data.get('transaction_type') == 'deposit',
                           label='ฝากเงิน', label_offset=6*mm)
        self._draw_checkbox(c, MARGIN_LEFT*mm + 50*mm, y_pos,
                           checked=data.get('transaction_type') == 'withdraw',
                           label='ถอนเงิน', label_offset=6*mm)
        self._draw_checkbox(c, MARGIN_LEFT*mm + 90*mm, y_pos,
                           checked=data.get('transaction_type') == 'exchange',
                           label='แลกเปลี่ยนเงินตรา', label_offset=6*mm)

        # 金额表格
        y_pos -= 15*mm
        table_data = [
            ['สกุลเงิน', 'จำนวนเงิน (บาท)', 'หมายเหตุ'],
            [data.get('currency_code', 'THB'),
             f"{data.get('amount_thb', 0):,.2f}",
             data.get('remarks', '')]
        ]
        col_widths = [40*mm, 50*mm, 70*mm]
        self._draw_table(c, table_data, MARGIN_LEFT*mm, y_pos, col_widths)

        # ส่วนที่ 4: ลายเซ็น
        y_pos -= 35*mm
        c.setFont(FONT_NAME_TH, FONT_SIZE_SECTION)
        c.drawString(MARGIN_LEFT*mm, y_pos, 'ส่วนที่ ๔ ผู้รายงาน')

        y_pos -= 10*mm
        c.setFont(FONT_NAME_TH, FONT_SIZE_NORMAL)
        c.drawString(MARGIN_LEFT*mm, y_pos, 'ชื่อผู้รายงาน')
        self._draw_underline(c, MARGIN_LEFT*mm + 30*mm, y_pos - 2*mm, 60*mm,
                            text=data.get('reporter_name', ''))

        y_pos -= 10*mm
        c.drawString(MARGIN_LEFT*mm, y_pos, 'ตำแหน่ง')
        self._draw_underline(c, MARGIN_LEFT*mm + 30*mm, y_pos - 2*mm, 60*mm,
                            text=data.get('reporter_position', ''))

        y_pos -= 10*mm
        c.drawString(MARGIN_LEFT*mm, y_pos, 'ลายมือชื่อ')
        self._draw_underline(c, MARGIN_LEFT*mm + 30*mm, y_pos - 2*mm, 60*mm)

        # 报告日期
        y_pos -= 10*mm
        c.drawString(MARGIN_LEFT*mm, y_pos, 'วันที่รายงาน')
        report_date = data.get('report_date', datetime.now().strftime('%d/%m/%Y'))
        self._draw_underline(c, MARGIN_LEFT*mm + 30*mm, y_pos - 2*mm, 40*mm,
                            text=report_date)

        # 表单编号
        c.setFont(FONT_NAME_TH, FONT_SIZE_SMALL)
        c.drawRightString(PAGE_WIDTH - MARGIN_RIGHT*mm, MARGIN_BOTTOM*mm,
                         'แบบ ปปง. ๑-๐๑')

        # ========== 第2页 ==========
        c.showPage()

        # 绘制法律声明
        self._draw_footer_disclaimer(c, page_num=2)

        # 表单编号
        c.setFont(FONT_NAME_TH, FONT_SIZE_SMALL)
        c.drawRightString(PAGE_WIDTH - MARGIN_RIGHT*mm, MARGIN_BOTTOM*mm,
                         'แบบ ปปง. ๑-๐๑ (หน้า ๒)')

        # 保存PDF
        c.save()

        return output_path

    def generate_amlo_102(self, data: Dict, output_path: str) -> str:
        """生成AMLO-1-02资产交易报告

        Args:
            data: 报告数据字典
            output_path: 输出文件路径

        Returns:
            生成的PDF文件路径
        """
        c = canvas.Canvas(output_path, pagesize=A4)

        # 绘制报告编号框
        self._draw_report_number_box(c, data.get('report_number', ''))

        # 标题
        c.setFont(FONT_NAME_TH, FONT_SIZE_TITLE)
        c.drawCentredString(PAGE_WIDTH/2, PAGE_HEIGHT - 30*mm,
                           'แบบรายงานการทำธุรกรรมที่เกี่ยวกับทรัพย์สิน')

        # 副标题
        c.setFont(FONT_NAME_TH, FONT_SIZE_NORMAL)
        c.drawCentredString(PAGE_WIDTH/2, PAGE_HEIGHT - 38*mm,
                           'ตามมาตรา ๑๓ แห่งพระราชบัญญัติป้องกันและปราบปรามการฟอกเงิน พ.ศ. ๒๕๔๒')

        # 报告类型
        y_pos = PAGE_HEIGHT - 48*mm
        self._draw_checkbox(c, MARGIN_LEFT*mm, y_pos,
                           checked=data.get('is_amendment', False) == False,
                           label='รายงานฉบับแรก', label_offset=6*mm)
        self._draw_checkbox(c, MARGIN_LEFT*mm + 50*mm, y_pos,
                           checked=data.get('is_amendment', False) == True,
                           label='รายงานฉบับแก้ไข', label_offset=6*mm)

        # ส่วนที่ 1: ผู้ทำธุรกรรม (与AMLO-1-01相同结构)
        y_pos -= 10*mm
        c.setFont(FONT_NAME_TH, FONT_SIZE_SECTION)
        c.drawString(MARGIN_LEFT*mm, y_pos, 'ส่วนที่ ๑ ผู้ทำธุรกรรม')

        # 交易者信息（简化版）
        y_pos -= 8*mm
        self._draw_checkbox(c, MARGIN_LEFT*mm, y_pos,
                           checked=data.get('maker_type') == 'person',
                           label='บุคคลธรรมดา', label_offset=6*mm)
        self._draw_checkbox(c, MARGIN_LEFT*mm + 50*mm, y_pos,
                           checked=data.get('maker_type') == 'company',
                           label='นิติบุคคล', label_offset=6*mm)

        y_pos -= 10*mm
        c.setFont(FONT_NAME_TH, FONT_SIZE_NORMAL)
        c.drawString(MARGIN_LEFT*mm, y_pos, 'ชื่อ-นามสกุล')
        self._draw_underline(c, MARGIN_LEFT*mm + 30*mm, y_pos - 2*mm, 120*mm,
                            text=data.get('maker_name', ''))

        # ส่วนที่ 3: ข้อเท็จจริงเกี่ยวกับทรัพย์สิน
        y_pos -= 15*mm
        c.setFont(FONT_NAME_TH, FONT_SIZE_SECTION)
        c.drawString(MARGIN_LEFT*mm, y_pos, 'ส่วนที่ ๓ ข้อเท็จจริงเกี่ยวกับทรัพย์สิน')

        # 资产交易类型
        y_pos -= 10*mm
        c.setFont(FONT_NAME_TH, FONT_SIZE_NORMAL)
        c.drawString(MARGIN_LEFT*mm, y_pos, 'ประเภทธุรกรรม')

        y_pos -= 8*mm
        self._draw_checkbox(c, MARGIN_LEFT*mm + 10*mm, y_pos,
                           checked=data.get('asset_transaction_type') == 'mortgage',
                           label='จำนอง', label_offset=6*mm)
        self._draw_checkbox(c, MARGIN_LEFT*mm + 50*mm, y_pos,
                           checked=data.get('asset_transaction_type') == 'sale',
                           label='ขายฝาก', label_offset=6*mm)
        self._draw_checkbox(c, MARGIN_LEFT*mm + 90*mm, y_pos,
                           checked=data.get('asset_transaction_type') == 'transfer',
                           label='โอนเงิน', label_offset=6*mm)

        # 资产类型
        y_pos -= 10*mm
        c.drawString(MARGIN_LEFT*mm, y_pos, 'ประเภทของทรัพย์สิน')

        y_pos -= 8*mm
        self._draw_checkbox(c, MARGIN_LEFT*mm + 10*mm, y_pos,
                           checked=data.get('asset_type') == 'land',
                           label='ที่ดิน', label_offset=6*mm)
        self._draw_checkbox(c, MARGIN_LEFT*mm + 50*mm, y_pos,
                           checked=data.get('asset_type') == 'building',
                           label='สิ่งปลูกสร้าง', label_offset=6*mm)

        # 资产价值
        y_pos -= 12*mm
        c.drawString(MARGIN_LEFT*mm, y_pos, 'มูลค่าทรัพย์สิน (บาท)')
        self._draw_underline(c, MARGIN_LEFT*mm + 45*mm, y_pos - 2*mm, 60*mm,
                            text=f"{data.get('asset_value_thb', 0):,.2f}")

        # ส่วนที่ 4: ผู้รายงาน
        y_pos -= 20*mm
        c.setFont(FONT_NAME_TH, FONT_SIZE_SECTION)
        c.drawString(MARGIN_LEFT*mm, y_pos, 'ส่วนที่ ๔ ผู้รายงาน')

        y_pos -= 10*mm
        c.setFont(FONT_NAME_TH, FONT_SIZE_NORMAL)
        c.drawString(MARGIN_LEFT*mm, y_pos, 'ชื่อผู้รายงาน')
        self._draw_underline(c, MARGIN_LEFT*mm + 30*mm, y_pos - 2*mm, 60*mm,
                            text=data.get('reporter_name', ''))

        # 表单编号
        c.setFont(FONT_NAME_TH, FONT_SIZE_SMALL)
        c.drawRightString(PAGE_WIDTH - MARGIN_RIGHT*mm, MARGIN_BOTTOM*mm,
                         'แบบ ปปง. ๑-๐๒')

        c.save()
        return output_path

    def generate_amlo_103(self, data: Dict, output_path: str) -> str:
        """生成AMLO-1-03可疑交易报告

        Args:
            data: 报告数据字典
            output_path: 输出文件路径

        Returns:
            生成的PDF文件路径
        """
        c = canvas.Canvas(output_path, pagesize=A4)

        # 绘制报告编号框
        self._draw_report_number_box(c, data.get('report_number', ''))

        # 标题
        c.setFont(FONT_NAME_TH, FONT_SIZE_TITLE)
        c.drawCentredString(PAGE_WIDTH/2, PAGE_HEIGHT - 30*mm,
                           'แบบรายงานการทำธุรกรรมที่มีเหตุอันควรสงสัย')

        # 副标题
        c.setFont(FONT_NAME_TH, FONT_SIZE_NORMAL)
        c.drawCentredString(PAGE_WIDTH/2, PAGE_HEIGHT - 38*mm,
                           'ตามมาตรา ๑๓ แห่งพระราชบัญญัติป้องกันและปราบปรามการฟอกเงิน พ.ศ. ๒๕๔๒')

        # 报告类型
        y_pos = PAGE_HEIGHT - 48*mm
        self._draw_checkbox(c, MARGIN_LEFT*mm, y_pos,
                           checked=data.get('is_amendment', False) == False,
                           label='รายงานฉบับแรก', label_offset=6*mm)
        self._draw_checkbox(c, MARGIN_LEFT*mm + 50*mm, y_pos,
                           checked=data.get('is_amendment', False) == True,
                           label='รายงานฉบับแก้ไข', label_offset=6*mm)

        # 是否已提交CTR/ATR
        y_pos -= 10*mm
        c.setFont(FONT_NAME_TH, FONT_SIZE_NORMAL)
        c.drawString(MARGIN_LEFT*mm, y_pos, 'ได้ส่งรายงาน ปปง. ๑-๐๑ หรือ ปปง. ๑-๐๒ แล้ว')
        self._draw_checkbox(c, MARGIN_LEFT*mm + 80*mm, y_pos,
                           checked=data.get('has_filed_ctr_atr', False) == True,
                           label='ใช่', label_offset=6*mm)
        self._draw_checkbox(c, MARGIN_LEFT*mm + 100*mm, y_pos,
                           checked=data.get('has_filed_ctr_atr', False) == False,
                           label='ไม่ใช่', label_offset=6*mm)

        # 如果已提交，填写编号
        if data.get('has_filed_ctr_atr'):
            y_pos -= 8*mm
            c.drawString(MARGIN_LEFT*mm + 10*mm, y_pos, 'เลขที่รายงาน')
            self._draw_underline(c, MARGIN_LEFT*mm + 40*mm, y_pos - 2*mm, 60*mm,
                                text=data.get('previous_report_number', ''))

        # ส่วนที่ 1-4 (可选)
        y_pos -= 15*mm
        c.setFont(FONT_NAME_TH, FONT_SIZE_NORMAL)
        c.drawString(MARGIN_LEFT*mm, y_pos,
                    'หากได้ส่งรายงาน ปปง. ๑-๐๑ หรือ ปปง. ๑-๐๒ แล้ว ไม่ต้องกรอกส่วนที่ ๑-๔')

        # ส่วนที่ 1: ผู้ทำธุรกรรม (简化版)
        y_pos -= 12*mm
        c.setFont(FONT_NAME_TH, FONT_SIZE_SECTION)
        c.drawString(MARGIN_LEFT*mm, y_pos, 'ส่วนที่ ๑ ผู้ทำธุรกรรม')

        y_pos -= 10*mm
        c.setFont(FONT_NAME_TH, FONT_SIZE_NORMAL)
        c.drawString(MARGIN_LEFT*mm, y_pos, 'ชื่อ-นามสกุล')
        self._draw_underline(c, MARGIN_LEFT*mm + 30*mm, y_pos - 2*mm, 120*mm,
                            text=data.get('maker_name', ''))

        # ส่วนที่ 5: เหตุอันควรสงสัย (可疑原因 - 核心部分)
        y_pos -= 20*mm
        c.setFont(FONT_NAME_TH, FONT_SIZE_SECTION)
        c.drawString(MARGIN_LEFT*mm, y_pos, 'ส่วนที่ ๕ เหตุอันควรสงสัย')

        # 多行文本框
        y_pos -= 10*mm
        c.setFont(FONT_NAME_TH, FONT_SIZE_NORMAL)

        # 绘制多行文本区域
        text_box_x = MARGIN_LEFT*mm
        text_box_y = y_pos - 50*mm
        text_box_width = PAGE_WIDTH - (MARGIN_LEFT + MARGIN_RIGHT)*mm
        text_box_height = 50*mm

        # 边框
        c.rect(text_box_x, text_box_y, text_box_width, text_box_height)

        # 填充可疑原因文本（多行）
        suspicion_reasons = data.get('suspicion_reasons', '')
        if suspicion_reasons:
            # 简单的多行文本处理
            lines = suspicion_reasons.split('\n')
            text_y = text_box_y + text_box_height - 8*mm

            for line in lines[:6]:  # 最多6行
                c.drawString(text_box_x + 5*mm, text_y, line)
                text_y -= 7*mm

        # ส่วนที่ 6: ผู้รายงาน
        y_pos = text_box_y - 15*mm
        c.setFont(FONT_NAME_TH, FONT_SIZE_SECTION)
        c.drawString(MARGIN_LEFT*mm, y_pos, 'ส่วนที่ ๖ ผู้รายงาน')

        y_pos -= 10*mm
        c.setFont(FONT_NAME_TH, FONT_SIZE_NORMAL)
        c.drawString(MARGIN_LEFT*mm, y_pos, 'ชื่อผู้รายงาน')
        self._draw_underline(c, MARGIN_LEFT*mm + 30*mm, y_pos - 2*mm, 60*mm,
                            text=data.get('reporter_name', ''))

        y_pos -= 10*mm
        c.drawString(MARGIN_LEFT*mm, y_pos, 'วันที่รายงาน')
        report_date = data.get('report_date', datetime.now().strftime('%d/%m/%Y'))
        self._draw_underline(c, MARGIN_LEFT*mm + 30*mm, y_pos - 2*mm, 40*mm,
                            text=report_date)

        # 表单编号
        c.setFont(FONT_NAME_TH, FONT_SIZE_SMALL)
        c.drawRightString(PAGE_WIDTH - MARGIN_RIGHT*mm, MARGIN_BOTTOM*mm,
                         'แบบ ปปง. ๑-๐๓')

        c.save()
        return output_path

    def generate_pdf(self, report_type: str, data: Dict, output_path: str) -> str:
        """统一的PDF生成入口

        Args:
            report_type: 报告类型 (AMLO-1-01, AMLO-1-02, AMLO-1-03)
            data: 报告数据字典
            output_path: 输出文件路径

        Returns:
            生成的PDF文件路径

        Raises:
            ValueError: 不支持的报告类型
        """
        if report_type == 'AMLO-1-01':
            # 使用最终精确版生成器
            from .amlo_101_final import AMLO101Final
            generator = AMLO101Final()
            return generator.generate(data, output_path)
        elif report_type == 'AMLO-1-02':
            return self.generate_amlo_102(data, output_path)
        elif report_type == 'AMLO-1-03':
            return self.generate_amlo_103(data, output_path)
        else:
            raise ValueError(f"不支持的报告类型: {report_type}")
