# 双向交易数据迁移路由
from flask import Blueprint, jsonify, request
from utils.dual_direction_migration_tools import DualDirectionMigrationTools
from services.auth_service import token_required, has_permission
import logging

logger = logging.getLogger(__name__)

dual_direction_migration_bp = Blueprint('dual_direction_migration', __name__)

@dual_direction_migration_bp.route('/api/dual-direction-migration/run-all', methods=['POST'])
def run_all_migrations():
    """运行所有双向交易相关的数据迁移"""
    try:
        # 验证权限
        auth_result = AuthService.verify_token(request)
        if not auth_result['valid']:
            return jsonify({
                'success': False,
                'message': auth_result['message']
            }), 401

        # 验证系统管理权限
        if not AuthService.has_permission(auth_result['user_id'], 'system_manage'):
            return jsonify({
                'success': False,
                'message': '需要系统管理权限'
            }), 403

        logger.info(f"开始执行双向交易数据迁移，操作员: {auth_result['login_code']}")

        # 执行所有迁移
        result = DualDirectionMigrationTools.run_all_migrations()

        if result['success']:
            logger.info(f"双向交易数据迁移成功完成，操作员: {auth_result['login_code']}")
            return jsonify({
                'success': True,
                'message': result['message'],
                'details': result['details']
            })
        else:
            logger.error(f"双向交易数据迁移失败，操作员: {auth_result['login_code']}")
            return jsonify({
                'success': False,
                'message': result['message'],
                'details': result['details']
            }), 500

    except Exception as e:
        logger.error(f"双向交易数据迁移异常: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'迁移失败: {str(e)}'
        }), 500

@dual_direction_migration_bp.route('/api/dual-direction-migration/add-transaction-group-fields', methods=['POST'])
def add_transaction_group_fields():
    """添加交易组字段"""
    try:
        # 验证权限
        auth_result = AuthService.verify_token(request)
        if not auth_result['valid']:
            return jsonify({
                'success': False,
                'message': auth_result['message']
            }), 401

        if not AuthService.has_permission(auth_result['user_id'], 'system_manage'):
            return jsonify({
                'success': False,
                'message': '需要系统管理权限'
            }), 403

        # 执行迁移
        result = DualDirectionMigrationTools.add_transaction_group_fields()

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"添加交易组字段失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'添加字段失败: {str(e)}'
        }), 500

@dual_direction_migration_bp.route('/api/dual-direction-migration/add-customer-fields', methods=['POST'])
def add_customer_enhanced_fields():
    """添加增强的客户信息字段"""
    try:
        # 验证权限
        auth_result = AuthService.verify_token(request)
        if not auth_result['valid']:
            return jsonify({
                'success': False,
                'message': auth_result['message']
            }), 401

        if not AuthService.has_permission(auth_result['user_id'], 'system_manage'):
            return jsonify({
                'success': False,
                'message': '需要系统管理权限'
            }), 403

        # 执行迁移
        result = DualDirectionMigrationTools.add_customer_enhanced_fields()

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"添加客户信息字段失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'添加客户信息字段失败: {str(e)}'
        }), 500

@dual_direction_migration_bp.route('/api/dual-direction-migration/add-branch-fields', methods=['POST'])
def add_branch_enhanced_fields():
    """添加增强的网点信息字段"""
    try:
        # 验证权限
        auth_result = AuthService.verify_token(request)
        if not auth_result['valid']:
            return jsonify({
                'success': False,
                'message': auth_result['message']
            }), 401

        if not AuthService.has_permission(auth_result['user_id'], 'system_manage'):
            return jsonify({
                'success': False,
                'message': '需要系统管理权限'
            }), 403

        # 执行迁移
        result = DualDirectionMigrationTools.add_branch_enhanced_fields()

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"添加网点信息字段失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'添加网点信息字段失败: {str(e)}'
        }), 500

@dual_direction_migration_bp.route('/api/dual-direction-migration/backfill-direction-data', methods=['POST'])
def backfill_transaction_direction_data():
    """补填交易方向数据"""
    try:
        # 验证权限
        auth_result = AuthService.verify_token(request)
        if not auth_result['valid']:
            return jsonify({
                'success': False,
                'message': auth_result['message']
            }), 401

        if not AuthService.has_permission(auth_result['user_id'], 'system_manage'):
            return jsonify({
                'success': False,
                'message': '需要系统管理权限'
            }), 403

        # 执行数据补填
        result = DualDirectionMigrationTools.backfill_transaction_direction_data()

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"补填交易方向数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'补填数据失败: {str(e)}'
        }), 500

@dual_direction_migration_bp.route('/api/dual-direction-migration/validate', methods=['GET'])
def validate_migration():
    """验证迁移是否成功"""
    try:
        # 验证权限
        auth_result = AuthService.verify_token(request)
        if not auth_result['valid']:
            return jsonify({
                'success': False,
                'message': auth_result['message']
            }), 401

        if not AuthService.has_permission(auth_result['user_id'], 'system_manage'):
            return jsonify({
                'success': False,
                'message': '需要系统管理权限'
            }), 403

        # 执行验证
        result = DualDirectionMigrationTools.validate_migration()

        return jsonify(result)

    except Exception as e:
        logger.error(f"验证迁移失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'验证失败: {str(e)}'
        }), 500