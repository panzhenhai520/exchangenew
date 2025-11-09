"""
币种相关工具函数
统一管理本币信息获取逻辑，避免硬编码
"""
import logging
from services.db_service import DatabaseService
from models.exchange_models import Branch


def get_base_currency_id_from_branch(branch_id):
    """
    根据网点ID获取该网点的本币ID
    统一函数，避免硬编码
    
    Args:
        branch_id: 网点ID
        
    Returns:
        int: 本币ID，如果无法获取则返回None
    """
    try:
        session = DatabaseService.get_session()
        branch = session.query(Branch).filter_by(id=branch_id).first()
        if branch and branch.base_currency_id:
            logging.info(f"[OK] 网点 {branch_id} 的本币ID: {branch.base_currency_id}")
            return branch.base_currency_id
        else:
            logging.error(f"[ERROR] 无法获取网点 {branch_id} 的本币ID")
            return None
    except Exception as e:
        logging.error(f"[ERROR] 获取网点本币ID失败: {str(e)}")
        return None
    finally:
        DatabaseService.close_session(session)


def is_base_currency(branch_id, currency_id):
    """
    检查指定币种ID是否为指定网点的本币
    
    Args:
        branch_id: 网点ID
        currency_id: 要检查的币种ID
        
    Returns:
        bool: 是否为本币
    """
    base_currency_id = get_base_currency_id_from_branch(branch_id)
    return base_currency_id is not None and currency_id == base_currency_id


def get_base_currency_info_from_branch(branch_id):
    """
    根据网点ID获取该网点的完整本币信息
    
    Args:
        branch_id: 网点ID
        
    Returns:
        dict: 本币信息 {id, code, name}，如果无法获取则返回None
    """
    try:
        session = DatabaseService.get_session()
        branch = session.query(Branch).filter_by(id=branch_id).first()
        if branch and branch.base_currency_id and branch.base_currency:
            base_currency_info = {
                'id': branch.base_currency_id,
                'code': branch.base_currency.currency_code,
                'name': branch.base_currency.currency_name
            }
            logging.info(f"[OK] 网点 {branch_id} 的本币信息: {base_currency_info}")
            return base_currency_info
        else:
            logging.error(f"[ERROR] 无法获取网点 {branch_id} 的本币信息")
            return None
    except Exception as e:
        logging.error(f"[ERROR] 获取网点本币信息失败: {str(e)}")
        return None
    finally:
        DatabaseService.close_session(session) 