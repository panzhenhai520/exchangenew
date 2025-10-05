"""
HTML转PDF服务 - 使用Puppeteer将HTML转换为PDF
"""
import asyncio
import tempfile
import os
import logging
import threading
from typing import Dict, Any, Optional
from .html_template_service import HTMLTemplateService
from .layout_service import LayoutService

logger = logging.getLogger(__name__)

class HTMLToPDFService:
    """HTML转PDF服务 - 线程安全版本"""
    
    def __init__(self):
        self.html_template_service = HTMLTemplateService()
        self.layout_service = LayoutService()
    
    def generate_pdf(self, 
                    file_path: str,
                    data: Dict[str, Any],
                    branch_id: Optional[int] = None,
                    document_type: str = 'exchange') -> bool:
        """
        生成PDF文件 - 线程安全版本
        
        Args:
            file_path: PDF文件保存路径
            data: 打印数据
            branch_id: 网点ID
            document_type: 单据类型
            
        Returns:
            bool: 生成是否成功
        """
        try:
            logger.info(f"开始HTML转PDF生成 - 文件路径: {file_path}")
            
            # 1. 生成HTML内容
            logger.info("生成HTML模板...")
            layout_config = self._get_layout_config_sync(branch_id, document_type)
            html_content = self.html_template_service.generate_exchange_receipt(data, layout_config)
            
            # 2. 尝试使用weasyprint（如果可用）
            try:
                import weasyprint
                logger.info("使用WeasyPrint进行HTML转PDF...")
                return self._convert_with_weasyprint(html_content, file_path)
            except ImportError:
                logger.info("WeasyPrint不可用，尝试使用pyppeteer...")
            
            # 3. 使用pyppeteer（在新线程中运行以避免信号问题）
            return self._convert_with_pyppeteer_thread(html_content, file_path)
                
        except Exception as e:
            logger.error(f"HTML转PDF生成失败: {str(e)}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return False
    
    def _convert_with_weasyprint(self, html_content: str, output_path: str) -> bool:
        """使用WeasyPrint转换HTML为PDF"""
        try:
            import weasyprint
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # 生成PDF
            document = weasyprint.HTML(string=html_content)
            document.write_pdf(output_path)
            
            logger.info(f"WeasyPrint PDF生成成功: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"WeasyPrint转换失败: {str(e)}")
            return False
    
    def _convert_with_pyppeteer_thread(self, html_content: str, output_path: str) -> bool:
        """在新线程中使用pyppeteer转换HTML为PDF"""
        try:
            import threading
            import queue
            
            result_queue = queue.Queue()
            
            def run_in_thread():
                """在新线程中运行pyppeteer"""
                try:
                    # 在新线程中创建新的事件循环
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        success = loop.run_until_complete(
                            self._convert_html_to_pdf_async(html_content, output_path)
                        )
                        result_queue.put(('success', success))
                    finally:
                        loop.close()
                        
                except Exception as e:
                    result_queue.put(('error', str(e)))
            
            # 启动线程
            thread = threading.Thread(target=run_in_thread)
            thread.daemon = True
            thread.start()
            
            # 等待结果（最多30秒）
            thread.join(timeout=30)
            
            if thread.is_alive():
                logger.error("pyppeteer转换超时")
                return False
            
            # 获取结果
            try:
                result_type, result_value = result_queue.get_nowait()
                if result_type == 'success':
                    return result_value
                else:
                    logger.error(f"pyppeteer转换失败: {result_value}")
                    return False
            except queue.Empty:
                logger.error("未能获取pyppeteer转换结果")
                return False
                
        except Exception as e:
            logger.error(f"pyppeteer线程转换失败: {str(e)}")
            return False
    
    async def _convert_html_to_pdf_async(self, html_content: str, output_path: str) -> bool:
        """异步转换HTML为PDF"""
        try:
            from pyppeteer import launch
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # 启动浏览器 - 禁用信号处理，移除有问题的参数
            browser = await launch(
                headless=True,
                handleSIGINT=False,  # 禁用SIGINT信号处理
                handleSIGTERM=False,  # 禁用SIGTERM信号处理
                handleSIGHUP=False,   # 禁用SIGHUP信号处理
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--disable-default-apps',
                    '--disable-background-timer-throttling',
                    '--disable-renderer-backgrounding',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-extensions',
                    '--disable-plugins'
                ]
            )
            
            try:
                page = await browser.newPage()
                
                # 设置页面内容
                await page.setContent(html_content)
                
                # 生成PDF
                await page.pdf({
                    'path': output_path,
                    'format': 'A4',
                    'margin': {
                        'top': '10mm',
                        'bottom': '10mm',
                        'left': '10mm',
                        'right': '10mm'
                    },
                    'printBackground': True
                })
                
                await page.close()
                logger.info(f"pyppeteer PDF生成成功: {output_path}")
                return True
                
            finally:
                await browser.close()
                
        except Exception as e:
            logger.error(f"pyppeteer异步转换失败: {str(e)}")
            return False
    
    def _get_layout_config_sync(self, branch_id: Optional[int], document_type: str) -> Dict[str, Any]:
        """同步获取布局配置"""
        try:
            if not branch_id:
                return self._get_default_layout_config()
            
            # 获取网点布局配置
            layout_name = self.layout_service.get_default_layout_name(branch_id, document_type)
            layout_elements = self.layout_service.get_layout_elements(branch_id, document_type, layout_name)
            
            # layout_elements现在返回的是字典，而不是对象列表
            # 查找element_positions配置
            element_positions = None
            
            # 检查是否直接包含element_positions键
            if 'element_positions' in layout_elements:
                element_positions_str = layout_elements['element_positions']
                # 尝试解析JSON字符串
                try:
                    import json
                    if isinstance(element_positions_str, str):
                        element_positions = json.loads(element_positions_str)
                    else:
                        element_positions = element_positions_str
                except json.JSONDecodeError:
                    logger.warning(f"无法解析element_positions JSON: {element_positions_str}")
                    element_positions = None
            
            if element_positions and isinstance(element_positions, dict):
                # 转换像素坐标为mm坐标
                converted_config = self._convert_coordinates_to_mm(element_positions)
                logger.info(f"使用网点布局配置: {layout_name}")
                return converted_config
            else:
                # 使用默认配置
                logger.info("使用默认布局配置")
                return self._get_default_layout_config()
                
        except Exception as e:
            logger.error(f"获取布局配置失败: {str(e)}")
            return self._get_default_layout_config()
    
    def _convert_coordinates_to_mm(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """将像素坐标转换为毫米坐标"""
        # 转换比例：1px = 0.352778mm (基于96 DPI)
        PX_TO_MM = 0.352778
        
        def convert_element(element_config):
            if isinstance(element_config, dict):
                converted = element_config.copy()
                
                # 转换位置和尺寸
                for key in ['top', 'left', 'width', 'height']:
                    if key in converted and isinstance(converted[key], (int, float)):
                        converted[key] = round(converted[key] * PX_TO_MM, 2)
                
                return converted
            return element_config
        
        if 'value' in config:
            converted_config = {'value': {}}
            for element_name, element_config in config['value'].items():
                converted_config['value'][element_name] = convert_element(element_config)
            return converted_config
        
        return config
    
    def _get_default_layout_config(self) -> Dict[str, Any]:
        """获取默认布局配置"""
        return {
            'value': {
                'logo': {'top': 5, 'left': 105, 'width': 90, 'height': 45, 'visible': True, 'textAlign': 'center'},
                'title': {'top': 25, 'left': 105, 'width': 0, 'height': 15, 'visible': True, 'textAlign': 'center'},
                'subtitle': {'top': 45, 'left': 105, 'width': 0, 'height': 12, 'visible': True, 'textAlign': 'center'},
                'branch': {'top': 65, 'left': 105, 'width': 0, 'height': 11, 'visible': True, 'textAlign': 'center'},
                'content': {'top': 85, 'left': 20, 'width': 170, 'height': 120, 'visible': True, 'textAlign': 'left'},
                'signature': {'top': 220, 'left': 20, 'width': 170, 'height': 30, 'visible': True, 'textAlign': 'center'},
                'watermark': {'visible': False, 'text': '样本', 'opacity': 0.1}
            }
        } 