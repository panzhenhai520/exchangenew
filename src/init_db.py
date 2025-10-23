from datetime import datetime, date
from models.exchange_models import Base, Branch, Role, Operator, Currency, Permission, RolePermission, ExchangeTransaction, ExchangeRate, PermissionTranslation, DenominationPublishDetail
from models.denomination_models import CurrencyDenomination, DenominationRate, TransactionDenomination
from models.report_models import Base as ReportBase
from services.db_service import DatabaseService, engine
# from data.init_currency_templates import init_currency_templates
import os
from sqlalchemy import text, inspect

def init_permission_translations(session):
    """初始化权限国际化数据"""
    print("正在初始化权限国际化数据...")
    
    # 权限翻译数据
    permission_translations = {
        'system_manage': {
            'en': 'System Management Permission',
            'th': 'สิทธิ์การจัดการระบบ'
        },
        'user_manage': {
            'en': 'User Management Permission',
            'th': 'สิทธิ์การจัดการผู้ใช้'
        },
        'role_manage': {
            'en': 'Role Management Permission',
            'th': 'สิทธิ์การจัดการบทบาท'
        },
        'branch_manage': {
            'en': 'Branch Management Permission',
            'th': 'สิทธิ์การจัดการสาขา'
        },
        'currency_manage': {
            'en': 'Currency Management Permission',
            'th': 'สิทธิ์การจัดการสกุลเงิน'
        },
        'rate_manage': {
            'en': 'Exchange Rate Management Permission',
            'th': 'สิทธิ์การจัดการอัตราแลกเปลี่ยน'
        },
        'exchange_operate': {
            'en': 'Currency Exchange Operation Permission',
            'th': 'สิทธิ์การดำเนินการแลกเปลี่ยนเงินตรา'
        },
        'report_view': {
            'en': 'Report Viewing Permission',
            'th': 'สิทธิ์การดูรายงาน'
        },
        'log_view': {
            'en': 'Log Viewing Permission',
            'th': 'สิทธิ์การดูบันทึก'
        },
        'balance_manage': {
            'en': 'Balance Management Permission',
            'th': 'สิทธิ์การจัดการยอดคงเหลือ'
        },
        'end_of_day': {
            'en': 'End of Day Operation Permission',
            'th': 'สิทธิ์การดำเนินการปิดวัน'
        },
        'view_transactions': {
            'en': 'Transaction Viewing Permission',
            'th': 'สิทธิ์การดูรายการธุรกรรม'
        },
        'export_data': {
            'en': 'Data Export Permission',
            'th': 'สิทธิ์การส่งออกข้อมูล'
        }
    }
    
    # 获取所有权限
    permissions = session.query(Permission).all()
    permission_dict = {perm.permission_name: perm for perm in permissions}
    
    # 创建翻译记录
    for perm_name, translations in permission_translations.items():
        if perm_name in permission_dict:
            permission = permission_dict[perm_name]
            
            for lang_code, description in translations.items():
                # 检查翻译是否已存在
                existing_translation = session.query(PermissionTranslation).filter_by(
                    permission_id=permission.id,
                    language_code=lang_code
                ).first()
                
                if not existing_translation:
                    translation = PermissionTranslation(
                        permission_id=permission.id,
                        language_code=lang_code,
                        description=description,
                        created_at=datetime.utcnow()
                    )
                    session.add(translation)
    
    DatabaseService.commit_session(session)
    print("[OK] 权限国际化数据初始化完成")


def check_and_update_database_structure():
    """检查并更新数据库结构以符合当前标准"""
    print("正在检查和更新数据库结构...")
    session = DatabaseService.get_session()

    try:
        # 检查并添加双向交易相关字段到 exchange_transactions 表
        inspector = inspect(engine)

        # 获取 exchange_transactions 表的列信息
        if 'exchange_transactions' in inspector.get_table_names():
            existing_columns = [col['name'] for col in inspector.get_columns('exchange_transactions')]

            # 需要添加的字段
            required_fields = {
                'seqno': 'INT',
                'exchange_type': 'VARCHAR(50) DEFAULT "normal"',
                'approval_serial': 'VARCHAR(30)',
                'id_expiry_date': 'DATE',
                'asset_details': 'TEXT',
                'bot_flag': 'INT DEFAULT 0',
                'fcd_flag': 'INT DEFAULT 0',
                'use_fcd': 'TINYINT(1) DEFAULT 0',
                'payment_method': 'VARCHAR(50) DEFAULT "cash"',
                'payment_method_note': 'VARCHAR(200)',
                'receipt_language': 'VARCHAR(5) DEFAULT "zh"',
                'issuing_country_code': 'VARCHAR(2)',
                'funding_source': 'VARCHAR(50)',
                'business_group_id': 'VARCHAR(100)',
                'group_sequence': 'INT DEFAULT 1',
                'transaction_direction': 'VARCHAR(20)',
                'customer_country_code': 'VARCHAR(10)',
                'customer_address': 'TEXT',
                'occupation': 'VARCHAR(100)',
                'workplace': 'VARCHAR(200)',
                'work_phone': 'VARCHAR(20)'
            }

            for field_name, field_type in required_fields.items():
                if field_name not in existing_columns:
                    try:
                        alter_sql = f"ALTER TABLE exchange_transactions ADD COLUMN {field_name} {field_type}"
                        session.execute(text(alter_sql))
                        session.commit()
                        print(f"[OK] 已添加字段: exchange_transactions.{field_name}")
                    except Exception as e:
                        print(f"[WARNING] 添加字段 {field_name} 失败: {e}")
                        session.rollback()
                else:
                    print(f"[INFO] 字段已存在: exchange_transactions.{field_name}")

        # 检查并添加网点相关字段到 branches 表
        if 'branches' in inspector.get_table_names():
            existing_columns = [col['name'] for col in inspector.get_columns('branches')]

            # 需要添加的字段
            required_fields = {
                'license_number': 'VARCHAR(100)',
                'website': 'VARCHAR(255)',
                'company_name': 'VARCHAR(255)',
                'tax_id': 'VARCHAR(50)',
                'receipt_template_type': 'VARCHAR(50) DEFAULT "standard"',
                'institution_type': 'VARCHAR(50) DEFAULT "money_changer"',
                'amlo_institution_code': 'VARCHAR(10)',
                'amlo_branch_code': 'VARCHAR(10)',
                'bot_sender_code': 'VARCHAR(20)',
                'bot_branch_area_code': 'VARCHAR(20)',
                'bot_license_number': 'VARCHAR(20)'
            }

            for field_name, field_type in required_fields.items():
                if field_name not in existing_columns:
                    try:
                        alter_sql = f"ALTER TABLE branches ADD COLUMN {field_name} {field_type}"
                        session.execute(text(alter_sql))
                        session.commit()
                        print(f"[OK] 已添加字段: branches.{field_name}")
                    except Exception as e:
                        print(f"[WARNING] 添加字段 {field_name} 失败: {e}")
                        session.rollback()
                else:
                    print(f"[INFO] 字段已存在: branches.{field_name}")

        # 检查并创建索引（MySQL兼容版本）
        try:
            # 检查索引是否存在，不存在则创建
            indexes_to_create = [
                ("idx_exchange_transactions_business_group_id", "exchange_transactions", "business_group_id"),
                ("idx_exchange_transactions_direction", "exchange_transactions", "transaction_direction")
            ]

            for index_name, table_name, column_name in indexes_to_create:
                # 检查索引是否存在
                check_index_sql = f"""
                SELECT COUNT(*) as cnt FROM information_schema.statistics
                WHERE table_schema = DATABASE()
                AND table_name = '{table_name}'
                AND index_name = '{index_name}'
                """
                result = session.execute(text(check_index_sql)).fetchone()

                if result[0] == 0:  # 索引不存在
                    create_index_sql = f"CREATE INDEX {index_name} ON {table_name}({column_name})"
                    session.execute(text(create_index_sql))
                    print(f"[OK] 创建索引: {index_name}")
                else:
                    print(f"[INFO] 索引已存在: {index_name}")

            session.commit()
            print("[OK] 数据库索引检查完成")
        except Exception as e:
            print(f"[WARNING] 索引创建失败: {e}")
            session.rollback()

        print("[OK] 数据库结构检查和更新完成")

    except Exception as e:
        print(f"[ERROR] 数据库结构更新失败: {e}")
        session.rollback()
        import traceback
        print("错误详情:")
        print(traceback.format_exc())
    finally:
        DatabaseService.close_session(session)


def init_database():
    """初始化数据库结构并插入基础数据"""
    print("开始初始化数据库...")
    
    # 检查是否需要重置数据库
    should_reset = os.environ.get('RESET_DB', 'false').lower() == 'true'
    
    if should_reset:
        # 重置数据库（开发环境）
        Base.metadata.drop_all(bind=engine)
        print("[OK] 数据库表已清空")
    
    # 创建所有表（如果不存在）
    Base.metadata.create_all(bind=engine)
    # 如果有report_models，也创建相关表
    try:
        ReportBase.metadata.create_all(bind=engine)
    except:
        pass
    print("[OK] 数据库表创建完成")

    # 检查并更新数据库结构
    check_and_update_database_structure()

    session = DatabaseService.get_session()

    try:
        # 检查是否已经初始化
        admin = session.query(Operator).filter_by(login_code='admin').first()
        if admin:
            print("数据库已经初始化，跳过基础数据创建")
            # 但仍然检查并初始化权限翻译
            existing_translations = session.query(PermissionTranslation).first()
            if not existing_translations:
                init_permission_translations(session)
            return

        # 初始化基础币种
        print("正在初始化基础币种...")
        cny = Currency(
            currency_code='CNY',
            currency_name='人民币',
            country='中国',
            flag_code='CN',
            symbol='¥',
            created_at=datetime.utcnow()
        )
        session.add(cny)
        DatabaseService.commit_session(session)  # 立即提交以获取ID
        print(f"[OK] 人民币币种创建成功，ID: {cny.id}")
        
        base_currency_id = cny.id
        print(f"基础币种ID: {base_currency_id}")

        # 初始化网点
        print("正在初始化网点...")
        branches = [
            Branch(
                branch_name='总行营业部',
                branch_code='HO001',
                address='北京市朝阳区金融街1号',
                base_currency_id=base_currency_id,
                is_active=True,
                created_at=datetime.utcnow()
            ),
            Branch(
                branch_name='北京分行',
                branch_code='BJ001',
                address='北京市海淀区中关村大街10号',
                base_currency_id=base_currency_id,
                is_active=True,
                created_at=datetime.utcnow()
            ),
            Branch(
                branch_name='上海分行',
                branch_code='SH001',
                address='上海市浦东新区陆家嘴金融中心',
                base_currency_id=base_currency_id,
                is_active=True,
                created_at=datetime.utcnow()
            ),
        ]
        session.add_all(branches)
        DatabaseService.commit_session(session)  # 立即提交
        print("[OK] 网点初始化完成")

        # 初始化系统权限
        print("正在初始化系统权限...")
        permissions = [
            Permission(permission_name='system_manage', description='系统管理权限'),
            Permission(permission_name='user_manage', description='用户管理权限'),
            Permission(permission_name='role_manage', description='角色管理权限'),
            Permission(permission_name='branch_manage', description='网点管理权限'),
            Permission(permission_name='currency_manage', description='币种管理权限'),
            Permission(permission_name='rate_manage', description='汇率管理权限'),
            Permission(permission_name='exchange_operate', description='兑换业务操作权限'),
            Permission(permission_name='report_view', description='报表查看权限'),
            Permission(permission_name='log_view', description='日志查看权限'),
            Permission(permission_name='balance_manage', description='余额管理权限'),
            Permission(permission_name='end_of_day', description='日审操作权限'),
            Permission(permission_name='view_transactions', description='查看交易记录权限'),
            Permission(permission_name='export_data', description='导出数据权限')
        ]
        session.add_all(permissions)
        DatabaseService.commit_session(session)
        print("[OK] 系统权限初始化完成")

        # 初始化权限国际化数据
        init_permission_translations(session)

        # 初始化角色
        print("正在初始化角色...")
        admin_role = Role(role_name='系统管理员', description='SYSTEM_ADMIN_DESCRIPTION')
        branch_admin_role = Role(role_name='分行管理员', description='BRANCH_ADMIN_DESCRIPTION')
        session.add_all([admin_role, branch_admin_role])
        DatabaseService.commit_session(session)
        print("[OK] 角色初始化完成")

        # 为系统管理员角色分配所有权限
        print("正在分配系统管理员权限...")
        for perm in permissions:
            role_perm = RolePermission(
                role_id=admin_role.id,
                permission_id=perm.id,
                created_at=datetime.utcnow()
            )
            session.add(role_perm)
        DatabaseService.commit_session(session)
        print("[OK] 系统管理员权限分配完成")

        # 初始化管理员操作员
        print("正在初始化管理员账号...")
        admin = Operator(
            login_code='admin',
            password_hash='e10adc3949ba59abbe56e057f20f883e',  # 123456
            name='系统管理员',
            branch_id=1,  # 默认总行
            role_id=admin_role.id,  # 使用刚创建的管理员角色ID
            is_active=True,
            status='active',  # 新增状态字段
            created_at=datetime.utcnow()
        )
        session.add(admin)
        DatabaseService.commit_session(session)  # 立即提交
        print("[OK] 管理员账号创建成功")

        print("[OK] 基础数据初始化完成")

        # 初始化币种模板数据
        print("正在初始化币种模板...")
        try:
            from data.init_currency_templates import init_currency_templates
            init_currency_templates()
            print("[OK] 币种模板初始化完成")
        except ImportError as e:
            print(f"[WARNING]  币种模板初始化跳过: {e}")
        except Exception as e:
            print(f"[WARNING]  币种模板初始化失败: {e}")


    except Exception as e:
        DatabaseService.rollback_session(session)
        print(f"[ERROR] 初始化失败: {str(e)}")
        import traceback
        print("错误详情:")
        print(traceback.format_exc())
    finally:
        DatabaseService.close_session(session)


if __name__ == '__main__':
    """
    主函数：支持以下环境变量
    - INIT_DB=true: 执行完整的数据库初始化（包括基础数据）
    - UPDATE_STRUCTURE=true: 仅更新数据库结构（不初始化基础数据）
    - RESET_DB=true: 重置数据库（删除所有表后重建）

    使用示例：
    python init_db.py                    # 检查并更新结构
    INIT_DB=true python init_db.py       # 完整初始化
    UPDATE_STRUCTURE=true python init_db.py  # 仅更新结构
    RESET_DB=true INIT_DB=true python init_db.py  # 重置并完整初始化
    """
    import sys

    init_full = os.environ.get('INIT_DB', 'false').lower() == 'true'
    update_structure = os.environ.get('UPDATE_STRUCTURE', 'false').lower() == 'true'

    if init_full:
        print("执行完整数据库初始化...")
        init_database()
    elif update_structure:
        print("仅更新数据库结构...")
        # 确保表存在
        Base.metadata.create_all(bind=engine)
        try:
            ReportBase.metadata.create_all(bind=engine)
        except:
            pass
        check_and_update_database_structure()
    else:
        print("检查并更新数据库结构...")
        print("提示：使用 INIT_DB=true 执行完整初始化")
        print("     使用 UPDATE_STRUCTURE=true 仅更新结构")

        # 默认行为：检查并更新结构
        Base.metadata.create_all(bind=engine)
        try:
            ReportBase.metadata.create_all(bind=engine)
        except:
            pass
        check_and_update_database_structure()

    print("数据库迁移脚本执行完成")
