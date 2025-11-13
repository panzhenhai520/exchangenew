# -*- coding: utf-8 -*-
"""
AMLO API Routes (Refactored)

Thin route handlers that delegate to service layer.
All business logic has been moved to services/amlo/ modules.

Version: v2.0
Created: 2025-10-02
Refactored: 2025-11-03
"""

from flask import Blueprint, request, jsonify, g, send_file
from functools import wraps
from services.db_service import SessionLocal
from services.auth_service import token_required
from datetime import datetime
import traceback
import logging
import os
import json
from io import BytesIO
from sqlalchemy import text

# Import AMLO services
from services.amlo import (
    ReservationService,
    AuditService,
    ReportService,
    PDFGenerationService,
    SignatureService
)

# PDF helpers
from services.pdf.amlo_data_mapper import AMLODataMapper
from services.pdf.pdf_field_mapping import map_pdf_fields_to_db

# Get logger instance
logger = logging.getLogger(__name__)

# Create Blueprint
app_amlo = Blueprint('app_amlo', __name__, url_prefix='/api/amlo')

# Paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AMLO_TEMPLATE_DIR = os.path.join(PROJECT_ROOT, 'Re')
AMLO_UPLOAD_BASE_DIR = os.path.join(PROJECT_ROOT, 'src', 'amlo_uploads')


def amlo_permission_required(permission):
    """
    Permission decorator for AMLO routes
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Permission checking logic can be added here
            # For now, just pass through
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def _ensure_directory(path: str):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def _resolve_project_path(relative_path: str):
    return os.path.normpath(os.path.join(PROJECT_ROOT, relative_path))


def _load_form_data(raw):
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw.copy()
    try:
        return json.loads(raw)
    except Exception:
        return {}


def _sanitize_filename(value: str, fallback: str) -> str:
    if not value:
        return fallback
    value = value.strip().replace(' ', '_')
    allowed = []
    for ch in value:
        if ch.isalnum() or ch in ('-', '_', '.'):
            allowed.append(ch)
    safe = ''.join(allowed)
    return safe or fallback


def _extract_pdf_form_fields(pdf_path: str):
    import fitz  # PyMuPDF

    field_values = {}
    doc = fitz.open(pdf_path)
    try:
        for page in doc:
            widgets = page.widgets() or []
            for widget in widgets:
                name = widget.field_name
                if not name:
                    continue
                value = widget.field_value
                field_type = widget.field_type
                if field_type == fitz.PDF_WIDGET_TYPE_CHECKBOX:
                    if isinstance(value, str):
                        normalized = value.lower() in ('yes', 'on', 'true', '1')
                    else:
                        normalized = bool(value)
                else:
                    normalized = '' if value is None else str(value)
                field_values[name] = normalized
    finally:
        doc.close()
    return field_values


def _fill_pdf_form_fields(doc, form_data):
    import fitz  # PyMuPDF

    filled_count = 0
    for page in doc:
        for widget in page.widgets():
            field_name = widget.field_name
            if not field_name or field_name not in form_data:
                continue
            value = form_data[field_name]
            field_type = widget.field_type
            try:
                if field_type == fitz.PDF_WIDGET_TYPE_TEXT:
                    widget.field_value = '' if value is None else str(value)
                    widget.update()
                    filled_count += 1
                elif field_type == fitz.PDF_WIDGET_TYPE_CHECKBOX:
                    if isinstance(value, bool):
                        widget.field_value = value
                    elif isinstance(value, str):
                        widget.field_value = value.lower() in ('true', 'yes', '1', 'on')
                    else:
                        widget.field_value = bool(value)
                    widget.update()
                    filled_count += 1
                elif field_type == fitz.PDF_WIDGET_TYPE_COMBOBOX:
                    widget.field_value = '' if value is None else str(value)
                    widget.update()
                    filled_count += 1
                else:
                    # Fall back to string value
                    widget.field_value = '' if value is None else str(value)
                    widget.update()
                    filled_count += 1
            except Exception as widget_error:
                logger.warning(f"[fill_pdf_form_fields] Failed field {field_name}: {widget_error}")
    return filled_count


# ==============================================================================
# RESERVATION MANAGEMENT ROUTES
# ==============================================================================

@app_amlo.route('/check-customer-reservation', methods=['GET'])
@token_required
def check_customer_reservation(current_user):
    """
    Check if customer has existing AMLO reservation
    """
    session = SessionLocal()
    try:
        customer_id = request.args.get('customer_id')
        if not customer_id:
            return jsonify({'success': False, 'message': 'Customer ID required'}), 400

        branch_id = g.current_user.get('branch_id')
        if not branch_id:
            return jsonify({'success': False, 'message': 'Branch ID not found'}), 400

        # Use service
        has_reservation, reservation_data = ReservationService.check_customer_has_reservation(
            session, customer_id, branch_id
        )

        if has_reservation:
            return jsonify({
                'success': True,
                'has_reservation': True,
                'reservation': reservation_data
            })
        else:
            return jsonify({
                'success': True,
                'has_reservation': False
            })

    except Exception as e:
        logger.error(f"[check_customer_reservation] Error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Failed to check reservation: {str(e)}'
        }), 500
    finally:
        session.close()


@app_amlo.route('/reservations', methods=['GET'])
@token_required
# @amlo_permission_required('amlo_reservation_view')
def get_reservations(current_user):
    """
    List AMLO reservations with pagination and filtering
    """
    session = SessionLocal()
    try:
        # 检查用户是否为管理员，管理员可以查看所有分支的预约
        is_admin = g.current_user.get('is_admin', False)
        branch_id = g.current_user.get('branch_id')

        if not branch_id and not is_admin:
            return jsonify({'success': False, 'message': 'Branch ID not found'}), 400

        # Extract filters from query params
        filters = {
            'status': request.args.get('status'),
            'customer_id': request.args.get('customer_id'),
            'report_type': request.args.get('report_type'),
            'start_date': request.args.get('start_date'),
            'end_date': request.args.get('end_date')
        }

        # Pagination
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))

        # 管理员查看所有分支，普通用户只查看自己的分支
        query_branch_id = None if is_admin else branch_id

        # Use service
        result = ReservationService.list_reservations(
            session, query_branch_id, filters, page, page_size
        )

        return jsonify(result)

    except Exception as e:
        logger.error(f"[get_reservations] Error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Failed to list reservations: {str(e)}'
        }), 500
    finally:
        session.close()


@app_amlo.route('/reservations/<int:reservation_id>', methods=['GET'])
@token_required
def get_reservation_detail(current_user, reservation_id):
    """
    Get detailed reservation information
    """
    session = SessionLocal()
    try:
        branch_id = g.current_user.get('branch_id')

        # Use service (optional branch filtering)
        success, reservation_data, error = ReservationService.get_reservation_by_id(
            session, reservation_id, branch_id
        )

        if not success:
            return jsonify({'success': False, 'message': error}), 404

        return jsonify({
            'success': True,
            'data': reservation_data
        })

    except Exception as e:
        logger.error(f"[get_reservation_detail] Error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Failed to get reservation: {str(e)}'
        }), 500
    finally:
        session.close()


@app_amlo.route('/reservations/<int:reservation_id>', methods=['PUT'])
@token_required
def update_reservation(current_user, reservation_id):
    """
    Update reservation form data and denomination data
    """
    session = SessionLocal()
    try:
        request_data = request.get_json() or {}
        form_data = request_data.get('form_data')
        denomination_data = request_data.get('denomination_data')

        if not form_data:
            return jsonify({'success': False, 'message': 'Form data required'}), 400

        user_id = g.current_user.get('id')

        # Use service
        success, error = ReservationService.update_reservation_form_data(
            session, reservation_id, form_data, user_id, denomination_data
        )

        if not success:
            return jsonify({'success': False, 'message': error}), 400

        return jsonify({
            'success': True,
            'message': 'Reservation updated successfully'
        })

    except Exception as e:
        logger.error(f"[update_reservation] Error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Failed to update reservation: {str(e)}'
        }), 500
    finally:
        session.close()


@app_amlo.route('/reservations', methods=['POST'])
@token_required
def create_reservation(current_user):
    """
    Create new AMLO reservation
    """
    session = SessionLocal()
    try:
        request_data = request.get_json() or {}

        # Extract required fields
        report_type = request_data.get('report_type')
        form_data = request_data.get('form_data', {})

        if not report_type:
            return jsonify({'success': False, 'message': 'Report type required'}), 400

        # Extract transaction data
        customer_id = request_data.get('customer_id', '')
        customer_name = request_data.get('customer_name', '')
        customer_country_code = request_data.get('customer_country_code', '')
        direction = request_data.get('direction', '')
        currency_id = request_data.get('currency_id')
        currency_code = request_data.get('currency_code', 'USD')
        amount = request_data.get('amount', 0)
        local_amount = request_data.get('local_amount', 0)
        rate = request_data.get('rate', 0)
        transaction_id = request_data.get('transaction_id')

        # Get user and branch info
        branch_id = g.current_user.get('branch_id')
        user_id = g.current_user.get('id')

        if not branch_id:
            return jsonify({'success': False, 'message': 'Branch ID not found'}), 400

        # Use reservation service to create reservation
        success, reservation_data, error = ReservationService.create_reservation(
            session=session,
            report_type=report_type,
            customer_id=customer_id,
            customer_name=customer_name,
            customer_country_code=customer_country_code,
            direction=direction,
            currency_id=currency_id,
            currency_code=currency_code,
            amount=amount,
            local_amount=local_amount,
            rate=rate,
            branch_id=branch_id,
            user_id=user_id,
            transaction_id=transaction_id,
            form_data=form_data
        )

        if not success:
            return jsonify({'success': False, 'message': error}), 400

        # Generate PDF automatically
        from services.amlo.pdf_generation_service import PDFGenerationService
        pdf_success, pdf_path, pdf_error = PDFGenerationService.generate_single_pdf(
            session,
            reservation_data['id']
        )

        if pdf_success and pdf_path:
            reservation_data['pdf_path'] = pdf_path
            logger.info(f"[create_reservation] PDF generated: {pdf_path}")
        else:
            logger.warning(f"[create_reservation] PDF generation failed: {pdf_error}")

        return jsonify({
            'success': True,
            'message': 'Reservation created successfully',
            'data': reservation_data
        })

    except Exception as e:
        logger.error(f"[create_reservation] Error: {e}", exc_info=True)
        session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to create reservation: {str(e)}'
        }), 500
    finally:
        session.close()


@app_amlo.route('/reservations/<int:reservation_id>/resubmit', methods=['POST'])
@token_required
def resubmit_reservation(current_user, reservation_id):
    """
    Resubmit a rejected or completed reservation with updated data
    """
    session = SessionLocal()
    try:
        request_data = request.get_json() or {}
        form_data = request_data.get('form_data')
        denomination_data = request_data.get('denomination_data')
        previous_report_number = request_data.get('previous_report_number')
        remarks = request_data.get('remarks')

        if not form_data:
            return jsonify({'success': False, 'message': 'Form data required'}), 400

        user_id = g.current_user.get('id')

        # Use service
        success, updated_reservation, error = ReservationService.resubmit_reservation(
            session, reservation_id, form_data, denomination_data,
            previous_report_number, remarks, user_id
        )

        if not success:
            return jsonify({'success': False, 'message': error}), 400

        return jsonify({
            'success': True,
            'message': 'Reservation resubmitted successfully',
            'data': updated_reservation
        })

    except Exception as e:
        logger.error(f"[resubmit_reservation] Error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Failed to resubmit reservation: {str(e)}'
        }), 500
    finally:
        session.close()


@app_amlo.route('/reservations/<int:reservation_id>/complete', methods=['POST'])
@token_required
def complete_reservation(current_user, reservation_id):
    """
    Mark reservation as completed after transaction
    """
    session = SessionLocal()
    try:
        request_data = request.get_json() or {}
        transaction_id = request_data.get('transaction_id') or request_data.get('linked_transaction_id')
        actual_amount = request_data.get('actual_amount')
        user_id = g.current_user.get('id')

        # Use service
        success, error = ReservationService.complete_reservation(
            session, reservation_id, transaction_id, actual_amount, user_id
        )

        if not success:
            return jsonify({'success': False, 'message': error}), 400

        return jsonify({
            'success': True,
            'message': 'Reservation completed successfully'
        })

    except Exception as e:
        logger.error(f"[complete_reservation] Error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Failed to complete reservation: {str(e)}'
        }), 500
    finally:
        session.close()


# ==============================================================================
# AUDIT ROUTES
# ==============================================================================

@app_amlo.route('/reservations/<int:reservation_id>/audit', methods=['POST'])
@token_required
@amlo_permission_required('amlo_reservation_audit')
def audit_reservation(current_user, reservation_id):
    """
    Audit a reservation (approve or reject)
    """
    session = SessionLocal()
    try:
        request_data = request.get_json() or {}
        action = request_data.get('action')
        rejection_reason = request_data.get('rejection_reason')
        remarks = request_data.get('remarks')

        if not action:
            return jsonify({'success': False, 'message': 'Action required'}), 400

        auditor_id = g.current_user.get('id')

        # Use service
        success, result_data, error = AuditService.audit_reservation(
            session, reservation_id, action, auditor_id, rejection_reason, remarks
        )

        if not success:
            return jsonify({'success': False, 'message': error}), 400

        return jsonify({
            'success': True,
            'message': f'Reservation {action}d successfully',
            'data': result_data
        })

    except Exception as e:
        logger.error(f"[audit_reservation] Error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Failed to audit reservation: {str(e)}'
        }), 500
    finally:
        session.close()


@app_amlo.route('/reservations/<int:reservation_id>/reverse-audit', methods=['POST'])
@token_required
@amlo_permission_required('amlo_reservation_audit')
def reverse_audit(current_user, reservation_id):
    """
    Reverse audit (revert to pending status)
    """
    session = SessionLocal()
    try:
        request_data = request.get_json() or {}
        remarks = request_data.get('remarks')
        auditor_id = g.current_user.get('id')

        # Use service
        success, error = AuditService.reverse_audit(
            session, reservation_id, auditor_id, remarks
        )

        if not success:
            return jsonify({'success': False, 'message': error}), 400

        return jsonify({
            'success': True,
            'message': 'Audit reversed successfully'
        })

    except Exception as e:
        logger.error(f"[reverse_audit] Error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Failed to reverse audit: {str(e)}'
        }), 500
    finally:
        session.close()


@app_amlo.route('/reservations/<int:reservation_id>/submit-and-generate-pdf', methods=['POST'])
@token_required
@amlo_permission_required('amlo_reservation_view')
def submit_and_generate_pdf(current_user, reservation_id):
    """
    Submit reservation (auto-approve) and immediately generate PDF

    This is a convenience endpoint for the "Print CTR" button on pending reservations.
    It will:
    1. Auto-approve the pending reservation
    2. Create the AMLO report
    3. Generate and return the PDF
    """
    session = SessionLocal()
    try:
        auditor_id = g.current_user.get('id')

        logger.info(f"[submit_and_generate_pdf] Processing reservation {reservation_id}")

        # Step 1: Auto-approve the reservation
        success, result_data, error = AuditService.audit_reservation(
            session=session,
            reservation_id=reservation_id,
            action='approve',
            auditor_id=auditor_id,
            rejection_reason=None,
            remarks='自动批准用于PDF生成'  # Auto-approved for PDF generation
        )

        if not success:
            logger.error(f"[submit_and_generate_pdf] Audit failed: {error}")
            return jsonify({
                'success': False,
                'message': f'提交预约失败: {error}'
            }), 400

        # Step 2: Get the created report ID
        report_id = result_data.get('amlo_report_id')

        if not report_id:
            logger.error(f"[submit_and_generate_pdf] No report ID returned from audit")
            return jsonify({
                'success': False,
                'message': '报告创建失败，无法生成PDF'
            }), 500

        logger.info(f"[submit_and_generate_pdf] Report created: {report_id}, generating PDF...")

        # Step 3: Generate PDF
        success, pdf_path, error = PDFGenerationService.generate_single_pdf(
            session, report_id
        )

        if not success:
            logger.error(f"[submit_and_generate_pdf] PDF generation failed: {error}")
            return jsonify({
                'success': False,
                'message': f'PDF生成失败: {error}'
            }), 404

        # Step 4: Return PDF file
        logger.info(f"[submit_and_generate_pdf] Success! Returning PDF: {pdf_path}")

        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=os.path.basename(pdf_path)
        )

    except Exception as e:
        session.rollback()
        logger.error(f"[submit_and_generate_pdf] Unexpected error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'处理失败: {str(e)}'
        }), 500
    finally:
        session.close()


# ==============================================================================
# REPORT MANAGEMENT ROUTES
# ==============================================================================

@app_amlo.route('/reports', methods=['GET'])
@token_required
@amlo_permission_required('amlo_report_view')
def get_amlo_reports(current_user):
    """
    List AMLO reports with pagination and filtering
    """
    session = SessionLocal()
    try:
        branch_id = g.current_user.get('branch_id')
        if not branch_id:
            return jsonify({'success': False, 'message': 'Branch ID not found'}), 400

        # Extract filters
        filters = {
            'is_reported': request.args.get('is_reported'),
            'report_type': request.args.get('report_type'),
            'customer_id': request.args.get('customer_id'),
            'reservation_id': request.args.get('reservation_id'),
            'start_date': request.args.get('start_date'),
            'end_date': request.args.get('end_date')
        }

        # Convert is_reported to boolean if provided
        if filters['is_reported'] is not None:
            filters['is_reported'] = filters['is_reported'].lower() in ('true', '1', 'yes')

        # Pagination
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))

        # Use service
        result = ReportService.list_reports(
            session, branch_id, filters, page, page_size
        )

        return jsonify(result)

    except Exception as e:
        logger.error(f"[get_amlo_reports] Error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Failed to list reports: {str(e)}'
        }), 500
    finally:
        session.close()


@app_amlo.route('/reports/mark-reported', methods=['POST'])
@token_required
def mark_amlo_reported(current_user):
    """
    Mark reports as submitted to AMLO
    """
    session = SessionLocal()
    try:
        request_data = request.get_json() or {}
        report_ids = request_data.get('ids') or request_data.get('report_ids')

        if not report_ids:
            return jsonify({'success': False, 'message': 'Report IDs required'}), 400

        reporter_id = g.current_user.get('id')

        # Use service
        success, result_data, error = ReportService.mark_reports_as_submitted(
            session, report_ids, reporter_id
        )

        if not success:
            return jsonify({'success': False, 'message': error}), 400

        return jsonify({
            'success': True,
            'message': f'{len(report_ids)} reports marked as submitted',
            'data': result_data
        })

    except Exception as e:
        logger.error(f"[mark_amlo_reported] Error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Failed to mark reports: {str(e)}'
        }), 500
    finally:
        session.close()


@app_amlo.route('/reports/batch-report', methods=['POST'])
@token_required
@amlo_permission_required('amlo_report_submit')
def batch_report(current_user):
    """
    Batch submit multiple reports (with validation)
    """
    session = SessionLocal()
    try:
        request_data = request.get_json() or {}
        report_ids = request_data.get('report_ids')

        if not report_ids:
            return jsonify({'success': False, 'message': 'Report IDs required'}), 400

        reporter_id = g.current_user.get('id')

        # Use service (with validation)
        success, result_data, error = ReportService.batch_submit_reports(
            session, report_ids, reporter_id
        )

        if not success:
            return jsonify({'success': False, 'message': error}), 400

        return jsonify({
            'success': True,
            'message': 'Reports submitted successfully',
            'data': result_data
        })

    except Exception as e:
        logger.error(f"[batch_report] Error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Failed to batch submit: {str(e)}'
        }), 500
    finally:
        session.close()


# ==============================================================================
# PDF EDITING & UPLOAD ROUTES
# ==============================================================================

@app_amlo.route('/reservations/<int:reservation_id>/editable-pdf', methods=['GET'])
@token_required
def get_editable_pdf(current_user, reservation_id):
    """
    Return editable PDF with AcroForm fields pre-filled using reservation data.
    """
    session = SessionLocal()
    try:
        reservation = session.execute(
            text("""
                SELECT
                    rt.id,
                    rt.report_type,
                    rt.reservation_no,
                    rt.customer_id,
                    rt.customer_name,
                    rt.amount,
                    rt.local_amount,
                    rt.form_data,
                    ar.report_no
                FROM Reserved_Transaction rt
                LEFT JOIN AMLOReport ar ON rt.id = ar.reserved_id
                WHERE rt.id = :id
            """),
            {'id': reservation_id}
        ).fetchone()

        if not reservation:
            return jsonify({'success': False, 'message': 'Reservation not found'}), 404

        form_data = _load_form_data(reservation.form_data)
        reservation_no = reservation.reservation_no or ''
        report_no = reservation.report_no or ''

        mapper = AMLODataMapper()
        reservation_dict = {
            'report_type': reservation.report_type,
            'reservation_no': reservation_no,
            'customer_name': reservation.customer_name,
            'customer_id': reservation.customer_id,
            'amount': reservation.amount,
            'local_amount': reservation.local_amount,
            'form_data': form_data
        }

        pdf_fields = mapper.map_reservation_to_pdf_fields(
            reservation.report_type or 'AMLO-1-01',
            reservation_dict,
            form_data
        )

        template_map = {
            'AMLO-1-01': '1-01-fill.pdf',
            'AMLO-1-02': '1-02-fill.pdf',
            'AMLO-1-03': '1-03-fill.pdf'
        }
        template_name = template_map.get(reservation.report_type, '1-01-fill.pdf')
        template_path = os.path.join(AMLO_TEMPLATE_DIR, template_name)

        if not os.path.exists(template_path):
            return jsonify({'success': False, 'message': f'PDF template not found: {template_name}'}), 404

        import fitz  # PyMuPDF
        doc = fitz.open(template_path)
        try:
            filled_count = _fill_pdf_form_fields(doc, pdf_fields)
            logger.info(f"[get_editable_pdf] Filled {filled_count} fields for reservation {reservation_id}")

            buffer = BytesIO()
            doc.save(buffer, deflate=True)
            buffer.seek(0)
        finally:
            doc.close()

        download_flag = request.args.get('download', '').lower()
        force_download = download_flag in ('1', 'true', 'yes', 'download')
        filename_base = report_no or reservation_no or f'AMLO-{reservation_id}'
        download_name = f'{filename_base}.pdf'

        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=force_download,
            download_name=download_name
        )

    except Exception as e:
        logger.error(f"[get_editable_pdf] Error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Failed to generate editable PDF: {str(e)}'
        }), 500
    finally:
        session.close()


@app_amlo.route('/reservations/<int:reservation_id>/upload-filled-pdf', methods=['POST'])
@token_required
def upload_filled_pdf(current_user, reservation_id):
    """
    Upload a locally edited PDF, parse its fields, and store the parsed data back into the reservation.
    """
    session = SessionLocal()
    try:
        file_storage = request.files.get('file')
        if file_storage is None or not file_storage.filename:
            return jsonify({'success': False, 'message': 'PDF file is required'}), 400

        if not file_storage.filename.lower().endswith('.pdf'):
            return jsonify({'success': False, 'message': 'Only PDF files are supported'}), 400

        reservation = session.execute(
            text("""
                SELECT rt.report_type, rt.reservation_no, ar.report_no, rt.form_data
                FROM Reserved_Transaction rt
                LEFT JOIN AMLOReport ar ON rt.id = ar.reserved_id
                WHERE rt.id = :reservation_id
            """),
            {'reservation_id': reservation_id}
        ).fetchone()

        if not reservation:
            return jsonify({'success': False, 'message': 'Reservation not found'}), 404

        now = datetime.now()
        relative_dir = os.path.join('src', 'amlo_uploads', str(now.year), f'{now.month:02d}')
        absolute_dir = os.path.join(PROJECT_ROOT, relative_dir)
        _ensure_directory(absolute_dir)

        safe_base = _sanitize_filename(
            reservation.report_no or reservation.reservation_no or f"reservation-{reservation_id}",
            f"reservation-{reservation_id}"
        )
        saved_filename = f"{reservation.report_type or 'AMLO'}_{safe_base}_{int(now.timestamp())}.pdf"
        saved_path = os.path.join(absolute_dir, saved_filename)
        file_storage.save(saved_path)
        relative_path = os.path.relpath(saved_path, PROJECT_ROOT).replace('\\', '/')

        pdf_fields = _extract_pdf_form_fields(saved_path)
        mapped_fields = map_pdf_fields_to_db(reservation.report_type or 'AMLO-1-01', pdf_fields)

        form_data = _load_form_data(reservation.form_data)
        form_data.update(mapped_fields)
        form_data['__uploaded_pdf_path'] = relative_path
        form_data['__uploaded_pdf_filename'] = saved_filename
        form_data['__uploaded_pdf_uploaded_at'] = now.isoformat()
        form_data['__uploaded_pdf_fields'] = pdf_fields

        session.execute(
            text("""
                UPDATE Reserved_Transaction
                SET form_data = :form_data,
                    updated_at = NOW()
                WHERE id = :reservation_id
            """),
            {
                'form_data': json.dumps(form_data, ensure_ascii=False),
                'reservation_id': reservation_id
            }
        )
        session.commit()

        logger.info(f"[upload_filled_pdf] Reservation {reservation_id} uploaded PDF saved to {relative_path}")

        return jsonify({
            'success': True,
            'message': 'PDF uploaded successfully',
            'uploaded_pdf_url': f"/api/amlo/reservations/{reservation_id}/uploaded-pdf?cache={int(now.timestamp())}",
            'parsed_fields': len(mapped_fields)
        })

    except Exception as e:
        session.rollback()
        logger.error(f"[upload_filled_pdf] Error: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'Failed to upload PDF: {str(e)}'}), 500
    finally:
        session.close()


@app_amlo.route('/reservations/<int:reservation_id>/uploaded-pdf', methods=['GET'])
@token_required
def serve_uploaded_pdf(current_user, reservation_id):
    """
    Serve the previously uploaded PDF file back to the browser.
    """
    session = SessionLocal()
    try:
        record = session.execute(
            text("SELECT form_data FROM Reserved_Transaction WHERE id = :reservation_id"),
            {'reservation_id': reservation_id}
        ).fetchone()

        if not record:
            return jsonify({'success': False, 'message': 'Reservation not found'}), 404

        form_data = _load_form_data(record[0])
        relative_path = form_data.get('__uploaded_pdf_path')
        if not relative_path:
            return jsonify({'success': False, 'message': 'No uploaded PDF available'}), 404

        absolute_path = _resolve_project_path(relative_path)
        if not os.path.exists(absolute_path):
            return jsonify({'success': False, 'message': 'Uploaded PDF file missing'}), 404

        return send_file(
            absolute_path,
            mimetype='application/pdf',
            as_attachment=False,
            download_name=os.path.basename(absolute_path)
        )

    except Exception as e:
        logger.error(f"[serve_uploaded_pdf] Error: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        session.close()


# ==============================================================================
# PDF GENERATION ROUTES
# ==============================================================================

@app_amlo.route('/reservations/<int:reservation_id>/generate-pdf', methods=['GET'])
@token_required
@amlo_permission_required('amlo_report_view')
def generate_pdf_from_reservation(current_user, reservation_id):
    """
    Generate PDF directly from reservation ID (always regenerate to ensure latest version with signatures)
    """
    session = SessionLocal()
    try:
        logger.info(f"[generate_pdf_from_reservation] Generating PDF for reservation {reservation_id}")

        # 🔧 FIX: Always regenerate PDF to ensure we get the latest version with signatures
        # Don't rely on database pdf_path which may be outdated or use different naming conventions
        pdf_success, pdf_path, pdf_error = PDFGenerationService.generate_single_pdf(
            session, reservation_id
        )

        if not pdf_success:
            logger.error(f"[generate_pdf_from_reservation] PDF generation failed: {pdf_error}")
            return jsonify({
                'success': False,
                'message': f'PDF生成失败: {pdf_error}'
            }), 404

        # Ensure pdf_path is absolute
        if not os.path.isabs(pdf_path):
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            pdf_path = os.path.join(project_root, pdf_path)

        # Normalize path
        pdf_path = os.path.normpath(pdf_path)

        logger.info(f"[generate_pdf_from_reservation] PDF generated successfully: {pdf_path}")
        logger.info(f"[generate_pdf_from_reservation] File exists: {os.path.exists(pdf_path)}")

        if not os.path.exists(pdf_path):
            logger.error(f"[generate_pdf_from_reservation] PDF file does not exist after generation: {pdf_path}")
            return jsonify({
                'success': False,
                'message': f'PDF文件生成后不存在: {pdf_path}'
            }), 500

        # Return PDF file
        logger.info(f"[generate_pdf_from_reservation] Sending PDF file: {pdf_path}")
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=False,  # Display in browser instead of download
            download_name=os.path.basename(pdf_path)
        )

    except Exception as e:
        logger.error(f"[generate_pdf_from_reservation] Error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'生成PDF失败: {str(e)}'
        }), 500
    finally:
        session.close()


@app_amlo.route('/reports/<int:report_id>/generate-pdf', methods=['GET'])
@token_required
@amlo_permission_required('amlo_report_view')
def generate_report_pdf(current_user, report_id):
    """
    Generate single AMLO report PDF
    """
    session = SessionLocal()
    try:
        # Use service to generate PDF
        success, pdf_path, error = PDFGenerationService.generate_single_pdf(
            session, report_id
        )

        if not success:
            return jsonify({'success': False, 'message': error}), 404

        # Return PDF file
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=os.path.basename(pdf_path)
        )

    except Exception as e:
        logger.error(f"[generate_report_pdf] Error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Failed to generate PDF: {str(e)}'
        }), 500
    finally:
        session.close()


@app_amlo.route('/reports/batch-generate-pdf', methods=['POST'])
@token_required
@amlo_permission_required('amlo_report_view')
def batch_generate_pdf(current_user):
    """
    Generate multiple PDFs as ZIP archive
    """
    session = SessionLocal()
    try:
        request_data = request.get_json() or {}
        report_ids = request_data.get('report_ids')

        if not report_ids:
            return jsonify({'success': False, 'message': 'Report IDs required'}), 400

        branch_id = g.current_user.get('branch_id')

        # Use service
        success, zip_buffer, error = PDFGenerationService.generate_pdf_batch_as_zip(
            session, report_ids, branch_id
        )

        if not success:
            return jsonify({'success': False, 'message': error}), 400

        # Return ZIP file
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'AMLO_Reports_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
        )

    except Exception as e:
        logger.error(f"[batch_generate_pdf] Error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Failed to generate batch PDFs: {str(e)}'
        }), 500
    finally:
        session.close()


@app_amlo.route('/blank-form/<report_type>', methods=['GET'])
@token_required
def serve_blank_form(current_user, report_type):
    """
    Serve blank AMLO form PDF
    """
    try:
        # Use service
        success, file_path, error = PDFGenerationService.get_blank_form_path(report_type)

        if not success:
            return jsonify({'success': False, 'message': error}), 404

        # Return PDF file
        return send_file(
            file_path,
            mimetype='application/pdf',
            as_attachment=False,
            download_name=f'{report_type}_blank.pdf'
        )

    except Exception as e:
        logger.error(f"[serve_blank_form] Error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Failed to serve blank form: {str(e)}'
        }), 500


# ==============================================================================
# SIGNATURE MANAGEMENT ROUTES
# ==============================================================================

@app_amlo.route('/reservations/<int:reservation_id>/signature', methods=['POST'])
@token_required
def save_reporter_signature(current_user, reservation_id):
    """
    Save reporter signature for reservation
    Simplified endpoint for single signature submission with reporter_date
    """
    print(f"\n{'='*80}", flush=True)
    print(f"[SIGNATURE_DEBUG] ===== ENDPOINT CALLED: save_reporter_signature =====", flush=True)
    print(f"[SIGNATURE_DEBUG] Reservation ID: {reservation_id}", flush=True)
    print(f"[SIGNATURE_DEBUG] User: {current_user.get('username') if current_user else 'Unknown'}", flush=True)
    print(f"{'='*80}\n", flush=True)

    session = SessionLocal()
    try:
        request_data = request.get_json() or {}
        print(f"[SIGNATURE_DEBUG] Request data keys: {list(request_data.keys())}", flush=True)

        signature_data = request_data.get('signature')
        reporter_date = request_data.get('reporter_date')

        if not signature_data:
            return jsonify({'success': False, 'message': 'Signature data is required'}), 400

        # Save reporter signature
        signatures = {
            'reporter_signature': signature_data,
            'customer_signature': None,
            'auditor_signature': None
        }

        print(f"[SIGNATURE_DEBUG] Starting to save signature for reservation {reservation_id}", flush=True)

        success, result_data, error = SignatureService.save_reservation_signatures(
            session, reservation_id, signatures, 'base64'
        )

        print(f"[SIGNATURE_DEBUG] Signature save result: success={success}, error={error}", flush=True)

        if not success:
            return jsonify({'success': False, 'message': error}), 400

        print(f"[SIGNATURE_DEBUG] Signature saved successfully", flush=True)

        # Update reporter_date if provided
        if reporter_date:
            # Update form_data with reporter_date
            from sqlalchemy import text
            update_sql = text("""
                UPDATE Reserved_Transaction
                SET form_data = JSON_SET(COALESCE(form_data, '{}'), '$.reporter_date', :reporter_date)
                WHERE id = :reservation_id
            """)
            session.execute(update_sql, {
                'reporter_date': reporter_date,
                'reservation_id': reservation_id
            })
            session.commit()

        # 🆕 重新生成PDF以显示签名
        print(f"[SIGNATURE_DEBUG] ===== Starting PDF regeneration for reservation {reservation_id} =====", flush=True)
        logger.info(f"[save_reporter_signature] Regenerating PDF for reservation {reservation_id} with signature")
        try:
            print(f"[SIGNATURE_DEBUG] Calling PDFGenerationService.generate_single_pdf()", flush=True)
            # 直接使用reservation_id重新生成PDF（generate_single_pdf会自动读取签名）
            pdf_success, pdf_path, pdf_error = PDFGenerationService.generate_single_pdf(
                session, reservation_id
            )

            print(f"[SIGNATURE_DEBUG] PDF generation result: success={pdf_success}, path={pdf_path}, error={pdf_error}", flush=True)

            if pdf_success:
                logger.info(f"[save_reporter_signature] PDF regenerated successfully: {pdf_path}")
                print(f"[SIGNATURE_DEBUG] ✅ PDF regenerated successfully: {pdf_path}", flush=True)
                result_data['pdf_regenerated'] = True
                result_data['pdf_path'] = pdf_path
            else:
                logger.warning(f"[save_reporter_signature] PDF regeneration failed: {pdf_error}")
                print(f"[SIGNATURE_DEBUG] ❌ PDF regeneration failed: {pdf_error}", flush=True)
                result_data['pdf_regenerated'] = False
                result_data['pdf_error'] = pdf_error
        except Exception as pdf_ex:
            logger.error(f"[save_reporter_signature] PDF regeneration error: {pdf_ex}", exc_info=True)
            print(f"[SIGNATURE_DEBUG] ❌ PDF regeneration exception: {pdf_ex}", flush=True)
            import traceback
            traceback.print_exc()
            result_data['pdf_regenerated'] = False
            result_data['pdf_error'] = str(pdf_ex)

        return jsonify({
            'success': True,
            'message': 'Reporter signature saved successfully',
            'data': result_data
        })

    except Exception as e:
        logger.error(f"[save_reporter_signature] Error: {e}", exc_info=True)
        session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to save signature: {str(e)}'
        }), 500
    finally:
        session.close()


# ==============================================================================
# ERROR HANDLERS
# ==============================================================================

@app_amlo.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'Resource not found'
    }), 404


@app_amlo.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'message': 'Internal server error'
    }), 500
