#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
翻译检查API
提供Web接口来检查翻译完整性
"""

from flask import Blueprint, jsonify
import sys
import os
from pathlib import Path

# 添加utils目录到Python路径
utils_path = Path(__file__).parent.parent / 'utils'
sys.path.insert(0, str(utils_path))

from i18n_checker import I18nChecker

i18n_checker_bp = Blueprint('i18n_checker', __name__)

@i18n_checker_bp.route('/api/i18n/check', methods=['GET'])
def check_translations():
    """检查翻译完整性"""
    try:
        # 创建检查器实例
        checker = I18nChecker()
        
        # 运行检查
        report = checker.run_check()
        
        return jsonify({
            "success": True,
            "data": report
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"检查失败: {str(e)}"
        }), 500

@i18n_checker_bp.route('/api/i18n/check/simple', methods=['GET'])
def check_translations_simple():
    """简化的翻译检查，只返回缺失的key"""
    try:
        # 创建检查器实例
        checker = I18nChecker()
        
        # 运行检查
        report = checker.run_check()
        
        # 只返回缺失的key
        return jsonify({
            "success": True,
            "missing_keys": report['missing_keys'],
            "missing_count": len(report['missing_keys']),
            "total_used": len(report['used_keys']),
            "total_available": len(report['available_keys'])
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"检查失败: {str(e)}"
        }), 500 