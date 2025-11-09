# -*- coding: utf-8 -*-
"""
AMLO PDF表单填充服务 V2
使用PyPDF2直接填充PDF表单字段

支持:
- AMLO-1-01 (CTR - Cash Transaction Report)
- AMLO-1-02 (ATR - Asset Transaction Report)
- AMLO-1-03 (STR - Suspicious Transaction Report)
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import NameObject, TextStringObject, BooleanObject, DictionaryObject
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

try:
    from .amlo_csv_field_loader import get_csv_field_loader
except ImportError:
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from amlo_csv_field_loader import get_csv_field_loader


class AMLOPDFFiller:
    """AMLO PDF表单填充器 - 基于PyPDF2"""

    def __init__(self):
        """初始化填充器"""
        self.csv_loader = get_csv_field_loader()
        print("[AMLOPDFFiller] Initialized with CSV field mappings")

    def fill_form(self, report_type: str, data: Dict[str, Any], output_path: str) -> str:
        """
        填充AMLO表单

        Args:
            report_type: 报告类型 ('AMLO-1-01', 'AMLO-1-02', 'AMLO-1-03')
            data: 表单数据字典 (field_name -> value)
            output_path: 输出PDF文件路径

        Returns:
            生成的PDF文件路径

        Example:
            >>> filler = AMLOPDFFiller()
            >>> data = {
            ...     'fill_52': 'FI-001-25-001',  # 报告编号
            ...     'comb_1': '1234567890123',    # 身份证号
            ...     'fill_4': 'นายสมชาย ใจดี',  # 姓名
            ...     'Check Box2': True,           # 勾选框
            ... }
            >>> filler.fill_form('AMLO-1-01', data, 'output.pdf')
        """
        try:
            # 获取模板路径
            template_path = self.csv_loader.get_template_path(report_type)
            print(f"[AMLOPDFFiller] Using template: {template_path}")

            # 读取PDF模板
            reader = PdfReader(template_path)
            writer = PdfWriter()

            # 复制所有页面
            for page in reader.pages:
                writer.add_page(page)

            # 获取字段映射
            field_mapping = self.csv_loader.get_field_mapping(report_type)

            # 填充表单字段
            filled_count = self._fill_pdf_fields(writer, data, field_mapping)

            # 设置NeedAppearances标志
            print(f"[AMLOPDFFiller] Setting NeedAppearances flag...")
            if "/AcroForm" in writer._root_object:
                writer._root_object["/AcroForm"].update({
                    NameObject("/NeedAppearances"): BooleanObject(True)
                })

            # 写入临时PDF文件
            temp_path = output_path + '.temp.pdf'
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(temp_path, 'wb') as output_file:
                writer.write(output_file)

            print(f"[AMLOPDFFiller] Filled {filled_count} fields")
            print(f"[AMLOPDFFiller] Temporary PDF written: {temp_path}")

            # 尝试真正flatten表单（使用reportlab叠加文本）
            print(f"[AMLOPDFFiller] Attempting to flatten PDF for browser compatibility...")
            try:
                self._overlay_field_values(temp_path, output_path, data, field_mapping)
                # 删除临时文件
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                print(f"[AMLOPDFFiller] PDF flattened successfully")
            except Exception as e:
                print(f"[AMLOPDFFiller] Warning: flatten overlay failed: {e}")
                # 如果flatten失败，使用原PDF
                import shutil
                shutil.move(temp_path, output_path)
                print(f"[AMLOPDFFiller] Using non-flattened PDF")

            print(f"[AMLOPDFFiller] PDF generated: {output_path}")

            return output_path

        except Exception as e:
            print(f"[AMLOPDFFiller] Error filling form: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _fill_pdf_fields(self, writer: PdfWriter, data: Dict[str, Any], field_mapping: Dict) -> int:
        """
        填充PDF字段

        Args:
            writer: PDF写入器
            data: 表单数据
            field_mapping: 字段映射配置

        Returns:
            填充的字段数量
        """
        filled_count = 0

        try:
            # 使用update_page_form_field_values方法来填充字段
            for page_num, page in enumerate(writer.pages):
                for field_name, value in data.items():
                    if field_name in field_mapping:
                        field_info = field_mapping[field_name]
                        field_type = field_info.get('type', 'text')

                        try:
                            if field_type == 'checkbox':
                                # 复选框
                                checkbox_value = '/Yes' if value in (True, 'true', '1', 1, 'yes', 'Yes') else '/Off'
                                writer.update_page_form_field_values(
                                    page,
                                    {field_name: checkbox_value}
                                )
                            else:
                                # 文本字段或组合字段
                                str_value = str(value) if value is not None else ''
                                writer.update_page_form_field_values(
                                    page,
                                    {field_name: str_value}
                                )

                            filled_count += 1
                            print(f"[AMLOPDFFiller] Filled field: {field_name} = {value}")

                        except Exception as e:
                            print(f"[AMLOPDFFiller] Error filling field {field_name}: {e}")

        except Exception as e:
            print(f"[AMLOPDFFiller] Error in _fill_pdf_fields: {e}")
            import traceback
            traceback.print_exc()

        return filled_count

    def _update_field(self, field, value: Any, field_type: str) -> bool:
        """
        更新单个字段

        Args:
            field: PDF字段对象
            value: 字段值
            field_type: 字段类型 ('text', 'checkbox', 'comb')

        Returns:
            是否成功更新
        """
        try:
            if field_type == 'checkbox':
                # 复选框字段
                if value in (True, 'true', '1', 1, 'yes', 'Yes'):
                    field.update({
                        NameObject('/V'): NameObject('/Yes'),
                        NameObject('/AS'): NameObject('/Yes')
                    })
                else:
                    field.update({
                        NameObject('/V'): NameObject('/Off'),
                        NameObject('/AS'): NameObject('/Off')
                    })
                return True

            elif field_type in ('text', 'comb'):
                # 文本字段或组合字段
                str_value = str(value) if value is not None else ''
                field.update({
                    NameObject('/V'): TextStringObject(str_value)
                })
                return True

            return False

        except Exception as e:
            print(f"[AMLOPDFFiller] Error updating field: {e}")
            return False


    def extract_field_names(self, report_type: str) -> list:
        """
        提取PDF模板中的所有字段名

        Args:
            report_type: 报告类型

        Returns:
            字段名列表
        """
        try:
            template_path = self.csv_loader.get_template_path(report_type)
            reader = PdfReader(template_path)

            field_names = []
            if reader.get_fields():
                for field_name in reader.get_fields().keys():
                    field_names.append(field_name)

            return field_names

        except Exception as e:
            print(f"[AMLOPDFFiller] Error extracting field names: {e}")
            return []

    def preview_data_mapping(self, report_type: str, data: Dict[str, Any]) -> Dict:
        """
        预览数据映射情况

        Args:
            report_type: 报告类型
            data: 表单数据

        Returns:
            映射统计信息
        """
        field_mapping = self.csv_loader.get_field_mapping(report_type)

        mapped_fields = []
        unmapped_fields = []
        missing_data = []

        # 检查数据中的字段是否在映射中
        for field_name, value in data.items():
            if field_name in field_mapping:
                mapped_fields.append(field_name)
            else:
                unmapped_fields.append(field_name)

        # 检查映射中的字段是否有数据
        for field_name in field_mapping.keys():
            if field_name not in data:
                missing_data.append(field_name)

        return {
            'report_type': report_type,
            'total_data_fields': len(data),
            'total_mapped_fields': len(field_mapping),
            'mapped_count': len(mapped_fields),
            'unmapped_count': len(unmapped_fields),
            'missing_data_count': len(missing_data),
            'mapped_fields': mapped_fields[:10],  # 只显示前10个
            'unmapped_fields': unmapped_fields[:10],
            'missing_data': missing_data[:10]
        }

    def _overlay_field_values(self, input_path: str, output_path: str, data: Dict[str, Any], field_mapping: Dict) -> None:
        """
        在PDF上叠加字段值（使用reportlab绘制静态文本）

        这个方法读取已填充的PDF，在字段位置绘制可见的静态文本，
        解决浏览器PDF查看器不显示表单字段值的问题。

        Args:
            input_path: 输入PDF（已填充表单）
            output_path: 输出PDF（叠加文本后）
            data: 字段数据
            field_mapping: 字段映射
        """
        try:
            # 注册泰文字体
            thai_font = 'Helvetica'
            try:
                font_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                    'fonts',
                    'Sarabun-Regular.ttf'
                )
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('Sarabun', font_path))
                    thai_font = 'Sarabun'
                    print(f"[AMLOPDFFiller] Using Thai font: Sarabun")
                else:
                    print(f"[AMLOPDFFiller] Thai font not found, using Helvetica")
            except Exception as e:
                print(f"[AMLOPDFFiller] Error loading Thai font: {e}")

            # 读取PDF
            reader = PdfReader(input_path)
            writer = PdfWriter()

            # 获取所有表单字段
            fields = reader.get_fields()
            if not fields:
                print(f"[AMLOPDFFiller] No fields found for overlay")
                import shutil
                shutil.copy2(input_path, output_path)
                return

            print(f"[AMLOPDFFiller] Overlaying {len(fields)} fields")

            # 处理每一页
            for page_num, page in enumerate(reader.pages):
                # 获取页面尺寸
                page_width = float(page.mediabox.width)
                page_height = float(page.mediabox.height)

                # 创建覆盖层
                packet = io.BytesIO()
                can = canvas.Canvas(packet, pagesize=(page_width, page_height))

                # 在字段位置绘制文本
                fields_drawn = 0
                for field_name, field_obj in fields.items():
                    # 检查字段是否有值
                    value = field_obj.get('/V')
                    if not value or str(value).strip() == '':
                        continue

                    # 跳过复选框
                    if str(value) in ['/Yes', '/Off']:
                        continue

                    # 获取字段位置
                    if '/Rect' not in field_obj:
                        continue

                    rect = field_obj['/Rect']
                    x1, y1, x2, y2 = float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3])

                    # 计算文本位置
                    x = x1 + 2
                    y = y1 + ((y2 - y1) / 3)  # 垂直居中

                    # 绘制文本
                    can.setFont(thai_font, 9)
                    can.setFillColorRGB(0, 0, 0)
                    can.drawString(x, y, str(value))
                    fields_drawn += 1

                if fields_drawn > 0:
                    print(f"[AMLOPDFFiller] Drew {fields_drawn} fields on page {page_num + 1}")

                # 完成覆盖层
                can.save()
                packet.seek(0)

                # 读取覆盖层
                overlay = PdfReader(packet)
                overlay_page = overlay.pages[0]

                # 合并页面
                page.merge_page(overlay_page)
                writer.add_page(page)

            # 写入输出文件
            with open(output_path, 'wb') as f:
                writer.write(f)

            print(f"[AMLOPDFFiller] Overlay complete")

        except Exception as e:
            print(f"[AMLOPDFFiller] Error in overlay: {e}")
            import traceback
            traceback.print_exc()
            raise


# 测试代码
if __name__ == '__main__':
    filler = AMLOPDFFiller()

    # 测试数据
    test_data = {
        # 报告编号区域
        'fill_52': 'FI-001-68-001',

        # 复选框
        'Check Box2': True,  # 报告原版
        'Check Box3': False,  # 报告修订版

        # 交易人信息
        'comb_1': '1234567890123',  # 身份证号
        'fill_4': 'นายสมชาย ใจดี',  # 姓名

        # 交易日期
        'fill_37': '18',  # 日
        'fill_38': '10',  # 月
        'fill_39': '2568',  # 年(佛历)

        # 金额
        'fill_48': '2500000',  # 本币金额
    }

    # 预览映射
    print("\n" + "="*60)
    print("Data Mapping Preview")
    print("="*60)
    preview = filler.preview_data_mapping('AMLO-1-01', test_data)
    for key, value in preview.items():
        if not isinstance(value, list):
            print(f"{key}: {value}")

    # 生成测试PDF
    output_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'test_output')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'test_amlo_101.pdf')

    print("\n" + "="*60)
    print("Generating Test PDF")
    print("="*60)
    result_path = filler.fill_form('AMLO-1-01', test_data, output_path)
    print(f"Test PDF created: {result_path}")
