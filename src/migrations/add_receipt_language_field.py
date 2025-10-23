#!/usr/bin/env python3
"""
数据库迁移脚本：为exchange_transactions表添加receipt_language和issuing_country_code字段
"""

import sys
import os
from sqlalchemy import text

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_receipt_language_field():
    """为exchange_transactions表添加receipt_language和issuing_country_code字段"""

    session = None
    try:
        session = DatabaseService.get_session()

        logger.info("开始为exchange_transactions表添加新字段...")

        # 检查receipt_language字段是否已存在
        check_receipt_language_sql = """
        SELECT COUNT(*)
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'exchange_transactions'
        AND COLUMN_NAME = 'receipt_language'
        """
        result = session.execute(text(check_receipt_language_sql)).scalar()

        if result == 0:
            # 添加receipt_language字段
            alter_sql = """
            ALTER TABLE exchange_transactions
            ADD COLUMN receipt_language VARCHAR(5) DEFAULT 'zh'
            COMMENT '收据打印语言: zh, en, th'
            AFTER payment_method_note
            """
            logger.info(f"执行SQL: {alter_sql}")
            session.execute(text(alter_sql))
            session.commit()
            logger.info("✅ 成功添加字段: receipt_language")
        else:
            logger.info("⚠️ 字段已存在，跳过: receipt_language")

        # 检查issuing_country_code字段是否已存在
        check_issuing_country_sql = """
        SELECT COUNT(*)
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'exchange_transactions'
        AND COLUMN_NAME = 'issuing_country_code'
        """
        result = session.execute(text(check_issuing_country_sql)).scalar()

        if result == 0:
            # 添加issuing_country_code字段
            alter_sql = """
            ALTER TABLE exchange_transactions
            ADD COLUMN issuing_country_code VARCHAR(2)
            COMMENT '签发国家代码'
            AFTER receipt_language
            """
            logger.info(f"执行SQL: {alter_sql}")
            session.execute(text(alter_sql))
            session.commit()
            logger.info("✅ 成功添加字段: issuing_country_code")
        else:
            logger.info("⚠️ 字段已存在，跳过: issuing_country_code")

        logger.info("✅ 所有字段添加完成")
        return True

    except Exception as e:
        logger.error(f"❌ 添加字段失败: {str(e)}")
        if session:
            session.rollback()
        return False

    finally:
        if session:
            DatabaseService.close_session(session)

def verify_migration():
    """验证迁移结果"""
    session = None
    try:
        session = DatabaseService.get_session()

        # 测试查询新字段
        result = session.execute(text("SELECT receipt_language, issuing_country_code FROM exchange_transactions LIMIT 1"))
        logger.info("✅ 新字段查询测试成功")

        return True

    except Exception as e:
        logger.error(f"❌ 验证迁移失败: {str(e)}")
        return False

    finally:
        if session:
            DatabaseService.close_session(session)

if __name__ == "__main__":
    logger.info("🚀 开始数据库迁移...")

    if add_receipt_language_field():
        logger.info("✅ 字段添加成功，开始验证...")
        if verify_migration():
            logger.info("🎉 数据库迁移完成并验证成功！")
        else:
            logger.error("❌ 迁移验证失败")
    else:
        logger.error("❌ 数据库迁移失败")
