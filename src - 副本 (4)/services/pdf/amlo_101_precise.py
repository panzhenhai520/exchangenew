# -*- coding: utf-8 -*-
"""
AMLO-1-01 精确版本生成器
基于分层布局配置文件 - amlo_101_precise_layout.json
"""

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
import os
import json
from typing import Dict

class AMLO101Precise:
    """基于精确分层配置的AMLO-1-01生成器"""

    def __init__(self):
        # 加载修正后的配置文件
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                   'amlo_101_corrected_layout.json')
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

    def _draw_layer1_borders(self, c: canvas.Canvas):
        """第一层：绘制三层边框"""
        borders = self.config['layer1_borders']

        # 外层边框
        outer = borders['outer']
        c.saveState()
        c.setLineWidth(outer['line_width'])
        c.rect(outer['x'], outer['y'], outer['width'], outer['height'])
        c.restoreState()

        # 中层边框（最粗）
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

    def _draw_layer2_separators(self, c: canvas.Canvas):
        """第二层：绘制主要区域分隔线 - 支持三线结构"""
        regions = self.config['layer2_regions']
        xl = regions['content_left']
        xr = regions['content_right']

        # 5条分隔线(有些是三线结构)
        for i in range(1, 6):
            sep_key = f'separator_{i}'
            if sep_key in regions:
                sep = regions[sep_key]
                c.saveState()

                # 检查是否为三线结构
                if sep.get('triple_line', False):
                    # 绘制三条线：顶部细线、中间粗线、底部细线
                    if 'line_top' in sep:
                        c.setLineWidth(sep['line_top']['line_width'])
                        c.line(xl, sep['line_top']['y'], xr, sep['line_top']['y'])
                    if 'line_middle' in sep:
                        c.setLineWidth(sep['line_middle']['line_width'])
                        c.line(xl, sep['line_middle']['y'], xr, sep['line_middle']['y'])
                    if 'line_bottom' in sep:
                        c.setLineWidth(sep['line_bottom']['line_width'])
                        c.line(xl, sep['line_bottom']['y'], xr, sep['line_bottom']['y'])
                else:
                    # 单线
                    c.setLineWidth(sep['line_width'])
                    c.line(xl, sep['y'], xr, sep['y'])

                c.restoreState()

    def _draw_region_a_header(self, c: canvas.Canvas):
        """绘制区域A：标题和报告编号 - 支持双层边框和勾选符号"""
        layout = self.config['region_a_header_layout']

        # 左侧灰色标题框 - 双层边框
        title_box = layout['title_box']
        c.saveState()
        c.setFillColor(HexColor(title_box.get('outer_box', title_box)['background_color']))

        # 外层边框
        outer = title_box.get('outer_box', title_box)
        c.setLineWidth(outer['border_width'])
        c.rect(outer['x'], outer['y'], outer['width'], outer['height'], fill=1, stroke=1)

        # 内层边框（如果存在）
        if 'inner_box' in title_box:
            inner = title_box['inner_box']
            c.setLineWidth(inner['border_width'])
            c.rect(inner['x'], inner['y'], inner['width'], inner['height'], fill=0, stroke=1)

        c.setFillColor(HexColor('#000000'))

        # 标题文字（支持bold）
        title_text = title_box['title_text']
        if title_text.get('font_bold', False):
            # 使用Sarabun-Bold（如果可用），否则通过重复绘制模拟加粗
            c.setFont(title_text['font'], title_text['font_size'])
            # 模拟加粗：绘制多次略微偏移
            for offset in [0, 0.3]:
                c.drawString(title_text['x'] + offset, title_text['y'], title_text['content'])
        else:
            c.setFont(title_text['font'], title_text['font_size'])
            c.drawString(title_text['x'], title_text['y'], title_text['content'])

        # 勾选符号（如果存在）
        if 'checkmark' in title_box:
            checkmark = title_box['checkmark']
            c.setFont('Sarabun', checkmark['font_size'])
            c.drawString(checkmark['x'], checkmark['y'], checkmark['symbol'])

        # 副标题
        subtitle = title_box['subtitle_text']
        c.setFont(subtitle['font'], subtitle['font_size'])
        c.drawString(subtitle['x'], subtitle['y'], subtitle['content'])
        c.restoreState()

        # 右上角表单编号
        form_code = layout['form_code']
        c.setFont(form_code['font'], form_code['font_size'])
        c.drawRightString(form_code['x'], form_code['y'], form_code['text'])

        # 报告编号行
        rn_line = layout['report_number_line']

        # เลขที่ 标签
        label = rn_line['label_lekhti']
        c.setFont('Sarabun', label['font_size'])
        c.drawString(label['x'], label['y'], label['text'])

        # สถาบันการเงิน (3个方框)
        inst = rn_line['institution_boxes']
        self._draw_small_boxes(c, inst['x_start'], inst['y'], inst['count'],
                              inst.get('box_width', inst.get('box_size', 11.34)),
                              inst.get('box_height', inst.get('box_size', 11.34)),
                              inst['box_gap'])
        c.setFont('Sarabun', inst['label']['font_size'])
        c.drawCentredString(inst['label']['x_center'], inst['label']['y'],
                           inst['label']['text'])

        # 分隔线1 - 连接竖线
        sep1 = rn_line['separator_1']
        c.setLineWidth(sep1['line_width'])
        if all(k in sep1 for k in ['x1', 'y1', 'x2', 'y2']):
            # 竖线
            c.line(sep1['x1'], sep1['y1'], sep1['x2'], sep1['y2'])
        else:
            # 横线（兼容旧格式）
            c.line(sep1['x1'], sep1['y'], sep1['x2'], sep1['y'])

        # สาขา (3个方框)
        branch = rn_line['branch_boxes']
        self._draw_small_boxes(c, branch['x_start'], branch['y'], branch['count'],
                              branch.get('box_width', branch.get('box_size', 11.34)),
                              branch.get('box_height', branch.get('box_size', 11.34)),
                              branch['box_gap'])
        c.setFont('Sarabun', branch['label']['font_size'])
        c.drawCentredString(branch['label']['x_center'], branch['label']['y'],
                           branch['label']['text'])

        # 分隔线2
        sep2 = rn_line['separator_2']
        c.setLineWidth(sep2['line_width'])
        if all(k in sep2 for k in ['x1', 'y1', 'x2', 'y2']):
            c.line(sep2['x1'], sep2['y1'], sep2['x2'], sep2['y2'])
        else:
            c.line(sep2['x1'], sep2['y'], sep2['x2'], sep2['y'])

        # ปี พ.ศ. (2个方框)
        year = rn_line['year_boxes']
        self._draw_small_boxes(c, year['x_start'], year['y'], year['count'],
                              year.get('box_width', year.get('box_size', 11.34)),
                              year.get('box_height', year.get('box_size', 11.34)),
                              year['box_gap'])
        c.setFont('Sarabun', year['label_line1']['font_size'])
        c.drawString(year['label_line1']['x'], year['label_line1']['y'],
                    year['label_line1']['text'])
        c.drawString(year['label_line2']['x'], year['label_line2']['y'],
                    year['label_line2']['text'])

        # 分隔线3
        sep3 = rn_line['separator_3']
        c.setLineWidth(sep3['line_width'])
        if all(k in sep3 for k in ['x1', 'y1', 'x2', 'y2']):
            c.line(sep3['x1'], sep3['y1'], sep3['x2'], sep3['y2'])
        else:
            c.line(sep3['x1'], sep3['y'], sep3['x2'], sep3['y'])

        # เลขลำดับรายงาน (长方框)
        serial = rn_line['serial_box']
        c.rect(serial['x'], serial['y'], serial['width'], serial['height'])
        c.setFont('Sarabun', serial['label']['font_size'])
        c.drawString(serial['label']['x'], serial['label']['y'], serial['label']['text'])

    def _draw_region_b_options(self, c: canvas.Canvas):
        """绘制区域B：选项行"""
        layout = self.config['region_b_options_layout']

        # รายงานฉบับหลัก
        cb1 = layout['checkbox_original']
        self._draw_checkbox(c, cb1['x'], cb1['y'], cb1['size'])
        c.setFont('Sarabun', cb1['label']['font_size'])
        c.drawString(cb1['label']['x'], cb1['label']['y'], cb1['label']['text'])

        # รายงานฉบับแก้ไข
        cb2 = layout['checkbox_revised']
        self._draw_checkbox(c, cb2['x'], cb2['y'], cb2['size'])
        c.setFont('Sarabun', cb2['label']['font_size'])
        c.drawString(cb2['label']['x'], cb2['label']['y'], cb2['label']['text'])

        # 修订次数下划线
        rev_line = layout['revision_line']
        c.setLineWidth(rev_line['line_width'])
        c.line(rev_line['x'], rev_line['y'], rev_line['x'] + rev_line['width'], rev_line['y'])

        # 日期标签和下划线
        date_label = layout['date_label']
        c.setFont('Sarabun', date_label['font_size'])
        c.drawString(date_label['x'], date_label['y'], date_label['text'])

        date_line = layout['date_line']
        c.setLineWidth(date_line['line_width'])
        c.line(date_line['x'], date_line['y'], date_line['x'] + date_line['width'], date_line['y'])

        # 竖线分隔
        v_sep = layout['vertical_separator']
        c.setLineWidth(v_sep['line_width'])
        c.line(v_sep['x'], v_sep['y_bottom'], v_sep['x'], v_sep['y_top'])

        # รวมเอกสาร
        total_label = layout['total_pages_label']
        c.setFont('Sarabun', total_label['font_size'])
        c.drawString(total_label['x'], total_label['y'], total_label['text'])

        total_line = layout['total_pages_line']
        c.setLineWidth(total_line['line_width'])
        c.line(total_line['x'], total_line['y'], total_line['x'] + total_line['width'], total_line['y'])

        pages_unit = layout['pages_unit']
        c.setFont('Sarabun', pages_unit['font_size'])
        c.drawString(pages_unit['x'], pages_unit['y'], pages_unit['text'])

    def _draw_region_c_section1(self, c: canvas.Canvas):
        """绘制区域C：ส่วนที่ ๑"""
        layout = self.config['region_c_section1_layout']

        # 标题框
        title_box = layout['title_box']
        c.saveState()
        c.setFillColor(HexColor(title_box['background_color']))
        c.setLineWidth(title_box['border_width'])
        c.rect(title_box['x'], title_box['y'], title_box['width'], title_box['height'],
               fill=1, stroke=1)
        c.setFillColor(HexColor('#000000'))
        c.setFont('Sarabun', title_box['text']['font_size'])
        c.drawString(title_box['text']['x'], title_box['text']['y'], title_box['text']['content'])
        c.restoreState()

        # ID方框组
        id_group = layout['id_box_group']

        # 灰色说明框
        exp_box = id_group['explanation_box']
        c.saveState()
        c.setFillColor(HexColor(exp_box['background_color']))
        # 向上延伸到区域顶部
        y_extends_to = exp_box['y_extends_to']
        height = y_extends_to - exp_box['y']
        c.rect(exp_box['x'], exp_box['y'], exp_box['width'], height, fill=1, stroke=0)
        c.restoreState()

        # 13个ID方框
        id_boxes = id_group['id_boxes']
        self._draw_id_boxes(c, id_boxes['x_start'], id_boxes['y'], id_boxes['count'],
                           id_boxes['box_size'], id_boxes['box_gap'])

        # 说明文字
        c.setFillColor(HexColor('#000000'))
        c.setFont('Sarabun', 6.5)
        for line in exp_box['text_lines']:
            c.drawString(exp_box['x'] + 5, line['y'], line['text'])

        # 字段
        self._draw_section1_fields(c, layout['fields'])

    def _draw_section1_fields(self, c: canvas.Canvas, fields: Dict):
        """绘制ส่วนที่ ๑的字段"""
        # 获取复选框默认大小
        checkbox_size = self.config.get('checkbox_style', {}).get('size_default', 8.5)

        # ๑.๑ ชื่อ-นามสกุล
        f11 = fields['field_1_1']
        c.setFont('Sarabun', f11['label']['font_size'])
        c.drawString(f11['label']['x'], f11['y'], f11['label']['text'])
        ul = f11['underline']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # 两个复选框
        cb_self = fields['checkbox_self']
        self._draw_checkbox(c, cb_self['x'], cb_self['y'], cb_self['size'])
        c.setFont('Sarabun', cb_self['label']['font_size'])
        c.drawString(cb_self['label']['x'], cb_self['y'], cb_self['label']['text'])

        cb_agent = fields['checkbox_agent']
        self._draw_checkbox(c, cb_agent['x'], cb_agent['y'], cb_agent['size'])
        c.setFont('Sarabun', cb_agent['label']['font_size'])
        c.drawString(cb_agent['label']['x'], cb_agent['y'], cb_agent['label']['text'])

        # ๑.๒ ที่อยู่
        f12 = fields['field_1_2']
        c.setFont('Sarabun', f12['label']['font_size'])
        c.drawString(f12['label']['x'], f12['y'], f12['label']['text'])
        ul = f12['underline']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # ๑.๒ 第二行
        f12_l2 = fields['field_1_2_line2']
        c.setFont('Sarabun', f12_l2['phone_label']['font_size'])
        c.drawString(f12_l2['phone_label']['x'], f12_l2['y'], f12_l2['phone_label']['text'])
        ul = f12_l2['phone_line']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        c.drawString(f12_l2['fax_label']['x'], f12_l2['y'], f12_l2['fax_label']['text'])
        ul = f12_l2['fax_line']
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # ๑.๓ อาชีพ สถานที่ทำงาน โทรศัพท์
        f13 = fields['field_1_3']
        c.setFont('Sarabun', f13['occupation_label']['font_size'])
        c.drawString(f13['occupation_label']['x'], f13['y'], f13['occupation_label']['text'])
        ul = f13['occupation_line']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        c.drawString(f13['workplace_label']['x'], f13['y'], f13['workplace_label']['text'])
        ul = f13['workplace_line']
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        c.drawString(f13['phone_label']['x'], f13['y'], f13['phone_label']['text'])
        ul = f13['phone_line']
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # ๑.๔ สถานที่สะดวกในการติดต่อ
        f14 = fields['field_1_4']
        c.setFont('Sarabun', f14['label']['font_size'])
        c.drawString(f14['label']['x'], f14['y'], f14['label']['text'])
        ul = f14['underline']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # ๑.๔ 第二行
        f14_l2 = fields['field_1_4_line2']
        c.setFont('Sarabun', f14_l2['phone_label']['font_size'])
        c.drawString(f14_l2['phone_label']['x'], f14_l2['y'], f14_l2['phone_label']['text'])
        ul = f14_l2['phone_line']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        c.drawString(f14_l2['fax_label']['x'], f14_l2['y'], f14_l2['fax_label']['text'])
        ul = f14_l2['fax_line']
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # ๑.๕ หลักฐานที่ใช้ในการทำธุรกรรม
        f15 = fields['field_1_5']
        c.setFont('Sarabun', f15['label']['font_size'])
        c.drawString(f15['label']['x'], f15['y'], f15['label']['text'])

        # 第一行复选框
        for cb_data in f15['checkboxes_line1']:
            self._draw_checkbox(c, cb_data['x'], cb_data['y'], checkbox_size)
            c.setFont('Sarabun', 8)
            c.drawString(cb_data['x'] + 11.5, cb_data['y'] + 1, cb_data['label'])

        # 第二行复选框
        for cb_data in f15['checkboxes_line2']:
            self._draw_checkbox(c, cb_data['x'], cb_data['y'], checkbox_size)
            c.setFont('Sarabun', 8)
            c.drawString(cb_data['x'] + 11.5, cb_data['y'] + 1, cb_data['label'])

        ul = f15['other_line']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # ๑.๕ 详细信息
        f15_det = fields['field_1_5_details']
        c.setFont('Sarabun', f15_det['number_label']['font_size'])
        c.drawString(f15_det['number_label']['x'], f15_det['y'], f15_det['number_label']['text'])
        ul = f15_det['number_line']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        c.drawString(f15_det['issued_by_label']['x'], f15_det['y'], f15_det['issued_by_label']['text'])
        ul = f15_det['issued_by_line']
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        c.drawString(f15_det['issued_date_label']['x'], f15_det['y'], f15_det['issued_date_label']['text'])
        ul = f15_det['issued_date_line']
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        c.drawString(f15_det['expiry_label']['x'], f15_det['y'], f15_det['expiry_label']['text'])
        ul = f15_det['expiry_line']
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

    def _draw_region_d_section2(self, c: canvas.Canvas):
        """绘制区域D：ส่วนที่ ๒"""
        layout = self.config['region_d_section2_layout']

        # 标题框
        title_box = layout['title_box']
        c.saveState()
        c.setFillColor(HexColor(title_box['background_color']))
        c.setLineWidth(title_box['border_width'])
        c.rect(title_box['x'], title_box['y'], title_box['width'], title_box['height'],
               fill=1, stroke=1)
        c.setFillColor(HexColor('#000000'))
        c.setFont('Sarabun', title_box['text']['font_size'])
        c.drawString(title_box['text']['x'], title_box['text']['y'], title_box['text']['content'])
        c.restoreState()

        # 右侧3个复选框
        checkbox_size = self.config.get('checkbox_style', {}).get('size_default', 8.5)
        cbs_right = layout['checkboxes_right']
        for key in ['checkbox_1', 'checkbox_2', 'checkbox_3']:
            cb = cbs_right[key]
            self._draw_checkbox(c, cbs_right['x'], cb['y'], checkbox_size)
            c.setFont('Sarabun', 8)
            c.drawString(cbs_right['x'] + 11.5, cb['y'] + 1, cb['label'])

        # ID方框组
        id_group = layout['id_box_group']

        # 灰色说明框
        exp_box = id_group['explanation_box']
        c.saveState()
        c.setFillColor(HexColor(exp_box['background_color']))
        y_extends_to = exp_box['y_extends_to']
        height = y_extends_to - exp_box['y']
        c.rect(exp_box['x'], exp_box['y'], exp_box['width'], height, fill=1, stroke=0)
        c.restoreState()

        # 13个ID方框
        id_boxes = id_group['id_boxes']
        self._draw_id_boxes(c, id_boxes['x_start'], id_boxes['y'], id_boxes['count'],
                           id_boxes['box_size'], id_boxes['box_gap'])

        # 说明文字（4行）
        c.setFillColor(HexColor('#000000'))
        c.setFont('Sarabun', 6.5)
        for line in exp_box['text_lines']:
            c.drawString(exp_box['x'] + 5, line['y'], line['text'])

        # 字段
        self._draw_section2_fields(c, layout['fields'])

    def _draw_section2_fields(self, c: canvas.Canvas, fields: Dict):
        """绘制ส่วนที่ ๒的字段"""
        # 获取复选框默认大小
        checkbox_size = self.config.get('checkbox_style', {}).get('size_default', 8.5)

        # ๒.๑ ชื่อ
        f21 = fields['field_2_1']
        c.setFont('Sarabun', f21['label']['font_size'])
        c.drawString(f21['label']['x'], f21['y'], f21['label']['text'])
        ul = f21['underline']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # ๒.๒ ที่อยู่/สถานที่ตั้ง
        f22 = fields['field_2_2']
        c.setFont('Sarabun', f22['label']['font_size'])
        c.drawString(f22['label']['x'], f22['y'], f22['label']['text'])
        ul = f22['underline']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # ๒.๒ 第二行（只有横线）
        f22_l2 = fields['field_2_2_line2']
        ul = f22_l2['underline']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # ๒.๒ 第三行（โทรศัพท์ โทรสาร）
        if 'field_2_2_line3' in fields:
            f22_l3 = fields['field_2_2_line3']
            c.setFont('Sarabun', f22_l3['phone_label']['font_size'])
            c.drawString(f22_l3['phone_label']['x'], f22_l3['y'], f22_l3['phone_label']['text'])
            ul = f22_l3['phone_line']
            c.setLineWidth(ul['line_width'])
            c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

            c.drawString(f22_l3['fax_label']['x'], f22_l3['y'], f22_l3['fax_label']['text'])
            ul = f22_l3['fax_line']
            c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # ๒.๓ อาชีพ สถานที่ทำงาน โทรศัพท์
        f23 = fields['field_2_3']
        c.setFont('Sarabun', f23['occupation_label']['font_size'])
        c.drawString(f23['occupation_label']['x'], f23['y'], f23['occupation_label']['text'])
        ul = f23['occupation_line']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        c.drawString(f23['workplace_label']['x'], f23['y'], f23['workplace_label']['text'])
        ul = f23['workplace_line']
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        c.drawString(f23['phone_label']['x'], f23['y'], f23['phone_label']['text'])
        ul = f23['phone_line']
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # ๒.๓ นิติบุคคล
        f23_corp = fields['field_2_3_corporate']
        c.setFont('Sarabun', f23_corp['label']['font_size'])
        c.drawString(f23_corp['label']['x'], f23_corp['y'], f23_corp['label']['text'])
        ul = f23_corp['underline']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # ๒.๔ สถานที่สะดวกในการติดต่อ
        f24 = fields['field_2_4']
        c.setFont('Sarabun', f24['label']['font_size'])
        c.drawString(f24['label']['x'], f24['y'], f24['label']['text'])
        ul = f24['underline']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # ๒.๔ 第二行
        f24_l2 = fields['field_2_4_line2']
        ul = f24_l2['underline']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        c.setFont('Sarabun', f24_l2['phone_label']['font_size'])
        c.drawString(f24_l2['phone_label']['x'], f24_l2['y'], f24_l2['phone_label']['text'])
        ul = f24_l2['phone_line']
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        c.drawString(f24_l2['fax_label']['x'], f24_l2['y'], f24_l2['fax_label']['text'])
        ul = f24_l2['fax_line']
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # ๒.๕ หลักฐานที่ใช้ในการทำธุรกรรม
        f25 = fields['field_2_5']
        c.setFont('Sarabun', f25['label']['font_size'])
        c.drawString(f25['label']['x'], f25['y'], f25['label']['text'])

        # 第一行复选框
        for cb_data in f25['checkboxes_line1']:
            self._draw_checkbox(c, cb_data['x'], cb_data['y'], checkbox_size)
            c.setFont('Sarabun', 8)
            c.drawString(cb_data['x'] + 11.5, cb_data['y'] + 1, cb_data['label'])

        # 第二行复选框
        for cb_data in f25['checkboxes_line2']:
            self._draw_checkbox(c, cb_data['x'], cb_data['y'], checkbox_size)
            c.setFont('Sarabun', 8)
            c.drawString(cb_data['x'] + 11.5, cb_data['y'] + 1, cb_data['label'])

        # อื่นๆ (โปรดระบุ) 横线
        if 'other_specify_line' in f25:
            ul = f25['other_specify_line']
            c.setLineWidth(ul['line_width'])
            c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # ๒.๕ 详细信息
        f25_det = fields['field_2_5_details']
        c.setFont('Sarabun', f25_det['number_label']['font_size'])
        c.drawString(f25_det['number_label']['x'], f25_det['y'], f25_det['number_label']['text'])
        ul = f25_det['number_line']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        c.drawString(f25_det['issued_by_label']['x'], f25_det['y'], f25_det['issued_by_label']['text'])
        ul = f25_det['issued_by_line']
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        c.drawString(f25_det['issued_date_label']['x'], f25_det['y'], f25_det['issued_date_label']['text'])
        ul = f25_det['issued_date_line']
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        c.drawString(f25_det['expiry_label']['x'], f25_det['y'], f25_det['expiry_label']['text'])
        ul = f25_det['expiry_line']
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

    def _draw_region_e_section3(self, c: canvas.Canvas):
        """绘制区域E：ส่วนที่ ๓"""
        layout = self.config['region_e_section3_layout']

        # 标题框
        title_box = layout['title_box']
        c.saveState()
        c.setFillColor(HexColor(title_box['background_color']))
        c.setLineWidth(title_box['border_width'])
        c.rect(title_box['x'], title_box['y'], title_box['width'], title_box['height'],
               fill=1, stroke=1)
        c.setFillColor(HexColor('#000000'))
        c.setFont('Sarabun', title_box['text']['font_size'])
        c.drawString(title_box['text']['x'], title_box['text']['y'], title_box['text']['content'])
        c.restoreState()

        # 交易日期
        trans_date = layout['transaction_date']
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

        c.drawString(trans_date['year_label']['x'], trans_date['year_label']['y'],
                    trans_date['year_label']['text'])
        ul = trans_date['year_line']
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # ๓.๑ 标签
        f31 = layout['field_3_1_label']
        c.setFont('Sarabun', f31['font_size'])
        c.drawString(f31['x'], f31['y'], f31['text'])

        # 交易框
        self._draw_transaction_boxes(c, layout['transaction_boxes'])

        # ๓.๒
        f32 = layout['field_3_2']
        c.setFont('Sarabun', f32['label']['font_size'])
        c.drawString(f32['label']['x'], f32['y'], f32['label']['text'])
        ul = f32['underline']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # ๓.๓
        f33 = layout['field_3_3']
        c.setFont('Sarabun', f33['label']['font_size'])
        c.drawString(f33['label']['x'], f33['y'], f33['label']['text'])
        ul = f33['underline']
        c.setLineWidth(ul['line_width'])
        c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

    def _draw_transaction_boxes(self, c: canvas.Canvas, boxes: Dict):
        """绘制交易框"""
        # 获取复选框默认大小
        checkbox_size = self.config.get('checkbox_style', {}).get('size_default', 8.5)

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
        self._draw_checkbox(c, cb['x'], cb['y'], checkbox_size)
        c.setFont('Sarabun', cb.get('font_size', 8))
        c.drawString(cb['x'] + 11.5, cb['y'] + 1, cb['label'])

        # จำนวน (บาท) - 先绘制灰色背景
        amt_label = content['amount_column_label']
        # 绘制灰色背景区域
        v_sep = left['vertical_separator']
        solid_line = content.get('solid_line_1', content['dashed_lines'])
        start_y = solid_line.get('y', solid_line.get('line_1_y'))

        # 如果指定了gray_bg_height，使用指定高度；否则延伸到表格顶部
        if 'gray_bg_height' in amt_label:
            bg_height = amt_label['gray_bg_height']
        else:
            bg_height = boxes['y_top'] - start_y

        c.saveState()
        c.setFillColor(HexColor('#E8E8E8'))
        # 绘制灰色背景，并添加边框（与表格边框粗细一致）
        c.setLineWidth(left['border_width'])
        c.rect(v_sep['x'], start_y, left['x'] + left['width'] - v_sep['x'],
               bg_height, fill=1, stroke=1)
        c.restoreState()
        # 绘制文字 - 使用drawCentredString居中
        c.setFont('Sarabun', amt_label['font_size'])
        c.drawCentredString(amt_label['x'], amt_label['y'], amt_label['text'])

        # 账号框
        acc_label = content['account_number_label']
        c.setFont('Sarabun', acc_label['font_size'])
        c.drawString(acc_label['x'], acc_label['y'], acc_label['text'])
        acc_boxes = content['account_number_boxes']
        self._draw_account_boxes(c, acc_boxes['x'], acc_boxes['y'], acc_boxes['count'],
                                acc_boxes.get('box_width', acc_boxes.get('box_size', 8.50)),
                                acc_boxes.get('box_height', acc_boxes.get('box_size', 8.50)),
                                acc_boxes['box_gap'])

        # 相关账户
        rel_label = content['related_account_label']
        c.setFont('Sarabun', rel_label['font_size'])
        c.drawString(rel_label['x'], rel_label['y'], rel_label['text'])
        rel_boxes = content['related_account_boxes']
        self._draw_account_boxes(c, rel_boxes['x'], rel_boxes['y'], rel_boxes['count'],
                                rel_boxes.get('box_width', rel_boxes.get('box_size', 8.50)),
                                rel_boxes.get('box_height', rel_boxes.get('box_size', 8.50)),
                                rel_boxes['box_gap'])

        # (หากมี)
        if_any = content['if_any_label']
        c.setFont('Sarabun', if_any['font_size'])
        c.drawString(if_any['x'], if_any['y'], if_any['text'])

        # 其他复选框
        for key in ['checkbox_buy_instruments', 'checkbox_check', 'checkbox_draft',
                   'checkbox_other_instruments', 'checkbox_buy_foreign_currency',
                   'checkbox_other_transaction']:
            cb = content[key]
            self._draw_checkbox(c, cb['x'], cb['y'], checkbox_size)
            c.setFont('Sarabun', cb.get('font_size', 8))
            c.drawString(cb['x'] + 11.5, cb['y'] + 1, cb['label'])

        # 其他下划线
        for key in ['other_instruments_line', 'other_transaction_line_1', 'other_transaction_line_2']:
            if key in content:
                ul = content[key]
                c.setLineWidth(ul['line_width'])
                c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # 第一根实线（如果存在）
        if 'solid_line_1' in content:
            solid = content['solid_line_1']
            c.saveState()
            c.setLineWidth(solid.get('line_width', 0.5))
            c.line(solid['x_start'], solid['y'], solid['x_end'], solid['y'])
            c.restoreState()

        # 8条虚线
        dashed = content['dashed_lines']
        # 设置线宽（如果指定）
        if 'line_width' in dashed:
            c.setLineWidth(dashed['line_width'])
        # Only set dash pattern if not solid lines (dash_pattern != [0, 0])
        if dashed['dash_pattern'] != [0, 0]:
            c.setDash(dashed['dash_pattern'][0], dashed['dash_pattern'][1])
        # 检查是否有单独的line_y定义，如果有则使用，否则使用first_line_y和y_spacing
        if 'line_1_y' in dashed:
            # 使用单独定义的每条线的y坐标
            for i in range(1, dashed['count'] + 1):
                line_key = f'line_{i}_y'
                if line_key in dashed:
                    y = dashed[line_key]
                    c.line(dashed['x_start'], y, dashed['x_end'], y)
        else:
            # 使用first_line_y和y_spacing
            y = dashed['first_line_y']
            for i in range(dashed['count']):
                c.line(dashed['x_start'], y - i * dashed['y_spacing'],
                      dashed['x_end'], y - i * dashed['y_spacing'])
        c.setDash()  # 恢复实线

        # รวมเงิน行（如果存在total_row）
        if 'total_row' in content:
            total_row = content['total_row']
            # 绘制上方横线（如果存在）
            if 'horizontal_line_above' in total_row:
                hl = total_row['horizontal_line_above']
                c.setLineWidth(hl['line_width'])
                c.line(hl['x_start'], hl['y'], hl['x_end'], hl['y'])
            # 绘制下方横线
            hl = total_row['horizontal_line_below']
            c.setLineWidth(hl['line_width'])
            c.line(hl['x_start'], hl['y'], hl['x_end'], hl['y'])
            # 绘制รวมเงิน文字（支持加粗）
            total = total_row['total_label']
            c.setFont('Sarabun', total['font_size'])
            if total.get('font_bold', False):
                # 模拟加粗：绘制多次略微偏移
                for offset in [0, 0.3]:
                    c.drawString(total['x'] + offset, total['y'], total['text'])
            else:
                c.drawString(total['x'], total['y'], total['text'])
        elif 'total_label' in content:
            # 兼容旧格式
            total = content['total_label']
            c.setFont('Sarabun', total['font_size'])
            c.drawString(total['x'], total['y'], total['text'])

        # 灰色文字框
        total_box = content['total_in_words_box']
        c.saveState()
        c.setFillColor(HexColor(total_box['background_color']))
        # 如果配置中指定了边框宽度，则绘制边框
        if 'border_width' in total_box:
            c.setLineWidth(total_box['border_width'])
            c.rect(total_box['x'], total_box['y'], total_box['width'], total_box['height'],
                   fill=1, stroke=1)
        else:
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
        self._draw_checkbox(c, cb['x'], cb['y'], checkbox_size)
        c.setFont('Sarabun', cb.get('font_size', 8))
        c.drawString(cb['x'] + 11.5, cb['y'] + 1, cb['label'])

        # จำนวน (บาท) - 先绘制灰色背景
        amt_label = content['amount_column_label']
        # 绘制灰色背景区域
        v_sep_right = right['vertical_separator']
        solid_line_right = content.get('solid_line_1', content['dashed_lines'])
        start_y_right = solid_line_right.get('y', solid_line_right.get('line_1_y'))

        # 如果指定了gray_bg_height，使用指定高度；否则延伸到表格顶部
        if 'gray_bg_height' in amt_label:
            bg_height_right = amt_label['gray_bg_height']
        else:
            bg_height_right = boxes['y_top'] - start_y_right

        c.saveState()
        c.setFillColor(HexColor('#E8E8E8'))
        # 绘制灰色背景，并添加边框（与表格边框粗细一致）
        c.setLineWidth(right['border_width'])
        c.rect(v_sep_right['x'], start_y_right, right['x'] + right['width'] - v_sep_right['x'],
               bg_height_right, fill=1, stroke=1)
        c.restoreState()
        # 绘制文字 - 使用drawCentredString居中
        c.setFont('Sarabun', amt_label['font_size'])
        c.drawCentredString(amt_label['x'], amt_label['y'], amt_label['text'])

        # 账号框
        acc_label = content['account_number_label']
        c.setFont('Sarabun', acc_label['font_size'])
        c.drawString(acc_label['x'], acc_label['y'], acc_label['text'])
        acc_boxes = content['account_number_boxes']
        self._draw_account_boxes(c, acc_boxes['x'], acc_boxes['y'], acc_boxes['count'],
                                acc_boxes.get('box_width', acc_boxes.get('box_size', 8.50)),
                                acc_boxes.get('box_height', acc_boxes.get('box_size', 8.50)),
                                acc_boxes['box_gap'])

        # 相关账户
        rel_label = content['related_account_label']
        c.setFont('Sarabun', rel_label['font_size'])
        c.drawString(rel_label['x'], rel_label['y'], rel_label['text'])
        rel_boxes = content['related_account_boxes']
        self._draw_account_boxes(c, rel_boxes['x'], rel_boxes['y'], rel_boxes['count'],
                                rel_boxes.get('box_width', rel_boxes.get('box_size', 8.50)),
                                rel_boxes.get('box_height', rel_boxes.get('box_size', 8.50)),
                                rel_boxes['box_gap'])

        # (หากมี)
        if_any = content['if_any_label']
        c.setFont('Sarabun', if_any['font_size'])
        c.drawString(if_any['x'], if_any['y'], if_any['text'])

        # 其他复选框
        for key in ['checkbox_sell_instruments', 'checkbox_check', 'checkbox_draft',
                   'checkbox_other_instruments', 'checkbox_sell_foreign_currency',
                   'checkbox_other_transaction']:
            cb = content[key]
            self._draw_checkbox(c, cb['x'], cb['y'], checkbox_size)
            c.setFont('Sarabun', cb.get('font_size', 8))
            c.drawString(cb['x'] + 11.5, cb['y'] + 1, cb['label'])

        # 其他下划线
        for key in ['other_instruments_line', 'other_transaction_line_1', 'other_transaction_line_2']:
            if key in content:
                ul = content[key]
                c.setLineWidth(ul['line_width'])
                c.line(ul['x'], ul['y'], ul['x'] + ul['width'], ul['y'])

        # 第一根实线（如果存在）
        if 'solid_line_1' in content:
            solid = content['solid_line_1']
            c.saveState()
            c.setLineWidth(solid.get('line_width', 0.5))
            c.line(solid['x_start'], solid['y'], solid['x_end'], solid['y'])
            c.restoreState()

        # 8条虚线
        dashed = content['dashed_lines']
        # 设置线宽（如果指定）
        if 'line_width' in dashed:
            c.setLineWidth(dashed['line_width'])
        # Only set dash pattern if not solid lines (dash_pattern != [0, 0])
        if dashed['dash_pattern'] != [0, 0]:
            c.setDash(dashed['dash_pattern'][0], dashed['dash_pattern'][1])
        # 检查是否有单独的line_y定义，如果有则使用，否则使用first_line_y和y_spacing
        if 'line_1_y' in dashed:
            # 使用单独定义的每条线的y坐标
            for i in range(1, dashed['count'] + 1):
                line_key = f'line_{i}_y'
                if line_key in dashed:
                    y = dashed[line_key]
                    c.line(dashed['x_start'], y, dashed['x_end'], y)
        else:
            # 使用first_line_y和y_spacing
            y = dashed['first_line_y']
            for i in range(dashed['count']):
                c.line(dashed['x_start'], y - i * dashed['y_spacing'],
                      dashed['x_end'], y - i * dashed['y_spacing'])
        c.setDash()

        # รวมเงิน行（如果存在total_row）
        if 'total_row' in content:
            total_row = content['total_row']
            # 绘制上方横线（如果存在）
            if 'horizontal_line_above' in total_row:
                hl = total_row['horizontal_line_above']
                c.setLineWidth(hl['line_width'])
                c.line(hl['x_start'], hl['y'], hl['x_end'], hl['y'])
            # 绘制下方横线
            hl = total_row['horizontal_line_below']
            c.setLineWidth(hl['line_width'])
            c.line(hl['x_start'], hl['y'], hl['x_end'], hl['y'])
            # 绘制รวมเงิน文字（支持加粗）
            total = total_row['total_label']
            c.setFont('Sarabun', total['font_size'])
            if total.get('font_bold', False):
                # 模拟加粗：绘制多次略微偏移
                for offset in [0, 0.3]:
                    c.drawString(total['x'] + offset, total['y'], total['text'])
            else:
                c.drawString(total['x'], total['y'], total['text'])
        elif 'total_label' in content:
            # 兼容旧格式
            total = content['total_label']
            c.setFont('Sarabun', total['font_size'])
            c.drawString(total['x'], total['y'], total['text'])

        # 灰色文字框
        total_box = content['total_in_words_box']
        c.saveState()
        c.setFillColor(HexColor(total_box['background_color']))
        # 如果配置中指定了边框宽度，则绘制边框
        if 'border_width' in total_box:
            c.setLineWidth(total_box['border_width'])
            c.rect(total_box['x'], total_box['y'], total_box['width'], total_box['height'],
                   fill=1, stroke=1)
        else:
            c.rect(total_box['x'], total_box['y'], total_box['width'], total_box['height'],
                   fill=1, stroke=0)
        c.setFillColor(HexColor('#000000'))
        c.setFont('Sarabun', total_box['text']['font_size'])
        c.drawString(total_box['text']['x'], total_box['text']['y'],
                    total_box['text']['content'])
        c.restoreState()

    def _draw_region_f_section4(self, c: canvas.Canvas):
        """绘制区域F：ส่วนที่ ๔ - 使用双竖线分隔"""
        layout = self.config['region_f_section4_layout']

        # 标题框
        title_box = layout['title_box']
        c.saveState()
        c.setFillColor(HexColor(title_box['background_color']))
        c.setLineWidth(title_box['border_width'])
        c.rect(title_box['x'], title_box['y'], title_box['width'], title_box['height'],
               fill=1, stroke=1)
        c.setFillColor(HexColor('#000000'))
        c.setFont('Sarabun', title_box['text']['font_size'])
        c.drawString(title_box['text']['x'], title_box['text']['y'], title_box['text']['content'])
        c.restoreState()

        # 签名区域 - 双竖线结构
        sig_area = layout['signature_area']

        # 绘制左竖线
        v_left = sig_area['vertical_line_left']
        c.setLineWidth(v_left['line_width'])
        c.line(v_left['x'], v_left['y1'], v_left['x'], v_left['y2'])

        # 绘制右竖线
        v_right = sig_area['vertical_line_right']
        c.setLineWidth(v_right['line_width'])
        c.line(v_right['x'], v_right['y1'], v_right['x'], v_right['y2'])

        # 左侧区域内容
        left = sig_area['left_area']

        cb1 = left['checkbox_institution_records']
        self._draw_checkbox(c, cb1['x'], cb1['y'], cb1['size'])
        c.setFont('Sarabun', cb1.get('font_size', 7))
        c.drawString(cb1['x'] + 11.5, cb1['y'] + 1, cb1['label'])

        date1 = left['date_label_1']
        c.setFont('Sarabun', date1['font_size'])
        c.drawString(date1['x'], date1['y'], date1['text'])

        cb2 = left['checkbox_no_signature']
        self._draw_checkbox(c, cb2['x'], cb2['y'], cb2['size'])
        c.setFont('Sarabun', cb2.get('font_size', 7))
        c.drawString(cb2['x'] + 11.5, cb2['y'] + 1, cb2['label'])

        sig1 = left['signature_label']
        c.setFont('Sarabun', sig1['font_size'])
        c.drawString(sig1['x'], sig1['y'], sig1['text'])

        # 右侧区域内容
        right = sig_area['right_area']

        date2 = right['date_label']
        c.setFont('Sarabun', date2['font_size'])
        # 支持靠右对齐
        if date2.get('alignment') == 'right':
            c.drawRightString(date2['x'], date2['y'], date2['text'])
        else:
            c.drawString(date2['x'], date2['y'], date2['text'])

        sig2 = right['signature_label']
        c.setFont('Sarabun', sig2['font_size'])
        c.drawString(sig2['x'], sig2['y'], sig2['text'])

    def _draw_checkbox(self, c: canvas.Canvas, x: float, y: float, size: float):
        """绘制复选框"""
        c.saveState()
        # 使用配置文件中的边框宽度
        border_width = self.config.get('checkbox_style', {}).get('border_width', 0.5)
        c.setLineWidth(border_width)
        c.setFillColor(HexColor('#FFFFFF'))
        c.rect(x, y, size, size, fill=1, stroke=1)
        c.restoreState()

    def _draw_small_boxes(self, c: canvas.Canvas, x: float, y: float, count: int,
                         box_width: float, box_height: float, box_gap: float):
        """绘制小方格序列（报告编号用）- 支持不同宽高"""
        c.saveState()
        for i in range(count):
            box_x = x + i * (box_width + box_gap)
            c.setLineWidth(0.5)
            c.setFillColor(HexColor('#FFFFFF'))
            c.rect(box_x, y, box_width, box_height, fill=1, stroke=1)
        c.restoreState()

    def _draw_id_boxes(self, c: canvas.Canvas, x: float, y: float, count: int,
                      box_size: float, box_gap: float):
        """绘制ID方格序列（13个）"""
        c.saveState()
        for i in range(count):
            box_x = x + i * (box_size + box_gap)
            c.setLineWidth(0.5)
            c.setFillColor(HexColor('#FFFFFF'))
            c.rect(box_x, y, box_size, box_size, fill=1, stroke=1)
        c.restoreState()

    def _draw_account_boxes(self, c: canvas.Canvas, x: float, y: float, count: int,
                           box_width: float, box_height: float, box_gap: float):
        """绘制账号方格序列（10个）- 支持不同宽高（长方形）"""
        c.saveState()
        for i in range(count):
            box_x = x + i * (box_width + box_gap)
            c.setLineWidth(0.5)
            c.setFillColor(HexColor('#FFFFFF'))
            c.rect(box_x, y, box_width, box_height, fill=1, stroke=1)
        c.restoreState()

    def generate(self, data: Dict, output_path: str):
        """生成PDF"""
        c = canvas.Canvas(output_path, pagesize=A4)

        # 按分层顺序绘制
        print("[1/9] Drawing layer 1: Borders...")
        self._draw_layer1_borders(c)

        print("[2/9] Drawing layer 2: Separators...")
        self._draw_layer2_separators(c)

        print("[3/9] Drawing Region A: Header...")
        self._draw_region_a_header(c)

        print("[4/9] Drawing Region B: Options...")
        self._draw_region_b_options(c)

        print("[5/9] Drawing Region C: Section 1...")
        self._draw_region_c_section1(c)

        print("[6/9] Drawing Region D: Section 2...")
        self._draw_region_d_section2(c)

        print("[7/9] Drawing Region E: Section 3...")
        self._draw_region_e_section3(c)

        print("[8/9] Drawing Region F: Section 4...")
        self._draw_region_f_section4(c)

        print("[9/9] Saving PDF...")
        c.save()
        return output_path

if __name__ == '__main__':
    generator = AMLO101Precise()
    output = 'D:\\Code\\ExchangeNew\\src\\test_output\\AMLO_101_section3_v32_test.pdf'
    generator.generate({}, output)
    print(f"\nGenerated: {output}")
