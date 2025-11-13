# -*- coding: utf-8 -*-
"""
AMLO PDF表单填充服务 - 使用ReportLab绘制覆盖层
这种方式比直接填充表单字段更可靠，能正确显示中文、泰文、英文

参考原始的 amlo_form_filler.py 实现
"""

import os
from typing import Any, Dict
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from io import BytesIO
import base64

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
        self.current_report_type = None  # 存储当前报告类型
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

    def fill_form(self, report_type: str, data: Dict[str, Any], output_path: str, flatten: bool = False, signatures: Dict[str, str] = None) -> str:
        """填充表单（使用ReportLab覆盖层方式，flatten参数仅为兼容性保留）

        Args:
            report_type: 报告类型 (e.g., 'AMLO-1-01')
            data: 字段数据字典
            output_path: 输出PDF路径
            flatten: 兼容参数，覆盖层方式本身就不可编辑
            signatures: 签名数据字典（可选），包含:
                - reporter_signature: 报告人签名（Base64 PNG）
                - customer_signature: 客户签名（Base64 PNG）
                - auditor_signature: 审核人签名（Base64 PNG）

        Returns:
            生成的PDF文件路径
        """
        try:
            # 保存当前报告类型供其他方法使用
            self.current_report_type = report_type

            # 自动填充日期字段为当前日期
            from datetime import datetime
            now = datetime.now()
            date_str = f"{now.day:02d}/{now.month:02d}/{now.year}"

            # 自动填充report_date（dd/mm/yyyy格式）
            if 'report_date' not in data or not data['report_date']:
                data['report_date'] = date_str
                print(f"[AMLOPDFFillerOverlay] Auto-fill report_date: {data['report_date']}")

            # 自动填充reporter_date（dd/mm/yyyy格式）
            if 'reporter_date' not in data or not data['reporter_date']:
                data['reporter_date'] = date_str
                print(f"[AMLOPDFFillerOverlay] Auto-fill reporter_date: {data['reporter_date']}")

            # 自动填充reporter_signature_date分隔字段（如果存在）
            if ('reporter_signature_date_day' not in data or not data['reporter_signature_date_day']):
                data['reporter_signature_date_day'] = now.day
                print(f"[AMLOPDFFillerOverlay] Auto-fill reporter_signature_date_day: {data['reporter_signature_date_day']}")

            if ('reporter_signature_date_month' not in data or not data['reporter_signature_date_month']):
                data['reporter_signature_date_month'] = now.month
                print(f"[AMLOPDFFillerOverlay] Auto-fill reporter_signature_date_month: {data['reporter_signature_date_month']}")

            if ('reporter_signature_date_year' not in data or not data['reporter_signature_date_year']):
                # 判断是否使用佛历
                base_currency = data.get('base_currency', 'THB')
                year = now.year + 543 if base_currency == 'THB' else now.year
                data['reporter_signature_date_year'] = year
                print(f"[AMLOPDFFillerOverlay] Auto-fill reporter_signature_date_year: {data['reporter_signature_date_year']} (base_currency={base_currency})")

            template_path = self.csv_loader.get_template_path(report_type)
            print(f"[AMLOPDFFillerOverlay] Using template: {template_path}")

            if not os.path.exists(template_path):
                raise FileNotFoundError(f"Template not found: {template_path}")

            field_mapping = self.csv_loader.get_field_mapping(report_type)

            # 创建覆盖层PDF（包含文本，不包含签名）
            # 签名将在最后用PyMuPDF直接绘制，以确保正确嵌入
            overlay_buffer, checkbox_data = self._create_overlay_pdf(data, field_mapping, template_path, signatures=None)

            # 合并模板和覆盖层（同时填充复选框），并用PyMuPDF绘制签名
            self._merge_pdfs(template_path, overlay_buffer, checkbox_data, output_path, signatures=signatures)

            print(f"[AMLOPDFFillerOverlay] PDF generated: {output_path}")
            return output_path

        except Exception as exc:
            print(f"[AMLOPDFFillerOverlay] Error filling form: {exc}")
            import traceback
            traceback.print_exc()
            raise

    def _create_overlay_pdf(self, data: Dict[str, Any], field_mapping: Dict, template_path: str, signatures: Dict[str, str] = None) -> tuple:
        """创建覆盖层PDF

        Args:
            signatures: 签名数据字典（可选）

        Returns:
            tuple: (overlay_buffer, checkbox_data) - 覆盖层PDF和复选框数据
        """
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)

        # 读取模板以获取页数和字段位置
        import fitz
        doc = fitz.open(template_path)
        num_pages = len(doc)

        print(f"[AMLOPDFFillerOverlay] 模板页数: {num_pages}，准备创建{num_pages}页覆盖层")

        filled_count = 0
        checkbox_data = {}  # 保存复选框数据，用于后续填充

        # 处理每一页
        for page_num in range(num_pages):
            page = doc[page_num]
            widgets = list(page.widgets()) if page.widgets() else []

            print(f"[AMLOPDFFillerOverlay] 处理第{page_num + 1}页，字段数: {len(widgets)}")

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

            # 在第一页处理完后绘制签名（如果提供）
            if page_num == 0 and signatures:
                print(f"[AMLOPDFFillerOverlay] 在第一页绘制签名")
                self.draw_signatures_on_canvas(c, signatures)

            # 如果不是最后一页，创建新页
            if page_num < num_pages - 1:
                c.showPage()
                print(f"[AMLOPDFFillerOverlay] 第{page_num + 1}页处理完成，创建下一页")

        doc.close()

        c.save()
        buffer.seek(0)

        print(f"[AMLOPDFFillerOverlay] 创建了{num_pages}页覆盖层PDF")
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

        支持AMLO-1-01, AMLO-1-02, AMLO-1-03
        报告编号格式: 001-001-68-110045USD
        分四段: [3位]-[3位]-[2位]-[序列号]
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

        # 根据报告类型选择不同的框位置
        if self.current_report_type == 'AMLO-1-02':
            # 1-02的框位置 (测量结果)
            box_positions = [
                310.08, 326.28, 342.54,  # 第一组 (3位)
                367.68, 383.94, 400.20,  # 第二组 (3位)
                425.28, 441.48,          # 第三组 (2位)
            ]
            serial_box_x0 = 463.56
            serial_box_width = 108.06
            box_width = 16.26
            y_offset = 7  # Y偏移量
        elif self.current_report_type == 'AMLO-1-03':
            # 1-03的框位置 (测量结果)
            box_positions = [
                310.02, 326.34, 342.60,  # 第一组 (3位)
                373.02, 389.34, 405.66,  # 第二组 (3位)
                439.50, 455.82,          # 第三组 (2位)
            ]
            serial_box_x0 = 480  # 序列号位置估算
            serial_box_width = 90
            box_width = 16.32
            y_offset = 7
        else:
            # AMLO-1-01 (默认)
            box_positions = [
                305.28, 321.48, 337.74,  # 第一组 (3位)
                362.16, 378.48, 394.68,  # 第二组 (3位)
                419.04, 435.30,          # 第三组 (2位)
            ]
            serial_box_x0 = 463.56
            serial_box_width = 108.06
            box_width = 16.32
            y_offset = 7

        # Y坐标（垂直居中）
        y = page_height - rect.y1 + y_offset

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

    def _draw_signature(self, c: canvas.Canvas, signature_data: str, x: float, y: float, width: float = 120, height: float = 40):
        """在PDF上绘制签名图片

        Args:
            c: ReportLab canvas对象
            signature_data: Base64编码的签名图片 (data:image/png;base64,...)
            x, y: 签名位置坐标 (ReportLab坐标系，从页面底部开始)
            width, height: 签名显示尺寸（单位：点）
        """
        if not signature_data:
            return

        try:
            # 去除data URL前缀
            if ',' in signature_data:
                signature_data = signature_data.split(',', 1)[1]

            # 解码Base64
            image_bytes = base64.b64decode(signature_data)
            image_buffer = BytesIO(image_bytes)

            # 使用ImageReader加载图片
            img = ImageReader(image_buffer)

            # 绘制到PDF
            c.drawImage(img, x, y, width=width, height=height, mask='auto', preserveAspectRatio=True)

            print(f"[AMLOPDFFillerOverlay] Drew signature at ({x}, {y}) size={width}x{height}")

        except Exception as e:
            print(f"[AMLOPDFFillerOverlay] Error drawing signature: {e}")

    def draw_signatures_on_canvas(self, c: canvas.Canvas, signatures: Dict[str, str], report_type: str = None):
        """在canvas上绘制所有签名

        Args:
            c: ReportLab canvas对象
            signatures: 签名数据字典，包含:
                - reporter_signature: 报告人签名
                - customer_signature: 客户签名
                - auditor_signature: 审核人签名
            report_type: 报告类型（可选，用于确定签名位置）
        """
        if not signatures:
            return

        # 使用当前报告类型或传入的报告类型
        report_type = report_type or self.current_report_type

        # 签名位置配置（根据AMLO表单实际位置）
        # 这里使用AMLO-1-01表单的位置作为示例
        # Y坐标是从页面底部开始的ReportLab坐标
        signature_positions = {
            'AMLO-1-01': {
                'reporter': {'x': 680, 'y': 100, 'width': 110, 'height': 35},   # 报告人签名区(右侧sig_reporter) - 调高Y坐标
                'customer': {'x': 280, 'y': 100, 'width': 110, 'height': 35},   # 交易者签名区(左侧sig_transactor) - 调高Y坐标
                'auditor': {'x': 400, 'y': 200, 'width': 120, 'height': 40}     # 审核人签名区
            },
            'AMLO-1-02': {
                'reporter': {'x': 680, 'y': 100, 'width': 110, 'height': 35},
                'customer': {'x': 280, 'y': 100, 'width': 110, 'height': 35},
                'auditor': {'x': 400, 'y': 200, 'width': 120, 'height': 40}
            },
            'AMLO-1-03': {
                'reporter': {'x': 680, 'y': 100, 'width': 110, 'height': 35},
                'customer': {'x': 280, 'y': 100, 'width': 110, 'height': 35},
                'auditor': {'x': 400, 'y': 200, 'width': 120, 'height': 40}
            }
        }

        # 获取当前报告类型的签名位置
        positions = signature_positions.get(report_type, signature_positions['AMLO-1-01'])

        # 绘制报告人签名
        if signatures.get('reporter_signature'):
            pos = positions['reporter']
            self._draw_signature(c, signatures['reporter_signature'], pos['x'], pos['y'], pos['width'], pos['height'])

        # 绘制客户签名
        if signatures.get('customer_signature'):
            pos = positions['customer']
            self._draw_signature(c, signatures['customer_signature'], pos['x'], pos['y'], pos['width'], pos['height'])

        # 绘制审核人签名
        if signatures.get('auditor_signature'):
            pos = positions['auditor']
            self._draw_signature(c, signatures['auditor_signature'], pos['x'], pos['y'], pos['width'], pos['height'])

    def _merge_pdfs(self, template_path: str, overlay_buffer: BytesIO, checkbox_data: dict, output_path: str, signatures: Dict[str, str] = None):
        """合并模板PDF和覆盖层PDF，并绘制签名

        新策略：完全使用PyMuPDF，放弃pdfrw
        1. 用PyMuPDF打开模板
        2. 填充复选框字段
        3. 叠加覆盖层PDF（文本内容）
        4. 绘制签名图像
        5. 保存最终PDF
        """
        import fitz

        print(f"[AMLOPDFFillerOverlay] ===== 开始PDF合并（纯PyMuPDF方式）=====")

        # 1. 使用PyMuPDF打开模板
        doc = fitz.open(template_path)
        page = doc[0]

        print(f"[AMLOPDFFillerOverlay] 模板加载完成，页数: {len(doc)}")

        # 2. 填充复选框字段
        checkbox_count = 0
        widgets = list(page.widgets()) if page.widgets() else []
        for widget in widgets:
            field_name = widget.field_name
            if field_name in checkbox_data and checkbox_data[field_name]:
                try:
                    widget.field_value = True
                    widget.update()
                    checkbox_count += 1
                except Exception as e:
                    print(f"[AMLOPDFFillerOverlay] Error setting checkbox {field_name}: {e}")

        if checkbox_count > 0:
            print(f"[AMLOPDFFillerOverlay] 已填充 {checkbox_count} 个复选框")

        # 3. 叠加覆盖层PDF（使用PyMuPDF的show_pdf_page）
        overlay_buffer.seek(0)
        overlay_doc = fitz.open("pdf", overlay_buffer.read())

        print(f"[AMLOPDFFillerOverlay] 覆盖层加载完成，页数: {len(overlay_doc)}")

        # 将覆盖层的每一页叠加到对应页面
        for page_num in range(min(len(doc), len(overlay_doc))):
            target_page = doc[page_num]
            overlay_page = overlay_doc[page_num]

            # 获取页面矩形
            page_rect = target_page.rect

            # 使用show_pdf_page叠加覆盖层
            target_page.show_pdf_page(
                page_rect,  # 目标矩形（整个页面）
                overlay_doc,  # 源PDF文档
                page_num,  # 源页面编号
                overlay=True  # 作为覆盖层
            )

        overlay_doc.close()
        print(f"[AMLOPDFFillerOverlay] 覆盖层叠加完成")

        # 4. 绘制签名图像
        if signatures:
            print(f"[AMLOPDFFillerOverlay] 准备绘制 {len(signatures)} 个签名")

            # 检查插入前的图像数量
            page = doc[0]
            images_before = page.get_images(full=True)
            print(f"[AMLOPDFFillerOverlay] 插入签名前图像数量: {len(images_before)}")

            self._draw_signatures_with_pymupdf(doc, signatures)

            # 检查插入后的图像数量
            images_after = page.get_images(full=True)
            print(f"[AMLOPDFFillerOverlay] 插入签名后图像数量: {len(images_after)}")

            # 验证签名图像
            if len(images_after) > len(images_before):
                print(f"[AMLOPDFFillerOverlay] ✅ 成功添加 {len(images_after) - len(images_before)} 个签名图像")
            else:
                print(f"[AMLOPDFFillerOverlay] ⚠️ 警告：图像数量没有增加！")

        # 5. 保存最终PDF
        try:
            # 确保输出路径是绝对路径
            if not os.path.isabs(output_path):
                output_path = os.path.abspath(output_path)
                print(f"[AMLOPDFFillerOverlay] 转换为绝对路径: {output_path}")

            # 创建目录
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                print(f"[AMLOPDFFillerOverlay] 创建目录: {output_dir}")

            print(f"[AMLOPDFFillerOverlay] 正在保存PDF: {output_path}")

            # 使用正确的保存参数
            doc.save(
                output_path,
                garbage=0,      # 不删除任何对象
                deflate=True,   # 压缩流
                clean=False,    # 不清理结构
                expand=False    # 不展开对象
            )

            doc.close()

            # 验证文件是否真的创建了
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"[AMLOPDFFillerOverlay] ✅ PDF保存成功")
                print(f"[AMLOPDFFillerOverlay] 文件大小: {file_size} bytes")
                print(f"[AMLOPDFFillerOverlay] 文件路径: {output_path}")
            else:
                print(f"[AMLOPDFFillerOverlay] ⚠️ 警告：文件保存后不存在！")
                print(f"[AMLOPDFFillerOverlay] 尝试的路径: {output_path}")

            print(f"[AMLOPDFFillerOverlay] ===== PDF合并完成 =====")

        except Exception as e:
            print(f"[AMLOPDFFillerOverlay] ❌ PDF保存失败: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _draw_signatures_with_pymupdf(self, doc, signatures: Dict[str, str]):
        """使用PyMuPDF直接在PDF上绘制签名图像，动态读取字段位置

        Args:
            doc: PyMuPDF Document对象
            signatures: 签名数据字典
        """
        import fitz
        import base64

        page = doc[0]  # 第一页
        page_height = page.rect.height

        # 1. 动态读取签名字段位置
        reporter_field_rect = None
        customer_field_rect = None

        widgets = list(page.widgets()) if page.widgets() else []
        for widget in widgets:
            if widget.field_name == 'sig_reporter':
                reporter_field_rect = widget.rect
            elif widget.field_name == 'sig_transactor':
                customer_field_rect = widget.rect

        # 默认位置（如果找不到字段）
        if not reporter_field_rect:
            reporter_field_rect = fitz.Rect(680, 707, 790, 742)
        if not customer_field_rect:
            customer_field_rect = fitz.Rect(280, 707, 390, 742)

        print(f"[AMLOPDFFillerOverlay] Reporter signature field: {reporter_field_rect}")
        print(f"[AMLOPDFFillerOverlay] Customer signature field: {customer_field_rect}")

        # 3. 绘制签名（覆盖在字段位置上）
        for sig_type, sig_data in signatures.items():
            if not sig_data:
                continue

            # 确定使用哪个字段的位置
            if sig_type == 'reporter_signature':
                field_rect = reporter_field_rect
            elif sig_type == 'customer_signature':
                field_rect = customer_field_rect
            elif sig_type == 'auditor_signature':
                continue  # 审核人签名暂时跳过
            else:
                continue

            try:
                # 去除data URL前缀
                if ',' in sig_data:
                    sig_data = sig_data.split(',', 1)[1]

                # 解码Base64
                image_bytes = base64.b64decode(sig_data)
                print(f"[AMLOPDFFillerOverlay] Decoded {sig_type} image: {len(image_bytes)} bytes")

                # 扩大签名显示区域 - 比字段框大100%（向四周各扩展50%）
                width_expand = field_rect.width * 0.5
                height_expand = field_rect.height * 0.5
                signature_rect = fitz.Rect(
                    field_rect.x0 - width_expand/2,
                    field_rect.y0 - height_expand/2,
                    field_rect.x1 + width_expand/2,
                    field_rect.y1 + height_expand/2
                )
                rect = signature_rect
                print(f"[AMLOPDFFillerOverlay] Original field rect: {field_rect}")
                print(f"[AMLOPDFFillerOverlay] Expanded signature rect: {rect}")

                # 插入图像 - 尝试多种方法确保图像被正确嵌入
                inserted = False

                try:
                    # 方法1: 使用stream直接插入 (推荐方法)
                    print(f"[AMLOPDFFillerOverlay] Trying insert_image with stream...")
                    result = page.insert_image(rect, stream=image_bytes, keep_proportion=True, overlay=True)
                    print(f"[AMLOPDFFillerOverlay] insert_image result: {result}")

                    if result:
                        inserted = True
                        print(f"[AMLOPDFFillerOverlay] ✅ Successfully inserted {sig_type} with PyMuPDF")
                        print(f"[AMLOPDFFillerOverlay] Position: {rect}")
                        # 注意：report_date通过字段填充显示（Line 86-91），不需要在此重复绘制

                    else:
                        print(f"[AMLOPDFFillerOverlay] ⚠️ insert_image returned None or empty result")

                except Exception as img_err:
                    print(f"[AMLOPDFFillerOverlay] ❌ Method 1 failed: {img_err}")
                    import traceback
                    traceback.print_exc()

                # 方法2: 如果方法1失败，尝试使用filename参数（先保存临时文件）
                if not inserted:
                    try:
                        print(f"[AMLOPDFFillerOverlay] Trying insert_image with temp file...")
                        import tempfile
                        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                            tmp.write(image_bytes)
                            tmp_path = tmp.name

                        result = page.insert_image(rect, filename=tmp_path, keep_proportion=True, overlay=True)
                        print(f"[AMLOPDFFillerOverlay] insert_image (file) result: {result}")

                        # 删除临时文件
                        try:
                            os.remove(tmp_path)
                        except:
                            pass

                        if result:
                            inserted = True
                            print(f"[AMLOPDFFillerOverlay] ✅ Successfully inserted {sig_type} using temp file method")
                        else:
                            print(f"[AMLOPDFFillerOverlay] ⚠️ insert_image (file) returned None")

                    except Exception as file_err:
                        print(f"[AMLOPDFFillerOverlay] ❌ Method 2 failed: {file_err}")
                        import traceback
                        traceback.print_exc()

                if not inserted:
                    print(f"[AMLOPDFFillerOverlay] ❌❌ CRITICAL: Failed to insert {sig_type} using all methods!")
                else:
                    print(f"[AMLOPDFFillerOverlay] ✅✅ {sig_type} insertion confirmed")

            except Exception as e:
                print(f"[AMLOPDFFillerOverlay] ❌ Error drawing {sig_type} with PyMuPDF: {e}")
                import traceback
                traceback.print_exc()


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
