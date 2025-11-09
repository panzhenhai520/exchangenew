# -*- coding: utf-8 -*-
"""
RepForm核心API路由
提供动态报告生成的核心接口
版本: v1.0
创建日期: 2025-10-02
"""

from flask import Blueprint, request, jsonify, g
from functools import wraps
from services.db_service import SessionLocal
from services.repform import (
    FieldManager,
    RuleEngine,
    FormBuilder,
    FormValidator,
    ReportDataService
)
from services.auth_service import token_required, permission_required
import traceback
import json

# 创建Blueprint
app_repform = Blueprint('app_repform', __name__, url_prefix='/api')


# 权限装饰器
def repform_permission_required(permission):
    """RepForm权限检查装饰器"""
    return permission_required(permission)


@app_repform.route('/repform/report-types', methods=['GET'])
@token_required
def get_report_types(current_user):
    """
    获取所有报告类型列表

    GET /api/repform/report-types

    响应:
    {
        "success": true,
        "data": [
            {
                "report_type": "AMLO-1-01",
                "report_name": "现金交易报告",
                "field_count": 11,
                "required_count": 11
            },
            ...
        ]
    }
    """
    session = SessionLocal()

    try:
        report_types = FieldManager.get_all_report_types(session)

        return jsonify({
            'success': True,
            'data': report_types
        })

    except Exception as e:
        print(f"Error in get_report_types: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取报告类型失败: {str(e)}'
        }), 500

    finally:
        session.close()


@app_repform.route('/repform/form-definition/<report_type>', methods=['GET'])
@token_required
def get_form_definition(current_user, report_type):
    """
    获取表单定义

    GET /api/repform/form-definition/AMLO-1-01?language=zh

    查询参数:
    - language: 语言 (zh/en/th)，默认zh

    响应:
    {
        "success": true,
        "data": {
            "report_type": "AMLO-1-01",
            "report_name": "现金交易报告",
            "field_groups": [...],
            "total_fields": 11
        }
    }
    """
    session = SessionLocal()

    try:
        language = request.args.get('language', 'zh')

        # 验证report_type
        valid_types = [
            'AMLO-1-01', 'AMLO-1-02', 'AMLO-1-03',
            'BOT_BuyFX', 'BOT_SellFX', 'BOT_Provider', 'BOT_FCD'
        ]

        if report_type not in valid_types:
            return jsonify({
                'success': False,
                'message': f'无效的报告类型: {report_type}'
            }), 400

        form_definition = FieldManager.get_form_definition(
            session,
            report_type,
            language
        )

        return jsonify({
            'success': True,
            'data': form_definition
        })

    except Exception as e:
        print(f"Error in get_form_definition: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取表单定义失败: {str(e)}'
        }), 500

    finally:
        session.close()


@app_repform.route('/repform/form-schema/<report_type>', methods=['GET'])
@token_required
def get_form_schema(current_user, report_type):
    """
    获取表单Schema（供前端渲染）

    GET /api/repform/form-schema/AMLO-1-01?language=zh

    查询参数:
    - language: 语言 (zh/en/th)，默认zh

    响应:
    {
        "success": true,
        "data": {
            "report_type": "AMLO-1-01",
            "report_name": "现金交易报告",
            "form_items": [...],
            "validation_rules": {...}
        }
    }
    """
    session = SessionLocal()

    try:
        language = request.args.get('language', 'zh')

        form_schema = FormBuilder.build_form_schema(
            session,
            report_type,
            language
        )

        return jsonify({
            'success': True,
            'data': form_schema
        })

    except Exception as e:
        print(f"Error in get_form_schema: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取表单Schema失败: {str(e)}'
        }), 500

    finally:
        session.close()


@app_repform.route('/repform/check-trigger', methods=['POST'])
@token_required
def check_trigger(current_user):
    """
    检查触发条件

    POST /api/repform/check-trigger

    请求体:
    {
        "report_type": "AMLO-1-01",
        "data": {
            "total_amount": 6000000,
            "currency_code": "USD",
            "customer_id": "1234567890123"
        },
        "branch_id": 1
    }

    响应:
    {
        "success": true,
        "triggers": {
            "amlo": {
                "triggered": true,
                "report_type": "AMLO-1-01",
                "message_cn": "该交易金额达到500万泰铢...",
                "allow_continue": false
            },
            "bot": {
                "triggered": false
            }
        },
        "customer_stats": {
            "cumulative_amount_1month": 8500000,
            "transaction_count_1month": 15
        }
    }
    """
    session = SessionLocal()

    try:
        request_data = request.get_json()
        print(f"\n========== [check_trigger] 收到AMLO触发检查请求 ==========", flush=True)
        print(f"[check_trigger] 请求数据: {request_data}", flush=True)

        if not request_data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400

        report_type = request_data.get('report_type')
        data = request_data.get('data', {})
        branch_id = request_data.get('branch_id') or g.current_user.get('branch_id')

        print(f"[check_trigger] report_type={report_type}, branch_id={branch_id}", flush=True)
        print(f"[check_trigger] data={data}", flush=True)

        if not report_type:
            return jsonify({
                'success': False,
                'message': '缺少report_type参数'
            }), 400

        # 检查触发条件
        try:
            trigger_result = RuleEngine.check_triggers(
                db_session=session,
                report_type=report_type,
                data=data,
                branch_id=branch_id
            )
            print(f"[check_trigger] 触发检查结果: {trigger_result}", flush=True)
        except Exception as trigger_error:
            print(f"[check_trigger] RuleEngine.check_triggers失败: {str(trigger_error)}", flush=True)
            traceback.print_exc()
            # 如果触发检查失败，返回未触发状态而不是500错误
            trigger_result = {
                'triggered': False,
                'trigger_rules': [],
                'highest_priority_rule': None,
                'allow_continue': True
            }

        # 获取客户统计（如果提供了customer_id）
        customer_stats = {}
        customer_id = data.get('customer_id')
        if customer_id:
            customer_stats = RuleEngine.get_customer_stats(
                session,
                customer_id,
                days=30
            )

        # 构建响应
        triggers = {}

        # AMLO触发
        if report_type.startswith('AMLO'):
            triggers['amlo'] = {
                'triggered': trigger_result['triggered'],
                'report_type': report_type if trigger_result['triggered'] else None,
                'message_cn': trigger_result.get('message_cn', ''),
                'message_en': trigger_result.get('message_en', ''),
                'message_th': trigger_result.get('message_th', ''),
                'allow_continue': trigger_result.get('allow_continue', False)
            }

        # BOT触发
        elif report_type.startswith('BOT'):
            triggers['bot'] = {
                'triggered': trigger_result['triggered'],
                'report_types': [report_type] if trigger_result['triggered'] else []
            }

        return jsonify({
            'success': True,
            'triggers': triggers,
            'customer_stats': customer_stats
        })

    except Exception as e:
        print(f"Error in check_trigger: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'检查触发条件失败: {str(e)}'
        }), 500

    finally:
        session.close()


@app_repform.route('/repform/validate-form', methods=['POST'])
@token_required
def validate_form(current_user):
    """
    验证表单数据

    POST /api/repform/validate-form

    请求体:
    {
        "report_type": "AMLO-1-01",
        "form_data": {
            "customer_name": "张三",
            "customer_address": "北京市...",
            ...
        }
    }

    响应:
    {
        "success": true,
        "valid": true,
        "errors": []
    }
    """
    session = SessionLocal()

    try:
        request_data = request.get_json()

        report_type = request_data.get('report_type')
        form_data = request_data.get('form_data', {})

        if not report_type or not form_data:
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            }), 400

        # 验证表单数据
        is_valid, errors = FormValidator.validate_form_data(
            session,
            report_type,
            form_data
        )

        return jsonify({
            'success': True,
            'valid': is_valid,
            'errors': errors
        })

    except Exception as e:
        print(f"Error in validate_form: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'验证表单失败: {str(e)}'
        }), 500

    finally:
        session.close()


@app_repform.route('/repform/save-reservation', methods=['POST'])
@token_required
def save_reservation(current_user):
    """
    保存预约兑换记录

    POST /api/repform/save-reservation

    请求体:
    {
        "customer_id": "1234567890123",
        "customer_name": "张三",
        "customer_country_code": "CN",
        "currency_id": 2,
        "direction": "buy",
        "amount": 10000,
        "local_amount": 6000000,
        "rate": 32.5,
        "trigger_type": "CTR",
        "report_type": "AMLO-1-01",
        "form_data": {...},
        "exchange_type": "large_amount",
        "funding_source": "salary"
    }

    响应:
    {
        "success": true,
        "reservation_id": 1,
        "reservation_no": "123-456-68-0731001",
        "message": "预约兑换记录已创建"
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

        # 补充当前用户信息
        current_user = g.current_user
        request_data['branch_id'] = request_data.get('branch_id') or current_user['branch_id']
        request_data['operator_id'] = request_data.get('operator_id') or current_user['id']

        # 验证必填字段
        required_fields = [
            'customer_id', 'customer_name', 'currency_id', 'direction',
            'amount', 'local_amount', 'rate', 'trigger_type', 'report_type', 'form_data'
        ]

        missing_fields = [f for f in required_fields if f not in request_data]
        if missing_fields:
            return jsonify({
                'success': False,
                'message': f'缺少必填字段: {", ".join(missing_fields)}'
            }), 400

        # 先验证表单数据
        print(f"[DEBUG] 开始验证表单数据:")
        print(f"[DEBUG] report_type: {request_data['report_type']}")
        print(f"[DEBUG] form_data keys: {list(request_data['form_data'].keys())}")
        print(f"[DEBUG] form_data: {json.dumps(request_data['form_data'], indent=2, ensure_ascii=False)}")

        is_valid, errors = FormValidator.validate_form_data(
            session,
            request_data['report_type'],
            request_data['form_data']
        )

        if not is_valid:
            print(f"[DEBUG] 表单验证失败，错误列表:")
            for error in errors:
                print(f"[DEBUG]   - {error}")

            return jsonify({
                'success': False,
                'message': '表单验证失败',
                'errors': errors
            }), 400

        print(f"[DEBUG] 表单验证通过")

        # 保存预约记录
        reservation_id = ReportDataService.save_reservation(
            session,
            request_data
        )

        # 获取预约流水号
        reservation = ReportDataService.get_reservation_by_id(session, reservation_id)

        # 🆕 立即创建AMLO报告记录和生成PDF
        report_id = None
        report_no = None
        pdf_path = None

        try:
            print(f"[DEBUG] 开始为预约 {reservation_id} 创建AMLO报告和PDF")

            # 创建AMLO报告记录
            from services.amlo.report_creation_service import ReportCreationService
            report_result = ReportCreationService.create_report_for_reservation(
                session, reservation_id
            )

            if report_result['success']:
                report_id = report_result['report_id']
                report_no = report_result['report_no']
                pdf_path = report_result.get('pdf_path')
                print(f"[DEBUG] 成功创建报告: ID={report_id}, NO={report_no}, PDF={pdf_path}")
            else:
                print(f"[DEBUG] 创建报告失败: {report_result.get('error')}")
                # 不中断流程，预约已创建成功

        except Exception as e:
            print(f"[ERROR] 创建报告和PDF时发生异常: {str(e)}")
            import traceback
            traceback.print_exc()
            # 不中断流程，预约已创建成功

        return jsonify({
            'success': True,
            'reservation_id': reservation_id,
            'reservation_no': reservation.get('reservation_no'),
            'report_id': report_id,
            'report_no': report_no,
            'pdf_path': pdf_path,
            'message': '预约兑换记录已创建，报告已生成' if report_id else '预约兑换记录已创建，等待审核'
        })

    except Exception as e:
        print(f"Error in save_reservation: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'保存预约记录失败: {str(e)}'
        }), 500

    finally:
        session.close()


@app_repform.route('/repform/reservation/<int:reservation_id>', methods=['GET'])
@token_required
def get_reservation(current_user, reservation_id):
    """
    获取预约记录详情

    GET /api/repform/reservation/1

    响应:
    {
        "success": true,
        "data": {
            "id": 1,
            "reservation_no": "123-456-68-0731001",
            "customer_name": "张三",
            "status": "pending",
            ...
        }
    }
    """
    session = SessionLocal()

    try:
        reservation = ReportDataService.get_reservation_by_id(session, reservation_id)

        if not reservation:
            return jsonify({
                'success': False,
                'message': f'预约记录不存在: {reservation_id}'
            }), 404

        return jsonify({
            'success': True,
            'data': reservation
        })

    except Exception as e:
        print(f"Error in get_reservation: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取预约记录失败: {str(e)}'
        }), 500

    finally:
        session.close()


@app_repform.route('/repform/customer-history/<customer_id>', methods=['GET'])
@token_required
def get_customer_history(current_user, customer_id):
    """
    获取客户历史交易统计

    GET /api/repform/customer-history/1234567890123?days=30

    查询参数:
    - days: 统计天数，默认30

    响应:
    {
        "success": true,
        "data": {
            "customer_id": "1234567890123",
            "cumulative_amount_1month": 8500000,
            "transaction_count_1month": 15,
            "last_transaction_date": "2025-10-01"
        }
    }
    """
    session = SessionLocal()

    try:
        days = int(request.args.get('days', 30))

        customer_stats = RuleEngine.get_customer_stats(
            session,
            customer_id,
            days
        )

        customer_stats['customer_id'] = customer_id

        return jsonify({
            'success': True,
            'data': customer_stats
        })

    except Exception as e:
        print(f"Error in get_customer_history: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取客户历史失败: {str(e)}'
        }), 500

    finally:
        session.close()


# 错误处理
@app_repform.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': '接口不存在'
    }), 404


@app_repform.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'message': '服务器内部错误'
    }), 500
