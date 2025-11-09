#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
翻译检查工具
检查Vue文件中使用的翻译key是否在翻译文件中存在
"""

import os
import re
import json
import glob
from pathlib import Path

class I18nChecker:
    def __init__(self, project_root='.'):
        self.project_root = Path(project_root)
        self.vue_files = []
        self.translation_files = {}
        self.used_keys = set()
        self.available_keys = set()
        self.missing_keys = set()
        
    def scan_vue_files(self):
        """扫描所有Vue文件"""
        vue_pattern = self.project_root / 'views' / '**' / '*.vue'
        self.vue_files = list(glob.glob(str(vue_pattern), recursive=True))
        print(f"找到 {len(self.vue_files)} 个Vue文件")
        
    def extract_translation_keys_from_vue(self, file_path):
        """从Vue文件中提取翻译key"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 匹配 $t('key') 或 $t("key") 模式
            patterns = [
                r'\$t\([\'"]([^\'"]+)[\'"]\)',  # $t('key') 或 $t("key")
                r'\$t\([\'"]([^\'"]+)[\'"]\s*,\s*\{[^}]*\}\)',  # $t('key', {params})
            ]
            
            keys = set()
            for pattern in patterns:
                matches = re.findall(pattern, content)
                keys.update(matches)
                
            return keys
        except Exception as e:
            print(f"读取文件 {file_path} 失败: {e}")
            return set()
    
    def scan_all_vue_keys(self):
        """扫描所有Vue文件中的翻译key"""
        for vue_file in self.vue_files:
            keys = self.extract_translation_keys_from_vue(vue_file)
            self.used_keys.update(keys)
            print(f"从 {os.path.basename(vue_file)} 提取到 {len(keys)} 个翻译key")
    
    def load_translation_files(self):
        """加载翻译文件"""
        i18n_dir = self.project_root / 'i18n' / 'modules'
        if not i18n_dir.exists():
            print(f"翻译目录不存在: {i18n_dir}")
            return
            
        # 扫描所有语言文件
        for lang_file in i18n_dir.rglob('*.js'):
            if lang_file.name.endswith(('.js')):
                lang_code = lang_file.parent.name
                if lang_code not in self.translation_files:
                    self.translation_files[lang_code] = {}
                self.translation_files[lang_code][lang_file.name] = lang_file
                
        print(f"找到翻译文件: {sum(len(files) for files in self.translation_files.values())} 个")
    
    def extract_keys_from_js_file(self, file_path):
        """从JS文件中提取翻译key"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 简单的key提取（基于对象属性模式）
            # 匹配 "key": "value" 或 'key': 'value' 模式
            patterns = [
                r'[\'"]([a-zA-Z_][a-zA-Z0-9_.]*)[\'"]\s*:\s*[\'"][^\'"]*[\'"]',  # "key": "value"
                r'[\'"]([a-zA-Z_][a-zA-Z0-9_.]*)[\'"]\s*:',  # "key":
            ]
            
            keys = set()
            for pattern in patterns:
                matches = re.findall(pattern, content)
                keys.update(matches)
                
            return keys
        except Exception as e:
            print(f"读取翻译文件 {file_path} 失败: {e}")
            return set()
    
    def build_available_keys(self):
        """构建可用的翻译key"""
        for lang_code, files in self.translation_files.items():
            for file_name, file_path in files.items():
                keys = self.extract_keys_from_js_file(file_path)
                self.available_keys.update(keys)
                print(f"从 {lang_code}/{file_name} 提取到 {len(keys)} 个翻译key")
    
    def find_missing_keys(self):
        """查找缺失的翻译key"""
        self.missing_keys = self.used_keys - self.available_keys
        return self.missing_keys
    
    def generate_report(self):
        """生成检查报告"""
        report = {
            'summary': {
                'vue_files_count': len(self.vue_files),
                'translation_files_count': sum(len(files) for files in self.translation_files.values()),
                'used_keys_count': len(self.used_keys),
                'available_keys_count': len(self.available_keys),
                'missing_keys_count': len(self.missing_keys)
            },
            'missing_keys': list(self.missing_keys),
            'used_keys': list(self.used_keys),
            'available_keys': list(self.available_keys)
        }
        return report
    
    def run_check(self):
        """运行完整的检查流程"""
        print("=== 开始翻译检查 ===")
        
        # 1. 扫描Vue文件
        print("\n1. 扫描Vue文件...")
        self.scan_vue_files()
        
        # 2. 提取Vue文件中的翻译key
        print("\n2. 提取Vue文件中的翻译key...")
        self.scan_all_vue_keys()
        
        # 3. 加载翻译文件
        print("\n3. 加载翻译文件...")
        self.load_translation_files()
        
        # 4. 构建可用key
        print("\n4. 构建可用翻译key...")
        self.build_available_keys()
        
        # 5. 查找缺失的key
        print("\n5. 查找缺失的翻译key...")
        missing_keys = self.find_missing_keys()
        
        # 6. 生成报告
        print("\n6. 生成检查报告...")
        report = self.generate_report()
        
        return report

def main():
    """主函数"""
    checker = I18nChecker()
    report = checker.run_check()
    
    print("\n=== 检查结果 ===")
    print(f"Vue文件数量: {report['summary']['vue_files_count']}")
    print(f"翻译文件数量: {report['summary']['translation_files_count']}")
    print(f"使用的翻译key数量: {report['summary']['used_keys_count']}")
    print(f"可用的翻译key数量: {report['summary']['available_keys_count']}")
    print(f"缺失的翻译key数量: {report['summary']['missing_keys_count']}")
    
    if report['missing_keys']:
        print(f"\n缺失的翻译key ({len(report['missing_keys'])} 个):")
        for key in sorted(report['missing_keys']):
            print(f"  - {key}")
    else:
        print("\n[OK] 所有翻译key都已找到！")
    
    # 保存报告到文件
    report_file = 'i18n_check_report.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n检查报告已保存到: {report_file}")

if __name__ == "__main__":
    main() 