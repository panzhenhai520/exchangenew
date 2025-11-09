# -*- coding: utf-8 -*-
"""
AMLO报告字段映射配置
包含AMLO-1-01、AMLO-1-02、AMLO-1-03三种报告类型的完整字段映射

坐标系统: PDF坐标系，原点在左下角
单位: points (1 point = 1/72 inch)
"""

from datetime import datetime

# ==================== AMLO-1-01 (CTR - 现金交易报告) ====================

AMLO_101_FIELDS = {
    # 区域A - 报告编号
    'institution_code': {
        'type': 'multi_char_boxes',
        'boxes': [
            {'x': 310.0, 'y': 789.0, 'width': 14.0, 'height': 18.0},
            {'x': 324.0, 'y': 789.0, 'width': 14.0, 'height': 18.0},
            {'x': 338.0, 'y': 789.0, 'width': 14.0, 'height': 18.0}
        ],
        'font_size': 12,
        'align': 'center'
    },
    'branch_code': {
        'type': 'multi_char_boxes',
        'boxes': [
            {'x': 356.0, 'y': 789.0, 'width': 14.0, 'height': 18.0},
            {'x': 370.0, 'y': 789.0, 'width': 14.0, 'height': 18.0},
            {'x': 384.0, 'y': 789.0, 'width': 14.0, 'height': 18.0}
        ],
        'font_size': 12,
        'align': 'center'
    },
    'year_be': {
        'type': 'multi_char_boxes',
        'boxes': [
            {'x': 402.0, 'y': 789.0, 'width': 14.0, 'height': 18.0},
            {'x': 416.0, 'y': 789.0, 'width': 14.0, 'height': 18.0}
        ],
        'font_size': 12,
        'align': 'center',
        'formatter': lambda date: str((date.year if hasattr(date, 'year') else datetime.now().year) + 543)[-2:]
    },
    'report_serial_number': {
        'type': 'text',
        'x': 434.0,
        'y': 795.0,
        'width': 84.0,
        'font_size': 10,
        'align': 'center'
    },

    # 区域B - 选项行
    'report_type_original': {
        'type': 'checkbox',
        'x': 33.0,
        'y': 761.0,
        'size': 6.0
    },
    'report_type_revised': {
        'type': 'checkbox',
        'x': 98.0,
        'y': 761.0,
        'size': 6.0
    },
    'revision_number': {
        'type': 'text',
        'x': 205.0,
        'y': 766.0,
        'width': 30.0,
        'font_size': 9,
        'align': 'center'
    },
    'revision_date': {
        'type': 'text',
        'x': 265.0,
        'y': 766.0,
        'width': 35.0,
        'font_size': 9,
        'align': 'center',
        'formatter': lambda date: date.strftime('%d/%m/%Y') if hasattr(date, 'strftime') else str(date)
    },
    'total_pages': {
        'type': 'text',
        'x': 481.0,
        'y': 766.0,
        'width': 25.0,
        'font_size': 9,
        'align': 'center',
        'default': '1'
    },

    # 区域C - ส่วนที่ ๑ 填报人信息
    'maker_id_card': {
        'type': 'multi_char_boxes',
        'boxes': [
            {'x': 366.48 + i * 14.17, 'y': 724.82, 'width': 14.17, 'height': 14.17}
            for i in range(13)
        ],
        'font_size': 11,
        'align': 'center'
    },
    'maker_full_name': {
        'type': 'text',
        'x': 75.8,
        'y': 670.0,
        'width': 280.68,
        'font_size': 10,
        'align': 'left'
    },
    'maker_transaction_by_self': {
        'type': 'checkbox',
        'x': 33.8,
        'y': 655.0,
        'size': 8.5
    },
    'maker_transaction_on_behalf': {
        'type': 'checkbox',
        'x': 33.8,
        'y': 643.0,
        'size': 8.5
    },
    'maker_address_line1': {
        'type': 'text',
        'x': 51.8,
        'y': 631.0,
        'width': 519.78,
        'font_size': 9,
        'align': 'left'
    },
    'maker_phone': {
        'type': 'text',
        'x': 191.8,
        'y': 619.0,
        'width': 153.0,
        'font_size': 9,
        'align': 'left'
    },
    'maker_fax': {
        'type': 'text',
        'x': 379.8,
        'y': 619.0,
        'width': 191.78,
        'font_size': 9,
        'align': 'left'
    },
    'maker_occupation': {
        'type': 'text',
        'x': 62.8,
        'y': 607.0,
        'width': 108.0,
        'font_size': 9,
        'align': 'left'
    },
    'maker_workplace': {
        'type': 'text',
        'x': 226.8,
        'y': 607.0,
        'width': 180.0,
        'font_size': 9,
        'align': 'left'
    },
    'maker_work_phone': {
        'type': 'text',
        'x': 444.8,
        'y': 607.0,
        'width': 126.78,
        'font_size': 9,
        'align': 'left'
    },

    # 区域E - ส่วนที่ ๓ 交易事实
    'transaction_date_day': {
        'type': 'text',
        'x': 358.0,
        'y': 378.0,
        'width': 55.0,
        'font_size': 9,
        'align': 'center',
        'formatter': lambda date: date.strftime('%d') if hasattr(date, 'strftime') else ''
    },
    'transaction_date_month': {
        'type': 'text',
        'x': 442.0,
        'y': 378.0,
        'width': 63.0,
        'font_size': 9,
        'align': 'center',
        'formatter': lambda date: date.strftime('%m') if hasattr(date, 'strftime') else ''
    },
    'transaction_date_year_be': {
        'type': 'text',
        'x': 528.0,
        'y': 378.0,
        'width': 43.58,
        'font_size': 9,
        'align': 'center',
        'formatter': lambda date: str(date.year + 543) if hasattr(date, 'year') else ''
    },

    # 左侧交易框 - 存款/买入
    'transaction_left_type_deposit': {
        'type': 'checkbox',
        'x': 32.7,
        'y': 322.68,
        'size': 6.5
    },
    'transaction_left_type_buy_foreign_currency': {
        'type': 'checkbox',
        'x': 32.7,
        'y': 222.68,
        'size': 6.5
    },
    'transaction_left_total_amount': {
        'type': 'text',
        'x': 227.45,
        'y': 156.0,
        'width': 65.25,
        'font_size': 10,
        'align': 'right',
        'formatter': lambda amount: f'{float(amount):,.2f}' if amount else '0.00'
    },

    # 右侧交易框 - 取款/卖出
    'transaction_right_type_withdraw': {
        'type': 'checkbox',
        'x': 307.7,
        'y': 322.68,
        'size': 6.5
    },
    'transaction_right_type_sell_foreign_currency': {
        'type': 'checkbox',
        'x': 307.7,
        'y': 222.68,
        'size': 6.5
    },
    'transaction_right_total_amount': {
        'type': 'text',
        'x': 502.45,
        'y': 156.0,
        'width': 65.25,
        'font_size': 10,
        'align': 'right',
        'formatter': lambda amount: f'{float(amount):,.2f}' if amount else '0.00'
    },

    # 受益人和交易目的
    'transaction_beneficiary_name': {
        'type': 'text',
        'x': 207.68,
        'y': 114.5,
        'width': 363.9,
        'font_size': 9,
        'align': 'left'
    },
    'transaction_purpose': {
        'type': 'text',
        'x': 167.68,
        'y': 98.0,
        'width': 403.9,
        'font_size': 9,
        'align': 'left'
    },

    # 区域F - 签名区
    'signature_right_report_date': {
        'type': 'text',
        'x': 460.0,
        'y': 69.5,
        'width': 80.0,
        'font_size': 8,
        'align': 'right',
        'formatter': lambda date: date.strftime('%d/%m/%Y') if hasattr(date, 'strftime') else str(date)
    }
}

# ==================== 数据库字段到PDF字段的映射 ====================

DB_TO_PDF_MAPPING_101 = {
    # 报告编号
    'institution_code': 'branch.institution_code',
    'branch_code': 'branch.branch_code',
    'year_be': 'transaction_date',
    'report_serial_number': 'reservation_no',

    # 选项
    'report_type_original': lambda data: data.get('is_original', True),
    'total_pages': lambda data: '1',

    # 填报人信息
    'maker_id_card': 'customer_id',
    'maker_full_name': 'customer_name',
    'maker_transaction_by_self': lambda data: not data.get('is_on_behalf', False),
    'maker_transaction_on_behalf': lambda data: data.get('is_on_behalf', False),
    'maker_address_line1': 'customer_address',
    'maker_phone': 'customer_phone',
    'maker_occupation': 'customer_occupation',

    # 交易日期
    'transaction_date_day': 'transaction_date',
    'transaction_date_month': 'transaction_date',
    'transaction_date_year_be': 'transaction_date',

    # 交易类型和金额
    'transaction_left_type_buy_foreign_currency': lambda data: data.get('transaction_type') == 'buy',
    'transaction_left_total_amount': lambda data: data.get('foreign_amount') if data.get('transaction_type') == 'buy' else '',
    'transaction_right_type_sell_foreign_currency': lambda data: data.get('transaction_type') == 'sell',
    'transaction_right_total_amount': lambda data: data.get('foreign_amount') if data.get('transaction_type') == 'sell' else '',

    # 交易目的
    'transaction_purpose': 'transaction_purpose',
    'transaction_beneficiary_name': 'beneficiary_name',

    # 报告日期
    'signature_right_report_date': lambda data: datetime.now()
}

# ==================== AMLO-1-02 和 AMLO-1-03 配置 ====================
# (简化版本，可以后续扩展)

AMLO_102_FIELDS = AMLO_101_FIELDS.copy()
DB_TO_PDF_MAPPING_102 = DB_TO_PDF_MAPPING_101.copy()

AMLO_103_FIELDS = AMLO_101_FIELDS.copy()
DB_TO_PDF_MAPPING_103 = DB_TO_PDF_MAPPING_101.copy()

# ==================== 报告类型配置字典 ====================

# 计算模板文件的绝对路径
import os as _os
_CURRENT_DIR = _os.path.dirname(_os.path.abspath(__file__))
_PROJECT_ROOT = _os.path.dirname(_os.path.dirname(_os.path.dirname(_CURRENT_DIR)))
_TEMPLATE_DIR = _os.path.join(_PROJECT_ROOT, 'src', 'static', 'amlo_forms')

REPORT_CONFIGS = {
    'AMLO-1-01': {
        'template': _os.path.join(_TEMPLATE_DIR, 'AMLO-1-01.pdf'),
        'fields': AMLO_101_FIELDS,
        'db_mapping': DB_TO_PDF_MAPPING_101
    },
    'AMLO-1-02': {
        'template': _os.path.join(_TEMPLATE_DIR, 'AMLO-1-02.pdf'),
        'fields': AMLO_102_FIELDS,
        'db_mapping': DB_TO_PDF_MAPPING_102
    },
    'AMLO-1-03': {
        'template': _os.path.join(_TEMPLATE_DIR, 'AMLO-1-03.pdf'),
        'fields': AMLO_103_FIELDS,
        'db_mapping': DB_TO_PDF_MAPPING_103
    }
}
