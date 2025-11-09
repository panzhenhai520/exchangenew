#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
80mm热敏打印机优化的外币兑换收据生成器
根据Receipt size example.jpg设计，符合泰国银行外币兑换票据格式
"""

import logging
import os
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, KeepTogether, SimpleDocTemplate
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from .pdf_base import PDFBase

logger = logging.getLogger(__name__)

class ThermalExchangePDFGenerator(PDFBase):
    """80mm热敏打印机优化的外币兑换收据生成器"""

    # 80mm热敏纸设置
    THERMAL_WIDTH = 80 * mm
    THERMAL_MARGIN = 3 * mm
    CONTENT_WIDTH = 74 * mm

    @staticmethod
    def create_thermal_pdf_doc(file_path, estimated_height=150*mm):
        """创建80mm热敏打印PDF文档"""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        return SimpleDocTemplate(
            file_path,
            pagesize=(ThermalExchangePDFGenerator.THERMAL_WIDTH, estimated_height),
            rightMargin=ThermalExchangePDFGenerator.THERMAL_MARGIN,
            leftMargin=ThermalExchangePDFGenerator.THERMAL_MARGIN,
            topMargin=ThermalExchangePDFGenerator.THERMAL_MARGIN,
            bottomMargin=ThermalExchangePDFGenerator.THERMAL_MARGIN
        )

    @staticmethod
    def get_thermal_styles(font_name):
        """获取热敏打印优化的样式"""
        return {
            'header_main': ParagraphStyle(
                'HeaderMain',
                fontName=font_name,
                fontSize=9,
                alignment=TA_CENTER,
                spaceAfter=2,
                leading=10
            ),
            'header_sub': ParagraphStyle(
                'HeaderSub',
                fontName=font_name,
                fontSize=7,
                alignment=TA_CENTER,
                spaceAfter=1,
                leading=8
            ),
            'transaction_type': ParagraphStyle(
                'TransactionType',
                fontName=font_name,
                fontSize=14,
                alignment=TA_CENTER,
                spaceAfter=4,
                leading=16,
                fontWeight='bold'
            ),
            'subtitle': ParagraphStyle(
                'Subtitle',
                fontName=font_name,
                fontSize=8,
                alignment=TA_CENTER,
                spaceAfter=3,
                leading=9
            ),
            'detail_label': ParagraphStyle(
                'DetailLabel',
                fontName=font_name,
                fontSize=7,
                alignment=TA_LEFT,
                spaceAfter=1,
                leading=8
            ),
            'detail_value': ParagraphStyle(
                'DetailValue',
                fontName=font_name,
                fontSize=7,
                alignment=TA_LEFT,
                spaceAfter=1,
                leading=8,
                fontWeight='bold'
            ),
            'table_header': ParagraphStyle(
                'TableHeader',
                fontName=font_name,
                fontSize=6,
                alignment=TA_CENTER,
                leading=7
            ),
            'table_cell': ParagraphStyle(
                'TableCell',
                fontName=font_name,
                fontSize=7,
                alignment=TA_CENTER,
                leading=8
            ),
            'total': ParagraphStyle(
                'Total',
                fontName=font_name,
                fontSize=9,
                alignment=TA_RIGHT,
                fontWeight='bold',
                spaceAfter=2,
                leading=10
            ),
            'footer': ParagraphStyle(
                'Footer',
                fontName=font_name,
                fontSize=6,
                alignment=TA_CENTER,
                spaceAfter=1,
                leading=7
            ),
            'signature': ParagraphStyle(
                'Signature',
                fontName=font_name,
                fontSize=7,
                alignment=TA_CENTER,
                spaceAfter=2,
                leading=8
            ),
            'small_info': ParagraphStyle(
                'SmallInfo',
                fontName=font_name,
                fontSize=6,
                alignment=TA_LEFT,
                spaceAfter=1,
                leading=7,
                leftIndent=3*mm
            )
        }

    @staticmethod
    def generate_thermal_pdf(transaction_data, file_path, language='zh'):
        """
        生成80mm热敏打印优化的兑换交易PDF

        Args:
            transaction_data: 交易数据字典
            file_path: PDF文件保存路径
            language: 语言代码 ('zh', 'en', 'th')

        Returns:
            bool: 生成是否成功
        """
        try:
            # 获取多语言文本
            texts = ThermalExchangePDFGenerator._get_thermal_texts(language)

            # 初始化字体支持，使用支持中文的字体
            PDFBase.init_fonts(language)
            
            # 获取安全的字体名称（支持中文）
            if language == 'zh':
                font_name = 'SimHei' if 'SimHei' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'
            elif language == 'th':
                font_name = 'ArialUnicode' if 'ArialUnicode' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'
            else:
                font_name = 'Tahoma' if 'Tahoma' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'
            
            logger.info(f"使用字体: {font_name} (语言: {language})")
            styles = ThermalExchangePDFGenerator.get_thermal_styles(font_name)

            # 创建PDF文档 - 预估高度
            doc = ThermalExchangePDFGenerator.create_thermal_pdf_doc(file_path, 180*mm)

            # 构建PDF内容
            story = []

            # 1. 标题头部 - 公司信息（新增）
            if transaction_data.get('company_full_name'):
                story.append(Paragraph(f"<b>{transaction_data['company_full_name']}</b>", styles['header_main']))
                if transaction_data.get('tax_registration_number'):
                    story.append(Paragraph(
                        f"{texts['tax_number']}: {transaction_data['tax_registration_number']}",
                        styles['header_sub']
                    ))
                story.append(Spacer(1, 2))

            # 网点信息
            if transaction_data.get('branch_name'):
                story.append(Paragraph(f"<b>{transaction_data['branch_name']}</b>", styles['header_main']))
                if transaction_data.get('branch_code'):
                    story.append(Paragraph(f"{texts['branch_code']}: {transaction_data['branch_code']}", styles['header_sub']))

            # 许可证和联系信息
            if transaction_data.get('branch_license'):
                story.append(Paragraph(f"{texts['license']}: {transaction_data['branch_license']}", styles['header_sub']))
            if transaction_data.get('branch_website'):
                story.append(Paragraph(f"{texts['website']}: {transaction_data['branch_website']}", styles['header_sub']))

            story.append(Spacer(1, 4))

            # 2. 交易类型 (BUY/SELL)
            transaction_type = transaction_data.get('type', '').upper()
            if transaction_type in ['BUY', 'BUY_FOREIGN']:
                type_display = 'BUY'
            elif transaction_type in ['SELL', 'SELL_FOREIGN']:
                type_display = 'SELL'
            else:
                type_display = transaction_type

            story.append(Paragraph(type_display, styles['transaction_type']))
            story.append(Spacer(1, 3))

            # 3. Statement标题
            story.append(Paragraph(texts['statement_title'], styles['subtitle']))
            story.append(Spacer(1, 3))

            # 4. 交易详情
            # 基本信息
            story.append(Paragraph(f"{texts['transaction_no']}: {transaction_data.get('transaction_no', '')}", styles['detail_label']))
            story.append(Paragraph(f"{texts['date_time']}: {transaction_data.get('transaction_date', '')} {transaction_data.get('transaction_time', '')}", styles['detail_label']))

            # 付款方式（新增）
            payment_method_display = {
                'cash': texts['payment_cash'],
                'instrument_cheque': texts.get('payment_instrument_cheque', texts['payment_other']),
                'instrument_draft': texts.get('payment_instrument_draft', texts['payment_other']),
                'instrument_other': texts.get('payment_instrument_other', texts['payment_other']),
                'other': texts.get('payment_other_method', texts['payment_other'])
            }.get(transaction_data.get('payment_method', 'cash'), texts['payment_cash'])

            story.append(Paragraph(f"{texts['payment_method']}: {payment_method_display}", styles['detail_label']))
            if transaction_data.get('payment_method_note'):
                story.append(Paragraph(f"  {texts['payment_note']}: {transaction_data['payment_method_note']}", styles['small_info']))

            story.append(Spacer(1, 2))

            # 客户信息
            if transaction_data.get('customer_name'):
                story.append(Paragraph(f"{texts['customer_name']}: {transaction_data['customer_name']}", styles['detail_label']))
            if transaction_data.get('customer_id'):
                story.append(Paragraph(f"{texts['customer_id']}: {transaction_data['customer_id']}", styles['detail_label']))

            # 国家信息优化（新增）
            if transaction_data.get('customer_country_code'):
                country_name = ThermalExchangePDFGenerator._get_country_name(
                    transaction_data['customer_country_code'],
                    language,
                    transaction_data.get('session')
                )
                story.append(Paragraph(
                    f"{texts['country']}: {country_name} ({transaction_data['customer_country_code']})",
                    styles['detail_label']
                ))

            if transaction_data.get('customer_address'):
                story.append(Paragraph(f"{texts['address']}: {transaction_data['customer_address']}", styles['detail_label']))

            story.append(Spacer(1, 4))

            # 5. 币种交易表格
            currency_table = ThermalExchangePDFGenerator._create_thermal_currency_table(
                transaction_data, styles, texts, font_name
            )
            story.append(currency_table)
            story.append(Spacer(1, 3))

            # 6. 总计
            total_data = ThermalExchangePDFGenerator._create_thermal_total_section(
                transaction_data, styles, texts, font_name
            )
            story.extend(total_data)
            story.append(Spacer(1, 5))

            # 7. 货币来源说明
            story.append(Paragraph(texts['money_source'], styles['footer']))
            story.append(Spacer(1, 2))

            # 8. 注意事项
            story.append(Paragraph(texts['notice'], styles['footer']))
            story.append(Spacer(1, 4))

            # 9. 签名区域
            signature_section = ThermalExchangePDFGenerator._create_thermal_signature_section(
                transaction_data, styles, texts
            )
            story.extend(signature_section)

            # 10. 感谢语
            story.append(Spacer(1, 3))
            story.append(Paragraph(texts['thank_you'], styles['footer']))

            # 生成PDF
            doc.build(story)

            logger.info(f"热敏兑换收据PDF生成成功: {file_path}")
            return True

        except Exception as e:
            logger.error(f"生成热敏兑换收据PDF失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return False

    @staticmethod
    def _create_thermal_currency_table(transaction_data, styles, texts, font_name='Helvetica'):
        """创建币种交易表格"""
        # 表格数据
        table_data = [
            [texts['no'], texts['currency'], texts['qty'], texts['rate'], texts['amount_local']]
        ]

        # 添加交易数据行
        foreign_currency = transaction_data.get('currency_code', 'USD')
        foreign_amount = abs(float(transaction_data.get('amount', 0)))
        exchange_rate = float(transaction_data.get('rate', 0))
        local_amount = abs(float(transaction_data.get('local_amount', 0)))
        base_currency = transaction_data.get('base_currency_code', 'THB')

        table_data.append([
            '1',
            foreign_currency,
            f"{foreign_amount:.2f}",
            f"{exchange_rate:.4f}",
            f"{local_amount:.2f}"
        ])

        # 创建表格
        table = Table(table_data, colWidths=[
            8*mm,   # No
            12*mm,  # Currency
            15*mm,  # Qty
            15*mm,  # Rate
            20*mm   # Amount
        ])

        # 表格样式
        table.setStyle(TableStyle([
            # 表头样式
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 6),
            ('FONTSIZE', (0, 1), (-1, -1), 7),

            # 边框
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),

            # 内容样式
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        return table

    @staticmethod
    def _create_thermal_total_section(transaction_data, styles, texts, font_name='Helvetica'):
        """创建总计部分"""
        total_elements = []

        local_amount = abs(float(transaction_data.get('local_amount', 0)))
        base_currency = transaction_data.get('base_currency_code', 'THB')

        # 总计表格
        total_data = [
            [texts['total_label'], f"{local_amount:.2f}"]
        ]

        total_table = Table(total_data, colWidths=[50*mm, 20*mm])
        total_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))

        total_elements.append(total_table)

        return total_elements

    @staticmethod
    def _create_thermal_signature_section(transaction_data, styles, texts):
        """创建签名区域"""
        signature_elements = []

        # 客户签名
        signature_elements.append(Paragraph(texts['customer_signature'], styles['signature']))
        signature_elements.append(Spacer(1, 8))  # 签名空间
        signature_elements.append(Paragraph("_" * 20, styles['signature']))
        signature_elements.append(Paragraph(texts['customer'], styles['footer']))
        signature_elements.append(Spacer(1, 3))

        # 柜员信息
        operator_name = transaction_data.get('operator_name', '')
        if operator_name:
            signature_elements.append(Paragraph(f"{texts['teller']}: {operator_name}", styles['footer']))

        return signature_elements

    @staticmethod
    def _get_thermal_texts(language):
        """获取热敏打印对应语言的文本"""
        texts = {
            'zh': {
                'statement_title': '外币兑换业务凭证 Statement of Currency Exchange',
                'tax_number': '税务登记号',
                'license': '营业执照',
                'website': '网站',
                'branch_code': '网点代码',
                'transaction_no': '流水号码',
                'date_time': '日期/时间',
                'payment_method': '付款方式',
                'payment_note': '付款备注',
                'payment_cash': '现金',
                'payment_instrument_cheque': '金融票据（支票）',
                'payment_instrument_draft': '金融票据（银行汇票）',
                'payment_instrument_other': '金融票据（其他票据）',
                'payment_other_method': '其他方式',
                'payment_bank': '银行转账',
                'payment_fcd': 'FCD账户',
                'payment_other': '其他',
                'reference_no': '参考号码',
                'customer_name': '客户姓名',
                'customer_id': '证件号码',
                'country': '国家/地区',
                'country_code': '国家代码',
                'address': '地址',
                'no': '序号',
                'currency': '币种',
                'qty': '数量',
                'rate': '汇率',
                'amount_local': '金额(泰铢)',
                'total_label': '合计(TOTAL)',
                'money_source': '资金来源于客户',
                'notice': '本凭证作为银行已经收取和支付的证明，客户已经检查并确认了正确的金额',
                'customer_signature': '客户签名',
                'customer': '客户',
                'teller': '柜员',
                'thank_you': 'Thank you.'
            },
            'en': {
                'statement_title': 'Statement of Currency Exchange',
                'tax_number': 'Tax Registration No',
                'license': 'Business License',
                'website': 'Website',
                'branch_code': 'Branch Code',
                'transaction_no': 'Transaction No',
                'date_time': 'Date/Time',
                'payment_method': 'Payment Method',
                'payment_note': 'Payment Note',
                'payment_cash': 'Cash',
                'payment_instrument_cheque': 'Instrument (Cheque)',
                'payment_instrument_draft': 'Instrument (Bank Draft)',
                'payment_instrument_other': 'Instrument (Other Note)',
                'payment_other_method': 'Other Method',
                'payment_bank': 'Bank Transfer',
                'payment_fcd': 'FCD Account',
                'payment_other': 'Other',
                'reference_no': 'Reference No',
                'customer_name': 'Customer Name',
                'customer_id': 'ID Number',
                'country': 'Country/Region',
                'country_code': 'Country Code',
                'address': 'Address',
                'no': 'No.',
                'currency': 'Currency',
                'qty': 'Qty',
                'rate': 'Rate',
                'amount_local': 'Amount(Baht)',
                'total_label': 'TOTAL(BAHT)',
                'money_source': 'Money from Customer',
                'notice': 'This receipt serves as evidence that customer has already checked and received the correct amount of money in full',
                'customer_signature': 'Customer Signature',
                'customer': 'Customer',
                'teller': 'Teller',
                'thank_you': 'Thank you.'
            },
            'th': {
                'statement_title': 'ใบยืนยันการแลกเปลี่ยนเงินตราต่างประเทศ',
                'tax_number': 'เลขทะเบียนภาษี',
                'license': 'ใบอนุญาตประกอบธุรกิจ',
                'website': 'เว็บไซต์',
                'branch_code': 'รหัสสาขา',
                'transaction_no': 'เลขที่รายการ',
                'date_time': 'วันที่/เวลา',
                'payment_method': 'วิธีชำระเงิน',
                'payment_note': 'หมายเหตุการชำระเงิน',
                'payment_cash': 'เงินสด',
                'payment_instrument_cheque': 'ตราสารการเงิน (เช็ค)',
                'payment_instrument_draft': 'ตราสารการเงิน (ดราฟต์)',
                'payment_instrument_other': 'ตราสารการเงิน (อื่นๆ)',
                'payment_other_method': 'วิธีอื่น',
                'payment_bank': 'โอนเงินผ่านธนาคาร',
                'payment_fcd': 'บัญชี FCD',
                'payment_other': 'อื่นๆ',
                'reference_no': 'เลขที่อ้างอิง',
                'customer_name': 'ชื่อลูกค้า',
                'customer_id': 'เลขประจำตัว',
                'country': 'ประเทศ/ภูมิภาค',
                'country_code': 'รหัสประเทศ',
                'address': 'ที่อยู่',
                'no': 'ลำดับ',
                'currency': 'สกุลเงิน',
                'qty': 'จำนวน',
                'rate': 'อัตรา',
                'amount_local': 'จำนวนเงิน(บาท)',
                'total_label': 'รวม(บาท)',
                'money_source': 'เงินจากลูกค้า',
                'notice': 'ใบเสร็จนี้เป็นหลักฐานว่าลูกค้าได้ตรวจสอบและรับเงินครบถ้วนถูกต้องแล้ว',
                'customer_signature': 'ลายเซ็นลูกค้า',
                'customer': 'ลูกค้า',
                'teller': 'เจ้าหน้าที่',
                'thank_you': 'ขอบคุณค่ะ'
            }
        }

        return texts.get(language, texts['en'])  # Default to English if language not found

    @staticmethod
    def _get_country_name(country_code, language, session):
        """
        根据国家代码和语言获取完整国家名称

        Args:
            country_code: ISO 3166-1 alpha-2国家代码
            language: 语言代码 ('zh', 'en', 'th')
            session: 数据库会话

        Returns:
            str: 完整国家名称，如果未找到返回国家代码
        """
        from models.exchange_models import Country

        try:
            country = session.query(Country).filter_by(
                country_code=country_code,
                is_active=True
            ).first()

            if country:
                if language == 'en':
                    return country.country_name_en
                elif language == 'th':
                    return country.country_name_th or country.country_name_en
                else:
                    return country.country_name_zh
            return country_code
        except Exception as e:
            logger.warning(f"Failed to get country name for {country_code}: {e}")
            return country_code

    @staticmethod
    def generate_pdf(transaction_data, file_path, language='zh'):
        """兼容性方法 - 调用热敏PDF生成"""
        return ThermalExchangePDFGenerator.generate_thermal_pdf(transaction_data, file_path, language)
