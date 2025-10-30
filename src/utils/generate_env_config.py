"""
生成机顶盒前端配置文件
从 .env 文件读取配置并生成 JavaScript 配置文件
"""
import os
from pathlib import Path


def generate_env_config():
    """生成前端环境配置文件"""
    from datetime import datetime

    # 读取环境变量
    current_ip = os.getenv('CURRENT_IP', 'localhost')
    backend_port = os.getenv('BACKEND_PORT', '5001')
    frontend_port = os.getenv('FRONTEND_PORT', '8080')
    default_branch = os.getenv('DEFAULT_BRANCH', 'A005')

    # 构建URL
    backend_url = f'http://{current_ip}:{backend_port}'
    frontend_url = f'http://{current_ip}:{frontend_port}'
    api_base_url = f'http://{current_ip}:{backend_port}'

    # 生成JavaScript配置文件内容
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    config_content = f"""// Auto-generated runtime config - {timestamp}
window.ENV_CONFIG = {{
  API_BASE_URL: '{api_base_url}',
  CURRENT_IP: '{current_ip}',
  BACKEND_PORT: {backend_port},
  FRONTEND_PORT: {frontend_port},
  BACKEND_URL: '{backend_url}',
  FRONTEND_URL: '{frontend_url}',
  DEFAULT_BRANCH: '{default_branch}'
}};

console.log('[ENV_CONFIG] Runtime configuration loaded successfully');
console.log('[ENV_CONFIG] API_BASE_URL:', window.ENV_CONFIG.API_BASE_URL);
console.log('[ENV_CONFIG] CURRENT_IP:', window.ENV_CONFIG.CURRENT_IP);
"""
    
    # 确定配置文件路径
    current_dir = Path(__file__).parent.parent
    config_file_path = current_dir / 'static' / 'env-config.js'
    
    # 确保 static 目录存在
    config_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 写入配置文件
    with open(config_file_path, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print(f"[环境配置生成] 配置文件已生成: {config_file_path}")
    print(f"[环境配置生成] BACKEND_URL: {backend_url}")
    print(f"[环境配置生成] FRONTEND_URL: {frontend_url}")
    print(f"[环境配置生成] DEFAULT_BRANCH: {default_branch}")
    
    return config_file_path


if __name__ == '__main__':
    # 如果直接运行此脚本，需要先加载 .env 文件
    from dotenv import load_dotenv
    dotenv_path = Path(__file__).parent.parent / '.env'
    load_dotenv(dotenv_path)
    
    generate_env_config()


