#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
面值系统数据库迁移脚本
添加面值相关的表结构
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from services.db_service import DatabaseService
from services.db_service import get_db_url

def create_denomination_tables():
    """创建面值相关表"""
    
    # 创建币种面值表
    create_currency_denominations = """
    CREATE TABLE IF NOT EXISTS currency_denominations (
        id INT AUTO_INCREMENT PRIMARY KEY,
        currency_id INT NOT NULL,
        denomination_value DECIMAL(15,2) NOT NULL,
        denomination_type VARCHAR(20) NOT NULL CHECK (denomination_type IN ('bill', 'coin')),
        is_active BOOLEAN DEFAULT TRUE,
        sort_order INT DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (currency_id) REFERENCES currencies(id),
        UNIQUE KEY unique_currency_denomination (currency_id, denomination_value, denomination_type)
    );
    """
    
    # 创建面值汇率表
    create_denomination_rates = """
    CREATE TABLE IF NOT EXISTS denomination_rates (
        id INT AUTO_INCREMENT PRIMARY KEY,
        branch_id INT NOT NULL,
        currency_id INT NOT NULL,
        denomination_id INT NOT NULL,
        rate_date DATE NOT NULL,
        buy_rate DECIMAL(10,4) NOT NULL,
        sell_rate DECIMAL(10,4) NOT NULL,
        created_by INT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        sort_order INT DEFAULT 0,
        FOREIGN KEY (branch_id) REFERENCES branches(id),
        FOREIGN KEY (currency_id) REFERENCES currencies(id),
        FOREIGN KEY (denomination_id) REFERENCES currency_denominations(id),
        FOREIGN KEY (created_by) REFERENCES operators(id),
        UNIQUE KEY unique_denomination_rate (branch_id, currency_id, denomination_id, rate_date)
    );
    """
    
    # 创建交易面值详情表
    create_transaction_denominations = """
    CREATE TABLE IF NOT EXISTS transaction_denominations (
        id INT AUTO_INCREMENT PRIMARY KEY,
        transaction_id INT NOT NULL,
        denomination_id INT NOT NULL,
        quantity INT NOT NULL,
        total_amount DECIMAL(15,2) NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (transaction_id) REFERENCES exchange_transactions(id),
        FOREIGN KEY (denomination_id) REFERENCES currency_denominations(id)
    );
    """
    
    # 创建索引
    create_indexes = [
        "CREATE INDEX idx_currency_denominations_currency_id ON currency_denominations(currency_id);",
        "CREATE INDEX idx_currency_denominations_type ON currency_denominations(denomination_type);",
        "CREATE INDEX idx_currency_denominations_active ON currency_denominations(is_active);",
        "CREATE INDEX idx_denomination_rates_branch_date ON denomination_rates(branch_id, rate_date);",
        "CREATE INDEX idx_denomination_rates_currency ON denomination_rates(currency_id);",
        "CREATE INDEX idx_denomination_rates_denomination ON denomination_rates(denomination_id);",
        "CREATE INDEX idx_transaction_denominations_transaction ON transaction_denominations(transaction_id);",
        "CREATE INDEX idx_transaction_denominations_denomination ON transaction_denominations(denomination_id);"
    ]
    
    try:
        # 创建数据库连接
        database_url = get_db_url()
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # 开始事务
            trans = conn.begin()
            
            try:
                # 创建表
                print("创建币种面值表...")
                conn.execute(text(create_currency_denominations))
                
                print("创建面值汇率表...")
                conn.execute(text(create_denomination_rates))
                
                print("创建交易面值详情表...")
                conn.execute(text(create_transaction_denominations))
                
                # 创建索引
                print("创建索引...")
                for index_sql in create_indexes:
                    conn.execute(text(index_sql))
                
                # 提交事务
                trans.commit()
                print("✅ 面值系统表创建成功！")
                
            except Exception as e:
                # 回滚事务
                trans.rollback()
                print(f"❌ 创建表失败: {str(e)}")
                raise
                
    except Exception as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        raise

def populate_default_denominations():
    """为现有币种添加默认面值"""
    
    # 常见币种的默认面值
    default_denominations = {
        'USD': [
            (1, 'bill'), (5, 'bill'), (10, 'bill'), (20, 'bill'), (50, 'bill'), (100, 'bill'),
            (0.01, 'coin'), (0.05, 'coin'), (0.10, 'coin'), (0.25, 'coin'), (0.50, 'coin'), (1, 'coin')
        ],
        'EUR': [
            (5, 'bill'), (10, 'bill'), (20, 'bill'), (50, 'bill'), (100, 'bill'), (200, 'bill'), (500, 'bill'),
            (0.01, 'coin'), (0.02, 'coin'), (0.05, 'coin'), (0.10, 'coin'), (0.20, 'coin'), (0.50, 'coin'), (1, 'coin'), (2, 'coin')
        ],
        'GBP': [
            (5, 'bill'), (10, 'bill'), (20, 'bill'), (50, 'bill'),
            (0.01, 'coin'), (0.02, 'coin'), (0.05, 'coin'), (0.10, 'coin'), (0.20, 'coin'), (0.50, 'coin'), (1, 'coin'), (2, 'coin')
        ],
        'JPY': [
            (1000, 'bill'), (2000, 'bill'), (5000, 'bill'), (10000, 'bill'),
            (1, 'coin'), (5, 'coin'), (10, 'coin'), (50, 'coin'), (100, 'coin'), (500, 'coin')
        ],
        'CNY': [
            (1, 'bill'), (5, 'bill'), (10, 'bill'), (20, 'bill'), (50, 'bill'), (100, 'bill'),
            (0.01, 'coin'), (0.02, 'coin'), (0.05, 'coin'), (0.1, 'coin'), (0.2, 'coin'), (0.5, 'coin'), (1, 'coin')
        ],
        'HKD': [
            (10, 'bill'), (20, 'bill'), (50, 'bill'), (100, 'bill'), (500, 'bill'), (1000, 'bill'),
            (0.10, 'coin'), (0.20, 'coin'), (0.50, 'coin'), (1, 'coin'), (2, 'coin'), (5, 'coin'), (10, 'coin')
        ]
    }
    
    try:
        database_url = get_db_url()
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            trans = conn.begin()
            
            try:
                # 获取所有币种（排除本币）
                result = conn.execute(text("""
                    SELECT c.id, c.currency_code 
                    FROM currencies c 
                    LEFT JOIN branches b ON c.id = b.base_currency_id 
                    WHERE b.base_currency_id IS NULL
                """))
                currencies = {row[1]: row[0] for row in result}
                
                print(f"找到 {len(currencies)} 个币种")
                
                # 为每个币种添加默认面值
                for currency_code, currency_id in currencies.items():
                    if currency_code in default_denominations:
                        denominations = default_denominations[currency_code]
                        print(f"为 {currency_code} 添加 {len(denominations)} 个面值...")
                        
                        for i, (value, type_) in enumerate(denominations):
                            # 检查面值是否已存在
                            check_result = conn.execute(text("""
                                SELECT COUNT(*) FROM currency_denominations 
                                WHERE currency_id = :currency_id 
                                AND denomination_value = :value 
                                AND denomination_type = :type
                            """), {
                                'currency_id': currency_id,
                                'value': value,
                                'type': type_
                            })
                            
                            if check_result.scalar() == 0:
                                conn.execute(text("""
                                    INSERT INTO currency_denominations 
                                    (currency_id, denomination_value, denomination_type, sort_order, is_active)
                                    VALUES (:currency_id, :value, :type, :sort_order, 1)
                                """), {
                                    'currency_id': currency_id,
                                    'value': value,
                                    'type': type_,
                                    'sort_order': i
                                })
                
                trans.commit()
                print("✅ 默认面值添加成功！")
                
            except Exception as e:
                trans.rollback()
                print(f"❌ 添加默认面值失败: {str(e)}")
                raise
                
    except Exception as e:
        print(f"❌ 添加默认面值失败: {str(e)}")
        raise

def main():
    """主函数"""
    print("🚀 开始创建面值系统表...")
    
    try:
        # 创建表
        create_denomination_tables()
        
        # 添加默认面值
        print("\n📝 添加默认面值...")
        populate_default_denominations()
        
        print("\n✅ 面值系统初始化完成！")
        print("\n📋 已创建的表:")
        print("  - currency_denominations (币种面值表)")
        print("  - denomination_rates (面值汇率表)")
        print("  - transaction_denominations (交易面值详情表)")
        
    except Exception as e:
        print(f"\n❌ 初始化失败: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()