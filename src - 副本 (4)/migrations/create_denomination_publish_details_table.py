#!/usr/bin/env python3
"""
创建面值汇率发布详情表
"""

from services.db_service import DatabaseService, engine
from models.exchange_models import DenominationPublishDetail
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_denomination_publish_details_table():
    """创建面值汇率发布详情表"""
    session = DatabaseService.get_session()
    try:
        # 检查表是否已存在
        result = session.execute(text("SHOW TABLES LIKE 'denomination_publish_details'")).fetchall()
        if result:
            logger.info("表 denomination_publish_details 已存在")
            return True
        
        # 创建表
        create_table_sql = """
        CREATE TABLE denomination_publish_details (
            id INT AUTO_INCREMENT PRIMARY KEY,
            publish_record_id INT NOT NULL,
            currency_id INT NOT NULL,
            denomination_id INT NOT NULL,
            denomination_value DECIMAL(15,2) NOT NULL,
            denomination_type VARCHAR(20) NOT NULL,
            buy_rate DECIMAL(10,4) NOT NULL,
            sell_rate DECIMAL(10,4) NOT NULL,
            sort_order INT DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (publish_record_id) REFERENCES rate_publish_records(id) ON DELETE CASCADE,
            FOREIGN KEY (currency_id) REFERENCES currencies(id) ON DELETE CASCADE,
            FOREIGN KEY (denomination_id) REFERENCES currency_denominations(id) ON DELETE CASCADE,
            INDEX idx_publish_record_id (publish_record_id),
            INDEX idx_currency_id (currency_id),
            INDEX idx_denomination_id (denomination_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        session.execute(text(create_table_sql))
        session.commit()
        logger.info("✅ 表 denomination_publish_details 创建成功")
        return True
        
    except Exception as e:
        session.rollback()
        logger.error(f"❌ 创建表失败: {str(e)}")
        return False
    finally:
        DatabaseService.close_session(session)

def verify_table_structure():
    """验证表结构"""
    session = DatabaseService.get_session()
    try:
        # 查看表结构
        result = session.execute(text("DESCRIBE denomination_publish_details")).fetchall()
        logger.info("表结构:")
        for row in result:
            logger.info(f"  {row[0]} {row[1]} {row[2]} {row[3]} {row[4]} {row[5]}")
        return True
    except Exception as e:
        logger.error(f"验证表结构失败: {str(e)}")
        return False
    finally:
        DatabaseService.close_session(session)

if __name__ == "__main__":
    print("开始创建面值汇率发布详情表...")
    
    if create_denomination_publish_details_table():
        print("✅ 表创建成功")
        verify_table_structure()
    else:
        print("❌ 表创建失败")