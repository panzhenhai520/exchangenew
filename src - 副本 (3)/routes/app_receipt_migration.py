from flask import Blueprint, jsonify
from services.auth_service import token_required, has_permission
from utils.receipt_enhancement_migration import ReceiptEnhancementMigration
from utils.init_country_data import CountryDataInitializer
import logging

logger = logging.getLogger(__name__)

receipt_migration_bp = Blueprint('receipt_migration', __name__, url_prefix='/api/migrations/receipt')

@receipt_migration_bp.route('/run', methods=['POST'])
@token_required
@has_permission('system_admin')
def run_receipt_migrations(*args):
    """执行收据增强功能的数据迁移"""
    current_user = args[0] if args else None
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401

    try:
        result = ReceiptEnhancementMigration.run_all_migrations()
        return jsonify(result), 200 if result['success'] else 500

    except Exception as e:
        logger.error(f"执行收据迁移失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'迁移执行失败: {str(e)}'
        }), 500

@receipt_migration_bp.route('/create-country-table', methods=['POST'])
@token_required
@has_permission('system_admin')
def create_country_table(*args):
    """创建国家信息表"""
    current_user = args[0] if args else None
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401

    try:
        result = ReceiptEnhancementMigration.create_country_table()
        return jsonify(result), 200 if result['success'] else 500

    except Exception as e:
        logger.error(f"创建国家表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'创建失败: {str(e)}'
        }), 500

@receipt_migration_bp.route('/init-countries', methods=['POST'])
@token_required
@has_permission('system_admin')
def init_countries(*args):
    """初始化195个国家数据"""
    current_user = args[0] if args else None
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401

    try:
        result = CountryDataInitializer.initialize_countries()
        return jsonify(result), 200 if result['success'] else 500

    except Exception as e:
        logger.error(f"初始化国家数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'初始化失败: {str(e)}'
        }), 500
