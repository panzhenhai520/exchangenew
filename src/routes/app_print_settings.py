from flask import Blueprint, request, jsonify
from datetime import datetime
from src.services.auth_service import token_required, has_permission
from src.services.db_service import DatabaseService
from src.models.exchange_models import PrintSettings, Branch
from src.services.layout_service import LayoutService
import json
import logging
import base64
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('app_print_settings')

# Create blueprint for print settings
print_settings_bp = Blueprint('print_settings', __name__, url_prefix='/api/print-settings')

def get_current_user_branch_id(current_user):
    """获取当前用户的网点ID"""
    if current_user and 'branch_id' in current_user:
        return current_user['branch_id']
    else:
        raise ValueError('无法获取当前用户的网点信息')

def validate_branch_access(current_user):
    """验证并获取当前用户的网点ID，如果无效则抛出异常"""
    branch_id = current_user.get('branch_id')
    if not branch_id:
        raise ValueError('无法获取当前用户的网点信息，请重新登录')
    return branch_id

@print_settings_bp.route('/templates', methods=['GET'])
@token_required
@has_permission('system_manage')
def get_print_settings(current_user):
    """获取打印设置"""
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
    
    # 获取单据类型参数
    document_type = request.args.get('document_type', 'exchange')
    layout_name = request.args.get('layout_name', 'default')
    
    try:
        # 获取可用布局列表
        layouts = LayoutService.get_layouts_by_document_type(current_user['branch_id'], document_type)
        
        # 如果没有布局，创建标准布局
        if not layouts:
            LayoutService.create_standard_layouts(current_user['branch_id'], document_type)
            layouts = LayoutService.get_layouts_by_document_type(current_user['branch_id'], document_type)
        
        # 确定要使用的布局名称
        if layout_name == 'default':
            # 查找默认布局
            default_layout = next((l for l in layouts if l.get('is_default')), None)
            if default_layout:
                layout_name = default_layout['name']
            elif layouts:
                layout_name = layouts[0]['name']
            else:
                layout_name = 'default'
        
        # 使用新的布局服务获取布局元素
        elements = LayoutService.get_layout_elements(current_user['branch_id'], document_type, layout_name)
        
        # 如果没有设置，使用默认值
        if not elements:
            settings_dict = get_default_print_settings()
        else:
            # 将扁平化的元素配置转换为前端期望的嵌套格式
            settings_dict = convert_elements_to_frontend_format(elements)
        
        return jsonify({
            'success': True,
            'document_type': document_type,
            'layout_name': layout_name,
            'settings': settings_dict
        })
        
    except Exception as e:
        logger.error(f"Get print settings failed: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

def convert_elements_to_frontend_format(elements):
    """将扁平化的元素配置转换为前端期望的嵌套格式"""
    settings_dict = {}
    
    # 纸张设置
    settings_dict['paper_size'] = {
        'value': {
            'width': elements.get('paper_width', 210),
            'height': elements.get('paper_height', 297),
            'name': elements.get('paper_name', 'A4'),
            'orientation': elements.get('paper_orientation', 'portrait')
        },
        'description': '纸张大小和方向设置（毫米）'
    }
    
    # 边距设置
    settings_dict['margins'] = {
        'value': {
            'top': elements.get('margin_top', 10),
            'right': elements.get('margin_right', 10),
            'bottom': elements.get('margin_bottom', 10),
            'left': elements.get('margin_left', 10)
        },
        'description': '页面边距设置（毫米）'
    }
    
    # 字体设置
    settings_dict['font_settings'] = {
        'value': {
            'family': elements.get('font_family', 'SimSun'),
            'size': elements.get('font_size', 12),
            'color': elements.get('font_color', '#000000'),
            'bold': elements.get('font_bold', False)
        },
        'description': '全局字体设置'
    }
    
    # 标题设置
    settings_dict['header_settings'] = {
        'value': {
            'show_logo': elements.get('logo_show', False),
            'show_branch_info': elements.get('branch_show', True),
            'title_size': elements.get('title_size', 16),
            'title_bold': elements.get('title_bold', True),
            'title_color': elements.get('title_color', '#000000'),
            'title_font_family': elements.get('title_font_family', 'SimHei'),
            'logo_width': elements.get('logo_width', 120),
            'logo_height': elements.get('logo_height', 60),
            'logo_alignment': elements.get('logo_alignment', 'center'),
            'logo_margin': elements.get('logo_margin', 10),
            'logo_data': elements.get('logo_data', None),
            'logo_position': elements.get('logo_position', 'header')
        },
        'description': '页眉和标题设置'
    }
    
    # 布局设置
    settings_dict['layout_settings'] = {
        'value': {
            'line_spacing': elements.get('line_spacing', 1.2),
            'table_border': elements.get('table_border', True),
            'auto_page_break': elements.get('auto_page_break', True),
            'content_style': elements.get('content_style', 'table'),
            'alignment': elements.get('alignment', 'left'),
            'table_alignment': elements.get('table_alignment', 'center'),
            'title_alignment': elements.get('title_alignment', 'center'),
            'row_spacing': elements.get('row_spacing', 'normal'),
            'field_label_width': elements.get('field_label_width', 40),
            'section_spacing': elements.get('section_spacing', 15),
            'show_field_labels': elements.get('show_field_labels', True)
        },
        'description': '页面布局和内容样式设置'
    }
    
    # 签名设置
    settings_dict['signature_settings'] = {
        'value': {
            'signature_style': elements.get('signature_style', 'double'),
            'show_date_line': elements.get('show_date_line', True),
            'single_label': elements.get('single_label', '签名/Signature'),
            'left_label': elements.get('left_label', '客户签名/Customer'),
            'right_label': elements.get('right_label', '柜员签名/Teller'),
            'signature_height': elements.get('signature_height', 40),
            'signature_width': elements.get('signature_width', 150),
            'date_format': elements.get('date_format', 'YYYY年MM月DD日')
        },
        'description': '签名区域设置'
    }
    
    # 高级设置
    settings_dict['advanced_settings'] = {
        'value': {
            'watermark_enabled': elements.get('watermark_enabled', False),
            'watermark_text': elements.get('watermark_text', '样本'),
            'watermark_opacity': elements.get('watermark_opacity', 0.1),
            'page_numbering': elements.get('page_numbering', False),
            'header_line': elements.get('header_line', True),
            'footer_line': elements.get('footer_line', True),
            'print_quality': elements.get('print_quality', 'high'),
            'color_mode': elements.get('color_mode', 'color')
        },
        'description': '高级打印设置'
    }
    
    # 元素位置设置 - 包装在value中以保持与其他设置一致的格式
    settings_dict['element_positions'] = {
        'value': {
            'logo': {
                'top': elements.get('logo_top', 5),
                'left': elements.get('logo_left', 10),
                'width': elements.get('logo_width', 30),
                'height': elements.get('logo_height', 30),
                'textAlign': elements.get('logo_alignment', 'center'),
                'visible': elements.get('logo_show', True),
                'fontFamily': elements.get('font_family', 'SimSun'),
                'fontSize': elements.get('font_size', 8),
                'color': elements.get('font_color', '#000000')
            },
            'title': {
                'top': elements.get('title_top', 15),
                'left': elements.get('title_left', 50),
                'width': elements.get('title_width', 110),
                'height': elements.get('title_height', 20),
                'textAlign': elements.get('title_align', 'center'),
                'visible': elements.get('title_show', True),
                'fontFamily': elements.get('title_font_family', 'SimHei'),
                'fontSize': elements.get('title_size', 12),
                'color': elements.get('title_color', '#000000')
            },
            'subtitle': {
                'top': elements.get('subtitle_top', 25),
                'left': elements.get('subtitle_left', 50),
                'width': elements.get('subtitle_width', 110),
                'height': elements.get('subtitle_height', 15),
                'textAlign': elements.get('subtitle_align', 'center'),
                'visible': elements.get('subtitle_show', True),
                'fontFamily': elements.get('subtitle_font_family', 'SimSun'),
                'fontSize': elements.get('subtitle_font_size', 10),
                'color': elements.get('subtitle_color', '#000000')
            },
            'branch': {
                'top': elements.get('branch_top', 35),
                'left': elements.get('branch_left', 50),
                'width': elements.get('branch_width', 110),
                'height': elements.get('branch_height', 15),
                'textAlign': elements.get('branch_align', 'center'),
                'visible': elements.get('branch_show', True),
                'fontFamily': elements.get('branch_font_family', 'SimSun'),
                'fontSize': elements.get('branch_font_size', 8),
                'color': elements.get('branch_color', '#000000')
            },
            'content': {
                'top': elements.get('content_top', 50),
                'left': elements.get('content_left', 10),
                'width': elements.get('content_width', 190),
                'height': elements.get('content_height', 100),
                'textAlign': 'left',
                'visible': elements.get('content_show', True),
                'fontFamily': elements.get('content_font_family', 'SimSun'),
                'fontSize': elements.get('content_font_size', 12),
                'color': elements.get('content_color', '#000000'),
                'fontWeight': elements.get('content_font_weight', 'normal')
            },
            'signature': {
                'top': elements.get('signature_top', 200),
                'left': elements.get('signature_left', 10),
                'width': elements.get('signature_width', 190),
                'height': elements.get('signature_height', 40),
                'textAlign': 'center',
                'visible': elements.get('signature_show', True),
                'fontFamily': elements.get('signature_font_family', 'SimSun'),
                'fontSize': elements.get('signature_font_size', 10),
                'color': elements.get('signature_color', '#000000'),
                'fontWeight': elements.get('signature_font_weight', 'normal')
            },
            'watermark': {
                'top': elements.get('watermark_top', 120),
                'left': elements.get('watermark_left', 80),
                'width': elements.get('watermark_width', 50),
                'height': elements.get('watermark_height', 30),
                'textAlign': 'center',
                'visible': elements.get('watermark_enabled', False),
                'fontFamily': elements.get('font_family', 'SimSun'),
                'fontSize': elements.get('watermark_font_size', 24),
                'color': '#cccccc'
            }
        },
        'description': '元素位置配置信息'
    }
    
    return settings_dict

@print_settings_bp.route('/templates', methods=['POST'])
@token_required
@has_permission('system_manage')
def save_print_settings(current_user):
    """保存打印设置"""
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
    
    data = request.get_json()
    if not data or 'settings' not in data:
        return jsonify({'success': False, 'message': '无效的请求数据'}), 400
    
    # 获取单据类型，默认为exchange
    document_type = data.get('document_type', 'exchange')
    layout_name = data.get('layout_name', '表格格式')  # 获取布局名称，默认为表格格式
    settings = data['settings']
    element_positions = data.get('elementPositions', {})  # 获取元素位置数据
    
    logger.info(f"保存设置 - 单据类型: {document_type}, 布局: {layout_name}")
    logger.info(f"元素位置数据: {element_positions}")
    
    try:
        # 将前端嵌套格式转换为扁平化的元素配置
        elements = convert_frontend_format_to_elements(settings)
        
        # 处理元素位置数据
        if element_positions:
            elements.update(convert_element_positions_to_elements(element_positions))
        
        logger.info(f"转换后的元素配置: {elements}")
        
        # 使用布局服务保存设置
        success = LayoutService.save_layout(
            branch_id=current_user['branch_id'],
            document_type=document_type,
            layout_name=layout_name,
            elements=elements,
            is_default=True  # 保持为默认布局
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': f'{document_type}类型打印设置保存成功'
            })
        else:
            return jsonify({'success': False, 'message': '保存失败'}), 500
        
    except Exception as e:
        logger.error(f"Save print settings failed: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

def convert_frontend_format_to_elements(settings):
    """将前端格式的设置转换为扁平化的元素配置"""
    elements = {}
    
    logger.info(f"转换前端格式设置: {list(settings.keys())}")
    
    # 纸张大小设置
    if 'paper_size' in settings:
        paper = settings['paper_size']['value']
        elements['paper_width'] = paper.get('width', 210)
        elements['paper_height'] = paper.get('height', 297)
        elements['paper_name'] = paper.get('name', 'A4')
        elements['paper_orientation'] = paper.get('orientation', 'portrait')
        logger.info(f"纸张设置: {paper}")
    
    # 页边距设置
    if 'margins' in settings:
        margins = settings['margins']['value']
        elements['margin_top'] = margins.get('top', 10)
        elements['margin_right'] = margins.get('right', 10)
        elements['margin_bottom'] = margins.get('bottom', 10)
        elements['margin_left'] = margins.get('left', 10)
        logger.info(f"页边距设置: {margins}")
    
    # 字体设置
    if 'font_settings' in settings:
        font = settings['font_settings']['value']
        elements['font_family'] = font.get('family', 'SimSun')
        elements['font_size'] = font.get('size', 12)
        elements['font_color'] = font.get('color', '#000000')
        elements['font_bold'] = font.get('bold', False)
        logger.info(f"字体设置: {font}")

    # 标题设置
    if 'header_settings' in settings:
        header = settings['header_settings']['value']
        elements['logo_show'] = header.get('show_logo', False)
        elements['branch_show'] = header.get('show_branch_info', True)
        elements['title_size'] = header.get('title_size', 16)
        elements['title_bold'] = header.get('title_bold', True)
        elements['title_color'] = header.get('title_color', '#000000')
        elements['title_font_family'] = header.get('title_font_family', 'SimHei')
        elements['logo_data'] = header.get('logo_data', None)
        elements['logo_width'] = header.get('logo_width', 120)
        elements['logo_height'] = header.get('logo_height', 60)
        elements['logo_alignment'] = header.get('logo_alignment', 'center')
        elements['logo_margin'] = header.get('logo_margin', 10)
        elements['logo_position'] = header.get('logo_position', 'header')
        logger.info(f"标题设置: {header}")

    # 布局设置
    if 'layout_settings' in settings:
        layout = settings['layout_settings']['value']
        elements['line_spacing'] = layout.get('line_spacing', 1.2)
        elements['table_border'] = layout.get('table_border', True)
        elements['auto_page_break'] = layout.get('auto_page_break', True)
        elements['content_style'] = layout.get('content_style', 'table')
        elements['alignment'] = layout.get('alignment', 'left')
        elements['table_alignment'] = layout.get('table_alignment', 'center')
        elements['title_alignment'] = layout.get('title_alignment', 'center')
        elements['row_spacing'] = layout.get('row_spacing', 'normal')
        elements['field_label_width'] = layout.get('field_label_width', 40)
        elements['section_spacing'] = layout.get('section_spacing', 15)
        elements['show_field_labels'] = layout.get('show_field_labels', True)
        logger.info(f"布局设置: {layout}")

    # 签名设置
    if 'signature_settings' in settings:
        signature = settings['signature_settings']['value']
        elements['signature_style'] = signature.get('signature_style', 'double')
        elements['show_date_line'] = signature.get('show_date_line', True)
        elements['single_label'] = signature.get('single_label', '签名/Signature')
        elements['left_label'] = signature.get('left_label', '客户签名/Customer')
        elements['right_label'] = signature.get('right_label', '柜员签名/Teller')
        elements['signature_height'] = signature.get('signature_height', 40)
        elements['signature_width'] = signature.get('signature_width', 150)
        elements['date_format'] = signature.get('date_format', 'YYYY年MM月DD日')
        logger.info(f"签名设置: {signature}")
    
    # 高级设置
    if 'advanced_settings' in settings:
        advanced = settings['advanced_settings']['value']
        elements['watermark_enabled'] = advanced.get('watermark_enabled', False)
        elements['watermark_text'] = advanced.get('watermark_text', '样本')
        elements['watermark_opacity'] = advanced.get('watermark_opacity', 0.1)
        elements['page_numbering'] = advanced.get('page_numbering', False)
        elements['header_line'] = advanced.get('header_line', True)
        elements['footer_line'] = advanced.get('footer_line', True)
        elements['print_quality'] = advanced.get('print_quality', 'high')
        elements['color_mode'] = advanced.get('color_mode', 'color')
        logger.info(f"高级设置: {advanced}")

    logger.info(f"转换完成，生成元素配置: {len(elements)} 个字段")
    return elements

def convert_element_positions_to_elements(element_positions):
    """将前端的elementPositions数据转换为扁平化的元素配置"""
    elements = {}
    
    logger.info(f"转换元素位置数据: {element_positions}")
    
    # Logo位置 - 只保留位置信息，logo的显示、对齐、尺寸等属性由header_settings统一管理
    if 'logo' in element_positions:
        logo = element_positions['logo']
        elements['logo_top'] = logo.get('top', 5)
        elements['logo_left'] = logo.get('left', 105)
        # 注意：不再保存logo的width、height、textAlign、visible等属性，避免重复
        logger.info(f"Logo位置: top={elements['logo_top']}, left={elements['logo_left']}")
    
    # 标题位置
    if 'title' in element_positions:
        title = element_positions['title']
        elements['title_top'] = title.get('top', 25)
        elements['title_left'] = title.get('left', 105)
        elements['title_width'] = title.get('width', 0)
        elements['title_height'] = title.get('height', 30)
        elements['title_align'] = title.get('textAlign', 'center')
        elements['title_show'] = title.get('visible', True)
        # 保存标题的字体属性
        elements['title_font_family'] = title.get('fontFamily', 'SimHei')
        elements['title_size'] = title.get('fontSize', 12)
        elements['title_color'] = title.get('color', '#000000')
        logger.info(f"标题位置: top={elements['title_top']}, left={elements['title_left']}")
    
    # 副标题位置
    if 'subtitle' in element_positions:
        subtitle = element_positions['subtitle']
        elements['subtitle_top'] = subtitle.get('top', 25)
        elements['subtitle_left'] = subtitle.get('left', 50)
        elements['subtitle_width'] = subtitle.get('width', 110)
        elements['subtitle_height'] = subtitle.get('height', 15)
        elements['subtitle_align'] = subtitle.get('textAlign', 'center')
        elements['subtitle_show'] = subtitle.get('visible', True)
        elements['subtitle_font_family'] = subtitle.get('fontFamily', 'SimSun')
        elements['subtitle_font_size'] = subtitle.get('fontSize', 10)
        elements['subtitle_color'] = subtitle.get('color', '#000000')
        logger.info(f"副标题位置: top={elements['subtitle_top']}, left={elements['subtitle_left']}")
    
    # 网点信息位置
    if 'branch' in element_positions:
        branch = element_positions['branch']
        elements['branch_top'] = branch.get('top', 45)
        elements['branch_left'] = branch.get('left', 105)
        elements['branch_width'] = branch.get('width', 0)
        elements['branch_height'] = branch.get('height', 20)
        elements['branch_align'] = branch.get('textAlign', 'center')
        elements['branch_show'] = branch.get('visible', True)
        elements['branch_font_family'] = branch.get('fontFamily', 'SimSun')
        elements['branch_font_size'] = branch.get('fontSize', 8)
        elements['branch_color'] = branch.get('color', '#000000')
        logger.info(f"网点信息位置: top={elements['branch_top']}, left={elements['branch_left']}")
    
    # 内容区域位置
    if 'content' in element_positions:
        content = element_positions['content']
        elements['content_top'] = content.get('top', 65)
        elements['content_left'] = content.get('left', 5)
        elements['content_width'] = content.get('width', 200)
        elements['content_height'] = content.get('height', 150)
        elements['content_show'] = content.get('visible', True)
        # 添加content元素的字体属性保存
        elements['content_font_family'] = content.get('fontFamily', 'SimSun')
        elements['content_font_size'] = content.get('fontSize', 12)
        elements['content_color'] = content.get('color', '#000000')
        elements['content_font_weight'] = content.get('fontWeight', 'normal')
        logger.info(f"内容位置: top={elements['content_top']}, left={elements['content_left']}")
        logger.info(f"内容字体: family={elements['content_font_family']}, size={elements['content_font_size']}, color={elements['content_color']}")
    
    # 签名区域位置
    if 'signature' in element_positions:
        signature = element_positions['signature']
        elements['signature_top'] = signature.get('top', 220)
        elements['signature_left'] = signature.get('left', 5)
        elements['signature_width'] = signature.get('width', 200)
        elements['signature_height'] = signature.get('height', 30)
        elements['signature_show'] = signature.get('visible', True)
        # 添加signature元素的字体属性保存
        elements['signature_font_family'] = signature.get('fontFamily', 'SimSun')
        elements['signature_font_size'] = signature.get('fontSize', 10)
        elements['signature_color'] = signature.get('color', '#000000')
        elements['signature_font_weight'] = signature.get('fontWeight', 'normal')
        logger.info(f"签名位置: top={elements['signature_top']}, left={elements['signature_left']}")
        logger.info(f"签名字体: family={elements['signature_font_family']}, size={elements['signature_font_size']}, color={elements['signature_color']}")
    
    # 水印设置
    if 'watermark' in element_positions:
        watermark = element_positions['watermark']
        elements['watermark_show'] = watermark.get('visible', False)
        elements['watermark_text'] = watermark.get('text', '样本')
        elements['watermark_opacity'] = watermark.get('opacity', 0.1)
        # 添加水印位置信息
        elements['watermark_top'] = watermark.get('top', 120)
        elements['watermark_left'] = watermark.get('left', 80)
        elements['watermark_width'] = watermark.get('width', 50)
        elements['watermark_height'] = watermark.get('height', 30)
        elements['watermark_font_size'] = watermark.get('fontSize', 24)
        logger.info(f"水印设置: show={elements['watermark_show']}, text={elements['watermark_text']}")
    
    return elements

@print_settings_bp.route('/templates/reset', methods=['POST'])
@token_required
@has_permission('system_manage')
def reset_print_settings(current_user):
    """重置打印设置为默认值"""
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
    
    data = request.get_json() or {}
    document_type = data.get('document_type', 'exchange')
    
    try:
        # 使用布局服务创建标准布局
        LayoutService.create_standard_layouts(current_user['branch_id'], document_type)
        
        return jsonify({
            'success': True,
            'message': f'{document_type}类型打印设置已重置为默认值'
        })
        
    except Exception as e:
        logger.error(f"Reset print settings failed: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

def get_default_print_settings():
    """获取默认打印设置 - 完整版本"""
    return {
        'paper_size': {
            'value': {
                'width': 210,  # mm
                'height': 297,  # mm
                'name': 'A4',
                'orientation': 'portrait'  # 恢复：纸张方向 portrait/landscape
            },
            'description': '纸张大小和方向设置（毫米）'
        },
        'margins': {
            'value': {
                'top': 20,
                'right': 20,
                'bottom': 20,
                'left': 20
            },
            'description': '页边距设置（毫米）'
        },
        'font_settings': {
            'value': {
                'family': 'SimSun',
                'size': 10,
                'bold': False,
                'color': '#000000'  # 恢复：字体颜色
            },
            'description': '字体设置'
        },
        'header_settings': {
            'value': {
                'show_logo': True,
                'show_branch_info': True,
                'title_size': 16,
                'title_bold': True,
                'title_color': '#000000',  # 恢复：标题颜色
                'logo_width': 120,  # 恢复：Logo宽度
                'logo_height': 60,  # 恢复：Logo高度
                'logo_alignment': 'center',  # 恢复：Logo对齐方式
                'logo_margin': 10,  # 恢复：Logo边距
                'logo_data': None,  # 恢复：Logo数据
                'logo_position': 'header'  # 恢复：Logo位置 header/left/right
            },
            'description': '页眉和Logo设置'
        },
        'layout_settings': {
            'value': {
                'line_spacing': 1.2,
                'table_border': True,
                'auto_page_break': True,
                'content_style': 'table',  # 'simple'(简洁) 或 'table'(表格)
                'alignment': 'left',  # 恢复：内容对齐方式
                'table_alignment': 'center',  # 恢复：表格对齐方式
                'title_alignment': 'center',  # 恢复：标题对齐方式
                'row_spacing': 'normal',  # 恢复：行间距样式 compact/normal/loose
                'field_label_width': 40,  # 恢复：字段标签宽度百分比
                'section_spacing': 15,  # 恢复：区域间距
                'show_field_labels': True  # 恢复：显示字段标签
            },
            'description': '布局和对齐设置'
        },
        'signature_settings': {
            'value': {
                'signature_style': 'double',  # 'none', 'single', 'double'
                'show_date_line': True,
                'single_label': '签名/Signature',
                'left_label': '客户签名/Customer',
                'right_label': '柜员签名/Teller',
                'signature_height': 40,  # 恢复：签名框高度
                'signature_width': 150,  # 恢复：签名框宽度
                'date_format': 'YYYY年MM月DD日'  # 恢复：日期格式
            },
            'description': '签名区域设置'
        },
        'custom_paper': {
            'value': {
                'enabled': False,
                'width': 80,  # mm (热敏纸宽度)
                'height': 200,  # mm
                'name': '自定义',
                'orientation': 'portrait'  # 恢复：自定义纸张方向
            },
            'description': '自定义纸张大小'
        },
        'element_positions': {
            'value': {
                'logo': { 
                    'top': 5, 'left': 10, 'width': 120, 'height': 60,
                    'textAlign': 'center', 'visible': True,
                    'fontSize': 12, 'fontWeight': 'normal', 'color': '#000000'
                },
                'title': { 
                    'top': 50, 'left': 10, 'width': None, 'height': 30,
                    'textAlign': 'center', 'visible': True,
                    'fontSize': 16, 'fontWeight': 'bold', 'color': '#000000'
                },
                'transactionNo': { 
                    'top': 100, 'left': 10, 'width': 300, 'height': 20,
                    'textAlign': 'left', 'visible': True,
                    'fontSize': 12, 'fontWeight': 'normal', 'color': '#000000'
                },
                'transactionTime': { 
                    'top': 130, 'left': 10, 'width': 300, 'height': 20,
                    'textAlign': 'left', 'visible': True,
                    'fontSize': 12, 'fontWeight': 'normal', 'color': '#000000'
                },
                'transactionAmount': { 
                    'top': 160, 'left': 10, 'width': 300, 'height': 20,
                    'textAlign': 'left', 'visible': True,
                    'fontSize': 12, 'fontWeight': 'normal', 'color': '#000000'
                },
                'exchangeAmount': { 
                    'top': 190, 'left': 10, 'width': 300, 'height': 20,
                    'textAlign': 'left', 'visible': True,
                    'fontSize': 12, 'fontWeight': 'normal', 'color': '#000000'
                },
                'exchangeRate': { 
                    'top': 220, 'left': 10, 'width': 300, 'height': 20,
                    'textAlign': 'left', 'visible': True,
                    'fontSize': 12, 'fontWeight': 'normal', 'color': '#000000'
                },
                'customerInfo': { 
                    'top': 250, 'left': 10, 'width': 300, 'height': 20,
                    'textAlign': 'left', 'visible': True,
                    'fontSize': 12, 'fontWeight': 'normal', 'color': '#000000'
                },
                'signature': { 
                    'top': 310, 'left': 10, 'width': None, 'height': 40,
                    'textAlign': 'center', 'visible': True,
                    'fontSize': 12, 'fontWeight': 'normal', 'color': '#000000'
                },
                'notice': { 
                    'top': 400, 'left': 10, 'width': None, 'height': 30,
                    'textAlign': 'center', 'visible': True,
                    'fontSize': 10, 'fontWeight': 'normal', 'color': '#666666'
                }
            },
            'description': '可视化布局元素位置和样式设置'
        },
        'advanced_settings': {
            'value': {
                'watermark_enabled': False,  # 恢复：水印功能
                'watermark_text': '样本',
                'watermark_opacity': 0.1,
                'page_numbering': False,  # 恢复：页码
                'header_line': True,  # 恢复：页眉分割线
                'footer_line': True,  # 恢复：页脚分割线
                'print_quality': 'high',  # 恢复：打印质量 draft/normal/high
                'color_mode': 'color'  # 恢复：颜色模式 color/grayscale/bw
            },
            'description': '高级打印设置'
        }
    } 

@print_settings_bp.route('/logos', methods=['GET'])
@token_required
@has_permission('system_manage')
def get_logos(current_user):
    """获取Logo列表"""
    try:
        branch_id = request.args.get('branch_id', current_user.get('branch_id'))
        document_type = request.args.get('document_type', 'exchange')
        
        session = DatabaseService.get_session()
        try:
            # 获取header_settings中的logo信息
            setting = session.query(PrintSettings).filter_by(
                branch_id=branch_id,
                document_type=document_type,
                setting_key='header_settings'
            ).first()
            
            logos = []
            if setting and setting.setting_value:
                header_settings = json.loads(setting.setting_value)
                if header_settings.get('logo_data'):
                    logos.append({
                        'id': 1,
                        'name': 'current_logo',
                        'data': header_settings['logo_data'],
                        'active': header_settings.get('show_logo', False)
                    })
            
            return jsonify({
                'success': True,
                'logos': logos
            })
            
        except Exception as e:
            logger.error(f"获取Logo列表失败: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
        finally:
            DatabaseService.close_session(session)
            
    except Exception as e:
        logger.error(f"获取Logo列表失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500



@print_settings_bp.route('/logo/delete', methods=['POST'])
@token_required
@has_permission('system_manage')
def delete_logo(current_user):
    """删除Logo"""
    try:
        data = request.get_json()
        branch_id = data.get('branch_id', current_user.get('branch_id'))
        document_type = data.get('document_type', 'exchange')
        
        session = DatabaseService.get_session()
        try:
            # 查找现有的header_settings
            existing_setting = session.query(PrintSettings).filter_by(
                branch_id=branch_id,
                document_type=document_type,
                setting_key='header_settings'
            ).first()
            
            if existing_setting:
                header_settings = json.loads(existing_setting.setting_value)
                header_settings['logo_data'] = None
                header_settings['show_logo'] = False
                existing_setting.setting_value = json.dumps(header_settings, ensure_ascii=False)
                existing_setting.updated_at = datetime.now()
                session.commit()
                
                # 记录操作日志 - 暂时注释掉，避免错误
                # log_activity(
                #     current_user['id'],
                #     'logo_delete',
                #     f'删除Logo',
                #     {'branch_id': branch_id, 'document_type': document_type}
                # )
                
                return jsonify({'success': True, 'message': 'Logo删除成功'})
            else:
                return jsonify({'success': False, 'message': 'Logo设置不存在'}), 404
                
        except Exception as e:
            session.rollback()
            logger.error(f"删除Logo失败: {str(e)}")
            return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500
        finally:
            DatabaseService.close_session(session)
            
    except Exception as e:
        logger.error(f"删除Logo失败: {str(e)}")
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500

@print_settings_bp.route('/layout-editor-config', methods=['GET'])
@token_required
@has_permission('system_manage')
def get_layout_editor_config(current_user):
    """获取布局编辑器配置"""
    try:
        branch_id = request.args.get('branch_id', current_user.get('branch_id'))
        document_type = request.args.get('document_type', 'exchange')
        
        # 获取当前设置
        settings = get_print_settings_by_branch(branch_id, document_type)
        
        return jsonify({
            'success': True,
            'config': {
                'branch_id': branch_id,
                'document_type': document_type,
                'editor_url': f'/print-layout-editor?branch_id={branch_id}&document_type={document_type}',
                'current_settings': settings,
                'available_fields': {
                    'exchange': ['date', 'receipt_number', 'customer_name', 'amount', 'rate', 'total'],
                    'balance_adjust': ['date', 'adjust_number', 'currency', 'old_balance', 'adjustment', 'new_balance'],
                    'reversal': ['date', 'reversal_number', 'original_receipt', 'amount', 'reason'],
                    'eod': ['date', 'branch_name', 'operator', 'totals']
                }
            }
        })
        
    except Exception as e:
        logger.error(f"获取布局编辑器配置失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取配置失败: {str(e)}'}), 500

@print_settings_bp.route('/layout-editor', methods=['GET'])
@token_required
@has_permission('system_manage')
def open_layout_editor(current_user):
    """打开可视化布局编辑器"""
    try:
        branch_id = request.args.get('branch_id', current_user.get('branch_id'))
        document_type = request.args.get('document_type', 'exchange')
        
        # 获取当前设置
        settings = get_print_settings_by_branch(branch_id, document_type)
        
        return jsonify({
            'success': True,
            'editor_url': f'/print-layout-editor?branch_id={branch_id}&document_type={document_type}',
            'settings': settings
        })
        
    except Exception as e:
        logger.error(f"打开布局编辑器失败: {str(e)}")
        return jsonify({'success': False, 'message': f'打开编辑器失败: {str(e)}'}), 500

def get_print_settings_by_branch(branch_id, document_type='exchange'):
    """获取指定网点和单据类型的打印设置"""
    session = DatabaseService.get_session()
    try:
        settings = session.query(PrintSettings).filter_by(
            branch_id=branch_id,
            document_type=document_type,
            is_active=True
        ).all()
        
        if not settings:
            return get_default_print_settings()
        
        # 构建设置字典
        settings_dict = {}
        for setting in settings:
            try:
                # 尝试解析JSON值
                value = json.loads(setting.setting_value) if setting.setting_value else None
            except json.JSONDecodeError:
                value = setting.setting_value
            
            settings_dict[setting.setting_key] = {
                'value': value,
                'description': setting.description,
                'updated_at': setting.updated_at.isoformat() if setting.updated_at else None
            }
        
        return settings_dict
        
    except Exception as e:
        logger.error(f"获取打印设置失败: {str(e)}")
        return get_default_print_settings()
    finally:
        DatabaseService.close_session(session)

@print_settings_bp.route('/layouts/list', methods=['GET'])
@token_required
@has_permission('system_manage')
def get_layouts_list(current_user):
    """获取指定单据类型的布局列表"""
    try:
        document_type = request.args.get('document_type', 'exchange')
        branch_id = validate_branch_access(current_user)
        
        layouts = LayoutService.get_layouts_by_document_type(branch_id, document_type)
        
        return jsonify({
            'success': True,
            'layouts': layouts,
            'message': '布局列表获取成功'
        })
        
    except ValueError as ve:
        return jsonify({
            'success': False,
            'message': str(ve)
        }), 400
    except Exception as e:
        logger.error(f"获取布局列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取布局列表失败: {str(e)}'
        }), 500

@print_settings_bp.route('/layouts', methods=['GET'])
@token_required
@has_permission('system_manage')
def get_layout_settings(current_user):
    """获取指定布局的设置"""
    try:
        document_type = request.args.get('document_type', 'exchange')
        layout_name = request.args.get('layout_name', '表格格式')
        branch_id = current_user.get('branch_id', 1)
        
        elements = LayoutService.get_layout_elements(branch_id, document_type, layout_name)
        
        if not elements:
            return jsonify({
                'success': False,
                'message': '布局不存在或无配置数据'
            })
        
        # 转换为前端格式
        frontend_settings = convert_elements_to_frontend_format(elements)
        
        return jsonify({
            'success': True,
            'settings': frontend_settings,
            'message': '布局设置获取成功'
        })
        
    except Exception as e:
        logger.error(f"获取布局设置失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取布局设置失败: {str(e)}'
        }), 500

@print_settings_bp.route('/layouts/create', methods=['POST'])
@token_required
@has_permission('system_manage')
def create_layout(current_user):
    """创建新布局"""
    try:
        data = request.get_json()
        document_type = data.get('document_type', 'exchange')
        layout_name = data.get('layout_name')
        template = data.get('template', '')
        description = data.get('description', '')
        branch_id = current_user.get('branch_id', 1)
        
        if not layout_name:
            return jsonify({
                'success': False,
                'message': '布局名称不能为空'
            })
        
        # 检查布局是否已存在
        existing_layouts = LayoutService.get_layouts_by_document_type(branch_id, document_type)
        if any(layout['name'] == layout_name for layout in existing_layouts):
            return jsonify({
                'success': False,
                'message': '布局名称已存在'
            })
        
        # 创建布局
        if template and template in ['表格格式', '简洁格式']:
            # 基于标准模板创建
            LayoutService.create_standard_layouts(branch_id, document_type, layout_name, template)
        elif template:
            # 基于现有布局复制
            source_elements = LayoutService.get_layout_elements(branch_id, document_type, template)
            if source_elements:
                LayoutService.save_layout(branch_id, document_type, layout_name, source_elements, False)
        else:
            # 创建空白布局
            LayoutService.create_standard_layouts(branch_id, document_type, layout_name, '表格格式')
        
        return jsonify({
            'success': True,
            'message': '布局创建成功'
        })
        
    except Exception as e:
        logger.error(f"创建布局失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'创建布局失败: {str(e)}'
        }), 500

@print_settings_bp.route('/layouts/copy', methods=['POST'])
@token_required
@has_permission('system_manage')
def copy_layout(current_user):
    """复制布局"""
    try:
        data = request.get_json()
        document_type = data.get('document_type', 'exchange')
        source_layout_name = data.get('source_layout_name')
        target_layout_name = data.get('target_layout_name')
        branch_id = current_user.get('branch_id', 1)
        
        if not source_layout_name or not target_layout_name:
            return jsonify({
                'success': False,
                'message': '源布局名称和目标布局名称不能为空'
            })
        
        # 检查目标布局是否已存在
        existing_layouts = LayoutService.get_layouts_by_document_type(branch_id, document_type)
        if any(layout['name'] == target_layout_name for layout in existing_layouts):
            return jsonify({
                'success': False,
                'message': '目标布局名称已存在'
            })
        
        # 获取源布局配置
        source_elements = LayoutService.get_layout_elements(branch_id, document_type, source_layout_name)
        if not source_elements:
            return jsonify({
                'success': False,
                'message': '源布局不存在'
            })
        
        # 复制布局
        LayoutService.save_layout(branch_id, document_type, target_layout_name, source_elements, False)
        
        return jsonify({
            'success': True,
            'message': '布局复制成功'
        })
        
    except Exception as e:
        logger.error(f"复制布局失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'复制布局失败: {str(e)}'
        }), 500

@print_settings_bp.route('/layouts/delete', methods=['DELETE'])
@token_required
@has_permission('system_manage')
def delete_layout(current_user):
    """删除布局（仅删除print_settings表中的记录）"""
    try:
        data = request.get_json()
        document_type = data.get('document_type', 'exchange')
        layout_name = data.get('layout_name')
        branch_id = current_user.get('branch_id', 1)
        
        if not layout_name:
            return jsonify({
                'success': False,
                'message': '布局名称不能为空'
            })
        
        session = DatabaseService.get_session()
        try:
            # 检查是否为默认布局（在print_templates表中）
            from sqlalchemy import text
            template_query = text('''
                SELECT COUNT(*) FROM print_templates 
                WHERE branch_id = :branch_id 
                AND document_type = :document_type 
                AND layout_name = :layout_name
            ''')
            
            template_result = session.execute(template_query, {
                'branch_id': branch_id,
                'document_type': document_type,
                'layout_name': layout_name
            }).scalar()
            
            if template_result > 0:
                return jsonify({
                    'success': False,
                    'message': '不允许删除默认布局，默认布局存储在模板表中不可删除'
                })
            
            # 检查布局是否存在于print_settings表中
            settings_count = session.query(PrintSettings).filter_by(
                branch_id=branch_id,
                document_type=document_type,
                layout_name=layout_name
            ).count()
            
            if settings_count == 0:
                return jsonify({
                    'success': False,
                    'message': '布局不存在'
                })
            
            # 删除print_settings表中的布局记录
            deleted_count = session.query(PrintSettings).filter_by(
                branch_id=branch_id,
                document_type=document_type,
                layout_name=layout_name
            ).delete()
            
            session.commit()
            
            logger.info(f"删除布局成功: branch_id={branch_id}, document_type={document_type}, layout_name={layout_name}, deleted_count={deleted_count}")
            
            return jsonify({
                'success': True,
                'message': f'布局 "{layout_name}" 已删除（删除了 {deleted_count} 条设置记录）'
            })
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            DatabaseService.close_session(session)
        
    except Exception as e:
        logger.error(f"删除布局失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'删除布局失败: {str(e)}'
        }), 500

@print_settings_bp.route('/layouts/set-default', methods=['POST'])
@token_required
@has_permission('system_manage')
def set_default_layout(current_user):
    """设置默认布局"""
    try:
        data = request.get_json()
        document_type = data.get('document_type', 'exchange')
        layout_name = data.get('layout_name')
        branch_id = current_user.get('branch_id', 1)
        
        if not layout_name:
            return jsonify({
                'success': False,
                'message': '布局名称不能为空'
            })
        
        # 检查布局是否存在
        layouts = LayoutService.get_layouts_by_document_type(branch_id, document_type)
        if not any(layout['name'] == layout_name for layout in layouts):
            return jsonify({
                'success': False,
                'message': '指定的布局不存在'
            })
        
        # 设置默认布局
        session = DatabaseService.get_session()
        try:
            # 先取消所有布局的默认状态
            session.query(PrintSettings).filter_by(
                branch_id=branch_id,
                document_type=document_type
            ).update({'is_default_layout': False})
            
            # 设置指定布局为默认
            session.query(PrintSettings).filter_by(
                branch_id=branch_id,
                document_type=document_type,
                layout_name=layout_name
            ).update({'is_default_layout': True})
            
            session.commit()
            
            return jsonify({
                'success': True,
                'message': '默认布局设置成功'
            })
            
        finally:
            DatabaseService.close_session(session)
        
    except Exception as e:
        logger.error(f"设置默认布局失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'设置默认布局失败: {str(e)}'
        }), 500 


# ===========================================
# 新的 print_templates 模板管理 API
# ===========================================

@print_settings_bp.route('/templates/list', methods=['GET'])
@token_required
@has_permission('system_manage')
def get_templates_list(current_user):
    """获取模板列表"""
    try:
        document_type = request.args.get('document_type', 'exchange')
        branch_id = current_user.get('branch_id', 1)
        
        session = DatabaseService.get_session()
        try:
            # 查询 print_templates 表
            from sqlalchemy import text
            query = text('''
                SELECT id, layout_name, description, is_default_layout, created_at
                FROM print_templates 
                WHERE branch_id = :branch_id AND document_type = :document_type
                ORDER BY is_default_layout DESC, layout_name ASC
            ''')
            
            result = session.execute(query, {
                'branch_id': branch_id,
                'document_type': document_type
            })
            
            templates = []
            for row in result:
                templates.append({
                    'id': row[0],
                    'layout_name': row[1],
                    'description': row[2],
                    'is_default_layout': bool(row[3]),
                    'created_at': row[4]
                })
            
            return jsonify({
                'success': True,
                'templates': templates
            })
            
        finally:
            DatabaseService.close_session(session)
        
    except Exception as e:
        logger.error(f"获取模板列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取模板列表失败: {str(e)}'
        }), 500

@print_settings_bp.route('/templates/create', methods=['POST'])
@token_required
@has_permission('system_manage')
def create_template(current_user):
    """创建新模板"""
    try:
        data = request.get_json()
        document_type = data.get('document_type', 'exchange')
        layout_name = data.get('layout_name')
        settings_json = data.get('settings_json')
        description = data.get('description', '')
        branch_id = current_user.get('branch_id', 1)
        
        if not layout_name:
            return jsonify({
                'success': False,
                'message': '布局名称不能为空'
            })
        
        session = DatabaseService.get_session()
        try:
            # 检查布局名称是否已存在
            from sqlalchemy import text
            check_query = text('''
                SELECT COUNT(*) FROM print_templates 
                WHERE branch_id = :branch_id AND document_type = :document_type AND layout_name = :layout_name
            ''')
            
            result = session.execute(check_query, {
                'branch_id': branch_id,
                'document_type': document_type,
                'layout_name': layout_name
            })
            
            if result.scalar() > 0:
                return jsonify({
                    'success': False,
                    'message': '布局名称已存在'
                })
            
            # 插入新模板
            insert_query = text('''
                INSERT INTO print_templates 
                (branch_id, document_type, layout_name, settings_json, description, is_default_layout, created_at, updated_at)
                VALUES (:branch_id, :document_type, :layout_name, :settings_json, :description, 0, datetime('now'), datetime('now'))
            ''')
            
            session.execute(insert_query, {
                'branch_id': branch_id,
                'document_type': document_type,
                'layout_name': layout_name,
                'settings_json': settings_json,
                'description': description
            })
            
            session.commit()
            
            return jsonify({
                'success': True,
                'message': '模板创建成功'
            })
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            DatabaseService.close_session(session)
        
    except Exception as e:
        logger.error(f"创建模板失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'创建模板失败: {str(e)}'
        }), 500

@print_settings_bp.route('/templates/duplicate', methods=['POST'])
@token_required
@has_permission('system_manage')
def duplicate_template(current_user):
    """复制模板"""
    try:
        data = request.get_json()
        document_type = data.get('document_type', 'exchange')
        source_layout_name = data.get('source_layout_name')
        new_layout_name = data.get('new_layout_name')
        branch_id = current_user.get('branch_id', 1)
        
        if not source_layout_name or not new_layout_name:
            return jsonify({
                'success': False,
                'message': '源布局名称和新布局名称不能为空'
            })
        
        session = DatabaseService.get_session()
        try:
            from sqlalchemy import text
            
            # 检查新布局名称是否已存在
            check_query = text('''
                SELECT COUNT(*) FROM print_templates 
                WHERE branch_id = :branch_id AND document_type = :document_type AND layout_name = :layout_name
            ''')
            
            result = session.execute(check_query, {
                'branch_id': branch_id,
                'document_type': document_type,
                'layout_name': new_layout_name
            })
            
            if result.scalar() > 0:
                return jsonify({
                    'success': False,
                    'message': '新布局名称已存在'
                })
            
            # 获取源模板数据
            source_query = text('''
                SELECT settings_json, description FROM print_templates 
                WHERE branch_id = :branch_id AND document_type = :document_type AND layout_name = :layout_name
            ''')
            
            source_result = session.execute(source_query, {
                'branch_id': branch_id,
                'document_type': document_type,
                'layout_name': source_layout_name
            })
            
            source_data = source_result.fetchone()
            if not source_data:
                return jsonify({
                    'success': False,
                    'message': '源布局不存在'
                })
            
            # 插入新模板
            insert_query = text('''
                INSERT INTO print_templates 
                (branch_id, document_type, layout_name, settings_json, description, is_default_layout, created_at, updated_at)
                VALUES (:branch_id, :document_type, :layout_name, :settings_json, :description, 0, datetime('now'), datetime('now'))
            ''')
            
            session.execute(insert_query, {
                'branch_id': branch_id,
                'document_type': document_type,
                'layout_name': new_layout_name,
                'settings_json': source_data[0],
                'description': f'{source_data[1]} 的备份'
            })
            
            session.commit()
            
            return jsonify({
                'success': True,
                'message': '模板复制成功'
            })
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            DatabaseService.close_session(session)
        
    except Exception as e:
        logger.error(f"复制模板失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'复制模板失败: {str(e)}'
        }), 500

@print_settings_bp.route('/templates/delete', methods=['DELETE'])
@token_required
@has_permission('system_manage')
def delete_template(current_user):
    """删除模板"""
    try:
        document_type = request.args.get('document_type', 'exchange')
        layout_name = request.args.get('layout_name')
        branch_id = current_user.get('branch_id', 1)
        
        if not layout_name:
            return jsonify({
                'success': False,
                'message': '布局名称不能为空'
            })
        
        session = DatabaseService.get_session()
        try:
            from sqlalchemy import text
            
            # 检查是否为默认布局
            check_query = text('''
                SELECT is_default_layout FROM print_templates 
                WHERE branch_id = :branch_id AND document_type = :document_type AND layout_name = :layout_name
            ''')
            
            result = session.execute(check_query, {
                'branch_id': branch_id,
                'document_type': document_type,
                'layout_name': layout_name
            })
            
            template_data = result.fetchone()
            if not template_data:
                return jsonify({
                    'success': False,
                    'message': '指定的布局不存在'
                })
            
            if template_data[0]:  # is_default_layout
                return jsonify({
                    'success': False,
                    'message': '不能删除默认布局'
                })
            
            # 检查是否还有其他布局
            count_query = text('''
                SELECT COUNT(*) FROM print_templates 
                WHERE branch_id = :branch_id AND document_type = :document_type
            ''')
            
            count_result = session.execute(count_query, {
                'branch_id': branch_id,
                'document_type': document_type
            })
            
            if count_result.scalar() <= 1:
                return jsonify({
                    'success': False,
                    'message': '至少需要保留一个布局'
                })
            
            # 删除模板
            delete_query = text('''
                DELETE FROM print_templates 
                WHERE branch_id = :branch_id AND document_type = :document_type AND layout_name = :layout_name
            ''')
            
            session.execute(delete_query, {
                'branch_id': branch_id,
                'document_type': document_type,
                'layout_name': layout_name
            })
            
            session.commit()
            
            return jsonify({
                'success': True,
                'message': '模板删除成功'
            })
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            DatabaseService.close_session(session)
        
    except Exception as e:
        logger.error(f"删除模板失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'删除模板失败: {str(e)}'
        }), 500

@print_settings_bp.route('/templates/set-default', methods=['POST'])
@token_required
@has_permission('system_manage')
def set_default_template(current_user):
    """设置默认模板"""
    try:
        data = request.get_json()
        document_type = data.get('document_type', 'exchange')
        layout_name = data.get('layout_name')
        branch_id = current_user.get('branch_id', 1)
        
        if not layout_name:
            return jsonify({
                'success': False,
                'message': '布局名称不能为空'
            })
        
        session = DatabaseService.get_session()
        try:
            from sqlalchemy import text
            
            # 检查布局是否存在
            check_query = text('''
                SELECT settings_json FROM print_templates 
                WHERE branch_id = :branch_id AND document_type = :document_type AND layout_name = :layout_name
            ''')
            
            result = session.execute(check_query, {
                'branch_id': branch_id,
                'document_type': document_type,
                'layout_name': layout_name
            })
            
            template_data = result.fetchone()
            if not template_data:
                return jsonify({
                    'success': False,
                    'message': '指定的布局不存在'
                })
            
            # 先取消所有布局的默认状态
            clear_default_query = text('''
                UPDATE print_templates 
                SET is_default_layout = 0, updated_at = datetime('now')
                WHERE branch_id = :branch_id AND document_type = :document_type
            ''')
            
            session.execute(clear_default_query, {
                'branch_id': branch_id,
                'document_type': document_type
            })
            
            # 设置指定布局为默认
            set_default_query = text('''
                UPDATE print_templates 
                SET is_default_layout = 1, updated_at = datetime('now')
                WHERE branch_id = :branch_id AND document_type = :document_type AND layout_name = :layout_name
            ''')
            
            session.execute(set_default_query, {
                'branch_id': branch_id,
                'document_type': document_type,
                'layout_name': layout_name
            })
            
            # 同时更新 print_settings 表，将新的默认布局设置应用到 print_settings 表
            settings_json = template_data[0]
            if settings_json:
                try:
                    settings_dict = json.loads(settings_json)
                    
                    # 先删除旧的 print_settings 记录
                    delete_settings_query = text('''
                        DELETE FROM print_settings 
                        WHERE branch_id = :branch_id AND document_type = :document_type AND is_default_layout = 1
                    ''')
                    
                    session.execute(delete_settings_query, {
                        'branch_id': branch_id,
                        'document_type': document_type
                    })
                    
                    # 将JSON设置转换并插入到 print_settings 表
                    # 这里需要将settings_dict展开为多条记录
                    # 暂时简化处理，后续可以完善
                    
                except json.JSONDecodeError:
                    logger.warning(f"模板 {layout_name} 的 settings_json 格式无效")
            
            session.commit()
            
            return jsonify({
                'success': True,
                'message': '默认模板设置成功'
            })
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            DatabaseService.close_session(session)
        
    except Exception as e:
        logger.error(f"设置默认模板失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'设置默认模板失败: {str(e)}'
        }), 500

@print_settings_bp.route('/templates/rename', methods=['PUT'])
@token_required
@has_permission('system_manage')
def rename_layout(current_user):
    """重命名布局，同步更新 print_templates 和 print_settings 表"""
    try:
        data = request.get_json()
        document_type = data.get('document_type', 'exchange')
        old_layout_name = data.get('old_layout_name')
        new_layout_name = data.get('new_layout_name')
        branch_id = current_user.get('branch_id', 1)
        
        if not old_layout_name or not new_layout_name:
            return jsonify({
                'success': False,
                'message': '旧布局名称和新布局名称都不能为空'
            })
        
        if old_layout_name == new_layout_name:
            return jsonify({
                'success': False,
                'message': '新布局名称与旧名称相同'
            })
        
        session = DatabaseService.get_session()
        try:
            from sqlalchemy import text
            
            # 检查旧布局是否存在
            check_old_query = text('''
                SELECT COUNT(*) FROM print_settings 
                WHERE branch_id = :branch_id AND document_type = :document_type AND layout_name = :old_layout_name
            ''')
            
            old_count = session.execute(check_old_query, {
                'branch_id': branch_id,
                'document_type': document_type,
                'old_layout_name': old_layout_name
            }).scalar()
            
            if old_count == 0:
                return jsonify({
                    'success': False,
                    'message': f'布局 "{old_layout_name}" 不存在'
                })
            
            # 检查新布局名称是否已存在
            check_new_query = text('''
                SELECT COUNT(*) FROM print_settings 
                WHERE branch_id = :branch_id AND document_type = :document_type AND layout_name = :new_layout_name
            ''')
            
            new_count = session.execute(check_new_query, {
                'branch_id': branch_id,
                'document_type': document_type,
                'new_layout_name': new_layout_name
            }).scalar()
            
            if new_count > 0:
                return jsonify({
                    'success': False,
                    'message': f'布局名称 "{new_layout_name}" 已存在'
                })
            
            # 开始事务：同时更新两个表
            
            # 1. 更新 print_settings 表中的布局名称
            update_settings_query = text('''
                UPDATE print_settings 
                SET layout_name = :new_layout_name, updated_at = datetime('now')
                WHERE branch_id = :branch_id AND document_type = :document_type AND layout_name = :old_layout_name
            ''')
            
            session.execute(update_settings_query, {
                'branch_id': branch_id,
                'document_type': document_type,
                'old_layout_name': old_layout_name,
                'new_layout_name': new_layout_name
            })
            
            # 2. 更新 print_templates 表中的布局名称（如果存在的话）
            update_templates_query = text('''
                UPDATE print_templates 
                SET layout_name = :new_layout_name, updated_at = datetime('now')
                WHERE branch_id = :branch_id AND document_type = :document_type AND layout_name = :old_layout_name
            ''')
            
            session.execute(update_templates_query, {
                'branch_id': branch_id,
                'document_type': document_type,
                'old_layout_name': old_layout_name,
                'new_layout_name': new_layout_name
            })
            
            session.commit()
            
            logger.info(f"布局重命名成功: {old_layout_name} -> {new_layout_name} (网点: {branch_id}, 单据类型: {document_type})")
            
            return jsonify({
                'success': True,
                'message': f'布局名称已从 "{old_layout_name}" 更新为 "{new_layout_name}"'
            })
            
        except Exception as e:
            session.rollback()
            logger.error(f"重命名布局失败: {str(e)}")
            raise e
        finally:
            DatabaseService.close_session(session)
        
    except Exception as e:
        logger.error(f"重命名布局失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'重命名布局失败: {str(e)}'
        }), 500

@print_settings_bp.route('/extract-frontend-formats', methods=['POST'])
@token_required
@has_permission('system_manage')
def extract_frontend_formats(current_user):
    """提取前端现有的打印格式并保存为默认模板"""
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
    
    data = request.get_json() or {}
    
    try:
        # 从前端接收各业务类型的格式配置
        frontend_formats = data.get('formats', {})
        branch_id = validate_branch_access(current_user)
        
        session = DatabaseService.get_session()
        try:
            created_templates = []
            
            # 为每种业务类型创建默认模板
            for document_type, format_config in frontend_formats.items():
                # 创建模板记录
                template_data = {
                    'branch_id': branch_id,
                    'document_type': document_type,
                    'layout_name': 'frontend_default',
                    'description': f'{document_type}业务前端默认格式',
                    'is_default_layout': True,
                    'settings_json': json.dumps(format_config, ensure_ascii=False),
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }
                
                # 检查是否已存在
                existing = session.execute(text('''
                    SELECT id FROM print_templates 
                    WHERE branch_id = :branch_id AND document_type = :document_type AND layout_name = :layout_name
                '''), {
                    'branch_id': branch_id,
                    'document_type': document_type,
                    'layout_name': 'frontend_default'
                }).first()
                
                if existing:
                    # 更新现有模板
                    session.execute(text('''
                        UPDATE print_templates 
                        SET settings_json = :settings_json, updated_at = :updated_at
                        WHERE id = :id
                    '''), {
                        'id': existing[0],
                        'settings_json': template_data['settings_json'],
                        'updated_at': template_data['updated_at']
                    })
                else:
                    # 创建新模板
                    session.execute(text('''
                        INSERT INTO print_templates 
                        (branch_id, document_type, layout_name, description, is_default_layout, settings_json, created_at, updated_at)
                        VALUES (:branch_id, :document_type, :layout_name, :description, :is_default_layout, :settings_json, :created_at, :updated_at)
                    '''), template_data)
                
                # 同时更新到print_settings表（展开JSON为字段）
                _sync_template_to_settings(session, branch_id, document_type, 'frontend_default', format_config)
                
                created_templates.append({
                    'document_type': document_type,
                    'layout_name': 'frontend_default',
                    'status': 'updated' if existing else 'created'
                })
            
            session.commit()
            
            return jsonify({
                'success': True,
                'message': '前端格式提取完成',
                'created_templates': created_templates
            })
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            DatabaseService.close_session(session)
        
    except Exception as e:
        logger.error(f"提取前端格式失败: {str(e)}")
        return jsonify({'success': False, 'message': f'提取失败: {str(e)}'}), 500

def _sync_template_to_settings(session, branch_id, document_type, layout_name, format_config):
    """将模板JSON配置同步到print_settings表"""
    try:
        # 先删除现有配置
        session.execute(text('''
            DELETE FROM print_settings 
            WHERE branch_id = :branch_id AND document_type = :document_type AND layout_name = :layout_name
        '''), {
            'branch_id': branch_id,
            'document_type': document_type,
            'layout_name': layout_name
        })
        
        # 展开格式配置为print_settings记录
        for setting_key, setting_data in format_config.items():
            session.execute(text('''
                INSERT INTO print_settings (branch_id, document_type, layout_name, setting_key, setting_value, description, created_at)
                VALUES (:branch_id, :document_type, :layout_name, :setting_key, :setting_value, :description, :created_at)
            '''), {
                'branch_id': branch_id,
                'document_type': document_type,
                'layout_name': layout_name,
                'setting_key': setting_key,
                'setting_value': json.dumps(setting_data.get('value', {}), ensure_ascii=False),
                'description': setting_data.get('description', ''),
                'created_at': datetime.now()
            })
        
    except Exception as e:
        logger.error(f"同步模板到设置表失败: {str(e)}")
        raise e

@print_settings_bp.route('/restore-factory-defaults', methods=['POST'])
@token_required
@has_permission('system_manage')
def restore_factory_defaults(current_user):
    """恢复到出厂默认格式"""
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
    
    data = request.get_json() or {}
    
    try:
        document_type = data.get('document_type', 'exchange')
        layout_name = data.get('layout_name', 'frontend_default')
        branch_id = validate_branch_access(current_user)
        
        # 获取出厂默认格式（与前端硬编码保持一致）
        factory_formats = get_factory_default_formats()
        
        if document_type not in factory_formats:
            return jsonify({
                'success': False,
                'message': f'不支持的单据类型: {document_type}'
            })
        
        format_config = factory_formats[document_type]
        
        session = DatabaseService.get_session()
        try:
            # 1. 删除现有的 print_settings 记录
            session.execute(text('''
                DELETE FROM print_settings 
                WHERE branch_id = :branch_id AND document_type = :document_type AND layout_name = :layout_name
            '''), {
                'branch_id': branch_id,
                'document_type': document_type,
                'layout_name': layout_name
            })
            
            # 2. 删除现有的 print_templates 记录
            session.execute(text('''
                DELETE FROM print_templates 
                WHERE branch_id = :branch_id AND document_type = :document_type AND layout_name = :layout_name
            '''), {
                'branch_id': branch_id,
                'document_type': document_type,
                'layout_name': layout_name
            })
            
            # 3. 重新创建出厂默认模板
            template_data = {
                'branch_id': branch_id,
                'document_type': document_type,
                'layout_name': layout_name,
                'description': f'{document_type}业务出厂默认格式',
                'is_default_layout': True,
                'settings_json': json.dumps(format_config, ensure_ascii=False),
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            session.execute(text('''
                INSERT INTO print_templates 
                (branch_id, document_type, layout_name, description, is_default_layout, settings_json, created_at, updated_at)
                VALUES (:branch_id, :document_type, :layout_name, :description, :is_default_layout, :settings_json, :created_at, :updated_at)
            '''), template_data)
            
            # 4. 同步到 print_settings 表
            _sync_template_to_settings(session, branch_id, document_type, layout_name, format_config)
            
            session.commit()
            
            logger.info(f"恢复出厂默认格式成功: branch_id={branch_id}, document_type={document_type}, layout_name={layout_name}")
            
            return jsonify({
                'success': True,
                'message': f'已恢复 {document_type} 业务到出厂默认格式',
                'restored_layout': {
                    'document_type': document_type,
                    'layout_name': layout_name,
                    'status': 'restored'
                }
            })
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            DatabaseService.close_session(session)
        
    except Exception as e:
        logger.error(f"恢复出厂默认格式失败: {str(e)}")
        return jsonify({'success': False, 'message': f'恢复失败: {str(e)}'}), 500

def get_factory_default_formats():
    """获取出厂默认格式配置（与前端硬编码保持一致）"""
    return {
        'exchange': {
            'paper_size': {
                'value': {'width': 210, 'height': 297, 'name': 'A4', 'orientation': 'portrait'},
                'description': '纸张大小和方向设置'
            },
            'margins': {
                'value': {'top': 20, 'right': 20, 'bottom': 20, 'left': 20},
                'description': '页面边距设置'
            },
            'font_settings': {
                'value': {'family': 'SimSun', 'size': 10, 'color': '#000000', 'bold': False},
                'description': '全局字体设置'
            },
            'header_settings': {
                'value': {
                    'show_logo': True,
                    'show_branch_info': True,
                    'title_size': 16,
                    'title_bold': True,
                    'logo_width': 120,
                    'logo_height': 60,
                    'logo_alignment': 'center'
                },
                'description': '页眉设置'
            },
            'layout_settings': {
                'value': {
                    'line_spacing': 1.2,
                    'table_border': True,
                    'auto_page_break': True,
                    'content_style': 'table'
                },
                'description': '布局设置'
            },
            'signature_settings': {
                'value': {
                    'signature_style': 'double',
                    'show_date_line': True,
                    'single_label': '签名/Signature',
                    'left_label': '客户签名/Customer',
                    'right_label': '柜员签名/Teller'
                },
                'description': '签名设置'
            },
            'element_positions': {
                'value': {
                    'logo': {'top': 5, 'left': 105, 'width': 120, 'height': 60, 'textAlign': 'center', 'visible': True},
                    'title': {'top': 25, 'left': 105, 'width': 0, 'height': 20, 'textAlign': 'center', 'visible': True},
                    'subtitle': {'top': 45, 'left': 105, 'width': 0, 'height': 15, 'textAlign': 'center', 'visible': True},
                    'branch': {'top': 65, 'left': 105, 'width': 0, 'height': 15, 'textAlign': 'center', 'visible': True},
                    'content': {'top': 85, 'left': 20, 'width': 170, 'height': 120, 'textAlign': 'left', 'visible': True},
                    'signature': {'top': 220, 'left': 20, 'width': 170, 'height': 40, 'textAlign': 'left', 'visible': True}
                },
                'description': '元素位置设置'
            }
        },
        'reversal': {
            'paper_size': {
                'value': {'width': 210, 'height': 297, 'name': 'A4', 'orientation': 'portrait'},
                'description': '纸张大小和方向设置'
            },
            'margins': {
                'value': {'top': 20, 'right': 20, 'bottom': 20, 'left': 20},
                'description': '页面边距设置'
            },
            'font_settings': {
                'value': {'family': 'SimSun', 'size': 10, 'color': '#000000', 'bold': False},
                'description': '全局字体设置'
            },
            'header_settings': {
                'value': {'show_logo': True, 'show_branch_info': True, 'title_size': 16, 'title_bold': True},
                'description': '页眉设置'
            },
            'layout_settings': {
                'value': {'line_spacing': 1.2, 'table_border': True, 'auto_page_break': True, 'content_style': 'table'},
                'description': '布局设置'
            }
        },
        'balance_adjustment': {
            'paper_size': {
                'value': {'width': 210, 'height': 297, 'name': 'A4', 'orientation': 'portrait'},
                'description': '纸张大小和方向设置'
            },
            'margins': {
                'value': {'top': 20, 'right': 20, 'bottom': 20, 'left': 20},
                'description': '页面边距设置'
            },
            'font_settings': {
                'value': {'family': 'SimSun', 'size': 10, 'color': '#000000', 'bold': False},
                'description': '全局字体设置'
            }
        },
        'balance_summary': {
            'paper_size': {
                'value': {'width': 210, 'height': 297, 'name': 'A4', 'orientation': 'portrait'},
                'description': '纸张大小和方向设置'
            },
            'margins': {
                'value': {'top': 20, 'right': 20, 'bottom': 20, 'left': 20},
                'description': '页面边距设置'
            }
        },
        'eod_report': {
            'paper_size': {
                'value': {'width': 210, 'height': 297, 'name': 'A4', 'orientation': 'portrait'},
                'description': '纸张大小和方向设置'
            },
            'margins': {
                'value': {'top': 15, 'right': 15, 'bottom': 15, 'left': 15},
                'description': '页面边距设置'
            }
        }
    }

