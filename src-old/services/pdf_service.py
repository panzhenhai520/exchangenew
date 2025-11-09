#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PDF票据生成服务 - 增强版
用于生成兑换交易的PDF票据（支持数据库个性化设置）
基于备份版本的成功经验进行改进
"""

import os
import logging
from datetime import datetime, date
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, BaseDocTemplate, PageTemplate, Frame
from reportlab.platypus.flowables import Flowable
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 修复导入问题
try:
    from models.exchange_models import PrintSettings
    from services.db_service import DatabaseService
except ImportError:
    # 如果导入失败，使用独立模式
    PrintSettings = None
    DatabaseService = None
    
import json
try:
    from src.services.layout_service import LayoutService
except ImportError:
    # 当从src目录内运行时的相对导入
    from services.layout_service import LayoutService

try:
    from src.services.html_pdf_service import HTMLToPDFService
except ImportError:
    # 当从src目录内运行时的相对导入
    from services.html_pdf_service import HTMLToPDFService

logger = logging.getLogger(__name__)

# 统一单位换算系统
class UnitConverter:
    """统一单位换算系统 - 确保前后端完全一致"""
    
    # PDF标准：72 DPI
    PX_TO_PT = 0.75  # 1px = 0.75pt
    PT_TO_PX = 1.333  # 1pt = 1.333px
    MM_TO_PT = 2.834645669  # 1mm = 2.834645669pt
    
    # 预览缩放比例（与前端完全一致）
    PREVIEW_SCALE = 0.75
    
    # A4纸张标准尺寸（毫米）
    A4_WIDTH_MM = 210
    A4_HEIGHT_MM = 297
    
    @classmethod
    def px_to_pt(cls, px):
        """像素转点"""
        return px * cls.PX_TO_PT
    
    @classmethod
    def pt_to_px(cls, pt):
        """点转像素"""
        return pt * cls.PT_TO_PX
    
    @classmethod
    def mm_to_pt(cls, mm):
        """毫米转点 - PDF标准转换"""
        return mm * cls.MM_TO_PT
    
    @classmethod
    def mm_to_px(cls, mm):
        """毫米转像素 - 用于前端预览"""
        return mm * cls.MM_TO_PT * cls.PT_TO_PX
    
    @classmethod
    def get_preview_size(cls, px_size):
        """获取预览尺寸（与前端预览完全一致）"""
        return px_size * cls.PREVIEW_SCALE
    
    @classmethod
    def convert_frontend_position_to_pdf(cls, position, page_height_mm=A4_HEIGHT_MM, margins=None):
        """将前端坐标转换为PDF坐标 - 关键修复函数"""
        if not position:
            return None
            
        # 获取边距信息
        margins = margins or {'top': 0, 'left': 0, 'right': 0, 'bottom': 0}
        
        # 前端坐标系：从顶部开始，单位毫米
        # PDF坐标系：从底部开始，单位点(pt)
        
        # X坐标转换：考虑左边距
        pdf_x = cls.mm_to_pt(position.get('left', 0) + margins.get('left', 0))
        
        # Y坐标转换：关键修复 - 考虑元素高度和边距
        top_mm = position.get('top', 0)
        height_mm = position.get('height', 0)
        
        # 从页面顶部的距离转换为从底部的距离
        # 考虑顶部边距和元素高度
        pdf_y = cls.mm_to_pt(page_height_mm - (top_mm + margins.get('top', 0) + height_mm))
        
        return {
            'x': pdf_x,
            'y': pdf_y,
            'width': cls.mm_to_pt(position.get('width', 0)) if position.get('width') else None,
            'height': cls.mm_to_pt(position.get('height', 0)) if position.get('height') else None
        }

# 统一字体映射系统
FONT_MAPPING = {
    'SimSun': 'SimSun',
    'SimHei': 'SimHei', 
    'KaiTi': 'KaiTi',
    'Microsoft YaHei': 'SimHei',  # 回退到SimHei
    'Arial': 'Helvetica',
    'Times New Roman': 'Times-Roman',
    'Tahoma': 'Tahoma',  # 泰语字体支持
    'Thai': 'Tahoma',    # 泰语字体别名
}

# 字体颜色转换
def hex_to_reportlab_color(hex_color):
    """将十六进制颜色转换为reportlab颜色"""
    if not hex_color or not hex_color.startswith('#'):
        return colors.black
    
    try:
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return colors.Color(r, g, b)
    except (ValueError, IndexError):
        return colors.black

class PDFReceiptService:
    """PDF单据生成服务 - 增强版支持打印设置"""
    
    # 默认打印设置 - 基于备份版本的成功配置
    DEFAULT_SETTINGS = {
        'paper_size': {'width': 210, 'height': 297, 'name': 'A4'},
        'margins': {'top': 20, 'right': 20, 'bottom': 20, 'left': 20},  # 使用备份版本的20mm边距
        'font_settings': {'family': 'SimSun', 'size': 10, 'bold': False},  # 使用备份版本的10号字体
        'header_settings': {'show_logo': True, 'show_branch_info': True, 'title_size': 16, 'title_bold': True},
        'layout_settings': {
            'line_spacing': 1.2, 
            'table_border': True, 
            'auto_page_break': True,
            'content_style': 'table'  # 新增：内容样式 - 'simple' 或 'table'
        },
        'signature_settings': {
            'signature_style': 'double',  # 'none', 'single', 'double'
            'show_date_line': True,
            'single_label': '签名/Signature',
            'left_label': '客户签名/Customer',
            'right_label': '柜员签名/Teller'
        }
    }
    
    @classmethod
    def _convert_px_to_mm(cls, px_value):
        """精确的像素到毫米转换 - 基于前端实际渲染尺寸"""
        if px_value is None:
            return 0
        
        try:
            px_value = float(px_value)
            # 重新计算转换比例：
            # 前端A4预览实际宽度约280px，对应实际210mm
            # 但需要考虑CSS缩放和边距影响
            # 经过测试，更精确的比例是：
            mm_value = px_value * 0.352778  # 1px = 25.4mm/72dpi ≈ 0.353mm
            logger.debug(f"精确坐标转换: {px_value}px -> {mm_value}mm")
            return mm_value
        except (ValueError, TypeError):
            logger.warning(f"坐标转换失败: {px_value}，使用默认值0")
            return 0
    
    @classmethod
    def _get_print_settings(cls, branch_id, document_type='exchange'):
        """获取网点的打印设置 - 使用新的布局服务"""
        logger.info(f"=== 开始获取打印设置 ===")
        logger.info(f"branch_id: {branch_id}, document_type: {document_type}")
        
        if not branch_id:
            logger.info(f"branch_id为空，使用默认打印设置")
            return cls.DEFAULT_SETTINGS
            
        try:
            # 获取默认布局名称
            logger.info(f"调用 LayoutService.get_default_layout_name({branch_id}, {document_type})")
            layout_name = LayoutService.get_default_layout_name(branch_id, document_type)
            logger.info(f"获取到布局名称: {layout_name}")
            
            # 获取布局元素配置
            logger.info(f"调用 LayoutService.get_layout_elements({branch_id}, {document_type}, {layout_name})")
            elements = LayoutService.get_layout_elements(branch_id, document_type, layout_name)
            logger.info(f"获取到元素配置数量: {len(elements) if elements else 0}")
            
            if not elements:
                logger.info(f"网点{branch_id}未配置{document_type}类型打印设置，使用默认设置")
                return cls.DEFAULT_SETTINGS
            
            # 转换为PDF服务需要的格式
            final_settings = {
                'paper_size': {
                    'width': elements.get('paper_width', 210),
                    'height': elements.get('paper_height', 297),
                    'name': 'A4',
                    'orientation': elements.get('paper_orientation', 'portrait')
                },
                'margins': {
                    'top': elements.get('margin_top', 10),
                    'right': elements.get('margin_right', 10),
                    'bottom': elements.get('margin_bottom', 10),
                    'left': elements.get('margin_left', 10)
                },
                'font_settings': {
                    'family': elements.get('font_family', 'SimSun'),
                    'size': elements.get('font_size', 12),
                    'bold': False,
                    'color': elements.get('font_color', '#000000')
                },
                'header_settings': {
                    'show_logo': elements.get('logo_show', True),
                    'show_branch_info': elements.get('branch_show', True),
                    'title_size': elements.get('title_size', 16),
                    'title_bold': elements.get('title_bold', True),
                    'logo_width': elements.get('logo_width', 120),  # 使用统一的默认值
                    'logo_height': elements.get('logo_height', 60),  # 使用统一的默认值
                    'logo_alignment': elements.get('logo_alignment', 'center'),  # 统一使用logo_alignment
                    'logo_data': elements.get('logo_data', None),  # 添加logo_data字段
                    'logo_position': 'header'
                },
                'layout_settings': {
                    'line_spacing': 1.2,
                    'table_border': elements.get('content_border', True),
                    'auto_page_break': True,
                    'content_style': elements.get('content_style', 'table')
                },
                'signature_settings': {
                    'signature_style': elements.get('signature_style', 'double'),
                    'show_date_line': True,
                    'single_label': '签名/Signature',
                    'left_label': '客户签名/Customer',
                    'right_label': '柜员签名/Teller'
                },
                'element_positions': {
                    'value': {
                        'logo': {
                            'top': cls._convert_px_to_mm(elements.get('logo_top', 5)),
                            'left': cls._convert_px_to_mm(elements.get('logo_left', 105)),
                            'width': cls._convert_px_to_mm(elements.get('logo_width', 120)),
                            'height': cls._convert_px_to_mm(elements.get('logo_height', 60)),
                            'textAlign': elements.get('logo_alignment', 'center'),
                            'visible': elements.get('logo_show', True)
                        },
                        'title': {
                            'top': cls._convert_px_to_mm(elements.get('title_top', 25)),
                            'left': cls._convert_px_to_mm(elements.get('title_left', 105)),
                            'width': cls._convert_px_to_mm(elements.get('title_width', 0)),
                            'height': cls._convert_px_to_mm(elements.get('title_height', 20)),
                            'textAlign': elements.get('title_align', 'center'),
                            'visible': elements.get('title_show', True)
                        },
                        'subtitle': {
                            'top': cls._convert_px_to_mm(elements.get('subtitle_top', 35)),
                            'left': cls._convert_px_to_mm(elements.get('subtitle_left', 105)),
                            'width': cls._convert_px_to_mm(elements.get('subtitle_width', 0)),
                            'height': cls._convert_px_to_mm(elements.get('subtitle_height', 15)),
                            'textAlign': elements.get('subtitle_align', 'center'),
                            'visible': elements.get('subtitle_show', True)
                        },
                        'branch': {
                            'top': cls._convert_px_to_mm(elements.get('branch_top', 45)),
                            'left': cls._convert_px_to_mm(elements.get('branch_left', 105)),
                            'width': cls._convert_px_to_mm(elements.get('branch_width', 0)),
                            'height': cls._convert_px_to_mm(elements.get('branch_height', 15)),
                            'textAlign': elements.get('branch_align', 'center'),
                            'visible': elements.get('branch_show', True)
                        },
                        'content': {
                            'top': cls._convert_px_to_mm(elements.get('content_top', 70)),
                            'left': cls._convert_px_to_mm(elements.get('content_left', 20)),
                            'width': cls._convert_px_to_mm(elements.get('content_width', 170)),
                            'height': cls._convert_px_to_mm(elements.get('content_height', 80)),
                            'textAlign': 'left',
                            'visible': elements.get('content_show', True)
                        },
                        'signature': {
                            'top': cls._convert_px_to_mm(elements.get('signature_top', 160)),
                            'left': cls._convert_px_to_mm(elements.get('signature_left', 20)),
                            'width': cls._convert_px_to_mm(elements.get('signature_width', 170)),
                            'height': cls._convert_px_to_mm(elements.get('signature_height', 40)),
                            'textAlign': 'center',
                            'visible': elements.get('signature_show', True)
                        },
                        'watermark': {
                            'visible': elements.get('watermark_show', False),
                            'text': elements.get('watermark_text', '样本'),
                            'opacity': elements.get('watermark_opacity', 0.1)
                        }
                    }
                }
            }
            
            logger.info(f"网点{branch_id}加载{document_type}类型布局'{layout_name}'成功")
            return final_settings
            
        except Exception as e:
            logger.error(f"获取打印设置失败: {str(e)}")
            return cls.DEFAULT_SETTINGS
    
    @classmethod
    def _get_page_size(cls, settings):
        """根据设置获取页面大小，支持纸张方向"""
        paper_config = settings.get('paper_size', cls.DEFAULT_SETTINGS['paper_size'])
        
        # 获取纸张尺寸
        width_mm = paper_config.get('width', 210)
        height_mm = paper_config.get('height', 297)
        orientation = paper_config.get('orientation', 'portrait')
        
        # 处理纸张方向
        if orientation == 'landscape':
            width_mm, height_mm = height_mm, width_mm
        
        # 转换毫米到点 (1mm = 2.834645669 points)
        width_pt = width_mm * mm
        height_pt = height_mm * mm
        
        return (width_pt, height_pt)
    
    @classmethod
    def _get_margins(cls, settings):
        """根据设置获取页边距"""
        margin_config = settings.get('margins', cls.DEFAULT_SETTINGS['margins'])
        
        return {
            'top': margin_config.get('top', 20) * mm,
            'right': margin_config.get('right', 20) * mm,
            'bottom': margin_config.get('bottom', 20) * mm,
            'left': margin_config.get('left', 20) * mm
        }
    
    @classmethod
    def _setup_fonts(cls, settings):
        """设置字体，支持颜色和样式（使用统一字体映射）"""
        font_config = settings.get('font_settings', cls.DEFAULT_SETTINGS['font_settings'])
        
        # 获取字体族设置
        font_family_setting = font_config.get('family', 'SimSun')
        
        # 使用统一字体映射
        font_family = FONT_MAPPING.get(font_family_setting, 'SimHei')
        
        # 注册中文字体
        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            
            # 检查字体是否已注册
            if font_family not in pdfmetrics.getRegisteredFontNames():
                # 尝试注册SimHei字体（黑体）
                try:
                    font_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'fonts', 'simhei.ttf')
                    if os.path.exists(font_path):
                        pdfmetrics.registerFont(TTFont('SimHei', font_path))
                        if font_family == 'SimHei':
                            logger.info(f"成功注册中文字体: SimHei")
                        else:
                            # 如果需要的字体不是SimHei，但SimHei可用，则使用SimHei作为回退
                            font_family = 'SimHei'
                            logger.info(f"字体 {font_family_setting} 不可用，回退到 SimHei")
                    else:
                        # 尝试注册Tahoma字体（支持泰语）
                        tahoma_paths = [
                            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'fonts', 'tahoma.ttf'),
                            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fonts', 'tahoma.ttf'),
                            os.path.join(os.path.dirname(__file__), '..', 'fonts', 'tahoma.ttf'),
                        ]
                        
                        tahoma_registered = False
                        for tahoma_path in tahoma_paths:
                            if os.path.exists(tahoma_path):
                                pdfmetrics.registerFont(TTFont('Tahoma', tahoma_path))
                                font_family = 'Tahoma'
                                logger.info(f"成功注册泰语字体: Tahoma from {tahoma_path}")
                                tahoma_registered = True
                                break
                        
                        if not tahoma_registered:
                            font_family = 'Helvetica'
                            logger.warning("未找到中文和泰语字体文件，使用默认字体 Helvetica")
                except Exception as font_error:
                    logger.warning(f"注册字体 {font_family} 失败: {font_error}")
                    font_family = 'Helvetica'
                
        except Exception as e:
            logger.warning(f"字体设置失败: {str(e)}")
            font_family = 'Helvetica'
        
        return font_family
    
    @classmethod
    def _add_logo(cls, story, settings, page_width):
        """添加Logo到文档，支持位置和大小设置（使用统一单位换算）"""
        header_config = settings.get('header_settings', cls.DEFAULT_SETTINGS['header_settings'])
        
        if not header_config.get('show_logo') or not header_config.get('logo_data'):
            return
        
        try:
            import base64
            from io import BytesIO
            from reportlab.platypus import Image
            
            # 解析base64图片数据
            logo_data = header_config.get('logo_data', '')
            if logo_data.startswith('data:image'):
                # 提取base64数据
                header, data = logo_data.split(',', 1)
                img_data = base64.b64decode(data)
                img_buffer = BytesIO(img_data)
                
                # 获取Logo尺寸设置（像素）
                logo_width_px = header_config.get('logo_width', 120)
                logo_height_px = header_config.get('logo_height', 60)
                logo_position = header_config.get('logo_position', 'header')
                logo_alignment = header_config.get('logo_alignment', 'center')
                
                # 使用统一的单位转换 - 直接转换为PDF点单位
                logo_width_pt = UnitConverter.px_to_pt(logo_width_px)
                logo_height_pt = UnitConverter.px_to_pt(logo_height_px)
                
                # 创建图片对象，保持纵横比
                logo_img = Image(img_buffer, width=logo_width_pt, height=logo_height_pt)
                
                # 设置图片的实际绘制尺寸
                logo_img.drawWidth = logo_width_pt
                logo_img.drawHeight = logo_height_pt
                
                # 统一对齐方式 - 与前端预览保持一致
                alignment_mapping = {
                    'center': 'CENTER',
                    'left': 'LEFT', 
                    'right': 'RIGHT',
                    'header': 'CENTER'  # header位置默认居中
                }
                logo_img.hAlign = alignment_mapping.get(logo_alignment, 'CENTER')
                
                # 添加Logo到文档
                story.append(logo_img)
                
                # 添加与前端预览一致的间距
                logo_margin = header_config.get('logo_margin', 10)
                story.append(Spacer(1, UnitConverter.px_to_pt(logo_margin)))
                
        except Exception as e:
            logger.error(f"添加Logo失败: {str(e)}")
            # 添加详细的错误信息以便调试
            import traceback
            logger.error(f"Logo处理详细错误: {traceback.format_exc()}")
    
    @classmethod
    def _add_watermark(cls, canvas, doc, settings):
        """添加水印，支持高级设置"""
        advanced_config = settings.get('advanced_settings', {})
        
        if not advanced_config.get('watermark_enabled', False):
            return
        
        try:
            watermark_text = advanced_config.get('watermark_text', '样本')
            watermark_opacity = advanced_config.get('watermark_opacity', 0.1)
            
            # 保存当前状态
            canvas.saveState()
            
            # 设置透明度和颜色
            canvas.setFillColorRGB(0.5, 0.5, 0.5, alpha=watermark_opacity)
            
            # 获取页面尺寸
            page_width = doc.pagesize[0]
            page_height = doc.pagesize[1]
            
            # 在页面中央添加旋转的水印
            canvas.translate(page_width/2, page_height/2)
            canvas.rotate(45)
            canvas.setFont('Helvetica-Bold', 60)
            canvas.drawCentredText(0, 0, watermark_text)
            
            # 恢复状态
            canvas.restoreState()
            
        except Exception as e:
            logger.error(f"添加水印失败: {str(e)}")
    
    @classmethod
    def _create_signature_section(cls, settings):
        """创建签名区域，支持详细设置（与前端预览一致）"""
        signature_config = settings.get('signature_settings', cls.DEFAULT_SETTINGS['signature_settings'])
        
        signature_style = signature_config.get('signature_style', 'double')
        if signature_style == 'none':
            return []
        
        elements = []
        show_date_line = signature_config.get('show_date_line', True)
        signature_height = signature_config.get('signature_height', 40)
        date_format = signature_config.get('date_format', 'YYYY年MM月DD日')
        
        # 获取字体设置
        font_name = cls._setup_fonts(settings)
        
        # 添加间距
        elements.append(Spacer(1, 20))
        
        if signature_style == 'single':
            # 单签名框 - 独立表格（与前端预览一致）
            single_label = signature_config.get('single_label', '签名/Signature')
            
            # 创建单个签名表格，使用下划线字符作为签名线
            signature_data = [
                ['_' * 30],  # 签名线（使用下划线字符）
                [single_label]   # 签名标签
            ]
            
            if show_date_line:
                current_date = datetime.now().strftime('%Y年%m月%d日' if 'YYYY年' in date_format else '%Y-%m-%d')
                signature_data.append([f'日期/Date: {current_date}'])
            
            signature_table = Table(signature_data, colWidths=[200])
            signature_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                # 第一行（签名线）使用等宽字体，使下划线更清晰
                ('FONTNAME', (0, 0), (0, 0), 'Courier'),
            ]))
            
            elements.append(signature_table)
            
        elif signature_style == 'double':
            # 双签名框 - 两个独立的签名区域（与前端预览一致）
            left_label = signature_config.get('left_label', '客户签名/Customer')
            right_label = signature_config.get('right_label', '柜员签名/Teller')
            
            # 创建包含两个签名框的表格，使用下划线字符作为签名线
            signature_data = [
                ['_' * 20, '_' * 20],  # 两个独立的签名线
                [left_label, right_label]  # 签名标签
            ]
            
            if show_date_line:
                current_date = datetime.now().strftime('%Y年%m月%d日' if 'YYYY年' in date_format else '%Y-%m-%d')
                signature_data.append([f'日期/Date: {current_date}', f'日期/Date: {current_date}'])
            
            # 创建双签名表格（与前端预览结构一致）
            signature_table = Table(signature_data, colWidths=[200, 200])
            signature_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                # 签名线行使用等宽字体，使下划线更清晰
                ('FONTNAME', (0, 0), (-1, 0), 'Courier'),
                # 添加左右分隔线，模拟两个独立的签名框
                ('LINEAFTER', (0, 0), (0, -1), 0.5, colors.lightgrey),
            ]))
            
            elements.append(signature_table)
        
        return elements
    
    @classmethod
    def generate_receipt_pdf(cls, data, file_path, branch_id=None, document_type='exchange', use_html_mode=False):
        """生成PDF单据 - 支持动态布局配置和HTML转PDF模式"""
        try:
            logger.info(f"开始生成PDF - 文件路径: {file_path}, 单据类型: {document_type}")
            
            # 统一使用硬编码格式（ReportLab传统布局）
            logger.info("=== 使用硬编码格式生成PDF ===")
            generation_method = "硬编码格式"
            
            # 获取打印设置 - 根据单据类型获取相应格式
            settings = cls._get_print_settings(branch_id, document_type)
            
            # 确保目录存在
            dir_path = os.path.dirname(file_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
                logger.info(f"目录创建成功: {dir_path}")
            
            # 获取页面设置
            page_size = cls._get_page_size(settings)
            margins = cls._get_margins(settings)
            font_name = cls._setup_fonts(settings)
            
            # 统一使用传统硬编码布局
            logger.info("=== 使用传统硬编码布局生成PDF ===")
            success = cls._generate_pdf_legacy(data, file_path, settings, page_size, margins, font_name, document_type)
            
            if success:
                logger.info(f"[OK] {generation_method}成功")
                logger.info(f"🎯 PDF生成方式: {generation_method}")
                return True
            else:
                logger.error(f"[ERROR] {generation_method}失败")
                return False
                
        except Exception as e:
            logger.error(f"PDF生成失败: {str(e)}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return False
    
    @classmethod
    def _has_valid_element_positions(cls, element_positions):
        """检查是否有有效的元素位置配置"""
        if not element_positions:
            return False
        
        # 处理包装在.value中的数据格式
        actual_positions = element_positions.get('value', element_positions)
        
        # 检查是否至少有基本的元素位置信息
        required_elements = ['title', 'content']
        for element in required_elements:
            if element in actual_positions and actual_positions[element].get('visible', True):
                return True
        
        return False

    @classmethod
    def _generate_pdf_with_positions(cls, data, file_path, settings, page_size, margins, font_name):
        """使用元素位置配置生成PDF"""
        from reportlab.pdfgen import canvas
        
        try:
            # 获取配置
            element_positions = settings.get('element_positions', {})
            font_config = settings.get('font_settings', cls.DEFAULT_SETTINGS['font_settings'])
            header_config = settings.get('header_settings', cls.DEFAULT_SETTINGS['header_settings'])
            layout_config = settings.get('layout_settings', cls.DEFAULT_SETTINGS['layout_settings'])
            
            # 直接使用Canvas创建PDF，避免Flowable的复杂性
            c = canvas.Canvas(file_path, pagesize=page_size)
            
            # 根据元素位置配置绘制各个元素
            cls._draw_positioned_elements(c, data, settings, font_name, page_size)
            
            # 保存PDF
            c.save()
            
            logger.info(f"动态布局PDF生成成功: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"动态布局PDF生成失败: {str(e)}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            # 回退到传统方式
            return cls._generate_pdf_legacy(data, file_path, settings, page_size, margins, font_name)

    @classmethod
    def _draw_positioned_elements(cls, canvas, data, settings, font_name, page_size):
        """在画布上绘制定位元素"""
        element_positions = settings.get('element_positions', {})
        font_config = settings.get('font_settings', cls.DEFAULT_SETTINGS['font_settings'])
        header_config = settings.get('header_settings', cls.DEFAULT_SETTINGS['header_settings'])
        
        # 处理包装在.value中的数据格式
        actual_positions = element_positions.get('value', element_positions)
        
        # 设置默认字体
        canvas.setFont(font_name, font_config.get('size', 12))
        
        # 辅助函数：统一处理visible字段（支持字符串和布尔值）
        def is_visible(element_config):
            visible = element_config.get('visible', True)
            if isinstance(visible, str):
                return visible.lower() == 'true'
            return bool(visible)
        
        # 绘制Logo
        logo_config = actual_positions.get('logo', {})
        if is_visible(logo_config) and header_config.get('show_logo', True):
            cls._draw_logo_positioned(canvas, logo_config, settings, page_size)
        
        # 绘制标题
        title_config = actual_positions.get('title', {})
        if is_visible(title_config):
            cls._draw_title_positioned(canvas, title_config, data, settings, font_name)
        
        # 绘制英文副标题
        subtitle_config = actual_positions.get('subtitle', {})
        if is_visible(subtitle_config):
            cls._draw_subtitle_positioned(canvas, subtitle_config, data, settings, font_name)
        
        # 绘制网点信息
        branch_config = actual_positions.get('branch', {})
        if is_visible(branch_config) and header_config.get('show_branch_info', True):
            cls._draw_branch_positioned(canvas, branch_config, data, settings, font_name)
        
        # 绘制内容
        content_config = actual_positions.get('content', {})
        if is_visible(content_config):
            cls._draw_content_positioned(canvas, content_config, data, settings, font_name)
        
        # 绘制签名区域
        signature_config = actual_positions.get('signature', {})
        if is_visible(signature_config):
            cls._draw_signature_positioned(canvas, signature_config, settings, font_name)

    @classmethod
    def _draw_title_positioned(cls, canvas, position, data, settings, font_name):
        """绘制定位的标题 - 使用统一坐标转换"""
        font_config = settings.get('font_settings', cls.DEFAULT_SETTINGS['font_settings'])
        header_config = settings.get('header_settings', cls.DEFAULT_SETTINGS['header_settings'])
        margins = settings.get('margins', {'top': 20, 'left': 20, 'right': 20, 'bottom': 20})
        
        # 使用统一坐标转换系统
        title_position = {
            'left': position.get('left', 105),
            'top': position.get('top', 25),
            'width': position.get('width', 0),
            'height': position.get('height', 20)  # 标题默认高度
        }
        
        pdf_pos = UnitConverter.convert_frontend_position_to_pdf(
            title_position, 
            UnitConverter.A4_HEIGHT_MM, 
            margins
        )
        
        if not pdf_pos:
            return
            
        # 字体大小：确保与前端预览一致
        font_size = header_config.get('title_size', 16)
        canvas.setFont(font_name, font_size)
        
        # 根据数据内容判断单据类型并显示相应标题
        if data.get('transaction_type') == 'REVERSAL':
            title = '交易冲正凭证'
        elif data.get('transaction_type') == 'BALANCE_ADJUSTMENT':
            title = '余额调节凭证'
        elif data.get('transaction_type') == 'INITIAL_BALANCE':
            title = '余额初始化凭证'
        elif data.get('is_eod_report'):
            title = '日结报表'
        else:
            title = '外币兑换交易凭证'
        
        # 计算文本宽度以实现对齐
        text_width = canvas.stringWidth(title, font_name, font_size)
        align = position.get('textAlign', 'center')
        
        # 对齐处理：以标题区域的中心为基准
        x = pdf_pos['x']
        if align == 'center':
            # 居中对齐：标题区域中心减去文本宽度的一半
            if pdf_pos['width']:
                x = pdf_pos['x'] + (pdf_pos['width'] - text_width) / 2
            else:
                x = pdf_pos['x'] - text_width / 2
        elif align == 'right':
            # 右对齐
            if pdf_pos['width']:
                x = pdf_pos['x'] + pdf_pos['width'] - text_width
            else:
                x = pdf_pos['x'] - text_width
        # left对齐使用默认的x坐标
        
        # Y坐标调整：文本基线位置
        y = pdf_pos['y'] + font_size * 0.3  # 调整基线位置
        
        canvas.drawString(x, y, title)

    @classmethod
    def _draw_subtitle_positioned(cls, canvas, position, data, settings, font_name):
        """绘制定位的英文副标题"""
        font_config = settings.get('font_settings', cls.DEFAULT_SETTINGS['font_settings'])
        margins = settings.get('margins', {'top': 20, 'left': 20, 'right': 20, 'bottom': 20})
        
        # 使用统一坐标转换系统
        subtitle_position = {
            'left': position.get('left', 105),
            'top': position.get('top', 35),
            'width': position.get('width', 0),
            'height': position.get('height', 15)  # 副标题默认高度
        }
        
        pdf_pos = UnitConverter.convert_frontend_position_to_pdf(
            subtitle_position, 
            UnitConverter.A4_HEIGHT_MM, 
            margins
        )
        
        if not pdf_pos:
            return
            
        # 字体大小比标题小一些
        font_size = max(font_config.get('size', 10) - 2, 8)
        canvas.setFont(font_name, font_size)
        
        # 获取英文副标题
        subtitle_map = {
            'REVERSAL': 'TRANSACTION REVERSAL RECEIPT',
            'BALANCE_ADJUSTMENT': 'BALANCE ADJUSTMENT RECEIPT',  
            'INITIAL_BALANCE': 'BALANCE INITIALIZATION RECEIPT',
            'eod_report': 'END OF DAY REPORT'
        }
        
        if data.get('is_eod_report'):
            subtitle = 'END OF DAY REPORT'
        else:
            subtitle = subtitle_map.get(data.get('transaction_type'), 'FOREIGN EXCHANGE TRANSACTION RECEIPT')
        
        # 计算文本宽度以实现对齐
        text_width = canvas.stringWidth(subtitle, font_name, font_size)
        align = position.get('textAlign', 'center')
        
        # 对齐处理
        x = pdf_pos['x']
        if align == 'center':
            if pdf_pos['width']:
                x = pdf_pos['x'] + (pdf_pos['width'] - text_width) / 2
            else:
                x = pdf_pos['x'] - text_width / 2
        elif align == 'right':
            if pdf_pos['width']:
                x = pdf_pos['x'] + pdf_pos['width'] - text_width
            else:
                x = pdf_pos['x'] - text_width
        
        # Y坐标调整：文本基线位置
        y = pdf_pos['y'] + font_size * 0.3
        
        canvas.drawString(x, y, subtitle)

    @classmethod
    def _draw_content_positioned(cls, canvas, position, data, settings, font_name):
        """绘制定位的内容区域 - 使用统一坐标转换"""
        font_config = settings.get('font_settings', cls.DEFAULT_SETTINGS['font_settings'])
        layout_config = settings.get('layout_settings', cls.DEFAULT_SETTINGS['layout_settings'])
        margins = settings.get('margins', {'top': 20, 'left': 20, 'right': 20, 'bottom': 20})
        
        # 使用统一坐标转换系统
        content_position = {
            'left': position.get('left', 20),
            'top': position.get('top', 70),
            'width': position.get('width', 170),
            'height': position.get('height', 80)
        }
        
        pdf_pos = UnitConverter.convert_frontend_position_to_pdf(
            content_position, 
            UnitConverter.A4_HEIGHT_MM, 
            margins
        )
        
        if not pdf_pos:
            return
            
        font_size = font_config.get('size', 10)
        canvas.setFont(font_name, font_size)
        
        # 根据content_style决定内容格式
        content_style = layout_config.get('content_style', 'table')
        
        if content_style == 'simple':
            # 简洁格式 - 逐行显示关键信息
            line_height = UnitConverter.mm_to_pt(font_size * 0.5)  # 转换行高为点单位
            current_y = pdf_pos['y'] + pdf_pos['height'] - line_height  # 从内容区域顶部开始
            
            lines = [
                f"交易编号: {data.get('transaction_no', '')}",
                f"交易时间: {data.get('formatted_datetime', '')}",
                f"交易金额: {data.get('from_amount', '')} {data.get('from_currency', '')}",
                f"兑换金额: {data.get('to_amount', '')} {data.get('to_currency', '')}",
                f"客户姓名: {data.get('customer_name', '')}"
            ]
            
            for line in lines:
                if current_y >= pdf_pos['y']:  # 检查是否超出区域底部
                    canvas.drawString(pdf_pos['x'], current_y, line)
                    current_y -= line_height
        else:
            # 表格格式 - 绘制表格
            cls._draw_table_positioned(canvas, pdf_pos['x'], pdf_pos['y'], pdf_pos['width'], pdf_pos['height'], data, settings, font_name)

    @classmethod
    def _draw_table_positioned(cls, canvas, x, y, width, height, data, settings, font_name):
        """绘制定位的表格 - 使用精确的坐标计算"""
        font_config = settings.get('font_settings', cls.DEFAULT_SETTINGS['font_settings'])
        layout_config = settings.get('layout_settings', cls.DEFAULT_SETTINGS['layout_settings'])
        
        font_size = font_config.get('size', 10)
        line_height = UnitConverter.mm_to_pt(font_size * 0.6)  # 使用统一单位转换
        
        # 表格数据 - 与前端预览保持完全一致
        table_data = [
            ('交易编号/No:', data.get('transaction_no', '')),
            ('交易日期/Date:', data.get('formatted_datetime', '')),
            ('交易金额/Amount:', f"{data.get('from_amount', '')} {data.get('from_currency', '')}"),
            ('兑换金额/Exchange:', f"{data.get('to_amount', '')} {data.get('to_currency', '')}"),
            ('交易汇率/Rate:', f"1 {data.get('foreign_currency', '')} = {data.get('rate', '')} {data.get('base_currency', '')}"),
            ('客户姓名/Name:', data.get('customer_name', '')),
            ('证件号码/ID:', data.get('customer_id', '')),
            ('交易用途/Purpose:', data.get('purpose', '')),
            ('备注/Remarks:', data.get('remarks', ''))
        ]
        
        # 计算列宽
        field_label_width_percent = layout_config.get('field_label_width', 40)
        label_width = width * (field_label_width_percent / 100)
        content_width = width * ((100 - field_label_width_percent) / 100)
        
        # 绘制表格 - 从表格区域顶部开始
        current_y = y + height - line_height  # 从区域顶部开始，向下绘制
        show_border = layout_config.get('table_border', True)
        
        canvas.setFont(font_name, font_size)
        
        for label, value in table_data:
            if current_y >= y:  # 检查是否超出区域底部
                # 绘制边框
                if show_border:
                    canvas.rect(x, current_y, label_width, line_height)
                    canvas.rect(x + label_width, current_y, content_width, line_height)
                
                # 绘制文本 - 调整文本基线位置
                text_y = current_y + line_height * 0.3  # 文本垂直居中
                canvas.drawString(x + UnitConverter.mm_to_pt(1), text_y, label)  # 1mm内边距
                canvas.drawString(x + label_width + UnitConverter.mm_to_pt(1), text_y, value)
                
                current_y -= line_height

    @classmethod
    def _draw_logo_positioned(cls, canvas, position, settings, page_size):
        """绘制定位的Logo - 使用统一坐标转换"""
        header_config = settings.get('header_settings', cls.DEFAULT_SETTINGS['header_settings'])
        margins = settings.get('margins', {'top': 20, 'left': 20, 'right': 20, 'bottom': 20})
        
        # 检查是否有Logo数据
        logo_data = header_config.get('logo_data')
        if not logo_data:
            logger.warning("Logo数据为空，跳过Logo绘制")
            return
        
        try:
            import base64
            from io import BytesIO
            from reportlab.lib.utils import ImageReader
            
            # 解析base64图片数据
            if logo_data.startswith('data:image'):
                # 提取base64数据
                header, data = logo_data.split(',', 1)
                img_data = base64.b64decode(data)
                img_buffer = BytesIO(img_data)
                
                # 使用统一坐标转换系统
                logo_position = {
                    'left': position.get('left', 105),
                    'top': position.get('top', 5),
                    'width': position.get('width', header_config.get('logo_width', 120)),
                    'height': position.get('height', header_config.get('logo_height', 60))
                }
                
                pdf_pos = UnitConverter.convert_frontend_position_to_pdf(
                    logo_position, 
                    UnitConverter.A4_HEIGHT_MM, 
                    margins
                )
                
                if not pdf_pos:
                    return
                
                # 根据对齐方式调整X坐标
                align = position.get('textAlign', 'center')
                x = pdf_pos['x']
                if align == 'center':
                    x = pdf_pos['x'] - pdf_pos['width'] / 2
                elif align == 'right':
                    x = pdf_pos['x'] - pdf_pos['width']
                
                # 绘制Logo
                canvas.drawImage(
                    ImageReader(img_buffer),
                    x, pdf_pos['y'],
                    width=pdf_pos['width'],
                    height=pdf_pos['height'],
                    preserveAspectRatio=True
                )
                
                logger.info(f"Logo绘制成功: 位置({x/mm:.1f}, {pdf_pos['y']/mm:.1f}), 尺寸({pdf_pos['width']/mm:.1f}x{pdf_pos['height']/mm:.1f})")
                
        except Exception as e:
            logger.error(f"绘制Logo失败: {str(e)}")
            import traceback
            logger.error(f"Logo绘制详细错误: {traceback.format_exc()}")

    @classmethod
    def _draw_branch_positioned(cls, canvas, position, data, settings, font_name):
        """绘制定位的网点信息 - 使用统一坐标转换"""
        font_config = settings.get('font_settings', cls.DEFAULT_SETTINGS['font_settings'])
        margins = settings.get('margins', {'top': 20, 'left': 20, 'right': 20, 'bottom': 20})
        
        # 使用统一坐标转换系统
        branch_position = {
            'left': position.get('left', 105),
            'top': position.get('top', 45),
            'width': position.get('width', 0),
            'height': position.get('height', 15)  # 网点信息默认高度
        }
        
        pdf_pos = UnitConverter.convert_frontend_position_to_pdf(
            branch_position, 
            UnitConverter.A4_HEIGHT_MM, 
            margins
        )
        
        if not pdf_pos:
            return
            
        font_size = font_config.get('size', 10)
        canvas.setFont(font_name, font_size)
        
        branch_info = f"{data.get('branch_name', '')}({data.get('branch_code', '')})"
        
        # 计算文本宽度以实现对齐
        text_width = canvas.stringWidth(branch_info, font_name, font_size)
        align = position.get('textAlign', 'center')
        
        # 对齐处理
        x = pdf_pos['x']
        if align == 'center':
            if pdf_pos['width']:
                x = pdf_pos['x'] + (pdf_pos['width'] - text_width) / 2
            else:
                x = pdf_pos['x'] - text_width / 2
        elif align == 'right':
            if pdf_pos['width']:
                x = pdf_pos['x'] + pdf_pos['width'] - text_width
            else:
                x = pdf_pos['x'] - text_width
        
        # Y坐标调整：文本基线位置
        y = pdf_pos['y'] + font_size * 0.3
        
        canvas.drawString(x, y, branch_info)

    @classmethod
    def _draw_signature_positioned(cls, canvas, position, settings, font_name):
        """绘制定位的签名区域 - 使用统一坐标转换"""
        signature_config = settings.get('signature_settings', cls.DEFAULT_SETTINGS['signature_settings'])
        font_config = settings.get('font_settings', cls.DEFAULT_SETTINGS['font_settings'])
        margins = settings.get('margins', {'top': 20, 'left': 20, 'right': 20, 'bottom': 20})
        
        # 使用统一坐标转换系统
        signature_position = {
            'left': position.get('left', 20),
            'top': position.get('top', 200),
            'width': position.get('width', 170),
            'height': position.get('height', 40)
        }
        
        pdf_pos = UnitConverter.convert_frontend_position_to_pdf(
            signature_position, 
            UnitConverter.A4_HEIGHT_MM, 
            margins
        )
        
        if not pdf_pos:
            return
            
        font_size = font_config.get('size', 8)
        canvas.setFont(font_name, font_size)
        
        signature_style = signature_config.get('signature_style', 'double')
        
        # 签名框高度
        box_height = pdf_pos['height'] / 2
        
        if signature_style == 'double':
            # 双签名框
            gap = UnitConverter.mm_to_pt(2)  # 签名框之间的间隙
            box_width = (pdf_pos['width'] - gap) / 2
            
            # 左侧签名框
            canvas.rect(pdf_pos['x'], pdf_pos['y'], box_width, box_height)
            label_y = pdf_pos['y'] + box_height + UnitConverter.mm_to_pt(1)
            canvas.drawString(pdf_pos['x'] + UnitConverter.mm_to_pt(2), label_y, 
                            signature_config.get('left_label', '客户签名/Customer'))
            
            # 右侧签名框  
            right_x = pdf_pos['x'] + box_width + gap
            canvas.rect(right_x, pdf_pos['y'], box_width, box_height)
            canvas.drawString(right_x + UnitConverter.mm_to_pt(2), label_y, 
                            signature_config.get('right_label', '柜员签名/Teller'))
        elif signature_style == 'single':
            # 单签名框
            canvas.rect(pdf_pos['x'], pdf_pos['y'], pdf_pos['width'], box_height)
            label_y = pdf_pos['y'] + box_height + UnitConverter.mm_to_pt(1)
            canvas.drawString(pdf_pos['x'] + UnitConverter.mm_to_pt(2), label_y, 
                            signature_config.get('single_label', '签名/Signature'))

    @classmethod
    def _generate_pdf_legacy(cls, data, file_path, settings, page_size, margins, font_name):
        """使用传统方式生成PDF（保持向后兼容）"""
        try:
            # 创建PDF文档
            doc = SimpleDocTemplate(
                file_path,
                pagesize=page_size,
                rightMargin=margins['right'],
                leftMargin=margins['left'],
                topMargin=margins['top'],
                bottomMargin=margins['bottom']
            )
            
            # 创建内容
            story = []
            
            # 获取样式
            styles = getSampleStyleSheet()
            
            # 自定义样式
            font_config = settings.get('font_settings', cls.DEFAULT_SETTINGS['font_settings'])
            header_config = settings.get('header_settings', cls.DEFAULT_SETTINGS['header_settings'])
            layout_config = settings.get('layout_settings', cls.DEFAULT_SETTINGS['layout_settings'])
            
            # 获取对齐设置
            def get_alignment(align_str):
                if align_str == 'left':
                    return TA_LEFT
                elif align_str == 'right':
                    return TA_RIGHT
                else:
                    return TA_CENTER
            
            title_alignment = get_alignment(layout_config.get('title_alignment', 'center'))
            content_alignment = get_alignment(layout_config.get('alignment', 'left'))
            
            # 获取字体颜色设置
            title_color = hex_to_reportlab_color(header_config.get('title_color', '#000000'))
            font_color = hex_to_reportlab_color(font_config.get('color', '#000000'))
            
            # 样式定义
            title_font_size = header_config.get('title_size', 16)
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontName=font_name,
                fontSize=title_font_size,
                spaceAfter=layout_config.get('section_spacing', 12),
                alignment=title_alignment,
                textColor=title_color,
                fontWeight='bold' if header_config.get('title_bold', True) else 'normal'
            )
            
            subtitle_font_size = max(font_config.get('size', 10) - 1, 8)
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=subtitle_font_size,
                spaceAfter=layout_config.get('section_spacing', 6) // 2,
                alignment=title_alignment,
                textColor=font_color
            )
            
            normal_font_size = font_config.get('size', 10)
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=normal_font_size,
                spaceAfter=layout_config.get('section_spacing', 6) // 2,
                alignment=content_alignment,
                textColor=font_color,
                leading=normal_font_size * layout_config.get('line_spacing', 1.2)
            )
            
            # 构建PDF内容
            
            # 1. Logo显示（如果启用）
            cls._add_logo(story, settings, page_size[0])
            
            # 2. 标题（中英双语）
            story.append(Paragraph("外币兑换交易凭证", title_style))
            story.append(Paragraph("FOREIGN EXCHANGE TRANSACTION RECEIPT", subtitle_style))
            
            # 3. 网点信息
            if header_config.get('show_branch_info', True):
                branch_info = f"{data.get('branch_name', '')}({data.get('branch_code', '')}) "
                branch_info += f"{data.get('transaction_type_desc', '')} {data.get('currency_code', '')}"
                story.append(Paragraph(branch_info, subtitle_style))
                story.append(Spacer(1, layout_config.get('section_spacing', 12)))
            
            # 4. 内容区域
            layout_style = layout_config.get('content_style', 'table')
            
            if layout_style == 'simple':
                # 简洁格式
                story.append(Paragraph(data.get('transaction_no', ''), normal_style))
                story.append(Spacer(1, 6))
                story.append(Paragraph(data.get('formatted_datetime', ''), normal_style))
                story.append(Spacer(1, 6))
                story.append(Paragraph(f"{data.get('from_amount', '')} {data.get('from_currency', '')}", normal_style))
                story.append(Spacer(1, 20))
            else:
                # 表格格式
                table_data = [
                    ['交易编号/No:', data.get('transaction_no', '')],
                    ['交易日期/Date:', data.get('formatted_datetime', '')],
                    ['交易金额/Amount:', f"{data.get('from_amount', '')} {data.get('from_currency', '')}"],
                    ['兑换金额/Exchange:', f"{data.get('to_amount', '')} {data.get('to_currency', '')}"],
                    ['交易汇率/Rate:', f"1 {data.get('foreign_currency', '')} = {data.get('rate', '')} {data.get('base_currency', '')}"],
                    ['客户姓名/Name:', data.get('customer_name', '')],
                ]
                
                # 添加可选字段
                if data.get('customer_id'):
                    table_data.append(['证件号码/ID:', data.get('customer_id', '')])
                
                if data.get('purpose'):
                    table_data.append(['交易用途/Purpose:', data.get('purpose', '')])
                
                if data.get('remarks'):
                    table_data.append(['备注/Remarks:', data.get('remarks', '')])
                
                # 创建表格
                field_label_width_percent = layout_config.get('field_label_width', 40)
                total_width = 160 * mm
                label_width = total_width * (field_label_width_percent / 100)
                content_width = total_width * ((100 - field_label_width_percent) / 100)
                
                table = Table(table_data, colWidths=[label_width, content_width])
                
                # 表格样式
                table_style = [
                    ('FONTNAME', (0, 0), (-1, -1), font_name),
                    ('FONTSIZE', (0, 0), (-1, -1), font_config.get('size', 10)),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ]
                
                # 根据设置决定是否添加表格边框
                if layout_config.get('table_border', True):
                    table_style.append(('GRID', (0, 0), (-1, -1), 0.5, colors.black))
                
                table.setStyle(TableStyle(table_style))
                story.append(table)
                story.append(Spacer(1, 20))
            
            # 5. 签名区域
            signature_elements = cls._create_signature_section(settings)
            story.extend(signature_elements)
            
            # 6. 注意事项
            notice_style = ParagraphStyle(
                'Notice',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=8,
                spaceAfter=3,
                alignment=TA_CENTER
            )
            
            story.append(Paragraph("注：此凭证为交易有效凭据，请妥善保管。", notice_style))
            story.append(Paragraph("Note: This is valid proof of transaction. Please keep it safe.", notice_style))
            
            # 7. 页脚
            story.append(Spacer(1, 10))
            footer_text = f"打印时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=8,
                alignment=TA_RIGHT
            )
            story.append(Paragraph(footer_text, footer_style))
            
            # 生成PDF
            doc.build(story)
            
            logger.info(f"传统布局PDF生成成功: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"传统布局PDF生成失败: {str(e)}")
            return False
    
    @classmethod
    def get_receipt_file_path(cls, transaction_no, transaction_date):
        """生成PDF文件路径 - 修改为生成到src/receipts目录下"""
        try:
            # 确保 transaction_date 是 date 对象
            if isinstance(transaction_date, str):
                transaction_date = datetime.strptime(transaction_date, '%Y-%m-%d').date()
            elif isinstance(transaction_date, datetime):
                transaction_date = transaction_date.date()
            
            # 构建文件路径 - 生成到src/receipts目录下
            # 从services目录出发：services -> src -> receipts
            file_path = os.path.join(
                os.path.dirname(__file__), '..', 'receipts',  # 相对于当前脚本的路径
                str(transaction_date.year), 
                f"{transaction_date.month:02d}", 
                f"{transaction_no}.pdf"
            )
            
            return os.path.abspath(file_path)  # 返回绝对路径
            
        except Exception as e:
            logger.error(f"生成文件路径失败: {str(e)}")
            # 返回一个默认路径 - 也生成到src/receipts目录下
            file_path = os.path.join(
                os.path.dirname(__file__), '..', 'receipts', 
                'default', f"{transaction_no}.pdf"
            )
            return os.path.abspath(file_path)
    
    @classmethod
    def generate_summary_pdf(cls, data, file_path, branch_id=None):
        """生成初始化余额汇总PDF（格式与浏览器打印预览完全一致）"""
        try:
            logger.info(f"开始生成汇总PDF - 文件路径: {file_path}")
            
            # 获取打印设置
            settings = cls._get_print_settings(branch_id, 'balance_summary')
            
            # 确保目录存在
            dir_path = os.path.dirname(file_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
                logger.info(f"目录创建成功: {dir_path}")
            
            # 获取页面设置
            page_size = cls._get_page_size(settings)
            margins = cls._get_margins(settings)
            font_name = cls._setup_fonts(settings)
            
            # 创建PDF文档
            doc = SimpleDocTemplate(
                file_path,
                pagesize=page_size,
                rightMargin=margins['right'],
                leftMargin=margins['left'],
                topMargin=margins['top'],
                bottomMargin=margins['bottom']
            )
            
            # 创建内容
            story = []
            
            # 获取样式
            styles = getSampleStyleSheet()
            
            # 自定义样式
            font_config = settings.get('font_settings', cls.DEFAULT_SETTINGS['font_settings'])
            header_config = settings.get('header_settings', cls.DEFAULT_SETTINGS['header_settings'])
            
            # 标题样式
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontName=font_name,
                fontSize=header_config.get('title_size', 16),
                spaceAfter=8,
                alignment=TA_CENTER
            )
            
            # 副标题样式
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=font_config.get('size', 10),
                spaceAfter=4,
                alignment=TA_CENTER
            )
            
            # 网点信息样式
            branch_style = ParagraphStyle(
                'BranchStyle',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=9,
                spaceAfter=10,
                alignment=TA_CENTER
            )
            
            # 构建初始化余额汇总PDF内容（与浏览器打印格式完全一致）
            
            # 1. 标题（中英双语）
            story.append(Paragraph("期初余额设置汇总单", title_style))
            story.append(Paragraph("INITIAL BALANCE SETTING SUMMARY", subtitle_style))
            
            # 2. 网点信息
            if header_config.get('show_branch_info', True):
                branch_info = f"{data.get('branch_name', '')}"
                story.append(Paragraph(branch_info, branch_style))
            
            story.append(Spacer(1, 10))
            
            # 3. 基本信息表格（与浏览器格式一致）
            basic_info_data = [
                ['设置日期/Date:', data.get('formatted_datetime', '')],
                ['操作员/Operator:', data.get('operator_name', '')],
                ['币种总数/Total Currencies:', f"{data.get('total_currencies', 0)} 种"],
            ]
            
            basic_info_table = Table(basic_info_data, colWidths=[60*mm, 100*mm])
            basic_info_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), font_config.get('size', 10)),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.black),
            ]))
            
            story.append(basic_info_table)
            story.append(Spacer(1, 15))
            
            # 4. 币种余额明细标题
            detail_title_style = ParagraphStyle(
                'DetailTitle',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=font_config.get('size', 10),
                spaceAfter=8,
                alignment=TA_LEFT
            )
            story.append(Paragraph("币种余额明细 / Currency Balance Details:", detail_title_style))
            
            # 5. 币种明细表格（与浏览器格式完全一致）
            transaction_records = data.get('transaction_records', [])
            if transaction_records:
                # 表头
                detail_data = [
                    ['序号', '币种代码', '调整前余额', '调整后余额', '调整金额', '交易编号']
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
                detail_table = Table(detail_data, colWidths=[12*mm, 18*mm, 25*mm, 25*mm, 20*mm, 45*mm])
                detail_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), font_name),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('FONTNAME', (0, 0), (-1, 0), font_name),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('LEFTPADDING', (0, 0), (-1, -1), 2),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ]))
                
                story.append(detail_table)
                story.append(Spacer(1, 20))
            
            # 6. 签名区域（与浏览器格式一致）
            signature_elements = cls._create_signature_section(settings)
            story.extend(signature_elements)
            
            # 7. 注意事项
            notice_style = ParagraphStyle(
                'Notice',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=8,
                spaceAfter=3,
                alignment=TA_CENTER
            )
            
            story.append(Paragraph("注：此凭证为期初余额设置有效凭据，请妥善保管。", notice_style))
            story.append(Paragraph("Note: This is valid proof of initial balance setting. Please keep it safe.", notice_style))
            
            # 生成PDF
            doc.build(story)
            
            final_path = os.path.abspath(file_path)
            logger.info(f"汇总PDF生成成功: {final_path}")
            return True
            
        except Exception as e:
            logger.error(f"汇总PDF生成失败: {str(e)}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return False
    
    @classmethod
    def generate_balance_adjustment_pdf(cls, data, file_path, branch_id=None):
        """生成余额调节凭证PDF（格式与浏览器打印预览完全一致）"""
        try:
            logger.info(f"开始生成余额调节PDF - 文件路径: {file_path}")
            
            # 获取打印设置
            settings = cls._get_print_settings(branch_id, 'balance_adjustment')
            
            # 确保目录存在
            dir_path = os.path.dirname(file_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
                logger.info(f"目录创建成功: {dir_path}")
            
            # 获取页面设置
            page_size = cls._get_page_size(settings)
            margins = cls._get_margins(settings)
            font_name = cls._setup_fonts(settings)
            
            # 创建PDF文档
            doc = SimpleDocTemplate(
                file_path,
                pagesize=page_size,
                rightMargin=margins['right'],
                leftMargin=margins['left'],
                topMargin=margins['top'],
                bottomMargin=margins['bottom']
            )
            
            # 创建内容
            story = []
            
            # 获取样式
            styles = getSampleStyleSheet()
            
            # 自定义样式
            font_config = settings.get('font_settings', cls.DEFAULT_SETTINGS['font_settings'])
            header_config = settings.get('header_settings', cls.DEFAULT_SETTINGS['header_settings'])
            
            # 标题样式
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontName=font_name,
                fontSize=header_config.get('title_size', 16),
                spaceAfter=12,
                alignment=TA_CENTER
            )
            
            # 副标题样式
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=font_config.get('size', 10),
                spaceAfter=6,
                alignment=TA_CENTER
            )
            
            # 构建余额调节凭证内容（与浏览器打印格式完全一致）
            
            # 1. 标题（中英双语）
            story.append(Paragraph("余额调整凭证", title_style))
            story.append(Paragraph("BALANCE ADJUSTMENT RECEIPT", subtitle_style))
            
            # 2. 添加网点信息（参考外币兑换凭证格式）
            if data.get('branch_display'):
                branch_style = ParagraphStyle(
                    'BranchInfo',
                    parent=styles['Normal'],
                    fontName=font_name,
                    fontSize=font_config.get('size', 10),
                    spaceAfter=10,
                    alignment=TA_CENTER
                )
                story.append(Paragraph(data.get('branch_display', ''), branch_style))
            
            story.append(Spacer(1, 15))
            
            # 3. 交易信息表格（简洁格式，与浏览器打印一致）
            table_data = [
                ['调整编号/No:', data.get('transaction_no', '')],
                ['调整日期/Date:', data.get('adjustment_date', '')],
                ['调整时间/Time:', data.get('adjustment_time', '')],
                ['币种/Currency:', f"{data.get('currency_name', '')} ({data.get('currency_code', '')})"],
                ['调整前余额/Before:', f"{data.get('before_balance', 0):.2f}"],
                ['调整金额/Amount:', f"{'+' if data.get('adjustment_type') == 'increase' else '-'}{abs(data.get('adjustment_amount', 0)):.2f}"],
                ['调整后余额/After:', f"{data.get('after_balance', 0):.2f}"],
                ['调整原因/Reason:', data.get('reason', '')],
                ['操作员/Operator:', data.get('operator_name', '')],
            ]
            
            # 创建表格（简洁样式）
            table = Table(table_data, colWidths=[50*mm, 110*mm])
            table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), font_config.get('size', 10)),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.black),
            ]))
            
            story.append(table)
            story.append(Spacer(1, 25))
            
            # 4. 签名区域（与浏览器打印格式一致）
            signature_elements = cls._create_signature_section(settings)
            story.extend(signature_elements)
            
            # 5. 注意事项
            notice_style = ParagraphStyle(
                'Notice',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=8,
                spaceAfter=3,
                alignment=TA_CENTER
            )
            
            story.append(Paragraph("注：此凭证为余额调整有效凭据，请妥善保管。", notice_style))
            story.append(Paragraph("Note: This is valid proof of balance adjustment. Please keep it safe.", notice_style))
            
            # 生成PDF
            doc.build(story)
            
            final_path = os.path.abspath(file_path)
            logger.info(f"余额调节PDF生成成功: {final_path}")
            return True
            
        except Exception as e:
            logger.error(f"余额调节PDF生成失败: {str(e)}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return False
    
    @classmethod
    def generate_pdf_from_html(cls, html_content, file_path, branch_id=None):
        """从HTML内容生成PDF（确保与浏览器打印预览完全一致）"""
        try:
            # 首先尝试使用weasyprint
            try:
                import weasyprint
                logger.info(f"使用weasyprint从HTML生成PDF - 文件路径: {file_path}")
                
                # 确保目录存在
                dir_path = os.path.dirname(file_path)
                if dir_path:
                    os.makedirs(dir_path, exist_ok=True)
                    logger.info(f"目录创建成功: {dir_path}")
                
                # 构建完整的HTML文档
                full_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        @page {{
                            size: A4;
                            margin: 10mm;
                        }}
                        
                        body {{
                            font-family: 'SimSun', serif;
                            font-size: 12pt;
                            line-height: 1.4;
                            color: black;
                            background: white;
                            margin: 0;
                            padding: 0;
                        }}
                        
                        .receipt-container {{
                            background: white;
                            padding: 15px;
                            font-family: 'SimSun', serif;
                            font-size: 12px;
                            line-height: 1.4;
                            border: none;
                            margin: 0;
                        }}
                        
                        .text-center {{
                            text-align: center;
                        }}
                        
                        .summary-info-table {{
                            width: 100%;
                            border-collapse: collapse;
                            margin: 10px 0;
                        }}
                        
                        .summary-info-table td {{
                            padding: 3px 8px;
                            border-bottom: 1px solid black;
                            vertical-align: top;
                        }}
                        
                        .summary-info-table td:first-child {{
                            font-weight: bold;
                            width: 35%;
                        }}
                        
                        .currency-table {{
                            width: 100%;
                            border-collapse: collapse;
                            font-size: 10px;
                            margin-top: 10px;
                        }}
                        
                        .currency-table th,
                        .currency-table td {{
                            padding: 4px 2px;
                            border: 1px solid black;
                            text-align: center;
                            vertical-align: middle;
                        }}
                        
                        .currency-table th {{
                            background-color: #f5f5f5;
                            font-weight: bold;
                        }}
                        
                        .currency-table .transaction-no {{
                            font-family: 'Courier New', monospace;
                            font-size: 9px;
                        }}
                        
                        .signature-box {{
                            border: 1px solid black;
                            padding: 10px 5px;
                            margin: 5px 2px;
                            min-height: 40px;
                            text-align: center;
                        }}
                        
                        .signature-line {{
                            border-bottom: 1px solid black;
                            height: 20px;
                            margin: 3px 0;
                        }}
                        
                        .notice-section {{
                            margin-top: 15px;
                            padding-top: 10px;
                            border-top: 1px solid black;
                            text-align: center;
                            font-size: 8px;
                        }}
                        
                        .row {{
                            display: flex;
                            flex-wrap: wrap;
                        }}
                        
                        .col-6 {{
                            width: 50%;
                            padding: 0 2px;
                        }}
                        
                        .text-success {{
                            color: #28a745;
                        }}
                        
                        .text-danger {{
                            color: #dc3545;
                        }}
                        
                        h5 {{
                            font-size: 16px;
                            margin: 10px 0;
                        }}
                        
                        h6 {{
                            font-size: 12px;
                            margin: 8px 0;
                        }}
                        
                        small {{
                            font-size: 10px;
                        }}
                    </style>
                </head>
                <body>
                    {html_content}
                </body>
                </html>
                """
                
                # 使用weasyprint生成PDF
                weasyprint.HTML(string=full_html).write_pdf(file_path)
                
                final_path = os.path.abspath(file_path)
                logger.info(f"weasyprint生成PDF成功: {final_path}")
                return True
                
            except ImportError:
                logger.warning("weasyprint未安装，使用reportlab解析HTML内容生成PDF")
                pass
            
            # 回退到reportlab解析HTML内容
            return cls._generate_pdf_from_html_fallback(html_content, file_path, branch_id)
            
        except Exception as e:
            logger.error(f"从HTML生成PDF失败: {str(e)}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return False
    
    @classmethod
    def _generate_pdf_from_html_fallback(cls, html_content, file_path, branch_id=None):
        """回退方法：使用reportlab解析HTML内容生成PDF"""
        try:
            import re
            from html import unescape
            
            logger.info("使用reportlab解析HTML内容生成PDF")
            
            # 确保目录存在
            dir_path = os.path.dirname(file_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
                logger.info(f"目录创建成功: {dir_path}")
            
            # 获取打印设置
            settings = cls._get_print_settings(branch_id)
            
            # 获取页面设置
            page_size = cls._get_page_size(settings)
            margins = cls._get_margins(settings)
            font_name = cls._setup_fonts(settings)
            
            # 创建PDF文档
            doc = SimpleDocTemplate(
                file_path,
                pagesize=page_size,
                rightMargin=margins['right'],
                leftMargin=margins['left'],
                topMargin=margins['top'],
                bottomMargin=margins['bottom']
            )
            
            # 创建内容
            story = []
            
            # 获取样式
            styles = getSampleStyleSheet()
            
            # 自定义样式
            font_config = settings.get('font_settings', cls.DEFAULT_SETTINGS['font_settings'])
            header_config = settings.get('header_settings', cls.DEFAULT_SETTINGS['header_settings'])
            
            # 获取对齐设置 - 转换为reportlab常量
            def get_alignment(align_str):
                if align_str == 'left':
                    return TA_LEFT
                elif align_str == 'right':
                    return TA_RIGHT
                else:
                    return TA_CENTER
            
            title_alignment = get_alignment(settings.get('layout_settings', cls.DEFAULT_SETTINGS['layout_settings']).get('title_alignment', 'center'))
            content_alignment = get_alignment(settings.get('layout_settings', cls.DEFAULT_SETTINGS['layout_settings']).get('alignment', 'left'))
            
            # 获取字体颜色设置
            title_color = hex_to_reportlab_color(header_config.get('title_color', '#000000'))
            font_color = hex_to_reportlab_color(font_config.get('color', '#000000'))
            
            # 标题样式 - 使用打印设置中的对齐方式和统一字体大小
            title_font_size = header_config.get('title_size', 16)
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontName=font_name,
                fontSize=title_font_size,  # 直接使用设置的字体大小，不缩放
                spaceAfter=layout_config.get('section_spacing', 12),
                alignment=title_alignment,
                textColor=title_color,
                fontWeight='bold' if header_config.get('title_bold', True) else 'normal'
            )
            
            # 副标题样式 - 使用打印设置中的对齐方式
            subtitle_font_size = max(font_config.get('size', 10) - 1, 8)  # 比正文小1号
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=subtitle_font_size,
                spaceAfter=layout_config.get('section_spacing', 6) // 2,
                alignment=title_alignment,
                textColor=font_color
            )
            
            # 正文样式 - 使用打印设置中的对齐方式和字体设置
            normal_font_size = font_config.get('size', 10)
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=normal_font_size,  # 直接使用设置的字体大小
                spaceAfter=layout_config.get('section_spacing', 6) // 2,
                alignment=content_alignment,
                textColor=font_color,
                leading=normal_font_size * layout_config.get('line_spacing', 1.2)  # 设置行高
            )
            
            # 解析HTML内容
            # 提取标题
            title_match = re.search(r'<h5[^>]*>(.*?)</h5>', html_content, re.DOTALL)
            if title_match:
                title_text = unescape(re.sub(r'<[^>]+>', '', title_match.group(1)).strip())
                story.append(Paragraph(title_text, title_style))
            
            # 提取副标题
            subtitle_match = re.search(r'<small[^>]*>(.*?)</small>', html_content, re.DOTALL)
            if subtitle_match:
                subtitle_text = unescape(re.sub(r'<[^>]+>', '', subtitle_match.group(1)).strip())
                story.append(Paragraph(subtitle_text, subtitle_style))
            
            # 提取网点信息
            branch_match = re.search(r'<div class="small mt-1"[^>]*>(.*?)</div>', html_content, re.DOTALL)
            if branch_match:
                branch_text = unescape(re.sub(r'<[^>]+>', '', branch_match.group(1)).strip())
                story.append(Paragraph(branch_text, subtitle_style))
            
            story.append(Spacer(1, 10))
            
            # 解析基本信息表格
            basic_info_pattern = r'<table class="summary-info-table[^"]*"[^>]*>(.*?)</table>'
            basic_info_match = re.search(basic_info_pattern, html_content, re.DOTALL)
            if basic_info_match:
                table_html = basic_info_match.group(1)
                rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL)
                
                table_data = []
                for row in rows:
                    cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                    if cells:
                        cell_texts = [unescape(re.sub(r'<[^>]+>', '', cell).strip()) for cell in cells]
                        table_data.append(cell_texts)
                
                if table_data:
                    basic_info_table = Table(table_data, colWidths=[60*mm, 100*mm])
                    basic_info_table.setStyle(TableStyle([
                        ('FONTNAME', (0, 0), (-1, -1), font_name),
                        ('FONTSIZE', (0, 0), (-1, -1), font_config.get('size', 10)),
                        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 6),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.black),
                    ]))
                    story.append(basic_info_table)
                    story.append(Spacer(1, 15))
            
            # 提取币种明细标题
            detail_title_match = re.search(r'<h6[^>]*>(.*?)</h6>', html_content, re.DOTALL)
            if detail_title_match:
                detail_title_text = unescape(re.sub(r'<[^>]+>', '', detail_title_match.group(1)).strip())
                story.append(Paragraph(detail_title_text, normal_style))
            
            # 解析币种明细表格
            currency_table_pattern = r'<table class="currency-table[^"]*"[^>]*>(.*?)</table>'
            currency_table_match = re.search(currency_table_pattern, html_content, re.DOTALL)
            if currency_table_match:
                table_html = currency_table_match.group(1)
                
                # 提取表头
                thead_match = re.search(r'<thead[^>]*>(.*?)</thead>', table_html, re.DOTALL)
                tbody_match = re.search(r'<tbody[^>]*>(.*?)</tbody>', table_html, re.DOTALL)
                
                table_data = []
                
                # 处理表头
                if thead_match:
                    header_rows = re.findall(r'<tr[^>]*>(.*?)</tr>', thead_match.group(1), re.DOTALL)
                    for row in header_rows:
                        cells = re.findall(r'<th[^>]*>(.*?)</th>', row, re.DOTALL)
                        if cells:
                            cell_texts = [unescape(re.sub(r'<[^>]+>', '', cell).strip()) for cell in cells]
                            table_data.append(cell_texts)
                
                # 处理表体
                if tbody_match:
                    body_rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tbody_match.group(1), re.DOTALL)
                    for row in body_rows:
                        cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                        if cells:
                            cell_texts = [unescape(re.sub(r'<[^>]+>', '', cell).strip()) for cell in cells]
                            table_data.append(cell_texts)
                
                if table_data:
                    detail_table = Table(table_data, colWidths=[12*mm, 18*mm, 25*mm, 25*mm, 20*mm, 45*mm])
                    detail_table.setStyle(TableStyle([
                        ('FONTNAME', (0, 0), (-1, -1), font_name),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                        ('FONTNAME', (0, 0), (-1, 0), font_name),
                        ('FONTSIZE', (0, 0), (-1, 0), 9),
                        ('LEFTPADDING', (0, 0), (-1, -1), 2),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                        ('TOPPADDING', (0, 0), (-1, -1), 3),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ]))
                    story.append(detail_table)
                    story.append(Spacer(1, 20))
            
            # 添加签名区域
            signature_elements = cls._create_signature_section(settings)
            story.extend(signature_elements)
            
            # 添加注意事项
            notice_style = ParagraphStyle(
                'Notice',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=8,
                spaceAfter=3,
                alignment=TA_CENTER
            )
            
            story.append(Paragraph("注：此凭证为期初余额设置有效凭据，请妥善保管。", notice_style))
            story.append(Paragraph("Note: This is valid proof of initial balance setting. Please keep it safe.", notice_style))
            
            # 生成PDF
            doc.build(story)
            
            final_path = os.path.abspath(file_path)
            logger.info(f"reportlab解析HTML生成PDF成功: {final_path}")
            return True
            
        except Exception as e:
            logger.error(f"reportlab解析HTML生成PDF失败: {str(e)}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return False
    
    @classmethod
    def generate_eod_pdf(cls, data, file_path, branch_id=None, mode='simple'):
        """生成日结报表PDF（统一格式，支持简单和详细模式）"""
        try:
            logger.info(f"开始生成日结报表PDF - 文件路径: {file_path}, 模式: {mode}")
            
            # 获取打印设置
            settings = cls._get_print_settings(branch_id, 'eod_report')
            
            # 确保目录存在
            dir_path = os.path.dirname(file_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
                logger.info(f"目录创建成功: {dir_path}")
            
            # 获取页面设置
            page_size = cls._get_page_size(settings)
            margins = cls._get_margins(settings)
            font_name = cls._setup_fonts(settings)
            
            # 创建PDF文档
            doc = SimpleDocTemplate(
                file_path,
                pagesize=page_size,
                rightMargin=margins['right'],
                leftMargin=margins['left'],
                topMargin=margins['top'],
                bottomMargin=margins['bottom']
            )
            
            # 创建内容
            story = []
            
            # 获取样式
            styles = getSampleStyleSheet()
            
            # 自定义样式
            font_config = settings.get('font_settings', cls.DEFAULT_SETTINGS['font_settings'])
            header_config = settings.get('header_settings', cls.DEFAULT_SETTINGS['header_settings'])
            layout_config = settings.get('layout_settings', cls.DEFAULT_SETTINGS['layout_settings'])
            
            # 标题样式
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontName=font_name,
                fontSize=header_config.get('title_size', 16),
                spaceAfter=12,
                alignment=TA_CENTER
            )
            
            # 副标题样式
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=font_config.get('size', 10),
                spaceAfter=8,
                alignment=TA_CENTER
            )
            
            # 正文样式
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=font_config.get('size', 10),
                spaceAfter=6
            )
            
            # 构建日结报表PDF内容
            
            # 1. 标题（中英双语）
            mode_title = "日结报表（详细版）" if mode == 'detailed' else "日结报表（简要版）"
            mode_title_en = "END OF DAY REPORT (DETAILED)" if mode == 'detailed' else "END OF DAY REPORT (SUMMARY)"
            
            story.append(Paragraph(mode_title, title_style))
            story.append(Paragraph(mode_title_en, subtitle_style))
            
            # 2. 网点信息
            if header_config.get('show_branch_info', True):
                branch_info = f"{data.get('branch_name', '')}({data.get('branch_code', '')}) "
                branch_info += f"{data.get('transaction_type_desc', '')} {data.get('currency_code', '')}"
                story.append(Paragraph(branch_info, subtitle_style))
                story.append(Spacer(1, 12))
            
            story.append(Spacer(1, 15))
            
            # 3. 基本信息表格
            basic_info_data = [
                ['日结日期/Date:', data.get('eod_date', '')],
                ['生成时间/Generated:', data.get('generated_at', '')],
                ['操作员/Operator:', data.get('operator_name', '')],
                ['日结ID/EOD ID:', str(data.get('eod_id', ''))],
            ]
            
            basic_info_table = Table(basic_info_data, colWidths=[50*mm, 100*mm])
            basic_info_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), font_config.get('size', 10)),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.black),
            ]))
            
            story.append(basic_info_table)
            story.append(Spacer(1, 15))
            
            # 4. 交易统计汇总
            story.append(Paragraph("交易统计汇总 / Transaction Summary:", normal_style))
            
            transaction_summary_data = [
                ['总交易笔数/Total Transactions:', str(data.get('total_transactions', 0))],
                ['买入交易/Buy Transactions:', str(data.get('buy_transactions', 0))],
                ['卖出交易/Sell Transactions:', str(data.get('sell_transactions', 0))],
            ]
            
            transaction_table = Table(transaction_summary_data, colWidths=[70*mm, 80*mm])
            transaction_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), font_config.get('size', 10)),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.black),
            ]))
            
            story.append(transaction_table)
            story.append(Spacer(1, 15))
            
            # 5. 余额汇总
            balance_summary = data.get('balance_summary', [])
            if balance_summary:
                story.append(Paragraph("余额汇总 / Balance Summary:", normal_style))
                
                # 表头
                balance_data = [
                    ['币种', '期初余额', '期末余额', '理论余额', '差额', '状态']
                ]
                
                # 数据行
                for balance in balance_summary:
                    status = '✓' if balance.get('is_match', False) else '✗'
                    balance_data.append([
                        balance.get('currency_code', ''),
                        f"{balance.get('opening_balance', 0):.2f}",
                        f"{balance.get('actual_balance', 0):.2f}",
                        f"{balance.get('theoretical_balance', 0):.2f}",
                        f"{balance.get('difference', 0):.2f}",
                        status
                    ])
                
                # 创建表格
                balance_table = Table(balance_data, colWidths=[20*mm, 25*mm, 25*mm, 25*mm, 20*mm, 15*mm])
                balance_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), font_name),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('LEFTPADDING', (0, 0), (-1, -1), 2),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ]))
                
                story.append(balance_table)
                story.append(Spacer(1, 15))
            
            # 6. 交款汇总（如果有）
            cash_out_summary = data.get('cash_out_summary', [])
            if cash_out_summary:
                story.append(Paragraph("交款汇总 / Cash Out Summary:", normal_style))
                
                # 表头
                cash_out_data = [
                    ['币种', '交款金额', '剩余余额']
                ]
                
                # 数据行
                for cash_out in cash_out_summary:
                    cash_out_data.append([
                        cash_out.get('currency_code', ''),
                        f"{cash_out.get('cash_out_amount', 0):.2f}",
                        f"{cash_out.get('remaining_balance', 0):.2f}"
                    ])
                
                # 创建表格
                cash_out_table = Table(cash_out_data, colWidths=[40*mm, 40*mm, 40*mm])
                cash_out_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), font_name),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ]))
                
                story.append(cash_out_table)
                story.append(Spacer(1, 20))
            
            # 7. 签名区域
            signature_elements = cls._create_signature_section(settings)
            story.extend(signature_elements)
            
            # 8. 页脚
            footer_text = f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 模式: {mode}"
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=8,
                alignment=TA_CENTER
            )
            story.append(Paragraph(footer_text, footer_style))
            
            # 生成PDF
            doc.build(story)
            
            final_path = os.path.abspath(file_path)
            logger.info(f"日结报表PDF生成成功: {final_path}")
            return True
            
        except Exception as e:
            logger.error(f"日结报表PDF生成失败: {str(e)}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return False 