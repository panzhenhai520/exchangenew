# 在 models/exchange_models.py 中添加批次管理模型

class PublishBatch(Base):
    """发布批次管理"""
    __tablename__ = 'publish_batches'
    
    id = Column(Integer, primary_key=True)
    batch_id = Column(String(50), unique=True, nullable=False, comment='批次ID')
    branch_id = Column(Integer, ForeignKey('branches.id'), nullable=False, comment='网点ID')
    publisher_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='发布者ID')
    publisher_name = Column(String(100), nullable=False, comment='发布者姓名')
    batch_type = Column(String(20), nullable=False, comment='批次类型：denomination_rates')
    total_currencies = Column(Integer, nullable=False, comment='总币种数')
    total_denominations = Column(Integer, nullable=False, comment='总面值数')
    publish_time = Column(DateTime, nullable=False, comment='发布时间')
    publish_date = Column(Date, nullable=False, comment='发布日期')
    theme = Column(String(20), default='light', comment='主题')
    language = Column(String(10), default='zh', comment='语言')
    display_config = Column(Text, comment='显示配置JSON')
    notes = Column(Text, comment='备注')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

class BatchCurrencyToken(Base):
    """批次币种Token映射"""
    __tablename__ = 'batch_currency_tokens'
    
    id = Column(Integer, primary_key=True)
    batch_id = Column(String(50), ForeignKey('publish_batches.batch_id'), nullable=False, comment='批次ID')
    currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False, comment='币种ID')
    currency_code = Column(String(10), nullable=False, comment='币种代码')
    access_token = Column(String(100), nullable=False, comment='访问Token')
    denomination_count = Column(Integer, nullable=False, comment='面值数量')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

