#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日结报表PDF生成器 - 专业样式版本  
专门处理日结相关报表的PDF生成，具有完整的报表格式和专业样式
"""

import logging
from datetime import datetime
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from .pdf_base import PDFBase
import os
import json
import glob
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from services.db_service import DatabaseService
from models.exchange_models import Currency

logger = logging.getLogger(__name__)

# 导入统一的币种翻译服务
from .currency_translation_service import CurrencyTranslationService

def get_currency_name(currency_code, language='zh'):
    """获取币种的多语言名称"""
    return CurrencyTranslationService.get_currency_name(currency_code, language)

class EODReportPDFGenerator(PDFBase):
    """日结报表PDF生成器"""
    
    # 统一表格宽度常量
    TABLE_TOTAL_WIDTH = 160 * mm
    
    @staticmethod
    def _get_branch_info(branch_id):
        """根据branch_id获取网点信息"""
        try:
            from services.db_service import DatabaseService
            from models.exchange_models import Branch
            
            session = DatabaseService.get_session()
            try:
                branch = session.query(Branch).filter_by(id=branch_id).first()
                if branch:
                    return {
                        'branch_code': branch.branch_code,
                        'branch_name': branch.branch_name
                    }
                else:
                    logger.warning(f"未找到branch_id={branch_id}的网点信息")
                    return {
                        'branch_code': 'N/A',
                        'branch_name': '未知网点'
                    }
            finally:
                DatabaseService.close_session(session)
        except Exception as e:
            logger.error(f"获取网点信息失败: {e}")
            return {
                'branch_code': 'N/A', 
                'branch_name': '未知网点'
            }
    
    @staticmethod
    def generate_pdf(report_data, file_path):
        """生成日结报表PDF文件"""
        try:
            report_type = report_data.get('report_type', 'income')
            
            if report_type == 'income' or report_type == 'eod_income':
                return EODReportPDFGenerator._generate_comprehensive_eod_report(report_data, file_path)
            else:
                logger.error(f"不支持的报表类型: {report_type}")
                return False
                
        except Exception as e:
            logger.error(f"生成日结报表PDF失败: {e}")
            return False
    
    @staticmethod
    def _generate_comprehensive_eod_report(report_data, file_path):
        """生成综合日结报表PDF（包含收入统计、外币库存、本币库存）"""
        try:
            # 【新增】多语言支持 - 根据report_data中的language参数选择字体和文本
            language = report_data.get('language', 'zh')  # 默认中文
            font_name = EODReportPDFGenerator.init_fonts(language)
            styles = EODReportPDFGenerator.get_styles(font_name)
            
            # 创建PDF文档
            doc = EODReportPDFGenerator.create_pdf_doc(file_path)
            
            # 构建PDF内容
            story = []
            
            # 【修复】从content.header中提取正确的信息
            content = report_data.get('content', {})
            header = content.get('header', {})
            
            # 获取报表数据 - 优先从header中获取，然后从根级别获取
            eod_date = header.get('date') or report_data.get('eod_date', report_data.get('date', datetime.now().date()))
            eod_id = header.get('eod_id') or report_data.get('eod_id', 'N/A')
            branch_id = header.get('branch_id') or report_data.get('branch_id')
            
            # 【新增】获取时间范围信息
            time_range = report_data.get('time_range')
            start_time = time_range.get('start_time') if time_range else None
            end_time = time_range.get('end_time') if time_range else None
            
            # 【调试】记录时间范围数据获取情况
            logger.info(f"🔍 PDF数据接收检查:")
            logger.info(f"  - time_range对象: {time_range}")
            logger.info(f"  - start_time: {start_time} ({type(start_time)})")
            logger.info(f"  - end_time: {end_time} ({type(end_time)})")
            logger.info(f"  - eod_date: {eod_date} ({type(eod_date)})")
            
            # 【修复】获取真实的网点信息
            if branch_id:
                branch_info = EODReportPDFGenerator._get_branch_info(branch_id)
                branch_display = f"{branch_info['branch_code']} {branch_info['branch_name']}"
            else:
                branch_display = report_data.get('branch_name', '未知网点')
            
            # 【修复】处理不同的数据结构 - 支持两种数据格式
            if content and content.get('sections'):
                # 新的结构化数据格式（content.sections）
                income_reports = EODReportPDFGenerator._extract_income_reports_from_content(content)
                stock_reports = EODReportPDFGenerator._extract_stock_reports_from_content(content)
                base_currency_data = EODReportPDFGenerator._extract_base_currency_from_content(content)
            else:
                # 直接的数据格式（income_reports, stock_reports）
                income_reports = report_data.get('income_reports', [])
                stock_reports = report_data.get('stock_reports', [])
                base_currency_data = report_data.get('base_currency_data', {})
                
                # 【新增】如果没有base_currency_data，尝试从content中提取
                if not base_currency_data and content:
                    base_currency_data = content
            
            # 【调试】记录数据状态
            logger.info(f"PDF数据状态 - 收入报表: {len(income_reports)}, 库存报表: {len(stock_reports)}, 本币数据: {'有' if base_currency_data else '无'}")
            
            # 报表头部
            story.extend(EODReportPDFGenerator._create_report_header(eod_date, eod_id, branch_display, start_time, end_time, styles, language))
            
            # 【修复】外币收入统计表格 - 总是显示，即使是负收入
            if income_reports and len(income_reports) > 0:
                story.extend(EODReportPDFGenerator._create_income_statistics_table(income_reports, font_name, styles, language))
            else:
                # 显示空的收入统计表格
                empty_income_text = EODReportPDFGenerator._get_text('no_foreign_income', language)
                story.append(Paragraph(EODReportPDFGenerator._get_text('foreign_income_title', language), styles["section_title"]))
                story.append(Spacer(1, 10))
                story.append(Paragraph(empty_income_text, styles["normal"]))
            story.append(Spacer(1, 15))
            
            # 【修复】外币库存统计表格 - 总是显示，已排除本币
            if stock_reports and len(stock_reports) > 0:
                story.extend(EODReportPDFGenerator._create_foreign_stock_table(stock_reports, font_name, styles, language))
            else:
                # 显示空的库存统计表格
                empty_stock_text = EODReportPDFGenerator._get_text('no_foreign_stock', language)
                story.append(Paragraph(EODReportPDFGenerator._get_text('foreign_stock_title', language), styles["section_title"]))
                story.append(Spacer(1, 10))
                story.append(Paragraph(empty_stock_text, styles["normal"]))
            story.append(Spacer(1, 15))
            
            # 本币库存统计表格
            if base_currency_data:
                story.extend(EODReportPDFGenerator._create_base_currency_table(base_currency_data, font_name, styles, language))
            
            # 签名区域
            story.extend(EODReportPDFGenerator._create_signature_section(styles, language))
            
            # 生成PDF
            doc.build(story)
            
            logger.info(f"综合日结报表PDF生成成功: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"生成综合日结报表PDF失败: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return False
    
    @staticmethod
    def _extract_income_reports_from_content(content):
        """从结构化内容中提取收入报表数据"""
        income_reports = []
        try:
            sections = content.get('sections', [])
            for section in sections:
                # 【修复】匹配section的type而不是title，因为title可能会变化
                if section.get('type') == 'income' or section.get('title') in ['收入统计', '各币种收入统计']:
                    data = section.get('data', [])
                    for item in data:
                        if isinstance(item, dict) and 'currency_code' in item:
                            income_reports.append({
                                'currency_code': item.get('currency_code', ''),
                                'buy_amount': float(item.get('buy_amount', 0)),
                                'sell_amount': float(item.get('sell_amount', 0)),
                                'reversal_amount': float(item.get('reversal_amount', 0)),
                                'income': float(item.get('income', 0)),
                                'spread_income': float(item.get('spread_income', 0))
                            })
                    break
        except Exception as e:
            logger.warning(f"提取收入报表数据失败: {e}")
        return income_reports
    
    @staticmethod
    def _extract_stock_reports_from_content(content):
        """从结构化内容中提取库存报表数据"""
        stock_reports = []
        try:
            sections = content.get('sections', [])
            for section in sections:
                # 【修复】匹配section的type而不是title，因为title可能会变化
                if section.get('type') == 'stock' or section.get('title') in ['外币库存', '库存统计']:
                    data = section.get('data', [])
                    for item in data:
                        if isinstance(item, dict) and 'currency_code' in item:
                            stock_reports.append({
                                'currency_code': item.get('currency_code', ''),
                                'opening_balance': float(item.get('opening_balance', 0)),
                                'change_amount': float(item.get('change_amount', 0)),
                                'current_balance': float(item.get('current_balance', 0))
                            })
                    break
        except Exception as e:
            logger.warning(f"提取库存报表数据失败: {e}")
        return stock_reports
    
    @staticmethod
    def _extract_base_currency_from_content(content):
        """从结构化内容中提取本币数据"""
        base_currency_data = {}
        try:
            sections = content.get('sections', [])
            for section in sections:
                # 【修复】匹配section的type而不是title，因为title可能会变化
                if section.get('type') == 'base_currency' or section.get('title') in ['本币库存', '本币统计']:
                    data = section.get('data', {})
                    if isinstance(data, dict):
                        base_currency_data = {
                            'currency_code': data.get('currency_code', 'THB'),
                            'opening_balance': float(data.get('opening_balance', 0)),
                            'income_amount': float(data.get('income_amount', 0)),
                            'expense_amount': float(data.get('expense_amount', 0)),
                            'adjustment_amount': float(data.get('adjustment_amount', 0)),
                            'cash_out_amount': float(data.get('cash_out_amount', 0)),
                            'reversal_amount': float(data.get('reversal_amount', 0)),
                            'current_balance': float(data.get('current_balance', 0))
                        }
                    break
        except Exception as e:
            logger.warning(f"提取本币数据失败: {e}")
        return base_currency_data
    
    @staticmethod
    def _create_report_header(eod_date, eod_id, branch_name, start_time, end_time, styles, language):
        """创建报表头部"""
        header_elements = []
        
        # 主标题
        header_elements.append(Paragraph(EODReportPDFGenerator._get_text('report_title', language), styles['title']))
        header_elements.append(Spacer(1, 10))
        
        # 【用户要求】直接显示查询收入函数的传入参数，用什么时间查就显示什么时间
        # 不要有逻辑，直接引用
        logger.info(f"🔍 PDF时间处理 - start_time: {start_time} ({type(start_time)}), end_time: {end_time} ({type(end_time)})")
        
        if start_time is not None and end_time is not None:
            try:
                from datetime import datetime
                
                # 【修复】更强健的时间对象处理
                def convert_to_datetime(time_obj):
                    """将各种时间格式转换为datetime对象"""
                    if isinstance(time_obj, datetime):
                        return time_obj
                    elif isinstance(time_obj, str):
                        # 尝试多种字符串格式
                        formats = [
                            '%Y-%m-%d %H:%M:%S.%f',  # 带微秒
                            '%Y-%m-%d %H:%M:%S',     # 标准格式
                            '%Y-%m-%dT%H:%M:%S.%fZ', # ISO格式带微秒
                            '%Y-%m-%dT%H:%M:%S',     # ISO格式
                            '%Y-%m-%dT%H:%M:%S.%f',  # ISO格式带微秒无Z
                        ]
                        for fmt in formats:
                            try:
                                return datetime.strptime(time_obj, fmt)
                            except:
                                continue
                        # 如果都不行，尝试fromisoformat
                        try:
                            return datetime.fromisoformat(time_obj.replace('Z', '+00:00'))
                        except:
                            raise ValueError(f"无法解析时间格式: {time_obj}")
                    else:
                        raise ValueError(f"不支持的时间类型: {type(time_obj)}")
                
                # 转换时间对象
                start_dt = convert_to_datetime(start_time)
                end_dt = convert_to_datetime(end_time)
                
                # 【用户要求】直接使用 yyyy-mm-dd hh:mm:ss 格式显示查询时间范围
                start_str = start_dt.strftime("%Y-%m-%d %H:%M:%S")
                end_str = end_dt.strftime("%Y-%m-%d %H:%M:%S")
                time_range_str = f"{start_str} - {end_str}"
                
                # 记录调试信息
                logger.info(f"📅 时间范围格式化成功: {time_range_str}")
                    
            except Exception as e:
                # 如果时间格式化失败，直接使用原始时间字符串，不做任何转换
                logger.error(f"[ERROR] 时间范围格式化失败: {e}, start_time={start_time}, end_time={end_time}")
                time_range_str = f"{start_time} - {end_time}"
                logger.info(f"📅 使用原始时间字符串: {time_range_str}")
        else:
            # 【警告】只有在start_time和end_time都为None时才回退到使用eod_date
            logger.warning(f"[WARNING] start_time或end_time为None，回退到使用eod_date: {eod_date}")
            
            # 回退到使用eod_date
            if isinstance(eod_date, str):
                try:
                    from datetime import datetime
                    # 尝试解析各种日期时间格式
                    for fmt in ['%Y年%m月%d日 %H:%M:%S', '%Y年%m月%d日', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y/%m/%d %H:%M:%S', '%Y/%m/%d', '%Y%m%d']:
                        try:
                            parsed_datetime = datetime.strptime(eod_date, fmt)
                            time_range_str = parsed_datetime.strftime('%Y-%m-%d %H:%M:%S')
                            break
                        except:
                            continue
                    else:
                        time_range_str = str(eod_date)
                except:
                    time_range_str = str(eod_date)
            else:
                # 如果是date或datetime对象，格式化为 yyyy-mm-dd hh:mm:ss
                try:
                    if hasattr(eod_date, 'time'):
                        # datetime对象
                        time_range_str = eod_date.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        # date对象，添加当前时间
                        from datetime import datetime, time
                        current_time = datetime.now().time()
                        combined_datetime = datetime.combine(eod_date, current_time)
                        time_range_str = combined_datetime.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    time_range_str = str(eod_date)
        
        # 副标题信息 - 【优化】分行显示，避免内容过长
        # 第一行：时间范围
        time_line = f"{EODReportPDFGenerator._get_text('eod_time_range', language)}: {time_range_str}"
        header_elements.append(Paragraph(time_line, styles['subtitle']))
        
        # 第二行：日结ID和分支信息
        if language == 'th':
            info_line = f"{EODReportPDFGenerator._get_text('eod_id', language)}: {eod_id}. {EODReportPDFGenerator._get_text('branch', language)}: {branch_name}"
        elif language == 'en':
            info_line = f"{EODReportPDFGenerator._get_text('eod_id', language)}: {eod_id}. {EODReportPDFGenerator._get_text('branch', language)}: {branch_name}"
        else:  # zh - 中文
            info_line = f"{EODReportPDFGenerator._get_text('eod_id', language)}: {eod_id}. {EODReportPDFGenerator._get_text('branch', language)}: {branch_name}"
        
        header_elements.append(Paragraph(info_line, styles['subtitle']))
        header_elements.append(Spacer(1, 5))
        
        # 生成时间 - 根据语言使用不同格式，【修复】中文符号改英文符号
        if language == 'th':
            generate_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        elif language == 'en':
            generate_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:  # zh - 中文
            generate_time = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
            
        header_elements.append(Paragraph(f"{EODReportPDFGenerator._get_text('generated_time', language)}: {generate_time}", styles['normal']))
        header_elements.append(Spacer(1, 20))
        
        return header_elements
    
    @staticmethod
    def _create_income_statistics_table(income_reports, font_name, styles, language):
        """创建收入统计表格"""
        elements = []
        
        # 表格标题
        elements.append(Paragraph(EODReportPDFGenerator._get_text('foreign_income_title', language), styles["section_title"]))
        elements.append(Spacer(1, 10))
        
        # 表头
        headers = [EODReportPDFGenerator._get_text('currency', language), EODReportPDFGenerator._get_text('buy_amount', language), EODReportPDFGenerator._get_text('sell_amount', language), EODReportPDFGenerator._get_text('reversal_amount', language), EODReportPDFGenerator._get_text('net_income', language), EODReportPDFGenerator._get_text('spread_income', language)]
        
        # 构建表格数据
        table_data = [headers]
        total_income = 0
        total_spread_income = 0
        
        for report in income_reports:
            currency_code = report.get("currency_code", "N/A")
            
            # 【修复】支持两种字段名格式
            buy_amount = float(report.get("buy_amount", report.get("total_buy", 0)))
            sell_amount = float(report.get("sell_amount", report.get("total_sell", 0)))
            reversal_amount = float(report.get("reversal_amount", 0))
            income = float(report.get("income", 0))
            spread_income = float(report.get("spread_income", 0))
            
            total_income += income
            total_spread_income += spread_income
            
            row = [
                currency_code,
                EODReportPDFGenerator._format_amount(buy_amount),
                EODReportPDFGenerator._format_amount(sell_amount),
                EODReportPDFGenerator._format_signed_amount(reversal_amount),
                EODReportPDFGenerator._format_signed_amount(income),  # 净收入也显示带符号
                EODReportPDFGenerator._format_amount(spread_income)
            ]
            table_data.append(row)
        
        # 合计行
        total_row = [
            EODReportPDFGenerator._get_text('total', language), "-", "-", "-",
            EODReportPDFGenerator._format_signed_amount(total_income),  # 总收入也显示带符号
            EODReportPDFGenerator._format_amount(total_spread_income)
        ]
        table_data.append(total_row)
        
        # 创建表格
        table = Table(table_data, colWidths=EODReportPDFGenerator._get_col_widths(len(headers)))
        
        # 表格样式
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),  # 表头改为浅蓝色
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),       # 表头文字改为黑色，更易读
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, -1), font_name),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            # 数据行使用浅色背景
            ("BACKGROUND", (0, 1), (-1, -2), colors.beige),     # 数据行用米色背景
            # 【修复】合计行样式
            ("BACKGROUND", (0, -1), (-1, -1), colors.lightsteelblue),  # 合计行用浅钢蓝色
            ("FONTNAME", (0, -1), (-1, -1), font_name),
            ("FONTSIZE", (0, -1), (-1, -1), 10),
        ]))
        
        elements.append(table)
        return elements
    
    @staticmethod  
    def _create_foreign_stock_table(stock_reports, font_name, styles, language):
        """创建外币库存统计表格"""
        elements = []
        
        elements.append(Paragraph(EODReportPDFGenerator._get_text('foreign_stock_title', language), styles["section_title"]))
        elements.append(Spacer(1, 10))
        
        headers = [EODReportPDFGenerator._get_text('currency', language), EODReportPDFGenerator._get_text('opening_balance', language), EODReportPDFGenerator._get_text('change_amount', language), EODReportPDFGenerator._get_text('current_balance', language), EODReportPDFGenerator._get_text('status', language)]
        table_data = [headers]
        
        for report in stock_reports:
            currency_code = report.get("currency_code", "N/A")
            
            # 【修复】支持不同的字段名格式
            opening_balance = float(report.get("opening_balance", 0))
            change_amount = float(report.get("change_amount", 0))
            current_balance = float(report.get("current_balance", report.get("stock_balance", 0)))
            
            # 【修复】状态判断逻辑
            status_text = "正常"  # 默认正常
            if language == 'en':
                status_text = "Normal"
            elif language == 'th':
                status_text = "ปกติ"
                
            if current_balance <= 0:
                if language == 'en':
                    status_text = "Out of Stock"
                elif language == 'th':
                    status_text = "สินค้าหมด"
                else:
                    status_text = "缺货"
            elif current_balance < 1000:
                if language == 'en':
                    status_text = "Low Stock"
                elif language == 'th':
                    status_text = "สต็อกต่ำ"
                else:
                    status_text = "库存不足"
            
            row = [
                currency_code,
                EODReportPDFGenerator._format_amount(opening_balance),
                EODReportPDFGenerator._format_signed_amount(change_amount),
                EODReportPDFGenerator._format_amount(current_balance),
                status_text
            ]
            table_data.append(row)
        
        # 创建表格
        table = Table(table_data, colWidths=EODReportPDFGenerator._get_col_widths(len(headers)))
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),  # 表头改为浅蓝色
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),       # 表头文字改为黑色，更易读
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, -1), font_name),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            # 数据行使用浅色背景
            ("BACKGROUND", (0, 1), (-1, -2), colors.beige),     # 数据行用米色背景
        ]))
        
        elements.append(table)
        return elements
    
    @staticmethod
    def _create_base_currency_table(base_currency_data, font_name, styles, language):
        """创建本币库存统计表格"""
        elements = []
        
        # 【修复】获取货币代码，支持多种数据格式
        currency_code = base_currency_data.get("currency_code", "THB")
        if not currency_code or currency_code == "":
            currency_code = "THB"  # 默认泰铢
            
        elements.append(Paragraph(f"{EODReportPDFGenerator._get_text('base_currency_title', language)} ({currency_code})", styles["section_title"]))
        elements.append(Spacer(1, 10))
        
        # 【修复】使用新的CalBaseCurrency数据格式，显示带符号的金额
        opening_balance = float(base_currency_data.get("opening_balance", 0))
        income_amount = float(base_currency_data.get("income_amount", 0))
        expense_amount = float(base_currency_data.get("expense_amount", 0))
        adjustment_amount = float(base_currency_data.get("adjustment_amount", 0))
        cash_out_amount = float(base_currency_data.get("cash_out_amount", 0))
        reversal_amount = float(base_currency_data.get("reversal_amount", 0))
        current_balance = float(base_currency_data.get("current_balance", 0))
        
        table_data = [
            [EODReportPDFGenerator._get_text('item', language), EODReportPDFGenerator._get_text('amount', language)],
            [EODReportPDFGenerator._get_text('opening_balance', language), EODReportPDFGenerator._format_amount(opening_balance)],
            [EODReportPDFGenerator._get_text('income_amount', language), EODReportPDFGenerator._format_signed_amount(income_amount) if income_amount != 0 else "0.00"],
            [EODReportPDFGenerator._get_text('expense_amount', language), EODReportPDFGenerator._format_signed_amount(-expense_amount) if expense_amount != 0 else "0.00"],
            [EODReportPDFGenerator._get_text('adjustment_amount', language), EODReportPDFGenerator._format_signed_amount(reversal_amount)],
            [EODReportPDFGenerator._get_text('current_balance', language), EODReportPDFGenerator._format_amount(current_balance)],
        ]
        
        table = Table(table_data, colWidths=EODReportPDFGenerator._get_col_widths(len(table_data[0])))
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),  # 表头改为浅蓝色
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),       # 表头文字改为黑色，更易读
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("FONTNAME", (0, 0), (-1, -1), font_name),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            # 数据行使用浅色背景
            ("BACKGROUND", (0, 1), (-1, -2), colors.beige),     # 数据行用米色背景
        ]))
        
        elements.append(table)
        return elements
    
    @staticmethod
    def _create_signature_section(styles, language):
        """创建签名区域"""
        elements = []
        
        elements.append(Spacer(1, 30))
        elements.append(Paragraph(EODReportPDFGenerator._get_text('signature_section', language), styles["section_title"]))
        elements.append(Spacer(1, 15))
        
        # 【修复】调整签名区域布局和字体
        # 根据语言选择合适的字体
        if language == 'th':
            font_name = "Tahoma"  # 泰语使用Tahoma字体
        elif language == 'en':
            font_name = "Tahoma"  # 英语使用Tahoma字体
        else:  # zh - 中文
            font_name = "SimHei"  # 中文使用SimHei字体
        
        # 【修复】调整签名布局，横线紧跟在文字后面
        signature_data = [
            [EODReportPDFGenerator._get_text('preparer', language) + " " + "_" * 20, "", EODReportPDFGenerator._get_text('reviewer', language) + " " + "_" * 20, "", EODReportPDFGenerator._get_text('date', language) + " " + "_" * 20, ""],
            ["", "", "", "", "", ""],
            [EODReportPDFGenerator._get_text('note', language), "", "", "", "", ""]
        ]
        
        # 【修复】调整列宽，让横线紧跟在文字后面
        signature_table = Table(signature_data, colWidths=[50*mm, 10*mm, 50*mm, 10*mm, 50*mm, 10*mm])
        signature_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), font_name),  # 【修复】使用合适的字体
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("SPAN", (0, 2), (-1, 2)),
            ("FONTSIZE", (0, 2), (-1, 2), 8),
            ("TEXTCOLOR", (0, 2), (-1, 2), colors.grey),
            # 【新增】增加行间距
            ("BOTTOMPADDING", (0, 0), (-1, 1), 8),
        ]))
        
        elements.append(signature_table)
        return elements
    
    @staticmethod
    def _format_amount(amount):
        """格式化金额显示"""
        if amount == 0:
            return "0.00"
        return f"{amount:,.2f}"
    
    @staticmethod
    def _format_signed_amount(amount):
        """格式化带符号的金额显示"""
        if amount == 0:
            return "0.00"
        elif amount > 0:
            return f"+{amount:,.2f}"
        else:
            return f"{amount:,.2f}"

    @staticmethod
    def _get_text(key, language='zh'):
        """获取多语言文本"""
        text_mapping = {
            'zh': {
                'report_title': '日结收入及库存统计报表',
                'eod_summary_report_title': '日结汇总报表',
                'eod_detailed_report_title': '日结详细报表',
                'eod_time': '日结时间',
                'eod_time_range': '日结时间范围',
                'eod_id': '日结编号',
                'branch': '网点',
                'generated_time': '生成时间',
                'generated_at': '生成时间',
                'foreign_income_title': '1. 外币收入统计',
                'foreign_stock_title': '2. 外币库存统计', 
                'base_currency_title': '3. 本币库存统计',
                'currency': '币种',
                'currency_name': '币种名称',
                'buy_amount': '买入量',
                'sell_amount': '卖出量',
                'reversal_amount': '冲正量',
                'net_income': '净收入',
                'spread_income': '点差收入',
                'total': '合计',
                'opening_balance': '期初余额',
                'actual_balance': '实际余额',
                'theoretical_balance': '理论余额',
                'change_amount': '变动金额',
                'current_balance': '期末余额',
                'status': '状态',
                'item': '项目',
                'amount': '金额',
                'income_amount': '收入金额',
                'expense_amount': '支出金额',
                'adjustment_amount': '冲正金额',
                'transaction_statistics': '交易统计',
                'total_transactions': '交易总数',
                'buy_transactions': '买入交易',
                'sell_transactions': '卖出交易',
                'transactions_unit': '笔',
                'balance_summary': '余额汇总',
                'cash_out_summary': '交款汇总',
                'cash_out_amount': '交款金额',
                'remaining_balance': '剩余余额',
                'income_summary': '收入汇总',
                'total_buy': '买入总额',
                'total_sell': '卖出总额',
                'income': '收入',
                'signature_section': '签名确认',
                'preparer': '制表人',
                'reviewer': '审核人',
                'date': '日期',
                'note': '说明: 本报表反映当日外币兑换业务收入及库存情况, 请相关人员核实确认.',
                'no_foreign_income': '本日结期间无外币收入记录',
                'no_foreign_stock': '本日结期间无外币库存变动记录',
                'no_base_currency': '本日结期间无本币库存变动记录',
                'difference_adjustment_table': '差额调节表',
                'adjust_amount': '调节金额',
                'adjust_reason': '调节原因',
                'difference_table': '差额表',
                'difference': '差异',
                'difference_report_table': '差额报告表',
                'difference_reason': '差额原因'
            },
            'th': {
                'report_title': 'รายงานสถิติรายได้และสต็อกปลายวัน',
                'eod_summary_report_title': 'รายงานสรุปการปิดวัน',
                'eod_detailed_report_title': 'รายงานรายละเอียดการปิดวัน',
                'eod_time': 'เวลาปิดงาน',
                'eod_time_range': 'ช่วงเวลาปิดงาน',
                'eod_id': 'รหัสปิดงาน',
                'branch': 'สาขา',
                'generated_time': 'เวลาสร้าง',
                'generated_at': 'สร้างเมื่อ',
                'foreign_income_title': '1. สถิติรายได้เงินตราต่างประเทศ',
                'foreign_stock_title': '2. สถิติสต็อกเงินตราต่างประเทศ',
                'base_currency_title': '3. สถิติสต็อกเงินบาท',
                'currency': 'สกุลเงิน',
                'currency_name': 'ชื่อสกุลเงิน',
                'buy_amount': 'ปริมาณซื้อ',
                'sell_amount': 'ปริมาณขาย',
                'reversal_amount': 'ปริมาณยกเลิก',
                'net_income': 'รายได้สุทธิ',
                'spread_income': 'รายได้ส่วนต่าง',
                'total': 'รวม',
                'opening_balance': 'ยอดเริ่มต้น',
                'actual_balance': 'ยอดเงินจริง',
                'theoretical_balance': 'ยอดเงินตามทฤษฎี',
                'change_amount': 'จำนวนเปลี่ยนแปลง',
                'current_balance': 'ยอดปัจจุบัน',
                'status': 'สถานะ',
                'item': 'รายการ',
                'amount': 'จำนวน',
                'income_amount': 'จำนวนรายได้',
                'expense_amount': 'จำนวนค่าใช้จ่าย',
                'adjustment_amount': 'จำนวนยกเลิก',
                'transaction_statistics': 'สถิติการทำธุรกรรม',
                'total_transactions': 'ธุรกรรมทั้งหมด',
                'buy_transactions': 'ธุรกรรมการซื้อ',
                'sell_transactions': 'ธุรกรรมการขาย',
                'transactions_unit': 'รายการ',
                'balance_summary': 'สรุปยอดเงิน',
                'cash_out_summary': 'สรุปการถอนเงิน',
                'cash_out_amount': 'จำนวนเงินที่ถอน',
                'remaining_balance': 'ยอดเงินคงเหลือ',
                'income_summary': 'สรุปรายได้',
                'difference_adjustment_table': 'ตารางการปรับส่วนต่าง',
                'adjust_amount': 'จำนวนการปรับ',
                'adjust_reason': 'เหตุผลการปรับ',
                'difference_table': 'ตารางส่วนต่าง',
                'difference': 'ส่วนต่าง',
                'difference_report_table': 'ตารางรายงานส่วนต่าง',
                'difference_reason': 'เหตุผลส่วนต่าง',
                'total_buy': 'ยอดซื้อทั้งหมด',
                'total_sell': 'ยอดขายทั้งหมด',
                'income': 'รายได้',
                'signature_section': 'การยืนยันลายเซ็น',
                'preparer': 'ผู้จัดทำ',
                'reviewer': 'ผู้ตรวจสอบ',
                'date': 'วันที่',
                'note': 'หมายเหตุ: รายงานนี้แสดงรายได้และสต็อกจากการแลกเปลี่ยนเงินตราต่างประเทศในวันนั้น กรุณาตรวจสอบยืนยันโดยเจ้าหน้าที่ที่เกี่ยวข้อง',
                'no_foreign_income': 'ไม่มีรายการรายได้เงินตราต่างประเทศในช่วงปิดงานนี้',
                'no_foreign_stock': 'ไม่มีรายการเปลี่ยนแปลงสต็อกเงินตราต่างประเทศในช่วงปิดงานนี้',
                'no_base_currency': 'ไม่มีรายการเปลี่ยนแปลงสต็อกเงินบาทในช่วงปิดงานนี้'
            },
            'en': {
                'report_title': 'End-of-Day Income and Inventory Statistics Report',
                'eod_summary_report_title': 'Daily Settlement Summary Report',
                'eod_detailed_report_title': 'Daily Settlement Detailed Report',
                'eod_time': 'EOD Time',
                'eod_time_range': 'EOD Time Range',
                'eod_id': 'EOD ID',
                'branch': 'Branch',
                'generated_time': 'Generated Time',
                'generated_at': 'Generated At',
                'foreign_income_title': '1. Foreign Currency Income Statistics',
                'foreign_stock_title': '2. Foreign Currency Inventory Statistics',
                'base_currency_title': '3. Base Currency Inventory Statistics',
                'currency': 'Currency',
                'currency_name': 'Currency Name',
                'buy_amount': 'Buy Amount',
                'sell_amount': 'Sell Amount',
                'reversal_amount': 'Reversal Amount',
                'net_income': 'Net Income',
                'spread_income': 'Spread Income',
                'total': 'Total',
                'opening_balance': 'Opening Balance',
                'actual_balance': 'Actual Balance',
                'theoretical_balance': 'Theoretical Balance',
                'change_amount': 'Change Amount',
                'current_balance': 'Current Balance',
                'status': 'Status',
                'item': 'Item',
                'amount': 'Amount',
                'income_amount': 'Income Amount',
                'expense_amount': 'Expense Amount',
                'adjustment_amount': 'Reversal Amount',
                'transaction_statistics': 'Transaction Statistics',
                'total_transactions': 'Total Transactions',
                'buy_transactions': 'Buy Transactions',
                'sell_transactions': 'Sell Transactions',
                'transactions_unit': 'transactions',
                'balance_summary': 'Balance Summary',
                'cash_out_summary': 'Cash Out Summary',
                'cash_out_amount': 'Cash Out Amount',
                'remaining_balance': 'Remaining Balance',
                'income_summary': 'Income Summary',
                'total_buy': 'Total Buy',
                'total_sell': 'Total Sell',
                'income': 'Income',
                'signature_section': 'Signature Confirmation',
                'preparer': 'Preparer',
                'reviewer': 'Reviewer',
                'date': 'Date',
                'note': 'Note: This report reflects the daily foreign exchange business income and inventory status. Please verify and confirm by relevant personnel.',
                'no_foreign_income': 'No foreign currency income records during this EOD period',
                'no_foreign_stock': 'No foreign currency inventory change records during this EOD period',
                'no_base_currency': 'No base currency inventory change records during this EOD period',
                'difference_adjustment_table': 'Difference Adjustment Table',
                'adjust_amount': 'Adjustment Amount',
                'adjust_reason': 'Adjustment Reason',
                'difference_table': 'Difference Table',
                'difference': 'Difference',
                'difference_report_table': 'Difference Report Table',
                'difference_reason': 'Difference Reason'
            }
        }
        
        return text_mapping.get(language, text_mapping['zh']).get(key, f'[{key}]')

    @staticmethod
    def generate_simple_eod_report_pdf(print_data, file_path, language='zh'):
        """
        生成简单日结报表PDF - 第7步专用
        
        Args:
            print_data: 打印数据，包含header和sections
            file_path: 输出文件路径
            language: 语言代码 ('zh', 'en', 'th')
            
        Returns:
            bool: 生成是否成功
        """
        try:
            logger.info(f"🎨 开始生成第7步PDF - 文件: {file_path}, 语言: {language}")
            logger.info(f"📊 打印数据结构: {print_data.keys()}")
            logger.info(f"🌍 语言参数检查: 传入语言={language}, 类型={type(language)}")
            
            # 多语言支持
            try:
                font_name = EODReportPDFGenerator.init_fonts(language)
                logger.info(f"🎨 字体初始化成功: {font_name}")
            except Exception as font_error:
                logger.error(f"[ERROR] 字体初始化失败: {font_error}")
                # 降级到默认字体
                font_name = 'Helvetica'
                logger.info(f"🎨 使用降级字体: {font_name}")
            
            styles = EODReportPDFGenerator.get_styles(font_name)
            
            # 创建PDF文档
            doc = EODReportPDFGenerator.create_pdf_doc(file_path)
            
            # 构建PDF内容
            story = []
            
            # 从print_data中提取信息
            header = print_data.get('header', {})
            sections = print_data.get('sections', [])
            
            # 获取基本信息
            eod_date = header.get('date', datetime.now().strftime('%Y年%m月%d日'))
            eod_id = header.get('eod_id', 'N/A')
            branch_id = header.get('branch_id')
            generated_time = header.get('generated_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            # 获取网点信息
            if branch_id:
                branch_info = EODReportPDFGenerator._get_branch_info(branch_id)
                branch_display = f"{branch_info['branch_code']} {branch_info['branch_name']}"
            else:
                branch_display = header.get('branch_name', '未知网点')
            
            logger.info(f"📋 处理sections: {len(sections)} 个")
            
            # 获取营业时间范围
            business_start_time = header.get('business_start_time')
            business_end_time = header.get('business_end_time')
            
            # 创建报表头部
            story.extend(EODReportPDFGenerator._create_simple_report_header(
                eod_date, eod_id, branch_display, generated_time, styles, language, business_start_time, business_end_time
            ))
            
            # 处理各个sections
            for i, section in enumerate(sections):
                section_type = section.get('type')
                section_data = section.get('data', {})
                
                logger.info(f"📋 处理section {i+1}: {section_type}")
                
                if section_type == 'transaction_summary':
                    # 交易统计
                    story.extend(EODReportPDFGenerator._create_transaction_summary_table(
                        section_data, font_name, styles, language
                    ))
                elif section_type == 'balance_summary':
                    # 余额汇总
                    story.extend(EODReportPDFGenerator._create_balance_summary_table(
                        section_data, font_name, styles, language
                    ))
                elif section_type == 'cash_out_summary':
                    # 交款汇总
                    story.extend(EODReportPDFGenerator._create_cash_out_summary_table(
                        section_data, font_name, styles, language
                    ))
                elif section_type == 'income_summary':
                    # 收入汇总（详细模式）
                    story.extend(EODReportPDFGenerator._create_income_summary_table(
                        section_data, font_name, styles, language
                    ))
                elif section_type == 'difference_adjustment_table':
                    # 差额调节表
                    story.extend(EODReportPDFGenerator._create_difference_adjustment_table(
                        section_data, font_name, styles, language
                    ))
                elif section_type == 'difference_report_table':
                    # 差额报告表
                    story.extend(EODReportPDFGenerator._create_difference_report_table(
                        section_data, font_name, styles, language
                    ))
                
                story.append(Spacer(1, 15))
            
            # 添加签名区域
            story.extend(EODReportPDFGenerator._create_signature_section(styles, language))
            
            # 生成PDF
            doc.build(story)
            
            logger.info(f"[OK] 第7步PDF生成成功: {file_path}")
            return {
                'success': True,
                'file_path': file_path,
                'message': '日结报表PDF生成成功'
            }
            
        except Exception as e:
            import traceback
            logger.error(f"生成第7步PDF失败: {e}\n{traceback.format_exc()}")
            return {
                'success': False,
                'message': f'生成第7步PDF失败: {str(e)}'
            }
    
    @staticmethod
    def _create_simple_report_header(eod_date, eod_id, branch_name, generated_time, styles, language, business_start_time=None, business_end_time=None):
        """创建简单报表头部"""
        story = []
        
        # 【调试】输出营业时间范围
        print(f"🔍 PDF头部 - business_start_time: {business_start_time}")
        print(f"🔍 PDF头部 - business_end_time: {business_end_time}")
        print(f"🔍 PDF头部 - 类型: {type(business_start_time)}, {type(business_end_time)}")
        
        # 标题
        title_text = EODReportPDFGenerator._get_text('eod_summary_report_title', language)
        story.append(Paragraph(title_text, styles["title"]))
        story.append(Spacer(1, 20))
        
        # 副标题 - 分行显示
        subtitle_parts = []
        
        # 第一行：日结时间范围（如果有）
        if business_start_time and business_end_time:
            try:
                from datetime import datetime
                
                # 转换时间对象
                def convert_to_datetime(time_obj):
                    if isinstance(time_obj, datetime):
                        return time_obj
                    elif isinstance(time_obj, str):
                        formats = ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f']
                        for fmt in formats:
                            try:
                                return datetime.strptime(time_obj, fmt)
                            except:
                                continue
                        try:
                            return datetime.fromisoformat(time_obj.replace('Z', '+00:00'))
                        except:
                            raise ValueError(f"无法解析时间格式: {time_obj}")
                    else:
                        raise ValueError(f"不支持的时间类型: {type(time_obj)}")
                
                start_dt = convert_to_datetime(business_start_time)
                end_dt = convert_to_datetime(business_end_time)
                
                start_str = start_dt.strftime("%Y-%m-%d %H:%M:%S")
                end_str = end_dt.strftime("%Y-%m-%d %H:%M:%S")
                time_range_str = f"{start_str} - {end_str}"
                
                # 显示日结时间范围
                time_line = f"{EODReportPDFGenerator._get_text('eod_time_range', language)}: {time_range_str}"
                subtitle_parts.append(time_line)
                print(f"🔍 PDF头部 - 添加时间范围行: {time_line}")
                
            except Exception as e:
                logger.error(f"[ERROR] 日结时间范围格式化失败: {e}")
                print(f"[ERROR] 日结时间范围格式化失败: {e}")
        else:
            print(f"🔍 PDF头部 - 没有营业时间范围数据")
        
        # 第二行：生成时间
        subtitle_parts.append(f"{EODReportPDFGenerator._get_text('generated_at', language)}: {generated_time}")
        
        # 第三行：EOD ID和网点
        eod_info = f"{EODReportPDFGenerator._get_text('eod_id', language)}: {eod_id} | {EODReportPDFGenerator._get_text('branch', language)}: {branch_name}"
        subtitle_parts.append(eod_info)
        
        # 添加副标题行
        for part in subtitle_parts:
            story.append(Paragraph(part, styles["subtitle"]))
        
        story.append(Spacer(1, 20))
        
        return story
    
    @staticmethod
    def _create_transaction_summary_table(transaction_data, font_name, styles, language):
        """创建交易统计表格"""
        story = []
        
        # 表格标题
        title_text = EODReportPDFGenerator._get_text('transaction_statistics', language)
        story.append(Paragraph(title_text, styles["section_title"]))
        story.append(Spacer(1, 10))
        
        # 表格数据
        data = [
            [
                EODReportPDFGenerator._get_text('total_transactions', language),
                f"{transaction_data.get('total_transactions', 0)} {EODReportPDFGenerator._get_text('transactions_unit', language)}"
            ],
            [
                EODReportPDFGenerator._get_text('buy_transactions', language),
                f"{transaction_data.get('buy_transactions', 0)} {EODReportPDFGenerator._get_text('transactions_unit', language)}"
            ],
            [
                EODReportPDFGenerator._get_text('sell_transactions', language),
                f"{transaction_data.get('sell_transactions', 0)} {EODReportPDFGenerator._get_text('transactions_unit', language)}"
            ]
        ]
        
        # 创建表格 - 使用统一的列宽
        table = Table(data, colWidths=EODReportPDFGenerator._get_col_widths(len(data[0])))
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.lightblue),  # 表头改为浅蓝色
            ("TEXTCOLOR", (0, 0), (0, -1), colors.black),       # 表头文字改为黑色，更易读
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("FONTNAME", (0, 0), (-1, -1), font_name),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            # 数据行使用浅色背景
            ("BACKGROUND", (1, 0), (1, -1), colors.beige),     # 数据行用米色背景
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        
        story.append(table)
        return story
    
    @staticmethod
    def _create_balance_summary_table(balance_data, font_name, styles, language):
        """创建余额汇总表格"""
        story = []
        
        # 余额汇总标题
        title_text = EODReportPDFGenerator._get_text('balance_summary', language)
        story.append(Paragraph(title_text, styles["section_title"]))
        story.append(Spacer(1, 10))
        
        balance_summary = balance_data.get('balance_summary', [])
        cash_out_summary = balance_data.get('cash_out_summary', [])
        
        logger.info(f"🔍 PDF余额汇总表格 - 余额数据数量: {len(balance_summary)}")
        logger.info(f"🔍 PDF余额汇总表格 - 交款数据数量: {len(cash_out_summary)}")
        logger.info(f"🔍 PDF余额汇总表格 - 余额数据: {balance_summary}")
        
        if balance_summary:
            # 余额表格
            headers = [
                EODReportPDFGenerator._get_text('currency', language),
                EODReportPDFGenerator._get_text('currency_name', language),
                EODReportPDFGenerator._get_text('opening_balance', language),
                EODReportPDFGenerator._get_text('actual_balance', language),
                EODReportPDFGenerator._get_text('theoretical_balance', language),
                EODReportPDFGenerator._get_text('difference', language),
                EODReportPDFGenerator._get_text('status', language)
            ]
            
            data = [headers]
            for item in balance_summary:
                currency_code = item.get('currency_code', '')
                # 使用币种翻译函数获取正确的币种名称
                translated_currency_name = get_currency_name(currency_code, language)
                
                # 【调试】记录币种翻译过程
                logger.info(f"🔍 余额表格币种翻译: {currency_code} -> {translated_currency_name} (语言: {language})")
                
                # 【调试】记录状态信息
                status_text = item.get('status', '')
                logger.info(f"🔍 余额表格状态调试: 币种={currency_code}, 状态={status_text}, 类型={type(status_text)}")
                
                data.append([
                    currency_code,
                    translated_currency_name,
                    EODReportPDFGenerator._format_amount(item.get('opening_balance', 0)),
                    EODReportPDFGenerator._format_amount(item.get('actual_balance', 0)),
                    EODReportPDFGenerator._format_amount(item.get('theoretical_balance', 0)),
                    EODReportPDFGenerator._format_signed_amount(item.get('difference', 0)),
                    status_text
                ])
            
            # 创建表格 - 使用统一的列宽
            table = Table(data, colWidths=EODReportPDFGenerator._get_col_widths(len(headers), 'balance'))
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),  # 表头改为浅蓝色
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),       # 表头文字改为黑色，更易读
                ("ALIGN", (0, 0), (0, -1), "CENTER"),  # 币种代码居中
                ("ALIGN", (1, 0), (1, -1), "LEFT"),    # 币种名称左对齐
                ("ALIGN", (2, 0), (5, -1), "RIGHT"),   # 金额列右对齐
                ("ALIGN", (6, 0), (6, -1), "CENTER"),  # 状态列居中
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                # 数据行使用浅色背景
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),     # 数据行用米色背景
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))
            
            story.append(table)
            story.append(Spacer(1, 15))
        
        if cash_out_summary:
            # 交款汇总表格
            cash_out_title = EODReportPDFGenerator._get_text('cash_out_summary', language)
            story.append(Paragraph(cash_out_title, styles["section_title"]))
            story.append(Spacer(1, 10))
            
            headers = [
                EODReportPDFGenerator._get_text('currency', language),
                EODReportPDFGenerator._get_text('currency_name', language),
                EODReportPDFGenerator._get_text('cash_out_amount', language),
                EODReportPDFGenerator._get_text('remaining_balance', language)
            ]
            
            data = [headers]
            for item in cash_out_summary:
                currency_code = item.get('currency_code', '')
                # 使用币种翻译函数获取正确的币种名称
                translated_currency_name = get_currency_name(currency_code, language)
                
                # 【调试】记录币种翻译过程
                logger.info(f"🔍 交款汇总表格币种翻译: {currency_code} -> {translated_currency_name} (语言: {language})")
                
                data.append([
                    currency_code,
                    translated_currency_name,
                    EODReportPDFGenerator._format_amount(item.get('cash_out_amount', 0)),
                    EODReportPDFGenerator._format_amount(item.get('remaining_balance', 0))
                ])
            
            # 创建表格 - 使用统一的列宽
            table = Table(data, colWidths=EODReportPDFGenerator._get_col_widths(len(headers), 'cash_out'))
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),  # 表头改为浅蓝色
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),       # 表头文字改为黑色，更易读
                ("ALIGN", (0, 0), (0, -1), "CENTER"),  # 币种代码居中
                ("ALIGN", (1, 0), (1, -1), "LEFT"),    # 币种名称左对齐
                ("ALIGN", (2, 0), (-1, -1), "RIGHT"),  # 金额列右对齐
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                # 数据行使用浅色背景
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),     # 数据行用米色背景
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))
            
            story.append(table)
        
        return story
    
    @staticmethod
    def _create_cash_out_summary_table(cash_out_data, font_name, styles, language):
        """创建交款汇总表格"""
        story = []
        
        # 表格标题
        title_text = EODReportPDFGenerator._get_text('cash_out_summary', language)
        story.append(Paragraph(title_text, styles["section_title"]))
        story.append(Spacer(1, 10))
        
        # 检查是否有数据
        cash_out_summary = cash_out_data.get('cash_out_summary', [])
        if not cash_out_summary:
            story.append(Paragraph(EODReportPDFGenerator._get_text('no_data', language), styles["normal"]))
            return story
        
        # 表头
        headers = [
            EODReportPDFGenerator._get_text('currency', language),  # 使用currency而不是currency_code
            EODReportPDFGenerator._get_text('currency_name', language),
            EODReportPDFGenerator._get_text('cash_out_amount', language),
            EODReportPDFGenerator._get_text('remaining_balance', language)
        ]
        
        # 数据行
        data = [headers]
        for item in cash_out_summary:
            currency_code = item.get('currency_code', '')
            currency_name = item.get('currency_name', '')
            
            # 【新增】币种名称翻译
            translated_currency_name = get_currency_name(currency_code, language)
            if translated_currency_name != currency_code:
                currency_name = translated_currency_name
            
            # 【调试】记录币种翻译过程
            logger.info(f"🔍 交款汇总表格币种翻译: {currency_code} -> {translated_currency_name} (语言: {language})")
            
            data.append([
                currency_code,
                translated_currency_name,
                EODReportPDFGenerator._format_amount(item.get('cash_out_amount', 0)),
                EODReportPDFGenerator._format_amount(item.get('remaining_balance', 0))
            ])
        
        # 创建表格 - 使用统一的列宽
        table = Table(data, colWidths=EODReportPDFGenerator._get_col_widths(len(headers), 'cash_out'))
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),  # 表头改为浅蓝色
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),       # 表头文字改为黑色，更易读
            ("ALIGN", (0, 0), (0, -1), "CENTER"),  # 币种代码居中
            ("ALIGN", (1, 0), (1, -1), "LEFT"),    # 币种名称左对齐
            ("ALIGN", (2, 0), (-1, -1), "RIGHT"),  # 金额列右对齐
            ("FONTNAME", (0, 0), (-1, -1), font_name),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            # 数据行使用浅色背景
            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),     # 数据行用米色背景
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 10))
        
        return story

    @staticmethod
    def _create_income_summary_table(income_data, font_name, styles, language):
        """创建收入汇总表格（详细模式）"""
        story = []
        
        # 收入汇总标题
        title_text = EODReportPDFGenerator._get_text('income_summary', language)
        story.append(Paragraph(title_text, styles["section_title"]))
        story.append(Spacer(1, 10))
        
        income_summary = income_data.get('income_summary', [])
        
        if income_summary:
            headers = [
                EODReportPDFGenerator._get_text('currency', language),
                EODReportPDFGenerator._get_text('currency_name', language),
                EODReportPDFGenerator._get_text('total_buy', language),
                EODReportPDFGenerator._get_text('total_sell', language),
                EODReportPDFGenerator._get_text('income', language),
                EODReportPDFGenerator._get_text('spread_income', language)
            ]
            
            data = [headers]
            for item in income_summary:
                currency_code = item.get('currency_code', '')
                # 使用币种翻译函数获取正确的币种名称
                translated_currency_name = get_currency_name(currency_code, language)
                
                # 【调试】记录币种翻译过程
                logger.info(f"🔍 收入汇总表格币种翻译: {currency_code} -> {translated_currency_name} (语言: {language})")
                
                data.append([
                    currency_code,
                    translated_currency_name,
                    EODReportPDFGenerator._format_amount(item.get('total_buy', 0)),
                    EODReportPDFGenerator._format_amount(item.get('total_sell', 0)),
                    EODReportPDFGenerator._format_amount(item.get('income', 0)),
                    EODReportPDFGenerator._format_amount(item.get('spread_income', 0))
                ])
            
            # 创建表格 - 使用统一的列宽
            table = Table(data, colWidths=EODReportPDFGenerator._get_col_widths(len(headers), 'income'))
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),  # 表头改为浅蓝色
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),       # 表头文字改为黑色，更易读
                ("ALIGN", (0, 0), (0, -1), "CENTER"),  # 币种代码居中
                ("ALIGN", (1, 0), (1, -1), "LEFT"),    # 币种名称左对齐
                ("ALIGN", (2, 0), (-1, -1), "RIGHT"),  # 金额列右对齐
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                # 数据行使用浅色背景
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),     # 数据行用米色背景
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))
            
            story.append(table)
        
        return story

    @staticmethod
    def _get_col_widths(num_cols, table_type=None):
        """根据列数和表格类型计算统一的列宽"""
        if num_cols == 5:
            if table_type == 'difference_adjustment':  # 差额调节表：币种名称、理论余额、实际余额、调节金额、调节原因
                return [32*mm, 32*mm, 32*mm, 32*mm, 32*mm]
            elif table_type == 'difference_report':  # 差额报告表：币种名称、理论余额、实际余额、差异、差额原因
                return [32*mm, 32*mm, 32*mm, 32*mm, 32*mm]
            else:  # 默认5列表格
                return [32*mm, 32*mm, 32*mm, 32*mm, 32*mm]
        elif num_cols == 4:
            if table_type == 'cash_out':  # 交款汇总表：币种、币种名称、交款金额、剩余余额
                return [40*mm, 40*mm, 40*mm, 40*mm]
            else:  # 默认4列表格
                return [40*mm, 40*mm, 40*mm, 40*mm]
        elif num_cols == 7:
            if table_type == 'balance':  # 余额汇总表：币种、币种名称、期初余额、实际余额、理论余额、差异、状态
                return [20*mm, 20*mm, 20*mm, 20*mm, 20*mm, 20*mm, 40*mm]  # 增加状态列宽度
            else:  # 默认7列表格
                return [23*mm, 23*mm, 23*mm, 23*mm, 23*mm, 23*mm, 22*mm]
        elif num_cols == 6:
            if table_type == 'income':  # 收入汇总表：币种、币种名称、总买入、总卖出、收入、点差收入
                return [27*mm, 27*mm, 27*mm, 27*mm, 27*mm, 25*mm]
            else:  # 默认6列表格
                return [27*mm, 27*mm, 27*mm, 27*mm, 27*mm, 25*mm]
        elif num_cols == 2:
            # 两列表格（如本币库存统计）：项目、金额
            return [80*mm, 80*mm]
        else:
            return [EODReportPDFGenerator.TABLE_TOTAL_WIDTH / num_cols] * num_cols

    @staticmethod
    def _create_difference_adjustment_table(difference_data, font_name, styles, language):
        """创建差额调节表"""
        story = []
        
        # 差额调节表标题
        title_text = EODReportPDFGenerator._get_text('difference_adjustment_table', language)
        story.append(Paragraph(title_text, styles["section_title"]))
        story.append(Spacer(1, 10))
        
        difference_adjustment_summary = difference_data.get('difference_adjustment_summary', [])
        
        if difference_adjustment_summary:
            headers = [
                EODReportPDFGenerator._get_text('currency_name', language),
                EODReportPDFGenerator._get_text('theoretical_balance', language),
                EODReportPDFGenerator._get_text('actual_balance', language),
                EODReportPDFGenerator._get_text('adjust_amount', language),
                EODReportPDFGenerator._get_text('adjust_reason', language)
            ]
            
            data = [headers]
            for item in difference_adjustment_summary:
                currency_code = item.get('currency_code', '')
                currency_name = item.get('currency_name', '')
                # 使用币种翻译函数获取正确的币种名称
                translated_currency_name = get_currency_name(currency_code, language)
                
                # 使用原始实际余额（如果有的话）
                display_actual_balance = item.get('original_actual_balance', item.get('actual_balance', 0))
                
                # 根据语言翻译调节原因
                reason_text = item.get('reason', '')
                if language == 'en':
                    # 如果是英文版本，将泰文或中文原因翻译为英文
                    if 'การปรับส่วนต่าง' in reason_text or '日结差额调节' in reason_text:
                        reason_text = 'EOD Difference Adjustment'
                    elif 'EOD' in reason_text:
                        reason_text = 'EOD Difference Adjustment'
                elif language == 'th':
                    # 如果是泰文版本，将中文或英文原因翻译为泰文
                    if '日结差额调节' in reason_text or 'EOD Difference Adjustment' in reason_text:
                        reason_text = 'การปรับส่วนต่าง EOD'
                    elif 'EOD' in reason_text:
                        reason_text = 'การปรับส่วนต่าง EOD'
                else:
                    # 如果是中文版本，将泰文或英文原因翻译为中文
                    if 'การปรับส่วนต่าง' in reason_text or 'EOD Difference Adjustment' in reason_text:
                        reason_text = '日结差额调节'
                    elif 'EOD' in reason_text:
                        reason_text = '日结差额调节'
                
                data.append([
                    translated_currency_name,
                    EODReportPDFGenerator._format_amount(item.get('theoretical_balance', 0)),
                    EODReportPDFGenerator._format_amount(display_actual_balance),
                    EODReportPDFGenerator._format_signed_amount(item.get('adjust_amount', 0)),
                    reason_text
                ])
            
            # 创建表格 - 使用统一的列宽
            table = Table(data, colWidths=EODReportPDFGenerator._get_col_widths(len(headers), 'difference_adjustment'))
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),  # 表头改为浅蓝色
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),       # 表头文字改为黑色，更易读
                ("ALIGN", (0, 0), (0, -1), "CENTER"),  # 币种名称居中
                ("ALIGN", (1, 0), (3, -1), "RIGHT"),   # 金额列右对齐
                ("ALIGN", (4, 0), (4, -1), "LEFT"),    # 调节原因列左对齐
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                # 数据行使用浅色背景
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),     # 数据行用米色背景
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))
            
            story.append(table)
        
        return story

    @staticmethod
    def _create_difference_report_table(difference_data, font_name, styles, language):
        """创建差额报告表"""
        story = []
        
        # 差额报告表标题
        title_text = EODReportPDFGenerator._get_text('difference_report_table', language)
        story.append(Paragraph(title_text, styles["section_title"]))
        story.append(Spacer(1, 10))
        
        difference_report_summary = difference_data.get('difference_report_summary', [])
        
        if difference_report_summary:
            headers = [
                EODReportPDFGenerator._get_text('currency_name', language),
                EODReportPDFGenerator._get_text('theoretical_balance', language),
                EODReportPDFGenerator._get_text('actual_balance', language),
                EODReportPDFGenerator._get_text('difference', language),
                EODReportPDFGenerator._get_text('difference_reason', language)
            ]
            
            data = [headers]
            for item in difference_report_summary:
                currency_code = item.get('currency_code', '')
                currency_name = item.get('currency_name', '')
                # 使用币种翻译函数获取正确的币种名称
                translated_currency_name = get_currency_name(currency_code, language)
                
                data.append([
                    translated_currency_name,
                    EODReportPDFGenerator._format_amount(item.get('theoretical_balance', 0)),
                    EODReportPDFGenerator._format_amount(item.get('actual_balance', 0)),
                    EODReportPDFGenerator._format_signed_amount(item.get('difference', 0)),
                    ''  # 差额原因留空
                ])
            
            # 创建表格 - 使用统一的列宽
            table = Table(data, colWidths=EODReportPDFGenerator._get_col_widths(len(headers), 'difference_report'))
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),  # 表头改为浅蓝色
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),       # 表头文字改为黑色，更易读
                ("ALIGN", (0, 0), (0, -1), "CENTER"),  # 币种名称居中
                ("ALIGN", (1, 0), (3, -1), "RIGHT"),   # 金额列右对齐
                ("ALIGN", (4, 0), (4, -1), "LEFT"),    # 差额原因列左对齐
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                # 数据行使用浅色背景
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),     # 数据行用米色背景
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))
            
            story.append(table)
        
        return story