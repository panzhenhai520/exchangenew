import os
import logging
from datetime import datetime
from decimal import Decimal
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from models.exchange_models import EODStatus, Currency, Operator
from services.db_service import DatabaseService
from utils.i18n_utils import I18nUtils

class DifferenceReportService:
    """差额报告生成服务"""
    
    @staticmethod
    def generate_difference_adjustment_report(eod_id, adjust_data, language='zh'):
        """
        生成差额调节报告
        """
        session = DatabaseService.get_session()
        try:
            # 获取EOD信息
            eod_status = session.query(EODStatus).filter_by(id=eod_id).first()
            if not eod_status:
                return {'success': False, 'message': '日结记录不存在'}
            
            # 获取操作员信息
            operator = session.query(Operator).filter_by(id=eod_status.started_by).first()
            operator_name = operator.name if operator else '未知操作员'
            
            # 生成报告文件名
            date_str = eod_status.date.strftime('%Y%m%d')
            filename_base = f"{date_str}EOD{eod_id:03d}Diff"
            
            # 根据语言生成不同版本的文件名
            if language == 'th':
                filename = f"{filename_base}_th.pdf"
            elif language == 'en':
                filename = f"{filename_base}_en.pdf"
            else:
                filename = f"{filename_base}.pdf"
            
            # 创建报告目录
            year_month = eod_status.date.strftime('%Y/%m')
            report_dir = os.path.join('manager', year_month)
            os.makedirs(report_dir, exist_ok=True)
            
            filepath = os.path.join(report_dir, filename)
            
            # 生成PDF报告
            DifferenceReportService._create_difference_adjustment_pdf(
                filepath, eod_status, adjust_data, operator_name, language
            )
            
            return {
                'success': True,
                'message': f'差额调节报告已生成: {filename}',
                'filepath': filepath,
                'filename': filename
            }
            
        except Exception as e:
            logging.error(f"生成差额调节报告失败: {str(e)}")
            return {'success': False, 'message': f'生成差额调节报告失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def generate_difference_report(eod_id, verification_results, language='zh'):
        """
        生成差额报告（忽略差额时）
        """
        session = DatabaseService.get_session()
        try:
            # 获取EOD信息
            eod_status = session.query(EODStatus).filter_by(id=eod_id).first()
            if not eod_status:
                return {'success': False, 'message': '日结记录不存在'}
            
            # 获取操作员信息
            operator = session.query(Operator).filter_by(id=eod_status.started_by).first()
            operator_name = operator.name if operator else '未知操作员'
            
            # 生成报告文件名
            date_str = eod_status.date.strftime('%Y%m%d')
            filename_base = f"{date_str}EOD{eod_id:03d}Diff"
            
            # 根据语言生成不同版本的文件名
            if language == 'th':
                filename = f"{filename_base}_th.pdf"
            elif language == 'en':
                filename = f"{filename_base}_en.pdf"
            else:
                filename = f"{filename_base}.pdf"
            
            # 创建报告目录
            year_month = eod_status.date.strftime('%Y/%m')
            report_dir = os.path.join('manager', year_month)
            os.makedirs(report_dir, exist_ok=True)
            
            filepath = os.path.join(report_dir, filename)
            
            # 生成PDF报告
            DifferenceReportService._create_difference_pdf(
                filepath, eod_status, verification_results, operator_name, language
            )
            
            return {
                'success': True,
                'message': f'差额报告已生成: {filename}',
                'filepath': filepath,
                'filename': filename
            }
            
        except Exception as e:
            logging.error(f"生成差额报告失败: {str(e)}")
            return {'success': False, 'message': f'生成差额报告失败: {str(e)}'}
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def _create_difference_adjustment_pdf(filepath, eod_status, adjust_data, operator_name, language):
        """
        创建差额调节报告PDF
        """
        # 注册字体 - 改进字体处理
        try:
            if language == 'zh':
                # 尝试多个中文字体路径
                font_paths = [
                    'fonts/simhei.ttf',
                    'src/fonts/simhei.ttf',
                    '../fonts/simhei.ttf',
                    '../../fonts/simhei.ttf'
                ]
                font_name = 'SimHei'
                font_registered = False
                for font_path in font_paths:
                    if os.path.exists(font_path):
                        try:
                            pdfmetrics.registerFont(TTFont('SimHei', font_path))
                            font_registered = True
                            logging.info(f"成功注册中文字体: {font_path}")
                            break
                        except Exception as font_error:
                            logging.warning(f"注册字体失败 {font_path}: {font_error}")
                            continue
                if not font_registered:
                    font_name = 'Helvetica'
                    logging.warning("无法注册中文字体，使用Helvetica")
            elif language == 'th':
                # 尝试多个泰文字体路径
                font_paths = [
                    'fonts/tahoma.ttf',
                    'src/fonts/tahoma.ttf',
                    '../fonts/tahoma.ttf',
                    '../../fonts/tahoma.ttf'
                ]
                font_name = 'Tahoma'
                font_registered = False
                for font_path in font_paths:
                    if os.path.exists(font_path):
                        try:
                            pdfmetrics.registerFont(TTFont('Tahoma', font_path))
                            font_registered = True
                            logging.info(f"成功注册泰文字体: {font_path}")
                            break
                        except Exception as font_error:
                            logging.warning(f"注册字体失败 {font_path}: {font_error}")
                            continue
                if not font_registered:
                    font_name = 'Helvetica'
                    logging.warning("无法注册泰文字体，使用Helvetica")
            else:
                font_name = 'Helvetica'
        except Exception as e:
            logging.error(f"字体注册失败: {e}")
            font_name = 'Helvetica'
        
        # 创建PDF文档
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        
        # 获取样式 - 与收入报表保持一致
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName=font_name,
            fontSize=18,
            spaceAfter=30,
            alignment=1,  # 居中
            textColor=colors.black  # 黑色标题，与收入报表一致
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=10,
            spaceAfter=12
        )
        
        section_style = ParagraphStyle(
            'SectionStyle',
            parent=styles['Heading2'],
            fontName=font_name,
            fontSize=12,
            spaceAfter=15,
            textColor=colors.black  # 黑色章节标题，与收入报表一致
        )
        
        # 标题
        try:
            title_text = I18nUtils.get_message('reports.difference_adjustment_title', language)
        except Exception as e:
            logging.warning(f"获取翻译失败，使用默认标题: {e}")
            if language == 'zh':
                title_text = '日结差额调节报告'
            elif language == 'en':
                title_text = 'EOD Difference Adjustment Report'
            elif language == 'th':
                title_text = 'รายงานการปรับปรุงส่วนต่างการปิดบัญชี'
            else:
                title_text = '日结差额调节报告'
        story.append(Paragraph(title_text, title_style))
        story.append(Spacer(1, 20))
        
        # 基本信息 - 改进表格样式
        def safe_get_message(key, language, default_zh='', default_en='', default_th=''):
            """改进的翻译获取函数，确保返回正确的翻译"""
            try:
                # 首先尝试使用I18nUtils获取翻译
                message = I18nUtils.get_message(key, language)
                # 如果返回的是key本身，说明没有找到翻译，使用默认值
                if message == key:
                    if language == 'zh':
                        return default_zh
                    elif language == 'en':
                        return default_en
                    elif language == 'th':
                        return default_th
                    else:
                        return default_zh
                return message
            except Exception as e:
                logging.warning(f"获取翻译失败 {key}: {e}")
                if language == 'zh':
                    return default_zh
                elif language == 'en':
                    return default_en
                elif language == 'th':
                    return default_th
                else:
                    return default_zh
        
        # 【修复】确保操作员姓名正确显示
        if not operator_name or operator_name == '未知操作员':
            operator_name = '系统管理员' if language == 'zh' else ('System Administrator' if language == 'en' else 'ผู้ดูแลระบบ')
        
        info_data = [
            [safe_get_message('reports.eod_id', language, '日结编号', 'EOD ID', 'รหัสการปิดบัญชี'), f"EOD{eod_status.id:03d}"],
            [safe_get_message('reports.eod_date', language, '日结日期', 'EOD Date', 'วันที่ปิดบัญชี'), eod_status.date.strftime('%Y-%m-%d')],
            [safe_get_message('reports.eod_time', language, '日结时间', 'EOD Time', 'เวลาปิดบัญชี'), eod_status.started_at.strftime('%Y-%m-%d %H:%M:%S') if eod_status.started_at else ''],
            [safe_get_message('reports.operator', language, '操作员', 'Operator', 'ผู้ดำเนินการ'), operator_name]
        ]
        
        info_table = Table(info_data, colWidths=[1.8*inch, 2.8*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),  # 黑色边框，与收入报表一致
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),  # 浅蓝色背景
            ('TEXTCOLOR', (0, 0), (0, -1), colors.black),  # 黑色文字，与收入报表一致
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),  # 米色背景，与收入报表一致
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # 差额调节明细
        subtitle_text = safe_get_message('reports.adjustment_details', language, '差额调节明细', 'Adjustment Details', 'รายละเอียดการปรับปรุง')
        story.append(Paragraph(subtitle_text, section_style))
        story.append(Spacer(1, 10))
        
        # 表头
        headers = [
            safe_get_message('reports.currency', language, '币种', 'Currency', 'สกุลเงิน'),
            safe_get_message('reports.theoretical_balance', language, '理论库存', 'Theoretical Balance', 'ยอดตามทฤษฎี'),
            safe_get_message('reports.actual_balance', language, '实际库存', 'Actual Balance', 'ยอดจริง'),
            safe_get_message('reports.adjust_amount', language, '调节金额', 'Adjust Amount', 'จำนวนการปรับปรุง'),
            safe_get_message('reports.reason', language, '调节原因', 'Reason', 'เหตุผล')
        ]
        
        table_data = [headers]
        
        # 添加调节数据
        for item in adjust_data:
            # 获取币种名称 - 使用翻译
            currency_code = item.get('currency_code', '')
            currency_name = item.get('currency_name', '')
            
            # 使用统一的币种翻译服务
            from services.currency_translation_service import CurrencyTranslationService
            translated_name = CurrencyTranslationService.get_currency_name(currency_code, language)
            
            # 根据语言翻译调节原因
            reason_text = item['reason']
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
            
            # 计算原始实际余额：当前实际余额 - 调节金额
            original_actual_balance = item['actual_balance'] - item['adjust_amount']
            row = [
                f"{currency_code} ({translated_name})",
                f"{item['theoretical_balance']:.2f}",
                f"{original_actual_balance:.2f}",  # 使用原始实际余额
                f"{item['adjust_amount']:+.2f}",
                reason_text
            ]
            table_data.append(row)
        
        # 创建表格 - 调整列宽度，让三张表格宽度一致，原因列更宽
        table = Table(table_data, colWidths=[1.3*inch, 1.1*inch, 1.1*inch, 1.1*inch, 2.0*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),  # 黑色边框，与收入报表一致
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),  # 浅蓝色表头背景，与收入报表一致
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),  # 黑色表头文字，与收入报表一致
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),  # 米色数据行背景，与收入报表一致
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # 第一列居中
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),  # 其他列右对齐，与收入报表一致
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 4),
            # 调节金额列的特殊样式
            ('TEXTCOLOR', (3, 1), (3, -1), colors.darkred),  # 调节金额用深红色
            ('FONTSIZE', (3, 1), (3, -1), 10),  # 调节金额字体稍大
        ]))
        
        story.append(table)
        story.append(Spacer(1, 30))
        
        # 签名区域 - 改进签名区域样式
        signature_text = safe_get_message('reports.signature_area', language, '签名区域', 'Signature Area', 'พื้นที่ลงนาม')
        story.append(Paragraph(signature_text, section_style))
        story.append(Spacer(1, 20))
        
        signature_data = [
            [safe_get_message('reports.operator_signature', language, '操作员签名', 'Operator Signature', 'ลายเซ็นผู้ดำเนินการ'), ''],
            [safe_get_message('reports.supervisor_signature', language, '主管签名', 'Supervisor Signature', 'ลายเซ็นผู้ดูแล'), '']
        ]
        
        signature_table = Table(signature_data, colWidths=[2.3*inch, 2.3*inch])
        signature_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),  # 黑色边框，与收入报表一致
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),  # 浅蓝色标签背景，与收入报表一致
            ('TEXTCOLOR', (0, 0), (0, -1), colors.black),  # 黑色标签文字，与收入报表一致
            ('BACKGROUND', (1, 0), (1, -1), colors.white),  # 白色签名区域
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 20),
        ]))
        
        story.append(signature_table)
        
        # 生成PDF
        doc.build(story)
    
    @staticmethod
    def _create_difference_pdf(filepath, eod_status, verification_results, operator_name, language):
        """
        创建差额报告PDF（忽略差额时）
        """
        # 注册字体 - 改进字体处理
        try:
            if language == 'zh':
                # 尝试多个中文字体路径
                font_paths = [
                    'fonts/simhei.ttf',
                    'src/fonts/simhei.ttf',
                    '../fonts/simhei.ttf',
                    '../../fonts/simhei.ttf'
                ]
                font_name = 'SimHei'
                font_registered = False
                for font_path in font_paths:
                    if os.path.exists(font_path):
                        try:
                            pdfmetrics.registerFont(TTFont('SimHei', font_path))
                            font_registered = True
                            logging.info(f"成功注册中文字体: {font_path}")
                            break
                        except Exception as font_error:
                            logging.warning(f"注册字体失败 {font_path}: {font_error}")
                            continue
                if not font_registered:
                    font_name = 'Helvetica'
                    logging.warning("无法注册中文字体，使用Helvetica")
            elif language == 'th':
                # 尝试多个泰文字体路径
                font_paths = [
                    'fonts/tahoma.ttf',
                    'src/fonts/tahoma.ttf',
                    '../fonts/tahoma.ttf',
                    '../../fonts/tahoma.ttf'
                ]
                font_name = 'Tahoma'
                font_registered = False
                for font_path in font_paths:
                    if os.path.exists(font_path):
                        try:
                            pdfmetrics.registerFont(TTFont('Tahoma', font_path))
                            font_registered = True
                            logging.info(f"成功注册泰文字体: {font_path}")
                            break
                        except Exception as font_error:
                            logging.warning(f"注册字体失败 {font_path}: {font_error}")
                            continue
                if not font_registered:
                    font_name = 'Helvetica'
                    logging.warning("无法注册泰文字体，使用Helvetica")
            else:
                font_name = 'Helvetica'
        except Exception as e:
            logging.error(f"字体注册失败: {e}")
            font_name = 'Helvetica'
        
        # 创建PDF文档
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        
        # 获取样式 - 改进样式定义
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName=font_name,
            fontSize=18,
            spaceAfter=30,
            alignment=1,  # 居中
            textColor=colors.darkred  # 深红色标题（区分于调节报告）
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=10,
            spaceAfter=12
        )
        
        section_style = ParagraphStyle(
            'SectionStyle',
            parent=styles['Heading2'],
            fontName=font_name,
            fontSize=12,
            spaceAfter=15,
            textColor=colors.darkorange  # 深橙色章节标题
        )
        
        # 标题
        try:
            title_text = I18nUtils.get_message('reports.difference_report_title', language)
        except Exception as e:
            logging.warning(f"获取翻译失败，使用默认标题: {e}")
            if language == 'zh':
                title_text = '日结差额报告'
            elif language == 'en':
                title_text = 'EOD Difference Report'
            elif language == 'th':
                title_text = 'รายงานส่วนต่างการปิดบัญชี'
            else:
                title_text = '日结差额报告'
        story.append(Paragraph(title_text, title_style))
        story.append(Spacer(1, 20))
        
        # 基本信息 - 改进表格样式
        def safe_get_message(key, language, default_zh='', default_en='', default_th=''):
            """改进的翻译获取函数，确保返回正确的翻译"""
            try:
                # 首先尝试使用I18nUtils获取翻译
                message = I18nUtils.get_message(key, language)
                # 如果返回的是key本身，说明没有找到翻译，使用默认值
                if message == key:
                    if language == 'zh':
                        return default_zh
                    elif language == 'en':
                        return default_en
                    elif language == 'th':
                        return default_th
                    else:
                        return default_zh
                return message
            except Exception as e:
                logging.warning(f"获取翻译失败 {key}: {e}")
                if language == 'zh':
                    return default_zh
                elif language == 'en':
                    return default_en
                elif language == 'th':
                    return default_th
                else:
                    return default_zh
        
        # 【修复】确保操作员姓名正确显示
        if not operator_name or operator_name == '未知操作员':
            operator_name = '系统管理员' if language == 'zh' else ('System Administrator' if language == 'en' else 'ผู้ดูแลระบบ')
        
        info_data = [
            [safe_get_message('reports.eod_id', language, '日结编号', 'EOD ID', 'รหัสการปิดบัญชี'), f"EOD{eod_status.id:03d}"],
            [safe_get_message('reports.eod_date', language, '日结日期', 'EOD Date', 'วันที่ปิดบัญชี'), eod_status.date.strftime('%Y-%m-%d')],
            [safe_get_message('reports.eod_time', language, '日结时间', 'EOD Time', 'เวลาปิดบัญชี'), eod_status.started_at.strftime('%Y-%m-%d %H:%M:%S') if eod_status.started_at else ''],
            [safe_get_message('reports.operator', language, '操作员', 'Operator', 'ผู้ดำเนินการ'), operator_name]
        ]
        
        info_table = Table(info_data, colWidths=[1.8*inch, 2.8*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),  # 黑色边框，与收入报表一致
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),  # 浅蓝色背景，与收入报表一致
            ('TEXTCOLOR', (0, 0), (0, -1), colors.black),  # 黑色文字，与收入报表一致
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),  # 米色背景，与收入报表一致
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # 差额明细
        subtitle_text = safe_get_message('reports.difference_details', language, '差额明细', 'Difference Details', 'รายละเอียดส่วนต่าง')
        story.append(Paragraph(subtitle_text, section_style))
        story.append(Spacer(1, 10))
        
        # 表头
        headers = [
            safe_get_message('reports.currency', language, '币种', 'Currency', 'สกุลเงิน'),
            safe_get_message('reports.theoretical_balance', language, '理论库存', 'Theoretical Balance', 'ยอดตามทฤษฎี'),
            safe_get_message('reports.actual_balance', language, '实际库存', 'Actual Balance', 'ยอดจริง'),
            safe_get_message('reports.difference', language, '差异', 'Difference', 'ส่วนต่าง')
        ]
        
        table_data = [headers]
        
        # 添加差额数据
        for result in verification_results:
            if not result['is_match']:  # 只显示有差异的币种
                # 获取币种名称 - 使用翻译
                currency_code = result.get('currency_code', '')
                currency_name = result.get('currency_name', '')
                
                # 使用统一的币种翻译服务
                from services.currency_translation_service import CurrencyTranslationService
                translated_name = CurrencyTranslationService.get_currency_name(currency_code, language)
                
                row = [
                    f"{currency_code} ({translated_name})",
                    f"{result['theoretical_balance']:.2f}",
                    f"{result['actual_balance']:.2f}",
                    f"{result['difference']:+.2f}"
                ]
                table_data.append(row)
        
        # 创建表格 - 调整列宽度，让三张表格宽度一致
        table = Table(table_data, colWidths=[1.3*inch, 1.1*inch, 1.1*inch, 1.1*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),  # 黑色边框，与收入报表一致
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),  # 浅蓝色表头背景，与收入报表一致
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),  # 黑色表头文字，与收入报表一致
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),  # 米色数据行背景，与收入报表一致
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # 第一列居中
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),  # 其他列右对齐，与收入报表一致
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 4),
            # 差异列的特殊样式
            ('TEXTCOLOR', (3, 1), (3, -1), colors.darkred),  # 差异用深红色
            ('FONTSIZE', (3, 1), (3, -1), 10),  # 差异字体稍大
        ]))
        
        story.append(table)
        story.append(Spacer(1, 30))
        
        # 说明文字
        note_text = safe_get_message('reports.difference_note', language, '本报告记录了日结过程中发现的余额差异，已强制继续日结流程。', 'This report records the balance differences found during EOD process, and the EOD process has been forced to continue.', 'รายงานนี้บันทึกส่วนต่างของยอดเงินที่พบในระหว่างกระบวนการปิดบัญชี และกระบวนการปิดบัญชีได้ถูกบังคับให้ดำเนินการต่อ')
        story.append(Paragraph(note_text, normal_style))
        story.append(Spacer(1, 30))
        
        # 签名区域 - 改进签名区域样式
        signature_text = safe_get_message('reports.signature_area', language, '签名区域', 'Signature Area', 'พื้นที่ลงนาม')
        story.append(Paragraph(signature_text, section_style))
        story.append(Spacer(1, 20))
        
        signature_data = [
            [safe_get_message('reports.operator_signature', language, '操作员签名', 'Operator Signature', 'ลายเซ็นผู้ดำเนินการ'), ''],
            [safe_get_message('reports.supervisor_signature', language, '主管签名', 'Supervisor Signature', 'ลายเซ็นผู้ดูแล'), '']
        ]
        
        signature_table = Table(signature_data, colWidths=[2.3*inch, 2.3*inch])
        signature_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),  # 黑色边框，与收入报表一致
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),  # 浅蓝色标签背景，与收入报表一致
            ('TEXTCOLOR', (0, 0), (0, -1), colors.black),  # 黑色标签文字，与收入报表一致
            ('BACKGROUND', (1, 0), (1, -1), colors.white),  # 白色签名区域
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 20),
        ]))
        
        story.append(signature_table)
        
        # 生成PDF
        doc.build(story) 