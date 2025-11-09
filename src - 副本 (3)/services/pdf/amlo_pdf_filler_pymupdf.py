# -*- coding: utf-8 -*-
"""
AMLO PDF表单填充服务 - 基于PyMuPDF (fitz)
负责将数据写入 PDF 表单并在需要时进行 flatten，
同时手动绘制报告编号和文字，确保泰文/中文/英文都能正常显示。
"""

import os
import re
from typing import Any, Dict, List, Optional, Tuple
import fitz  # PyMuPDF

try:
    from .amlo_csv_field_loader import get_csv_field_loader
except ImportError:
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from amlo_csv_field_loader import get_csv_field_loader


class AMLOPDFFillerPyMuPDF:
    """AMLO PDF 表单填充器"""

    _CJK_FONT_CANDIDATES: Tuple[Tuple[str, str], ...] = (
        # 优先使用TTF格式，PyMuPDF对TTC支持有限
        ('SimHei', r'C:\Windows\Fonts\simhei.ttf'),  # 黑体
        ('SimKai', r'C:\Windows\Fonts\simkai.ttf'),  # 楷体
        ('ArialUnicodeMS', r'C:\Windows\Fonts\arialuni.ttf'),
        # TTC作为备选
        ('MicrosoftYaHei', r'C:\Windows\Fonts\msyh.ttc'),
        ('SimSun', r'C:\Windows\Fonts\simsun.ttc'),
    )

    def __init__(self) -> None:
        self.csv_loader = get_csv_field_loader()
        self._report_font_name = 'Sarabun'
        self._report_font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'Sarabun-Regular.ttf')
        self._font_warning_logged = False
        self._cjk_font: Tuple[Optional[str], Optional[str]] = self._resolve_system_font(self._CJK_FONT_CANDIDATES)
        if not self._cjk_font[0]:
            print("[AMLOPDFFillerPyMuPDF] Warning: no Chinese-compatible font located; Chinese characters may not render.")
        print("[AMLOPDFFillerPyMuPDF] Initialized with CSV field mappings")

        # 字体注册缓存
        self._font_registry = {}  # {doc_id: {font_path: xref}}

    def fill_form(self, report_type: str, data: Dict[str, Any], output_path: str, flatten: bool = False) -> str:
        """填充表单并可选地进行 flatten。

        默认 flatten=False 保持表单可编辑。
        设置 flatten=True 将表单转换为静态内容（不可编辑）。
        """
        try:
            template_path = self.csv_loader.get_template_path(report_type)
            print(f"[AMLOPDFFillerPyMuPDF] Using template: {template_path}")

            doc = fitz.open(template_path)
            print(f"[AMLOPDFFillerPyMuPDF] Opened PDF: {doc.page_count} pages")

            field_mapping = self.csv_loader.get_field_mapping(report_type)
            filled_count, report_number_jobs, text_overlay_jobs = self._fill_pdf_fields(doc, data, field_mapping, flatten)
            print(f"[AMLOPDFFillerPyMuPDF] Filled {filled_count} fields")

            if not flatten:
                # 保持可编辑模式：只填充字段值，不使用overlay，不移除字段
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                doc.save(output_path, garbage=4, deflate=True)
                doc.close()
                print(f"[AMLOPDFFillerPyMuPDF] Editable PDF generated: {output_path}")
                return output_path

            print("[AMLOPDFFillerPyMuPDF] Flattening PDF...")

            # 步骤1：先移除所有表单字段（但保留填写的值）
            for page in doc:
                widgets = list(page.widgets()) if page.widgets() else []
                for widget in widgets:
                    try:
                        # 确保字段值已更新
                        widget.update()
                    except Exception:
                        pass

            # 步骤2：现在绘制overlays（在移除字段后，确保在最上层）
            self._render_overlays(doc, report_number_jobs, text_overlay_jobs)

            # 步骤3：再次遍历移除字段widget对象
            for page in doc:
                widgets = list(page.widgets()) if page.widgets() else []
                for widget in widgets:
                    try:
                        widget.remove()
                    except Exception:
                        pass

            # 步骤4：保存（不使用clean以保留字体）
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            doc.save(output_path, garbage=4, deflate=True, clean=False)
            doc.close()

            print(f"[AMLOPDFFillerPyMuPDF] PDF flattened successfully -> {output_path}")
            return output_path

        except Exception as exc:
            print(f"[AMLOPDFFillerPyMuPDF] Error filling form: {exc}")
            import traceback
            traceback.print_exc()
            raise

    # ------------------------------------------------------------------ #
    # 内部方法
    # ------------------------------------------------------------------ #

    def _resolve_system_font(self, candidates: Tuple[Tuple[str, str], ...]) -> Tuple[Optional[str], Optional[str]]:
        for font_name, font_path in candidates:
            if os.path.exists(font_path):
                return font_name, font_path
        return None, None

    def _ensure_font_registered(self, doc: fitz.Document, font_name: Optional[str], font_path: Optional[str]) -> Optional[int]:
        """
        确保字体被注册到PDF文档中，并返回字体的xref引用。
        这样可以确保字体被嵌入，避免乱码问题。
        """
        if not font_path or not os.path.exists(font_path):
            return None

        doc_id = id(doc)
        if doc_id not in self._font_registry:
            self._font_registry[doc_id] = {}

        # 检查是否已经注册过
        if font_path in self._font_registry[doc_id]:
            return self._font_registry[doc_id][font_path]

        # 注册新字体
        try:
            # 对于PyMuPDF，我们使用fontfile参数直接在insert_textbox时指定
            # 但我们仍然缓存字体路径以避免重复检查
            self._font_registry[doc_id][font_path] = True
            return None
        except Exception as e:
            print(f"[AMLOPDFFillerPyMuPDF] Failed to register font {font_path}: {e}")
            return None

    def _select_font_for_text(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        if not text:
            return self._report_font_name, self._report_font_path

        has_cjk = any(self._is_cjk_char(ch) for ch in text)
        has_thai = any(self._is_thai_char(ch) for ch in text)

        if has_cjk and self._cjk_font[0]:
            return self._cjk_font

        if has_thai:
            return self._report_font_name, self._report_font_path

        return self._report_font_name, self._report_font_path

    def _fill_pdf_fields(
        self,
        doc: fitz.Document,
        data: Dict[str, Any],
        field_mapping: Dict,
        flatten: bool
    ) -> tuple[int, List[Dict[str, Any]], List[Dict[str, Any]]]:
        filled_count = 0
        report_number_jobs: List[Dict[str, Any]] = []
        text_overlay_jobs: List[Dict[str, Any]] = []

        try:
            for page_index in range(doc.page_count):
                page = doc[page_index]
                widgets = page.widgets() or []

                for widget in widgets:
                    field_name = widget.field_name
                    if not field_name or field_name not in data:
                        continue

                    value = data[field_name]
                    field_info = field_mapping.get(field_name, {})
                    try:
                        # 特殊处理：报告编号字段（fill_52）
                        if field_name == 'fill_52':
                            if flatten:
                                # Flatten模式：记录位置，稍后通过overlay绘制
                                report_number_jobs.append({
                                    'page_index': page_index,
                                    'rect': widget.rect,
                                    'value': str(value)
                                })
                                widget.field_value = ''
                                widget.update()
                                filled_count += 1
                                continue
                            else:
                                # 可编辑模式：直接填充字段值
                                widget.field_value = str(value) if value is not None else ''
                                widget.update()
                                filled_count += 1
                                continue

                        if widget.field_type == fitz.PDF_WIDGET_TYPE_TEXT:
                            str_value = str(value) if value is not None else ''
                            str_value = str_value.replace('\r\n', '\n')

                            font_name, font_path = self._select_font_for_text(str_value)
                            self._ensure_font_registered(doc, font_name, font_path)

                            if font_name:
                                widget.text_font = font_name

                            if widget.text_fontsize is None or widget.text_fontsize <= 0:
                                widget.text_fontsize = 10

                            widget.field_value = str_value
                            widget.update()

                            if flatten and str_value:
                                # Flatten模式：记录overlay绘制任务
                                # 安全获取text_align，默认为左对齐
                                try:
                                    align = widget.text_align if hasattr(widget, 'text_align') and widget.text_align in (0, 1, 2) else 0
                                except:
                                    align = 0

                                text_overlay_jobs.append({
                                    'page_index': page_index,
                                    'rect': widget.rect,
                                    'value': str_value,
                                    'fontname': font_name,
                                    'fontfile': font_path,
                                    'fontsize': widget.text_fontsize,
                                    'align': align,
                                })
                            filled_count += 1
                            continue

                        if widget.field_type == fitz.PDF_WIDGET_TYPE_CHECKBOX:
                            widget.field_value = "Yes" if value in (True, 'true', '1', 1, 'yes', 'Yes', '/Yes') else "Off"
                            widget.update()
                            filled_count += 1
                            continue

                        if widget.field_type in (
                            fitz.PDF_WIDGET_TYPE_COMBOBOX,
                            fitz.PDF_WIDGET_TYPE_LISTBOX,
                            fitz.PDF_WIDGET_TYPE_RADIOBUTTON
                        ):
                            widget.field_value = str(value) if value is not None else ''
                            widget.update()
                            filled_count += 1
                            continue

                        widget.field_value = str(value) if value is not None else ''
                        widget.update()
                        filled_count += 1

                    except Exception as exc:
                        print(f"[AMLOPDFFillerPyMuPDF] Error filling field {field_name}: {exc}")

        except Exception as exc:
            print(f"[AMLOPDFFillerPyMuPDF] Error in _fill_pdf_fields: {exc}")
            import traceback
            traceback.print_exc()

        return filled_count, report_number_jobs, text_overlay_jobs

    def _render_overlays(
        self,
        doc: fitz.Document,
        report_number_jobs: List[Dict[str, Any]],
        text_overlay_jobs: List[Dict[str, Any]]
    ) -> None:
        # 为每个页面创建一个Shape对象来绘制所有内容
        page_shapes = {}

        if report_number_jobs:
            self._draw_report_numbers_to_shapes(doc, report_number_jobs, page_shapes)
        if text_overlay_jobs:
            self._draw_text_overlays_to_shapes(doc, text_overlay_jobs, page_shapes)

        # 提交所有Shape
        for page_index, shape in page_shapes.items():
            shape.commit()

    def _draw_report_numbers_to_shapes(
        self,
        doc: fitz.Document,
        jobs: List[Dict[str, Any]],
        page_shapes: Dict[int, Any]
    ) -> None:
        """使用Shape方法绘制报告编号（写入内容流而非overlay）"""
        if not jobs:
            return

        self._ensure_font_registered(doc, self._report_font_name, self._report_font_path)

        for job in jobs:
            page_index = job.get('page_index')
            rect = job.get('rect')
            value = (job.get('value') or '').strip()

            if rect is None or page_index is None:
                continue

            # 获取或创建该页面的Shape
            if page_index not in page_shapes:
                page_shapes[page_index] = doc[page_index].new_shape()

            shape = page_shapes[page_index]

            # 简单方案：直接在整个字段内居中显示完整的报告编号
            # 不再尝试复杂的格子布局，直接一次性绘制
            shape.insert_textbox(
                rect,
                value,
                fontsize=10,
                fontname=self._report_font_name,
                fontfile=self._report_font_path,
                color=(0, 0, 0),  # 黑色
                align=1  # 居中
            )

    def _draw_report_numbers_old(self, doc: fitz.Document, jobs: List[Dict[str, Any]]) -> None:
        if not jobs:
            return

        self._ensure_font_registered(doc, self._report_font_name, self._report_font_path)

        for job in jobs:
            page_index = job.get('page_index')
            rect = job.get('rect')
            value = (job.get('value') or '').strip()

            if rect is None or page_index is None:
                continue

            page = doc[page_index]

            # 使用实际字段尺寸计算布局
            field_width = rect.width
            field_height = rect.height

            # 根据实际测量值调整布局参数
            # fill_52字段实际宽度约268.69pt，高度约23.89pt
            # 布局：3格-gap-3格-gap-2格-gap-序列号
            # 格子数量：3+3+2=8个，间距7个，组间距3个
            # 简化策略：平均分配空间给8个数字框，序列号占剩余空间

            num_boxes = 8  # 总共8个数字框
            gap_ratio = 0.15  # 间距占框宽度的比例

            # 计算每个数字框的宽度（包含间距）
            box_unit_width = field_width / (num_boxes + num_boxes * gap_ratio + 6)  # 6为序列号预留更多空间
            box_size = box_unit_width  # 框宽度
            gap = box_unit_width * gap_ratio  # 间距
            group_gap = gap * 1.2  # 组间距稍大

            # 高度使用字段高度的大部分
            box_height = field_height * 0.90

            # 垂直居中
            y_offset = (field_height - box_height) / 2
            y0 = rect.y0 + y_offset
            y1 = y0 + box_height

            # 字体大小根据框高度调整，稍微小一点以确保能放下
            fontsize = box_height * 0.65

            group1, group2, group3, serial = self._split_report_number(value)
            groups = [group1, group2, group3]
            expected_lengths = [3, 3, 2]

            cursor = rect.x0 + gap * 0.3  # 左侧留小间距
            for group, expected_len in zip(groups, expected_lengths):
                for idx_char in range(expected_len):
                    ch = group[idx_char] if idx_char < len(group) else ''
                    box_rect = fitz.Rect(cursor, y0, cursor + box_size,  y1)
                    page.insert_textbox(
                        box_rect,
                        ch,
                        fontsize=fontsize,
                        fontname=self._report_font_name,
                        fontfile=self._report_font_path,
                        set_simple=0,  # 使用完整的CID字体支持
                        align=1,
                        overlay=True
                    )
                    cursor += box_size
                    if idx_char < expected_len - 1:
                        cursor += gap
                cursor += group_gap

            serial_rect = fitz.Rect(cursor, y0, rect.x1 - gap * 0.5, y1)
            page.insert_textbox(
                serial_rect,
                serial,
                fontsize=fontsize,
                fontname=self._report_font_name,
                fontfile=self._report_font_path,
                set_simple=0,  # 使用完整的CID字体支持
                align=1,
                overlay=True
            )

    def _draw_text_overlays_to_shapes(
        self,
        doc: fitz.Document,
        jobs: List[Dict[str, Any]],
        page_shapes: Dict[int, Any]
    ) -> None:
        """使用Shape方法绘制文本（写入内容流而非overlay）"""
        if not jobs:
            return

        for job in jobs:
            page_index = job.get('page_index')
            rect = job.get('rect')
            value = job.get('value', '')

            if page_index is None or rect is None or not value:
                continue

            # 获取或创建该页面的Shape
            if page_index not in page_shapes:
                try:
                    page_shapes[page_index] = doc[page_index].new_shape()
                except IndexError:
                    continue

            shape = page_shapes[page_index]

            fontname = job.get('fontname') or self._report_font_name
            fontfile = job.get('fontfile') or self._report_font_path
            fontsize = job.get('fontsize') or 10
            align = job.get('align', 0)

            self._ensure_font_registered(doc, fontname, fontfile)

            try:
                shape.insert_textbox(
                    rect,
                    value,
                    fontsize=fontsize,
                    fontname=fontname,
                    fontfile=fontfile,
                    set_simple=0,
                    color=(0, 0, 0),  # 黑色
                    align=align
                )
            except Exception as exc:
                print(f"[AMLOPDFFillerPyMuPDF] Failed to draw text with shape: {exc}")

    def _draw_text_overlays_old(self, doc: fitz.Document, jobs: List[Dict[str, Any]]) -> None:
        if not jobs:
            return

        for job in jobs:
            page_index = job.get('page_index')
            rect = job.get('rect')
            value = job.get('value', '')

            if page_index is None or rect is None or not value:
                continue

            try:
                page = doc[page_index]
            except IndexError:
                continue

            fontname = job.get('fontname') or self._report_font_name
            fontfile = job.get('fontfile') or self._report_font_path
            fontsize = job.get('fontsize') or 10
            align = job.get('align')

            if align == 1:
                align = fitz.TEXT_ALIGN_CENTER
            elif align == 2:
                align = fitz.TEXT_ALIGN_RIGHT
            else:
                align = fitz.TEXT_ALIGN_LEFT

            self._ensure_font_registered(doc, fontname, fontfile)

            try:
                # 强制使用fontfile参数以确保字体被嵌入
                # set_simple=0确保使用完整的Unicode支持
                result = page.insert_textbox(
                    rect,
                    value,
                    fontsize=fontsize,
                    fontname=fontname,
                    fontfile=fontfile,
                    set_simple=0,  # 使用完整的CID字体支持Unicode
                    align=align,
                    overlay=True,
                    render_mode=0  # 0=填充模式（默认）
                )
                if result < 0:
                    print(f"[AMLOPDFFillerPyMuPDF] Warning: Text may not fit in box (error code {result}): {value[:50]}...")
            except Exception as exc:
                print(f"[AMLOPDFFillerPyMuPDF] Failed to draw text overlay: {exc}")
                # 尝试备用方法：使用insert_text
                try:
                    # 计算文本插入点（左上角）
                    insert_point = fitz.Point(rect.x0 + 2, rect.y0 + fontsize + 2)
                    page.insert_text(
                        insert_point,
                        value,
                        fontsize=fontsize,
                        fontname=fontname,
                        fontfile=fontfile,
                        set_simple=0,
                        overlay=True
                    )
                    print(f"[AMLOPDFFillerPyMuPDF] Used fallback insert_text method")
                except Exception as exc2:
                    print(f"[AMLOPDFFillerPyMuPDF] Fallback also failed: {exc2}")

    @staticmethod
    def _split_report_number(value: str) -> tuple[str, str, str, str]:
        raw = (value or '').strip()
        if not raw:
            return '', '', '', ''

        filtered = ''.join(ch for ch in raw if ch.isalnum() or ch == '-')
        parts = filtered.split('-') if '-' in filtered else []

        if len(parts) >= 4:
            part1, part2, part3 = parts[0], parts[1], parts[2]
            serial_raw = ''.join(parts[3:])
        else:
            digits_only = ''.join(ch for ch in filtered if ch.isdigit())
            part1 = digits_only[:3]
            part2 = digits_only[3:6]
            part3 = digits_only[6:8]
            serial_raw = ''.join(ch for ch in filtered if ch.isalnum())[8:] or filtered

        def normalize(segment: str, length: int) -> str:
            normalized = ''.join(ch for ch in (segment or '').upper() if ch.isalnum())
            if not normalized:
                return ''
            digits = ''.join(ch for ch in normalized if ch.isdigit())
            candidate = digits if digits else normalized
            trimmed = candidate[-length:]
            if digits and trimmed.isdigit():
                return trimmed.zfill(length)
            if len(trimmed) < length:
                pad_char = '0' if trimmed.isdigit() else ' '
                return trimmed.rjust(length, pad_char)
            return trimmed

        group1 = normalize(part1, 3)
        group2 = normalize(part2, 3)
        group3 = normalize(part3, 2)
        serial = ''.join(ch for ch in (serial_raw or '').upper() if ch.isalnum())

        return group1, group2, group3, serial or serial_raw

    @staticmethod
    def _is_cjk_char(char: str) -> bool:
        code = ord(char)
        return (
            0x4E00 <= code <= 0x9FFF or
            0x3400 <= code <= 0x4DBF or
            0x20000 <= code <= 0x2A6DF or
            0x2A700 <= code <= 0x2B73F or
            0x2B740 <= code <= 0x2B81F or
            0x2B820 <= code <= 0x2CEAF or
            0xF900 <= code <= 0xFAFF or
            0x2F800 <= code <= 0x2FA1F
        )

    @staticmethod
    def _is_thai_char(char: str) -> bool:
        code = ord(char)
        return 0x0E00 <= code <= 0x0E7F


if __name__ == '__main__':
    filler = AMLOPDFFillerPyMuPDF()
    sample_data = {
        'fill_52': 'FI-001-68-100001USD',
        'fill_4': '测试用户 ทดสอบ',
        'fill_5': '广东省深圳市福田区梅林街道梅兴苑2-1203',
        'fill_48': '2500000',
        'fill_50': '2500000',
        'Check Box2': True,
        'Check Box3': False,
    }
    output_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'test_output')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'test_amlo_pymupdf.pdf')
    filler.fill_form('AMLO-1-01', sample_data, output_path, flatten=True)
