#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AMLO和BOT合规报告系统 - 数据库迁移执行脚本
版本: v1.0
创建日期: 2025-10-02
说明: 执行AMLO/BOT合规报告系统的数据库迁移
"""

import os
import sys
from pathlib import Path

# 设置Windows控制台UTF-8编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import pymysql
from dotenv import load_dotenv


def get_db_connection():
    """获取数据库连接"""
    # 加载环境变量
    env_path = project_root.parent / '.env'
    load_dotenv(env_path)

    # 从环境变量获取数据库配置（使用MYSQL_前缀）
    config = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DATABASE', 'Exchange'),
        'charset': os.getenv('MYSQL_CHARSET', 'utf8mb4')
    }

    return pymysql.connect(**config)


def read_sql_file(file_path):
    """读取SQL文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"❌ 读取SQL文件失败: {file_path}")
        print(f"   错误: {str(e)}")
        return None


def execute_sql_statements(cursor, sql_content, description):
    """执行SQL语句（处理多语句）"""
    print(f"\n📋 开始执行: {description}")

    # 分割SQL语句（按分号分隔，但忽略存储过程中的分号）
    statements = []
    current_statement = []
    in_delimiter = False

    for line in sql_content.split('\n'):
        stripped_line = line.strip()

        # 跳过注释和空行
        if not stripped_line or stripped_line.startswith('--'):
            continue

        # 检测DELIMITER关键字
        if stripped_line.startswith('DELIMITER'):
            in_delimiter = not in_delimiter
            continue

        current_statement.append(line)

        # 如果不在DELIMITER块中，检查分号结尾
        if not in_delimiter and stripped_line.endswith(';'):
            statement = '\n'.join(current_statement).strip()
            if statement:
                statements.append(statement)
            current_statement = []

    # 添加最后一条语句
    if current_statement:
        statement = '\n'.join(current_statement).strip()
        if statement:
            statements.append(statement)

    # 执行每条语句
    success_count = 0
    error_count = 0

    for i, statement in enumerate(statements, 1):
        try:
            # 跳过SET命令（某些MySQL版本可能不支持）
            if statement.upper().startswith('SET FOREIGN_KEY_CHECKS') or \
               statement.upper().startswith('SET NAMES'):
                cursor.execute(statement)
                continue

            # 执行语句
            cursor.execute(statement)
            success_count += 1

            # 对于CREATE TABLE和INSERT语句，显示详细信息
            if statement.upper().startswith('CREATE TABLE'):
                table_name = statement.split('`')[1] if '`' in statement else 'unknown'
                print(f"   ✓ [{i}/{len(statements)}] 创建表: {table_name}")
            elif statement.upper().startswith('INSERT INTO'):
                table_name = statement.split('`')[1] if '`' in statement else 'unknown'
                print(f"   ✓ [{i}/{len(statements)}] 插入数据: {table_name}")
            elif statement.upper().startswith('ALTER TABLE'):
                table_name = statement.split('`')[1] if '`' in statement else 'unknown'
                print(f"   ✓ [{i}/{len(statements)}] 修改表: {table_name}")
            else:
                print(f"   ✓ [{i}/{len(statements)}] 执行成功")

        except pymysql.Error as e:
            error_count += 1
            print(f"   ✗ [{i}/{len(statements)}] 执行失败: {e}")
            # 对于非关键错误（如表已存在），继续执行
            if e.args[0] not in (1050, 1060, 1061):  # Table exists, Column exists, Duplicate key
                raise

    print(f"\n   📊 执行结果: 成功 {success_count} 条, 失败 {error_count} 条")
    return success_count, error_count


def run_migration():
    """执行数据库迁移"""
    print("=" * 70)
    print("🚀 AMLO和BOT合规报告系统 - 数据库迁移")
    print("=" * 70)

    # 获取SQL文件路径
    migration_dir = Path(__file__).parent
    schema_file = migration_dir / '006_amlo_bot_compliance.sql'
    data_file = migration_dir / '006_amlo_bot_compliance_data.sql'

    # 检查文件是否存在
    if not schema_file.exists():
        print(f"❌ SQL文件不存在: {schema_file}")
        return False

    if not data_file.exists():
        print(f"❌ SQL文件不存在: {data_file}")
        return False

    # 读取SQL文件
    print("\n📖 读取SQL文件...")
    schema_sql = read_sql_file(schema_file)
    data_sql = read_sql_file(data_file)

    if not schema_sql or not data_sql:
        return False

    print(f"   ✓ 读取表结构SQL文件: {schema_file.name}")
    print(f"   ✓ 读取初始化数据SQL文件: {data_file.name}")

    # 连接数据库
    print("\n🔌 连接数据库...")
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        print("   ✓ 数据库连接成功")
    except Exception as e:
        print(f"   ❌ 数据库连接失败: {str(e)}")
        return False

    try:
        # 执行表结构SQL
        success1, error1 = execute_sql_statements(
            cursor,
            schema_sql,
            "创建表结构"
        )
        connection.commit()

        # 执行初始化数据SQL
        success2, error2 = execute_sql_statements(
            cursor,
            data_sql,
            "初始化数据"
        )
        connection.commit()

        # 验证迁移结果
        print("\n🔍 验证迁移结果...")

        # 检查关键表是否创建成功
        tables_to_check = [
            'report_fields',
            'trigger_rules',
            'Reserved_Transaction',
            'AMLOReport',
            'BOT_BuyFX',
            'BOT_SellFX',
            'BOT_Provider',
            'BOT_FCD',
            'funding_sources',
            'audit_log'
        ]

        for table_name in tables_to_check:
            cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
            result = cursor.fetchone()
            if result:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"   ✓ 表 {table_name} 存在 (记录数: {count})")
            else:
                print(f"   ✗ 表 {table_name} 不存在")

        # 检查exchange_transactions表是否添加了新字段
        cursor.execute("DESCRIBE exchange_transactions")
        columns = [row[0] for row in cursor.fetchall()]
        new_fields = [
            'seqno', 'exchange_type', 'approval_serial', 'funding_source',
            'occupation', 'workplace', 'work_phone', 'id_expiry_date',
            'asset_details', 'bot_flag', 'fcd_flag', 'use_fcd'
        ]

        print(f"\n   检查exchange_transactions表新增字段:")
        for field in new_fields:
            if field in columns:
                print(f"   ✓ 字段 {field} 已添加")
            else:
                print(f"   ✗ 字段 {field} 未添加")

        print("\n" + "=" * 70)
        print("✅ 数据库迁移完成！")
        print("=" * 70)
        print(f"\n📊 迁移统计:")
        print(f"   - 成功执行语句: {success1 + success2} 条")
        print(f"   - 失败语句: {error1 + error2} 条")
        print(f"   - 创建表: {len(tables_to_check)} 张")
        print(f"   - 扩展字段: {len(new_fields)} 个")

        return True

    except Exception as e:
        print(f"\n❌ 迁移执行失败: {str(e)}")
        connection.rollback()
        return False

    finally:
        cursor.close()
        connection.close()
        print("\n🔌 数据库连接已关闭")


if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)
