#!/usr/bin/env python3
"""
直接使用SQL创建表
"""

import pymysql
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def create_table():
    """直接创建表"""
    try:
        # 数据库连接参数
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'exchange'),
            'charset': 'utf8mb4'
        }
        
        # 连接数据库
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor()
        
        # 检查表是否存在
        cursor.execute("SHOW TABLES LIKE 'denomination_publish_details'")
        result = cursor.fetchall()
        
        if result:
            print("✅ 表 denomination_publish_details 已存在")
            return True
        
        # 创建表
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
            FOREIGN KEY (publish_record_id) REFERENCES rate_publish_records(id) ON DELETE CASCADE,
            FOREIGN KEY (currency_id) REFERENCES currencies(id) ON DELETE CASCADE,
            FOREIGN KEY (denomination_id) REFERENCES currency_denominations(id) ON DELETE CASCADE,
            INDEX idx_publish_record_id (publish_record_id),
            INDEX idx_currency_id (currency_id),
            INDEX idx_denomination_id (denomination_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        cursor.execute(create_table_sql)
        connection.commit()
        print("✅ 表 denomination_publish_details 创建成功")
        
        # 验证表结构
        cursor.execute("DESCRIBE denomination_publish_details")
        columns = cursor.fetchall()
        print("\n表结构:")
        for column in columns:
            print(f"  {column[0]} {column[1]} {column[2]} {column[3]} {column[4]} {column[5]}")
        
        return True
        
    except Exception as e:
        print(f"❌ 创建表失败: {str(e)}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    print("开始创建 denomination_publish_details 表...")
    create_table()