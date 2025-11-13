#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统一的币种翻译服务
为所有PDF生成器提供币种多语言翻译功能
支持数据库动态查询和配置文件动态加载
"""

import logging
import json
import os
from .db_service import DatabaseService
from models.exchange_models import Currency

logger = logging.getLogger(__name__)

class CurrencyTranslationService:
    """统一的币种翻译服务"""
    
    # 配置文件路径
    CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'currency_translations.json')
    
    # 内存缓存
    _translations_cache = None
    _cache_loaded = False
    
    @staticmethod
    def get_currency_name(currency_code, language='zh'):
        """获取币种的多语言名称"""
        if not currency_code:
            return ''
        
        # 语言代码映射
        lang_map = {'zh': 'zh', 'zh-CN': 'zh', 'en': 'en', 'en-US': 'en', 'th': 'th', 'th-TH': 'th'}
        current_lang = lang_map.get(language, 'zh')
        
        # 1. 首先尝试从数据库获取翻译
        try:
            translated_name = CurrencyTranslationService._get_from_database(currency_code, current_lang)
            if translated_name and translated_name != currency_code:
                logger.debug(f"🔍 数据库币种翻译: {currency_code} -> {translated_name} (语言: {current_lang})")
                return translated_name
        except Exception as e:
            logger.warning(f"数据库查询失败: {e}")
        
        # 2. 从配置文件获取翻译
        try:
            translated_name = CurrencyTranslationService._get_from_config(currency_code, current_lang)
            if translated_name:
                logger.debug(f"🔍 配置文件币种翻译: {currency_code} -> {translated_name} (语言: {current_lang})")
                return translated_name
        except Exception as e:
            logger.warning(f"配置文件查询失败: {e}")
        
        # 3. 如果都没有找到，返回币种代码本身
        logger.debug(f"🔍 币种未找到翻译，返回代码: {currency_code}")
        return currency_code
    
    @staticmethod
    def _get_from_database(currency_code, language):
        """从数据库获取币种翻译"""
        session = DatabaseService.get_session()
        try:
            currency = session.query(Currency).filter_by(currency_code=currency_code).first()
            if currency:
                # 【关键修复】检查是否是自定义币种
                if currency.custom_flag_filename:
                    logger.debug(f"🔍 自定义币种: {currency_code} -> {currency.currency_name}")
                    return currency.currency_name  # 自定义币种直接使用数据库名称
                
                # 预设币种的处理
                if language == 'zh':
                    return currency.currency_name
                else:
                    # 对于非中文语言，暂时返回币种代码
                    # 后续可以扩展Currency表添加多语言字段
                    return currency_code
            return None
        except Exception as e:
            logger.error(f"数据库查询币种翻译失败: {e}")
            return None
        finally:
            session.close()
    
    @staticmethod
    def _get_from_config(currency_code, language):
        """从配置文件获取币种翻译"""
        # 加载配置文件
        translations = CurrencyTranslationService._load_config()
        if not translations:
            return None
        
        # 查找币种翻译
        if currency_code in translations:
            currency_translations = translations[currency_code]
            if isinstance(currency_translations, dict) and language in currency_translations:
                return currency_translations[language]
        
        return None
    
    @staticmethod
    def _load_config():
        """加载配置文件"""
        if CurrencyTranslationService._cache_loaded:
            return CurrencyTranslationService._translations_cache
        
        try:
            if os.path.exists(CurrencyTranslationService.CONFIG_FILE_PATH):
                with open(CurrencyTranslationService.CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                    CurrencyTranslationService._translations_cache = json.load(f)
                    CurrencyTranslationService._cache_loaded = True
                    logger.info(f"✅ 成功加载币种翻译配置文件: {CurrencyTranslationService.CONFIG_FILE_PATH}")
                    return CurrencyTranslationService._translations_cache
            else:
                logger.info(f"📝 币种翻译配置文件不存在，将创建: {CurrencyTranslationService.CONFIG_FILE_PATH}")
                CurrencyTranslationService._create_default_config()
                return CurrencyTranslationService._translations_cache
        except Exception as e:
            logger.error(f"加载币种翻译配置文件失败: {e}")
            return None
    
    @staticmethod
    def _create_default_config():
        """创建默认配置文件"""
        default_translations = {
            "USD": {
                "zh": "美元",
                "en": "US Dollar",
                "th": "ดอลลาร์สหรัฐ"
            },
            "EUR": {
                "zh": "欧元",
                "en": "Euro",
                "th": "ยูโร"
            },
            "GBP": {
                "zh": "英镑",
                "en": "British Pound",
                "th": "ปอนด์อังกฤษ"
            },
            "JPY": {
                "zh": "日元",
                "en": "Japanese Yen",
                "th": "เยนญี่ปุ่น"
            },
            "THB": {
                "zh": "泰铢",
                "en": "Thai Baht",
                "th": "บาทไทย"
            },
            "CNY": {
                "zh": "人民币",
                "en": "Chinese Yuan",
                "th": "หยวนจีน"
            }
        }
        
        try:
            # 确保目录存在
            config_dir = os.path.dirname(CurrencyTranslationService.CONFIG_FILE_PATH)
            os.makedirs(config_dir, exist_ok=True)
            
            # 写入默认配置
            with open(CurrencyTranslationService.CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(default_translations, f, ensure_ascii=False, indent=2)
            
            CurrencyTranslationService._translations_cache = default_translations
            CurrencyTranslationService._cache_loaded = True
            logger.info(f"✅ 成功创建默认币种翻译配置文件")
            
        except Exception as e:
            logger.error(f"创建默认配置文件失败: {e}")
    
    @staticmethod
    def add_translation(currency_code, translations):
        """动态添加币种翻译"""
        try:
            # 加载当前配置
            current_translations = CurrencyTranslationService._load_config()
            if not current_translations:
                current_translations = {}
            
            # 添加新翻译
            current_translations[currency_code] = translations
            
            # 保存到配置文件
            config_dir = os.path.dirname(CurrencyTranslationService.CONFIG_FILE_PATH)
            os.makedirs(config_dir, exist_ok=True)
            
            with open(CurrencyTranslationService.CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(current_translations, f, ensure_ascii=False, indent=2)
            
            # 更新缓存
            CurrencyTranslationService._translations_cache = current_translations
            
            logger.info(f"✅ 成功添加币种翻译: {currency_code}")
            return True
            
        except Exception as e:
            logger.error(f"添加币种翻译失败: {e}")
            return False
    
    @staticmethod
    def reload_config():
        """重新加载配置文件"""
        CurrencyTranslationService._cache_loaded = False
        CurrencyTranslationService._translations_cache = None
        return CurrencyTranslationService._load_config() 