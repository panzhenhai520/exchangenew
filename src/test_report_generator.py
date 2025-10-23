#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('.')

from services.db_service import DatabaseService
from services.report_number_generator import ReportNumberGenerator

def test_report_generator():
    """测试报告编号生成器"""
    session = DatabaseService.get_session()
    
    try:
        print("=== 测试AMLO报告编号生成器 ===")
        
        # 测试参数
        branch_id = 1  # 假设网点ID为1
        currency_code = 'USD'
        operator_id = 1
        
        # 生成AMLO报告编号
        report_number = ReportNumberGenerator.generate_amlo_report_number(
            session=session,
            branch_id=branch_id,
            currency_code=currency_code,
            operator_id=operator_id
        )
        
        print(f"生成的AMLO报告编号: {report_number}")
        
        # 解析报告编号
        parsed_info = ReportNumberGenerator.parse_report_number(report_number)
        print(f"解析结果: {parsed_info}")
        
        # 验证报告编号
        is_valid = ReportNumberGenerator.validate_report_number(report_number, 'AMLO')
        print(f"验证结果: {is_valid}")
        
        # 再次生成一个编号（测试序列号递增）
        report_number2 = ReportNumberGenerator.generate_amlo_report_number(
            session=session,
            branch_id=branch_id,
            currency_code=currency_code,
            operator_id=operator_id
        )
        
        print(f"第二个AMLO报告编号: {report_number2}")
        
        # 测试不同币种
        eur_number = ReportNumberGenerator.generate_amlo_report_number(
            session=session,
            branch_id=branch_id,
            currency_code='EUR',
            operator_id=operator_id
        )
        
        print(f"EUR币种报告编号: {eur_number}")
        
        print("\n=== 测试BOT报告编号生成器 ===")
        
        # 生成BOT报告编号
        bot_number = ReportNumberGenerator.generate_bot_report_number(
            session=session,
            branch_id=branch_id,
            report_type='BuyFX',
            operator_id=operator_id
        )
        
        print(f"生成的BOT报告编号: {bot_number}")
        
        # 解析BOT报告编号
        bot_parsed = ReportNumberGenerator.parse_report_number(bot_number)
        print(f"BOT解析结果: {bot_parsed}")
        
        # 验证BOT报告编号
        bot_valid = ReportNumberGenerator.validate_report_number(bot_number, 'BOT')
        print(f"BOT验证结果: {bot_valid}")
        
        print("\n=== 测试统计信息 ===")
        
        # 获取统计信息
        stats = ReportNumberGenerator.get_sequence_statistics(session, branch_id)
        print(f"统计信息: {stats}")
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"测试失败: {e}")
        raise e
    finally:
        session.close()

if __name__ == '__main__':
    test_report_generator()



