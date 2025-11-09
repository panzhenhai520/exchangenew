#!/usr/bin/env python3
"""
修复CurrencyBalance表balance字段精度问题
将Float类型改为Numeric(15,2)类型
"""

import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from services.db_service import DatabaseService
from sqlalchemy import text
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_balance_precision():
    """修复CurrencyBalance表balance字段精度问题"""
    session = DatabaseService.get_session()
    
    try:
        logger.info("开始修复CurrencyBalance表balance字段精度问题...")
        
        # 1. 备份现有数据
        logger.info("备份现有余额数据...")
        backup_query = text("""
            CREATE TABLE IF NOT EXISTS currency_balances_backup AS 
            SELECT * FROM currency_balances
        """)
        session.execute(backup_query)
        session.commit()
        logger.info("✅ 余额数据备份完成")
        
        # 2. 修改balance字段类型
        logger.info("修改balance字段类型从Float到Numeric(15,2)...")
        
        # 对于MySQL，需要重建表
        # 先删除已存在的新表（如果存在）
        drop_existing_table = text("DROP TABLE IF EXISTS currency_balances_new")
        session.execute(drop_existing_table)
        logger.info("✅ 清理已存在的新表")
        
        # 先创建新表结构
        create_new_table = text("""
            CREATE TABLE currency_balances_new (
                id INT PRIMARY KEY AUTO_INCREMENT,
                branch_id INT NOT NULL,
                currency_id INT NOT NULL,
                balance DECIMAL(15,2) DEFAULT 0.00,
                updated_at DATETIME,
                FOREIGN KEY (branch_id) REFERENCES branches (id),
                FOREIGN KEY (currency_id) REFERENCES currencies (id)
            )
        """)
        session.execute(create_new_table)
        logger.info("✅ 新表结构创建完成")
        
        # 复制数据到新表 - 修复MySQL语法
        copy_data = text("""
            INSERT INTO currency_balances_new (id, branch_id, currency_id, balance, updated_at)
            SELECT id, branch_id, currency_id, 
                   CASE 
                       WHEN balance IS NULL THEN 0.00
                       ELSE CAST(balance AS DECIMAL(15,2))
                   END as balance,
                   updated_at
            FROM currency_balances
        """)
        session.execute(copy_data)
        logger.info("✅ 数据复制完成")
        
        # 删除旧表
        drop_old_table = text("DROP TABLE currency_balances")
        session.execute(drop_old_table)
        logger.info("✅ 旧表删除完成")
        
        # 重命名新表
        rename_table = text("ALTER TABLE currency_balances_new RENAME TO currency_balances")
        session.execute(rename_table)
        logger.info("✅ 表重命名完成")
        
        # 3. 验证修复结果
        logger.info("验证修复结果...")
        verify_query = text("""
            SELECT COUNT(*) as total_records,
                   SUM(CASE WHEN balance IS NULL THEN 1 ELSE 0 END) as null_balances,
                   SUM(CASE WHEN balance = 0 THEN 1 ELSE 0 END) as zero_balances
            FROM currency_balances
        """)
        result = session.execute(verify_query).fetchone()
        
        logger.info(f"✅ 验证完成:")
        logger.info(f"  - 总记录数: {result[0]}")
        logger.info(f"  - NULL余额数: {result[1]}")
        logger.info(f"  - 零余额数: {result[2]}")
        
        # 4. 测试精度
        logger.info("测试精度处理...")
        test_precision = text("""
            INSERT INTO currency_balances (branch_id, currency_id, balance, updated_at)
            VALUES (1, 1, 0.4, NOW())
        """)
        session.execute(test_precision)
        
        # 查询测试数据
        test_query = text("""
            SELECT balance FROM currency_balances 
            WHERE branch_id = 1 AND currency_id = 1 
            ORDER BY id DESC LIMIT 1
        """)
        test_result = session.execute(test_query).fetchone()
        
        if test_result:
            logger.info(f"✅ 精度测试成功: 0.4 存储为 {test_result[0]}")
        else:
            logger.warning("⚠️ 精度测试失败")
        
        # 清理测试数据
        cleanup_test = text("""
            DELETE FROM currency_balances 
            WHERE branch_id = 1 AND currency_id = 1 AND balance = 0.4
        """)
        session.execute(cleanup_test)
        
        session.commit()
        logger.info("✅ CurrencyBalance表balance字段精度修复完成")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 修复失败: {str(e)}")
        session.rollback()
        return False
        
    finally:
        DatabaseService.close_session(session)

if __name__ == "__main__":
    success = fix_balance_precision()
    if success:
        print("✅ 余额精度修复成功")
    else:
        print("❌ 余额精度修复失败")
        sys.exit(1) 