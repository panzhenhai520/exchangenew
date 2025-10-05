#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易报警事件 API
提供交易报警事件的查询和管理接口
"""

import logging
from flask import Blueprint, request, jsonify
from functools import wraps

from services.auth_service import token_required, has_permission
from services.transaction_alert_service import TransactionAlertService

logger = logging.getLogger(__name__)

# 创建蓝图
transaction_alerts_bp = Blueprint('transaction_alerts', __name__, url_prefix='/api/transaction-alerts')

@transaction_alerts_bp.route('/create', methods=['POST'])
@token_required
def create_alert(current_user):
    """
    创建交易报警事件
    
    Request Body:
        - currency_id (int): 币种ID
        - alert_type (str): 报警类型
        - alert_level (str): 报警级别
        - current_balance (float): 当前余额
        - threshold_value (float): 阈值
        - transaction_amount (float): 交易金额
        - transaction_type (str): 交易类型
        - after_balance (float): 交易后余额
        - message (str): 报警信息
    
    权限要求:
        - 任何有交易执行权限的用户都可以创建报警
    """
    try:
        data = request.get_json()
        
        # 验证必要字段
        required_fields = ['currency_id', 'alert_type', 'alert_level', 'message']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'缺少必要字段: {field}'
                }), 400
        
        # 创建报警记录
        result = TransactionAlertService.create_alert(
            branch_id=current_user['branch_id'],
            currency_id=data['currency_id'],
            operator_id=current_user['id'],
            alert_type=data['alert_type'],
            alert_level=data['alert_level'],
            current_balance=data.get('current_balance', 0),
            threshold_value=data.get('threshold_value', 0),
            transaction_amount=data.get('transaction_amount', 0),
            transaction_type=data.get('transaction_type', ''),
            after_balance=data.get('after_balance', 0),
            message=data['message']
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"创建交易报警失败: {e}")
        return jsonify({
            'success': False,
            'message': f'创建交易报警失败: {str(e)}'
        }), 500

@transaction_alerts_bp.route('/statistics', methods=['GET'])
@token_required
def get_alert_statistics(current_user):
    """
    获取交易报警事件统计信息
    
    Query Parameters:
        days: 统计天数，默认7天
    
    权限要求:
        - 普通操作员：只能查看自己相关的统计
        - 网点管理权限：可以查看网点所有统计
    """
    try:
        days = int(request.args.get('days', 7))
        
        # 检查权限
        has_branch_manage = False
        try:
            # 尝试检查是否有网点管理权限
            @has_permission('branch_manage')
            def check_permission():
                return True
            check_permission.__globals__['current_user'] = current_user
            check_permission()
            has_branch_manage = True
        except:
            has_branch_manage = False
        
        if has_branch_manage:
            # 有网点管理权限，可以查看网点所有统计
            result = TransactionAlertService.get_alert_statistics(
                current_user['branch_id'], days
            )
        else:
            # 普通操作员，只返回基础统计（不涉及敏感信息）
            result = TransactionAlertService.get_alert_statistics(
                current_user['branch_id'], days
            )
            # 过滤敏感信息，只保留概要统计
            if result['success'] and 'statistics' in result:
                stats = result['statistics']
                result['statistics'] = {
                    'total_alerts': stats.get('total_alerts', 0),
                    'unresolved_alerts': stats.get('unresolved_alerts', 0),
                    'days': stats.get('days', days)
                }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"获取报警统计失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取报警统计失败: {str(e)}'
        }), 500

@transaction_alerts_bp.route('/list', methods=['GET'])
@token_required
@has_permission('branch_manage')
def get_alert_list(current_user):
    """
    获取交易报警事件列表
    
    Query Parameters:
        limit: 限制数量，默认50
        resolved: 是否已解决 (true/false)，不传表示全部
    
    权限要求:
        - 需要网点管理权限
    """
    try:
        limit = int(request.args.get('limit', 50))
        resolved = request.args.get('resolved')
        
        resolved_filter = None
        if resolved is not None:
            resolved_filter = resolved.lower() == 'true'
        
        # 使用网点管理权限查询
        from services.transaction_alert_service import TransactionAlertService
        
        db_service = TransactionAlertService()
        result = db_service.get_alerts_by_branch(
            current_user['branch_id'], limit, resolved_filter
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"获取报警列表失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取报警列表失败: {str(e)}'
        }), 500

@transaction_alerts_bp.route('/my-alerts', methods=['GET'])
@token_required
def get_my_alerts(current_user):
    """
    获取当前操作员相关的报警事件
    
    Query Parameters:
        limit: 限制数量，默认20
    
    权限要求:
        - 任何登录用户都可以查看自己的报警
    """
    try:
        limit = int(request.args.get('limit', 20))
        
        from services.transaction_alert_service import TransactionAlertService
        
        db_service = TransactionAlertService()
        result = db_service.get_alerts_by_operator(current_user['id'], limit)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"获取个人报警失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取个人报警失败: {str(e)}'
        }), 500

@transaction_alerts_bp.route('/<int:alert_id>/resolve', methods=['POST'])
@token_required
@has_permission('branch_manage')
def resolve_alert(current_user, alert_id):
    """
    解决报警事件
    
    权限要求:
        - 需要网点管理权限
    """
    try:
        from services.transaction_alert_service import TransactionAlertService
        
        result = TransactionAlertService.resolve_alert(alert_id, current_user['id'])
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"解决报警事件失败: {e}")
        return jsonify({
            'success': False,
            'message': f'解决报警事件失败: {str(e)}'
        }), 500 