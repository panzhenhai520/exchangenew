#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import socket
from typing import Optional

class EnvironmentConfig:
    """环境配置管理类，自动检测并配置系统环境"""

    def __init__(self):
        self._current_ip = None
        self._backend_port = None
        self._frontend_port = None

    @property
    def current_ip(self) -> str:
        """获取当前机器IP地址"""
        if self._current_ip is None:
            self._current_ip = self._detect_current_ip()
        return self._current_ip

    @property
    def backend_port(self) -> int:
        """获取后端端口"""
        if self._backend_port is None:
            self._backend_port = int(os.environ.get('BACKEND_PORT', '5001'))
        return self._backend_port

    @property
    def frontend_port(self) -> int:
        """获取前端端口"""
        if self._frontend_port is None:
            self._frontend_port = int(os.environ.get('FRONTEND_PORT', '8080'))
        return self._frontend_port

    @property
    def backend_url(self) -> str:
        """获取后端完整URL"""
        return f"http://{self.current_ip}:{self.backend_port}"

    @property
    def frontend_url(self) -> str:
        """获取前端完整URL"""
        return f"http://{self.current_ip}:{self.frontend_port}"

    def _detect_current_ip(self) -> str:
        """自动检测当前机器的IP地址"""
        # 优先使用环境变量设置的IP
        env_ip = os.environ.get('CURRENT_IP')
        if env_ip and self._is_valid_ip(env_ip):
            print(f"[环境配置] 使用环境变量IP: {env_ip}")
            return env_ip

        try:
            # 尝试连接外部地址来获取本机IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                # 连接到一个外部地址（不需要真的连接成功）
                s.connect(('8.8.8.8', 80))
                detected_ip = s.getsockname()[0]

                # 验证检测到的IP是否为内网地址
                if self._is_local_ip(detected_ip):
                    print(f"[环境配置] 自动检测IP: {detected_ip}")
                    return detected_ip
                else:
                    print(f"[环境配置] 检测到外网IP {detected_ip}，使用默认IP")

        except Exception as e:
            print(f"[环境配置] IP检测失败: {e}")

        # 回退方案：使用常见的开发机器IP模式
        fallback_ips = [
            '192.168.13.56',  # 当前机器
            '192.168.0.18',   # 旧机器
            '192.168.1.100',  # 常见开发IP
            '127.0.0.1'       # 本地回环
        ]

        for ip in fallback_ips:
            if self._test_ip_connectivity(ip):
                print(f"[环境配置] 使用回退IP: {ip}")
                return ip

        # 最终回退
        print(f"[环境配置] 使用最终回退IP: 127.0.0.1")
        return '127.0.0.1'

    def _is_valid_ip(self, ip: str) -> bool:
        """验证IP地址格式是否正确"""
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False

    def _is_local_ip(self, ip: str) -> bool:
        """检查是否为内网IP地址"""
        if ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.'):
            return True
        if ip == '127.0.0.1' or ip == 'localhost':
            return True
        return False

    def _test_ip_connectivity(self, ip: str) -> bool:
        """测试IP地址的连通性"""
        try:
            # 简单的端口测试
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                # 测试常见端口
                for port in [self.backend_port, 80, 443]:
                    try:
                        result = s.connect_ex((ip, port))
                        if result == 0:
                            return True
                    except:
                        continue
            return False
        except:
            return False

    def get_cors_origins(self) -> list:
        """获取CORS允许的源列表"""
        origins = [
            r"http://localhost:\d+",
            r"http://127\.0\.0\.1:\d+",
            f"http://{self.current_ip}:{self.frontend_port}",
            f"http://{self.current_ip}:{self.backend_port}",
            "null"
        ]

        # 添加常见的开发端口
        for port in [3000, 8080, 8081, 5001, 5173]:
            origins.append(f"http://{self.current_ip}:{port}")

        return origins

    def generate_config_js(self) -> str:
        """生成前端配置JavaScript代码"""
        return f"""// 自动生成的环境配置
window.ENV_CONFIG = {{
    BACKEND_URL: '{self.backend_url}',
    FRONTEND_URL: '{self.frontend_url}',
    CURRENT_IP: '{self.current_ip}',
    BACKEND_PORT: {self.backend_port},
    FRONTEND_PORT: {self.frontend_port},
    GENERATED_AT: '{self._get_timestamp()}'
}};

// 兼容性配置
if (typeof module !== 'undefined' && module.exports) {{
    module.exports = window.ENV_CONFIG;
}}
"""

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def save_env_file(self, filepath: str = None):
        """保存环境配置到.env文件"""
        if filepath is None:
            filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')

        env_content = f"""# 自动生成的环境配置文件
# 生成时间: {self._get_timestamp()}

# 网络配置
CURRENT_IP={self.current_ip}
BACKEND_PORT={self.backend_port}
FRONTEND_PORT={self.frontend_port}
BACKEND_URL={self.backend_url}
FRONTEND_URL={self.frontend_url}

# Flask配置
SECRET_KEY=exchange-ok-secret-key-2025-dev-mode

# 数据库配置
DB_TYPE=mysql
DB_HOST=localhost
DB_PORT=3306
DB_NAME=exchange_db
DB_USER=root
DB_PASSWORD=root

# 日志配置
LOG_MODE=development
LOG_LEVEL=INFO
"""

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(env_content)
            print(f"[环境配置] 环境文件已保存: {filepath}")
            return True
        except Exception as e:
            print(f"[环境配置] 保存环境文件失败: {e}")
            return False

# 全局实例
env_config = EnvironmentConfig()

def get_current_ip() -> str:
    """获取当前IP地址的快捷函数"""
    return env_config.current_ip

def get_backend_url() -> str:
    """获取后端URL的快捷函数"""
    return env_config.backend_url

def get_frontend_url() -> str:
    """获取前端URL的快捷函数"""
    return env_config.frontend_url