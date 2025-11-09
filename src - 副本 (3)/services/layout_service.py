"""
打印布局管理服务
统一管理所有单据类型的打印布局配置
"""
import json
import logging
from datetime import datetime
try:
    from src.services.db_service import DatabaseService
    from src.models.exchange_models import PrintSettings
except ImportError:
    # 当从src目录内运行时的相对导入
    from services.db_service import DatabaseService
    from models.exchange_models import PrintSettings

logger = logging.getLogger(__name__)

class LayoutService:
    """打印布局管理服务"""
    
    # 标准布局模板定义
    STANDARD_LAYOUTS = {
        'exchange': {
            '表格格式': {
                'description': '标准表格格式，显示完整的交易信息表格',
                'elements': {
                    'paper_width': 210,
                    'paper_height': 297,
                    'paper_orientation': 'portrait',
                    'margin_top': 10,
                    'margin_right': 10,
                    'margin_bottom': 10,
                    'margin_left': 10,
                    'font_family': 'SimSun',
                    'font_size': 12,
                    'font_color': '#000000',
                    'logo_show': True,
                    'logo_top': 5,
                    'logo_left': 105,
                    'logo_width': 120,
                    'logo_height': 60,
                    'title_show': True,
                    'title_top': 25,
                    'title_left': 105,
                    'title_width': 0,
                    'title_height': 20,
                    'title_align': 'center',
                    'title_size': 16,
                    'title_bold': True,
                    'branch_show': True,
                    'branch_top': 45,
                    'branch_left': 105,
                    'branch_width': 0,
                    'branch_height': 15,
                    'branch_align': 'center',
                    'content_show': True,
                    'content_top': 70,
                    'content_left': 20,
                    'content_width': 170,
                    'content_height': 80,
                    'content_style': 'table',
                    'content_border': True,
                    'signature_show': True,
                    'signature_style': 'double',
                    'signature_top': 160,
                    'signature_left': 20,
                    'signature_width': 170,
                    'signature_height': 40,
                    'watermark_show': False,
                    'watermark_text': '样本',
                    'watermark_opacity': 0.1
                }
            },
            '简洁格式': {
                'description': '简洁格式，以简单列表形式显示交易信息',
                'elements': {
                    'paper_width': 210,
                    'paper_height': 297,
                    'paper_orientation': 'portrait',
                    'margin_top': 15,
                    'margin_right': 15,
                    'margin_bottom': 15,
                    'margin_left': 15,
                    'font_family': 'SimSun',
                    'font_size': 11,
                    'font_color': '#000000',
                    'logo_show': True,
                    'logo_top': 8,
                    'logo_left': 95,
                    'logo_width': 80,
                    'logo_height': 40,
                    'title_show': True,
                    'title_top': 35,
                    'title_left': 95,
                    'title_width': 0,
                    'title_height': 18,
                    'title_align': 'center',
                    'title_size': 14,
                    'title_bold': True,
                    'branch_show': True,
                    'branch_top': 55,
                    'branch_left': 95,
                    'branch_width': 0,
                    'branch_height': 12,
                    'branch_align': 'center',
                    'content_show': True,
                    'content_top': 75,
                    'content_left': 25,
                    'content_width': 160,
                    'content_height': 70,
                    'content_style': 'simple',
                    'content_border': False,
                    'signature_show': True,
                    'signature_style': 'single',
                    'signature_top': 155,
                    'signature_left': 25,
                    'signature_width': 160,
                    'signature_height': 35,
                    'watermark_show': False,
                    'watermark_text': '样本',
                    'watermark_opacity': 0.1
                }
            }
        },
        'reversal': {
            '表格格式': {
                'description': '冲正业务标准表格格式',
                'elements': {
                    'paper_width': 210,
                    'paper_height': 297,
                    'paper_orientation': 'portrait',
                    'margin_top': 10,
                    'margin_right': 10,
                    'margin_bottom': 10,
                    'margin_left': 10,
                    'font_family': 'SimSun',
                    'font_size': 12,
                    'font_color': '#000000',
                    'logo_show': True,
                    'logo_top': 5,
                    'logo_left': 105,
                    'logo_width': 120,
                    'logo_height': 60,
                    'title_show': True,
                    'title_top': 25,
                    'title_left': 105,
                    'title_width': 0,
                    'title_height': 20,
                    'title_align': 'center',
                    'title_size': 16,
                    'title_bold': True,
                    'branch_show': True,
                    'branch_top': 45,
                    'branch_left': 105,
                    'branch_width': 0,
                    'branch_height': 15,
                    'branch_align': 'center',
                    'content_show': True,
                    'content_top': 70,
                    'content_left': 20,
                    'content_width': 170,
                    'content_height': 80,
                    'content_style': 'table',
                    'content_border': True,
                    'signature_show': True,
                    'signature_style': 'double',
                    'signature_top': 160,
                    'signature_left': 20,
                    'signature_width': 170,
                    'signature_height': 40,
                    'watermark_show': False,
                    'watermark_text': '样本',
                    'watermark_opacity': 0.1
                }
            }
        },
        'balance_adjustment': {
            '表格格式': {
                'description': '余额调节业务标准表格格式',
                'elements': {
                    'paper_width': 210,
                    'paper_height': 297,
                    'paper_orientation': 'portrait',
                    'margin_top': 10,
                    'margin_right': 10,
                    'margin_bottom': 10,
                    'margin_left': 10,
                    'font_family': 'SimSun',
                    'font_size': 12,
                    'font_color': '#000000',
                    'logo_show': True,
                    'logo_top': 5,
                    'logo_left': 105,
                    'logo_width': 120,
                    'logo_height': 60,
                    'title_show': True,
                    'title_top': 25,
                    'title_left': 105,
                    'title_width': 0,
                    'title_height': 20,
                    'title_align': 'center',
                    'title_size': 16,
                    'title_bold': True,
                    'branch_show': True,
                    'branch_top': 45,
                    'branch_left': 105,
                    'branch_width': 0,
                    'branch_height': 15,
                    'branch_align': 'center',
                    'content_show': True,
                    'content_top': 70,
                    'content_left': 20,
                    'content_width': 170,
                    'content_height': 80,
                    'content_style': 'table',
                    'content_border': True,
                    'signature_show': True,
                    'signature_style': 'double',
                    'signature_top': 160,
                    'signature_left': 20,
                    'signature_width': 170,
                    'signature_height': 40,
                    'watermark_show': False,
                    'watermark_text': '样本',
                    'watermark_opacity': 0.1
                }
            }
        },
        'balance_initialization': {
            '表格格式': {
                'description': '余额初始化业务标准表格格式',
                'elements': {
                    'paper_width': 210,
                    'paper_height': 297,
                    'paper_orientation': 'portrait',
                    'margin_top': 10,
                    'margin_right': 10,
                    'margin_bottom': 10,
                    'margin_left': 10,
                    'font_family': 'SimSun',
                    'font_size': 12,
                    'font_color': '#000000',
                    'logo_show': True,
                    'logo_top': 5,
                    'logo_left': 105,
                    'logo_width': 120,
                    'logo_height': 60,
                    'title_show': True,
                    'title_top': 25,
                    'title_left': 105,
                    'title_width': 0,
                    'title_height': 20,
                    'title_align': 'center',
                    'title_size': 16,
                    'title_bold': True,
                    'branch_show': True,
                    'branch_top': 45,
                    'branch_left': 105,
                    'branch_width': 0,
                    'branch_height': 15,
                    'branch_align': 'center',
                    'content_show': True,
                    'content_top': 70,
                    'content_left': 20,
                    'content_width': 170,
                    'content_height': 80,
                    'content_style': 'table',
                    'content_border': True,
                    'signature_show': True,
                    'signature_style': 'double',
                    'signature_top': 160,
                    'signature_left': 20,
                    'signature_width': 170,
                    'signature_height': 40,
                    'watermark_show': False,
                    'watermark_text': '样本',
                    'watermark_opacity': 0.1
                }
            }
        },
        'eod_report': {
            '表格格式': {
                'description': '日结报表标准表格格式',
                'elements': {
                    'paper_width': 210,
                    'paper_height': 297,
                    'paper_orientation': 'portrait',
                    'margin_top': 10,
                    'margin_right': 10,
                    'margin_bottom': 10,
                    'margin_left': 10,
                    'font_family': 'SimSun',
                    'font_size': 12,
                    'font_color': '#000000',
                    'logo_show': True,
                    'logo_top': 5,
                    'logo_left': 105,
                    'logo_width': 120,
                    'logo_height': 60,
                    'title_show': True,
                    'title_top': 25,
                    'title_left': 105,
                    'title_width': 0,
                    'title_height': 20,
                    'title_align': 'center',
                    'title_size': 16,
                    'title_bold': True,
                    'branch_show': True,
                    'branch_top': 45,
                    'branch_left': 105,
                    'branch_width': 0,
                    'branch_height': 15,
                    'branch_align': 'center',
                    'content_show': True,
                    'content_top': 70,
                    'content_left': 20,
                    'content_width': 170,
                    'content_height': 80,
                    'content_style': 'table',
                    'content_border': True,
                    'signature_show': True,
                    'signature_style': 'double',
                    'signature_top': 160,
                    'signature_left': 20,
                    'signature_width': 170,
                    'signature_height': 40,
                    'watermark_show': False,
                    'watermark_text': '样本',
                    'watermark_opacity': 0.1
                }
            }
        }
    }
    
    @classmethod
    def get_layouts_by_document_type(cls, branch_id, document_type):
        """获取指定单据类型的所有布局"""
        session = DatabaseService.get_session()
        try:
            # 查询该网点该单据类型的所有布局
            layouts = session.query(PrintSettings.layout_name)\
                .filter_by(branch_id=branch_id, document_type=document_type)\
                .distinct().all()
            
            # 获取当前默认布局名称
            from sqlalchemy import text
            default_query = text('''
                SELECT layout_name FROM print_templates 
                WHERE branch_id = :branch_id AND document_type = :document_type 
                LIMIT 1
            ''')
            
            default_result = session.execute(default_query, {
                'branch_id': branch_id,
                'document_type': document_type
            }).fetchone()
            
            default_layout_name = default_result[0] if default_result else None
            
            result = []
            for (layout_name,) in layouts:
                result.append({
                    'name': layout_name,
                    'is_default': layout_name == default_layout_name,
                    'description': cls._get_layout_description(document_type, layout_name)
                })
            
            # 严格按照数据库数据返回，没有数据就返回空列表
            return result
            
        except Exception as e:
            logger.error(f"获取布局列表失败: {str(e)}")
            return []
        finally:
            DatabaseService.close_session(session)
    
    @classmethod
    def get_layout_elements(cls, branch_id, document_type, layout_name):
        """获取指定布局的所有元素配置"""
        session = DatabaseService.get_session()
        try:
            settings = session.query(PrintSettings)\
                .filter_by(
                    branch_id=branch_id,
                    document_type=document_type,
                    layout_name=layout_name,
                    is_active=True
                ).all()
            
            elements = {}
            for setting in settings:
                try:
                    # 首先尝试解析JSON格式的旧数据
                    if setting.setting_value and setting.setting_value.startswith('{'):
                        import json
                        json_data = json.loads(setting.setting_value)
                        
                        # 将JSON数据转换为扁平化格式
                        if setting.setting_key == 'paper_size':
                            elements['paper_width'] = json_data.get('width', 210)
                            elements['paper_height'] = json_data.get('height', 297)
                            elements['paper_orientation'] = json_data.get('orientation', 'portrait')
                        elif setting.setting_key == 'margins':
                            elements['margin_top'] = json_data.get('top', 10)
                            elements['margin_right'] = json_data.get('right', 10)
                            elements['margin_bottom'] = json_data.get('bottom', 10)
                            elements['margin_left'] = json_data.get('left', 10)
                        elif setting.setting_key == 'font_settings':
                            elements['font_family'] = json_data.get('family', 'SimSun')
                            elements['font_size'] = json_data.get('size', 12)
                            elements['font_color'] = json_data.get('color', '#000000')
                        elif setting.setting_key == 'header_settings':
                            elements['logo_show'] = json_data.get('show_logo', True)
                            elements['branch_show'] = json_data.get('show_branch_info', True)
                            elements['title_size'] = json_data.get('title_size', 16)
                            elements['title_bold'] = json_data.get('title_bold', True)
                            # 添加Logo数据处理
                            elements['logo_data'] = json_data.get('logo_data', None)
                            elements['logo_width'] = json_data.get('logo_width', 120)
                            elements['logo_height'] = json_data.get('logo_height', 60)
                            elements['logo_alignment'] = json_data.get('logo_alignment', 'center')
                            elements['logo_margin'] = json_data.get('logo_margin', 10)
                        elif setting.setting_key == 'layout_settings':
                            elements['content_style'] = json_data.get('content_style', 'table')
                            elements['content_border'] = json_data.get('table_border', True)
                        elif setting.setting_key == 'signature_settings':
                            elements['signature_style'] = json_data.get('signature_style', 'double')
                            elements['signature_show'] = True
                        elif setting.setting_key == 'element_positions':
                            # 处理元素位置数据 - 只保留位置信息，不保留重复的显示和对齐设置
                            if isinstance(json_data, dict):
                                for element_name, position in json_data.items():
                                    if element_name == 'logo':
                                        elements['logo_top'] = position.get('top', 5)
                                        elements['logo_left'] = position.get('left', 105)
                                    elif element_name == 'title':
                                        elements['title_top'] = position.get('top', 25)
                                        elements['title_left'] = position.get('left', 105)
                                        elements['title_width'] = position.get('width', 0)
                                        elements['title_height'] = position.get('height', 20)
                                        elements['title_align'] = position.get('textAlign', 'center')
                                        elements['title_show'] = position.get('visible', True)
                                    elif element_name == 'branch':
                                        elements['branch_top'] = position.get('top', 45)
                                        elements['branch_left'] = position.get('left', 105)
                                        elements['branch_width'] = position.get('width', 0)
                                        elements['branch_height'] = position.get('height', 15)
                                        elements['branch_align'] = position.get('textAlign', 'center')
                                        elements['branch_show'] = position.get('visible', True)
                                    elif element_name == 'content':
                                        elements['content_top'] = position.get('top', 70)
                                        elements['content_left'] = position.get('left', 20)
                                        elements['content_width'] = position.get('width', 170)
                                        elements['content_height'] = position.get('height', 80)
                                        elements['content_show'] = position.get('visible', True)
                                    elif element_name == 'signature':
                                        elements['signature_top'] = position.get('top', 160)
                                        elements['signature_left'] = position.get('left', 20)
                                        elements['signature_width'] = position.get('width', 170)
                                        elements['signature_height'] = position.get('height', 40)
                                        elements['signature_show'] = position.get('visible', True)
                                    elif element_name == 'watermark':
                                        elements['watermark_show'] = position.get('visible', False)
                                        elements['watermark_text'] = position.get('text', '样本')
                                        elements['watermark_opacity'] = position.get('opacity', 0.1)
                    else:
                        # 处理扁平化格式的新数据
                        if setting.setting_value and setting.setting_value.isdigit():
                            elements[setting.setting_key] = int(setting.setting_value)
                        elif setting.setting_value and setting.setting_value.replace('.', '').isdigit():
                            elements[setting.setting_key] = float(setting.setting_value)
                        elif setting.setting_value and setting.setting_value.lower() in ['true', 'false']:
                            elements[setting.setting_key] = setting.setting_value.lower() == 'true'
                        else:
                            elements[setting.setting_key] = setting.setting_value
                except Exception as e:
                    logger.warning(f"解析设置 {setting.setting_key} 失败: {str(e)}")
                    # 使用原始值作为回退
                    elements[setting.setting_key] = setting.setting_value
            
            # 严格按照数据库数据返回，没有配置就返回空字典
            return elements
            
        except Exception as e:
            logger.error(f"获取布局元素失败: {str(e)}")
            return {}
        finally:
            DatabaseService.close_session(session)
    
    @classmethod
    def save_layout(cls, branch_id, document_type, layout_name, elements, is_default=False):
        """保存布局配置"""
        logger.info(f"开始保存布局 - 网点ID: {branch_id}, 单据类型: {document_type}, 布局名称: {layout_name}")
        logger.info(f"要保存的元素数量: {len(elements)}")
        logger.info(f"元素详情: {elements}")
        
        session = DatabaseService.get_session()
        try:
            # 如果设置为默认布局，先取消其他布局的默认状态
            if is_default:
                logger.info("设置为默认布局，取消其他布局的默认状态")
                updated_count = session.query(PrintSettings)\
                    .filter_by(branch_id=branch_id, document_type=document_type)\
                    .update({'is_default_layout': False})
                logger.info(f"取消默认状态的记录数: {updated_count}")
            
            # 使用UPSERT操作：先尝试更新，如果不存在则插入
            current_time = datetime.utcnow()
            saved_count = 0
            updated_count = 0
            
            for key, value in elements.items():
                # 检查是否已存在该配置 - 必须包含layout_name以区分不同布局
                existing = session.query(PrintSettings).filter_by(
                    branch_id=branch_id,
                    document_type=document_type,
                    layout_name=layout_name,  # 添加layout_name条件
                    setting_key=key
                ).first()
                
                if existing:
                    # 更新现有记录
                    existing.setting_value = str(value)
                    existing.description = cls._get_element_description(key)
                    existing.is_default_layout = is_default
                    existing.updated_at = current_time
                    updated_count += 1
                    logger.info(f"更新配置: {key} = {value}")
                else:
                    # 插入新记录
                    new_setting = PrintSettings(
                        branch_id=branch_id,
                        document_type=document_type,
                        layout_name=layout_name,
                        setting_key=key,
                        setting_value=str(value),
                        description=cls._get_element_description(key),
                        is_default_layout=is_default,
                        is_active=True,
                        created_at=current_time,
                        updated_at=current_time
                    )
                    session.add(new_setting)
                    saved_count += 1
                    logger.info(f"添加配置: {key} = {value}")
            
            logger.info(f"总共更新了 {updated_count} 条配置记录")
            logger.info(f"总共添加了 {saved_count} 条配置记录")
            
            # 提交事务
            logger.info("提交数据库事务")
            session.commit()
            logger.info("布局保存成功")
            return True
            
        except Exception as e:
            logger.error(f"保存布局失败: {e}")
            logger.error(f"错误详情: {e}")
            session.rollback()
            return False
        finally:
            DatabaseService.close_session(session)
    
    @classmethod
    def get_default_layout_name(cls, branch_id, document_type):
        """获取默认布局名称"""
        session = DatabaseService.get_session()
        try:
            # 从print_templates表获取默认布局名称
            from sqlalchemy import text
            default_query = text('''
                SELECT layout_name FROM print_templates 
                WHERE branch_id = :branch_id AND document_type = :document_type 
                LIMIT 1
            ''')
            
            default_result = session.execute(default_query, {
                'branch_id': branch_id,
                'document_type': document_type
            }).fetchone()
            
            if default_result:
                return default_result[0]
            else:
                # 如果print_templates表中没有记录，返回第一个布局
                first_layout = session.query(PrintSettings.layout_name)\
                    .filter_by(branch_id=branch_id, document_type=document_type)\
                    .first()
                return first_layout.layout_name if first_layout else None
                
        except Exception as e:
            logger.error(f"获取默认布局名称失败: {str(e)}")
            return None
        finally:
            DatabaseService.close_session(session)
    
    @classmethod
    def create_standard_layouts(cls, branch_id, document_type, layout_name=None, template_name='表格格式'):
        """创建标准布局 - 支持指定布局名称和模板"""
        logger.info(f"为网点{branch_id}创建{document_type}类型的布局: {layout_name or '默认布局'}")
        
        standard_layouts = cls.STANDARD_LAYOUTS.get(document_type, {})
        if not standard_layouts:
            logger.warning(f"未找到{document_type}类型的标准布局模板")
            return
        
        # 如果指定了布局名称，只创建该布局
        if layout_name:
            template_config = standard_layouts.get(template_name)
            if not template_config:
                logger.error(f"未找到模板: {template_name}")
                return
            
            session = DatabaseService.get_session()
            try:
                # 检查布局是否已存在
                existing = session.query(PrintSettings).filter_by(
                    branch_id=branch_id,
                    document_type=document_type,
                    layout_name=layout_name
                ).first()
                
                if existing:
                    logger.info(f"布局 {layout_name} 已存在，跳过创建")
                    return
                
                # 创建布局配置
                elements = template_config['elements']
                is_default = False  # 新创建的布局默认不是默认布局
                
                for element_key, element_value in elements.items():
                    setting = PrintSettings(
                        branch_id=branch_id,
                        document_type=document_type,
                        layout_name=layout_name,
                        setting_key=element_key,
                        setting_value=str(element_value),
                        description=cls._get_element_description(element_key),
                        is_default_layout=is_default,
                        is_active=True
                    )
                    session.add(setting)
                
                session.commit()
                logger.info(f"创建布局成功: {layout_name}")
                
            except Exception as e:
                session.rollback()
                logger.error(f"创建布局失败: {str(e)}")
                raise e
            finally:
                DatabaseService.close_session(session)
        else:
            # 创建所有标准布局
            session = DatabaseService.get_session()
            try:
                for layout_name, layout_config in standard_layouts.items():
                    # 检查布局是否已存在
                    existing = session.query(PrintSettings).filter_by(
                        branch_id=branch_id,
                        document_type=document_type,
                        layout_name=layout_name
                    ).first()
                    
                    if existing:
                        logger.info(f"布局 {layout_name} 已存在，跳过创建")
                        continue
                    
                    # 创建布局配置
                    elements = layout_config['elements']
                    is_default = layout_name == '表格格式'  # 表格格式为默认布局
                    
                    for element_key, element_value in elements.items():
                        setting = PrintSettings(
                            branch_id=branch_id,
                            document_type=document_type,
                            layout_name=layout_name,
                            setting_key=element_key,
                            setting_value=str(element_value),
                            description=cls._get_element_description(element_key),
                            is_default_layout=is_default,
                            is_active=True
                        )
                        session.add(setting)
                    
                    logger.info(f"创建布局: {layout_name}")
                
                session.commit()
                logger.info(f"网点{branch_id}的{document_type}类型标准布局创建完成")
                
            except Exception as e:
                session.rollback()
                logger.error(f"创建标准布局失败: {str(e)}")
                raise e
            finally:
                DatabaseService.close_session(session)
    
    @classmethod
    def _get_layout_description(cls, document_type, layout_name):
        """获取布局描述"""
        return cls.STANDARD_LAYOUTS.get(document_type, {}).get(layout_name, {}).get('description', '')
    
    @classmethod
    def initialize_branch_layouts(cls, branch_id):
        """为新建网点初始化所有单据类型的打印格式"""
        logger.info(f"开始为网点{branch_id}初始化所有单据类型的打印格式...")
        
        # 定义所有支持的单据类型
        document_types = ['exchange', 'reversal', 'balance_adjustment', 'balance_initialization', 'eod_report']
        
        try:
            for document_type in document_types:
                logger.info(f"  初始化{document_type}类型的布局...")
                try:
                    cls.create_standard_layouts(branch_id, document_type)
                    logger.info(f"  ✓ {document_type}类型布局初始化成功")
                except Exception as e:
                    logger.error(f"  ✗ {document_type}类型布局初始化失败: {str(e)}")
                    # 继续初始化其他类型，不因单个类型失败而中断
                    continue
            
            logger.info(f"网点{branch_id}的所有单据类型打印格式初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"为网点{branch_id}初始化打印格式失败: {str(e)}")
            return False

    @classmethod
    def _get_element_description(cls, element_key):
        """获取元素描述"""
        descriptions = {
            'paper_width': '纸张宽度(mm)',
            'paper_height': '纸张高度(mm)',
            'paper_orientation': '纸张方向',
            'margin_top': '上边距(mm)',
            'margin_right': '右边距(mm)',
            'margin_bottom': '下边距(mm)',
            'margin_left': '左边距(mm)',
            'font_family': '字体族',
            'font_size': '字体大小',
            'font_color': '字体颜色',
            'logo_show': '显示Logo',
            'logo_top': 'Logo顶部位置(mm)',
            'logo_left': 'Logo左侧位置(mm)',
            'logo_width': 'Logo宽度(mm)',
            'logo_height': 'Logo高度(mm)',
            'logo_data': 'Logo图片数据',
            'logo_alignment': 'Logo对齐方式',
            'logo_margin': 'Logo边距(mm)',
            'title_show': '显示标题',
            'title_top': '标题顶部位置(mm)',
            'title_left': '标题左侧位置(mm)',
            'title_width': '标题宽度(mm)',
            'title_height': '标题高度(mm)',
            'title_align': '标题对齐方式',
            'title_size': '标题字体大小',
            'title_bold': '标题加粗',
            'branch_show': '显示网点信息',
            'branch_top': '网点信息顶部位置(mm)',
            'branch_left': '网点信息左侧位置(mm)',
            'branch_width': '网点信息宽度(mm)',
            'branch_height': '网点信息高度(mm)',
            'branch_align': '网点信息对齐方式',
            'content_show': '显示内容',
            'content_top': '内容顶部位置(mm)',
            'content_left': '内容左侧位置(mm)',
            'content_width': '内容宽度(mm)',
            'content_height': '内容高度(mm)',
            'content_style': '内容样式',
            'content_border': '显示内容边框',
            'signature_show': '显示签名',
            'signature_style': '签名样式',
            'signature_top': '签名顶部位置(mm)',
            'signature_left': '签名左侧位置(mm)',
            'signature_width': '签名宽度(mm)',
            'signature_height': '签名高度(mm)',
            'watermark_show': '显示水印',
            'watermark_text': '水印文字',
            'watermark_opacity': '水印透明度'
        }
        return descriptions.get(element_key, element_key) 