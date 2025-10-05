#!/usr/bin/env python3
"""
面值汇率相关API
"""

from flask import Blueprint, request, jsonify
from sqlalchemy import func, desc
from models.exchange_models import Currency
from models.denomination_models import CurrencyDenomination, DenominationRate
from services.db_service import DatabaseService
from services.auth_service import token_required, has_permission
from datetime import datetime

# 币种多语言映射
def get_currency_names(currency_code):
    """获取币种的多语言名称"""
    currency_mappings = {
        'USD': {'zh': '美元', 'en': 'US Dollar', 'th': 'ดอลลาร์สหรัฐ'},
        'EUR': {'zh': '欧元', 'en': 'Euro', 'th': 'ยูโร'},
        'GBP': {'zh': '英镑', 'en': 'British Pound', 'th': 'ปอนด์อังกฤษ'},
        'JPY': {'zh': '日元', 'en': 'Japanese Yen', 'th': 'เยนญี่ปุ่น'},
        'CNY': {'zh': '人民币', 'en': 'Chinese Yuan', 'th': 'หยวนจีน'},
        'HKD': {'zh': '港币', 'en': 'Hong Kong Dollar', 'th': 'ดอลลาร์ฮ่องกง'},
        'SGD': {'zh': '新加坡元', 'en': 'Singapore Dollar', 'th': 'ดอลลาร์สิงคโปร์'},
        'KRW': {'zh': '韩元', 'en': 'South Korean Won', 'th': 'วอนเกาหลีใต้'},
        'MYR': {'zh': '马来西亚林吉特', 'en': 'Malaysian Ringgit', 'th': 'ริงกิตมาเลเซีย'},
        'THB': {'zh': '泰铢', 'en': 'Thai Baht', 'th': 'บาทไทย'},
        'CAD': {'zh': '加拿大元', 'en': 'Canadian Dollar', 'th': 'ดอลลาร์แคนาดา'},
        'AUD': {'zh': '澳大利亚元', 'en': 'Australian Dollar', 'th': 'ดอลลาร์ออสเตรเลีย'},
        'CHF': {'zh': '瑞士法郎', 'en': 'Swiss Franc', 'th': 'ฟรังก์สวิส'},
        'NZD': {'zh': '新西兰元', 'en': 'New Zealand Dollar', 'th': 'ดอลลาร์นิวซีแลนด์'},
        'SEK': {'zh': '瑞典克朗', 'en': 'Swedish Krona', 'th': 'โครนาสวีเดน'},
        'NOK': {'zh': '挪威克朗', 'en': 'Norwegian Krone', 'th': 'โครนานอร์เวย์'},
        'DKK': {'zh': '丹麦克朗', 'en': 'Danish Krone', 'th': 'โครนาเดนมาร์ก'},
        'RUB': {'zh': '俄罗斯卢布', 'en': 'Russian Ruble', 'th': 'รูเบิลรัสเซีย'},
        'INR': {'zh': '印度卢比', 'en': 'Indian Rupee', 'th': 'รูปีอินเดีย'},
        'PHP': {'zh': '菲律宾比索', 'en': 'Philippine Peso', 'th': 'เปโซฟิลิปปินส์'},
        'IDR': {'zh': '印尼卢比', 'en': 'Indonesian Rupiah', 'th': 'รูเปียอินโดนีเซีย'},
        'VND': {'zh': '越南盾', 'en': 'Vietnamese Dong', 'th': 'ดองเวียดนาม'},
        'TWD': {'zh': '新台币', 'en': 'New Taiwan Dollar', 'th': 'ดอลลาร์ไต้หวันใหม่'},
    }

    return currency_mappings.get(currency_code, {
        'zh': currency_code,  # 默认使用币种代码
        'en': currency_code,
        'th': currency_code
    })

denominations_api_bp = Blueprint('denominations_api', __name__, url_prefix='/api/denominations-api')

@denominations_api_bp.route('/currencies-with-denominations', methods=['GET'])
@token_required
@has_permission('rate_manage')
def get_currencies_with_denominations(current_user):
    """获取所有设置了面值汇率的币种（含今日发布状态）"""
    session = DatabaseService.get_session()
    try:
        # 查询所有币种及其面值设置
        currencies = session.query(Currency).all()
        today = datetime.now().date()

        result = []
        for currency in currencies:
            # 获取该币种的面值设置
            denominations = session.query(CurrencyDenomination).filter_by(
                currency_id=currency.id
            ).all()

            if denominations:
                # 获取最新的面值汇率
                denomination_rates = []
                for denom in denominations:
                    latest_rate = session.query(DenominationRate).filter_by(
                        denomination_id=denom.id
                    ).order_by(desc(DenominationRate.created_at)).first()

                    if latest_rate:
                        denomination_rates.append({
                            'id': denom.id,
                            'denomination_value': float(denom.denomination_value),
                            'denomination_type': denom.denomination_type,
                            'buy_rate': float(latest_rate.buy_rate) if latest_rate.buy_rate else None,
                            'sell_rate': float(latest_rate.sell_rate) if latest_rate.sell_rate else None,
                            'last_updated': latest_rate.created_at.isoformat() if latest_rate.created_at else None
                        })

                if denomination_rates:
                    # 检查该币种今日是否已发布
                    from models.exchange_models import RatePublishRecord, DenominationPublishDetail

                    today_published = session.query(RatePublishRecord).join(
                        DenominationPublishDetail
                    ).filter(
                        func.date(RatePublishRecord.created_at) == today,
                        DenominationPublishDetail.currency_id == currency.id
                    ).first() is not None

                    # 计算最后更新时间
                    last_updated = max(
                        [d['last_updated'] for d in denomination_rates if d['last_updated']],
                        default=None
                    )

                    # 获取币种的多语言名称
                    currency_names = get_currency_names(currency.currency_code)

                    result.append({
                        'id': currency.id,
                        'currency_code': currency.currency_code,
                        'currency_name': currency.currency_name,
                        'currency_names': currency_names,  # 新增：多语言名称
                        'flag_code': currency.flag_code,
                        'custom_flag_filename': currency.custom_flag_filename,
                        'denominations': denomination_rates,
                        'last_updated': last_updated,
                        'published_today': today_published  # 新增：今日是否已发布
                    })
        
        print(f"[面值汇率API] 返回 {len(result)} 个币种:")
        for curr in result:
            status = "已发布" if curr['published_today'] else "未发布"
            print(f"  - {curr['currency_code']}: {len(curr['denominations'])} 个面值, 今日状态: {status}")

        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        print(f"获取币种面值汇率失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取数据失败: {str(e)}'}), 500
    finally:
        DatabaseService.close_session(session)

@denominations_api_bp.route('/currency/<int:currency_id>/denominations', methods=['GET'])
@token_required
@has_permission('rate_manage')
def get_currency_denominations(current_user, currency_id):
    """获取指定币种的面值设置"""
    session = DatabaseService.get_session()
    try:
        # 获取币种信息
        currency = session.query(Currency).filter_by(id=currency_id).first()
        if not currency:
            return jsonify({'success': False, 'message': '币种不存在'}), 404
        
        # 获取面值设置
        denominations = session.query(CurrencyDenomination).filter_by(
            currency_id=currency_id
        ).all()
        
        result = []
        for denom in denominations:
            # 获取最新的面值汇率
            latest_rate = session.query(DenominationRate).filter_by(
                denomination_id=denom.id
            ).order_by(desc(DenominationRate.created_at)).first()
            
            result.append({
                'id': denom.id,
                'denomination_value': float(denom.denomination_value),
                'denomination_type': denom.denomination_type,
                'buy_rate': float(latest_rate.buy_rate) if latest_rate and latest_rate.buy_rate else None,
                'sell_rate': float(latest_rate.sell_rate) if latest_rate and latest_rate.sell_rate else None,
                'last_updated': latest_rate.created_at.isoformat() if latest_rate and latest_rate.created_at else None
            })
        
        return jsonify({
            'success': True,
            'data': {
                'currency': {
                    'id': currency.id,
                    'currency_code': currency.currency_code,
                    'currency_name': currency.currency_name,
                    'flag_code': currency.flag_code,
                    'custom_flag_filename': currency.custom_flag_filename
                },
                'denominations': result
            }
        })
        
    except Exception as e:
        print(f"获取币种面值设置失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取数据失败: {str(e)}'}), 500
    finally:
        DatabaseService.close_session(session)