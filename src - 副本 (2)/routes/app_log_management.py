#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日志管理Web API路由
提供日志统计、清理、下载等功能的Web接口
"""

from flask import Blueprint, jsonify, request, send_file, Response
from flask_cors import cross_origin
import os
import sys
import logging
from datetime import datetime, timedelta
import zipfile
import tempfile
import io

# 添加utils目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.log_manager import LogManager
from config.log_config import LogConfig, LogPresets
from utils.safe_error_handler import safe_error_response
from services.db_service import DatabaseService
from services.auth_service import token_required, has_permission

# 创建蓝图
log_management_bp = Blueprint('log_management', __name__)
logger = logging.getLogger(__name__)

def get_time_ago(timestamp):
    """计算相对时间显示"""
    if not timestamp:
        return '未知时间'
    
    now = datetime.utcnow()
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days}天前"
    elif diff.seconds >= 3600:
        hours = diff.seconds // 3600
        return f"{hours}小时前"
    elif diff.seconds >= 60:
        minutes = diff.seconds // 60
        return f"{minutes}分钟前"
    else:
        return "刚刚"

@log_management_bp.route('/api/log-management/stats', methods=['GET'])
@cross_origin()
def get_log_stats():
    """获取日志统计信息"""
    try:
        log_manager = LogManager(LogConfig.get_log_dir())
        stats = log_manager.get_log_stats()
        
        # 添加配置信息
        config_info = {
            'rotation_max_size_mb': LogConfig.ROTATION_MAX_SIZE_MB,
            'rotation_backup_count': LogConfig.ROTATION_BACKUP_COUNT,
            'cleanup_old_days': LogConfig.CLEANUP_OLD_DAYS,
            'cleanup_large_size_mb': LogConfig.CLEANUP_LARGE_SIZE_MB,
            'compress_old_days': LogConfig.COMPRESS_OLD_DAYS,
            'log_level': LogConfig.LOG_LEVEL,
            'log_dir': LogConfig.get_log_dir(),
            'archive_dir': LogConfig.get_archive_dir()
        }
        
        return jsonify({
            'success': True,
            'data': {
                'stats': stats,
                'config': config_info,
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"获取日志统计失败: {e}")
        return safe_error_response(f"获取日志统计失败: {str(e)}", 500)

@log_management_bp.route('/api/log-management/cleanup', methods=['POST'])
@cross_origin()
def cleanup_logs():
    """执行日志清理"""
    try:
        data = request.get_json() or {}
        
        # 获取清理参数
        clean_old_days = data.get('clean_old_days', LogConfig.CLEANUP_OLD_DAYS)
        clean_large_mb = data.get('clean_large_mb', LogConfig.CLEANUP_LARGE_SIZE_MB)
        compress_days = data.get('compress_days', LogConfig.COMPRESS_OLD_DAYS)
        enable_archive = data.get('enable_archive', True)
        
        log_manager = LogManager(LogConfig.get_log_dir())
        
        # 获取清理前的统计
        stats_before = log_manager.get_log_stats()
        
        results = {
            'cleaned_old': 0,
            'cleaned_large': 0,
            'compressed': 0,
            'archived': 0,
            'space_saved_mb': 0
        }
        
        # 执行清理操作
        if clean_old_days > 0:
            results['cleaned_old'] = log_manager.clean_old_logs(clean_old_days)
        
        if clean_large_mb > 0:
            results['cleaned_large'] = log_manager.clean_large_logs(clean_large_mb)
        
        if compress_days > 0:
            results['compressed'] = log_manager.compress_old_logs(compress_days)
        
        if enable_archive:
            results['archived'] = log_manager.archive_logs()
        
        # 获取清理后的统计
        stats_after = log_manager.get_log_stats()
        results['space_saved_mb'] = round(stats_before['total_size_mb'] - stats_after['total_size_mb'], 2)
        
        logger.info(f"日志清理完成: {results}")
        
        return jsonify({
            'success': True,
            'data': {
                'results': results,
                'stats_before': stats_before,
                'stats_after': stats_after,
                'timestamp': datetime.now().isoformat()
            },
            'message': '日志清理完成'
        })
        
    except Exception as e:
        logger.error(f"日志清理失败: {e}")
        return safe_error_response(f"日志清理失败: {str(e)}", 500)

@log_management_bp.route('/api/log-management/files', methods=['GET'])
@cross_origin()
def get_log_files():
    """获取日志文件列表"""
    try:
        log_manager = LogManager(LogConfig.get_log_dir())
        files = log_manager.get_log_files()
        
        return jsonify({
            'success': True,
            'data': files,
            'message': '获取日志文件列表成功'
        })
        
    except Exception as e:
        logger.error(f"获取日志文件列表失败: {e}")
        return safe_error_response(f"获取日志文件列表失败: {str(e)}", 500)

@log_management_bp.route('/api/log-management/files/<filename>/content', methods=['GET'])
@cross_origin()
def get_log_content(filename):
    """获取日志文件内容"""
    try:
        log_manager = LogManager(LogConfig.get_log_dir())
        content = log_manager.get_log_content(filename)
        
        return jsonify({
            'success': True,
            'data': content,
            'message': '获取日志内容成功'
        })
        
    except Exception as e:
        logger.error(f"获取日志内容失败: {e}")
        return safe_error_response(f"获取日志内容失败: {str(e)}", 500)

@log_management_bp.route('/api/log-management/files/<filename>', methods=['DELETE'])
@cross_origin()
def delete_log_file(filename):
    """删除日志文件"""
    try:
        log_manager = LogManager(LogConfig.get_log_dir())
        result = log_manager.delete_log_file(filename)
        
        return jsonify({
            'success': True,
            'data': result,
            'message': '删除日志文件成功'
        })
        
    except Exception as e:
        logger.error(f"删除日志文件失败: {e}")
        return safe_error_response(f"删除日志文件失败: {str(e)}", 500)

@log_management_bp.route('/api/log-management/archive', methods=['POST'])
@cross_origin()
@token_required
@has_permission('system_manage')
def archive_logs(current_user, *args):
    """归档日志文件"""
    try:
        log_manager = LogManager(LogConfig.get_log_dir())
        result = log_manager.archive_logs(LogConfig.get_archive_dir())
        
        return jsonify({
            'success': True,
            'data': {'archived_count': result},
            'message': '归档日志成功'
        })
        
    except Exception as e:
        logger.error(f"归档日志失败: {e}")
        return safe_error_response(f"归档日志失败: {str(e)}", 500)

@log_management_bp.route('/api/log-management/compress', methods=['POST'])
@cross_origin()
@token_required
@has_permission('system_manage')
def compress_logs(current_user, *args):
    """压缩日志文件"""
    try:
        log_manager = LogManager(LogConfig.get_log_dir())
        result = log_manager.compress_old_logs()
        
        return jsonify({
            'success': True,
            'data': {'compressed_count': result, 'saved_size': '未知'},
            'message': '压缩日志成功'
        })
        
    except Exception as e:
        logger.error(f"压缩日志失败: {e}")
        return safe_error_response(f"压缩日志失败: {str(e)}", 500)

@log_management_bp.route('/api/log-management/export', methods=['GET'])
@cross_origin()
def export_logs():
    """导出日志文件"""
    try:
        # 确保导出目录存在
        export_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'exports')
        if not os.path.exists(export_dir):
            os.makedirs(export_dir, exist_ok=True)
            logger.info(f"创建导出目录: {export_dir}")
        
        # 生成带时间戳的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"system_logs_{timestamp}.log"
        export_path = os.path.join(export_dir, filename)
        
        # 复制当前日志文件到导出目录
        log_file = os.path.join(LogConfig.get_log_dir(), "app.log")
        if os.path.exists(log_file):
            import shutil
            shutil.copy2(log_file, export_path)
            logger.info(f"日志文件已导出到: {export_path}")
        else:
            # 如果app.log不存在，创建一个包含当前日志内容的文件
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write(f"日志导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n")
                # 可以在这里添加其他日志内容
                f.write("系统日志导出完成\n")
        
        # 生成下载URL
        download_url = f"/downloads/{filename}"
        
        return jsonify({
            'success': True,
            'message': '日志导出成功',
            'file_path': export_path,
            'download_url': download_url
        })
        
    except Exception as e:
        logger.error(f"导出日志失败: {e}")
        return safe_error_response(f"导出日志失败: {str(e)}", 500)

@log_management_bp.route('/api/log-management/operations', methods=['GET'])
@cross_origin()
def get_recent_operations():
    """获取最近操作记录"""
    try:
        from services.activity_service import ActivityService
        from datetime import datetime, timedelta
        
        # 记录当前操作
        try:
            # 从token中获取当前用户信息
            from flask import g
            current_user = getattr(g, 'current_user', None)
            
            if current_user:
                ActivityService.log_activity(
                    operator_id=current_user['id'],
                    activity_type='page_view',
                    description='查看系统日志管理页面',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent'),
                    branch_id=current_user.get('branch_id')  # 传递网点ID
                )
            else:
                # 如果没有用户信息，使用默认值但要传递branch_id
                operator_session = DatabaseService.get_session()
                try:
                    from models.exchange_models import Operator
                    operator = operator_session.query(Operator).filter_by(id=1).first()
                    if operator:
                        ActivityService.log_activity(
                            operator_id=1,
                            activity_type='page_view',
                            description='查看系统日志管理页面',
                            ip_address=request.remote_addr,
                            user_agent=request.headers.get('User-Agent'),
                            branch_id=operator.branch_id  # 从操作员记录中获取网点ID
                        )
                finally:
                    DatabaseService.close_session(operator_session)
        except Exception as log_error:
            logger.warning(f"记录操作活动失败: {log_error}")
        
        # 获取查询参数
        limit = request.args.get('limit', 10, type=int)
        hours = request.args.get('hours', 168, type=int)  # 默认获取7天内的记录
        
        # 限制查询范围
        limit = min(limit, 50)  # 最多50条
        hours = min(hours, 720)  # 最多30天
        
        # 计算时间范围
        start_date = datetime.utcnow() - timedelta(hours=hours)
        
        # 获取所有操作员的最近活动记录
        session = DatabaseService.get_session()
        try:
            from models.exchange_models import OperatorActivityLog, Operator, Branch
            from sqlalchemy.orm import joinedload
            from sqlalchemy import desc
            
            # 查询最近的操作记录
            query = session.query(OperatorActivityLog).options(
                joinedload(OperatorActivityLog.operator),
                joinedload(OperatorActivityLog.branch)
            ).filter(
                OperatorActivityLog.created_at >= start_date
            ).order_by(desc(OperatorActivityLog.created_at)).limit(limit)
            
            activities = query.all()
            
            operations = []
            for activity in activities:
                # 格式化操作类型显示名称
                activity_type_map = {
                    'login': '登录系统',
                    'logout': '退出系统', 
                    'action': '执行操作',
                    'page_view': '页面访问',
                    'transaction': '交易操作',
                    'rate_update': '汇率更新',
                    'balance_adjust': '余额调整',
                    'user_manage': '用户管理',
                    'system_config': '系统配置',
                    'report_generate': '报表生成',
                    'end_of_day': '日结操作'
                }
                
                operation_data = {
                    'id': activity.id,
                    'operation_type': activity.activity_type,
                    'operation_name': activity_type_map.get(activity.activity_type, activity.activity_type),
                    'description': activity.activity_description or '无描述',
                    'operator_name': activity.operator.name if activity.operator else '未知操作员',
                    'operator_code': activity.operator.login_code if activity.operator else '未知',
                    'branch_name': activity.branch.branch_name if activity.branch else '未知网点',
                    'ip_address': activity.ip_address or '未知IP',
                    'created_at': activity.created_at.strftime('%Y-%m-%d %H:%M:%S') if activity.created_at else None,
                    'time_ago': get_time_ago(activity.created_at) if activity.created_at else '未知时间'
                }
                operations.append(operation_data)
                
        finally:
            DatabaseService.close_session(session)
        
        return jsonify({
            'success': True,
            'data': operations,
            'message': f'获取最近{len(operations)}条操作记录成功'
        })
        
    except Exception as e:
        logger.error(f"获取最近操作记录失败: {e}")
        return safe_error_response(f"获取最近操作记录失败: {str(e)}", 500)

@log_management_bp.route('/api/log-management/tail/<int:lines>', methods=['GET'])
@cross_origin()
def tail_log(lines=100):
    """获取日志文件的最后几行"""
    try:
        log_file = os.path.join(LogConfig.LOG_DIR, 'app.log')
        
        if not os.path.exists(log_file):
            return safe_error_response("日志文件不存在", 404)
        
        # 限制行数范围
        lines = max(1, min(lines, 1000))
        
        with open(log_file, 'r', encoding='utf-8') as f:
            # 读取最后几行
            file_lines = f.readlines()
            tail_lines = file_lines[-lines:] if len(file_lines) > lines else file_lines
        
        return jsonify({
            'success': True,
            'data': {
                'lines': [line.rstrip() for line in tail_lines],
                'total_lines': len(file_lines),
                'requested_lines': lines,
                'returned_lines': len(tail_lines),
                'file_size_mb': round(os.path.getsize(log_file) / (1024 * 1024), 2)
            }
        })
        
    except Exception as e:
        logger.error(f"读取日志文件失败: {e}")
        return safe_error_response(f"读取日志文件失败: {str(e)}", 500)

@log_management_bp.route('/api/log-management/page-access', methods=['POST'])
@cross_origin()
def record_page_access():
    """记录页面访问日志"""
    try:
        from services.activity_service import ActivityService
        from flask import g
        
        data = request.get_json() or {}
        page_name = data.get('page_name', '未知页面')
        page_path = data.get('page_path', '/')
        from_path = data.get('from_path', '直接访问')
        
        # 获取当前用户信息
        current_user = getattr(g, 'current_user', None)
        
        if current_user:
            # 记录页面访问日志
            ActivityService.log_activity(
                operator_id=current_user['id'],
                activity_type='page_view',
                description=f'访问页面: {page_name} (从 {from_path} -> {page_path})',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                branch_id=current_user.get('branch_id')
            )
            
            return jsonify({
                'success': True,
                'message': '页面访问记录成功'
            })
        else:
            # 用户未登录时静默处理，不返回错误，避免影响页面加载
            # logger.debug(f"页面访问记录跳过 - 用户未登录: {page_name}")
            return jsonify({
                'success': True,
                'message': '页面访问记录跳过'
            })
            
    except Exception as e:
        logger.error(f"记录页面访问失败: {e}")
        return safe_error_response(f"记录页面访问失败: {str(e)}", 500) 

@log_management_bp.route('/api/log-management/check-locks', methods=['GET'])
@cross_origin()
def check_log_locks():
    """检查日志文件占用情况"""
    try:
        from scripts.check_log_locks import check_log_file_locks
        
        # 检查日志文件占用情况
        has_locks = check_log_file_locks()
        
        return jsonify({
            'success': True,
            'data': {
                'has_locks': has_locks,
                'timestamp': datetime.now().isoformat()
            },
            'message': '日志文件占用检查完成'
        })
        
    except Exception as e:
        logger.error(f"检查日志文件占用失败: {e}")
        return safe_error_response(f"检查日志文件占用失败: {str(e)}", 500)

@log_management_bp.route('/api/log-management/restart', methods=['POST'])
@cross_origin()
def restart_logging_system():
    """重启日志系统"""
    try:
        from scripts.check_log_locks import restart_logging_system
        
        # 重启日志系统
        success = restart_logging_system()
        
        return jsonify({
            'success': success,
            'data': {
                'restarted': success,
                'timestamp': datetime.now().isoformat()
            },
            'message': '日志系统重启完成' if success else '日志系统重启失败'
        })
        
    except Exception as e:
        logger.error(f"重启日志系统失败: {e}")
        return safe_error_response(f"重启日志系统失败: {str(e)}", 500) 