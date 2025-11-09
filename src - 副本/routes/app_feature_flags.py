"""
特性开关管理API
用于动态控制系统特性开关
"""

from flask import Blueprint, request, jsonify, g
from services.auth_service import token_required
from config.features import FeatureFlags
import logging

app_feature_flags = Blueprint('feature_flags', __name__)
logger = logging.getLogger(__name__)

@app_feature_flags.route('/feature-flags', methods=['GET'])
@token_required
def get_feature_flags(current_user):
    """获取所有特性开关状态"""
    try:
        # 用户权限已在token_required装饰器中验证
        
        # 获取所有特性开关状态
        features = FeatureFlags.get_all_features()
        
        # 添加特性开关的描述信息
        feature_descriptions = {
            'FEATURE_NEW_BUSINESS_TIME_RANGE': '新业务时间范围计算',
            'FEATURE_NEW_PERIOD_BALANCE': '新期初余额获取方式',
            'ENABLE_ENHANCED_BALANCE_CALCULATION': '增强余额计算',
            'ENABLE_COMPREHENSIVE_STATISTICS': '完整统计报表',
            'ENABLE_BALANCE_CONSISTENCY_CHECK': '余额一致性检查',
            'ENABLE_EOD_DEBUG_LOGGING': '日结调试日志',
            'ENABLE_PERFORMANCE_MONITORING': '性能监控'
        }
        
        result = {}
        for feature_name, enabled in features.items():
            result[feature_name] = {
                'enabled': enabled,
                'description': feature_descriptions.get(feature_name, ''),
                'key': feature_name
            }
        
        return jsonify({
            'success': True,
            'features': result
        })
        
    except Exception as e:
        logger.error(f"获取特性开关失败: {str(e)}")
        return jsonify({'error': '获取特性开关失败'}), 500

@app_feature_flags.route('/feature-flags/<feature_name>', methods=['POST'])
@token_required
def set_feature_flag(current_user, feature_name):
    """设置特性开关状态"""
    try:
        # 用户权限已在token_required装饰器中验证
        
        # 获取请求参数
        data = request.get_json()
        if not data or 'enabled' not in data:
            return jsonify({'error': '缺少必要参数'}), 400
        
        enabled = data['enabled']
        
        # 验证特性开关名称
        if feature_name not in FeatureFlags._DEFAULT_FEATURES:
            return jsonify({'error': '无效的特性开关名称'}), 400
        
        # 设置特性开关
        success = FeatureFlags.set_feature(feature_name, enabled)
        
        if success:
            logger.info(f"用户 {current_user.get('name', '未知')} 设置特性开关 {feature_name} = {enabled}")
            return jsonify({
                'success': True,
                'message': f'特性开关 {feature_name} 已设置为 {enabled}'
            })
        else:
            return jsonify({'error': '设置特性开关失败'}), 500
            
    except Exception as e:
        logger.error(f"设置特性开关失败: {str(e)}")
        return jsonify({'error': '设置特性开关失败'}), 500

@app_feature_flags.route('/feature-flags/eod-settings', methods=['GET'])
@token_required
def get_eod_feature_settings(current_user):
    """获取日结相关的特性开关设置"""
    try:
        # 用户权限已在token_required装饰器中验证
        
        # 获取日结相关的特性开关
        eod_features = [
            'FEATURE_NEW_BUSINESS_TIME_RANGE',
            'FEATURE_NEW_PERIOD_BALANCE',
            'ENABLE_ENHANCED_BALANCE_CALCULATION',
            'ENABLE_COMPREHENSIVE_STATISTICS',
            'ENABLE_BALANCE_CONSISTENCY_CHECK'
        ]
        
        features = {}
        for feature_name in eod_features:
            features[feature_name] = {
                'enabled': FeatureFlags.is_enabled(feature_name),
                'description': {
                    'FEATURE_NEW_BUSINESS_TIME_RANGE': '新业务时间范围计算',
                    'FEATURE_NEW_PERIOD_BALANCE': '新期初余额获取方式',
                    'ENABLE_ENHANCED_BALANCE_CALCULATION': '增强余额计算',
                    'ENABLE_COMPREHENSIVE_STATISTICS': '完整统计报表',
                    'ENABLE_BALANCE_CONSISTENCY_CHECK': '余额一致性检查'
                }.get(feature_name, ''),
                'key': feature_name
            }
        
        return jsonify({
            'success': True,
            'features': features
        })
        
    except Exception as e:
        logger.error(f"获取日结特性开关失败: {str(e)}")
        return jsonify({'error': '获取日结特性开关失败'}), 500

@app_feature_flags.route('/feature-flags/batch-update', methods=['POST'])
@token_required
def batch_update_feature_flags(current_user):
    """批量更新特性开关状态"""
    try:
        # 用户权限已在token_required装饰器中验证
        
        # 获取请求参数
        data = request.get_json()
        if not data or 'features' not in data:
            return jsonify({'error': '缺少必要参数'}), 400
        
        features = data['features']
        results = {}
        
        # 批量更新特性开关
        for feature_name, enabled in features.items():
            if feature_name in FeatureFlags._DEFAULT_FEATURES:
                success = FeatureFlags.set_feature(feature_name, enabled)
                results[feature_name] = success
                
                if success:
                    logger.info(f"用户 {current_user.get('name', '未知')} 设置特性开关 {feature_name} = {enabled}")
        
        return jsonify({
            'success': True,
            'results': results,
            'message': '特性开关批量更新完成'
        })
        
    except Exception as e:
        logger.error(f"批量更新特性开关失败: {str(e)}")
        return jsonify({'error': '批量更新特性开关失败'}), 500 