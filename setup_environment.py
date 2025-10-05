#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
环境自动配置脚本
解决每次迁移到新机器时的配置问题
"""

import os
import sys
import json
from pathlib import Path

# 添加src目录到Python路径
src_dir = os.path.join(os.path.dirname(__file__), 'src')
sys.path.append(src_dir)

from src.config.environment import env_config

def update_vue_config():
    """更新Vue配置文件"""
    vue_config_path = 'vue.config.js'

    if not os.path.exists(vue_config_path):
        print("[错误] vue.config.js 文件不存在")
        return False

    try:
        with open(vue_config_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 替换proxy target配置
        old_patterns = [
            'http://192.168.0.18:5001',
            'http://192.168.13.56:5001',
            'http://127.0.0.1:5001',
            'http://localhost:5001'
        ]

        new_target = env_config.backend_url

        for pattern in old_patterns:
            content = content.replace(f"'{pattern}'", f"'{new_target}'")
            content = content.replace(f'"{pattern}"', f'"{new_target}"')

        # 更新network地址显示
        old_network_patterns = [
            '192.168.0.18',
            '192.168.13.56',
            '127.0.0.1',
            'localhost'
        ]

        for pattern in old_network_patterns:
            content = content.replace(f"'{pattern}'", f"'{env_config.current_ip}'")
            content = content.replace(f'"{pattern}"', f'"{env_config.current_ip}"')

        with open(vue_config_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"[成功] vue.config.js 已更新 - 后端URL: {new_target}")
        return True

    except Exception as e:
        print(f"[错误] 更新vue.config.js失败: {e}")
        return False

def update_env_local():
    """更新前端环境配置"""
    env_local_path = '.env.local'

    try:
        env_content = f"""# 自动生成的前端环境配置
VUE_APP_API_BASE_URL={env_config.backend_url}
VUE_APP_CURRENT_IP={env_config.current_ip}
VUE_APP_BACKEND_PORT={env_config.backend_port}
VUE_APP_FRONTEND_PORT={env_config.frontend_port}
"""

        with open(env_local_path, 'w', encoding='utf-8') as f:
            f.write(env_content)

        print(f"[成功] .env.local 已更新 - API URL: {env_config.backend_url}")
        return True

    except Exception as e:
        print(f"[错误] 更新.env.local失败: {e}")
        return False

def update_show_html():
    """更新Show.html中的IP配置"""
    show_html_path = 'src/static/Show.html'

    if not os.path.exists(show_html_path):
        print("[错误] Show.html 文件不存在")
        return False

    try:
        with open(show_html_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 替换所有可能的旧IP地址
        old_ips = ['192.168.0.18', '192.168.13.56', '127.0.0.1']
        new_ip = env_config.current_ip

        for old_ip in old_ips:
            if old_ip != new_ip:
                content = content.replace(old_ip, new_ip)

        with open(show_html_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"[成功] Show.html 已更新 - 服务器IP: {new_ip}")
        return True

    except Exception as e:
        print(f"[错误] 更新Show.html失败: {e}")
        return False

def update_frontend_api_config():
    """更新前端API配置"""
    api_config_path = 'src/services/api/index.js'

    if not os.path.exists(api_config_path):
        print("[警告] 前端API配置文件不存在，跳过")
        return True

    try:
        with open(api_config_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 替换baseURL配置
        old_patterns = [
            'http://192.168.0.18:5001',
            'http://192.168.13.56:5001',
            'http://127.0.0.1:5001',
            'http://localhost:5001'
        ]

        new_url = env_config.backend_url

        for pattern in old_patterns:
            content = content.replace(pattern, new_url)

        with open(api_config_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"[成功] 前端API配置已更新 - API URL: {new_url}")
        return True

    except Exception as e:
        print(f"[错误] 更新前端API配置失败: {e}")
        return False

def create_config_json():
    """创建配置信息JSON文件"""
    config_info = {
        "current_ip": env_config.current_ip,
        "backend_url": env_config.backend_url,
        "frontend_url": env_config.frontend_url,
        "backend_port": env_config.backend_port,
        "frontend_port": env_config.frontend_port,
        "generated_at": env_config._get_timestamp(),
        "cors_origins": env_config.get_cors_origins()
    }

    try:
        with open('environment_config.json', 'w', encoding='utf-8') as f:
            json.dump(config_info, f, indent=2, ensure_ascii=False)

        print(f"[成功] 环境配置信息已保存到 environment_config.json")
        return True

    except Exception as e:
        print(f"[错误] 保存配置信息失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("[启动] ExchangeOK 环境自动配置工具")
    print("=" * 60)

    print(f"\n[信息] 检测到的环境信息:")
    print(f"   当前IP地址: {env_config.current_ip}")
    print(f"   后端服务URL: {env_config.backend_url}")
    print(f"   前端服务URL: {env_config.frontend_url}")

    print(f"\n[配置] 开始自动配置...")

    # 执行各项配置更新
    tasks = [
        ("生成.env文件", lambda: env_config.save_env_file()),
        ("更新Vue配置", update_vue_config),
        ("更新前端环境配置", update_env_local),
        ("更新Show.html", update_show_html),
        ("更新前端API配置", update_frontend_api_config),
        ("创建配置信息文件", create_config_json)
    ]

    success_count = 0
    for task_name, task_func in tasks:
        print(f"\n[处理] {task_name}...")
        try:
            if task_func():
                success_count += 1
            else:
                print(f"[错误] {task_name} 失败")
        except Exception as e:
            print(f"[异常] {task_name} 异常: {e}")

    print(f"\n" + "=" * 60)
    print(f"[完成] 配置完成! 成功: {success_count}/{len(tasks)}")
    print("=" * 60)

    if success_count == len(tasks):
        print("\n[成功] 所有配置都已成功更新!")
        print("[提示] 现在可以启动系统了:")
        print("   后端: cd src && python main.py")
        print("   前端: npm run serve")
        print(f"   访问: {env_config.frontend_url}")
    else:
        print(f"\n[警告] 有 {len(tasks) - success_count} 个配置项更新失败，请手动检查")

    return success_count == len(tasks)

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n👋 配置过程被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n[错误] 配置过程发生异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)