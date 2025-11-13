# -*- coding: utf-8 -*-
"""
AMLO PDF生成服务 - 完整集成版本
整合CSV字段加载、业务数据映射和PDF填充功能

用法:
    from services.pdf.amlo_pdf_service import generate_amlo_pdf

    # 直接从数据库记录生成PDF
    pdf_path = generate_amlo_pdf(reservation_id, output_dir='/path/to/output')
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

try:
    from .amlo_csv_field_loader import get_csv_field_loader
    from .amlo_pdf_filler_pymupdf import AMLOPDFFillerPyMuPDF  # 使用PyMuPDF支持可编辑表单
    from .amlo_pdf_filler_overlay import AMLOPDFFillerOverlay  # 用于签名PDF（不可编辑）
    from .amlo_data_mapper import AMLODataMapper
except ImportError:
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from amlo_csv_field_loader import get_csv_field_loader
    from amlo_pdf_filler_pymupdf import AMLOPDFFillerPyMuPDF
    from amlo_pdf_filler_overlay import AMLOPDFFillerOverlay
    from amlo_data_mapper import AMLODataMapper


class AMLOPDFService:
    """AMLO PDF生成服务"""

    def __init__(self):
        """初始化服务"""
        self.csv_loader = get_csv_field_loader()
        self.pdf_filler_editable = AMLOPDFFillerPyMuPDF()  # 可编辑PDF（无签名）
        self.pdf_filler_with_signature = AMLOPDFFillerOverlay()  # 带签名PDF（不可编辑）
        self.data_mapper = AMLODataMapper()
        print("[AMLOPDFService] Initialized successfully (hybrid mode: editable + signature support)")

    def generate_pdf_from_reservation(
        self,
        reservation_data: Dict[str, Any],
        output_path: str
    ) -> str:
        """
        从预约数据生成AMLO PDF报告

        Args:
            reservation_data: 预约记录数据，必须包含:
                - report_type: 报告类型 ('AMLO-1-01', 'AMLO-1-02', 'AMLO-1-03')
                - reservation_no: 预约编号
                - customer_id: 客户证件号
                - customer_name: 客户姓名
                - direction: 交易方向 ('buy'/'sell')
                - currency_code: 币种代码
                - local_amount: 本币金额 (THB)
                - amount: 外币金额
                - transaction_date: 交易日期
                - form_data: 表单数据JSON字符串或字典
            output_path: 输出PDF文件路径

        Returns:
            生成的PDF文件路径

        Example:
            >>> service = AMLOPDFService()
            >>> reservation = {
            ...     'report_type': 'AMLO-1-01',
            ...     'reservation_no': 'FI-001-68-001',
            ...     'customer_id': '1234567890123',
            ...     'customer_name': 'นายสมชาย ใจดี',
            ...     'direction': 'buy',
            ...     'currency_code': 'USD',
            ...     'local_amount': 2500000,
            ...     'transaction_date': '2025-10-18',
            ...     'form_data': {'maker_phone': '02-1234567', ...}
            ... }
            >>> pdf_path = service.generate_pdf_from_reservation(reservation, 'output.pdf')
        """
        try:
            # 获取报告类型
            report_type = reservation_data.get('report_type')
            if not report_type:
                raise ValueError("Missing report_type in reservation_data")

            # 解析form_data
            form_data = reservation_data.get('form_data', {})
            if isinstance(form_data, str):
                form_data = json.loads(form_data)

            print(f"[AMLOPDFService] Generating {report_type} PDF")
            print(f"[AMLOPDFService] Reservation No: {reservation_data.get('reservation_no')}")

            # 1. 映射业务数据到PDF字段
            pdf_fields = self.data_mapper.map_reservation_to_pdf_fields(
                report_type,
                reservation_data,
                form_data
            )

            print(f"[AMLOPDFService] Mapped {len(pdf_fields)} fields")

            # 提取签名数据
            signatures = {}
            if reservation_data.get('reporter_signature'):
                sig_data = reservation_data['reporter_signature']
                print(f"[AMLOPDFService] Reporter signature length: {len(sig_data) if sig_data else 0}")
                signatures['reporter_signature'] = sig_data
            if reservation_data.get('customer_signature'):
                sig_data = reservation_data['customer_signature']
                print(f"[AMLOPDFService] Customer signature length: {len(sig_data) if sig_data else 0}")
                signatures['customer_signature'] = sig_data
            if reservation_data.get('auditor_signature'):
                sig_data = reservation_data['auditor_signature']
                print(f"[AMLOPDFService] Auditor signature length: {len(sig_data) if sig_data else 0}")
                signatures['auditor_signature'] = sig_data

            # 2. 填充PDF表单
            # 🔧 修复：始终使用Overlay filler（ReportLab）以确保：
            # - 中文、泰文、英文正确显示（SimHei + Sarabun字体）
            # - 报告编号精确对齐到PDF模板的框格中
            # - checkbox和所有字段正确渲染
            #
            # 注意：Overlay方式生成的PDF不可编辑（这是预期行为，确保数据完整性）
            print(f"[AMLOPDFService] Using Overlay filler for multilingual support")
            result_path = self.pdf_filler_with_signature.fill_form(
                report_type,
                pdf_fields,
                output_path,
                signatures=signatures if signatures else None
            )
            if signatures:
                print(f"[AMLOPDFService] Embedded {len(signatures)} signature(s)")

            print(f"[AMLOPDFService] PDF generated successfully: {result_path}")
            if signatures:
                print(f"[AMLOPDFService] Embedded {len(signatures)} signature(s)")
            return result_path

        except Exception as e:
            print(f"[AMLOPDFService] Error generating PDF: {e}")
            import traceback
            traceback.print_exc()
            raise

    def generate_pdf_from_db(
        self,
        db_session: Session,
        reservation_id: int,
        output_dir: Optional[str] = None
    ) -> str:
        """
        从数据库记录生成AMLO PDF报告

        Args:
            db_session: 数据库会话
            reservation_id: 预约记录ID
            output_dir: 输出目录，默认为 src/amlo_reports/YYYY/MM/

        Returns:
            生成的PDF文件路径
        """
        from sqlalchemy import text

        try:
            # 查询预约记录（包括签名字段）
            sql = text("""
                SELECT
                    r.id,
                    r.reservation_no,
                    r.report_type,
                    r.customer_id,
                    r.customer_name,
                    r.customer_country_code,
                    r.currency_id,
                    c.currency_code as currency_code,
                    r.direction,
                    r.amount,
                    r.local_amount as amount_thb,
                    r.rate,
                    r.form_data,
                    r.created_at as transaction_date,
                    r.branch_id,
                    r.reporter_signature,
                    r.customer_signature,
                    r.auditor_signature
                FROM Reserved_Transaction r
                LEFT JOIN currencies c ON r.currency_id = c.id
                WHERE r.id = :reservation_id
            """)

            result = db_session.execute(sql, {'reservation_id': reservation_id}).fetchone()

            if not result:
                raise ValueError(f"Reservation {reservation_id} not found")

            # 构建预约数据（包括签名）
            reservation_data = {
                'id': result[0],
                'reservation_no': result[1],
                'report_type': result[2],
                'customer_id': result[3],
                'customer_name': result[4],
                'customer_country_code': result[5],
                'currency_id': result[6],
                'currency_code': result[7],
                'direction': result[8],
                'amount': float(result[9]) if result[9] else 0,
                'local_amount': float(result[10]) if result[10] else 0,
                'amount_thb': float(result[10]) if result[10] else 0,
                'rate': float(result[11]) if result[11] else 0,
                'form_data': result[12],
                'transaction_date': result[13],
                'branch_id': result[14],
                # 签名数据
                'reporter_signature': result[15],
                'customer_signature': result[16],
                'auditor_signature': result[17]
            }

            # 确定输出路径
            if not output_dir:
                # 默认路径: amlo_pdfs/YYYY/MM/ (按年月组织，项目根目录，不是src下)
                now = datetime.now()
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                output_dir = os.path.join(project_root, 'amlo_pdfs', str(now.year), f'{now.month:02d}')

            os.makedirs(output_dir, exist_ok=True)

            # 生成文件名: AMLO-1-01_FI-001-68-001.pdf
            report_type = reservation_data['report_type']
            reservation_no = reservation_data['reservation_no'].replace('/', '-').replace('\\', '-')
            filename = f"{report_type}_{reservation_no}.pdf"
            output_path = os.path.join(output_dir, filename)

            # 生成PDF
            return self.generate_pdf_from_reservation(reservation_data, output_path)

        except Exception as e:
            print(f"[AMLOPDFService] Error generating PDF from DB: {e}")
            import traceback
            traceback.print_exc()
            raise


# 便利函数
def generate_amlo_pdf(
    reservation_id: int,
    db_session: Session,
    output_dir: Optional[str] = None
) -> str:
    """
    快捷函数: 从预约记录ID生成AMLO PDF

    Args:
        reservation_id: 预约记录ID
        db_session: 数据库会话
        output_dir: 输出目录（可选）

    Returns:
        生成的PDF文件路径
    """
    service = AMLOPDFService()
    return service.generate_pdf_from_db(db_session, reservation_id, output_dir)


# 测试代码
if __name__ == '__main__':
    service = AMLOPDFService()

    # 模拟预约数据
    test_reservation = {
        'report_type': 'AMLO-1-01',
        'reservation_no': 'FI-001-68-001',
        'customer_id': '1234567890123',
        'customer_name': 'นายสมชาย ใจดี',
        'customer_address': '123 ถนนสุขุมวิท แขวงคลองเตย เขตคลองเตย กรุงเทพมหานคร 10110',
        'direction': 'buy',
        'currency_code': 'USD',
        'local_amount': 2500000,
        'amount': 75000,
        'transaction_date': datetime(2025, 10, 18),
        'form_data': {
            'maker_phone': '02-1234567',
            'maker_occupation': 'ธุรกิจส่วนตัว',
            'maker_id_type': 'id_card',
            'transaction_purpose': 'เพื่อการท่องเที่ยว',
            'is_amendment_report': False,
        }
    }

    # 生成测试PDF
    output_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'test_output')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'amlo_101_integrated.pdf')

    print("\n" + "="*60)
    print("Testing Integrated AMLO PDF Generation")
    print("="*60)

    result_path = service.generate_pdf_from_reservation(test_reservation, output_path)

    print("\n" + "="*60)
    print(f"SUCCESS! PDF created at: {result_path}")
    print("="*60)
