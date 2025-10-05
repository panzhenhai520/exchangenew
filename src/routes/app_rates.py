from datetime import datetime, date, timedelta
from decimal import Decimal
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import func, and_, or_
from models.exchange_models import ExchangeRate, Currency, SystemLog, CurrencyTemplate, Branch, RatePublishRecord, RatePublishDetail, ExchangeTransaction, BranchCurrency, BranchBalanceAlert, DenominationPublishDetail
from services.db_service import DatabaseService
from services.auth_service import token_required, has_permission
from utils.multilingual_log_service import multilingual_logger

def auto_init_daily_rates(session, branch_id, today):
    """自动初始化每日汇率记录，确保排序继承"""
    try:
        # 获取网点信息和本币ID
        branch = session.query(Branch).filter_by(id=branch_id).first()
        if not branch:
            return
            
        base_currency_id = branch.base_currency_id
        
        # 获取被禁用的币种ID列表
        disabled_currency_ids = session.query(BranchCurrency.currency_id).filter(
            BranchCurrency.branch_id == branch_id,
            BranchCurrency.is_enabled == False
        ).all()
        
        disabled_currency_id_list = [row[0] for row in disabled_currency_ids]
        
        # 删除被禁用币种的今日汇率记录
        current_app.logger.info(f"[DEBUG] 自动初始化 - 被禁用的币种ID列表: {disabled_currency_id_list}")
        if disabled_currency_id_list:
            # 先查询要删除的记录
            records_to_delete = session.query(ExchangeRate).filter(
                ExchangeRate.branch_id == branch_id,
                ExchangeRate.rate_date == today,
                ExchangeRate.currency_id.in_(disabled_currency_id_list)
            ).all()
            current_app.logger.info(f"[DEBUG] 自动初始化 - 找到 {len(records_to_delete)} 个被禁用币种的汇率记录需要删除")
            for record in records_to_delete:
                current_app.logger.info(f"[DEBUG] 自动初始化 - 将删除: 网点{record.branch_id} 币种{record.currency_id} 日期{record.rate_date}")
            
            deleted_count = session.query(ExchangeRate).filter(
                ExchangeRate.branch_id == branch_id,
                ExchangeRate.rate_date == today,
                ExchangeRate.currency_id.in_(disabled_currency_id_list)
            ).delete()
            current_app.logger.info(f"[DEBUG] 自动初始化 - 实际删除了 {deleted_count} 个被禁用币种的汇率记录")
        else:
            current_app.logger.info(f"[DEBUG] 自动初始化 - 没有需要删除的被禁用币种")
        
        # 检查今天是否还有汇率记录
        today_rates_count = session.query(ExchangeRate).filter(
            ExchangeRate.branch_id == branch_id,
            ExchangeRate.rate_date == today
        ).count()
        
        if today_rates_count > 0:
            # 今天已有汇率记录，但需要检查是否有被禁用的币种需要重新初始化
            print(f"[DEBUG] 自动初始化 - 今天已有 {today_rates_count} 个汇率记录，检查是否需要重新初始化")
            
            # 获取当前启用的币种列表
            enabled_currencies = session.query(Currency).filter(
                Currency.id != base_currency_id,
                ~Currency.id.in_(disabled_currency_id_list)  # 排除被禁用的币种
            ).all()
            
            # 检查是否有启用的币种没有今日汇率记录
            existing_currency_ids = session.query(ExchangeRate.currency_id).filter(
                ExchangeRate.branch_id == branch_id,
                ExchangeRate.rate_date == today
            ).all()
            existing_currency_id_list = [row[0] for row in existing_currency_ids]
            
            missing_currencies = [c for c in enabled_currencies if c.id not in existing_currency_id_list]
            
            if missing_currencies:
                print(f"[DEBUG] 自动初始化 - 发现 {len(missing_currencies)} 个启用的币种缺少今日汇率记录")
                # 为缺少的币种创建汇率记录
                for currency in missing_currencies:
                    # 查找昨天的对应记录来继承排序和汇率
                    yesterday_rate = next(
                        (rate for rate in yesterday_rates if rate.currency_id == currency.id), 
                        None
                    )
                    
                    # 确定排序值和汇率
                    if yesterday_rate and yesterday_rate.sort_order:
                        sort_order = yesterday_rate.sort_order
                        buy_rate = yesterday_rate.buy_rate
                        sell_rate = yesterday_rate.sell_rate
                    else:
                        # 使用默认值
                        sort_order = currency.id
                        buy_rate = 0
                        sell_rate = 0
                    
                    # 创建今天的汇率记录
                    new_rate = ExchangeRate(
                        currency_id=currency.id,
                        branch_id=branch_id,
                        rate_date=today,
                        buy_rate=buy_rate,
                        sell_rate=sell_rate,
                        created_by=1,  # 系统创建
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                        sort_order=sort_order
                    )
                    
                    session.add(new_rate)
                
                session.commit()
                print(f"[DEBUG] 自动初始化 - 为 {len(missing_currencies)} 个币种创建了汇率记录")
            else:
                print(f"[DEBUG] 自动初始化 - 所有启用的币种都有今日汇率记录，无需重新初始化")
            return
        
        # 获取昨天的汇率记录
        yesterday = today - timedelta(days=1)
        yesterday_rates = session.query(ExchangeRate).filter(
            ExchangeRate.branch_id == branch_id,
            ExchangeRate.rate_date == yesterday
        ).all()
        
        # 获取所有货币（排除本币，只包含启用的币种）
        # 使用新的BranchCurrency表来检查币种是否在当前网点被启用
        # 如果币种在BranchCurrency表中没有记录，默认认为是启用的
        all_currencies = session.query(Currency).filter(
            Currency.id != base_currency_id,
            ~Currency.id.in_(disabled_currency_id_list)  # 排除被禁用的币种
        ).all()
        
        # 添加调试信息
        disabled_count = session.query(BranchCurrency).filter(
            BranchCurrency.branch_id == branch_id,
            BranchCurrency.is_enabled == False
        ).count()
        print(f"[DEBUG] 自动初始化 - 网点{branch_id}, 禁用的币种数量: {disabled_count}")
        print(f"[DEBUG] 自动初始化 - 将创建 {len(all_currencies)} 个币种的汇率记录")
        for currency in all_currencies:
            print(f"[DEBUG] 自动初始化 - 币种: {currency.currency_code}")
        
        # 为每个货币创建今天的汇率记录
        for currency in all_currencies:
            # 查找昨天的对应记录来继承排序和汇率
            yesterday_rate = next(
                (rate for rate in yesterday_rates if rate.currency_id == currency.id), 
                None
            )
            
            # 确定排序值和汇率
            if yesterday_rate and yesterday_rate.sort_order:
                sort_order = yesterday_rate.sort_order
                buy_rate = yesterday_rate.buy_rate
                sell_rate = yesterday_rate.sell_rate
            else:
                # 使用默认值
                sort_order = currency.id
                buy_rate = 0
                sell_rate = 0
            
            # 创建今天的汇率记录
            new_rate = ExchangeRate(
                currency_id=currency.id,
                branch_id=branch_id,
                rate_date=today,
                buy_rate=buy_rate,
                sell_rate=sell_rate,
                created_by=1,  # 系统创建
                created_at=datetime.now(),
                updated_at=datetime.now(),
                sort_order=sort_order
            )
            
            session.add(new_rate)
        
        # 提交更改
        session.commit()
        current_app.logger.info(f"[API] /rates/all - 自动初始化了 {len(all_currencies)} 个货币的汇率记录")
        
    except Exception as e:
        current_app.logger.error(f"[API] /rates/all - 自动初始化失败: {str(e)}")
        session.rollback()

rates_bp = Blueprint('rates', __name__, url_prefix='/api/rates')

@rates_bp.route('/all', methods=['GET'])
@token_required
def get_all_exchange_rates(current_user):
    session = DatabaseService.get_session()
    try:
        branch_id = current_user['branch_id']
        today = date.today()
        
        # 获取published_only参数
        published_only = request.args.get('published_only', 'false').lower() == 'true'
        current_app.logger.info(f"[API] /rates/all - published_only: {published_only}")

        # 【新增】自动初始化每日汇率记录
        auto_init_daily_rates(session, branch_id, today)

        # 获取网点信息和本币ID
        branch = session.query(Branch).filter_by(id=branch_id).first()
        if not branch:
            return jsonify({'success': False, 'message': '网点信息不存在'}), 404
            
        base_currency_id = branch.base_currency_id

        # 根据参数决定发布状态判断逻辑
        published_currency_ids = set()
        if published_only:
            # 严格模式：返回今日所有发布记录的累积货币（支持多次发布）
            publish_records = session.query(RatePublishRecord).filter(
                RatePublishRecord.branch_id == branch_id,
                RatePublishRecord.publish_date == today
            ).order_by(RatePublishRecord.publish_time.desc()).all()
            
            if publish_records:
                # 累积所有发布记录的货币ID
                for publish_record in publish_records:
                    record_currency_ids = set(
                        detail.currency_id for detail in 
                        session.query(RatePublishDetail).filter(
                            RatePublishDetail.publish_record_id == publish_record.id
                        ).all()
                    )
                    published_currency_ids.update(record_currency_ids)
                
                current_app.logger.info(f"[API] /rates/all - 严格模式，今日发布记录数: {len(publish_records)}, 累积发布货币数: {len(published_currency_ids)}")
                current_app.logger.info(f"[API] /rates/all - 累积发布的货币ID列表: {published_currency_ids}")
            else:
                current_app.logger.info(f"[API] /rates/all - 严格模式，今日无发布记录")
                return jsonify({
                    'success': True, 
                    'rates': [],
                    'last_update': datetime.now().isoformat(),
                    'published_only': published_only
                })
        else:
            # 宽松模式：查询发布记录但不强制要求
            publish_record = session.query(RatePublishRecord).filter(
                RatePublishRecord.branch_id == branch_id,
                RatePublishRecord.publish_date == today
            ).order_by(RatePublishRecord.publish_time.desc()).first()
            
            if publish_record:
                published_currency_ids = set(
                    detail.currency_id for detail in 
                    session.query(RatePublishDetail).filter(
                        RatePublishDetail.publish_record_id == publish_record.id
                    ).all()
                )
                current_app.logger.info(f"[API] /rates/all - 宽松模式，找到发布记录，发布货币数: {len(published_currency_ids)}")
                current_app.logger.info(f"[API] /rates/all - 发布的货币ID列表: {published_currency_ids}")
            else:
                current_app.logger.info(f"[API] /rates/all - 宽松模式，今日无发布记录")

        # 获取被禁用的币种ID列表（用于过滤今日汇率记录）
        disabled_currency_ids = session.query(BranchCurrency.currency_id).filter(
            BranchCurrency.branch_id == branch_id,
            BranchCurrency.is_enabled == False
        ).all()
        disabled_currency_id_list = [row[0] for row in disabled_currency_ids]
        
        # 获取今日汇率记录（排除本币和被禁用的币种）
        today_rates_query = session.query(ExchangeRate).join(Currency).filter(
            ExchangeRate.branch_id == branch_id,
            ExchangeRate.rate_date == today,
            Currency.id != base_currency_id,
            ~Currency.id.in_(disabled_currency_id_list)  # 排除被禁用的币种
        )
        
        if published_only:
            # 严格模式：只返回真正发布的货币
            today_rates_query = today_rates_query.filter(
                Currency.id.in_(published_currency_ids)
            )
        
        # 按照sort_order排序，如果sort_order为None则按currency_code排序
        # MySQL兼容的排序方式
        today_rates = today_rates_query.order_by(
            ExchangeRate.sort_order.asc(),
            Currency.currency_code.asc()
        ).all()

        # 获取其他所有货币（如果不是published_only模式）
        other_currencies = []
        if not published_only:
            # 对于没有今日汇率的货币，获取最近一次的汇率记录来获取sort_order
            # 安全地获取今日汇率的币种ID列表
            today_rate_currency_ids = [rate.currency_id for rate in today_rates if rate is not None]
            other_currencies_query = session.query(Currency).filter(
                Currency.id != base_currency_id,
                ~Currency.id.in_(today_rate_currency_ids),
                ~Currency.id.in_(disabled_currency_id_list)  # 排除被禁用的币种
            )
            other_currencies = other_currencies_query.order_by(Currency.currency_code.asc()).all()

        yesterday = today - timedelta(days=1)
        result = []

        # 处理今日有汇率的币种
        for rate in today_rates:
            if rate is None:
                current_app.logger.warning("[API] /rates/all - 跳过None汇率对象")
                continue
                
            currency = rate.currency
            if currency is None:
                current_app.logger.warning(f"[API] /rates/all - 汇率ID {rate.id} 的currency为None")
                continue
                
            today_rate = rate
            latest_rate = today_rate

            # 获取昨天的汇率用于计算变化
            yesterday_rate = session.query(ExchangeRate).filter(
                ExchangeRate.currency_id == currency.id,
                ExchangeRate.branch_id == branch_id,
                ExchangeRate.rate_date == yesterday
            ).first()

            # 计算变化率
            change = 0
            change_percentage = 0
            if yesterday_rate and latest_rate:
                change = latest_rate.buy_rate - yesterday_rate.buy_rate
                change_percentage = (change / yesterday_rate.buy_rate) * 100 if yesterday_rate.buy_rate else 0

            # 判断是否今日手动编辑过
            is_edited_today = False
            editor_name = None
            if today_rate:
                if today_rate.updated_at and today_rate.created_at:
                    time_diff = (today_rate.updated_at - today_rate.created_at).total_seconds()
                    updated_today = today_rate.updated_at.date() == today
                    created_today = today_rate.created_at.date() == today
                    
                    is_edited_today = (
                        (time_diff > 1) or
                        (updated_today and not created_today) or
                        (updated_today and created_today and abs(time_diff) > 1)
                    )
                    
                # 获取编辑者姓名
                if today_rate.created_by:
                    try:
                        from models.exchange_models import Operator
                        editor = session.query(Operator).filter_by(id=today_rate.created_by).first()
                        if editor and editor.name:
                            editor_name = editor.name
                        else:
                            editor_name = '系统管理员'
                    except Exception as e:
                        current_app.logger.warning(f"[API] /rates/all - 获取编辑者信息失败: {str(e)}")
                        editor_name = '系统管理员'
                else:
                    editor_name = '系统管理员'
            
            # 添加真正的发布状态标识
            is_really_published = currency.id in published_currency_ids
            
            # 判断发布状态 - 按用户要求：网点=当前网点，发布日期=当前日期就是已发布
            if published_only:
                # 严格模式：能走到这里说明肯定在发布记录中
                is_today_published = True
            else:
                # 宽松模式：汇率管理页面用，优先检查真正的发布记录
                is_today_published = False
                if is_really_published:
                    # 方式1：如果在发布记录中，直接标记为已发布
                    is_today_published = True
                elif today_rate:
                    # 方式2：检查是否执行了批量保存且是今日保存
                    batch_saved_time_str = getattr(today_rate, 'batch_saved_time', None)
                    if (getattr(today_rate, 'batch_saved', 0) == 1 and 
                        batch_saved_time_str and
                        batch_saved_time_str.startswith(today.strftime('%Y-%m-%d'))):
                        is_today_published = True
                    # 方式3：如果没有批量保存标记，检查是否今日创建或更新（兼容原有逻辑）
                    elif getattr(today_rate, 'batch_saved', 0) == 0:
                        created_today = today_rate.created_at and today_rate.created_at.date() == today
                        updated_today = today_rate.updated_at and today_rate.updated_at.date() == today
                        is_today_published = created_today or updated_today
            
            current_app.logger.debug(f"[API] {currency.currency_code}: published_only={published_only}, is_today_published={is_today_published}, is_really_published={is_really_published}")

            rate_data = {
                'currency_id': currency.id,
                'currency_code': currency.currency_code,
                'currency_name': currency.currency_name,
                'flag_code': currency.flag_code,
                'custom_flag_filename': currency.custom_flag_filename,  # 添加自定义图标字段
                'rate_date': latest_rate.rate_date.isoformat() if latest_rate else today.isoformat(),
                'buy_rate': latest_rate.buy_rate if latest_rate else None,
                'sell_rate': latest_rate.sell_rate if latest_rate else None,
                'daily_change': round(change, 4),
                'daily_change_percentage': round(change_percentage, 2),
                'is_today_rate': latest_rate == today_rate if latest_rate else False,
                'has_rate': latest_rate is not None,
                'is_published': is_today_published,  # 用于显示绿勾/时钟的状态
                'is_really_published': is_really_published,  # 真正的发布状态
                'is_edited_today': is_edited_today,
                'last_updated': latest_rate.updated_at.isoformat() if latest_rate and latest_rate.updated_at else None,
                'last_editor': latest_rate.created_by if latest_rate else None,
                'publisher_name': editor_name,
                'last_publish_time': latest_rate.updated_at.isoformat() if latest_rate and latest_rate.updated_at else None,
                # 添加批量保存相关字段
                'batch_saved': bool(getattr(latest_rate, 'batch_saved', 0)) if latest_rate else False,
                'batch_saved_time': getattr(latest_rate, 'batch_saved_time', None) if latest_rate else None,
                'batch_saved_by': getattr(latest_rate, 'batch_saved_by', None) if latest_rate else None
            }
            result.append(rate_data)

        # 只有在不限制发布状态时，才处理没有今日汇率的其他币种
        if not published_only:
            for currency in other_currencies:
                # 获取最近一次的汇率
                latest_rate = session.query(ExchangeRate).filter(
                    ExchangeRate.currency_id == currency.id,
                    ExchangeRate.branch_id == branch_id
                ).order_by(
                    ExchangeRate.rate_date.desc()
                ).first()

                # 获取昨天的汇率用于计算变化
                yesterday_rate = session.query(ExchangeRate).filter(
                    ExchangeRate.currency_id == currency.id,
                    ExchangeRate.branch_id == branch_id,
                    ExchangeRate.rate_date == yesterday
                ).first()

                # 计算变化率
                change = 0
                change_percentage = 0
                if yesterday_rate and latest_rate:
                    change = latest_rate.buy_rate - yesterday_rate.buy_rate
                    change_percentage = (change / yesterday_rate.buy_rate) * 100 if yesterday_rate.buy_rate else 0

                rate_data = {
                    'currency_id': currency.id,
                    'currency_code': currency.currency_code,
                    'currency_name': currency.currency_name,
                    'flag_code': currency.flag_code,
                    'custom_flag_filename': currency.custom_flag_filename,  # 添加自定义图标字段
                    'rate_date': latest_rate.rate_date.isoformat() if latest_rate else today.isoformat(),
                    'buy_rate': latest_rate.buy_rate if latest_rate else None,
                    'sell_rate': latest_rate.sell_rate if latest_rate else None,
                    'daily_change': round(change, 4),
                    'daily_change_percentage': round(change_percentage, 2),
                    'is_today_rate': False,  # 没有今日汇率
                    'has_rate': latest_rate is not None,
                    'is_published': False,  # 今日未保存
                    'is_really_published': False,  # 真正未发布
                    'is_edited_today': False,  # 今日未编辑
                    'last_updated': latest_rate.updated_at.isoformat() if latest_rate and latest_rate.updated_at else None,
                    'last_editor': latest_rate.created_by if latest_rate else None,
                    'publisher_name': None,  # 没有发布者
                    'last_publish_time': None  # 没有发布时间
                }
                result.append(rate_data)

        # 对最终结果进行排序，确保整体顺序正确
        # 1. 今日有汇率的货币按 sort_order 排序（已经有 sort_order 信息）
        # 2. 今日无汇率的货币按 currency_code 排序（放在最后）
        today_rates_result = [r for r in result if r.get('is_today_rate', False)]
        other_rates_result = [r for r in result if not r.get('is_today_rate', False)]
        
        # 对今日汇率按数组索引排序（因为已经按 sort_order 处理过了）
        # 对其他汇率按货币代码排序
        other_rates_result.sort(key=lambda x: x['currency_code'])
        
        # 合并结果：今日汇率在前，其他汇率在后
        final_result = today_rates_result + other_rates_result
        
        current_app.logger.info(f"[API] /rates/all - Found {len(final_result)} exchangeable currencies (published_only: {published_only})")
        current_app.logger.debug(f"[API] /rates/all - Today rates: {len(today_rates_result)}, Other rates: {len(other_rates_result)}")
        
        return jsonify({
            'success': True, 
            'rates': final_result,
            'last_update': datetime.now().isoformat(),
            'published_only': published_only
        })
    except Exception as e:
        current_app.logger.error(f"[API] /rates/all - Error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@rates_bp.route('/currencies', methods=['GET'])
@token_required
def get_supported_currencies(current_user):
    session = DatabaseService.get_session()
    try:
        currencies = session.query(Currency).all()
        result = []
        for c in currencies:
            # 检查币种是否在使用中（有汇率记录）
            is_in_use = session.query(ExchangeRate).filter_by(currency_id=c.id).first() is not None
            
            result.append({
                'id': c.id,
                'currency_code': c.currency_code,
                'currency_name': c.currency_name,
                'flag_code': c.flag_code,
                'symbol': c.symbol,
                'custom_flag_filename': c.custom_flag_filename,  # 【修复】添加自定义图标字段
                'is_in_use': is_in_use  # 【修复】添加使用状态字段
            })
        return jsonify({'success': True, 'currencies': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@rates_bp.route('/set_rate', methods=['POST'])
@token_required
@has_permission('rate_manage')
def set_rate(*args, **kwargs):
    # 从装饰器中获取current_user
    current_user = kwargs.get('current_user') or args[0]
    
    print(f"[后端调试] set_rate API被调用")
    print(f"[后端调试] 请求方法: {request.method}")
    print(f"[后端调试] 请求路径: {request.path}")
    print(f"[后端调试] Content-Type: {request.content_type}")
    
    data = request.json
    print(f"[后端调试] 接收到的原始数据: {data}")
    if not data or not all(k in data for k in ['currency_id', 'buy_rate', 'sell_rate']):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    # 添加调试信息
    print(f"[DEBUG] set_rate - 收到的数据: {data}")
    print(f"[DEBUG] set_rate - batch_saved: {data.get('batch_saved')}")
    print(f"[DEBUG] set_rate - is_published: {data.get('is_published')}")
    print(f"[DEBUG] set_rate - current_user: {current_user}")
    
    session = DatabaseService.get_session()
    try:
        # Check if currency exists
        currency = session.query(Currency).filter_by(id=data['currency_id']).first()
        if not currency:
            return jsonify({'success': False, 'message': 'Currency not found'}), 404
        
        # Check if rate exists for today
        today = date.today()
        rate = session.query(ExchangeRate).filter_by(
            currency_id=data['currency_id'],
            branch_id=current_user['branch_id'],
            rate_date=today
        ).first()
        
        if rate:
            # Update existing rate
            old_buy_rate = rate.buy_rate
            old_sell_rate = rate.sell_rate
            rate.buy_rate = data['buy_rate']
            rate.sell_rate = data['sell_rate']
            rate.updated_at = datetime.utcnow()
            
            # 处理批量保存相关字段
            if data.get('batch_saved'):
                print(f"[DEBUG] set_rate - 设置批量保存字段")
                rate.batch_saved = 1  # 使用1而不是True
                rate.batch_saved_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                rate.batch_saved_by = current_user.get('name', '未知用户')
                print(f"[DEBUG] set_rate - batch_saved设置为: {rate.batch_saved}")
                print(f"[DEBUG] set_rate - batch_saved_by设置为: {rate.batch_saved_by}")
            
            # 处理发布相关字段
            if data.get('is_published'):
                print(f"[DEBUG] set_rate - 设置发布相关字段")
                rate.is_published = 1  # 使用1而不是True
                rate.publisher_name = current_user.get('name', '未知用户')
                rate.last_publish_time = datetime.utcnow()
                print(f"[DEBUG] set_rate - is_published设置为: {rate.is_published}")
                print(f"[DEBUG] set_rate - publisher_name设置为: {rate.publisher_name}")
            
            action = f"Updated exchange rate for {currency.currency_code}"
            operation = "UPDATE_RATE"
            
            # 记录汇率更新日志 - 使用当前用户的语言设置
            user_language = current_user.get('language', 'zh-CN')
            multilingual_logger.log_rate_update(
                operator_id=current_user['id'],
                branch_id=current_user['branch_id'],
                currency_code=currency.currency_code,
                buy_rate=float(data['buy_rate']),
                sell_rate=float(data['sell_rate']),
                ip_address=request.remote_addr,
                language=user_language
            )
        else:
            # Create new rate
            now = datetime.utcnow()
            
            # 【新增】继承排序逻辑：获取最近一次的有效排序
            sort_order = 0  # 默认排序值
            try:
                # 查找最近一次有排序信息的汇率记录（按日期倒序）
                last_rate_with_sort = session.query(ExchangeRate).filter(
                    ExchangeRate.currency_id == data['currency_id'],
                    ExchangeRate.branch_id == current_user['branch_id'],
                    ExchangeRate.sort_order > 0  # 确保有排序信息
                ).order_by(ExchangeRate.rate_date.desc()).first()
                
                if last_rate_with_sort:
                    sort_order = last_rate_with_sort.sort_order
                    print(f"[DEBUG] set_rate - 继承排序: currency_id={data['currency_id']}, sort_order={sort_order}")
                else:
                    # 如果没有历史排序，使用currency_id作为默认排序
                    sort_order = data['currency_id']
                    print(f"[DEBUG] set_rate - 使用默认排序: currency_id={data['currency_id']}, sort_order={sort_order}")
            except Exception as sort_error:
                print(f"[DEBUG] set_rate - 获取排序信息失败: {sort_error}")
                sort_order = data['currency_id']  # 使用currency_id作为默认排序
            
            rate = ExchangeRate(
                currency_id=data['currency_id'],
                branch_id=current_user['branch_id'],
                rate_date=today,
                buy_rate=data['buy_rate'],
                sell_rate=data['sell_rate'],
                created_by=current_user['id'],
                created_at=now,
                updated_at=now,
                sort_order=sort_order  # 设置继承的排序值
            )
            
            # 处理批量保存相关字段
            if data.get('batch_saved'):
                print(f"[DEBUG] set_rate - 创建新记录时设置批量保存字段")
                rate.batch_saved = 1  # 使用1而不是True
                rate.batch_saved_time = now.strftime('%Y-%m-%d %H:%M:%S')
                rate.batch_saved_by = current_user.get('name', '未知用户')
                print(f"[DEBUG] set_rate - 新记录 batch_saved设置为: {rate.batch_saved}")
                print(f"[DEBUG] set_rate - 新记录 batch_saved_by设置为: {rate.batch_saved_by}")
            
            # 处理发布相关字段
            if data.get('is_published'):
                print(f"[DEBUG] set_rate - 创建新记录时设置发布相关字段")
                rate.is_published = 1  # 使用1而不是True
                rate.publisher_name = current_user.get('name', '未知用户')
                rate.last_publish_time = now
                print(f"[DEBUG] set_rate - 新记录 is_published设置为: {rate.is_published}")
                print(f"[DEBUG] set_rate - 新记录 publisher_name设置为: {rate.publisher_name}")
            
            session.add(rate)
            action = f"Set new exchange rate for {currency.currency_code}"
            operation = "CREATE_RATE"
        
        # 日志记录已通过multilingual_logger处理，无需重复记录
        
        # 在提交前检查字段值
        print(f"[DEBUG] set_rate - 提交前检查：batch_saved = {getattr(rate, 'batch_saved', 'NOT_SET')}")
        print(f"[DEBUG] set_rate - 提交前检查：is_published = {getattr(rate, 'is_published', 'NOT_SET')}")
        print(f"[DEBUG] set_rate - 提交前检查：batch_saved_by = {getattr(rate, 'batch_saved_by', 'NOT_SET')}")
        print(f"[DEBUG] set_rate - 提交前检查：publisher_name = {getattr(rate, 'publisher_name', 'NOT_SET')}")
        
        DatabaseService.commit_session(session)
        return jsonify({
            'success': True, 
            'message': 'Exchange rate updated successfully',
            'rate': {
                'id': rate.id,
                'currency_code': currency.currency_code,
                'currency_name': currency.currency_name,
                'buy_rate': rate.buy_rate,
                'sell_rate': rate.sell_rate,
                'updated_at': rate.updated_at.isoformat()
            }
        })
    
    except Exception as e:
        DatabaseService.rollback_session(session)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@rates_bp.route('/current', methods=['GET'])
@token_required
def get_current_rates(current_user):
    session = DatabaseService.get_session()
    try:
        today = date.today()
        branch_id = current_user['branch_id']
        
        # 获取published_only参数
        published_only = request.args.get('published_only', 'false').lower() == 'true'
        
        # 检查今日发布记录，获取已发布的币种ID
        published_currency_ids = set()
        publish_record = session.query(RatePublishRecord).filter(
            RatePublishRecord.branch_id == branch_id,
            RatePublishRecord.publish_date == today
        ).order_by(RatePublishRecord.publish_time.desc()).first()
        
        if publish_record:
            published_currency_ids = set(
                detail.currency_id for detail in 
                session.query(RatePublishDetail).filter(
                    RatePublishDetail.publish_record_id == publish_record.id
                ).all()
            )
        
        # Join with Currency to get currency details, order by sort_order
        rates = session.query(
            ExchangeRate, Currency
        ).join(
            Currency, ExchangeRate.currency_id == Currency.id
        ).filter(
            ExchangeRate.rate_date == today,
            ExchangeRate.branch_id == current_user['branch_id']
        ).order_by(ExchangeRate.sort_order.asc(), Currency.currency_code.asc()).all()
        
        result = []
        for rate, currency in rates:
            # 判断是否今日手动编辑过
            is_edited_today = False
            editor_name = None
            
            if rate.updated_at and rate.created_at:
                # 检查是否有编辑操作的痕迹
                time_diff = (rate.updated_at - rate.created_at).total_seconds()
                updated_today = rate.updated_at.date() == today
                created_today = rate.created_at.date() == today
                
                is_edited_today = (
                    (time_diff > 1) or  # 正常编辑情况
                    (updated_today and not created_today) or  # 跨日编辑
                    (updated_today and created_today and abs(time_diff) > 1)  # 今天的编辑
                )
            elif rate.updated_at:
                updated_date = rate.updated_at.date()
                is_edited_today = updated_date == today
                
            # 获取编辑者姓名
            if rate.created_by:
                print(f"[DEBUG] getCurrentRates - currency_id={currency.id}: created_by={rate.created_by}")
                from models.exchange_models import Operator
                editor = session.query(Operator).filter_by(id=rate.created_by).first()
                print(f"[DEBUG] getCurrentRates - currency_id={currency.id}: 查询到的editor={editor}")
                if editor:
                    print(f"[DEBUG] getCurrentRates - currency_id={currency.id}: editor.name={editor.name}")
                    editor_name = editor.name
                else:
                    print(f"[DEBUG] getCurrentRates - currency_id={currency.id}: 在operators表中未找到ID为{rate.created_by}的用户")
                    editor_name = '系统管理员'
            else:
                print(f"[DEBUG] getCurrentRates - currency_id={currency.id}: created_by为空")
                editor_name = '系统管理员'
            
            # 判断发布状态 - 按用户要求：网点=当前网点，发布日期=当前日期就是已发布
            is_really_published = currency.id in published_currency_ids
            
            if published_only:
                # 严格模式：能走到这里说明肯定在发布记录中
                is_today_published = True
            else:
                # 宽松模式：汇率管理页面用，优先检查真正的发布记录
                is_today_published = False
                if is_really_published:
                    # 方式1：如果在发布记录中，直接标记为已发布
                    is_today_published = True
                elif rate:
                    # 方式2：检查是否执行了批量保存且是今日保存
                    batch_saved_time_str = getattr(rate, 'batch_saved_time', None)
                    if (getattr(rate, 'batch_saved', 0) == 1 and 
                        batch_saved_time_str and
                        batch_saved_time_str.startswith(today.strftime('%Y-%m-%d'))):
                        is_today_published = True
                    # 方式3：如果没有批量保存标记，检查是否今日创建或更新（兼容原有逻辑）
                    elif getattr(rate, 'batch_saved', 0) == 0:
                        created_today = rate.created_at and rate.created_at.date() == today
                        updated_today = rate.updated_at and rate.updated_at.date() == today
                        is_today_published = created_today or updated_today
            
            result.append({
                'id': rate.id,
                'currency_id': currency.id,
                'currency_code': currency.currency_code,
                'currency_name': currency.currency_name,
                'flag_code': currency.flag_code,
                'custom_flag_filename': currency.custom_flag_filename,  # 添加自定义图标字段
                'buy_rate': rate.buy_rate,
                'sell_rate': rate.sell_rate,
                'updated_at': rate.updated_at.isoformat() if rate.updated_at else None,
                'is_edited_today': is_edited_today,  # 添加今日编辑状态
                'publisher_name': editor_name,  # 添加编辑者姓名
                'last_publish_time': rate.updated_at.isoformat() if rate.updated_at else None,  # 添加发布时间
                'rate_date': rate.rate_date.isoformat() if rate.rate_date else None,
                # 添加发布状态相关字段
                'is_published': is_today_published,  # 用于显示绿勾/时钟的状态
                'is_really_published': is_really_published,  # 真正的发布状态
                # 添加批量保存相关字段
                'batch_saved': bool(getattr(rate, 'batch_saved', 0)),
                'batch_saved_time': getattr(rate, 'batch_saved_time', None),
                'batch_saved_by': getattr(rate, 'batch_saved_by', None)
            })
        
        return jsonify({
            'success': True,
            'rates': result,
            'date': today.isoformat()
        })
    
    except Exception as e:
        print(f"[ERROR] /api/rates/current failed: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@rates_bp.route('/currency/<int:currency_id>/history', methods=['GET'])
@token_required
def get_currency_rate_history(current_user, currency_id):
    session = DatabaseService.get_session()
    try:
        # 获取查询参数
        days = request.args.get('days', 7, type=int)
        branch_id = current_user['branch_id']
        
        # 获取该币种最新的汇率日期作为结束日期
        latest_rate = session.query(ExchangeRate).filter(
            ExchangeRate.currency_id == currency_id,
            ExchangeRate.branch_id == branch_id
        ).order_by(ExchangeRate.rate_date.desc()).first()
        
        if not latest_rate:
            print(f"No rates found for currency {currency_id} in branch {branch_id}")
            return jsonify({
                'success': True,
                'history': []
            })
            
        end_date = latest_rate.rate_date
        start_date = end_date - timedelta(days=days)

        print(f"Fetching rate history for currency {currency_id} in branch {branch_id} from {start_date} to {end_date}")

        # 查询指定币种的历史汇率
        rates = session.query(
            ExchangeRate,
            Currency
        ).join(
            Currency,
            ExchangeRate.currency_id == Currency.id
        ).filter(
            ExchangeRate.currency_id == currency_id,
            ExchangeRate.branch_id == branch_id,
            ExchangeRate.rate_date >= start_date,
            ExchangeRate.rate_date <= end_date
        ).order_by(
            ExchangeRate.rate_date.asc()
        ).all()

        print(f"Found {len(rates)} rate records")

        result = []
        for rate, currency in rates:
            rate_data = {
                'date': rate.rate_date.isoformat(),
                'buy_rate': float(rate.buy_rate),
                'sell_rate': float(rate.sell_rate),
                'currency_code': currency.currency_code
            }
            result.append(rate_data)

        print(f"Returning {len(result)} history records")
        return jsonify({
            'success': True,
            'history': result
        })

    except Exception as e:
        print(f"Error in get_currency_rate_history: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@rates_bp.route('/publish_daily_rates', methods=['POST'])
@token_required
@has_permission('rate_manage')
def publish_daily_rates(*args):
    """
    选择可兑换外币并初始化今日汇率列表。
    如果汇率未手动设置，则使用前一天的汇率作为初始值。
    注意：这只是初始化，真正的发布需要通过"应用发布"功能。
    """
    current_user = args[0] if args else None
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401

    data = request.json or {}
    target_date = data.get('target_date')
    
    if target_date:
        try:
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format'}), 400
    else:
        target_date = date.today()
    
    session = DatabaseService.get_session()
    try:
        # Get branch information
        branch = session.query(Branch).filter_by(id=current_user['branch_id']).first()
        if not branch:
            return jsonify({
                'success': False,
                'message': 'Branch not found'
            }), 404

        # Get all active currencies except base currency
        currencies = session.query(Currency).filter(
            Currency.id != branch.base_currency_id
        ).all()
        
        published_rates = []
        for currency in currencies:
            # Check if rate already exists for target date and branch
            existing_rate = session.query(ExchangeRate).filter(
                ExchangeRate.currency_id == currency.id,
                ExchangeRate.branch_id == current_user['branch_id'],
                ExchangeRate.rate_date == target_date
            ).first()
            
            if existing_rate:
                published_rates.append({
                    'currency_code': currency.currency_code,
                    'buy_rate': existing_rate.buy_rate,
                    'sell_rate': existing_rate.sell_rate,
                    'status': 'already_exists'
                })
                continue
            
            # Get previous day's rate for the same branch
            previous_day = target_date - timedelta(days=1)
            previous_rate = session.query(ExchangeRate).filter(
                ExchangeRate.currency_id == currency.id,
                ExchangeRate.branch_id == current_user['branch_id'],
                ExchangeRate.rate_date == previous_day
            ).first()
            
            if not previous_rate:
                published_rates.append({
                    'currency_code': currency.currency_code,
                    'status': 'skipped_no_previous_rate'
                })
                continue
            
            # Create new rate based on previous day's rate
            now = datetime.utcnow()
            
            # 【新增】继承排序逻辑：从前一天汇率记录继承排序
            sort_order = previous_rate.sort_order if previous_rate.sort_order else currency.id
            
            new_rate = ExchangeRate(
                currency_id=currency.id,
                branch_id=current_user['branch_id'],
                rate_date=target_date,
                buy_rate=previous_rate.buy_rate,
                sell_rate=previous_rate.sell_rate,
                created_by=current_user['id'],
                created_at=now,
                updated_at=now,  # 发布时created_at = updated_at，说明未手动编辑
                sort_order=sort_order  # 继承前一天的排序
            )
            session.add(new_rate)
            
            published_rates.append({
                'currency_code': currency.currency_code,
                'buy_rate': new_rate.buy_rate,
                'sell_rate': new_rate.sell_rate,
                'status': 'published_from_previous'
            })
            
            # Log the action
            log = SystemLog(
                operation='PUBLISH_DAILY_RATE',
                operator_id=current_user['id'],
                log_type='rate_publish',
                action=f"Auto-published rate for {currency.currency_code}",
                details=f"Branch: {branch.branch_name}, Date: {target_date}, Buy rate: {new_rate.buy_rate}, Sell rate: {new_rate.sell_rate}",
                ip_address=request.remote_addr
            )
            session.add(log)
        
        DatabaseService.commit_session(session)
        
        return jsonify({
            'success': True,
            'message': f'已初始化 {len(published_rates)} 种外币的汇率列表，请编辑汇率后点击"应用发布"',
            'branch': branch.branch_name,
            'date': target_date.isoformat(),
            'published_rates': published_rates
        })
    
    except Exception as e:
        DatabaseService.rollback_session(session)
        print(f"Error in publish_daily_rates: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@rates_bp.route('/add_currency', methods=['POST'])
@token_required
@has_permission('rate_manage')
def add_currency(*args, **kwargs):
    """Add a new currency to the system"""
    # 从装饰器中获取current_user
    current_user = kwargs.get('current_user') or args[0]
    
    data = request.json
    required_fields = ['currency_code', 'currency_name', 'buy_rate', 'sell_rate']
    
    print(f"Adding new currency. Data received: {data}")
    print(f"Current user: {current_user}")
    print(f"[DEBUG] custom_flag_filename in request: {data.get('custom_flag_filename')}")
    print(f"[DEBUG] currency_name in request: {data.get('currency_name')}")
    
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'}), 400
        
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({
            'success': False, 
            'message': f'Missing required fields: {", ".join(missing_fields)}'
        }), 400
    
    try:
        buy_rate = float(data['buy_rate'])
        sell_rate = float(data['sell_rate'])
        if buy_rate <= 0 or sell_rate <= 0:
            return jsonify({
                'success': False,
                'message': 'Buy rate and sell rate must be positive numbers'
            }), 400
    except (ValueError, TypeError):
        return jsonify({
            'success': False,
            'message': 'Invalid buy_rate or sell_rate format'
        }), 400
    
    session = DatabaseService.get_session()
    try:
        # 1. 检查是否是本币
        branch = session.query(Branch).filter_by(id=current_user['branch_id']).first()
        if not branch:
            return jsonify({'success': False, 'message': '找不到网点信息'}), 404
            
        base_currency = session.query(Currency).filter_by(id=branch.base_currency_id).first()
        if base_currency and base_currency.currency_code == data['currency_code'].upper():
            return jsonify({
                'success': False,
                'message': f"不能添加本币 {data['currency_code']} 作为外币"
            }), 400

        # 2. 检查今日是否已有该币种的汇率记录
        existing_rate = session.query(ExchangeRate).filter(
            ExchangeRate.currency_id == session.query(Currency.id).filter(
                Currency.currency_code == data['currency_code'].upper()
            ).scalar(),
            ExchangeRate.branch_id == current_user['branch_id'],
            ExchangeRate.rate_date == date.today()
        ).first()

        if existing_rate:
            return jsonify({
                'success': False, 
                'message': f"币种 {data['currency_code']} 今日已有汇率记录"
            }), 400
        
        # 3. 检查是否在CurrencyTemplate中存在（用于自定义币种）
        currency_template = session.query(CurrencyTemplate).filter_by(
            currency_code=data['currency_code'].upper(),
            is_active=True
        ).first()
        
        # 如果是从CurrencyTemplate添加的币种，使用模板中的信息
        if currency_template:
            print(f"[DEBUG] 从CurrencyTemplate添加币种: {currency_template.currency_code}")
            print(f"[DEBUG] 模板中的currency_name: {currency_template.currency_name}")
            print(f"[DEBUG] 模板中的custom_flag_filename: {currency_template.custom_flag_filename}")
            currency_name = currency_template.currency_name
            country = currency_template.country
            flag_code = currency_template.flag_code
            custom_flag_filename = currency_template.custom_flag_filename
        else:
            # 使用请求中的数据
            print(f"[DEBUG] 使用请求中的数据")
            currency_name = data['currency_name']
            country = data.get('country')
            flag_code = data.get('flag_code', '').upper()
            custom_flag_filename = data.get('custom_flag_filename')
        
        # 4. 检查币种是否已存在于Currency表中，如果存在则使用现有记录，否则创建新记录
        existing_currency = session.query(Currency).filter_by(
            currency_code=data['currency_code'].upper()
        ).first()
        
        if existing_currency:
            # 使用现有币种记录
            new_currency = existing_currency
            print(f"[DEBUG] 使用现有Currency记录: {existing_currency.currency_code}")
        else:
            # 创建新币种记录
            new_currency = Currency(
                currency_code=data['currency_code'].upper(),
                currency_name=currency_name,
                country=country,
                flag_code=flag_code,
                custom_flag_filename=custom_flag_filename,
                created_at=datetime.utcnow()
            )
            session.add(new_currency)
            session.flush()
            print(f"[DEBUG] 创建新Currency记录: {new_currency.currency_code}")
        
        # 处理网点币种关联 - 使用新的BranchCurrency表
        branch_currency = session.query(BranchCurrency).filter_by(
            branch_id=current_user['branch_id'],
            currency_id=new_currency.id
        ).first()
        
        if branch_currency:
            # 如果币种被禁用，重新启用它
            if not branch_currency.is_enabled:
                branch_currency.is_enabled = True
                branch_currency.updated_at = datetime.utcnow()
                print(f"[DEBUG] 重新启用被删除的币种: {new_currency.currency_code}")
        else:
            # 创建启用记录
            branch_currency = BranchCurrency(
                branch_id=current_user['branch_id'],
                currency_id=new_currency.id,
                is_enabled=True
            )
            session.add(branch_currency)
            print(f"[DEBUG] 创建新的网点币种关联: {new_currency.currency_code}")
        
        print(f"[DEBUG] 创建的Currency对象:")
        print(f"[DEBUG] - currency_code: {new_currency.currency_code}")
        print(f"[DEBUG] - currency_name: {new_currency.currency_name}")
        print(f"[DEBUG] - custom_flag_filename: {new_currency.custom_flag_filename}")
        
        # 4. 添加初始汇率
        today = date.today()
        
        # 【新增】为新币种设置排序：获取当前最大排序值并加1
        try:
            max_sort_order = session.query(ExchangeRate).filter(
                ExchangeRate.branch_id == current_user['branch_id'],
                ExchangeRate.rate_date == today
            ).with_entities(func.max(ExchangeRate.sort_order)).scalar()
            
            sort_order = (max_sort_order or 0) + 1
            print(f"[DEBUG] add_currency - 新币种排序: currency_id={new_currency.id}, sort_order={sort_order}")
        except Exception as sort_error:
            print(f"[DEBUG] add_currency - 获取排序信息失败: {sort_error}")
            sort_order = new_currency.id  # 使用currency_id作为默认排序
        
        new_rate = ExchangeRate(
            currency_id=new_currency.id,
            branch_id=current_user['branch_id'],
            rate_date=today,
            buy_rate=buy_rate,
            sell_rate=sell_rate,
            created_by=current_user['id'],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            sort_order=sort_order  # 设置排序值
        )
        session.add(new_rate)
        
        # 5. 记录操作日志
        log = SystemLog(
            operation='ADD_CURRENCY',
            operator_id=current_user['id'],
            log_type='currency_management',
            action=f"Added new currency {new_currency.currency_code}",
            details=f"Currency: {new_currency.currency_code}, Initial buy rate: {buy_rate}, Initial sell rate: {sell_rate}",
            ip_address=request.remote_addr
        )
        session.add(log)
        
        DatabaseService.commit_session(session)
        print(f"Successfully added new currency: {new_currency.currency_code}")
        
        return jsonify({
            'success': True,
            'message': '币种添加成功',
            'currency': {
                'id': new_currency.id,
                'currency_code': new_currency.currency_code,
                'currency_name': new_currency.currency_name,
                'flag_code': new_currency.flag_code
            }
        })
    
    except Exception as e:
        DatabaseService.rollback_session(session)
        print(f"Error adding currency: {str(e)}")
        return jsonify({'success': False, 'message': f'添加币种时出错: {str(e)}'}), 500
    finally:
        DatabaseService.close_session(session)

@rates_bp.route('/currency_templates', methods=['GET'])
@token_required
def get_currency_templates(current_user):
    """获取所有可用的币种模板，可选择排除已在今日汇率列表中的币种"""
    session = DatabaseService.get_session()
    try:
        # 获取要排除的币种代码列表
        exclude_currency_codes = request.args.get('exclude_currency_codes', '')
        exclude_codes = []
        if exclude_currency_codes:
            exclude_codes = [code.strip().upper() for code in exclude_currency_codes.split(',') if code.strip()]
        
        # 构建查询
        query = session.query(CurrencyTemplate).filter_by(is_active=True)
        
        # 如果有排除的币种代码，添加过滤条件
        if exclude_codes:
            query = query.filter(~CurrencyTemplate.currency_code.in_(exclude_codes))
            print(f"[get_currency_templates] 排除币种代码: {exclude_codes}")
        
        templates = query.all()
        result = [template.to_dict() for template in templates]
        
        # 添加被删除的币种（在当前网点被禁用的币种）
        branch_id = current_user['branch_id']
        disabled_currencies = session.query(Currency).join(
            BranchCurrency
        ).filter(
            BranchCurrency.branch_id == branch_id,
            BranchCurrency.is_enabled == False
        ).all()
        
        for currency in disabled_currencies:
            # 检查是否在排除列表中
            if currency.currency_code not in exclude_codes:
                # 创建币种模板格式的数据
                template_data = {
                    'id': currency.id,
                    'currency_code': currency.currency_code,
                    'currency_name': currency.currency_name,
                    'country': currency.country or currency.currency_name,
                    'flag_code': currency.flag_code or currency.currency_code.lower(),
                    'symbol': currency.symbol or currency.currency_code,
                    'description': f'被删除的币种 - {currency.currency_name}',
                    'custom_flag_filename': currency.custom_flag_filename,
                    'is_active': True
                }
                result.append(template_data)
        
        print(f"[get_currency_templates] 返回 {len(result)} 个币种模板（包括 {len(disabled_currencies)} 个被删除的币种）")
        if exclude_codes:
            print(f"[get_currency_templates] 已排除 {len(exclude_codes)} 个已在今日汇率列表中的币种")
        
        return jsonify(result)
    except Exception as e:
        print(f"Error in get_currency_templates: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@rates_bp.route('/available_currencies', methods=['GET'])
@token_required
def get_available_currencies(current_user):
    session = DatabaseService.get_session()
    try:
        branch_id = current_user['branch_id']
        
        # 新增参数：是否只返回当日发布的汇率
        published_only = request.args.get('published_only', 'false').lower() == 'true'

        # 获取网点信息和本币
        branch = session.query(Branch).filter_by(id=branch_id).first()
        if not branch:
            return jsonify({'success': False, 'message': '网点信息不存在'}), 404
            
        if not branch.base_currency_id:
            return jsonify({'success': False, 'message': '网点未设置本币'}), 404
            
        # 验证本币是否存在
        base_currency = session.query(Currency).filter_by(id=branch.base_currency_id).first()
        if not base_currency:
            return jsonify({'success': False, 'message': '网点本币信息不存在'}), 404

        if published_only:
            # 只返回今日最新发布的币种（包括标准汇率和面值汇率发布记录）
            today = date.today()

            # 查询今日的最新发布记录
            publish_record = session.query(RatePublishRecord).filter(
                RatePublishRecord.branch_id == branch_id,
                RatePublishRecord.publish_date == today
            ).order_by(RatePublishRecord.publish_time.desc()).first()

            if publish_record:
                # 获取标准汇率发布的币种ID列表
                published_details = session.query(RatePublishDetail).filter(
                    RatePublishDetail.publish_record_id == publish_record.id
                ).all()

                standard_currency_ids = [detail.currency_id for detail in published_details]

                # 获取面值汇率发布的币种ID列表
                denomination_details = session.query(DenominationPublishDetail).filter(
                    DenominationPublishDetail.publish_record_id == publish_record.id
                ).all()

                denomination_currency_ids = [detail.currency_id for detail in denomination_details]

                # 合并所有已发布的币种ID（去重）
                all_published_currency_ids = list(set(standard_currency_ids + denomination_currency_ids))

                currencies = session.query(Currency).filter(
                    Currency.id != branch.base_currency_id,  # 排除本币
                    Currency.id.in_(all_published_currency_ids)
                ).all()

                print(f"[available_currencies] published_only=true, 发布记录ID: {publish_record.id}")
                print(f"[available_currencies] 标准汇率发布币种ID: {standard_currency_ids}")
                print(f"[available_currencies] 面值汇率发布币种ID: {denomination_currency_ids}")
                print(f"[available_currencies] 合并后的币种ID列表: {all_published_currency_ids}")
                print(f"[available_currencies] 返回今日最新发布的{len(currencies)}种外币")
            else:
                # 没有发布记录，返回空列表
                currencies = []
                print(f"[available_currencies] published_only=true, 今日无发布记录，返回0种外币")
        else:
            # 查询所有非本币的币种（排除被禁用的币种）
            # 使用新的BranchCurrency表来检查币种是否在当前网点被禁用
            disabled_currency_ids = session.query(BranchCurrency.currency_id).filter(
                BranchCurrency.branch_id == branch_id,
                BranchCurrency.is_enabled == False
            ).all()
            
            disabled_currency_id_list = [row[0] for row in disabled_currency_ids]
            
            currencies = session.query(Currency).filter(
                Currency.id != branch.base_currency_id,  # 排除本币
                ~Currency.id.in_(disabled_currency_id_list)  # 排除被禁用的币种
            ).all()
            print(f"[available_currencies] published_only=false, 返回所有{len(currencies)}种外币（排除被禁用的币种）")

        # 添加多语言币种名称映射
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

        result = []
        for currency in currencies:
            currency_data = {
                'id': currency.id,
                'currency_code': currency.currency_code,
                'currency_name': currency.currency_name,
                'flag_code': currency.flag_code,
                'custom_flag_filename': currency.custom_flag_filename,  # 添加自定义图标字段
                'symbol': currency.symbol
            }
            
            # 添加多语言名称
            if currency.currency_code in currency_names_map:
                currency_data['currency_names'] = currency_names_map[currency.currency_code]
            else:
                # 对于新币种，生成基础的多语言支持
                currency_data['currency_names'] = {
                    'zh': currency.currency_name,  # 使用数据库中的中文名称
                    'en': f"{currency.currency_code} ({currency.currency_name})",  # 英文显示币种代码+中文名
                    'th': f"{currency.currency_code} ({currency.currency_name})"   # 泰文显示币种代码+中文名
                }
            
            result.append(currency_data)

        return jsonify({'success': True, 'currencies': result})
    except Exception as e:
        print(f"Error in get_available_currencies: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@rates_bp.route('/currencies/code/<currency_code>', methods=['GET'])
@token_required
def get_currency_by_code(current_user, currency_code):
    """根据币种代码获取币种信息"""
    session = DatabaseService.get_session()
    try:
        currency = session.query(Currency).filter_by(
            currency_code=currency_code.upper()
        ).first()
        
        if currency:
            return jsonify({
                'success': True,
                'currency': {
                    'id': currency.id,
                    'currency_code': currency.currency_code,
                    'currency_name': currency.currency_name,
                    'flag_code': currency.flag_code,
                    'symbol': currency.symbol
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': f'未找到币种代码为 {currency_code} 的币种'
            }), 404
            
    except Exception as e:
        print(f"Error in get_currency_by_code: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@rates_bp.route('/currencies/<currency_code>', methods=['DELETE'])
@token_required
@has_permission('rate_manage')
def delete_currency(current_user, currency_code):
    """从当前网点删除币种（删除汇率记录和币种本身）"""
    session = DatabaseService.get_session()
    try:
        branch_id = current_user['branch_id']
        
        # 检查币种是否存在
        currency = session.query(Currency).filter_by(currency_code=currency_code.upper()).first()
        if not currency:
            return jsonify({'success': False, 'message': f'币种 {currency_code} 不存在'}), 404
        
        # 检查是否为本币
        branch = session.query(Branch).filter_by(id=branch_id).first()
        if branch and branch.base_currency_id == currency.id:
            return jsonify({'success': False, 'message': '不能删除本币'}), 400
        
        # 删除当前网点的汇率记录
        deleted_rates_count = session.query(ExchangeRate).filter_by(
            currency_id=currency.id,
            branch_id=branch_id
        ).delete()
        
        # 删除相关的汇率发布详情记录
        deleted_publish_details_count = session.query(RatePublishDetail).filter_by(
            currency_id=currency.id
        ).delete()
        
        # 删除余额报警设置（如果存在）
        deleted_alerts_count = session.query(BranchBalanceAlert).filter_by(
            currency_id=currency.id,
            branch_id=branch_id
        ).delete()
        
        # 检查是否有历史交易记录
        has_transactions = session.query(ExchangeTransaction).filter_by(
            currency_id=currency.id
        ).first() is not None
        
        # 处理网点币种关联 - 使用新的BranchCurrency表
        print(f"[DEBUG] 开始处理币种 {currency_code} 的网点关联")
        branch_currency = session.query(BranchCurrency).filter_by(
            branch_id=branch_id,
            currency_id=currency.id
            ).first()
            
        print(f"[DEBUG] 币种 {currency_code} 的BranchCurrency记录: {branch_currency}")
        
        if branch_currency:
            # 更新为禁用状态
            print(f"[DEBUG] 更新币种 {currency_code} 为禁用状态，当前状态: {branch_currency.is_enabled}")
            branch_currency.is_enabled = False
            branch_currency.updated_at = datetime.utcnow()
            deleted_currency = False  # 没有删除币种本身
            print(f"[DEBUG] 更新后状态: {branch_currency.is_enabled}")
        else:
            # 创建禁用记录
            print(f"[DEBUG] 创建币种 {currency_code} 的禁用记录")
            branch_currency = BranchCurrency(
                branch_id=branch_id,
                currency_id=currency.id,
                is_enabled=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(branch_currency)
            deleted_currency = False  # 没有删除币种本身
            print(f"[DEBUG] 创建禁用记录完成")
        
        # 记录操作日志
        log = SystemLog(
            operation='REMOVE_CURRENCY_FROM_BRANCH',
            operator_id=current_user['id'],
            log_type='currency_management',
            action=f"Removed currency {currency_code} from branch",
            details=f"Currency: {currency_code}, Branch ID: {branch_id}, Deleted rate records: {deleted_rates_count}, Deleted publish details: {deleted_publish_details_count}, Deleted alerts: {deleted_alerts_count}, Deleted currency: {deleted_currency}",
            ip_address=request.remote_addr
        )
        session.add(log)
        
        DatabaseService.commit_session(session)
        
        message = f'币种 {currency_code} 已从当前网点移除（删除了 {deleted_rates_count} 条汇率记录，{deleted_publish_details_count} 条发布详情记录，{deleted_alerts_count} 条报警设置'
        if deleted_currency:
            message += '，并删除了币种本身'
        elif has_transactions:
            message += f'，但保留了币种本身（因为有 {session.query(ExchangeTransaction).filter_by(currency_id=currency.id).count()} 条历史交易记录）'
        message += '）'
        
        return jsonify({
            'success': True, 
            'message': message
        })
        
    except Exception as e:
        DatabaseService.rollback_session(session)
        print(f"Error in delete_currency: {str(e)}")
        return jsonify({'success': False, 'message': f'删除币种失败: {str(e)}'}), 500
    finally:
        DatabaseService.close_session(session)

@rates_bp.route('/last_rate/<currency_code>', methods=['GET'])
@token_required
@has_permission('rate_manage')
def get_last_rate(current_user, currency_code):
    """获取指定币种最近一次的有效汇率"""
    session = DatabaseService.get_session()
    try:
        branch_id = current_user['branch_id']
        
        # 检查币种是否存在
        currency = session.query(Currency).filter_by(currency_code=currency_code.upper()).first()
        if not currency:
            return jsonify({'success': False, 'message': f'币种 {currency_code} 不存在'}), 404
        
        # 查询最近一次的有效汇率记录
        last_rate = session.query(ExchangeRate).filter(
            ExchangeRate.currency_id == currency.id,
            ExchangeRate.branch_id == branch_id,
            ExchangeRate.buy_rate > 0,  # 确保汇率有效
            ExchangeRate.sell_rate > 0
        ).order_by(ExchangeRate.rate_date.desc(), ExchangeRate.created_at.desc()).first()
        
        if last_rate:
            return jsonify({
                'success': True,
                'last_rate': {
                    'buy_rate': float(last_rate.buy_rate),
                    'sell_rate': float(last_rate.sell_rate),
                    'rate_date': last_rate.rate_date.strftime('%Y-%m-%d'),
                    'created_at': last_rate.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': f'币种 {currency_code} 没有找到有效的历史汇率记录'
            }), 404
            
    except Exception as e:
        print(f"Error in get_last_rate: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)

@rates_bp.route('/last_rates_all', methods=['GET'])
@token_required
@has_permission('rate_manage')
def get_last_rates_all(current_user):
    """获取所有币种最近一次的有效汇率"""
    session = DatabaseService.get_session()
    try:
        branch_id = current_user['branch_id']
        
        # 获取所有支持的币种
        currencies = session.query(Currency).all()
        result = {}
        
        for currency in currencies:
            # 查询最近一次的有效汇率记录
            last_rate = session.query(ExchangeRate).filter(
                ExchangeRate.currency_id == currency.id,
                ExchangeRate.branch_id == branch_id,
                ExchangeRate.buy_rate > 0,  # 确保汇率有效
                ExchangeRate.sell_rate > 0
            ).order_by(ExchangeRate.rate_date.desc(), ExchangeRate.created_at.desc()).first()
            
            if last_rate:
                result[currency.currency_code] = {
                    'buy_rate': float(last_rate.buy_rate),
                    'sell_rate': float(last_rate.sell_rate),
                    'rate_date': last_rate.rate_date.strftime('%Y-%m-%d'),
                    'created_at': last_rate.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
        
        return jsonify({
            'success': True,
            'last_rates': result,
            'total_currencies': len(currencies),
            'found_rates': len(result)
        })
            
    except Exception as e:
        print(f"Error in get_last_rates_all: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        DatabaseService.close_session(session)
