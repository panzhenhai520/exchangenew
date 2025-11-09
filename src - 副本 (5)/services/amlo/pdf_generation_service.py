# -*- coding: utf-8 -*-
"""
AMLO PDF Generation Service

Handles PDF generation for AMLO reports including:
- Data transformation for PDF templates
- Single PDF generation
- Batch PDF generation as ZIP
- Blank form serving
"""

import logging
import json
import os
import tempfile
import zipfile
from io import BytesIO
from typing import Dict, Any, Optional, Tuple
from sqlalchemy import text
from datetime import datetime

from .db_helpers import AMLODatabaseHelper

logger = logging.getLogger(__name__)


class PDFGenerationService:
    """Service layer for AMLO PDF generation"""

    # Blank form directory
    BLANK_FORMS_DIR = os.path.join('src', 'static', 'amlo_forms')

    # PDF output directory
    # 使用项目根目录的amlo_pdfs
    PDF_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'amlo_pdfs')

    @staticmethod
    def normalize_bool(value: Any) -> bool:
        """
        Normalize various value types to boolean

        Args:
            value: Value to normalize

        Returns:
            Boolean value
        """
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in ('1', 'true', 'yes', 'y', 'on')
        if isinstance(value, (int, float)):
            return value != 0
        return False

    @staticmethod
    def combine_name_fields(
        form_data: Dict[str, Any],
        prefix: str,
        fallback: str = ''
    ) -> str:
        """
        Combine name fields (title, firstname, lastname, company)

        Args:
            form_data: Form data dictionary
            prefix: Field prefix (e.g., 'maker', 'joint_party')
            fallback: Fallback value if no name found

        Returns:
            Combined name string
        """
        title = form_data.get(f'{prefix}_title') or ''
        first = form_data.get(f'{prefix}_firstname') or ''
        last = form_data.get(f'{prefix}_lastname') or ''
        company = form_data.get(f'{prefix}_company_name') or ''
        full = form_data.get(f'{prefix}_full_name') or ''

        parts = [p for p in [title, first, last] if p]
        if company:
            parts.append(company)

        candidate = full or ' '.join(parts).strip()
        return candidate or fallback

    @staticmethod
    def combine_address_fields(form_data: Dict[str, Any], prefix: str) -> str:
        """
        Combine address fields

        Args:
            form_data: Form data dictionary
            prefix: Field prefix (e.g., 'maker_address')

        Returns:
            Combined address string
        """
        order = [
            'number', 'village', 'lane', 'road',
            'subdistrict', 'district', 'province', 'postalcode'
        ]
        values = []
        for suffix in order:
            key = f'{prefix}_{suffix}'
            val = form_data.get(key)
            if val:
                values.append(str(val))
        return ' '.join(values).strip()

    @staticmethod
    def parse_date_from_components(
        form_data: Dict[str, Any],
        day_key: str,
        month_key: str,
        year_key: str
    ) -> Optional[datetime]:
        """
        Parse date from separate day/month/year fields

        Args:
            form_data: Form data dictionary
            day_key: Key for day field
            month_key: Key for month field
            year_key: Key for year field

        Returns:
            Datetime object or None
        """
        day = form_data.get(day_key)
        month = form_data.get(month_key)
        year = form_data.get(year_key)

        if not all([day, month, year]):
            return None

        try:
            day = int(day)
            month = int(month)
            year = int(year)
            if year < 100:
                year += 2000
            return datetime(year, month, day)
        except Exception:
            return None

    @staticmethod
    def build_pdf_data_payload(
        session,
        reservation_row,
        form_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build PDF data payload from reservation record

        Args:
            session: SQLAlchemy session
            reservation_row: Reservation database row
            form_data: Optional parsed form data (will parse from row if not provided)

        Returns:
            Dict with PDF data ready for template filling
        """
        try:
            # Parse form_data if not provided
            if form_data is None:
                form_data_raw = reservation_row[11] if len(reservation_row) > 11 else None
                form_data = AMLODatabaseHelper.parse_form_data(form_data_raw)

            # Extract basic fields
            reservation_id = reservation_row[0]
            reservation_no = reservation_row[1]
            direction = (reservation_row[3] or '').lower()
            customer_name = reservation_row[5] or ''
            customer_id = reservation_row[6] or ''
            customer_address = reservation_row[7] or ''
            branch_id = reservation_row[8]
            amount = reservation_row[10]

            # Combine name fields
            maker_name = PDFGenerationService.combine_name_fields(form_data, 'maker', customer_name)
            joint_party_name = PDFGenerationService.combine_name_fields(
                form_data, 'joint_party', form_data.get('joint_party_name', '')
            )

            # Combine address fields
            maker_address = PDFGenerationService.combine_address_fields(form_data, 'maker_address') or customer_address
            joint_party_address = (
                form_data.get('joint_party_address') or
                PDFGenerationService.combine_address_fields(form_data, 'joint_party_address')
            )

            # Extract other fields
            maker_phone = form_data.get('maker_phone') or form_data.get('maker_mobile') or ''
            maker_occupation = form_data.get('maker_occupation_type') or form_data.get('maker_occupation') or ''
            maker_employer = form_data.get('maker_occupation_employer') or ''
            beneficiary_name = joint_party_name or form_data.get('beneficiary_name', '')

            # Transaction type and amounts
            transaction_type = 'buy' if direction == 'buy' else 'sell'
            foreign_amount = float(form_data.get('total_amount') or amount or 0)
            amount_thb = float(form_data.get('amount_thb') or reservation_row[10] or 0)

            # Dates
            form_transaction_date = PDFGenerationService.parse_date_from_components(
                form_data, 'transaction_date_day', 'transaction_date_month', 'transaction_date_year'
            )
            transaction_date = form_transaction_date

            form_report_date = PDFGenerationService.parse_date_from_components(
                form_data, 'report_date_day', 'report_date_month', 'report_date_year'
            )
            report_date_str = (form_report_date or datetime.now()).strftime('%d/%m/%Y')

            # Get branch codes
            institution_code, branch_code = PDFGenerationService._get_branch_codes(session, branch_id)

            # Build PDF data
            pdf_data = {
                'report_number': reservation_no,
                'is_amendment': PDFGenerationService.normalize_bool(form_data.get('is_amendment_report')),
                'maker_type': 'juristic' if PDFGenerationService.normalize_bool(form_data.get('maker_type_juristic')) else 'person',
                'maker_name': maker_name,
                'maker_id': form_data.get('maker_id_number') or customer_id,
                'maker_address': maker_address,
                'maker_phone': maker_phone,
                'maker_occupation': maker_occupation or maker_employer,
                'joint_party_name': joint_party_name,
                'joint_party_address': joint_party_address or '',
                'transaction_date': (transaction_date.strftime('%d/%m/%Y') if transaction_date else ''),
                'transaction_type': transaction_type,
                'currency_code': form_data.get('currency_code') or form_data.get('foreign_currency_code') or '',
                'foreign_amount': foreign_amount,
                'amount_thb': amount_thb,
                'remarks': form_data.get('remarks', ''),
                'transaction_purpose': form_data.get('transaction_purpose') or form_data.get('exchange_other_transaction') or '',
                'beneficiary_name': beneficiary_name or form_data.get('joint_party_name', ''),
                'reporter_name': form_data.get('reporter_name', ''),
                'reporter_position': form_data.get('reporter_position', ''),
                'report_date': report_date_str,
                'institution_code': institution_code,
                'branch_code': branch_code,
                'form_data': form_data
            }

            logger.info(f"[PDFGenerationService] Built PDF data for reservation {reservation_id}")
            return pdf_data

        except Exception as e:
            logger.error(f"[PDFGenerationService] Error building PDF data: {e}", exc_info=True)
            return {}

    @staticmethod
    def _get_branch_codes(session, branch_id: int) -> Tuple[str, str]:
        """
        Get institution and branch codes

        Args:
            session: SQLAlchemy session
            branch_id: Branch ID

        Returns:
            Tuple of (institution_code, branch_code)
        """
        try:
            # Try to get codes from ReportNumberGenerator
            from services.report_number_generator import ReportNumberGenerator
            branch_codes = ReportNumberGenerator.get_branch_codes(session, branch_id)
            institution_code = branch_codes['institution_code']
            branch_code = branch_codes['branch_code']
        except Exception as e:
            logger.warning(f"[PDFGenerationService] Failed to get branch codes: {e}")
            # Fallback to default
            institution_code = '001'
            branch_code = '001'

        return institution_code, branch_code

    @staticmethod
    def generate_single_pdf(
        session,
        reservation_id: int,
        output_dir: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Generate single AMLO PDF report

        Args:
            session: SQLAlchemy session
            reservation_id: Reservation ID
            output_dir: Optional output directory (defaults to PDF_OUTPUT_DIR/YYYY/MM/)

        Returns:
            Tuple of (success, pdf_path, error_message)
        """
        try:
            # Import PDF service
            from services.pdf.amlo_pdf_service import AMLOPDFService
            from datetime import datetime

            # Use output directory with year/month subdirectories
            if output_dir is None:
                # Create year/month subdirectory structure: amlo_pdfs/YYYY/MM/
                now = datetime.now()
                year_month_dir = os.path.join(
                    PDFGenerationService.PDF_OUTPUT_DIR,
                    str(now.year),
                    f"{now.month:02d}"
                )
                output_dir = year_month_dir

            # Ensure directory exists
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"[PDFGenerationService] Output directory: {output_dir}")

            # Generate PDF using AMLOPDFService
            pdf_service = AMLOPDFService()
            pdf_path = pdf_service.generate_pdf_from_db(
                session,
                reservation_id,
                output_dir=output_dir
            )

            if not pdf_path or not os.path.exists(pdf_path):
                return False, None, "PDF generation failed"

            logger.info(f"[PDFGenerationService] Generated PDF for reservation {reservation_id}: {pdf_path}")
            return True, pdf_path, None

        except Exception as e:
            logger.error(f"[PDFGenerationService] Error generating PDF for reservation {reservation_id}: {e}", exc_info=True)
            return False, None, f"Failed to generate PDF: {str(e)}"

    @staticmethod
    def generate_pdf_batch_as_zip(
        session,
        report_ids: list,
        branch_id: int
    ) -> Tuple[bool, Optional[BytesIO], Optional[str]]:
        """
        Generate multiple PDFs and return as ZIP archive

        Args:
            session: SQLAlchemy session
            report_ids: List of report IDs
            branch_id: Branch ID for filtering

        Returns:
            Tuple of (success, zip_buffer, error_message)
        """
        try:
            from services.pdf.amlo_pdf_filler_overlay import AMLOPDFFillerOverlay

            if not report_ids:
                return False, None, "No report IDs provided"

            # Create ZIP buffer
            zip_buffer = BytesIO()
            zip_file = zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED)

            pdf_filler = AMLOPDFFillerOverlay()
            generated_count = 0

            for report_id in report_ids:
                try:
                    # Query reservation data
                    sql = text("""
                        SELECT
                            r.id, r.reservation_no, r.report_type, r.direction, r.status,
                            r.customer_name, r.customer_id, r.customer_address,
                            r.branch_id, r.currency_id, r.amount,
                            r.form_data, r.created_at, r.updated_at
                        FROM Reserved_Transaction r
                        WHERE r.id = :report_id AND r.branch_id = :branch_id
                    """)

                    result = session.execute(sql, {
                        'report_id': report_id,
                        'branch_id': branch_id
                    }).fetchone()

                    if not result:
                        logger.warning(f"[PDFGenerationService] Report {report_id} not found")
                        continue

                    # Build PDF data
                    pdf_data = PDFGenerationService.build_pdf_data_payload(session, result)

                    # Get report type
                    report_type = result[2]  # report_type field

                    # Generate PDF to temp file
                    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                        temp_path = tmp_file.name

                    try:
                        # Use PDF filler to generate
                        output_path = pdf_filler.fill_form(
                            report_type,
                            pdf_data,
                            temp_path
                        )

                        if output_path and os.path.exists(output_path):
                            # Add to ZIP
                            filename = f"{result[1]}_{report_type}.pdf"  # reservation_no + report_type
                            with open(output_path, 'rb') as pdf_file:
                                zip_file.writestr(filename, pdf_file.read())
                            generated_count += 1
                            logger.info(f"[PDFGenerationService] Added {filename} to ZIP")

                    finally:
                        # Clean up temp file
                        if os.path.exists(temp_path):
                            try:
                                os.unlink(temp_path)
                            except Exception:
                                pass

                except Exception as pdf_error:
                    logger.error(f"[PDFGenerationService] Error generating PDF for report {report_id}: {pdf_error}")
                    continue

            zip_file.close()

            if generated_count == 0:
                return False, None, "No PDFs were generated"

            zip_buffer.seek(0)
            logger.info(f"[PDFGenerationService] Generated ZIP with {generated_count} PDFs")
            return True, zip_buffer, None

        except Exception as e:
            logger.error(f"[PDFGenerationService] Error generating batch PDFs: {e}", exc_info=True)
            return False, None, f"Failed to generate batch PDFs: {str(e)}"

    @staticmethod
    def get_blank_form_path(report_type: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Get file path for blank AMLO form

        Args:
            report_type: Report type (AMLO-1-01, AMLO-1-02, AMLO-1-03)

        Returns:
            Tuple of (success, file_path, error_message)
        """
        try:
            # Validate report type
            valid_types = ['AMLO-1-01', 'AMLO-1-02', 'AMLO-1-03']
            if report_type not in valid_types:
                return False, None, f"Invalid report type: {report_type}"

            # Build file path
            filename = f"{report_type}.pdf"
            file_path = os.path.join(PDFGenerationService.BLANK_FORMS_DIR, filename)

            # Check if file exists
            if not os.path.exists(file_path):
                return False, None, f"Blank form not found: {file_path}"

            return True, file_path, None

        except Exception as e:
            logger.error(f"[PDFGenerationService] Error getting blank form path: {e}", exc_info=True)
            return False, None, f"Failed to get blank form: {str(e)}"
