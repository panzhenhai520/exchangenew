# -*- coding: utf-8 -*-
"""
AMLO Report Creation Service

Handles automatic creation of AMLO reports and PDF generation
when a reservation is submitted.
"""

import logging
import os
from typing import Dict, Any
from sqlalchemy import text
from datetime import datetime

logger = logging.getLogger(__name__)


class ReportCreationService:
    """Service for creating AMLO reports from reservations"""

    @staticmethod
    def create_report_for_reservation(
        session,
        reservation_id: int
    ) -> Dict[str, Any]:
        """
        Create AMLO report and generate PDF for a reservation

        Args:
            session: SQLAlchemy session
            reservation_id: Reservation ID

        Returns:
            Dict with success, report_id, report_no, pdf_path, error
        """
        try:
            # 1. 查询预约信息
            reservation = session.execute(text("""
                SELECT
                    id, reservation_no, report_type, customer_name, customer_id,
                    branch_id, currency_id, amount, local_amount, operator_id
                FROM Reserved_Transaction
                WHERE id = :reservation_id
            """), {'reservation_id': reservation_id}).fetchone()

            if not reservation:
                return {
                    'success': False,
                    'error': f'Reservation {reservation_id} not found'
                }

            # 2. 生成报告编号
            report_no = ReportCreationService._generate_report_number(
                session,
                reservation[2],  # report_type
                reservation[5]   # branch_id
            )

            # 3. 确定报告格式
            report_format = reservation[2]  # report_type即report_format (AMLO-1-01)
            if report_format not in ('AMLO-1-01', 'AMLO-1-02', 'AMLO-1-03'):
                report_format = 'AMLO-1-01'

            # 4. 插入AMLOReport记录
            insert_sql = text("""
                INSERT INTO AMLOReport (
                    reserved_id, report_no, report_type, report_format,
                    customer_name, customer_id,
                    branch_id, transaction_amount, transaction_date,
                    pdf_filename, pdf_path,
                    is_reported, operator_id, created_at
                ) VALUES (
                    :reserved_id, :report_no, :report_type, :report_format,
                    :customer_name, :customer_id,
                    :branch_id, :transaction_amount, NOW(),
                    :pdf_filename, :pdf_path,
                    0, :operator_id, NOW()
                )
            """)

            pdf_filename = f'{report_no}.pdf'
            pdf_path = f'amlo_pdfs/{pdf_filename}'

            result = session.execute(insert_sql, {
                'reserved_id': reservation_id,
                'report_no': report_no,
                'report_type': 'CTR',  # Default type
                'report_format': report_format,
                'customer_name': reservation[3],
                'customer_id': reservation[4],
                'branch_id': reservation[5],
                'transaction_amount': reservation[8] or reservation[7],  # local_amount or amount
                'pdf_filename': pdf_filename,
                'pdf_path': pdf_path,
                'operator_id': reservation[9]
            })

            report_id = result.lastrowid
            session.commit()

            logger.info(f"[ReportCreationService] Created report {report_no} (ID: {report_id}) for reservation {reservation_id}")

            # 5. 生成PDF
            try:
                pdf_result = ReportCreationService._generate_pdf(
                    session, reservation_id, report_no
                )
                if pdf_result['success']:
                    logger.info(f"[ReportCreationService] Generated PDF: {pdf_result['pdf_path']}")
                else:
                    logger.warning(f"[ReportCreationService] PDF generation failed: {pdf_result.get('error')}")
            except Exception as pdf_error:
                logger.error(f"[ReportCreationService] PDF generation exception: {pdf_error}", exc_info=True)
                pdf_result = {'success': False, 'error': str(pdf_error)}

            return {
                'success': True,
                'report_id': report_id,
                'report_no': report_no,
                'pdf_path': pdf_result.get('pdf_path') if pdf_result['success'] else None,
                'pdf_generated': pdf_result['success']
            }

        except Exception as e:
            session.rollback()
            logger.error(f"[ReportCreationService] Error creating report for reservation {reservation_id}: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Failed to create report: {str(e)}'
            }

    @staticmethod
    def _generate_report_number(session, report_type: str, branch_id: int) -> str:
        """
        Generate unique report number

        Format: AMLO-1-01_BranchCode-XXXXXX

        Args:
            session: SQLAlchemy session
            report_type: Report type (e.g., AMLO-1-01)
            branch_id: Branch ID

        Returns:
            Report number string
        """
        try:
            # Get branch code
            branch_sql = text("SELECT branch_code FROM branches WHERE id = :branch_id")
            branch_result = session.execute(branch_sql, {'branch_id': branch_id}).fetchone()
            branch_code = branch_result[0] if branch_result else '000'

            # Get next sequence number for this report type and branch
            count_sql = text("""
                SELECT COUNT(*)
                FROM AMLOReport
                WHERE report_format = :report_type
                  AND branch_id = :branch_id
                  AND YEAR(created_at) = YEAR(NOW())
            """)
            count = session.execute(count_sql, {
                'report_type': report_type,
                'branch_id': branch_id
            }).scalar() or 0

            sequence = count + 1
            report_no = f"{report_type}_{branch_code}-{sequence:06d}"

            logger.info(f"[ReportCreationService] Generated report number: {report_no}")
            return report_no

        except Exception as e:
            logger.error(f"[ReportCreationService] Error generating report number: {e}", exc_info=True)
            # Fallback
            return f"{report_type}_000-000001"

    @staticmethod
    def _generate_pdf(session, reservation_id: int, report_no: str) -> Dict[str, Any]:
        """
        Generate PDF for reservation using existing PDF service

        Args:
            session: SQLAlchemy session
            reservation_id: Reservation ID
            report_no: Report number for filename

        Returns:
            Dict with success, pdf_path, error
        """
        try:
            # 1. 查询预约完整数据
            reservation_sql = text("""
                SELECT
                    r.id, r.reservation_no, r.report_type, r.customer_id, r.customer_name,
                    r.direction, r.amount, r.local_amount, r.rate, r.form_data,
                    r.created_at, c.currency_code
                FROM Reserved_Transaction r
                LEFT JOIN currencies c ON r.currency_id = c.id
                WHERE r.id = :reservation_id
            """)

            result = session.execute(reservation_sql, {'reservation_id': reservation_id}).fetchone()
            if not result:
                return {'success': False, 'error': 'Reservation not found'}

            # 2. 准备预约数据
            import json
            form_data = result[9]
            if isinstance(form_data, str):
                try:
                    form_data = json.loads(form_data)
                except:
                    form_data = {}

            reservation_data = {
                'report_type': result[2],
                'reservation_no': result[1],
                'customer_id': result[3],
                'customer_name': result[4],
                'direction': result[5],
                'amount': float(result[6]) if result[6] else 0,
                'local_amount': float(result[7]) if result[7] else 0,
                'rate': float(result[8]) if result[8] else 0,
                'currency_code': result[11] or 'USD',
                'transaction_date': result[10].strftime('%Y-%m-%d') if result[10] else '',
                'form_data': form_data
            }

            # 3. 准备输出路径
            output_dir = 'amlo_pdfs'
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f'{report_no}.pdf')

            # 4. 生成PDF (保持原有格式)
            from services.pdf.amlo_pdf_service import AMLOPDFService

            pdf_service = AMLOPDFService()
            pdf_path = pdf_service.generate_pdf_from_reservation(
                reservation_data,
                output_path
            )

            if pdf_path and os.path.exists(pdf_path):
                return {
                    'success': True,
                    'pdf_path': pdf_path
                }
            else:
                return {
                    'success': False,
                    'error': 'PDF file not generated'
                }

        except Exception as e:
            logger.error(f"[ReportCreationService] PDF generation error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
