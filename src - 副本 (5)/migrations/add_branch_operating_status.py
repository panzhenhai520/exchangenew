#!/usr/bin/env python3
"""
数据库迁移脚本 - 添加网点营业状态控制表
创建时间: 2024-12-28
用途: 控制期初设置和营业数据管理
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from services.db_service import DatabaseService
from models.exchange_models import Base, BranchOperatingStatus
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_branch_operating_status_table():
    """创建网点营业状态表"""
    try:
        # 获取数据库连接
        session = DatabaseService.get_session()
        engine = session.get_bind()
        
        logger.info("开始创建网点营业状态表...")
        
        # 检查表是否已存在
        result = engine.execute(text("""
            SELECT COUNT(*) as count 
            FROM sqlite_master 
            WHERE type='table' AND name='branch_operating_status'
        """)).fetchone()
        
        if result.count > 0:
            logger.info("表 branch_operating_status 已存在，跳过创建")
            return True
        
        # 创建表
        BranchOperatingStatus.__table__.create(engine)
        logger.info("成功创建表 branch_operating_status")
        
        # 为现有网点添加默认状态记录
        from models.exchange_models import Branch
        branches = session.query(Branch).all()
        
        for branch in branches:
            # 检查是否已有状态记录
            existing_status = session.query(BranchOperatingStatus).filter_by(
                branch_id=branch.id
            ).first()
            
            if not existing_status:
                # 检查该网点是否已有初始余额设置
                from models.exchange_models import ExchangeTransaction
                has_initial_balance = session.query(ExchangeTransaction).filter_by(
                    branch_id=branch.id,
                    type='initial_balance'
                ).first()
                
                # 创建状态记录
                status = BranchOperatingStatus(
                    branch_id=branch.id,
                    is_initial_setup_completed=bool(has_initial_balance),
                    initial_setup_date=has_initial_balance.created_at if has_initial_balance else None,
                    initial_setup_by=has_initial_balance.operator_id if has_initial_balance else None,
                    operating_start_date=has_initial_balance.transaction_date if has_initial_balance else None
                )
                session.add(status)
                
                logger.info(f"为网点 {branch.branch_name} (ID: {branch.id}) 创建营业状态记录")
        
        session.commit()
        logger.info("成功初始化所有网点的营业状态")
        return True
        
    except Exception as e:
        logger.error(f"创建网点营业状态表失败: {str(e)}")
        session.rollback()
        return False
    finally:
        DatabaseService.close_session(session)

def rollback_branch_operating_status_table():
    """回滚：删除网点营业状态表"""
    try:
        session = DatabaseService.get_session()
        engine = session.get_bind()
        
        logger.info("开始删除网点营业状态表...")
        
        # 删除表
        engine.execute(text("DROP TABLE IF EXISTS branch_operating_status"))
        logger.info("成功删除表 branch_operating_status")
        return True
        
    except Exception as e:
        logger.error(f"删除网点营业状态表失败: {str(e)}")
        return False
    finally:
        DatabaseService.close_session(session)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='网点营业状态表迁移脚本')
    parser.add_argument('--rollback', action='store_true', help='回滚迁移')
    args = parser.parse_args()
    
    if args.rollback:
        success = rollback_branch_operating_status_table()
        action = "回滚"
    else:
        success = create_branch_operating_status_table()
        action = "执行"
    
    if success:
        logger.info(f"迁移{action}成功")
        sys.exit(0)
    else:
        logger.error(f"迁移{action}失败")
        sys.exit(1)

if __name__ == "__main__":
    main() 