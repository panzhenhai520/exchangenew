# -*- coding: utf-8 -*-
"""
AMLO PDF Flattener - 将填充的表单字段转换为可见的静态内容

解决问题：
- PyPDF2填充表单后，某些PDF阅读器（浏览器）不显示内容
- NeedAppearances标志不够，需要真正的flatten（表单转静态）
"""

import os
from typing import Dict, Any
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io


class AMLOPDFFlattener:
    """PDF表单Flattener - 使用reportlab叠加可见文本"""

    def __init__(self):
        """初始化Flattener"""
        # 注册泰文字体
        try:
            font_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'fonts',
                'Sarabun-Regular.ttf'
            )
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('Sarabun', font_path))
                self.thai_font = 'Sarabun'
                print(f"[AMLOPDFFlattener] Thai font registered: {font_path}")
            else:
                self.thai_font = 'Helvetica'
                print(f"[AMLOPDFFlattener] Thai font not found, using Helvetica")
        except Exception as e:
            self.thai_font = 'Helvetica'
            print(f"[AMLOPDFFlattener] Error loading Thai font: {e}")

    def flatten_filled_pdf(self, input_path: str, output_path: str, field_data: Dict[str, Any]) -> str:
        """
        Flatten已填充的PDF（将表单字段转为可见的静态文本）

        Args:
            input_path: 已填充表单的PDF路径
            output_path: 输出PDF路径
            field_data: 字段数据（用于获取坐标和值）

        Returns:
            输出PDF路径
        """
        try:
            print(f"[AMLOPDFFlattener] Flattening PDF: {input_path}")

            # 读取已填充的PDF
            reader = PdfReader(input_path)

            # 获取PDF表单字段及其位置
            fields = reader.get_fields()
            if not fields:
                print(f"[AMLOPDFFlattener] No form fields found, copying as-is")
                import shutil
                shutil.copy2(input_path, output_path)
                return output_path

            print(f"[AMLOPDFFlattener] Found {len(fields)} form fields")

            # 创建新的PDF writer
            writer = PdfWriter()

            # 处理每一页
            for page_num, page in enumerate(reader.pages):
                print(f"[AMLOPDFFlattener] Processing page {page_num + 1}")

                # 创建覆盖层（用reportlab画文本）
                packet = io.BytesIO()
                can = canvas.Canvas(packet, pagesize=letter)

                # 在字段位置绘制文本
                fields_drawn = 0
                for field_name, field_obj in fields.items():
                    # 检查字段是否有值
                    if '/V' not in field_obj:
                        continue

                    value = field_obj.get('/V')
                    if not value or value == '':
                        continue

                    # 获取字段位置（矩形区域）
                    if '/Rect' in field_obj:
                        rect = field_obj['/Rect']
                        # PDF坐标: [x1, y1, x2, y2]
                        x1, y1, x2, y2 = float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3])

                        # 计算文本位置（左下角）
                        x = x1 + 2  # 稍微偏移避免边框
                        y = y1 + 2

                        # 选择字体
                        font_name = self.thai_font
                        font_size = 10

                        # 绘制文本
                        can.setFont(font_name, font_size)
                        can.drawString(x, y, str(value))
                        fields_drawn += 1

                print(f"[AMLOPDFFlattener] Drew {fields_drawn} field values on page {page_num + 1}")

                # 完成这一页的覆盖层
                can.save()

                # 移动到packet开始位置
                packet.seek(0)

                # 读取覆盖层PDF
                overlay_pdf = PdfReader(packet)
                overlay_page = overlay_pdf.pages[0]

                # 合并原页面和覆盖层
                page.merge_page(overlay_page)

                # 添加到writer
                writer.add_page(page)

            # 写入输出文件
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)

            print(f"[AMLOPDFFlattener] Flattened PDF saved: {output_path}")
            return output_path

        except Exception as e:
            print(f"[AMLOPDFFlattener] Error flattening PDF: {e}")
            import traceback
            traceback.print_exc()
            # 如果flatten失败，复制原文件
            import shutil
            shutil.copy2(input_path, output_path)
            return output_path


# 测试代码
if __name__ == '__main__':
    flattener = AMLOPDFFlattener()

    # 测试文件路径
    input_pdf = r'D:\Code\ExchangeNew\amlo_pdfs\AMLO-1-01_001-001-68-100067USD.pdf'
    output_pdf = r'D:\Code\ExchangeNew\amlo_pdfs\AMLO-1-01_001-001-68-100067USD_flattened.pdf'

    if os.path.exists(input_pdf):
        flattener.flatten_filled_pdf(input_pdf, output_pdf, {})
        print(f"Test flatten complete: {output_pdf}")
    else:
        print(f"Test file not found: {input_pdf}")
