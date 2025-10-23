#!/usr/bin/env python3
"""
报表相关数据模型
包含：
- 日收入报表模型
- 日库存报表模型
- 合规触发规则模型
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, Text, ForeignKey
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


class TriggerRule(Base):
    """触发规则配置（AMLO/BOT）"""
    __tablename__ = 'trigger_rules'

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_name = Column(String(200), nullable=False, comment='规则名称(中文)')
    rule_name_en = Column(String(200), comment='规则名称(英文)')
    rule_name_th = Column(String(200), comment='规则名称(泰文)')

    report_type = Column(String(50), nullable=False, comment='报告类型(AMLO-1-01/BOT_BuyFX等)')
    rule_expression = Column(Text, nullable=False, comment='规则表达式(JSON格式)')

    description_cn = Column(Text, comment='规则描述(中文)')
    description_en = Column(Text, comment='规则描述(英文)')
    description_th = Column(Text, comment='规则描述(泰文)')

    priority = Column(Integer, default=50, comment='优先级(数值越大优先级越高)')
    allow_continue = Column(Boolean, default=True, comment='触发后是否允许继续交易')

    warning_message_cn = Column(String(500), comment='警告消息(中文)')
    warning_message_en = Column(String(500), comment='警告消息(英文)')
    warning_message_th = Column(String(500), comment='警告消息(泰文)')

    # 别名字段，与warning_message_*功能相同
    message_cn = Column(String(500), comment='提示消息(中文)')
    message_en = Column(String(500), comment='提示消息(英文)')
    message_th = Column(String(500), comment='提示消息(泰文)')

    branch_id = Column(Integer, ForeignKey('branches.id'), nullable=True, comment='网点ID(NULL表示全局规则)')
    is_active = Column(Boolean, default=True, comment='是否启用')

    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    def to_dict(self):
        """转换为字典格式"""
        import json

        # 解析rule_expression JSON
        rule_expression_obj = {}
        if self.rule_expression:
            try:
                rule_expression_obj = json.loads(self.rule_expression)
            except:
                rule_expression_obj = {}

        return {
            'id': self.id,
            'rule_name': self.rule_name,
            'rule_name_en': self.rule_name_en,
            'rule_name_th': self.rule_name_th,
            'report_type': self.report_type,
            'rule_expression': rule_expression_obj,
            'description_cn': self.description_cn,
            'description_en': self.description_en,
            'description_th': self.description_th,
            'priority': self.priority,
            'allow_continue': self.allow_continue,
            'warning_message_cn': self.warning_message_cn,
            'warning_message_en': self.warning_message_en,
            'warning_message_th': self.warning_message_th,
            'message_cn': self.message_cn,
            'message_en': self.message_en,
            'message_th': self.message_th,
            'branch_id': self.branch_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }