#!/usr/bin/env python3
"""
数据库迁移脚本：创建SystemConfig表
用于存储系统配置，包括特性开关
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from services.db_service import DatabaseService, engine
from models.exchange_models import SystemConfig, Base
from datetime import datetime
import sqlite3

def create_system_config_table():
    """创建SystemConfig表"""
    try:
        # 创建表（如果不存在）
        Base.metadata.create_all(engine, tables=[SystemConfig.__table__])
        
        print("✅ SystemConfig表创建成功")
        return True
        
    except Exception as e:
        print(f"❌ 创建SystemConfig表失败: {e}")
        return False

def initialize_feature_flags():
    """初始化默认特性开关设置"""
    try:
        from sqlalchemy.orm import sessionmaker
        
        # 直接创建会话，避免使用DatabaseService可能的Flask依赖
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # 默认特性开关配置
        default_features = [
            {
                'config_key': 'feature_flag_FEATURE_NEW_BUSINESS_TIME_RANGE',
                'config_value': 'true',
                'config_category': 'feature_flags',
                'description': '启用新业务时间范围计算'
            },
            {
                'config_key': 'feature_flag_FEATURE_NEW_PERIOD_BALANCE',
                'config_value': 'true',
                'config_category': 'feature_flags',
                'description': '启用新期初余额获取方式'
            },
            {
                'config_key': 'feature_flag_ENABLE_ENHANCED_BALANCE_CALCULATION',
                'config_value': 'false',
                'config_category': 'feature_flags',
                'description': '启用增强余额计算'
            },
            {
                'config_key': 'feature_flag_ENABLE_COMPREHENSIVE_STATISTICS',
                'config_value': 'false',
                'config_category': 'feature_flags',
                'description': '启用完整统计报表'
            },
            {
                'config_key': 'feature_flag_ENABLE_BALANCE_CONSISTENCY_CHECK',
                'config_value': 'false',
                'config_category': 'feature_flags',
                'description': '启用余额一致性检查'
            },
            {
                'config_key': 'feature_flag_ENABLE_EOD_DEBUG_LOGGING',
                'config_value': 'true',
                'config_category': 'feature_flags',
                'description': '启用日结调试日志'
            },
            {
                'config_key': 'feature_flag_ENABLE_PERFORMANCE_MONITORING',
                'config_value': 'false',
                'config_category': 'feature_flags',
                'description': '启用性能监控'
            }
        ]
        
        # 检查并插入特性开关配置
        for feature in default_features:
            existing_config = session.query(SystemConfig).filter_by(
                config_key=feature['config_key'],
                config_category=feature['config_category']
            ).first()
            
            if not existing_config:
                config = SystemConfig(
                    config_key=feature['config_key'],
                    config_value=feature['config_value'],
                    config_category=feature['config_category'],
                    description=feature['description'],
                    is_active=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                session.add(config)
                print(f"✅ 添加特性开关: {feature['config_key']}")
            else:
                print(f"ℹ️  特性开关已存在: {feature['config_key']}")
        
        session.commit()
        print("✅ 特性开关初始化完成")
        
    except Exception as e:
        print(f"❌ 初始化特性开关失败: {e}")
        if 'session' in locals():
            session.rollback()
        raise
        
    finally:
        if 'session' in locals():
            session.close()

def check_table_exists():
    """检查SystemConfig表是否存在"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='system_configs'
            """)).fetchone()
            return result is not None
    except Exception as e:
        print(f"❌ 检查表存在性失败: {e}")
        return False

def main():
    """主函数"""
    print("🔧 开始SystemConfig表迁移...")
    
    # 初始化数据库服务
    DatabaseService.init_db()
    
    try:
        # 检查表是否已存在
        if check_table_exists():
            print("ℹ️  SystemConfig表已存在，跳过创建")
        else:
            # 创建表
            if not create_system_config_table():
                print("❌ 数据库迁移失败")
                return False
        
        # 初始化特性开关
        initialize_feature_flags()
        
        print("✅ SystemConfig表迁移完成")
        return True
        
    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 