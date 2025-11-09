#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易报警事件服务
提供交易报警事件的创建、查询、管理功能
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from models.exchange_models import TransactionAlert, Branch, Currency, Operator
from services.db_service import DatabaseService

logger = logging.getLogger(__name__)

class TransactionAlertService:
    """交易报警事件服务"""
    
    @staticmethod
    def create_alert(branch_id: int, currency_id: int, operator_id: int, 
                    alert_type: str, alert_level: str, current_balance: Decimal,
                    transaction_amount: Decimal, transaction_type: str, 
                    after_balance: Decimal, message: str, threshold_value: Optional[Decimal] = None) -> Dict[str, Any]:
        """
        创建交易报警事件
        
        Args:
            branch_id: 网点ID
            currency_id: 币种ID
            operator_id: 操作员ID
            alert_type: 报警类型 (threshold_min, threshold_max, insufficient_balance)
            alert_level: 报警级别 (warning, critical)
            current_balance: 当前余额
            transaction_amount: 交易金额
            transaction_type: 交易类型 (buy, sell)
            after_balance: 交易后余额
            message: 报警消息
            threshold_value: 阈值（可选）
            
        Returns:
            创建结果
        """
        try:
            db_service = DatabaseService()
            session = db_service.get_session()
            
            try:
                # 创建报警记录
                alert = TransactionAlert(
                    branch_id=branch_id,
                    currency_id=currency_id,
                    operator_id=operator_id,
                    alert_type=alert_type,
                    alert_level=alert_level,
                    current_balance=current_balance,
                    threshold_value=threshold_value,
                    transaction_amount=transaction_amount,
                    transaction_type=transaction_type,
                    after_balance=after_balance,
                    message=message,
                    created_at=datetime.utcnow()
                )
                
                session.add(alert)
                session.commit()
                
                logger.info(f"创建交易报警事件成功: {alert.id}")
                
                return {
                    'success': True,
                    'alert_id': alert.id,
                    'message': '交易报警事件创建成功'
                }
                
            except Exception as e:
                session.rollback()
                raise e
                
        except Exception as e:
            logger.error(f"创建交易报警事件失败: {e}")
            return {
                'success': False,
                'message': f'创建交易报警事件失败: {str(e)}'
            }
        finally:
            session.close()
    
    @staticmethod
    def get_alerts_by_branch(branch_id: int, limit: int = 50, resolved: Optional[bool] = None) -> Dict[str, Any]:
        """
        获取网点的报警事件列表
        
        Args:
            branch_id: 网点ID
            limit: 限制数量
            resolved: 是否已解决 (None表示全部)
        
        Returns:
            报警事件列表
        """
        try:
            db_service = DatabaseService()
            session = db_service.get_session()
            
            try:
                query = session.query(TransactionAlert).filter(
                    TransactionAlert.branch_id == branch_id
                )
                
                if resolved is not None:
                    query = query.filter(TransactionAlert.is_resolved == resolved)
                
                alerts = query.order_by(desc(TransactionAlert.created_at)).limit(limit).all()
                
                # 获取相关信息
                alert_list = []
                for alert in alerts:
                    alert_dict = alert.to_dict()
                    
                    # 获取币种信息
                    currency = session.query(Currency).filter_by(id=alert.currency_id).first()
                    if currency:
                        alert_dict['currency_code'] = currency.currency_code
                        alert_dict['currency_name'] = currency.currency_name
                    
                    # 获取操作员信息
                    operator = session.query(Operator).filter_by(id=alert.operator_id).first()
                    if operator:
                        alert_dict['operator_name'] = operator.name
                    
                    # 获取解决人信息
                    if alert.resolved_by:
                        resolver = session.query(Operator).filter_by(id=alert.resolved_by).first()
                        if resolver:
                            alert_dict['resolver_name'] = resolver.name
                    
                    alert_list.append(alert_dict)
                
                return {
                    'success': True,
                    'alerts': alert_list,
                    'total': len(alert_list)
                }
                
            except Exception as e:
                raise e
                
        except Exception as e:
            logger.error(f"获取报警事件列表失败: {e}")
            return {
                'success': False,
                'message': f'获取报警事件列表失败: {str(e)}',
                'alerts': []
            }
        finally:
            session.close()
    
    @staticmethod
    def get_alerts_by_operator(operator_id: int, limit: int = 50) -> Dict[str, Any]:
        """
        获取操作员相关的报警事件
        
        Args:
            operator_id: 操作员ID
            limit: 限制数量
        
        Returns:
            报警事件列表
        """
        try:
            db_service = DatabaseService()
            session = db_service.get_session()
            
            try:
                alerts = session.query(TransactionAlert).filter(
                    TransactionAlert.operator_id == operator_id
                ).order_by(desc(TransactionAlert.created_at)).limit(limit).all()
                
                alert_list = []
                for alert in alerts:
                    alert_dict = alert.to_dict()
                    
                    # 获取币种信息
                    currency = session.query(Currency).filter_by(id=alert.currency_id).first()
                    if currency:
                        alert_dict['currency_code'] = currency.currency_code
                        alert_dict['currency_name'] = currency.currency_name
                    
                    alert_list.append(alert_dict)
                
                return {
                    'success': True,
                    'alerts': alert_list,
                    'total': len(alert_list)
                }
                
            except Exception as e:
                raise e
                
        except Exception as e:
            logger.error(f"获取操作员报警事件失败: {e}")
            return {
                'success': False,
                'message': f'获取操作员报警事件失败: {str(e)}',
                'alerts': []
            }
        finally:
            session.close()
    
    @staticmethod
    def resolve_alert(alert_id: int, resolver_id: int) -> Dict[str, Any]:
        """
        解决报警事件
        
        Args:
            alert_id: 报警事件ID
            resolver_id: 解决人ID
        
        Returns:
            解决结果
        """
        try:
            db_service = DatabaseService()
            session = db_service.get_session()
            
            try:
                alert = session.query(TransactionAlert).filter_by(id=alert_id).first()
                if not alert:
                    return {
                        'success': False,
                        'message': '报警事件不存在'
                    }
                
                if alert.is_resolved:
                    return {
                        'success': False,
                        'message': '报警事件已经解决'
                    }
                
                alert.is_resolved = True
                alert.resolved_at = datetime.utcnow()
                alert.resolved_by = resolver_id
                
                session.commit()
                
                logger.info(f"解决报警事件成功: {alert_id}")
                
                return {
                    'success': True,
                    'message': '报警事件解决成功'
                }
                
            except Exception as e:
                session.rollback()
                raise e
                
        except Exception as e:
            logger.error(f"解决报警事件失败: {e}")
            return {
                'success': False,
                'message': f'解决报警事件失败: {str(e)}'
            }
        finally:
            session.close()
    
    @staticmethod
    def get_alert_statistics(branch_id: int, days: int = 7) -> Dict[str, Any]:
        """
        获取报警事件统计信息
        
        Args:
            branch_id: 网点ID
            days: 统计天数
        
        Returns:
            统计信息
        """
        try:
            db_service = DatabaseService()
            session = db_service.get_session()
            
            try:
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=days)
                
                # 总报警数
                total_alerts = session.query(TransactionAlert).filter(
                    and_(
                        TransactionAlert.branch_id == branch_id,
                        TransactionAlert.created_at >= start_date
                    )
                ).count()
                
                # 未解决报警数
                unresolved_alerts = session.query(TransactionAlert).filter(
                    and_(
                        TransactionAlert.branch_id == branch_id,
                        TransactionAlert.created_at >= start_date,
                        TransactionAlert.is_resolved == False
                    )
                ).count()
                
                # 最近5条未解决报警
                recent_alerts = session.query(TransactionAlert).filter(
                    and_(
                        TransactionAlert.branch_id == branch_id,
                        TransactionAlert.is_resolved == False
                    )
                ).order_by(desc(TransactionAlert.created_at)).limit(5).all()
                
                recent_alert_list = []
                for alert in recent_alerts:
                    alert_dict = alert.to_dict()
                    # 获取币种信息
                    currency = session.query(Currency).filter_by(id=alert.currency_id).first()
                    if currency:
                        alert_dict['currency_code'] = currency.currency_code
                        alert_dict['currency_name'] = currency.currency_name
                    recent_alert_list.append(alert_dict)
                
                return {
                    'success': True,
                    'statistics': {
                        'total_alerts': total_alerts,
                        'unresolved_alerts': unresolved_alerts,
                        'recent_alerts': recent_alert_list,
                        'days': days
                    }
                }
                
            except Exception as e:
                raise e
                
        except Exception as e:
            logger.error(f"获取报警统计失败: {e}")
            return {
                'success': False,
                'message': f'获取报警统计失败: {str(e)}',
                'statistics': {}
            }
        finally:
            session.close() 