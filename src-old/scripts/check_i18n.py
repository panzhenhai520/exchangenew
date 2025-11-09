#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
i18n翻译问题快速诊断脚本
用于检查和修复翻译缺失问题
"""

import json
import os
import re
import sys
from pathlib import Path

# 支持的语言列表
SUPPORTED_LOCALES = ['zh-CN', 'en-US', 'th-TH']

def load_locale_files():
    """加载所有语言文件"""
    locales = {}
    locale_dir = Path(__file__).parent.parent / 'locales'
    
    for locale in SUPPORTED_LOCALES:
        locale_file = locale_dir / f'{locale}.json'
        if locale_file.exists():
            try:
                with open(locale_file, 'r', encoding='utf-8') as f:
                    locales[locale] = json.load(f)
                print(f"✅ 已加载 {locale} 翻译文件")
            except json.JSONDecodeError as e:
                print(f"❌ {locale} 文件JSON格式错误: {e}")
        else:
            print(f"❌ {locale} 翻译文件不存在: {locale_file}")
    
    return locales

def get_nested_keys(obj, prefix=''):
    """递归获取所有嵌套的key"""
    keys = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            new_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                keys.extend(get_nested_keys(value, new_key))
            else:
                keys.append(new_key)
    return keys

def scan_vue_files():
    """扫描Vue文件中使用的翻译key"""
    used_keys = set()
    vue_dir = Path(__file__).parent.parent
    
    # 排除的目录
    exclude_dirs = {'.git', 'node_modules', 'dist', 'build', '__pycache__', 'venv'}
    
    def scan_directory(directory):
        for item in directory.iterdir():
            if item.is_file() and item.suffix == '.vue':
                scan_vue_file(item)
            elif item.is_dir() and item.name not in exclude_dirs:
                scan_directory(item)
    
    def scan_vue_file(file_path):
        try:
            content = file_path.read_text(encoding='utf-8')
            # 匹配 $t('xxx') 和 t('xxx') 模式
            patterns = [
                r'\$t\([\'"]([a-zA-Z0-9_.]+)[\'"]\)',
                r'[^$]t\([\'"]([a-zA-Z0-9_.]+)[\'"]\)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    used_keys.add(match)
        except Exception as e:
            print(f"警告: 读取文件失败 {file_path}: {e}")
    
    scan_directory(vue_dir)
    return list(used_keys)

def check_translation_completeness():
    """检查翻译完整性"""
    print("\n🔍 开始检查翻译完整性...")
    
    locales = load_locale_files()
    if not locales:
        print("❌ 无法加载任何语言文件")
        return
    
    # 以中文为基准
    base_locale = 'zh-CN'
    if base_locale not in locales:
        print(f"❌ 基准语言文件 {base_locale} 不存在")
        return
    
    base_keys = get_nested_keys(locales[base_locale])
    print(f"📊 基准语言 {base_locale} 包含 {len(base_keys)} 个翻译key")
    
    issues_found = False
    
    # 检查每种语言的完整性
    for locale in SUPPORTED_LOCALES:
        if locale == base_locale or locale not in locales:
            continue
            
        locale_keys = get_nested_keys(locales[locale])
        missing_keys = set(base_keys) - set(locale_keys)
        extra_keys = set(locale_keys) - set(base_keys)
        
        if missing_keys:
            issues_found = True
            print(f"\n❌ {locale} 缺失 {len(missing_keys)} 个翻译:")
            for key in sorted(list(missing_keys)[:10]):  # 只显示前10个
                print(f"   - {key}")
            if len(missing_keys) > 10:
                print(f"   ... 还有 {len(missing_keys) - 10} 个")
        
        if extra_keys:
            print(f"\n⚠️  {locale} 多出 {len(extra_keys)} 个翻译:")
            for key in sorted(list(extra_keys)[:5]):  # 只显示前5个
                print(f"   + {key}")
            if len(extra_keys) > 5:
                print(f"   ... 还有 {len(extra_keys) - 5} 个")
    
    if not issues_found:
        print("\n✅ 所有语言文件的翻译都是完整的！")

def check_used_keys():
    """检查代码中使用的翻译key"""
    print("\n🔍 扫描Vue文件中使用的翻译key...")
    
    used_keys = scan_vue_files()
    print(f"📊 在Vue文件中找到 {len(used_keys)} 个翻译key")
    
    # 加载翻译文件
    locales = load_locale_files()
    if 'zh-CN' not in locales:
        print("❌ 无法检查，缺少中文翻译文件")
        return
    
    available_keys = get_nested_keys(locales['zh-CN'])
    missing_in_translations = set(used_keys) - set(available_keys)
    
    if missing_in_translations:
        print(f"\n🚨 代码中使用但翻译文件中缺失的key ({len(missing_in_translations)} 个):")
        for key in sorted(list(missing_in_translations)):
            print(f"   - {key}")
    else:
        print("\n✅ 所有使用的翻译key都在翻译文件中存在！")

def generate_missing_translations():
    """为缺失的翻译生成占位符"""
    print("\n🔧 生成缺失翻译的占位符...")
    
    locales = load_locale_files()
    base_locale = 'zh-CN'
    
    if base_locale not in locales:
        print("❌ 缺少基准语言文件")
        return
    
    base_keys = get_nested_keys(locales[base_locale])
    locale_dir = Path(__file__).parent.parent / 'locales'
    
    for locale in SUPPORTED_LOCALES:
        if locale == base_locale or locale not in locales:
            continue
        
        locale_keys = get_nested_keys(locales[locale])
        missing_keys = set(base_keys) - set(locale_keys)
        
        if missing_keys:
            print(f"\n🔧 为 {locale} 添加 {len(missing_keys)} 个占位符翻译...")
            
            # 为每个缺失的key添加占位符
            locale_data = locales[locale].copy()
            
            for key in missing_keys:
                parts = key.split('.')
                current = locale_data
                
                # 创建嵌套结构
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                
                # 添加占位符翻译
                last_part = parts[-1]
                current[last_part] = f"[{locale}] {key}"
            
            # 保存文件
            locale_file = locale_dir / f'{locale}.json'
            with open(locale_file, 'w', encoding='utf-8') as f:
                json.dump(locale_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 已更新 {locale_file}")

def main():
    """主函数"""
    print("🌍 i18n翻译问题诊断工具")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
    else:
        command = 'check'
    
    if command == 'check':
        check_translation_completeness()
        check_used_keys()
    elif command == 'fix':
        generate_missing_translations()
        print("\n✅ 修复完成！请重启应用并刷新浏览器缓存。")
    elif command == 'scan':
        check_used_keys()
    else:
        print("使用方法:")
        print("  python check_i18n.py check  - 检查翻译完整性")
        print("  python check_i18n.py fix    - 自动修复缺失翻译")
        print("  python check_i18n.py scan   - 扫描使用的翻译key")

if __name__ == '__main__':
    main() 