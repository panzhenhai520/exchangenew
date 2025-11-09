#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
语言工具函数
用于从HTTP请求中获取当前用户的语言设置
"""

from flask import request
from typing import Optional

def get_current_language(default_language: str = 'zh-CN') -> str:
    """
    从HTTP请求中获取当前用户的语言设置
    
    Args:
        default_language: 默认语言，如果无法获取则使用此语言
        
    Returns:
        str: 语言代码 ('zh-CN', 'en-US', 'th-TH')
    """
    try:
        # 优先从请求头中获取语言设置
        # 1. 查看是否有专门的语言头
        if hasattr(request, 'headers') and request.headers:
            # 检查自定义语言头
            custom_lang = request.headers.get('X-Language') or request.headers.get('Language')
            if custom_lang:
                return normalize_language(custom_lang)
            
            # 检查Accept-Language头
            accept_language = request.headers.get('Accept-Language')
            if accept_language:
                # 解析Accept-Language头，取第一个语言
                languages = accept_language.split(',')
                if languages:
                    primary_lang = languages[0].split(';')[0].strip()
                    return normalize_language(primary_lang)
        
        # 2. 从查询参数中获取
        if hasattr(request, 'args') and request.args:
            lang_param = request.args.get('lang') or request.args.get('language')
            if lang_param:
                return normalize_language(lang_param)
        
        # 3. 从POST参数中获取
        if hasattr(request, 'json') and request.json:
            lang_json = request.json.get('language') or request.json.get('lang')
            if lang_json:
                return normalize_language(lang_json)
        
        # 4. 从form数据中获取
        if hasattr(request, 'form') and request.form:
            lang_form = request.form.get('language') or request.form.get('lang')
            if lang_form:
                return normalize_language(lang_form)
        
    except Exception:
        # 如果获取失败，使用默认语言
        pass
    
    return default_language

def normalize_language(language: str) -> str:
    """
    标准化语言代码
    
    Args:
        language: 原始语言代码
        
    Returns:
        str: 标准化后的语言代码
    """
    if not language:
        return 'zh-CN'
    
    # 转换为小写进行匹配
    lang_lower = language.lower()
    
    # 映射表：支持多种格式的语言代码
    language_mapping = {
        # 中文
        'zh': 'zh-CN',
        'zh-cn': 'zh-CN',
        'zh_cn': 'zh-CN',
        'chinese': 'zh-CN',
        'cn': 'zh-CN',
        
        # 英文
        'en': 'en-US',
        'en-us': 'en-US',
        'en_us': 'en-US',
        'english': 'en-US',
        'us': 'en-US',
        
        # 泰文
        'th': 'th-TH',
        'th-th': 'th-TH',
        'th_th': 'th-TH',
        'thai': 'th-TH',
        'thailand': 'th-TH'
    }
    
    # 查找匹配的语言代码
    normalized = language_mapping.get(lang_lower)
    if normalized:
        return normalized
    
    # 如果没有找到匹配项，尝试提取主要语言部分
    if '-' in language:
        primary_lang = language.split('-')[0].lower()
        normalized = language_mapping.get(primary_lang)
        if normalized:
            return normalized
    
    if '_' in language:
        primary_lang = language.split('_')[0].lower()
        normalized = language_mapping.get(primary_lang)
        if normalized:
            return normalized
    
    # 如果仍然没有找到，返回默认语言
    return 'zh-CN'

def get_supported_languages() -> list:
    """
    获取支持的语言列表
    
    Returns:
        list: 支持的语言代码列表
    """
    return ['zh-CN', 'en-US', 'th-TH']

def is_supported_language(language: str) -> bool:
    """
    检查是否为支持的语言
    
    Args:
        language: 语言代码
        
    Returns:
        bool: 是否支持该语言
    """
    return language in get_supported_languages() 