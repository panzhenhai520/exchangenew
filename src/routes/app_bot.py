# -*- coding: utf-8 -*-
"""
BOT报告API路由
提供BOT报表查询和导出的核心接口
版本: v1.0
创建日期: 2025-10-02
"""

from flask import Blueprint, request, jsonify, g, send_file
from functools import wraps
from services.db_service import SessionLocal
from services.auth_service import token_required, permission_required
from sqlalchemy import text
import traceback
import json
from datetime import datetime, timedelta
import io
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
import logging

# Get logger instance - DO NOT call basicConfig() here as it will override
# the logging configuration already set in main.py
logger = logging.getLogger(__name__)

# 创建Blueprint - 统一使用url_prefix方式
app_bot = Blueprint('app_bot', __name__, url_prefix='/api/bot')


# 权限装饰器
def bot_permission_required(permission):
    """BOT权限检查装饰器"""
    return permission_required(permission)


@app_bot.route('/check-trigger', methods=['POST'])
@token_required
def check_bot_trigger(current_user):
    """
    检查BOT触发条件

    POST /api/bot/check-trigger

    请求体:
    {
        "use_fcd": true/false,           # 是否使用FCD账户
        "direction": "buy"/"sell",        # 交易方向
        "local_amount": 2000000,          # 本币金额
        "verification_amount": 50000,     # 换算后的验证金额(按配置币种)
        "currency_code": "USD",           # 交易币种
        "branch_id": 1                    # 网点ID(可选)
    }

    响应:
    {
        "success": true,
        "bot_flag": 1,                    # 0或1
        "fcd_flag": 1,                    # 0或1
        "bot_report_type": "BOT_BuyFX",   # BOT_BuyFX/BOT_SellFX/null
        "fcd_report_type": "BOT_FCD",     # BOT_FCD/null
        "message": "需要生成BOT报告"
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

        use_fcd = request_data.get('use_fcd', False)
        direction = request_data.get('direction')
        local_amount = float(request_data.get('local_amount', 0))
        verification_amount = float(request_data.get('verification_amount', 0))
        currency_code = request_data.get('currency_code')
        branch_id = request_data.get('branch_id') or g.current_user.get('branch_id')

        # 初始化标记
        bot_flag = 0
        fcd_flag = 0
        bot_report_type = None
        fcd_report_type = None
        messages = []

        # 查询BOT触发规则
        # 1. 检查买入/卖出外币触发条件
        if direction == 'buy':
            check_report_type = 'BOT_BuyFX'
        elif direction == 'sell':
            check_report_type = 'BOT_SellFX'
        else:
            return jsonify({
                'success': False,
                'message': '交易方向参数错误'
            }), 400

        # 查询对应的触发规则
        rule_sql = text("""
            SELECT
                id, rule_name, report_type, rule_expression,
                priority, allow_continue,
                warning_message_cn, warning_message_en, warning_message_th
            FROM trigger_rules
            WHERE report_type = :report_type
                AND is_active = TRUE
                AND (branch_id IS NULL OR branch_id = :branch_id)
            ORDER BY priority DESC, id ASC
            LIMIT 1
        """)

        rule_result = session.execute(
            rule_sql,
            {'report_type': check_report_type, 'branch_id': branch_id}
        )
        rule_row = rule_result.first()

        if rule_row:
            # 解析规则表达式
            try:
                rule_expression = json.loads(rule_row[3])  # rule_expression

                # 构建数据进行规则评估
                eval_data = {
                    'direction': direction,
                    'local_amount': local_amount,
                    'verification_amount': verification_amount,
                    'currency_code': currency_code,
                    'use_fcd': use_fcd
                }

                # 导入RuleEngine进行评估
                from services.repform.rule_engine import RuleEngine

                if RuleEngine.evaluate_rule(rule_expression, eval_data):
                    bot_flag = 1
                    bot_report_type = check_report_type
                    messages.append(rule_row[6] or f'需要生成{check_report_type}报告')  # warning_message_cn

            except Exception as e:
                logger.error(f"Error evaluating BOT rule: {str(e)}")

        # 2. 检查FCD账户触发条件
        if use_fcd:
            fcd_rule_sql = text("""
                SELECT
                    id, rule_name, report_type, rule_expression,
                    priority, allow_continue,
                    warning_message_cn, warning_message_en, warning_message_th
                FROM trigger_rules
                WHERE report_type = 'BOT_FCD'
                    AND is_active = TRUE
                    AND (branch_id IS NULL OR branch_id = :branch_id)
                ORDER BY priority DESC, id ASC
                LIMIT 1
            """)

            fcd_rule_result = session.execute(
                fcd_rule_sql,
                {'branch_id': branch_id}
            )
            fcd_rule_row = fcd_rule_result.first()

            if fcd_rule_row:
                try:
                    fcd_rule_expression = json.loads(fcd_rule_row[3])

                    eval_data = {
                        'direction': direction,
                        'local_amount': local_amount,
                        'verification_amount': verification_amount,
                        'currency_code': currency_code,
                        'use_fcd': True
                    }

                    from services.repform.rule_engine import RuleEngine

                    if RuleEngine.evaluate_rule(fcd_rule_expression, eval_data):
                        fcd_flag = 1
                        fcd_report_type = 'BOT_FCD'
                        messages.append(fcd_rule_row[6] or '需要生成FCD报告')

                except Exception as e:
                    logger.error(f"Error evaluating FCD rule: {str(e)}")

        # 返回结果
        return jsonify({
            'success': True,
            'bot_flag': bot_flag,
            'fcd_flag': fcd_flag,
            'bot_report_type': bot_report_type,
            'fcd_report_type': fcd_report_type,
            'message': '; '.join(messages) if messages else '无需生成BOT报告',
            'triggered': (bot_flag == 1 or fcd_flag == 1)
        })

    except Exception as e:
        logger.error(f"Error in check_bot_trigger: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'检查BOT触发条件失败: {str(e)}'
        }), 500

    finally:
        session.close()


@app_bot.route('/t1-buy-fx', methods=['GET'])
@token_required
@bot_permission_required('bot_report_view')
def get_t1_buy_fx(current_user):
    """
    查询T+1买入外币报表数据（昨天到今天）

    GET /api/bot/t1-buy-fx

    响应:
    {
        "success": true,
        "data": {
            "date_range": "2025-10-10 to 2025-10-11",
            "items": [...],
            "total_count": 10,
            "total_amount_thb": 5000000,
            "unreported_count": 5,
            "overdue_count": 2
        }
    }
    """
    session = SessionLocal()

    try:
        # 获取当前用户的branch_id
        branch_id = g.current_user.get('branch_id')
        
        # T+1时间范围：昨天到今天
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        # 查询BOT_BuyFX记录（昨天到今天）
        sql = text("""
            SELECT
                b.id,
                b.transaction_no,
                b.transaction_date,
                b.customer_name,
                b.customer_id_number,
                b.customer_country_code,
                b.buy_currency_code as currency_code,
                b.buy_amount as foreign_amount,
                b.local_amount,
                b.exchange_rate,
                b.usd_equivalent,
                b.is_reported,
                b.report_time,
                b.created_at,
                DATEDIFF(CURDATE(), b.transaction_date) as days_diff
            FROM BOT_BuyFX b
            WHERE b.branch_id = :branch_id
                AND b.transaction_date >= :start_date
                AND b.transaction_date <= :end_date
            ORDER BY b.transaction_date ASC, b.transaction_no ASC
        """)

        result = session.execute(sql, {
            'branch_id': branch_id,
            'start_date': yesterday,
            'end_date': today
        })
        items = [dict(row._mapping) for row in result]

        # 计算汇总统计
        total_count = len(items)
        total_amount_thb = sum([float(item['local_amount'] or 0) for item in items])
        unreported_count = sum([1 for item in items if not item['is_reported']])
        overdue_count = sum([1 for item in items if not item['is_reported'] and item['days_diff'] > 1])

        return jsonify({
            'success': True,
            'data': {
                'date_range': f"{yesterday} to {today}",
                'start_date': str(yesterday),
                'end_date': str(today),
                'items': items,
                'total_count': total_count,
                'total_amount_thb': total_amount_thb,
                'unreported_count': unreported_count,
                'overdue_count': overdue_count
            }
        })

    except Exception as e:
        logger.error(f"Error in get_t1_buy_fx: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'查询买入外币报表失败: {str(e)}'
        }), 500

    finally:
        session.close()


@app_bot.route('/t1-sell-fx', methods=['GET'])
@token_required
@bot_permission_required('bot_report_view')
def get_t1_sell_fx(current_user):
    """
    查询T+1卖出外币报表数据（昨天到今天）

    GET /api/bot/t1-sell-fx

    响应:
    {
        "success": true,
        "data": {
            "date_range": "2025-10-10 to 2025-10-11",
            "items": [...],
            "total_count": 8,
            "total_amount_thb": 3000000,
            "unreported_count": 3,
            "overdue_count": 1
        }
    }
    """
    session = SessionLocal()

    try:
        # 获取当前用户的branch_id
        branch_id = g.current_user.get('branch_id')
        
        # T+1时间范围：昨天到今天
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        # 查询BOT_SellFX记录（昨天到今天）
        sql = text("""
            SELECT
                b.id,
                b.transaction_no,
                b.transaction_date,
                b.customer_name,
                b.customer_id_number,
                b.customer_country_code,
                b.sell_currency_code as currency_code,
                b.sell_amount as foreign_amount,
                b.local_amount,
                b.exchange_rate,
                b.usd_equivalent,
                b.is_reported,
                b.report_time,
                b.created_at,
                DATEDIFF(CURDATE(), b.transaction_date) as days_diff
            FROM BOT_SellFX b
            WHERE b.branch_id = :branch_id
                AND b.transaction_date >= :start_date
                AND b.transaction_date <= :end_date
            ORDER BY b.transaction_date ASC, b.transaction_no ASC
        """)

        result = session.execute(sql, {
            'branch_id': branch_id,
            'start_date': yesterday,
            'end_date': today
        })
        items = [dict(row._mapping) for row in result]

        # 计算汇总统计
        total_count = len(items)
        total_amount_thb = sum([float(item['local_amount'] or 0) for item in items])
        unreported_count = sum([1 for item in items if not item['is_reported']])
        overdue_count = sum([1 for item in items if not item['is_reported'] and item['days_diff'] > 1])

        return jsonify({
            'success': True,
            'data': {
                'date_range': f"{yesterday} to {today}",
                'start_date': str(yesterday),
                'end_date': str(today),
                'items': items,
                'total_count': total_count,
                'total_amount_thb': total_amount_thb,
                'unreported_count': unreported_count,
                'overdue_count': overdue_count
            }
        })

    except Exception as e:
        logger.error(f"Error in get_t1_sell_fx: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'查询卖出外币报表失败: {str(e)}'
        }), 500

    finally:
        session.close()


@app_bot.route('/export-buy-fx', methods=['GET'])
@token_required
@bot_permission_required('bot_report_export')
def export_buy_fx_excel(current_user):
    """
    导出BOT报表Excel（完整格式，从manager目录）

    GET /api/bot/export-buy-fx?month=10&year=2025

    查询参数:
    - month: 报告月份 (1-12)，默认当前月
    - year: 报告年份（公历），默认当前年

    响应:
    Excel文件下载或生成新报表
    """
    session = SessionLocal()

    try:
        # 获取月份和年份参数
        month_str = request.args.get('month')
        year_str = request.args.get('year')
        
        if not month_str or not year_str:
            today = datetime.now()
            month = today.month
            year = today.year
        else:
            month = int(month_str)
            year = int(year_str)

        # 获取当前用户的branch_id
        branch_id = g.current_user.get('branch_id')
        
        # 转换为佛历年份
        buddhist_year = year + 543
        
        # 检查manager目录中是否已有报表
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        manager_dir = os.path.join(current_dir, '..', 'manager', str(year), f"{month:02d}")
        report_filename = f"BOT_Report_{year}{month:02d}.xlsx"
        report_path = os.path.join(manager_dir, report_filename)
        
        # 如果文件不存在，生成新报表
        if not os.path.exists(report_path):
            from services.bot_template_based_generator import BOTTemplateBasedGenerator
            
            try:
                report_path = BOTTemplateBasedGenerator.generate_report(
                    db_session=session,
                    branch_id=branch_id,
                    report_month=month,
                    report_year=buddhist_year
                )
            except Exception as e:
                logger.error(f"生成BOT报表失败: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': f'生成报表失败: {str(e)}'
                }), 500
        
        # 返回文件
        return send_file(
            report_path,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=os.path.basename(report_path)
        )

    except Exception as e:
        logger.error(f"Error in export_buy_fx_excel: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'导出Excel失败: {str(e)}'
        }), 500

    finally:
        session.close()


@app_bot.route('/export-sell-fx', methods=['GET'])
@token_required
@bot_permission_required('bot_report_export')
def export_sell_fx_excel(current_user):
    """
    导出BOT报表Excel（与buy-fx相同，从manager目录）

    GET /api/bot/export-sell-fx?month=10&year=2025

    查询参数:
    - month: 报告月份 (1-12)，默认当前月
    - year: 报告年份（公历），默认当前年

    响应:
    Excel文件下载
    """
    # 复用export_buy_fx_excel的逻辑，因为它们在同一个Excel文件中
    return export_buy_fx_excel(current_user)


@app_bot.route('/mark-reported', methods=['POST'])
@token_required
@bot_permission_required('bot_report_export')
def mark_bot_reported(current_user):
    """
    标记BOT记录为已上报
    
    POST /api/bot/mark-reported
    {
        "table": "BOT_BuyFX",  // BOT_BuyFX, BOT_SellFX, BOT_FCD, BOT_Provider
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
        table_name = data.get('table')
        ids = data.get('ids', [])
        
        if not table_name or not ids:
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            }), 400
        
        # 验证表名（防止SQL注入）
        valid_tables = ['BOT_BuyFX', 'BOT_SellFX', 'BOT_FCD', 'BOT_Provider']
        if table_name not in valid_tables:
            return jsonify({
                'success': False,
                'message': '无效的表名'
            }), 400
        
        # 获取当前用户ID
        user_id = g.current_user.get('id', 1)
        
        # 更新记录
        sql = text(f"""
            UPDATE {table_name}
            SET is_reported = TRUE,
                report_time = NOW(),
                reported_by = :user_id
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
            'message': f'成功标记{result.rowcount}条记录为已上报'
        })
        
    except Exception as e:
        session.rollback()
        logger.error(f"标记已上报失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'标记失败: {str(e)}'
        }), 500
    finally:
        session.close()


@app_bot.route('/list-reports', methods=['GET'])
@token_required
@bot_permission_required('bot_report_view')
def list_bot_reports(current_user):
    """
    列出manager目录下的BOT报表文件
    
    GET /api/bot/list-reports?year=2025
    
    查询参数:
    - year: 年份，默认当前年
    
    返回:
    {
        "success": true,
        "reports": [
            {
                "year": 2025,
                "month": 10,
                "filename": "BOT_Report_202510.xlsx",
                "path": "...",
                "size": 185470,
                "created_at": "2025-10-11 01:16:57"
            }
        ]
    }
    """
    try:
        # 获取年份参数
        year_str = request.args.get('year')
        year = int(year_str) if year_str else datetime.now().year
        
        # 获取当前用户的branch_id
        branch_id = g.current_user.get('branch_id')
        
        # 构建manager目录路径
        import os
        import glob
        current_dir = os.path.dirname(os.path.abspath(__file__))
        manager_year_dir = os.path.join(current_dir, '..', 'manager', str(year))
        
        reports = []
        
        if os.path.exists(manager_year_dir):
            # 遍历所有月份目录
            for month in range(1, 13):
                month_dir = os.path.join(manager_year_dir, f"{month:02d}")
                if os.path.exists(month_dir):
                    # 查找BOT报表文件
                    pattern = os.path.join(month_dir, "BOT_Report_*.xlsx")
                    files = glob.glob(pattern)
                    
                    for file_path in files:
                        stat = os.stat(file_path)
                        reports.append({
                            'year': year,
                            'month': month,
                            'filename': os.path.basename(file_path),
                            'path': file_path,
                            'size': stat.st_size,
                            'created_at': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                        })
        
        return jsonify({
            'success': True,
            'reports': reports,
            'count': len(reports)
        })
        
    except Exception as e:
        logger.error(f"列出BOT报表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'列出报表失败: {str(e)}'
        }), 500


@app_bot.route('/save-buy-fx', methods=['POST'])
@token_required
def save_bot_buy_fx(current_user):
    """
    保存BOT买入外币报表记录

    POST /api/bot/save-buy-fx

    请求体:
    {
        "transaction_id": 12345,
        "report_date": "2025-10-01",
        "json_data": {...}
    }

    响应:
    {
        "success": true,
        "report_id": 1
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

        transaction_id = request_data.get('transaction_id')
        report_date = request_data.get('report_date')
        json_data = request_data.get('json_data', {})

        if not transaction_id or not report_date:
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            }), 400

        # 插入记录
        sql = text("""
            INSERT INTO BOT_BuyFX (
                transaction_id, report_date, json_data,
                branch_id, operator_id, created_at
            ) VALUES (
                :transaction_id, :report_date, :json_data,
                :branch_id, :operator_id, NOW()
            )
        """)

        current_user = g.current_user
        params = {
            'transaction_id': transaction_id,
            'report_date': report_date,
            'json_data': json.dumps(json_data, ensure_ascii=False),
            'branch_id': current_user['branch_id'],
            'operator_id': current_user['id']
        }

        result = session.execute(sql, params)
        session.commit()

        return jsonify({
            'success': True,
            'report_id': result.lastrowid
        })

    except Exception as e:
        session.rollback()
        logger.error(f"Error in save_bot_buy_fx: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'保存记录失败: {str(e)}'
        }), 500

    finally:
        session.close()


@app_bot.route('/save-sell-fx', methods=['POST'])
@token_required
def save_bot_sell_fx(current_user):
    """
    保存BOT卖出外币报表记录

    POST /api/bot/save-sell-fx

    请求体:
    {
        "transaction_id": 12345,
        "report_date": "2025-10-01",
        "json_data": {...}
    }

    响应:
    {
        "success": true,
        "report_id": 1
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

        transaction_id = request_data.get('transaction_id')
        report_date = request_data.get('report_date')
        json_data = request_data.get('json_data', {})

        if not transaction_id or not report_date:
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            }), 400

        # 插入记录
        sql = text("""
            INSERT INTO BOT_SellFX (
                transaction_id, report_date, json_data,
                branch_id, operator_id, created_at
            ) VALUES (
                :transaction_id, :report_date, :json_data,
                :branch_id, :operator_id, NOW()
            )
        """)

        current_user = g.current_user
        params = {
            'transaction_id': transaction_id,
            'report_date': report_date,
            'json_data': json.dumps(json_data, ensure_ascii=False),
            'branch_id': current_user['branch_id'],
            'operator_id': current_user['id']
        }

        result = session.execute(sql, params)
        session.commit()

        return jsonify({
            'success': True,
            'report_id': result.lastrowid
        })

    except Exception as e:
        session.rollback()
        logger.error(f"Error in save_bot_sell_fx: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'保存记录失败: {str(e)}'
        }), 500

    finally:
        session.close()


# 错误处理
@app_bot.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': '接口不存在'
    }), 404


@app_bot.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'message': '服务器内部错误'
    }), 500
