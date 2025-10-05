#!/usr/bin/env python3
"""
报表相关数据模型
包含：
- 日收入报表模型
- 日库存报表模型
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean
from sqlalchemy.types import DECIMAL
from datetime import datetime

# 导入相同的Base，确保所有模型都注册到同一个metadata中
from .exchange_models import Base

class DailyIncomeReport(Base):
    """日收入报表"""
    __tablename__ = 'daily_income_reports'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_date = Column(Date, nullable=False, comment='报表日期')
    branch_id = Column(Integer, nullable=False, comment='网点ID')
    currency_code = Column(String(10), nullable=False, comment='外币币种')
    base_currency = Column(String(10), nullable=False, comment='本币币种')
    
    # 交易统计
    total_buy = Column(DECIMAL(15,2), nullable=False, default=0, comment='当日买入外币总量')
    total_sell = Column(DECIMAL(15,2), nullable=False, default=0, comment='当日卖出外币总量(绝对值)')
    buy_rate = Column(DECIMAL(10,4), nullable=False, default=0, comment='平均买入汇率')
    sell_rate = Column(DECIMAL(10,4), nullable=False, default=0, comment='平均卖出汇率')
    
    # 收益计算
    income = Column(DECIMAL(15,2), nullable=False, default=0, comment='实际净收入(本币)')
    spread_income = Column(DECIMAL(15,2), nullable=False, default=0, comment='估算点差收益(本币)')
    
    # 状态控制
    is_final = Column(Boolean, default=False, comment='是否为正式日结数据')
    eod_id = Column(Integer, nullable=True, comment='关联日结ID')
    generated_at = Column(DateTime, default=datetime.now, comment='报表生成时间')
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'report_date': self.report_date.isoformat() if self.report_date else None,
            'branch_id': self.branch_id,
            'currency_code': self.currency_code,
            'base_currency': self.base_currency,
            'total_buy': float(self.total_buy) if self.total_buy else 0.0,
            'total_sell': float(self.total_sell) if self.total_sell else 0.0,
            'buy_rate': float(self.buy_rate) if self.buy_rate else 0.0,
            'sell_rate': float(self.sell_rate) if self.sell_rate else 0.0,
            'income': float(self.income) if self.income else 0.0,
            'spread_income': float(self.spread_income) if self.spread_income else 0.0,
            'is_final': self.is_final,
            'eod_id': self.eod_id,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None
        }

class DailyForeignStock(Base):
    """日库存报表"""
    __tablename__ = 'daily_foreign_stock'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_date = Column(Date, nullable=False, comment='报表日期')
    branch_id = Column(Integer, nullable=False, comment='网点ID')
    currency_code = Column(String(10), nullable=False, comment='外币币种')
    base_currency = Column(String(10), nullable=False, comment='本币币种')
    
    # 交易统计
    total_buy = Column(DECIMAL(15,2), nullable=False, default=0, comment='累计买入外币总量')
    total_sell = Column(DECIMAL(15,2), nullable=False, default=0, comment='累计卖出外币总量(绝对值)')
    
    # 库存统计
    opening_balance = Column(DECIMAL(15,2), nullable=False, default=0, comment='期初余额')
    change_amount = Column(DECIMAL(15,2), nullable=False, default=0, comment='变动金额')
    current_balance = Column(DECIMAL(15,2), nullable=False, default=0, comment='当前余额')
    stock_balance = Column(DECIMAL(15,2), nullable=False, default=0, comment='剩余库存外币数量')
    
    # 状态控制
    is_final = Column(Boolean, default=False, comment='是否为正式日结数据')
    eod_id = Column(Integer, nullable=True, comment='关联日结ID')
    generated_at = Column(DateTime, default=datetime.now, comment='报表生成时间')
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'report_date': self.report_date.isoformat() if self.report_date else None,
            'branch_id': self.branch_id,
            'currency_code': self.currency_code,
            'base_currency': self.base_currency,
            'total_buy': float(self.total_buy) if self.total_buy else 0.0,
            'total_sell': float(self.total_sell) if self.total_sell else 0.0,
            'opening_balance': float(self.opening_balance) if self.opening_balance else 0.0,
            'change_amount': float(self.change_amount) if self.change_amount else 0.0,
            'current_balance': float(self.current_balance) if self.current_balance else 0.0,
            'stock_balance': float(self.stock_balance) if self.stock_balance else 0.0,
            'is_final': self.is_final,
            'eod_id': self.eod_id,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None
        }

class DailyStockReport(Base):
    """日库存报表"""
    __tablename__ = 'daily_stock_reports'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_date = Column(Date, nullable=False, comment='报表日期')
    branch_id = Column(Integer, nullable=False, comment='网点ID')
    currency_code = Column(String(10), nullable=False, comment='外币币种')
    base_currency = Column(String(10), nullable=False, comment='本币币种')
    
    # 库存统计
    total_buy = Column(DECIMAL(15,2), nullable=False, default=0, comment='当日买入外币总量')
    total_sell = Column(DECIMAL(15,2), nullable=False, default=0, comment='当日卖出外币总量')
    total_initial = Column(DECIMAL(15,2), nullable=False, default=0, comment='期初余额')
    total_adjust = Column(DECIMAL(15,2), nullable=False, default=0, comment='调节金额')
    total_cash_out = Column(DECIMAL(15,2), nullable=False, default=0, comment='交款金额')
    stock_balance = Column(DECIMAL(15,2), nullable=False, default=0, comment='库存余额')
    
    # 状态控制
    is_final = Column(Boolean, default=False, comment='是否为正式日结数据')
    eod_id = Column(Integer, nullable=True, comment='关联日结ID')
    generated_at = Column(DateTime, default=datetime.now, comment='报表生成时间')
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'report_date': self.report_date.isoformat() if self.report_date else None,
            'branch_id': self.branch_id,
            'currency_code': self.currency_code,
            'base_currency': self.base_currency,
            'total_buy': float(self.total_buy) if self.total_buy else 0.0,
            'total_sell': float(self.total_sell) if self.total_sell else 0.0,
            'total_initial': float(self.total_initial) if self.total_initial else 0.0,
            'total_adjust': float(self.total_adjust) if self.total_adjust else 0.0,
            'total_cash_out': float(self.total_cash_out) if self.total_cash_out else 0.0,
            'stock_balance': float(self.stock_balance) if self.stock_balance else 0.0,
            'is_final': self.is_final,
            'eod_id': self.eod_id,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None
        } 