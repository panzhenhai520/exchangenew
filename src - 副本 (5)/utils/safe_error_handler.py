"""
后端安全错误处理工具
用于屏蔽敏感的数据库和系统信息，提供友好的错误响应
"""

import re
import logging
from flask import jsonify

# 配置日志
logger = logging.getLogger(__name__)

# 敏感关键词模式（正则表达式）
SENSITIVE_PATTERNS = [
    # 数据库相关
    r'sqlite.*error',
    r'mysql.*error',
    r'postgresql.*error',
    r'database.*error',
    r'table.*not.*found',
    r'column.*not.*found',
    r'foreign.*key.*constraint',
    r'unique.*constraint',
    r'primary.*key.*constraint',
    r'check.*constraint',
    r'not.*null.*constraint',
    
    # SQLAlchemy相关
    r'sqlalchemy\..*',
    r'operationalerror',
    r'integrityerror',
    r'dataerror',
    r'programmingerror',
    r'interfaceerror',
    r'databaseerror',
    
    # 系统路径和文件
    r'traceback.*',
    r'file\s+".*"',
    r'line\s+\d+',
    r'module\s+.*',
    r'function\s+.*',
    r'/usr/.*',
    r'/var/.*',
    r'/home/.*',
    r'/opt/.*',
    r'[cd]:\\.*',
    
    # Python相关
    r'python.*error',
    r'flask.*error',
    r'werkzeug.*error',
    r'jinja2.*error',
    r'attributeerror',
    r'typeerror',
    r'valueerror',
    r'keyerror',
    r'indexerror',
    r'nameerror',
    
    # 网络和服务器信息
    r'localhost:\d+',
    r'127\.0\.0\.1:\d+',
    r'0\.0\.0\.0:\d+',
    r'port\s+\d+',
    r'socket.*error',
    r'connection.*refused',
    r'connection.*timeout',
    r'host.*unreachable'
]

# 友好的错误消息映射
FRIENDLY_MESSAGES = {
    # 数据库相关错误
    'constraint': '数据约束冲突，请检查输入数据',
    'foreign_key': '数据关联错误，请先处理相关数据',
    'unique': '数据已存在，请检查后重试',
    'not_null': '必填字段不能为空',
    'data_too_long': '输入数据过长，请缩短后重试',
    
    # 权限相关
    'permission_denied': '权限不足，请联系管理员',
    'access_denied': '访问被拒绝，请检查权限',
    'unauthorized': '未授权访问，请重新登录',
    
    # 业务逻辑错误
    'validation_error': '数据验证失败，请检查输入',
    'business_rule': '业务规则验证失败',
    'operation_failed': '操作失败，请稍后重试',
    
    # 系统错误
    'database_error': '数据库操作失败，请稍后重试',
    'server_error': '服务器内部错误，请联系管理员',
    'network_error': '网络连接异常，请检查网络设置',
    
    # 默认消息
    'default': '操作失败，请稍后重试或联系系统管理员'
}

def contains_sensitive_info(message):
    """
    检查错误消息是否包含敏感信息
    
    Args:
        message (str): 错误消息
        
    Returns:
        bool: 是否包含敏感信息
    """
    if not message or not isinstance(message, str):
        return False
    
    message_lower = message.lower()
    
    # 检查是否匹配敏感模式
    for pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, message_lower, re.IGNORECASE):
            return True
    
    return False

def get_safe_error_message(error, default_message="操作失败"):
    """
    获取安全的错误消息
    
    Args:
        error: 异常对象或错误消息
        default_message (str): 默认错误消息
        
    Returns:
        str: 安全的错误消息
    """
    try:
        # 提取错误消息
        if hasattr(error, 'message'):
            message = str(error.message)
        elif hasattr(error, 'args') and error.args:
            message = str(error.args[0])
        else:
            message = str(error)
        
        # 检查是否包含敏感信息
        if contains_sensitive_info(message):
            # 根据错误类型返回友好消息
            message_lower = message.lower()
            
            if any(keyword in message_lower for keyword in ['constraint', 'foreign key']):
                return FRIENDLY_MESSAGES['constraint']
            elif any(keyword in message_lower for keyword in ['unique', 'duplicate']):
                return FRIENDLY_MESSAGES['unique']
            elif any(keyword in message_lower for keyword in ['not null', 'required']):
                return FRIENDLY_MESSAGES['not_null']
            elif any(keyword in message_lower for keyword in ['permission', 'access']):
                return FRIENDLY_MESSAGES['permission_denied']
            elif any(keyword in message_lower for keyword in ['database', 'sql']):
                return FRIENDLY_MESSAGES['database_error']
            else:
                return FRIENDLY_MESSAGES['default']
        else:
            # 消息安全，可以返回
            return message
            
    except Exception as e:
        # 错误处理过程中出错，返回最安全的默认消息
        logger.error(f"Error in get_safe_error_message: {e}")
        return default_message

def safe_error_response(error, message=None, status_code=500):
    """
    创建安全的错误响应
    
    Args:
        error: 异常对象
        message (str): 自定义错误消息
        status_code (int): HTTP状态码
        
    Returns:
        tuple: (response, status_code)
    """
    try:
        # 记录原始错误（用于调试）
        logger.error(f"Original error: {error}", exc_info=True)
        
        # 获取安全的错误消息
        if message:
            safe_message = message
        else:
            safe_message = get_safe_error_message(error)
        
        # 创建响应
        response = {
            'success': False,
            'message': safe_message
        }
        
        return jsonify(response), status_code
        
    except Exception as e:
        # 最后的安全网
        logger.error(f"Error in safe_error_response: {e}")
        return jsonify({
            'success': False,
            'message': FRIENDLY_MESSAGES['default']
        }), 500

def handle_database_error(error):
    """
    处理数据库相关错误
    
    Args:
        error: 数据库异常对象
        
    Returns:
        tuple: (response, status_code)
    """
    error_message = str(error)
    
    # 根据具体的数据库错误类型返回友好消息
    if 'foreign key constraint' in error_message.lower():
        return safe_error_response(error, '该数据存在关联记录，无法删除', 400)
    elif 'unique constraint' in error_message.lower():
        return safe_error_response(error, '数据已存在，请检查后重试', 400)
    elif 'not null constraint' in error_message.lower():
        return safe_error_response(error, '必填字段不能为空', 400)
    elif 'check constraint' in error_message.lower():
        return safe_error_response(error, '数据格式不正确', 400)
    else:
        return safe_error_response(error, FRIENDLY_MESSAGES['database_error'], 500)

def handle_validation_error(error):
    """
    处理数据验证错误
    
    Args:
        error: 验证异常对象
        
    Returns:
        tuple: (response, status_code)
    """
    return safe_error_response(error, FRIENDLY_MESSAGES['validation_error'], 400)

def handle_permission_error(error):
    """
    处理权限相关错误
    
    Args:
        error: 权限异常对象
        
    Returns:
        tuple: (response, status_code)
    """
    return safe_error_response(error, FRIENDLY_MESSAGES['permission_denied'], 403)

# 装饰器：安全的API错误处理
def safe_api_error_handler(func):
    """
    装饰器：为API函数提供安全的错误处理
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"API error in {func.__name__}: {e}", exc_info=True)
            return safe_error_response(e)
    
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper 