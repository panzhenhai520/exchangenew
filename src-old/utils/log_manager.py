#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日志管理工具
提供日志清理、统计、轮转等功能
"""

import os
import glob
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class LogManager:
    """日志管理器"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.logger = logging.getLogger(__name__)
    
    def get_log_files(self) -> List[Dict]:
        """获取所有日志文件信息"""
        if not os.path.exists(self.log_dir):
            return []
        
        # 获取所有.log文件
        pattern = os.path.join(self.log_dir, "*.log*")
        log_files = glob.glob(pattern)
        file_list = []
        
        for log_file in sorted(log_files):
            try:
                file_stat = os.stat(log_file)
                filename = os.path.basename(log_file)
                
                file_info = {
                    'name': filename,
                    'size': self._format_file_size(file_stat.st_size),
                    'size_bytes': file_stat.st_size,
                    'modified_time': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                    'is_current': filename == 'app.log'
                }
                file_list.append(file_info)
                
            except Exception as e:
                self.logger.error(f"获取文件信息失败: {log_file}, 错误: {e}")
        
        return file_list
    
    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def get_log_stats(self) -> Dict:
        """获取日志统计信息"""
        log_files = self.get_log_files()
        
        # 计算统计信息
        total_size_bytes = sum(f['size_bytes'] for f in log_files)
        current_log_size = 0
        archived_count = 0
        
        # 查找当前日志文件大小
        for file_info in log_files:
            if file_info['is_current']:
                current_log_size = file_info['size_bytes']
        
        # 查找归档文件数量
        archive_dir = os.path.join(os.path.dirname(self.log_dir), 'archive')
        if os.path.exists(archive_dir):
            archived_count = len([f for f in os.listdir(archive_dir) if f.endswith('.log')])
        
        stats = {
            "current_log_size": self._format_file_size(current_log_size),
            "total_logs_count": len(log_files),
            "total_size": self._format_file_size(total_size_bytes),
            "archived_count": archived_count,
            "total_size_mb": round(total_size_bytes / (1024 * 1024), 2)
        }
        
        return stats
    
    def clean_old_logs(self, days: int = 30) -> int:
        """清理指定天数之前的日志文件"""
        if days <= 0:
            raise ValueError("天数必须大于0")
        
        cutoff_date = datetime.now() - timedelta(days=days)
        log_files = self.get_log_files()
        cleaned_count = 0
        
        for file_info in log_files:
            filename = file_info['name']
            # 跳过当前活动的日志文件
            if file_info['is_current']:
                continue
                
            try:
                log_file_path = os.path.join(self.log_dir, filename)
                file_stat = os.stat(log_file_path)
                modified_time = datetime.fromtimestamp(file_stat.st_mtime)
                
                if modified_time < cutoff_date:
                    os.remove(log_file_path)
                    cleaned_count += 1
                    self.logger.info(f"已删除旧日志文件: {filename}")
                    
            except Exception as e:
                self.logger.error(f"删除日志文件失败: {filename}, 错误: {e}")
        
        return cleaned_count
    
    def clean_large_logs(self, max_size_mb: int = 50) -> int:
        """清理超过指定大小的日志文件"""
        if max_size_mb <= 0:
            raise ValueError("文件大小限制必须大于0")
        
        log_files = self.get_log_files()
        cleaned_count = 0
        max_size_bytes = max_size_mb * 1024 * 1024
        
        for file_info in log_files:
            filename = file_info['name']
            # 跳过当前活动的日志文件
            if file_info['is_current']:
                continue
                
            try:
                log_file_path = os.path.join(self.log_dir, filename)
                file_stat = os.stat(log_file_path)
                
                if file_stat.st_size > max_size_bytes:
                    os.remove(log_file_path)
                    cleaned_count += 1
                    size_mb = file_stat.st_size / (1024 * 1024)
                    self.logger.info(f"已删除大日志文件: {filename} ({size_mb:.2f}MB)")
                    
            except Exception as e:
                self.logger.error(f"删除日志文件失败: {filename}, 错误: {e}")
        
        return cleaned_count
    
    def compress_old_logs(self, days: int = 7) -> int:
        """压缩指定天数之前的日志文件"""
        try:
            import gzip
            import shutil
        except ImportError:
            self.logger.error("压缩功能需要gzip模块")
            return 0
        
        if days <= 0:
            raise ValueError("天数必须大于0")
        
        cutoff_date = datetime.now() - timedelta(days=days)
        log_files = self.get_log_files()
        compressed_count = 0
        
        for file_info in log_files:
            filename = file_info['name']
            # 跳过已经压缩的文件
            if filename.endswith('.gz'):
                continue
                
            # 跳过当前活动的日志文件
            if file_info['is_current']:
                continue
                
            try:
                log_file_path = os.path.join(self.log_dir, filename)
                file_stat = os.stat(log_file_path)
                modified_time = datetime.fromtimestamp(file_stat.st_mtime)
                
                if modified_time < cutoff_date:
                    # 压缩文件
                    compressed_file_path = log_file_path + '.gz'
                    with open(log_file_path, 'rb') as f_in:
                        with gzip.open(compressed_file_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    # 删除原文件
                    os.remove(log_file_path)
                    compressed_count += 1
                    self.logger.info(f"已压缩日志文件: {filename} -> {filename}.gz")
                    
            except Exception as e:
                self.logger.error(f"压缩日志文件失败: {filename}, 错误: {e}")
        
        return compressed_count
    
    def archive_logs(self, archive_dir: str = "archive") -> int:
        """归档旧日志文件到指定目录"""
        if not os.path.exists(archive_dir):
            os.makedirs(archive_dir)
        
        log_files = self.get_log_files()
        archived_count = 0
        
        # 只归档非当前日志文件（通常是app.log.1, app.log.2等）
        for file_info in log_files:
            filename = file_info['name']
            
            # 跳过当前活动的日志文件
            if file_info['is_current']:
                continue
                
            try:
                log_file_path = os.path.join(self.log_dir, filename)
                archive_path = os.path.join(archive_dir, filename)
                
                # 如果归档文件已存在，添加时间戳
                if os.path.exists(archive_path):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    name, ext = os.path.splitext(filename)
                    archive_path = os.path.join(archive_dir, f"{name}_{timestamp}{ext}")
                
                # 移动文件到归档目录
                os.rename(log_file_path, archive_path)
                archived_count += 1
                self.logger.info(f"已归档日志文件: {filename} -> {os.path.basename(archive_path)}")
                
            except Exception as e:
                self.logger.error(f"归档日志文件失败: {filename}, 错误: {e}")
        
        return archived_count
    
    def get_log_content(self, filename: str, max_lines: int = 1000) -> str:
        """获取日志文件内容"""
        log_file_path = os.path.join(self.log_dir, filename)
        
        if not os.path.exists(log_file_path):
            raise FileNotFoundError(f"日志文件不存在: {filename}")
        
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # 限制返回的行数以避免内存问题
                if len(lines) > max_lines:
                    lines = lines[-max_lines:]
                return ''.join(lines)
        except Exception as e:
            self.logger.error(f"读取日志文件失败: {log_file_path}, 错误: {e}")
            raise
    
    def delete_log_file(self, filename: str) -> bool:
        """删除指定的日志文件"""
        log_file_path = os.path.join(self.log_dir, filename)
        
        # 不允许删除当前活动的日志文件
        if filename == "app.log":
            raise ValueError("不能删除当前活动的日志文件")
        
        if not os.path.exists(log_file_path):
            raise FileNotFoundError(f"日志文件不存在: {filename}")
        
        try:
            os.remove(log_file_path)
            self.logger.info(f"已删除日志文件: {log_file_path}")
            return True
        except Exception as e:
            self.logger.error(f"删除日志文件失败: {log_file_path}, 错误: {e}")
            raise
    
    def print_stats(self):
        """打印日志统计信息"""
        stats = self.get_log_stats()
        
        print(f"\n📊 日志统计信息:")
        print(f"   总文件数: {stats['total_files']}")
        print(f"   总大小: {stats['total_size_mb']:.2f} MB")
        print(f"   日志目录: {os.path.abspath(self.log_dir)}")
        
        if stats['files']:
            print(f"\n📁 文件详情:")
            for file_info in stats['files']:
                print(f"   {file_info['name']:<20} {file_info['size_mb']:>8.2f}MB  {file_info['modified']}  ({file_info['age_days']}天前)")
        
        print()


def main():
    """命令行工具主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ExchangeOK日志管理工具")
    parser.add_argument("--stats", action="store_true", help="显示日志统计信息")
    parser.add_argument("--clean-old", type=int, metavar="DAYS", help="清理N天前的日志文件")
    parser.add_argument("--clean-large", type=int, metavar="MB", help="清理超过N MB的日志文件")
    parser.add_argument("--compress", type=int, metavar="DAYS", help="压缩N天前的日志文件")
    parser.add_argument("--archive", action="store_true", help="归档旧日志文件")
    parser.add_argument("--log-dir", default="logs", help="日志目录路径")
    
    args = parser.parse_args()
    
    # 创建日志管理器
    log_manager = LogManager(args.log_dir)
    
    if args.stats:
        log_manager.print_stats()
    
    if args.clean_old:
        count = log_manager.clean_old_logs(args.clean_old)
        print(f"[OK] 已清理 {count} 个旧日志文件")
    
    if args.clean_large:
        count = log_manager.clean_large_logs(args.clean_large)
        print(f"[OK] 已清理 {count} 个大日志文件")
    
    if args.compress:
        count = log_manager.compress_old_logs(args.compress)
        print(f"[OK] 已压缩 {count} 个日志文件")
    
    if args.archive:
        count = log_manager.archive_logs()
        print(f"[OK] 已归档 {count} 个日志文件")
    
    # 如果没有指定任何操作，显示帮助
    if not any([args.stats, args.clean_old, args.clean_large, args.compress, args.archive]):
        parser.print_help()


if __name__ == "__main__":
    main() 