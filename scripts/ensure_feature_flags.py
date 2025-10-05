#!/usr/bin/env python3
"""
确保特性开关在数据库中的正确设置
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from services.db_service import DatabaseService
from models.exchange_models import SystemConfig
from datetime import datetime

def ensure_feature_flags():
    """确保特性开关在数据库中的正确设置"""
    
    # 需要确保为True的特性开关
    required_true_features = [
        'FEATURE_NEW_PERIOD_BALANCE'
    ]
    
    session = DatabaseService.get_session()
    try:
        for feature_name in required_true_features:
            config_key = f'feature_flag_{feature_name}'
            
            # 查找现有配置
            config = session.query(SystemConfig).filter_by(
                config_key=config_key,
                config_category='feature_flags'
            ).first()
            
            if config:
                # 如果配置存在但值不是True，则更新
                if config.config_value.lower() != 'true':
                    config.config_value = 'true'
                    config.updated_at = datetime.now()
                    print(f"✅ 更新特性开关 {feature_name} 为 True")
                else:
                    print(f"✅ 特性开关 {feature_name} 已经是 True")
            else:
                # 如果配置不存在，则创建
                config = SystemConfig(
                    config_key=config_key,
                    config_value='true',
                    config_category='feature_flags',
                    description=f'Feature flag for {feature_name}',
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                session.add(config)
                print(f"✅ 创建特性开关 {feature_name} 并设置为 True")
        
        session.commit()
        print("🎉 所有特性开关设置完成！")
        
    except Exception as e:
        session.rollback()
        print(f"❌ 设置特性开关失败: {e}")
        raise
    finally:
        DatabaseService.close_session(session)

if __name__ == '__main__':
    print("🔧 开始设置特性开关...")
    ensure_feature_flags()
    print("✨ 特性开关设置完成！") 