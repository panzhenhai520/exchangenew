#!/usr/bin/env python3
"""
迁移脚本：添加报表相关表
- daily_income_reports
- daily_foreign_stock  
- daily_stock_reports
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy import create_engine, text, text
from services.db_service import DatabaseService
from models.report_models import Base, DailyIncomeReport, DailyStockReport, DailyForeignStock

def add_report_tables():
    """添加报表相关表"""
    print("开始添加报表相关表...")
    
    session = DatabaseService.get_session()
    
    try:
        # 创建所有表 - 使用session的引擎
        Base.metadata.create_all(session.bind, checkfirst=True)
        print("✅ 报表相关表创建成功")
        
        # 验证表是否存在
        # 检查daily_income_reports表
        result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='daily_income_reports'"))
        if result.fetchone():
            print("✅ daily_income_reports 表存在")
        else:
            print("❌ daily_income_reports 表不存在")
        
        # 检查daily_stock_reports表
        result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='daily_stock_reports'"))
        if result.fetchone():
            print("✅ daily_stock_reports 表存在")
        else:
            print("❌ daily_stock_reports 表不存在")
        
        # 检查daily_foreign_stock表
        result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='daily_foreign_stock'"))
        if result.fetchone():
            print("✅ daily_foreign_stock 表存在")
        else:
            print("❌ daily_foreign_stock 表不存在")
        
        session.commit()
        
    except Exception as e:
        print(f"❌ 添加报表表失败: {str(e)}")
        session.rollback()
        raise
    finally:
        DatabaseService.close_session(session)
    
    print("报表表迁移完成!")

if __name__ == '__main__':
    add_report_tables() 