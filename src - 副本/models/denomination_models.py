from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, Date, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# 导入相同的Base，确保所有模型都注册到同一个metadata中
from .exchange_models import Base

class CurrencyDenomination(Base):
    """币种面值表"""
    __tablename__ = 'currency_denominations'

    id = Column(Integer, primary_key=True)
    currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False)
    denomination_value = Column(Numeric(15, 2), nullable=False)  # 面值金额
    denomination_type = Column(String(20), nullable=False)  # 'bill' 纸币 或 'coin' 硬币
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 外键关系
    currency = relationship("Currency", backref="denominations")
    
    # 复合唯一约束：每个币种的每种面值只能有一条记录
    __table_args__ = (
        UniqueConstraint('currency_id', 'denomination_value', 'denomination_type', name='uq_currency_denomination'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'currency_id': self.currency_id,
            'denomination_value': float(self.denomination_value),
            'denomination_type': self.denomination_type,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class DenominationRate(Base):
    """面值汇率表"""
    __tablename__ = 'denomination_rates'

    id = Column(Integer, primary_key=True)
    branch_id = Column(Integer, ForeignKey('branches.id'), nullable=False)
    currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False)
    denomination_id = Column(Integer, ForeignKey('currency_denominations.id'), nullable=False)
    rate_date = Column(Date, nullable=False)
    buy_rate = Column(Numeric(10, 4), nullable=False)
    sell_rate = Column(Numeric(10, 4), nullable=False)
    created_by = Column(Integer, ForeignKey('operators.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sort_order = Column(Integer, default=0)
    
    # 外键关系
    branch = relationship("Branch", backref="denomination_rates")
    currency = relationship("Currency", backref="denomination_rates")
    denomination = relationship("CurrencyDenomination", backref="rates")
    operator = relationship("Operator", backref="denomination_rates")
    
    # 复合唯一约束：每个网点每个币种每个面值每天只能有一条记录
    __table_args__ = (
        UniqueConstraint('branch_id', 'currency_id', 'denomination_id', 'rate_date', name='uq_denomination_rate'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'branch_id': self.branch_id,
            'currency_id': self.currency_id,
            'denomination_id': self.denomination_id,
            'denomination_value': float(self.denomination.denomination_value) if self.denomination else None,
            'denomination_type': self.denomination.denomination_type if self.denomination else None,
            'rate_date': self.rate_date.isoformat() if self.rate_date else None,
            'buy_rate': float(self.buy_rate),
            'sell_rate': float(self.sell_rate),
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'sort_order': self.sort_order
        }

class TransactionDenomination(Base):
    """交易面值详情表"""
    __tablename__ = 'transaction_denominations'

    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey('exchange_transactions.id'), nullable=False)
    denomination_id = Column(Integer, ForeignKey('currency_denominations.id'), nullable=False)
    quantity = Column(Integer, nullable=False)  # 张数/枚数
    total_amount = Column(Numeric(15, 2), nullable=False)  # 总金额
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 外键关系
    transaction = relationship("ExchangeTransaction", backref="denomination_details")
    denomination = relationship("CurrencyDenomination", backref="transaction_details")
    
    def to_dict(self):
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'denomination_id': self.denomination_id,
            'denomination_value': float(self.denomination.denomination_value) if self.denomination else None,
            'denomination_type': self.denomination.denomination_type if self.denomination else None,
            'quantity': self.quantity,
            'total_amount': float(self.total_amount),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }