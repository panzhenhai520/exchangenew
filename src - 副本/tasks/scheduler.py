#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""任务调度器 - 定时执行清理任务"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging

logger = logging.getLogger(__name__)

# 全局调度器实例
scheduler = None

def init_scheduler():
    """初始化定时任务调度器"""
    global scheduler
    
    if scheduler is not None:
        logger.warning("调度器已经初始化，跳过重复初始化")
        return scheduler
    
    scheduler = BackgroundScheduler()
    
    # 添加EOD会话锁定清理任务（每小时执行）
    try:
        from tasks.cleanup_stale_eod_sessions import cleanup_stale_sessions
        
        scheduler.add_job(
            cleanup_stale_sessions,
            trigger=IntervalTrigger(hours=1),
            id='cleanup_stale_eod_sessions',
            name='清理孤立EOD会话锁定',
            replace_existing=True
        )
        
        logger.info("[OK] 已添加定时任务: 清理孤立EOD会话锁定（每小时执行）")
    except Exception as e:
        logger.error(f"添加清理任务失败: {str(e)}")
    
    # 启动调度器
    scheduler.start()
    logger.info("[OK] 任务调度器已启动")
    
    return scheduler

def shutdown_scheduler():
    """关闭调度器"""
    global scheduler
    
    if scheduler is not None:
        scheduler.shutdown()
        logger.info("任务调度器已关闭")
        scheduler = None

def get_scheduler():
    """获取调度器实例"""
    return scheduler

