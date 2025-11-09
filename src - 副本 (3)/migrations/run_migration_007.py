# -*- coding: utf-8 -*-
"""
执行007_amlo_bot_permissions.sql迁移脚本
添加AMLO/BOT合规系统的7个新权限
版本: v1.0
创建日期: 2025-10-02
"""

import sys
import os
from pathlib import Path
import pymysql
from dotenv import load_dotenv
import codecs

# Windows UTF-8编码处理
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 获取项目根目录
project_root = Path(__file__).resolve().parent.parent

# 加载环境变量
env_path = project_root.parent / '.env'
load_dotenv(env_path)

print("=" * 70)
print("AMLO/BOT权限初始化脚本")
print("=" * 70)
print(f"项目根目录: {project_root}")
print(f"环境文件: {env_path}")
print()

def get_db_connection():
    """获取数据库连接"""
    config = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DATABASE', 'Exchange'),
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }

    print(f"数据库配置:")
    print(f"  Host: {config['host']}")
    print(f"  User: {config['user']}")
    print(f"  Database: {config['database']}")
    print()

    return pymysql.connect(**config)

def execute_sql_file(connection, sql_file_path):
    """执行SQL文件"""
    print(f"执行SQL文件: {sql_file_path}")
    print("-" * 70)

    with open(sql_file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # 分割SQL语句
    statements = []
    current_statement = []

    for line in sql_content.split('\n'):
        # 跳过注释行和空行
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith('--'):
            continue

        current_statement.append(line)

        # 如果遇到分号，则认为是一条完整的SQL语句
        if stripped_line.endswith(';'):
            statement = '\n'.join(current_statement).strip()
            if statement:
                statements.append(statement)
            current_statement = []

    # 执行SQL语句
    cursor = connection.cursor()
    success_count = 0
    failed_count = 0

    for i, statement in enumerate(statements, 1):
        try:
            # 跳过SELECT验证语句的输出控制
            if statement.strip().startswith('SELECT') and 'message' in statement:
                message_text = statement.split('as message')[0].strip().replace('SELECT ', '').replace("'", '')
                print(f"\n{message_text}")
                cursor.execute(statement.replace("as message", ""))
                continue

            cursor.execute(statement)

            # 如果是SELECT语句，打印结果
            if statement.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                if results:
                    print(f"\n查询结果 ({len(results)}条):")
                    for row in results:
                        print(f"  {row}")
            else:
                affected_rows = cursor.rowcount
                print(f"✓ 语句 {i}: 影响 {affected_rows} 行")

            success_count += 1

        except Exception as e:
            print(f"✗ 语句 {i} 失败: {str(e)}")
            print(f"  SQL: {statement[:100]}...")
            failed_count += 1

    connection.commit()
    cursor.close()

    print()
    print("=" * 70)
    print("执行统计:")
    print(f"  成功: {success_count} 条")
    print(f"  失败: {failed_count} 条")
    print("=" * 70)

    return success_count, failed_count

def verify_permissions(connection):
    """验证权限是否正确添加"""
    print("\n" + "=" * 70)
    print("验证权限...")
    print("=" * 70)

    cursor = connection.cursor()

    # 查询新增权限
    permission_names = [
        'amlo_reservation_view',
        'amlo_reservation_audit',
        'amlo_report_view',
        'amlo_report_submit',
        'bot_report_view',
        'bot_report_export',
        'compliance_config'
    ]

    placeholders = ', '.join(['%s'] * len(permission_names))
    sql = f"""
        SELECT
            p.id,
            p.permission_name,
            p.description,
            COUNT(rp.role_id) as role_count
        FROM permissions p
        LEFT JOIN role_permissions rp ON p.id = rp.permission_id
        WHERE p.permission_name IN ({placeholders})
        GROUP BY p.id, p.permission_name, p.description
        ORDER BY p.permission_name
    """

    cursor.execute(sql, permission_names)
    permissions = cursor.fetchall()

    print(f"\n找到 {len(permissions)} 个权限:")
    print(f"{'ID':<6} {'权限名称':<30} {'说明':<50} {'角色数':<10}")
    print("-" * 100)

    for perm in permissions:
        print(f"{perm['id']:<6} {perm['permission_name']:<30} {perm['description']:<50} "
              f"{perm['role_count']:<10}")

    cursor.close()

    return len(permissions) == 7

def main():
    """主函数"""
    connection = None

    try:
        # 连接数据库
        connection = get_db_connection()
        print("✓ 数据库连接成功\n")

        # 执行SQL文件
        sql_file = project_root / 'migrations' / '007_amlo_bot_permissions.sql'
        success_count, failed_count = execute_sql_file(connection, sql_file)

        if failed_count > 0:
            print("\n⚠ 警告: 有部分SQL语句执行失败")
            return 1

        # 验证权限
        if verify_permissions(connection):
            print("\n✓ 所有权限验证通过")
            print("\n" + "=" * 70)
            print("迁移完成!")
            print("=" * 70)
            return 0
        else:
            print("\n✗ 权限验证失败: 未找到全部7个权限")
            return 1

    except Exception as e:
        print(f"\n✗ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        if connection:
            connection.close()
            print("\n数据库连接已关闭")

if __name__ == '__main__':
    exit_code = main()

    print("\n按任意键退出...")
    try:
        input()
    except:
        pass

    sys.exit(exit_code)
