"""
添加 institution_type 字段到 branches 表

用途：记录网点的机构类型（货币兑换商、银行、金融机构等）
这个字段用于AMLO报告中的报告机构类型自动填充

执行方式:
    python src/migrations/add_institution_type_to_branches.py

作者: Claude Code
日期: 2025-10-13
"""

import sys
import os
from sqlalchemy import Column, String, text
from sqlalchemy import inspect

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService

def add_institution_type_to_branches():
    """添加 institution_type 字段到 branches 表"""
    print("=" * 60)
    print("开始执行迁移：添加 institution_type 字段到 branches 表")
    print("=" * 60)

    db = DatabaseService()

    try:
        with db.get_session() as session:
            # 检查表是否存在
            inspector = inspect(session.bind)
            if 'branches' not in inspector.get_table_names():
                print("[ERROR] branches 表不存在，请先运行 init_db.py")
                return False

            # 检查字段是否已存在
            existing_columns = [col['name'] for col in inspector.get_columns('branches')]

            if 'institution_type' in existing_columns:
                print("[INFO] institution_type 字段已存在，跳过迁移")
                return True

            # 添加 institution_type 字段
            print("[INFO] 正在添加 institution_type 字段...")
            alter_sql = text("""
                ALTER TABLE branches
                ADD COLUMN institution_type VARCHAR(50) DEFAULT 'money_changer'
                COMMENT '机构类型：money_changer(货币兑换商)/bank(银行)/financial_institution(金融机构)/other(其他)'
            """)

            session.execute(alter_sql)
            session.commit()

            print("[OK] ✅ 成功添加 institution_type 字段到 branches 表")
            print("[INFO] 字段类型: VARCHAR(50)")
            print("[INFO] 默认值: 'money_changer'")
            print("[INFO] 可选值: money_changer, bank, financial_institution, other")

            # 验证字段已添加
            inspector = inspect(session.bind)
            columns = [col['name'] for col in inspector.get_columns('branches')]
            if 'institution_type' in columns:
                print("[OK] ✅ 字段验证成功")
                return True
            else:
                print("[ERROR] ❌ 字段验证失败")
                return False

    except Exception as e:
        print(f"[ERROR] ❌ 迁移失败: {e}")
        import traceback
        print("错误详情:")
        print(traceback.format_exc())
        return False

    finally:
        print("=" * 60)
        print("迁移脚本执行完毕")
        print("=" * 60)

if __name__ == '__main__':
    success = add_institution_type_to_branches()
    exit(0 if success else 1)
