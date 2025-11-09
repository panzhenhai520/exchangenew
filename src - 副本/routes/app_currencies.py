from flask import Blueprint, jsonify
from models.exchange_models import Currency
from services.db_service import DatabaseService
from services.auth_service import token_required

currencies_bp = Blueprint('currencies', __name__, url_prefix='/api/currencies')

@currencies_bp.route('', methods=['GET'])
@token_required
def get_currencies(current_user):
    """获取所有币种信息"""
    session = DatabaseService.get_session()
    try:
        currencies = session.query(Currency).all()
        result = []
        for currency in currencies:
            result.append({
                'id': currency.id,
                'code': currency.currency_code,
                'name': currency.currency_name,
                'country': currency.country,
                'flag_code': currency.flag_code,
                'symbol': currency.symbol
            })
        
        return jsonify({
            'success': True,
            'currencies': result
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@currencies_bp.route('/code/<currency_code>', methods=['GET'])
@token_required
def get_currency_by_code(current_user, currency_code):
    """根据币种代码获取币种信息"""
    session = DatabaseService.get_session()
    try:
        currency = session.query(Currency).filter_by(currency_code=currency_code).first()
        
        if not currency:
            return jsonify({
                'success': False,
                'message': f'Currency not found with code: {currency_code}'
            }), 404
        
        return jsonify({
            'success': True,
            'currency': {
                'id': currency.id,
                'code': currency.currency_code,
                'name': currency.currency_name,
                'country': currency.country,
                'flag_code': currency.flag_code,
                'symbol': currency.symbol
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session) 