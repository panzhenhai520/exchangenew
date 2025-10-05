from flask import Blueprint, request, jsonify
from datetime import datetime
from models.exchange_models import TransactionPurposeLimit, Branch, Currency
from services.db_service import DatabaseService
from services.auth_service import token_required, has_permission
from sqlalchemy import and_
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

purpose_limits_bp = Blueprint('purpose_limits', __name__, url_prefix='/api/system/purpose-limits')

@purpose_limits_bp.route('', methods=['GET'])
@token_required
@has_permission('system_manage')
def get_purpose_limits(current_user):
    """获取交易用途限额列表"""
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
    
    session = DatabaseService.get_session()
    try:
        # 获取查询参数
        currency_code = request.args.get('currency_code', '').strip()
        is_active = request.args.get('is_active', '').strip()
        
        # 构建查询
        query = session.query(TransactionPurposeLimit).filter_by(branch_id=current_user['branch_id'])
        
        # 根据币种筛选
        if currency_code:
            query = query.filter(TransactionPurposeLimit.currency_code == currency_code)
            
        # 根据状态筛选
        if is_active:
            active_value = is_active.lower() == 'true'
            query = query.filter(TransactionPurposeLimit.is_active == active_value)
            
        # 按创建时间倒序
        purpose_limits = query.order_by(TransactionPurposeLimit.created_at.desc()).all()
        
        # 转换为字典列表
        result = [limit.to_dict() for limit in purpose_limits]
        
        return jsonify({
            'success': True,
            'purpose_limits': result,
            'total': len(result)
        })
        
    except Exception as e:
        logger.error(f"获取用途限额失败: {str(e)}")
        return jsonify({'success': False, 'message': '获取数据失败'}), 500
    finally:
        DatabaseService.close_session(session)

@purpose_limits_bp.route('', methods=['POST'])
@token_required
@has_permission('system_manage')
def create_purpose_limit(current_user):
    """创建新的交易用途限额"""
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
    
    session = DatabaseService.get_session()
    try:
        data = request.get_json()
        
        # 验证必要字段
        required_fields = ['purpose_name', 'currency_code', 'max_amount', 'display_message']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'message': f'缺少必要字段: {field}'}), 400
        
        # 检查同网点、同币种、同用途是否已存在
        existing = session.query(TransactionPurposeLimit).filter(
            and_(
                TransactionPurposeLimit.branch_id == current_user['branch_id'],
                TransactionPurposeLimit.purpose_name == data['purpose_name'],
                TransactionPurposeLimit.currency_code == data['currency_code']
            )
        ).first()
        
        if existing:
            return jsonify({
                'success': False, 
                'message': f'该网点的{data["currency_code"]}币种{data["purpose_name"]}用途限额已存在'
            }), 400
        
        # 创建新记录
        purpose_limit = TransactionPurposeLimit(
            branch_id=current_user['branch_id'],
            purpose_name=data['purpose_name'],
            currency_code=data['currency_code'],
            max_amount=float(data['max_amount']),
            display_message=data['display_message'],
            is_active=data.get('is_active', True),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        session.add(purpose_limit)
        session.commit()
        
        return jsonify({
            'success': True,
            'message': '用途限额创建成功',
            'purpose_limit': purpose_limit.to_dict()
        })
        
    except Exception as e:
        session.rollback()
        logger.error(f"创建用途限额失败: {str(e)}")
        return jsonify({'success': False, 'message': '创建失败'}), 500
    finally:
        DatabaseService.close_session(session)

@purpose_limits_bp.route('/<int:limit_id>', methods=['PUT'])
@token_required
@has_permission('system_manage')
def update_purpose_limit(current_user, limit_id):
    """更新交易用途限额"""
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
    
    session = DatabaseService.get_session()
    try:
        data = request.get_json()
        
        # 查找记录
        purpose_limit = session.query(TransactionPurposeLimit).filter(
            and_(
                TransactionPurposeLimit.id == limit_id,
                TransactionPurposeLimit.branch_id == current_user['branch_id']
            )
        ).first()
        
        if not purpose_limit:
            return jsonify({'success': False, 'message': '记录不存在'}), 404
        
        # 更新字段
        if 'purpose_name' in data:
            purpose_limit.purpose_name = data['purpose_name']
        if 'currency_code' in data:
            purpose_limit.currency_code = data['currency_code']
        if 'max_amount' in data:
            purpose_limit.max_amount = float(data['max_amount'])
        if 'display_message' in data:
            purpose_limit.display_message = data['display_message']
        if 'is_active' in data:
            purpose_limit.is_active = data['is_active']
            
        purpose_limit.updated_at = datetime.utcnow()
        
        session.commit()
        
        return jsonify({
            'success': True,
            'message': '用途限额更新成功',
            'purpose_limit': purpose_limit.to_dict()
        })
        
    except Exception as e:
        session.rollback()
        logger.error(f"更新用途限额失败: {str(e)}")
        return jsonify({'success': False, 'message': '更新失败'}), 500
    finally:
        DatabaseService.close_session(session)

@purpose_limits_bp.route('/<int:limit_id>', methods=['DELETE'])
@token_required
@has_permission('system_manage')
def delete_purpose_limit(current_user, limit_id):
    """删除交易用途限额"""
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
    
    session = DatabaseService.get_session()
    try:
        # 查找记录
        purpose_limit = session.query(TransactionPurposeLimit).filter(
            and_(
                TransactionPurposeLimit.id == limit_id,
                TransactionPurposeLimit.branch_id == current_user['branch_id']
            )
        ).first()
        
        if not purpose_limit:
            return jsonify({'success': False, 'message': '记录不存在'}), 404
        
        session.delete(purpose_limit)
        session.commit()
        
        return jsonify({
            'success': True,
            'message': '用途限额删除成功'
        })
        
    except Exception as e:
        session.rollback()
        logger.error(f"删除用途限额失败: {str(e)}")
        return jsonify({'success': False, 'message': '删除失败'}), 500
    finally:
        DatabaseService.close_session(session)

@purpose_limits_bp.route('/by-currency/<currency_code>', methods=['GET'])
@token_required
@has_permission('transaction_execute')
def get_purposes_by_currency(current_user, currency_code):
    """根据币种获取可用的交易用途列表（用于兑换页面）"""
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
    
    logger.info(f"Getting purposes for currency: {currency_code}, branch: {current_user['branch_id']}")
    
    session = DatabaseService.get_session()
    try:
        # 先检查该网点是否有任何用途限额数据
        total_limits = session.query(TransactionPurposeLimit).filter(
            TransactionPurposeLimit.branch_id == current_user['branch_id']
        ).count()
        logger.info(f"Total purpose limits for branch {current_user['branch_id']}: {total_limits}")
        
        # 查询该网点该币种的所有激活用途限额
        purpose_limits = session.query(TransactionPurposeLimit).filter(
            and_(
                TransactionPurposeLimit.branch_id == current_user['branch_id'],
                TransactionPurposeLimit.currency_code == currency_code,
                TransactionPurposeLimit.is_active == True
            )
        ).order_by(TransactionPurposeLimit.purpose_name).all()
        
        logger.info(f"Found {len(purpose_limits)} active purpose limits for currency {currency_code}")
        
        # 如果没有找到该币种的数据，检查是否有其他币种的数据
        if len(purpose_limits) == 0:
            all_currencies = session.query(TransactionPurposeLimit.currency_code).filter(
                TransactionPurposeLimit.branch_id == current_user['branch_id']
            ).distinct().all()
            available_currencies = [c[0] for c in all_currencies]
            logger.info(f"Available currencies with purpose limits: {available_currencies}")
        
        # 转换为简化的格式（用于下拉选择）
        result = []
        for limit in purpose_limits:
            result.append({
                'id': limit.id,
                'purpose_name': limit.purpose_name,
                'max_amount': float(limit.max_amount),
                'display_message': limit.display_message
            })
        
        logger.info(f"Returning {len(result)} purposes: {[p['purpose_name'] for p in result]}")
        
        return jsonify({
            'success': True,
            'purposes': result
        })
        
    except Exception as e:
        logger.error(f"获取币种用途失败: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': '获取数据失败'}), 500
    finally:
        DatabaseService.close_session(session) 