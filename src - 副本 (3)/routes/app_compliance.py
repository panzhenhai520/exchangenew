# -*- coding: utf-8 -*-
"""
合规配置API路由
提供字段定义、触发规则、资金来源等配置管理接口
版本: v1.0
创建日期: 2025-10-02
"""

from flask import Blueprint, request, jsonify, g
from functools import wraps
from services.db_service import SessionLocal
from services.auth_service import token_required, permission_required
from sqlalchemy import text
import traceback
import json

# 创建Blueprint
app_compliance = Blueprint('app_compliance', __name__)


# 权限装饰器
def compliance_permission_required(permission):
    """合规配置权限检查装饰器"""
    return permission_required(permission)


@app_compliance.route('/api/compliance/fields', methods=['GET'])
@token_required
@compliance_permission_required('compliance_config')
def get_report_fields(current_user):
    """
    获取报告字段定义列表

    GET /api/compliance/fields?report_type=AMLO-1-01&is_active=true

    查询参数:
    - report_type: 报告类型（可选）
    - is_active: 是否激活（可选）

    响应:
    {
        "success": true,
        "data": [...]
    }
    """
    session = SessionLocal()

    try:
        report_type = request.args.get('report_type')
        is_active = request.args.get('is_active')

        # 构建查询条件
        where_clauses = []
        params = {}

        if report_type:
            where_clauses.append('report_type = :report_type')
            params['report_type'] = report_type

        if is_active is not None:
            where_clauses.append('is_active = :is_active')
            params['is_active'] = (is_active.lower() == 'true')

        where_sql = ' AND '.join(where_clauses) if where_clauses else '1=1'

        sql = text(f"""
            SELECT *
            FROM report_fields
            WHERE {where_sql}
            ORDER BY report_type, fill_order
        """)

        result = session.execute(sql, params)
        fields = [dict(row._mapping) for row in result]

        # 解析validation_rule JSON
        for field in fields:
            if field.get('validation_rule'):
                try:
                    field['validation_rule'] = json.loads(field['validation_rule'])
                except:
                    field['validation_rule'] = {}

        return jsonify({
            'success': True,
            'data': fields
        })

    except Exception as e:
        print(f"Error in get_report_fields: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取字段定义失败: {str(e)}'
        }), 500

    finally:
        session.close()


@app_compliance.route('/api/compliance/fields', methods=['POST'])
@token_required
@compliance_permission_required('compliance_config')
def create_report_field(current_user):
    """
    创建报告字段定义

    POST /api/compliance/fields

    请求体:
    {
        "field_name": "test_field",
        "field_type": "VARCHAR",
        "field_length": 100,
        "field_cn_name": "测试字段",
        "field_en_name": "Test Field",
        "field_th_name": "ฟิลด์ทดสอบ",
        "report_type": "AMLO-1-01",
        "field_group": "基本信息",
        "fill_order": 100,
        "is_required": true,
        "is_active": true,
        "validation_rule": {...}
    }

    响应:
    {
        "success": true,
        "field_id": 28
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

        # 必填字段检查
        required_fields = [
            'field_name', 'field_type', 'field_cn_name',
            'field_en_name', 'field_th_name', 'report_type'
        ]

        missing_fields = [f for f in required_fields if f not in request_data]
        if missing_fields:
            return jsonify({
                'success': False,
                'message': f'缺少必填字段: {", ".join(missing_fields)}'
            }), 400

        # 插入记录
        sql = text("""
            INSERT INTO report_fields (
                field_name, field_type, field_length, field_precision,
                field_cn_name, field_en_name, field_th_name,
                report_type, field_group, fill_order,
                is_required, fillpos, placeholder, help_text_cn, help_text_en, help_text_th,
                validation_rule, is_active, created_at
            ) VALUES (
                :field_name, :field_type, :field_length, :field_precision,
                :field_cn_name, :field_en_name, :field_th_name,
                :report_type, :field_group, :fill_order,
                :is_required, :fillpos, :placeholder, :help_text_cn, :help_text_en, :help_text_th,
                :validation_rule, :is_active, NOW()
            )
        """)

        validation_rule = request_data.get('validation_rule', {})
        if isinstance(validation_rule, dict):
            validation_rule = json.dumps(validation_rule, ensure_ascii=False)

        params = {
            'field_name': request_data['field_name'],
            'field_type': request_data['field_type'],
            'field_length': request_data.get('field_length'),
            'field_precision': request_data.get('field_precision'),
            'field_cn_name': request_data['field_cn_name'],
            'field_en_name': request_data['field_en_name'],
            'field_th_name': request_data['field_th_name'],
            'report_type': request_data['report_type'],
            'field_group': request_data.get('field_group'),
            'fill_order': request_data.get('fill_order', 999),
            'is_required': request_data.get('is_required', False),
            'fillpos': request_data.get('fillpos'),
            'placeholder': request_data.get('placeholder'),
            'help_text_cn': request_data.get('help_text_cn'),
            'help_text_en': request_data.get('help_text_en'),
            'help_text_th': request_data.get('help_text_th'),
            'validation_rule': validation_rule,
            'is_active': request_data.get('is_active', True)
        }

        result = session.execute(sql, params)
        session.commit()

        return jsonify({
            'success': True,
            'field_id': result.lastrowid
        })

    except Exception as e:
        session.rollback()
        print(f"Error in create_report_field: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'创建字段失败: {str(e)}'
        }), 500

    finally:
        session.close()


@app_compliance.route('/api/compliance/fields/<int:field_id>', methods=['PUT'])
@token_required
@compliance_permission_required('compliance_config')
def update_report_field(current_user, field_id):
    """
    更新报告字段定义

    PUT /api/compliance/fields/28

    请求体:
    {
        "field_cn_name": "新的中文名称",
        "is_active": false,
        ...
    }

    响应:
    {
        "success": true,
        "message": "更新成功"
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

        # 构建更新字段
        update_fields = []
        params = {'field_id': field_id}

        allowed_fields = [
            'field_type', 'field_length', 'field_precision',
            'field_cn_name', 'field_en_name', 'field_th_name',
            'field_group', 'fill_order', 'is_required', 'fillpos', 'placeholder',
            'help_text_cn', 'help_text_en', 'help_text_th', 'is_active'
        ]

        for field in allowed_fields:
            if field in request_data:
                update_fields.append(f'{field} = :{field}')
                params[field] = request_data[field]

        if 'validation_rule' in request_data:
            validation_rule = request_data['validation_rule']
            if isinstance(validation_rule, dict):
                validation_rule = json.dumps(validation_rule, ensure_ascii=False)
            update_fields.append('validation_rule = :validation_rule')
            params['validation_rule'] = validation_rule

        if not update_fields:
            return jsonify({
                'success': False,
                'message': '没有要更新的字段'
            }), 400

        update_fields.append('updated_at = NOW()')

        sql = text(f"""
            UPDATE report_fields
            SET {', '.join(update_fields)}
            WHERE id = :field_id
        """)

        session.execute(sql, params)
        session.commit()

        return jsonify({
            'success': True,
            'message': '更新成功'
        })

    except Exception as e:
        session.rollback()
        print(f"Error in update_report_field: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'更新字段失败: {str(e)}'
        }), 500

    finally:
        session.close()


@app_compliance.route('/api/compliance/trigger-rules', methods=['GET'])
@token_required
@compliance_permission_required('compliance_config')
def get_trigger_rules(current_user):
    """
    获取触发规则列表

    GET /api/compliance/trigger-rules?report_type=AMLO-1-01&is_active=true

    查询参数:
    - report_type: 报告类型（可选）
    - is_active: 是否激活（可选）

    响应:
    {
        "success": true,
        "data": [...]
    }
    """
    session = SessionLocal()

    try:
        report_type = request.args.get('report_type')
        is_active = request.args.get('is_active')
        branch_id = current_user.get('branch_id')

        # 构建查询条件
        where_clauses = ['(branch_id IS NULL OR branch_id = :branch_id)']
        params = {'branch_id': branch_id}

        if report_type:
            where_clauses.append('report_type = :report_type')
            params['report_type'] = report_type

        if is_active is not None:
            where_clauses.append('is_active = :is_active')
            params['is_active'] = (is_active.lower() == 'true')

        where_sql = ' AND '.join(where_clauses)

        sql = text(f"""
            SELECT *
            FROM trigger_rules
            WHERE {where_sql}
            ORDER BY priority DESC, created_at DESC
        """)

        result = session.execute(sql, params)
        rules = [dict(row._mapping) for row in result]

        # 解析rule_expression JSON
        for rule in rules:
            if rule.get('rule_expression'):
                try:
                    rule['rule_expression'] = json.loads(rule['rule_expression'])
                except:
                    rule['rule_expression'] = {}

        return jsonify({
            'success': True,
            'data': rules
        })

    except Exception as e:
        print(f"Error in get_trigger_rules: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取触发规则失败: {str(e)}'
        }), 500

    finally:
        session.close()


@app_compliance.route('/api/compliance/trigger-rules', methods=['POST'])
@token_required
@compliance_permission_required('compliance_config')
def create_trigger_rule(current_user):
    """
    创建触发规则

    POST /api/compliance/trigger-rules

    请求体:
    {
        "rule_name": "测试规则",
        "rule_name_en": "Test Rule",
        "rule_name_th": "กฎทดสอบ",
        "report_type": "AMLO-1-01",
        "rule_expression": {
            "logic": "AND",
            "conditions": [...]
        },
        "priority": 10,
        "allow_continue": true,
        "message_cn": "触发提示",
        "message_en": "Trigger message",
        "message_th": "ข้อความทริกเกอร์",
        "is_active": true
    }

    响应:
    {
        "success": true,
        "rule_id": 8
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

        # 必填字段检查
        required_fields = [
            'rule_name', 'report_type', 'rule_expression'
        ]

        missing_fields = [f for f in required_fields if f not in request_data]
        if missing_fields:
            return jsonify({
                'success': False,
                'message': f'缺少必填字段: {", ".join(missing_fields)}'
            }), 400

        # 插入记录
        sql = text("""
            INSERT INTO trigger_rules (
                rule_name, rule_name_en, rule_name_th,
                report_type, rule_expression, priority,
                allow_continue, message_cn, message_en, message_th,
                branch_id, is_active, created_at
            ) VALUES (
                :rule_name, :rule_name_en, :rule_name_th,
                :report_type, :rule_expression, :priority,
                :allow_continue, :message_cn, :message_en, :message_th,
                :branch_id, :is_active, NOW()
            )
        """)

        rule_expression = request_data['rule_expression']
        if isinstance(rule_expression, dict):
            rule_expression = json.dumps(rule_expression, ensure_ascii=False)

        # 如果指定了branch_id，使用指定的；否则使用NULL表示全局规则
        branch_id = request_data.get('branch_id')

        params = {
            'rule_name': request_data['rule_name'],
            'rule_name_en': request_data.get('rule_name_en'),
            'rule_name_th': request_data.get('rule_name_th'),
            'report_type': request_data['report_type'],
            'rule_expression': rule_expression,
            'priority': request_data.get('priority', 50),
            'allow_continue': request_data.get('allow_continue', True),
            'message_cn': request_data.get('message_cn'),
            'message_en': request_data.get('message_en'),
            'message_th': request_data.get('message_th'),
            'branch_id': branch_id,
            'is_active': request_data.get('is_active', True)
        }

        result = session.execute(sql, params)
        session.commit()

        return jsonify({
            'success': True,
            'rule_id': result.lastrowid
        })

    except Exception as e:
        session.rollback()
        print(f"Error in create_trigger_rule: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'创建触发规则失败: {str(e)}'
        }), 500

    finally:
        session.close()


@app_compliance.route('/api/compliance/trigger-rules/<int:rule_id>', methods=['PUT'])
@token_required
@compliance_permission_required('compliance_config')
def update_trigger_rule(current_user, rule_id):
    """
    更新触发规则

    PUT /api/compliance/trigger-rules/8

    请求体:
    {
        "priority": 20,
        "is_active": false,
        ...
    }

    响应:
    {
        "success": true,
        "message": "更新成功"
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

        # 构建更新字段
        update_fields = []
        params = {'rule_id': rule_id}

        allowed_fields = [
            'rule_name', 'rule_name_en', 'rule_name_th',
            'priority', 'allow_continue',
            'message_cn', 'message_en', 'message_th',
            'is_active'
        ]

        for field in allowed_fields:
            if field in request_data:
                update_fields.append(f'{field} = :{field}')
                params[field] = request_data[field]

        if 'rule_expression' in request_data:
            rule_expression = request_data['rule_expression']
            if isinstance(rule_expression, dict):
                rule_expression = json.dumps(rule_expression, ensure_ascii=False)
            update_fields.append('rule_expression = :rule_expression')
            params['rule_expression'] = rule_expression

        if not update_fields:
            return jsonify({
                'success': False,
                'message': '没有要更新的字段'
            }), 400

        update_fields.append('updated_at = NOW()')

        sql = text(f"""
            UPDATE trigger_rules
            SET {', '.join(update_fields)}
            WHERE id = :rule_id
        """)

        session.execute(sql, params)
        session.commit()

        return jsonify({
            'success': True,
            'message': '更新成功'
        })

    except Exception as e:
        session.rollback()
        print(f"Error in update_trigger_rule: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'更新触发规则失败: {str(e)}'
        }), 500

    finally:
        session.close()


@app_compliance.route('/api/compliance/funding-sources', methods=['GET'])
@token_required
def get_funding_sources(current_user):
    """
    获取资金来源列表

    GET /api/compliance/funding-sources?is_active=true

    查询参数:
    - is_active: 是否激活（可选）

    响应:
    {
        "success": true,
        "data": [...]
    }
    """
    session = SessionLocal()

    try:
        is_active = request.args.get('is_active')

        where_sql = '1=1'
        params = {}

        if is_active is not None:
            where_sql = 'is_active = :is_active'
            params['is_active'] = (is_active.lower() == 'true')

        sql = text(f"""
            SELECT *
            FROM funding_sources
            WHERE {where_sql}
            ORDER BY sort_order, id
        """)

        result = session.execute(sql, params)
        sources = [dict(row._mapping) for row in result]

        return jsonify({
            'success': True,
            'data': sources
        })

    except Exception as e:
        print(f"Error in get_funding_sources: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取资金来源失败: {str(e)}'
        }), 500

    finally:
        session.close()


# 错误处理
@app_compliance.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': '接口不存在'
    }), 404


@app_compliance.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'message': '服务器内部错误'
    }), 500
