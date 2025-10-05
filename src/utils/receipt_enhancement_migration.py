# 收据增强功能的数据迁移工具
from datetime import datetime
from sqlalchemy import text
from services.db_service import DatabaseService
import logging

logger = logging.getLogger(__name__)

class ReceiptEnhancementMigration:
    """收据增强功能的数据迁移工具"""

    @staticmethod
    def create_country_table():
        """创建国家信息表"""
        session = DatabaseService.get_session()
        try:
            # 检查表是否已存在
            result = session.execute(text("""
                SELECT COUNT(*)
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'countries'
            """))
            table_exists = result.scalar() > 0

            if not table_exists:
                session.execute(text("""
                    CREATE TABLE countries (
                        id INT PRIMARY KEY AUTO_INCREMENT,
                        country_code VARCHAR(2) UNIQUE NOT NULL COMMENT 'ISO 3166-1 alpha-2国家代码',
                        country_name_zh VARCHAR(100) NOT NULL COMMENT '中文国家名',
                        country_name_en VARCHAR(100) NOT NULL COMMENT '英文国家名',
                        country_name_th VARCHAR(100) NULL COMMENT '泰文国家名',
                        phone_code VARCHAR(10) NULL COMMENT '电话区号',
                        currency_code VARCHAR(3) NULL COMMENT '主要货币代码',
                        is_active BOOLEAN NOT NULL DEFAULT TRUE,
                        sort_order INT DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                    COMMENT='国家信息表'
                """))
                logger.info("已创建countries表")
                session.commit()
                return {'success': True, 'message': '国家信息表创建成功'}
            else:
                logger.info("countries表已存在，跳过创建")
                return {'success': True, 'message': '国家信息表已存在'}

        except Exception as e:
            session.rollback()
            logger.error(f"创建countries表失败: {str(e)}")
            return {'success': False, 'message': f'创建失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)

    @staticmethod
    def add_branch_receipt_fields():
        """为branches表添加收据相关字段"""
        session = DatabaseService.get_session()
        try:
            # 检查字段是否已存在
            result = session.execute(text("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'branches'
            """))
            columns = [row[0] for row in result.fetchall()]

            fields_added = []

            # 添加公司全称字段
            if 'company_full_name' not in columns:
                session.execute(text("""
                    ALTER TABLE branches
                    ADD COLUMN company_full_name VARCHAR(255) NULL
                    COMMENT '公司全称'
                """))
                fields_added.append('company_full_name')
                logger.info("已添加company_full_name字段到branches表")

            # 添加税务登记号字段
            if 'tax_registration_number' not in columns:
                session.execute(text("""
                    ALTER TABLE branches
                    ADD COLUMN tax_registration_number VARCHAR(100) NULL
                    COMMENT '税务登记号'
                """))
                fields_added.append('tax_registration_number')
                logger.info("已添加tax_registration_number字段到branches表")

            session.commit()
            return {
                'success': True,
                'message': f'网点收据信息字段更新完成，添加字段: {", ".join(fields_added)}' if fields_added else '所有字段已存在'
            }

        except Exception as e:
            session.rollback()
            logger.error(f"添加网点收据信息字段失败: {str(e)}")
            return {'success': False, 'message': f'添加字段失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)

    @staticmethod
    def add_transaction_payment_fields():
        """为exchange_transactions表添加付款方式和语言相关字段"""
        session = DatabaseService.get_session()
        try:
            # 检查字段是否已存在
            result = session.execute(text("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'exchange_transactions'
            """))
            columns = [row[0] for row in result.fetchall()]

            fields_added = []

            # 添加付款方式字段
            if 'payment_method' not in columns:
                session.execute(text("""
                    ALTER TABLE exchange_transactions
                    ADD COLUMN payment_method VARCHAR(50) DEFAULT 'cash'
                    COMMENT '付款方式: cash, bank_transfer, fcd_account, other'
                """))
                fields_added.append('payment_method')
                logger.info("已添加payment_method字段到exchange_transactions表")

            # 添加付款方式备注字段
            if 'payment_method_note' not in columns:
                session.execute(text("""
                    ALTER TABLE exchange_transactions
                    ADD COLUMN payment_method_note VARCHAR(200) NULL
                    COMMENT '付款方式备注（当选择"其他"时填写）'
                """))
                fields_added.append('payment_method_note')
                logger.info("已添加payment_method_note字段到exchange_transactions表")

            # 添加收据打印语言字段
            if 'receipt_language' not in columns:
                session.execute(text("""
                    ALTER TABLE exchange_transactions
                    ADD COLUMN receipt_language VARCHAR(5) DEFAULT 'zh'
                    COMMENT '收据打印语言: zh, en, th'
                """))
                fields_added.append('receipt_language')
                logger.info("已添加receipt_language字段到exchange_transactions表")

            # 添加签发国家代码字段
            if 'issuing_country_code' not in columns:
                session.execute(text("""
                    ALTER TABLE exchange_transactions
                    ADD COLUMN issuing_country_code VARCHAR(2) NULL
                    COMMENT '签发国家代码'
                """))
                fields_added.append('issuing_country_code')
                logger.info("已添加issuing_country_code字段到exchange_transactions表")

            session.commit()
            return {
                'success': True,
                'message': f'交易付款信息字段更新完成，添加字段: {", ".join(fields_added)}' if fields_added else '所有字段已存在'
            }

        except Exception as e:
            session.rollback()
            logger.error(f"添加交易付款信息字段失败: {str(e)}")
            return {'success': False, 'message': f'添加字段失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)

    @staticmethod
    def run_all_migrations():
        """执行所有迁移"""
        results = []

        # 1. 创建国家表
        result1 = ReceiptEnhancementMigration.create_country_table()
        results.append(result1)

        # 2. 添加网点收据字段
        result2 = ReceiptEnhancementMigration.add_branch_receipt_fields()
        results.append(result2)

        # 3. 添加交易付款字段
        result3 = ReceiptEnhancementMigration.add_transaction_payment_fields()
        results.append(result3)

        # 汇总结果
        all_success = all(r['success'] for r in results)
        messages = [r['message'] for r in results]

        return {
            'success': all_success,
            'message': '\n'.join(messages),
            'details': results
        }
