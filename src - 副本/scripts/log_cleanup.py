#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ExchangeOK 日志清理脚本
用于定期清理旧日志文件，可配置为Windows定时任务或cron作业
"""

import os
import sys
import logging
from datetime import datetime

# 添加父目录到路径以便导入utils模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.log_manager import LogManager

# 配置清理脚本的日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join("logs", "cleanup.log"), encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """主清理函数"""
    logger.info("=== 开始日志清理任务 ===")
    
    try:
        # 创建日志管理器
        log_manager = LogManager("logs")
        
        # 获取清理前的统计信息
        stats_before = log_manager.get_log_stats()
        logger.info(f"清理前: {stats_before['total_files']}个文件, {stats_before['total_size_mb']:.2f}MB")
        
        total_cleaned = 0
        
        # 1. 清理30天前的旧日志
        old_count = log_manager.clean_old_logs(days=30)
        total_cleaned += old_count
        if old_count > 0:
            logger.info(f"清理了 {old_count} 个30天前的旧日志文件")
        
        # 2. 清理超过100MB的大日志文件
        large_count = log_manager.clean_large_logs(max_size_mb=100)
        total_cleaned += large_count
        if large_count > 0:
            logger.info(f"清理了 {large_count} 个超过100MB的大日志文件")
        
        # 3. 压缩7天前的日志文件
        compressed_count = log_manager.compress_old_logs(days=7)
        if compressed_count > 0:
            logger.info(f"压缩了 {compressed_count} 个7天前的日志文件")
        
        # 4. 归档轮转的日志文件
        archived_count = log_manager.archive_logs()
        if archived_count > 0:
            logger.info(f"归档了 {archived_count} 个轮转的日志文件")
        
        # 获取清理后的统计信息
        stats_after = log_manager.get_log_stats()
        logger.info(f"清理后: {stats_after['total_files']}个文件, {stats_after['total_size_mb']:.2f}MB")
        
        # 计算节省的空间
        space_saved = stats_before['total_size_mb'] - stats_after['total_size_mb']
        if space_saved > 0:
            logger.info(f"节省磁盘空间: {space_saved:.2f}MB")
        
        if total_cleaned == 0 and compressed_count == 0 and archived_count == 0:
            logger.info("没有需要清理的日志文件")
        
        logger.info("=== 日志清理任务完成 ===")
        
    except Exception as e:
        logger.error(f"日志清理任务失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 