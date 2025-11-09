import os
import shutil
from datetime import datetime
from flask import current_app, jsonify, url_for
from flask_jwt_extended import jwt_required
from . import logs_blueprint

@logs_blueprint.route('/export', methods=['GET'])
@token_required
def export_logs():
    print("[DEBUG] export_logs函数被调用")  # 确认函数被调用
    try:
        # 获取应用根路径
        app_root = current_app.root_path
        print(f"[DEBUG] 应用根路径: {app_root}")  # 调试信息

        # 确保导出目录存在
        export_dir = os.path.join(app_root, 'exports')
        print(f"[DEBUG] 导出目录: {export_dir}")  # 调试信息

        if not os.path.exists(export_dir):
            print(f"[DEBUG] 创建目录: {export_dir}")
            os.makedirs(export_dir, exist_ok=True)

        # 生成带时间戳的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"system_logs_{timestamp}.log"
        export_path = os.path.join(export_dir, filename)
        print(f"[DEBUG] 导出文件路径: {export_path}")  # 调试信息

        # 复制日志文件到导出目录
        log_file = current_app.config['LOG_FILE']
        print(f"[DEBUG] 源日志文件: {log_file}")  # 调试信息
        shutil.copy2(log_file, export_path)
        print(f"[DEBUG] 文件复制成功到: {export_path}")  # 调试信息

        # 生成下载URL
        download_url = url_for('download_file', filename=filename, _external=True)
        print(f"[DEBUG] 下载URL: {download_url}")  # 调试信息

        return jsonify({
            'success': True,
            'message': '日志导出成功',
            'file_path': export_path,
            'download_url': download_url
        })
    except Exception as e:
        print(f"[ERROR] 导出失败: {str(e)}")  # 错误信息
        return jsonify({'success': False, 'message': f'导出失败: {str(e)}'}), 500 