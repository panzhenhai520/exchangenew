#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
冲正交易PDF生成器
专门处理冲正交易的PDF票据生成
"""

import logging
import os
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from .pdf_base import PDFBase

logger = logging.getLogger(__name__)

class ReversalPDFGenerator(PDFBase):
    """冲正交易PDF生成器"""
    
    @staticmethod
    def generate_pdf(transaction_data, file_path, language='zh'):
        """
        生成冲正交易PDF文件
        
        Args:
            transaction_data: 交易数据字典
            file_path: PDF文件保存路径
            language: 语言代码 ('zh', 'en', 'th')
            
        Returns:
            bool: 生成是否成功
        """
        try:
            # 【修复】确保目录存在
            dir_path = os.path.dirname(file_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
                logger.info(f"[OK] 目录创建成功: {dir_path}")
            
            # 获取多语言文本
            texts = ReversalPDFGenerator._get_language_texts(language)
            
            # 初始化字体和样式
            font_name = ReversalPDFGenerator.init_fonts(language)
            styles = ReversalPDFGenerator.get_styles(font_name)
            
            # 创建PDF文档
            doc = ReversalPDFGenerator.create_pdf_doc(file_path)
            
            # 构建PDF内容
            story = []
            
            # 添加标题
            story.append(Paragraph(texts['title'], styles['title']))
            
            # 重新打印标记
            if transaction_data.get('reprint_time'):
                story.append(Paragraph(texts['reprint'].format(transaction_data['reprint_time']), styles['reprint']))
            
            # 网点信息
            branch_name = transaction_data.get('branch_name', '')
            branch_code = transaction_data.get('branch_code', '')
            if branch_name or branch_code:
                branch_info = f"{branch_name}({branch_code})"
                story.append(Paragraph(branch_info, styles['branch']))
            
            story.append(Spacer(1, 15))
            
            # 添加冲正信息表格
            table = ReversalPDFGenerator._create_reversal_table(transaction_data, font_name, texts)
            story.append(table)
            story.append(Spacer(1, 25))
            
            # 添加签名区域
            signature_table = ReversalPDFGenerator._create_signature_table(transaction_data, font_name, texts)
            story.append(signature_table)
            story.append(Spacer(1, 20))
            
            # 添加注意事项
            from reportlab.lib.styles import ParagraphStyle
            notice_style = ParagraphStyle(
                'Notice',
                parent=styles['notice'],
                spaceAfter=3,
                alignment=TA_CENTER
            )
            
            story.append(Paragraph(texts['notice'], notice_style))
            
            # 生成PDF
            doc.build(story)
            
            logger.info(f"冲正单据PDF生成成功: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"冲正单据PDF生成失败: {e}")
            return False
    
    @staticmethod
    def _get_language_texts(language):
        """获取对应语言的文本"""
        texts = {
            'zh': {
                'title': '外币兑换交易冲正凭证',
                'reprint': '【重新打印】 {}',
                'reversal_no': '冲正编号',
                'reversal_date': '冲正日期',
                'original_no': '原交易编号',
                'amount': '冲正金额',
                'reason': '冲正原因',
                'operator': '操作员',
                'customer_signature': '客户签名',
                'teller_signature': '柜员签名',
                'date': '日期',
                'notice': '注：此凭证为交易冲正有效凭据，请妥善保管。'
            },
            'en': {
                'title': 'FOREIGN EXCHANGE TRANSACTION REVERSAL RECEIPT',
                'reprint': '[REPRINT] {}',
                'reversal_no': 'Reversal No',
                'reversal_date': 'Reversal Date',
                'original_no': 'Original No',
                'amount': 'Amount',
                'reason': 'Reason',
                'operator': 'Operator',
                'customer_signature': 'Customer Signature',
                'teller_signature': 'Teller Signature',
                'date': 'Date',
                'notice': 'Note: This is valid proof of transaction reversal. Please keep it safe.'
            },
            'th': {
                'title': 'ใบเสร็จการยกเลิกธุรกรรมแลกเปลี่ยนเงินตราต่างประเทศ',
                'reprint': '[พิมพ์ซ้ำ] {}',
                'reversal_no': 'เลขที่การยกเลิก',
                'reversal_date': 'วันที่ยกเลิก',
                'original_no': 'เลขที่ธุรกรรมเดิม',
                'amount': 'จำนวนเงินที่ยกเลิก',
                'reason': 'เหตุผลการยกเลิก',
                'operator': 'ผู้ดำเนินการ',
                'customer_signature': 'ลายเซ็นลูกค้า',
                'teller_signature': 'ลายเซ็นพนักงาน',
                'date': 'วันที่',
                'notice': 'หมายเหตุ: นี่คือหลักฐานที่ถูกต้องของการยกเลิกธุรกรรม กรุณาเก็บรักษาไว้อย่างปลอดภัย'
            }
        }
        return texts.get(language, texts['zh'])  # 默认返回中文
    
    @staticmethod
    def _create_reversal_table(transaction_data, font_name, texts):
        """创建冲正信息表格"""
        table_data = [
            [f"{texts['reversal_no']}:", transaction_data.get('reversal_no', '')],
            [f"{texts['reversal_date']}:", transaction_data.get('reversal_time', '')],
            [f"{texts['original_no']}:", transaction_data.get('original_no', '')],
            [f"{texts['amount']}:", f"{transaction_data.get('amount', '')} {transaction_data.get('currency_code', '')}"],
            [f"{texts['reason']}:", transaction_data.get('reason', '')],
        ]
        
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
        # 冲正业务中，客户是原交易客户，柜员是操作冲正的柜员
        customer_name = transaction_data.get('original_customer_name', '原交易客户')
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
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.95, 0.95, 0.95)),
        ]))
        
        return signature_table 