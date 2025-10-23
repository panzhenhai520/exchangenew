from flask import Blueprint, request, jsonify
from sqlalchemy import func, desc
from datetime import datetime, date, timedelta
from models.exchange_models import ExchangeTransaction, Currency, Branch, ExchangeRate, RatePublishRecord, RatePublishDetail, CurrencyBalance, BranchBalanceAlert, EODStatus, Operator
from models.denomination_models import CurrencyDenomination, DenominationRate
from models.exchange_models import DenominationPublishDetail
from services.db_service import DatabaseService
from services.auth_service import token_required, has_permission
import secrets
import hashlib
import json
import logging

logger = logging.getLogger(__name__)
import re
import os

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

# 存储发布的汇率数据（内存中，用于机顶盒访问）
published_rates_cache = {}

def update_show_html_branch_code(branch_code):
    """更新Show.html文件中的网点代码"""
    try:
        # 只更新实际存在的Show.html文件
        show_html_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'Show.html')
        
        # 检查文件是否存在
        if not os.path.exists(show_html_path):
            logger.info(f"[更新Show.html] 文件不存在: {show_html_path}")
            return False
            
        # 读取文件内容
        with open(show_html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"[更新Show.html] 当前网点代码: {branch_code}")
        logger.info(f"[更新Show.html] 文件路径: {show_html_path}")
        
        # 使用更精确的正则表达式匹配
        # 匹配 return "A005"; 这样的格式
        pattern = r'return\s+"([^"]+)";'
        
        # 检查是否找到匹配
        match = re.search(pattern, content)
        if match:
            current_code = match.group(1)
            logger.info(f"[更新Show.html] 找到当前网点代码: {current_code}")
            
            if current_code == branch_code:
                logger.info(f"[更新Show.html] 网点代码已经是 {branch_code}，无需更新")
                return True
            
            # 执行替换
            new_content = re.sub(pattern, f'return "{branch_code}";', content)
            
            # 写回文件
            with open(show_html_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            logger.info(f"[更新Show.html] 成功更新网点代码: {current_code} -> {branch_code}")
            return True
        else:
            logger.info(f"[更新Show.html] 未找到网点代码模式")
            return False
        
    except Exception as e:
        logger.info(f"[更新Show.html] 更新失败: {str(e)}")
        return False

@dashboard_bp.route('/overview', methods=['GET'])
@token_required
def get_dashboard_overview(current_user):
    """获取仪表板概览数据"""
    session = DatabaseService.get_session()
    try:
        # 获取当前汇率 - 只获取当前用户分支的汇率
        today = date.today()
        rates = session.query(ExchangeRate).join(Currency).filter(
            ExchangeRate.branch_id == current_user['branch_id'],
            ExchangeRate.rate_date == today
        ).all()
        
        rate_data = []
        for rate in rates:
            if rate is None or rate.currency is None:
                continue
                
            rate_data.append({
                'id': rate.id,
                'currency_id': rate.currency_id,
                'currency_code': rate.currency.currency_code,
                'currency_name': rate.currency.currency_name,
                'flag_code': rate.currency.flag_code,
                'buy_rate': float(rate.buy_rate),
                'sell_rate': float(rate.sell_rate),
                'rate_date': rate.rate_date.isoformat(),
                'updated_at': rate.updated_at.isoformat() if rate.updated_at else None
            })

        return jsonify({
            'success': True,
            'rates': rate_data
        })
    except Exception as e:
        logger.error(f"in dashboard overview: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@dashboard_bp.route('/publish-rates', methods=['POST'])
@token_required
@has_permission('rate_manage')
def publish_rates_for_display(*args, **kwargs):
    """发布汇率到机顶盒显示并保存发布记录"""
    current_user = kwargs.get('current_user') or args[0]
    data = request.json or {}
    
    session = DatabaseService.get_session()
    try:
        # 获取分支信息
        branch = session.query(Branch).filter_by(id=current_user['branch_id']).first()
        if not branch:
            return jsonify({'success': False, 'message': '找不到网点信息'}), 404
            
        # 获取汇率数据
        rates_data = data.get('rates', [])
        theme = data.get('theme', 'light')
        language = data.get('language', 'zh')
        
        # 获取显示配置参数
        display_config = data.get('display_config', {})
        items_per_page = display_config.get('items_per_page', 12)
        refresh_interval = display_config.get('refresh_interval', 3600)
        
        logger.info(f"[发布配置调试] 接收到的display_config: {display_config}")
        logger.info(f"[发布配置调试] items_per_page: {items_per_page} (类型: {type(items_per_page)})")
        logger.info(f"[发布配置调试] refresh_interval: {refresh_interval} (类型: {type(refresh_interval)})")
        
        # 验证配置参数
        if not isinstance(items_per_page, int) or items_per_page < 6 or items_per_page > 20:
            logger.info(f"[发布配置调试] items_per_page 验证失败，使用默认值12")
            items_per_page = 12
        if not isinstance(refresh_interval, int) or refresh_interval < 5 or refresh_interval > 86400:
            logger.info(f"[发布配置调试] refresh_interval 验证失败，使用默认值3600")
            refresh_interval = 3600
            
        logger.info(f"[发布配置调试] 最终使用的配置: items_per_page={items_per_page}, refresh_interval={refresh_interval}")
        
        if not rates_data:
            return jsonify({'success': False, 'message': '汇率数据不能为空'}), 400
        
        # 生成访问token
        token = secrets.token_urlsafe(32)
        
        # 准备存储的备注信息（包含配置参数）
        notes_data = {
            'user_notes': data.get('notes', ''),
            'display_config': {
                'items_per_page': items_per_page,
                'refresh_interval': refresh_interval
            }
        }
        notes_json = json.dumps(notes_data, ensure_ascii=False)
        
        logger.debug(f"发布汇率 - current_user: {current_user}")
        logger.debug(f"发布汇率 - current_user name: {current_user.get('name', 'None')}")
        
        # 创建发布记录
        publish_record = RatePublishRecord(
            branch_id=current_user['branch_id'],
            publish_date=date.today(),
            publish_time=datetime.now(),
            publisher_id=current_user['id'],
            publisher_name=current_user.get('name') or '系统管理员',  # 如果没有name字段才使用默认值
            total_currencies=len(rates_data),
            publish_theme=theme,
            access_token=token,
            notes=notes_json
        )
        session.add(publish_record)
        session.flush()  # 获取ID
        
        # 创建发布详情记录
        for index, rate in enumerate(rates_data):
            # 确保汇率值不为空，提供默认值
            buy_rate = rate.get('buy_rate')
            sell_rate = rate.get('sell_rate')
            
            if buy_rate is None or buy_rate == '':
                buy_rate = 0.0
            if sell_rate is None or sell_rate == '':
                sell_rate = 0.0
                
            try:
                buy_rate = float(buy_rate)
                sell_rate = float(sell_rate)
            except (ValueError, TypeError):
                buy_rate = 0.0
                sell_rate = 0.0
            
            detail = RatePublishDetail(
                publish_record_id=publish_record.id,
                currency_id=rate['currency_id'],
                currency_code=rate['currency_code'],
                currency_name=rate['currency_name'],
                buy_rate=buy_rate,
                sell_rate=sell_rate,
                sort_order=index
            )
            session.add(detail)
        
        # 添加多语言币种名称
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
            'ZAR': {'zh': '南非兰特', 'en': 'South African Rand', 'th': 'แรนด์แอฟริกาใต้'},
            'BND': {'zh': '文莱元', 'en': 'Brunei Dollar', 'th': 'ดอลลาร์บรูไน'},
            'BHD': {'zh': '巴林第纳尔', 'en': 'Bahraini Dinar', 'th': 'ดีนาร์บาห์เรน'},
            'THB': {'zh': '泰铢', 'en': 'Thai Baht', 'th': 'บาทไทย'},
            'MYR': {'zh': '马来西亚林吉特', 'en': 'Malaysian Ringgit', 'th': 'ริงกิตมาเลเซีย'},
            'PHP': {'zh': '菲律宾比索', 'en': 'Philippine Peso', 'th': 'เปโซฟิลิปปินส์'},
            'VND': {'zh': '越南盾', 'en': 'Vietnamese Dong', 'th': 'ด่องเวียดนาม'},
            'IDR': {'zh': '印尼盾', 'en': 'Indonesian Rupiah', 'th': 'รูเปียห์อินโดนีเซีย'}
        }
        
        # 为每个汇率数据添加多语言名称
        enhanced_rates_data = []
        for rate in rates_data:
            enhanced_rate = rate.copy()
            currency_code = rate['currency_code']
            
            # 🌟 添加自定义图标字段获取逻辑
            currency_id = rate.get('currency_id')
            if currency_id:
                # 从数据库获取币种的完整信息，包括自定义图标
                currency = session.query(Currency).filter_by(id=currency_id).first()
                if currency:
                    enhanced_rate['custom_flag_filename'] = currency.custom_flag_filename
                    # 确保flag_code字段存在
                    if not enhanced_rate.get('flag_code'):
                        enhanced_rate['flag_code'] = currency.flag_code or currency_code.lower()
                else:
                    enhanced_rate['custom_flag_filename'] = None
                    if not enhanced_rate.get('flag_code'):
                        enhanced_rate['flag_code'] = currency_code.lower()
            else:
                enhanced_rate['custom_flag_filename'] = None
                if not enhanced_rate.get('flag_code'):
                    enhanced_rate['flag_code'] = currency_code.lower()
            
            # 如果在预设映射中找到，使用预设的多语言名称
            if currency_code in currency_names_map:
                enhanced_rate['currency_names'] = currency_names_map[currency_code]
            else:
                # 对于新币种，生成基础的多语言支持
                enhanced_rate['currency_names'] = {
                    'zh': rate['currency_name'],  # 使用数据库中的中文名称
                    'en': f"{currency_code} ({rate['currency_name']})",  # 英文显示币种代码+中文名
                    'th': f"{currency_code} ({rate['currency_name']})"   # 泰文显示币种代码+中文名
                }
            enhanced_rates_data.append(enhanced_rate)
        
        # 获取网点本币信息
        base_currency_code = None
        if branch.base_currency_id:
            base_currency = session.query(Currency).filter_by(id=branch.base_currency_id).first()
            if base_currency:
                base_currency_code = base_currency.currency_code
        
        # 准备发布的数据
        published_data = {
            'branch': {
                'code': branch.branch_code,
                'name': branch.branch_name,
                'base_currency': base_currency_code
            },
            'rates': enhanced_rates_data,
            'theme': theme,
            'language': language,
            'display_config': {
                'items_per_page': items_per_page,
                'refresh_interval': refresh_interval
            },
            'published_at': datetime.now().isoformat(),
            'published_by': current_user.get('name') or '系统管理员',  # 如果没有name字段才使用默认值
            'publish_record_id': publish_record.id
        }
        
        # 清除该分支的旧缓存（保留其他分支的缓存）
        branch_tokens_to_remove = []
        for cached_token, cached_data in published_rates_cache.items():
            if cached_data.get('branch', {}).get('code') == branch.branch_code:
                branch_tokens_to_remove.append(cached_token)
        
        # 删除旧的缓存
        for old_token in branch_tokens_to_remove:
            del published_rates_cache[old_token]
            logger.info(f"[缓存清理] 删除旧缓存: {old_token}")
        
        # 存储到缓存中
        published_rates_cache[token] = published_data
        logger.info(f"[缓存更新] 新缓存已存储: {token}, 货币数量: {len(rates_data)}")
        
        # 提交数据库事务
        DatabaseService.commit_session(session)
        
        # 生成访问URL - 从环境变量读取服务器地址
        import os
        current_ip = os.getenv('CURRENT_IP', 'localhost')
        frontend_port = os.getenv('FRONTEND_PORT', '8080')
        base_url = f'http://{current_ip}:{frontend_port}'
        logger.info(f"[发布汇率URL] 使用base_url: {base_url}")
        access_url = f"{base_url}/api/dashboard/display-rates/{token}?theme={theme}&lang={language}"
        
        # 更新show.html文件中的网点代码
        logger.info(f"[发布汇率] 当前用户branch_id: {current_user['branch_id']}")
        logger.info(f"[发布汇率] 查询到的branch.branch_code: {branch.branch_code}")
        update_success = update_show_html_branch_code(branch.branch_code)
        if update_success:
            logger.info(f"[发布汇率] 已自动更新show.html中的网点代码为: {branch.branch_code}")
        else:
            logger.info(f"[发布汇率] 更新show.html失败，但发布成功")
        
        return jsonify({
            'success': True,
            'message': '汇率已成功发布',
            'redirect_url': access_url,
            'token': token,
            'theme': theme,
            'publish_record_id': publish_record.id
        })
        
    except Exception as e:
        DatabaseService.rollback_session(session)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@dashboard_bp.route('/publish-records', methods=['GET'])
@token_required
def get_publish_records(current_user):
    """获取发布记录列表"""
    session = DatabaseService.get_session()
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # 构建查询
        query = session.query(RatePublishRecord).filter(
            RatePublishRecord.branch_id == current_user['branch_id']
        )
        
        # 日期过滤
        if date_from:
            query = query.filter(RatePublishRecord.publish_date >= date_from)
        if date_to:
            query = query.filter(RatePublishRecord.publish_date <= date_to)
        
        # 排序和分页
        query = query.order_by(desc(RatePublishRecord.publish_time))
        total = query.count()
        records = query.offset((page - 1) * per_page).limit(per_page).all()
        
        # 转换为字典
        result = []
        for record in records:
            # 处理备注信息，如果是JSON格式则解析
            notes_text = record.notes
            if notes_text:
                try:
                    import json
                    notes_data = json.loads(notes_text)
                    if isinstance(notes_data, dict) and 'user_notes' in notes_data:
                        notes_text = notes_data['user_notes']
                except:
                    # 如果解析失败，保持原始文本
                    pass
            
            result.append({
                'id': record.id,
                'publish_date': record.publish_date.isoformat(),
                'publish_time': record.publish_time.isoformat(),
                'publisher_name': record.publisher_name,
                'total_currencies': record.total_currencies,
                'publish_theme': record.publish_theme,
                'access_token': record.access_token,
                'notes': notes_text
            })
        
        return jsonify({
            'success': True,
            'records': result,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@dashboard_bp.route('/publish-records/<int:record_id>', methods=['GET'])
@token_required
def get_publish_record_detail(current_user, record_id):
    """获取发布记录详情"""
    session = DatabaseService.get_session()
    try:
        # 获取发布记录
        record = session.query(RatePublishRecord).filter(
            RatePublishRecord.id == record_id,
            RatePublishRecord.branch_id == current_user['branch_id']
        ).first()
        
        if not record:
            return jsonify({'success': False, 'message': '发布记录不存在'}), 404
        
        # 获取详情数据
        details = session.query(RatePublishDetail).filter(
            RatePublishDetail.publish_record_id == record_id
        ).order_by(RatePublishDetail.sort_order).all()
        
        # 获取币种的国旗信息
        detail_list = []
        for detail in details:
            currency = session.query(Currency).filter_by(id=detail.currency_id).first()
            detail_list.append({
                'currency_id': detail.currency_id,
                'currency_code': detail.currency_code,
                'currency_name': detail.currency_name,
                'flag_code': currency.flag_code if currency else '',
                'custom_flag_filename': currency.custom_flag_filename if currency else None,
                'buy_rate': float(detail.buy_rate),
                'sell_rate': float(detail.sell_rate),
                'sort_order': detail.sort_order
            })
        
        # 处理备注信息，如果是JSON格式则解析
        notes_text = record.notes
        if notes_text:
            try:
                import json
                notes_data = json.loads(notes_text)
                if isinstance(notes_data, dict) and 'user_notes' in notes_data:
                    notes_text = notes_data['user_notes']
            except:
                # 如果解析失败，保持原始文本
                pass
        
        result = {
            'id': record.id,
            'publish_date': record.publish_date.isoformat(),
            'publish_time': record.publish_time.isoformat(),
            'publisher_name': record.publisher_name,
            'total_currencies': record.total_currencies,
            'publish_theme': record.publish_theme,
            'notes': notes_text,
            'details': detail_list
        }
        
        return jsonify({
            'success': True,
            'record': result
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@dashboard_bp.route('/settop-box/auto-url/<branch_code>', methods=['GET'])
def get_settop_box_url(branch_code):
    """机顶盒获取所有汇率展示URL"""
    try:
        # 🔧 方案1：优先从数据库查找最新的发布记录，确保数据一致性
        logger.info(f"[机顶盒URL] 优先从数据库查找分支 {branch_code} 的最新发布记录")
        
        session = DatabaseService.get_session()
        try:
            # 🔧 方案1：优先查找批次发布记录
            batch_records = session.query(RatePublishRecord).join(
                Branch, RatePublishRecord.branch_id == Branch.id
            ).filter(
                Branch.branch_code == branch_code,
                RatePublishRecord.notes.like('%批次发布%')
            ).order_by(desc(RatePublishRecord.publish_time)).all()
            
            if batch_records:
                # 优先使用批次发布记录
                latest_batch = batch_records[0]
                batch_token = latest_batch.access_token
                
                logger.info(f"[机顶盒URL] 找到批次发布记录: {batch_token[:8]}...")
                
                # 构建批次URL
                theme = latest_batch.publish_theme or 'light'
                language = 'zh'
                
                redirect_url = f"/api/dashboard/display-batch-rates/{batch_token}?theme={theme}&lang={language}"
                
                return jsonify({
                    'success': True,
                    'data': {
                        'redirect_url': redirect_url,
                        'batch_id': batch_token,
                        'publish_time': latest_batch.publish_time.isoformat(),
                        'currency_count': latest_batch.total_currencies
                    }
                })
            
            # 如果没有批次记录，查找普通面值汇率发布记录
            denomination_records = session.query(RatePublishRecord).join(
                Branch, RatePublishRecord.branch_id == Branch.id
            ).filter(
                Branch.branch_code == branch_code,
                RatePublishRecord.notes.like('%面值汇率发布%')
            ).order_by(desc(RatePublishRecord.publish_time)).all()
            
            if denomination_records:
                # 使用最新的面值汇率发布记录
                latest_record = denomination_records[0]
                record_token = latest_record.access_token
                
                logger.info(f"[机顶盒URL] 找到面值汇率发布记录: {record_token[:8]}...")
                
                # 构建普通URL
                theme = latest_record.publish_theme or 'light'
                language = 'zh'
                
                redirect_url = f"/api/dashboard/display-rates/{record_token}?theme={theme}&lang={language}"
                
                return jsonify({
                    'success': True,
                    'data': {
                        'redirect_url': redirect_url,
                        'token': record_token,
                        'publish_time': latest_record.publish_time.isoformat(),
                        'currency_count': latest_record.total_currencies
                    }
                })
            
            # 如果都没有，查找标准汇率发布记录
            standard_records = session.query(RatePublishRecord).join(
                Branch, RatePublishRecord.branch_id == Branch.id
            ).filter(
                Branch.branch_code == branch_code
            ).order_by(desc(RatePublishRecord.publish_time)).all()
            
            if standard_records:
                latest_record = standard_records[0]
                record_token = latest_record.access_token
                
                logger.info(f"[机顶盒URL] 找到标准汇率发布记录: {record_token[:8]}...")
                
                theme = latest_record.publish_theme or 'light'
                language = 'zh'
                
                redirect_url = f"/api/dashboard/display-rates/{record_token}?theme={theme}&lang={language}"
                
                return jsonify({
                    'success': True,
                    'data': {
                        'redirect_url': redirect_url,
                        'token': record_token,
                        'publish_time': latest_record.publish_time.isoformat(),
                        'currency_count': latest_record.total_currencies
                    }
                })
            
            logger.info(f"[机顶盒URL] 分支 {branch_code} 没有找到任何发布记录")
            return jsonify({
                'success': False, 
                'message': f'没有找到网点 {branch_code} 的汇率发布记录'
            }), 404
        finally:
            DatabaseService.close_session(session)
        
    except Exception as e:
        logger.error(f"获取机顶盒URL失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取机顶盒URL失败: {str(e)}'}), 500

@dashboard_bp.route('/display-rates/<token>', methods=['GET'])
def get_display_rates(token):
    """机顶盒获取汇率数据"""
    # 检查URL参数是否要求强制刷新
    force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
    
    # 首先检查内存缓存
    if token in published_rates_cache and not force_refresh:
        data = published_rates_cache[token]
        
        # 检查是否是面值汇率数据
        if data.get('has_denominations', False):
            # 面值汇率数据，直接返回
            return jsonify({
                'success': True,
                'data': data
            })
        else:
            # 标准汇率数据，合并同分支的所有汇率
            branch_code = data['branch']['code']
            all_rates = []
            
            # 从缓存中获取该分支的所有发布记录
            for cache_token, cache_data in published_rates_cache.items():
                if cache_data['branch']['code'] == branch_code and not cache_data.get('has_denominations', False):
                    all_rates.extend(cache_data.get('rates', []))
            
            # 去重，保留最新的汇率数据
            unique_rates = {}
            for rate in all_rates:
                currency_code = rate['currency_code']
                if currency_code not in unique_rates:
                    unique_rates[currency_code] = rate
            
            # 更新数据中的汇率列表
            data['rates'] = list(unique_rates.values())
            data['total_currencies'] = len(data['rates'])
            
            return jsonify({
                'success': True,
                'data': data
            })
    
    # 如果内存缓存中没有，从数据库恢复
    session = DatabaseService.get_session()
    try:
        # 查找发布记录
        publish_record = session.query(RatePublishRecord).filter_by(
            access_token=token
        ).first()
        
        if not publish_record:
            return jsonify({
                'success': False, 
                'message': '无效的访问令牌或数据已过期'
            }), 404
        
        # 检查是否是面值汇率发布记录
        if publish_record.notes and '面值汇率发布' in publish_record.notes:
            # 处理面值汇率数据
            from models.denomination_models import CurrencyDenomination
            
            # 获取面值汇率发布详情
            denomination_details = session.query(DenominationPublishDetail).filter_by(
                publish_record_id=publish_record.id
            ).all()
            
            if not denomination_details:
                return jsonify({
                    'success': False, 
                    'message': '面值汇率数据不存在'
                }), 404
            
            # 获取网点信息
            branch = session.query(Branch).filter_by(id=publish_record.branch_id).first()
            if not branch:
                return jsonify({
                    'success': False, 
                    'message': '网点不存在'
                }), 404
            
            # 按币种分组获取面值汇率数据
            currency_groups = {}
            for detail in denomination_details:
                currency_id = detail.currency_id
                if currency_id not in currency_groups:
                    currency_groups[currency_id] = []
                currency_groups[currency_id].append(detail)
            
            # 获取所有涉及的币种信息
            currency_ids = list(currency_groups.keys())
            currencies = session.query(Currency).filter(Currency.id.in_(currency_ids)).all()
            currency_map = {c.id: c for c in currencies}
            
            # 构建面值汇率数据，包含币种信息，同时去重
            denomination_rates_data = []
            seen_denominations = set()  # 用于去重的集合
            
            for detail in denomination_details:
                currency = currency_map.get(detail.currency_id)
                if currency:
                    # 创建唯一标识符：币种ID + 面值ID + 面值类型
                    unique_key = f"{detail.currency_id}_{detail.denomination_id}_{detail.denomination_type}"
                    
                    # 检查是否已经处理过这个面值
                    if unique_key not in seen_denominations:
                        seen_denominations.add(unique_key)
                        denomination_rates_data.append({
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
                        })
                    else:
                        logger.warning(f"跳过重复的面值汇率: {unique_key}")
            
            # 解析显示配置
            theme = 'light'
            language = 'zh'
            items_per_page = 12
            refresh_interval = 3600
            
            if publish_record.notes and '|' in publish_record.notes:
                try:
                    config_parts = publish_record.notes.split('|')
                    for part in config_parts[1:]:  # 跳过第一部分"面值汇率发布"
                        if ':' in part:
                            key, value = part.split(':', 1)
                            if key == 'theme':
                                theme = value
                            elif key == 'lang':
                                language = value
                            elif key == 'page':
                                items_per_page = int(value)
                            elif key == 'refresh':
                                refresh_interval = int(value)
                except (ValueError, IndexError):
                    pass  # 使用默认值
            
            # 构建返回数据
            data = {
                'branch': {
                    'id': branch.id,
                    'name': branch.branch_name,
                    'code': branch.branch_code
                },
                'denomination_rates': denomination_rates_data,
                'publish_time': publish_record.publish_time.isoformat(),
                'published_at': publish_record.publish_time.isoformat(),  # 添加published_at字段
                'has_denominations': True,
                'theme': theme,
                'language': language,
                'display_config': {
                    'items_per_page': items_per_page,
                    'refresh_interval': refresh_interval
                }
            }
            
            # 更新缓存
            published_rates_cache[token] = data
            
            return jsonify({
                'success': True,
                'data': data
            })
        
        # 获取发布详情
        publish_details = session.query(RatePublishDetail).filter_by(
            publish_record_id=publish_record.id
        ).order_by(RatePublishDetail.sort_order).all()
        
        # 获取网点信息
        branch = session.query(Branch).filter_by(id=publish_record.branch_id).first()
        base_currency_code = None
        if branch and branch.base_currency_id:
            base_currency = session.query(Currency).filter_by(id=branch.base_currency_id).first()
            if base_currency:
                base_currency_code = base_currency.currency_code
        
        # 多语言币种名称映射
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
            'ZAR': {'zh': '南非兰特', 'en': 'South African Rand', 'th': 'แรนด์แอฟริกาใต้'},
            'BND': {'zh': '文莱元', 'en': 'Brunei Dollar', 'th': 'ดอลลาร์บรูไน'},
            'BHD': {'zh': '巴林第纳尔', 'en': 'Bahraini Dinar', 'th': 'ดีนาร์บาห์เรน'},
            'THB': {'zh': '泰铢', 'en': 'Thai Baht', 'th': 'บาทไทย'},
            'MYR': {'zh': '马来西亚林吉特', 'en': 'Malaysian Ringgit', 'th': 'ริงกิตมาเลเซีย'},
            'PHP': {'zh': '菲律宾比索', 'en': 'Philippine Peso', 'th': 'เปโซฟิลิปปินส์'},
            'VND': {'zh': '越南盾', 'en': 'Vietnamese Dong', 'th': 'ด่องเวียดนาม'},
            'IDR': {'zh': '印尼盾', 'en': 'Indonesian Rupiah', 'th': 'รูเปียห์อินโดนีเซีย'}
        }
        
        # 重建汇率数据
        rates_data = []
        for detail in publish_details:
            # 从数据库获取正确的 flag_code 和 custom_flag_filename
            currency = session.query(Currency).filter_by(id=detail.currency_id).first()
            flag_code = currency.flag_code if currency and currency.flag_code else detail.currency_code.lower()
            custom_flag_filename = currency.custom_flag_filename if currency else None
            
            rate_data = {
                'currency_id': detail.currency_id,
                'currency_code': detail.currency_code,
                'currency_name': detail.currency_name,
                'buy_rate': float(detail.buy_rate),
                'sell_rate': float(detail.sell_rate),
                'flag_code': flag_code,
                'custom_flag_filename': custom_flag_filename  # 添加自定义图标字段
            }
            
            # 添加多语言名称
            if detail.currency_code in currency_names_map:
                rate_data['currency_names'] = currency_names_map[detail.currency_code]
            else:
                rate_data['currency_names'] = {
                    'zh': detail.currency_name,
                    'en': f"{detail.currency_code} ({detail.currency_name})",
                    'th': f"{detail.currency_code} ({detail.currency_name})"
                }
            
            rates_data.append(rate_data)
        
        # 解析配置参数（从notes字段）
        display_config = {'items_per_page': 12, 'refresh_interval': 3600}  # 默认配置
        if publish_record.notes:
            try:
                logger.info(f"[数据恢复调试] 从数据库notes字段解析: {publish_record.notes}")
                notes_data = json.loads(publish_record.notes)
                logger.info(f"[数据恢复调试] 解析后的notes_data: {notes_data}")
                if isinstance(notes_data, dict) and 'display_config' in notes_data:
                    stored_config = notes_data['display_config']
                    logger.info(f"[数据恢复调试] 存储的配置: {stored_config}")
                    if isinstance(stored_config, dict):
                        display_config = {
                            'items_per_page': stored_config.get('items_per_page', 12),
                            'refresh_interval': stored_config.get('refresh_interval', 3600)
                        }
                        logger.info(f"[数据恢复调试] 恢复的配置: {display_config}")
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                # 如果解析失败，使用默认配置
                logger.info(f"[数据恢复调试] 配置解析失败: {e}, 使用默认配置")
                pass
        
        # 获取该分支的所有发布记录，合并汇率数据
        all_rates_data = rates_data.copy()  # 先包含当前记录的汇率
        
        # 查找该分支的其他发布记录
        other_records = session.query(RatePublishRecord).filter(
            RatePublishRecord.branch_id == publish_record.branch_id,
            RatePublishRecord.id != publish_record.id
        ).order_by(desc(RatePublishRecord.publish_time)).all()
        
        # 从其他发布记录中获取汇率数据
        for other_record in other_records:
            other_details = session.query(RatePublishDetail).filter_by(
                publish_record_id=other_record.id
            ).order_by(RatePublishDetail.sort_order).all()
            
            for detail in other_details:
                # 检查是否已经存在该币种的汇率
                existing_rate = next((rate for rate in all_rates_data if rate['currency_code'] == detail.currency_code), None)
                if not existing_rate:
                    # 如果不存在，则添加
                    currency = session.query(Currency).filter_by(id=detail.currency_id).first()
                    flag_code = currency.flag_code if currency and currency.flag_code else detail.currency_code.lower()
                    
                    rate_data = {
                        'currency_id': detail.currency_id,
                        'currency_code': detail.currency_code,
                        'currency_name': detail.currency_name,
                        'buy_rate': float(detail.buy_rate),
                        'sell_rate': float(detail.sell_rate),
                        'flag_code': flag_code
                    }
                    
                    # 添加多语言名称
                    if detail.currency_code in currency_names_map:
                        rate_data['currency_names'] = currency_names_map[detail.currency_code]
                    else:
                        rate_data['currency_names'] = {
                            'zh': detail.currency_name,
                            'en': f"{detail.currency_code} ({detail.currency_name})",
                            'th': f"{detail.currency_code} ({detail.currency_name})"
                        }
                    
                    all_rates_data.append(rate_data)
        
        # 重建完整数据
        data = {
            'branch': {
                'code': branch.branch_code if branch else 'A005',
                'name': branch.branch_name if branch else '未知网点',
                'base_currency': base_currency_code
            },
            'rates': all_rates_data,
            'theme': publish_record.publish_theme or 'light',
            'language': 'zh',  # 默认中文
            'display_config': display_config,
            'published_at': publish_record.publish_time.isoformat(),
            'published_by': publish_record.publisher_name,
            'publish_record_id': publish_record.id
        }
        
        # 重新加载到内存缓存中
        published_rates_cache[token] = data
        
        return jsonify({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        logger.error(f"in get_display_rates: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'获取汇率数据失败: {str(e)}'
        }), 500
    finally:
        DatabaseService.close_session(session)

@dashboard_bp.route('/transaction_stats', methods=['GET'])
@token_required
def get_transaction_stats(current_user):
    """获取交易统计数据"""
    session = DatabaseService.get_session()
    try:
        # 获取今日交易统计
        today = date.today()
        stats = session.query(
            func.count().label('total_count'),
            func.sum(ExchangeTransaction.buy_amount).label('total_buy_amount'),
            func.sum(ExchangeTransaction.sell_amount).label('total_sell_amount')
        ).filter(
            func.date(ExchangeTransaction.transaction_date) == today
        ).first()

        return jsonify({
            'success': True,
            'stats': {
                'total_count': stats.total_count or 0,
                'total_buy_amount': float(stats.total_buy_amount or 0),
                'total_sell_amount': float(stats.total_sell_amount or 0)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@dashboard_bp.route('/recent_transactions', methods=['GET'])
@token_required
def get_recent_transactions(current_user):
    """获取最近交易记录"""
    limit = request.args.get('limit', 10, type=int)
    if limit > 50:  # 限制最大返回数量
        limit = 50

    session = DatabaseService.get_session()
    try:
        print("Fetching recent transactions with limit:", limit)
        
        # 先检查是否有交易记录
        count = session.query(ExchangeTransaction).count()
        logger.info(f"Total transactions in database: {count}")
        
        # 检查第一条记录的内容
        first_transaction = session.query(ExchangeTransaction).first()
        if first_transaction:
            print("First transaction details:")
            logger.info(f"  ID: {first_transaction.id}")
            logger.info(f"  Transaction No: {first_transaction.transaction_no}")
            logger.info(f"  Type: {first_transaction.type}")
            logger.info(f"  Amount: {first_transaction.amount}")
            logger.info(f"  Rate: {first_transaction.rate}")
            logger.info(f"  Currency ID: {first_transaction.currency_id}")
        
        # Query with proper joins for both buy and sell currencies
        transactions = session.query(
            ExchangeTransaction,
            Currency.currency_code.label('currency_code'),
            Currency.currency_name.label('currency_name'),
            Currency.flag_code.label('flag_code'),
            Branch.base_currency_id
        ).join(
            Currency, ExchangeTransaction.currency_id == Currency.id
        ).join(
            Branch, ExchangeTransaction.branch_id == Branch.id
        ).order_by(
            desc(ExchangeTransaction.created_at)
        ).limit(limit).all()

        logger.info(f"Found {len(transactions)} transactions after join")
        
        # 获取基础货币信息的缓存
        base_currency_cache = {}
        result = []
        for transaction, currency_code, currency_name, flag_code, base_currency_id in transactions:
            # 获取网点本币代码
            if base_currency_id not in base_currency_cache:
                base_currency = session.query(Currency).filter_by(id=base_currency_id).first()
                base_currency_cache[base_currency_id] = base_currency.currency_code if base_currency else 'USD'
            base_currency_code = base_currency_cache[base_currency_id]
            
            transaction_data = {
                'id': transaction.id,
                'transaction_no': transaction.transaction_no,
                'type': transaction.type,
                'buy_currency_code': currency_code if transaction.type == 'buy' else base_currency_code,
                'sell_currency_code': base_currency_code if transaction.type == 'buy' else currency_code,
                'amount': float(transaction.amount),
                'cny_amount': float(transaction.amount * transaction.rate),
                'customer_name': transaction.customer_name,
                'transaction_date': transaction.transaction_date.strftime('%Y-%m-%d') if transaction.transaction_date else transaction.created_at.strftime('%Y-%m-%d')
            }
            logger.info(f"Processing transaction: {transaction_data}")
            result.append(transaction_data)

        return jsonify({
            'success': True,
            'transactions': result
        })

    except Exception as e:
        print("Error in get_recent_transactions:", str(e))
        import traceback
        print("Full traceback:", traceback.format_exc())
        DatabaseService.rollback_session(session)
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
    finally:
        DatabaseService.close_session(session)

@dashboard_bp.route('/transaction_trends', methods=['GET'])
@token_required
def get_transaction_trends(current_user):
    """获取交易趋势数据"""
    days = request.args.get('days', 7, type=int)
    if days > 30:  # 限制最大天数
        days = 30

    session = DatabaseService.get_session()
    try:
        # 获取最近N天的交易趋势
        trends = session.query(
            func.date(ExchangeTransaction.transaction_date).label('date'),
            func.count().label('count'),
            func.sum(ExchangeTransaction.buy_amount).label('buy_amount'),
            func.sum(ExchangeTransaction.sell_amount).label('sell_amount')
        ).group_by(
            func.date(ExchangeTransaction.transaction_date)
        ).order_by(
            desc('date')
        ).limit(days).all()

        result = []
        for trend in trends:
            result.append({
                'date': trend.date.isoformat(),
                'count': trend.count,
                'buy_amount': float(trend.buy_amount or 0),
                'sell_amount': float(trend.sell_amount or 0)
            })

        return jsonify({
            'success': True,
            'trends': result
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@dashboard_bp.route('/business-stats', methods=['GET'])
@token_required
def get_business_stats(current_user):
    """获取业务统计数据"""
    session = DatabaseService.get_session()
    
    try:
        from datetime import datetime, date, timedelta
        from sqlalchemy import func, and_, or_
        
        # 计算7天前的日期
        seven_days_ago = date.today() - timedelta(days=7)
        branch_id = current_user['branch_id']
        
        # 1. 7天交易统计（按天分组）
        transaction_stats = session.query(
            func.DATE(ExchangeTransaction.transaction_date).label('date'),
            func.count(ExchangeTransaction.id).label('count')
        ).filter(
            and_(
                ExchangeTransaction.branch_id == branch_id,
                ExchangeTransaction.type.in_(['buy', 'sell']),
                ExchangeTransaction.transaction_date >= seven_days_ago
            )
        ).group_by(func.DATE(ExchangeTransaction.transaction_date)).all()
        
        # 2. 7天冲正统计（按天分组）
        reversal_stats = session.query(
            func.DATE(ExchangeTransaction.transaction_date).label('date'),
            func.count(ExchangeTransaction.id).label('count')
        ).filter(
            and_(
                ExchangeTransaction.branch_id == branch_id,
                ExchangeTransaction.type == 'reversal',
                ExchangeTransaction.transaction_date >= seven_days_ago
            )
        ).group_by(func.DATE(ExchangeTransaction.transaction_date)).all()
        
        # 3. 汇率发布状态
        latest_publish = session.query(RatePublishRecord).filter_by(
            branch_id=branch_id
        ).order_by(RatePublishRecord.publish_time.desc()).first()
        
        # 4. 买入最多外币排行（7天）
        buy_ranking = session.query(
            Currency.currency_code,
            Currency.currency_name,
            func.count(ExchangeTransaction.id).label('count')
        ).join(
            ExchangeTransaction, Currency.id == ExchangeTransaction.currency_id
        ).filter(
            and_(
                ExchangeTransaction.branch_id == branch_id,
                ExchangeTransaction.type == 'buy',
                ExchangeTransaction.transaction_date >= seven_days_ago
            )
        ).group_by(Currency.id).order_by(func.count(ExchangeTransaction.id).desc()).limit(3).all()
        
        # 5. 卖出最多外币排行（7天）
        sell_ranking = session.query(
            Currency.currency_code,
            Currency.currency_name,
            func.count(ExchangeTransaction.id).label('count')
        ).join(
            ExchangeTransaction, Currency.id == ExchangeTransaction.currency_id
        ).filter(
            and_(
                ExchangeTransaction.branch_id == branch_id,
                ExchangeTransaction.type == 'sell',
                ExchangeTransaction.transaction_date >= seven_days_ago
            )
        ).group_by(Currency.id).order_by(func.count(ExchangeTransaction.id).desc()).limit(3).all()
        
        # 6. 余额预警统计 - 分步查询避免复杂JOIN
        try:
            low_alerts = 0
            high_alerts = 0
            alert_details = []  # 存储具体的预警详情
            
            # 获取当前分支的所有活跃预警设置
            branch_alerts = session.query(BranchBalanceAlert).filter(
                and_(
                    BranchBalanceAlert.branch_id == branch_id,
                    BranchBalanceAlert.is_active == True
                )
            ).all()
            
            # 对每个预警设置，检查对应的余额
            for alert in branch_alerts:
                balance_record = session.query(CurrencyBalance).filter(
                    and_(
                        CurrencyBalance.branch_id == branch_id,
                        CurrencyBalance.currency_id == alert.currency_id
                    )
                ).first()
                
                if balance_record:
                    # 获取币种信息
                    currency = session.query(Currency).filter_by(id=alert.currency_id).first()
                    
                    current_balance = float(balance_record.balance)
                    min_threshold = float(alert.min_threshold)
                    max_threshold = float(alert.max_threshold)
                    
                    # 检查是否低于下限
                    if current_balance < min_threshold:
                        low_alerts += 1
                        alert_details.append({
                            'currency_code': currency.currency_code if currency else '',
                            'currency_name': currency.currency_name if currency else '',
                            'type': 'low',
                            'current_balance': current_balance,
                            'threshold': min_threshold
                        })
                    
                    # 检查是否超过上限
                    if current_balance > max_threshold:
                        high_alerts += 1
                        alert_details.append({
                            'currency_code': currency.currency_code if currency else '',
                            'currency_name': currency.currency_name if currency else '',
                            'type': 'high', 
                            'current_balance': current_balance,
                            'threshold': max_threshold
                        })
            
            balance_alerts_result = {
                'low_alerts': low_alerts,
                'high_alerts': high_alerts,
                'alert_details': alert_details  # 新增详细信息
            }
            
        except Exception as e:
            logger.info(f"余额预警查询错误: {e}")
            balance_alerts_result = {'low_alerts': 0, 'high_alerts': 0, 'alert_details': []}
        
        # 7. 最近日结时间 - 增加详细信息
        latest_eod = session.query(EODStatus).filter(
            and_(
                EODStatus.branch_id == branch_id,
                EODStatus.status == 'completed'
            )
        ).order_by(EODStatus.completed_at.desc()).first()
        
        # 获取日结操作人信息
        eod_operator_name = None
        if latest_eod and latest_eod.completed_by:
            operator = session.query(Operator).filter_by(id=latest_eod.completed_by).first()
            eod_operator_name = operator.name if operator else '未知操作员'
        
        # 格式化数据
        result = {
            'transaction_trend': [
                {
                    'date': str(stat.date),
                    'count': stat.count
                } for stat in transaction_stats
            ],
            'reversal_trend': [
                {
                    'date': str(stat.date), 
                    'count': stat.count
                } for stat in reversal_stats
            ],
            'rate_publish_status': {
                'last_publish_time': latest_publish.publish_time.isoformat() if latest_publish else None,
                'publisher_name': latest_publish.publisher_name if latest_publish else None,
                'total_currencies': latest_publish.total_currencies if latest_publish else 0
            },
            'buy_ranking': [
                {
                    'currency_code': item.currency_code,
                    'currency_name': item.currency_name,
                    'count': item.count
                } for item in buy_ranking
            ],
            'sell_ranking': [
                {
                    'currency_code': item.currency_code,
                    'currency_name': item.currency_name,
                    'count': item.count
                } for item in sell_ranking
            ],
            'balance_alerts': balance_alerts_result,
            'eod_status': {
                'last_eod_time': latest_eod.completed_at.isoformat() if latest_eod else None,
                'last_eod_date': str(latest_eod.date) if latest_eod else None,
                'eod_operator_name': eod_operator_name
            },
            'cache_time': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        logger.info(f"获取业务统计失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取业务统计失败: {str(e)}'
        }), 500
    finally:
        DatabaseService.close_session(session)

@dashboard_bp.route('/clear-publish-cache', methods=['POST'])
@token_required
@has_permission('rate_manage')
def clear_publish_cache(*args, **kwargs):
    """清除发布缓存（用于调试）"""
    current_user = kwargs.get('current_user') or args[0]
    global published_rates_cache
    session = None
    
    try:
        logger.info(f"[清除缓存] 开始清除缓存，用户: {current_user.get('name', 'unknown')}")
        logger.info(f"[清除缓存] 用户分支ID: {current_user.get('branch_id')}")
        
        # 获取分支信息
        session = DatabaseService.get_session()
        branch = session.query(Branch).filter_by(id=current_user['branch_id']).first()
        
        if not branch:
            logger.info(f"[清除缓存] 找不到分支信息，分支ID: {current_user.get('branch_id')}")
            return jsonify({'success': False, 'message': '找不到网点信息'}), 404
        
        logger.info(f"[清除缓存] 找到分支: {branch.branch_code} ({branch.branch_name})")
        
        # 清除该分支的缓存
        branch_tokens_to_remove = []
        cache_count_before = len(published_rates_cache)
        
        for cached_token, cached_data in published_rates_cache.items():
            cached_branch_code = cached_data.get('branch', {}).get('code')
            if cached_branch_code == branch.branch_code:
                branch_tokens_to_remove.append(cached_token)
                logger.info(f"[清除缓存] 标记删除缓存: {cached_token[:8]}... (分支: {cached_branch_code})")
        
        removed_count = len(branch_tokens_to_remove)
        for old_token in branch_tokens_to_remove:
            del published_rates_cache[old_token]
            logger.info(f"[清除缓存] 删除缓存: {old_token[:8]}...")
        
        cache_count_after = len(published_rates_cache)
        logger.info(f"[清除缓存] 缓存清理完成: {cache_count_before} -> {cache_count_after} (删除: {removed_count})")
        
        return jsonify({
            'success': True, 
            'message': f'已清除 {removed_count} 个缓存项',
            'removed_tokens': [token[:8] + '...' for token in branch_tokens_to_remove],
            'cache_count_before': cache_count_before,
            'cache_count_after': cache_count_after
        })
        
    except Exception as e:
        logger.info(f"[清除缓存] 异常: {str(e)}")
        import traceback
        logger.info(f"[清除缓存] 异常堆栈: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'清除缓存失败: {str(e)}'}), 500
    finally:
        if session:
            DatabaseService.close_session(session)

@dashboard_bp.route('/cache-status', methods=['GET'])
@token_required
def get_cache_status(current_user):
    """获取缓存状态（用于调试）"""
    try:
        cache_info = []
        for token, data in published_rates_cache.items():
            cache_info.append({
                'token': token[:8] + '...',  # 只显示前8位
                'branch_code': data.get('branch', {}).get('code'),
                'currencies_count': len(data.get('rates', [])),
                'published_at': data.get('published_at'),
                'theme': data.get('theme')
            })
        
        return jsonify({
            'success': True,
            'cache_count': len(published_rates_cache),
            'cache_items': cache_info
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@dashboard_bp.route('/save-rate-sort-order', methods=['POST'])
@token_required
def save_rate_sort_order(current_user):
    """保存汇率排序"""
    try:
        data = request.get_json()
        if not data or 'rates' not in data:
            return jsonify({'success': False, 'message': '缺少排序数据'}), 400

        session = DatabaseService.get_session()
        
        # 获取当天日期
        from datetime import date
        today = date.today()

        # 保存每个汇率的排序位置
        for index, rate_data in enumerate(data['rates']):
            if 'currency_id' not in rate_data:
                continue

            # 更新当天汇率记录的排序字段
            session.query(ExchangeRate).filter(
                ExchangeRate.currency_id == rate_data['currency_id'],
                ExchangeRate.branch_id == current_user['branch_id'],
                ExchangeRate.rate_date == today
            ).update({
                'sort_order': index
            })

        session.commit()

        return jsonify({
            'success': True,
            'message': '排序已保存'
        })

    except Exception as e:
        logger.error(f"in save_rate_sort_order: {str(e)}")
        session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@dashboard_bp.route('/publish-denomination-rates', methods=['POST'])
@token_required
@has_permission('rate_manage')
def publish_denomination_rates(current_user):
    """发布面值汇率到机顶盒显示"""
    data = request.get_json()
    
    if not data or 'currency_id' not in data or 'denomination_rates' not in data:
        return jsonify({'success': False, 'message': '缺少必要参数'}), 400
    
    session = DatabaseService.get_session()
    try:
        # 检查今日已有的面值汇率发布记录（累积式发布）
        today = datetime.now().date()
        existing_records = session.query(RatePublishRecord).filter_by(
            branch_id=current_user['branch_id'],
            publish_date=today
        ).filter(
            RatePublishRecord.notes.like('%面值汇率发布%')
        ).all()
        
        # 获取所有已有的面值汇率数据（包含币种信息）
        existing_denomination_rates = []
        for record in existing_records:
            details = session.query(DenominationPublishDetail).filter_by(
                publish_record_id=record.id
            ).all()
            for detail in details:
                # 获取币种信息
                currency_info = session.query(Currency).filter_by(id=detail.currency_id).first()
                if currency_info:
                    existing_denomination_rates.append({
                        'currency_id': detail.currency_id,
                        'currency_code': currency_info.currency_code,
                        'currency_name': currency_info.currency_name,
                        'flag_code': currency_info.flag_code,
                        'custom_flag_filename': currency_info.custom_flag_filename,
                        'denomination_id': detail.denomination_id,
                        'denomination_value': detail.denomination_value,
                        'denomination_type': detail.denomination_type,
                        'buy_rate': detail.buy_rate,
                        'sell_rate': detail.sell_rate
                    })
        
        logger.info(f"今日已有 {len(existing_records)} 条面值汇率发布记录，{len(existing_denomination_rates)} 个面值汇率")
        
        # 获取币种信息
        currency = session.query(Currency).filter_by(id=data['currency_id']).first()
        if not currency:
            return jsonify({'success': False, 'message': '币种不存在'}), 404
        
        # 获取网点信息
        branch = session.query(Branch).filter_by(id=current_user['branch_id']).first()
        if not branch:
            return jsonify({'success': False, 'message': '网点不存在'}), 404
        
        # 准备面值汇率数据
        denomination_rates_data = []
        valid_denominations = []
        
        for rate_data in data['denomination_rates']:
            # 验证必要字段
            if not all(key in rate_data for key in ['denomination_id', 'buy_rate', 'sell_rate']):
                continue
                
            # 验证汇率数据
            try:
                buy_rate = float(rate_data['buy_rate'])
                sell_rate = float(rate_data['sell_rate'])
                if buy_rate <= 0 or sell_rate <= 0:
                    continue
            except (ValueError, TypeError):
                continue
            
            # 获取面值信息
            denomination = session.query(CurrencyDenomination).filter_by(
                id=rate_data['denomination_id'],
                currency_id=data['currency_id']  # 确保面值属于当前币种
            ).first()
            
            if denomination:
                denomination_rates_data.append({
                    'denomination_id': denomination.id,  # 添加denomination_id字段
                    'denomination_value': denomination.denomination_value,
                    'denomination_type': denomination.denomination_type,
                    'buy_rate': buy_rate,
                    'sell_rate': sell_rate
                })
                valid_denominations.append({
                    'denomination_id': denomination.id,
                    'denomination_value': denomination.denomination_value,
                    'denomination_type': denomination.denomination_type,
                    'buy_rate': buy_rate,
                    'sell_rate': sell_rate
                })
            else:
                logger.warning(f"面值不存在: denomination_id={rate_data['denomination_id']}, currency_id={data['currency_id']}")
        
        if not valid_denominations:
            return jsonify({'success': False, 'message': '没有有效的面值汇率数据'}), 400
        
        # 合并已有数据和当前数据（同币种覆盖，不同币种累积）
        merged_denomination_rates = []
        
        # 添加已有数据（排除当前币种）
        for existing_rate in existing_denomination_rates:
            if existing_rate['currency_id'] != data['currency_id']:
                merged_denomination_rates.append(existing_rate)
        
        # 添加当前币种的新数据（覆盖同币种的旧数据）
        for denom_data in valid_denominations:
            merged_denomination_rates.append({
                'currency_id': data['currency_id'],
                'denomination_id': denom_data['denomination_id'],
                'denomination_value': denom_data['denomination_value'],
                'denomination_type': denom_data['denomination_type'],
                'buy_rate': denom_data['buy_rate'],
                'sell_rate': denom_data['sell_rate']
            })
        
        logger.info(f"合并后面值汇率总数: {len(merged_denomination_rates)} (已有: {len(existing_denomination_rates)}, 新增: {len(valid_denominations)})")
        
        # 生成访问令牌
        token = secrets.token_urlsafe(32)
        
        # 准备发布数据
        publish_time = datetime.now()
        # 构建合并后的面值汇率数据（包含所有币种）
        # 已有数据已经包含币种信息，直接使用
        all_denomination_rates_for_display = merged_denomination_rates
        
        publish_data = {
            'branch': {
                'id': branch.id,
                'name': branch.branch_name,
                'code': branch.branch_code
            },
            'denomination_rates': all_denomination_rates_for_display,
            'publish_time': publish_time.isoformat(),
            'published_at': publish_time.isoformat(),  # 添加published_at字段用于API查询
            'has_denominations': True,  # 标记为面值汇率
            'theme': 'light',  # 添加主题字段
            'language': 'zh',  # 添加语言字段
            'display_config': {
                'items_per_page': 20,
                'refresh_interval': 30
            }
        }
        
        # 开始事务处理
        try:
            # 删除当前币种的旧发布记录（同币种覆盖）
            today = datetime.now().date()
            old_records = session.query(RatePublishRecord).filter_by(
                branch_id=current_user['branch_id'],
                publish_date=today
            ).filter(
                RatePublishRecord.notes.like(f'%面值汇率发布-{currency.currency_code}%')
            ).all()
            
            for old_record in old_records:
                # 删除关联的详情记录
                session.query(DenominationPublishDetail).filter_by(
                    publish_record_id=old_record.id
                ).delete()
                # 删除发布记录
                session.delete(old_record)
            
            if old_records:
                logger.info(f"已删除 {len(old_records)} 条 {currency.currency_code} 的旧发布记录")
            
            # 保存发布记录（只记录当前币种）
            publish_record = RatePublishRecord(
                branch_id=current_user['branch_id'],
                publisher_id=current_user['id'],
                publisher_name=current_user.get('name', '未知用户'),
                publish_date=datetime.now().date(),
                publish_time=datetime.now(),
                access_token=token,
                publish_theme='default',
                total_currencies=len(valid_denominations),  # 当前币种的面值数量
                notes=f'面值汇率发布-{currency.currency_code}'
            )
            session.add(publish_record)
            session.flush()  # 获取ID但不提交
            
            # 保存面值汇率发布详情（只保存当前币种）
            for denom_data in valid_denominations:
                detail = DenominationPublishDetail(
                    publish_record_id=publish_record.id,
                    currency_id=data['currency_id'],
                    denomination_id=denom_data['denomination_id'],
                    denomination_value=denom_data['denomination_value'],
                    denomination_type=denom_data['denomination_type'],
                    buy_rate=denom_data['buy_rate'],
                    sell_rate=denom_data['sell_rate']
                )
                session.add(detail)
            
            # 提交数据库事务
            session.commit()
            
            # 数据库操作成功后，更新内存缓存和文件
            published_rates_cache[token] = publish_data
            update_show_html_branch_code(branch.branch_code)
            
            logger.info(f"面值汇率发布成功: 币种={currency.currency_code}, 面值数量={len(valid_denominations)}, 令牌={token}")
            
        except Exception as db_error:
            # 数据库操作失败，回滚事务
            session.rollback()
            logger.error(f"数据库操作失败，已回滚: {str(db_error)}")
            raise db_error
        
        return jsonify({
            'success': True,
            'message': '面值汇率发布成功',
            'data': {
                'token': token,
                'display_url': f'/api/dashboard/display-rates/{token}',
                'publish_time': publish_data['publish_time']
            }
        })
        
    except Exception as e:
        session.rollback()
        logger.error(f"发布面值汇率失败: {str(e)}")
        return jsonify({'success': False, 'message': f'发布失败: {str(e)}'}), 500
    finally:
        DatabaseService.close_session(session)

# 已删除旧的publish-multi-currency-denomination-rates路由，使用新的批次发布API
# 已删除旧的publish-multi-currency-denomination-rates路由，使用新的批次发布API
    """发布多币种面值汇率到机顶盒显示（使用批次ID管理）"""
    data = request.get_json()
    
    if not data or 'currencies' not in data:
        return jsonify({'success': False, 'message': '缺少必要参数'}), 400
    
    session = DatabaseService.get_session()
    try:
        # 🔧 方案1：生成批次ID
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{current_user['branch_id']}"
        logger.info(f"[批次发布] 生成批次ID: {batch_id}")
        
        # 获取显示配置
        theme = data.get('theme', 'light')
        language = data.get('language', 'zh')
        items_per_page = data.get('items_per_page', 20)
        refresh_interval = data.get('refresh_interval', 3600)
        
        # 验证刷新间隔
        if not isinstance(refresh_interval, int) or refresh_interval < 5 or refresh_interval > 86400:
            logger.info(f"[批次发布] refresh_interval 验证失败，使用默认值3600")
            refresh_interval = 3600
        # 检查今日已有的面值汇率发布记录（累积式发布）
        today = datetime.now().date()
        existing_records = session.query(RatePublishRecord).filter_by(
            branch_id=current_user['branch_id'],
            publish_date=today
        ).filter(
            RatePublishRecord.notes.like('%面值汇率发布%')
        ).all()
        
        # 获取所有已有的面值汇率数据（包含币种信息）
        existing_denomination_rates = []
        for record in existing_records:
            details = session.query(DenominationPublishDetail).filter_by(
                publish_record_id=record.id
            ).all()
            for detail in details:
                # 获取币种信息
                currency_info = session.query(Currency).filter_by(id=detail.currency_id).first()
                if currency_info:
                    existing_denomination_rates.append({
                        'currency_id': detail.currency_id,
                        'currency_code': currency_info.currency_code,
                        'currency_name': currency_info.currency_name,
                        'flag_code': currency_info.flag_code,
                        'custom_flag_filename': currency_info.custom_flag_filename,
                        'denomination_id': detail.denomination_id,
                        'denomination_value': detail.denomination_value,
                        'denomination_type': detail.denomination_type,
                        'buy_rate': detail.buy_rate,
                        'sell_rate': detail.sell_rate
                    })
        
        logger.info(f"今日已有 {len(existing_records)} 条面值汇率发布记录，{len(existing_denomination_rates)} 个面值汇率")
        
        # 获取网点信息
        branch = session.query(Branch).filter_by(id=current_user['branch_id']).first()
        if not branch:
            return jsonify({'success': False, 'message': '网点不存在'}), 404
        
        # 删除当前要发布币种的旧记录（替换式发布）
        current_currency_ids = [currency_data['currency_id'] for currency_data in data['currencies']]
        
        # 删除今日该币种的旧发布记录
        for currency_id in current_currency_ids:
            # 查找该币种的旧发布记录
            old_records = session.query(RatePublishRecord).filter_by(
                branch_id=current_user['branch_id'],
                publish_date=today
            ).filter(
                RatePublishRecord.notes.like('%面值汇率发布%')
            ).all()
            
            for old_record in old_records:
                # 检查该记录是否包含当前币种
                old_details = session.query(DenominationPublishDetail).filter_by(
                    publish_record_id=old_record.id,
                    currency_id=currency_id
                ).all()
                
                if old_details:
                    # 删除该币种的旧详情记录
                    for detail in old_details:
                        session.delete(detail)
                    
                    # 如果该发布记录没有其他币种了，删除整个发布记录
                    remaining_details = session.query(DenominationPublishDetail).filter_by(
                        publish_record_id=old_record.id
                    ).count()
                    
                    if remaining_details == 0:
                        session.delete(old_record)
                        logger.info(f"删除空的发布记录: {old_record.id}")
                    else:
                        logger.info(f"从发布记录 {old_record.id} 中删除币种 {currency_id} 的旧记录")
        
        # 获取其他币种的现有数据（不包含当前要发布的币种）
        merged_denomination_rates = []
        for existing_rate in existing_denomination_rates:
            if existing_rate['currency_id'] not in current_currency_ids:
                merged_denomination_rates.append(existing_rate)
        
        # 处理每个币种的面值汇率
        all_denomination_rates = []
        total_denominations = 0
        
        for currency_data in data['currencies']:
            currency_id = currency_data['currency_id']
            denomination_rates = currency_data['denomination_rates']
            
            # 获取币种信息
            currency = session.query(Currency).filter_by(id=currency_id).first()
            if not currency:
                continue
            
            # 准备面值汇率数据
            valid_denominations = []
            
            for rate_data in denomination_rates:
                # 验证必要字段
                if not all(key in rate_data for key in ['denomination_id', 'buy_rate', 'sell_rate']):
                    continue
                    
                # 验证汇率数据
                try:
                    buy_rate = float(rate_data['buy_rate'])
                    sell_rate = float(rate_data['sell_rate'])
                    if buy_rate <= 0 or sell_rate <= 0:
                        continue
                except (ValueError, TypeError):
                    continue
                
                # 获取面值信息
                denomination = session.query(CurrencyDenomination).filter_by(
                    id=rate_data['denomination_id'],
                    currency_id=currency_id
                ).first()
                
                if denomination:
                    valid_denominations.append({
                        'currency_id': currency_id,  # 添加currency_id
                        'currency_code': currency.currency_code,  # 添加币种代码
                        'currency_name': currency.currency_name,  # 添加币种名称
                        'flag_code': currency.flag_code,  # 添加国旗代码
                        'custom_flag_filename': currency.custom_flag_filename,  # 添加自定义图标
                        'denomination_id': denomination.id,
                        'denomination_value': denomination.denomination_value,
                        'denomination_type': denomination.denomination_type,
                        'buy_rate': buy_rate,
                        'sell_rate': sell_rate
                    })
            
            if valid_denominations:
                # 添加到总的面值汇率列表
                all_denomination_rates.extend(valid_denominations)
                total_denominations += len(valid_denominations)
                
                # 添加到合并列表
                merged_denomination_rates.extend(valid_denominations)
        
        if not all_denomination_rates:
            return jsonify({'success': False, 'message': '没有有效的面值汇率数据'}), 400
        
        logger.info(f"合并后面值汇率总数: {len(merged_denomination_rates)} (已有: {len(existing_denomination_rates)}, 新增: {len(all_denomination_rates)})")
        
        # 生成访问令牌
        token = secrets.token_urlsafe(32)
        
        # 获取显示配置参数
        theme = data.get('theme', 'light')
        language = data.get('language', 'zh')
        display_config = data.get('display_config', {})
        items_per_page = display_config.get('items_per_page', 12)
        refresh_interval = display_config.get('refresh_interval', 3600)
        
        # 验证配置参数
        if not isinstance(items_per_page, int) or items_per_page < 6 or items_per_page > 20:
            items_per_page = 12
        if not isinstance(refresh_interval, int) or refresh_interval < 5 or refresh_interval > 86400:
            refresh_interval = 3600
        
        # 准备发布数据（使用合并后的数据）
        publish_time = datetime.now()
        publish_data = {
            'branch': {
                'id': branch.id,
                'name': branch.branch_name,
                'code': branch.branch_code
            },
            'denomination_rates': merged_denomination_rates,
            'publish_time': publish_time.isoformat(),
            'published_at': publish_time.isoformat(),
            'has_denominations': True,
            'theme': theme,
            'language': language,
            'display_config': {
                'items_per_page': items_per_page,
                'refresh_interval': refresh_interval
            }
        }
        
        # 🔧 修复：清理该分支的旧面值汇率发布记录，确保Token唯一性
        logger.info(f"[批量发布] 清理分支 {current_user['branch_id']} 的旧面值汇率发布记录")
        old_records = session.query(RatePublishRecord).filter_by(
            branch_id=current_user['branch_id']
        ).filter(
            RatePublishRecord.notes.like('%面值汇率发布%')
        ).all()
        
        for old_record in old_records:
            # 删除相关的面值汇率详情
            session.query(DenominationPublishDetail).filter_by(
                publish_record_id=old_record.id
            ).delete()
            # 删除发布记录
            session.delete(old_record)
            logger.info(f"[批量发布] 删除旧发布记录: {old_record.access_token[:8]}...")
        
        # 开始事务处理
        try:
            # 保存发布记录
            publish_record = RatePublishRecord(
                branch_id=current_user['branch_id'],
                publisher_id=current_user['id'],
                publisher_name=current_user.get('name', '未知用户'),
                publish_date=datetime.now().date(),
                publish_time=datetime.now(),
                access_token=token,
                publish_theme=theme,  # 保存主题
                total_currencies=total_denominations,
                notes=f'面值汇率发布|theme:{theme}|lang:{language}|page:{items_per_page}|refresh:{refresh_interval}'  # 保存显示配置
            )
            session.add(publish_record)
            session.flush()  # 获取ID
            
            # 保存面值汇率发布详情
            for detail_data in all_denomination_rates:
                detail = DenominationPublishDetail(
                    publish_record_id=publish_record.id,
                    currency_id=detail_data.get('currency_id', 0),  # 从detail_data中获取
                    denomination_id=detail_data['denomination_id'],
                    denomination_value=detail_data['denomination_value'],
                    denomination_type=detail_data['denomination_type'],
                    buy_rate=detail_data['buy_rate'],
                    sell_rate=detail_data['sell_rate']
                )
                session.add(detail)
            
            # 提交数据库事务
            session.commit()
            
            # 数据库操作成功后，更新内存缓存和文件
            published_rates_cache[token] = publish_data
            update_show_html_branch_code(branch.branch_code)
            
            logger.info(f"多币种面值汇率发布成功: 总面值数量={total_denominations}, 令牌={token}")
            
        except Exception as db_error:
            # 数据库操作失败，回滚事务
            session.rollback()
            logger.error(f"数据库操作失败，已回滚: {str(db_error)}")
            raise db_error
        
        return jsonify({
            'success': True,
            'message': '多币种面值汇率发布成功',
            'data': {
                'token': token,
                'display_url': f'/api/dashboard/display-rates/{token}',
                'publish_time': publish_data['publish_time']
            }
        })
        
    except Exception as e:
        session.rollback()
        logger.error(f"发布多币种面值汇率失败: {str(e)}")
        return jsonify({'success': False, 'message': f'发布失败: {str(e)}'}), 500
    finally:
        DatabaseService.close_session(session)

@dashboard_bp.route('/clear-cache', methods=['POST'])
@token_required
@has_permission('rate_manage')
def clear_cache(current_user):
    """清理发布缓存"""
    try:
        # 清理所有缓存
        published_rates_cache.clear()
        logger.info(f"用户 {current_user.get('name', '未知用户')} 清理了所有发布缓存")
        
        return jsonify({
            'success': True,
            'message': '缓存清理成功'
        })
    except Exception as e:
        logger.error(f"清理缓存失败: {str(e)}")
        return jsonify({'success': False, 'message': f'清理缓存失败: {str(e)}'}), 500

@dashboard_bp.route('/denomination-publish-history', methods=['GET'])
@token_required
@has_permission('rate_manage')
def get_denomination_publish_history(current_user):
    """获取面值汇率发布历史"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    currency_id = request.args.get('currency_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    session = DatabaseService.get_session()
    try:
        # 构建查询条件
        query = session.query(RatePublishRecord).filter_by(
            branch_id=current_user['branch_id']
        ).filter(
            RatePublishRecord.notes.like('%面值汇率发布%')
        )
        
        # 添加过滤条件
        if currency_id:
            query = query.join(DenominationPublishDetail).filter(
                DenominationPublishDetail.currency_id == currency_id
            )
        
        if start_date:
            query = query.filter(RatePublishRecord.publish_date >= start_date)
        
        if end_date:
            query = query.filter(RatePublishRecord.publish_date <= end_date)
        
        # 排序和分页
        query = query.order_by(desc(RatePublishRecord.publish_time))
        
        total = query.count()
        records = query.offset((page - 1) * per_page).limit(per_page).all()
        
        # 获取详细信息
        result = []
        for record in records:
            # 获取面值汇率详情
            details = session.query(DenominationPublishDetail).filter_by(
                publish_record_id=record.id
            ).join(Currency).all()
            
            denomination_rates = []
            for detail in details:
                denomination_rates.append({
                    'denomination_value': float(detail.denomination_value),
                    'denomination_type': detail.denomination_type,
                    'buy_rate': float(detail.buy_rate),
                    'sell_rate': float(detail.sell_rate)
                })
            
            result.append({
                'id': record.id,
                'publish_date': record.publish_date.isoformat() if record.publish_date else None,
                'publish_time': record.publish_time.isoformat() if record.publish_time else None,
                'publisher_name': record.publisher_name,
                'total_denominations': record.total_currencies,
                'access_token': record.access_token,
                'notes': record.notes,
                'denomination_rates': denomination_rates,
                'created_at': record.created_at.isoformat() if record.created_at else None
            })
        
        return jsonify({
            'success': True,
            'data': {
                'records': result,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            }
        })
        
    except Exception as e:
        logger.error(f"获取面值汇率发布历史失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取历史失败: {str(e)}'}), 500
    finally:
        DatabaseService.close_session(session)

@dashboard_bp.route('/denomination-publish-detail/<int:record_id>', methods=['GET'])
@token_required
@has_permission('rate_manage')
def get_denomination_publish_detail(current_user, record_id):
    """获取面值汇率发布详情"""
    session = DatabaseService.get_session()
    try:
        # 获取发布记录
        record = session.query(RatePublishRecord).filter_by(
            id=record_id,
            branch_id=current_user['branch_id']
        ).first()
        
        if not record:
            return jsonify({'success': False, 'message': '发布记录不存在'}), 404
        
        # 获取面值汇率详情
        details = session.query(DenominationPublishDetail).filter_by(
            publish_record_id=record.id
        ).join(Currency).all()
        
        denomination_rates = []
        for detail in details:
            denomination_rates.append({
                'denomination_id': detail.denomination_id,
                'denomination_value': float(detail.denomination_value),
                'denomination_type': detail.denomination_type,
                'buy_rate': float(detail.buy_rate),
                'sell_rate': float(detail.sell_rate),
                'spread': float(detail.sell_rate - detail.buy_rate)
            })
        
        return jsonify({
            'success': True,
            'data': {
                'record': {
                    'id': record.id,
                    'publish_date': record.publish_date.isoformat() if record.publish_date else None,
                    'publish_time': record.publish_time.isoformat() if record.publish_time else None,
                    'publisher_name': record.publisher_name,
                    'total_denominations': record.total_currencies,
                    'access_token': record.access_token,
                    'notes': record.notes,
                    'created_at': record.created_at.isoformat() if record.created_at else None
                },
                'denomination_rates': denomination_rates
            }
        })
        
    except Exception as e:
        logger.error(f"获取面值汇率发布详情失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取详情失败: {str(e)}'}), 500
    finally:
        DatabaseService.close_session(session)

@dashboard_bp.route('/publish-detail/<int:record_id>', methods=['GET'])
@token_required
@has_permission('rate_manage')
def get_publish_detail(current_user, record_id):
    """获取发布记录详情（自动识别面值汇率或标准汇率）"""
    session = DatabaseService.get_session()
    try:
        # 获取发布记录
        record = session.query(RatePublishRecord).filter(
            RatePublishRecord.id == record_id,
            RatePublishRecord.branch_id == current_user['branch_id']
        ).first()
        
        if not record:
            return jsonify({'success': False, 'message': '发布记录不存在'}), 404
        
        # 检查是否有面值汇率详情
        denomination_details = session.query(DenominationPublishDetail).filter_by(
            publish_record_id=record.id
        ).all()
        
        if denomination_details:
            # 面值汇率发布记录
            denomination_rates = []
            for detail in denomination_details:
                # 获取币种信息
                currency = session.query(Currency).filter_by(id=detail.currency_id).first()
                denomination_rates.append({
                    'denomination_id': detail.denomination_id,
                    'currency_id': detail.currency_id,
                    'currency_code': currency.currency_code if currency else 'UNKNOWN',
                    'currency_name': currency.currency_name if currency else '未知币种',
                    'denomination_value': float(detail.denomination_value),
                    'denomination_type': detail.denomination_type,
                    'buy_rate': float(detail.buy_rate),
                    'sell_rate': float(detail.sell_rate),
                    'spread': float(detail.sell_rate - detail.buy_rate)
                })
            
            return jsonify({
                'success': True,
                'data': {
                    'record': {
                        'id': record.id,
                        'publish_date': record.publish_date.isoformat() if record.publish_date else None,
                        'publish_time': record.publish_time.isoformat() if record.publish_time else None,
                        'publisher_name': record.publisher_name,
                        'total_currencies': record.total_currencies,
                        'access_token': record.access_token,
                        'notes': record.notes,
                        'created_at': record.created_at.isoformat() if record.created_at else None
                    },
                    'type': 'denomination',
                    'denomination_rates': denomination_rates
                }
            })
        else:
            # 标准汇率发布记录
            details = session.query(RatePublishDetail).filter(
                RatePublishDetail.publish_record_id == record_id
            ).order_by(RatePublishDetail.sort_order).all()
            
            rates = []
            for detail in details:
                currency = session.query(Currency).filter_by(id=detail.currency_id).first()
                rates.append({
                    'currency_id': detail.currency_id,
                    'currency_code': detail.currency_code,
                    'currency_name': detail.currency_name,
                    'buy_rate': float(detail.buy_rate),
                    'sell_rate': float(detail.sell_rate),
                    'spread': float(detail.sell_rate - detail.buy_rate),
                    'sort_order': detail.sort_order
                })
            
            return jsonify({
                'success': True,
                'data': {
                    'record': {
                        'id': record.id,
                        'publish_date': record.publish_date.isoformat() if record.publish_date else None,
                        'publish_time': record.publish_time.isoformat() if record.publish_time else None,
                        'publisher_name': record.publisher_name,
                        'total_currencies': record.total_currencies,
                        'access_token': record.access_token,
                        'notes': record.notes,
                        'created_at': record.created_at.isoformat() if record.created_at else None
                    },
                    'type': 'standard',
                    'rates': rates
                }
            })
        
    except Exception as e:
        logger.error(f"获取发布记录详情失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取详情失败: {str(e)}'}), 500
    finally:
        DatabaseService.close_session(session)

@dashboard_bp.route('/today-denomination-currencies', methods=['GET'])
@token_required
@has_permission('rate_manage')
def get_today_denomination_currencies(current_user):
    """获取今日已设置面值汇率的币种"""
    session = DatabaseService.get_session()
    try:
        today = datetime.now().date()
        
        # 查询今日已设置面值汇率的币种（从DenominationRate表查询）
        query = session.query(
            Currency.id.label('currency_id'),
            Currency.currency_code,
            Currency.currency_name,
            func.count(DenominationRate.id).label('denomination_count')
        ).join(
            DenominationRate, Currency.id == DenominationRate.currency_id
        ).filter(
            DenominationRate.branch_id == current_user['branch_id'],
            DenominationRate.rate_date == today
        ).group_by(
            Currency.id, Currency.currency_code, Currency.currency_name
        ).order_by(Currency.currency_code)
        
        results = query.all()
        
        currencies = []
        for result in results:
            currencies.append({
                'currency_id': result.currency_id,
                'currency_code': result.currency_code,
                'currency_name': result.currency_name,
                'denomination_count': result.denomination_count
            })
        
        logger.info(f"获取今日已设置面值汇率的币种: {len(currencies)}个币种")
        for currency in currencies:
            logger.info(f"  - {currency['currency_code']}: {currency['denomination_count']}个面值")
        
        return jsonify({
            'success': True,
            'data': currencies
        })
        
    except Exception as e:
        logger.error(f"获取今日已设置币种失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500
    finally:
        DatabaseService.close_session(session)

@dashboard_bp.route('/currency-denomination-rates/<int:currency_id>', methods=['GET'])
@token_required
@has_permission('rate_manage')
def get_currency_denomination_rates(current_user, currency_id):
    """获取指定币种的面值汇率数据（从DenominationRate表获取已设置的数据）"""
    session = DatabaseService.get_session()
    try:
        today = datetime.now().date()
        
        # 🔧 修复：查询DenominationRate表（已设置的面值汇率），而不是DenominationPublishDetail表（已发布的面值汇率）
        query = session.query(DenominationRate).join(
            CurrencyDenomination, DenominationRate.denomination_id == CurrencyDenomination.id
        ).filter(
            DenominationRate.branch_id == current_user['branch_id'],
            DenominationRate.rate_date == today,
            DenominationRate.currency_id == currency_id
        ).order_by(CurrencyDenomination.sort_order, CurrencyDenomination.denomination_value)
        
        results = query.all()
        
        denomination_rates = []
        for result in results:
            denomination_rates.append({
                'denomination_id': result.denomination_id,
                'denomination_value': float(result.denomination.denomination_value),
                'denomination_type': result.denomination.denomination_type,
                'buy_rate': float(result.buy_rate),
                'sell_rate': float(result.sell_rate)
            })
        
        return jsonify({
            'success': True,
            'data': denomination_rates
        })
        
    except Exception as e:
        logger.error(f"获取币种面值汇率失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500
    finally:
        DatabaseService.close_session(session)

@dashboard_bp.route('/currency-balance/<int:currency_id>', methods=['GET'])
@token_required
def get_currency_balance(current_user, currency_id):
    """获取指定币种的当前余额"""
    session = DatabaseService.get_session()
    try:
        branch_id = current_user['branch_id']

        # 查询币种余额
        balance_record = session.query(CurrencyBalance).filter_by(
            branch_id=branch_id,
            currency_id=currency_id
        ).first()

        if balance_record:
            balance = float(balance_record.balance)
        else:
            # 如果没有余额记录，返回0
            balance = 0.0

        # 获取币种信息
        currency = session.query(Currency).filter_by(id=currency_id).first()
        currency_code = currency.currency_code if currency else f'CUR_{currency_id}'
        currency_name = currency.currency_name if currency else '未知币种'

        return jsonify({
            'success': True,
            'balance': balance,
            'currency_id': currency_id,
            'currency_code': currency_code,
            'currency_name': currency_name,
            'last_updated': balance_record.updated_at.isoformat() if balance_record and balance_record.updated_at else None
        })

    except Exception as e:
        logger.error(f"获取币种余额失败: currency_id={currency_id}, error={str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取币种余额失败: {str(e)}',
            'balance': 0.0
        }), 500
    finally:
        DatabaseService.close_session(session)
