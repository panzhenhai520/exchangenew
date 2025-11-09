"""
HTML模板服务 - 生成标准化的HTML打印模板
"""
import json
from typing import Dict, Any, Optional
from datetime import datetime

class HTMLTemplateService:
    """HTML模板生成服务"""
    
    def __init__(self):
        self.base_style = """
        <style>
            @page {
                size: A4;
                margin: 0;
                padding: 0;
            }
            
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'SimHei', 'Microsoft YaHei', sans-serif;
                font-size: 12px;
                line-height: 1.4;
                color: #000;
                width: 210mm;
                min-height: 297mm;
                background: white;
                position: relative;
            }
            
            .receipt-container {
                width: 100%;
                height: 100%;
                position: relative;
                padding: 0;
            }
            
            .element {
                position: absolute;
                box-sizing: border-box;
            }
            
            .logo {
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .logo img {
                max-width: 100%;
                max-height: 100%;
                object-fit: contain;
            }
            
            .title {
                font-size: 18px;
                font-weight: bold;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .subtitle {
                font-size: 14px;
                color: #666;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .branch {
                font-size: 14px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .content {
                font-size: 12px;
                overflow: hidden;
            }
            
            .content table {
                width: 100%;
                border-collapse: collapse;
                font-size: 11px;
            }
            
            .content table th,
            .content table td {
                border: 1px solid #000;
                padding: 4px;
                text-align: left;
                vertical-align: middle;
            }
            
            .content table th {
                background-color: #f5f5f5;
                font-weight: bold;
                text-align: center;
            }
            
            .info-section {
                margin-bottom: 10px;
            }
            
            .info-row {
                display: flex;
                margin-bottom: 5px;
            }
            
            .info-label {
                font-weight: bold;
                min-width: 80px;
            }
            
            .signature {
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 12px;
            }
            
            .watermark {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%) rotate(-45deg);
                font-size: 72px;
                color: rgba(0, 0, 0, 0.1);
                pointer-events: none;
                z-index: 1000;
            }
            
            .text-left { text-align: left !important; }
            .text-center { text-align: center !important; }
            .text-right { text-align: right !important; }
        </style>
        """
    
    def generate_exchange_receipt(self, data: Dict[str, Any], layout_config: Dict[str, Any]) -> str:
        """生成兑换单据HTML"""
        
        # 获取布局配置
        elements = layout_config.get('value', {})
        
        # 构建HTML内容
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>外币兑换单据</title>
            {self.base_style}
        </head>
        <body>
            <div class="receipt-container">
                {self._generate_logo_element(data, elements.get('logo', {}))}
                {self._generate_title_element(data, elements.get('title', {}))}
                {self._generate_subtitle_element(data, elements.get('subtitle', {}))}
                {self._generate_branch_element(data, elements.get('branch', {}))}
                {self._generate_content_element(data, elements.get('content', {}))}
                {self._generate_signature_element(data, elements.get('signature', {}))}
                {self._generate_watermark_element(elements.get('watermark', {}))}
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _generate_logo_element(self, data: Dict[str, Any], config: Dict[str, Any]) -> str:
        """生成Logo元素"""
        if not config.get('visible', True):
            return ""
        
        logo_data = data.get('logo_data')
        if not logo_data:
            return ""
        
        style = self._build_element_style(config)
        
        return f"""
        <div class="element logo" style="{style}">
            <img src="data:image/png;base64,{logo_data}" alt="Logo" />
        </div>
        """
    
    def _generate_title_element(self, data: Dict[str, Any], config: Dict[str, Any]) -> str:
        """生成标题元素"""
        if not config.get('visible', True):
            return ""
        
        title = data.get('title', '外币兑换单据')
        style = self._build_element_style(config)
        
        return f"""
        <div class="element title" style="{style}">
            {title}
        </div>
        """
    
    def _generate_subtitle_element(self, data: Dict[str, Any], config: Dict[str, Any]) -> str:
        """生成副标题元素"""
        if not config.get('visible', True):
            return ""
        
        subtitle = data.get('subtitle', 'Foreign Exchange Receipt')
        style = self._build_element_style(config)
        
        return f"""
        <div class="element subtitle" style="{style}">
            {subtitle}
        </div>
        """
    
    def _generate_branch_element(self, data: Dict[str, Any], config: Dict[str, Any]) -> str:
        """生成网点信息元素"""
        if not config.get('visible', True):
            return ""
        
        branch_name = data.get('branch_name', '总行营业部')
        style = self._build_element_style(config)
        
        return f"""
        <div class="element branch" style="{style}">
            {branch_name}
        </div>
        """
    
    def _generate_content_element(self, data: Dict[str, Any], config: Dict[str, Any]) -> str:
        """生成内容元素"""
        if not config.get('visible', True):
            return ""
        
        style = self._build_element_style(config)
        
        # 基本信息
        info_html = self._generate_basic_info(data)
        
        # 交易表格
        table_html = self._generate_transaction_table(data)
        
        return f"""
        <div class="element content" style="{style}">
            {info_html}
            {table_html}
        </div>
        """
    
    def _generate_basic_info(self, data: Dict[str, Any]) -> str:
        """生成基本信息部分"""
        return f"""
        <div class="info-section">
            <div class="info-row">
                <span class="info-label">交易编号:</span>
                <span>{data.get('transaction_no', 'N/A')}</span>
            </div>
            <div class="info-row">
                <span class="info-label">交易时间:</span>
                <span>{data.get('transaction_date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}</span>
            </div>
            <div class="info-row">
                <span class="info-label">操作员:</span>
                <span>{data.get('operator', 'N/A')}</span>
            </div>
        </div>
        """
    
    def _generate_transaction_table(self, data: Dict[str, Any]) -> str:
        """生成交易表格"""
        transactions = data.get('transactions', [])
        
        if not transactions:
            # 使用示例数据
            transactions = [{
                'transaction_no': data.get('transaction_no', 'A005202506250001'),
                'date': data.get('transaction_date', '2025-06-25'),
                'amount': '1000.00',
                'exchange_amount': '6800.00',
                'rate': '6.8000',
                'customer_name': '张三',
                'id_number': '110101199001011234',
                'purpose': '旅游',
                'remark': '现金兑换'
            }]
        
        table_rows = ""
        for tx in transactions:
            table_rows += f"""
            <tr>
                <td>{tx.get('transaction_no', '')}</td>
                <td>{tx.get('date', '')}</td>
                <td class="text-right">{tx.get('amount', '')}</td>
                <td class="text-right">{tx.get('exchange_amount', '')}</td>
                <td class="text-right">{tx.get('rate', '')}</td>
                <td>{tx.get('customer_name', '')}</td>
                <td>{tx.get('id_number', '')}</td>
                <td>{tx.get('purpose', '')}</td>
                <td>{tx.get('remark', '')}</td>
            </tr>
            """
        
        return f"""
        <table>
            <thead>
                <tr>
                    <th>交易编号</th>
                    <th>日期</th>
                    <th>金额</th>
                    <th>兑换金额</th>
                    <th>汇率</th>
                    <th>客户姓名</th>
                    <th>证件号码</th>
                    <th>交易用途</th>
                    <th>备注</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
        """
    
    def _generate_signature_element(self, data: Dict[str, Any], config: Dict[str, Any]) -> str:
        """生成签名元素"""
        if not config.get('visible', True):
            return ""
        
        style = self._build_element_style(config)
        
        return f"""
        <div class="element signature" style="{style}">
            <div>客户签名：________________　　操作员：{data.get('operator', 'N/A')}</div>
        </div>
        """
    
    def _generate_watermark_element(self, config: Dict[str, Any]) -> str:
        """生成水印元素"""
        if not config.get('visible', False):
            return ""
        
        text = config.get('text', '样本')
        opacity = config.get('opacity', 0.1)
        
        return f"""
        <div class="watermark" style="opacity: {opacity};">
            {text}
        </div>
        """
    
    def _build_element_style(self, config: Dict[str, Any]) -> str:
        """构建元素样式"""
        styles = []
        
        # 位置和尺寸 (直接使用mm单位)
        if 'top' in config:
            styles.append(f"top: {config['top']}mm")
        if 'left' in config:
            styles.append(f"left: {config['left']}mm")
        if 'width' in config and config['width'] > 0:
            styles.append(f"width: {config['width']}mm")
        if 'height' in config and config['height'] > 0:
            styles.append(f"height: {config['height']}mm")
        
        # 文本对齐
        if 'textAlign' in config:
            styles.append(f"text-align: {config['textAlign']}")
            styles.append(f"justify-content: {self._get_flex_align(config['textAlign'])}")
        
        return "; ".join(styles)
    
    def _get_flex_align(self, text_align: str) -> str:
        """将文本对齐转换为flex对齐"""
        align_map = {
            'left': 'flex-start',
            'center': 'center',
            'right': 'flex-end'
        }
        return align_map.get(text_align, 'flex-start') 