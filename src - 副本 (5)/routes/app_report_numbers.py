#!/usr/bin/env python3
"""
报告编号管理API
提供报告编号生成、查询、统计等功能
"""

from flask import Blueprint, request, jsonify, g
from sqlalchemy import text
from datetime import datetime

from services.db_service import DatabaseService
from services.report_number_generator import ReportNumberGenerator
from services.auth_service import token_required, has_permission

report_number_bp = Blueprint('report_numbers', __name__, url_prefix='/api')


@report_number_bp.route('/report-numbers/amlo/generate', methods=['POST'])
@token_required
@has_permission('amlo_report_generate')
def generate_amlo_report_number(current_user):
    """
    生成AMLO报告编号
    
    POST /api/report-numbers/amlo/generate
    {
        "currency_code": "USD",
        "transaction_id": 123  // 可选
    }
    
    响应:
    {
        "success": true,
        "data": {
            "report_number": "001-001-68-100015USD",
            "institution_code": "001",
            "branch_code": "001",
            "year_suffix": "68",
            "sequence_number": "100015",
            "currency_code": "USD"
        }
    }
    """
    session = DatabaseService.get_session()
    
    try:
        current_user = g.current_user
        branch_id = current_user.get('branch_id')
        operator_id = current_user.get('id')
        
        if not branch_id:
            return jsonify({
                'success': False,
                'message': '用户网点信息不完整'
            }), 400
        
        data = request.get_json() or {}
        currency_code = data.get('currency_code', '').strip().upper()
        transaction_id = data.get('transaction_id')
        
        if not currency_code:
            return jsonify({
                'success': False,
                'message': '币种代码不能为空'
            }), 400
        
        if len(currency_code) != 3:
            return jsonify({
                'success': False,
                'message': '币种代码必须为3位ISO 4217标准代码'
            }), 400
        
        # 生成报告编号
        report_number = ReportNumberGenerator.generate_amlo_report_number(
            session=session,
            branch_id=branch_id,
            currency_code=currency_code,
            operator_id=operator_id,
            transaction_id=transaction_id
        )
        
        # 解析报告编号
        parsed_info = ReportNumberGenerator.parse_report_number(report_number)
        
        return jsonify({
            'success': True,
            'data': {
                'report_number': report_number,
                'institution_code': parsed_info['institution_code'],
                'branch_code': parsed_info['branch_code'],
                'year_suffix': parsed_info['year_suffix'],
                'sequence_number': parsed_info['sequence_number'],
                'currency_code': parsed_info['currency_code']
            }
        })
        
    except Exception as e:
        DatabaseService.rollback_session(session)
        print(f"生成AMLO报告编号失败: {e}")
        return jsonify({
            'success': False,
            'message': f'生成报告编号失败: {str(e)}'
        }), 500
        
    finally:
        DatabaseService.close_session(session)


@report_number_bp.route('/report-numbers/bot/generate', methods=['POST'])
@token_required
@has_permission('bot_report_generate')
def generate_bot_report_number(current_user):
    """
    生成BOT报告编号
    
    POST /api/report-numbers/bot/generate
    {
        "report_type": "BuyFX",
        "transaction_id": 123  // 可选
    }
    
    响应:
    {
        "success": true,
        "data": {
            "report_number": "001-001-68-000001",
            "institution_code": "001",
            "branch_code": "001", 
            "year_suffix": "68",
            "sequence_number": "100015",
            "report_type": "BuyFX"
        }
    }
    """
    session = DatabaseService.get_session()
    
    try:
        current_user = g.current_user
        branch_id = current_user.get('branch_id')
        operator_id = current_user.get('id')
        
        if not branch_id:
            return jsonify({
                'success': False,
                'message': '用户网点信息不完整'
            }), 400
        
        data = request.get_json() or {}
        report_type = data.get('report_type', '').strip()
        transaction_id = data.get('transaction_id')
        
        if not report_type:
            return jsonify({
                'success': False,
                'message': '报告类型不能为空'
            }), 400
        
        valid_types = ['BuyFX', 'SellFX', 'FCD']
        if report_type not in valid_types:
            return jsonify({
                'success': False,
                'message': f'报告类型必须是: {", ".join(valid_types)}'
            }), 400
        
        # 生成报告编号
        report_number = ReportNumberGenerator.generate_bot_report_number(
            session=session,
            branch_id=branch_id,
            report_type=report_type,
            operator_id=operator_id,
            transaction_id=transaction_id
        )
        
        # 解析报告编号
        parsed_info = ReportNumberGenerator.parse_report_number(report_number)
        
        return jsonify({
            'success': True,
            'data': {
                'report_number': report_number,
                'institution_code': parsed_info['institution_code'],
                'branch_code': parsed_info['branch_code'],
                'year_suffix': parsed_info['year_suffix'],
                'sequence_number': parsed_info['sequence_number'],
                'report_type': report_type
            }
        })
        
    except Exception as e:
        DatabaseService.rollback_session(session)
        print(f"生成BOT报告编号失败: {e}")
        return jsonify({
            'success': False,
            'message': f'生成报告编号失败: {str(e)}'
        }), 500
        
    finally:
        DatabaseService.close_session(session)


@report_number_bp.route('/report-numbers/validate', methods=['POST'])
@token_required
def validate_report_number(current_user):
    """
    验证报告编号格式
    
    POST /api/report-numbers/validate
    {
        "report_number": "001-001-68-000001USD",
        "report_type": "AMLO"  // 可选，自动检测
    }
    
    响应:
    {
        "success": true,
        "data": {
            "is_valid": true,
            "report_type": "AMLO",
            "parsed_info": {...}
        }
    }
    """
    try:
        data = request.get_json() or {}
        report_number = data.get('report_number', '').strip()
        
        if not report_number:
            return jsonify({
                'success': False,
                'message': '报告编号不能为空'
            }), 400
        
        # 自动检测报告类型
        report_type = data.get('report_type', 'AMLO')
        if len(report_number.split('-')[-1]) > 6:
            report_type = 'AMLO'
        else:
            report_type = 'BOT'
        
        # 验证格式
        is_valid = ReportNumberGenerator.validate_report_number(report_number, report_type)
        
        if is_valid:
            parsed_info = ReportNumberGenerator.parse_report_number(report_number)
            return jsonify({
                'success': True,
                'data': {
                    'is_valid': True,
                    'report_type': report_type,
                    'parsed_info': parsed_info
                }
            })
        else:
            return jsonify({
                'success': True,
                'data': {
                    'is_valid': False,
                    'report_type': report_type,
                    'parsed_info': None
                }
            })
        
    except Exception as e:
        print(f"验证报告编号失败: {e}")
        return jsonify({
            'success': False,
            'message': f'验证失败: {str(e)}'
        }), 500


@report_number_bp.route('/report-numbers/statistics', methods=['GET'])
@token_required
@has_permission('report_number_view')
def get_report_number_statistics(current_user):
    """
    获取报告编号使用统计
    
    GET /api/report-numbers/statistics?year_month=2025-10&branch_id=1
    
    响应:
    {
        "success": true,
        "data": {
            "year_month": "2025-10",
            "amlo_sequences": [...],
            "bot_sequences": [...]
        }
    }
    """
    session = DatabaseService.get_session()
    
    try:
        current_user = g.current_user
        branch_id = current_user.get('branch_id')
        
        # 允许管理员查看其他网点的统计
        requested_branch_id = request.args.get('branch_id', type=int)
        if requested_branch_id and current_user.get('role_name') in ['Admin', 'SuperAdmin']:
            branch_id = requested_branch_id
        
        year_month = request.args.get('year_month')
        
        # 获取统计信息
        statistics = ReportNumberGenerator.get_sequence_statistics(
            session=session,
            branch_id=branch_id,
            year_month=year_month
        )
        
        return jsonify({
            'success': True,
            'data': statistics
        })
        
    except Exception as e:
        print(f"获取统计信息失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取统计信息失败: {str(e)}'
        }), 500
        
    finally:
        DatabaseService.close_session(session)


@report_number_bp.route('/report-numbers/history', methods=['GET'])
@token_required
@has_permission('report_number_view')
def get_report_number_history(current_user):
    """
    获取报告编号使用历史
    
    GET /api/report-numbers/history?page=1&page_size=20&start_date=2025-10-01&end_date=2025-10-31
    
    响应:
    {
        "success": true,
        "data": {
            "items": [...],
            "total": 100,
            "page": 1,
            "page_size": 20,
            "total_pages": 5
        }
    }
    """
    session = DatabaseService.get_session()
    
    try:
        current_user = g.current_user
        branch_id = current_user.get('branch_id')
        
        # 分页参数
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        report_type = request.args.get('report_type')
        
        # 构建查询条件
        where_clauses = ['rnl.branch_id = :branch_id']
        params = {'branch_id': branch_id}
        
        if start_date:
            where_clauses.append('DATE(rnl.created_at) >= :start_date')
            params['start_date'] = start_date
        
        if end_date:
            where_clauses.append('DATE(rnl.created_at) <= :end_date')
            params['end_date'] = end_date
        
        if report_type:
            where_clauses.append('rnl.report_type = :report_type')
            params['report_type'] = report_type
        
        where_sql = ' AND '.join(where_clauses)
        
        # 查询总数
        count_sql = text(f"""
            SELECT COUNT(*)
            FROM report_number_logs rnl
            WHERE {where_sql}
        """)
        
        total_result = session.execute(count_sql, params)
        total = total_result.scalar() or 0
        
        # 查询数据
        offset = (page - 1) * page_size
        
        data_sql = text(f"""
            SELECT 
                rnl.id,
                rnl.report_number,
                rnl.report_type,
                rnl.currency_code,
                rnl.created_at,
                u.name as operator_name,
                b.branch_name,
                t.id as transaction_id
            FROM report_number_logs rnl
            LEFT JOIN users u ON rnl.operator_id = u.id
            LEFT JOIN branch b ON rnl.branch_id = b.id
            LEFT JOIN exchange_transactions t ON rnl.transaction_id = t.id
            WHERE {where_sql}
            ORDER BY rnl.created_at DESC
            LIMIT :limit OFFSET :offset
        """)
        
        params['limit'] = page_size
        params['offset'] = offset
        
        data_result = session.execute(data_sql, params)
        items = [dict(row._mapping) for row in data_result]
        
        # 计算总页数
        total_pages = (total + page_size - 1) // page_size
        
        return jsonify({
            'success': True,
            'data': {
                'items': items,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages
            }
        })
        
    except Exception as e:
        print(f"获取历史记录失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取历史记录失败: {str(e)}'
        }), 500
        
    finally:
        DatabaseService.close_session(session)
