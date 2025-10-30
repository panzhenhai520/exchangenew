# -*- coding: utf-8 -*-
"""
环境配置同步脚本
从 .env 文件读取配置并同步到所有配置文件
包括: .env.local, environment_config.json, env-config.js
"""
import os
import json
from datetime import datetime
from pathlib import Path


def load_env_file(env_path):
    """加载 .env 文件"""
    env_vars = {}
    if not os.path.exists(env_path):
        print(f"[X] .env 文件不存在: {env_path}")
        return env_vars

    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 跳过注释和空行
            if not line or line.startswith('#'):
                continue
            # 解析 KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()

    return env_vars


def sync_env_local(env_vars, project_root):
    """同步 .env.local 文件 (Vue 编译时使用)"""
    env_local_path = project_root / '.env.local'

    current_ip = env_vars.get('CURRENT_IP', 'localhost')
    backend_port = env_vars.get('BACKEND_PORT', '5001')
    frontend_port = env_vars.get('FRONTEND_PORT', '8080')

    api_base_url = f'http://{current_ip}:{backend_port}'

    content = f"""VUE_APP_API_BASE_URL={api_base_url}
VUE_APP_CURRENT_IP={current_ip}
VUE_APP_BACKEND_PORT={backend_port}
VUE_APP_FRONTEND_PORT={frontend_port}
"""

    with open(env_local_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"[OK] 已同步 .env.local")
    print(f"   VUE_APP_API_BASE_URL={api_base_url}")


def sync_env_config_json(env_vars, project_root):
    """同步 environment_config.json (CORS配置)"""
    config_path = project_root / 'environment_config.json'

    current_ip = env_vars.get('CURRENT_IP', 'localhost')
    backend_port = env_vars.get('BACKEND_PORT', '5001')
    frontend_port = env_vars.get('FRONTEND_PORT', '8080')

    backend_url = f'http://{current_ip}:{backend_port}'
    frontend_url = f'http://{current_ip}:{frontend_port}'

    config = {
        "current_ip": current_ip,
        "backend_url": backend_url,
        "frontend_url": frontend_url,
        "backend_port": int(backend_port),
        "frontend_port": int(frontend_port),
        "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "cors_origins": [
            "http://localhost:\\d+",
            "http://127\\.0\\.0\\.1:\\d+",
            f"http://{current_ip}:{frontend_port}",
            f"http://{current_ip}:{backend_port}",
            "null",
            f"http://{current_ip}:3000",
            f"http://{current_ip}:8081",
            f"http://{current_ip}:8082",
            f"http://{current_ip}:8083",
            f"http://{current_ip}:5173"
        ]
    }

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"[OK] 已同步 environment_config.json")
    print(f"   current_ip={current_ip}")
    print(f"   backend_url={backend_url}")


def sync_env_config_js(env_vars, project_root):
    """同步 src/static/env-config.js (运行时配置)"""
    config_path = project_root / 'src' / 'static' / 'env-config.js'
    config_path.parent.mkdir(parents=True, exist_ok=True)

    current_ip = env_vars.get('CURRENT_IP', 'localhost')
    backend_port = env_vars.get('BACKEND_PORT', '5001')
    frontend_port = env_vars.get('FRONTEND_PORT', '8080')
    default_branch = env_vars.get('DEFAULT_BRANCH', 'A005')

    api_base_url = f'http://{current_ip}:{backend_port}'
    backend_url = f'http://{current_ip}:{backend_port}'
    frontend_url = f'http://{current_ip}:{frontend_port}'

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    content = f"""// Auto-generated runtime config - {timestamp}
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

    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"[OK] 已同步 src/static/env-config.js")
    print(f"   API_BASE_URL={api_base_url}")


def main():
    """主函数"""
    print("=" * 80)
    print("环境配置同步脚本")
    print("=" * 80)

    # 获取项目根目录
    project_root = Path(__file__).parent
    env_path = project_root / '.env'

    print(f"\n[*] 项目根目录: {project_root}")
    print(f"[*] .env 文件路径: {env_path}")

    # 加载 .env 文件
    print(f"\n[*] 加载 .env 文件...")
    env_vars = load_env_file(env_path)

    if not env_vars:
        print("[X] 未能加载 .env 文件或文件为空")
        return

    print(f"[OK] 成功加载 {len(env_vars)} 个环境变量")
    print(f"\n关键配置:")
    print(f"  CURRENT_IP = {env_vars.get('CURRENT_IP', '未设置')}")
    print(f"  BACKEND_PORT = {env_vars.get('BACKEND_PORT', '未设置')}")
    print(f"  FRONTEND_PORT = {env_vars.get('FRONTEND_PORT', '未设置')}")

    # 同步各个配置文件
    print(f"\n[*] 开始同步配置文件...")
    sync_env_local(env_vars, project_root)
    sync_env_config_json(env_vars, project_root)
    sync_env_config_js(env_vars, project_root)

    print(f"\n" + "=" * 80)
    print("[OK] 所有配置文件同步完成!")
    print("=" * 80)
    print(f"\n下一步:")
    print(f"  1. 重启后端服务: python src/main.py")
    print(f"  2. 重新编译前端: npm run build")
    print(f"  3. 或重启前端开发服务器: npm run serve")
    print(f"\n提示:")
    print(f"  - 如果只是更换IP，重启服务即可，无需重新编译")
    print(f"  - 浏览器可能有缓存，建议使用 Ctrl+F5 强制刷新")
    print("")


if __name__ == '__main__':
    main()
