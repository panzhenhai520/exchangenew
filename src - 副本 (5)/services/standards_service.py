"""
规范管理服务
处理兑换提醒信息维护、票据文件查看、余额报警设置等功能
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from services.db_service import DatabaseService
from models.exchange_models import (
    TransactionPurposeLimit, 
    BranchBalanceAlert, 
    Currency, 
    Branch,
    ExchangeTransaction,
    CurrencyTemplate
)

logger = logging.getLogger(__name__)

class StandardsService:
    """规范管理服务类"""
    
    @staticmethod
    def get_purpose_limits(branch_id: int) -> List[Dict[str, Any]]:
        """获取兑换提醒信息列表"""
        session = DatabaseService.get_session()
        try:
            # 连接Currency表获取完整的币种信息
            limits = session.query(TransactionPurposeLimit, Currency).join(
                Currency, TransactionPurposeLimit.currency_code == Currency.currency_code
            ).filter(
                TransactionPurposeLimit.branch_id == branch_id
            ).order_by(TransactionPurposeLimit.created_at.desc()).all()

            result = []
            for limit, currency in limits:
                limit_dict = limit.to_dict()
                limit_dict['currency_name'] = currency.currency_name
                result.append(limit_dict)

            return result
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def get_purpose_limits_by_currency(branch_id: int, currency_code: str) -> List[Dict[str, Any]]:
        """根据币种代码获取兑换提醒信息列表（用于兑换页面）"""
        session = DatabaseService.get_session()
        try:
            limits = session.query(TransactionPurposeLimit).filter(
                TransactionPurposeLimit.branch_id == branch_id,
                TransactionPurposeLimit.currency_code == currency_code,
                TransactionPurposeLimit.is_active == True
            ).order_by(TransactionPurposeLimit.purpose_name).all()

            result = []
            for limit in limits:
                result.append(limit.to_dict())

            return result
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def create_purpose_limit(branch_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建兑换提醒信息"""
        session = DatabaseService.get_session()
        try:
            # 检查是否已存在相同的用途和币种
            existing = session.query(TransactionPurposeLimit).filter(
                TransactionPurposeLimit.branch_id == branch_id,
                TransactionPurposeLimit.purpose_name == data['purpose_name'],
                TransactionPurposeLimit.currency_code == data['currency_code']
            ).first()
            
            if existing:
                raise ValueError(f"用途 '{data['purpose_name']}' 和币种 '{data['currency_code']}' 的限制已存在")
            
            limit = TransactionPurposeLimit(
                branch_id=branch_id,
                purpose_name=data['purpose_name'],
                currency_code=data['currency_code'],
                max_amount=data['max_amount'],
                display_message=data['display_message'],
                is_active=data.get('is_active', True)
            )
            
            session.add(limit)
            DatabaseService.commit_session(session)
            
            return limit.to_dict()
        except Exception as e:
            DatabaseService.rollback_session(session)
            raise e
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def update_purpose_limit(branch_id: int, limit_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新兑换提醒信息"""
        session = DatabaseService.get_session()
        try:
            limit = session.query(TransactionPurposeLimit).filter(
                TransactionPurposeLimit.id == limit_id,
                TransactionPurposeLimit.branch_id == branch_id
            ).first()
            
            if not limit:
                raise ValueError("未找到指定的限制规则")
            
            # 更新字段
            for key, value in data.items():
                if hasattr(limit, key) and key != 'id':
                    setattr(limit, key, value)
            
            limit.updated_at = datetime.utcnow()
            DatabaseService.commit_session(session)
            
            return limit.to_dict()
        except Exception as e:
            DatabaseService.rollback_session(session)
            raise e
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def delete_purpose_limit(branch_id: int, limit_id: int) -> bool:
        """删除兑换提醒信息"""
        session = DatabaseService.get_session()
        try:
            limit = session.query(TransactionPurposeLimit).filter(
                TransactionPurposeLimit.id == limit_id,
                TransactionPurposeLimit.branch_id == branch_id
            ).first()
            
            if not limit:
                raise ValueError("未找到指定的限制规则")
            
            session.delete(limit)
            DatabaseService.commit_session(session)
            
            return True
        except Exception as e:
            DatabaseService.rollback_session(session)
            raise e
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def get_balance_alerts(branch_id: int) -> List[Dict[str, Any]]:
        """获取余额报警设置列表"""
        session = DatabaseService.get_session()
        try:
            alerts = session.query(BranchBalanceAlert, Currency).join(
                Currency, BranchBalanceAlert.currency_id == Currency.id
            ).filter(
                BranchBalanceAlert.branch_id == branch_id
            ).all()
            
            result = []
            for alert, currency in alerts:
                alert_dict = alert.to_dict()
                alert_dict['currency_code'] = currency.currency_code
                alert_dict['currency_name'] = currency.currency_name
                result.append(alert_dict)
            
            return result
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def create_or_update_balance_alert(branch_id: int, currency_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建或更新余额报警设置"""
        session = DatabaseService.get_session()
        try:
            # 如果currency_id为null，说明币种未启用，需要先创建Currency记录
            if currency_id is None:
                currency_code = data.get('currency_code')
                if not currency_code:
                    raise ValueError("币种代码不能为空")
                
                # 查找币种模板
                template = session.query(CurrencyTemplate).filter(
                    CurrencyTemplate.currency_code == currency_code
                ).first()
                
                if not template:
                    raise ValueError(f"未找到币种模板: {currency_code}")
                
                # 创建Currency记录
                currency = Currency(
                    currency_code=template.currency_code,
                    currency_name=template.currency_name,
                    is_active=True
                )
                session.add(currency)
                session.flush()  # 获取新创建的ID
                currency_id = currency.id
            
            # 查找现有记录
            alert = session.query(BranchBalanceAlert).filter(
                BranchBalanceAlert.branch_id == branch_id,
                BranchBalanceAlert.currency_id == currency_id
            ).first()
            
            if alert:
                # 更新现有记录
                alert.min_threshold = data.get('min_threshold')
                alert.max_threshold = data.get('max_threshold')
                alert.is_active = data.get('is_active', True)
                alert.updated_at = datetime.utcnow()
            else:
                # 创建新记录
                alert = BranchBalanceAlert(
                    branch_id=branch_id,
                    currency_id=currency_id,
                    min_threshold=data.get('min_threshold'),
                    max_threshold=data.get('max_threshold'),
                    is_active=data.get('is_active', True)
                )
                session.add(alert)
            
            DatabaseService.commit_session(session)
            
            # 获取币种信息
            currency = session.query(Currency).filter(Currency.id == currency_id).first()
            result = alert.to_dict()
            if currency:
                result['currency_code'] = currency.currency_code
                result['currency_name'] = currency.currency_name
            
            return result
        except Exception as e:
            DatabaseService.rollback_session(session)
            raise e
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def delete_balance_alert(branch_id: int, alert_id: int) -> bool:
        """删除余额报警设置"""
        session = DatabaseService.get_session()
        try:
            alert = session.query(BranchBalanceAlert).filter(
                BranchBalanceAlert.id == alert_id,
                BranchBalanceAlert.branch_id == branch_id
            ).first()
            
            if not alert:
                raise ValueError("未找到指定的报警设置")
            
            session.delete(alert)
            DatabaseService.commit_session(session)
            
            return True
        except Exception as e:
            DatabaseService.rollback_session(session)
            raise e
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def get_available_currencies() -> List[Dict[str, Any]]:
        """获取可用的币种列表（包括未启用的币种）"""
        session = DatabaseService.get_session()
        try:
            # 获取所有币种模板
            templates = session.query(CurrencyTemplate).filter(
                CurrencyTemplate.is_active == True
            ).all()
            
            # 获取所有在交易记录中使用过的币种ID（基于交易记录判断）
            from models.exchange_models import ExchangeTransaction
            used_currency_ids = session.query(ExchangeTransaction.currency_id).distinct().all()
            used_currency_id_set = {row[0] for row in used_currency_ids}
            
            # 获取使用过的币种代码
            used_currencies = session.query(Currency.currency_code).filter(
                Currency.id.in_(used_currency_id_set)
            ).all()
            used_currency_codes = {row[0] for row in used_currencies}
            
            result = []
            for template in templates:
                # 检查是否在交易记录中使用过
                is_in_use = template.currency_code in used_currency_codes
                
                # 如果在交易记录中使用过，使用currencies表的ID
                currency_id = None
                if is_in_use:
                    currency = session.query(Currency).filter(
                        Currency.currency_code == template.currency_code
                    ).first()
                    if currency:
                        currency_id = currency.id
                
                result.append({
                    'id': currency_id,  # 未启用的币种ID为null
                    'currency_code': template.currency_code,
                    'currency_name': template.currency_name,
                    'is_in_use': is_in_use
                })
            
            return result
        finally:
            DatabaseService.close_session(session) 