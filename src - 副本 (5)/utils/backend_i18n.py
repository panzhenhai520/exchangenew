# Backend Internationalization System
from typing import Dict, Any, Optional
import os
import json
import logging

logger = logging.getLogger(__name__)

class BackendI18n:
    """Backend internationalization system for error messages and API responses"""

    def __init__(self):
        self._translations = {}
        self._default_language = 'zh-CN'
        self._load_translations()

    def _load_translations(self):
        """Load translation files from the backend i18n directory"""
        try:
            # Define the path to backend translations
            backend_i18n_dir = os.path.join(os.path.dirname(__file__), '..', 'i18n', 'backend')

            if os.path.exists(backend_i18n_dir):
                for filename in os.listdir(backend_i18n_dir):
                    if filename.endswith('.json'):
                        language_code = filename[:-5]  # Remove .json extension
                        file_path = os.path.join(backend_i18n_dir, filename)

                        with open(file_path, 'r', encoding='utf-8') as f:
                            self._translations[language_code] = json.load(f)
                            logger.info(f"Loaded backend translations for {language_code}")
            else:
                logger.warning(f"Backend i18n directory not found: {backend_i18n_dir}")
                # Initialize with default empty structure
                self._translations = {
                    'zh-CN': {},
                    'en-US': {},
                    'th-TH': {}
                }
        except Exception as e:
            logger.error(f"Failed to load backend translations: {str(e)}")
            # Initialize with default empty structure
            self._translations = {
                'zh-CN': {},
                'en-US': {},
                'th-TH': {}
            }

    def translate(self, key: str, language: str = None, **kwargs) -> str:
        """
        Translate a message key to the specified language

        Args:
            key: Translation key (e.g., 'exchange.insufficient_balance')
            language: Target language code (e.g., 'zh-CN', 'en-US', 'th-TH')
            **kwargs: Variables to substitute in the translation template

        Returns:
            Translated message string
        """
        if not language:
            language = self._default_language

        # Normalize language code
        language = self._normalize_language_code(language)

        try:
            # Navigate through nested keys (e.g., 'exchange.insufficient_balance')
            keys = key.split('.')
            translation = self._translations.get(language, {})

            for k in keys:
                if isinstance(translation, dict) and k in translation:
                    translation = translation[k]
                else:
                    # Fallback to default language
                    if language != self._default_language:
                        return self.translate(key, self._default_language, **kwargs)
                    # Fallback to key itself if no translation found
                    logger.warning(f"Translation not found for key '{key}' in language '{language}'")
                    return key

            # If translation is still a dict, return the key
            if isinstance(translation, dict):
                logger.warning(f"Translation key '{key}' points to a dict, not a string")
                return key

            # Substitute variables in the translation template
            if kwargs:
                try:
                    return translation.format(**kwargs)
                except (KeyError, ValueError) as e:
                    logger.warning(f"Failed to format translation '{translation}' with args {kwargs}: {e}")
                    return translation

            return translation

        except Exception as e:
            logger.error(f"Translation error for key '{key}' in language '{language}': {str(e)}")
            return key

    def _normalize_language_code(self, language: str) -> str:
        """Normalize language code to supported format"""
        language_map = {
            'zh': 'zh-CN',
            'zh_CN': 'zh-CN',
            'zh-cn': 'zh-CN',
            'en': 'en-US',
            'en_US': 'en-US',
            'en-us': 'en-US',
            'th': 'th-TH',
            'th_TH': 'th-TH',
            'th-th': 'th-TH'
        }

        return language_map.get(language, language)

    def get_supported_languages(self) -> list:
        """Get list of supported language codes"""
        return list(self._translations.keys())

    def set_default_language(self, language: str):
        """Set the default language"""
        self._default_language = self._normalize_language_code(language)

# Global instance
backend_i18n = BackendI18n()

def t(key: str, language: str = None, **kwargs) -> str:
    """
    Shorthand function for translation

    Args:
        key: Translation key
        language: Target language code
        **kwargs: Variables for template substitution

    Returns:
        Translated message
    """
    return backend_i18n.translate(key, language, **kwargs)

def get_request_language(request) -> str:
    """
    Extract language preference from Flask request

    Args:
        request: Flask request object

    Returns:
        Language code (e.g., 'zh-CN', 'en-US', 'th-TH')
    """
    try:
        # Try to get language from request headers
        if hasattr(request, 'headers'):
            # Check for custom language header
            custom_lang = request.headers.get('X-Language') or request.headers.get('Language')
            if custom_lang:
                return backend_i18n._normalize_language_code(custom_lang)

            # Check Accept-Language header
            accept_language = request.headers.get('Accept-Language')
            if accept_language:
                # Parse Accept-Language header (simplified)
                languages = [lang.strip().split(';')[0] for lang in accept_language.split(',')]
                for lang in languages:
                    normalized = backend_i18n._normalize_language_code(lang)
                    if normalized in backend_i18n.get_supported_languages():
                        return normalized

        # Try to get language from request JSON data
        if hasattr(request, 'get_json'):
            try:
                data = request.get_json()
                if data and isinstance(data, dict):
                    lang = data.get('language')
                    if lang:
                        return backend_i18n._normalize_language_code(lang)
            except:
                pass

        # Try to get language from request args
        if hasattr(request, 'args'):
            lang = request.args.get('language') or request.args.get('lang')
            if lang:
                return backend_i18n._normalize_language_code(lang)

    except Exception as e:
        logger.warning(f"Failed to extract language from request: {str(e)}")

    # Default to Chinese
    return 'zh-CN'