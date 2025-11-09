#!/usr/bin/env python3
"""
数据库迁移：添加合规表的多语言字段
- report_fields表添加field_group的多语言字段
- trigger_rules表添加rule_name的多语言字段
"""

from services.db_service import DatabaseService
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    """执行迁移"""
    session = DatabaseService.get_session()
    
    try:
        # 1. 为report_fields表添加字段分组的多语言字段
        logger.info("Step 1: Adding multilingual field_group columns to report_fields table...")
        
        # 检查字段是否已存在
        check_sql = text("""
            SELECT COUNT(*) as count
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'report_fields'
            AND COLUMN_NAME IN ('field_group_cn', 'field_group_en', 'field_group_th')
        """)
        
        result = session.execute(check_sql)
        count = result.scalar()
        
        if count == 0:
            # 添加字段
            alter_sql = text("""
                ALTER TABLE report_fields
                ADD COLUMN field_group_cn VARCHAR(100) DEFAULT NULL COMMENT '字段分组-中文' AFTER field_group,
                ADD COLUMN field_group_en VARCHAR(100) DEFAULT NULL COMMENT '字段分组-英文' AFTER field_group_cn,
                ADD COLUMN field_group_th VARCHAR(100) DEFAULT NULL COMMENT '字段分组-泰文' AFTER field_group_en
            """)
            session.execute(alter_sql)
            logger.info("✅ Successfully added field_group multilingual columns")
            
            # 将现有field_group的值迁移到field_group_cn
            migrate_data_sql = text("""
                UPDATE report_fields
                SET field_group_cn = field_group
                WHERE field_group IS NOT NULL AND field_group != ''
            """)
            session.execute(migrate_data_sql)
            logger.info("✅ Migrated existing field_group data to field_group_cn")
        else:
            logger.info("⚠️ Field_group multilingual columns already exist, skipping...")
        
        # 2. 为trigger_rules表添加rule_name的多语言字段
        logger.info("Step 2: Adding multilingual rule_name columns to trigger_rules table...")
        
        # 检查字段是否已存在
        check_sql = text("""
            SELECT COUNT(*) as count
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'trigger_rules'
            AND COLUMN_NAME IN ('rule_name_en', 'rule_name_th')
        """)
        
        result = session.execute(check_sql)
        count = result.scalar()
        
        if count == 0:
            # 添加字段
            alter_sql = text("""
                ALTER TABLE trigger_rules
                ADD COLUMN rule_name_en VARCHAR(100) DEFAULT NULL COMMENT '规则名称-英文' AFTER rule_name,
                ADD COLUMN rule_name_th VARCHAR(100) DEFAULT NULL COMMENT '规则名称-泰文' AFTER rule_name_en
            """)
            session.execute(alter_sql)
            logger.info("✅ Successfully added rule_name multilingual columns")
        else:
            logger.info("⚠️ Rule_name multilingual columns already exist, skipping...")
        
        # 提交事务
        session.commit()
        logger.info("=" * 60)
        logger.info("✅ Migration completed successfully!")
        
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise
    finally:
        session.close()

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("Starting database migration: Add multilingual fields")
    logger.info("=" * 60)
    migrate()

