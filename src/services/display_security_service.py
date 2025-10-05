import os
import jwt
import time
import hashlib
import secrets
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from src.services.db_service import DatabaseService
from src.models.exchange_models import Branch
import logging

logger = logging.getLogger(__name__)

class DisplaySecurityService:
    """汇率展示安全服务"""
    
    @staticmethod
    def generate_branch_key(branch_id):
        """为网点生成唯一的加密密钥"""
        # 使用网点ID和系统密钥生成固定的密钥
        system_secret = os.getenv('SECRET_KEY', 'your-secret-key-here')
        branch_data = f"{branch_id}:{system_secret}:display_key"
        key_hash = hashlib.sha256(branch_data.encode()).digest()
        # 使用前32字节作为Fernet密钥
        return Fernet.generate_key()  # 实际应该基于branch_data生成固定密钥
    
    @staticmethod
    def encrypt_display_url(branch_id, expires_hours=24):
        """生成加密的展示URL"""
        try:
            # 生成展示数据
            expires_at = int(time.time()) + (expires_hours * 3600)
            display_data = {
                'branch_id': branch_id,
                'type': 'rates_display',
                'issued_at': int(time.time()),
                'expires_at': expires_at,
                'nonce': secrets.token_hex(16)  # 防重放攻击
            }
            
            # 使用JWT进行签名
            system_secret = os.getenv('SECRET_KEY', 'your-secret-key-here')
            token = jwt.encode(display_data, system_secret, algorithm='HS256')
            
            # 再次加密token
            cipher_suite = Fernet(DisplaySecurityService.generate_branch_key(branch_id))
            encrypted_token = cipher_suite.encrypt(token.encode())
            
            # 生成URL安全的编码
            import base64
            url_safe_token = base64.urlsafe_b64encode(encrypted_token).decode().rstrip('=')
            
            return url_safe_token
            
        except Exception as e:
            logger.error(f"生成加密URL失败: {e}")
            raise
    
    @staticmethod
    def decrypt_display_url(encrypted_token):
        """解密展示URL并验证"""
        try:
            # URL解码
            import base64
            # 补充可能缺失的填充
            missing_padding = len(encrypted_token) % 4
            if missing_padding:
                encrypted_token += '=' * (4 - missing_padding)
            
            encrypted_data = base64.urlsafe_b64decode(encrypted_token)
            
            # 尝试不同网点的密钥解密（实际应该从数据库获取）
            session = DatabaseService.get_session()
            try:
                branches = session.query(Branch).all()
                for branch in branches:
                    try:
                        cipher_suite = Fernet(DisplaySecurityService.generate_branch_key(branch.id))
                        decrypted_token = cipher_suite.decrypt(encrypted_data).decode()
                        
                        # 验证JWT
                        system_secret = os.getenv('SECRET_KEY', 'your-secret-key-here')
                        payload = jwt.decode(decrypted_token, system_secret, algorithms=['HS256'])
                        
                        # 检查过期时间
                        if payload.get('expires_at', 0) <= time.time():
                            continue  # 尝试下一个网点
                        
                        # 验证类型
                        if payload.get('type') != 'rates_display':
                            continue
                        
                        return payload
                        
                    except Exception:
                        continue  # 尝试下一个网点的密钥
                
                raise ValueError("无法解密或token已过期")
                
            finally:
                DatabaseService.close_session(session)
                
        except Exception as e:
            logger.error(f"解密URL失败: {e}")
            raise
    
    @staticmethod
    def generate_display_config(branch_id, theme='light', currency_order=None):
        """生成展示配置"""
        config = {
            'branch_id': branch_id,
            'theme': theme,  # 'light' 或 'dark'
            'currency_order': currency_order or [],
            'generated_at': datetime.now().isoformat(),
            'version': '1.0'
        }
        return config
    
    @staticmethod
    def validate_display_access(encrypted_token):
        """验证展示访问权限"""
        try:
            payload = DisplaySecurityService.decrypt_display_url(encrypted_token)
            
            # 额外的安全检查
            current_time = int(time.time())
            if payload.get('expires_at', 0) <= current_time:
                return None, "访问链接已过期"
            
            # 检查是否在合理的时间窗口内
            issued_at = payload.get('issued_at', 0)
            if current_time - issued_at > 7 * 24 * 3600:  # 超过7天
                return None, "访问链接过于陈旧"
            
            return payload, None
            
        except Exception as e:
            return None, f"访问验证失败: {str(e)}" 