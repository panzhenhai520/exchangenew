# -*- coding: utf-8 -*-
"""
AMLO PDF表单填充服务
使用pdfrw和ReportLab在现有PDF模板上精确填充文本

支持:
- AMLO-1-01 (CTR - Cash Transaction Report)
- AMLO-1-02 (ATR - Asset Transaction Report)
- AMLO-1-03 (STR - Suspicious Transaction Report)
"""

import os
from datetime import datetime
from pdfrw import PdfReader, PdfWriter, PageMerge
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO

try:
    from .amlo_field_mappings import REPORT_CONFIGS
except ImportError:
    # 直接运行时的导入方式
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from amlo_field_mappings import REPORT_CONFIGS


class AMLOFormFiller:
    """AMLO表单自动填充器"""

    def __init__(self):
        """初始化填充器"""
        self._register_fonts()

    def _register_fonts(self):
        """注册泰语字体"""
        try:
            # 尝试注册Sarabun字体
            font_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'fonts')
            sarabun_path = os.path.join(font_dir, 'Sarabun-Regular.ttf')

            if os.path.exists(sarabun_path):
                pdfmetrics.registerFont(TTFont('Sarabun', sarabun_path))
                print("[AMLOFormFiller] Thai font registered successfully")
                self.thai_font = 'Sarabun'
            else:
                print(f"[AMLOFormFiller] Thai font not found at {sarabun_path}, using Helvetica")
                self.thai_font = 'Helvetica'
        except Exception as e:
            print(f"[AMLOFormFiller] Font registration failed: {e}")
            self.thai_font = 'Helvetica'

    def fill_form(self, report_type, data, output_path):
        """
        填充AMLO表单

        Args:
            report_type (str): 报告类型 ('AMLO-1-01', 'AMLO-1-02', 'AMLO-1-03')
            data (dict): 业务数据字典
            output_path (str): 输出PDF文件路径

        Returns:
            str: 生成的PDF文件路径

        Example:
            >>> filler = AMLOFormFiller()
            >>> data = {
            ...     'customer_id': '1234567890123',
            ...     'customer_name': 'นายสมชาย ใจดี',
            ...     'transaction_date': datetime(2025, 10, 18),
            ...     'foreign_amount': 75000.00,
            ...     'transaction_type': 'buy'
            ... }
            >>> filler.fill_form('AMLO-1-01', data, 'output.pdf')
        """
        # 获取报告配置
        if report_type not in REPORT_CONFIGS:
            raise ValueError(f"Unsupported report type: {report_type}")

        config = REPORT_CONFIGS[report_type]
        template_path = config['template']
        field_configs = config['fields']
        db_mapping = config['db_mapping']

        # 检查模板文件
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found: {template_path}")

        # 从业务数据提取PDF字段值
        pdf_field_values = self._extract_field_values(data, db_mapping, field_configs)

        # 创建覆盖层PDF
        overlay_pdf = self._create_overlay_pdf(field_configs, pdf_field_values)

        # 合并模板和覆盖层
        self._merge_pdfs(template_path, overlay_pdf, output_path)

        print(f"[AMLOFormFiller] PDF generated: {output_path}")
        return output_path

    def _extract_field_values(self, data, db_mapping, field_configs):
        """从业务数据提取PDF字段值"""
        pdf_values = {}

        # 记录transaction_type以便调试
        print(f"[_extract_field_values] 输入data中的transaction_type='{data.get('transaction_type')}'")

        for pdf_field, source in db_mapping.items():
            try:
                # 如果source是函数，调用函数
                if callable(source):
                    value = source(data)
                # 如果source是字符串路径，从data中提取
                elif isinstance(source, str):
                    value = self._get_nested_value(data, source)
                else:
                    value = source

                # 应用字段格式化器
                if pdf_field in field_configs:
                    formatter = field_configs[pdf_field].get('formatter')
                    if formatter and value is not None:
                        value = formatter(value)

                # 应用默认值
                if value is None or value == '':
                    default = field_configs.get(pdf_field, {}).get('default')
                    if default:
                        value = default

                pdf_values[pdf_field] = value

                # 记录关键字段的值
                if 'amount' in pdf_field or 'type' in pdf_field:
                    print(f"[_extract_field_values] {pdf_field}={value}")

            except Exception as e:
                print(f"[AMLOFormFiller] Error extracting {pdf_field}: {e}")
                pdf_values[pdf_field] = ''

        return pdf_values

    def _get_nested_value(self, data, path):
        """从嵌套字典获取值 (支持点号分隔路径)"""
        keys = path.split('.')
        value = data

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None

            if value is None:
                return None

        return value

    def _create_overlay_pdf(self, field_configs, field_values):
        """创建覆盖层PDF（包含填充的文本）"""
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)

        # 遍历所有字段并绘制
        for field_name, field_config in field_configs.items():
            value = field_values.get(field_name)

            if value is None or value == '':
                continue

            field_type = field_config.get('type')

            try:
                if field_type == 'text':
                    self._draw_text_field(c, field_config, value)

                elif field_type == 'multi_char_boxes':
                    self._draw_multi_char_boxes(c, field_config, value)

                elif field_type == 'checkbox':
                    if value:  # 只有True时才画勾
                        self._draw_checkbox(c, field_config)

            except Exception as e:
                print(f"[AMLOFormFiller] Error drawing {field_name}: {e}")

        c.save()
        buffer.seek(0)
        return buffer

    def _draw_text_field(self, c, config, text):
        """绘制文本字段"""
        x = config['x']
        y = config['y']
        width = config.get('width', 100)
        font_size = config.get('font_size', 10)
        align = config.get('align', 'left')

        # 设置字体
        c.setFont(self.thai_font, font_size)

        # 根据对齐方式调整X坐标
        if align == 'center':
            text_width = c.stringWidth(str(text), self.thai_font, font_size)
            x = x + (width - text_width) / 2
        elif align == 'right':
            text_width = c.stringWidth(str(text), self.thai_font, font_size)
            x = x + width - text_width

        c.drawString(x, y, str(text))

    def _draw_multi_char_boxes(self, c, config, text):
        """绘制多字符方框字段（如身份证号）"""
        boxes = config['boxes']
        font_size = config.get('font_size', 11)
        align = config.get('align', 'center')

        text_str = str(text).replace('-', '').replace(' ', '')

        for i, box in enumerate(boxes):
            if i >= len(text_str):
                break

            char = text_str[i]
            x = box['x']
            y = box['y']
            width = box['width']
            height = box['height']

            c.setFont('Helvetica', font_size)

            # 居中绘制字符
            if align == 'center':
                char_width = c.stringWidth(char, 'Helvetica', font_size)
                x = x + (width - char_width) / 2

            c.drawString(x, y + 3, char)  # +3是垂直居中调整

    def _draw_checkbox(self, c, config):
        """绘制复选框勾选标记"""
        x = config['x']
        y = config['y']
        size = config.get('size', 6.0)

        # 绘制勾选标记
        c.setFont('Helvetica', 10)
        c.drawString(x + 0.5, y + 0.5, '✓')

    def _merge_pdfs(self, template_path, overlay_buffer, output_path):
        """合并模板PDF和覆盖层PDF"""
        # 读取模板PDF
        template = PdfReader(template_path)

        # 读取覆盖层PDF
        overlay = PdfReader(overlay_buffer)

        # 合并第一页（大多数AMLO报告只有一页）
        merger = PageMerge(template.pages[0])
        merger.add(overlay.pages[0]).render()

        # 保存
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        PdfWriter(output_path, trailer=template).write()


# ==================== 便捷函数 ====================

def generate_amlo_pdf(report_type, data, output_path):
    """
    便捷函数：生成AMLO PDF报告

    Args:
        report_type: 'AMLO-1-01', 'AMLO-1-02', 'AMLO-1-03'
        data: 业务数据字典
        output_path: 输出文件路径

    Returns:
        生成的PDF文件路径
    """
    filler = AMLOFormFiller()
    return filler.fill_form(report_type, data, output_path)


def adapt_route_data_to_pdf_data(route_data):
    """
    适配器函数：将app_amlo.py路由的数据结构转换为PDF填充器所需格式

    Args:
        route_data (dict): 从app_amlo.py路由传入的数据字典，包含:
            - report_number: 报告编号
            - maker_name: 填报人姓名
            - maker_id: 填报人身份证号
            - maker_address: 地址
            - transaction_date: 交易日期字符串 (dd/mm/yyyy格式)
            - amount_thb: 泰铢金额
            - currency_code: 货币代码
            - transaction_type: 交易类型
            等...

    Returns:
        dict: 转换后的数据字典，匹配amlo_field_mappings.py中的DB_TO_PDF_MAPPING
    """
    from datetime import datetime

    form_data = route_data.get('form_data') or {}

    def form_value(key, default=''):
        value = form_data.get(key)
        if value in (None, ''):
            return default
        return value

    def combine_name(prefix, fallback=''):
        title = form_value(f'{prefix}_title', '')
        first = form_value(f'{prefix}_firstname', '')
        last = form_value(f'{prefix}_lastname', '')
        company = form_value(f'{prefix}_company_name', '')
        full = form_value(f'{prefix}_full_name', '')
        parts = [p for p in [title, first, last] if p]
        if company:
            parts.append(company)
        candidate = full or ' '.join(parts).strip()
        return candidate or fallback

    def combine_address(prefix):
        parts = []
        for suffix in ['number', 'village', 'lane', 'road', 'subdistrict', 'district', 'province', 'postalcode']:
            val = form_value(f'{prefix}_{suffix}', '')
            if val:
                parts.append(str(val))
        return ' '.join(parts).strip()

    def parse_bool(value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in ('1', 'true', 'yes', 'y', 'on')
        if isinstance(value, (int, float)):
            return value != 0
        return False

    # 解析日期字符串
    transaction_date_str = route_data.get('transaction_date', '')
    try:
        if transaction_date_str:
            # 输入格式: dd/mm/yyyy
            transaction_date = datetime.strptime(transaction_date_str, '%d/%m/%Y')
        else:
            transaction_date = datetime.now()
    except ValueError:
        transaction_date = datetime.now()

    # 转换交易类型 (exchange -> buy/sell)
    transaction_type = route_data.get('transaction_type') or 'buy'
    if transaction_type not in ('buy', 'sell'):
        transaction_type = 'buy'

    beneficiary_name = route_data.get('beneficiary_name') or combine_name('joint_party', '本人')
    maker_name = route_data.get('maker_name') or combine_name('maker')
    maker_address = route_data.get('maker_address') or combine_address('maker_address')
    maker_phone = route_data.get('maker_phone') or form_value('maker_phone', '')
    maker_occupation = route_data.get('maker_occupation') or form_value('maker_occupation_type', '')
    if not maker_occupation:
        maker_occupation = form_value('maker_occupation_business_type', '')

    customer_id = route_data.get('maker_id') or form_value('maker_id_number', '')
    if not customer_id:
        customer_id = route_data.get('customer_id', '')

    is_on_behalf = route_data.get('maker_type') == 'agent'
    joint_party_exists = parse_bool(form_value('joint_party_exists', False))
    joint_party_has_name = any(form_value(k, '') for k in ['joint_party_firstname', 'joint_party_lastname', 'joint_party_company_name'])
    if joint_party_exists or joint_party_has_name:
        is_on_behalf = True

    foreign_amount = route_data.get('foreign_amount')
    if foreign_amount is None or foreign_amount == '':
        foreign_amount = route_data.get('amount_thb', 0)

    transaction_purpose = route_data.get('transaction_purpose') or form_value('transaction_purpose', '') or form_value('exchange_other_transaction', '')

    institution_code = route_data.get('institution_code', '001')
    branch_code = route_data.get('branch_code', '001')

    # 构建适配后的数据
    adapted_data = {
        # 客户信息
        'customer_id': customer_id,
        'customer_name': maker_name,
        'customer_address': maker_address or route_data.get('customer_address', ''),
        'customer_phone': maker_phone,
        'customer_occupation': maker_occupation,

        # 交易信息
        'transaction_date': transaction_date,
        'transaction_type': transaction_type,
        'foreign_amount': float(foreign_amount or 0),
        'transaction_purpose': transaction_purpose,
        'beneficiary_name': beneficiary_name,

        # 预约信息
        'reservation_no': route_data.get('report_number', ''),
        'is_original': not route_data.get('is_amendment', False),
        'is_on_behalf': is_on_behalf,

        # 分支信息
        'branch': {
            'institution_code': str(institution_code).zfill(3),
            'branch_code': str(branch_code).zfill(3)
        }
    }

    print(f"[adapt_route_data_to_pdf_data] 输入transaction_type={route_data.get('transaction_type')}, 输出transaction_type={adapted_data['transaction_type']}, foreign_amount={adapted_data['foreign_amount']}")

    return adapted_data


# ==================== 测试代码 ====================

if __name__ == '__main__':
    # 测试数据
    test_data = {
        'customer_id': '1234567890123',
        'customer_name': 'นายสมชาย ใจดี',
        'customer_address': '123 ถ.สุขุมวิท แขวงคลองเตย',
        'customer_phone': '02-1234567',
        'customer_occupation': 'พนักงานบริษัท',
        'transaction_date': datetime(2025, 10, 18),
        'transaction_type': 'buy',
        'foreign_amount': 75000.00,
        'transaction_purpose': 'ท่องเที่ยว',
        'beneficiary_name': 'ตนเอง',
        'reservation_no': 'AMLO20251018001',
        'is_original': True,
        'is_on_behalf': False,
        'branch': {
            'institution_code': '001',
            'branch_code': '002'
        }
    }

    # 生成PDF（使用绝对路径）
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    output_file = os.path.join(project_root, 'test_amlo_101.pdf')

    try:
        generate_amlo_pdf('AMLO-1-01', test_data, output_file)
        print(f"\n[SUCCESS] Test PDF generated: {output_file}")
        print("Please open it to verify the fields are filled correctly.")
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
