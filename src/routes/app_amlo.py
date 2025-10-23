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
from services.pdf import AMLOPDFGenerator, AMLOFormFiller, adapt_route_data_to_pdf_data
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
                branch_id, operator_id, reporter_id, language,
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
    生成AMLO报告PDF文件

    GET /api/amlo/reports/<report_id>/generate-pdf

    响应:
    - 成功: 返回PDF文件流 (application/pdf)
    - 失败: {"success": false, "message": "错误信息"}
    """
    session = SessionLocal()

    try:
        # 查询报告记录
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
            WHERE r.id = :report_id AND r.branch_id = :branch_id
        """)

        result = session.execute(report_sql, {
            'report_id': report_id,
            'branch_id': g.current_user.get('branch_id')
        }).fetchone()

        if not result:
            return jsonify({
                'success': False,
                'message': '报告不存在'
            }), 404

        # 解析form_data
        form_data = json.loads(result.form_data) if result.form_data else {}

        # 构建PDF数据
        pdf_data = {
            'report_number': result.reservation_no,
            'is_amendment': form_data.get('is_amendment', False),
            'maker_type': form_data.get('maker_type', 'person'),
            'maker_name': result.customer_name,
            'maker_id': result.customer_id,
            'maker_address': result.customer_address or '',
            'joint_party_name': form_data.get('joint_party_name', ''),
            'transaction_date': result.transaction_date.strftime('%d/%m/%Y') if result.transaction_date else '',
            'transaction_type': 'exchange',
            'currency_code': form_data.get('currency_code', 'USD'),
            'amount_thb': float(result.amount_thb or 0),
            'remarks': form_data.get('remarks', ''),
            'reporter_name': result.reporter_name or '',
            'reporter_position': form_data.get('reporter_position', ''),
            'report_date': datetime.now().strftime('%d/%m/%Y')
        }

        # AMLO-1-02特定字段
        if result.report_type == 'AMLO-1-02':
            pdf_data.update({
                'asset_transaction_type': form_data.get('asset_transaction_type', 'transfer'),
                'asset_type': form_data.get('asset_type', 'land'),
                'asset_value_thb': float(result.amount_thb or 0)
            })

        # AMLO-1-03特定字段
        if result.report_type == 'AMLO-1-03':
            pdf_data.update({
                'has_filed_ctr_atr': form_data.get('has_filed_ctr_atr', False),
                'previous_report_number': form_data.get('previous_report_number', ''),
                'suspicion_reasons': form_data.get('suspicion_reasons', '')
            })

        # 生成PDF - 使用新的表单填充器
        filler = AMLOFormFiller()

        # 创建临时文件
        temp_dir = tempfile.gettempdir()
        pdf_filename = f"AMLO_{result.report_type.replace('-', '_')}_{result.reservation_no}.pdf"
        pdf_path = os.path.join(temp_dir, pdf_filename)

        # 转换数据格式并生成PDF文件
        adapted_data = adapt_route_data_to_pdf_data(pdf_data)
        filler.fill_form(result.report_type, adapted_data, pdf_path)

        # 返回PDF文件
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=pdf_filename
        )

    except Exception as e:
        logger.error(f"Error in generate_report_pdf: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'生成PDF失败: {str(e)}'
        }), 500

    finally:
        session.close()


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
                # 解析form_data并构建PDF数据（与单个生成相同）
                form_data = json.loads(result.form_data) if result.form_data else {}

                pdf_data = {
                    'report_number': result.reservation_no,
                    'is_amendment': form_data.get('is_amendment', False),
                    'maker_type': form_data.get('maker_type', 'person'),
                    'maker_name': result.customer_name,
                    'maker_id': result.customer_id,
                    'maker_address': result.customer_address or '',
                    'transaction_date': result.transaction_date.strftime('%d/%m/%Y') if result.transaction_date else '',
                    'amount_thb': float(result.amount_thb or 0),
                    'reporter_name': result.reporter_name or '',
                    'report_date': datetime.now().strftime('%d/%m/%Y')
                }

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
