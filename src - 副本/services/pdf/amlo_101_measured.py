# -*- coding: utf-8 -*-
"""
AMLO-1-01 基于精确测量的生成器
所有坐标和尺寸基于标准PDF的实际测量值
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
import os
from typing import Dict

PAGE_WIDTH, PAGE_HEIGHT = A4  # 595 x 842 点

# 颜色
GRAY_BG = HexColor('#E8E8E8')
BLACK = HexColor('#000000')
WHITE = HexColor('#FFFFFF')

# ========== 基于标准PDF测量的精确坐标 ==========
# 所有值以点(point)为单位，1点 = 1/72英寸

# 三层边框（精确测量值）
BORDER_OUTER_X = 19.56
BORDER_OUTER_Y = 19.28
BORDER_OUTER_WIDTH = 558.42
BORDER_OUTER_HEIGHT = 803.16
BORDER_OUTER_LINE = 0.84

BORDER_MIDDLE_X = 21.60
BORDER_MIDDLE_Y = 21.32
BORDER_MIDDLE_WIDTH = 554.34
BORDER_MIDDLE_HEIGHT = 799.08
BORDER_MIDDLE_LINE = 1.62

BORDER_INNER_X = 23.70
BORDER_INNER_Y = 23.36
BORDER_INNER_WIDTH = 550.20
BORDER_INNER_HEIGHT = 794.94
BORDER_INNER_LINE = 0.84

# 内容边界
CONTENT_LEFT = 28.8
CONTENT_RIGHT = PAGE_WIDTH - 28.8

# 标题框（测量值）
TITLE_BOX_X = 43.20
TITLE_BOX_Y = 784.34
TITLE_BOX_WIDTH = 194.22
TITLE_BOX_HEIGHT = 28.86

# 主分隔线（最粗的那条）
MAIN_SEPARATOR_Y = 754.82
SEPARATOR_LINE_WIDTH = 1.98

# 其他分隔线
SEP2_Y = 770.00
SEP2_WIDTH = 0.96
SEP3_Y = 771.26
SEP3_WIDTH = 0.54

# ID框（13位）
ID_BOX_WIDTH = 14.46
ID_BOX_HEIGHT = 17.34
ID_BOX_GAP = 14.4  # 框间距

# 区域框尺寸（从测量推算）
SECTION_BOX_HEIGHT = 28.86  # 与标题框相同

class AMLO101Measured:
    def __init__(self):
        try:
            font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'Sarabun-Regular.ttf')
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('Sarabun', font_path))
        except:
            pass

    def _borders(self, c):
        """绘制三层边框 - 精确测量值"""
        c.saveState()

        # 外层
        c.setLineWidth(BORDER_OUTER_LINE)
        c.rect(BORDER_OUTER_X, BORDER_OUTER_Y,
               BORDER_OUTER_WIDTH, BORDER_OUTER_HEIGHT)

        # 中层（粗）
        c.setLineWidth(BORDER_MIDDLE_LINE)
        c.rect(BORDER_MIDDLE_X, BORDER_MIDDLE_Y,
               BORDER_MIDDLE_WIDTH, BORDER_MIDDLE_HEIGHT)

        # 内层
        c.setLineWidth(BORDER_INNER_LINE)
        c.rect(BORDER_INNER_X, BORDER_INNER_Y,
               BORDER_INNER_WIDTH, BORDER_INNER_HEIGHT)

        c.restoreState()

    def _title_box(self, c):
        """绘制标题框 - 精确位置和尺寸"""
        c.saveState()

        # 灰色背景框
        c.setFillColor(GRAY_BG)
        c.setLineWidth(0.72)
        c.rect(TITLE_BOX_X, TITLE_BOX_Y,
               TITLE_BOX_WIDTH, TITLE_BOX_HEIGHT,
               fill=1, stroke=1)

        # 标题文字
        c.setFillColor(BLACK)
        c.setFont('Sarabun', 12)
        # 左对齐，留2mm边距
        c.drawString(TITLE_BOX_X + 5, TITLE_BOX_Y + 10,
                    'แบบรายงานการทำธุรกรรมที่ใช้เงินสด')

        c.restoreState()

    def _separator(self, c, y, width=1.98):
        """绘制分隔线"""
        c.saveState()
        c.setLineWidth(width)
        c.line(CONTENT_LEFT, y, CONTENT_RIGHT, y)
        c.restoreState()

    def _id_boxes(self, c, start_x, start_y, count=13):
        """绘制ID号码框 - 精确尺寸"""
        c.saveState()

        for i in range(count):
            x = start_x + i * ID_BOX_GAP
            c.setLineWidth(0.5)
            c.setFillColor(WHITE)
            c.rect(x, start_y, ID_BOX_WIDTH, ID_BOX_HEIGHT,
                   fill=1, stroke=1)

        c.restoreState()

    def _checkbox(self, c, x, y, size=3*mm, text='', checked=False):
        """绘制复选框"""
        c.saveState()
        c.setLineWidth(0.5)
        c.setFillColor(WHITE)
        c.rect(x, y, size, size, fill=1, stroke=1)

        if checked:
            c.setFont('Helvetica', 8)
            c.drawString(x + 0.4*mm, y + 0.4*mm, '✓')

        if text:
            c.setFillColor(BLACK)
            c.setFont('Sarabun', 8)
            c.drawString(x + size + 1.5*mm, y + 0.5*mm, text)

        c.restoreState()

    def _fill_text(self, c, x, y, text, font='Sarabun', size=8):
        """填写文本（在下划线上方）"""
        if text:
            c.saveState()
            c.setFont(font, size)
            c.setFillColor(BLACK)
            c.drawString(x, y, str(text))
            c.restoreState()

    def _fill_boxes(self, c, start_x, start_y, text, box_width=14.46, gap=14.4):
        """在方格中填写数字或文本"""
        if not text:
            return

        c.saveState()
        c.setFont('Sarabun', 10)
        c.setFillColor(BLACK)

        text = str(text).strip()
        for i, char in enumerate(text[:13]):  # 最多13位
            x = start_x + i * gap + box_width/3
            c.drawString(x, start_y + 3, char)

        c.restoreState()

    def _underline(self, c, x, y, width):
        """下划线"""
        c.setLineWidth(0.3)
        c.line(x, y, x + width, y)

    def generate(self, data: Dict, path: str):
        """
        生成AMLO 1-01报表PDF

        data字典结构:
        {
            'report_number': '001-001-68-00001',  # 报告编号
            'report_type': 'original',  # 'original' 或 'revised'
            'revision_number': '',  # 修订次数
            'revision_date': '',  # 修订日期
            'total_pages': '1',  # 总页数

            'customer': {
                'id_number': '1234567890123',  # 身份证号
                'name': 'สมชาย ใจดี',  # 姓名
                'address': '123 ถนนสุขุมวิท กรุงเทพฯ 10110',  # 地址
                'nationality': 'ไทย',  # 国籍
                'occupation': 'พนักงานบริษัท',  # 职业
                'phone': '02-123-4567',  # 电话
                'id_type': 'national_id',  # 证件类型
                'id_number_doc': '1234567890123',
                'id_issue_date': '01/01/2015',
                'id_expiry_date': '01/01/2025',
                'id_issue_place': 'กรุงเทพฯ',
                'transaction_by': 'self'  # 'self' 或 'agent'
            },

            'transaction': {
                'type': 'buy',  # 'buy' 或 'sell'
                'amount': '10000',  # 金额
                'currency': 'USD',  # 币种
                'thb_equivalent': '350000',  # 泰铢等值
                'date': '15/01/2568',  # 日期
                'time': '14:30',  # 时间
                'purpose': 'ท่องเที่ยว'  # 目的
            },

            'reporter': {
                'institution': 'ธนาคารกรุงเทพ จำกัด (มหาชน)',  # 机构名称
                'branch_address': 'สาขาสีลม 123 ถนนสีลม กรุงเทพฯ',  # 分行地址
                'staff_name': 'สมหญิง รักงาน',  # 员工姓名
                'staff_position': 'เจ้าหน้าที่แลกเปลี่ยนเงินตรา',  # 职位
                'phone': '02-234-5678',
                'fax': '02-234-5679',
                'report_date': '15/01/2568'
            }
        }
        """
        c = canvas.Canvas(path, pagesize=A4)

        # 1. 三层边框
        self._borders(c)

        # 2. 标题框
        self._title_box(c)

        # 3. 说明文字（标题框下方）
        c.setFont('Sarabun', 6.5)
        c.drawString(TITLE_BOX_X, TITLE_BOX_Y - 10,
                    '(โปรดกาเครื่องหมาย ✓ หน้าข้อที่เลือกและระบุข้อความตามที่กำหนดไว้ทุกข้อ)')

        # 4. 右上角：แบบ ปปง. ๑-๐๑
        c.setFont('Sarabun', 9)
        c.drawRightString(CONTENT_RIGHT, TITLE_BOX_Y + 35, 'แบบ ปปง. ๑-๐๑')

        # 5. 右上角报告编号区（方格结构）
        # เลขที่标签
        c.setFont('Sarabun', 7)
        c.drawString(TITLE_BOX_X + TITLE_BOX_WIDTH + 15, TITLE_BOX_Y + 20, 'เลขที่')

        # 第一组3个框（สถาบันการเงิน）
        box1_x = TITLE_BOX_X + TITLE_BOX_WIDTH + 35
        box1_y = TITLE_BOX_Y + 18
        box_size = 4*mm
        gap = 0.5*mm

        for i in range(3):
            c.rect(box1_x + i*(box_size+gap), box1_y, box_size, box_size)
        c.setFont('Sarabun', 6.5)
        c.drawCentredString(box1_x + 1.5*(box_size+gap), box1_y - 8, 'สถาบันการเงิน')

        # 横线连接
        c.line(box1_x + 3*(box_size+gap) + 1, box1_y + box_size/2,
               box1_x + 3*(box_size+gap) + 8, box1_y + box_size/2)

        # 第二组3个框（สาขา）
        box2_x = box1_x + 3*(box_size+gap) + 8
        for i in range(3):
            c.rect(box2_x + i*(box_size+gap), box1_y, box_size, box_size)
        c.drawCentredString(box2_x + 1.5*(box_size+gap), box1_y - 8, 'สาขา')

        # 横线连接
        c.line(box2_x + 3*(box_size+gap) + 1, box1_y + box_size/2,
               box2_x + 3*(box_size+gap) + 8, box1_y + box_size/2)

        # 第三组2个框（ปี พ.ศ.）
        box3_x = box2_x + 3*(box_size+gap) + 8
        for i in range(2):
            c.rect(box3_x + i*(box_size+gap), box1_y, box_size, box_size)
        c.setFont('Sarabun', 5.5)
        c.drawString(box3_x - 2, box1_y - 8, 'ปี พ.ศ.')
        c.drawString(box3_x - 2, box1_y - 14, '(ใช้ ๒ หลักสุดท้าย)')

        # 横线连接
        c.line(box3_x + 2*(box_size+gap) + 1, box1_y + box_size/2,
               box3_x + 2*(box_size+gap) + 8, box1_y + box_size/2)

        # 长框（เลขลำดับรายงาน）
        long_x = box3_x + 2*(box_size+gap) + 8
        long_w = CONTENT_RIGHT - long_x
        c.rect(long_x, box1_y, long_w, box_size + 3)
        c.setFont('Sarabun', 7)
        c.drawString(long_x + 2, box1_y + 4, 'เลขลำดับรายงาน')

        # 6. 第一条粗分隔线（三条细线结构）
        y_sep1 = SEP3_Y
        c.setLineWidth(SEP3_WIDTH)
        c.line(CONTENT_LEFT, y_sep1, CONTENT_RIGHT, y_sep1)
        c.setLineWidth(SEP2_WIDTH)
        c.line(CONTENT_LEFT, SEP2_Y, CONTENT_RIGHT, SEP2_Y)
        c.setLineWidth(SEP3_WIDTH)
        c.line(CONTENT_LEFT, SEP3_Y - 2, CONTENT_RIGHT, SEP3_Y - 2)

        # 7. 区域2：选项行（高度较小）
        y_opt = SEP3_Y - 15
        report_type = data.get('report_type', 'original')
        self._checkbox(c, CONTENT_LEFT + 10, y_opt, text='รายงานฉบับหลัก',
                      checked=(report_type == 'original'))
        self._checkbox(c, CONTENT_LEFT + 80, y_opt, text='รายงานฉบับแก้ไข/ เพิ่มเติม ครั้งที่',
                      checked=(report_type == 'revised'))

        # 下划线
        self._underline(c, CONTENT_LEFT + 180, y_opt - 2, 30)
        if report_type == 'revised':
            self._fill_text(c, CONTENT_LEFT + 185, y_opt, data.get('revision_number', ''))
        c.setFont('Sarabun', 8)
        c.drawString(CONTENT_LEFT + 212, y_opt, 'ลงวันที่')
        self._underline(c, CONTENT_LEFT + 238, y_opt - 2, 30)
        if report_type == 'revised':
            self._fill_text(c, CONTENT_LEFT + 243, y_opt, data.get('revision_date', ''))

        # 竖线分隔
        div_x = CONTENT_LEFT + 240
        c.setLineWidth(0.5)
        c.line(div_x, y_opt - 5, div_x, y_opt + 8)

        # 右侧文字
        c.drawString(div_x + 6, y_opt, 'รวมเอกสารจำนวนทั้งสิ้น')
        self._underline(c, div_x + 80, y_opt - 2, 25)
        c.drawString(div_x + 107, y_opt, 'แผ่น')

        # 8. 第二条粗分隔线
        self._separator(c, MAIN_SEPARATOR_Y, SEPARATOR_LINE_WIDTH)

        # 9. ส่วนที่ ๑
        y_sec1 = MAIN_SEPARATOR_Y - 35

        # 标题框
        c.saveState()
        c.setFillColor(GRAY_BG)
        c.rect(CONTENT_LEFT, y_sec1, 155, SECTION_BOX_HEIGHT, fill=1, stroke=1)
        c.setFillColor(BLACK)
        c.setFont('Sarabun', 9.5)
        c.drawString(CONTENT_LEFT + 5, y_sec1 + 8, 'ส่วนที่ ๑. ผู้ทำธุรกรรม')
        c.restoreState()

        # 13位ID框（右侧）
        id13_x = CONTENT_RIGHT - 200
        id13_y = y_sec1 + 5
        self._id_boxes(c, id13_x, id13_y, 13)

        # 填充ID号码
        customer = data.get('customer', {})
        if customer.get('id_number'):
            self._fill_boxes(c, id13_x, id13_y, customer['id_number'])

        # ID框下方说明（灰色背景）
        explain_y = id13_y - 50
        c.saveState()
        c.setFillColor(GRAY_BG)
        c.rect(id13_x - 5, explain_y, 210, 40, fill=1, stroke=0)

        c.setFillColor(BLACK)
        c.setFont('Sarabun', 6.5)
        c.drawString(id13_x, explain_y + 32, 'โปรดระบุเลขที่บัตรประจำตัวประชาชน')
        c.drawString(id13_x, explain_y + 24, 'หากเป็นคนต่างด้าว โปรดระบุเลขที่หนังสือเดินทาง หรือเลขที่')
        c.drawString(id13_x, explain_y + 16, 'เอกสารประจำตัวอื่นๆ โดยให้กรอกเลขชิดด้านซ้ายเป็นหลัก')
        c.restoreState()

        # ส่วนที่ ๑ 字段
        yf = y_sec1 - 15

        c.setFont('Sarabun', 8)
        c.drawString(CONTENT_LEFT, yf, '๑.๑ ชื่อ-นามสกุล')
        self._underline(c, CONTENT_LEFT + 70, yf - 2, 350)
        # 填充姓名
        self._fill_text(c, CONTENT_LEFT + 75, yf, customer.get('name', ''))

        yf -= 12
        transaction_by = customer.get('transaction_by', 'self')
        self._checkbox(c, CONTENT_LEFT + 5, yf,
                      text='ทำธุรกรรมด้วยตนเอง (หากมีผู้ร่วมทำธุรกรรม ให้ระบุรายละเอียดของผู้ร่วมทำธุรกรรมในส่วนที่ ๒ ด้วย)',
                      checked=(transaction_by == 'self'))

        yf -= 12
        self._checkbox(c, CONTENT_LEFT + 5, yf,
                      text='ทำธุรกรรมแทนผู้อื่น (โปรดระบุรายละเอียดของผู้มอบหมาย หรือผู้มอบอำนาจในส่วนที่ ๒ ด้วย)',
                      checked=(transaction_by == 'agent'))

        # 1.2 地址
        yf -= 15
        c.drawString(CONTENT_LEFT, yf, '๑.๒ ที่อยู่')
        self._underline(c, CONTENT_LEFT + 35, yf - 2, 420)
        self._fill_text(c, CONTENT_LEFT + 40, yf, customer.get('address', ''))

        # 1.3 国籍
        yf -= 12
        c.drawString(CONTENT_LEFT, yf, '๑.๓ สัญชาติ')
        self._underline(c, CONTENT_LEFT + 50, yf - 2, 80)
        self._fill_text(c, CONTENT_LEFT + 55, yf, customer.get('nationality', ''))
        c.drawString(CONTENT_LEFT + 135, yf, 'อาชีพ')
        self._underline(c, CONTENT_LEFT + 170, yf - 2, 100)
        self._fill_text(c, CONTENT_LEFT + 175, yf, customer.get('occupation', ''))
        c.drawString(CONTENT_LEFT + 275, yf, 'โทรศัพท์')
        self._underline(c, CONTENT_LEFT + 320, yf - 2, 100)
        self._fill_text(c, CONTENT_LEFT + 325, yf, customer.get('phone', ''))

        # 1.4 证件信息
        yf -= 15
        c.drawString(CONTENT_LEFT, yf, '๑.๔ ประเภทเอกสารประจำตัว')

        yf -= 12
        id_type = customer.get('id_type', 'national_id')
        self._checkbox(c, CONTENT_LEFT + 5, yf, text='บัตรประจำตัวประชาชน',
                      checked=(id_type == 'national_id'))
        self._checkbox(c, CONTENT_LEFT + 110, yf, text='หนังสือเดินทาง',
                      checked=(id_type == 'passport'))
        self._checkbox(c, CONTENT_LEFT + 200, yf, text='ใบอนุญาตขับรถ',
                      checked=(id_type == 'driver_license'))
        self._checkbox(c, CONTENT_LEFT + 290, yf, text='อื่น ๆ (ระบุ)',
                      checked=(id_type == 'other'))
        self._underline(c, CONTENT_LEFT + 350, yf - 2, 70)
        if id_type == 'other':
            self._fill_text(c, CONTENT_LEFT + 355, yf, customer.get('id_type_other', ''))

        yf -= 12
        c.drawString(CONTENT_LEFT + 5, yf, 'เลขที่เอกสาร')
        self._underline(c, CONTENT_LEFT + 55, yf - 2, 120)
        self._fill_text(c, CONTENT_LEFT + 60, yf, customer.get('id_number_doc', ''))
        c.drawString(CONTENT_LEFT + 180, yf, 'วันออกเอกสาร')
        self._underline(c, CONTENT_LEFT + 240, yf - 2, 60)
        self._fill_text(c, CONTENT_LEFT + 245, yf, customer.get('id_issue_date', ''))
        c.drawString(CONTENT_LEFT + 305, yf, 'วันหมดอายุ')
        self._underline(c, CONTENT_LEFT + 360, yf - 2, 60)
        self._fill_text(c, CONTENT_LEFT + 365, yf, customer.get('id_expiry_date', ''))

        yf -= 12
        c.drawString(CONTENT_LEFT + 5, yf, 'สถานที่ออกเอกสาร')
        self._underline(c, CONTENT_LEFT + 80, yf - 2, 340)
        self._fill_text(c, CONTENT_LEFT + 85, yf, customer.get('id_issue_place', ''))

        # 第二条粗分隔线 - ส่วนที่ ๒
        yf -= 25
        self._separator(c, yf, SEPARATOR_LINE_WIDTH)

        # 10. ส่วนที่ ๒
        yf -= 35

        # 标题框
        c.saveState()
        c.setFillColor(GRAY_BG)
        c.rect(CONTENT_LEFT, yf, 330, SECTION_BOX_HEIGHT, fill=1, stroke=1)
        c.setFillColor(BLACK)
        c.setFont('Sarabun', 9.5)
        c.drawString(CONTENT_LEFT + 5, yf + 8, 'ส่วนที่ ๒. ผู้ร่วมทำธุรกรรม ผู้มอบหมาย หรือผู้มอบอำนาจ')
        c.restoreState()

        # 13位ID框（右侧）
        id13_x2 = CONTENT_RIGHT - 200
        id13_y2 = yf + 5
        self._id_boxes(c, id13_x2, id13_y2, 13)

        # ID框下方说明（灰色背景）
        explain_y2 = id13_y2 - 50
        c.saveState()
        c.setFillColor(GRAY_BG)
        c.rect(id13_x2 - 5, explain_y2, 210, 40, fill=1, stroke=0)

        c.setFillColor(BLACK)
        c.setFont('Sarabun', 6.5)
        c.drawString(id13_x2, explain_y2 + 32, 'โปรดระบุเลขที่บัตรประจำตัวประชาชน')
        c.drawString(id13_x2, explain_y2 + 24, 'หากเป็นคนต่างด้าว โปรดระบุเลขที่หนังสือเดินทาง หรือเลขที่')
        c.drawString(id13_x2, explain_y2 + 16, 'เอกสารประจำตัวอื่นๆ โดยให้กรอกเลขชิดด้านซ้ายเป็นหลัก')
        c.restoreState()

        # ส่วนที่ ๒ 字段
        yf2 = yf - 15

        c.setFont('Sarabun', 8)
        c.drawString(CONTENT_LEFT, yf2, '๒.๑ ชื่อ-นามสกุล')
        self._underline(c, CONTENT_LEFT + 70, yf2 - 2, 350)

        yf2 -= 12
        c.drawString(CONTENT_LEFT, yf2, '๒.๒ ที่อยู่')
        self._underline(c, CONTENT_LEFT + 35, yf2 - 2, 420)

        yf2 -= 12
        c.drawString(CONTENT_LEFT, yf2, '๒.๓ สัญชาติ')
        self._underline(c, CONTENT_LEFT + 50, yf2 - 2, 80)
        c.drawString(CONTENT_LEFT + 135, yf2, 'อาชีพ')
        self._underline(c, CONTENT_LEFT + 170, yf2 - 2, 100)
        c.drawString(CONTENT_LEFT + 275, yf2, 'โทรศัพท์')
        self._underline(c, CONTENT_LEFT + 320, yf2 - 2, 100)

        yf2 -= 15
        c.drawString(CONTENT_LEFT, yf2, '๒.๔ ประเภทเอกสารประจำตัว')

        yf2 -= 12
        self._checkbox(c, CONTENT_LEFT + 5, yf2, text='บัตรประจำตัวประชาชน')
        self._checkbox(c, CONTENT_LEFT + 110, yf2, text='หนังสือเดินทาง')
        self._checkbox(c, CONTENT_LEFT + 200, yf2, text='ใบอนุญาตขับรถ')
        self._checkbox(c, CONTENT_LEFT + 290, yf2, text='อื่น ๆ (ระบุ)')
        self._underline(c, CONTENT_LEFT + 350, yf2 - 2, 70)

        yf2 -= 12
        c.drawString(CONTENT_LEFT + 5, yf2, 'เลขที่เอกสาร')
        self._underline(c, CONTENT_LEFT + 55, yf2 - 2, 120)
        c.drawString(CONTENT_LEFT + 180, yf2, 'วันออกเอกสาร')
        self._underline(c, CONTENT_LEFT + 240, yf2 - 2, 60)
        c.drawString(CONTENT_LEFT + 305, yf2, 'วันหมดอายุ')
        self._underline(c, CONTENT_LEFT + 360, yf2 - 2, 60)

        yf2 -= 12
        c.drawString(CONTENT_LEFT + 5, yf2, 'สถานที่ออกเอกสาร')
        self._underline(c, CONTENT_LEFT + 80, yf2 - 2, 340)

        # 第三条粗分隔线 - ส่วนที่ ๓
        yf2 -= 25
        self._separator(c, yf2, SEPARATOR_LINE_WIDTH)

        # 11. ส่วนที่ ๓ - 交易详情
        yf3 = yf2 - 35

        # 标题框
        c.saveState()
        c.setFillColor(GRAY_BG)
        c.rect(CONTENT_LEFT, yf3, 180, SECTION_BOX_HEIGHT, fill=1, stroke=1)
        c.setFillColor(BLACK)
        c.setFont('Sarabun', 9.5)
        c.drawString(CONTENT_LEFT + 5, yf3 + 8, 'ส่วนที่ ๓. รายละเอียดการทำธุรกรรม')
        c.restoreState()

        yf3 -= 15
        c.setFont('Sarabun', 8)
        c.drawString(CONTENT_LEFT, yf3, '๓.๑ ประเภทธุรกรรม')

        transaction = data.get('transaction', {})
        yf3 -= 12
        trans_type = transaction.get('type', 'buy')
        self._checkbox(c, CONTENT_LEFT + 5, yf3, text='ซื้อเงินตราต่างประเทศ',
                      checked=(trans_type == 'buy'))
        self._checkbox(c, CONTENT_LEFT + 150, yf3, text='ขายเงินตราต่างประเทศ',
                      checked=(trans_type == 'sell'))

        yf3 -= 15
        c.drawString(CONTENT_LEFT, yf3, '๓.๒ จำนวนเงิน')
        self._underline(c, CONTENT_LEFT + 60, yf3 - 2, 120)
        self._fill_text(c, CONTENT_LEFT + 65, yf3, transaction.get('amount', ''))
        c.drawString(CONTENT_LEFT + 185, yf3, 'สกุลเงิน')
        self._underline(c, CONTENT_LEFT + 230, yf3 - 2, 80)
        self._fill_text(c, CONTENT_LEFT + 235, yf3, transaction.get('currency', ''))

        yf3 -= 12
        c.drawString(CONTENT_LEFT + 5, yf3, 'เทียบเท่า')
        self._underline(c, CONTENT_LEFT + 50, yf3 - 2, 120)
        self._fill_text(c, CONTENT_LEFT + 55, yf3, transaction.get('thb_equivalent', ''))
        c.drawString(CONTENT_LEFT + 175, yf3, 'บาท')

        yf3 -= 15
        c.drawString(CONTENT_LEFT, yf3, '๓.๓ วันที่ทำธุรกรรม')
        self._underline(c, CONTENT_LEFT + 80, yf3 - 2, 100)
        self._fill_text(c, CONTENT_LEFT + 85, yf3, transaction.get('date', ''))
        c.drawString(CONTENT_LEFT + 185, yf3, 'เวลา')
        self._underline(c, CONTENT_LEFT + 215, yf3 - 2, 60)
        self._fill_text(c, CONTENT_LEFT + 220, yf3, transaction.get('time', ''))

        yf3 -= 15
        c.drawString(CONTENT_LEFT, yf3, '๓.๔ วัตถุประสงค์ในการทำธุรกรรม')
        self._underline(c, CONTENT_LEFT + 140, yf3 - 2, 280)
        self._fill_text(c, CONTENT_LEFT + 145, yf3, transaction.get('purpose', ''))

        # 第四条粗分隔线 - ส่วนที่ ๔
        yf3 -= 25
        self._separator(c, yf3, SEPARATOR_LINE_WIDTH)

        # 12. ส่วนที่ ๔ - 报告人信息
        yf4 = yf3 - 35

        # 标题框
        c.saveState()
        c.setFillColor(GRAY_BG)
        c.rect(CONTENT_LEFT, yf4, 200, SECTION_BOX_HEIGHT, fill=1, stroke=1)
        c.setFillColor(BLACK)
        c.setFont('Sarabun', 9.5)
        c.drawString(CONTENT_LEFT + 5, yf4 + 8, 'ส่วนที่ ๔. สถาบันการเงินผู้รายงาน')
        c.restoreState()

        yf4 -= 15
        c.setFont('Sarabun', 8)
        c.drawString(CONTENT_LEFT, yf4, '๔.๑ ชื่อสถาบันการเงิน')
        self._underline(c, CONTENT_LEFT + 90, yf4 - 2, 330)
        reporter = data.get('reporter', {})
        self._fill_text(c, CONTENT_LEFT + 95, yf4, reporter.get('institution', ''))

        yf4 -= 12
        c.drawString(CONTENT_LEFT, yf4, '๔.๒ ที่อยู่สาขาที่รับรายงาน')
        self._underline(c, CONTENT_LEFT + 110, yf4 - 2, 310)
        self._fill_text(c, CONTENT_LEFT + 115, yf4, reporter.get('branch_address', ''))

        yf4 -= 15
        c.drawString(CONTENT_LEFT, yf4, '๔.๓ ชื่อผู้จัดทำรายงาน')
        self._underline(c, CONTENT_LEFT + 95, yf4 - 2, 150)
        self._fill_text(c, CONTENT_LEFT + 100, yf4, reporter.get('staff_name', ''))
        c.drawString(CONTENT_LEFT + 250, yf4, 'ตำแหน่ง')
        self._underline(c, CONTENT_LEFT + 295, yf4 - 2, 125)
        self._fill_text(c, CONTENT_LEFT + 300, yf4, reporter.get('staff_position', ''))

        yf4 -= 12
        c.drawString(CONTENT_LEFT + 5, yf4, 'โทรศัพท์')
        self._underline(c, CONTENT_LEFT + 50, yf4 - 2, 100)
        self._fill_text(c, CONTENT_LEFT + 55, yf4, reporter.get('phone', ''))
        c.drawString(CONTENT_LEFT + 155, yf4, 'โทรสาร')
        self._underline(c, CONTENT_LEFT + 200, yf4 - 2, 100)
        self._fill_text(c, CONTENT_LEFT + 205, yf4, reporter.get('fax', ''))

        yf4 -= 15
        c.drawString(CONTENT_LEFT, yf4, '๔.๔ ลายมือชื่อผู้จัดทำรายงาน')
        self._underline(c, CONTENT_LEFT + 120, yf4 - 2, 120)
        # 签名通常留空，等待手工签署
        c.drawString(CONTENT_LEFT + 245, yf4, 'วันที่')
        self._underline(c, CONTENT_LEFT + 280, yf4 - 2, 80)
        self._fill_text(c, CONTENT_LEFT + 285, yf4, reporter.get('report_date', ''))

        yf4 -= 12
        c.setFont('Sarabun', 7)
        c.drawString(CONTENT_LEFT + 30, yf4, '(ลายมือชื่อผู้จัดทำรายงาน)')

        c.save()
        return path

if __name__ == '__main__':
    gen = AMLO101Measured()
    output = 'test_measured.pdf'

    # 测试数据
    test_data = {
        'report_number': '001-001-68-00001',
        'report_type': 'original',  # 或 'revised'
        'revision_number': '',
        'revision_date': '',
        'total_pages': '1',

        'customer': {
            'id_number': '1234567890123',
            'name': 'สมชาย ใจดี',
            'address': '123 ถนนสุขุมวิท แขวงคลองเตย เขตคลองเตย กรุงเทพฯ 10110',
            'nationality': 'ไทย',
            'occupation': 'พนักงานบริษัท',
            'phone': '02-123-4567',
            'id_type': 'national_id',  # national_id, passport, driver_license, other
            'id_number_doc': '1234567890123',
            'id_issue_date': '01/01/2558',
            'id_expiry_date': '01/01/2573',
            'id_issue_place': 'กรุงเทพมหานคร',
            'transaction_by': 'self'  # self 或 agent
        },

        'transaction': {
            'type': 'buy',  # buy 或 sell
            'amount': '15,000.00',
            'currency': 'USD',
            'thb_equivalent': '520,500.00',
            'date': '15/03/2568',
            'time': '14:30',
            'purpose': 'เพื่อการท่องเที่ยวต่างประเทศ'
        },

        'reporter': {
            'institution': 'ธนาคารกรุงเทพ จำกัด (มหาชน)',
            'branch_address': 'สาขาสีลม 123 ถนนสีลม แขวงสีลม เขตบางรัก กรุงเทพฯ 10500',
            'staff_name': 'สมหญิง รักงาน',
            'staff_position': 'เจ้าหน้าที่แลกเปลี่ยนเงินตรา',
            'phone': '02-234-5678',
            'fax': '02-234-5679',
            'report_date': '15/03/2568'
        }
    }

    gen.generate(test_data, output)
    print(f"Generated: {output}")
