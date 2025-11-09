#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化PDF票据生成服务
使用模块化方式生成各种类型的PDF票据
"""

import os
import logging
import base64
from datetime import datetime
from .pdf_base import PDFBase
from .exchange_pdf_generator import ExchangePDFGenerator
from .dual_direction_pdf_generator import DualDirectionPDFGenerator
from .reversal_pdf_generator import ReversalPDFGenerator
from .balance_pdf_generator import BalancePDFGenerator
from .summary_pdf_generator import SummaryPDFGenerator
from .eod_report_pdf_generator import EODReportPDFGenerator

logger = logging.getLogger(__name__)

class SimplePDFService:
    """简化的PDF生成服务 - 模块化方式"""
    
    @staticmethod
    def get_manager_file_path(report_type, filename_prefix=None, eod_id=None, eod_date=None):
        """
        获取manager目录下的文件路径，按年月组织
        支持EOD规范命名：yyyymmddEOD{日结id}income.pdf / yyyymmddEOD{日结id}cashout.pdf
        
        Args:
            report_type: 报表类型 ('income', 'stock', 'eod', 'cashout')
            filename_prefix: 文件名前缀（可选）
            eod_id: 日结ID（用于EOD规范命名）
            eod_date: 日结日期（用于EOD规范命名）
            
        Returns:
            str: 完整的文件路径
        """
        try:
            # 获取当前时间或使用指定日期
            if eod_date:
                target_date = eod_date if isinstance(eod_date, datetime) else datetime.strptime(str(eod_date), '%Y-%m-%d')
            else:
                target_date = datetime.now()
                
            year = target_date.strftime('%Y')
            month = target_date.strftime('%m')
            
            # 构建文件名 - EOD规范命名
            if eod_id and report_type in ['income', 'cashout']:
                # EOD规范命名：yyyymmddEOD{日结id:03d}income.pdf 或 yyyymmddEOD{日结id:03d}cashout.pdf
                date_str = target_date.strftime('%Y%m%d')
                filename = f"{date_str}EOD{eod_id:03d}{report_type}.pdf"
            elif filename_prefix:
                # 使用自定义前缀
                timestamp = target_date.strftime('%Y%m%d_%H%M%S')
                filename = f"{filename_prefix}_{timestamp}.pdf"
            else:
                # 默认命名
                timestamp = target_date.strftime('%Y%m%d_%H%M%S')
                filename = f"{report_type}_report_{timestamp}.pdf"
            
            # 获取当前文件所在目录下的manager目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            manager_dir = os.path.join(current_dir, '..', 'manager', year, month)
            
            # 确保目录存在
            os.makedirs(manager_dir, exist_ok=True)
            
            return os.path.join(manager_dir, filename)
            
        except Exception as e:
            logger.error(f"创建manager文件路径失败: {e}")
            # 降级到临时文件
            return PDFBase.create_temp_file()
    
    @staticmethod
    def generate_exchange_receipt(transaction, session, reprint_time=None, language='zh'):
        """
        生成兑换交易PDF票据
        
        Args:
            transaction: 交易记录对象
            session: 数据库会话
            reprint_time: 重新打印时间（可选）
            language: 语言代码 ('zh', 'en', 'th')
            
        Returns:
            str: PDF文件的base64编码内容
        """
        try:
            # 获取相关数据
            from models.exchange_models import Currency, Operator, Branch
            currency = session.query(Currency).filter_by(id=transaction.currency_id).first()
            operator = session.query(Operator).filter_by(id=transaction.operator_id).first()
            branch = session.query(Branch).filter_by(id=transaction.branch_id).first()
            
            # 获取网点本币信息
            base_currency_code = 'USD'  # 避免硬编码CNY，使用通用默认值
            if branch and branch.base_currency_id:
                base_currency = session.query(Currency).filter_by(id=branch.base_currency_id).first()
                if base_currency:
                    base_currency_code = base_currency.currency_code
            
            # 构建交易数据
            transaction_data = {
                'transaction_no': transaction.transaction_no,
                'transaction_date': transaction.transaction_date.strftime('%Y-%m-%d') if transaction.transaction_date else '',
                'transaction_time': transaction.transaction_time or '',
                'formatted_datetime': f"{transaction.transaction_date.strftime('%Y-%m-%d')} {transaction.transaction_time}" if transaction.transaction_date and transaction.transaction_time else '',
                'type': transaction.type,
                'amount': transaction.amount,
                'rate': transaction.rate,
                'local_amount': transaction.local_amount,
                'currency_code': currency.currency_code if currency else '',
                'base_currency': base_currency_code,  # 添加本币信息
                'base_currency_code': base_currency_code,  # 兼容性字段
                'customer_name': transaction.customer_name or '',
                'customer_id': transaction.customer_id or '',
                'customer_address': getattr(transaction, 'customer_address', '') or '',
                'customer_country_code': getattr(transaction, 'customer_country_code', '') or 'TH',
                'purpose': transaction.purpose or '',
                'remarks': transaction.remarks or '',
                'operator_name': operator.name if operator else '',
                'branch_name': branch.branch_name if branch else '',
                'branch_code': branch.branch_code if branch else '',
                'branch_license': getattr(branch, 'license_number', '') if branch else '',
                'branch_website': getattr(branch, 'website', '') if branch else '',
                # 新增字段
                'company_full_name': branch.company_full_name if branch else '',
                'tax_registration_number': branch.tax_registration_number if branch else '',
                'payment_method': getattr(transaction, 'payment_method', 'cash') or 'cash',
                'payment_is_foreign_account': bool(getattr(transaction, 'use_fcd', False) or getattr(transaction, 'payment_is_foreign_account', False)),
                'payment_method_note': getattr(transaction, 'payment_method_note', '') or '',
                'reprint_time': reprint_time.strftime('%Y-%m-%d %H:%M:%S') if reprint_time else None,
                'language': language,  # 添加语言标识
                'session': session  # 传递session用于查询国家名称
            }
            
            # 生成临时文件路径
            temp_file = PDFBase.create_temp_file()
            
            # 生成PDF，传递语言参数
            success = ExchangePDFGenerator.generate_pdf(transaction_data, temp_file, language)
            
            if success:
                # 读取文件内容并编码为base64
                with open(temp_file, 'rb') as f:
                    pdf_content = base64.b64encode(f.read()).decode('utf-8')
                
                # 删除临时文件
                os.remove(temp_file)
                
                return pdf_content
            else:
                raise Exception("PDF生成失败")
                
        except Exception as e:
            logger.error(f"生成兑换收据失败: {e}")
            raise

    @staticmethod
    def generate_dual_direction_receipt(business_group_data, session, language='zh'):
        """
        生成双向交易PDF票据

        Args:
            business_group_data: 业务组数据，包含多个交易记录和面值详情
            session: 数据库会话
            language: 语言代码 ('zh', 'en', 'th')

        Returns:
            str: PDF文件的base64编码内容
        """
        try:
            return DualDirectionPDFGenerator.generate_dual_direction_receipt(business_group_data, session, language)
        except Exception as e:
            logger.error(f"生成双向交易收据失败: {e}")
            raise

    @staticmethod
    def generate_reversal_receipt(transaction, session, reprint_time=None, language='zh'):
        """
        生成交易冲正PDF票据
        
        Args:
            transaction: 冲正交易记录对象
            session: 数据库会话
            reprint_time: 重新打印时间（可选）
            language: 语言代码 ('zh', 'en', 'th')
            
        Returns:
            str: PDF文件的base64编码内容
        """
        try:
            # 获取相关数据
            from models.exchange_models import Currency, Operator, Branch, ExchangeTransaction
            currency = session.query(Currency).filter_by(id=transaction.currency_id).first()
            operator = session.query(Operator).filter_by(id=transaction.operator_id).first()
            branch = session.query(Branch).filter_by(id=transaction.branch_id).first()
            
            # 获取原交易记录
            original_tx = None
            if transaction.original_transaction_no:
                original_tx = session.query(ExchangeTransaction).filter_by(
                    transaction_no=transaction.original_transaction_no
                ).first()
            
            # 构建交易数据
            transaction_data = {
                'reversal_no': transaction.transaction_no,
                'reversal_time': f"{transaction.transaction_date.strftime('%Y-%m-%d')} {transaction.transaction_time}" if transaction.transaction_date and transaction.transaction_time else '',
                'original_no': transaction.original_transaction_no or '',
                'amount': abs(float(transaction.amount)),  # 显示绝对值
                'currency_code': currency.currency_code if currency else '',
                'reason': transaction.customer_name or '交易冲正',  # customer_name字段存储冲正原因
                'operator_name': operator.name if operator else '',
                'branch_name': branch.branch_name if branch else '',
                'branch_code': branch.branch_code if branch else '',
                'original_customer_name': original_tx.customer_name if original_tx else '原交易客户',
                'reprint_time': reprint_time.strftime('%Y-%m-%d %H:%M:%S') if reprint_time else None
            }
            
            # 生成临时文件路径
            temp_file = PDFBase.create_temp_file()
            
            # 生成PDF，传递语言参数
            success = ReversalPDFGenerator.generate_pdf(transaction_data, temp_file, language)
            
            if success:
                # 读取文件内容并编码为base64
                with open(temp_file, 'rb') as f:
                    pdf_content = base64.b64encode(f.read()).decode('utf-8')
                
                # 删除临时文件
                os.remove(temp_file)
                
                return pdf_content
            else:
                raise Exception("PDF生成失败")
                
        except Exception as e:
            logger.error(f"生成冲正收据失败: {e}")
            raise
    
    @staticmethod
    def generate_balance_receipt(transaction, session, balance_type, reprint_time=None, language='zh'):
        """
        生成余额操作PDF票据
        
        Args:
            transaction: 交易记录对象
            session: 数据库会话
            balance_type: 余额类型 ('adjustment' 或 'initial')
            reprint_time: 重新打印时间（可选）
            language: 语言代码 ('zh', 'en', 'th')
            
        Returns:
            str: PDF文件的base64编码内容
        """
        try:
            # 获取相关数据
            from models.exchange_models import Currency, Operator, Branch
            currency = session.query(Currency).filter_by(id=transaction.currency_id).first()
            operator = session.query(Operator).filter_by(id=transaction.operator_id).first()
            branch = session.query(Branch).filter_by(id=transaction.branch_id).first()
            
            # 构建交易数据
            transaction_data = {
                'transaction_no': transaction.transaction_no,
                'transaction_date': transaction.transaction_date.strftime('%Y-%m-%d') if transaction.transaction_date else '',
                'transaction_time': transaction.transaction_time or '',
                'formatted_datetime': f"{transaction.transaction_date.strftime('%Y-%m-%d')} {transaction.transaction_time}" if transaction.transaction_date and transaction.transaction_time else '',
                'currency_code': currency.currency_code if currency else '',
                'currency_name': currency.currency_name if currency else '',  # 添加币种名称
                'custom_flag_filename': currency.custom_flag_filename if currency else None,  # 添加自定义图标文件名
                'amount': transaction.amount,
                'balance_before': getattr(transaction, 'balance_before', ''),
                'balance_after': getattr(transaction, 'balance_after', ''),
                'reason': transaction.customer_name or '',  # customer_name字段存储原因
                'operator_name': operator.name if operator else '',
                'branch_name': branch.branch_name if branch else '',
                'branch_code': branch.branch_code if branch else '',
                'reprint_time': reprint_time.strftime('%Y-%m-%d %H:%M:%S') if reprint_time else None,
                'language': language  # 添加语言标识
            }
            
            # 生成临时文件路径
            temp_file = PDFBase.create_temp_file()
            
            # 生成PDF
            success = BalancePDFGenerator.generate_pdf(transaction_data, temp_file, balance_type, language)
            
            if success:
                # 读取文件内容并编码为base64
                with open(temp_file, 'rb') as f:
                    pdf_content = base64.b64encode(f.read()).decode('utf-8')
                
                # 删除临时文件
                os.remove(temp_file)
                
                return pdf_content
            else:
                raise Exception("PDF生成失败")
                
        except Exception as e:
            logger.error(f"生成余额收据失败: {e}")
            raise
    
    @staticmethod
    def generate_summary_receipt(summary_data, language='zh'):
        """
        生成期初余额汇总PDF票据
        
        Args:
            summary_data: 汇总数据字典
            language: 语言代码 ('zh', 'en', 'th')
            
        Returns:
            str: PDF文件的base64编码内容
        """
        try:
            # 生成临时文件路径
            temp_file = PDFBase.create_temp_file()
            
            # 生成PDF
            success = SummaryPDFGenerator.generate_pdf(summary_data, temp_file, language)
            
            if success:
                # 读取文件内容并编码为base64
                with open(temp_file, 'rb') as f:
                    pdf_content = base64.b64encode(f.read()).decode('utf-8')
                
                # 删除临时文件
                os.remove(temp_file)
                
                return pdf_content
            else:
                raise Exception("PDF生成失败")
                
        except Exception as e:
            logger.error(f"生成汇总收据失败: {e}")
            raise

    @staticmethod
    def get_receipt_file_path(transaction_no, transaction_date=None, language='zh'):
        """
        生成PDF文件路径
        
        Args:
            transaction_no: 交易号
            transaction_date: 交易日期（可选）
            language: 语言代码（可选）
            
        Returns:
            str: 文件路径
        """
        return PDFBase.get_receipt_file_path(transaction_no, transaction_date, language)
    
    @staticmethod
    def generate_income_report_pdf(income_data, language='zh'):
        """
        生成收入报表PDF（兼容旧版本）
        
        Args:
            income_data: 收入报表数据（字典或对象列表）
            language: 语言代码
            
        Returns:
            str: PDF文件的base64编码内容
        """
        try:
            # 处理不同类型的输入数据
            if isinstance(income_data, dict):
                # 如果是字典，直接使用
                reports_data = income_data
            elif isinstance(income_data, list):
                # 如果是列表，检查是否包含对象
                if income_data and hasattr(income_data[0], 'to_dict'):
                    # 如果是对象列表，转换为字典
                    reports_data = [report.to_dict() for report in income_data]
                else:
                    # 如果是字典列表，直接使用
                    reports_data = income_data
            else:
                # 其他情况，尝试调用to_dict
                reports_data = income_data.to_dict() if hasattr(income_data, 'to_dict') else income_data
            
            # 构建报表数据
            report_data = {
                'title': '动态收入统计报表',
                'report_type': 'income',
                'language': language,
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'reports': reports_data.get('currencies', []) if isinstance(reports_data, dict) else reports_data,
                'branch_name': reports_data.get('branch_name', '') if isinstance(reports_data, dict) else '',
                'base_currency': reports_data.get('base_currency', '') if isinstance(reports_data, dict) else '',
                'time_range': f"{reports_data.get('start_time', '')} - {reports_data.get('end_time', '')}" if isinstance(reports_data, dict) else '',
                'total_income': reports_data.get('total_income', 0) if isinstance(reports_data, dict) else 0,
                'total_spread_income': reports_data.get('total_spread_income', 0) if isinstance(reports_data, dict) else 0
            }
            
            # 获取manager目录下的文件路径 - 使用EOD规范命名
            eod_id = income_data.get('eod_id')
            eod_date = income_data.get('eod_date')
            file_path = SimplePDFService.get_manager_file_path('income', None, eod_id, eod_date)
            logger.info(f"生成收入报表PDF，文件路径: {file_path}")
            
            # 生成PDF
            success = EODReportPDFGenerator.generate_pdf(report_data, file_path)
            
            if success:
                # 读取文件内容并编码为base64
                with open(file_path, 'rb') as f:
                    pdf_content = base64.b64encode(f.read()).decode('utf-8')
                
                logger.info(f"收入报表PDF生成成功，已保存到: {file_path}")
                return pdf_content
            else:
                raise Exception("PDF生成失败")
                
        except Exception as e:
            logger.error(f"生成收入报表PDF失败: {e}")
            raise
    
    @staticmethod
    def generate_eod_income_report_pdf(print_data, filename, target_date, language='zh'):
        """
        生成日结收入报表PDF文件（新版本，用于日结流程）
        
        Args:
            print_data: 打印数据字典，包含income_reports和stock_reports
            filename: 文件名
            target_date: 目标日期
            language: 语言代码
            
        Returns:
            dict: 包含success状态和file_path的字典
        """
        try:
            # 构建报表数据
            report_data = {
                'title': '日结收入统计报表',
                'report_type': 'eod_income',
                'language': language,
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'date': print_data['date'],
                'branch_id': print_data['branch_id'],
                'eod_id': print_data['eod_id'],
                'income_reports': print_data['income_reports'],
                'stock_reports': print_data['stock_reports']
            }
            
            # 获取文件保存路径（与兑换业务共用路径）
            file_path = PDFBase.get_receipt_file_path(filename, target_date)
            
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 生成PDF
            success = EODReportPDFGenerator.generate_pdf(report_data, file_path)
            
            if success:
                return {
                    'success': True,
                    'file_path': file_path,
                    'filename': filename
                }
            else:
                return {
                    'success': False,
                    'message': 'PDF生成失败'
                }
                
        except Exception as e:
            logger.error(f"生成日结收入报表PDF失败: {e}")
            return {
                'success': False,
                'message': f'生成日结收入报表PDF失败: {str(e)}'
            }
    
    @staticmethod
    def generate_eod_income_report_pdf_to_manager(print_data, filename, target_date, eod_id=None, language='zh'):
        """
        生成日结收入报表PDF文件到manager目录（按年月组织）
        
        Args:
            print_data: 打印数据字典，包含income_reports和stock_reports
            filename: 文件名（EOD规范命名格式）
            target_date: 目标日期
            eod_id: 日结ID
            language: 语言代码 ('zh', 'en', 'th')
            
        Returns:
            dict: 包含success状态和file_path的字典
        """
        try:
            # 使用get_manager_file_path获取文件路径
            output_file = SimplePDFService.get_manager_file_path(
                'income', 
                eod_id=eod_id, 
                eod_date=target_date
            )
            
            # 如果filename不是默认生成的，使用传入的filename
            if filename and not filename.startswith('income_report_'):
                # 保持目录结构，只替换文件名
                output_file = os.path.join(os.path.dirname(output_file), filename)
            
            # 【新增】重新生成时删除旧的PDF文件
            if os.path.exists(output_file):
                try:
                    os.remove(output_file)
                    logger.info(f"删除旧的PDF文件: {output_file}")
                except Exception as e:
                    logger.warning(f"删除旧PDF文件失败: {e}")
            
            # 【新增】检查并删除同名但有数字后缀的文件（处理文件名冲突）
            manager_dir = os.path.dirname(output_file)
            base_filename = os.path.splitext(os.path.basename(output_file))[0]
            if os.path.exists(manager_dir):
                for existing_file in os.listdir(manager_dir):
                    if existing_file.startswith(base_filename) and existing_file.endswith('.pdf'):
                        existing_path = os.path.join(manager_dir, existing_file)
                        try:
                            os.remove(existing_path)
                            logger.info(f"删除冲突的PDF文件: {existing_path}")
                        except Exception as e:
                            logger.warning(f"删除冲突PDF文件失败: {e}")
            
            logger.info(f"开始生成收入报表PDF到manager目录: {output_file}")
            
            # 构建完整的打印数据
            comprehensive_data = {
                'date': target_date.isoformat() if hasattr(target_date, 'isoformat') else str(target_date),
                'branch_id': print_data.get('branch_id'),
                'eod_id': print_data.get('eod_id') or eod_id,
                'income_reports': print_data.get('income_reports', []),
                'stock_reports': print_data.get('stock_reports', []),
                'base_currency_data': print_data.get('base_currency_data')
            }
            
            # 记录PDF生成详情
            logger.info(f"生成{language}语言PDF - EOD ID: {comprehensive_data.get('eod_id')}")
            
            # 构建完整的打印数据结构
            formatted_print_data = {
                'header': {
                    'title': '综合日结报表',
                    'date': target_date.strftime('%Y年%m月%d日') if hasattr(target_date, 'strftime') else str(target_date),
                    'branch_id': comprehensive_data['branch_id'],
                    'eod_id': comprehensive_data['eod_id'],
                    'generated_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                'sections': [
                    {
                        'title': '各币种收入统计',
                        'type': 'income',
                        'data': comprehensive_data['income_reports']
                    },
                    {
                        'title': '外币库存',
                        'type': 'stock',
                        'data': comprehensive_data['stock_reports']
                    }
                ]
            }
            
            # 添加本币库存数据（总是添加，如果没有数据会显示"暂无数据"）
            base_currency_section = {
                'title': '本币库存',
                'type': 'base_currency',
                'data': comprehensive_data.get('base_currency_data')
            }
            formatted_print_data['sections'].append(base_currency_section)
            
            # 本币库存数据已准备就绪
            logger.info(f"本币库存数据已加入PDF - 语言: {language}")
            
            # 生成PDF
            # 使用正确的方法名和数据格式
            report_data_for_pdf = {
                'report_type': 'eod_income',
                'title': formatted_print_data['header']['title'],
                'content': formatted_print_data,
                'language': language,
                'time_range': print_data.get('time_range')  # 【修复】传递CalGain查询的实际时间范围
            }
            success = EODReportPDFGenerator.generate_pdf(report_data_for_pdf, output_file)
            
            if success:
                logger.info(f"收入报表PDF生成成功: {output_file}")
                return {
                    'success': True,
                    'file_path': output_file,
                    'filename': os.path.basename(output_file),
                    'message': '收入报表PDF生成成功'
                }
            else:
                logger.error(f"收入报表PDF生成失败: {output_file}")
                return {
                    'success': False,
                    'message': '收入报表PDF生成失败'
                }
                
        except Exception as e:
            logger.error(f"生成收入报表PDF到manager目录失败: {e}")
            return {
                'success': False,
                'message': f'生成收入报表PDF失败: {str(e)}'
            }
    
    @staticmethod
    def generate_stock_report_pdf(stock_data, language='zh'):
        """
        生成库存报表PDF
        
        Args:
            stock_data: 库存报表数据（字典或对象列表）
            language: 语言代码
            
        Returns:
            str: PDF文件的base64编码内容
        """
        try:
            # 处理不同类型的输入数据
            if isinstance(stock_data, dict):
                # 如果是字典，直接使用
                reports_data = stock_data
            elif isinstance(stock_data, list):
                # 如果是列表，检查是否包含对象
                if stock_data and hasattr(stock_data[0], 'to_dict'):
                    # 如果是对象列表，转换为字典
                    reports_data = [report.to_dict() for report in stock_data]
                else:
                    # 如果是字典列表，直接使用
                    reports_data = stock_data
            else:
                # 其他情况，尝试调用to_dict
                reports_data = stock_data.to_dict() if hasattr(stock_data, 'to_dict') else stock_data
            
            # 构建报表数据
            report_data = {
                'title': '库存外币统计报表',
                'report_type': 'stock',
                'language': language,
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'reports': reports_data.get('currencies', []) if isinstance(reports_data, dict) else reports_data,
                'branch_name': reports_data.get('branch_name', '') if isinstance(reports_data, dict) else '',
                'base_currency': reports_data.get('base_currency', '') if isinstance(reports_data, dict) else '',
                'time_range': f"{reports_data.get('start_time', '')} - {reports_data.get('end_time', '')}" if isinstance(reports_data, dict) else ''
            }
            
            # 获取manager目录下的文件路径
            file_path = SimplePDFService.get_manager_file_path('stock', 'foreign_currency_stock_report')
            logger.info(f"生成库存报表PDF，文件路径: {file_path}")
            
            # 生成PDF
            success = EODReportPDFGenerator.generate_pdf(report_data, file_path)
            
            if success:
                # 读取文件内容并编码为base64
                with open(file_path, 'rb') as f:
                    pdf_content = base64.b64encode(f.read()).decode('utf-8')
                
                logger.info(f"库存报表PDF生成成功，已保存到: {file_path}")
                return pdf_content
            else:
                raise Exception("PDF生成失败")
                
        except Exception as e:
            logger.error(f"生成库存报表PDF失败: {e}")
            raise
    
    @staticmethod
    def generate_eod_summary_pdf(eod_data, language='zh'):
        """
        生成日结汇总报表PDF
        
        Args:
            eod_data: 日结数据字典
            language: 语言代码
            
        Returns:
            str: PDF文件的base64编码内容
        """
        try:
            # 构建报表数据
            report_data = {
                'title': '日结汇总报表',
                'report_type': 'eod_summary',
                'language': language,
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'eod_data': eod_data
            }
            
            # 生成临时文件路径
            temp_file = PDFBase.create_temp_file()
            
            # 生成PDF
            success = EODReportPDFGenerator.generate_pdf(report_data, temp_file)
            
            if success:
                # 读取文件内容并编码为base64
                with open(temp_file, 'rb') as f:
                    pdf_content = base64.b64encode(f.read()).decode('utf-8')
                
                # 删除临时文件
                os.remove(temp_file)
                
                return pdf_content
            else:
                raise Exception("PDF生成失败")
                
        except Exception as e:
            logger.error(f"生成日结汇总报表PDF失败: {e}")
            raise
    
    @staticmethod
    def generate_eod_balance_report_pdf(balance_data, language='zh'):
        """
        生成日结余额报表PDF（含余额调节记录）
        
        Args:
            balance_data: 余额数据字典
            language: 语言代码
            
        Returns:
            str: PDF文件的base64编码内容
        """
        try:
            # 构建报表数据
            report_data = {
                'title': '日结余额报表',
                'report_type': 'eod_balance',
                'language': language,
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'balance_data': balance_data
            }
            
            # 生成临时文件路径
            temp_file = PDFBase.create_temp_file()
            
            # 生成PDF
            success = EODReportPDFGenerator.generate_pdf(report_data, temp_file)
            
            if success:
                # 读取文件内容并编码为base64
                with open(temp_file, 'rb') as f:
                    pdf_content = base64.b64encode(f.read()).decode('utf-8')
                
                # 删除临时文件
                os.remove(temp_file)
                
                return pdf_content
            else:
                raise Exception("PDF生成失败")
                
        except Exception as e:
            logger.error(f"生成日结余额报表PDF失败: {e}")
            raise 
    
    @staticmethod
    def generate_comprehensive_eod_report_pdf(comprehensive_data, filename, target_date, language='zh'):
        """
        生成综合日结报表PDF - 包含外币收入、外币库存、本币库存
        
        Args:
            comprehensive_data: 综合报表数据
            filename: 输出文件名
            target_date: 目标日期
            language: 语言代码 ('zh', 'en', 'th')
            
        Returns:
            dict: 包含成功状态和文件路径的字典
        """
        try:
            # 构建输出文件路径
            receipts_dir = os.path.join(os.path.dirname(__file__), '..', 'receipts')
            year = target_date.year
            month = target_date.month
            
            # 创建年月子目录
            target_dir = os.path.join(receipts_dir, str(year), f"{month:02d}")
            os.makedirs(target_dir, exist_ok=True)
            
            output_file = os.path.join(target_dir, filename)
            
            # 构建完整的打印数据
            print_data = {
                'header': {
                    'title': '综合日结报表',
                    'date': target_date.strftime('%Y年%m月%d日'),
                    'branch_id': comprehensive_data['branch_id'],
                    'eod_id': comprehensive_data['eod_id'],
                    'generated_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                'sections': [
                    {
                        'title': '收入',
                        'type': 'income',
                        'data': comprehensive_data['income_reports']
                    },
                    {
                        'title': '外币库存',
                        'type': 'stock',
                        'data': comprehensive_data['stock_reports']
                    },
                    {
                        'title': '本币库存',
                        'type': 'base_currency',
                        'data': comprehensive_data['base_currency_data']
                    }
                ]
            }
            
            # 生成PDF
            success = EODReportPDFGenerator.generate_comprehensive_pdf(print_data, output_file, language)
            
            if success:
                return {
                    'success': True,
                    'file_path': output_file,
                    'message': '综合报表PDF生成成功'
                }
            else:
                return {
                    'success': False,
                    'message': '综合报表PDF生成失败'
                }
                
        except Exception as e:
            logger.error(f"生成综合日结报表PDF失败: {e}")
            return {
                'success': False,
                'message': f'生成综合日结报表PDF失败: {str(e)}'
            }
    
    @staticmethod
    def generate_simple_eod_report_pdf(report_data, filename, target_date, language='zh'):
        """
        生成简单日结报表PDF - 用于第7步（统一使用manager目录）
        
        Args:
            report_data: 报表数据
            filename: 输出文件名
            target_date: 目标日期
            language: 语言代码
            
        Returns:
            dict: 包含成功状态和文件路径的字典
        """
        try:
            # 从report_data中提取eod_id
            eod_id = None
            if 'header' in report_data and 'eod_id' in report_data['header']:
                eod_id = report_data['header']['eod_id']
            
            # 检查传入的filename是否已经包含语言后缀
            if filename and ('_en.pdf' in filename or '_th.pdf' in filename or filename.endswith('.pdf')):
                # 如果filename已经包含语言后缀，直接使用
                # 获取manager目录路径
                year = target_date.strftime('%Y')
                month = target_date.strftime('%m')
                current_dir = os.path.dirname(os.path.abspath(__file__))
                manager_dir = os.path.join(current_dir, '..', 'manager', year, month)
                os.makedirs(manager_dir, exist_ok=True)
                output_file = os.path.join(manager_dir, filename)
            else:
                # 使用get_manager_file_path获取统一路径，传递eod_id以生成正确的文件名
                output_file = SimplePDFService.get_manager_file_path('cashout', None, eod_id, target_date)
            
            # 检查传入的数据结构
            if 'header' in report_data and 'sections' in report_data:
                # 已经是构建好的print_data，直接使用
                print_data = report_data
            else:
                # 原始report_data，需要构建
                print_data = {
                    'header': {
                        'title': '日结报表',
                        'date': target_date.strftime('%Y年%m月%d日'),
                        'branch_id': report_data.get('branch_id'),
                        'eod_id': report_data.get('eod_id'),
                        'generated_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    },
                    'report_data': report_data
                }
            
            # 生成PDF（使用与第5步相同的方法）
            pdf_result = EODReportPDFGenerator.generate_simple_eod_report_pdf(print_data, output_file, language)
            
            if pdf_result['success']:
                return {
                    'success': True,
                    'file_path': output_file,
                    'message': '日结报表PDF生成成功'
                }
            else:
                return {
                    'success': False,
                    'message': pdf_result.get('message', '日结报表PDF生成失败')
                }
                
        except Exception as e:
            logger.error(f"生成简单日结报表PDF失败: {e}")
            return {
                'success': False,
                'message': f'生成简单日结报表PDF失败: {str(e)}'
            } 