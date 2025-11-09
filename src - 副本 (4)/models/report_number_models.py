#!/usr/bin/env python3
"""
报告编号管理相关数据模型
包含：
- AMLO报告编号序列表
- BOT报告编号序列表
- 报告编号生成规则管理
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, Text, ForeignKey, UniqueConstraint, Index
from sqlalchemy.types import DECIMAL
from datetime import datetime

# 导入相同的Base，确保所有模型都注册到同一个metadata中
from .exchange_models import Base

class AMLOReportSequence(Base):
    """AMLO报告编号序列表"""
    __tablename__ = 'amlo_report_sequences'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    branch_id = Column(Integer, nullable=False, comment='网点ID')
    currency_code = Column(String(3), nullable=False, comment='币种代码(ISO 4217)')
    year_month = Column(String(7), nullable=False, comment='年月(YYYY-MM)')
    current_sequence = Column(Integer, nullable=False, default=0, comment='当前序列号')
    last_used_at = Column(DateTime, default=datetime.now, comment='最后使用时间')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 唯一约束：每个网点+币种+年月只能有一个序列
    __table_args__ = (
        UniqueConstraint('branch_id', 'currency_code', 'year_month', name='uk_branch_currency_month'),
        Index('idx_branch_currency_month', 'branch_id', 'currency_code', 'year_month'),
        Index('idx_year_month', 'year_month'),
    )

class BOTReportSequence(Base):
    """BOT报告编号序列表"""
    __tablename__ = 'bot_report_sequences'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    branch_id = Column(Integer, nullable=False, comment='网点ID')
    report_type = Column(String(20), nullable=False, comment='报告类型(BuyFX/SellFX/FCD)')
    year_month = Column(String(7), nullable=False, comment='年月(YYYY-MM)')
    current_sequence = Column(Integer, nullable=False, default=0, comment='当前序列号')
    last_used_at = Column(DateTime, default=datetime.now, comment='最后使用时间')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 唯一约束：每个网点+报告类型+年月只能有一个序列
    __table_args__ = (
        UniqueConstraint('branch_id', 'report_type', 'year_month', name='uk_branch_type_month'),
        Index('idx_branch_type_month', 'branch_id', 'report_type', 'year_month'),
        Index('idx_year_month', 'year_month'),
    )

class ReportNumberLog(Base):
    """报告编号使用日志表"""
    __tablename__ = 'report_number_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_number = Column(String(50), nullable=False, comment='生成的报告编号')
    report_type = Column(String(20), nullable=False, comment='报告类型(AMLO/BOT)')
    branch_id = Column(Integer, nullable=False, comment='网点ID')
    currency_code = Column(String(3), nullable=True, comment='币种代码(仅AMLO报告)')
    sequence_id = Column(Integer, nullable=False, comment='关联的序列记录ID')
    transaction_id = Column(Integer, nullable=True, comment='关联的交易ID')
    operator_id = Column(Integer, nullable=False, comment='操作员ID')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    # 索引
    __table_args__ = (
        Index('idx_report_number', 'report_number'),
        Index('idx_branch_date', 'branch_id', 'created_at'),
        Index('idx_sequence_id', 'sequence_id'),
    )





