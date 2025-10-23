from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, Date, Numeric, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

class Branch(Base):
    __tablename__ = 'branches'

    id = Column(Integer, primary_key=True)
    branch_name = Column(String(100), nullable=False)
    branch_code = Column(String(20), nullable=False, unique=True)
    address = Column(String(255))
    manager_name = Column(String(100))  # 网点管理人
    phone_number = Column(String(20))   # 网点电话号码
    base_currency_id = Column(Integer, ForeignKey('currencies.id'))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 增强网点信息字段（用于80mm收据）
    license_number = Column(String(100))  # 许可证编号
    website = Column(String(255))  # 网址
    company_name = Column(String(200))  # 公司名称（收据抬头）
    tax_id = Column(String(50))  # 纳税人识别号
    receipt_template_type = Column(String(20), default='80mm')  # 收据模板类型

    # 新增收据信息字段
    company_full_name = Column(String(255))  # 公司全称
    tax_registration_number = Column(String(100))  # 税务登记号

    # 机构类型（用于AMLO报告）
    institution_type = Column(String(50), default='money_changer')  # 机构类型：money_changer/bank/financial_institution/other

    # AMLO / BOT 监管字段
    amlo_institution_code = Column(String(10))  # 央行分配的3位机构代码
    amlo_branch_code = Column(String(10))  # 报告使用的3位网点代码
    bot_sender_code = Column(String(20))  # BOT数据报送机构代码
    bot_branch_area_code = Column(String(20))  # BOT要求的营业场所区域代码
    bot_license_number = Column(String(20))  # BOT专用许可证编号

    operators = relationship("Operator", back_populates="branch")
    balances = relationship("CurrencyBalance", back_populates="branch")
    transactions = relationship("ExchangeTransaction", back_populates="branch")
    rates = relationship("ExchangeRate", back_populates="branch")
    base_currency = relationship("Currency", foreign_keys=[base_currency_id])
    print_settings = relationship("PrintSettings", back_populates="branch")

class Role(Base):
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True)
    role_name = Column(String(50), nullable=False, unique=True)
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    permissions = relationship("RolePermission", back_populates="role")
    operators = relationship("Operator", back_populates="role")

class Permission(Base):
    __tablename__ = 'permissions'

    id = Column(Integer, primary_key=True)
    permission_name = Column(String(50), nullable=False, unique=True)
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    roles = relationship("RolePermission", back_populates="permission")

class RolePermission(Base):
    __tablename__ = 'role_permissions'

    id = Column(Integer, primary_key=True)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    permission_id = Column(Integer, ForeignKey('permissions.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission", back_populates="roles")

class Operator(Base):
    __tablename__ = 'operators'

    id = Column(Integer, primary_key=True)
    login_code = Column(String(20), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    branch_id = Column(Integer, ForeignKey('branches.id'), nullable=False)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 新增用户信息字段
    id_card_number = Column(String(50))
    phone_number = Column(String(20))
    mobile_number = Column(String(20))
    address = Column(Text)
    email = Column(String(100))
    status = Column(String(20), default='active')  # active, inactive, locked, suspended

    branch = relationship("Branch", back_populates="operators")
    role = relationship("Role", back_populates="operators")
    transactions = relationship("ExchangeTransaction", back_populates="operator")
    logs = relationship("SystemLog", back_populates="operator")

class Currency(Base):
    __tablename__ = 'currencies'

    id = Column(Integer, primary_key=True)
    currency_code = Column(String(3), nullable=False, unique=True)
    currency_name = Column(String(50), nullable=False)
    country = Column(String(50))
    flag_code = Column(String(2))
    created_at = Column(DateTime, default=datetime.utcnow)
    symbol = Column(String(10))  #
    branch_id = Column(Integer, ForeignKey('branches.id'))  # 添加branch_id字段
    custom_flag_filename = Column(String(255))  # 自定义图标文件名
    rates = relationship("ExchangeRate", back_populates="currency")
    balances = relationship("CurrencyBalance", back_populates="currency")
    transactions = relationship("ExchangeTransaction", back_populates="currency")

class BranchCurrency(Base):
    """网点币种关联表 - 管理网点级别的币种启用/禁用状态"""
    __tablename__ = 'branch_currencies'
    
    id = Column(Integer, primary_key=True)
    branch_id = Column(Integer, ForeignKey('branches.id'), nullable=False)
    currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)  # 是否启用
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 外键关系
    branch = relationship("Branch", backref="branch_currencies")
    currency = relationship("Currency", backref="branch_currencies")
    
    # 复合唯一约束：每个网点的每种币种只能有一条记录
    __table_args__ = (
        UniqueConstraint('branch_id', 'currency_id', name='uq_branch_currency'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'branch_id': self.branch_id,
            'currency_id': self.currency_id,
            'is_enabled': self.is_enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ExchangeRate(Base):
    __tablename__ = 'exchange_rates'

    id = Column(Integer, primary_key=True)
    branch_id = Column(Integer, ForeignKey('branches.id'), nullable=False)
    currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False)
    rate_date = Column(Date, nullable=False)
    buy_rate = Column(Float, nullable=False)
    sell_rate = Column(Float, nullable=False)
    created_by = Column(Integer, ForeignKey('operators.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    sort_order = Column(Integer, default=0)  # 排序顺序
    
    # 批量保存相关字段
    batch_saved = Column(Integer, default=0)  # 是否批量保存 (0=否, 1=是)
    batch_saved_time = Column(String(50), nullable=True)  # 批量保存时间
    batch_saved_by = Column(String(100), nullable=True)  # 批量保存操作员姓名
    
    currency = relationship("Currency", back_populates="rates")
    branch = relationship("Branch", back_populates="rates")

class CurrencyBalance(Base):
    __tablename__ = 'currency_balances'

    id = Column(Integer, primary_key=True)
    branch_id = Column(Integer, ForeignKey('branches.id'), nullable=False)
    currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False)
    balance = Column(Numeric(15, 2), default=0)  # 【修复】改为Numeric类型，解决精度问题
    updated_at = Column(DateTime)

    branch = relationship("Branch", back_populates="balances")
    currency = relationship("Currency", back_populates="balances")


class ExchangeTransaction(Base):
    __tablename__ = 'exchange_transactions'

    id = Column(Integer, primary_key=True)
    seqno = Column(Integer)  # 交易序列号
    transaction_no = Column(String(20), nullable=False, unique=True)
    branch_id = Column(Integer, ForeignKey('branches.id'), nullable=False)
    currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False)
    type = Column(String(20), nullable=False)
    exchange_type = Column(String(50), default='normal')  # 兑换类型: normal, large_amount, asset_mortgage
    approval_serial = Column(String(30))  # 审批流水号
    amount = Column(Numeric(15, 2), nullable=False)
    rate = Column(Numeric(10, 4), nullable=False)
    local_amount = Column(Numeric(15, 2), nullable=False)
    customer_name = Column(String(100))
    customer_id = Column(String(50))
    id_expiry_date = Column(Date)  # 证件有效期
    operator_id = Column(Integer, ForeignKey('operators.id'), nullable=False)
    transaction_date = Column(Date, nullable=False)
    transaction_time = Column(String(10), nullable=False)
    created_at = Column(DateTime)
    original_transaction_no = Column(String(20))
    balance_before = Column(Numeric(15, 2))
    balance_after = Column(Numeric(15, 2))
    status = Column(String(20), default='completed')

    # 新增字段：用途、备注、票据文件名、打印次数
    purpose = Column(String(100))  # 交易用途
    remarks = Column(Text)  # 备注信息
    asset_details = Column(Text)  # 资产明细
    bot_flag = Column(Integer, default=0)  # BOT标记
    fcd_flag = Column(Integer, default=0)  # FCD标记
    use_fcd = Column(Boolean, default=False)  # 是否使用FCD账户
    payment_method = Column(String(50), default='cash')  # 付款方式: cash, bank_transfer, fcd_account, other
    payment_method_note = Column(String(200))  # 付款方式备注（当选择"其他"时填写）
    receipt_language = Column(String(5), default='zh')  # 收据打印语言: zh, en, th
    issuing_country_code = Column(String(2))  # 签发国家代码
    funding_source = Column(String(50))  # 资金来源
    receipt_filename = Column(String(255))  # 票据文件名
    print_count = Column(Integer, default=0)  # 票据打印次数

    # 双向交易支持字段
    business_group_id = Column(String(50))  # 业务组ID，用于关联拆分的交易
    group_sequence = Column(Integer, default=1)  # 组内序号
    transaction_direction = Column(String(20))  # 交易方向（显式记录买入/卖出）

    # 增强客户信息字段（用于80mm收据）
    customer_country_code = Column(String(5))  # 客户国家代码
    customer_address = Column(Text)  # 客户地址
    occupation = Column(String(100))  # 职业
    workplace = Column(String(200))  # 工作单位
    work_phone = Column(String(20))  # 工作电话

    branch = relationship("Branch", back_populates="transactions")
    currency = relationship("Currency", back_populates="transactions")
    operator = relationship("Operator", back_populates="transactions")

class SystemLog(Base):
    __tablename__ = 'system_logs'

    id = Column(Integer, primary_key=True)
    operation = Column(String(100), nullable=False)
    operator_id = Column(Integer, ForeignKey('operators.id'))
    log_type = Column(String(50), nullable=False)
    action = Column(String(255), nullable=False)
    details = Column(Text)
    ip_address = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    operator = relationship("Operator", back_populates="logs")

class EndOfDayReport(Base):
    __tablename__ = 'end_of_day_reports'

    id = Column(Integer, primary_key=True)
    branch_id = Column(Integer, ForeignKey('branches.id'), nullable=False)
    report_date = Column(Date, nullable=False)
    transaction_count = Column(Integer, default=0)
    buy_total = Column(Float, default=0.0)
    sell_total = Column(Float, default=0.0)
    buy_cny_total = Column(Float, default=0.0)
    sell_cny_total = Column(Float, default=0.0)
    net_cny_flow = Column(Float, default=0.0)
    operator_id = Column(Integer, ForeignKey('operators.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    branch = relationship("Branch")
    operator = relationship("Operator")

class CurrencyTemplate(Base):
    """基础币种信息表"""
    __tablename__ = 'currency_templates'
    
    id = Column(Integer, primary_key=True)
    currency_code = Column(String(10), unique=True, nullable=False)
    currency_name = Column(String(50), nullable=False)
    country = Column(String(50), nullable=False)
    flag_code = Column(String(2), nullable=False)
    symbol = Column(String(10))
    description = Column(Text)
    custom_flag_filename = Column(String(255))  # 自定义图标文件名
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'currency_code': self.currency_code,
            'currency_name': self.currency_name,
            'country': self.country,
            'flag_code': self.flag_code,
            'symbol': self.symbol,
            'description': self.description,
            'custom_flag_filename': self.custom_flag_filename,
            'is_active': self.is_active
        }

class EODStatus(Base):
    __tablename__ = 'eod_status'

    id = Column(Integer, primary_key=True)
    branch_id = Column(Integer, ForeignKey('branches.id'), nullable=False)
    date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default='pending')  # pending, processing, completed, cancelled
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    started_by = Column(Integer, ForeignKey('operators.id'), nullable=False)
    completed_by = Column(Integer, ForeignKey('operators.id'), nullable=True)
    cancel_reason = Column(String(500), nullable=True)
    print_count = Column(Integer, default=0)
    print_operator_id = Column(Integer, ForeignKey('operators.id'))
    fail_reason = Column(String(255))
    is_locked = Column(Boolean, default=False)  # 营业锁定状态
    step = Column(Integer, default=1)  # 当前步骤 1-8
    step_status = Column(String(20), default='pending')  # pending, processing, completed, failed
    
    # 【新增】业务时间范围字段
    business_start_time = Column(DateTime, nullable=True)  # 业务统计开始时间
    business_end_time = Column(DateTime, nullable=True)    # 业务统计结束时间
    
    # Relationships
    branch = relationship('Branch', backref='eod_statuses')
    starter = relationship('Operator', foreign_keys=[started_by], backref='started_eods')
    completer = relationship('Operator', foreign_keys=[completed_by], backref='completed_eods')
    print_operator = relationship('Operator', foreign_keys=[print_operator_id], backref='printed_eods')
    # history = relationship('EODHistory', backref='eod_status', uselist=False)  # 已废弃
    print_logs = relationship('EODPrintLog', backref='eod_status')
    balance_verifications = relationship('EODBalanceVerification', backref='eod_status')

# ============================================================================
# 【已废弃】旧EOD表模型 - 2025-10-10 简化后不再使用
# 说明：
# - 已迁移到新表：EODBalanceVerification
# - 期初余额统一从 EODBalanceVerification.actual_balance 获取
# - 保留定义仅为向后兼容，实际数据已备份到 backup/ 目录
# - 如需删除，请先确认系统稳定运行1-2个月
# ============================================================================

# class EODHistory(Base):
#     __tablename__ = 'eod_history'
#
#     id = Column(Integer, primary_key=True)
#     eod_status_id = Column(Integer, ForeignKey('eod_status.id'), nullable=False)
#     branch_id = Column(Integer, ForeignKey('branches.id'), nullable=False)
#     date = Column(Date, nullable=False)
#     total_transactions = Column(Integer, nullable=False, default=0)
#     total_buy_amount = Column(Numeric(20, 2), nullable=False, default=0)
#     total_sell_amount = Column(Numeric(20, 2), nullable=False, default=0)
#     total_adjust_amount = Column(Numeric(20, 2), nullable=False, default=0)
#     cash_out_amount = Column(Numeric(20, 2), nullable=False, default=0)
#     cash_out_operator_id = Column(Integer, ForeignKey('operators.id'))
#     cash_receiver_id = Column(Integer, ForeignKey('operators.id'))
#     created_at = Column(DateTime, default=func.now())
#     
#     # Relationships
#     branch = relationship('Branch', backref='eod_histories')
#     cash_out_operator = relationship('Operator', foreign_keys=[cash_out_operator_id], backref='cash_out_eods')
#     cash_receiver = relationship('Operator', foreign_keys=[cash_receiver_id], backref='received_cash_eods')
#     balance_snapshots = relationship('EODBalanceSnapshot', backref='eod_history')

# class EODBalanceSnapshot(Base):
#     __tablename__ = 'eod_balance_snapshot'
#
#     id = Column(Integer, primary_key=True)
#     eod_history_id = Column(Integer, ForeignKey('eod_history.id'), nullable=False)
#     currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False)
#     opening_balance = Column(Numeric(20, 2), nullable=False, default=0)
#     closing_balance = Column(Numeric(20, 2), nullable=False, default=0)
#     theoretical_balance = Column(Numeric(20, 2), nullable=False, default=0)
#     actual_balance = Column(Numeric(20, 2), nullable=False, default=0)
#     difference = Column(Numeric(20, 2), nullable=False, default=0)
#     cash_out_amount = Column(Numeric(20, 2), nullable=False, default=0)
#     remaining_balance = Column(Numeric(20, 2), nullable=False, default=0)
#     
#     # Relationships
#     currency = relationship('Currency', backref='balance_snapshots')

class EODBalanceVerification(Base):
    __tablename__ = 'eod_balance_verification'

    id = Column(Integer, primary_key=True, autoincrement=True)
    eod_status_id = Column(Integer, ForeignKey('eod_status.id'), nullable=False)
    currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False)
    opening_balance = Column(Numeric(20, 2), nullable=False, default=0)
    theoretical_balance = Column(Numeric(20, 2), nullable=False, default=0)
    actual_balance = Column(Numeric(20, 2), nullable=False, default=0)
    is_match = Column(Boolean, nullable=False, default=False)
    difference = Column(Numeric(20, 2), nullable=False, default=0)
    verified_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    currency = relationship('Currency', backref='balance_verifications')

class EODPrintLog(Base):
    __tablename__ = 'eod_print_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    eod_status_id = Column(Integer, ForeignKey('eod_status.id'), nullable=False)
    printed_by = Column(Integer, ForeignKey('operators.id'), nullable=False)
    printed_at = Column(DateTime, default=datetime.utcnow)
    mode = Column(String(10), nullable=False)  # simple, detailed
    print_count = Column(Integer, default=1)

    # Relationships
    printer = relationship('Operator', backref='print_logs')

class EODCashOut(Base):
    __tablename__ = 'eod_cash_out'

    id = Column(Integer, primary_key=True, autoincrement=True)
    eod_status_id = Column(Integer, ForeignKey('eod_status.id'), nullable=False)
    currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False)
    cash_out_amount = Column(Numeric(20, 2), nullable=False, default=0)
    remaining_balance = Column(Numeric(20, 2), nullable=False, default=0)
    transaction_id = Column(Integer, ForeignKey('exchange_transactions.id'))  # 关联的交款流水
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    currency = relationship('Currency', backref='cash_outs')
    transaction = relationship('ExchangeTransaction', backref='cash_out_records')

# 新增操作员活跃状态记录模型
class OperatorActivityLog(Base):
    __tablename__ = 'operator_activity_logs'
    
    id = Column(Integer, primary_key=True)
    operator_id = Column(Integer, ForeignKey('operators.id'), nullable=False)
    activity_type = Column(String(50), nullable=False)  # login, logout, action, idle, page_view
    activity_description = Column(Text)
    ip_address = Column(String(50))
    user_agent = Column(Text)
    session_id = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    branch_id = Column(Integer, ForeignKey('branches.id'))
    
    # Relationships
    operator = relationship("Operator", backref="activity_logs")
    branch = relationship("Branch")

# 新增权限国际化模型
class PermissionTranslation(Base):
    __tablename__ = 'permission_translations'
    
    id = Column(Integer, primary_key=True)
    permission_id = Column(Integer, ForeignKey('permissions.id'), nullable=False)
    language_code = Column(String(5), nullable=False)  # zh, en, th
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    permission = relationship("Permission", backref="translations")

class TransactionPurposeLimit(Base):
    """交易用途限额表"""
    __tablename__ = 'transaction_purpose_limits'

    id = Column(Integer, primary_key=True)
    branch_id = Column(Integer, ForeignKey('branches.id'), nullable=False)
    purpose_name = Column(String(50), nullable=False)
    currency_code = Column(String(10), nullable=False)
    max_amount = Column(Numeric(15, 2), nullable=False)
    display_message = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    branch = relationship("Branch", backref="purpose_limits")

    def to_dict(self):
        return {
            'id': self.id,
            'branch_id': self.branch_id,
            'purpose_name': self.purpose_name,
            'currency_code': self.currency_code,
            'max_amount': float(self.max_amount),
            'display_message': self.display_message,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ReceiptSequence(Base):
    """票据编号序列表 - 确保每个网点的票据编号连续性"""
    __tablename__ = 'receipt_sequences'

    id = Column(Integer, primary_key=True)
    branch_id = Column(Integer, ForeignKey('branches.id'), nullable=False, unique=True)
    current_sequence = Column(Integer, nullable=False, default=0)
    last_date = Column(Date, nullable=False, default=datetime.utcnow().date)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    branch = relationship("Branch", backref="receipt_sequence")

    def to_dict(self):
        return {
            'id': self.id,
            'branch_id': self.branch_id,
            'current_sequence': self.current_sequence,
            'last_date': self.last_date.isoformat() if self.last_date else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class PrintSettings(Base):
    """打印设置表"""
    __tablename__ = 'print_settings'
    
    id = Column(Integer, primary_key=True)
    branch_id = Column(Integer, ForeignKey('branches.id'), nullable=False)
    document_type = Column(String(50), nullable=False, default='exchange')  # 单据类型 exchange, reversal, balance_adjustment, eod_report
    layout_name = Column(String(50), nullable=False, default='表格格式')  # 新增：布局名称
    setting_key = Column(String(50), nullable=False)  # 设置键名
    setting_value = Column(Text, nullable=True)  # 设置值（字符串格式）
    description = Column(String(200), nullable=True)  # 设置说明
    is_default_layout = Column(Boolean, default=False, nullable=False)  # 新增：是否为默认布局
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 外键关系
    branch = relationship("Branch", back_populates="print_settings")
    
    # 更新复合唯一约束：包含布局名称
    __table_args__ = (
        UniqueConstraint('branch_id', 'document_type', 'layout_name', 'setting_key', name='uk_branch_document_layout_setting'),
    )

class BranchBalanceAlert(Base):
    """网点余额报警设置表"""
    __tablename__ = 'branch_balance_alerts'
    
    id = Column(Integer, primary_key=True)
    branch_id = Column(Integer, ForeignKey('branches.id'), nullable=False)
    currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False)
    min_threshold = Column(Numeric(15, 2), nullable=True)  # 最低报警阈值
    max_threshold = Column(Numeric(15, 2), nullable=True)  # 最高报警阈值
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 外键关系
    branch = relationship("Branch", backref="balance_alerts")
    currency = relationship("Currency", backref="balance_alerts")
    
    # 复合唯一约束：每个网点的每种币种只能有一个报警设置
    __table_args__ = (
        UniqueConstraint('branch_id', 'currency_id', name='uq_branch_currency_alert'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'branch_id': self.branch_id,
            'currency_id': self.currency_id,
            'min_threshold': float(self.min_threshold) if self.min_threshold else None,
            'max_threshold': float(self.max_threshold) if self.max_threshold else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class RatePublishRecord(Base):
    """汇率发布记录表"""
    __tablename__ = 'rate_publish_records'
    
    id = Column(Integer, primary_key=True)
    branch_id = Column(Integer, ForeignKey('branches.id'), nullable=False)
    publish_date = Column(Date, nullable=False)
    publish_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    publisher_id = Column(Integer, ForeignKey('operators.id'), nullable=False)
    publisher_name = Column(String(100), nullable=False)  # 冗余字段，便于查询
    total_currencies = Column(Integer, nullable=False, default=0)  # 发布的币种数量
    publish_theme = Column(String(20), default='light')  # 发布时的主题设置
    access_token = Column(String(100))  # 机顶盒访问token
    notes = Column(Text)  # 发布备注
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 外键关系
    branch = relationship("Branch", backref="rate_publish_records")
    publisher = relationship("Operator", backref="published_rates")
    details = relationship("RatePublishDetail", back_populates="publish_record", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'branch_id': self.branch_id,
            'publish_date': self.publish_date.isoformat() if self.publish_date else None,
            'publish_time': self.publish_time.isoformat() if self.publish_time else None,
            'publisher_id': self.publisher_id,
            'publisher_name': self.publisher_name,
            'total_currencies': self.total_currencies,
            'publish_theme': self.publish_theme,
            'access_token': self.access_token,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class RatePublishDetail(Base):
    """汇率发布详情表"""
    __tablename__ = 'rate_publish_details'
    
    id = Column(Integer, primary_key=True)
    publish_record_id = Column(Integer, ForeignKey('rate_publish_records.id'), nullable=False)
    currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False)
    currency_code = Column(String(3), nullable=False)  # 冗余字段，便于查询
    currency_name = Column(String(50), nullable=False)  # 冗余字段，便于查询
    buy_rate = Column(Numeric(10, 4), nullable=False)
    sell_rate = Column(Numeric(10, 4), nullable=False)
    sort_order = Column(Integer, default=0)  # 排序顺序
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 外键关系
    publish_record = relationship("RatePublishRecord", back_populates="details")
    currency = relationship("Currency", backref="publish_details")
    
    def to_dict(self):
        return {
            'id': self.id,
            'publish_record_id': self.publish_record_id,
            'currency_id': self.currency_id,
            'currency_code': self.currency_code,
            'currency_name': self.currency_name,
            'buy_rate': float(self.buy_rate) if self.buy_rate else 0,
            'sell_rate': float(self.sell_rate) if self.sell_rate else 0,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class DenominationPublishDetail(Base):
    """面值汇率发布详情表"""
    __tablename__ = 'denomination_publish_details'
    
    id = Column(Integer, primary_key=True)
    publish_record_id = Column(Integer, ForeignKey('rate_publish_records.id'), nullable=False)
    currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False)
    denomination_id = Column(Integer, ForeignKey('currency_denominations.id'), nullable=False)
    denomination_value = Column(Numeric(15, 2), nullable=False)  # 面值金额
    denomination_type = Column(String(20), nullable=False)  # 'bill' 纸币 或 'coin' 硬币
    buy_rate = Column(Numeric(10, 4), nullable=False)
    sell_rate = Column(Numeric(10, 4), nullable=False)
    sort_order = Column(Integer, default=0)  # 排序顺序
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 外键关系
    publish_record = relationship("RatePublishRecord", backref="denomination_details")
    currency = relationship("Currency", backref="denomination_publish_details")
    # Note: CurrencyDenomination is defined in denomination_models.py
    # This relationship requires both models to be imported together
    # denomination = relationship("CurrencyDenomination", backref="publish_details", foreign_keys=[denomination_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'publish_record_id': self.publish_record_id,
            'currency_id': self.currency_id,
            'denomination_id': self.denomination_id,
            'denomination_value': float(self.denomination_value) if self.denomination_value else 0,
            'denomination_type': self.denomination_type,
            'buy_rate': float(self.buy_rate) if self.buy_rate else 0,
            'sell_rate': float(self.sell_rate) if self.sell_rate else 0,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class TransactionAlert(Base):
    """交易报警事件表"""
    __tablename__ = 'transaction_alerts'
    
    id = Column(Integer, primary_key=True)
    branch_id = Column(Integer, ForeignKey('branches.id'), nullable=False)
    currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False)
    operator_id = Column(Integer, ForeignKey('operators.id'), nullable=False)
    alert_type = Column(String(50), nullable=False)  # threshold_min, threshold_max, insufficient_balance
    alert_level = Column(String(20), nullable=False)  # warning, critical
    current_balance = Column(Numeric(15, 2), nullable=False)
    threshold_value = Column(Numeric(15, 2), nullable=True)  # 阈值，余额不足时为null
    transaction_amount = Column(Numeric(15, 2), nullable=False)  # 引起报警的交易金额
    transaction_type = Column(String(20), nullable=False)  # buy, sell
    after_balance = Column(Numeric(15, 2), nullable=False)  # 交易后余额
    message = Column(Text, nullable=False)  # 报警消息
    is_resolved = Column(Boolean, default=False, nullable=False)  # 是否已解决
    resolved_at = Column(DateTime, nullable=True)  # 解决时间
    resolved_by = Column(Integer, ForeignKey('operators.id'), nullable=True)  # 解决人
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 外键关系
    branch = relationship("Branch", backref="transaction_alerts")
    currency = relationship("Currency", backref="transaction_alerts")
    operator = relationship("Operator", foreign_keys=[operator_id], backref="created_alerts")
    resolver = relationship("Operator", foreign_keys=[resolved_by], backref="resolved_alerts")
    
    def to_dict(self):
        return {
            'id': self.id,
            'branch_id': self.branch_id,
            'currency_id': self.currency_id,
            'operator_id': self.operator_id,
            'alert_type': self.alert_type,
            'alert_level': self.alert_level,
            'current_balance': float(self.current_balance),
            'threshold_value': float(self.threshold_value) if self.threshold_value else None,
            'transaction_amount': float(self.transaction_amount),
            'transaction_type': self.transaction_type,
            'after_balance': float(self.after_balance),
            'message': self.message,
            'is_resolved': self.is_resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolved_by': self.resolved_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class BranchOperatingStatus(Base):
    """网点营业状态表 - 控制期初设置和营业数据管理"""
    __tablename__ = 'branch_operating_status'
    
    id = Column(Integer, primary_key=True)
    branch_id = Column(Integer, ForeignKey('branches.id'), nullable=False, unique=True)
    is_initial_setup_completed = Column(Boolean, default=False, nullable=False)  # 是否完成期初设置
    initial_setup_date = Column(DateTime, nullable=True)  # 期初设置完成时间
    initial_setup_by = Column(Integer, ForeignKey('operators.id'), nullable=True)  # 期初设置操作员
    last_data_reset_date = Column(DateTime, nullable=True)  # 最后一次数据重置时间
    last_data_reset_by = Column(Integer, ForeignKey('operators.id'), nullable=True)  # 数据重置操作员
    data_reset_count = Column(Integer, default=0, nullable=False)  # 数据重置次数
    operating_start_date = Column(Date, nullable=True)  # 营业开始日期
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 外键关系
    branch = relationship("Branch", backref="operating_status")
    initial_setup_operator = relationship("Operator", foreign_keys=[initial_setup_by], backref="initial_setups")
    last_reset_operator = relationship("Operator", foreign_keys=[last_data_reset_by], backref="data_resets")

    def to_dict(self):
        return {
            'id': self.id,
            'branch_id': self.branch_id,
            'is_initial_setup_completed': self.is_initial_setup_completed,
            'initial_setup_date': self.initial_setup_date.isoformat() if self.initial_setup_date else None,
            'initial_setup_by': self.initial_setup_by,
            'last_data_reset_date': self.last_data_reset_date.isoformat() if self.last_data_reset_date else None,
            'last_data_reset_by': self.last_data_reset_by,
            'data_reset_count': self.data_reset_count,
            'operating_start_date': self.operating_start_date.isoformat() if self.operating_start_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class PrintTemplate(Base):
    """打印模板表"""
    __tablename__ = 'print_templates'
    
    id = Column(Integer, primary_key=True)
    branch_id = Column(Integer, ForeignKey('branches.id'), nullable=False)
    document_type = Column(String(50), nullable=False, default='exchange')
    layout_name = Column(String(50), nullable=False)
    settings_json = Column(Text)
    description = Column(String(200))
    is_default_layout = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 外键关系
    branch = relationship("Branch", backref="print_templates")
    
    # 复合唯一约束
    __table_args__ = (
        UniqueConstraint('branch_id', 'document_type', 'layout_name', name='uq_branch_document_layout'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'branch_id': self.branch_id,
            'document_type': self.document_type,
            'layout_name': self.layout_name,
            'settings_json': self.settings_json,
            'description': self.description,
            'is_default_layout': self.is_default_layout,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class EODStepAction(Base):
    """日结步骤操作记录表"""
    __tablename__ = 'eod_step_actions'
    
    id = Column(Integer, primary_key=True)
    eod_status_id = Column(Integer, ForeignKey('eod_status.id'), nullable=False)
    step_number = Column(Integer, nullable=False)
    action_type = Column(String(50), nullable=False)
    action_data = Column(Text)
    rollback_data = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('operators.id'), nullable=False)
    
    # 外键关系
    eod_status = relationship("EODStatus", backref="step_actions")
    creator = relationship("Operator", backref="eod_step_actions")

    def to_dict(self):
        return {
            'id': self.id,
            'eod_status_id': self.eod_status_id,
            'step_number': self.step_number,
            'action_type': self.action_type,
            'action_data': self.action_data,
            'rollback_data': self.rollback_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by
        }

class SystemConfig(Base):
    """系统配置表 - 用于存储各种系统配置，包括特性开关"""
    __tablename__ = 'system_configs'
    
    id = Column(Integer, primary_key=True)
    config_key = Column(String(100), nullable=False)  # 配置键
    config_value = Column(Text, nullable=True)  # 配置值
    config_category = Column(String(50), nullable=False, default='general')  # 配置分类
    description = Column(String(500), nullable=True)  # 配置描述
    is_active = Column(Boolean, default=True, nullable=False)  # 是否启用
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 复合唯一约束：配置键 + 分类
    __table_args__ = (
        UniqueConstraint('config_key', 'config_category', name='uk_config_key_category'),
    )
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'config_key': self.config_key,
            'config_value': self.config_value,
            'config_category': self.config_category,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class EODSessionLock(Base):
    """日结会话锁定表 - 确保只有单一终端可以进行日结"""
    __tablename__ = 'eod_session_locks'

    id = Column(Integer, primary_key=True)
    branch_id = Column(Integer, ForeignKey('branches.id'), nullable=False)
    eod_status_id = Column(Integer, ForeignKey('eod_status.id'), nullable=False)
    session_id = Column(String(100), nullable=False)  # 会话ID
    operator_id = Column(Integer, ForeignKey('operators.id'), nullable=False)
    ip_address = Column(String(50), nullable=False)  # IP地址
    user_agent = Column(Text)  # 用户代理
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # 外键关系
    branch = relationship("Branch", backref="eod_session_locks")
    eod_status = relationship("EODStatus", backref="session_locks")
    operator = relationship("Operator", backref="eod_session_locks")

    # 复合唯一约束：每个网点只能有一个活跃的日结会话
    __table_args__ = (
        UniqueConstraint('branch_id', 'is_active', name='uq_branch_active_eod_session'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'branch_id': self.branch_id,
            'eod_status_id': self.eod_status_id,
            'session_id': self.session_id,
            'operator_id': self.operator_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'is_active': self.is_active
        }

class Country(Base):
    """国家信息表 - 支持多语言国家名称"""
    __tablename__ = 'countries'

    id = Column(Integer, primary_key=True)
    country_code = Column(String(2), unique=True, nullable=False)  # ISO 3166-1 alpha-2国家代码
    country_name_zh = Column(String(100), nullable=False)  # 中文国家名
    country_name_en = Column(String(100), nullable=False)  # 英文国家名
    country_name_th = Column(String(100))  # 泰文国家名
    phone_code = Column(String(10))  # 电话区号
    currency_code = Column(String(3))  # 主要货币代码
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0)  # 排序顺序
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'country_code': self.country_code,
            'country_name_zh': self.country_name_zh,
            'country_name_en': self.country_name_en,
            'country_name_th': self.country_name_th,
            'phone_code': self.phone_code,
            'currency_code': self.currency_code,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
