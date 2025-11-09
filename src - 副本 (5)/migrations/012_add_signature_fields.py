# -*- coding: utf-8 -*-
"""
数据库迁移: 添加签名字段到Reserved_Transaction表

迁移版本: 012
创建日期: 2025-11-03
功能: 为AMLO预约表添加签名存储字段，支持报告人、客户、审核人的签名

字段说明:
- reporter_signature: 报告人签名图片(Base64 PNG或文件路径)
- customer_signature: 客户签名图片
- auditor_signature: 审核人签名图片
- signature_storage_type: 签名存储方式 (base64/file)
- signature_timestamps: JSON字段，存储各签名的时间戳
"""

import os
import sys
from sqlalchemy import text
import logging

# Ensure project root is on sys.path to reuse existing services
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.db_service import DatabaseService  # noqa: E402

logger = logging.getLogger(__name__)


def upgrade():
    """执行迁移：添加签名字段"""
    print("\n" + "="*80)
    print("[Migration 012] Adding signature fields to Reserved_Transaction")
    print("="*80 + "\n")

    with DatabaseService.get_session() as session:
        try:
            # 1. 检查表是否存在
            check_table_sql = text("""
                SELECT COUNT(*) as count
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'Reserved_Transaction'
            """)
            result = session.execute(check_table_sql).fetchone()

            if result[0] == 0:
                print("[ERROR] Reserved_Transaction table not found")
                return False

            print("[OK] Reserved_Transaction table exists")

            # 2. 检查字段是否已存在
            check_columns_sql = text("""
                SELECT COLUMN_NAME
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'Reserved_Transaction'
                  AND COLUMN_NAME IN (
                      'reporter_signature',
                      'customer_signature',
                      'auditor_signature',
                      'signature_storage_type',
                      'signature_timestamps'
                  )
            """)
            existing_columns = [row[0] for row in session.execute(check_columns_sql).fetchall()]

            if existing_columns:
                print(f"[WARNING] Fields already exist, skipping: {', '.join(existing_columns)}")

            # 3. 添加签名字段
            fields_to_add = []

            if 'reporter_signature' not in existing_columns:
                fields_to_add.append(
                    "ADD COLUMN reporter_signature TEXT DEFAULT NULL COMMENT '报告人签名(Base64 PNG或文件路径)'"
                )

            if 'customer_signature' not in existing_columns:
                fields_to_add.append(
                    "ADD COLUMN customer_signature TEXT DEFAULT NULL COMMENT '客户签名(Base64 PNG或文件路径)'"
                )

            if 'auditor_signature' not in existing_columns:
                fields_to_add.append(
                    "ADD COLUMN auditor_signature TEXT DEFAULT NULL COMMENT '审核人签名(Base64 PNG或文件路径)'"
                )

            if 'signature_storage_type' not in existing_columns:
                fields_to_add.append(
                    "ADD COLUMN signature_storage_type VARCHAR(20) DEFAULT 'base64' COMMENT '签名存储方式: base64或file'"
                )

            if 'signature_timestamps' not in existing_columns:
                fields_to_add.append(
                    "ADD COLUMN signature_timestamps JSON DEFAULT NULL COMMENT '签名时间戳JSON: {reporter: timestamp, customer: timestamp, auditor: timestamp}'"
                )

            if fields_to_add:
                alter_sql = f"""
                    ALTER TABLE Reserved_Transaction
                    {', '.join(fields_to_add)}
                """

                print(f"\n[SQL] Executing ALTER TABLE statement")
                print(f"{alter_sql}\n")

                session.execute(text(alter_sql))
                session.commit()

                print(f"[OK] Successfully added {len(fields_to_add)} signature fields")
            else:
                print("[OK] All signature fields already exist, skipping")

            # 4. 验证字段已添加
            verify_sql = text("""
                SELECT
                    COLUMN_NAME,
                    DATA_TYPE,
                    COLUMN_DEFAULT,
                    COLUMN_COMMENT
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'Reserved_Transaction'
                  AND COLUMN_NAME IN (
                      'reporter_signature',
                      'customer_signature',
                      'auditor_signature',
                      'signature_storage_type',
                      'signature_timestamps'
                  )
                ORDER BY COLUMN_NAME
            """)

            print("\n" + "-"*80)
            print("[VERIFY] Checking added fields:")
            print("-"*80)

            columns = session.execute(verify_sql).fetchall()
            for col in columns:
                print(f"  {col[0]:30} {col[1]:15} DEFAULT: {col[2] or 'NULL':10} | {col[3]}")

            # 5. 检查表中现有记录数
            count_sql = text("SELECT COUNT(*) as count FROM Reserved_Transaction")
            record_count = session.execute(count_sql).fetchone()[0]
            print(f"\n[INFO] Existing records in table: {record_count}")

            print("\n" + "="*80)
            print("[SUCCESS] Migration completed: Signature fields added")
            print("="*80 + "\n")

            return True

        except Exception as e:
            session.rollback()
            print(f"\n[ERROR] Migration failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def downgrade():
    """回滚迁移：删除签名字段"""
    print("\n" + "="*80)
    print("[Migration 012 Rollback] Removing signature fields")
    print("="*80 + "\n")

    with DatabaseService.get_session() as session:
        try:
            # 检查字段是否存在
            check_columns_sql = text("""
                SELECT COLUMN_NAME
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'Reserved_Transaction'
                  AND COLUMN_NAME IN (
                      'reporter_signature',
                      'customer_signature',
                      'auditor_signature',
                      'signature_storage_type',
                      'signature_timestamps'
                  )
            """)
            existing_columns = [row[0] for row in session.execute(check_columns_sql).fetchall()]

            if not existing_columns:
                print("[OK] Signature fields not found, nothing to rollback")
                return True

            # 删除字段
            drop_clauses = [f"DROP COLUMN {col}" for col in existing_columns]
            alter_sql = f"""
                ALTER TABLE Reserved_Transaction
                {', '.join(drop_clauses)}
            """

            print(f"[SQL] Executing DROP COLUMN statement:")
            print(f"{alter_sql}\n")

            session.execute(text(alter_sql))
            session.commit()

            print(f"[OK] Successfully removed {len(existing_columns)} signature fields")
            print("\n" + "="*80)
            print("[SUCCESS] Rollback completed")
            print("="*80 + "\n")

            return True

        except Exception as e:
            session.rollback()
            print(f"\n[ERROR] Rollback failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'downgrade':
        success = downgrade()
    else:
        success = upgrade()

    sys.exit(0 if success else 1)
