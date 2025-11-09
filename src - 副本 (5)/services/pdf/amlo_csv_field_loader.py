# -*- coding: utf-8 -*-
"""
AMLO CSV字段映射加载器
从CSV文件加载PDF字段填充位置配置

CSV格式:
page,field_name,type,nearby_th_label

支持的字段类型:
- text: 文本字段
- checkbox: 复选框字段
- comb: 组合字段(如身份证号码的单个字符框)
"""

import os
import csv
from typing import Dict, List, Tuple
from datetime import datetime


class AMLOCSVFieldLoader:
    """AMLO CSV字段映射加载器"""

    def __init__(self, csv_dir=None):
        """
        初始化加载器

        Args:
            csv_dir: CSV文件目录,默认为Re目录
        """
        if csv_dir is None:
            # 默认使用Re目录
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            csv_dir = os.path.join(project_root, 'Re')

        self.csv_dir = csv_dir
        self.field_mappings = {}
        self._load_all_mappings()

    def _load_all_mappings(self):
        """加载所有CSV映射文件"""
        csv_files = {
            'AMLO-1-01': '1-01-field-map.csv',
            'AMLO-1-02': '1-02-field-map.csv',
            'AMLO-1-03': '1-03-field-map.csv'
        }

        for report_type, csv_file in csv_files.items():
            csv_path = os.path.join(self.csv_dir, csv_file)
            if os.path.exists(csv_path):
                self.field_mappings[report_type] = self._load_csv(csv_path)
                print(f"[AMLOCSVFieldLoader] Loaded {report_type}: {len(self.field_mappings[report_type])} fields")
            else:
                print(f"[AMLOCSVFieldLoader] Warning: {csv_path} not found")
                self.field_mappings[report_type] = {}

    def _load_csv(self, csv_path: str) -> Dict[str, Dict]:
        """
        从CSV文件加载字段映射

        Returns:
            {
                'field_name': {
                    'page': 1,
                    'type': 'text',
                    'label': 'nearby_th_label'
                },
                ...
            }
        """
        field_map = {}

        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    page = int(row['page']) if row['page'] else 1
                    field_name = row['field_name'].strip()
                    field_type = row['type'].strip().lower()
                    label = row['nearby_th_label'].strip()

                    # 处理复合字段名(如 fill_5、fill_5_2 或 fill_4、fill_4_2)
                    field_names = [fn.strip() for fn in field_name.split('、')]

                    for fn in field_names:
                        if not fn:
                            continue

                        field_map[fn] = {
                            'page': page,
                            'type': field_type,
                            'label': label,
                            'original_name': field_name  # 保留原始复合字段名
                        }

            return field_map

        except Exception as e:
            print(f"[AMLOCSVFieldLoader] Error loading {csv_path}: {e}")
            return {}

    def get_field_mapping(self, report_type: str) -> Dict[str, Dict]:
        """
        获取指定报告类型的字段映射

        Args:
            report_type: 报告类型 ('AMLO-1-01', 'AMLO-1-02', 'AMLO-1-03')

        Returns:
            字段映射字典
        """
        return self.field_mappings.get(report_type, {})

    def get_field_info(self, report_type: str, field_name: str) -> Dict:
        """
        获取指定字段的信息

        Args:
            report_type: 报告类型
            field_name: 字段名称

        Returns:
            字段信息字典,如果字段不存在则返回None
        """
        mapping = self.get_field_mapping(report_type)
        return mapping.get(field_name)

    def get_fields_by_page(self, report_type: str, page: int) -> Dict[str, Dict]:
        """
        获取指定页面的所有字段

        Args:
            report_type: 报告类型
            page: 页码

        Returns:
            该页面的字段映射字典
        """
        mapping = self.get_field_mapping(report_type)
        return {
            field_name: field_info
            for field_name, field_info in mapping.items()
            if field_info['page'] == page
        }

    def get_fields_by_type(self, report_type: str, field_type: str) -> Dict[str, Dict]:
        """
        获取指定类型的所有字段

        Args:
            report_type: 报告类型
            field_type: 字段类型 ('text', 'checkbox', 'comb')

        Returns:
            该类型的字段映射字典
        """
        mapping = self.get_field_mapping(report_type)
        return {
            field_name: field_info
            for field_name, field_info in mapping.items()
            if field_info['type'] == field_type.lower()
        }

    def list_all_fields(self, report_type: str) -> List[str]:
        """
        列出报告的所有字段名

        Args:
            report_type: 报告类型

        Returns:
            字段名列表
        """
        mapping = self.get_field_mapping(report_type)
        return sorted(mapping.keys())

    def get_template_path(self, report_type: str) -> str:
        """
        获取PDF模板路径

        Args:
            report_type: 报告类型

        Returns:
            模板文件的完整路径
        """
        template_files = {
            'AMLO-1-01': '1-01-fill.pdf',
            'AMLO-1-02': '1-02-fill.pdf',
            'AMLO-1-03': '1-03-fill.pdf'
        }

        template_file = template_files.get(report_type)
        if not template_file:
            raise ValueError(f"Unknown report type: {report_type}")

        template_path = os.path.join(self.csv_dir, template_file)

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found: {template_path}")

        return template_path

    def get_statistics(self, report_type: str) -> Dict:
        """
        获取字段统计信息

        Args:
            report_type: 报告类型

        Returns:
            统计信息字典
        """
        mapping = self.get_field_mapping(report_type)

        if not mapping:
            return {
                'total_fields': 0,
                'by_type': {},
                'by_page': {}
            }

        # 按类型统计
        by_type = {}
        for field_info in mapping.values():
            field_type = field_info['type']
            by_type[field_type] = by_type.get(field_type, 0) + 1

        # 按页码统计
        by_page = {}
        for field_info in mapping.values():
            page = field_info['page']
            by_page[page] = by_page.get(page, 0) + 1

        return {
            'total_fields': len(mapping),
            'by_type': by_type,
            'by_page': by_page
        }


# 全局单例实例
_loader_instance = None


def get_csv_field_loader() -> AMLOCSVFieldLoader:
    """获取CSV字段加载器的全局单例实例"""
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = AMLOCSVFieldLoader()
    return _loader_instance


# 测试代码
if __name__ == '__main__':
    loader = AMLOCSVFieldLoader()

    for report_type in ['AMLO-1-01', 'AMLO-1-02', 'AMLO-1-03']:
        print(f"\n{'='*60}")
        print(f"Report Type: {report_type}")
        print(f"{'='*60}")

        stats = loader.get_statistics(report_type)
        print(f"Total fields: {stats['total_fields']}")
        print(f"By type: {stats['by_type']}")
        print(f"By page: {stats['by_page']}")

        # 显示前5个字段
        fields = loader.list_all_fields(report_type)
        print(f"\nFirst 5 fields:")
        for field_name in fields[:5]:
            field_info = loader.get_field_info(report_type, field_name)
            print(f"  {field_name}: {field_info}")
