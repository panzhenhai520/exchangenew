#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
兑换交易PDF生成器
专门处理兑换交易的PDF票据生成
"""

import logging
import os
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from .pdf_base import PDFBase
from .thermal_exchange_pdf_generator import ThermalExchangePDFGenerator

logger = logging.getLogger(__name__)

class ExchangePDFGenerator(PDFBase):
    """兑换交易PDF生成器"""
    
    @staticmethod
    def generate_pdf(transaction_data, file_path, language='zh'):
        """
        生成80mm热敏打印优化的兑换交易PDF文件

        Args:
            transaction_data: 交易数据字典
            file_path: PDF文件保存路径
            language: 语言代码 ('zh', 'en', 'th')

        Returns:
            bool: 生成是否成功
        """
        try:
            # 使用新的热敏打印生成器
            return ThermalExchangePDFGenerator.generate_thermal_pdf(transaction_data, file_path, language)

        except Exception as e:
            logger.error(f"生成兑换收据PDF失败: {e}")
            return False
    
    @staticmethod
    def _get_language_texts(language):
        """获取对应语言的文本"""
        texts = {
            'zh': {
                'title': '外币兑换交易凭证',
                'transaction_no': '交易编号',
                'transaction_date': '交易日期',
                'transaction_amount': '交易金额',
                'exchange_amount': '兑换金额',
                'exchange_rate': '交易汇率',
                'customer_name': '客户姓名',
                'customer_id': '证件号码',
                'transaction_purpose': '交易用途',
                'remarks': '备注',
                'operator': '操作员',
                'customer_signature': '客户签名',
                'teller_signature': '柜员签名',
                'date': '日期',
                'notice': '<b>注意事项:</b><br/>1. 请核对交易信息，如有疑问请及时联系银行。<br/>2. 本凭证请妥善保管，作为交易凭证。<br/>3. 如需查询或投诉，请联系客服热线。'
            },
            'en': {
                'title': 'FOREIGN EXCHANGE TRANSACTION RECEIPT',
                'transaction_no': 'Transaction No',
                'transaction_date': 'Transaction Date',
                'transaction_amount': 'Transaction Amount',
                'exchange_amount': 'Exchange Amount',
                'exchange_rate': 'Exchange Rate',
                'customer_name': 'Customer Name',
                'customer_id': 'ID Number',
                'transaction_purpose': 'Transaction Purpose',
                'remarks': 'Remarks',
                'operator': 'Operator',
                'customer_signature': 'Customer Signature',
                'teller_signature': 'Teller Signature',
                'date': 'Date',
                'notice': '<b>Notice:</b><br/>1. Please verify transaction details, contact bank if any questions.<br/>2. Keep this receipt safely as transaction proof.<br/>3. For inquiries or complaints, please contact customer service.'
            },
            'th': {
                'title': 'ใบเสร็จการแลกเปลี่ยนเงินตราต่างประเทศ',
                'transaction_no': 'หมายเลขธุรกรรม',
                'transaction_date': 'วันที่ทำธุรกรรม',
                'transaction_amount': 'จำนวนเงินธุรกรรม',
                'exchange_amount': 'จำนวนเงินแลกเปลี่ยน',
                'exchange_rate': 'อัตราแลกเปลี่ยน',
                'customer_name': 'ชื่อลูกค้า',
                'customer_id': 'หมายเลขบัตรประชาชน',
                'transaction_purpose': 'วัตถุประสงค์',
                'remarks': 'หมายเหตุ',
                'operator': 'ผู้ดำเนินการ',
                'customer_signature': 'ลายเซ็นลูกค้า',
                'teller_signature': 'ลายเซ็นพนักงาน',
                'date': 'วันที่',
                'notice': '<b>หมายเหตุ:</b><br/>1. กรุณาตรวจสอบข้อมูลการทำธุรกรรม หากมีข้อสงสัยกรุณาติดต่อธนาคาร<br/>2. กรุณาเก็บใบเสร็จนี้ไว้เป็นหลักฐานการทำธุรกรรม<br/>3. หากต้องการสอบถามหรือร้องเรียน กรุณาติดต่อศูนย์บริการลูกค้า'
            }
        }
        return texts.get(language, texts['zh'])  # 默认返回中文
    
    @staticmethod
    def _create_transaction_table(transaction_data, font_name, texts):
        """创建交易信息表格"""
        table_data = [
            [f"{texts['transaction_no']}:", transaction_data.get('transaction_no', '')],
            [f"{texts['transaction_date']}:", transaction_data.get('formatted_datetime', transaction_data.get('transaction_date', ''))],
        ]
        
        # 获取本币代码（从网点信息中获取，避免硬编码CNY）
        base_currency = transaction_data.get('base_currency', 'USD')
        
        # 获取金额数据并取绝对值（打印显示不要负数）
        amount = abs(float(transaction_data.get('amount', 0)))
        local_amount = abs(float(transaction_data.get('local_amount', 0)))
        
        # 根据交易类型设置金额显示
        transaction_type = transaction_data.get('type', '')
        if transaction_type == 'sell':
            # 银行卖出外币（客户买入外币）
            # 交易金额：客户支付的本币，兑换金额：客户得到的外币
            table_data.extend([
                [f"{texts['transaction_amount']}:", f"{local_amount} {base_currency}"],
                [f"{texts['exchange_amount']}:", f"{amount} {transaction_data.get('currency_code', '')}"],
                [f"{texts['exchange_rate']}:", f"1 {transaction_data.get('currency_code', '')} = {transaction_data.get('rate', '')} {base_currency}"],
            ])
        elif transaction_type == 'buy':
            # 银行买入外币（客户卖出外币）
            # 交易金额：客户支付的外币，兑换金额：客户得到的本币
            table_data.extend([
                [f"{texts['transaction_amount']}:", f"{amount} {transaction_data.get('currency_code', '')}"],
                [f"{texts['exchange_amount']}:", f"{local_amount} {base_currency}"],
                [f"{texts['exchange_rate']}:", f"1 {transaction_data.get('currency_code', '')} = {transaction_data.get('rate', '')} {base_currency}"],
            ])
        else:
            # 通用格式
            table_data.extend([
                [f"{texts['transaction_amount']}:", f"{amount} {transaction_data.get('currency_code', '')}"],
                [f"{texts['exchange_amount']}:", f"{local_amount} {base_currency}"],
                [f"{texts['exchange_rate']}:", f"1 {transaction_data.get('currency_code', '')} = {transaction_data.get('rate', '')} {base_currency}"],
            ])
        
        # 客户信息
        table_data.append([f"{texts['customer_name']}:", transaction_data.get('customer_name', '')])
        
        # 可选信息
        if transaction_data.get('customer_id'):
            table_data.append([f"{texts['customer_id']}:", transaction_data.get('customer_id', '')])
        
        if transaction_data.get('purpose'):
            table_data.append([f"{texts['transaction_purpose']}:", transaction_data.get('purpose', '')])
        
        if transaction_data.get('remarks'):
            table_data.append([f"{texts['remarks']}:", transaction_data.get('remarks', '')])
        
        # 操作员信息
        if transaction_data.get('operator_name'):
            table_data.append([f"{texts['operator']}:", transaction_data.get('operator_name', '')])
        
        # 创建表格
        table = Table(table_data, colWidths=[65*mm, 95*mm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.95, 0.95, 0.95)),
        ]))
        
        return table
    
    @staticmethod
    def _create_signature_table(transaction_data, font_name, texts):
        """创建签名区域表格"""
        customer_name = transaction_data.get('customer_name', '')
        operator_name = transaction_data.get('operator_name', '')
        
        signature_data = [
            [texts['customer_signature'], texts['teller_signature']],
            [customer_name, operator_name],  # 第一行：打印姓名
            ['', ''],  # 第二行：留空用于手写签名
            [f"{texts['date']}:_____________", f"{texts['date']}:_____________"]
        ]
        
        signature_table = Table(signature_data, colWidths=[80*mm, 80*mm])
        signature_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, 2), [colors.white]),
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.95, 0.95, 0.95)),
        ]))
        
        return signature_table 