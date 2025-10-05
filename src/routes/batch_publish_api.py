from flask import Blueprint, request, jsonify
from datetime import datetime
import secrets
import logging
from services.db_service import DatabaseService
from models.exchange_models import RatePublishRecord, DenominationPublishDetail, Currency, Branch
from services.auth_service import token_required, has_permission

# 创建批次发布API的Blueprint
batch_publish_bp = Blueprint('batch_publish', __name__, url_prefix='/api/dashboard')

logger = logging.getLogger(__name__)

@batch_publish_bp.route('/publish-batch-denomination-rates', methods=['POST'])
@token_required
@has_permission('rate_manage')
def publish_batch_denomination_rates(current_user):
    """发布批次面值汇率到机顶盒显示（方案1：使用批次ID管理）"""
    data = request.get_json()
    
    if not data or 'currencies' not in data:
        return jsonify({'success': False, 'message': '缺少必要参数'}), 400
    
    session = DatabaseService.get_session()
    try:
        # 🔧 方案1：生成批次ID
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{current_user['branch_id']}"
        print(f"[批次发布] 生成批次ID: {batch_id}")
        
        # 获取显示配置
        theme = data.get('theme', 'light')
        language = data.get('language', 'zh')
        items_per_page = data.get('items_per_page', 20)
        refresh_interval = data.get('refresh_interval', 3600)
        notes = data.get('notes', '')
        
        # 验证刷新间隔
        if not isinstance(refresh_interval, int) or refresh_interval < 5 or refresh_interval > 86400:
            print(f"[批次发布] refresh_interval 验证失败，使用默认值3600")
            refresh_interval = 3600
        
        # 🔧 方案1：清理该分支的旧批次记录
        today = datetime.now().date()
        print(f"[批次发布] 清理分支 {current_user['branch_id']} 的旧批次记录")
        
        # 删除旧的批次记录
        old_batches = session.query(RatePublishRecord).filter_by(
            branch_id=current_user['branch_id']
        ).filter(
            RatePublishRecord.notes.like('%批次发布%')
        ).all()
        
        for old_batch in old_batches:
            # 删除相关的面值汇率详情
            session.query(DenominationPublishDetail).filter_by(
                publish_record_id=old_batch.id
            ).delete()
            # 删除发布记录
            session.delete(old_batch)
            print(f"[批次发布] 删除旧批次记录: {old_batch.access_token[:8]}...")
        
        # 处理每个币种的面值汇率
        batch_currency_tokens = []  # 存储每个币种的Token
        all_denomination_rates = []  # 存储所有面值汇率数据
        total_denominations = 0
        
        for currency_data in data['currencies']:
            currency_id = currency_data['currency_id']
            denomination_rates = currency_data['denomination_rates']
            
            # 获取币种信息
            currency = session.query(Currency).filter_by(id=currency_id).first()
            if not currency:
                print(f"[批次发布] 币种不存在: {currency_id}")
                continue
            
            # 验证面值汇率数据
            valid_denominations = []
            for rate_data in denomination_rates:
                if not all(key in rate_data for key in ['denomination_id', 'buy_rate', 'sell_rate']):
                    continue
                    
                try:
                    buy_rate = float(rate_data['buy_rate'])
                    sell_rate = float(rate_data['sell_rate'])
                    if buy_rate <= 0 or sell_rate <= 0:
                        continue
                except (ValueError, TypeError):
                    continue
                
                # 获取面值信息（简化处理，直接使用传入的数据）
                denomination = {
                    'id': rate_data['denomination_id'],
                    'denomination_value': rate_data.get('denomination_value', 0),
                    'denomination_type': rate_data.get('denomination_type', 'bill')
                }
                
                if denomination:
                    valid_denominations.append({
                        'denomination_id': denomination['id'],
                        'denomination_value': denomination['denomination_value'],
                        'denomination_type': denomination['denomination_type'],
                        'buy_rate': buy_rate,
                        'sell_rate': sell_rate
                    })
            
            if not valid_denominations:
                print(f"[批次发布] 币种 {currency.currency_code} 没有有效的面值汇率")
                continue
            
            # 🔧 方案1：为每个币种生成独立的Token
            currency_token = f"{batch_id}_{currency.currency_code}_{len(valid_denominations)}"
            print(f"[批次发布] 币种 {currency.currency_code} 生成Token: {currency_token}")
            
            # 存储币种Token信息
            batch_currency_tokens.append({
                'currency_id': currency_id,
                'currency_code': currency.currency_code,
                'access_token': currency_token,
                'denomination_count': len(valid_denominations)
            })
            
            # 构建面值汇率数据
            for denom_data in valid_denominations:
                all_denomination_rates.append({
                    'currency_id': currency_id,
                    'currency_code': currency.currency_code,
                    'currency_name': currency.currency_name,
                    'flag_code': currency.flag_code,
                    'custom_flag_filename': currency.custom_flag_filename,
                    'denomination_id': denom_data['denomination_id'],
                    'denomination_value': denom_data['denomination_value'],
                    'denomination_type': denom_data['denomination_type'],
                    'buy_rate': denom_data['buy_rate'],
                    'sell_rate': denom_data['sell_rate']
                })
            
            total_denominations += len(valid_denominations)
        
        if not all_denomination_rates:
            return jsonify({'success': False, 'message': '没有有效的面值汇率数据'}), 400
        
        # 🔧 方案1：生成批次主Token（用于机顶盒URL）
        batch_main_token = f"{batch_id}_main"
        publish_time = datetime.now()
        
        # 构建批次数据
        batch_data = {
            'batch_id': batch_id,
            'batch_main_token': batch_main_token,
            'currency_tokens': batch_currency_tokens,
            'branch': {
                'id': current_user['branch_id'],
                'name': current_user.get('branch_name', '未知网点'),
                'code': current_user.get('branch_code', 'Unknown')
            },
            'denomination_rates': all_denomination_rates,
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
        
        # 开始事务处理
        try:
            # 🔧 方案1：保存批次主记录
            publish_record = RatePublishRecord(
                branch_id=current_user['branch_id'],
                publisher_id=current_user['id'],
                publisher_name=current_user.get('name', '未知用户'),
                publish_date=publish_time.date(),
                publish_time=publish_time,
                access_token=batch_main_token,
                publish_theme=theme,
                total_currencies=len(batch_currency_tokens),
                notes=f'批次发布|batch_id:{batch_id}|theme:{theme}|lang:{language}|page:{items_per_page}|refresh:{refresh_interval}|notes:{notes}'
            )
            session.add(publish_record)
            session.flush()  # 获取ID
            
            # 保存面值汇率发布详情
            for detail_data in all_denomination_rates:
                detail = DenominationPublishDetail(
                    publish_record_id=publish_record.id,
                    currency_id=detail_data['currency_id'],
                    denomination_id=detail_data['denomination_id'],
                    denomination_value=detail_data['denomination_value'],
                    denomination_type=detail_data['denomination_type'],
                    buy_rate=detail_data['buy_rate'],
                    sell_rate=detail_data['sell_rate']
                )
                session.add(detail)
            
            # 提交数据库事务
            session.commit()
            
            # 数据库操作成功
            print(f"[批次发布] 批次数据已保存到数据库: {batch_main_token}")
            
            logger.info(f"批次面值汇率发布成功: 批次ID={batch_id}, 币种数={len(batch_currency_tokens)}, 总面值数={total_denominations}")
            
            return jsonify({
                'success': True,
                'message': '批次面值汇率发布成功',
                'data': {
                    'batch_id': batch_id,
                    'batch_main_token': batch_main_token,
                    'currency_tokens': batch_currency_tokens,
                    'display_url': f'/api/dashboard/display-batch-rates/{batch_main_token}',
                    'publish_time': batch_data['publish_time']
                }
            })
            
        except Exception as db_error:
            # 数据库操作失败，回滚事务
            session.rollback()
            logger.error(f"数据库操作失败，已回滚: {str(db_error)}")
            raise db_error
        
    except Exception as e:
        session.rollback()
        logger.error(f"发布批次面值汇率失败: {str(e)}")
        return jsonify({'success': False, 'message': f'发布失败: {str(e)}'}), 500
    finally:
        DatabaseService.close_session(session)
