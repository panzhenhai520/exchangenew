from flask import Blueprint, request, jsonify, send_file
from datetime import datetime, date, timedelta
import os
import glob
import logging
from sqlalchemy import and_, func, desc
from sqlalchemy.orm import joinedload
from services.db_service import DatabaseService
from services.auth_service import token_required, has_permission, check_eod_session_permission
from services.eod_service import EODService
from models.exchange_models import EODStatus, EODBalanceVerification, EODCashOut, ExchangeTransaction, Currency, Branch, Operator  # EODHistory, EODBalanceSnapshot 已废弃
from utils.i18n_utils import I18nUtils


# 创建logger实例
logger = logging.getLogger(__name__)

end_of_day_bp = Blueprint('end_of_day', __name__, url_prefix='/api/end_of_day')

@end_of_day_bp.route('/start', methods=['POST'])
@token_required
@has_permission('end_of_day')
def start_eod(current_user):
    """
    步骤1: 开始日结 - 营业锁定和会话锁定
    """
    try:
        data = request.get_json()
        branch_id = data.get('branch_id')
        target_date = data.get('date', date.today().isoformat())
        operator_id = current_user['id']
        
        if not branch_id:
            return jsonify({'success': False, 'message': 'Branch ID is required'}), 400
        
        # 转换日期格式
        if isinstance(target_date, str):
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        
        # 获取会话信息
        from flask import session
        session_id = session.get('eod_session_id') or session.get('session_id') or request.headers.get('X-Session-ID') or f"eod_{current_user['id']}_{datetime.now().timestamp()}"
        ip_address = request.remote_addr or 'unknown'
        user_agent = request.headers.get('User-Agent', '')
        
        result = EODService.start_eod(
            branch_id=branch_id,
            operator_id=operator_id,
            target_date=target_date,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if result['success']:
            # 保存会话ID到session中
            session['eod_session_id'] = session_id
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'开始日结失败: {str(e)}'}), 500

@end_of_day_bp.route('/<int:eod_id>/continue', methods=['POST'])
@token_required
@has_permission('end_of_day')
def continue_eod(current_user, eod_id):
    """
    继续现有日结流程 - 设置会话ID以便后续操作
    """
    try:
        # 获取会话信息
        from flask import session
        session_id = session.get('eod_session_id') or session.get('session_id') or request.headers.get('X-Session-ID') or f"eod_{current_user['id']}_{datetime.now().timestamp()}"
        ip_address = request.remote_addr or 'unknown'
        user_agent = request.headers.get('User-Agent', '')
        
        # 验证EOD是否存在并且属于当前用户的分支
        session_db = DatabaseService.get_session()
        try:
            eod_status = session_db.query(EODStatus).filter_by(id=eod_id).first()
            if not eod_status:
                return jsonify({'success': False, 'message': '日结记录不存在'}), 404
            
            if eod_status.branch_id != current_user['branch_id']:
                return jsonify({'success': False, 'message': '无权限访问该日结'}), 403
            
            # 设置会话ID用于后续操作
            session['eod_session_id'] = session_id
            
            # 记录继续操作的会话信息
            result = EODService.continue_eod_session(
                eod_id=eod_id,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'message': '成功继续现有流程',
                    'session_id': session_id,
                    'eod_id': eod_id
                }), 200
            else:
                return jsonify(result), 400
                
        finally:
            DatabaseService.close_session(session_db)
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'继续日结失败: {str(e)}'}), 500

@end_of_day_bp.route('/<int:eod_id>/balance', methods=['GET'])
@token_required
@has_permission('end_of_day')
@check_eod_session_permission
def extract_balance(current_user, eod_id):
    """
    步骤2: 提取余额
    """
    try:
        result = EODService.extract_balance(eod_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'提取余额失败: {str(e)}'}), 500

@end_of_day_bp.route('/<int:eod_id>/calc', methods=['GET'])
@token_required
@has_permission('end_of_day')
@check_eod_session_permission
def calculate_balance(current_user, eod_id):
    """
    步骤3: 计算理论余额
    """
    try:
        result = EODService.calculate_theoretical_balance(eod_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'计算理论余额失败: {str(e)}'}), 500

@end_of_day_bp.route('/<int:eod_id>/check', methods=['GET'])
@token_required
@has_permission('end_of_day')
@check_eod_session_permission
def verify_balance(current_user, eod_id):
    """
    步骤4: 核对余额
    """
    try:
        result = EODService.verify_balance(eod_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'核对余额失败: {str(e)}'}), 500

@end_of_day_bp.route('/<int:eod_id>/verify', methods=['POST'])
@token_required
@has_permission('end_of_day')
@check_eod_session_permission
def handle_verification(current_user, eod_id):
    """
    步骤5: 处理核对结果 - 一致则继续，不一致则取消或强制继续
    """
    try:
        data = request.get_json()
        action = data.get('action')  # 'continue' or 'cancel'
        reason = data.get('reason', '')
        
        result = EODService.handle_verification_result(eod_id, action, reason)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'处理核对结果失败: {str(e)}'}), 500

@end_of_day_bp.route('/<int:eod_id>/handle_difference', methods=['POST'])
@token_required
@has_permission('end_of_day')
@check_eod_session_permission
def handle_balance_difference(current_user, eod_id):
    """
    处理余额差额选择：cancel, force, adjust
    """
    try:
        data = request.get_json()
        action = data.get('action')  # 'cancel', 'force', 'adjust'
        reason = data.get('reason', '')
        
        result = EODService.handle_balance_difference(eod_id, action, reason)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'处理余额差额失败: {str(e)}'}), 500

@end_of_day_bp.route('/<int:eod_id>/adjust_difference', methods=['POST'])
@token_required
@has_permission('end_of_day')
@check_eod_session_permission
def adjust_eod_difference(current_user, eod_id):
    """
    执行日结差额调节
    """
    try:
        data = request.get_json()
        adjust_data = data.get('adjust_data', [])
        
        result = EODService.adjust_eod_difference(eod_id, adjust_data, current_user['id'])
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'差额调节失败: {str(e)}'}), 500

@end_of_day_bp.route('/<int:eod_id>/cashout', methods=['POST'])
@token_required
@has_permission('end_of_day')
@check_eod_session_permission
def process_cash_out(current_user, eod_id):
    """
    步骤6: 完成交款
    """
    try:
        data = request.get_json()
        cash_out_data = data.get('cash_out_data', [])
        cash_receiver_name = data.get('cash_receiver_name')  # 收款人姓名
        cash_out_remark = data.get('cash_out_remark', '')  # 交款备注
        operator_id = current_user['id']
        
        # 验证交款数据格式
        for cash_out in cash_out_data:
            if 'currency_id' not in cash_out or 'amount' not in cash_out:
                return jsonify({'success': False, 'message': 'Invalid cash out data format'}), 400
        
        result = EODService.process_cash_out(eod_id, cash_out_data, operator_id, cash_receiver_name, cash_out_remark)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'交款处理失败: {str(e)}'}), 500

@end_of_day_bp.route('/<int:eod_id>/preview', methods=['GET'])
@token_required
@has_permission('end_of_day')
def preview_report(current_user, eod_id):
    """
    步骤7: 预览报表 - 用于第7步生成报表数据，不检查步骤状态
    """
    try:
        mode = request.args.get('mode', 'simple')  # simple or detailed
        
        if mode not in ['simple', 'detailed']:
            return jsonify({'success': False, 'message': 'Invalid report mode'}), 400
        
        # 直接调用print_report中的数据生成逻辑（不检查步骤状态）
        result = EODService.generate_preview_report(eod_id, mode)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'预览报表失败: {str(e)}'}), 500

@end_of_day_bp.route('/<int:eod_id>/report', methods=['GET'])
@token_required
@has_permission('end_of_day')
def generate_report(current_user, eod_id):
    """
    步骤8: 生成日结报表 - 必须先完成第7步打印
    """
    try:
        mode = request.args.get('mode', 'simple')  # simple or detailed
        
        if mode not in ['simple', 'detailed']:
            return jsonify({'success': False, 'message': 'Invalid report mode'}), 400
        
        result = EODService.generate_report(eod_id, mode)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'生成报表失败: {str(e)}'}), 500

@end_of_day_bp.route('/<int:eod_id>/print', methods=['POST'])
@token_required
@has_permission('end_of_day')
def print_report(current_user, eod_id):
    """
    打印日结报表 - 统一PDF生成 (已移除会话检查)
    """
    try:
        data = request.get_json()
        mode = data.get('mode', 'simple')
        operator_id = current_user['id']
        
        # 【修复】获取请求数据中的语言参数
        language = data.get('language', 'zh')
        
        # 【修复】标准化语言代码，处理 th-TH -> th, en-US -> en 的映射
        def normalize_language_code(lang_code):
            """标准化语言代码"""
            if not lang_code:
                return 'zh'
            
            lang_code = lang_code.lower()
            if lang_code.startswith('th'):
                return 'th'
            elif lang_code.startswith('en'):
                return 'en'
            elif lang_code.startswith('zh'):
                return 'zh'
            else:
                return 'zh'  # 默认中文
        
        original_language = language
        language = normalize_language_code(language)
        
        # 【调试】记录语言参数
        logger.info(f"🌍 打印日结报表请求 - EOD ID: {eod_id}, 原始语言参数: {original_language}, 标准化后: {language}, 请求数据: {data}")
        
        if mode not in ['simple', 'detailed']:
            return jsonify({'success': False, 'message': 'Invalid print mode'}), 400
        
        result = EODService.print_report(eod_id, operator_id, mode, language)
        
        if result['success']:
            # 【修复】根据语言参数过滤返回的文件
            if 'generated_files' in result:
                # 过滤出指定语言的文件
                filtered_files = [f for f in result['generated_files'] if f.get('language') == language]
                if filtered_files:
                    # 只返回指定语言的文件
                    result['generated_files'] = filtered_files
                    result['current_language'] = language
                    logger.info(f"🌍 第7步返回{language}语言的文件: {[f.get('filename') for f in filtered_files]}")
                else:
                    logger.warning(f"🌍 第7步未找到{language}语言的文件，返回所有文件")
            
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'打印失败: {str(e)}'}), 500

@end_of_day_bp.route('/<int:eod_id>/complete', methods=['POST'])
@token_required
@has_permission('end_of_day')
@check_eod_session_permission
def complete_eod(current_user, eod_id):
    """
    步骤8: 完成日结
    """
    try:
        operator_id = current_user['id']
        
        # 【修复】获取会话ID用于权限验证
        session_id = request.headers.get('X-Session-ID') or request.args.get('session_id')
        
        result = EODService.complete_eod(eod_id, operator_id, session_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'完成日结失败: {str(e)}'}), 500

@end_of_day_bp.route('/<int:eod_id>/auto-recover-session', methods=['POST'])
@token_required
@has_permission('end_of_day')
def auto_recover_eod_session(current_user, eod_id):
    """
    自动恢复日结会话
    """
    try:
        operator_id = current_user['id']
        
        # 获取会话ID
        session_id = request.headers.get('X-Session-ID') or request.args.get('session_id')
        
        result = EODService.auto_recover_eod_session(eod_id, operator_id, session_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'自动恢复会话失败: {str(e)}'}), 500

@end_of_day_bp.route('/<int:eod_id>/status', methods=['GET'])
@token_required
@has_permission('end_of_day')
def get_eod_status(current_user, eod_id):
    """
    获取日结状态
    """
    try:
        result = EODService.get_eod_status(eod_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取日结状态失败: {str(e)}'}), 500

@end_of_day_bp.route('/lock-status', methods=['GET'])
@token_required
@has_permission('end_of_day')
def check_business_lock(current_user):
    """
    检查营业锁定状态
    """
    try:
        branch_id = request.args.get('branch_id')
        if not branch_id:
            return jsonify({'success': False, 'message': 'Branch ID is required'}), 400
        
        result = EODService.check_business_lock(int(branch_id))
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'检查营业锁定状态失败: {str(e)}'}), 500

@end_of_day_bp.route('/<int:eod_id>/cancel', methods=['POST'])
@token_required
@has_permission('end_of_day')
def cancel_eod(current_user, eod_id):
    """
    取消日结 - 允许任何有权限的用户取消当前网点的日结
    """
    try:
        data = request.get_json()
        reason = data.get('reason', '用户取消')
        operator_id = current_user['id']
        
        # 检查EOD是否属于当前用户的网点
        session = DatabaseService.get_session()
        try:
            eod_status = session.query(EODStatus).filter_by(id=eod_id).first()
            if not eod_status:
                return jsonify({'success': False, 'message': '日结记录不存在'}), 404
            
            # 检查网点权限
            if eod_status.branch_id != current_user['branch_id']:
                return jsonify({'success': False, 'message': '无权限取消其他网点的日结'}), 403
                
        finally:
            DatabaseService.close_session(session)
        
        result = EODService.cancel_eod(eod_id, reason, operator_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'取消日结失败: {str(e)}'}), 500

@end_of_day_bp.route('/<int:eod_id>/cancel_completed', methods=['POST'])
@token_required
@has_permission('end_of_day')
def cancel_completed_eod(current_user, eod_id):
    """
    取消已完成的日结记录
    """
    try:
        branch_id = current_user['branch_id']
        session = DatabaseService.get_session()
        
        try:
            # 查找日结记录
            eod_status = session.query(EODStatus).filter(
                EODStatus.id == eod_id,
                EODStatus.branch_id == branch_id,
                EODStatus.status == 'completed'
            ).first()
            
            if not eod_status:
                return jsonify({'success': False, 'message': '日结记录不存在或状态不正确'}), 404
            
            # 更新状态为已取消
            eod_status.status = 'cancelled'
            eod_status.cancel_reason = '用户取消已完成日结'
            session.commit()
            
            return jsonify({
                'success': True,
                'message': '已成功取消日结记录'
            }), 200
            
        finally:
            DatabaseService.close_session(session)
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'取消已完成日结失败: {str(e)}'}), 500

@end_of_day_bp.route('/<int:eod_id>/reset-to-print', methods=['POST'])
@token_required
@has_permission('end_of_day')
def reset_to_print_step(current_user, eod_id):
    """
    重置日结状态到第7步 - 用于修正错误跳过打印步骤的情况
    """
    try:
        operator_id = current_user['id']
        
        result = EODService.reset_to_print_step(eod_id, operator_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'重置失败: {str(e)}'}), 500

@end_of_day_bp.route('/summary', methods=['GET'])
@token_required
@has_permission('end_of_day')
def get_eod_summary(current_user):
    """
    获取日结汇总信息
    """
    try:
        branch_id = request.args.get('branch_id')
        target_date = request.args.get('date', date.today().isoformat())
        
        if not branch_id:
            return jsonify({'success': False, 'message': 'Branch ID is required'}), 400
        
        # 转换日期格式
        if isinstance(target_date, str):
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        
        result = EODService.get_eod_summary(int(branch_id), target_date)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取日结汇总失败: {str(e)}'}), 500

@end_of_day_bp.route('/check_completed', methods=['GET'])
@token_required
@has_permission('end_of_day')
def check_completed_eod(current_user):
    """
    检查指定日期是否有已完成的日结
    """
    try:
        target_date = request.args.get('date')
        if not target_date:
            return jsonify({'success': False, 'message': '缺少日期参数'}), 400
        
        # 解析日期
        from datetime import datetime
        try:
            parsed_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'message': '日期格式错误'}), 400
        
        branch_id = current_user['branch_id']
        result = EODService.check_completed_eod(branch_id, parsed_date)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'检查已完成日结失败: {str(e)}'}), 500

@end_of_day_bp.route('/check_existing', methods=['GET'])
@token_required
@has_permission('end_of_day')
def check_existing_eod(current_user):
    """
    检查是否有进行中或已完成的日结
    """
    try:
        branch_id = current_user['branch_id']
        session = DatabaseService.get_session()
        
        try:
            # 检查进行中的日结
            existing_eod = session.query(EODStatus).filter(
                EODStatus.branch_id == branch_id,
                EODStatus.status == 'processing'
            ).first()
            
            # 检查已完成的日结（今天）
            from datetime import date
            today = date.today()
            completed_eod = session.query(EODStatus).filter(
                EODStatus.branch_id == branch_id,
                EODStatus.status == 'completed',
                EODStatus.date == today
            ).first()
            
            result = {
                'success': True,
                'existing': {
                    'id': existing_eod.id,
                    'date': existing_eod.date.isoformat(),
                    'status': existing_eod.status,
                    'started_at': existing_eod.started_at.isoformat() if existing_eod.started_at else None
                } if existing_eod else None,
                'completed': {
                    'eod_id': completed_eod.id,
                    'date': completed_eod.date.isoformat(),
                    'status': completed_eod.status,
                    'completed_at': completed_eod.completed_at.isoformat() if completed_eod.completed_at else None
                } if completed_eod else None
            }
            
            return jsonify(result), 200
            
        finally:
            DatabaseService.close_session(session)
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'检查现有日结失败: {str(e)}'}), 500

@end_of_day_bp.route('/today_history', methods=['GET'])
@token_required
@has_permission('end_of_day')
def get_today_eod_history(current_user):
    """
    获取当天日结历史
    """
    try:
        target_date = request.args.get('date')
        if not target_date:
            return jsonify({'success': False, 'message': '缺少日期参数'}), 400
        
        # 解析日期
        from datetime import datetime
        try:
            parsed_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'message': '日期格式错误'}), 400
        
        branch_id = current_user['branch_id']
        result = EODService.get_today_eod_history(branch_id, parsed_date)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取当天日结历史失败: {str(e)}'}), 500

@end_of_day_bp.route('/latest', methods=['GET'])
@token_required
@has_permission('end_of_day')
def get_latest_eod(current_user):
    """
    获取最新的日结记录，用于计算时间范围
    """
    try:
        branch_id = request.args.get('branch_id')
        before_date = request.args.get('before_date')
        
        if not branch_id:
            branch_id = current_user['branch_id']
        
        # 验证权限：只能查询自己分支的数据
        if int(branch_id) != current_user['branch_id']:
            return jsonify({'success': False, 'message': '无权限查询其他分支的数据'}), 403
        
        session = DatabaseService.get_session()
        try:
            # 【修复】查询EODStatus表而不是EODHistory表，获取最新已完成的日结记录
            query = session.query(EODStatus).filter(
                EODStatus.branch_id == branch_id,
                EODStatus.status == 'completed'
            )
            
            if before_date:
                # 解析日期字符串
                from datetime import datetime
                try:
                    parsed_date = datetime.strptime(before_date, '%Y-%m-%d').date()
                    query = query.filter(EODStatus.date < parsed_date)
                except ValueError:
                    return jsonify({'success': False, 'message': '日期格式错误'}), 400
            
            latest_eod = query.order_by(desc(EODStatus.completed_at)).first()
            
            if latest_eod:
                return jsonify({
                    'success': True,
                    'latest_eod': {
                        'id': latest_eod.id,
                        'date': latest_eod.date.isoformat(),
                        'started_at': latest_eod.started_at.isoformat() if latest_eod.started_at else None,
                        'completed_at': latest_eod.completed_at.isoformat() if latest_eod.completed_at else None
                    }
                }), 200
            else:
                # 【新增】当没有已完成的日结记录时，查找第一笔交易时间作为建议的开始时间
                first_transaction = session.query(ExchangeTransaction).filter(
                    ExchangeTransaction.branch_id == branch_id
                ).order_by(ExchangeTransaction.created_at.asc()).first()
                
                if first_transaction and first_transaction.created_at:
                    # 返回第一笔交易信息，供前端计算时间范围
                    return jsonify({
                        'success': True,
                        'latest_eod': None,
                        'first_transaction': {
                            'created_at': first_transaction.created_at.isoformat(),
                            'suggested_start_time': first_transaction.created_at.isoformat()
                        }
                    }), 200
                else:
                    return jsonify({
                        'success': True,
                        'latest_eod': None,
                        'first_transaction': None
                    }), 200
                
        finally:
            DatabaseService.close_session(session)
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取最新日结记录失败: {str(e)}'}), 500

@end_of_day_bp.route('/<eod_no>/download-receipt', methods=['GET'])
@token_required
@has_permission('end_of_day')
def download_eod_report(current_user, eod_no):
    """
    下载日结报表PDF文件 - 支持多语言
    """
    try:
        # 获取语言参数
        language = request.args.get('lang', 'zh')
        
        # 标准化语言代码
        def normalize_language_code(lang_code):
            if not lang_code:
                return 'zh'
            lang_code = lang_code.lower()
            if lang_code.startswith('th'):
                return 'th'
            elif lang_code.startswith('en'):
                return 'en'
            elif lang_code.startswith('zh'):
                return 'zh'
            else:
                return 'zh'
        
        language = normalize_language_code(language)
        
        # 从eod_no解析出eod_id (格式: EOD00000001)
        logger.info(f"🌍 下载PDF请求 - eod_no: '{eod_no}', language: {language}, 操作员: {current_user.get('name', '未知')}")
        if not eod_no.startswith('EOD'):
            from utils.i18n_utils import I18nUtils
            # 根据请求的语言参数获取对应的错误消息
            if language == 'en':
                message = I18nUtils.get_message('eod.invalid_eod_id_format', 'en-US')
            elif language == 'th':
                message = I18nUtils.get_message('eod.invalid_eod_id_format', 'th-TH')
            else:
                message = I18nUtils.get_message('eod.invalid_eod_id_format', 'zh-CN')
            logger.error(f"❌ EOD编号格式错误 - eod_no: '{eod_no}', 翻译消息: '{message}'")
            return jsonify({'success': False, 'message': message}), 400
        
        try:
            eod_id = int(eod_no[3:])  # 去掉 EOD 前缀
        except ValueError:
            return jsonify({'success': False, 'message': '无效的日结编号'}), 400
        
        session = DatabaseService.get_session()
        try:
            eod_status = session.query(EODStatus).filter_by(id=eod_id).first()
            if not eod_status:
                return jsonify({'success': False, 'message': '日结记录不存在'}), 404
            
            # 检查权限：只能下载自己分支的日结报表
            if current_user['branch_id'] != eod_status.branch_id:
                return jsonify({'success': False, 'message': '无权限访问该日结报表'}), 403
            
            # 构建文件路径 - 根据语言选择对应的文件
            date_str = eod_status.date.strftime('%Y%m%d')
            
            # 根据语言构建文件名
            if language == 'en':
                file_pattern = f"{date_str}EOD{eod_id}*_en.pdf"
            elif language == 'th':
                file_pattern = f"{date_str}EOD{eod_id}*_th.pdf"
            else:  # zh - 只匹配没有语言后缀的文件
                file_pattern = f"{date_str}EOD{eod_id}*.pdf"
                # 排除带有语言后缀的文件
                exclude_patterns = [f"{date_str}EOD{eod_id}*_en.pdf", f"{date_str}EOD{eod_id}*_th.pdf"]
            
            # 搜索PDF文件 - 优先搜索cashout文件（第7步）
            manager_dir = os.path.join(os.path.dirname(__file__), '..', 'manager')
            year_dir = os.path.join(manager_dir, str(eod_status.date.year))
            month_dir = os.path.join(year_dir, f"{eod_status.date.month:02d}")
            
            # 【调试】记录搜索路径和模式
            logger.info(f"🌍 搜索PDF文件 - 语言: {language}, 目录: {month_dir}")
            logger.info(f"🌍 文件模式: {file_pattern}")
            
            pdf_files = []
            if os.path.exists(month_dir):
                # 首先尝试匹配cashout文件（第7步）
                cashout_pattern = file_pattern.replace('EOD', 'EOD').replace('*.pdf', 'cashout*.pdf')
                logger.info(f"🌍 搜索cashout文件模式: {cashout_pattern}")
                pdf_files = glob.glob(os.path.join(month_dir, cashout_pattern))
                logger.info(f"🌍 找到cashout文件: {pdf_files}")
                
                # 如果没找到cashout文件，尝试匹配其他文件
                if not pdf_files:
                    logger.info(f"🌍 未找到cashout文件，尝试通用模式: {file_pattern}")
                    pdf_files = glob.glob(os.path.join(month_dir, file_pattern))
                    logger.info(f"🌍 找到通用文件: {pdf_files}")
                
                # 如果是中文语言，排除带有语言后缀的文件
                if language == 'zh' and pdf_files:
                    filtered_files = []
                    for file_path in pdf_files:
                        filename = os.path.basename(file_path)
                        # 排除带有 _en 或 _th 后缀的文件
                        if not (filename.endswith('_en.pdf') or filename.endswith('_th.pdf')):
                            filtered_files.append(file_path)
                    pdf_files = filtered_files
                    logger.info(f"🌍 中文语言过滤后文件: {pdf_files}")
            else:
                logger.warning(f"🌍 目录不存在: {month_dir}")
            
            if not pdf_files:
                # 如果找不到对应语言的文件，尝试找默认文件
                if language != 'zh':
                    logger.info(f"🌍 未找到{language}语言文件，尝试回退到默认文件")
                    default_pattern = f"{date_str}EOD{eod_id}*.pdf"
                    # 先尝试cashout文件
                    fallback_cashout_pattern = default_pattern.replace('*.pdf', 'cashout*.pdf')
                    logger.info(f"🌍 回退cashout模式: {fallback_cashout_pattern}")
                    pdf_files = glob.glob(os.path.join(month_dir, fallback_cashout_pattern))
                    logger.info(f"🌍 回退cashout文件: {pdf_files}")
                    if not pdf_files:
                        # 再尝试其他文件
                        logger.info(f"🌍 回退通用模式: {default_pattern}")
                        pdf_files = glob.glob(os.path.join(month_dir, default_pattern))
                        logger.info(f"🌍 回退通用文件: {pdf_files}")
                    if pdf_files:
                        language = 'zh'  # 使用默认语言
                        logger.info(f"🌍 使用默认语言文件: {pdf_files}")
            
            if not pdf_files:
                logger.error(f"❌ 未找到任何PDF文件 (语言: {language})")
                return jsonify({'success': False, 'message': f'日结报表文件不存在 (语言: {language})'}), 404
            
            # 使用最新的文件
            file_path = max(pdf_files, key=os.path.getctime)
            
            if not os.path.exists(file_path):
                logger.error(f"❌ 文件不存在: {file_path}")
                return jsonify({'success': False, 'message': '日结报表文件不存在'}), 404
            
            logger.info(f"✅ 最终选择PDF文件: {file_path}")
            
            # 构建正确的下载文件名
            date_str = eod_status.date.strftime('%Y%m%d')
            if language == 'zh':
                download_name = f"{date_str}EOD{eod_id:03d}cashout.pdf"
            else:
                download_name = f"{date_str}EOD{eod_id:03d}cashout_{language}.pdf"
            
            logger.info(f"🌍 准备返回PDF文件 - 文件名: {download_name}")
            
            # 返回PDF文件
            return send_file(
                file_path,
                as_attachment=True,
                download_name=download_name,
                mimetype='application/pdf'
            )
            
        finally:
            DatabaseService.close_session(session)
            
    except Exception as e:
        import traceback
        logger.info(f"下载日结报表失败: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': f'下载失败: {str(e)}'}), 500

@end_of_day_bp.route('/<int:eod_id>/income-statistics', methods=['POST'])
@token_required
@has_permission('end_of_day')
def generate_income_statistics(current_user, eod_id):
    """
    新增步骤：收入统计 - 生成收入报表和库存报表
    在交款前进行
    """
    try:
        operator_id = current_user['id']
        
        # 获取请求中的语言参数
        data = request.get_json() or {}
        language = data.get('language', 'zh')  # 默认中文
        
        result = EODService.generate_income_statistics(eod_id, operator_id, language)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'收入统计失败: {str(e)}'}), 500

@end_of_day_bp.route('/<int:eod_id>/finalize-reports', methods=['POST'])
@token_required
@has_permission('end_of_day')
def finalize_reports(current_user, eod_id):
    """
    确认报表并标记为最终版本
    """
    try:
        operator_id = current_user['id']
        
        result = EODService.finalize_income_reports(eod_id, operator_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'确认报表失败: {str(e)}'}), 500

@end_of_day_bp.route('/<int:eod_id>/print-reports', methods=['POST'])
@token_required
@has_permission('end_of_day')
def print_income_reports(current_user, eod_id):
    """
    打印收入报表 - 使用统一的SimplePDFService，支持多语言
    """
    try:
        operator_id = current_user['id']
        
        # 获取请求数据中的语言参数
        request_data = request.get_json() or {}
        language = request_data.get('language', 'zh')
        
        # 【修复】标准化语言代码，处理 th-TH -> th, en-US -> en 的映射
        def normalize_language_code(lang_code):
            """标准化语言代码"""
            if not lang_code:
                return 'zh'
            
            lang_code = lang_code.lower()
            if lang_code.startswith('th'):
                return 'th'
            elif lang_code.startswith('en'):
                return 'en'
            elif lang_code.startswith('zh'):
                return 'zh'
            else:
                return 'zh'  # 默认中文
        
        original_language = language
        language = normalize_language_code(language)
        
        # 【调试】记录语言参数
        logger.info(f"🌍 打印报表请求 - EOD ID: {eod_id}, 原始语言参数: {original_language}, 标准化后: {language}, 请求数据: {request_data}")
        
        result = EODService.print_income_reports(eod_id, operator_id, language)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'打印收入报表失败: {str(e)}'}), 500

@end_of_day_bp.route('/<int:eod_id>/print-comprehensive-reports', methods=['POST'])
@token_required
@has_permission('end_of_day')
def print_comprehensive_reports(current_user, eod_id):
    """
    打印综合报表 - 外币收入、外币库存、本币库存
    """
    try:
        operator_id = current_user['id']
        
        result = EODService.print_comprehensive_reports(eod_id, operator_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'打印综合报表失败: {str(e)}'}), 500

@end_of_day_bp.route('/history', methods=['GET'])
@token_required
@has_permission('end_of_day')
def get_eod_history(current_user):
    """
    获取日结历史记录
    """
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        branch_id = current_user.get('branch_id')
        if not branch_id:
            return jsonify({'success': False, 'message': '网点信息不存在'}), 400
        
        session = DatabaseService.get_session()
        try:
            # 构建查询
            query = session.query(EODStatus).filter_by(
                branch_id=branch_id,
                status='completed'
            )
            
            # 添加日期过滤
            if start_date:
                query = query.filter(EODStatus.date >= start_date)
            if end_date:
                query = query.filter(EODStatus.date <= end_date)
            
            # 按日期倒序
            query = query.order_by(EODStatus.date.desc())
            
            # 分页
            total = query.count()
            eod_records = query.offset((page - 1) * per_page).limit(per_page).all()
            
            # 格式化返回数据
            history_list = []
            for eod in eod_records:
                # 获取操作员姓名
                started_by_name = '未知操作员'
                completed_by_name = '未知操作员'
                
                if eod.started_by:
                    started_operator = session.query(Operator).filter_by(id=eod.started_by).first()
                    if started_operator:
                        started_by_name = started_operator.name
                
                if eod.completed_by:
                    completed_operator = session.query(Operator).filter_by(id=eod.completed_by).first()
                    if completed_operator:
                        completed_by_name = completed_operator.name
                
                history_list.append({
                    'id': eod.id,
                    'date': eod.date.isoformat(),
                    'started_at': eod.started_at.isoformat() if eod.started_at else None,
                    'completed_at': eod.completed_at.isoformat() if eod.completed_at else None,
                    'started_by': started_by_name,
                    'completed_by': completed_by_name,
                    'print_count': eod.print_count or 0,
                    'status': eod.status,
                    'business_start_time': eod.business_start_time.isoformat() if eod.business_start_time else None,
                    'business_end_time': eod.business_end_time.isoformat() if eod.business_end_time else None
                })
            
            return jsonify({
                'success': True,
                'data': {
                    'history': history_list,
                    'records': history_list,
                    'pagination': {
                        'page': page,
                        'per_page': per_page,
                        'total': total,
                        'pages': (total + per_page - 1) // per_page
                    }
                }
            }), 200
            
        finally:
            DatabaseService.close_session(session)
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取日结历史失败: {str(e)}'}), 500

def _calculate_opening_balance_from_transactions_for_base_currency(session, branch_id, currency_id, eod_start_time):
    """
    当本币没有上次日结记录时，按照用户要求的逻辑计算期初余额
    
    规则：
    1. 查找该币种在日结开始时间之前的第一笔交易
    2. 第一笔交易的local_amount值直接作为期初余额（本币使用local_amount字段）
    3. 变化统计从第一笔交易时间+1秒开始
    
    Args:
        session: 数据库会话
        branch_id: 网点ID
        currency_id: 币种ID
        eod_start_time: 日结开始时间
    
    Returns:
        tuple: (期初余额, 变化统计开始时间)
    """
    # 查询该币种在日结开始时间前的第一笔交易（按时间正序）
    first_transaction = session.query(ExchangeTransaction).filter(
        and_(
            ExchangeTransaction.branch_id == branch_id,
            ExchangeTransaction.currency_id == currency_id,
            ExchangeTransaction.created_at < eod_start_time,
            ExchangeTransaction.type.in_(['initial_balance', 'adjust_balance', 'buy', 'sell', 'reversal', 'cash_out'])
        )
    ).order_by(ExchangeTransaction.created_at.asc()).first()
    
    if not first_transaction:
        logger.info(f"本币{currency_id}无历史交易记录，期初余额为0")
        return 0.0, eod_start_time
    
    # 本币使用local_amount字段
    opening_balance = float(first_transaction.local_amount)
    
    # 变化统计从第一笔交易时间之后开始（+1秒）
    change_start_time = first_transaction.created_at + timedelta(seconds=1)
    
    logger.info(f"本币{currency_id}期初余额计算：第一笔交易ID={first_transaction.id}, 时间={first_transaction.created_at}, 期初余额={opening_balance}")
    logger.info(f"本币{currency_id}变化统计开始时间：{change_start_time}")
    
    return opening_balance, change_start_time


@end_of_day_bp.route('/<int:eod_id>/base-currency/<currency_code>/transactions', methods=['GET'])
@token_required
@has_permission('end_of_day')
def get_base_currency_transactions(current_user, eod_id, currency_code):
    """
    获取指定EOD记录的本币交易明细
    【修复】与CalGain函数保持一致的查询条件和时间范围
    """
    session = None
    try:
        session = DatabaseService.get_session()
        
        # 验证日结记录存在性
        eod_status = session.query(EODStatus).filter_by(id=eod_id).first()
        if not eod_status:
            return jsonify({'success': False, 'message': '日结记录不存在'}), 404
        
        branch_id = eod_status.branch_id
        
        # 获取分支的基准货币
        branch = session.query(Branch).options(
            joinedload(Branch.base_currency)
        ).filter_by(id=branch_id).first()
        
        if not branch:
            return jsonify({'success': False, 'message': '分支不存在'}), 404
        
        base_currency = branch.base_currency
        if not base_currency or base_currency.currency_code != currency_code:
            return jsonify({'success': False, 'message': '币种不是基准货币'}), 400
        
        # 【修复】使用与CalBalance完全相同的期初余额和时间范围逻辑
        target_date = eod_status.date
        eod_start_time = eod_status.started_at if eod_status.started_at else datetime.now()
        
        # 导入特性开关
        from config.features import FeatureFlags
        
        # 期初余额和变化统计时间范围
        opening_balance = 0.0
        change_start_time = eod_start_time
        change_end_time = datetime.now()
        
        # 根据特性开关决定期初余额获取方式
        if FeatureFlags.FEATURE_NEW_PERIOD_BALANCE:
            # 【新方式】从EODBalanceVerification表获取上次日结的actual_balance
            logger.info("🔧 本币明细查询使用新方式：从EODBalanceVerification表获取期初余额")
            
            # 查找上次已完成日结的余额验证记录
            prev_eod_verification = session.query(EODBalanceVerification).join(EODStatus).filter(
                EODStatus.branch_id == branch_id,
                EODStatus.status == 'completed',
                EODBalanceVerification.currency_id == base_currency.id
            ).order_by(desc(EODStatus.completed_at)).first()
            
            if prev_eod_verification:
                # 有上次日结记录：使用上次日结验证后的实际余额作为期初
                opening_balance = float(prev_eod_verification.actual_balance)
                
                # 变化统计从上次日结结束时间+1秒开始
                prev_eod_status = session.query(EODStatus).filter_by(
                    id=prev_eod_verification.eod_status_id
                ).first()
                if prev_eod_status and prev_eod_status.completed_at:
                    change_start_time = prev_eod_status.completed_at + timedelta(seconds=1)
                    change_end_time = eod_start_time  # 到当前日结开始时间
                    
                logger.info(f"{currency_code} 期初余额: {opening_balance} (来自EODBalanceVerification)")
                logger.info(f"{currency_code} 变化统计时间: {change_start_time} 到 {change_end_time}")
            else:
                # 没有上次日结记录：按照用户要求的逻辑计算期初余额
                opening_balance, change_start_time = _calculate_opening_balance_from_transactions_for_base_currency(
                    session, branch_id, base_currency.id, eod_start_time
                )
                change_end_time = eod_start_time  # 到当前日结开始时间
                
                logger.info(f"{currency_code} 期初余额: {opening_balance} (第一笔交易值)")
                logger.info(f"{currency_code} 变化统计时间: {change_start_time} 到 {change_end_time}")
        else:
            # 【传统方式】从EODBalanceSnapshot表获取remaining_balance
            logger.info("🔧 本币明细查询使用传统方式：从EODBalanceSnapshot表获取期初余额")
            
            # 查找上次日结的余额快照
            prev_eod_snapshot = session.query(EODBalanceSnapshot).join(EODHistory).join(EODStatus).filter(
                EODStatus.branch_id == branch_id,
                EODStatus.status == 'completed',
                EODBalanceSnapshot.currency_id == base_currency.id
            ).order_by(desc(EODStatus.completed_at)).first()
            
            if prev_eod_snapshot:
                # 有上次日结记录：使用上次日结的剩余余额作为期初
                opening_balance = float(prev_eod_snapshot.remaining_balance)
                
                # 变化统计从上次日结结束时间+1秒开始
                prev_eod_history = session.query(EODHistory).filter_by(
                    id=prev_eod_snapshot.eod_history_id
                ).first()
                if prev_eod_history:
                    prev_eod_status = session.query(EODStatus).filter_by(
                        id=prev_eod_history.eod_status_id
                    ).first()
                    if prev_eod_status and prev_eod_status.completed_at:
                        change_start_time = prev_eod_status.completed_at + timedelta(seconds=1)
                        change_end_time = eod_start_time  # 到当前日结开始时间
                        
                logger.info(f"{currency_code} 期初余额: {opening_balance} (来自EODBalanceSnapshot)")
                logger.info(f"{currency_code} 变化统计时间: {change_start_time} 到 {change_end_time}")
            else:
                # 没有上次日结记录：按照用户要求的逻辑计算期初余额
                opening_balance, change_start_time = _calculate_opening_balance_from_transactions_for_base_currency(
                    session, branch_id, base_currency.id, eod_start_time
                )
                change_end_time = eod_start_time  # 到当前日结开始时间
                
                logger.info(f"{currency_code} 期初余额: {opening_balance} (第一笔交易值)")
                logger.info(f"{currency_code} 变化统计时间: {change_start_time} 到 {change_end_time}")
        
        # 使用计算出的时间范围作为查询条件
        start_time = change_start_time
        end_time = change_end_time
        
        # 【日志】记录查询条件
        logger.info(f"【本币明细查询】get_base_currency_transactions查询条件:")
        logger.info(f"  - 网点ID: {branch_id}")
        logger.info(f"  - 基准货币: {currency_code} (ID: {base_currency.id})")
        logger.info(f"  - 交易类型: ['buy', 'sell', 'adjust_balance', 'reversal', 'initial_balance']")
        logger.info(f"  - 时间范围: {start_time.strftime('%Y-%m-%d %H:%M:%S')} 到 {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"  - 时间条件SQL: created_at >= '{start_time}' AND created_at < '{end_time}'")
        
        # 【修复】使用与CalGain完全一致的查询条件
        # 1. 查询所有相关交易（包括外币兑换和直接本币交易）
        all_transactions = session.query(ExchangeTransaction).filter(
            and_(
                ExchangeTransaction.branch_id == branch_id,
                ExchangeTransaction.type.in_(['buy', 'sell', 'adjust_balance', 'reversal', 'initial_balance']),
                ExchangeTransaction.created_at >= start_time,
                ExchangeTransaction.created_at < end_time
            )
        ).order_by(ExchangeTransaction.created_at.desc()).all()
        
        # 【日志】记录查询结果
        logger.info(f"【本币明细查询】查询到 {len(all_transactions)} 笔交易记录")
        
        # 【日志】记录交易类型分布
        type_counts = {}
        for tx in all_transactions:
            type_counts[tx.type] = type_counts.get(tx.type, 0) + 1
        logger.info(f"【本币明细查询】交易类型分布: {type_counts}")
        
        # 组装交易明细 - 对于本币，所有交易都会产生local_amount的影响
        transaction_list = []
        
        for tx in all_transactions:
            # 【修复】过滤条件：只显示本币交易或影响本币的外币交易
            # 对于余额调节，只显示本币的余额调节，不显示外币的余额调节
            if tx.type == 'adjust_balance' and tx.currency_id != base_currency.id:
                continue  # 跳过外币的余额调节
            
            # 获取外币信息（如果不是本币交易）
            if tx.currency_id != base_currency.id:
                foreign_currency = session.query(Currency).filter_by(id=tx.currency_id).first()
                foreign_currency_code = foreign_currency.currency_code if foreign_currency else '外币'
            else:
                foreign_currency_code = currency_code
            
            # 【修复】本币交易统一使用local_amount字段
            local_amount = round(float(tx.local_amount), 2) if tx.local_amount is not None else 0.0
            
            # 根据交易类型确定描述和金额方向
            if tx.type == 'buy':
                # 买入外币，本币支出（负值）
                if tx.currency_id != base_currency.id:
                    description = f"eod.step5.buy_transaction {foreign_currency_code} {tx.amount}"
                else:
                    description = "eod.step5.buy_base_currency"
                amount = -abs(local_amount)  # 本币支出为负值
            elif tx.type == 'sell':
                # 卖出外币，本币收入（正值）
                if tx.currency_id != base_currency.id:
                    description = f"eod.step5.sell_transaction {foreign_currency_code} {tx.amount}"
                else:
                    description = "eod.step5.sell_base_currency"
                amount = abs(local_amount)  # 本币收入为正值
            elif tx.type == 'adjust_balance':
                # 余额调节
                description = f"eod.step5.adjust_balance_transaction {foreign_currency_code}"
                amount = local_amount  # 直接使用local_amount
            elif tx.type == 'reversal':
                # 冲正交易
                if tx.currency_id != base_currency.id:
                    description = f"eod.step5.reversal_transaction {foreign_currency_code} {tx.amount}"
                else:
                    description = "eod.step5.reversal_base_currency"
                amount = local_amount  # 直接使用local_amount
            elif tx.type == 'initial_balance':
                # 期初余额
                description = f"eod.step5.opening_balance {foreign_currency_code}"
                amount = local_amount if tx.currency_id == base_currency.id else 0  # 只有本币的期初余额影响本币
            else:
                description = f"eod.step5.other_transaction {foreign_currency_code}"
                amount = local_amount
            
            transaction_list.append({
                'id': tx.id,
                'transaction_no': tx.transaction_no,
                'type': tx.type,
                'amount': amount,  # 【修复】统一使用处理后的local_amount
                'rate': float(tx.rate) if tx.rate else 1.0,
                'local_amount': local_amount,  # 原始local_amount
                'foreign_amount': round(float(tx.amount), 2) if tx.amount is not None else 0.0,  # 原始外币金额
                'customer_name': tx.customer_name,
                'description': description,
                'created_at': tx.created_at.isoformat(),
                'foreign_currency': foreign_currency_code,
                'is_base_currency_transaction': tx.currency_id == base_currency.id
            })
        
        # 【日志】记录详细交易信息
        for tx_detail in transaction_list:
            logger.info(f"  本币交易明细: 单号={tx_detail['transaction_no']}, 类型={tx_detail['type']}, 本币金额={tx_detail['amount']}, 外币={tx_detail['foreign_currency']}")
        
        # 【修复】分别计算buy、sell、reversal的汇总金额
        buy_amount = sum(abs(tx['amount']) for tx in transaction_list if tx['type'] == 'buy')  # 买入金额（支出）
        sell_amount = sum(tx['amount'] for tx in transaction_list if tx['type'] == 'sell')    # 卖出金额（收入）
        reversal_amount = sum(tx['amount'] for tx in transaction_list if tx['type'] == 'reversal')  # 冲正金额
        
        # 【修复】收入金额和支出金额的计算逻辑：排除冲正业务
        # 收入金额：只计算正值的非冲正交易
        income_amount = sum(tx['amount'] for tx in transaction_list if tx['amount'] > 0 and tx['type'] != 'reversal')
        # 支出金额：只计算负值的非冲正交易
        expense_amount = sum(abs(tx['amount']) for tx in transaction_list if tx['amount'] < 0 and tx['type'] != 'reversal')
        
        # 兼容原有逻辑的统计数据
        total_income = sum(tx['amount'] for tx in transaction_list if tx['amount'] > 0)
        total_expense = sum(abs(tx['amount']) for tx in transaction_list if tx['amount'] < 0)
        net_change = total_income - total_expense
        
        # 【日志】记录统计结果
        logger.info(f"【本币明细查询】统计结果:")
        logger.info(f"  - 买入金额(支出): {buy_amount}")
        logger.info(f"  - 卖出金额(收入): {sell_amount}")
        logger.info(f"  - 冲正金额: {reversal_amount}")
        logger.info(f"  - 收入金额(排除冲正): {income_amount}")
        logger.info(f"  - 支出金额(排除冲正): {expense_amount}")
        logger.info(f"  - 总收入: {total_income}")
        logger.info(f"  - 总支出: {total_expense}")
        logger.info(f"  - 净变动: {net_change}")
        logger.info(f"  - 交易笔数: {len(transaction_list)}")
        
        # 【日志】输出查询条件对比总结
        logger.info("="*80)
        logger.info(f"【本币查询条件对比总结】币种: {currency_code}")
        logger.info(f"【汇总查询】CalGain条件: type IN ['buy', 'sell', 'adjust_balance', 'reversal', 'initial_balance']")
        logger.info(f"【明细查询】get_base_currency_transactions条件: type IN ['buy', 'sell', 'adjust_balance', 'reversal', 'initial_balance']")
        logger.info(f"【时间条件】两个查询均使用EOD实际时间范围: created_at >= '{start_time}' AND created_at < '{end_time}'")
        logger.info(f"【字段使用】本币交易统一使用local_amount字段")
        logger.info(f"【明细查询结果】{currency_code} 查询到 {len(transaction_list)} 笔交易记录")
        logger.info("="*80)
        
        return jsonify({
            'success': True,
            'data': {
                'currency_code': currency_code,
                'currency_name': base_currency.currency_name,
                'transaction_count': len(transaction_list),
                'opening_balance': opening_balance,  # 期初余额
                'buy_amount': buy_amount,  # 买入金额（支出）
                'sell_amount': sell_amount,  # 卖出金额（收入）
                'reversal_amount': reversal_amount,  # 冲正金额
                'income_amount': income_amount,  # 收入金额（排除冲正）
                'expense_amount': expense_amount,  # 支出金额（排除冲正）
                'total_income': total_income,
                'total_expense': total_expense,
                'net_change': net_change,
                'theoretical_balance': opening_balance + net_change,  # 理论余额
                'transactions': transaction_list,
                'time_range': {
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat()
                },
                'feature_flag': {
                    'FEATURE_NEW_PERIOD_BALANCE': FeatureFlags.FEATURE_NEW_PERIOD_BALANCE
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"获取本币交易明细异常: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': f'获取本币交易明细失败: {str(e)}'}), 500
    finally:
        if session:
            DatabaseService.close_session(session)

@end_of_day_bp.route('/cleanup-session', methods=['POST'])
@token_required
@has_permission('end_of_day')
def cleanup_eod_session_api(current_user):

    try:
        from utils.cleanup_eod_session import cleanup_current_branch_session
        
        if not current_user:
            return jsonify({
                'success': False,
                'message': '(u7b*g{vU_'
            }), 401
        
        
        result = cleanup_current_branch_session(current_user)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error in cleanup_eod_session_api: {str(e)}")
        return jsonify({
            'success': False,
            'message': f': {str(e)}'
        }), 500

@end_of_day_bp.route('/<int:eod_id>/download-income-report', methods=['GET'])
@token_required
def download_income_report(current_user, eod_id):
    """下载EOD收入报表PDF文件（从manager目录）"""
    try:
        import os
        from flask import send_file
        
        operator_id = current_user.get('user_id') or current_user.get('id')
        language = request.args.get('language', 'zh')
        
        # 【修复】标准化语言代码，处理 th-TH -> th, en-US -> en 的映射
        def normalize_language_code(lang_code):
            """标准化语言代码"""
            if not lang_code:
                return 'zh'
            
            lang_code = lang_code.lower()
            if lang_code.startswith('th'):
                return 'th'
            elif lang_code.startswith('en'):
                return 'en'
            elif lang_code.startswith('zh'):
                return 'zh'
            else:
                return 'zh'  # 默认中文
        
        original_language = language
        language = normalize_language_code(language)
        
        # 【调试】记录语言参数
        logger.info(f"🌍 下载PDF请求 - EOD ID: {eod_id}, 原始语言参数: {original_language}, 标准化后: {language}")
        
        # 获取EOD信息
        from services.db_service import DatabaseService
        from models.exchange_models import EODStatus
        
        session = DatabaseService.get_session()
        try:
            eod_status = session.query(EODStatus).filter_by(id=eod_id).first()
            if not eod_status:
                return jsonify({'success': False, 'message': '日结记录不存在'}), 404
            
            # 构建PDF文件路径
            from services.simple_pdf_service import SimplePDFService
            target_date = eod_status.date
            
            # 使用EOD规范命名（根据语言参数）
            date_str = target_date.strftime('%Y%m%d')
            if language == 'th':
                filename = f"{date_str}EOD{eod_id}income_th.pdf"
            elif language == 'en':
                filename = f"{date_str}EOD{eod_id}income_en.pdf"
            else:  # 默认中文
                filename = f"{date_str}EOD{eod_id}income.pdf"
            
            # 获取manager目录下的文件路径
            file_path = SimplePDFService.get_manager_file_path(
                'income', 
                eod_id=eod_id, 
                eod_date=target_date
            )
            
            # 确保使用正确的文件名
            file_path = os.path.join(os.path.dirname(file_path), filename)
            
            # 检查文件是否存在，如果不存在则搜索类似文件
            if not os.path.exists(file_path):
                # 搜索目录中是否有类似的文件（处理文件名冲突导致的数字后缀）
                manager_dir = os.path.dirname(file_path)
                
                # 根据语言构建搜索模式
                if language == 'th':
                    pattern_prefix = f"{date_str}EOD{eod_id}income_th"
                elif language == 'en':
                    pattern_prefix = f"{date_str}EOD{eod_id}income_en"
                else:
                    pattern_prefix = f"{date_str}EOD{eod_id}income"
                
                if os.path.exists(manager_dir):
                    for filename_candidate in os.listdir(manager_dir):
                        if filename_candidate.startswith(pattern_prefix) and filename_candidate.endswith('.pdf'):
                            # 找到匹配的文件
                            file_path = os.path.join(manager_dir, filename_candidate)
                            filename = filename_candidate  # 更新实际的文件名用于日志
                            logger.info(f"找到实际{language}版本PDF文件: {filename_candidate} (原期望: {filename})")
                            break
                    else:
                        # 没有找到匹配的文件
                        language_name = {'zh': '中文', 'th': '泰语', 'en': '英语'}.get(language, '中文')
                        return jsonify({'success': False, 'message': f'{language_name}版本PDF文件不存在，请先生成报表'}), 404
                else:
                    return jsonify({'success': False, 'message': 'PDF文件不存在，请先生成报表'}), 404
            
            # 记录下载日志
            from services.log_service import LogService
            LogService.log_system_event(
                f"下载EOD收入报表PDF - 日结ID: {eod_id}, 文件: {filename}, 语言: {language}",
                operator_id=operator_id,
                branch_id=eod_status.branch_id
            )
            
            # 返回PDF文件
            return send_file(
                file_path,
                as_attachment=False,  # 改为不强制下载，支持浏览器内打开
                download_name=filename,
                mimetype='application/pdf'
            )
            
        finally:
            DatabaseService.close_session(session)
        
    except Exception as e:
        logger.error(f"下载EOD收入报表PDF失败: {e}")
        return jsonify({'success': False, 'message': f'下载失败: {str(e)}'}), 500

@end_of_day_bp.route('/history/<int:eod_id>', methods=['GET'])
@token_required
@has_permission('end_of_day')
def get_eod_history_detail(current_user, eod_id):
    """
    获取日结历史详情
    """
    try:
        branch_id = current_user.get('branch_id')
        if not branch_id:
            return jsonify({'success': False, 'message': '网点信息不存在'}), 400
        
        session = DatabaseService.get_session()
        try:
            # 查询日结记录
            eod_status = session.query(EODStatus).filter_by(
                id=eod_id,
                branch_id=branch_id,
                status='completed'
            ).first()
            
            if not eod_status:
                return jsonify({'success': False, 'message': '日结记录不存在'}), 404
            
            # 查询日结历史记录
            eod_history = session.query(EODHistory).filter_by(
                eod_status_id=eod_id
            ).first()
            
            # 构建返回数据
            eod_info = {
                'id': eod_status.id,
                'date': eod_status.date.isoformat(),
                'started_at': eod_status.started_at.isoformat() if eod_status.started_at else None,
                'completed_at': eod_status.completed_at.isoformat() if eod_status.completed_at else None,
                'started_by': eod_status.started_by,
                'completed_by': eod_status.completed_by,
                'status': eod_status.status
            }
            
            # 如果有历史记录，添加额外信息
            if eod_history:
                # 查询按币种分类的交款信息
                cash_outs = session.query(EODCashOut).filter_by(
                    eod_status_id=eod_id
                ).all()
                
                # 构建按币种分类的交款金额
                cash_out_by_currency = []
                for cash_out in cash_outs:
                    cash_out_by_currency.append({
                        'currency_code': cash_out.currency.code,
                        'currency_name': cash_out.currency.name,
                        'amount': float(cash_out.cash_out_amount),
                        'remaining_balance': float(cash_out.remaining_balance)
                    })
                
                eod_info.update({
                    'total_transactions': eod_history.total_transactions,
                    'total_buy_amount': float(eod_history.total_buy_amount),
                    'total_sell_amount': float(eod_history.total_sell_amount),
                    'total_adjust_amount': float(eod_history.total_adjust_amount),
                    'cash_out_amount': float(eod_history.cash_out_amount),  # 保留总金额用于兼容
                    'cash_out_by_currency': cash_out_by_currency,  # 新增：按币种分类
                    'cash_out_operator': eod_history.cash_out_operator.name if eod_history.cash_out_operator else None,
                    'cash_receiver': eod_history.cash_receiver.name if eod_history.cash_receiver else None
                })
            
            return jsonify({
                'success': True,
                'eod_info': eod_info
            }), 200
            
        finally:
            DatabaseService.close_session(session)
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取日结详情失败: {str(e)}'}), 500

@end_of_day_bp.route('/history/<int:eod_id>/income-pdf', methods=['GET'])
@token_required
@has_permission('end_of_day')
def get_eod_income_pdf(current_user, eod_id):
    """
    获取日结收入报表PDF
    """
    try:
        language = request.args.get('language', 'zh')
        branch_id = current_user.get('branch_id')
        
        if not branch_id:
            return jsonify({'success': False, 'message': '网点信息不存在'}), 400
        
        session = DatabaseService.get_session()
        try:
            # 查询日结记录
            eod_status = session.query(EODStatus).filter_by(
                id=eod_id,
                branch_id=branch_id,
                status='completed'
            ).first()
            
            if not eod_status:
                return jsonify({'success': False, 'message': '日结记录不存在'}), 404
            
            # 构建PDF文件名 - 修复文件名格式
            date_str = eod_status.date.strftime('%Y%m%d')
            if language == 'zh':
                filename = f"{date_str}EOD{eod_id}income.pdf"
            elif language == 'en':
                filename = f"{date_str}EOD{eod_id}income_en.pdf"
            elif language == 'th':
                filename = f"{date_str}EOD{eod_id}income_th.pdf"
            else:
                filename = f"{date_str}EOD{eod_id}income.pdf"
            
            # 构建文件路径
            year_month = eod_status.date.strftime('%Y/%m')
            file_path = os.path.join(os.path.dirname(__file__), '..', 'manager', year_month, filename)
            
            # 检查文件是否存在
            if os.path.exists(file_path):
                # 返回文件URL - 修复URL格式
                pdf_url = f"/end_of_day/history/{eod_id}/income-pdf/download?language={language}"
                return jsonify({
                    'success': True,
                    'pdf_url': pdf_url,
                    'filename': filename
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': '收入报表文件不存在'
                }), 404
                
        finally:
            DatabaseService.close_session(session)
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取收入报表失败: {str(e)}'}), 500

@end_of_day_bp.route('/history/<int:eod_id>/cashout-pdf', methods=['GET'])
@token_required
@has_permission('end_of_day')
def get_eod_cashout_pdf(current_user, eod_id):
    """
    获取日结交款报表PDF
    """
    try:
        # 【修复】标准化语言代码，处理 th-TH -> th, en-US -> en 的映射
        def normalize_language_code(lang_code):
            """标准化语言代码"""
            if not lang_code:
                return 'zh'
            
            lang_code = lang_code.lower()
            if lang_code.startswith('th'):
                return 'th'
            elif lang_code.startswith('en'):
                return 'en'
            elif lang_code.startswith('zh'):
                return 'zh'
            else:
                return 'zh'  # 默认中文
        
        original_language = request.args.get('language', 'zh')
        language = normalize_language_code(original_language)
        
        # 【调试】记录语言参数标准化
        logger.info(f"🌍 获取交款报表 - 语言参数标准化: 原始: {original_language}, 标准化后: {language}")
        branch_id = current_user.get('branch_id')
        
        if not branch_id:
            return jsonify({'success': False, 'message': '网点信息不存在'}), 400
        
        session = DatabaseService.get_session()
        try:
            # 查询日结记录
            eod_status = session.query(EODStatus).filter_by(
                id=eod_id,
                branch_id=branch_id,
                status='completed'
            ).first()
            
            if not eod_status:
                return jsonify({'success': False, 'message': '日结记录不存在'}), 404
            
            # 构建PDF文件名 - 修复文件名格式
            date_str = eod_status.date.strftime('%Y%m%d')
            if language == 'zh':
                filename = f"{date_str}EOD{eod_id}cashout.pdf"
            elif language == 'en':
                filename = f"{date_str}EOD{eod_id}cashout_en.pdf"
            elif language == 'th':
                filename = f"{date_str}EOD{eod_id}cashout_th.pdf"
            else:
                filename = f"{date_str}EOD{eod_id}cashout.pdf"
            
            # 构建文件路径
            year_month = eod_status.date.strftime('%Y/%m')
            file_path = os.path.join(os.path.dirname(__file__), '..', 'manager', year_month, filename)
            
            # 检查文件是否存在
            if os.path.exists(file_path):
                # 返回文件URL - 修复URL格式
                pdf_url = f"/end_of_day/history/{eod_id}/cashout-pdf/download?language={language}"
                return jsonify({
                    'success': True,
                    'pdf_url': pdf_url,
                    'filename': filename
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': '交款报表文件不存在'
                }), 404
                
        finally:
            DatabaseService.close_session(session)
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取交款报表失败: {str(e)}'}), 500

@end_of_day_bp.route('/history/<int:eod_id>/income-pdf/download', methods=['GET'])
@token_required
@has_permission('end_of_day')
def download_eod_income_pdf(current_user, eod_id):
    """
    下载日结收入报表PDF
    """
    try:
        language = request.args.get('language', 'zh')
        branch_id = current_user.get('branch_id')
        
        if not branch_id:
            return jsonify({'success': False, 'message': '网点信息不存在'}), 400
        
        session = DatabaseService.get_session()
        try:
            # 查询日结记录
            eod_status = session.query(EODStatus).filter_by(
                id=eod_id,
                branch_id=branch_id,
                status='completed'
            ).first()
            
            if not eod_status:
                return jsonify({'success': False, 'message': '日结记录不存在'}), 404
            
            # 构建PDF文件名和路径 - 修复文件名格式
            date_str = eod_status.date.strftime('%Y%m%d')
            if language == 'zh':
                filename = f"{date_str}EOD{eod_id}income.pdf"
            elif language == 'en':
                filename = f"{date_str}EOD{eod_id}income_en.pdf"
            elif language == 'th':
                filename = f"{date_str}EOD{eod_id}income_th.pdf"
            else:
                filename = f"{date_str}EOD{eod_id}income.pdf"
            year_month = eod_status.date.strftime('%Y/%m')
            file_path = os.path.join(os.path.dirname(__file__), '..', 'manager', year_month, filename)
            
            # 检查文件是否存在
            if os.path.exists(file_path):
                return send_file(
                    file_path,
                    as_attachment=True,
                    download_name=filename,
                    mimetype='application/pdf'
                )
            else:
                return jsonify({
                    'success': False,
                    'message': '收入报表文件不存在'
                }), 404
                
        finally:
            DatabaseService.close_session(session)
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'下载收入报表失败: {str(e)}'}), 500

@end_of_day_bp.route('/history/<int:eod_id>/cashout-pdf/download', methods=['GET'])
@token_required
@has_permission('end_of_day')
def download_eod_cashout_pdf(current_user, eod_id):
    """
    下载日结交款报表PDF
    """
    try:
        # 【修复】标准化语言代码，处理 th-TH -> th, en-US -> en 的映射
        def normalize_language_code(lang_code):
            """标准化语言代码"""
            if not lang_code:
                return 'zh'
            
            lang_code = lang_code.lower()
            if lang_code.startswith('th'):
                return 'th'
            elif lang_code.startswith('en'):
                return 'en'
            elif lang_code.startswith('zh'):
                return 'zh'
            else:
                return 'zh'  # 默认中文
        
        original_language = request.args.get('language', 'zh')
        language = normalize_language_code(original_language)
        branch_id = current_user.get('branch_id')
        
        # 【调试】记录语言参数标准化
        logger.info(f"🌍 下载交款报表 - 语言参数标准化: 原始: {original_language}, 标准化后: {language}")
        
        if not branch_id:
            return jsonify({'success': False, 'message': '网点信息不存在'}), 400
        
        session = DatabaseService.get_session()
        try:
            # 查询日结记录
            eod_status = session.query(EODStatus).filter_by(
                id=eod_id,
                branch_id=branch_id,
                status='completed'
            ).first()
            
            if not eod_status:
                return jsonify({'success': False, 'message': '日结记录不存在'}), 404
            
            # 构建PDF文件名和路径 - 修复文件名格式
            date_str = eod_status.date.strftime('%Y%m%d')
            if language == 'zh':
                filename = f"{date_str}EOD{eod_id}cashout.pdf"
            elif language == 'en':
                filename = f"{date_str}EOD{eod_id}cashout_en.pdf"
            elif language == 'th':
                filename = f"{date_str}EOD{eod_id}cashout_th.pdf"
            else:
                filename = f"{date_str}EOD{eod_id}cashout.pdf"
            year_month = eod_status.date.strftime('%Y/%m')
            file_path = os.path.join(os.path.dirname(__file__), '..', 'manager', year_month, filename)
            
            # 检查文件是否存在
            if os.path.exists(file_path):
                return send_file(
                    file_path,
                    as_attachment=True,
                    download_name=filename,
                    mimetype='application/pdf'
                )
            else:
                return jsonify({
                    'success': False,
                    'message': '交款报表文件不存在'
                }), 404
                
        finally:
            DatabaseService.close_session(session)
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'下载交款报表失败: {str(e)}'}), 500

@end_of_day_bp.route('/<int:eod_id>/pdf-files', methods=['GET'])
@token_required
@has_permission('end_of_day')
def get_eod_pdf_files(current_user, eod_id):
    """
    获取日结记录的PDF文件列表
    """
    try:
        import os
        import glob
        from datetime import datetime
        
        session = DatabaseService.get_session()
        try:
            # 验证日结记录存在性
            eod_status = session.query(EODStatus).filter_by(id=eod_id).first()
            if not eod_status:
                return jsonify({'success': False, 'message': '日结记录不存在'}), 404
            
            target_date = eod_status.date
            date_str = target_date.strftime('%Y%m%d')
            
            # 构建文件目录路径 - 使用manager目录
            manager_dir = os.path.join(os.path.dirname(__file__), '..', 'manager')
            year = target_date.year
            month = target_date.month
            target_dir = os.path.join(manager_dir, str(year), f"{month:02d}")
            
            pdf_files = []
            
            if os.path.exists(target_dir):
                # 查找所有包含日结ID的PDF文件
                patterns = [
                    f"{date_str}EOD{eod_id}*.pdf",  # 收入报表和交款报表
                ]
                
                for pattern in patterns:
                    file_pattern_full = os.path.join(target_dir, pattern)
                    matching_files = glob.glob(file_pattern_full)
                    
                    for file_path in matching_files:
                        filename = os.path.basename(file_path)
                        file_stat = os.stat(file_path)
                        
                        # 确定文件类型
                        file_type = 'unknown'
                        if 'income' in filename:
                            file_type = 'income'
                        elif 'cashout' in filename:
                            file_type = 'eod_report'
                        elif 'Diff' in filename:
                            file_type = 'difference'
                        
                        # 构建URL - 使用新的PDF查看端点
                        if 'income' in filename:
                            # 确定语言
                            if '_en' in filename:
                                language = 'en'
                            elif '_th' in filename:
                                language = 'th'
                            else:
                                language = 'zh'
                            file_url = f"/api/end_of_day/history/{eod_id}/income-pdf/view?language={language}"
                        elif 'cashout' in filename:
                            # 确定语言
                            if '_en' in filename:
                                language = 'en'
                            elif '_th' in filename:
                                language = 'th'
                            else:
                                language = 'zh'
                            file_url = f"/api/end_of_day/history/{eod_id}/cashout-pdf/view?language={language}"
                        elif 'Diff' in filename:
                            # 确定语言
                            if '_en' in filename:
                                language = 'en'
                            elif '_th' in filename:
                                language = 'th'
                            else:
                                language = 'zh'
                            file_url = f"/api/end_of_day/history/{eod_id}/difference-pdf/view?language={language}"
                        else:
                            file_url = f"/api/end_of_day/history/{eod_id}/income-pdf/view"
                        
                        pdf_files.append({
                            'filename': filename,
                            'type': file_type,
                            'size': file_stat.st_size,
                            'created_at': datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                            'modified_at': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                            'url': file_url
                        })
            
            # 检查是否有差额调节记录
            from models.exchange_models import ExchangeTransaction
            eod_diff_transactions = session.query(ExchangeTransaction).filter(
                ExchangeTransaction.branch_id == eod_status.branch_id,
                ExchangeTransaction.type == 'Eod_diff',
                ExchangeTransaction.transaction_date == target_date
            ).all()
            
            has_adjustment = len(eod_diff_transactions) > 0
            
            # 按创建时间倒序排列
            pdf_files.sort(key=lambda x: x['created_at'], reverse=True)
            
            return jsonify({
                'success': True,
                'data': {
                    'eod_id': eod_id,
                    'eod_date': target_date.isoformat(),
                    'pdf_files': pdf_files,
                    'has_adjustment': has_adjustment
                }
            }), 200
            
        finally:
            DatabaseService.close_session(session)
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取PDF文件列表失败: {str(e)}'}), 500

@end_of_day_bp.route('/history/<int:eod_id>/income-pdf/view', methods=['GET'])
def view_eod_income_pdf(eod_id):
    """
    查看日结收入报表PDF（支持URL参数token和Authorization header）
    """
    try:
        language = request.args.get('language', 'zh')
        
        # 获取token - 优先从URL参数获取，其次从Authorization header获取
        token = request.args.get('token')
        if not token:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header[7:]  # 移除 'Bearer ' 前缀
        
        if not token:
            return jsonify({'success': False, 'message': '缺少访问令牌'}), 401
        
        # 验证token
        try:
            import jwt
            from datetime import datetime
            SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'ExchangeOK-JWT-Secret-Key-2025-Fixed')
            
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            user_id = payload['sub']
            
            # 获取用户信息
            session = DatabaseService.get_session()
            try:
                user = session.query(Operator).filter_by(id=user_id).first()
                if not user:
                    return jsonify({'success': False, 'message': '用户不存在或已禁用'}), 401
                
                current_user = {
                    'id': user.id,
                    'name': user.name,
                    'branch_id': user.branch_id,
                    'role_id': user.role_id
                }
            finally:
                DatabaseService.close_session(session)
                
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': '访问令牌已过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': '无效的访问令牌'}), 401
        except Exception as e:
            return jsonify({'success': False, 'message': f'访问令牌验证失败: {str(e)}'}), 401
        
        branch_id = current_user.get('branch_id')
        if not branch_id:
            return jsonify({'success': False, 'message': '网点信息不存在'}), 400
        
        session = DatabaseService.get_session()
        try:
            # 查询日结记录
            eod_status = session.query(EODStatus).filter_by(
                id=eod_id,
                branch_id=branch_id,
                status='completed'
            ).first()
            
            if not eod_status:
                return jsonify({'success': False, 'message': '日结记录不存在'}), 404
            
            # 构建PDF文件名和路径
            date_str = eod_status.date.strftime('%Y%m%d')
            if language == 'zh':
                filename = f"{date_str}EOD{eod_id}income.pdf"
            elif language == 'en':
                filename = f"{date_str}EOD{eod_id}income_en.pdf"
            elif language == 'th':
                filename = f"{date_str}EOD{eod_id}income_th.pdf"
            else:
                filename = f"{date_str}EOD{eod_id}income.pdf"
            
            year_month = eod_status.date.strftime('%Y/%m')
            file_path = os.path.join(os.path.dirname(__file__), '..', 'manager', year_month, filename)
            
            # 检查文件是否存在
            if os.path.exists(file_path):
                return send_file(
                    file_path,
                    as_attachment=False,  # 不下载，直接显示
                    download_name=filename,
                    mimetype='application/pdf'
                )
            else:
                return jsonify({
                    'success': False,
                    'message': '收入报表文件不存在'
                }), 404
                
        finally:
            DatabaseService.close_session(session)
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'查看收入报表失败: {str(e)}'}), 500

@end_of_day_bp.route('/history/<int:eod_id>/cashout-pdf/view', methods=['GET'])
def view_eod_cashout_pdf(eod_id):
    """
    查看日结交款报表PDF（支持URL参数token）
    """
    try:
        # 【修复】标准化语言代码，处理 th-TH -> th, en-US -> en 的映射
        def normalize_language_code(lang_code):
            """标准化语言代码"""
            if not lang_code:
                return 'zh'
            
            lang_code = lang_code.lower()
            if lang_code.startswith('th'):
                return 'th'
            elif lang_code.startswith('en'):
                return 'en'
            elif lang_code.startswith('zh'):
                return 'zh'
            else:
                return 'zh'  # 默认中文
        
        original_language = request.args.get('language', 'zh')
        language = normalize_language_code(original_language)
        
        # 【调试】记录语言参数标准化
        logger.info(f"🌍 查看交款报表 - 语言参数标准化: 原始: {original_language}, 标准化后: {language}")
        # 获取token - 优先从URL参数获取，其次从Authorization header获取
        token = request.args.get('token')
        if not token:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header[7:]  # 移除 'Bearer ' 前缀
        
        if not token:
            return jsonify({'success': False, 'message': '缺少访问令牌'}), 401
        
        # 验证token
        try:
            import jwt
            from datetime import datetime
            SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'ExchangeOK-JWT-Secret-Key-2025-Fixed')
            
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            user_id = payload['sub']
            
            # 获取用户信息
            session = DatabaseService.get_session()
            try:
                user = session.query(Operator).filter_by(id=user_id).first()
                if not user:
                    return jsonify({'success': False, 'message': '用户不存在或已禁用'}), 401
                
                current_user = {
                    'id': user.id,
                    'name': user.name,
                    'branch_id': user.branch_id,
                    'role_id': user.role_id
                }
            finally:
                DatabaseService.close_session(session)
                
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': '访问令牌已过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': '无效的访问令牌'}), 401
        except Exception as e:
            return jsonify({'success': False, 'message': f'访问令牌验证失败: {str(e)}'}), 401
        
        branch_id = current_user.get('branch_id')
        if not branch_id:
            return jsonify({'success': False, 'message': '网点信息不存在'}), 400
        
        session = DatabaseService.get_session()
        try:
            # 查询日结记录
            eod_status = session.query(EODStatus).filter_by(
                id=eod_id,
                branch_id=branch_id,
                status='completed'
            ).first()
            
            if not eod_status:
                return jsonify({'success': False, 'message': '日结记录不存在'}), 404
            
            # 构建PDF文件名和路径
            date_str = eod_status.date.strftime('%Y%m%d')
            if language == 'zh':
                filename = f"{date_str}EOD{eod_id}cashout.pdf"
            elif language == 'en':
                filename = f"{date_str}EOD{eod_id}cashout_en.pdf"
            elif language == 'th':
                filename = f"{date_str}EOD{eod_id}cashout_th.pdf"
            else:
                filename = f"{date_str}EOD{eod_id}cashout.pdf"
            
            year_month = eod_status.date.strftime('%Y/%m')
            file_path = os.path.join(os.path.dirname(__file__), '..', 'manager', year_month, filename)
            
            # 检查文件是否存在
            if os.path.exists(file_path):
                return send_file(
                    file_path,
                    as_attachment=False,  # 不下载，直接显示
                    download_name=filename,
                    mimetype='application/pdf'
                )
            else:
                return jsonify({
                    'success': False,
                    'message': '交款报表文件不存在'
                }), 404
                
        finally:
            DatabaseService.close_session(session)
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'查看交款报表失败: {str(e)}'}), 500

@end_of_day_bp.route('/<int:eod_id>/print_difference_adjustment_report', methods=['GET'])
@token_required
@has_permission('end_of_day')
def print_difference_adjustment_report(current_user, eod_id):
    """
    打印差额调节报告
    """
    try:
        language = request.args.get('language', 'zh')
        logger.info(f"🌍 差额调节报告请求 - EOD ID: {eod_id}, 语言: {language}, 操作员: {current_user.get('name', '未知')}")
        
        def normalize_language_code(lang_code):
            if lang_code == 'en-US':
                return 'en'
            elif lang_code == 'th-TH':
                return 'th'
            else:
                return 'zh'
        
        language = normalize_language_code(language)
        logger.info(f"🌍 标准化语言代码: {language}")
        
        # 获取EOD信息
        session = DatabaseService.get_session()
        try:
            eod_status = session.query(EODStatus).filter_by(id=eod_id).first()
            if not eod_status:
                logger.error(f"❌ EOD记录不存在: {eod_id}")
                return jsonify({'success': False, 'message': '日结记录不存在'}), 404
            
            logger.info(f"🌍 找到EOD记录: 日期={eod_status.date}, 分支={eod_status.branch_id}")
            
            # 构建文件路径
            year_month = eod_status.date.strftime('%Y/%m')
            date_str = eod_status.date.strftime('%Y%m%d')
            filename_base = f"{date_str}EOD{eod_id:03d}Diff"
            
            # 根据语言选择文件
            if language == 'th':
                filename = f"{filename_base}_th.pdf"
            elif language == 'en':
                filename = f"{filename_base}_en.pdf"
            else:
                filename = f"{filename_base}.pdf"
            
            filepath = os.path.join('manager', year_month, filename)
            logger.info(f"🌍 构建文件路径: {filepath}")
            
            if os.path.exists(filepath):
                logger.info(f"✅ 差额调节报告文件存在: {filepath}")
                formatted_eod_no = f"EOD{eod_id:08d}"
                logger.info(f"🌍 返回格式化EOD编号: {formatted_eod_no}")
                
                return jsonify({
                    'success': True,
                    'message': '差额调节报告获取成功',
                    'eod_no': formatted_eod_no,
                    'filename': filename,
                    'filepath': filepath
                }), 200
            else:
                logger.error(f"❌ 差额调节报告文件不存在: {filepath}")
                return jsonify({'success': False, 'message': '差额调节报告文件不存在'}), 404
                
        finally:
            DatabaseService.close_session(session)
            
    except Exception as e:
        logger.error(f"❌ 获取差额调节报告失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取差额调节报告失败: {str(e)}'}), 500

@end_of_day_bp.route('/<int:eod_id>/print_difference_report', methods=['GET'])
@token_required
@has_permission('end_of_day')
def print_difference_report(current_user, eod_id):
    """
    打印差额报告
    """
    try:
        language = request.args.get('language', 'zh')
        logger.info(f"🌍 差额报告请求 - EOD ID: {eod_id}, 语言: {language}, 操作员: {current_user.get('name', '未知')}")
        
        def normalize_language_code(lang_code):
            if lang_code == 'en-US':
                return 'en'
            elif lang_code == 'th-TH':
                return 'th'
            else:
                return 'zh'
        
        language = normalize_language_code(language)
        logger.info(f"🌍 标准化语言代码: {language}")
        
        # 获取EOD信息
        session = DatabaseService.get_session()
        try:
            eod_status = session.query(EODStatus).filter_by(id=eod_id).first()
            if not eod_status:
                logger.error(f"❌ EOD记录不存在: {eod_id}")
                return jsonify({'success': False, 'message': '日结记录不存在'}), 404
            
            logger.info(f"🌍 找到EOD记录: 日期={eod_status.date}, 分支={eod_status.branch_id}")
            
            # 构建文件路径
            year_month = eod_status.date.strftime('%Y/%m')
            date_str = eod_status.date.strftime('%Y%m%d')
            filename_base = f"{date_str}EOD{eod_id:03d}Diff"
            
            # 根据语言选择文件
            if language == 'th':
                filename = f"{filename_base}_th.pdf"
            elif language == 'en':
                filename = f"{filename_base}_en.pdf"
            else:
                filename = f"{filename_base}.pdf"
            
            filepath = os.path.join('manager', year_month, filename)
            logger.info(f"🌍 构建文件路径: {filepath}")
            
            if os.path.exists(filepath):
                logger.info(f"✅ 差额报告文件存在: {filepath}")
                formatted_eod_no = f"EOD{eod_id:08d}"
                logger.info(f"🌍 返回格式化EOD编号: {formatted_eod_no}")
                
                return jsonify({
                    'success': True,
                    'message': '差额报告获取成功',
                    'eod_no': formatted_eod_no,
                    'filename': filename,
                    'filepath': filepath
                }), 200
            else:
                logger.error(f"❌ 差额报告文件不存在: {filepath}")
                return jsonify({'success': False, 'message': '差额报告文件不存在'}), 404
                
        finally:
            DatabaseService.close_session(session)
            
    except Exception as e:
        logger.error(f"❌ 获取差额报告失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取差额报告失败: {str(e)}'}), 500

@end_of_day_bp.route('/<int:eod_id>/currency/<currency_code>/transactions', methods=['GET'])
@token_required
@has_permission('end_of_day')
@check_eod_session_permission
def get_currency_transactions_detail(current_user, eod_id, currency_code):
    """获取日结理论余额计算中特定币种的详细交易流水"""
    import time
    start_time = time.time()
    
    try:
        session = DatabaseService.get_session()
        
        # 获取日结记录
        eod_status = session.query(EODStatus).filter_by(id=eod_id).first()
        if not eod_status:
            return jsonify({'success': False, 'message': '日结记录不存在'}), 404
        
        # 权限检查：只能查看自己网点的日结
        if eod_status.branch_id != current_user.get('branch_id'):
            return jsonify({'success': False, 'message': '无权访问其他网点的日结数据'}), 403
        
        # 获取币种信息
        currency = session.query(Currency).filter(
            Currency.currency_code == currency_code
        ).first()
        
        if not currency:
            return jsonify({'success': False, 'message': f'币种代码 {currency_code} 不存在'}), 404
        
        # 获取网点信息
        branch = session.query(Branch).filter_by(id=eod_status.branch_id).first()
        if not branch:
            return jsonify({'success': False, 'message': '网点不存在'}), 404
        
        # 获取该币种的理论余额计算数据
        from services.eod_service import EODService
        balance_data = EODService.get_theoretical_balance_data(eod_id)
        
        if not balance_data.get('success'):
            return jsonify({'success': False, 'message': '获取理论余额计算数据失败'}), 500
        
        # 找到该币种的计算数据
        currency_calculation = None
        for calc in balance_data.get('calculations', []):
            if calc.get('currency_code') == currency_code:
                currency_calculation = calc
                break
        
        if not currency_calculation:
            return jsonify({'success': False, 'message': f'未找到币种 {currency_code} 的计算数据'}), 404
        
        # 获取时间范围
        change_start_time = datetime.fromisoformat(currency_calculation['change_start_time'].replace('Z', '+00:00')).replace(tzinfo=None) if currency_calculation.get('change_start_time') else None
        change_end_time = datetime.fromisoformat(currency_calculation['change_end_time'].replace('Z', '+00:00')).replace(tzinfo=None) if currency_calculation.get('change_end_time') else None
        
        if not change_start_time or not change_end_time:
            return jsonify({'success': False, 'message': '时间范围数据不完整'}), 500
        
        # 查询该币种在计算时间范围内的所有交易
        is_base_currency = (branch and branch.base_currency_id == currency.id)
        
        # 【优化】添加分页和限制，提高查询性能
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)  # 默认50条，最多100条
        per_page = min(per_page, 100)  # 限制最大数量
        offset = (page - 1) * per_page
        
        logger.info(f"【明细查询】币种: {currency_code}, 时间范围: {change_start_time} ~ {change_end_time}, 分页: {page}/{per_page}")
        
        if is_base_currency:
            # 本币：查询所有影响本币的交易（优化查询逻辑）
            # 使用UNION查询，避免重复查询和合并
            from sqlalchemy import union_all
            
            # 1. 直接对本币的交易
            direct_query = session.query(ExchangeTransaction).filter(
                ExchangeTransaction.branch_id == eod_status.branch_id,
                ExchangeTransaction.currency_id == currency.id,
                ExchangeTransaction.created_at >= change_start_time,
                ExchangeTransaction.created_at < change_end_time,
                ExchangeTransaction.status.in_(['completed', 'reversed']),
                ExchangeTransaction.type != 'Eod_diff'  # 排除日结差额调节交易
            )
            
            # 2. 所有外币交易对本币的影响
            foreign_query = session.query(ExchangeTransaction).filter(
                ExchangeTransaction.branch_id == eod_status.branch_id,
                ExchangeTransaction.currency_id != currency.id,
                ExchangeTransaction.created_at >= change_start_time,
                ExchangeTransaction.created_at < change_end_time,
                ExchangeTransaction.status.in_(['completed', 'reversed']),
                ExchangeTransaction.type != 'Eod_diff'  # 排除日结差额调节交易
            )
            
            # 合并查询并应用分页
            combined_query = direct_query.union_all(foreign_query).order_by(ExchangeTransaction.created_at.desc())
            all_transactions = combined_query.limit(per_page).offset(offset).all()
            
            logger.info(f"【本币查询】直接交易: {direct_query.count()}, 外币交易: {foreign_query.count()}, 返回: {len(all_transactions)}")
        else:
            # 外币：查询该币种的交易
            all_transactions = session.query(ExchangeTransaction).filter(
                ExchangeTransaction.branch_id == eod_status.branch_id,
                ExchangeTransaction.currency_id == currency.id,
                ExchangeTransaction.created_at >= change_start_time,
                ExchangeTransaction.created_at < change_end_time,
                ExchangeTransaction.status.in_(['completed', 'reversed']),
                ExchangeTransaction.type.in_(['buy', 'sell', 'reversal', 'adjust_balance', 'initial_balance'])  # 包含余额调整和初始余额
            ).order_by(ExchangeTransaction.created_at.desc()).limit(per_page).offset(offset).all()
        
        # 获取总记录数（用于分页）- 优化：避免重复查询
        if is_base_currency:
            # 对于本币，直接使用UNION查询的结果计数
            total_count_query = direct_query.union_all(foreign_query)
            total_count = total_count_query.count()
        else:
            # 对于外币，复用已有的查询条件
            total_count = session.query(ExchangeTransaction).filter(
                ExchangeTransaction.branch_id == eod_status.branch_id,
                ExchangeTransaction.currency_id == currency.id,
                ExchangeTransaction.created_at >= change_start_time,
                ExchangeTransaction.created_at < change_end_time,
                ExchangeTransaction.status.in_(['completed', 'reversed']),
                ExchangeTransaction.type.in_(['buy', 'sell', 'reversal', 'adjust_balance', 'initial_balance'])
            ).count()
        
        # 构建交易详情列表
        logger.info(f"【明细查询结果】币种: {currency_code}, 查询到 {len(all_transactions)} 笔交易, 总计: {total_count} 笔")
        
        transaction_details = []
        for tx in all_transactions:
            # 获取外币信息（如果不是本币交易）
            if tx.currency_id != currency.id:
                foreign_currency = session.query(Currency).filter_by(id=tx.currency_id).first()
                foreign_currency_code = foreign_currency.currency_code if foreign_currency else '外币'
            else:
                foreign_currency_code = currency_code
            
            # 根据交易类型确定描述和金额
            if is_base_currency:
                # 本币：使用local_amount
                amount = float(tx.local_amount)
                # 返回翻译键而不是预翻译的字符串，让前端处理翻译
                if tx.type == 'buy':
                    description = f"eod.step5.buy_transaction {foreign_currency_code} {tx.amount}"
                elif tx.type == 'sell':
                    description = f"eod.step5.sell_transaction {foreign_currency_code} {tx.amount}"
                elif tx.type == 'adjust_balance':
                    description = f"eod.step5.adjust_balance_transaction {foreign_currency_code}"
                elif tx.type == 'reversal':
                    description = f"eod.step5.reversal_transaction {foreign_currency_code} {tx.amount}"
                elif tx.type == 'initial_balance':
                    description = f"eod.step5.opening_balance {foreign_currency_code}"
                else:
                    description = f"eod.step5.other_transaction {foreign_currency_code}"
            else:
                # 外币：使用amount
                amount = round(float(tx.amount), 2) if tx.amount is not None else 0.0
                if tx.type == 'buy':
                    description = f"eod.step5.buy_transaction {foreign_currency_code} {amount}"
                elif tx.type == 'sell':
                    description = f"eod.step5.sell_transaction {foreign_currency_code} {amount}"
                elif tx.type == 'reversal':
                    description = f"eod.step5.reversal_transaction {foreign_currency_code} {amount}"
                elif tx.type == 'adjust_balance':
                    description = f"eod.step5.adjust_balance_transaction {foreign_currency_code}"
                elif tx.type == 'initial_balance':
                    description = f"eod.step5.opening_balance {foreign_currency_code}"
                else:
                    description = f"eod.step5.other_transaction {foreign_currency_code}"
            
            transaction_details.append({
                'id': tx.id,
                'transaction_no': tx.transaction_no,
                'type': tx.type,
                'amount': amount,
                'rate': float(tx.rate) if tx.rate else 1.0,
                'local_amount': round(float(tx.local_amount), 2) if tx.local_amount is not None else 0.0,
                'foreign_amount': round(float(tx.amount), 2) if tx.amount is not None else 0.0,
                'description': description,
                'created_at': tx.created_at.isoformat(),
                'foreign_currency': foreign_currency_code,
                'is_base_currency_transaction': tx.currency_id == currency.id,
                'customer_name': tx.customer_name,
                'memo': tx.remarks or ''
            })
        
        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"⏱️ 【明细查询完成】币种: {currency_code}, 耗时: {execution_time:.2f}秒, 返回: {len(transaction_details)} 笔交易")
        
        return jsonify({
            'success': True,
            'data': {
                'eod_id': eod_id,
                'currency_code': currency_code,
                'currency_name': currency.currency_name,
                'custom_flag_filename': currency.custom_flag_filename,
                'flag_code': currency.flag_code,
                'opening_balance': currency_calculation['opening_balance'],
                'daily_change': currency_calculation['daily_change'],
                'theoretical_balance': currency_calculation['theoretical_balance'],
                'actual_balance': currency_calculation['actual_balance'],
                'difference': currency_calculation['difference'],
                'change_start_time': currency_calculation['change_start_time'],
                'change_end_time': currency_calculation['change_end_time'],
                'transactions': transaction_details,
                'total_transactions': len(transaction_details),
                'is_base_currency': is_base_currency,
                'execution_time': execution_time,
                'pagination': {
                    'current_page': page,
                    'per_page': per_page,
                    'total_count': total_count,
                    'total_pages': (total_count + per_page - 1) // per_page,
                    'has_next': page * per_page < total_count,
                    'has_prev': page > 1
                }
            }
        })
        
    except Exception as e:
        logger.error(f"获取币种交易详情失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取交易详情失败: {str(e)}'}), 500
    
    finally:
        DatabaseService.close_session(session)

@end_of_day_bp.route('/history/<int:eod_id>/difference-pdf/view', methods=['GET'])
def view_eod_difference_pdf(eod_id):
    """
    查看日结差额报告PDF（支持URL参数token和Authorization header）
    """
    try:
        language = request.args.get('language', 'zh')
        
        # 获取token - 优先从URL参数获取，其次从Authorization header获取
        token = request.args.get('token')
        if not token:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header[7:]  # 移除 'Bearer ' 前缀
        
        if not token:
            return jsonify({'success': False, 'message': '缺少访问令牌'}), 401
        
        # 验证token
        try:
            import jwt
            from datetime import datetime
            SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'ExchangeOK-JWT-Secret-Key-2025-Fixed')
            
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            user_id = payload['sub']
            
            # 获取用户信息
            session = DatabaseService.get_session()
            try:
                user = session.query(Operator).filter_by(id=user_id).first()
                if not user:
                    return jsonify({'success': False, 'message': '用户不存在或已禁用'}), 401
                
                current_user = {
                    'id': user.id,
                    'name': user.name,
                    'branch_id': user.branch_id,
                    'role_id': user.role_id
                }
            finally:
                DatabaseService.close_session(session)
                
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': '访问令牌已过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': '无效的访问令牌'}), 401
        
        # 获取EOD信息
        session = DatabaseService.get_session()
        try:
            eod_status = session.query(EODStatus).filter_by(id=eod_id).first()
            if not eod_status:
                return jsonify({'success': False, 'message': '日结记录不存在'}), 404
            
            # 构建文件路径
            year_month = eod_status.date.strftime('%Y/%m')
            date_str = eod_status.date.strftime('%Y%m%d')
            filename_base = f"{date_str}EOD{eod_id:03d}Diff"
            
            # 根据语言选择文件
            if language == 'th':
                filename = f"{filename_base}_th.pdf"
            elif language == 'en':
                filename = f"{filename_base}_en.pdf"
            else:
                filename = f"{filename_base}.pdf"
            
            filepath = os.path.join('manager', year_month, filename)
            
            if os.path.exists(filepath):
                return send_file(filepath, as_attachment=False, mimetype='application/pdf')
            else:
                return jsonify({'success': False, 'message': '差额报告文件不存在'}), 404
                
        finally:
            DatabaseService.close_session(session)
            
    except Exception as e:
        logger.error(f"查看差额报告PDF失败: {str(e)}")
        return jsonify({'success': False, 'message': f'查看差额报告PDF失败: {str(e)}'}), 500



