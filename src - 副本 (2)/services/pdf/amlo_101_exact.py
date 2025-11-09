# -*- coding: utf-8 -*-
"""
AMLO-1-01 精确复刻版本
完全1:1复制标准报告的每一个细节
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, black, white
from datetime import datetime
import os
from typing import Dict

# A4尺寸
PAGE_WIDTH, PAGE_HEIGHT = A4

# 颜色定义
GRAY_BG = HexColor('#E0E0E0')  # 浅灰色背景
BLACK = HexColor('#000000')
WHITE = HexColor('#FFFFFF')

# 精确边距（缩小以匹配标准报告）
MARGIN_OUTER = 8*mm
MARGIN_MIDDLE = 9*mm
MARGIN_INNER = 10*mm
MARGIN_CONTENT = 15*mm  # 内容边距

class AMLO101ExactGenerator:
    """AMLO-1-01精确生成器"""

    def __init__(self):
        self._register_fonts()

    def _register_fonts(self):
        """注册字体"""
        try:
            font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'Sarabun-Regular.ttf')
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('Sarabun', font_path))
                print("[OK] Font registered")
        except Exception as e:
            print(f"Font error: {e}")

    def _triple_border(self, c: canvas.Canvas):
        """三层边框"""
        c.saveState()

        # 外层
        c.setLineWidth(0.5)
        c.rect(MARGIN_OUTER, MARGIN_OUTER,
               PAGE_WIDTH - 2*MARGIN_OUTER,
               PAGE_HEIGHT - 2*MARGIN_OUTER)

        # 中层（粗）
        c.setLineWidth(2)
        c.rect(MARGIN_MIDDLE, MARGIN_MIDDLE,
               PAGE_WIDTH - 2*MARGIN_MIDDLE,
               PAGE_HEIGHT - 2*MARGIN_MIDDLE)

        # 内层
        c.setLineWidth(0.5)
        c.rect(MARGIN_INNER, MARGIN_INNER,
               PAGE_WIDTH - 2*MARGIN_INNER,
               PAGE_HEIGHT - 2*MARGIN_INNER)

        c.restoreState()

    def _checkbox(self, c: canvas.Canvas, x: float, y: float,
                  label: str = '', checked: bool = False):
        """绘制复选框"""
        size = 3*mm
        c.saveState()
        c.setLineWidth(0.5)
        c.setFillColor(WHITE)
        c.rect(x, y, size, size, fill=1, stroke=1)

        if checked:
            c.setFont('Helvetica', 10)
            c.drawString(x + 0.5*mm, y + 0.3*mm, '✓')

        if label:
            c.setFont('Sarabun', 8)
            c.setFillColor(BLACK)
            c.drawString(x + size + 1.5*mm, y + 0.5*mm, label)

        c.restoreState()

    def _underline(self, c: canvas.Canvas, x: float, y: float, width: float):
        """下划线"""
        c.setLineWidth(0.3)
        c.line(x, y, x + width, y)

    def _id_boxes(self, c: canvas.Canvas, x: float, y: float, count: int = 13):
        """ID号码方格"""
        size = 5*mm
        gap = 0.8*mm

        c.saveState()
        for i in range(count):
            c.setLineWidth(0.5)
            c.setStrokeColor(BLACK)
            c.setFillColor(WHITE)
            c.rect(x + i*(size + gap), y, size, size, fill=1, stroke=1)
        c.restoreState()

    def generate(self, data: Dict, output_path: str) -> str:
        """生成PDF"""
        c = canvas.Canvas(output_path, pagesize=A4)

        # 三层边框
        self._triple_border(c)

        # ========== 区域1：标题区 ==========
        y = PAGE_HEIGHT - MARGIN_CONTENT - 5*mm
        x_left = MARGIN_CONTENT
        x_right = PAGE_WIDTH - MARGIN_CONTENT

        # 左侧：标题框（缩小宽度，避免重叠）
        title_w = 95*mm  # 缩小宽度
        title_h = 10*mm
        title_x = x_left
        title_y = y - title_h

        c.saveState()
        # 黑色边框 + 浅灰色背景
        c.setLineWidth(1)
        c.setStrokeColor(BLACK)
        c.setFillColor(GRAY_BG)
        c.rect(title_x, title_y, title_w, title_h, fill=1, stroke=1)

        # 标题文字（黑色）
        c.setFillColor(BLACK)
        c.setFont('Sarabun', 13)
        c.drawCentredString(title_x + title_w/2, title_y + 3*mm,
                           'แบบรายงานการทำธุรกรรมที่ใช้เงินสด')
        c.restoreState()

        # 标题框下方说明
        c.setFont('Sarabun', 6.5)
        c.setFillColor(BLACK)
        c.drawString(title_x, title_y - 3.5*mm,
                    '(โปรดกาเครื่องหมาย ✓ หน้าข้อที่เลือกและระบุข้อความตามที่กำหนดไว้ทุกข้อ)')

        # 右侧：报告编号结构
        # แบบ ปปง. ๑-๐๑
        c.setFont('Sarabun', 9)
        c.drawRightString(x_right, y + 2*mm, 'แบบ ปปง. ๑-๐๑')

        # 方格结构（从右向左）
        box_size = 4*mm
        box_gap = 0.5*mm
        box_y = y - 8*mm

        # 长框（最右侧）
        long_w = 45*mm
        long_x = x_right - long_w
        c.setLineWidth(0.5)
        c.rect(long_x, box_y, long_w, box_size + 1*mm)
        c.setFont('Sarabun', 7)
        c.drawString(long_x + 2*mm, box_y + 1.5*mm, 'เลขลำดับรายงาน')

        # 2个方格（ปี พ.ศ）
        box2_x = long_x - 3*mm - 2*(box_size + box_gap)
        for i in range(2):
            c.rect(box2_x + i*(box_size + box_gap), box_y, box_size, box_size)
        c.setFont('Sarabun', 6)
        c.drawString(box2_x - 2*mm, box_y - 3*mm, 'ปี พ.ศ(ใช้ ๒ หลักสุดท้าย)')

        # 横线连接
        c.line(box2_x + 2*(box_size + box_gap) + 0.5*mm, box_y + box_size/2,
               long_x - 0.5*mm, box_y + box_size/2)

        # 3个方格（สาขา）
        box3_x = box2_x - 3*mm - 3*(box_size + box_gap)
        for i in range(3):
            c.rect(box3_x + i*(box_size + box_gap), box_y, box_size, box_size)
        c.setFont('Sarabun', 7)
        c.drawCentredString(box3_x + 1.5*(box_size + box_gap), box_y - 3*mm, 'สาขา')

        # 横线连接
        c.line(box3_x + 3*(box_size + box_gap) + 0.5*mm, box_y + box_size/2,
               box2_x - 0.5*mm, box_y + box_size/2)

        # 3个方格（สถาบันการเงิน）
        box4_x = box3_x - 3*mm - 3*(box_size + box_gap)
        for i in range(3):
            c.rect(box4_x + i*(box_size + box_gap), box_y, box_size, box_size)
        c.drawCentredString(box4_x + 1.5*(box_size + box_gap), box_y - 3*mm, 'สถาบันการเงิน')

        # 横线连接
        c.line(box4_x + 3*(box_size + box_gap) + 0.5*mm, box_y + box_size/2,
               box3_x - 0.5*mm, box_y + box_size/2)

        # เลขที่
        c.drawString(box4_x - 10*mm, box_y + 0.5*mm, 'เลขที่')

        # ========== 区域1和区域2之间：一条粗线 ==========
        y = title_y - 8*mm
        c.setLineWidth(1.5)
        c.line(x_left, y, x_right, y)

        # ========== 区域2：选项区（高度较小）==========
        y -= 2*mm
        zone2_h = 7*mm

        # 左侧复选框
        cb_y = y - 4*mm
        self._checkbox(c, x_left + 3*mm, cb_y, 'รายงานฉบับหลัก')
        self._checkbox(c, x_left + 45*mm, cb_y, 'รายงานฉบับแก้ไข/ เพิ่มเติม ครั้งที่')

        # 下划线
        self._underline(c, x_left + 95*mm, cb_y - 0.5*mm, 15*mm)
        c.setFont('Sarabun', 8)
        c.drawString(x_left + 111*mm, cb_y, 'ลงวันที่')
        self._underline(c, x_left + 125*mm, cb_y - 0.5*mm, 15*mm)

        # 竖线分隔
        div_x = x_left + 115*mm
        c.setLineWidth(0.5)
        c.line(div_x, y - zone2_h, div_x, y)

        # 右侧文字
        c.drawString(div_x + 3*mm, cb_y, 'รวมเอกสารจำนวนทั้งสิ้น')
        self._underline(c, div_x + 38*mm, cb_y - 0.5*mm, 12*mm)
        c.drawString(div_x + 51*mm, cb_y, 'แผ่น')

        # ========== 区域2和区域3之间：粗线 ==========
        y = y - zone2_h - 2*mm
        c.setLineWidth(1.5)
        c.line(x_left, y, x_right, y)

        # ========== 区域3：ส่วนที่ ๑ ==========
        y -= 5*mm

        # 左侧：标题框（灰色背景）
        sec_title_w = 60*mm
        sec_title_h = 7*mm

        c.saveState()
        c.setLineWidth(1)
        c.setStrokeColor(BLACK)
        c.setFillColor(GRAY_BG)
        c.rect(x_left, y - sec_title_h, sec_title_w, sec_title_h, fill=1, stroke=1)

        c.setFillColor(BLACK)
        c.setFont('Sarabun', 10)
        c.drawString(x_left + 2*mm, y - sec_title_h + 2*mm, 'ส่วนที่ ๑. ผู้ทำธุรกรรม')
        c.restoreState()

        # 右侧：13个ID方格
        id_x = x_right - 78*mm
        id_y = y - 5*mm
        self._id_boxes(c, id_x, id_y, 13)

        # ID方格下方：浅灰色背景的说明框
        explain_w = 78*mm
        explain_h = 12*mm
        explain_y = id_y - explain_h - 1*mm

        c.saveState()
        c.setFillColor(GRAY_BG)
        c.rect(id_x, explain_y, explain_w, explain_h, fill=1, stroke=0)

        # 说明文字（黑色，确保可见）
        c.setFillColor(BLACK)
        c.setFont('Sarabun', 6.5)
        explain_lines = [
            'โปรดระบุเลขที่บัตรประจำตัวประชาชน',
            'หากเป็นคนต่างด้าว โปรดระบุเลขที่หนังสือเดินทาง หรือเลขที่',
            'เอกสารประจำตัวอื่นๆ โดยให้กรอกเลขชิดด้านซ้ายเป็นหลัก'
        ]
        text_y = explain_y + explain_h - 3*mm
        for line in explain_lines:
            c.drawString(id_x + 1*mm, text_y, line)
            text_y -= 3.5*mm
        c.restoreState()

        # ส่วนที่ ๑ 的字段内容
        y_field = y - sec_title_h - 3*mm

        # ๑.๑ ชื่อ-นามสกุล
        c.setFont('Sarabun', 8.5)
        c.setFillColor(BLACK)  # 确保文字是黑色
        c.drawString(x_left, y_field, '๑.๑ ชื่อ-นามสกุล')

        y_field -= 5*mm
        # 两个复选框
        self._checkbox(c, x_left + 3*mm, y_field,
                      'ทำธุรกรรมเป็นคนเดียว (ลงลายมือชื่อในการทำธุรกรรมในคนเดียว พ.ศ.๒๕๔๒)')

        y_field -= 5*mm
        self._checkbox(c, x_left + 3*mm, y_field,
                      'มีผู้ร่วมทำธุรกรรม (ให้ระบุชื่อและลงลายมือชื่อในส่วนที่ผู้ลงชื่อในการทำธุรกรรมใน พ.ศ.๒๕๔๒)')

        y_field -= 7*mm
        c.setFillColor(BLACK)
        c.drawString(x_left, y_field, '๑.๒ ชื่อ')
        self._underline(c, x_left + 12*mm, y_field - 0.5*mm, 65*mm)
        c.drawString(x_left + 80*mm, y_field, 'นามสกุล')
        self._underline(c, x_left + 98*mm, y_field - 0.5*mm, 82*mm)

        y_field -= 6*mm
        c.drawString(x_left, y_field, '๑.๓ ชื่อเกิด')
        self._underline(c, x_left + 18*mm, y_field - 0.5*mm, 48*mm)
        c.drawString(x_left + 68*mm, y_field, 'สถานที่เกิดเมือ')
        self._underline(c, x_left + 98*mm, y_field - 0.5*mm, 35*mm)
        c.drawString(x_left + 135*mm, y_field, 'นามสกุล')
        self._underline(c, x_left + 153*mm, y_field - 0.5*mm, 27*mm)

        y_field -= 6*mm
        c.drawString(x_left, y_field, '๑.๔ สัญชาติ')
        self._underline(c, x_left + 18*mm, y_field - 0.5*mm, 162*mm)

        y_field -= 6*mm
        c.drawString(x_left, y_field, '๑.๕ ที่อยู่ที่ติดต่อได้')
        self._underline(c, x_left + 30*mm, y_field - 0.5*mm, 150*mm)

        y_field -= 5*mm
        c.drawString(x_left + 5*mm, y_field, 'ตำบล/แขวง')
        self._underline(c, x_left + 25*mm, y_field - 0.5*mm, 43*mm)
        c.drawString(x_left + 70*mm, y_field, 'อำเภอ/เขต')
        self._underline(c, x_left + 93*mm, y_field - 0.5*mm, 43*mm)
        c.drawString(x_left + 138*mm, y_field, 'จังหวัด')
        self._underline(c, x_left + 155*mm, y_field - 0.5*mm, 25*mm)

        y_field -= 6*mm
        c.drawString(x_left, y_field, '๑.๖ หลักฐานสำหรับยืนยันตัวผู้ทำธุรกรรม:')

        y_field -= 5*mm
        self._checkbox(c, x_left + 3*mm, y_field, 'บัตรประจำตัวประชาชนกรณีเป็นบุคคลธรรมดา')
        self._checkbox(c, x_left + 75*mm, y_field, 'หนังสือเดินทาง')
        self._checkbox(c, x_left + 115*mm, y_field, 'ใบสำคัญประจำตัวคนต่างด้าว')

        y_field -= 5*mm
        self._checkbox(c, x_left + 3*mm, y_field, 'อื่นๆ (โปรดระบุ)')
        self._underline(c, x_left + 33*mm, y_field - 0.5*mm, 55*mm)

        y_field -= 5*mm
        c.drawString(x_left + 5*mm, y_field, 'เลขที่')
        self._underline(c, x_left + 18*mm, y_field - 0.5*mm, 48*mm)
        c.drawString(x_left + 68*mm, y_field, 'ออกให้')
        self._underline(c, x_left + 82*mm, y_field - 0.5*mm, 38*mm)
        c.drawString(x_left + 122*mm, y_field, 'หมดอายุ')
        self._underline(c, x_left + 140*mm, y_field - 0.5*mm, 40*mm)

        # ========== ส่วนที่ ๒ ==========
        y_field -= 10*mm
        c.setLineWidth(1.5)
        c.line(x_left, y_field, x_right, y_field)

        y_field -= 7*mm
        # 标题框
        c.saveState()
        c.setFillColor(GRAY_BG)
        c.rect(x_left, y_field, 115*mm, 7*mm, fill=1, stroke=1)
        c.setFillColor(BLACK)
        c.setFont('Sarabun', 10)
        c.drawString(x_left + 2*mm, y_field + 2*mm,
                    'ส่วนที่ ๒ ผู้ร่วมทำธุรกรรม ผู้รับมอบอาจ หรือผู้ลงมอบอำนาจ')
        c.restoreState()

        # 右侧复选框
        cb_x = x_right - 75*mm
        self._checkbox(c, cb_x, y_field + 4*mm, 'ผู้ร่วมทำธุรกรรม')
        self._checkbox(c, cb_x, y_field + 1*mm, 'ผู้รับมอบอาจ')
        self._checkbox(c, cb_x, y_field - 2*mm, 'ผู้ลงมอบอำนาจ')

        # 13位ID框
        self._id_boxes(c, cb_x, y_field - 8*mm, 13)

        y_field -= 15*mm
        c.setFillColor(BLACK)
        c.drawString(x_left, y_field, '๒.๑ ชื่อ')
        self._underline(c, x_left + 12*mm, y_field - 0.5*mm, 168*mm)

        # 更多字段...
        y_field -= 6*mm
        c.drawString(x_left, y_field, '๒.๒ ชื่อเกิด-นามสกุล')
        self._underline(c, x_left + 35*mm, y_field - 0.5*mm, 145*mm)

        # ========== ส่วนที่ ๓ ==========
        y_field -= 10*mm
        c.setLineWidth(1.5)
        c.line(x_left, y_field, x_right, y_field)

        y_field -= 7*mm
        c.saveState()
        c.setFillColor(GRAY_BG)
        c.rect(x_left, y_field, 85*mm, 7*mm, fill=1, stroke=1)
        c.setFillColor(BLACK)
        c.setFont('Sarabun', 10)
        c.drawString(x_left + 2*mm, y_field + 2*mm, 'ส่วนที่ ๓ ข้อเท็จจริงเกี่ยวกับธุรกรรม')
        c.restoreState()

        # 右侧日期
        c.setFont('Sarabun', 8)
        c.drawString(x_right - 75*mm, y_field + 3*mm, 'วันที่ทำธุรกรรม')
        self._underline(c, x_right - 40*mm, y_field + 2.5*mm, 15*mm)
        c.drawString(x_right - 23*mm, y_field + 3*mm, 'เดือน')
        self._underline(c, x_right - 10*mm, y_field + 2.5*mm, 10*mm)

        y_field -= 10*mm
        c.drawString(x_left, y_field, '๓.๑ ประเภทของธุรกรรม')

        # 左右两列交易表格
        y_field -= 8*mm

        # 左列：ฝากเงิน
        left_x = x_left
        left_w = 85*mm

        c.setFont('Sarabun', 9)
        self._checkbox(c, left_x, y_field, 'ฝากเงิน')
        c.drawString(left_x + 70*mm, y_field + 0.5*mm, 'จำนวน (บาท)')

        y_field -= 6*mm
        self._checkbox(c, left_x + 3*mm, y_field, 'เงินสด')

        y_field -= 5*mm
        c.setFont('Sarabun', 8)
        c.drawString(left_x + 5*mm, y_field, 'สกุลเงินต่างประเทศ')
        # 8个方格
        for i in range(8):
            c.rect(left_x + 38*mm + i*5.5*mm, y_field - 1*mm, 4.5*mm, 4.5*mm)

        # 竖虚线
        c.setDash(2, 2)
        c.line(left_x + 82*mm, y_field + 8*mm, left_x + 82*mm, y_field - 30*mm)
        c.setDash()

        y_field -= 6*mm
        c.drawString(left_x + 5*mm, y_field, 'จำนวนเงิน')
        self._underline(c, left_x + 22*mm, y_field - 0.5*mm, 55*mm)

        # 右列：ถอนเงิน（对称）
        right_x = left_x + left_w + 8*mm
        y_right = y_field + 18*mm

        self._checkbox(c, right_x, y_right, 'ถอนเงิน')
        c.setFont('Sarabun', 9)
        c.drawString(right_x + 70*mm, y_right + 0.5*mm, 'จำนวน (บาท)')

        # （类似左列...）

        # ========== ส่วนที่ ๔ ==========
        y_field -= 25*mm
        c.setLineWidth(1.5)
        c.line(x_left, y_field, x_right, y_field)

        y_field -= 7*mm
        c.saveState()
        c.setFillColor(GRAY_BG)
        c.rect(x_left, y_field, 30*mm, 7*mm, fill=1, stroke=1)
        c.setFillColor(BLACK)
        c.setFont('Sarabun', 10)
        c.drawString(x_left + 2*mm, y_field + 2*mm, 'ส่วนที่ ๔')
        c.restoreState()

        # 签名区域...
        y_field -= 10*mm
        c.setFont('Sarabun', 8)
        c.drawString(x_left, y_field, 'ลงชื่อ')
        self._underline(c, x_left + 15*mm, y_field - 0.5*mm, 50*mm)
        c.drawString(x_left + 68*mm, y_field, 'ผู้รายงาน')

        # 页脚
        c.setFont('Sarabun', 7)
        c.drawRightString(x_right, MARGIN_CONTENT, '(ทำแบบให้นี้ที่เกิดทำการบัญชี)')

        # 保存
        c.save()
        return output_path


if __name__ == '__main__':
    gen = AMLO101ExactGenerator()
    output = 'test_exact.pdf'
    gen.generate({}, output)
    print(f"Generated: {output}")
