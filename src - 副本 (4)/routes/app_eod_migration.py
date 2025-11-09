# EOD改进迁移管理API
from flask import Blueprint, request, jsonify
from services.auth_service import token_required, has_permission
from utils.eod_migration_tools import EODMigrationTools
import logging

logger = logging.getLogger(__name__)

eod_migration_bp = Blueprint('eod_migration', __name__, url_prefix='/api/eod/migration')

@eod_migration_bp.route('/status', methods=['GET'])
@token_required
@has_permission('admin')
def get_migration_status(current_user):
    """获取迁移状态"""
    try:
        result = EODMigrationTools.get_migration_status()
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取迁移状态失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取状态失败: {str(e)}'}), 500

@eod_migration_bp.route('/add-fields', methods=['POST'])
@token_required
@has_permission('admin')
def add_business_time_fields(current_user):
    """添加业务时间字段"""
    try:
        result = EODMigrationTools.add_business_time_fields()
        
        if result['success']:
            logger.info(f"管理员 {current_user['name']} 执行了添加业务时间字段操作")
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"添加业务时间字段失败: {str(e)}")
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'}), 500

@eod_migration_bp.route('/backfill-data', methods=['POST'])
@token_required
@has_permission('admin')
def backfill_business_time_data_legacy(current_user):
    """补填业务时间数据（旧端点）"""
    try:
        result = EODMigrationTools.backfill_business_time_data()
        
        if result['success']:
            logger.info(f"管理员 {current_user['name']} 执行了补填业务时间数据操作")
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"补填业务时间数据失败: {str(e)}")
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'}), 500

@eod_migration_bp.route('/backfill-business-time', methods=['POST'])
@token_required
@has_permission('admin')
def backfill_business_time(current_user):
    """补填业务时间数据"""
    try:
        result = EODMigrationTools.backfill_business_time_data()
        
        if result['success']:
            logger.info(f"管理员 {current_user['name']} 执行了补填业务时间数据操作")
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"补填业务时间数据失败: {str(e)}")
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'}), 500

@eod_migration_bp.route('/validate', methods=['GET'])
@token_required
@has_permission('admin')
def validate_data_consistency_legacy(current_user):
    """验证数据一致性（旧端点）"""
    try:
        eod_id = request.args.get('eod_id', type=int)
        result = EODMigrationTools.validate_data_consistency(eod_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"验证数据一致性失败: {str(e)}")
        return jsonify({'success': False, 'message': f'验证失败: {str(e)}'}), 500

@eod_migration_bp.route('/validate-consistency', methods=['GET'])
@token_required
@has_permission('admin')
def validate_consistency(current_user):
    """验证数据一致性"""
    try:
        eod_id = request.args.get('eod_id', type=int)
        result = EODMigrationTools.validate_data_consistency(eod_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"验证数据一致性失败: {str(e)}")
        return jsonify({'success': False, 'message': f'验证失败: {str(e)}'}), 500

@eod_migration_bp.route('/create-rollback', methods=['POST'])
@token_required
@has_permission('admin')
def create_rollback_script(current_user):
    """创建回滚脚本"""
    try:
        result = EODMigrationTools.create_rollback_script()
        
        if result['success']:
            logger.info(f"管理员 {current_user['name']} 创建了回滚脚本")
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"创建回滚脚本失败: {str(e)}")
        return jsonify({'success': False, 'message': f'创建失败: {str(e)}'}), 500

@eod_migration_bp.route('/feature-toggle', methods=['POST'])
@token_required
@has_permission('admin')
def toggle_feature(current_user):
    """切换特性开关"""
    try:
        data = request.get_json()
        feature_name = data.get('feature_name')
        enabled = data.get('enabled')
        
        if not feature_name or enabled is None:
            return jsonify({'success': False, 'message': '缺少必要参数'}), 400
        
        from config.features import FeatureFlags
        
        if hasattr(FeatureFlags, feature_name):
            setattr(FeatureFlags, feature_name, enabled)
            
            logger.info(f"管理员 {current_user['name']} {'启用' if enabled else '禁用'}了特性: {feature_name}")
            
            return jsonify({
                'success': True,
                'message': f'特性 {feature_name} 已{"启用" if enabled else "禁用"}',
                'feature_name': feature_name,
                'enabled': enabled
            })
        else:
            return jsonify({'success': False, 'message': f'未知特性: {feature_name}'}), 400
            
    except Exception as e:
        logger.error(f"切换特性开关失败: {str(e)}")
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'}), 500 