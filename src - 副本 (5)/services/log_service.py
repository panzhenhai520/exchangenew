"""
Log service module for the exchange system.
Provides functions for generating log messages and recording system logs.
"""

import logging
from datetime import datetime
from services.db_service import DatabaseService
from models.exchange_models import SystemLog

# 配置日志记录器
logger = logging.getLogger(__name__)

class LogService:
    """日志服务类 - 提供系统日志记录功能"""
    
    @staticmethod
    def log_system_event(message, operator_id=None, branch_id=None, ip_address=None):
        """
        记录系统事件日志
        
        Args:
            message (str): 日志消息
            operator_id (int, optional): 操作员ID
            branch_id (int, optional): 分支ID
            ip_address (str, optional): IP地址
        """
        try:
            # 记录到文件
            logger.info(f"[系统事件] {message} - 操作员: {operator_id}, 分支: {branch_id}")
            
            # 记录到数据库
            session = DatabaseService.get_session()
            try:
                system_log = SystemLog(
                    operator_id=operator_id,
                    operation='system_event',
                    log_type='system',  # 添加必需的log_type字段
                    action=message,  # 添加必需的action字段
                    details=message,
                    ip_address=ip_address,
                    created_at=datetime.now()
                )
                session.add(system_log)
                session.commit()
            except Exception as e:
                session.rollback()
                logger.error(f"记录系统日志到数据库失败: {str(e)}")
            finally:
                DatabaseService.close_session(session)
                
        except Exception as e:
            logger.error(f"记录系统事件失败: {str(e)}")
    
    @staticmethod
    def log_error(message, operator_id=None, branch_id=None, exception=None):
        """
        记录错误日志
        
        Args:
            message (str): 错误消息
            operator_id (int, optional): 操作员ID
            branch_id (int, optional): 分支ID
            exception (Exception, optional): 异常对象
        """
        try:
            error_msg = f"[错误] {message}"
            if exception:
                error_msg += f" - 异常: {str(exception)}"
            
            # 记录到文件
            logger.error(f"{error_msg} - 操作员: {operator_id}, 分支: {branch_id}")
            
            # 记录到数据库
            session = DatabaseService.get_session()
            try:
                system_log = SystemLog(
                    operator_id=operator_id,
                    operation='error',
                    log_type='error',  # 添加必需的log_type字段
                    action=error_msg,  # 添加必需的action字段
                    details=error_msg,
                    created_at=datetime.now()
                )
                session.add(system_log)
                session.commit()
            except Exception as e:
                session.rollback()
                logger.error(f"记录错误日志到数据库失败: {str(e)}")
            finally:
                DatabaseService.close_session(session)
                
        except Exception as e:
            logger.error(f"记录错误日志失败: {str(e)}")
    
    @staticmethod
    def log_business_operation(operation_type, message, operator_id=None, branch_id=None, transaction_id=None):
        """
        记录业务操作日志
        
        Args:
            operation_type (str): 操作类型
            message (str): 操作消息
            operator_id (int, optional): 操作员ID
            branch_id (int, optional): 分支ID
            transaction_id (int, optional): 交易ID
        """
        try:
            # 记录到文件
            logger.info(f"[业务操作] {operation_type}: {message} - 操作员: {operator_id}, 分支: {branch_id}, 交易: {transaction_id}")
            
            # 记录到数据库
            session = DatabaseService.get_session()
            try:
                system_log = SystemLog(
                    operator_id=operator_id,
                    operation=operation_type,
                    log_type='business',  # 添加必需的log_type字段
                    action=message,  # 添加必需的action字段
                    details=message,
                    created_at=datetime.now()
                )
                session.add(system_log)
                session.commit()
            except Exception as e:
                session.rollback()
                logger.error(f"记录业务操作日志到数据库失败: {str(e)}")
            finally:
                DatabaseService.close_session(session)
                
        except Exception as e:
            logger.error(f"记录业务操作日志失败: {str(e)}")

def generate_log_action(branch_code, exchange_type, foreign_currency, local_currency, foreign_amt, local_amt, rate, operator_id):
    """
    Generate a descriptive log message for exchange operations.
    
    Args:
        branch_code (str): The code of the branch where the operation occurred
        exchange_type (str): Type of exchange operation (sell_foreign, buy_foreign, init_balance, cash_out, adjust_balance)
        foreign_currency (str): The foreign currency code
        local_currency (str): The local currency code
        foreign_amt (float): Amount in foreign currency
        local_amt (float): Amount in local currency
        rate (float): Exchange rate used
        operator_id (int): ID of the operator performing the action
        
    Returns:
        str: A descriptive log message
    """
    if exchange_type == "sell_foreign":
        return f"网点{branch_code}操作员{operator_id}收到{foreign_amt}{foreign_currency}，按汇率{rate}兑出{local_amt}{local_currency}"
    elif exchange_type == "buy_foreign":
        return f"网点{branch_code}操作员{operator_id}收到{local_amt}{local_currency}，按汇率{rate}兑出{foreign_amt}{foreign_currency}"
    elif exchange_type == "init_balance":
        return f"网点{branch_code}操作员{operator_id}设置期初：{foreign_amt}{foreign_currency}"
    elif exchange_type == "cash_out":
        return f"网点{branch_code}操作员{operator_id}交款支出：{foreign_amt}{foreign_currency}"
    elif exchange_type == "adjust_balance":
        direction = "调增" if foreign_amt > 0 else "调减"
        return f"网点{branch_code}操作员{operator_id}手动{direction}{abs(foreign_amt)}{foreign_currency}"
    else:
        return f"网点{branch_code}操作员{operator_id}执行{exchange_type}操作：{foreign_amt}{foreign_currency}"

def record_system_log(db_session, operator_id, operation, details=None, ip_address=None):
    """
    Record a system log entry in the database.
    
    Args:
        db_session: Database session
        operator_id (int): ID of the operator performing the action
        operation (str): Type of operation
        details (str, optional): Additional details about the operation
        ip_address (str, optional): IP address of the client
        
    Returns:
        int: ID of the created log entry
    """
    try:
        cursor = db_session.cursor()
        cursor.execute(
            "INSERT INTO system_logs (operator_id, operation, details, ip_address) VALUES (?, ?, ?, ?)",
            (operator_id, operation, details, ip_address)
        )
        db_session.commit()
        return cursor.lastrowid
    except Exception as e:
        db_session.rollback()
        raise e
