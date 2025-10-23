from datetime import datetime, date
from decimal import Decimal
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import func, and_, or_
from models.denomination_models import CurrencyDenomination, DenominationRate, TransactionDenomination
from models.exchange_models import Currency, Branch, Operator
from services.db_service import DatabaseService
from services.auth_service import token_required, has_permission
from utils.multilingual_log_service import multilingual_logger
import logging

# 设置日志记录器
logger = logging.getLogger(__name__)



denomination_bp = Blueprint('denominations', __name__, url_prefix='/api/denominations')

@denomination_bp.route('/', methods=['OPTIONS'])
def handle_options():
    """处理CORS预检请求"""
    response = jsonify({'message': 'CORS preflight'})
    origin = request.headers.get('Origin')
    # 允许所有origin，由全局CORS配置统一管理
    response.headers['Access-Control-Allow-Origin'] = origin if origin else "*"
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,X-Requested-With,Accept,Origin'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Max-Age'] = '86400'
    return response, 200

@denomination_bp.route('/<int:currency_id>/last-rates', methods=['GET'])
@token_required
def get_last_denomination_rates(current_user, currency_id):
    """获取指定币种最近的面值汇率"""
    current_app.logger.info(f"获取币种 {currency_id} 的最近面值汇率")
    session = DatabaseService.get_session()
    try:
        # 验证币种是否存在
        currency = session.query(Currency).filter_by(id=currency_id).first()
        if not currency:
            return jsonify({'success': False, 'message': '币种不存在'}), 404
        
        # 获取最近的面值汇率记录（只获取当前网点的）
        from models.denomination_models import DenominationRate
        branch_id = current_user['branch_id']
        last_rates = session.query(DenominationRate).filter(
            DenominationRate.currency_id == currency_id,
            DenominationRate.branch_id == branch_id  # 添加网点过滤
        ).order_by(DenominationRate.created_at.desc()).all()
        
        if not last_rates:
            return jsonify({
                'success': True, 
                'message': '该币种暂无历史汇率记录',
                'data': []
            })
        
        # 按面值分组，获取每个面值的最新汇率
        rates_by_denomination = {}
        for rate in last_rates:
            # 通过关联的denomination对象获取面值信息
            if rate.denomination:
                denomination_value = float(rate.denomination.denomination_value)
                denomination_type = rate.denomination.denomination_type
                key = (rate.denomination_id, denomination_value, denomination_type)
                if key not in rates_by_denomination:
                    rates_by_denomination[key] = rate
        
        # 转换为字典格式
        result = []
        for (denomination_id, denomination_value, denomination_type), rate in rates_by_denomination.items():
            result.append({
                'denomination_id': denomination_id,
                'denomination_value': denomination_value,
                'denomination_type': denomination_type,
                'buy_rate': float(rate.buy_rate),
                'sell_rate': float(rate.sell_rate),
                'created_at': rate.created_at.isoformat() if rate.created_at else None
            })
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        current_app.logger.error(f"获取最近面值汇率失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取最近面值汇率失败: {str(e)}'}), 500
    finally:
        session.close()

@denomination_bp.route('/<int:currency_id>', methods=['GET'])
@token_required
def get_currency_denominations(current_user, currency_id):
    """获取指定币种的面值列表"""
    session = DatabaseService.get_session()
    try:
        # 验证币种是否存在
        currency = session.query(Currency).filter_by(id=currency_id).first()
        if not currency:
            return jsonify({'success': False, 'message': '币种不存在'}), 404
        
        # 获取面值列表
        denominations = session.query(CurrencyDenomination).filter(
            CurrencyDenomination.currency_id == currency_id,
            CurrencyDenomination.is_active == True
        ).order_by(CurrencyDenomination.sort_order, CurrencyDenomination.denomination_value).all()
        
        return jsonify({
            'success': True,
            'data': [denom.to_dict() for denom in denominations]
        })
        
    except Exception as e:
        current_app.logger.error(f"获取面值列表失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取面值列表失败: {str(e)}'}), 500
    finally:
        session.close()

@denomination_bp.route('/', methods=['POST', 'OPTIONS'])
@token_required
@has_permission('rate_manage')
def create_denomination(current_user):
    """创建面值"""
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'CORS preflight'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With,Accept')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response, 200
    
    session = DatabaseService.get_session()
    try:
        data = request.get_json()
        
        # 验证必要字段
        required_fields = ['currency_id', 'denomination_value', 'denomination_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'缺少必要字段: {field}'}), 400
        
        # 验证币种是否存在
        currency = session.query(Currency).filter_by(id=data['currency_id']).first()
        if not currency:
            return jsonify({'success': False, 'message': '币种不存在'}), 404
        
        # 检查面值是否已存在
        existing = session.query(CurrencyDenomination).filter(
            CurrencyDenomination.currency_id == data['currency_id'],
            CurrencyDenomination.denomination_value == Decimal(str(data['denomination_value'])),
            CurrencyDenomination.denomination_type == data['denomination_type']
        ).first()
        
        if existing:
            return jsonify({'success': False, 'message': '该面值已存在'}), 400
        
        # 创建面值
        denomination = CurrencyDenomination(
            currency_id=data['currency_id'],
            denomination_value=Decimal(str(data['denomination_value'])),
            denomination_type=data['denomination_type'],
            is_active=data.get('is_active', True),
            sort_order=data.get('sort_order', 0)
        )
        
        session.add(denomination)
        session.commit()
        
        # 记录日志
        multilingual_logger.log_system_operation(
            'create_denomination',
            operator_id=current_user['id'],
            branch_id=current_user['branch_id'],
            details=f"创建面值: 币种{currency.currency_code} 面值{denomination.denomination_value} {denomination.denomination_type}"
        )
        
        return jsonify({
            'success': True,
            'message': '面值创建成功',
            'data': denomination.to_dict()
        })
        
    except Exception as e:
        session.rollback()
        current_app.logger.error(f"创建面值失败: {str(e)}")
        return jsonify({'success': False, 'message': f'创建面值失败: {str(e)}'}), 500
    finally:
        session.close()

@denomination_bp.route('/<int:denomination_id>', methods=['PUT', 'OPTIONS'])
@token_required
@has_permission('rate_manage')
def update_denomination(current_user, denomination_id):
    """更新面值"""
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'CORS preflight'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With,Accept')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response, 200
    
    session = DatabaseService.get_session()
    try:
        data = request.get_json()
        
        # 查找面值
        denomination = session.query(CurrencyDenomination).filter_by(id=denomination_id).first()
        if not denomination:
            return jsonify({'success': False, 'message': '面值不存在'}), 404
        
        # 更新字段
        if 'denomination_value' in data:
            denomination.denomination_value = Decimal(str(data['denomination_value']))
        if 'denomination_type' in data:
            denomination.denomination_type = data['denomination_type']
        if 'is_active' in data:
            denomination.is_active = data['is_active']
        if 'sort_order' in data:
            denomination.sort_order = data['sort_order']
        
        denomination.updated_at = datetime.utcnow()
        
        session.commit()
        
        # 记录日志
        multilingual_logger.log_system_operation(
            'update_denomination',
            operator_id=current_user['id'],
            branch_id=current_user['branch_id'],
            details=f"更新面值: ID{denomination_id}"
        )
        
        return jsonify({
            'success': True,
            'message': '面值更新成功',
            'data': denomination.to_dict()
        })
        
    except Exception as e:
        session.rollback()
        current_app.logger.error(f"更新面值失败: {str(e)}")
        return jsonify({'success': False, 'message': f'更新面值失败: {str(e)}'}), 500
    finally:
        session.close()

@denomination_bp.route('/<int:denomination_id>', methods=['DELETE'])
@token_required
@has_permission('rate_manage')
def delete_denomination(current_user, denomination_id):
    """删除面值（软删除）"""
    session = DatabaseService.get_session()
    try:
        # 查找面值
        denomination = session.query(CurrencyDenomination).filter_by(id=denomination_id).first()
        if not denomination:
            return jsonify({'success': False, 'message': '面值不存在'}), 404
        
        # 检查是否有相关汇率记录
        rate_count = session.query(DenominationRate).filter_by(denomination_id=denomination_id).count()
        if rate_count > 0:
            return jsonify({'success': False, 'message': '该面值存在汇率记录，无法删除'}), 400
        
        # 软删除
        denomination.is_active = False
        denomination.updated_at = datetime.utcnow()
        
        session.commit()
        
        # 记录日志
        multilingual_logger.log_system_operation(
            'delete_denomination',
            operator_id=current_user['id'],
            branch_id=current_user['branch_id'],
            details=f"删除面值: ID{denomination_id}"
        )
        
        return jsonify({
            'success': True,
            'message': '面值删除成功'
        })
        
    except Exception as e:
        session.rollback()
        current_app.logger.error(f"删除面值失败: {str(e)}")
        return jsonify({'success': False, 'message': f'删除面值失败: {str(e)}'}), 500
    finally:
        session.close()

@denomination_bp.route('/rates', methods=['GET'])
@token_required
def get_denomination_rates(current_user):
    """获取面值汇率列表"""
    session = DatabaseService.get_session()
    try:
        branch_id = current_user['branch_id']
        currency_id = request.args.get('currency_id')
        rate_date = request.args.get('rate_date', date.today().isoformat())
        
        # 构建查询条件
        query = session.query(DenominationRate).filter(
            DenominationRate.branch_id == branch_id,
            DenominationRate.rate_date == rate_date
        )
        
        # 如果指定了币种ID，则按币种过滤
        if currency_id:
            query = query.filter(DenominationRate.currency_id == currency_id)
        
        # 获取面值汇率，按创建时间降序排列，确保获取最新的
        from sqlalchemy.orm import joinedload
        rates = query.options(
            joinedload(DenominationRate.currency),
            joinedload(DenominationRate.denomination)
        ).join(CurrencyDenomination).order_by(
            DenominationRate.currency_id,
            CurrencyDenomination.sort_order,
            CurrencyDenomination.denomination_value,
            DenominationRate.created_at.desc()
        ).all()
        
        # 去重：只保留每个面值的最新记录
        unique_rates = {}
        for rate in rates:
            # 通过面值ID和币种ID组合去重，确保每个面值只有一条记录
            key = f"{rate.currency_id}_{rate.denomination_id}"
            if key not in unique_rates:
                unique_rates[key] = rate
        
        # 构建包含币种信息的完整数据
        result_data = []
        for rate in unique_rates.values():
            rate_dict = rate.to_dict()
            # 添加币种信息
            if rate.currency:
                rate_dict.update({
                    'currency_code': rate.currency.currency_code,
                    'currency_name': rate.currency.currency_name,
                    'flag_code': rate.currency.flag_code,
                    'custom_flag_filename': rate.currency.custom_flag_filename
                })
            result_data.append(rate_dict)
        
        return jsonify({
            'success': True,
            'data': result_data
        })
        
    except Exception as e:
        current_app.logger.error(f"获取面值汇率失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取面值汇率失败: {str(e)}'}), 500
    finally:
        session.close()

@denomination_bp.route('/rates', methods=['POST'])
@token_required
@has_permission('rate_manage')
def set_denomination_rates(current_user):
    """设置面值汇率"""
    session = DatabaseService.get_session()
    try:
        data = request.get_json()
        
        # 验证必要字段
        required_fields = ['currency_id', 'denomination_id', 'buy_rate', 'sell_rate']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'缺少必要字段: {field}'}), 400
        
        branch_id = current_user['branch_id']
        rate_date = data.get('rate_date', date.today().isoformat())
        
        # 查找或创建面值汇率记录
        rate = session.query(DenominationRate).filter(
            DenominationRate.branch_id == branch_id,
            DenominationRate.currency_id == data['currency_id'],
            DenominationRate.denomination_id == data['denomination_id'],
            DenominationRate.rate_date == rate_date
        ).first()
        
        if rate:
            # 更新现有记录
            rate.buy_rate = Decimal(str(data['buy_rate']))
            rate.sell_rate = Decimal(str(data['sell_rate']))
            rate.updated_at = datetime.utcnow()
        else:
            # 创建新记录
            rate = DenominationRate(
                branch_id=branch_id,
                currency_id=data['currency_id'],
                denomination_id=data['denomination_id'],
                rate_date=rate_date,
                buy_rate=Decimal(str(data['buy_rate'])),
                sell_rate=Decimal(str(data['sell_rate'])),
                created_by=current_user['id']
            )
            session.add(rate)
        
        session.commit()
        
        # 记录日志
        multilingual_logger.log_system_operation(
            operation_key="denomination_rate_set",
            operator_id=current_user['id'],
            branch_id=branch_id,
            details=f"设置面值汇率: 币种{data['currency_id']} 面值{data['denomination_id']} 买入价{data['buy_rate']} 卖出价{data['sell_rate']}"
        )
        
        return jsonify({
            'success': True,
            'message': '面值汇率设置成功',
            'data': rate.to_dict()
        })
        
    except Exception as e:
        session.rollback()
        current_app.logger.error(f"设置面值汇率失败: {str(e)}")
        return jsonify({'success': False, 'message': f'设置面值汇率失败: {str(e)}'}), 500
    finally:
        session.close()

@denomination_bp.route('/rates/<int:rate_id>', methods=['PUT'])
@token_required
@has_permission('rate_manage')
def update_denomination_rate(current_user, rate_id):
    """更新面值汇率"""
    session = DatabaseService.get_session()
    try:
        data = request.get_json()
        
        # 查找汇率记录
        rate = session.query(DenominationRate).filter_by(id=rate_id).first()
        if not rate:
            return jsonify({'success': False, 'message': '汇率记录不存在'}), 404
        
        # 验证权限
        if rate.branch_id != current_user['branch_id']:
            return jsonify({'success': False, 'message': '无权限操作'}), 403
        
        # 更新汇率
        if 'buy_rate' in data:
            rate.buy_rate = Decimal(str(data['buy_rate']))
        if 'sell_rate' in data:
            rate.sell_rate = Decimal(str(data['sell_rate']))
        
        rate.updated_at = datetime.utcnow()
        
        session.commit()
        
        # 记录日志
        multilingual_logger.log_system_operation(
            'update_denomination_rate',
            operator_id=current_user['id'],
            branch_id=current_user['branch_id'],
            details=f"更新面值汇率: ID{rate_id}"
        )
        
        return jsonify({
            'success': True,
            'message': '面值汇率更新成功',
            'data': rate.to_dict()
        })
        
    except Exception as e:
        session.rollback()
        current_app.logger.error(f"更新面值汇率失败: {str(e)}")
        return jsonify({'success': False, 'message': f'更新面值汇率失败: {str(e)}'}), 500
    finally:
        session.close()