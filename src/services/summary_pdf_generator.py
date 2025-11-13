#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
汇总PDF生成器
专门处理期初余额汇总单据的PDF生成
"""

import logging
import os
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from .pdf_base import PDFBase

logger = logging.getLogger(__name__)

class SummaryPDFGenerator(PDFBase):
    """汇总PDF生成器"""
    
    @staticmethod
    def generate_pdf(summary_data, file_path, language='zh'):
        """
        生成期初余额汇总PDF文件
        
        Args:
            summary_data: 汇总数据字典
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
                logger.info(f"✅ 目录创建成功: {dir_path}")
            
            # 初始化字体和样式
            font_name = SummaryPDFGenerator.init_fonts(language)
            styles = SummaryPDFGenerator.get_styles(font_name)
            
            # 创建PDF文档
            doc = SummaryPDFGenerator.create_pdf_doc(file_path)
            
            # 构建PDF内容
            story = []
            
            # 标题
            title_text = SummaryPDFGenerator._get_title_text(language)
            story.append(Paragraph(title_text['title'], styles['title']))
            story.append(Paragraph(title_text['subtitle'], styles['subtitle']))
            
            # 网点信息
            branch_name = summary_data.get('branch_name', '')
            if branch_name:
                story.append(Paragraph(branch_name, styles['branch']))
            
            story.append(Spacer(1, 15))
            
            # 基本信息表格
            basic_info_table = SummaryPDFGenerator._create_basic_info_table(summary_data, font_name, language)
            story.append(basic_info_table)
            story.append(Spacer(1, 15))
            
            # 币种余额明细标题
            detail_title = SummaryPDFGenerator._get_detail_title(language)
            story.append(Paragraph(detail_title, styles['normal']))
            story.append(Spacer(1, 8))
            
            # 币种明细表格
            detail_table = SummaryPDFGenerator._create_detail_table(summary_data, font_name, language)
            story.append(detail_table)
            story.append(Spacer(1, 20))
            
            # 签名区域
            signature_table = SummaryPDFGenerator._create_signature_table(summary_data, font_name, language)
            story.append(signature_table)
            story.append(Spacer(1, 15))
            
            # 注意事项
            notice_text = SummaryPDFGenerator._get_notice_text(language)
            story.append(Paragraph(notice_text, styles['notice']))
            
            # 生成PDF
            doc.build(story)
            
            logger.info(f"期初余额汇总PDF生成成功: {file_path} (语言: {language})")
            return True
            
        except Exception as e:
            logger.error(f"生成期初余额汇总PDF失败: {e}")
            return False
    
    @staticmethod
    def _create_basic_info_table(summary_data, font_name, language):
        """创建基本信息表格"""
        # 获取多语言基本信息标签
        basic_labels = SummaryPDFGenerator._get_basic_info_labels(language)
        
        table_data = [
            [f"{basic_labels['date']}:", summary_data.get('formatted_datetime', '')],
            [f"{basic_labels['operator']}:", summary_data.get('operator_name', '')],
            [f"{basic_labels['total_currencies']}:", f"{summary_data.get('total_currencies', 0)} {basic_labels['types']}"],
        ]
        
        # 创建表格
        table = Table(table_data, colWidths=[60*mm, 100*mm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        
        return table
    
    @staticmethod
    def _create_detail_table(summary_data, font_name, language):
        """创建币种明细表格"""
        transaction_records = summary_data.get('transaction_records', [])
        
        # 获取多语言表格标题
        table_headers = SummaryPDFGenerator._get_table_headers(language)
        
        # 表头
        detail_data = [
            [table_headers['serial_no'], table_headers['currency_code'], 
             table_headers['balance_before'], table_headers['balance_after'], 
             table_headers['adjustment_amount'], table_headers['transaction_no']]
        ]
        
        # 数据行
        for i, record in enumerate(transaction_records, 1):
            change_amount = record.get('change', 0)
            change_display = f"{'+' if change_amount >= 0 else ''}{change_amount:.2f}"
            
            detail_data.append([
                str(i),
                record.get('currency_code', ''),
                f"{record.get('old_balance', 0):.2f}",
                f"{record.get('new_balance', 0):.2f}",
                change_display,
                record.get('transaction_no', '-')
            ])
        
        # 创建明细表格
        table = Table(detail_data, colWidths=[15*mm, 20*mm, 22*mm, 22*mm, 18*mm, 40*mm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, 0), font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        return table
    
    @staticmethod
    def _create_signature_table(summary_data, font_name, language):
        """创建签名表格"""
        # 获取多语言签名标签
        signature_labels = SummaryPDFGenerator._get_signature_labels(language)
        
        table_data = [
            [f"{signature_labels['prepared']}:", '', f"{signature_labels['reviewed']}:", '', f"{signature_labels['approved']}:", '']
        ]
        
        table = Table(table_data, colWidths=[25*mm, 25*mm, 25*mm, 25*mm, 25*mm, 25*mm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        return table
    
    @staticmethod
    def _get_notice_text(language):
        """获取注意事项文本"""
        if language == 'zh':
            return """
            <b>注意事项 / Notice:</b><br/>
            1. 此凭证为期初余额设置有效凭据，请妥善保管。<br/>
            2. 如有疑问请及时联系相关部门。<br/>
            1. This is valid proof of initial balance setting. Please keep it safe.<br/>
            2. Contact relevant department if any questions.
            """
        elif language == 'en':
            return """
            <b>Notice:</b><br/>
            1. This is valid proof of initial balance setting. Please keep it safe.<br/>
            2. Contact relevant department if any questions.
            """
        elif language == 'th':
            return """
            <b>ข้อสังเกต / Notice:</b><br/>
            1. นี่คือหลักฐานที่ถูกต้องของการตั้งค่ายอดเริ่มต้น โปรดรับรองความปลอดภัย<br/>
            2. ติดต่อแผนกที่เกี่ยวข้องหากมีคำถาม
            """
        else:
            return """
            <b>注意事项 / Notice:</b><br/>
            1. 此凭证为期初余额设置有效凭据，请妥善保管。<br/>
            2. 如有疑问请及时联系相关部门。<br/>
            1. This is valid proof of initial balance setting. Please keep it safe.<br/>
            2. Contact relevant department if any questions.
            """
    
    @staticmethod
    def _get_title_text(language):
        """获取标题文本"""
        if language == 'zh':
            return {'title': '期初余额设置汇总单', 'subtitle': 'INITIAL BALANCE SETTING SUMMARY'}
        elif language == 'en':
            return {'title': 'Initial Balance Setting Summary', 'subtitle': 'INITIAL BALANCE SETTING SUMMARY'}
        elif language == 'th':
            return {'title': 'สรุปยอดเริ่มต้นการตั้งค่า', 'subtitle': 'สรุปยอดเริ่มต้นการตั้งค่า'}
        else:
            return {'title': '期初余额设置汇总单', 'subtitle': 'INITIAL BALANCE SETTING SUMMARY'}
    
    @staticmethod
    def _get_detail_title(language):
        """获取币种余额明细标题"""
        if language == 'zh':
            return '币种余额明细 / Currency Balance Details:'
        elif language == 'en':
            return 'Currency Balance Details:'
        elif language == 'th':
            return 'รายละเอียดยอดคงเหลือสกุลเงิน:'
        else:
            return '币种余额明细 / Currency Balance Details:'
    
    @staticmethod
    def _get_table_headers(language):
        """获取表格标题"""
        headers = {
            'zh': {
                'serial_no': '序号',
                'currency_code': '币种代码',
                'balance_before': '调整前余额',
                'balance_after': '调整后余额',
                'adjustment_amount': '调整金额',
                'transaction_no': '交易编号'
            },
            'en': {
                'serial_no': 'No.',
                'currency_code': 'Currency',
                'balance_before': 'Before',
                'balance_after': 'After',
                'adjustment_amount': 'Amount',
                'transaction_no': 'Txn No.'
            },
            'th': {
                'serial_no': 'ลำดับ',
                'currency_code': 'สกุลเงิน',
                'balance_before': 'ก่อน',
                'balance_after': 'หลัง',
                'adjustment_amount': 'จำนวน',
                'transaction_no': 'เลขที่'
            }
        }
        return headers.get(language, headers['zh'])
    
    @staticmethod
    def _get_signature_labels(language):
        """获取签名标签"""
        labels = {
            'zh': {
                'prepared': '制单/Prepared',
                'reviewed': '复核/Reviewed',
                'approved': '批准/Approved'
            },
            'en': {
                'prepared': 'Prepared',
                'reviewed': 'Reviewed',
                'approved': 'Approved'
            },
            'th': {
                'prepared': 'จัดทำ',
                'reviewed': 'ตรวจสอบ',
                'approved': 'อนุมัติ'
            }
        }
        return labels.get(language, labels['zh'])
    
    @staticmethod
    def _get_basic_info_labels(language):
        """获取基本信息标签"""
        labels = {
            'zh': {
                'date': '设置日期/Date',
                'operator': '操作员/Operator',
                'total_currencies': '币种总数/Total Currencies',
                'types': '种'
            },
            'en': {
                'date': 'Date',
                'operator': 'Operator',
                'total_currencies': 'Total Currencies',
                'types': 'types'
            },
            'th': {
                'date': 'วันที่ตั้งค่า',
                'operator': 'ผู้ดำเนินการ',
                'total_currencies': 'จำนวนสกุลเงินทั้งหมด',
                'types': 'ประเภท'
            }
        }
        return labels.get(language, labels['zh']) 