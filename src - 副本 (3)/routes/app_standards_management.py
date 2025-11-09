"""
规范管理API路由
处理兑换提醒信息维护、票据文件查看、余额报警设置的HTTP请求
"""

from flask import Blueprint, request, jsonify
from services.auth_service import token_required, has_permission
from services.standards_service import StandardsService
from services.receipt_file_service import ReceiptFileService
# 移除不存在的error_handler依赖
import logging

logger = logging.getLogger(__name__)

def handle_error(e, message):
    """统一错误处理函数"""
    logger.error(f"{message}: {str(e)}")
    return jsonify({
        'success': False,
        'message': f'{message}: {str(e)}'
    }), 500

standards_management_bp = Blueprint('standards_management', __name__)

# ==================== 兑换提醒信息维护 API ====================

@standards_management_bp.route('/api/standards/purpose-limits', methods=['GET'])
@token_required
@has_permission('branch_manage')
def get_purpose_limits(current_user):
    """获取兑换提醒信息列表"""
    try:
        branch_id = current_user['branch_id']
        limits = StandardsService.get_purpose_limits(branch_id)
        
        return jsonify({
            'success': True,
            'purpose_limits': limits,
            'total': len(limits)
        })
    except Exception as e:
        logger.error(f"获取兑换提醒信息失败: {e}")
        return handle_error(e, '获取兑换提醒信息失败')

@standards_management_bp.route('/api/standards/purpose-limits', methods=['POST'])
@token_required
@has_permission('branch_manage')
def create_purpose_limit(current_user):
    """创建兑换提醒信息"""
    try:
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['purpose_name', 'currency_code', 'max_amount', 'display_message']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'message': f'缺少必需字段: {field}'
                }), 400
        
        branch_id = current_user['branch_id']
        limit = StandardsService.create_purpose_limit(branch_id, data)
        
        return jsonify({
            'success': True,
            'message': '兑换提醒信息创建成功',
            'purpose_limit': limit
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"创建兑换提醒信息失败: {e}")
        return handle_error(e, '创建兑换提醒信息失败')

@standards_management_bp.route('/api/standards/purpose-limits/<int:limit_id>', methods=['PUT'])
@token_required
@has_permission('branch_manage')
def update_purpose_limit(current_user, limit_id):
    """更新兑换提醒信息"""
    try:
        data = request.get_json()
        branch_id = current_user['branch_id']
        
        limit = StandardsService.update_purpose_limit(branch_id, limit_id, data)
        
        return jsonify({
            'success': True,
            'message': '兑换提醒信息更新成功',
            'purpose_limit': limit
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 404
    except Exception as e:
        logger.error(f"更新兑换提醒信息失败: {e}")
        return handle_error(e, '更新兑换提醒信息失败')

@standards_management_bp.route('/api/standards/purpose-limits/<int:limit_id>', methods=['DELETE'])
@token_required
@has_permission('branch_manage')
def delete_purpose_limit(current_user, limit_id):
    """删除兑换提醒信息"""
    try:
        branch_id = current_user['branch_id']
        StandardsService.delete_purpose_limit(branch_id, limit_id)
        
        return jsonify({
            'success': True,
            'message': '兑换提醒信息删除成功'
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 404
    except Exception as e:
        logger.error(f"删除兑换提醒信息失败: {e}")
        return handle_error(e, '删除兑换提醒信息失败')

@standards_management_bp.route('/api/standards/purpose-limits/by-currency/<currency_code>', methods=['GET'])
@token_required
@has_permission('exchange_manage')  # 兑换操作权限，不需要网点管理权限
def get_purpose_limits_by_currency(current_user, currency_code):
    """根据币种代码获取兑换提醒信息列表（用于兑换页面）"""
    try:
        branch_id = current_user['branch_id']
        limits = StandardsService.get_purpose_limits_by_currency(branch_id, currency_code)
        
        return jsonify({
            'success': True,
            'purposes': limits,
            'total': len(limits)
        })
    except Exception as e:
        logger.error(f"获取兑换提醒信息失败: {e}")
        return handle_error(e, '获取兑换提醒信息失败')

# ==================== 票据文件查看 API ====================

@standards_management_bp.route('/api/standards/receipt-files/years', methods=['GET'])
@token_required
@has_permission('branch_manage')
def get_available_years(current_user):
    """获取可用的年份列表"""
    try:
        years = ReceiptFileService.get_available_years()
        
        return jsonify({
            'success': True,
            'years': years
        })
    except Exception as e:
        logger.error(f"获取年份列表失败: {e}")
        return handle_error(e, '获取年份列表失败')

@standards_management_bp.route('/api/standards/receipt-files/months/<year>', methods=['GET'])
@token_required
@has_permission('branch_manage')
def get_available_months(current_user, year):
    """获取指定年份的可用月份列表"""
    try:
        months = ReceiptFileService.get_available_months(year)
        
        return jsonify({
            'success': True,
            'months': months
        })
    except Exception as e:
        logger.error(f"获取月份列表失败: {e}")
        return handle_error(e, '获取月份列表失败')

@standards_management_bp.route('/api/standards/receipt-files/<year>/<month>', methods=['GET'])
@token_required
@has_permission('branch_manage')
def get_receipt_files(current_user, year, month):
    """获取指定年月的票据文件列表"""
    try:
        branch_id = current_user['branch_id']
        files = ReceiptFileService.get_receipt_files(year, month, branch_id)
        
        return jsonify({
            'success': True,
            'files': files,
            'total': len(files)
        })
    except Exception as e:
        logger.error(f"获取票据文件列表失败: {e}")
        return handle_error(e, '获取票据文件列表失败')

@standards_management_bp.route('/api/standards/receipt-files/print', methods=['POST'])
@token_required
@has_permission('branch_manage')
def record_print_action(current_user):
    """记录票据打印操作"""
    try:
        data = request.get_json()
        
        if 'filename' not in data:
            return jsonify({
                'success': False,
                'message': '缺少文件名参数'
            }), 400
        
        filename = data['filename']
        operator_id = current_user['id']
        
        success = ReceiptFileService.record_print_action(filename, operator_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': '打印记录成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '打印记录失败'
            }), 500
            
    except Exception as e:
        logger.error(f"记录打印操作失败: {e}")
        return handle_error(e, '记录打印操作失败')

# ==================== 余额报警设置 API ====================

@standards_management_bp.route('/api/standards/balance-alerts', methods=['GET'])
@token_required
@has_permission('branch_manage')
def get_balance_alerts(current_user):
    """获取余额报警设置列表"""
    try:
        branch_id = current_user['branch_id']
        alerts = StandardsService.get_balance_alerts(branch_id)
        
        return jsonify({
            'success': True,
            'balance_alerts': alerts,
            'total': len(alerts)
        })
    except Exception as e:
        logger.error(f"获取余额报警设置失败: {e}")
        return handle_error(e, '获取余额报警设置失败')

@standards_management_bp.route('/api/standards/balance-alerts', methods=['POST'])
@token_required
@has_permission('branch_manage')
def create_or_update_balance_alert(current_user):
    """创建或更新余额报警设置"""
    try:
        data = request.get_json()
        
        if 'currency_code' not in data:
            return jsonify({
                'success': False,
                'message': '缺少币种代码参数'
            }), 400
        
        branch_id = current_user['branch_id']
        currency_id = data.get('currency_id')  # 可以为null
        
        alert = StandardsService.create_or_update_balance_alert(branch_id, currency_id, data)
        
        return jsonify({
            'success': True,
            'message': '余额报警设置保存成功',
            'balance_alert': alert
        })
    except Exception as e:
        logger.error(f"保存余额报警设置失败: {e}")
        return handle_error(e, '保存余额报警设置失败')

@standards_management_bp.route('/api/standards/balance-alerts/<int:alert_id>', methods=['DELETE'])
@token_required
@has_permission('branch_manage')
def delete_balance_alert(current_user, alert_id):
    """删除余额报警设置"""
    try:
        branch_id = current_user['branch_id']
        StandardsService.delete_balance_alert(branch_id, alert_id)
        
        return jsonify({
            'success': True,
            'message': '余额报警设置删除成功'
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 404
    except Exception as e:
        logger.error(f"删除余额报警设置失败: {e}")
        return handle_error(e, '删除余额报警设置失败')

# ==================== 通用API ====================

@standards_management_bp.route('/api/standards/currencies', methods=['GET'])
def get_available_currencies():
    """获取可用的币种列表"""
    try:
        currencies = StandardsService.get_available_currencies()
        
        return jsonify({
            'success': True,
            'currencies': currencies
        })
    except Exception as e:
        logger.error(f"获取币种列表失败: {e}")
        return handle_error(e, '获取币种列表失败') 