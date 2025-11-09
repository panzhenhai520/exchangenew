"""
修复DashboardPublishRecord表的唯一约束问题
"""

import sqlite3
from datetime import datetime
import os

def run_migration():
    """运行迁移"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'exchange_system.db')
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("开始修复DashboardPublishRecord表的唯一约束...")
        
        # 1. 检查当前表结构
        cursor.execute("PRAGMA table_info(dashboard_publish_records)")
        columns = cursor.fetchall()
        print(f"当前表结构: {[col[1] for col in columns]}")
        
        # 2. 检查是否存在唯一约束冲突的记录
        cursor.execute("""
            SELECT branch_id, publish_date, COUNT(*) as count
            FROM dashboard_publish_records 
            WHERE is_active = 1
            GROUP BY branch_id, publish_date
            HAVING COUNT(*) > 1
        """)
        conflicts = cursor.fetchall()
        
        if conflicts:
            print(f"发现 {len(conflicts)} 个冲突记录组:")
            for conflict in conflicts:
                print(f"  网点ID: {conflict[0]}, 发布日期: {conflict[1]}, 重复数量: {conflict[2]}")
            
            # 3. 修复冲突：保留最新的记录，将其他记录设为无效
            for branch_id, publish_date, count in conflicts:
                print(f"修复网点 {branch_id} 在 {publish_date} 的冲突记录...")
                
                # 获取该组中的所有记录，按创建时间排序
                cursor.execute("""
                    SELECT id, created_at 
                    FROM dashboard_publish_records 
                    WHERE branch_id = ? AND publish_date = ? AND is_active = 1
                    ORDER BY created_at DESC
                """, (branch_id, publish_date))
                
                records = cursor.fetchall()
                
                # 保留最新的记录，将其他记录设为无效
                if len(records) > 1:
                    latest_id = records[0][0]
                    old_ids = [record[0] for record in records[1:]]
                    
                    # 将旧记录设为无效
                    placeholders = ','.join(['?' for _ in old_ids])
                    cursor.execute(f"""
                        UPDATE dashboard_publish_records 
                        SET is_active = 0, updated_at = ?
                        WHERE id IN ({placeholders})
                    """, [datetime.utcnow().isoformat()] + old_ids)
                    
                    print(f"  保留记录ID: {latest_id}, 设为无效的记录ID: {old_ids}")
        else:
            print("未发现唯一约束冲突的记录")
        
        # 4. 提交更改
        conn.commit()
        print("修复完成！")
        
        # 5. 验证修复结果
        cursor.execute("""
            SELECT branch_id, publish_date, COUNT(*) as count
            FROM dashboard_publish_records 
            WHERE is_active = 1
            GROUP BY branch_id, publish_date
            HAVING COUNT(*) > 1
        """)
        remaining_conflicts = cursor.fetchall()
        
        if remaining_conflicts:
            print(f"警告：仍有 {len(remaining_conflicts)} 个冲突记录未修复")
            return False
        else:
            print("验证通过：所有冲突记录已修复")
            return True
            
    except Exception as e:
        print(f"迁移失败: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = run_migration()
    if success:
        print("✅ 迁移成功完成")
    else:
        print("❌ 迁移失败") 