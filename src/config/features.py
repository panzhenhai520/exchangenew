# 特性开关配置
# 用于控制新功能的逐步启用

class FeatureFlagsMeta(type):
    """元类，用于实现动态特性开关访问"""
    
    def __getattr__(cls, name):
        if name in cls._DEFAULT_FEATURES:
            return cls._get_feature_value(name)
        raise AttributeError(f"'{cls.__name__}' object has no attribute '{name}'")

class FeatureFlags(metaclass=FeatureFlagsMeta):
    """特性开关配置 - 支持动态配置"""
    
    # 默认配置（作为fallback）
    _DEFAULT_FEATURES = {
        'FEATURE_NEW_BUSINESS_TIME_RANGE': True,
        'FEATURE_NEW_PERIOD_BALANCE': True,
        'ENABLE_ENHANCED_BALANCE_CALCULATION': False,
        'ENABLE_COMPREHENSIVE_STATISTICS': False,
        'ENABLE_BALANCE_CONSISTENCY_CHECK': False,
        'ENABLE_EOD_DEBUG_LOGGING': True,
        'ENABLE_PERFORMANCE_MONITORING': False,
    }
    
    # 缓存配置（避免频繁数据库查询）
    _cache = {}
    _cache_timestamp = None
    _cache_duration = 300  # 5分钟缓存
    
    @classmethod
    def _get_from_database(cls, feature_name):
        """从数据库获取特性开关状态"""
        try:
            from services.db_service import DatabaseService
            from models.exchange_models import SystemConfig
            
            session = DatabaseService.get_session()
            try:
                config = session.query(SystemConfig).filter_by(
                    config_key=f'feature_flag_{feature_name}',
                    config_category='feature_flags'
                ).first()
                
                if config:
                    return config.config_value.lower() == 'true'
                return cls._DEFAULT_FEATURES.get(feature_name, False)
                
            finally:
                DatabaseService.close_session(session)
                
        except Exception as e:
            # 数据库异常时使用默认配置
            print(f"Warning: Failed to load feature flag {feature_name} from database: {e}")
            return cls._DEFAULT_FEATURES.get(feature_name, False)
    
    @classmethod
    def _update_cache(cls):
        """更新缓存"""
        import time
        current_time = time.time()
        
        if (cls._cache_timestamp is None or 
            current_time - cls._cache_timestamp > cls._cache_duration):
            
            cls._cache = {}
            for feature_name in cls._DEFAULT_FEATURES.keys():
                cls._cache[feature_name] = cls._get_from_database(feature_name)
            cls._cache_timestamp = current_time
    
    @classmethod
    def _get_feature_value(cls, feature_name):
        """获取特性开关值（带缓存）"""
        cls._update_cache()
        return cls._cache.get(feature_name, cls._DEFAULT_FEATURES.get(feature_name, False))
    
    @classmethod
    def is_enabled(cls, feature_name):
        """检查特性是否启用"""
        return cls._get_feature_value(feature_name)
    
    @classmethod
    def set_feature(cls, feature_name, enabled):
        """设置特性开关状态"""
        try:
            from services.db_service import DatabaseService
            from models.exchange_models import SystemConfig
            from datetime import datetime
            
            session = DatabaseService.get_session()
            try:
                config = session.query(SystemConfig).filter_by(
                    config_key=f'feature_flag_{feature_name}',
                    config_category='feature_flags'
                ).first()
                
                if config:
                    config.config_value = 'true' if enabled else 'false'
                    config.updated_at = datetime.now()
                else:
                    config = SystemConfig(
                        config_key=f'feature_flag_{feature_name}',
                        config_value='true' if enabled else 'false',
                        config_category='feature_flags',
                        description=f'Feature flag for {feature_name}',
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    session.add(config)
                
                session.commit()
                
                # 清除缓存
                cls._cache = {}
                cls._cache_timestamp = None
                
                return True
                
            except Exception as e:
                session.rollback()
                raise e
            finally:
                DatabaseService.close_session(session)
                
        except Exception as e:
            print(f"Error setting feature flag {feature_name}: {e}")
            return False
    
    @classmethod
    def get_all_features(cls):
        """获取所有特性的状态"""
        features = {}
        for feature_name in cls._DEFAULT_FEATURES.keys():
            features[feature_name] = cls._get_feature_value(feature_name)
        return features 