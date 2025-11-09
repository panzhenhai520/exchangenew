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
    from .amlo_pdf_filler_overlay import AMLOPDFFillerOverlay  # 使用覆盖层方式
    from .amlo_data_mapper import AMLODataMapper
except ImportError:
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from amlo_csv_field_loader import get_csv_field_loader
    from amlo_pdf_filler_overlay import AMLOPDFFillerOverlay
    from amlo_data_mapper import AMLODataMapper


class AMLOPDFService:
    """AMLO PDF生成服务"""

    def __init__(self):
        """初始化服务"""
        self.csv_loader = get_csv_field_loader()
        self.pdf_filler = AMLOPDFFillerOverlay()  # 使用覆盖层方式
        self.data_mapper = AMLODataMapper()
        print("[AMLOPDFService] Initialized successfully (using Overlay method)")

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
                signatures['reporter_signature'] = reservation_data['reporter_signature']
            if reservation_data.get('customer_signature'):
                signatures['customer_signature'] = reservation_data['customer_signature']
            if reservation_data.get('auditor_signature'):
                signatures['auditor_signature'] = reservation_data['auditor_signature']

            # 2. 填充PDF表单（使用覆盖层方式，包含签名）
            result_path = self.pdf_filler.fill_form(
                report_type,
                pdf_fields,
                output_path,
                signatures=signatures if signatures else None
            )

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
                    r.customer_address,
                    r.customer_country_code,
                    r.currency_id,
                    c.code as currency_code,
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
                'customer_address': result[5],
                'customer_country_code': result[6],
                'currency_id': result[7],
                'currency_code': result[8],
                'direction': result[9],
                'amount': float(result[10]) if result[10] else 0,
                'local_amount': float(result[11]) if result[11] else 0,
                'amount_thb': float(result[11]) if result[11] else 0,
                'rate': float(result[12]) if result[12] else 0,
                'form_data': result[13],
                'transaction_date': result[14],
                'branch_id': result[15],
                # 签名数据
                'reporter_signature': result[16],
                'customer_signature': result[17],
                'auditor_signature': result[18]
            }

            # 确定输出路径
            if not output_dir:
                # 默认路径: src/amlo_reports/YYYY/MM/
                now = datetime.now()
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                output_dir = os.path.join(project_root, 'src', 'amlo_reports', str(now.year), f'{now.month:02d}')

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
