# -*- coding: utf-8 -*-
"""
AMLO审核API路由
提供预约审核、报告上报的核心接口
版本: v1.0
创建日期: 2025-10-02
"""

from flask import Blueprint, request, jsonify, g, send_file
from functools import wraps
from services.db_service import SessionLocal
from services.repform import ReportDataService
from services.pdf import AMLOPDFGenerator, AMLOFormFiller, adapt_route_data_to_pdf_data, generate_amlo_pdf
from services.auth_service import token_required, permission_required
from sqlalchemy import text
from datetime import datetime
import traceback
import json
import os
import tempfile
import logging

# Get logger instance - DO NOT call basicConfig() here as it will override
# the logging configuration already set in main.py
logger = logging.getLogger(__name__)

# 创建Blueprint - 统一使用url_prefix方式
app_amlo = Blueprint('app_amlo', __name__, url_prefix='/api/amlo')


def _prepare_amlo_pdf_payload(session, result_row):
    """
    根据预约记录准备PDF填充数据

    Returns:
        (pdf_data, form_data)
    """
    form_data = json.loads(result_row.form_data) if result_row.form_data else {}

    def _normalize_bool(value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in ('1', 'true', 'yes', 'y', 'on')
        if isinstance(value, (int, float)):
            return value != 0
        return False

    def _combine_name(prefix: str, fallback: str = ''):
        title = form_data.get(f'{prefix}_title') or ''
        first = form_data.get(f'{prefix}_firstname') or ''
        last = form_data.get(f'{prefix}_lastname') or ''
        company = form_data.get(f'{prefix}_company_name') or ''
        full = form_data.get(f'{prefix}_full_name') or ''
        parts = [p for p in [title, first, last] if p]
        if company:
            parts.append(company)
        candidate = full or ' '.join(parts).strip()
        return candidate or fallback

    def _combine_address(prefix: str):
        order = [
            'number', 'village', 'lane', 'road',
            'subdistrict', 'district', 'province', 'postalcode'
        ]
        values = []
        for suffix in order:
            key = f'{prefix}_{suffix}'
            val = form_data.get(key)
            if val:
                values.append(str(val))
        return ' '.join(values).strip()

    def _parse_date_from_fields(day_key, month_key, year_key):
        day = form_data.get(day_key)
        month = form_data.get(month_key)
        year = form_data.get(year_key)
        if not all([day, month, year]):
            return None
        try:
            day = int(day)
            month = int(month)
            year = int(year)
            if year < 100:
                year += 2000
            return datetime(year, month, day)
        except Exception:
            return None

    maker_name = _combine_name('maker', result_row.customer_name or '')
    joint_party_name = _combine_name('joint_party', form_data.get('joint_party_name', ''))
    maker_address = _combine_address('maker_address') or result_row.customer_address or ''
    joint_party_address = form_data.get('joint_party_address') or _combine_address('joint_party_address')

    maker_phone = form_data.get('maker_phone') or form_data.get('maker_mobile') or ''
    maker_occupation = form_data.get('maker_occupation_type') or form_data.get('maker_occupation') or ''
    maker_employer = form_data.get('maker_occupation_employer') or ''
    beneficiary_name = joint_party_name or form_data.get('beneficiary_name', '')

    direction = (result_row.direction or '').lower()
    transaction_type = 'buy' if direction == 'buy' else 'sell'
    foreign_amount = float(form_data.get('total_amount') or result_row.amount or 0)
    amount_thb = float(result_row.amount_thb or form_data.get('amount_thb') or 0)

    logger.info(f"[PDF数据准备] 预约ID={result_row.id}, direction='{direction}', transaction_type='{transaction_type}', foreign_amount={foreign_amount}, amount_thb={amount_thb}")

    form_transaction_date = _parse_date_from_fields('transaction_date_day', 'transaction_date_month', 'transaction_date_year')
    transaction_date = form_transaction_date or result_row.transaction_date

    form_report_date = _parse_date_from_fields('report_date_day', 'report_date_month', 'report_date_year')
    report_date_str = (form_report_date or datetime.now()).strftime('%d/%m/%Y')

    branch_id = getattr(result_row, 'branch_id', None)
    institution_code, branch_code = None, None
    if branch_id:
        try:
            # 使用ReportNumberGenerator获取网点代码
            from services.report_number_generator import ReportNumberGenerator
            branch_codes = ReportNumberGenerator.get_branch_codes(session, branch_id)
            institution_code = branch_codes['institution_code']
            branch_code = branch_codes['branch_code']
        except Exception as fetch_error:
            logger.warning(f"获取网点机构代码失败: {fetch_error}")
            institution_code = getattr(result_row, 'amlo_institution_code', None) or '001'
            branch_code = getattr(result_row, 'branch_code', None) or '001'
    institution_code = institution_code or getattr(result_row, 'amlo_institution_code', None) or '001'
    branch_code = branch_code or getattr(result_row, 'branch_code', None) or '001'

    pdf_data = {
        'report_number': result_row.reservation_no,
        'is_amendment': _normalize_bool(form_data.get('is_amendment_report')),
        'maker_type': 'juristic' if _normalize_bool(form_data.get('maker_type_juristic')) else 'person',
        'maker_name': maker_name,
        'maker_id': form_data.get('maker_id_number') or result_row.customer_id,
        'maker_address': maker_address,
        'maker_phone': maker_phone,
        'maker_occupation': maker_occupation or maker_employer,
        'joint_party_name': joint_party_name,
        'joint_party_address': joint_party_address or '',
        'transaction_date': (transaction_date.strftime('%d/%m/%Y') if transaction_date else ''),
        'transaction_type': transaction_type,
        'currency_code': form_data.get('currency_code') or form_data.get('foreign_currency_code') or '',
        'foreign_amount': foreign_amount,
        'amount_thb': amount_thb,
        'remarks': form_data.get('remarks', ''),
        'transaction_purpose': form_data.get('transaction_purpose') or form_data.get('exchange_other_transaction') or '',
        'beneficiary_name': beneficiary_name or form_data.get('joint_party_name', ''),
        'reporter_name': getattr(result_row, 'reporter_name', None) or '',
        'reporter_position': form_data.get('reporter_position', ''),
        'report_date': report_date_str,
        'institution_code': institution_code,
        'branch_code': branch_code,
        'form_data': form_data
    }

    logger.info(f"[PDF数据准备] 最终pdf_data: transaction_type='{pdf_data['transaction_type']}', foreign_amount={pdf_data['foreign_amount']}")

    return pdf_data, form_data


# 权限装饰器
def amlo_permission_required(permission):
    """AMLO权限检查装饰器"""
    return permission_required(permission)


@app_amlo.route('/check-customer-reservation', methods=['GET'])
@token_required
def check_customer_reservation(current_user):
    """
    检查客户是否有预约记录
    
    GET /api/amlo/check-customer-reservation?customer_id=xxx
    
    返回:
    {
        "has_reservation": true,
        "status": "approved",  // pending, approved, rejected, completed
        "reservation_id": 123,
        "report_type": "AMLO-1-01",
        "approved_amount": 2130000,
        "audit_notes": "审核通过",
        "reject_reason": null,
        "auditor_name": "管理员"
    }
    """
    session = SessionLocal()
    
    try:
        customer_id = request.args.get('customer_id')
        if not customer_id:
            return jsonify({
                'success': False,
                'message': '缺少customer_id参数'
            }), 400
        
        # 查询最近的预约记录（未完成交易的）
        sql = text("""
            SELECT 
                r.id,
                r.reservation_no,
                r.report_type,
                r.status,
                r.local_amount,
                r.audit_notes,
                r.rejection_reason,
                r.auditor_id,
                u.name as auditor_name,
                r.created_at,
                r.audit_time
            FROM Reserved_Transaction r
            LEFT JOIN users u ON r.auditor_id = u.id
            WHERE r.customer_id = :customer_id
              AND r.status IN ('pending', 'approved', 'rejected')
            ORDER BY r.created_at DESC
            LIMIT 1
        """)
        
        result = session.execute(sql, {'customer_id': customer_id}).fetchone()
        
        if not result:
            return jsonify({
                'success': True,
                'has_reservation': False
            })
        
        return jsonify({
            'success': True,
            'has_reservation': True,
            'reservation_id': result[0],
            'reservation_no': result[1],
            'report_type': result[2],
            'status': result[3],
            'approved_amount': float(result[4]) if result[4] else 0,
            'audit_notes': result[5],
            'rejection_reason': result[6],
            'auditor_name': result[8],
            'created_at': str(result[9]),
            'audit_time': str(result[10]) if result[10] else None
        })
        
    except Exception as e:
        logger.error(f"Error checking customer reservation: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}'
        }), 500
    finally:
        session.close()


@app_amlo.route('/reservations', methods=['GET'])
@token_required
# @amlo_permission_required('amlo_reservation_view')  # 临时注释掉权限检查
def get_reservations(current_user):
    """
    查询预约记录列表

    GET /api/amlo/reservations?status=pending&page=1&page_size=20&start_date=2025-10-01&end_date=2025-10-31

    查询参数:
    - status: 状态过滤 (pending/approved/rejected/completed/reported)
    - page: 页码，默认1
    - page_size: 每页记录数，默认20
    - start_date: 开始日期
    - end_date: 结束日期
    - customer_id: 客户证件号
    - report_type: 报告类型

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
    session = SessionLocal()

    try:
        # 获取查询参数
        status = request.args.get('status')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        customer_id = request.args.get('customer_id')
        report_type = request.args.get('report_type')

        # 获取当前用户的branch_id
        branch_id = g.current_user.get('branch_id')

        logger.debug(f"查询预约记录 - 当前用户branch_id: {branch_id}")
        logger.debug(f"查询预约记录 - 状态过滤: {status if status else '无(查询所有状态)'}")
        logger.debug(f"查询预约记录 - page: {page}, page_size: {page_size}")

        # 构建查询条件
        where_clauses = ['branch_id = :branch_id']
        params = {'branch_id': branch_id}

        if status:
            where_clauses.append('status = :status')
            params['status'] = status

        if start_date:
            where_clauses.append('DATE(created_at) >= :start_date')
            params['start_date'] = start_date

        if end_date:
            where_clauses.append('DATE(created_at) <= :end_date')
            params['end_date'] = end_date

        if customer_id:
            where_clauses.append('customer_id = :customer_id')
            params['customer_id'] = customer_id

        if report_type:
            where_clauses.append('report_type = :report_type')
            params['report_type'] = report_type

        where_sql = ' AND '.join(where_clauses)

        logger.debug(f"执行的SQL查询条件: {where_sql}")
        logger.debug(f"查询参数: {params}")

        # 查询总数
        count_sql = text(f"""
            SELECT COUNT(*) as total
            FROM Reserved_Transaction
            WHERE {where_sql}
        """)

        count_result = session.execute(count_sql, params)
        total = count_result.scalar()

        logger.debug(f"查询总记录数: {total}")

        # 查询数据
        offset = (page - 1) * page_size
        data_sql = text(f"""
            SELECT
                id, reservation_no, customer_id, customer_name,
                currency_id, direction, amount, local_amount, rate,
                trigger_type, report_type, status,
                branch_id, operator_id, auditor_id,
                created_at, audit_time, rejection_reason,
                exchange_type, funding_source
            FROM Reserved_Transaction
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """)

        params['limit'] = page_size
        params['offset'] = offset

        data_result = session.execute(data_sql, params)
        items = [dict(row._mapping) for row in data_result]

        logger.debug(f"查询结果 - 总记录数: {total}, 返回记录数: {len(items)}")
        if len(items) > 0:
            logger.debug(f"第一条记录: id={items[0].get('id')}, reservation_no={items[0].get('reservation_no')}, status={items[0].get('status')}, branch_id={items[0].get('branch_id')}")

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
        logger.error(f"Error in get_reservations: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'查询预约记录失败: {str(e)}'
        }), 500

    finally:
        session.close()


@app_amlo.route('/reservations/<int:reservation_id>/audit', methods=['POST'])
@token_required
@amlo_permission_required('amlo_reservation_audit')
def audit_reservation(current_user, reservation_id):
    """
    审核预约记录

    POST /api/amlo/reservations/1/audit

    请求体:
    {
        "action": "approve",  // approve/reject
        "rejection_reason": "资金来源不明",  // 驳回时必填
        "remarks": "备注信息"
    }

    响应:
    {
        "success": true,
        "message": "审核通过"
    }
    """
    session = SessionLocal()

    try:
        request_data = request.get_json()

        if not request_data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400

        action = request_data.get('action')
        rejection_reason = request_data.get('rejection_reason')
        remarks = request_data.get('remarks')

        if action not in ['approve', 'reject']:
            return jsonify({
                'success': False,
                'message': 'action参数必须是approve或reject'
            }), 400

        if action == 'reject' and not rejection_reason:
            return jsonify({
                'success': False,
                'message': '驳回时必须提供驳回原因'
            }), 400

        # 检查预约记录是否存在
        reservation = ReportDataService.get_reservation_by_id(session, reservation_id)
        if not reservation:
            return jsonify({
                'success': False,
                'message': f'预约记录不存在: {reservation_id}'
            }), 404

        # 检查状态
        if reservation['status'] != 'pending':
            return jsonify({
                'success': False,
                'message': f'该预约记录状态为{reservation["status"]}，无法审核'
            }), 400

        # 更新状态
        new_status = 'approved' if action == 'approve' else 'rejected'
        current_user = g.current_user

        update_kwargs = {
            'auditor_id': current_user['id']
        }

        if rejection_reason:
            update_kwargs['rejection_reason'] = rejection_reason

        if remarks:
            update_kwargs['remarks'] = remarks

        success = ReportDataService.update_reservation_status(
            session,
            reservation_id,
            new_status,
            **update_kwargs
        )

        if success:
            # 🔧 修复：审核通过后自动创建AMLOReport记录
            if action == 'approve':
                try:
                    # 🔧 查询预约记录详情（修复表名：amlo_reservations -> Reserved_Transaction）
                    reservation_query = text("""
                        SELECT
                            r.reservation_no,
                            r.report_type,
                            r.customer_id,
                            r.customer_name,
                            r.local_amount,
                            r.currency_id,
                            r.direction,
                            r.created_at,
                            r.branch_id,
                            r.operator_id
                        FROM Reserved_Transaction r
                        WHERE r.id = :reservation_id
                    """)

                    reservation_data = session.execute(reservation_query, {'reservation_id': reservation_id}).fetchone()

                    if reservation_data:
                        # 查询币种代码
                        currency_query = text("""
                            SELECT code FROM currencies WHERE id = :currency_id
                        """)
                        currency_result = session.execute(currency_query, {'currency_id': reservation_data.currency_id}).fetchone()
                        currency_code = currency_result[0] if currency_result else 'USD'

                        # 创建AMLO报告记录（使用正确的表名和字段）
                        insert_sql = text("""
                            INSERT INTO AMLOReport (
                                report_no, report_type, report_format,
                                reserved_id, customer_id, customer_name,
                                transaction_amount, transaction_date, is_reported,
                                branch_id, operator_id, language,
                                created_at, updated_at
                            )
                            VALUES (
                                :report_no, :report_type, :report_format,
                                :reserved_id, :customer_id, :customer_name,
                                :transaction_amount, :transaction_date, 0,
                                :branch_id, :operator_id, 'th',
                                NOW(), NOW()
                            )
                        """)

                        session.execute(insert_sql, {
                            'report_no': reservation_data.reservation_no,
                            'report_type': reservation_data.report_type,
                            'report_format': reservation_data.report_type,  # 使用相同的report_type
                            'reserved_id': reservation_id,
                            'customer_id': reservation_data.customer_id,
                            'customer_name': reservation_data.customer_name,
                            'transaction_amount': float(reservation_data.local_amount or 0),
                            'transaction_date': reservation_data.created_at.date() if reservation_data.created_at else None,
                            'branch_id': reservation_data.branch_id,
                            'operator_id': reservation_data.operator_id
                        })

                        session.commit()

                        logger.info(f"✅ 审核通过，已为预约 {reservation_id} 创建AMLO报告记录 {reservation_data.reservation_no}")
                    else:
                        logger.warning(f"⚠️ 未找到预约记录 {reservation_id}，无法创建AMLO报告")

                except Exception as create_error:
                    logger.error(f"❌ 创建AMLO报告记录失败: {str(create_error)}")
                    session.rollback()  # 回滚报告创建，但保留审核状态
                    # 不影响审核结果，只记录错误
                    traceback.print_exc()

            message = '审核通过' if action == 'approve' else '已驳回'
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'message': '审核失败'
            }), 500

    except Exception as e:
        logger.error(f"Error in audit_reservation: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'审核预约失败: {str(e)}'
        }), 500

    finally:
        session.close()


@app_amlo.route('/reservations/<int:reservation_id>/reverse-audit', methods=['POST'])
@token_required
@amlo_permission_required('amlo_reservation_audit')
def reverse_audit(current_user, reservation_id):
    """
    反审核预约记录

    POST /api/amlo/reservations/1/reverse-audit

    请求体:
    {
        "remarks": "需要重新审核"
    }

    响应:
    {
        "success": true,
        "message": "已反审核"
    }
    """
    session = SessionLocal()

    try:
        request_data = request.get_json() or {}
        remarks = request_data.get('remarks')

        # 检查预约记录是否存在
        reservation = ReportDataService.get_reservation_by_id(session, reservation_id)
        if not reservation:
            return jsonify({
                'success': False,
                'message': f'预约记录不存在: {reservation_id}'
            }), 404

        # 检查状态
        if reservation['status'] not in ['approved', 'rejected']:
            return jsonify({
                'success': False,
                'message': f'该预约记录状态为{reservation["status"]}，无法反审核'
            }), 400

        # 更新状态为pending
        update_kwargs = {}
        if remarks:
            update_kwargs['remarks'] = remarks

        success = ReportDataService.update_reservation_status(
            session,
            reservation_id,
            'pending',
            **update_kwargs
        )

        if success:
            return jsonify({
                'success': True,
                'message': '已反审核'
            })
        else:
            return jsonify({
                'success': False,
                'message': '反审核失败'
            }), 500

    except Exception as e:
        logger.error(f"Error in reverse_audit: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'反审核失败: {str(e)}'
        }), 500

    finally:
        session.close()


@app_amlo.route('/reports', methods=['GET'])
@token_required
@amlo_permission_required('amlo_report_view')
def get_amlo_reports(current_user):
    """
    查询AMLO报告列表

    GET /api/amlo/reports?is_reported=false&page=1&page_size=20&start_date=2025-10-01&end_date=2025-10-31

    查询参数:
    - is_reported: 是否已上报 (true/false)
    - page: 页码，默认1
    - page_size: 每页记录数，默认20
    - start_date: 开始日期
    - end_date: 结束日期
    - report_type: 报告类型
    - customer_id: 客户证件号

    响应:
    {
        "success": true,
        "data": {
            "items": [...],
            "total": 50,
            "page": 1,
            "page_size": 20,
            "total_pages": 3
        }
    }
    """
    session = SessionLocal()

    try:
        # 获取查询参数
        is_reported = request.args.get('is_reported')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        report_type = request.args.get('report_type')
        customer_id = request.args.get('customer_id')

        # 获取当前用户的branch_id
        branch_id = g.current_user.get('branch_id')

        # 构建查询条件
        where_clauses = ['branch_id = :branch_id']
        params = {'branch_id': branch_id}

        if is_reported is not None:
            where_clauses.append('is_reported = :is_reported')
            params['is_reported'] = (is_reported.lower() == 'true')

        if start_date:
            where_clauses.append('DATE(created_at) >= :start_date')
            params['start_date'] = start_date

        if end_date:
            where_clauses.append('DATE(created_at) <= :end_date')
            params['end_date'] = end_date

        if report_type:
            where_clauses.append('report_type = :report_type')
            params['report_type'] = report_type

        if customer_id:
            where_clauses.append('customer_id = :customer_id')
            params['customer_id'] = customer_id

        where_sql = ' AND '.join(where_clauses)

        # 查询总数
        count_sql = text(f"""
            SELECT COUNT(*) as total
            FROM AMLOReport
            WHERE {where_sql}
        """)

        count_result = session.execute(count_sql, params)
        total = count_result.scalar()

        # 查询数据
        offset = (page - 1) * page_size
        data_sql = text(f"""
            SELECT
                id, report_no, report_type, report_format,
                reserved_id, transaction_id, customer_id, customer_name,
                transaction_amount, transaction_date,
                pdf_filename, pdf_path, is_reported, report_time,
                branch_id, operator_id, language,
                created_at, updated_at
            FROM AMLOReport
            WHERE {where_sql}
            ORDER BY created_at DESC
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
        logger.error(f"Error in get_amlo_reports: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'查询AMLO报告失败: {str(e)}'
        }), 500

    finally:
        session.close()


@app_amlo.route('/reports/mark-reported', methods=['POST'])
@token_required
def mark_amlo_reported(current_user):
    """
    标记AMLO报告为已上报
    
    POST /api/amlo/reports/mark-reported
    {
        "ids": [1, 2, 3]
    }
    
    返回:
    {
        "success": true,
        "updated_count": 3
    }
    """
    session = SessionLocal()
    
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        
        if not ids:
            return jsonify({
                'success': False,
                'message': '缺少报告ID'
            }), 400
        
        # 获取当前用户ID
        user_id = g.current_user.get('id', 1)
        
        # 更新记录
        sql = text("""
            UPDATE AMLOReport
            SET is_reported = TRUE,
                report_time = NOW(),
                reporter_id = :user_id
            WHERE id IN :ids
        """)
        
        result = session.execute(sql, {
            'user_id': user_id,
            'ids': tuple(ids)
        })
        
        session.commit()
        
        return jsonify({
            'success': True,
            'updated_count': result.rowcount,
            'message': f'成功标记{result.rowcount}条报告为已上报'
        })
        
    except Exception as e:
        session.rollback()
        logger.error(f"标记AMLO已上报失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'标记失败: {str(e)}'
        }), 500
    finally:
        session.close()


@app_amlo.route('/reports/batch-report', methods=['POST'])
@token_required
@amlo_permission_required('amlo_report_submit')
def batch_report(current_user):
    """
    批量上报AMLO报告

    POST /api/amlo/reports/batch-report

    请求体:
    {
        "report_ids": [1, 2, 3, 4]
    }

    响应:
    {
        "success": true,
        "message": "成功上报4条记录",
        "data": {
            "success_count": 4,
            "failed_count": 0,
            "failed_ids": []
        }
    }
    """
    session = SessionLocal()

    try:
        request_data = request.get_json()

        if not request_data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400

        report_ids = request_data.get('report_ids', [])

        if not report_ids or not isinstance(report_ids, list):
            return jsonify({
                'success': False,
                'message': 'report_ids必须是非空数组'
            }), 400

        current_user = g.current_user
        reporter_id = current_user['id']

        success_count = 0
        failed_count = 0
        failed_ids = []

        for report_id in report_ids:
            try:
                # 检查报告是否存在
                check_sql = text("""
                    SELECT id, is_reported
                    FROM AMLOReport
                    WHERE id = :report_id
                        AND branch_id = :branch_id
                """)

                check_result = session.execute(
                    check_sql,
                    {'report_id': report_id, 'branch_id': current_user['branch_id']}
                )
                report_row = check_result.first()

                if not report_row:
                    failed_count += 1
                    failed_ids.append(report_id)
                    continue

                if report_row[1]:  # is_reported
                    failed_count += 1
                    failed_ids.append(report_id)
                    continue

                # 更新为已上报
                update_sql = text("""
                    UPDATE AMLOReport
                    SET is_reported = TRUE,
                        report_time = NOW(),
                        reporter_id = :reporter_id,
                        updated_at = NOW()
                    WHERE id = :report_id
                """)

                session.execute(
                    update_sql,
                    {'report_id': report_id, 'reporter_id': reporter_id}
                )

                success_count += 1

            except Exception as e:
                logger.error(f"Error reporting AMLO report {report_id}: {str(e)}")
                failed_count += 1
                failed_ids.append(report_id)

        # 提交事务
        session.commit()

        return jsonify({
            'success': True,
            'message': f'成功上报{success_count}条记录',
            'data': {
                'success_count': success_count,
                'failed_count': failed_count,
                'failed_ids': failed_ids
            }
        })

    except Exception as e:
        session.rollback()
        logger.error(f"Error in batch_report: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'批量上报失败: {str(e)}'
        }), 500

    finally:
        session.close()


@app_amlo.route('/reservations/<int:reservation_id>/complete', methods=['POST'])
@token_required
def complete_reservation(current_user, reservation_id):
    """
    完成预约（交易完成后）

    POST /api/amlo/reservations/1/complete

    请求体:
    {
        "linked_transaction_id": 12345
    }

    响应:
    {
        "success": true,
        "message": "预约已完成"
    }
    """
    session = SessionLocal()

    try:
        request_data = request.get_json() or {}
        linked_transaction_id = request_data.get('linked_transaction_id')

        # 检查预约记录是否存在
        reservation = ReportDataService.get_reservation_by_id(session, reservation_id)
        if not reservation:
            return jsonify({
                'success': False,
                'message': f'预约记录不存在: {reservation_id}'
            }), 404

        # 检查状态
        if reservation['status'] != 'approved':
            return jsonify({
                'success': False,
                'message': f'该预约记录状态为{reservation["status"]}，无法完成'
            }), 400

        # 更新状态为completed
        update_kwargs = {}
        if linked_transaction_id:
            update_kwargs['linked_transaction_id'] = linked_transaction_id

        success = ReportDataService.update_reservation_status(
            session,
            reservation_id,
            'completed',
            **update_kwargs
        )

        if success:
            return jsonify({
                'success': True,
                'message': '预约已完成'
            })
        else:
            return jsonify({
                'success': False,
                'message': '完成预约失败'
            }), 500

    except Exception as e:
        logger.error(f"Error in complete_reservation: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'完成预约失败: {str(e)}'
        }), 500

    finally:
        session.close()


@app_amlo.route('/reports/<int:report_id>/generate-pdf', methods=['GET'])
@token_required
@amlo_permission_required('amlo_report_view')
def generate_report_pdf(current_user, report_id):
    """
    生成AMLO报告PDF文件 (使用新的CSV映射PDF生成器)

    GET /api/amlo/reports/<report_id>/generate-pdf

    响应:
    - 成功: 返回PDF文件流 (application/pdf)
    - 失败: {"success": false, "message": "错误信息"}
    """
    print(f"\n{'='*80}")
    print(f"[AMLO PDF STEP 1] 收到PDF生成请求")
    print(f"[AMLO PDF] 报告ID: {report_id}")
    print(f"[AMLO PDF] 用户: {current_user}")
    print(f"[AMLO PDF] 用户branch_id: {g.current_user.get('branch_id')}")
    print(f"{'='*80}\n")

    session = SessionLocal()
    print(f"[AMLO PDF STEP 2] 数据库会话已创建")

    try:
        # 查询报告记录
        print(f"[AMLO PDF STEP 3] 开始查询数据库...")
        report_sql = text("""
            SELECT
                r.id, r.reservation_no, r.report_type, r.customer_id, r.customer_name,
                r.currency_id, r.direction, r.amount, r.local_amount,
                r.form_data, r.created_at, r.branch_id,
                b.branch_name, b.branch_code, b.amlo_institution_code
            FROM Reserved_Transaction r
            LEFT JOIN branches b ON r.branch_id = b.id
            WHERE r.id = :report_id AND r.branch_id = :branch_id
        """)

        query_params = {
            'report_id': report_id,
            'branch_id': g.current_user.get('branch_id')
        }
        print(f"[AMLO PDF] 查询参数: {query_params}")

        result = session.execute(report_sql, query_params).fetchone()

        print(f"[AMLO PDF STEP 4] 数据库查询完成")
        print(f"[AMLO PDF] 查询结果: {'找到记录' if result else '未找到记录'}")

        if not result:
            print(f"[AMLO PDF] ERROR: 报告不存在 - ID: {report_id}, branch_id: {g.current_user.get('branch_id')}")
            return jsonify({
                'success': False,
                'message': '报告不存在'
            }), 404

        print(f"[AMLO PDF] 报告类型: {result.report_type}")
        print(f"[AMLO PDF] 预约编号: {result.reservation_no}")

        # 创建临时文件和项目目录副本
        print(f"[AMLO PDF STEP 5] 准备文件路径...")
        temp_dir = tempfile.gettempdir()
        pdf_filename = f"{result.report_type}_{result.reservation_no or result.id}.pdf"
        pdf_path = os.path.join(temp_dir, pdf_filename)
        print(f"[AMLO PDF] 临时文件路径: {pdf_path}")

        # 同时保存到项目目录的amlo_pdfs文件夹（方便查看）
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        amlo_pdf_dir = os.path.join(project_root, 'amlo_pdfs')
        print(f"[AMLO PDF] 项目根目录: {project_root}")
        print(f"[AMLO PDF] PDF保存目录: {amlo_pdf_dir}")
        print(f"[AMLO PDF] 目录是否存在: {os.path.exists(amlo_pdf_dir)}")

        print(f"[AMLO PDF STEP 6] 创建amlo_pdfs目录...")
        os.makedirs(amlo_pdf_dir, exist_ok=True)
        print(f"[AMLO PDF] 目录创建完成: {os.path.exists(amlo_pdf_dir)}")

        project_pdf_path = os.path.join(amlo_pdf_dir, pdf_filename)
        print(f"[AMLO PDF] 项目PDF路径: {project_pdf_path}")

        # 使用新的PDF生成服务 (基于CSV映射)
        print(f"[AMLO PDF STEP 7] 开始生成PDF...")
        logger.info(f"生成AMLO PDF - 记录ID: {report_id}, 类型: {result.report_type}")
        logger.info(f"PDF将保存到: {pdf_path}")
        logger.info(f"PDF副本保存到: {project_pdf_path}")

        # 方式1: 直接从数据库记录生成 (推荐)
        from services.pdf import AMLOPDFService
        print(f"[AMLO PDF] 导入AMLOPDFService成功")
        service = AMLOPDFService()
        print(f"[AMLO PDF] AMLOPDFService实例化成功")

        # 构建预约数据
        print(f"[AMLO PDF STEP 8] 构建预约数据...")

        # 解析form_data
        import json
        form_data_dict = json.loads(result.form_data) if result.form_data else {}
        print(f"[AMLO PDF] form_data已解析，包含 {len(form_data_dict)} 个字段")

        # 从form_data中提取交易日期
        transaction_date = None
        if form_data_dict:
            day = form_data_dict.get('transaction_date_day')
            month = form_data_dict.get('transaction_date_month')
            year = form_data_dict.get('transaction_date_year')

            if day and month and year:
                try:
                    # 转换佛历年份为公历（如果需要）
                    if int(year) > 2500:
                        year = int(year) - 543
                    from datetime import datetime
                    transaction_date = datetime(int(year), int(month), int(day))
                    print(f"[AMLO PDF] 交易日期: {transaction_date.strftime('%Y-%m-%d')}")
                except Exception as date_error:
                    print(f"[AMLO PDF] WARNING: 日期解析失败: {date_error}")
                    transaction_date = None

        # 从form_data中提取币种代码
        currency_code = form_data_dict.get('deposit_currency_code') or form_data_dict.get('withdrawal_currency_code') or 'USD'
        print(f"[AMLO PDF] 币种代码: {currency_code}")

        reservation_data = {
            'id': result.id,
            'reservation_no': result.reservation_no,
            'report_type': result.report_type,
            'customer_id': result.customer_id,
            'customer_name': result.customer_name,
            'currency_code': currency_code,
            'direction': result.direction,
            'amount': float(result.amount) if result.amount else 0,
            'local_amount': float(result.local_amount) if result.local_amount else 0,
            'transaction_date': transaction_date,
            'form_data': result.form_data,
            'branch_id': result.branch_id
        }
        print(f"[AMLO PDF] 预约数据: ID={reservation_data['id']}, 类型={reservation_data['report_type']}")
        print(f"[AMLO PDF] ⚠️ DIRECTION字段值: '{result.direction}' (类型: {type(result.direction).__name__})")
        print(f"[AMLO PDF] 金额: 外币={reservation_data['amount']}, 本币={reservation_data['local_amount']}")

        # 生成PDF
        print(f"[AMLO PDF STEP 9] 调用PDF生成服务...")
        print(f"[AMLO PDF] 目标路径: {pdf_path}")
        result_path = service.generate_pdf_from_reservation(reservation_data, pdf_path)
        print(f"[AMLO PDF STEP 10] PDF生成完成")
        print(f"[AMLO PDF] 返回路径: {result_path}")
        print(f"[AMLO PDF] 文件存在: {os.path.exists(result_path)}")
        if os.path.exists(result_path):
            print(f"[AMLO PDF] 文件大小: {os.path.getsize(result_path)} bytes")

        logger.info(f"PDF生成成功: {result_path}")

        # 复制一份到项目目录（方便查看）
        print(f"[AMLO PDF STEP 11] 复制PDF到项目目录...")
        try:
            import shutil
            shutil.copy2(result_path, project_pdf_path)
            print(f"[AMLO PDF] 复制成功")
            print(f"[AMLO PDF] 副本存在: {os.path.exists(project_pdf_path)}")
            if os.path.exists(project_pdf_path):
                print(f"[AMLO PDF] 副本大小: {os.path.getsize(project_pdf_path)} bytes")

            logger.info(f"PDF副本已保存: {project_pdf_path}")
            print(f"\n{'='*80}")
            print(f"[OK] AMLO PDF生成成功！")
            print(f"{'='*80}")
            print(f"临时文件: {result_path}")
            print(f"项目副本: {project_pdf_path}")
            print(f"文件名: {pdf_filename}")
            print(f"{'='*80}\n")
        except Exception as copy_error:
            print(f"[AMLO PDF] WARNING: 复制失败: {copy_error}")
            logger.warning(f"复制PDF到项目目录失败: {copy_error}")

        # 返回PDF文件
        print(f"[AMLO PDF STEP 12] 准备返回PDF文件...")
        print(f"[AMLO PDF] 使用send_file发送: {result_path}")
        return send_file(
            result_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=pdf_filename
        )

    except Exception as e:
        error_msg = f"生成PDF失败: {str(e)}"
        error_type = type(e).__name__
        logger.error(f"Error in generate_report_pdf: {error_msg}")

        print(f"\n{'='*80}")
        print(f"[ERROR] AMLO PDF生成失败！")
        print(f"{'='*80}")
        print(f"错误类型: {error_type}")
        print(f"错误信息: {error_msg}")
        print(f"报告ID: {report_id}")
        print(f"详细堆栈:")
        traceback.print_exc()
        print(f"{'='*80}\n")

        return jsonify({
            'success': False,
            'message': error_msg,
            'error_type': error_type
        }), 500

    finally:
        print(f"[AMLO PDF] 关闭数据库会话")
        session.close()
        print(f"[AMLO PDF] 请求处理完成\n")


@app_amlo.route('/reports/batch-generate-pdf', methods=['POST'])
@token_required
@amlo_permission_required('amlo_report_view')
def batch_generate_pdf(current_user):
    """
    批量生成AMLO报告PDF文件（打包为ZIP）

    POST /api/amlo/reports/batch-generate-pdf
    Body: {
        "report_ids": [1, 2, 3]
    }

    响应:
    - 成功: 返回ZIP文件流 (application/zip)
    - 失败: {"success": false, "message": "错误信息"}
    """
    session = SessionLocal()

    try:
        data = request.get_json()
        report_ids = data.get('report_ids', [])

        if not report_ids:
            return jsonify({
                'success': False,
                'message': '请提供报告ID列表'
            }), 400

        # 查询所有报告
        report_sql = text("""
            SELECT
                r.id, r.reservation_no, r.report_type, r.customer_id, r.customer_name,
                r.customer_address, r.currency_id, r.direction, r.amount, r.amount_thb,
                r.transaction_date, r.form_data, r.created_at,
                b.branch_name, b.branch_code,
                u.username as reporter_name
            FROM Reserved_Transaction r
            LEFT JOIN branch b ON r.branch_id = b.id
            LEFT JOIN users u ON r.created_by = u.id
            WHERE r.id IN :report_ids AND r.branch_id = :branch_id
        """)

        results = session.execute(report_sql, {
            'report_ids': tuple(report_ids),
            'branch_id': g.current_user.get('branch_id')
        }).fetchall()

        if not results:
            return jsonify({
                'success': False,
                'message': '未找到报告记录'
            }), 404

        # 生成所有PDF
        import zipfile
        import io

        zip_buffer = io.BytesIO()
        filler = AMLOFormFiller()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for result in results:
                pdf_data, form_data = _prepare_amlo_pdf_payload(session, result)

                if result.report_type == 'AMLO-1-02':
                    pdf_data.update({
                        'asset_transaction_type': form_data.get('asset_transaction_type', 'transfer'),
                        'asset_type': form_data.get('asset_type', 'land'),
                        'asset_value_thb': float(result.amount_thb or 0)
                    })

                if result.report_type == 'AMLO-1-03':
                    pdf_data.update({
                        'has_filed_ctr_atr': form_data.get('has_filed_ctr_atr', False),
                        'previous_report_number': form_data.get('previous_report_number', ''),
                        'suspicion_reasons': form_data.get('suspicion_reasons', '')
                    })

                # 生成PDF到临时文件 - 使用新的表单填充器
                temp_dir = tempfile.gettempdir()
                pdf_filename = f"AMLO_{result.report_type.replace('-', '_')}_{result.reservation_no}.pdf"
                pdf_path = os.path.join(temp_dir, pdf_filename)

                # 转换数据格式并生成PDF
                adapted_data = adapt_route_data_to_pdf_data(pdf_data)
                filler.fill_form(result.report_type, adapted_data, pdf_path)

                # 添加到ZIP
                with open(pdf_path, 'rb') as pdf_file:
                    zip_file.writestr(pdf_filename, pdf_file.read())

                # 删除临时文件
                os.remove(pdf_path)

        # 返回ZIP文件
        zip_buffer.seek(0)
        zip_filename = f"AMLO_Reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )

    except Exception as e:
        logger.error(f"Error in batch_generate_pdf: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'批量生成PDF失败: {str(e)}'
        }), 500

    finally:
        session.close()


@app_amlo.route('/blank-form/<report_type>', methods=['GET'])
@token_required
def serve_blank_form(current_user, report_type):
    """
    提供空白AMLO表单PDF文件

    GET /api/amlo/blank-form/AMLO-1-01

    响应:
    - 成功: 返回PDF文件流 (application/pdf)
    - 失败: {"success": false, "message": "错误信息"}
    """
    try:
        # PDF文件映射
        pdf_map = {
            'AMLO-1-01': 'รายงาน ปปง 1-01 ซื้อขายเกิน 500,000 บาท ยกเว้นเงินบาทแลก.pdf',
            'AMLO-1-02': 'รายงาน ปปง 1-02 ซื้อขายเกิน 800,000 บาท ยกเว้นเงินบาทแลก.pdf',
            'AMLO-1-03': 'รายงาน ปปง 1-03  ซื้อขายระหว่างนิติบุคลล.pdf'
        }

        # 检查报告类型是否有效
        if report_type not in pdf_map:
            return jsonify({
                'success': False,
                'message': f'无效的报告类型: {report_type}'
            }), 400

        # 获取PDF文件路径 - 使用新的标准化文件名
        standardized_filename = f"{report_type}.pdf"

        # PDF文件存储在src/static/amlo_forms/目录
        current_file = os.path.abspath(__file__)
        src_dir = os.path.dirname(os.path.dirname(current_file))
        amlo_forms_dir = os.path.join(src_dir, 'static', 'amlo_forms')
        pdf_path = os.path.join(amlo_forms_dir, standardized_filename)

        logger.info(f"[AMLO] 尝试访问空白表单: {pdf_path}")
        logger.info(f"[AMLO] 文件是否存在: {os.path.exists(pdf_path)}")

        # 检查文件是否存在
        if not os.path.exists(pdf_path):
            return jsonify({
                'success': False,
                'message': f'PDF文件不存在: {standardized_filename}'
            }), 404

        # 返回PDF文件 - 使用标准化文件名避免Windows编码问题
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=False,  # 在浏览器中直接打开而不是下载
            download_name=standardized_filename  # 使用英文文件名避免GBK编码错误
        )

    except Exception as e:
        logger.error(f"Error in serve_blank_form: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取空白表单失败: {str(e)}'
        }), 500


# 错误处理
@app_amlo.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': '接口不存在'
    }), 404


@app_amlo.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'message': '服务器内部错误'
    }), 500
