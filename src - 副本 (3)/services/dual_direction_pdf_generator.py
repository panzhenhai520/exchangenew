#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
双向交易PDF生成器
专门处理支持面值组合的双向兑换交易PDF票据生成
优化80mm热敏打印机输出
"""

import logging
import os
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from .pdf_base import PDFBase

logger = logging.getLogger(__name__)

class DualDirectionPDFGenerator(PDFBase):
    """双向交易PDF生成器 - 80mm热敏打印优化"""

    # 80mm热敏纸宽度设置
    THERMAL_WIDTH = 80 * mm
    THERMAL_MARGIN = 5 * mm
    CONTENT_WIDTH = 70 * mm

    @staticmethod
    def generate_dual_direction_receipt(business_group_data, session, language='zh'):
        """
        生成双向交易PDF票据

        Args:
            business_group_data: 业务组数据，包含所有相关交易
            session: 数据库会话
            language: 语言代码 ('zh', 'en', 'th')

        Returns:
            str: PDF文件的base64编码内容
        """
        try:
            # 获取相关数据
            from models.exchange_models import Currency, Operator, Branch

            # 获取业务组的基本信息（从第一条交易记录获取）
            first_transaction = business_group_data['transactions'][0] if business_group_data.get('transactions') else None
            if not first_transaction:
                raise ValueError("业务组数据中没有找到交易记录")

            # 查询相关的数据库记录
            branch = session.query(Branch).filter_by(id=business_group_data['branch_id']).first()
            operator = session.query(Operator).filter_by(id=business_group_data['operator_id']).first()

            # 获取网点本币信息
            base_currency_code = 'USD'  # 默认值
            if branch and branch.base_currency_id:
                base_currency = session.query(Currency).filter_by(id=branch.base_currency_id).first()
                if base_currency:
                    base_currency_code = base_currency.currency_code

            # 构建交易数据
            receipt_data = {
                'business_group_id': business_group_data['business_group_id'],
                'transaction_date': business_group_data.get('transaction_date'),
                'transaction_time': business_group_data.get('transaction_time'),
                'customer_info': business_group_data.get('customer_info', {}),
                'transactions': business_group_data['transactions'],
                'denomination_details': business_group_data.get('denomination_details', []),
                'branch_name': branch.branch_name if branch else '',
                'branch_code': branch.branch_code if branch else '',
                'branch_address': getattr(branch, 'address', '') if branch else '',
                'branch_phone': getattr(branch, 'phone_number', '') if branch else '',
                'branch_license': getattr(branch, 'license_number', '') if branch else '',
                'branch_website': getattr(branch, 'website', '') if branch else '',
                'branch_company': getattr(branch, 'company_name', '') if branch else '',
                # 新增字段
                'company_full_name': branch.company_full_name if branch else '',
                'tax_registration_number': branch.tax_registration_number if branch else '',
                'payment_method': business_group_data.get('payment_method', 'cash'),
                'payment_method_note': business_group_data.get('payment_method_note', ''),
                'operator_name': operator.name if operator else '',
                'base_currency': base_currency_code,
                'language': language,
                'session': session,  # 传递session用于查询国家名称
                'total_currencies': len(set(tx['currency_id'] for tx in business_group_data['transactions']))
            }

            # 生成临时文件路径
            temp_file = PDFBase.create_temp_file()

            # 生成PDF
            success = DualDirectionPDFGenerator._generate_thermal_pdf(receipt_data, temp_file, language)

            if success:
                # 读取文件内容并编码为base64
                import base64
                with open(temp_file, 'rb') as f:
                    pdf_content = base64.b64encode(f.read()).decode('utf-8')

                # 删除临时文件
                os.remove(temp_file)

                return pdf_content
            else:
                raise Exception("PDF生成失败")

        except Exception as e:
            logger.error(f"生成双向交易收据失败: {e}")
            raise

    @staticmethod
    def _generate_thermal_pdf(receipt_data, file_path, language='zh'):
        """
        生成80mm热敏纸优化的PDF

        Args:
            receipt_data: 收据数据
            file_path: 文件保存路径
            language: 语言代码

        Returns:
            bool: 生成是否成功
        """
        try:
            # 确保目录存在
            dir_path = os.path.dirname(file_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)

            # 获取多语言文本
            texts = DualDirectionPDFGenerator._get_language_texts(language)

            # 初始化字体并获取推荐的字体名称
            font_name = PDFBase.init_fonts(language)
            logger.info(f"PDFBase推荐字体: {font_name} (语言: {language})")

            # 确保字体已注册，否则降级到Helvetica
            registered_fonts = pdfmetrics.getRegisteredFontNames()
            if font_name not in registered_fonts:
                logger.warning(f"字体 {font_name} 未注册，降级使用Helvetica")
                font_name = 'Helvetica'

            logger.info(f"最终使用字体: {font_name}")
            styles = DualDirectionPDFGenerator._get_thermal_styles(font_name)

            # 创建自定义80mm页面大小的PDF文档
            from reportlab.platypus import SimpleDocTemplate
            doc = SimpleDocTemplate(
                file_path,
                pagesize=(DualDirectionPDFGenerator.THERMAL_WIDTH, 200*mm),  # 动态高度
                leftMargin=DualDirectionPDFGenerator.THERMAL_MARGIN,
                rightMargin=DualDirectionPDFGenerator.THERMAL_MARGIN,
                topMargin=10*mm,
                bottomMargin=10*mm
            )

            # 构建PDF内容
            story = []

            # 1. 公司抬头（居中粗体）
            if receipt_data.get('company_full_name'):
                story.append(Paragraph(f"<b>{receipt_data['company_full_name']}</b>", styles['center']))
                story.append(Spacer(1, 0.5*mm))

            # 2. 地址信息（居中小字）
            branch_address = receipt_data.get('branch_address', '')
            if branch_address:
                story.append(Paragraph(f"{texts.get('address', 'ที่อยู่')}: {branch_address}", styles['small_center']))
                story.append(Spacer(1, 0.5*mm))

            # 3. 电话和网站（一行显示）
            contact_parts = []
            branch_phone = receipt_data.get('branch_phone', '')
            branch_website = receipt_data.get('branch_website', '')
            if branch_phone:
                contact_parts.append(f"{texts.get('phone', 'โทร')}: {branch_phone}")
            if branch_website:
                contact_parts.append(f"{texts.get('website', 'เว็บไซต์')}: {branch_website}")
            if contact_parts:
                story.append(Paragraph("  ".join(contact_parts), styles['small_center']))
                story.append(Spacer(1, 1*mm))

            # 4. 票据类型和标题
            story.append(Paragraph("<b>SELL/ใบขายธนบัตร</b>", styles['center']))
            story.append(Paragraph(f"<b>{texts['title']}</b>", styles['title']))
            story.append(Spacer(1, 1*mm))

            # 5. 许可证号和日期时间（左右对齐）
            license_line_parts = []
            if receipt_data.get('branch_license'):
                license_line_parts.append(f"{texts['license']}: {receipt_data['branch_license']}")
            license_line_parts.append(f"{texts['date']}: {receipt_data.get('transaction_date', '')} {texts.get('time', 'เวลา')}: {receipt_data.get('transaction_time', '')}")
            if license_line_parts:
                story.append(Paragraph("  ".join(license_line_parts), styles['info']))

            # 6. 税号
            if receipt_data.get('tax_registration_number'):
                story.append(Paragraph(
                    f"{texts['tax_number']}: {receipt_data['tax_registration_number']}",
                    styles['info']
                ))

            # 7. 收据编号
            if receipt_data.get('business_group_id'):
                story.append(Paragraph(
                    f"<b>{texts.get('receipt_no', 'เลขที่/No.')}: {receipt_data['business_group_id']}</b>",
                    styles['info']
                ))
                story.append(Spacer(1, 1*mm))

            story.append(Paragraph("-" * 40, styles['separator']))
            story.append(Spacer(1, 1*mm))

            # 付款方式（新增）
            payment_method_display = {
                'cash': texts['payment_cash'],
                'instrument_cheque': texts.get('payment_instrument_cheque', texts['payment_other']),
                'instrument_draft': texts.get('payment_instrument_draft', texts['payment_other']),
                'instrument_other': texts.get('payment_instrument_other', texts['payment_other']),
                'other': texts.get('payment_other_method', texts['payment_other'])
            }.get(receipt_data.get('payment_method', 'cash'), texts['payment_cash'])

            story.append(Paragraph(f"<b>{texts['payment_method']}:</b> {payment_method_display}", styles['info']))
            if receipt_data.get('payment_method_note'):
                story.append(Paragraph(f"  {texts['payment_note']}: {receipt_data['payment_method_note']}", styles['small_info']))

            story.append(Spacer(1, 1.5*mm))

            # 客户信息
            customer_info = receipt_data.get('customer_info', {})
            if customer_info.get('name'):
                story.append(Paragraph(f"<b>{texts['customer_name']}:</b> {customer_info['name']}", styles['info']))
            if customer_info.get('id_number'):
                story.append(Paragraph(f"<b>{texts['customer_id']}:</b> {customer_info['id_number']}", styles['info']))

            # 国家信息优化（新增）
            if customer_info.get('country_code'):
                country_name = DualDirectionPDFGenerator._get_country_name(
                    customer_info['country_code'],
                    receipt_data['language'],
                    receipt_data.get('session')
                )
                story.append(Paragraph(
                    f"<b>{texts['country']}:</b> {country_name} ({customer_info['country_code']})",
                    styles['info']
                ))

            if customer_info.get('address'):
                story.append(Paragraph(f"<b>{texts['customer_address']}:</b> {customer_info['address']}", styles['info']))

            story.append(Spacer(1, 1.5*mm))
            story.append(Paragraph("-" * 40, styles['separator']))
            story.append(Spacer(1, 1.5*mm))

            # 面值详情表格
            if receipt_data.get('denomination_details'):
                story.append(Paragraph(f"<b>{texts['denomination_details']}</b>", styles['section_title']))
                story.append(Spacer(1, 1*mm))

                denomination_table = DualDirectionPDFGenerator._create_denomination_table(
                    receipt_data['denomination_details'], font_name, texts
                )
                story.append(denomination_table)
                story.append(Spacer(1, 1.5*mm))

            # 交易汇总
            story.append(Paragraph(f"<b>{texts['transaction_summary']}</b>", styles['section_title']))
            story.append(Spacer(1, 1*mm))

            # 按币种分组显示交易汇总
            currency_summary = DualDirectionPDFGenerator._create_currency_summary(
                receipt_data['transactions'], receipt_data['base_currency']
            )

            for currency_code, summary in currency_summary.items():
                story.append(Paragraph(f"<b>{currency_code}:</b>", styles['currency_header']))

                if summary['buy_amount'] > 0:
                    story.append(Paragraph(
                        f"  买入: {summary['buy_amount']:,.2f} {currency_code} → {summary['buy_local']:,.2f} {receipt_data['base_currency']}",
                        styles['transaction_line']
                    ))

                if summary['sell_amount'] > 0:
                    story.append(Paragraph(
                        f"  卖出: {summary['sell_amount']:,.2f} {currency_code} ← {summary['sell_local']:,.2f} {receipt_data['base_currency']}",
                        styles['transaction_line']
                    ))

                story.append(Paragraph(
                    f"  平均汇率: 1 {currency_code} = {summary['avg_rate']:,.4f} {receipt_data['base_currency']}",
                    styles['rate_line']
                ))
                story.append(Spacer(1, 1*mm))

            story.append(Spacer(1, 1.5*mm))
            story.append(Paragraph("-" * 40, styles['separator']))
            story.append(Spacer(1, 1.5*mm))

            # 操作员信息
            if receipt_data.get('operator_name'):
                story.append(Paragraph(f"<b>{texts['operator']}:</b> {receipt_data['operator_name']}", styles['info']))

            # 备注信息
            if customer_info.get('remarks'):
                story.append(Paragraph(f"<b>{texts['remarks']}:</b> {customer_info['remarks']}", styles['info']))

            story.append(Spacer(1, 2*mm))

            # 签名区域
            signature_section = DualDirectionPDFGenerator._create_signature_section(texts, styles)
            story.append(signature_section)

            story.append(Spacer(1, 2*mm))

            # 注意事项
            story.append(Paragraph(texts['notice'], styles['notice']))

            # 生成PDF
            doc.build(story)

            logger.info(f"双向交易收据PDF生成成功: {file_path}")
            return True

        except Exception as e:
            logger.error(f"生成双向交易收据PDF失败: {e}")
            return False

    @staticmethod
    def _get_language_texts(language):
        """获取对应语言的文本"""
        texts = {
            'zh': {
                'title': 'Statement of Currency Exchange / ใบเสร็จรับเงิน (Receipt)',
                'address': 'ที่อยู่',
                'phone': 'โทร',
                'time': 'เวลา',
                'tax_number': 'เลขประจำตัวผู้เสียภาษี',
                'license': 'ใบอนุญาตเลขที่',
                'receipt_no': 'เลขที่/No.',
                'website': 'เว็บไซต์',
                'branch_code': '网点代码',
                'business_group': '业务组号',
                'transaction_date': '交易日期',
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
                'customer_name': '客户姓名',
                'customer_id': '证件号码',
                'country': '国家/地区',
                'country_code': '国家/地区',
                'customer_address': '联系地址',
                'denomination_details': '面值明细',
                'transaction_summary': '交易汇总',
                'denomination': '面值',
                'type': '类型',
                'quantity': '数量',
                'direction': '方向',
                'subtotal': '小计',
                'rate': '汇率',
                'bill': '纸币',
                'coin': '硬币',
                'buy': '买入',
                'sell': '卖出',
                'operator': '操作员',
                'remarks': '备注',
                'customer_signature': '客户签名',
                'teller_signature': '柜员签名',
                'date': '日期',
                'notice': '注意事项:\n1. 请核对交易信息，如有疑问请及时联系。\n2. 本凭证请妥善保管，作为交易凭证。\n3. 如需查询，请提供业务组号。'
            },
            'en': {
                'title': 'Statement of Currency Exchange / ใบเสร็จรับเงิน (Receipt)',
                'address': 'ที่อยู่',
                'phone': 'โทร',
                'time': 'เวลา',
                'tax_number': 'เลขประจำตัวผู้เสียภาษี',
                'license': 'ใบอนุญาตเลขที่',
                'receipt_no': 'เลขที่/No.',
                'website': 'เว็บไซต์',
                'branch_code': 'Branch Code',
                'business_group': 'Business Group No',
                'transaction_date': 'Transaction Date',
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
                'customer_name': 'Customer Name',
                'customer_id': 'ID Number',
                'country': 'Country/Region',
                'country_code': 'Country/Region',
                'customer_address': 'Contact Address',
                'denomination_details': 'Denomination Details',
                'transaction_summary': 'Transaction Summary',
                'denomination': 'Denomination',
                'type': 'Type',
                'quantity': 'Quantity',
                'direction': 'Direction',
                'subtotal': 'Subtotal',
                'rate': 'Rate',
                'bill': 'Bill',
                'coin': 'Coin',
                'buy': 'Buy',
                'sell': 'Sell',
                'operator': 'Operator',
                'remarks': 'Remarks',
                'customer_signature': 'Customer Signature',
                'teller_signature': 'Teller Signature',
                'date': 'Date',
                'notice': 'Notice:\n1. Please verify transaction details.\n2. Keep this receipt as transaction proof.\n3. For inquiries, provide business group number.'
            },
            'th': {
                'title': 'Statement of Currency Exchange / ใบเสร็จรับเงิน (Receipt)',
                'address': 'ที่อยู่',
                'phone': 'โทร',
                'time': 'เวลา',
                'tax_number': 'เลขประจำตัวผู้เสียภาษี',
                'license': 'ใบอนุญาตเลขที่',
                'receipt_no': 'เลขที่/No.',
                'website': 'เว็บไซต์',
                'branch_code': 'รหัสสาขา',
                'business_group': 'หมายเลขกลุ่มธุรกิจ',
                'transaction_date': 'วันที่ทำธุรกรรม',
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
                'customer_name': 'ชื่อลูกค้า',
                'customer_id': 'หมายเลขบัตรประชาชน',
                'country': 'ประเทศ/ภูมิภาค',
                'country_code': 'ประเทศ/ภูมิภาค',
                'customer_address': 'ที่อยู่ติดต่อ',
                'denomination_details': 'รายละเอียดธนบัตร',
                'transaction_summary': 'สรุปการทำธุรกรรม',
                'denomination': 'มูลค่า',
                'type': 'ประเภท',
                'quantity': 'จำนวน',
                'direction': 'ทิศทาง',
                'subtotal': 'รวมย่อย',
                'rate': 'อัตรา',
                'bill': 'ธนบัตร',
                'coin': 'เหรียญ',
                'buy': 'ซื้อ',
                'sell': 'ขาย',
                'operator': 'ผู้ดำเนินการ',
                'remarks': 'หมายเหตุ',
                'customer_signature': 'ลายเซ็นลูกค้า',
                'teller_signature': 'ลายเซ็นพนักงาน',
                'date': 'วันที่',
                'notice': 'หมายเหตุ:\n1. กรุณาตรวจสอบข้อมูลการทำธุรกรรม\n2. กรุณาเก็บใบเสร็จนี้เป็นหลักฐาน\n3. หากต้องการสอบถาม กรุณาแจ้งหมายเลขกลุ่มธุรกิจ'
            }
        }
        return texts.get(language, texts['zh'])

    @staticmethod
    def _get_thermal_styles(font_name):
        """获取80mm热敏纸优化的样式"""
        styles = {
            'title': ParagraphStyle(
                'Title',
                fontName=font_name,
                fontSize=14,
                alignment=1,  # CENTER
                spaceAfter=6,
                fontWeight='bold'
            ),
            'center': ParagraphStyle(
                'Center',
                fontName=font_name,
                fontSize=10,
                alignment=1,
                spaceAfter=3
            ),
            'small_center': ParagraphStyle(
                'SmallCenter',
                fontName=font_name,
                fontSize=8,
                alignment=1,
                spaceAfter=2
            ),
            'info': ParagraphStyle(
                'Info',
                fontName=font_name,
                fontSize=9,
                alignment=0,  # LEFT
                spaceAfter=2
            ),
            'section_title': ParagraphStyle(
                'SectionTitle',
                fontName=font_name,
                fontSize=10,
                alignment=1,
                spaceAfter=3,
                fontWeight='bold'
            ),
            'currency_header': ParagraphStyle(
                'CurrencyHeader',
                fontName=font_name,
                fontSize=9,
                alignment=0,
                spaceAfter=1,
                fontWeight='bold'
            ),
            'transaction_line': ParagraphStyle(
                'TransactionLine',
                fontName=font_name,
                fontSize=8,
                alignment=0,
                spaceAfter=1
            ),
            'rate_line': ParagraphStyle(
                'RateLine',
                fontName=font_name,
                fontSize=8,
                alignment=0,
                spaceAfter=1
            ),
            'separator': ParagraphStyle(
                'Separator',
                fontName=font_name,
                fontSize=8,
                alignment=1,
                spaceAfter=2
            ),
            'notice': ParagraphStyle(
                'Notice',
                fontName=font_name,
                fontSize=7,
                alignment=0,
                spaceAfter=3
            ),
            'small_info': ParagraphStyle(
                'SmallInfo',
                fontName=font_name,
                fontSize=8,
                alignment=0,
                spaceAfter=1,
                leftIndent=5*mm
            )
        }
        return styles

    @staticmethod
    def _create_denomination_table(denomination_details, font_name, texts):
        """创建面值详情表格（80mm优化）"""
        # 表头
        table_data = [
            [texts['denomination'], texts['type'], texts['quantity'], texts['direction']]
        ]

        # 添加数据行
        for item in denomination_details:
            denomination_value = f"{item.get('denomination_value', 0):,.2f}"
            denomination_type = texts.get(item.get('denomination_type', 'bill'), item.get('denomination_type', ''))
            quantity = str(item.get('quantity', 0))
            direction = texts.get(item.get('direction', 'sell'), item.get('direction', ''))

            table_data.append([denomination_value, denomination_type, quantity, direction])

        # 创建表格（80mm宽度优化）
        table = Table(table_data, colWidths=[20*mm, 15*mm, 12*mm, 15*mm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.9, 0.9, 0.9)),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ]))

        return table

    @staticmethod
    def _create_currency_summary(transactions, base_currency):
        """创建按币种的交易汇总"""
        summary = {}

        for tx in transactions:
            currency_id = tx['currency_id']
            currency_code = tx.get('currency_code', f'CUR{currency_id}')
            direction = tx.get('direction', 'sell')
            amount = abs(float(tx.get('amount', 0)))
            local_amount = abs(float(tx.get('local_amount', 0)))
            rate = float(tx.get('rate', 0))

            if currency_code not in summary:
                summary[currency_code] = {
                    'buy_amount': 0,
                    'sell_amount': 0,
                    'buy_local': 0,
                    'sell_local': 0,
                    'total_weight': 0,
                    'weighted_rate': 0
                }

            if direction == 'sell':  # 网点买入外币
                summary[currency_code]['buy_amount'] += amount
                summary[currency_code]['buy_local'] += local_amount
            else:  # 网点卖出外币
                summary[currency_code]['sell_amount'] += amount
                summary[currency_code]['sell_local'] += local_amount

            # 计算加权平均汇率
            weight = amount
            summary[currency_code]['total_weight'] += weight
            summary[currency_code]['weighted_rate'] += rate * weight

        # 计算最终的平均汇率
        for currency_code in summary:
            if summary[currency_code]['total_weight'] > 0:
                summary[currency_code]['avg_rate'] = (
                    summary[currency_code]['weighted_rate'] / summary[currency_code]['total_weight']
                )
            else:
                summary[currency_code]['avg_rate'] = 0

        return summary

    @staticmethod
    def _create_signature_section(texts, styles):
        """创建签名区域"""
        from reportlab.platypus import Table, TableStyle

        signature_data = [
            [texts['customer_signature'], texts['teller_signature']],
            ['', ''],  # 留空用于签名
            ['', ''],  # 留空用于签名
            [f"{texts['date']}:_______", f"{texts['date']}:_______"]
        ]

        signature_table = Table(signature_data, colWidths=[35*mm, 35*mm])
        signature_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), styles['info'].fontName),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, 2), [colors.white]),
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.95, 0.95, 0.95)),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))

        return signature_table

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
