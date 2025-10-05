#!/usr/bin/env python3
"""
创建缺失的数据库表
"""

from services.db_service import DatabaseService, engine
from models.exchange_models import DenominationPublishDetail
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_missing_tables():
    """创建缺失的表"""
    try:
        # 使用SQLAlchemy的create_all方法
        DenominationPublishDetail.__table__.create(engine, checkfirst=True)
        logger.info("✅ 表 denomination_publish_details 创建成功")
        return True
    except Exception as e:
        logger.error(f"❌ 创建表失败: {str(e)}")
        return False

def verify_table_exists():
    """验证表是否存在"""
    session = DatabaseService.get_session()
    try:
        result = session.execute(text("SHOW TABLES LIKE 'denomination_publish_details'")).fetchall()
        exists = len(result) > 0
        logger.info(f"表 denomination_publish_details 存在: {exists}")
        return exists
    except Exception as e:
        logger.error(f"验证表存在失败: {str(e)}")
        return False
    finally:
        DatabaseService.close_session(session)

if __name__ == "__main__":
    print("开始创建缺失的数据库表...")
    
    if create_missing_tables():
        print("✅ 表创建成功")
        verify_table_exists()
    else:
        print("❌ 表创建失败")