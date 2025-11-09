#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PDF服务基础类
提供通用的字体初始化和工具方法
"""

import os
import logging
import tempfile
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)

class PDFBase:
    """PDF服务基础类"""
    
    @staticmethod
    def init_fonts(language='zh'):
        """初始化多语言字体支持"""
        try:
            # 检查字体是否已经注册，避免重复注册
            registered_font_names = pdfmetrics.getRegisteredFontNames()
            
            # 多个字体路径尝试（包括当前工作目录）
            current_dir = os.getcwd()
            
            # 尝试注册中文字体 - 优先使用系统字体
            simhei_paths = [
                # 优先使用系统字体
                'C:/Windows/Fonts/simhei.ttf',
                'C:/Windows/Fonts/SimHei.ttf',
                # 备用项目字体
                os.path.join(os.path.dirname(__file__), '..', 'fonts', 'simhei.ttf'),
                os.path.join(os.path.dirname(__file__), '..', 'fonts', 'SimHei.ttf'),
                os.path.join(os.path.dirname(__file__), '..', '..', 'fonts', 'simhei.ttf'),
                os.path.join(os.path.dirname(__file__), '..', '..', 'fonts', 'SimHei.ttf'),
                os.path.join(current_dir, 'fonts', 'simhei.ttf'),
                os.path.join(current_dir, 'src', 'fonts', 'simhei.ttf'),
            ]
            
            # 尝试注册Tahoma字体
            tahoma_paths = [
                os.path.join(os.path.dirname(__file__), '..', 'fonts', 'tahoma.ttf'),
                os.path.join(os.path.dirname(__file__), '..', 'fonts', 'Tahoma.ttf'),
                os.path.join(os.path.dirname(__file__), '..', '..', 'fonts', 'tahoma.ttf'),
                os.path.join(os.path.dirname(__file__), '..', '..', 'fonts', 'Tahoma.ttf'),
                os.path.join(current_dir, 'fonts', 'tahoma.ttf'),
                os.path.join(current_dir, 'src', 'fonts', 'tahoma.ttf'),
                # Windows系统字体路径
                'C:/Windows/Fonts/tahoma.ttf',
                'C:/Windows/Fonts/Tahoma.ttf',
            ]
            
            # 记录成功注册的字体
            available_fonts = {}
            
            # 注册中文字体（如果未注册）
            if 'SimHei' not in registered_font_names:
                for font_path in simhei_paths:
                    if os.path.exists(font_path):
                        try:
                            pdfmetrics.registerFont(TTFont('SimHei', font_path))
                            available_fonts['SimHei'] = font_path
                            logger.info(f"成功注册中文字体: {font_path}")
                            break
                        except Exception as e:
                            logger.warning(f"注册中文字体失败 {font_path}: {e}")
                            continue
            else:
                available_fonts['SimHei'] = 'already_registered'
                logger.info("SimHei字体已注册")
            
            # 注册Tahoma字体（如果未注册）
            if 'Tahoma' not in registered_font_names:
                for font_path in tahoma_paths:
                    if os.path.exists(font_path):
                        try:
                            pdfmetrics.registerFont(TTFont('Tahoma', font_path))
                            available_fonts['Tahoma'] = font_path
                            logger.info(f"成功注册Tahoma字体: {font_path}")
                            break
                        except Exception as e:
                            logger.warning(f"注册Tahoma字体失败 {font_path}: {e}")
                            continue
            else:
                available_fonts['Tahoma'] = 'already_registered'
                logger.info("Tahoma字体已注册")
            
            # 【新增】尝试注册泰文字体
            thai_font_paths = [
                # Windows系统泰文字体
                'C:/Windows/Fonts/THSarabun.ttf',
                'C:/Windows/Fonts/thsarabun.ttf',
                'C:/Windows/Fonts/THSarabunNew.ttf',
                'C:/Windows/Fonts/thsarabunnew.ttf',
                # 备用Unicode字体
                'C:/Windows/Fonts/ARIALUNI.TTF',
                'C:/Windows/Fonts/arialuni.ttf',
                # 项目字体
                os.path.join(os.path.dirname(__file__), '..', 'fonts', 'tahoma.ttf'),
                os.path.join(os.path.dirname(__file__), '..', '..', 'fonts', 'tahoma.ttf'),
            ]
            
            if 'ThaiFont' not in registered_font_names:
                for font_path in thai_font_paths:
                    if os.path.exists(font_path):
                        try:
                            pdfmetrics.registerFont(TTFont('ThaiFont', font_path))
                            available_fonts['ThaiFont'] = font_path
                            logger.info(f"成功注册泰文字体: {font_path}")
                            break
                        except Exception as e:
                            logger.warning(f"注册泰文字体失败 {font_path}: {e}")
                            continue
            else:
                available_fonts['ThaiFont'] = 'already_registered'
                logger.info("ThaiFont字体已注册")
            
            # 如果字体注册失败，尝试注册备用字体
            if 'SimHei' not in available_fonts and language == 'zh':
                # 尝试注册其他中文字体
                try:
                    # 尝试使用系统的Arial Unicode MS（如果有的话）
                    arial_unicode_paths = [
                        'C:/Windows/Fonts/ARIALUNI.TTF',
                        'C:/Windows/Fonts/arialuni.ttf',
                    ]
                    for font_path in arial_unicode_paths:
                        if os.path.exists(font_path):
                            pdfmetrics.registerFont(TTFont('ArialUnicode', font_path))
                            available_fonts['ArialUnicode'] = font_path
                            logger.info(f"成功注册备用Unicode字体: {font_path}")
                            break
                except Exception as e:
                    logger.warning(f"注册备用字体失败: {e}")
            
            # 根据语言选择合适的字体
            if language == 'zh':
                if 'SimHei' in available_fonts:
                    logger.info("选择中文字体: SimHei")
                    return 'SimHei'
                elif 'ArialUnicode' in available_fonts:
                    logger.info("选择备用Unicode字体: ArialUnicode")
                    return 'ArialUnicode'
                elif 'Tahoma' in available_fonts:
                    logger.info("降级使用Tahoma字体")
                    return 'Tahoma'
                else:
                    logger.warning("所有中文字体不可用，使用默认字体")
                    return 'Helvetica'
            elif language == 'th':
                # 【修复】泰文优先使用支持泰文的字体
                if 'ArialUnicode' in available_fonts:
                    logger.info("选择通用Unicode字体: ArialUnicode (支持中文、英文、泰文)")
                    return 'ArialUnicode'
                elif 'ThaiFont' in available_fonts:
                    logger.info("选择泰语字体: ThaiFont")
                    return 'ThaiFont'
                elif 'Tahoma' in available_fonts:
                    logger.info("选择Tahoma字体 (支持泰文)")
                    return 'Tahoma'
                elif 'SimHei' in available_fonts:
                    logger.info("降级使用SimHei字体 (不支持泰文，可能显示框框)")
                    return 'SimHei'
                else:
                    logger.warning("泰语字体不可用，使用默认字体")
                    return 'Helvetica'
            else:  # 英文或其他语言
                if 'Tahoma' in available_fonts:
                    logger.info("选择英文字体: Tahoma")
                    return 'Tahoma'
                else:
                    logger.info("使用默认英文字体: Helvetica")
                    return 'Helvetica'
            
        except Exception as e:
            logger.error(f"字体初始化完全失败: {e}，使用默认字体")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            return 'Helvetica'
    
    @staticmethod
    def create_pdf_doc(file_path):
        """创建PDF文档对象"""
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        return SimpleDocTemplate(
            file_path,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
    
    @staticmethod
    def get_styles(font_name):
        """获取常用样式"""
        styles = getSampleStyleSheet()
        
        return {
            'title': ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontName=font_name,
                fontSize=18,
                spaceAfter=12,
                alignment=TA_CENTER
            ),
            'subtitle': ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=12,
                spaceAfter=8,
                alignment=TA_CENTER
            ),
            'section_title': ParagraphStyle(
                'SectionTitle',
                parent=styles['Heading2'],
                fontName=font_name,
                fontSize=14,
                spaceAfter=10,
                alignment=TA_LEFT,
                textColor=colors.darkblue
            ),
            'branch': ParagraphStyle(
                'BranchStyle',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=10,
                spaceAfter=6,
                alignment=TA_CENTER
            ),
            'normal': ParagraphStyle(
                'NormalStyle',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=10,
                spaceAfter=6,
                alignment=TA_LEFT
            ),
            'reprint': ParagraphStyle(
                'ReprintStyle',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=10,
                spaceAfter=6,
                alignment=TA_CENTER,
                textColor=colors.red
            ),
            'notice': ParagraphStyle(
                'NoticeStyle',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=9,
                alignment=TA_LEFT
            )
        }
    
    @staticmethod
    def create_temp_file(suffix='.pdf'):
        """创建临时文件"""
        return tempfile.mktemp(suffix=suffix)
    
    @staticmethod
    def get_receipt_file_path(transaction_no, transaction_date=None, language='zh'):
        """获取票据文件路径"""
        from datetime import datetime
        
        if transaction_date is None:
            transaction_date = datetime.now()
        elif isinstance(transaction_date, str):
            try:
                transaction_date = datetime.strptime(transaction_date, '%Y-%m-%d')
            except ValueError:
                transaction_date = datetime.now()
        
        # 构建文件路径：receipts/年/月/交易编号.pdf
        year = transaction_date.strftime('%Y')
        month = transaction_date.strftime('%m')
        
        # 根据语言添加后缀
        if language == 'en':
            filename = f"{transaction_no}_en.pdf"
        elif language == 'th':
            filename = f"{transaction_no}_th.pdf"
        else:  # zh或其他语言
            filename = f"{transaction_no}.pdf"
        
        # 获取项目根目录下的receipts目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        receipts_dir = os.path.join(project_root, 'receipts', year, month)
        
        # 【修复】确保目录存在
        try:
            os.makedirs(receipts_dir, exist_ok=True)
            logger.info(f"✅ 目录创建成功: {receipts_dir}")
        except Exception as e:
            logger.error(f"❌ 目录创建失败: {receipts_dir}, 错误: {str(e)}")
        
        return os.path.join(receipts_dir, filename) 