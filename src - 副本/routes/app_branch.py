from flask import Blueprint, request, jsonify
from datetime import datetime, date
from models.exchange_models import Branch, Currency, ExchangeRate
from services.db_service import get_db_session
from services.auth_service import token_required, has_permission

branch_bp = Blueprint('branch', __name__, url_prefix='/branch')

@branch_bp.route('/<int:branch_id>/currencies', methods=['GET'])
@token_required
def get_branch_currencies(current_user, branch_id):
    """
    Get available currencies for a specific branch with today's exchange rates
    """
    session = get_db_session()
    try:
        # Get branch information
        branch = session.query(Branch).filter_by(id=branch_id).first()
        if not branch:
            return jsonify({
                'success': False,
                'message': 'Branch not found'
            }), 404

        today = date.today()

        # Get only today's exchange rates for the branch
        rates = session.query(
            ExchangeRate,
            Currency
        ).join(
            Currency,
            ExchangeRate.currency_id == Currency.id
        ).filter(
            ExchangeRate.branch_id == branch_id,
            ExchangeRate.rate_date == today
        ).all()

        # Format response
        currencies = []
        for rate, currency in rates:
            if currency.currency_code != branch.base_currency.currency_code:
                currencies.append({
                    'id': currency.id,
                    'currency_code': currency.currency_code,
                    'currency_name': currency.currency_name,
                    'flag_code': currency.flag_code,
                    'symbol': currency.symbol
                })

        return jsonify({
            'success': True,
            'currencies': currencies
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        session.close() 