# 双向交易和增强收据信息的数据迁移工具
from datetime import datetime
from sqlalchemy import text
from services.db_service import DatabaseService
import logging

logger = logging.getLogger(__name__)

class DualDirectionMigrationTools:
    """双向交易和增强收据信息的数据迁移工具"""

    @staticmethod
    def add_transaction_group_fields():
        """为exchange_transactions表添加业务组字段，支持双向交易拆分"""
        session = DatabaseService.get_session()
        try:
            # 检查字段是否已存在 (MySQL版本)
            result = session.execute(text("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'exchange_transactions'
            """))
            columns = [row[0] for row in result.fetchall()]

            fields_added = []

            # 添加业务组ID字段
            if 'business_group_id' not in columns:
                session.execute(text("ALTER TABLE exchange_transactions ADD COLUMN business_group_id VARCHAR(50) NULL"))
                fields_added.append('business_group_id')
                logger.info("已添加business_group_id字段到exchange_transactions表")

            # 添加组内序号字段
            if 'group_sequence' not in columns:
                session.execute(text("ALTER TABLE exchange_transactions ADD COLUMN group_sequence INTEGER DEFAULT 1"))
                fields_added.append('group_sequence')
                logger.info("已添加group_sequence字段到exchange_transactions表")

            # 添加交易方向字段（显式记录买入/卖出）
            if 'transaction_direction' not in columns:
                session.execute(text("ALTER TABLE exchange_transactions ADD COLUMN transaction_direction VARCHAR(20) NULL"))
                fields_added.append('transaction_direction')
                logger.info("已添加transaction_direction字段到exchange_transactions表")

            session.commit()
            return {
                'success': True,
                'message': f'交易表结构更新完成，添加字段: {", ".join(fields_added)}' if fields_added else '所有字段已存在'
            }

        except Exception as e:
            session.rollback()
            logger.error(f"添加交易组字段失败: {str(e)}")
            return {'success': False, 'message': f'添加字段失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)

    @staticmethod
    def add_customer_enhanced_fields():
        """为exchange_transactions表添加增强的客户信息字段，用于80mm收据"""
        session = DatabaseService.get_session()
        try:
            # 检查字段是否已存在 (MySQL版本)
            result = session.execute(text("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'exchange_transactions'
            """))
            columns = [row[0] for row in result.fetchall()]

            fields_added = []

            # 添加客户国家代码字段
            if 'customer_country_code' not in columns:
                session.execute(text("ALTER TABLE exchange_transactions ADD COLUMN customer_country_code VARCHAR(5) NULL"))
                fields_added.append('customer_country_code')
                logger.info("已添加customer_country_code字段到exchange_transactions表")

            # 添加客户地址字段
            if 'customer_address' not in columns:
                session.execute(text("ALTER TABLE exchange_transactions ADD COLUMN customer_address TEXT NULL"))
                fields_added.append('customer_address')
                logger.info("已添加customer_address字段到exchange_transactions表")

            session.commit()
            return {
                'success': True,
                'message': f'客户信息字段更新完成，添加字段: {", ".join(fields_added)}' if fields_added else '所有字段已存在'
            }

        except Exception as e:
            session.rollback()
            logger.error(f"添加客户信息字段失败: {str(e)}")
            return {'success': False, 'message': f'添加字段失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)

    @staticmethod
    def add_branch_enhanced_fields():
        """为branches表添加增强的网点信息字段，用于80mm收据"""
        session = DatabaseService.get_session()
        try:
            # 检查字段是否已存在 (MySQL版本)
            result = session.execute(text("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'branches'
            """))
            columns = [row[0] for row in result.fetchall()]

            fields_added = []

            # 添加许可证编号字段
            if 'license_number' not in columns:
                session.execute(text("ALTER TABLE branches ADD COLUMN license_number VARCHAR(100) NULL"))
                fields_added.append('license_number')
                logger.info("已添加license_number字段到branches表")

            # 添加网址字段
            if 'website' not in columns:
                session.execute(text("ALTER TABLE branches ADD COLUMN website VARCHAR(255) NULL"))
                fields_added.append('website')
                logger.info("已添加website字段到branches表")

            # 添加公司名称字段（收据抬头）
            if 'company_name' not in columns:
                session.execute(text("ALTER TABLE branches ADD COLUMN company_name VARCHAR(200) NULL"))
                fields_added.append('company_name')
                logger.info("已添加company_name字段到branches表")

            # 添加纳税人识别号字段
            if 'tax_id' not in columns:
                session.execute(text("ALTER TABLE branches ADD COLUMN tax_id VARCHAR(50) NULL"))
                fields_added.append('tax_id')
                logger.info("已添加tax_id字段到branches表")

            # 添加收据模板类型字段
            if 'receipt_template_type' not in columns:
                session.execute(text("ALTER TABLE branches ADD COLUMN receipt_template_type VARCHAR(20) DEFAULT '80mm'"))
                fields_added.append('receipt_template_type')
                logger.info("已添加receipt_template_type字段到branches表")

            session.commit()
            return {
                'success': True,
                'message': f'网点信息字段更新完成，添加字段: {", ".join(fields_added)}' if fields_added else '所有字段已存在'
            }

        except Exception as e:
            session.rollback()
            logger.error(f"添加网点信息字段失败: {str(e)}")
            return {'success': False, 'message': f'添加字段失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)

    @staticmethod
    def backfill_transaction_direction_data():
        """为现有交易记录补填transaction_direction字段"""
        session = DatabaseService.get_session()
        try:
            updated_count = 0

            # 获取所有缺少交易方向的记录
            transactions = session.execute(text("""
                SELECT id, type FROM exchange_transactions
                WHERE transaction_direction IS NULL OR transaction_direction = ''
            """)).fetchall()

            for transaction in transactions:
                transaction_id, transaction_type = transaction

                # 根据现有的type字段推断交易方向
                if transaction_type in ['buy', 'sell']:
                    direction = transaction_type
                elif transaction_type in ['sell_foreign', 'customer_sell_foreign']:
                    direction = 'sell'  # 网点买入外币
                elif transaction_type in ['buy_foreign', 'customer_buy_foreign']:
                    direction = 'buy'   # 网点卖出外币
                else:
                    direction = 'unknown'

                session.execute(text("""
                    UPDATE exchange_transactions
                    SET transaction_direction = :direction
                    WHERE id = :transaction_id
                """), {'direction': direction, 'transaction_id': transaction_id})

                updated_count += 1

            session.commit()
            return {
                'success': True,
                'message': f'交易方向数据补填完成，更新了 {updated_count} 条记录'
            }

        except Exception as e:
            session.rollback()
            logger.error(f"补填交易方向数据失败: {str(e)}")
            return {'success': False, 'message': f'补填数据失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)

    @staticmethod
    def run_all_migrations():
        """运行所有双向交易相关的数据迁移"""
        results = []

        logger.info("开始执行双向交易数据迁移...")

        # 1. 添加交易组字段
        result1 = DualDirectionMigrationTools.add_transaction_group_fields()
        results.append(f"交易组字段: {result1['message']}")

        # 2. 添加客户信息字段
        result2 = DualDirectionMigrationTools.add_customer_enhanced_fields()
        results.append(f"客户信息字段: {result2['message']}")

        # 3. 添加网点信息字段
        result3 = DualDirectionMigrationTools.add_branch_enhanced_fields()
        results.append(f"网点信息字段: {result3['message']}")

        # 4. 补填交易方向数据
        result4 = DualDirectionMigrationTools.backfill_transaction_direction_data()
        results.append(f"交易方向数据: {result4['message']}")

        # 检查是否有任何失败
        all_success = all(result['success'] for result in [result1, result2, result3, result4])

        logger.info("双向交易数据迁移完成")

        return {
            'success': all_success,
            'message': '所有迁移完成' if all_success else '部分迁移失败',
            'details': results
        }

    @staticmethod
    def validate_migration():
        """验证迁移是否成功"""
        session = DatabaseService.get_session()
        try:
            validation_results = []

            # 验证exchange_transactions表字段 (MySQL版本)
            result = session.execute(text("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'exchange_transactions'
            """))
            transaction_columns = [row[0] for row in result.fetchall()]

            required_transaction_fields = [
                'business_group_id', 'group_sequence', 'transaction_direction',
                'customer_country_code', 'customer_address'
            ]

            for field in required_transaction_fields:
                if field in transaction_columns:
                    validation_results.append(f"✅ exchange_transactions.{field} 字段存在")
                else:
                    validation_results.append(f"❌ exchange_transactions.{field} 字段缺失")

            # 验证branches表字段 (MySQL版本)
            result = session.execute(text("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'branches'
            """))
            branch_columns = [row[0] for row in result.fetchall()]

            required_branch_fields = [
                'license_number', 'website', 'company_name', 'tax_id', 'receipt_template_type'
            ]

            for field in required_branch_fields:
                if field in branch_columns:
                    validation_results.append(f"✅ branches.{field} 字段存在")
                else:
                    validation_results.append(f"❌ branches.{field} 字段缺失")

            # 检查交易方向数据补填情况 (只在字段存在时检查)
            if 'transaction_direction' in transaction_columns:
                result = session.execute(text("""
                    SELECT
                        COUNT(*) as total,
                        COUNT(CASE WHEN transaction_direction IS NOT NULL AND transaction_direction != '' THEN 1 END) as filled
                    FROM exchange_transactions
                """)).first()

                if result:
                    total, filled = result
                    validation_results.append(f"✅ 交易方向字段补填: {filled}/{total} 条记录")
            else:
                validation_results.append("❌ transaction_direction字段不存在，无法检查数据补填情况")

            return {
                'success': True,
                'message': '迁移验证完成',
                'details': validation_results
            }

        except Exception as e:
            logger.error(f"迁移验证失败: {str(e)}")
            return {'success': False, 'message': f'验证失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)