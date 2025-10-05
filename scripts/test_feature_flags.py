#!/usr/bin/env python3
"""
测试特性开关设置
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config.features import FeatureFlags

def test_feature_flags():
    """测试特性开关设置"""
    
    print("🔧 测试特性开关设置...")
    
    # 测试 FEATURE_NEW_PERIOD_BALANCE
    feature_value = FeatureFlags.FEATURE_NEW_PERIOD_BALANCE
    print(f"FEATURE_NEW_PERIOD_BALANCE: {feature_value}")
    
    if feature_value:
        print("✅ FEATURE_NEW_PERIOD_BALANCE 已正确设置为 True")
    else:
        print("❌ FEATURE_NEW_PERIOD_BALANCE 设置错误，应该是 True")
    
    # 测试其他特性开关
    print("\n📋 所有特性开关状态:")
    all_features = FeatureFlags.get_all_features()
    for feature_name, enabled in all_features.items():
        status = "✅ 启用" if enabled else "❌ 禁用"
        print(f"  {feature_name}: {status}")
    
    print("\n✨ 测试完成！")

if __name__ == '__main__':
    test_feature_flags() 