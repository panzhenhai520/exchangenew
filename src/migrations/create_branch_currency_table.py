#!/usr/bin/env python3
"""
创建网点币种关联表的迁移脚本
用于管理网点级别的币种启用/禁用状态
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from sqlalchemy import create_engine, text
from models.exchange_models import Base, BranchCurrency
from services.db_service import create_db_engine

def create_branch_currency_table():
    """创建网点币种关联表"""
    try:
        # 获取数据库连接
        engine = create_db_engine()
        
        # 创建表
        Base.metadata.create_all(engine, tables=[BranchCurrency.__table__])
        
        print("✅ 成功创建 branch_currencies 表")
        
        # 初始化现有币种的网点关联
        with engine.begin() as conn:
            # 获取所有网点和币种
            result = conn.execute(text("""
                SELECT b.id as branch_id, c.id as currency_id
                FROM branches b
                CROSS JOIN currencies c
                WHERE c.id != b.base_currency_id
            """))
            
            # 为每个网点-币种组合创建启用记录
            for row in result:
                conn.execute(text("""
                    INSERT INTO branch_currencies (branch_id, currency_id, is_enabled, created_at, updated_at)
                    VALUES (:branch_id, :currency_id, :is_enabled, :created_at, :updated_at)
                    ON DUPLICATE KEY UPDATE updated_at = :updated_at
                """), {
                    'branch_id': row.branch_id,
                    'currency_id': row.currency_id,
                    'is_enabled': True,
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                })
            
            print("✅ 成功初始化现有币种的网点关联记录")
            
    except Exception as e:
        print(f"❌ 创建网点币种关联表失败: {str(e)}")
        raise

if __name__ == "__main__":
    print("开始创建网点币种关联表...")
    create_branch_currency_table()
    print("✅ 迁移完成！") 