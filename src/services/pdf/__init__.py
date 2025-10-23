# -*- coding: utf-8 -*-
"""
PDF生成器模块
用于生成AMLO/BOT合规报告PDF

支持的PDF报告类型:
- AMLO-1-01: 现金交易报告 (Cash Transaction Report, ≥500,000 THB)
- AMLO-1-02: 资产交易报告 (Asset Transaction Report, ≥8,000,000 THB)
- AMLO-1-03: 可疑交易报告 (Suspicious Transaction Report)

使用示例:
    from services.pdf import AMLOPDFGenerator

    generator = AMLOPDFGenerator()

    # 生成AMLO-1-01报告
    data = {
        'report_number': 'A001-2025-001',
        'maker_name': 'ชื่อลูกค้า',
        'maker_id': '1234567890123',
        'transaction_date': '01/10/2025',
        'amount_thb': 500000.00,
        ...
    }
    pdf_path = generator.generate_pdf('AMLO-1-01', data, 'output.pdf')
"""

from .amlo_pdf_generator import AMLOPDFGenerator
from .amlo_form_filler import AMLOFormFiller, generate_amlo_pdf, adapt_route_data_to_pdf_data

__all__ = ['AMLOPDFGenerator', 'AMLOFormFiller', 'generate_amlo_pdf', 'adapt_route_data_to_pdf_data']
