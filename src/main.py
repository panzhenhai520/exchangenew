import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 加载.env文件 - 必须在最开始加载
from dotenv import load_dotenv
import json
from datetime import datetime as dt_datetime

# 加载项目根目录的.env文件
project_root = os.path.dirname(os.path.dirname(__file__))
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path)
print(f"[ENV] 加载环境配置文件: {dotenv_path}")

# 自动同步环境配置到所有配置文件
def auto_sync_environment():
    """自动同步.env到所有配置文件（.env.local, environment_config.json, env-config.js）"""
    try:
        current_ip = os.getenv('CURRENT_IP', 'localhost')
        backend_port = os.getenv('BACKEND_PORT', '5001')
        frontend_port = os.getenv('FRONTEND_PORT', '8080')
        backend_url = os.getenv('BACKEND_URL', f'http://{current_ip}:{backend_port}')
        frontend_url = os.getenv('FRONTEND_URL', f'http://{current_ip}:{frontend_port}')

        print(f"[ENV] CURRENT_IP: {current_ip}")
        print(f"[ENV] BACKEND_URL: {backend_url}")
        print(f"[ENV] FRONTEND_URL: {frontend_url}")

        # 1. 更新 .env.local
        env_local_path = os.path.join(project_root, '.env.local')
        env_local_content = f"""VUE_APP_API_BASE_URL={backend_url}
VUE_APP_CURRENT_IP={current_ip}
VUE_APP_BACKEND_PORT={backend_port}
VUE_APP_FRONTEND_PORT={frontend_port}
"""
        with open(env_local_path, 'w', encoding='utf-8') as f:
            f.write(env_local_content)
        print(f"[ENV] ✓ .env.local 已同步")

        # 2. 更新 environment_config.json
        config_path = os.path.join(project_root, 'environment_config.json')
        config_data = {
            "current_ip": current_ip,
            "backend_url": backend_url,
            "frontend_url": frontend_url,
            "backend_port": int(backend_port),
            "frontend_port": int(frontend_port),
            "generated_at": dt_datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "cors_origins": [
                "http://localhost:\\d+",
                "http://127\\.0\\.0\\.1:\\d+",
                f"http://{current_ip}:8080",
                f"http://{current_ip}:5001",
                "null",
                f"http://{current_ip}:3000",
                f"http://{current_ip}:8081",
                f"http://{current_ip}:8082",
                f"http://{current_ip}:8083",
                f"http://{current_ip}:5173"
            ]
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        print(f"[ENV] ✓ environment_config.json 已同步")

        # 3. 更新 src/static/env-config.js
        env_config_js = f"""// Auto-generated runtime config - {dt_datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
window.ENV_CONFIG = {{
  API_BASE_URL: '{backend_url}',
  CURRENT_IP: '{current_ip}',
  BACKEND_PORT: {backend_port},
  FRONTEND_PORT: {frontend_port}
}};
"""
        static_dir = os.path.join(project_root, 'src', 'static')
        os.makedirs(static_dir, exist_ok=True)
        env_config_path = os.path.join(static_dir, 'env-config.js')
        with open(env_config_path, 'w', encoding='utf-8') as f:
            f.write(env_config_js)
        print(f"[ENV] ✓ src/static/env-config.js 已同步")

        print(f"[ENV] 所有配置文件已自动同步！")
        return True
    except Exception as e:
        print(f"[ENV] ⚠️  配置同步失败: {e}")
        return False

# 启动时自动同步环境配置
auto_sync_environment()

from flask import Flask, jsonify, request, send_from_directory, render_template_string, make_response
from flask_cors import CORS
import logging
from datetime import datetime
from utils.safe_error_handler import safe_error_response
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from config.log_config import LogConfig

# Import blueprints
# 然后将相对导入改为从exchange_system开始的导入
from routes.app_rates import rates_bp
from routes.app_end_of_day import end_of_day_bp
from routes.app_query_transactions import transactions_bp
from routes.app_query_balances import balances_bp  # 保留blueprint定义
# operators_bp 已删除，功能合并到 user_bp
from routes.app_roles import roles_bp
from routes.app_auth import auth_bp
from routes.app_dashboard import dashboard_bp
from routes.app_system import system_bp
from routes.app_exchange import exchange_bp
from routes.app_currencies import currencies_bp
from routes.app_balance import balance_bp
from routes.app_reversal_query import reversal_query_bp
from routes.app_balance_adjust_query import balance_adjust_query_bp
from routes.app_user_management import user_bp
from routes.app_user_management import perm_bp
from routes.app_profile import profile_bp

from routes.app_print_settings import print_settings_bp
from routes.app_log_management import log_management_bp
from routes.app_currency_management import currency_management_bp
from routes.app_standards_management import standards_management_bp
from routes.app_purpose_limits import purpose_limits_bp
from routes.app_income_query import income_query_bp
from routes.app_foreign_stock_query import foreign_stock_query_bp
from routes.app_local_stock_query import local_stock_bp
from routes.app_transaction_alerts import transaction_alerts_bp
from routes.app_operating_status import operating_status_bp
from routes.app_reports import reports_bp
from routes.app_eod_step import eod_step_bp
from routes.app_eod_migration import eod_migration_bp
from routes.app_dual_direction_migration import dual_direction_migration_bp
from routes.app_receipt_migration import receipt_migration_bp
from routes.app_feature_flags import app_feature_flags
from routes.app_denominations import denomination_bp
from routes.app_denominations_api import denominations_api_bp
from routes.batch_publish_api import batch_publish_bp
from routes.batch_display_api import batch_display_bp
from routes.app_repform import app_repform
from routes.app_amlo import app_amlo
from routes.app_bot import app_bot
from routes.app_report_numbers import report_number_bp
from routes.app_compliance import app_compliance

# Import services and models
from services.db_service import DatabaseService, shutdown_session
from services.auth_service import token_required, has_permission
from models.exchange_models import Currency
# 导入所有模型以确保SQLAlchemy可以找到它们
from models import denomination_models, report_models
from init_db import init_database

# Configure logging with rotation
# 确保日志目录存在
LogConfig.ensure_directories()

# 检查环境变量决定日志模式
import os
if os.getenv('LOG_MODE') == 'production':
    LogConfig.enable_production_mode()
    print("Production mode enabled")
else:
    LogConfig.enable_debug_mode()
    print("Debug mode enabled")

# 导入安全的日志处理器
from utils.safe_log_handler import create_safe_file_handler

# 创建安全的文件处理器 - 避免Windows文件锁定问题
try:
    file_handler = create_safe_file_handler(
        log_dir=LogConfig.LOG_DIR,
        filename="app.log",
        handler_type="timed",
        when='midnight',
        interval=1,
        backupCount=LogConfig.ROTATION_BACKUP_COUNT,
        encoding='utf-8',
        delay=True
    )
    
    if file_handler is None:
        print("警告: 无法创建安全的日志文件处理器，将使用控制台日志记录")
        
except Exception as e:
    print(f"警告: 无法创建日志文件处理器: {e}")
    print("将使用控制台日志记录")
    file_handler = None

# 创建控制台处理器
console_handler = logging.StreamHandler()

# 设置日志格式 - 文件和控制台使用不同格式
file_config = LogConfig.get_file_format_config()
console_config = LogConfig.get_console_format_config()

file_formatter = logging.Formatter(
    file_config['format'],
    datefmt=file_config['datefmt']
)
console_formatter = logging.Formatter(
    console_config['format'],
    datefmt=console_config['datefmt']
)



# 配置根日志记录器
root_logger = logging.getLogger()
root_logger.setLevel(getattr(logging, LogConfig.LOG_LEVEL))

# 只在文件处理器可用时添加
if file_handler:
    root_logger.addHandler(file_handler)
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(getattr(logging, file_config['level']))

root_logger.addHandler(console_handler)
console_handler.setFormatter(console_formatter)
console_handler.setLevel(getattr(logging, console_config['level']))

# 设置第三方库日志为静默模式
LogConfig.setup_quiet_logging()

logger = logging.getLogger(__name__)

# 导入多语言日志服务
from utils.multilingual_log_service import multilingual_logger

# 调试页面HTML模板
DEBUG_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>打印凭证API调试器</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .debug-section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .debug-section h3 { margin-top: 0; color: #333; }
        .status { padding: 10px; margin: 10px 0; border-radius: 3px; }
        .success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .warning { background-color: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
        .info { background-color: #d1ecf1; color: #0c5460; border: 1px solid #b6d4d9; }
        button { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin: 5px; }
        button:hover { background: #0056b3; }
        button:disabled { background: #6c757d; cursor: not-allowed; }
        pre { background: #f8f9fa; padding: 10px; border-radius: 3px; overflow-x: auto; max-height: 300px; }
        input, select { padding: 8px; margin: 5px; border: 1px solid #ddd; border-radius: 3px; }
        .loading { color: #007bff; }
    </style>
</head>
<body>
    <h1>🔍 打印凭证API调试器</h1>
    
    <div class="debug-section">
        <h3>1. 检查本地存储状态</h3>
        <button onclick="checkLocalStorage()">检查Token和用户信息</button>
        <div id="localStorage-result"></div>
    </div>

    <div class="debug-section">
        <h3>2. 测试认证状态</h3>
        <button onclick="testAuth()">测试当前认证状态</button>
        <div id="auth-result"></div>
    </div>

    <div class="debug-section">
        <h3>3. 测试打印凭证API</h3>
        <label>交易ID: <input type="number" id="transactionId" value="1" min="1"></label>
        <button onclick="testPrintReceipt()">测试打印凭证API</button>
        <div id="print-result"></div>
    </div>

    <div class="debug-section">
        <h3>4. 检查用户权限</h3>
        <button onclick="checkPermissions()">检查用户权限</button>
        <div id="permissions-result"></div>
    </div>

    <div class="debug-section">
        <h3>5. 模拟登录获取新Token</h3>
        <div>
            <label>登录代码: <input type="text" id="loginCode" value="admin" placeholder="输入登录代码"></label><br>
            <label>密码: <input type="password" id="password" value="admin123" placeholder="输入密码"></label><br>
            <label>网点ID: <input type="number" id="branchId" value="1" min="1" placeholder="输入网点ID"></label><br>
            <button onclick="testLogin()">测试登录</button>
        </div>
        <div id="login-result"></div>
    </div>

    <script>
        // 使用fetch API创建类似axios的接口
        class ApiClient {
            constructor(baseURL) {
                this.baseURL = baseURL;
            }

            async request(url, options = {}) {
                const token = localStorage.getItem('token');
                console.log('🔍 API请求:', url);
                console.log('🔑 Token:', token ? token.substring(0, 50) + '...' : 'null');
                
                const headers = {
                    'Content-Type': 'application/json',
                    ...options.headers
                };

                if (token) {
                    const authToken = token.startsWith('Bearer ') ? token : `Bearer ${token}`;
                    headers.Authorization = authToken;
                    console.log('✅ 已添加认证头');
                } else {
                    console.log('⚠️ 本地存储中未找到token');
                }

                try {
                    const response = await fetch(this.baseURL + url, {
                        ...options,
                        headers
                    });

                    console.log('✅ API响应:', url, response.status);

                    let data;
                    const contentType = response.headers.get('content-type');
                    if (contentType && contentType.includes('application/json')) {
                        data = await response.json();
                    } else {
                        data = await response.text();
                    }

                    if (!response.ok) {
                        console.error('❌ API错误:', url, response.status, data);
                        const error = new Error(`HTTP ${response.status}`);
                        error.response = { status: response.status, data };
                        throw error;
                    }

                    return { data };
                } catch (error) {
                    console.error('❌ API请求失败:', error);
                    throw error;
                }
            }

            async get(url) {
                return this.request(url, { method: 'GET' });
            }

            async post(url, data) {
                return this.request(url, {
                    method: 'POST',
                    body: JSON.stringify(data)
                });
            }
        }

        // 创建API客户端实例
        const api = new ApiClient('/api');

        function showResult(elementId, content, type = 'info') {
            const element = document.getElementById(elementId);
            element.innerHTML = `<div class="status ${type}">${content}</div>`;
        }

        function checkLocalStorage() {
            const token = localStorage.getItem('token');
            const user = localStorage.getItem('user');
            
            let result = '<h4>本地存储检查结果：</h4>';
            
            if (token) {
                result += `<div class="success">✅ Token存在: ${token.substring(0, 50)}...</div>`;
                
                // 尝试解析token
                try {
                    const payload = JSON.parse(atob(token.split('.')[1]));
                    const exp = new Date(payload.exp * 1000);
                    const now = new Date();
                    
                    if (exp > now) {
                        result += `<div class="success">✅ Token未过期 (过期时间: ${exp.toLocaleString()})</div>`;
                    } else {
                        result += `<div class="error">❌ Token已过期 (过期时间: ${exp.toLocaleString()})</div>`;
                    }
                } catch (e) {
                    result += `<div class="warning">⚠️ 无法解析Token: ${e.message}</div>`;
                }
            } else {
                result += '<div class="error">❌ Token不存在</div>';
            }
            
            if (user) {
                try {
                    const userObj = JSON.parse(user);
                    result += `<div class="success">✅ 用户信息存在: ${userObj.name || '未知'} (ID: ${userObj.id})</div>`;
                    result += `<pre>${JSON.stringify(userObj, null, 2)}</pre>`;
                } catch (e) {
                    result += `<div class="error">❌ 用户信息格式错误: ${e.message}</div>`;
                }
            } else {
                result += '<div class="error">❌ 用户信息不存在</div>';
            }
            
            showResult('localStorage-result', result);
        }

        async function testAuth() {
            try {
                showResult('auth-result', '🔄 正在测试认证状态...', 'info');
                
                // 使用一个需要认证的简单接口测试
                const response = await api.get('/dashboard/stats');
                
                showResult('auth-result', 
                    `<h4>认证测试成功：</h4>
                    <div class="success">✅ 认证状态正常</div>
                    <pre>${JSON.stringify(response.data, null, 2)}</pre>`, 
                    'success'
                );
            } catch (error) {
                let errorMsg = '<h4>认证测试失败：</h4>';
                
                if (error.response?.status === 401) {
                    errorMsg += '<div class="error">❌ 认证失败 (401) - Token无效或已过期</div>';
                } else if (error.response?.status === 403) {
                    errorMsg += '<div class="error">❌ 权限不足 (403)</div>';
                } else {
                    errorMsg += `<div class="error">❌ 请求失败: ${error.message}</div>`;
                }
                
                if (error.response?.data) {
                    errorMsg += `<pre>${JSON.stringify(error.response.data, null, 2)}</pre>`;
                }
                
                showResult('auth-result', errorMsg, 'error');
            }
        }

        async function testPrintReceipt() {
            const transactionId = document.getElementById('transactionId').value;
            
            if (!transactionId) {
                showResult('print-result', '<div class="error">❌ 请输入交易ID</div>', 'error');
                return;
            }
            
            try {
                showResult('print-result', '🔄 正在测试打印凭证API...', 'info');
                
                const response = await api.post(`/exchange/transactions/${transactionId}/print-receipt`, {});
                
                showResult('print-result', 
                    `<h4>打印凭证API测试成功：</h4>
                    <div class="success">✅ API调用成功</div>
                    <pre>${JSON.stringify(response.data, null, 2)}</pre>`, 
                    'success'
                );
            } catch (error) {
                let errorMsg = '<h4>打印凭证API测试失败：</h4>';
                
                if (error.response?.status === 401) {
                    errorMsg += '<div class="error">❌ 认证失败 (401) - 这就是导致跳转登录页面的原因！</div>';
                } else if (error.response?.status === 403) {
                    errorMsg += '<div class="error">❌ 权限不足 (403) - 缺少transaction_execute权限</div>';
                } else if (error.response?.status === 404) {
                    errorMsg += '<div class="error">❌ 交易记录不存在 (404)</div>';
                } else {
                    errorMsg += `<div class="error">❌ 请求失败: ${error.message}</div>`;
                }
                
                if (error.response?.data) {
                    errorMsg += `<pre>${JSON.stringify(error.response.data, null, 2)}</pre>`;
                }
                
                showResult('print-result', errorMsg, 'error');
            }
        }

        async function checkPermissions() {
            try {
                showResult('permissions-result', '🔄 正在检查用户权限...', 'info');
                
                const user = localStorage.getItem('user');
                if (!user) {
                    showResult('permissions-result', '<div class="error">❌ 本地存储中未找到用户信息</div>', 'error');
                    return;
                }
                
                const userObj = JSON.parse(user);
                let result = '<h4>用户权限检查：</h4>';
                
                // 检查是否有所需权限
                const requiredPermission = 'transaction_execute';
                
                if (userObj.permissions && Array.isArray(userObj.permissions)) {
                    if (userObj.permissions.includes(requiredPermission)) {
                        result += `<div class="success">✅ 用户拥有${requiredPermission}权限</div>`;
                    } else {
                        result += `<div class="error">❌ 用户缺少${requiredPermission}权限</div>`;
                    }
                    
                    result += `<div class="info">用户所有权限: ${userObj.permissions.join(', ')}</div>`;
                } else {
                    result += '<div class="warning">⚠️ 用户信息中未找到权限列表</div>';
                }
                
                result += `<pre>${JSON.stringify(userObj, null, 2)}</pre>`;
                
                showResult('permissions-result', result);
            } catch (error) {
                showResult('permissions-result', 
                    `<div class="error">❌ 检查权限时出错: ${error.message}</div>`, 
                    'error'
                );
            }
        }

        async function testLogin() {
            const loginCode = document.getElementById('loginCode').value;
            const password = document.getElementById('password').value;
            const branchId = document.getElementById('branchId').value;
            
            if (!loginCode || !password || !branchId) {
                showResult('login-result', '<div class="error">❌ 请填写完整的登录信息</div>', 'error');
                return;
            }
            
            try {
                showResult('login-result', '🔄 正在尝试登录...', 'info');
                
                const response = await api.post('/auth/login', {
                    login_code: loginCode,
                    password: password,
                    branch: parseInt(branchId)
                });
                
                if (response.data.success) {
                    // 保存新的token和用户信息
                    localStorage.setItem('token', response.data.token);
                    localStorage.setItem('user', JSON.stringify(response.data.user));
                    
                    showResult('login-result', 
                        `<h4>登录成功：</h4>
                        <div class="success">✅ 获取到新的Token和用户信息</div>
                        <div class="info">现在可以重新测试打印凭证API</div>
                        <pre>${JSON.stringify(response.data, null, 2)}</pre>`, 
                        'success'
                    );
                } else {
                    showResult('login-result', 
                        `<div class="error">❌ 登录失败: ${response.data.message}</div>`, 
                        'error'
                    );
                }
            } catch (error) {
                let errorMsg = '<h4>登录测试失败：</h4>';
                
                if (error.response?.status === 401) {
                    errorMsg += '<div class="error">❌ 用户名或密码错误</div>';
                } else if (error.response?.status === 403) {
                    errorMsg += '<div class="error">❌ 用户已停用或网点权限不足</div>';
                } else {
                    errorMsg += `<div class="error">❌ 登录失败: ${error.message}</div>`;
                }
                
                if (error.response?.data) {
                    errorMsg += `<pre>${JSON.stringify(error.response.data, null, 2)}</pre>`;
                }
                
                showResult('login-result', errorMsg, 'error');
            }
        }

        // 页面加载时自动检查本地存储
        window.addEventListener('load', function() {
            console.log('🚀 调试页面已加载');
            checkLocalStorage();
        });
    </script>
</body>
</html>"""

def create_app():
    app = Flask(__name__)
    
    # Configure Flask secret key for session management
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'exchange-ok-secret-key-2025-dev-mode')
    
    # Configure CORS - 从环境变量读取配置
    current_ip = os.getenv('CURRENT_IP', 'localhost')
    frontend_port = os.getenv('FRONTEND_PORT', '8080')
    backend_port = os.getenv('BACKEND_PORT', '5001')
    
    # 构建CORS允许的源列表
    cors_origins = [
        r"http://localhost:\d+",  # 本地开发
        r"http://127\.0\.0\.1:\d+",  # 本地开发
        f"http://{current_ip}:{frontend_port}",  # 前端地址
        f"http://{current_ip}:{backend_port}",  # 后端地址
        "null"  # 文件协议
    ]
    
    print(f"[CORS] 当前IP: {current_ip}")
    print(f"[CORS] 前端端口: {frontend_port}")
    print(f"[CORS] 后端端口: {backend_port}")
    print(f"[CORS] 允许的源: {cors_origins}")

    CORS(app,
         origins=cors_origins,
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
         allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin", "Access-Control-Request-Method", "Access-Control-Request-Headers", "Cache-Control", "X-Language"],
         supports_credentials=True,
         expose_headers=["Content-Type", "Authorization", "Access-Control-Allow-Origin"]
    )
    
    # 添加全局OPTIONS处理
    @app.before_request
    def handle_preflight():
        # 添加请求日志
        print(f"\n========== [Flask] 收到请求 ==========", flush=True)
        print(f"[Flask] {request.method} {request.path}", flush=True)
        print(f"[Flask] Remote: {request.remote_addr}", flush=True)
        print(f"[Flask] Headers: {dict(request.headers)}", flush=True)

        if request.method == "OPTIONS":
            print(f"[Flask] OPTIONS预检请求，返回CORS头", flush=True)
            response = make_response()
            origin = request.headers.get('Origin')

            # 允许来自配置IP的请求
            response.headers["Access-Control-Allow-Origin"] = origin if origin else "*"
            response.headers["Access-Control-Allow-Methods"] = "GET,PUT,POST,DELETE,OPTIONS,PATCH"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization,X-Requested-With,Accept,Origin,Access-Control-Request-Method,Access-Control-Request-Headers,Cache-Control,X-Language"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Max-Age"] = "86400"
            return response
    
    # 添加全局响应处理器，确保所有响应都包含CORS头
    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get('Origin')
        if origin:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET,PUT,POST,DELETE,OPTIONS,PATCH"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization,X-Requested-With,Accept,Origin,Access-Control-Request-Method,Access-Control-Request-Headers,Cache-Control,X-Language"
        return response
    
    # Register blueprints with /api prefix
    app.register_blueprint(rates_bp)  # 已经包含 /api 前缀
    app.register_blueprint(end_of_day_bp)  # 已经包含 /api 前缀
    app.register_blueprint(transactions_bp)  # Already has /api prefix
    app.register_blueprint(balances_bp)  # 保留blueprint注册
    # operators_bp 已删除，功能合并到 user_bp
    app.register_blueprint(roles_bp)  # Already has /api prefix
    app.register_blueprint(auth_bp)  # 已经包含 /api 前缀
    app.register_blueprint(dashboard_bp)  # 已经包含 /api 前缀
    app.register_blueprint(system_bp)  # 已经包含 /api 前缀
    app.register_blueprint(exchange_bp)  # 已经包含 /api 前缀
    app.register_blueprint(currencies_bp)  # 已经包含 /api 前缀
    app.register_blueprint(balance_bp)  # 已经包含 /api 前缀
    app.register_blueprint(reversal_query_bp)  # 已经包含 /api 前缀
    app.register_blueprint(balance_adjust_query_bp)  # 已经包含 /api 前缀
    app.register_blueprint(user_bp)  # 用户管理蓝图，已经包含 /api 前缀
    app.register_blueprint(perm_bp)  # 权限管理蓝图，已经包含 /api 前缀
    app.register_blueprint(profile_bp)  # 个人信息蓝图，已经包含 /api 前缀
    app.register_blueprint(print_settings_bp)  # 新增：打印设置蓝图
    app.register_blueprint(log_management_bp)  # 新增：日志管理蓝图
    app.register_blueprint(currency_management_bp)  # 币种管理蓝图
    app.register_blueprint(standards_management_bp)  # 规范管理蓝图
    app.register_blueprint(purpose_limits_bp)  # 交易用途限额蓝图
    app.register_blueprint(income_query_bp)  # 动态收入查询蓝图
    app.register_blueprint(foreign_stock_query_bp)  # 库存外币查询蓝图
    app.register_blueprint(local_stock_bp)  # 本币库存查询蓝图
    app.register_blueprint(transaction_alerts_bp)  # 交易报警事件蓝图
    app.register_blueprint(operating_status_bp)  # 营业状态管理蓝图
    app.register_blueprint(reports_bp)  # 报表查询蓝图
    app.register_blueprint(eod_step_bp)  # 日结步骤管理蓝图
    app.register_blueprint(eod_migration_bp)  # EOD迁移管理蓝图
    app.register_blueprint(dual_direction_migration_bp)  # 双向交易迁移管理蓝图
    app.register_blueprint(receipt_migration_bp)  # 收据增强迁移管理蓝图
    app.register_blueprint(app_feature_flags, url_prefix='/api')  # 特性开关管理蓝图
    app.register_blueprint(denomination_bp)  # 面值管理蓝图
    app.register_blueprint(denominations_api_bp)  # 面值汇率API蓝图
    app.register_blueprint(batch_publish_bp)  # 批次发布API蓝图
    app.register_blueprint(batch_display_bp)  # 批次显示API蓝图
    app.register_blueprint(app_repform)  # RepForm核心API蓝图
    app.register_blueprint(app_amlo)  # AMLO审核API蓝图
    app.register_blueprint(app_bot)  # BOT报告API蓝图
    app.register_blueprint(report_number_bp)  # 报告编号管理API蓝图
    app.register_blueprint(app_compliance)  # 合规配置API蓝图

    # Register teardown function to cleanup database sessions
    app.teardown_appcontext(shutdown_session)
    
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

    # 添加调试页面路由
    @app.route('/debug_print_receipt.html', methods=['GET'])
    def debug_print_receipt():
        """调试打印凭证页面"""
        return render_template_string(DEBUG_PAGE_TEMPLATE)

    @app.route('/check_permissions.html', methods=['GET'])
    def check_permissions():
        """权限查看页面"""
        try:
            with open('templates/check_permissions.html', 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return "权限查看页面未找到", 404

    @app.route('/Show.html', methods=['GET'])
    def show_rates_display():
        """机顶盒汇率展示页面"""
        try:
            # 从static目录读取Show.html文件
            show_html_path = os.path.join(os.path.dirname(__file__), 'static', 'Show.html')
            print(f"[机顶盒页面] 尝试读取文件: {show_html_path}")
            print(f"[机顶盒页面] 文件存在: {os.path.exists(show_html_path)}")
            
            with open(show_html_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"[机顶盒页面] 文件读取成功，长度: {len(content)} 字符")
                return content
        except FileNotFoundError:
            print(f"[机顶盒页面] 文件未找到: {show_html_path}")
            return "汇率展示页面未找到", 404
        except Exception as e:
            print(f"[机顶盒页面] 读取文件异常: {e}")
            return f"读取页面失败: {str(e)}", 500

    # 添加静态文件路由，用于提供receipts目录下的PDF文件
    @app.route('/static/receipts/<path:filename>')
    def serve_receipt_files(filename):
        """提供receipts目录下的PDF文件"""
        try:
            receipts_dir = os.path.join(os.path.dirname(__file__), 'receipts')
            logger.info(f"尝试访问文件: {filename}, 目录: {receipts_dir}")
            
            # 确保文件路径安全，防止目录遍历攻击
            if '..' in filename or filename.startswith('/'):
                logger.warning(f"不安全的文件路径: {filename}")
                return jsonify({"success": False, "message": "文件路径不合法"}), 400
            
            full_path = os.path.join(receipts_dir, filename)
            if not os.path.exists(full_path):
                logger.warning(f"文件不存在: {full_path}")
                return jsonify({"success": False, "message": "文件不存在"}), 404
            
            # 只允许PDF文件
            if not filename.lower().endswith('.pdf'):
                logger.warning(f"不支持的文件类型: {filename}")
                return jsonify({"success": False, "message": "不支持的文件类型"}), 400
            
            return send_from_directory(receipts_dir, filename, mimetype='application/pdf')
        except Exception as e:
            logger.error(f"提供文件失败: {e}")
            return jsonify({"success": False, "message": "文件访问失败"}), 500

    # 添加国旗图标文件路由
    @app.route('/flags/<filename>')
    def serve_flag_files(filename):
        """提供国旗图标文件"""
        try:
            # 优先使用src/public/flags（自定义图标目录）
            current_file_dir = os.path.dirname(os.path.abspath(__file__))  # src目录
            project_root = os.path.dirname(current_file_dir)  # 项目根目录
            src_flags_dir = os.path.join(current_file_dir, 'public', 'flags')
            public_flags_dir = os.path.join(project_root, 'public', 'flags')
            
            # 优先查找src/public/flags（自定义图标）
            if os.path.exists(os.path.join(src_flags_dir, filename)):
                public_flags_dir = src_flags_dir
            # 如果src/public/flags中没有，查找项目根目录的public/flags（标准图标）
            elif os.path.exists(os.path.join(public_flags_dir, filename)):
                pass  # 使用默认的public_flags_dir
            else:
                logger.warning(f"文件不存在: {filename}")
            
            # 确保文件路径安全
            if '..' in filename or filename.startswith('/'):
                logger.warning(f"不安全的文件路径: {filename}")
                return jsonify({"success": False, "message": "文件路径不合法"}), 400
            
            # 检查文件是否存在
            full_path = os.path.join(public_flags_dir, filename)
            
            if os.path.exists(full_path):
                # 根据文件扩展名设置正确的MIME类型
                if filename.endswith('.svg'):
                    mimetype = 'image/svg+xml'
                elif filename.endswith('.png'):
                    mimetype = 'image/png'
                elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
                    mimetype = 'image/jpeg'
                else:
                    mimetype = 'image/svg+xml'  # 默认
                
                return send_from_directory(public_flags_dir, filename, mimetype=mimetype)
            
            # 如果找不到，返回默认图标
            logger.warning(f"国旗文件不存在: {filename}")
            return jsonify({"success": False, "message": "文件不存在"}), 404
            
        except Exception as e:
            logger.error(f"提供国旗文件失败: {e}")
            return jsonify({"success": False, "message": "文件访问失败"}), 500

    # 添加图片文件路由
    @app.route('/images/<filename>')
    def serve_image_files(filename):
        """提供图片文件"""
        try:
            # 优先使用src/public/images（自定义图片目录）
            current_file_dir = os.path.dirname(os.path.abspath(__file__))  # src目录
            project_root = os.path.dirname(current_file_dir)  # 项目根目录
            src_images_dir = os.path.join(current_file_dir, 'public', 'images')
            public_images_dir = os.path.join(project_root, 'public', 'images')
            
            # 优先查找src/public/images（自定义图片）
            if os.path.exists(os.path.join(src_images_dir, filename)):
                public_images_dir = src_images_dir
            # 如果src/public/images中没有，查找项目根目录的public/images（标准图片）
            elif os.path.exists(os.path.join(public_images_dir, filename)):
                pass  # 使用默认的public_images_dir
            else:
                logger.warning(f"图片文件不存在: {filename}")
            
            # 确保文件路径安全
            if '..' in filename or filename.startswith('/'):
                logger.warning(f"不安全的文件路径: {filename}")
                return jsonify({"success": False, "message": "文件路径不合法"}), 400
            
            # 检查文件是否存在
            full_path = os.path.join(public_images_dir, filename)
            
            if os.path.exists(full_path):
                # 根据文件扩展名设置正确的MIME类型
                if filename.endswith('.svg'):
                    mimetype = 'image/svg+xml'
                elif filename.endswith('.png'):
                    mimetype = 'image/png'
                elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
                    mimetype = 'image/jpeg'
                elif filename.endswith('.gif'):
                    mimetype = 'image/gif'
                else:
                    mimetype = 'image/png'  # 默认
                
                return send_from_directory(public_images_dir, filename, mimetype=mimetype)
            
            # 如果找不到，返回默认图片
            logger.warning(f"图片文件不存在: {filename}")
            return jsonify({"success": False, "message": "文件不存在"}), 404
            
        except Exception as e:
            logger.error(f"提供图片文件失败: {e}")
            return jsonify({"success": False, "message": "文件访问失败"}), 500

    # 添加测试路由
    @app.route('/test-help')
    def test_help():
        """测试help目录访问"""
        help_dir = os.path.join(os.path.dirname(__file__), 'help')
        files = []
        if os.path.exists(help_dir):
            for file in os.listdir(help_dir):
                if file.endswith('.pdf'):
                    files.append(file)
        
        return jsonify({
            "success": True,
            "help_dir": help_dir,
            "dir_exists": os.path.exists(help_dir),
            "files": files
        })

    # 添加help目录路由，用于提供帮助文档 - 必须在通用路由之前
    @app.route('/help/<path:filename>')
    def serve_help_files(filename):
        """提供help目录下的文件"""
        try:
            help_dir = os.path.join(os.path.dirname(__file__), 'help')
            print(f"[HELP] 尝试访问帮助文件: {filename}, 目录: {help_dir}")
            print(f"[HELP] 文件是否存在: {os.path.exists(help_dir)}")
            
            # 确保文件路径安全，防止目录遍历攻击
            if '..' in filename or filename.startswith('/'):
                print(f"[HELP] 不安全的文件路径: {filename}")
                return jsonify({"success": False, "message": "文件路径不合法"}), 400
            
            full_path = os.path.join(help_dir, filename)
            print(f"[HELP] 完整文件路径: {full_path}")
            print(f"[HELP] 文件是否存在: {os.path.exists(full_path)}")
            
            if not os.path.exists(full_path):
                print(f"[HELP] 帮助文件不存在: {full_path}")
                return jsonify({"success": False, "message": "文件不存在"}), 404
            
            # 只允许PDF文件
            if not filename.lower().endswith('.pdf'):
                print(f"[HELP] 不支持的文件类型: {filename}")
                return jsonify({"success": False, "message": "不支持的文件类型"}), 400
            
            print(f"[HELP] 成功提供文件: {filename}")
            return send_from_directory(help_dir, filename, mimetype='application/pdf')
        except Exception as e:
            print(f"[HELP] 提供帮助文件失败: {e}")
            return jsonify({"success": False, "message": "文件访问失败"}), 500

    # 前端 Vue 项目资源路径兜底，避免刷新页面 404
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        # 检查是否存在静态文件目录
        static_dirs = ['static/dist_frontend', 'static', 'templates']
        
        # API请求由蓝图处理，这里不拦截
        # if path.startswith('api/'):
        #     return jsonify({"success": False, "message": "请求的接口不存在"}), 404
        
        # 排除help路径，这些由专门的路由处理
        if path.startswith('help/'):
            return jsonify({"success": False, "message": "帮助文件不存在"}), 404
        
        # 排除flags和images路径，这些由专门的路由处理
        # 注意：这个检查应该在flags和images路由之后，所以这里不应该拦截
        # if path.startswith('flags/') or path.startswith('images/'):
        #     return jsonify({"success": False, "message": "文件不存在"}), 404
        
        # 尝试从不同目录查找静态文件
        for static_dir in static_dirs:
            try:
                if path == "" or path == "index.html":
                    index_file = os.path.join(static_dir, 'index.html')
                    if os.path.exists(index_file):
                        return send_from_directory(static_dir, 'index.html')
                else:
                    file_path = os.path.join(static_dir, path)
                    if os.path.exists(file_path):
                        return send_from_directory(static_dir, path)
            except:
                continue
        
        # 如果找不到静态文件，返回一个简单的HTML页面
        return """
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>外汇兑换系统</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1 { color: #333; text-align: center; }
                .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
                .info { background: #d1ecf1; color: #0c5460; border: 1px solid #b6d4d9; }
                .links { margin: 20px 0; }
                .links a { display: inline-block; margin: 10px; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
                .links a:hover { background: #0056b3; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🏦 外汇兑换系统</h1>
                <div class="status info">
                    系统正在运行中。请使用以下链接访问相关功能：
                </div>
                <div class="links">
                    <a href="/health">健康检查</a>
                    <a href="/debug_print_receipt.html">打印调试</a>
                    <a href="/api/dashboard/statistics">API测试</a>
                </div>
                <p>如果您需要访问前端界面，请确保已正确配置静态资源路径。</p>
            </div>
        </body>
        </html>
        """
    
    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api/'):
            return jsonify({"success": False, "message": "请求的接口不存在"}), 404
        # 对于其他404，返回简单页面而不是尝试查找静态文件
        return serve_frontend(''), 200
    
    @app.errorhandler(500)
    def internal_error(e):
        logging.error(f"Internal server error: {e}", exc_info=True)
        return safe_error_response(e, "服务器内部错误，请稍后重试", 500)

    # 全局错误处理器
    @app.errorhandler(Exception)
    def handle_exception(e):
        """全局异常处理器，确保不会泄露敏感信息"""
        # 记录原始错误用于调试
        logging.error(f"Unhandled exception: {e}", exc_info=True)
        
        # 返回安全的错误响应
        return safe_error_response(e, "系统暂时无法处理请求，请稍后重试", 500)
    
    # 在应用创建后添加静态文件目录配置
    app.static_folder = 'static'
    app.static_url_path = '/static'
    
    # 添加下载路由
    @app.route('/downloads/<filename>')
    def download_file(filename):
        export_dir = os.path.join(app.root_path, 'exports')
        print(f"[DEBUG] 下载请求: {filename}，目录: {export_dir}")  # 调试信息
        return send_from_directory(export_dir, filename)
    
    # 添加调试路由，显示所有注册的路由
    @app.route('/debug/routes')
    def debug_routes():
        """显示所有注册的路由"""
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({
                'endpoint': rule.endpoint,
                'methods': list(rule.methods),
                'rule': str(rule)
            })
        return jsonify(routes)
    
    return app

if __name__ == '__main__':
    try:
        # 简化启动日志输出
        print("ExchangeOK System Starting...")
        
        # 显示数据库配置信息
        from services.db_service import DB_TYPE
        print(f"Database Type: {DB_TYPE.upper()}")
        
        # 创建Flask应用
        app = create_app()
        
        # 只在首次运行或需要重置时初始化数据库
        if os.environ.get('INIT_DB', 'false').lower() == 'true':
            with app.app_context():
                init_database()
        elif os.environ.get('ENV', 'development') == 'development':
            # 在开发环境下，如果数据库为空，则初始化测试数据
            with app.app_context():
                session = DatabaseService.get_session()

        port = int(os.environ.get('PORT', 5001))
        
        print(f"Running on: http://localhost:{port}")
        
        # 禁用Flask开发服务器的警告信息
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        log.disabled = True  # 完全禁用werkzeug日志
        
        # 使用生产模式启动，减少冗余输出
        app.run(host='0.0.0.0', port=port, debug=True, threaded=True)
        
    except KeyboardInterrupt:
        print("\n👋 ExchangeOK System Shutting Down...")
        try:
            with app.app_context():
                multilingual_logger.log_system_operation(
                    'system_shutdown',
                    details="ExchangeOK外汇兑换系统正常关闭",
                    language='zh-CN'
                )
        except:
            pass  # 忽略关闭时的日志错误
    except Exception as e:
        logger.error(f"System Error: {e}")
        try:
            with app.app_context():
                multilingual_logger.log_system_operation(
                    'system_shutdown',
                    details=f"ExchangeOK外汇兑换系统异常关闭: {str(e)}",
                    language='zh-CN'
                )
        except:
            pass  # 忽略关闭时的日志错误
    finally:
        # 确保数据库连接关闭
        try:
            shutdown_session()
        except:
            pass  # 忽略关闭时的错误
