# -*- coding: utf-8 -*-
"""
AMLO-1-01 PDF生成器 - 基于JSON配置文件
严格按照amlo_101_layout_config.json中的坐标生成PDF
"""

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
import os
import json
from typing import Dict

class AMLO101FromConfig:
    """基于JSON配置的AMLO-1-01生成器"""

    def __init__(self):
        # 加载配置文件
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'amlo_101_layout_config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        # 注册字体
        self._register_fonts()

    def _register_fonts(self):
        """注册泰语字体"""
        try:
            font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'Sarabun-Regular.ttf')
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('Sarabun', font_path))
                print("[OK] Thai font registered")
        except Exception as e:
            print(f"Font error: {e}")

    def _draw_borders(self, c: canvas.Canvas):
        """绘制三层边框"""
        borders = self.config['borders']

        # 外层边框
        outer = borders['outer']
        c.saveState()
        c.setLineWidth(outer['line_width'])
        c.rect(outer['x'], outer['y'], outer['width'], outer['height'])
        c.restoreState()

        # 中层边框（粗线）
        middle = borders['middle']
        c.saveState()
        c.setLineWidth(middle['line_width'])
        c.rect(middle['x'], middle['y'], middle['width'], middle['height'])
        c.restoreState()

        # 内层边框
        inner = borders['inner']
        c.saveState()
        c.setLineWidth(inner['line_width'])
        c.rect(inner['x'], inner['y'], inner['width'], inner['height'])
        c.restoreState()

    def _draw_section_title(self, c: canvas.Canvas):
        """绘制标题区域"""
        section = self.config['section_title']

        # 绘制灰色背景框
        c.saveState()
        c.setFillColor(HexColor(section['background_color']))
        c.setLineWidth(section['border_width'])
        c.rect(section['x'], section['y'], section['width'], section['height'],
               fill=1, stroke=1)
        c.restoreState()

        # 绘制标题文字
        text = section['text']
        c.saveState()
        c.setFillColor(HexColor('#000000'))
        c.setFont(text['font'], text['font_size'])
        c.drawString(text['x'], text['y'], text['content'])
        c.restoreState()

        # 绘制副标题
        subtitle = section['subtitle']
        c.setFont(subtitle['font'], subtitle['font_size'])
        c.drawString(subtitle['x'], subtitle['y'], subtitle['content'])

    def _draw_form_code(self, c: canvas.Canvas):
        """绘制表单代码"""
        form_code = self.config['form_code']
        c.saveState()
        c.setFont(form_code['font'], form_code['font_size'])
        c.drawRightString(form_code['x'], form_code['y'], form_code['text'])
        c.restoreState()

    def _draw_report_number_area(self, c: canvas.Canvas):
        """绘制报告编号区域"""
        area = self.config['report_number_area']

        # เลขที่ 标签
        label = area['label']
        c.setFont('Sarabun', label['font_size'])
        c.drawString(label['x'], label['y'], label['text'])

        # 机构代码框
        inst = area['institution_boxes']
        self._draw_boxes(c, inst['x'], inst['y'], inst['count'],
                        inst['box_size'], inst['box_gap'])
        c.setFont('Sarabun', inst['label']['font_size'])
        c.drawCentredString(inst['label']['x'], inst['label']['y'],
                           inst['label']['text'])

        # 分隔线1
        sep1 = area['separator_line_1']
        c.setLineWidth(sep1['line_width'])
        c.line(sep1['x1'], sep1['y1'], sep1['x2'], sep1['y2'])

        # 分行代码框
        branch = area['branch_boxes']
        self._draw_boxes(c, branch['x'], branch['y'], branch['count'],
                        branch['box_size'], branch['box_gap'])
        c.setFont('Sarabun', branch['label']['font_size'])
        c.drawCentredString(branch['label']['x'], branch['label']['y'],
                           branch['label']['text'])

        # 分隔线2
        sep2 = area['separator_line_2']
        c.setLineWidth(sep2['line_width'])
        c.line(sep2['x1'], sep2['y1'], sep2['x2'], sep2['y2'])

        # 年份框
        year = area['year_boxes']
        self._draw_boxes(c, year['x'], year['y'], year['count'],
                        year['box_size'], year['box_gap'])
        c.setFont('Sarabun', year['label']['font_size'])
        c.drawString(year['label']['x'], year['label']['y'],
                    year['label']['text'])
        c.drawString(year['sub_label']['x'], year['sub_label']['y'],
                    year['sub_label']['text'])

        # 分隔线3
        sep3 = area['separator_line_3']
        c.setLineWidth(sep3['line_width'])
        c.line(sep3['x1'], sep3['y1'], sep3['x2'], sep3['y2'])

        # 序号框
        serial = area['serial_number_box']
        c.rect(serial['x'], serial['y'], serial['width'], serial['height'])
        c.setFont('Sarabun', serial['label']['font_size'])
        c.drawString(serial['label']['x'], serial['label']['y'],
                    serial['label']['text'])

    def _draw_main_separators(self, c: canvas.Canvas):
        """绘制主分隔线（3层线）"""
        seps = self.config['main_separators']

        for key in ['separator_1', 'separator_2', 'separator_3']:
            sep = seps[key]
            c.setLineWidth(sep['line_width'])
            c.line(sep['x_start'], sep['y'], sep['x_end'], sep['y'])

    def _draw_report_type_section(self, c: canvas.Canvas):
        """绘制报告类型选择区"""
        section = self.config['report_type_section']

        # รายงานฉบับหลัก
        cb1 = section['checkbox_original']
        self._draw_checkbox(c, cb1['x'], cb1['y'], cb1['size'])
        c.setFont('Sarabun', cb1['label']['font_size'])
        c.drawString(cb1['label']['x'], cb1['label']['y'], cb1['label']['text'])

        # รายงานฉบับแก้ไข
        cb2 = section['checkbox_revised']
        self._draw_checkbox(c, cb2['x'], cb2['y'], cb2['size'])
        c.setFont('Sarabun', cb2['label']['font_size'])
        c.drawString(cb2['label']['x'], cb2['label']['y'], cb2['label']['text'])

        # 下划线和标签
        rev_line = section['revision_number_line']
        c.setLineWidth(rev_line['line_width'])
        c.line(rev_line['x'], rev_line['y'], rev_line['x'] + rev_line['width'], rev_line['y'])

        date_label = section['date_label']
        c.setFont('Sarabun', date_label['font_size'])
        c.drawString(date_label['x'], date_label['y'], date_label['text'])

        date_line = section['date_line']
        c.setLineWidth(date_line['line_width'])
        c.line(date_line['x'], date_line['y'], date_line['x'] + date_line['width'], date_line['y'])

        # 竖线
        v_sep = section['vertical_separator']
        c.setLineWidth(v_sep['line_width'])
        c.line(v_sep['x'], v_sep['y'], v_sep['x'], v_sep['y'] + v_sep['height'])

        # รวมเอกสาร
        total_label = section['total_pages_label']
        c.setFont('Sarabun', total_label['font_size'])
        c.drawString(total_label['x'], total_label['y'], total_label['text'])

        total_line = section['total_pages_line']
        c.setLineWidth(total_line['line_width'])
        c.line(total_line['x'], total_line['y'], total_line['x'] + total_line['width'], total_line['y'])

        pages_unit = section['pages_unit']
        c.setFont('Sarabun', pages_unit['font_size'])
        c.drawString(pages_unit['x'], pages_unit['y'], pages_unit['text'])

    def _draw_thick_separator(self, c: canvas.Canvas, config_key: str):
        """绘制粗分隔线"""
        sep = self.config[config_key]
        c.setLineWidth(sep['line_width'])
        c.line(sep['x_start'], sep['y'], sep['x_end'], sep['y'])

    def _draw_section_1(self, c: canvas.Canvas):
        """绘制ส่วนที่ ๑"""
        section = self.config['section_1']

        # 标题框
        title_box = section['title_box']
        c.saveState()
        c.setFillColor(HexColor(title_box['background_color']))
        c.setLineWidth(title_box['border_width'])
        c.rect(title_box['x'], title_box['y'], title_box['width'], title_box['height'],
               fill=1, stroke=1)
        c.setFillColor(HexColor('#000000'))
        c.setFont('Sarabun', title_box['text']['font_size'])
        c.drawString(title_box['text']['x'], title_box['text']['y'],
                    title_box['text']['content'])
        c.restoreState()

        # 13位ID框
        id_boxes = section['id_boxes']
        self._draw_boxes(c, id_boxes['x'], id_boxes['y'], id_boxes['count'],
                        id_boxes['box_size'], id_boxes['box_gap'])

        # ID说明灰色框
        id_exp = section['id_explanation_box']
        c.saveState()
        c.setFillColor(HexColor(id_exp['background_color']))
        c.rect(id_exp['x'], id_exp['y'], id_exp['width'], id_exp['height'],
               fill=1, stroke=0)
        c.setFillColor(HexColor('#000000'))
        c.setFont('Sarabun', 6.5)
        for line in id_exp['lines']:
            c.drawString(id_exp['x'] + 5, line['y'], line['text'])
        c.restoreState()

        # 字段
        self._draw_section_1_fields(c, section['fields'])

    def _draw_section_1_fields(self, c: canvas.Canvas, fields: Dict):
        """绘制ส่วนที่ ๑的字段"""
        # ๑.๑ ชื่อ-นามสกุล
        f11 = fields['field_1_1']
        c.setFont('Sarabun', f11['label']['font_size'])
        c.drawString(f11['label']['x'], f11['label']['y'], f11['label']['text'])
        ul = f11['underline']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # 复选框
        cb_self = fields['checkbox_self']
        self._draw_checkbox(c, cb_self['x'], cb_self['y'], cb_self['size'])
        c.setFont('Sarabun', cb_self['label']['font_size'])
        c.drawString(cb_self['label']['x'], cb_self['label']['y'], cb_self['label']['text'])

        cb_agent = fields['checkbox_agent']
        self._draw_checkbox(c, cb_agent['x'], cb_agent['y'], cb_agent['size'])
        c.setFont('Sarabun', cb_agent['label']['font_size'])
        c.drawString(cb_agent['label']['x'], cb_agent['label']['y'], cb_agent['label']['text'])

        # ๑.๒ ที่อยู่
        f12 = fields['field_1_2']
        c.setFont('Sarabun', f12['label']['font_size'])
        c.drawString(f12['label']['x'], f12['label']['y'], f12['label']['text'])
        ul = f12['underline']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # ๑.๒ 第二行
        f12_l2 = fields['field_1_3_line2']
        c.setFont('Sarabun', f12_l2['phone_label']['font_size'])
        c.drawString(f12_l2['phone_label']['x'], f12_l2['phone_label']['y'],
                    f12_l2['phone_label']['text'])
        ul = f12_l2['phone_line']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        c.drawString(f12_l2['fax_label']['x'], f12_l2['fax_label']['y'],
                    f12_l2['fax_label']['text'])
        ul = f12_l2['fax_line']
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # ๑.๓
        f13 = fields['field_1_3']
        c.setFont('Sarabun', f13['occupation_label']['font_size'])
        c.drawString(f13['occupation_label']['x'], f13['occupation_label']['y'],
                    f13['occupation_label']['text'])
        ul = f13['occupation_line']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        c.drawString(f13['workplace_label']['x'], f13['workplace_label']['y'],
                    f13['workplace_label']['text'])
        ul = f13['workplace_line']
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        c.drawString(f13['phone_label']['x'], f13['phone_label']['y'],
                    f13['phone_label']['text'])
        ul = f13['phone_line']
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # ๑.๔
        f14 = fields['field_1_4']
        c.setFont('Sarabun', f14['label']['font_size'])
        c.drawString(f14['label']['x'], f14['label']['y'], f14['label']['text'])
        ul = f14['line']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # ๑.๔ 第二行
        f14_l2 = fields['field_1_4_line2']
        c.setFont('Sarabun', f14_l2['phone_label']['font_size'])
        c.drawString(f14_l2['phone_label']['x'], f14_l2['phone_label']['y'],
                    f14_l2['phone_label']['text'])
        ul = f14_l2['phone_line']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        c.drawString(f14_l2['fax_label']['x'], f14_l2['fax_label']['y'],
                    f14_l2['fax_label']['text'])
        ul = f14_l2['fax_line']
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # ๑.๕
        f15 = fields['field_1_5']
        c.setFont('Sarabun', f15['label']['font_size'])
        c.drawString(f15['label']['x'], f15['label']['y'], f15['label']['text'])

        # ๑.๕ 复选框
        for cb_data in f15['checkboxes_line1']:
            self._draw_checkbox(c, cb_data['x'], cb_data['y'], 8.5)
            c.setFont('Sarabun', 8)
            c.drawString(cb_data['x'] + 11.5, cb_data['y'] + 1, cb_data['label'])

        for cb_data in f15['checkboxes_line2']:
            self._draw_checkbox(c, cb_data['x'], cb_data['y'], 8.5)
            c.setFont('Sarabun', 8)
            c.drawString(cb_data['x'] + 11.5, cb_data['y'] + 1, cb_data['label'])

        ul = f15['other_line']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # ๑.๕ 详细信息
        f15_det = fields['field_1_5_details']
        c.setFont('Sarabun', f15_det['number_label']['font_size'])
        c.drawString(f15_det['number_label']['x'], f15_det['number_label']['y'],
                    f15_det['number_label']['text'])
        ul = f15_det['number_line']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        c.drawString(f15_det['issued_by_label']['x'], f15_det['issued_by_label']['y'],
                    f15_det['issued_by_label']['text'])
        ul = f15_det['issued_by_line']
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        c.drawString(f15_det['issued_date_label']['x'], f15_det['issued_date_label']['y'],
                    f15_det['issued_date_label']['text'])
        ul = f15_det['issued_date_line']
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        c.drawString(f15_det['expiry_label']['x'], f15_det['expiry_label']['y'],
                    f15_det['expiry_label']['text'])
        ul = f15_det['expiry_line']
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

    def _draw_section_2(self, c: canvas.Canvas):
        """绘制ส่วนที่ ๒ - 简化版本，结构与ส่วนที่ ๑类似"""
        section = self.config['section_2']

        # 标题框
        title_box = section['title_box']
        c.saveState()
        c.setFillColor(HexColor(title_box['background_color']))
        c.setLineWidth(title_box['border_width'])
        c.rect(title_box['x'], title_box['y'], title_box['width'], title_box['height'],
               fill=1, stroke=1)
        c.setFillColor(HexColor('#000000'))
        c.setFont('Sarabun', title_box['text']['font_size'])
        c.drawString(title_box['text']['x'], title_box['text']['y'],
                    title_box['text']['content'])
        c.restoreState()

        # 右侧3个复选框
        cbs_right = section['checkboxes_right']
        for key in ['checkbox_1', 'checkbox_2', 'checkbox_3']:
            cb = cbs_right[key]
            self._draw_checkbox(c, cbs_right['x'], cb['y'], 8.5)
            c.setFont('Sarabun', 8)
            c.drawString(cbs_right['x'] + 11.5, cb['y'] + 1, cb['label'])

        # 13位ID框
        id_boxes = section['id_boxes']
        self._draw_boxes(c, id_boxes['x'], id_boxes['y'], id_boxes['count'],
                        id_boxes['box_size'], id_boxes['box_gap'])

        # ID说明灰色框
        id_exp = section['id_explanation_box']
        c.saveState()
        c.setFillColor(HexColor(id_exp['background_color']))
        c.rect(id_exp['x'], id_exp['y'], id_exp['width'], id_exp['height'],
               fill=1, stroke=0)
        c.setFillColor(HexColor('#000000'))
        c.setFont('Sarabun', 6.5)
        for line in id_exp['lines']:
            c.drawString(id_exp['x'] + 5, line['y'], line['text'])
        c.restoreState()

        # 字段（简化处理）
        self._draw_section_2_fields(c, section['fields'])

    def _draw_section_2_fields(self, c: canvas.Canvas, fields: Dict):
        """绘制ส่วนที่ ๒的字段"""
        # ๒.๑
        f21 = fields['field_2_1']
        c.setFont('Sarabun', f21['label']['font_size'])
        c.drawString(f21['label']['x'], f21['label']['y'], f21['label']['text'])
        ul = f21['underline']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # ๒.๒
        f22 = fields['field_2_2']
        c.setFont('Sarabun', f22['label']['font_size'])
        c.drawString(f22['label']['x'], f22['label']['y'], f22['label']['text'])
        ul = f22['underline']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # ๒.๒ 第二行
        f22_l2 = fields['field_2_2_line2']
        ul = f22_l2['underline']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        c.setFont('Sarabun', f22_l2['phone_label']['font_size'])
        c.drawString(f22_l2['phone_label']['x'], f22_l2['phone_label']['y'],
                    f22_l2['phone_label']['text'])
        ul = f22_l2['phone_line']
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        c.drawString(f22_l2['fax_label']['x'], f22_l2['fax_label']['y'],
                    f22_l2['fax_label']['text'])
        ul = f22_l2['fax_line']
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # ๒.๓
        f23 = fields['field_2_3']
        c.setFont('Sarabun', f23['occupation_label']['font_size'])
        c.drawString(f23['occupation_label']['x'], f23['occupation_label']['y'],
                    f23['occupation_label']['text'])
        ul = f23['occupation_line']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        c.drawString(f23['workplace_label']['x'], f23['workplace_label']['y'],
                    f23['workplace_label']['text'])
        ul = f23['workplace_line']
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        c.drawString(f23['phone_label']['x'], f23['phone_label']['y'],
                    f23['phone_label']['text'])
        ul = f23['phone_line']
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # ๒.๓ นิติบุคคล
        f23_corp = fields['field_2_3_corporate']
        c.setFont('Sarabun', f23_corp['label']['font_size'])
        c.drawString(f23_corp['label']['x'], f23_corp['label']['y'],
                    f23_corp['label']['text'])
        ul = f23_corp['underline']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # ๒.๔
        f24 = fields['field_2_4']
        c.setFont('Sarabun', f24['label']['font_size'])
        c.drawString(f24['label']['x'], f24['label']['y'], f24['label']['text'])
        ul = f24['underline']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # ๒.๔ 第二行
        f24_l2 = fields['field_2_4_line2']
        ul = f24_l2['underline']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        c.setFont('Sarabun', f24_l2['phone_label']['font_size'])
        c.drawString(f24_l2['phone_label']['x'], f24_l2['phone_label']['y'],
                    f24_l2['phone_label']['text'])
        ul = f24_l2['phone_line']
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        c.drawString(f24_l2['fax_label']['x'], f24_l2['fax_label']['y'],
                    f24_l2['fax_label']['text'])
        ul = f24_l2['fax_line']
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # ๒.๕
        f25 = fields['field_2_5']
        c.setFont('Sarabun', f25['label']['font_size'])
        c.drawString(f25['label']['x'], f25['label']['y'], f25['label']['text'])

        # ๒.๕ 复选框
        for cb_data in f25['checkboxes_line1']:
            self._draw_checkbox(c, cb_data['x'], cb_data['y'], 8.5)
            c.setFont('Sarabun', 8)
            c.drawString(cb_data['x'] + 11.5, cb_data['y'] + 1, cb_data['label'])

        for cb_data in f25['checkboxes_line2']:
            self._draw_checkbox(c, cb_data['x'], cb_data['y'], 8.5)
            c.setFont('Sarabun', 8)
            c.drawString(cb_data['x'] + 11.5, cb_data['y'] + 1, cb_data['label'])

        # ๒.๕ 详细信息
        f25_det = fields['field_2_5_details']
        c.setFont('Sarabun', f25_det['number_label']['font_size'])
        c.drawString(f25_det['number_label']['x'], f25_det['number_label']['y'],
                    f25_det['number_label']['text'])
        ul = f25_det['number_line']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        c.drawString(f25_det['issued_by_label']['x'], f25_det['issued_by_label']['y'],
                    f25_det['issued_by_label']['text'])
        ul = f25_det['issued_by_line']
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        c.drawString(f25_det['issued_date_label']['x'], f25_det['issued_date_label']['y'],
                    f25_det['issued_date_label']['text'])
        ul = f25_det['issued_date_line']
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        c.drawString(f25_det['expiry_label']['x'], f25_det['expiry_label']['y'],
                    f25_det['expiry_label']['text'])
        ul = f25_det['expiry_line']
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

    def _draw_section_3(self, c: canvas.Canvas):
        """绘制ส่วนที่ ๓ - 交易信息"""
        section = self.config['section_3']

        # 标题框
        title_box = section['title_box']
        c.saveState()
        c.setFillColor(HexColor(title_box['background_color']))
        c.setLineWidth(title_box['border_width'])
        c.rect(title_box['x'], title_box['y'], title_box['width'], title_box['height'],
               fill=1, stroke=1)
        c.setFillColor(HexColor('#000000'))
        c.setFont('Sarabun', title_box['text']['font_size'])
        c.drawString(title_box['text']['x'], title_box['text']['y'],
                    title_box['text']['content'])
        c.restoreState()

        # 交易日期
        trans_date = section['transaction_date']
        c.setFont('Sarabun', trans_date['date_label']['font_size'])
        c.drawString(trans_date['date_label']['x'], trans_date['date_label']['y'],
                    trans_date['date_label']['text'])
        ul = trans_date['date_line']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        c.drawString(trans_date['month_label']['x'], trans_date['month_label']['y'],
                    trans_date['month_label']['text'])
        ul = trans_date['month_line']
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # ๓.๑标签
        f31 = section['field_3_1_label']
        c.setFont('Sarabun', f31['font_size'])
        c.drawString(f31['x'], f31['y'], f31['text'])

        # 交易框
        self._draw_transaction_boxes(c, section['transaction_boxes'])

        # ๓.๒
        f32 = section['field_3_2']
        c.setFont('Sarabun', f32['label']['font_size'])
        c.drawString(f32['label']['x'], f32['label']['y'], f32['label']['text'])
        ul = f32['underline']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # ๓.๓
        f33 = section['field_3_3']
        c.setFont('Sarabun', f33['label']['font_size'])
        c.drawString(f33['label']['x'], f33['label']['y'], f33['label']['text'])
        ul = f33['underline']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

    def _draw_transaction_boxes(self, c: canvas.Canvas, boxes: Dict):
        """绘制交易框"""
        # 左框（ฝากเงิน）
        left = boxes['left_box']
        c.setLineWidth(left['border_width'])
        c.rect(left['x'], left['y'], left['width'], left['height'])

        # 垂直分隔线
        v_sep = left['vertical_separator']
        c.setLineWidth(v_sep['line_width'])
        c.line(v_sep['x'], v_sep['y1'], v_sep['x'], v_sep['y2'])

        # 左框内容
        content = left['content']

        # ฝากเงิน复选框
        cb = content['checkbox_deposit']
        self._draw_checkbox(c, cb['x'], cb['y'], 8.5)
        c.setFont('Sarabun', 8)
        c.drawString(cb['x'] + 11.5, cb['y'] + 1, cb['label'])

        # จำนวน (บาท)
        amt_label = content['amount_column_label']
        c.setFont('Sarabun', amt_label['font_size'])
        c.drawString(amt_label['x'], amt_label['y'], amt_label['text'])

        # 账号框
        acc_label = content['account_number_label']
        c.setFont('Sarabun', acc_label['font_size'])
        c.drawString(acc_label['x'], acc_label['y'], acc_label['text'])
        acc_boxes = content['account_number_boxes']
        self._draw_boxes(c, acc_boxes['x'], acc_boxes['y'], acc_boxes['count'],
                        acc_boxes['box_size'], acc_boxes['box_gap'])

        # 相关账户
        rel_label = content['related_account_label']
        c.setFont('Sarabun', rel_label['font_size'])
        c.drawString(rel_label['x'], rel_label['y'], rel_label['text'])
        rel_boxes = content['related_account_boxes']
        self._draw_boxes(c, rel_boxes['x'], rel_boxes['y'], rel_boxes['count'],
                        rel_boxes['box_size'], rel_boxes['box_gap'])

        # (หากมี)
        if_any = content['if_any_label']
        c.setFont('Sarabun', if_any['font_size'])
        c.drawString(if_any['x'], if_any['y'], if_any['text'])

        # 其他复选框
        for key in ['checkbox_buy_instruments', 'checkbox_check', 'checkbox_draft',
                   'checkbox_other_instruments', 'checkbox_buy_foreign_currency',
                   'checkbox_other_transaction']:
            cb = content[key]
            self._draw_checkbox(c, cb['x'], cb['y'], 8.5)
            c.setFont('Sarabun', 8)
            c.drawString(cb['x'] + 11.5, cb['y'] + 1, cb['label'])

        # 其他下划线
        for key in ['other_instruments_line', 'other_transaction_line']:
            ul = content[key]
            c.setLineWidth(ul['line_width'])
            c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # 8条虚线
        dashed = content['dashed_lines']
        c.setDash(dashed['dash_pattern'][0], dashed['dash_pattern'][1])
        y = dashed['first_line_y']
        for i in range(dashed['count']):
            c.line(dashed['x_start'], y - i * dashed['y_spacing'],
                  dashed['x_end'], y - i * dashed['y_spacing'])
        c.setDash()  # 恢复实线

        # รวมเงิน
        total = content['total_label']
        c.setFont('Sarabun', total['font_size'])
        c.drawString(total['x'], total['y'], total['text'])

        # 灰色文字框
        total_box = content['total_in_words_box']
        c.saveState()
        c.setFillColor(HexColor(total_box['background_color']))
        c.rect(total_box['x'], total_box['y'], total_box['width'], total_box['height'],
               fill=1, stroke=0)
        c.setFillColor(HexColor('#000000'))
        c.setFont('Sarabun', total_box['text']['font_size'])
        c.drawString(total_box['text']['x'], total_box['text']['y'],
                    total_box['text']['content'])
        c.restoreState()

        # 右框（ถอนเงิน）
        right = boxes['right_box']
        c.setLineWidth(right['border_width'])
        c.rect(right['x'], right['y'], right['width'], right['height'])

        # 垂直分隔线
        v_sep = right['vertical_separator']
        c.setLineWidth(v_sep['line_width'])
        c.line(v_sep['x'], v_sep['y1'], v_sep['x'], v_sep['y2'])

        # 右框内容
        content = right['content']

        # ถอนเงิน复选框
        cb = content['checkbox_withdraw']
        self._draw_checkbox(c, cb['x'], cb['y'], 8.5)
        c.setFont('Sarabun', 8)
        c.drawString(cb['x'] + 11.5, cb['y'] + 1, cb['label'])

        # จำนวน (บาท)
        amt_label = content['amount_column_label']
        c.setFont('Sarabun', amt_label['font_size'])
        c.drawString(amt_label['x'], amt_label['y'], amt_label['text'])

        # 账号框
        acc_label = content['account_number_label']
        c.setFont('Sarabun', acc_label['font_size'])
        c.drawString(acc_label['x'], acc_label['y'], acc_label['text'])
        acc_boxes = content['account_number_boxes']
        self._draw_boxes(c, acc_boxes['x'], acc_boxes['y'], acc_boxes['count'],
                        acc_boxes['box_size'], acc_boxes['box_gap'])

        # 相关账户
        rel_label = content['related_account_label']
        c.setFont('Sarabun', rel_label['font_size'])
        c.drawString(rel_label['x'], rel_label['y'], rel_label['text'])
        rel_boxes = content['related_account_boxes']
        self._draw_boxes(c, rel_boxes['x'], rel_boxes['y'], rel_boxes['count'],
                        rel_boxes['box_size'], rel_boxes['box_gap'])

        # (หากมี)
        if_any = content['if_any_label']
        c.setFont('Sarabun', if_any['font_size'])
        c.drawString(if_any['x'], if_any['y'], if_any['text'])

        # 其他复选框
        for key in ['checkbox_sell_instruments', 'checkbox_check', 'checkbox_draft',
                   'checkbox_other_instruments', 'checkbox_sell_foreign_currency',
                   'checkbox_other_transaction']:
            cb = content[key]
            self._draw_checkbox(c, cb['x'], cb['y'], 8.5)
            c.setFont('Sarabun', 8)
            c.drawString(cb['x'] + 11.5, cb['y'] + 1, cb['label'])

        # 其他下划线
        for key in ['other_instruments_line', 'other_transaction_line']:
            ul = content[key]
            c.setLineWidth(ul['line_width'])
            c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # 8条虚线
        dashed = content['dashed_lines']
        c.setDash(dashed['dash_pattern'][0], dashed['dash_pattern'][1])
        y = dashed['first_line_y']
        for i in range(dashed['count']):
            c.line(dashed['x_start'], y - i * dashed['y_spacing'],
                  dashed['x_end'], y - i * dashed['y_spacing'])
        c.setDash()

        # รวมเงิน
        total = content['total_label']
        c.setFont('Sarabun', total['font_size'])
        c.drawString(total['x'], total['y'], total['text'])

        # 灰色文字框
        total_box = content['total_in_words_box']
        c.saveState()
        c.setFillColor(HexColor(total_box['background_color']))
        c.rect(total_box['x'], total_box['y'], total_box['width'], total_box['height'],
               fill=1, stroke=0)
        c.setFillColor(HexColor('#000000'))
        c.setFont('Sarabun', total_box['text']['font_size'])
        c.drawString(total_box['text']['x'], total_box['text']['y'],
                    total_box['text']['content'])
        c.restoreState()

    def _draw_section_4(self, c: canvas.Canvas):
        """绘制ส่วนที่ ๔ - 签名区"""
        section = self.config['section_4']

        # 标题框
        title_box = section['title_box']
        c.saveState()
        c.setFillColor(HexColor(title_box['background_color']))
        c.setLineWidth(title_box['border_width'])
        c.rect(title_box['x'], title_box['y'], title_box['width'], title_box['height'],
               fill=1, stroke=1)
        c.setFillColor(HexColor('#000000'))
        c.setFont('Sarabun', title_box['text']['font_size'])
        c.drawString(title_box['text']['x'], title_box['text']['y'],
                    title_box['text']['content'])
        c.restoreState()

        # 签名框
        sig_boxes = section['signature_boxes']

        # 左框
        left = sig_boxes['left_box']
        c.rect(left['x'], left['y'], left['width'], left['height'])

        cb1 = left['checkbox_institution_records']
        self._draw_checkbox(c, cb1['x'], cb1['y'], 8.5)
        c.setFont('Sarabun', 7)
        c.drawString(cb1['x'] + 11.5, cb1['y'] + 1, cb1['label'])

        date1 = left['date_label_1']
        c.setFont('Sarabun', date1['font_size'])
        c.drawString(date1['x'], date1['y'], date1['text'])

        cb2 = left['checkbox_no_signature']
        self._draw_checkbox(c, cb2['x'], cb2['y'], 8.5)
        c.setFont('Sarabun', 7)
        c.drawString(cb2['x'] + 11.5, cb2['y'] + 1, cb2['label'])

        sig1 = left['signature_label']
        c.setFont('Sarabun', sig1['font_size'])
        c.drawString(sig1['x'], sig1['y'], sig1['text'])

        # 右框
        right = sig_boxes['right_box']
        c.rect(right['x'], right['y'], right['width'], right['height'])

        date2 = right['date_label']
        c.setFont('Sarabun', date2['font_size'])
        c.drawString(date2['x'], date2['y'], date2['text'])

        sig2 = right['signature_label']
        c.setFont('Sarabun', sig2['font_size'])
        c.drawString(sig2['x'], sig2['y'], sig2['text'])

    def _draw_checkbox(self, c: canvas.Canvas, x: float, y: float, size: float):
        """绘制复选框"""
        c.saveState()
        c.setLineWidth(0.5)
        c.setFillColor(HexColor('#FFFFFF'))
        c.rect(x, y, size, size, fill=1, stroke=1)
        c.restoreState()

    def _draw_boxes(self, c: canvas.Canvas, x: float, y: float, count: int,
                    box_size: float, box_gap: float):
        """绘制方格序列"""
        c.saveState()
        for i in range(count):
            box_x = x + i * (box_size + box_gap)
            c.setLineWidth(0.5)
            c.setFillColor(HexColor('#FFFFFF'))
            c.rect(box_x, y, box_size, box_size, fill=1, stroke=1)
        c.restoreState()

    def generate(self, data: Dict, output_path: str):
        """生成PDF"""
        c = canvas.Canvas(output_path, pagesize=A4)

        # 按顺序绘制所有元素
        self._draw_borders(c)
        self._draw_section_title(c)
        self._draw_form_code(c)
        self._draw_report_number_area(c)
        self._draw_main_separators(c)
        self._draw_report_type_section(c)
        self._draw_thick_separator(c, 'thick_separator_1')
        self._draw_section_1(c)
        self._draw_thick_separator(c, 'thick_separator_2')
        self._draw_section_2(c)
        self._draw_thick_separator(c, 'thick_separator_3')
        self._draw_section_3(c)
        self._draw_thick_separator(c, 'thick_separator_4')
        self._draw_section_4(c)

        c.save()
        return output_path

if __name__ == '__main__':
    generator = AMLO101FromConfig()
    output = 'D:\\Code\\ExchangeNew\\src\\test_output\\AMLO_101_from_config.pdf'
    generator.generate({}, output)
    print(f"Generated: {output}")
