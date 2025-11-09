#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
余额操作PDF生成器
专门处理余额调节和初始化的PDF票据生成
完全按照日结报表的方法实现多语言支持
"""

import logging
import os
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from .pdf_base import PDFBase

# 导入统一的币种翻译服务
from .currency_translation_service import CurrencyTranslationService

def get_currency_name(currency_code, language='zh'):
    """获取币种的多语言名称"""
    return CurrencyTranslationService.get_currency_name(currency_code, language)

logger = logging.getLogger(__name__)

class BalancePDFGenerator(PDFBase):
    """余额操作PDF生成器 - 完全按照日结报表方法实现"""
    
    @staticmethod
    def generate_pdf(transaction_data, file_path, balance_type, language='zh'):
        """
        生成余额操作PDF文件
        
        Args:
            transaction_data: 交易数据字典
            file_path: PDF文件保存路径
            balance_type: 余额操作类型 ('adjustment', 'initial')
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
            
            logger.info(f"【调试】BalancePDFGenerator.generate_pdf被调用 - 文件: {file_path}, 类型: {balance_type}, 语言: {language}")
            logger.info(f"【调试】交易数据: {transaction_data}")
            
            logger.info(f"开始生成余额操作PDF - 文件: {file_path}, 类型: {balance_type}, 语言: {language}")
            
            # 【关键】按照日结报表的方法初始化字体和样式
            font_name = BalancePDFGenerator.init_fonts(language)
            styles = BalancePDFGenerator.get_styles(font_name)
            
            logger.info(f"【调试】字体初始化完成: {font_name}")
            
            # 创建PDF文档
            doc = BalancePDFGenerator.create_pdf_doc(file_path)
            
            # 构建PDF内容
            story = []
            
            # 添加标题
            title_text = BalancePDFGenerator._get_title_text(balance_type, language)
            logger.info(f"【调试】标题文本: {title_text}")
            story.append(Paragraph(title_text, styles['title']))
            
            # 重新打印标记
            if transaction_data.get('reprint_time'):
                reprint_text = BalancePDFGenerator._get_reprint_text(language, transaction_data['reprint_time'])
                story.append(Paragraph(reprint_text, styles['reprint']))
            
            story.append(Spacer(1, 15))
            
            # 添加余额信息表格
            table = BalancePDFGenerator._create_balance_table(transaction_data, font_name, styles, balance_type, language)
            story.append(table)
            story.append(Spacer(1, 25))
            
            # 添加签名区域
            signature_table = BalancePDFGenerator._create_signature_table(transaction_data, font_name, styles, language)
            story.append(signature_table)
            story.append(Spacer(1, 15))
            
            # 添加注意事项
            notice_text = BalancePDFGenerator._get_notice_text(balance_type, language)
            story.append(Paragraph(notice_text, styles['notice']))
            
            # 生成PDF
            doc.build(story)
            
            logger.info(f"余额操作PDF生成成功: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"生成余额操作PDF失败: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return False
    
    @staticmethod
    def _get_title_text(balance_type, language):
        """获取标题文本"""
        if balance_type == 'adjustment':
            titles = {
                'zh': '外币余额调节凭证',
                'en': 'FOREIGN CURRENCY BALANCE ADJUSTMENT RECEIPT',
                'th': 'ใบเสร็จการปรับยอดคงเหลือเงินตราต่างประเทศ'
            }
        else:  # initial
            titles = {
                'zh': '外币期初余额设置凭证',
                'en': 'FOREIGN CURRENCY INITIAL BALANCE SETTING RECEIPT',
                'th': 'ใบเสร็จการตั้งค่ายอดคงเหลือเริ่มต้นเงินตราต่างประเทศ'
            }
        return titles.get(language, titles['zh'])
    
    @staticmethod
    def _get_reprint_text(language, reprint_time):
        """获取重新打印文本"""
        reprint_labels = {
            'zh': '重新打印',
            'en': 'Reprint',
            'th': 'พิมพ์ซ้ำ'
        }
        label = reprint_labels.get(language, reprint_labels['zh'])
        return f"【{label}】 {reprint_time}"
    
    @staticmethod
    def _create_balance_table(transaction_data, font_name, styles, balance_type, language):
        """创建余额信息表格 - 完全按照日结报表的方法"""
        table_data = [
            [f"{BalancePDFGenerator._get_text('transaction_no', language)}:", transaction_data.get('transaction_no', '')],
            [f"{BalancePDFGenerator._get_text('transaction_date', language)}:", transaction_data.get('formatted_datetime', transaction_data.get('transaction_date', ''))],
        ]
        
        # 币种信息
        currency_code = transaction_data.get('currency_code', '')
        # 【关键】使用统一的币种翻译函数
        currency_display = get_currency_name(currency_code, language)
        table_data.append([f"{BalancePDFGenerator._get_text('currency', language)}:", f"{currency_display} ({currency_code})"])
        
        # 余额信息
        balance_before = float(transaction_data.get('balance_before', 0))
        balance_after = float(transaction_data.get('balance_after', 0))
        adjustment_amount = balance_after - balance_before
        
        table_data.extend([
            [f"{BalancePDFGenerator._get_text('balance_before', language)}:", f"{balance_before:.2f} {currency_code}"],
            [f"{BalancePDFGenerator._get_text('balance_after', language)}:", f"{balance_after:.2f} {currency_code}"],
            [f"{BalancePDFGenerator._get_text('adjustment_amount', language)}:", f"{adjustment_amount:+.2f} {currency_code}"],
        ])
        
        # 调节原因
        reason = transaction_data.get('reason', '')
        if reason:
            table_data.append([f"{BalancePDFGenerator._get_text('reason', language)}:", reason])
        
        # 操作员信息
        if transaction_data.get('operator_name'):
            # 【关键】根据语言本地化操作员姓名
            operator_name = transaction_data.get('operator_name', '')
            if language == 'th' and operator_name == '系统管理员':
                operator_name = 'ผู้ดูแลระบบ'
            elif language == 'en' and operator_name == '系统管理员':
                operator_name = 'System Administrator'
            
            table_data.append([f"{BalancePDFGenerator._get_text('operator', language)}:", operator_name])
        
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
    def _get_text(key, language='zh'):
        """获取多语言文本 - 完全按照日结报表的方法"""
        text_mapping = {
            'zh': {
                'transaction_no': '交易编号',
                'transaction_date': '交易日期',
                'currency': '币种',
                'balance_before': '调节前余额',
                'balance_after': '调节后余额',
                'adjustment_amount': '变动金额',
                'reason': '调节原因',
                'operator': '操作员',
                'operator_signature': '操作员签名',
                'supervisor_signature': '主管签名',
                'date': '日期'
            },
            'en': {
                'transaction_no': 'Transaction No',
                'transaction_date': 'Transaction Date',
                'currency': 'Currency',
                'balance_before': 'Balance Before',
                'balance_after': 'Balance After',
                'adjustment_amount': 'Adjustment Amount',
                'reason': 'Reason',
                'operator': 'Operator',
                'operator_signature': 'Operator Signature',
                'supervisor_signature': 'Supervisor Signature',
                'date': 'Date'
            },
            'th': {
                'transaction_no': 'หมายเลขธุรกรรม',
                'transaction_date': 'วันที่ทำธุรกรรม',
                'currency': 'สกุลเงิน',
                'balance_before': 'ยอดคงเหลือก่อนปรับ',
                'balance_after': 'ยอดคงเหลือหลังปรับ',
                'adjustment_amount': 'จำนวนเงินที่ปรับ',
                'reason': 'เหตุผล',
                'operator': 'ผู้ดำเนินการ',
                'operator_signature': 'ลายเซ็นผู้ดำเนินการ',
                'supervisor_signature': 'ลายเซ็นผู้ดูแล',
                'date': 'วันที่'
            }
        }
        return text_mapping.get(language, text_mapping['zh']).get(key, key)
    
    @staticmethod
    def _create_signature_table(transaction_data, font_name, styles, language):
        """创建签名区域表格 - 完全按照日结报表的方法"""
        operator_name = transaction_data.get('operator_name', '')
        
        # 【关键】根据语言本地化操作员姓名
        if language == 'th' and operator_name == '系统管理员':
            operator_name = 'ผู้ดูแลระบบ'
        elif language == 'en' and operator_name == '系统管理员':
            operator_name = 'System Administrator'
        
        signature_data = [
            [BalancePDFGenerator._get_text('operator_signature', language), BalancePDFGenerator._get_text('supervisor_signature', language)],
            [operator_name, ''],  # 第一行：打印操作员姓名，主管留空
            ['', ''],  # 第二行：留空用于手写签名
            [f"{BalancePDFGenerator._get_text('date', language)}:_____________", f"{BalancePDFGenerator._get_text('date', language)}:_____________"]
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
    
    @staticmethod
    def _get_notice_text(balance_type, language):
        """获取注意事项文本"""
        if balance_type == 'adjustment':
            notices = {
                'zh': """
                <b>注意事项 / Notice:</b><br/>
                1. 余额调节操作已完成，请核对调节后余额。<br/>
                2. 本凭证请妥善保管，作为余额调节凭证。<br/>
                3. 如有疑问请及时联系相关部门。<br/>
                1. Balance adjustment operation completed, please verify the adjusted balance.<br/>
                2. Keep this receipt safely as balance adjustment proof.<br/>
                3. Contact relevant department if any questions.
                """,
                'en': """
                <b>Notice / Notice:</b><br/>
                1. Balance adjustment operation completed, please verify the adjusted balance.<br/>
                2. Keep this receipt safely as balance adjustment proof.<br/>
                3. Contact relevant department if any questions.<br/>
                1. Balance adjustment operation completed, please verify the adjusted balance.<br/>
                2. Keep this receipt safely as balance adjustment proof.<br/>
                3. Contact relevant department if any questions.
                """,
                'th': """
                <b>หมายเหตุ / Notice:</b><br/>
                1. การดำเนินการปรับยอดคงเหลือเสร็จสิ้นแล้ว กรุณาตรวจสอบยอดคงเหลือที่ปรับแล้ว<br/>
                2. กรุณาเก็บใบเสร็จนี้ไว้อย่างปลอดภัยเป็นหลักฐานการปรับยอดคงเหลือ<br/>
                3. หากมีคำถามกรุณาติดต่อแผนกที่เกี่ยวข้อง<br/>
                1. Balance adjustment operation completed, please verify the adjusted balance.<br/>
                2. Keep this receipt safely as balance adjustment proof.<br/>
                3. Contact relevant department if any questions.
                """
            }
        else:  # initial
            notices = {
                'zh': """
                <b>注意事项 / Notice:</b><br/>
                1. 期初余额设置操作已完成，请核对设置后余额。<br/>
                2. 本凭证请妥善保管，作为期初余额设置凭证。<br/>
                3. 如有疑问请及时联系相关部门。<br/>
                1. Initial balance setting operation completed, please verify the set balance.<br/>
                2. Keep this receipt safely as initial balance setting proof.<br/>
                3. Contact relevant department if any questions.
                """,
                'en': """
                <b>Notice / Notice:</b><br/>
                1. Initial balance setting operation completed, please verify the set balance.<br/>
                2. Keep this receipt safely as initial balance setting proof.<br/>
                3. Contact relevant department if any questions.<br/>
                1. Initial balance setting operation completed, please verify the set balance.<br/>
                2. Keep this receipt safely as initial balance setting proof.<br/>
                3. Contact relevant department if any questions.
                """,
                'th': """
                <b>หมายเหตุ / Notice:</b><br/>
                1. การตั้งค่ายอดคงเหลือเริ่มต้นเสร็จสิ้นแล้ว กรุณาตรวจสอบยอดคงเหลือที่ตั้งค่าแล้ว<br/>
                2. กรุณาเก็บใบเสร็จนี้ไว้อย่างปลอดภัยเป็นหลักฐานการตั้งค่ายอดคงเหลือเริ่มต้น<br/>
                3. หากมีคำถามกรุณาติดต่อแผนกที่เกี่ยวข้อง<br/>
                1. Initial balance setting operation completed, please verify the set balance.<br/>
                2. Keep this receipt safely as initial balance setting proof.<br/>
                3. Contact relevant department if any questions.
                """
            }
        return notices.get(language, notices['zh']) 