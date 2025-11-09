import os
import sys
import uuid
import base64
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from services.auth_service import token_required, has_permission
from services.db_service import DatabaseService
from services.unified_log_service import UnifiedLogService
from sqlalchemy.exc import IntegrityError
import logging

# 设置日志记录器
logger = logging.getLogger(__name__)



# 添加data目录到路径
data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
if data_dir not in sys.path:
    sys.path.insert(0, data_dir)

try:
    from iso_countries import ISO_COUNTRIES_CURRENCIES, get_all_countries, get_unique_currencies
except ImportError:
    # 如果导入失败，使用基础数据
    ISO_COUNTRIES_CURRENCIES = []
    def get_all_countries():
        return []
    def get_unique_currencies():
        return []

# 导入模型
try:
    from models.exchange_models import CurrencyTemplate, Currency
except ImportError:
    from src.models.exchange_models import CurrencyTemplate, Currency

currency_management_bp = Blueprint('currency_management', __name__, url_prefix='/api/currency-management')

@currency_management_bp.route('/templates', methods=['GET'])
@token_required
@has_permission('currency_manage')
def get_currency_templates(*args, **kwargs):
    """获取所有币种模板"""
    current_user = kwargs.get('current_user') or args[0]
    session = None
    
    try:
        session = DatabaseService.get_session()
        
        # 查询所有币种模板
        templates = session.query(CurrencyTemplate).filter(
            CurrencyTemplate.is_active == True
        ).order_by(CurrencyTemplate.currency_code).all()
        
        # 获取所有在交易记录中使用过的币种ID（基于交易记录判断）
        from models.exchange_models import ExchangeTransaction
        used_currency_ids = session.query(ExchangeTransaction.currency_id).distinct().all()
        used_currency_id_set = {row[0] for row in used_currency_ids}
        
        # 获取使用过的币种代码
        used_currencies = session.query(Currency.currency_code).filter(
            Currency.id.in_(used_currency_id_set)
        ).all()
        used_currency_codes = {row[0] for row in used_currencies}
        
        template_list = []
        for template in templates:
            template_dict = template.to_dict()
            # 格式化创建时间
            if template.created_at:
                template_dict['created_at'] = template.created_at.strftime('%Y-%m-%d %H:%M:%S')
            
            # 检查是否在交易记录中使用过（基于交易记录判断）
            template_dict['is_in_use'] = template.currency_code in used_currency_codes
            
            template_list.append(template_dict)
        
        return jsonify({
            'success': True,
            'templates': template_list,
            'total': len(template_list)
        })
        
    except Exception as e:
        current_app.logger.error(f"获取币种模板失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取币种模板失败: {str(e)}'
        }), 500
    finally:
        if session:
            DatabaseService.close_session(session)

@currency_management_bp.route('/iso-countries', methods=['GET'])
@token_required
@has_permission('currency_manage')
def get_iso_countries(*args, **kwargs):
    """获取ISO标准国家数据"""
    current_user = kwargs.get('current_user') or args[0]
    try:
        # 使用完整的ISO数据
        iso_data = get_all_countries()
        countries = []
        
        for country_data in iso_data:
            countries.append({
                'code': country_data['country_code'],
                'name': country_data['country_code'],  # 使用国家代码作为翻译键
                'name_en': country_data['country_name_en'],
                'currency_code': country_data['currency_code'],
                'currency_name': country_data['currency_code'],  # 使用货币代码作为翻译键
                'currency_name_en': country_data['currency_name_en'],
                'currency_symbol': country_data['currency_symbol']
            })
        
        return jsonify({
            'success': True,
            'countries': countries,
            'total': len(countries)
        })
    except Exception as e:
        current_app.logger.error(f"获取ISO国家数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取ISO国家数据失败: {str(e)}'
        }), 500

@currency_management_bp.route('/iso-currencies', methods=['GET'])
@token_required
@has_permission('currency_manage')
def get_iso_currencies(*args, **kwargs):
    """获取ISO标准货币数据（去重）"""
    current_user = kwargs.get('current_user') or args[0]
    try:
        # 使用完整的ISO数据（去重）
        iso_data = get_unique_currencies()
        currencies = []
        
        for currency_data in iso_data:
            currencies.append({
                'code': currency_data['currency_code'],
                'name': currency_data['currency_code'],  # 使用货币代码作为翻译键
                'name_en': currency_data['currency_name_en'],
                'symbol': currency_data['currency_symbol'],
                'country_code': currency_data['country_code'],
                'country_name': currency_data['country_code']  # 使用国家代码作为翻译键
            })
        
        return jsonify({
            'success': True,
            'currencies': currencies,
            'total': len(currencies)
        })
    except Exception as e:
        current_app.logger.error(f"获取ISO货币数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取ISO货币数据失败: {str(e)}'
        }), 500

@currency_management_bp.route('/init-templates', methods=['POST'])
@token_required
@has_permission('currency_manage')
def init_currency_templates(*args, **kwargs):
    """初始化币种模板数据"""
    current_user = kwargs.get('current_user') or args[0]
    session = None
    
    try:
        session = DatabaseService.get_session()
        
        # 检查是否已有数据
        count = session.query(CurrencyTemplate).count()
        
        force_init = request.json and request.json.get('force', False)
        if count > 0 and not force_init:
            return jsonify({
                'success': False,
                'message': f'币种模板表已有 {count} 条记录，如需重新初始化请使用force参数',
                'existing_count': count
            })
        
        if force_init and count > 0:
            # 清空现有数据
            session.query(CurrencyTemplate).delete()
            current_app.logger.info("清空现有币种模板数据")
        
        # 使用ISO数据初始化
        iso_data = get_all_countries()
        templates_added = 0
        
        # 添加所有ISO标准货币模板（去重）
        added_currencies = set()
        for country in iso_data:
            currency_code = country['currency_code']
            if currency_code not in added_currencies:
                template = CurrencyTemplate(
                    currency_code=currency_code,
                    currency_name=country['currency_name_zh'],
                    country=country['country_name_zh'],
                    flag_code=country['country_code'],
                    symbol=country['currency_symbol'],
                    description=f"ISO 3166-1标准{country['currency_name_zh']}模板",
                    is_active=True
                )
                session.add(template)
                added_currencies.add(currency_code)
                templates_added += 1
        
        DatabaseService.commit_session(session)
        
        current_app.logger.info(f"成功初始化 {templates_added} 个币种模板")
        
        return jsonify({
            'success': True,
            'message': f'成功初始化 {templates_added} 个币种模板',
            'templates_added': templates_added,
            'total_currencies': len(added_currencies)
        })
        
    except Exception as e:
        if session:
            DatabaseService.rollback_session(session)
        current_app.logger.error(f"初始化币种模板失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'初始化币种模板失败: {str(e)}'
        }), 500
    finally:
        if session:
            DatabaseService.close_session(session)

@currency_management_bp.route('/templates', methods=['POST'])
@token_required
@has_permission('currency_manage')
def add_currency_template(*args, **kwargs):
    """新增币种模板"""
    current_user = kwargs.get('current_user') or args[0]
    data = request.json
    session = None
    
    if not data:
        return jsonify({'success': False, 'message': '没有提供数据'}), 400
    
    required_fields = ['currency_code', 'currency_name', 'country', 'flag_code']
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return jsonify({
            'success': False,
            'message': f'缺少必填字段: {", ".join(missing_fields)}'
        }), 400
    
    try:
        session = DatabaseService.get_session()
        
        # 检查币种代码是否已存在
        existing = session.query(CurrencyTemplate).filter_by(
            currency_code=data['currency_code'].upper()
        ).first()
        
        if existing:
            return jsonify({
                'success': False,
                'message': f'币种代码 {data["currency_code"]} 已存在'
            }), 400
        
        # 创建新模板
        template = CurrencyTemplate(
            currency_code=data['currency_code'].upper(),
            currency_name=data['currency_name'],
            country=data['country'],
            flag_code=data['flag_code'].upper(),
            symbol=data.get('symbol', ''),
            description=data.get('description', ''),
            custom_flag_filename=data.get('custom_flag_filename', ''),
            is_active=data.get('is_active', True)
        )
        
        session.add(template)
        DatabaseService.commit_session(session)
        
        current_app.logger.info(f"新增币种模板: {data['currency_code']}")
        
        return jsonify({
            'success': True,
            'message': '币种模板添加成功'
        })
        
    except IntegrityError as e:
        if session:
            DatabaseService.rollback_session(session)
        current_app.logger.error(f"新增币种模板失败（完整性约束）: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'币种代码 {data["currency_code"]} 已存在'
        }), 400
    except Exception as e:
        if session:
            DatabaseService.rollback_session(session)
        current_app.logger.error(f"新增币种模板失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'新增币种模板失败: {str(e)}'
        }), 500
    finally:
        if session:
            DatabaseService.close_session(session)

@currency_management_bp.route('/templates/<int:template_id>', methods=['PUT'])
@token_required
@has_permission('currency_manage')
def update_currency_template(*args, **kwargs):
    """更新币种模板"""
    current_user = kwargs.get('current_user') or args[0]
    template_id = kwargs.get('template_id')
    data = request.json
    session = None
    
    if not data:
        return jsonify({'success': False, 'message': '没有提供数据'}), 400
    
    try:
        session = DatabaseService.get_session()
        
        # 检查模板是否存在
        template = session.query(CurrencyTemplate).filter_by(id=template_id).first()
        if not template:
            return jsonify({
                'success': False,
                'message': '币种模板不存在'
            }), 404
        
        # 如果修改了币种代码，检查新代码是否已被其他模板使用
        if data['currency_code'].upper() != template.currency_code:
            existing = session.query(CurrencyTemplate).filter(
                CurrencyTemplate.currency_code == data['currency_code'].upper(),
                CurrencyTemplate.id != template_id
            ).first()
            
            if existing:
                return jsonify({
                    'success': False,
                    'message': f'币种代码 {data["currency_code"]} 已被其他模板使用'
                }), 400
        
        # 更新模板
        template.currency_code = data['currency_code'].upper()
        template.currency_name = data['currency_name']
        template.country = data['country']
        template.flag_code = data['flag_code'].upper()
        template.symbol = data.get('symbol', '')
        template.description = data.get('description', '')
        template.custom_flag_filename = data.get('custom_flag_filename', '')
        template.is_active = data.get('is_active', True)
        
        # 自动同步到Currency表
        currency = session.query(Currency).filter_by(currency_code=template.currency_code).first()
        if currency:
            # 更新Currency表中的对应记录
            currency.currency_name = template.currency_name
            currency.custom_flag_filename = template.custom_flag_filename
            currency.flag_code = template.flag_code
            currency.country = template.country
            currency.symbol = template.symbol
            current_app.logger.info(f"自动同步币种模板修改到Currency表: {template.currency_code}")
        else:
            current_app.logger.warning(f"Currency表中不存在币种 {template.currency_code}，无法同步")
        
        DatabaseService.commit_session(session)
        
        current_app.logger.info(f"更新币种模板: {template_id}")
        
        # 记录货币阈值修改日志
        try:
            log_service = UnifiedLogService()
            log_service.log_currency_threshold_change(
                operator_id=current_user['operator_id'],
                operator_name=current_user.get('name', '未知用户'),
                currency_code=template.currency_code,
                old_values=f'min_threshold: {template.min_threshold}, max_threshold: {template.max_threshold}',
                new_values=f'min_threshold: {data.get("min_threshold", template.min_threshold)}, max_threshold: {data.get("max_threshold", template.max_threshold)}',
                ip_address=request.remote_addr,
                branch_id=current_user['branch_id']
            )
        except Exception as log_error:
            # 日志记录失败不应该影响货币阈值修改流程
            print(f"货币阈值修改日志记录失败: {log_error}")
        
        return jsonify({
            'success': True,
            'message': '币种模板更新成功'
        })
        
    except IntegrityError as e:
        if session:
            DatabaseService.rollback_session(session)
        current_app.logger.error(f"更新币种模板失败（完整性约束）: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'币种代码 {data["currency_code"]} 已被其他模板使用'
        }), 400
    except Exception as e:
        if session:
            DatabaseService.rollback_session(session)
        current_app.logger.error(f"更新币种模板失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'更新币种模板失败: {str(e)}'
        }), 500
    finally:
        if session:
            DatabaseService.close_session(session)

@currency_management_bp.route('/templates/<int:template_id>', methods=['DELETE'])
@token_required
@has_permission('currency_manage')
def delete_currency_template(*args, **kwargs):
    """删除币种模板"""
    current_user = kwargs.get('current_user') or args[0]
    template_id = kwargs.get('template_id')
    session = None
    
    try:
        session = DatabaseService.get_session()
        
        # 检查模板是否存在
        template = session.query(CurrencyTemplate).filter_by(id=template_id).first()
        if not template:
            return jsonify({
                'success': False,
                'message': '币种模板不存在'
            }), 404
        
        # 检查是否在交易记录中被使用过
        from models.exchange_models import ExchangeTransaction
        currency = session.query(Currency).filter_by(currency_code=template.currency_code).first()
        
        if currency:
            # 检查是否有交易记录使用过这个币种
            transaction_count = session.query(ExchangeTransaction).filter_by(
                currency_id=currency.id
            ).count()
            
            if transaction_count > 0:
                return jsonify({
                    'success': False,
                    'message': f'该币种模板在交易记录中被使用过（{transaction_count} 笔交易），无法删除'
                }), 400
        
        # 删除模板
        session.delete(template)
        DatabaseService.commit_session(session)
        
        current_app.logger.info(f"删除币种模板: {template_id}")
        
        return jsonify({
            'success': True,
            'message': '币种模板删除成功'
        })
        
    except Exception as e:
        if session:
            DatabaseService.rollback_session(session)
        current_app.logger.error(f"删除币种模板失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'删除币种模板失败: {str(e)}'
        }), 500
    finally:
        if session:
            DatabaseService.close_session(session)

@currency_management_bp.route('/upload-flag', methods=['POST'])
@token_required
@has_permission('currency_manage')
def upload_flag(*args, **kwargs):
    """上传币种图标"""
    current_user = kwargs.get('current_user') or args[0]
    
    try:
        # 获取上传的文件数据
        data = request.json
        if not data or 'file_data' not in data or 'filename' not in data:
            return jsonify({'success': False, 'message': '没有提供文件数据'}), 400
        
        # 解码base64文件数据
        file_data = data['file_data']
        filename = data['filename']
        
        # 验证文件类型
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.svg')):
            return jsonify({'success': False, 'message': '只支持PNG、JPG、JPEG、SVG格式的图片'}), 400
        
        # 生成唯一文件名
        file_ext = os.path.splitext(filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        
        # 确保flags目录存在
        # 优先使用项目根目录的public/flags，如果不存在则使用src/public/flags
        current_file_dir = os.path.dirname(os.path.abspath(__file__))  # src目录
        project_root = os.path.dirname(current_file_dir)  # 项目根目录
        flags_dir = os.path.join(project_root, 'public', 'flags')
        
        # 如果项目根目录的public/flags不存在，使用src/public/flags
        if not os.path.exists(flags_dir):
            flags_dir = os.path.join(current_file_dir, 'public', 'flags')
        
        os.makedirs(flags_dir, exist_ok=True)
        
        # 写入文件
        file_path = os.path.join(flags_dir, unique_filename)
        
        # 如果是base64数据，需要解码
        if file_data.startswith('data:'):
            header, file_data = file_data.split(',', 1)
        
        with open(file_path, 'wb') as f:
            f.write(base64.b64decode(file_data))
        
        current_app.logger.info(f"上传币种图标成功: {unique_filename}")
        
        return jsonify({
            'success': True,
            'message': '图标上传成功',
            'filename': unique_filename,
            'url': f'/flags/{unique_filename}'
        })
        
    except Exception as e:
        current_app.logger.error(f"上传币种图标失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'上传币种图标失败: {str(e)}'
        }), 500