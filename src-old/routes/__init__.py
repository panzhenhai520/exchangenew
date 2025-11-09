# This file makes the routes directory a Python package

from flask import Flask, send_from_directory

def create_app():
    app = Flask(__name__)
    
    # 添加静态文件路由
    @app.route('/static/<path:filename>')
    def static_files(filename):
        return send_from_directory('static', filename)
    
    # ... 其他配置和蓝图注册 ...
    
    return app
