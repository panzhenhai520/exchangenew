# -*- coding: utf-8 -*-
"""
AMLO PDF表单填充服务 - 使用ReportLab绘制覆盖层
这种方式比直接填充表单字段更可靠，能正确显示中文、泰文、英文

参考原始的 amlo_form_filler.py 实现
"""

import os
from typing import Any, Dict
from pdfrw import PdfReader, PdfWriter, PageMerge
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO

try:
    from .amlo_csv_field_loader import get_csv_field_loader
except ImportError:
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from amlo_csv_field_loader import get_csv_field_loader


class AMLOPDFFillerOverlay:
    """AMLO PDF 表单填充器 - 使用覆盖层方式"""

    def __init__(self) -> None:
        self.csv_loader = get_csv_field_loader()
        self._register_fonts()
        print("[AMLOPDFFillerOverlay] Initialized with CSV field mappings")

    def _register_fonts(self):
        """注册字体"""
        try:
            # 泰文字体
            sarabun_path = os.path.join(os.path.dirname(__file__), 'fonts', 'Sarabun-Regular.ttf')
            if os.path.exists(sarabun_path):
                pdfmetrics.registerFont(TTFont('Sarabun', sarabun_path))
                self.thai_font = 'Sarabun'
                print("[AMLOPDFFillerOverlay] Thai font registered: Sarabun")
            else:
                self.thai_font = 'Helvetica'
                print("[AMLOPDFFillerOverlay] Thai font not found, using Helvetica")

            # 中文字体
            simhei_path = r'C:\Windows\Fonts\simhei.ttf'
            if os.path.exists(simhei_path):
                pdfmetrics.registerFont(TTFont('SimHei', simhei_path))
                self.chinese_font = 'SimHei'
                print("[AMLOPDFFillerOverlay] Chinese font registered: SimHei")
            else:
                self.chinese_font = 'Helvetica'
                print("[AMLOPDFFillerOverlay] Chinese font not found, using Helvetica")

        except Exception as e:
            print(f"[AMLOPDFFillerOverlay] Font registration error: {e}")
            self.thai_font = 'Helvetica'
            self.chinese_font = 'Helvetica'

    def fill_form(self, report_type: str, data: Dict[str, Any], output_path: str, flatten: bool = False) -> str:
        """填充表单（flatten参数仅为兼容性保留，覆盖层方式本身就是静态的）

        Args:
            report_type: 报告类型 (e.g., 'AMLO-1-01')
            data: 字段数据字典
            output_path: 输出PDF路径
            flatten: 兼容参数，覆盖层方式本身就不可编辑

        Returns:
            生成的PDF文件路径
        """
        try:
            template_path = self.csv_loader.get_template_path(report_type)
            print(f"[AMLOPDFFillerOverlay] Using template: {template_path}")

            if not os.path.exists(template_path):
                raise FileNotFoundError(f"Template not found: {template_path}")

            field_mapping = self.csv_loader.get_field_mapping(report_type)

            # 创建覆盖层PDF（仅包含文本，不包含复选框）
            overlay_buffer, checkbox_data = self._create_overlay_pdf(data, field_mapping, template_path)

            # 合并模板和覆盖层（同时填充复选框）
            self._merge_pdfs(template_path, overlay_buffer, checkbox_data, output_path)

            print(f"[AMLOPDFFillerOverlay] PDF generated: {output_path}")
            return output_path

        except Exception as exc:
            print(f"[AMLOPDFFillerOverlay] Error filling form: {exc}")
            import traceback
            traceback.print_exc()
            raise

    def _create_overlay_pdf(self, data: Dict[str, Any], field_mapping: Dict, template_path: str) -> tuple:
        """创建覆盖层PDF

        Returns:
            tuple: (overlay_buffer, checkbox_data) - 覆盖层PDF和复选框数据
        """
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)

        # 读取模板以获取字段位置
        import fitz
        doc = fitz.open(template_path)
        page = doc[0]

        filled_count = 0
        checkbox_data = {}  # 保存复选框数据，用于后续填充
        widgets = list(page.widgets()) if page.widgets() else []

        for widget in widgets:
            field_name = widget.field_name
            if not field_name or field_name not in data:
                continue

            value = data[field_name]
            if value is None or value == '':
                continue

            field_type = widget.field_type
            rect = widget.rect

            try:
                if field_type == fitz.PDF_WIDGET_TYPE_TEXT:
                    # 文本字段：在字段位置绘制文本
                    str_value = str(value)
                    self._draw_text_on_canvas(c, rect, str_value, widget)
                    filled_count += 1

                elif field_type == fitz.PDF_WIDGET_TYPE_CHECKBOX:
                    # 复选框：保存数据，稍后填充到表单字段
                    if value in (True, 'true', '1', 1, 'yes', 'Yes', '/Yes'):
                        checkbox_data[field_name] = True
                        filled_count += 1

            except Exception as e:
                print(f"[AMLOPDFFillerOverlay] Error drawing field {field_name}: {e}")

        doc.close()
        c.save()
        buffer.seek(0)

        print(f"[AMLOPDFFillerOverlay] Drew {filled_count} fields on overlay (text only)")
        return buffer, checkbox_data

    def _draw_text_on_canvas(self, c: canvas.Canvas, rect, text: str, widget):
        """在canvas上绘制文本"""
        field_name = widget.field_name if hasattr(widget, 'field_name') else ''

        # 特殊处理：报告编号（分四段显示在框内）
        if field_name == 'fill_52':
            self._draw_report_number(c, rect, text)
            return

        # 特殊处理：comb字段（证件编号等）- 使用精确框位置
        if field_name and field_name.startswith('comb_'):
            self._draw_comb_field(c, rect, text, field_name)
            return

        # 特殊处理：身份证号等多字符框字段
        if field_name in ['fill_56']:  # 身份证号字段
            self._draw_multi_char_boxes(c, rect, text, widget)
            return

        # ReportLab坐标系统：从页面底部开始
        # PyMuPDF rect: (x0, y0, x1, y1) 从页面顶部开始
        # 转换坐标：ReportLab_y = PageHeight - PyMuPDF_y

        page_height = A4[1]  # 页面高度

        # 转换坐标
        x = rect.x0
        y = page_height - rect.y1  # 底部Y坐标
        width = rect.width
        height = rect.height

        # 选择字体
        font_name = self._select_font_for_text(text)
        font_size = widget.text_fontsize if widget.text_fontsize and widget.text_fontsize > 0 else 10

        # 特殊处理：泰文金额大写字段 - 根据文本长度自适应字体大小
        if field_name in ['left_amount', 'right_amount']:
            font_size = self._calculate_adaptive_font_size(c, text, font_name, width, font_size)

        # 设置字体
        c.setFont(font_name, font_size)

        # 获取对齐方式
        try:
            align = widget.text_align if hasattr(widget, 'text_align') else 0
        except:
            align = 0

        # 计算文本位置
        if align == 1:  # 居中
            text_width = c.stringWidth(text, font_name, font_size)
            x = x + (width - text_width) / 2
        elif align == 2:  # 右对齐
            text_width = c.stringWidth(text, font_name, font_size)
            x = x + width - text_width - 2
        else:  # 左对齐
            x = x + 2

        # Y坐标调整：从底部向上偏移一点以垂直居中
        y = y + 2

        # 绘制文本
        c.drawString(x, y, text)

    def _draw_checkbox_on_canvas(self, c: canvas.Canvas, rect):
        """在canvas上绘制复选框勾选标记"""
        page_height = A4[1]

        # 转换坐标：ReportLab从底部开始，PyMuPDF从顶部开始
        x0 = rect.x0
        y0 = page_height - rect.y1  # 底部Y坐标
        width = rect.width
        height = rect.height

        # 使用ZapfDingbats字体绘制勾选标记
        # ZapfDingbats字符:
        # '4' = ✔ (粗勾号)
        # '3' = ✗ (X符号)
        # 'ü' = ✓ (细勾号)

        font_size = height * 0.75  # 使用框高度的75%作为字体大小
        c.setFont('ZapfDingbats', font_size)

        # 计算居中位置
        mark_char = '4'  # 使用粗勾号
        mark_width = c.stringWidth(mark_char, 'ZapfDingbats', font_size)

        # 水平居中，垂直略微向上偏移
        x = x0 + (width - mark_width) / 2
        y = y0 + height * 0.15  # 向上偏移15%

        # 设置黑色
        c.setFillColorRGB(0, 0, 0)

        c.drawString(x, y, mark_char)

    def _calculate_adaptive_font_size(self, c: canvas.Canvas, text: str, font_name: str,
                                      max_width: float, initial_size: float) -> float:
        """根据文本长度计算自适应字体大小"""
        if not text:
            return initial_size

        # 从初始大小开始测试
        font_size = initial_size
        min_size = 6  # 最小字体大小

        # 留出一些边距
        available_width = max_width - 4

        while font_size > min_size:
            text_width = c.stringWidth(text, font_name, font_size)
            if text_width <= available_width:
                return font_size
            font_size -= 0.5

        return min_size

    def _draw_report_number(self, c: canvas.Canvas, rect, text: str):
        """绘制报告编号，将每个字符显示在对应的框内

        报告编号格式: 001-001-68-110045USD
        分四段: [3位]-[3位]-[2位]-[序列号]

        根据实际PDF模板测量的框位置：
        - 框宽度: 16.3pt
        - 第1-3框: x0=305.28, 321.48, 337.74
        - 间距1: 8.1pt (337.74+16.32 = 354.06, 362.16-354.06 = 8.1)
        - 第4-6框: x0=362.16, 378.48, 394.68
        - 间距2: 8.04pt
        - 第7-8框: x0=419.04, 435.30
        - 间距3: 11.94pt
        - 序列号框: x0=463.56, width=108.06
        """
        page_height = A4[1]

        # 解析报告编号
        parts = text.strip().split('-')
        if len(parts) >= 4:
            group1 = parts[0][-3:].zfill(3)  # 前3位
            group2 = parts[1][-3:].zfill(3)  # 中3位
            group3 = parts[2][-2:].zfill(2)  # 2位
            serial = '-'.join(parts[3:])     # 剩余部分（序列号+货币）
        else:
            # 备用解析方式
            clean_text = text.replace('-', '')
            if len(clean_text) >= 8:
                group1 = clean_text[:3]
                group2 = clean_text[3:6]
                group3 = clean_text[6:8]
                serial = clean_text[8:]
            else:
                # 如果格式不对，直接显示
                y = page_height - rect.y1 + 2
                c.setFont('Helvetica', 10)
                c.drawString(rect.x0 + 2, y, text)
                return

        # 根据实际测量的框位置（绝对坐标）
        # rect.x0 = 303.71, 第一个框从305.28开始
        box_positions = [
            305.28, 321.48, 337.74,  # 第一组 (3位)
            362.16, 378.48, 394.68,  # 第二组 (3位)
            419.04, 435.30,          # 第三组 (2位)
        ]
        serial_box_x0 = 463.56
        serial_box_width = 108.06

        box_width = 16.32  # 框宽度

        # Y坐标（垂直居中）
        y = page_height - rect.y1 + 7

        # 字体设置
        font_size = 11
        c.setFont('Helvetica', font_size)

        # 合并所有数字
        all_digits = group1 + group2 + group3

        # 绘制8个数字框
        for i, char in enumerate(all_digits):
            if i < len(box_positions):
                x_center = box_positions[i] + box_width / 2
                c.drawCentredString(x_center, y, char)

        # 绘制序列号
        if serial:
            # 序列号在专用框内居中
            serial_x = serial_box_x0 + 2  # 左对齐，留小边距
            c.drawString(serial_x, y, serial)

    def _draw_comb_field(self, c: canvas.Canvas, rect, text: str, field_name: str):
        """绘制comb字段（证件编号等），每个字符精确显示在对应框内

        根据实际测量的框位置：
        - comb_1: 13个框，x0=377.40起，框宽14.46，无间距
        - comb_2: 13个框，x0=380.28起，框宽14.46，无间距
        - comb_3: 10个框，x0=75.18起，框宽14.46，无间距
        - comb_4: 10个框，x0=345.60起，框宽14.46，无间距
        - comb_5: 10个框，x0=75.18起，框宽14.46，无间距
        - comb_6: 10个框，x0=345.60起，框宽14.46，无间距
        """
        page_height = A4[1]

        # 清理文本
        clean_text = str(text).replace('-', '').replace(' ', '').strip()
        if not clean_text:
            return

        # 定义每个comb字段的框位置（精确测量值）
        comb_configs = {
            'comb_1': {
                'boxes': [377.40, 391.80, 406.20, 420.60, 435.00, 449.40, 463.80,
                         478.20, 492.60, 507.00, 521.40, 535.80, 550.20],
                'box_width': 14.46,
                'max_chars': 13
            },
            'comb_2': {
                'boxes': [380.28, 394.68, 409.08, 423.48, 437.88, 452.28, 466.68,
                         481.08, 495.48, 509.88, 524.28, 538.68, 553.08],
                'box_width': 14.46,
                'max_chars': 13
            },
            'comb_3': {
                'boxes': [75.18, 89.58, 103.98, 118.38, 132.78, 147.18, 161.58,
                         175.98, 190.38, 204.78],
                'box_width': 14.46,
                'max_chars': 10
            },
            'comb_4': {
                'boxes': [345.60, 360.00, 374.40, 388.80, 403.20, 417.60, 432.00,
                         446.40, 460.80, 475.20],
                'box_width': 14.46,
                'max_chars': 10
            },
            'comb_5': {
                'boxes': [75.18, 89.58, 103.98, 118.38, 132.78, 147.18, 161.58,
                         175.98, 190.38, 204.78],
                'box_width': 14.46,
                'max_chars': 10
            },
            'comb_6': {
                'boxes': [345.60, 360.00, 374.40, 388.80, 403.20, 417.60, 432.00,
                         446.40, 460.80, 475.20],
                'box_width': 14.46,
                'max_chars': 10
            },
        }

        # 获取当前字段的配置
        config = comb_configs.get(field_name)
        if not config:
            # 如果没有配置，使用通用方法
            self._draw_multi_char_boxes(c, rect, text, None)
            return

        box_positions = config['boxes']
        box_width = config['box_width']
        max_chars = config['max_chars']

        # 限制字符数量
        chars_to_draw = clean_text[:max_chars]

        # Y坐标（垂直居中）
        y = page_height - rect.y1 + (rect.height / 2) - 2

        # 字体设置
        font_size = min(10, rect.height * 0.65)
        c.setFont('Helvetica', font_size)

        # 绘制每个字符
        for i, char in enumerate(chars_to_draw):
            if i < len(box_positions):
                x_center = box_positions[i] + box_width / 2
                c.drawCentredString(x_center, y, char)

    def _draw_multi_char_boxes(self, c: canvas.Canvas, rect, text: str, widget):
        """绘制多字符框字段（如身份证号），每个字符显示在对应框内"""
        page_height = A4[1]

        # 清理文本（去除空格、破折号等）
        clean_text = str(text).replace('-', '').replace(' ', '').strip()

        if not clean_text:
            return

        # 字段总宽度
        total_width = rect.width
        char_count = len(clean_text)

        if char_count == 0:
            return

        # 计算每个字符框的宽度（平均分配）
        box_width = total_width / char_count

        # 字体大小
        font_size = min(11, rect.height * 0.7)
        c.setFont('Helvetica', font_size)

        # Y坐标（垂直居中）
        y = page_height - rect.y1 + 3

        # 绘制每个字符
        for i, char in enumerate(clean_text):
            x = rect.x0 + i * box_width
            # 在每个框内居中绘制
            c.drawCentredString(x + box_width/2, y, char)

    def _select_font_for_text(self, text: str) -> str:
        """根据文本内容选择合适的字体"""
        if not text:
            return self.thai_font

        # 检测中文字符
        has_cjk = any(0x4E00 <= ord(ch) <= 0x9FFF for ch in text if len(ch) == 1)
        if has_cjk:
            return self.chinese_font

        # 检测泰文字符
        has_thai = any(0x0E00 <= ord(ch) <= 0x0E7F for ch in text if len(ch) == 1)
        if has_thai:
            return self.thai_font

        # 默认使用泰文字体（也支持英文）
        return self.thai_font

    def _merge_pdfs(self, template_path: str, overlay_buffer: BytesIO, checkbox_data: dict, output_path: str):
        """合并模板PDF和覆盖层PDF

        策略：先用PyMuPDF填充表单字段（复选框），然后添加覆盖层（文本内容）
        """
        import fitz

        # 1. 使用PyMuPDF打开模板，填充复选框
        doc = fitz.open(template_path)
        page = doc[0]

        # 填充复选框字段
        widgets = list(page.widgets()) if page.widgets() else []
        for widget in widgets:
            field_name = widget.field_name
            if field_name in checkbox_data and checkbox_data[field_name]:
                try:
                    # 设置复选框为选中状态
                    widget.field_value = True
                    widget.update()
                except Exception as e:
                    print(f"[AMLOPDFFillerOverlay] Error setting checkbox {field_name}: {e}")

        # 2. 保存为临时文件（包含复选框值）
        temp_filled = BytesIO()
        doc.save(temp_filled)
        doc.close()
        temp_filled.seek(0)

        # 3. 用pdfrw读取已填充的PDF和覆盖层
        template = PdfReader(temp_filled)
        overlay = PdfReader(overlay_buffer)

        # 4. 合并第一页
        merger = PageMerge(template.pages[0])
        merger.add(overlay.pages[0]).render()

        # 如果有第二页，也合并
        if len(template.pages) > 1:
            if len(overlay.pages) > 1:
                merger2 = PageMerge(template.pages[1])
                merger2.add(overlay.pages[1]).render()

        # 5. 保存最终PDF
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        PdfWriter(output_path, trailer=template).write()

        if checkbox_data:
            print(f"[AMLOPDFFillerOverlay] Filled {len(checkbox_data)} checkboxes")


if __name__ == '__main__':
    # 测试代码
    filler = AMLOPDFFillerOverlay()
    sample_data = {
        'fill_52': '001-001-68-110049USD',
        'fill_4': '蔡◆海',
        'fill_5': '广◆省深圳市福田区梅林街道梅兴苑2-1203',
        'fill_48': '2500000.00',
        'fill_50': '2500000.00',
        'fill_42': 'USD 75,000',
        'left_amount': 'สองล้านห้าแสนบาทถ้วน',
        'Check Box2': True,
        'Check Box4': True,
        'Check Box23': True,
    }
    output_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'amlo_pdfs')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'test_overlay.pdf')
    filler.fill_form('AMLO-1-01', sample_data, output_path)
    print(f"\nTest PDF saved to: {output_path}")
