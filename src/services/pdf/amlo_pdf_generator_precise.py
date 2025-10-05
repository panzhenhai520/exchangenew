# -*- coding: utf-8 -*-
"""
AMLO PDF生成器 - 精确版本
1:1精确复制标准报告的每个元素、位置、间距、颜色
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from datetime import datetime
import os
from typing import Dict, List, Optional

# A4页面尺寸
PAGE_WIDTH, PAGE_HEIGHT = A4  # 210mm x 297mm

# 精确的颜色定义
COLOR_BLACK = HexColor('#000000')
COLOR_LIGHT_GRAY = HexColor('#D3D3D3')  # 浅灰色背景
COLOR_WHITE = HexColor('#FFFFFF')

# 字体配置
FONT_NAME_TH = 'Sarabun'
FONT_NAME_EN = 'Helvetica'

# 精确的边距（缩小以留出更多内容空间）
BORDER_OUTER = 8*mm      # 外边框距离页面边缘
BORDER_MIDDLE = 9*mm     # 中边框（+1mm）
BORDER_INNER = 10*mm     # 内边框（+1mm）
CONTENT_LEFT = 15*mm     # 内容左边距
CONTENT_RIGHT = PAGE_WIDTH - 15*mm  # 内容右边距
CONTENT_TOP = PAGE_HEIGHT - 15*mm   # 内容上边距

class AMLOPDFGeneratorPrecise:
    """AMLO PDF生成器 - 精确1:1复制标准格式"""

    def __init__(self):
        """初始化"""
        self.thai_font_available = self._register_fonts()
        if not self.thai_font_available:
            global FONT_NAME_TH
            FONT_NAME_TH = 'Helvetica'

    def _register_fonts(self):
        """注册泰语字体"""
        try:
            font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'Sarabun-Regular.ttf')
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('Sarabun', font_path))
                font_bold_path = os.path.join(os.path.dirname(__file__), 'fonts', 'Sarabun-Bold.ttf')
                if os.path.exists(font_bold_path):
                    pdfmetrics.registerFont(TTFont('Sarabun-Bold', font_bold_path))
                print("[OK] Thai font registered")
                return True
            return False
        except Exception as e:
            print(f"Font error: {e}")
            return False

    def _draw_triple_border(self, c: canvas.Canvas):
        """绘制三层边框 - 间距1mm"""
        c.saveState()

        # 外层细线
        c.setLineWidth(0.5)
        c.setStrokeColor(COLOR_BLACK)
        c.rect(BORDER_OUTER, BORDER_OUTER,
               PAGE_WIDTH - 2*BORDER_OUTER,
               PAGE_HEIGHT - 2*BORDER_OUTER)

        # 中层粗线
        c.setLineWidth(2.5)
        c.rect(BORDER_MIDDLE, BORDER_MIDDLE,
               PAGE_WIDTH - 2*BORDER_MIDDLE,
               PAGE_HEIGHT - 2*BORDER_MIDDLE)

        # 内层细线
        c.setLineWidth(0.5)
        c.rect(BORDER_INNER, BORDER_INNER,
               PAGE_WIDTH - 2*BORDER_INNER,
               PAGE_HEIGHT - 2*BORDER_INNER)

        c.restoreState()

    def _draw_zone1_title(self, c: canvas.Canvas):
        """
        绘制分区1：标题区域
        - 左侧：灰色背景标题框 + 说明文字
        - 右侧：报告编号方格结构
        """
        y_start = CONTENT_TOP

        # === 左侧：标题框（黑边框 + 浅灰色背景）===
        title_x = CONTENT_LEFT
        title_y = y_start - 12*mm
        title_width = 110*mm
        title_height = 10*mm

        c.saveState()

        # 绘制边框
        c.setLineWidth(1.5)
        c.setStrokeColor(COLOR_BLACK)
        c.setFillColor(COLOR_LIGHT_GRAY)
        c.rect(title_x, title_y, title_width, title_height, fill=1, stroke=1)

        # 标题文字（黑色）
        c.setFillColor(COLOR_BLACK)
        c.setFont(FONT_NAME_TH, 14)
        c.drawCentredString(title_x + title_width/2, title_y + 3*mm,
                           'แบบรายงานการทำธุรกรรมที่ใช้เงินสด')

        c.restoreState()

        # 说明文字（标题框下方）
        c.setFont(FONT_NAME_TH, 7)
        c.drawString(title_x, title_y - 4*mm,
                    '(โปรดกาเครื่องหมาย ✓ หน้าข้อที่เลือกและระบุข้อความตามที่กำหนดไว้ทุกข้อ)')

        # === 右侧：报告编号方格结构 ===
        # 从右向左排列：3框-3框-2框-长框
        right_x = CONTENT_RIGHT
        box_y = y_start - 8*mm
        box_size = 4*mm
        box_gap = 0.5*mm

        # 最上方：แบบ ปปง. ๑-๐๑
        c.setFont(FONT_NAME_TH, 9)
        c.drawRightString(right_x, box_y + 10*mm, 'แบบ ปปง. ๑-๐๑')

        # 长框（最右侧）
        long_box_width = 50*mm
        long_box_x = right_x - long_box_width
        c.setLineWidth(0.5)
        c.rect(long_box_x, box_y, long_box_width, box_size)
        c.setFont(FONT_NAME_TH, 7)
        c.drawString(long_box_x + 2*mm, box_y + 5*mm, 'เลขลำดับรายงาน')

        # 2个方格（左侧）
        box2_x = long_box_x - 3*mm - 2*(box_size + box_gap)
        for i in range(2):
            c.rect(box2_x + i*(box_size + box_gap), box_y, box_size, box_size)
        # 下方标签
        c.setFont(FONT_NAME_TH, 6)
        c.drawCentredString(box2_x + box_size, box_y - 3*mm, 'ปี พ.ศ(ใช้ ๒ หลักสุดท้าย)')

        # 横线连接
        c.line(long_box_x - 1*mm, box_y + box_size/2,
               box2_x + 2*(box_size + box_gap) + 1*mm, box_y + box_size/2)

        # 3个方格（สาขา）
        box3_x = box2_x - 3*mm - 3*(box_size + box_gap)
        for i in range(3):
            c.rect(box3_x + i*(box_size + box_gap), box_y, box_size, box_size)
        c.setFont(FONT_NAME_TH, 7)
        c.drawCentredString(box3_x + 1.5*box_size, box_y - 3*mm, 'สาขา')

        # 横线连接
        c.line(box2_x - 1*mm, box_y + box_size/2,
               box3_x + 3*(box_size + box_gap) + 1*mm, box_y + box_size/2)

        # 3个方格（สถาบันการเงิน）
        box4_x = box3_x - 3*mm - 3*(box_size + box_gap)
        for i in range(3):
            c.rect(box4_x + i*(box_size + box_gap), box_y, box_size, box_size)
        c.drawCentredString(box4_x + 1.5*box_size, box_y - 3*mm, 'สถาบันการเงิน')

        # 横线连接
        c.line(box3_x - 1*mm, box_y + box_size/2,
               box4_x + 3*(box_size + box_gap) + 1*mm, box_y + box_size/2)

        # เลขที่ 标签
        c.drawString(box4_x - 12*mm, box_y + 1*mm, 'เลขที่')

        return title_y - 8*mm  # 返回下一区域的Y坐标

    def _draw_zone2_options(self, c: canvas.Canvas, y_start: float):
        """
        绘制分区2：选项区域（较窄）
        - 三条细横线作为分隔
        - 左侧：รายงานฉบับหลัก/แก้ไข
        - 竖线分隔
        - 右侧：รวมเอกสาร
        """
        # 三条细横线（间距小）
        line_y = y_start
        for i in range(3):
            c.setLineWidth(0.3)
            c.line(CONTENT_LEFT, line_y - i*0.8*mm,
                   CONTENT_RIGHT, line_y - i*0.8*mm)

        # 内容区域（较窄）
        content_y = line_y - 3*mm
        zone_height = 8*mm

        # 左侧复选框
        checkbox_size = 3*mm
        c.setLineWidth(0.5)

        # รายงานฉบับหลัก
        c.rect(CONTENT_LEFT + 5*mm, content_y, checkbox_size, checkbox_size)
        c.setFont(FONT_NAME_TH, 9)
        c.drawString(CONTENT_LEFT + 10*mm, content_y + 0.5*mm, 'รายงานฉบับหลัก')

        # รายงานฉบับแก้ไข
        c.rect(CONTENT_LEFT + 50*mm, content_y, checkbox_size, checkbox_size)
        c.drawString(CONTENT_LEFT + 55*mm, content_y + 0.5*mm,
                    'รายงานฉบับแก้ไข/ เพิ่มเติม ครั้งที่')

        # 下划线
        c.setLineWidth(0.3)
        c.line(CONTENT_LEFT + 108*mm, content_y,
               CONTENT_LEFT + 125*mm, content_y)
        c.drawString(CONTENT_LEFT + 127*mm, content_y + 0.5*mm, 'ลงวันที่')
        c.line(CONTENT_LEFT + 143*mm, content_y,
               CONTENT_LEFT + 160*mm, content_y)

        # 竖线分隔
        divider_x = CONTENT_LEFT + 125*mm
        c.setLineWidth(0.5)
        c.line(divider_x, content_y - 1*mm, divider_x, content_y + zone_height - 1*mm)

        # 右侧文字
        c.drawString(divider_x + 3*mm, content_y + 0.5*mm,
                    'รวมเอกสารจำนวนทั้งสิ้น')
        c.line(divider_x + 45*mm, content_y,
               divider_x + 58*mm, content_y)
        c.drawString(divider_x + 60*mm, content_y + 0.5*mm, 'แผ่น')

        return content_y - zone_height

    def _draw_zone3_section1(self, c: canvas.Canvas, y_start: float):
        """
        绘制分区3：ส่วนที่ ๑. ผู้ทำธุรกรรม
        - 粗线分隔
        - 灰色背景标题框
        - 右侧13位ID方格 + 说明
        """
        # 粗线分隔
        c.setLineWidth(2)
        c.line(CONTENT_LEFT, y_start, CONTENT_RIGHT, y_start)

        y_current = y_start - 8*mm

        # 标题框（黑边框 + 浅灰色背景）
        title_width = 65*mm
        title_height = 7*mm

        c.saveState()
        c.setLineWidth(1.5)
        c.setStrokeColor(COLOR_BLACK)
        c.setFillColor(COLOR_LIGHT_GRAY)
        c.rect(CONTENT_LEFT, y_current, title_width, title_height, fill=1, stroke=1)

        c.setFillColor(COLOR_BLACK)
        c.setFont(FONT_NAME_TH, 11)
        c.drawString(CONTENT_LEFT + 2*mm, y_current + 2*mm, 'ส่วนที่ ๑. ผู้ทำธุรกรรม')
        c.restoreState()

        # 右侧：13位ID方格
        id_box_x = CONTENT_RIGHT - 78*mm
        id_box_y = y_current + 1*mm
        box_size = 5*mm
        box_gap = 0.8*mm

        for i in range(13):
            c.setLineWidth(0.5)
            c.setFillColor(COLOR_WHITE)
            c.rect(id_box_x + i*(box_size + box_gap), id_box_y,
                   box_size, box_size, fill=1, stroke=1)

        # 说明文字（13个方格正下方）
        explain_y = id_box_y - 4*mm
        c.setFont(FONT_NAME_TH, 6)
        explain_text = [
            'โปรดระบุเลขที่บัตรประจำตัวประชาชน',
            'หากเป็นคนต่างด้าว โปรดระบุเลขที่หนังสือเดินทาง หรือเลขที่',
            'เอกสารประจำตัวอื่นๆ โดยให้กรอกเลขชิดด้านซ้ายเป็นหลัก'
        ]
        for i, line in enumerate(explain_text):
            c.drawString(id_box_x, explain_y - i*3*mm, line)

        # === ส่วนที่ 1 的内容字段 ===
        y_field = y_current - 10*mm

        # ๑.๑ ชื่อ-นามสกุล
        c.setFont(FONT_NAME_TH, 9)
        c.drawString(CONTENT_LEFT, y_field, '๑.๑ ชื่อ-นามสกุล')

        y_field -= 5*mm
        # 复选框
        checkbox_size = 3*mm
        c.rect(CONTENT_LEFT + 5*mm, y_field, checkbox_size, checkbox_size)
        c.setFont(FONT_NAME_TH, 8)
        c.drawString(CONTENT_LEFT + 10*mm, y_field + 0.5*mm,
                    'ทำธุรกรรมเป็นคนเดียว (ลงลายมือชื่อในการทำธุรกรรมในคนเดียว พ.ศ.๒๕๔๒)')

        y_field -= 5*mm
        c.rect(CONTENT_LEFT + 5*mm, y_field, checkbox_size, checkbox_size)
        c.drawString(CONTENT_LEFT + 10*mm, y_field + 0.5*mm,
                    'มีผู้ร่วมทำธุรกรรม (ให้ระบุชื่อและลงลายมือชื่อในส่วนที่ผู้ลงชื่อในการทำธุรกรรมใน พ.ศ.๒๕๔๒)')

        y_field -= 7*mm
        c.drawString(CONTENT_LEFT, y_field, '๑.๒ ชื่อ')
        c.setLineWidth(0.3)
        c.line(CONTENT_LEFT + 15*mm, y_field - 1*mm,
               CONTENT_LEFT + 85*mm, y_field - 1*mm)
        c.drawString(CONTENT_LEFT + 90*mm, y_field, 'นามสกุล')
        c.line(CONTENT_LEFT + 110*mm, y_field - 1*mm,
               CONTENT_RIGHT - 5*mm, y_field - 1*mm)

        y_field -= 6*mm
        c.drawString(CONTENT_LEFT, y_field, '๑.๓ ชื่อเกิด')
        c.line(CONTENT_LEFT + 20*mm, y_field - 1*mm,
               CONTENT_LEFT + 70*mm, y_field - 1*mm)
        c.drawString(CONTENT_LEFT + 75*mm, y_field, 'สถานที่เกิดเมือ')
        c.line(CONTENT_LEFT + 110*mm, y_field - 1*mm,
               CONTENT_LEFT + 140*mm, y_field - 1*mm)
        c.drawString(CONTENT_LEFT + 145*mm, y_field, 'นามสกุล')
        c.line(CONTENT_LEFT + 165*mm, y_field - 1*mm,
               CONTENT_RIGHT - 5*mm, y_field - 1*mm)

        y_field -= 6*mm
        c.drawString(CONTENT_LEFT, y_field, '๑.๔ สัญชาติ')
        c.line(CONTENT_LEFT + 20*mm, y_field - 1*mm,
               CONTENT_RIGHT - 5*mm, y_field - 1*mm)

        y_field -= 6*mm
        c.drawString(CONTENT_LEFT, y_field, '๑.๕ ที่อยู่ที่ติดต่อได้')
        c.line(CONTENT_LEFT + 35*mm, y_field - 1*mm,
               CONTENT_RIGHT - 5*mm, y_field - 1*mm)

        y_field -= 5*mm
        c.drawString(CONTENT_LEFT + 5*mm, y_field, 'ตำบล/แขวง')
        c.line(CONTENT_LEFT + 25*mm, y_field - 1*mm,
               CONTENT_LEFT + 70*mm, y_field - 1*mm)
        c.drawString(CONTENT_LEFT + 75*mm, y_field, 'อำเภอ/เขต')
        c.line(CONTENT_LEFT + 100*mm, y_field - 1*mm,
               CONTENT_LEFT + 145*mm, y_field - 1*mm)
        c.drawString(CONTENT_LEFT + 150*mm, y_field, 'จังหวัด')
        c.line(CONTENT_LEFT + 167*mm, y_field - 1*mm,
               CONTENT_RIGHT - 5*mm, y_field - 1*mm)

        # 继续添加更多字段...
        y_field -= 6*mm
        c.drawString(CONTENT_LEFT, y_field, '๑.๖ หลักฐานสำหรับยืนยันตัวผู้ทำธุรกรรม:')

        y_field -= 5*mm
        c.rect(CONTENT_LEFT + 5*mm, y_field, checkbox_size, checkbox_size)
        c.drawString(CONTENT_LEFT + 10*mm, y_field + 0.5*mm,
                    'บัตรประจำตัวประชาชนกรณีเป็นบุคคลธรรมดา')
        c.rect(CONTENT_LEFT + 80*mm, y_field, checkbox_size, checkbox_size)
        c.drawString(CONTENT_LEFT + 85*mm, y_field + 0.5*mm, 'หนังสือเดินทาง')
        c.rect(CONTENT_LEFT + 125*mm, y_field, checkbox_size, checkbox_size)
        c.drawString(CONTENT_LEFT + 130*mm, y_field + 0.5*mm,
                    'ใบสำคัญประจำตัวคนต่างด้าว')

        y_field -= 5*mm
        c.rect(CONTENT_LEFT + 5*mm, y_field, checkbox_size, checkbox_size)
        c.drawString(CONTENT_LEFT + 10*mm, y_field + 0.5*mm, 'อื่นๆ (โปรดระบุ)')
        c.line(CONTENT_LEFT + 40*mm, y_field - 1*mm,
               CONTENT_LEFT + 100*mm, y_field - 1*mm)

        y_field -= 5*mm
        c.drawString(CONTENT_LEFT + 5*mm, y_field, 'เลขที่')
        c.line(CONTENT_LEFT + 20*mm, y_field - 1*mm,
               CONTENT_LEFT + 70*mm, y_field - 1*mm)
        c.drawString(CONTENT_LEFT + 75*mm, y_field, 'ออกให้')
        c.line(CONTENT_LEFT + 90*mm, y_field - 1*mm,
               CONTENT_LEFT + 130*mm, y_field - 1*mm)
        c.drawString(CONTENT_LEFT + 135*mm, y_field, 'หมดอายุ')
        c.line(CONTENT_LEFT + 153*mm, y_field - 1*mm,
               CONTENT_RIGHT - 5*mm, y_field - 1*mm)

        return y_field - 10*mm

    def generate_amlo_101(self, data: Dict, output_path: str) -> str:
        """生成AMLO-1-01报告 - 精确版本"""
        c = canvas.Canvas(output_path, pagesize=A4)

        # 1. 三层边框
        self._draw_triple_border(c)

        # 2. 分区1：标题区域
        y_pos = self._draw_zone1_title(c)

        # 3. 分区2：选项区域
        y_pos = self._draw_zone2_options(c, y_pos)

        # 4. 分区3：ส่วนที่ ๑
        y_pos = self._draw_zone3_section1(c, y_pos)

        # TODO: 继续添加 ส่วนที่ ๒, ๓, ๔

        # 保存
        c.save()
        return output_path


if __name__ == '__main__':
    generator = AMLOPDFGeneratorPrecise()
    test_data = {
        'report_number': '001-0001-25',
        'maker_id': '1234567890123'
    }
    output = 'test_precise.pdf'
    generator.generate_amlo_101(test_data, output)
    print(f"Generated: {output}")
