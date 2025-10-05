#!/usr/bin/env python3
"""
分步创建表
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.db_service import DatabaseService
from sqlalchemy import text

def create_table_step_by_step():
    """分步创建表"""
    session = DatabaseService.get_session()
    try:
        # 1. 先检查表是否存在
        result = session.execute(text("SHOW TABLES LIKE 'denomination_publish_details'")).fetchall()
        if result:
            print("✅ 表 denomination_publish_details 已存在")
            return True
        
        # 2. 创建表（不包含外键约束）
        create_table_sql = """
        CREATE TABLE denomination_publish_details (
            id INT AUTO_INCREMENT PRIMARY KEY,
            publish_record_id INT NOT NULL,
            currency_id INT NOT NULL,
            denomination_id INT NOT NULL,
            denomination_value DECIMAL(15,2) NOT NULL,
            denomination_type VARCHAR(20) NOT NULL,
            buy_rate DECIMAL(10,4) NOT NULL,
            sell_rate DECIMAL(10,4) NOT NULL,
            sort_order INT DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_publish_record_id (publish_record_id),
            INDEX idx_currency_id (currency_id),
            INDEX idx_denomination_id (denomination_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        session.execute(text(create_table_sql))
        session.commit()
        print("✅ 表 denomination_publish_details 创建成功")
        
        # 3. 添加外键约束
        try:
            # 添加外键约束
            fk_sqls = [
                "ALTER TABLE denomination_publish_details ADD CONSTRAINT fk_denom_publish_record FOREIGN KEY (publish_record_id) REFERENCES rate_publish_records(id) ON DELETE CASCADE",
                "ALTER TABLE denomination_publish_details ADD CONSTRAINT fk_denom_currency FOREIGN KEY (currency_id) REFERENCES currencies(id) ON DELETE CASCADE",
                "ALTER TABLE denomination_publish_details ADD CONSTRAINT fk_denom_denomination FOREIGN KEY (denomination_id) REFERENCES currency_denominations(id) ON DELETE CASCADE"
            ]
            
            for fk_sql in fk_sqls:
                try:
                    session.execute(text(fk_sql))
                    session.commit()
                    print(f"✅ 外键约束添加成功")
                except Exception as e:
                    print(f"⚠️ 外键约束添加失败（可能已存在）: {str(e)}")
                    
        except Exception as e:
            print(f"⚠️ 外键约束添加失败: {str(e)}")
        
        # 4. 验证表结构
        result = session.execute(text("DESCRIBE denomination_publish_details")).fetchall()
        print("\n表结构:")
        for row in result:
            print(f"  {row[0]} {row[1]} {row[2]} {row[3]} {row[4]} {row[5]}")
        
        return True
        
    except Exception as e:
        session.rollback()
        print(f"❌ 创建表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        DatabaseService.close_session(session)

if __name__ == "__main__":
    create_table_step_by_step()