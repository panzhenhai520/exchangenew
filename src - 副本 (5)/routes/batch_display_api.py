from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
from services.db_service import DatabaseService
from models.exchange_models import RatePublishRecord, DenominationPublishDetail, Currency, Branch

# 创建批次显示API的Blueprint
batch_display_bp = Blueprint('batch_display', __name__, url_prefix='/api/dashboard')

logger = logging.getLogger(__name__)

@batch_display_bp.route('/display-batch-rates/<batch_main_token>', methods=['GET'])
def get_display_batch_rates(batch_main_token):
    """获取批次面值汇率显示数据"""
    try:
        # 检查是否强制刷新
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
        
        # 直接从数据库获取批次数据
        session = DatabaseService.get_session()
        try:
            # 查找批次主记录
            publish_record = session.query(RatePublishRecord).filter_by(
                access_token=batch_main_token
            ).first()
            
            if not publish_record:
                return jsonify({
                    'success': False,
                    'message': '批次记录不存在'
                }), 404
            
            # 检查是否是批次发布
            if '批次发布' not in publish_record.notes:
                return jsonify({
                    'success': False,
                    'message': '不是批次发布记录'
                }), 400
            
            # 获取批次ID
            batch_id = None
            for note_part in publish_record.notes.split('|'):
                if note_part.startswith('batch_id:'):
                    batch_id = note_part.split(':', 1)[1]
                    break
            
            if not batch_id:
                return jsonify({
                    'success': False,
                    'message': '无法获取批次ID'
                }), 400
            
            # 获取面值汇率详情
            denomination_details = session.query(DenominationPublishDetail).filter_by(
                publish_record_id=publish_record.id
            ).all()
            
            if not denomination_details:
                return jsonify({
                    'success': False,
                    'message': '批次中没有面值汇率数据'
                }), 404
            
            # 获取币种信息
            currency_ids = list(set([detail.currency_id for detail in denomination_details]))
            currencies = session.query(Currency).filter(Currency.id.in_(currency_ids)).all()
            currency_map = {currency.id: currency for currency in currencies}
            
            # 🔧 添加多语言币种名称映射
            currency_names_map = {
                'CNY': {'zh': '人民币', 'en': 'Chinese Yuan', 'th': 'หยวนจีน'},
                'USD': {'zh': '美元', 'en': 'US Dollar', 'th': 'ดอลลาร์สหรัฐ'},
                'EUR': {'zh': '欧元', 'en': 'Euro', 'th': 'ยูโร'},
                'JPY': {'zh': '日元', 'en': 'Japanese Yen', 'th': 'เยนญี่ปุ่น'},
                'GBP': {'zh': '英镑', 'en': 'British Pound', 'th': 'ปอนด์อังกฤษ'},
                'CHF': {'zh': '瑞士法郎', 'en': 'Swiss Franc', 'th': 'ฟรังก์สวิส'},
                'HKD': {'zh': '港币', 'en': 'Hong Kong Dollar', 'th': 'ดอลลาร์ฮ่องกง'},
                'CAD': {'zh': '加元', 'en': 'Canadian Dollar', 'th': 'ดอลลาร์แคนาดา'},
                'SGD': {'zh': '新加坡元', 'en': 'Singapore Dollar', 'th': 'ดอลลาร์สิงคโปร์'},
                'RUB': {'zh': '卢布', 'en': 'Russian Ruble', 'th': 'รูเบิลรัสเซีย'},
                'NZD': {'zh': '新西兰元', 'en': 'New Zealand Dollar', 'th': 'ดอลลาร์นิวซีแลนด์'},
                'AUD': {'zh': '澳元', 'en': 'Australian Dollar', 'th': 'ดอลลาร์ออสเตรเลีย'},
                'KRW': {'zh': '韩元', 'en': 'Korean Won', 'th': 'วอนเกาหลี'},
                'INR': {'zh': '印度卢比', 'en': 'Indian Rupee', 'th': 'รูปีอินเดีย'},
                'SEK': {'zh': '瑞典克朗', 'en': 'Swedish Krona', 'th': 'โครนสวีเดน'},
                'SAR': {'zh': '沙特里亚尔', 'en': 'Saudi Riyal', 'th': 'ริยาลซาอุดิอาระเบีย'},
                'NOK': {'zh': '挪威克朗', 'en': 'Norwegian Krone', 'th': 'โครนนอร์เวย์'},
                'DKK': {'zh': '丹麦克朗', 'en': 'Danish Krone', 'th': 'โครนเดนมาร์ก'},
                'THB': {'zh': '泰铢', 'en': 'Thai Baht', 'th': 'บาทไทย'}
            }
            
            # 构建面值汇率数据
            denomination_rates_data = []
            seen_denominations = set()  # 用于去重
            
            for detail in denomination_details:
                currency = currency_map.get(detail.currency_id)
                if currency:
                    # 创建唯一标识符：币种ID + 面值ID + 面值类型
                    unique_key = f"{detail.currency_id}_{detail.denomination_id}_{detail.denomination_type}"
                    
                    # 检查是否已经处理过这个面值
                    if unique_key not in seen_denominations:
                        seen_denominations.add(unique_key)
                        
                        # 构建基础数据
                        rate_data = {
                            'currency_id': detail.currency_id,
                            'currency_code': currency.currency_code,
                            'currency_name': currency.currency_name,
                            'flag_code': currency.flag_code,
                            'custom_flag_filename': currency.custom_flag_filename,
                            'denomination_id': detail.denomination_id,
                            'denomination_value': float(detail.denomination_value),
                            'denomination_type': detail.denomination_type,
                            'buy_rate': float(detail.buy_rate),
                            'sell_rate': float(detail.sell_rate)
                        }
                        
                        # 🔧 添加多语言名称
                        if currency.currency_code in currency_names_map:
                            rate_data['currency_names'] = currency_names_map[currency.currency_code]
                        else:
                            rate_data['currency_names'] = {
                                'zh': currency.currency_name,
                                'en': f"{currency.currency_code} ({currency.currency_name})",
                                'th': f"{currency.currency_code} ({currency.currency_name})"
                            }
                        
                        denomination_rates_data.append(rate_data)
                    else:
                        logger.warning(f"跳过重复的面值汇率: {unique_key}")
            
            # 计算币种数量
            unique_currencies = set()
            for detail in denomination_rates_data:
                unique_currencies.add(detail['currency_code'])
            
            # 从notes中解析配置信息
            items_per_page = 20
            refresh_interval = 3600
            if publish_record.notes:
                # 解析notes中的配置：批次发布|batch_id:xxx|theme:xxx|lang:xxx|page:xxx|refresh:xxx|notes:xxx
                notes_parts = publish_record.notes.split('|')
                for part in notes_parts:
                    if part.startswith('page:'):
                        try:
                            items_per_page = int(part.split(':')[1])
                        except (ValueError, IndexError):
                            pass
                    elif part.startswith('refresh:'):
                        try:
                            refresh_interval = int(part.split(':')[1])
                        except (ValueError, IndexError):
                            pass
            
            # 构建批次数据
            batch_data = {
                'batch_id': batch_id,
                'batch_main_token': batch_main_token,
                'branch': {
                    'id': publish_record.branch_id,
                    'name': '未知网点',  # 可以从Branch表获取
                    'code': 'Unknown'
                },
                'denomination_rates': denomination_rates_data,
                'publish_time': publish_record.publish_time.isoformat(),
                'published_at': publish_record.publish_time.isoformat(),
                'has_denominations': True,
                'theme': publish_record.publish_theme or 'light',
                'language': 'zh',
                'display_config': {
                    'items_per_page': items_per_page,
                    'refresh_interval': refresh_interval
                },
                'total_currencies': len(unique_currencies),
                'total_denominations': len(denomination_rates_data)
            }
            
            return jsonify({
                'success': True,
                'data': batch_data
            })
            
        finally:
            DatabaseService.close_session(session)
        
    except Exception as e:
        logger.error(f"获取批次显示数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取数据失败: {str(e)}'
        }), 500
