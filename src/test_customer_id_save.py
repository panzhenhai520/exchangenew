# -*- coding: utf-8 -*-
"""
测试customer_id保存问题
检查Reserved_Transaction表中的customer_id字段
"""

from services.db_service import SessionLocal
from sqlalchemy import text

def main():
    print("=" * 80)
    print("检查Reserved_Transaction表中的customer_id字段")
    print("=" * 80)

    session = SessionLocal()

    try:
        # 查询最近的预约记录
        sql = text("""
            SELECT
                id,
                reservation_no,
                customer_id,
                customer_name,
                report_type,
                local_amount,
                status,
                branch_id,
                created_at
            FROM Reserved_Transaction
            ORDER BY created_at DESC
            LIMIT 10
        """)

        result = session.execute(sql)
        rows = result.fetchall()

        if not rows:
            print("\n[警告] Reserved_Transaction表中没有数据")
            return

        print(f"\n找到 {len(rows)} 条预约记录:\n")
        print(f"{'ID':<6} {'预约编号':<25} {'customer_id':<20} {'客户姓名':<15} {'报告类型':<12} {'本币金额':<12} {'状态':<10}")
        print("-" * 120)

        empty_count = 0
        for row in rows:
            id_val = row[0]
            reservation_no = row[1]
            customer_id = row[2] or "[空]"
            customer_name = row[3] or "-"
            report_type = row[4]
            local_amount = row[5]
            status = row[6]

            if not row[2]:
                empty_count += 1
                customer_id = f"[空] [WARNING]"

            print(f"{id_val:<6} {reservation_no:<25} {customer_id:<20} {customer_name:<15} {report_type:<12} {local_amount:<12,.2f} {status:<10}")

        print("-" * 120)
        print(f"\n统计:")
        print(f"  总记录数: {len(rows)}")
        print(f"  customer_id为空的记录: {empty_count}")
        print(f"  customer_id有值的记录: {len(rows) - empty_count}")

        if empty_count > 0:
            print(f"\n[严重问题] 发现 {empty_count} 条记录的customer_id为空!")
            print("这些记录可能是在修复前创建的，或者前端没有正确传递customer_id。")
        else:
            print("\n[良好] 所有记录的customer_id都有值。")

        # 检查表结构
        print("\n" + "=" * 80)
        print("检查Reserved_Transaction表结构")
        print("=" * 80)

        describe_sql = text("""
            DESCRIBE Reserved_Transaction
        """)

        describe_result = session.execute(describe_sql)
        columns = describe_result.fetchall()

        print("\ncustomer_id字段定义:")
        for col in columns:
            if col[0] == 'customer_id':
                print(f"  字段名: {col[0]}")
                print(f"  类型: {col[1]}")
                print(f"  允许NULL: {col[2]}")
                print(f"  键: {col[3]}")
                print(f"  默认值: {col[4]}")
                print(f"  额外信息: {col[5]}")
                break

    finally:
        session.close()

if __name__ == '__main__':
    main()
