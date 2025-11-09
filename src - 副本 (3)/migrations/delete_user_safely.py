#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全删除用户的脚本
处理外键约束，确保数据完整性
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.db_service import DatabaseService
from models.exchange_models import Operator, OperatorActivityLog, SystemLog, ExchangeTransaction
from sqlalchemy import text
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_user_info(user_id):
    """获取用户信息"""
    session = DatabaseService.get_session()
    try:
        user = session.query(Operator).filter(Operator.id == user_id).first()
        if user:
            return {
                'id': user.id,
                'name': user.name,
                'login_code': user.login_code,
                'role_name': user.role.role_name if user.role else '未分配'
            }
        return None
    finally:
        DatabaseService.close_session(session)

def count_related_records(user_id):
    """统计相关记录数量"""
    session = DatabaseService.get_session()
    try:
        activity_count = session.query(OperatorActivityLog).filter(
            OperatorActivityLog.operator_id == user_id
        ).count()
        
        system_log_count = session.query(SystemLog).filter(
            SystemLog.operator_id == user_id
        ).count()
        
        transaction_count = session.query(ExchangeTransaction).filter(
            ExchangeTransaction.operator_id == user_id
        ).count()
        
        return {
            'activity_logs': activity_count,
            'system_logs': system_log_count,
            'transactions': transaction_count
        }
    finally:
        DatabaseService.close_session(session)

def delete_user_safely(user_id):
    """安全删除用户"""
    session = DatabaseService.get_session()
    
    try:
        # 1. 获取用户信息
        user_info = get_user_info(user_id)
        if not user_info:
            logger.error(f"用户ID {user_id} 不存在")
            return False, "用户不存在"
        
        logger.info(f"准备删除用户: {user_info['name']} ({user_info['login_code']})")
        
        # 2. 统计相关记录
        counts = count_related_records(user_id)
        logger.info(f"相关记录统计:")
        logger.info(f"  - 活动日志: {counts['activity_logs']} 条")
        logger.info(f"  - 系统日志: {counts['system_logs']} 条")
        logger.info(f"  - 交易记录: {counts['transactions']} 条")
        
        # 3. 删除活动日志
        if counts['activity_logs'] > 0:
            deleted_activity = session.query(OperatorActivityLog).filter(
                OperatorActivityLog.operator_id == user_id
            ).delete()
            logger.info(f"已删除 {deleted_activity} 条活动日志")
        
        # 4. 删除系统日志
        if counts['system_logs'] > 0:
            deleted_system_logs = session.query(SystemLog).filter(
                SystemLog.operator_id == user_id
            ).delete()
            logger.info(f"已删除 {deleted_system_logs} 条系统日志")
        
        # 5. 删除交易记录（如果有）
        if counts['transactions'] > 0:
            deleted_transactions = session.query(ExchangeTransaction).filter(
                ExchangeTransaction.operator_id == user_id
            ).delete()
            logger.info(f"已删除 {deleted_transactions} 条交易记录")
        
        # 6. 删除用户
        user = session.query(Operator).filter(Operator.id == user_id).first()
        if user:
            session.delete(user)
            logger.info(f"已删除用户: {user_info['name']}")
        
        # 7. 提交事务
        DatabaseService.commit_session(session)
        logger.info("用户删除完成")
        return True, "用户删除成功"
        
    except Exception as e:
        DatabaseService.rollback_session(session)
        logger.error(f"删除用户时发生错误: {str(e)}")
        return False, f"删除失败: {str(e)}"
    finally:
        DatabaseService.close_session(session)

def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("使用方法: python delete_user_safely.py <user_id>")
        print("示例: python delete_user_safely.py 14")
        return
    
    try:
        user_id = int(sys.argv[1])
    except ValueError:
        print("错误: 用户ID必须是数字")
        return
    
    # 显示用户信息
    user_info = get_user_info(user_id)
    if not user_info:
        print(f"错误: 用户ID {user_id} 不存在")
        return
    
    print(f"\n用户信息:")
    print(f"  ID: {user_info['id']}")
    print(f"  姓名: {user_info['name']}")
    print(f"  登录代码: {user_info['login_code']}")
    print(f"  角色: {user_info['role_name']}")
    
    # 显示相关记录
    counts = count_related_records(user_id)
    print(f"\n相关记录:")
    print(f"  活动日志: {counts['activity_logs']} 条")
    print(f"  系统日志: {counts['system_logs']} 条")
    print(f"  交易记录: {counts['transactions']} 条")
    
    # 确认删除
    confirm = input(f"\n确定要删除用户 {user_info['name']} 吗？(y/N): ")
    if confirm.lower() != 'y':
        print("操作已取消")
        return
    
    # 执行删除
    success, message = delete_user_safely(user_id)
    if success:
        print(f"\n✅ {message}")
    else:
        print(f"\n❌ {message}")

if __name__ == "__main__":
    main() 