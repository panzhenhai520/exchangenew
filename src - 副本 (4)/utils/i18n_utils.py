import json
import os
from flask import request, has_request_context

class I18nUtils:
    """后端国际化工具类"""
    
    _messages = {}
    _loaded = False
    
    @classmethod
    def _load_messages(cls):
        """加载所有语言的消息"""
        if cls._loaded:
            return
            
        # 使用模块化翻译文件
        cls._messages = {}
        
        # 定义需要加载的模块
        modules = ['auth', 'reports', 'eod']
        
        for module in modules:
            # 加载模块的翻译
            module_translations = {
                'zh-CN': f'i18n/modules/{module}/zh-CN.js',
                'en-US': f'i18n/modules/{module}/en-US.js', 
                'th-TH': f'i18n/modules/{module}/th-TH.js'
            }
            
            for lang, file_path in module_translations.items():
                try:
                    if os.path.exists(file_path):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # 简单的JS对象解析（移除export default和最后的;）
                            content = content.replace('export default', '').replace(';', '')
                            # 解析JSON
                            data = json.loads(content)
                            
                            # 初始化语言字典
                            if lang not in cls._messages:
                                cls._messages[lang] = {}
                            
                            # 合并模块数据 - 处理嵌套结构
                            if module in data:
                                # 如果数据是嵌套的（如 {"eod": {...}}），提取内部数据
                                cls._messages[lang].update(data[module])
                            else:
                                # 如果数据是直接的，直接合并
                                cls._messages[lang].update(data)
                            print(f"成功加载 {lang} 的 {module} 模块翻译")
                    else:
                        print(f"翻译文件不存在: {file_path}")
                        # 如果文件不存在，使用默认消息
                        if lang not in cls._messages:
                            cls._messages[lang] = {}
                        
                        if module == 'auth':
                            cls._messages[lang][module] = {
                                'eod_permission_granted': '有权限进行日结操作',
                                'eod_permission_denied': '无权限进行日结操作',
                                'missing_permission': '缺少权限',
                                'business_locked': '营业已锁定，无法进行此操作',
                                'session_required': '缺少会话ID，无法进行日结操作',
                                'transaction_locked': '当前网点营业已锁定（日结进行中），无法进行交易操作',
                                'balance_locked': '当前网点营业已锁定（日结进行中），无法进行余额操作'
                            }
                        elif module == 'reports':
                            # 根据语言提供不同的默认消息
                            if lang == 'zh-CN':
                                cls._messages[lang][module] = {
                                    'difference_adjustment_title': '日结差额调节报告',
                                    'difference_report_title': '日结差额报告',
                                    'eod_id': '日结编号',
                                    'eod_date': '日结日期',
                                    'eod_time': '日结时间',
                                    'operator': '操作员',
                                    'adjustment_details': '差额调节明细',
                                    'difference_details': '差额明细',
                                    'theoretical_balance': '理论库存',
                                    'actual_balance': '实际库存',
                                    'adjust_amount': '调节金额',
                                    'difference': '差异',
                                    'reason': '调节原因',
                                    'signature_area': '签名区域',
                                    'operator_signature': '操作员签名',
                                    'supervisor_signature': '主管签名'
                                }
                            elif lang == 'en-US':
                                cls._messages[lang][module] = {
                                    'difference_adjustment_title': 'EOD Difference Adjustment Report',
                                    'difference_report_title': 'EOD Difference Report',
                                    'eod_id': 'EOD ID',
                                    'eod_date': 'EOD Date',
                                    'eod_time': 'EOD Time',
                                    'operator': 'Operator',
                                    'adjustment_details': 'Adjustment Details',
                                    'difference_details': 'Difference Details',
                                    'theoretical_balance': 'Theoretical Balance',
                                    'actual_balance': 'Actual Balance',
                                    'adjust_amount': 'Adjust Amount',
                                    'difference': 'Difference',
                                    'reason': 'Reason',
                                    'signature_area': 'Signature Area',
                                    'operator_signature': 'Operator Signature',
                                    'supervisor_signature': 'Supervisor Signature'
                                }
                            elif lang == 'th-TH':
                                cls._messages[lang][module] = {
                                    'difference_adjustment_title': 'รายงานการปรับปรุงส่วนต่างการปิดบัญชี',
                                    'difference_report_title': 'รายงานส่วนต่างการปิดบัญชี',
                                    'eod_id': 'รหัสการปิดบัญชี',
                                    'eod_date': 'วันที่ปิดบัญชี',
                                    'eod_time': 'เวลาปิดบัญชี',
                                    'operator': 'ผู้ดำเนินการ',
                                    'adjustment_details': 'รายละเอียดการปรับปรุง',
                                    'difference_details': 'รายละเอียดส่วนต่าง',
                                    'theoretical_balance': 'ยอดตามทฤษฎี',
                                    'actual_balance': 'ยอดจริง',
                                    'adjust_amount': 'จำนวนการปรับปรุง',
                                    'difference': 'ส่วนต่าง',
                                    'reason': 'เหตุผล',
                                    'signature_area': 'พื้นที่ลงนาม',
                                    'operator_signature': 'ลายเซ็นผู้ดำเนินการ',
                                    'supervisor_signature': 'ลายเซ็นผู้ดูแล'
                                }
                        elif module == 'eod':
                            # 根据语言提供不同的默认消息
                            if lang == 'zh-CN':
                                cls._messages[lang][module] = {
                                    'difference_report_title': '差额报告'
                                }
                            elif lang == 'en-US':
                                cls._messages[lang][module] = {
                                    'difference_report_title': 'Difference Report'
                                }
                            elif lang == 'th-TH':
                                cls._messages[lang][module] = {
                                    'difference_report_title': 'รายงานส่วนต่าง'
                                }
                except Exception as e:
                    print(f"加载翻译文件失败 {file_path}: {e}")
                    # 使用默认消息
                    if lang not in cls._messages:
                        cls._messages[lang] = {}
                    
                    if module == 'auth':
                        cls._messages[lang][module] = {
                            'eod_permission_granted': '有权限进行日结操作',
                            'eod_permission_denied': '无权限进行日结操作',
                            'missing_permission': '缺少权限',
                            'business_locked': '营业已锁定，无法进行此操作',
                            'session_required': '缺少会话ID，无法进行日结操作',
                            'transaction_locked': '当前网点营业已锁定（日结进行中），无法进行交易操作',
                            'balance_locked': '当前网点营业已锁定（日结进行中），无法进行余额操作'
                        }
                    elif module == 'reports':
                        # 根据语言提供不同的默认消息
                        if lang == 'zh-CN':
                            cls._messages[lang][module] = {
                                'difference_adjustment_title': '日结差额调节报告',
                                'difference_report_title': '日结差额报告',
                                'eod_id': '日结编号',
                                'eod_date': '日结日期',
                                'eod_time': '日结时间',
                                'operator': '操作员',
                                'adjustment_details': '差额调节明细',
                                'difference_details': '差额明细',
                                'theoretical_balance': '理论库存',
                                'actual_balance': '实际库存',
                                'adjust_amount': '调节金额',
                                'difference': '差异',
                                'reason': '调节原因',
                                'signature_area': '签名区域',
                                'operator_signature': '操作员签名',
                                'supervisor_signature': '主管签名'
                            }
                        elif lang == 'en-US':
                            cls._messages[lang][module] = {
                                'difference_adjustment_title': 'EOD Difference Adjustment Report',
                                'difference_report_title': 'EOD Difference Report',
                                'eod_id': 'EOD ID',
                                'eod_date': 'EOD Date',
                                'eod_time': 'EOD Time',
                                'operator': 'Operator',
                                'adjustment_details': 'Adjustment Details',
                                'difference_details': 'Difference Details',
                                'theoretical_balance': 'Theoretical Balance',
                                'actual_balance': 'Actual Balance',
                                'adjust_amount': 'Adjust Amount',
                                'difference': 'Difference',
                                'reason': 'Reason',
                                'signature_area': 'Signature Area',
                                'operator_signature': 'Operator Signature',
                                'supervisor_signature': 'Supervisor Signature'
                            }
                        elif lang == 'th-TH':
                            cls._messages[lang][module] = {
                                'difference_adjustment_title': 'รายงานการปรับปรุงส่วนต่างการปิดบัญชี',
                                'difference_report_title': 'รายงานส่วนต่างการปิดบัญชี',
                                'eod_id': 'รหัสการปิดบัญชี',
                                'eod_date': 'วันที่ปิดบัญชี',
                                'eod_time': 'เวลาปิดบัญชี',
                                'operator': 'ผู้ดำเนินการ',
                                'adjustment_details': 'รายละเอียดการปรับปรุง',
                                'difference_details': 'รายละเอียดส่วนต่าง',
                                'theoretical_balance': 'ยอดตามทฤษฎี',
                                'actual_balance': 'ยอดจริง',
                                'adjust_amount': 'จำนวนการปรับปรุง',
                                'difference': 'ส่วนต่าง',
                                'reason': 'เหตุผล',
                                'signature_area': 'พื้นที่ลงนาม',
                                'operator_signature': 'ลายเซ็นผู้ดำเนินการ',
                                'supervisor_signature': 'ลายเซ็นผู้ดูแล'
                            }
        
        cls._loaded = True
    
    @classmethod
    def get_language(cls):
        """从请求头获取客户端语言"""
        # 检查是否有请求上下文
        if not has_request_context():
            return 'zh-CN'  # 默认中文
            
        # 优先从请求头获取
        accept_language = request.headers.get('Accept-Language', '')
        
        # 解析Accept-Language头
        if 'zh' in accept_language.lower():
            return 'zh-CN'
        elif 'th' in accept_language.lower():
            return 'th-TH'
        elif 'en' in accept_language.lower():
            return 'en-US'
        
        # 默认中文
        return 'zh-CN'
    
    @classmethod
    def get_message(cls, key_path, language=None, **kwargs):
        """
        获取国际化消息
        
        Args:
            key_path: 消息键路径，如 'auth.eod_permission_denied'
            language: 语言代码，如果不提供则自动检测
            **kwargs: 用于格式化消息的参数
        
        Returns:
            格式化后的消息字符串
        """
        cls._load_messages()
        
        if language is None:
            language = cls.get_language()
        
        # 语言代码映射
        language_mapping = {
            'zh': 'zh-CN',
            'en': 'en-US', 
            'th': 'th-TH',
            'zh-CN': 'zh-CN',
            'en-US': 'en-US',
            'th-TH': 'th-TH'
        }
        
        # 获取标准化的语言代码
        normalized_language = language_mapping.get(language, 'zh-CN')
        
        # 获取消息
        messages = cls._messages.get(normalized_language, {})
        
        # 解析键路径
        keys = key_path.split('.')
        message = messages
        
        for key in keys:
            if isinstance(message, dict) and key in message:
                message = message[key]
            else:
                # 如果找不到，尝试使用中文作为fallback
                if normalized_language != 'zh-CN':
                    return cls.get_message(key_path, 'zh-CN', **kwargs)
                else:
                    # 返回键路径作为默认值
                    return key_path
        
        # 格式化消息
        if isinstance(message, str) and kwargs:
            try:
                return message.format(**kwargs)
            except (KeyError, ValueError):
                return message
        
        return message if isinstance(message, str) else key_path

# 便捷函数
def t(key_path, language=None, **kwargs):
    """获取国际化消息的简便函数"""
    return I18nUtils.get_message(key_path, language, **kwargs) 