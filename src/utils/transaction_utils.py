from datetime import datetime
import random
import string
from services.receipt_service import ReceiptService

def generate_unified_transaction_no(branch_id, transaction_type='EXCHANGE', session=None):
    """
    统一的单据号生成服务
    所有业务类型都使用相同的ReceiptService来确保格式一致
    
    Args:
        branch_id: 网点ID (必须提供)
        transaction_type: 业务类型 (EXCHANGE, ADJUSTMENT, INITIAL, REVERSAL, EOD)
        session: 数据库会话
    
    Returns:
        str: 统一格式的单据号 (例如: A005202506180013)
    """
    if not branch_id:
        raise ValueError("branch_id 是必需参数，无法生成统一格式的单据号")
    
    try:
        # 统一使用 ReceiptService 确保格式一致
        return ReceiptService.generate_receipt_number(branch_id, session)
    except Exception as e:
        raise Exception(f"票据号生成失败: {e}")

def generate_transaction_no(branch_id=None, session=None):
    """
    生成唯一的交易编号
    统一调用新的单据号生成服务
    
    Args:
        branch_id: 网点ID（推荐提供）
        session: 数据库会话（可选）
    
    Returns:
        str: 生成的交易编号
    """
    return generate_unified_transaction_no(branch_id, 'EXCHANGE', session)

def generate_receipt_number(branch_id, session=None):
    """
    生成票据编号（新版本）
    包含网点信息并确保连续性
    与generate_transaction_no保持完全一致
    """
    return generate_unified_transaction_no(branch_id, 'EXCHANGE', session) 