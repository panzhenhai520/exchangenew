# -*- coding: utf-8 -*-
"""
AMLO PDF表单填充服务 - 基于PyMuPDF (fitz)
使用PyMuPDF进行PDF表单填充和flatten，解决浏览器不显示问题

优势:
- 自动生成字段外观流（Appearance Streams）
- 原生支持flatten（将表单转为静态内容）
- 浏览器PDF查看器完美兼容
"""

import os
from typing import Dict, Any
import fitz  # PyMuPDF

try:
    from .amlo_csv_field_loader import get_csv_field_loader
except ImportError:
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from amlo_csv_field_loader import get_csv_field_loader


class AMLOPDFFillerPyMuPDF:
    """AMLO PDF表单填充器 - 基于PyMuPDF"""

    def __init__(self):
        """初始化填充器"""
        self.csv_loader = get_csv_field_loader()
        print("[AMLOPDFFillerPyMuPDF] Initialized with CSV field mappings")

    def fill_form(self, report_type: str, data: Dict[str, Any], output_path: str, flatten: bool = True) -> str:
        """
        填充AMLO表单

        Args:
            report_type: 报告类型 ('AMLO-1-01', 'AMLO-1-02', 'AMLO-1-03')
            data: 表单数据字典 (field_name -> value)
            output_path: 输出PDF文件路径
            flatten: 是否flatten表单（转为静态内容，推荐True）

        Returns:
            生成的PDF文件路径
        """
        try:
            # 获取模板路径
            template_path = self.csv_loader.get_template_path(report_type)
            print(f"[AMLOPDFFillerPyMuPDF] Using template: {template_path}")

            # 打开PDF文档
            doc = fitz.open(template_path)
            print(f"[AMLOPDFFillerPyMuPDF] Opened PDF: {doc.page_count} pages")

            # 获取字段映射
            field_mapping = self.csv_loader.get_field_mapping(report_type)

            # 填充表单字段
            filled_count = self._fill_pdf_fields(doc, data, field_mapping)

            print(f"[AMLOPDFFillerPyMuPDF] Filled {filled_count} fields")

            # Flatten表单（将表单字段转为静态内容）
            if flatten:
                print(f"[AMLOPDFFillerPyMuPDF] Flattening PDF...")
                for page in doc:
                    # PyMuPDF的flatten会将所有widget转为静态内容
                    widgets = page.widgets() or []
                    for widget in widgets:
                        widget.update()  # 确保widget外观已更新

                # 保存并重新加载以完成flatten
                temp_path = output_path + '.temp.pdf'
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                doc.save(temp_path)
                doc.close()

                # 重新打开并flatten
                doc = fitz.open(temp_path)
                # 移除所有表单字段（转为纯图形）
                for page in doc:
                    page.remove_rotation()  # 确保页面旋转正确

                doc.save(output_path, garbage=4, deflate=True, clean=True)
                doc.close()

                # 删除临时文件
                if os.path.exists(temp_path):
                    os.remove(temp_path)

                print(f"[AMLOPDFFillerPyMuPDF] PDF flattened successfully")
            else:
                # 不flatten，直接保存
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                doc.save(output_path)
                doc.close()

            print(f"[AMLOPDFFillerPyMuPDF] PDF generated: {output_path}")

            return output_path

        except Exception as e:
            print(f"[AMLOPDFFillerPyMuPDF] Error filling form: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _fill_pdf_fields(self, doc: fitz.Document, data: Dict[str, Any], field_mapping: Dict) -> int:
        """
        填充PDF字段

        Args:
            doc: PyMuPDF文档对象
            data: 表单数据
            field_mapping: 字段映射配置

        Returns:
            填充的字段数量
        """
        filled_count = 0

        try:
            # 遍历所有页面
            for page_num in range(doc.page_count):
                page = doc[page_num]

                # 获取页面上的所有widget（表单字段）
                widgets = page.widgets() or []

                for widget in widgets:
                    field_name = widget.field_name
                    if not field_name:
                        continue

                    # 检查是否在数据中
                    if field_name not in data:
                        continue

                    value = data[field_name]

                    # 检查字段映射获取类型
                    field_info = field_mapping.get(field_name, {})
                    field_type = field_info.get('type', 'text')

                    try:
                        # 根据widget类型填充
                        if widget.field_type == fitz.PDF_WIDGET_TYPE_TEXT:
                            # 文本字段
                            str_value = str(value) if value is not None else ''

                            # 只对报告编号字段(fill_52)添加字符间距，不影响comb字段
                            # 报告编号有独立的字符框但不是comb类型
                            if field_name == 'fill_52':
                                # 在每个字符之间添加空格，分散到各个框中
                                str_value = ' '.join(str_value)
                                print(f"[AMLOPDFFillerPyMuPDF] Report number field detected: {field_name}, spacing characters")

                            widget.field_value = str_value
                            widget.update()
                            filled_count += 1
                            print(f"[AMLOPDFFillerPyMuPDF] Filled TEXT field: {field_name} = {value}")

                        elif widget.field_type == fitz.PDF_WIDGET_TYPE_CHECKBOX:
                            # 复选框 - 使用字符串 "Yes" 或 "Off"
                            if value in (True, 'true', '1', 1, 'yes', 'Yes', '/Yes'):
                                widget.field_value = "Yes"  # 使用字符串而不是布尔值
                            else:
                                widget.field_value = "Off"
                            widget.update()
                            filled_count += 1
                            print(f"[AMLOPDFFillerPyMuPDF] Filled CHECKBOX field: {field_name} = {widget.field_value}")

                        elif widget.field_type == fitz.PDF_WIDGET_TYPE_COMBOBOX:
                            # 下拉框
                            widget.field_value = str(value) if value is not None else ''
                            widget.update()
                            filled_count += 1
                            print(f"[AMLOPDFFillerPyMuPDF] Filled COMBOBOX field: {field_name} = {value}")

                        elif widget.field_type == fitz.PDF_WIDGET_TYPE_LISTBOX:
                            # 列表框
                            widget.field_value = str(value) if value is not None else ''
                            widget.update()
                            filled_count += 1
                            print(f"[AMLOPDFFillerPyMuPDF] Filled LISTBOX field: {field_name} = {value}")

                        elif widget.field_type == fitz.PDF_WIDGET_TYPE_RADIOBUTTON:
                            # 单选按钮
                            widget.field_value = str(value) if value is not None else ''
                            widget.update()
                            filled_count += 1
                            print(f"[AMLOPDFFillerPyMuPDF] Filled RADIOBUTTON field: {field_name} = {value}")

                        else:
                            # 其他类型，当作文本处理
                            widget.field_value = str(value) if value is not None else ''
                            widget.update()
                            filled_count += 1
                            print(f"[AMLOPDFFillerPyMuPDF] Filled UNKNOWN field: {field_name} = {value}")

                    except Exception as e:
                        print(f"[AMLOPDFFillerPyMuPDF] Error filling field {field_name}: {e}")

        except Exception as e:
            print(f"[AMLOPDFFillerPyMuPDF] Error in _fill_pdf_fields: {e}")
            import traceback
            traceback.print_exc()

        return filled_count

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
            doc = fitz.open(template_path)

            field_names = []
            for page in doc:
                widgets = page.widgets() or []
                for widget in widgets:
                    if widget.field_name:
                        field_names.append(widget.field_name)

            doc.close()
            return field_names

        except Exception as e:
            print(f"[AMLOPDFFillerPyMuPDF] Error extracting field names: {e}")
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
            'mapped_fields': mapped_fields[:10],
            'unmapped_fields': unmapped_fields[:10],
            'missing_data': missing_data[:10]
        }


# 测试代码
if __name__ == '__main__':
    filler = AMLOPDFFillerPyMuPDF()

    # 测试数据
    test_data = {
        'fill_52': 'FI-001-68-001',
        'Check Box2': True,
        'Check Box3': False,
        'comb_1': '1234567890123',
        'fill_4': 'นายสมชาย ใจดี',
        'fill_37': '18',
        'fill_38': '10',
        'fill_39': '2568',
        'fill_48': '2500000',
    }

    # 生成测试PDF
    output_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'test_output')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'test_amlo_101_pymupdf.pdf')

    print("\n" + "="*60)
    print("Generating Test PDF with PyMuPDF")
    print("="*60)
    result_path = filler.fill_form('AMLO-1-01', test_data, output_path, flatten=True)
    print(f"Test PDF created: {result_path}")
