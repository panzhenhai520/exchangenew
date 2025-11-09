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

# Import AMLO services
from services.amlo import (
    ReservationService,
    AuditService,
    ReportService,
    PDFGenerationService,
    SignatureService
)

# Get logger instance
logger = logging.getLogger(__name__)

# Create Blueprint
app_amlo = Blueprint('app_amlo', __name__, url_prefix='/api/amlo')


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
                print(f"[SIGNATURE_DEBUG] [OK] PDF regenerated successfully: {pdf_path}", flush=True)
                result_data['pdf_regenerated'] = True
                result_data['pdf_path'] = pdf_path
            else:
                logger.warning(f"[save_reporter_signature] PDF regeneration failed: {pdf_error}")
                print(f"[SIGNATURE_DEBUG] [ERROR] PDF regeneration failed: {pdf_error}", flush=True)
                result_data['pdf_regenerated'] = False
                result_data['pdf_error'] = pdf_error
        except Exception as pdf_ex:
            logger.error(f"[save_reporter_signature] PDF regeneration error: {pdf_ex}", exc_info=True)
            print(f"[SIGNATURE_DEBUG] [ERROR] PDF regeneration exception: {pdf_ex}", flush=True)
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
# PDF EDITABLE REPORT ENDPOINTS
# ==============================================================================

@app_amlo.route('/reservations/<int:reservation_id>/editable-pdf', methods=['GET'])
@token_required
def get_editable_pdf(current_user, reservation_id):
    """
    Return editable PDF with AcroForm fields filled with reservation data
    This PDF can be edited directly in the browser
    """
    logger.info(f"[get_editable_pdf] Getting editable PDF for reservation {reservation_id}")

    session = SessionLocal()
    try:
        from sqlalchemy import text
        import pymupdf
        import json
        from io import BytesIO

        # 1. Get reservation data
        reservation = session.execute(text("""
            SELECT
                rt.id,
                rt.report_type,
                rt.customer_id,
                rt.customer_name,
                rt.amount,
                rt.local_amount,
                rt.form_data,
                rt.reporter_signature,
                ar.report_no
            FROM Reserved_Transaction rt
            LEFT JOIN AMLOReport ar ON rt.id = ar.reserved_id
            WHERE rt.id = :id
        """), {'id': reservation_id}).fetchone()

        if not reservation:
            return jsonify({
                'success': False,
                'error': 'Reservation not found'
            }), 404

        # 2. Parse form_data
        form_data = {}
        if reservation.form_data:
            try:
                form_data = json.loads(reservation.form_data) if isinstance(reservation.form_data, str) else reservation.form_data
            except:
                form_data = {}

        # Add structured fields to form_data for unified processing
        form_data['report_no'] = reservation.report_no or ''
        form_data['customer_name'] = reservation.customer_name or ''
        form_data['customer_id'] = reservation.customer_id or ''
        form_data['amount'] = str(reservation.amount or 0)
        form_data['local_amount'] = str(reservation.local_amount or 0)

        # 3. Convert database field names to PDF field names using mapper
        try:
            from services.pdf.amlo_data_mapper import AMLODataMapper

            mapper = AMLODataMapper()
            reservation_dict = {
                'reservation_no': reservation.report_no,
                'customer_name': reservation.customer_name,
                'customer_id': reservation.customer_id,
                'amount': reservation.amount,
                'local_amount': reservation.local_amount
            }

            # Map to PDF field names (fill_52, comb_1, etc.)
            pdf_fields = mapper.map_reservation_to_pdf_fields(
                report_type='AMLO-1-01',
                reservation_data=reservation_dict,
                form_data=form_data
            )
            logger.info(f"[get_editable_pdf] Mapped {len(pdf_fields)} fields using AMLODataMapper")

        except Exception as e:
            logger.warning(f"[get_editable_pdf] Failed to use mapper, using raw form_data: {e}")
            pdf_fields = form_data  # Fallback to original data

        # 4. Open PDF template (user's marked PDF with AcroForm fields)
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'Re', '1-01-fill.pdf'
        )

        if not os.path.exists(template_path):
            logger.error(f"[get_editable_pdf] Template PDF not found: {template_path}")
            return jsonify({
                'success': False,
                'error': f'Template PDF not found: {template_path}'
            }), 404

        logger.info(f"[get_editable_pdf] Opening template: {template_path}")
        doc = pymupdf.open(template_path)

        # 5. Fill PDF form fields with mapped data (keep fields editable, don't flatten)
        filled_count = _fill_pdf_form_fields(doc, pdf_fields)
        logger.info(f"[get_editable_pdf] Filled {filled_count} form fields")

        # 5. Save to BytesIO (keep as editable form)
        pdf_bytes = BytesIO()
        doc.save(pdf_bytes, garbage=4, deflate=True)
        pdf_bytes.seek(0)
        doc.close()

        logger.info(f"[get_editable_pdf] Returning editable PDF ({pdf_bytes.getbuffer().nbytes} bytes)")

        # 6. Return PDF
        return send_file(
            pdf_bytes,
            mimetype='application/pdf',
            as_attachment=False,
            download_name=f'AMLO_{reservation_id}_editable.pdf'
        )

    except Exception as e:
        logger.error(f"[get_editable_pdf] Error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Failed to generate editable PDF: {str(e)}'
        }), 500
    finally:
        session.close()


def _fill_pdf_form_fields(doc, form_data):
    """
    Fill PDF form fields with data from form_data dictionary

    Args:
        doc: PyMuPDF document object
        form_data: Dictionary of field_name -> value

    Returns:
        int: Number of fields filled
    """
    import pymupdf

    filled_count = 0

    for page_num in range(len(doc)):
        page = doc[page_num]

        # Iterate through all form widgets on the page
        for widget in page.widgets():
            field_name = widget.field_name

            if not field_name or field_name not in form_data:
                continue

            value = form_data[field_name]
            field_type = widget.field_type

            try:
                # Handle different field types
                if field_type == pymupdf.PDF_WIDGET_TYPE_TEXT:
                    # Text field
                    widget.field_value = str(value) if value is not None else ''
                    widget.update()
                    filled_count += 1

                elif field_type == pymupdf.PDF_WIDGET_TYPE_CHECKBOX:
                    # Checkbox field
                    # PyMuPDF uses True/False or 'Yes'/'Off' for checkboxes
                    if isinstance(value, bool):
                        widget.field_value = value
                    elif isinstance(value, str):
                        widget.field_value = value.lower() in ('true', 'yes', '1', 'on')
                    else:
                        widget.field_value = bool(value)
                    widget.update()
                    filled_count += 1

                elif field_type == pymupdf.PDF_WIDGET_TYPE_COMBOBOX or field_type == pymupdf.PDF_WIDGET_TYPE_LISTBOX:
                    # Dropdown/List field
                    widget.field_value = str(value) if value is not None else ''
                    widget.update()
                    filled_count += 1

                # Note: We don't flatten the form, keeping fields editable

            except Exception as e:
                logger.warning(f"[_fill_pdf_form_fields] Failed to fill field '{field_name}': {e}")
                continue

    return filled_count


@app_amlo.route('/reservations/<int:reservation_id>/flatten-pdf', methods=['POST'])
@token_required
def flatten_pdf_with_data(current_user, reservation_id):
    """
    Flatten PDF (convert form fields to static content) with latest data
    This endpoint:
    1. Accepts final form_data from frontend
    2. Fills PDF form fields
    3. Flattens the PDF (removes interactive fields)
    4. Saves as final PDF
    5. Returns flattened PDF file
    """
    logger.info(f"[flatten_pdf_with_data] Flattening PDF for reservation {reservation_id}")

    session = SessionLocal()
    try:
        from sqlalchemy import text
        import pymupdf
        import json
        from io import BytesIO

        # Get submitted form data
        request_data = request.get_json() or {}
        form_data = request_data.get('form_data', {})
        signature_data = request_data.get('signature_data', {})

        if not form_data:
            return jsonify({
                'success': False,
                'error': 'Form data is required'
            }), 400

        logger.info(f"[flatten_pdf_with_data] Received form_data with {len(form_data)} fields")

        # 1. Get reservation for report number and basic info
        reservation = session.execute(text("""
            SELECT
                rt.id,
                ar.report_no,
                rt.customer_name,
                rt.amount
            FROM Reserved_Transaction rt
            LEFT JOIN AMLOReport ar ON rt.id = ar.reserved_id
            WHERE rt.id = :id
        """), {'id': reservation_id}).fetchone()

        if not reservation:
            return jsonify({
                'success': False,
                'error': 'Reservation not found'
            }), 404

        report_no = reservation.report_no or 'DRAFT'

        # 2. Open PDF template
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'Re', '1-01-fill.pdf'
        )

        if not os.path.exists(template_path):
            return jsonify({
                'success': False,
                'error': f'Template PDF not found: {template_path}'
            }), 404

        doc = pymupdf.open(template_path)

        # 3. Fill form fields with latest data
        filled_count = _fill_pdf_form_fields(doc, form_data)
        logger.info(f"[flatten_pdf_with_data] Filled {filled_count} form fields")

        # 4. Add signature if provided
        if signature_data and signature_data.get('reporter_signature'):
            # TODO: Add signature to PDF using the signature service
            logger.info(f"[flatten_pdf_with_data] Signature data provided (will be added in future)")

        # 5. Flatten the PDF (convert form fields to static content)
        logger.info(f"[flatten_pdf_with_data] Flattening PDF...")
        for page_num in range(len(doc)):
            page = doc[page_num]
            # Remove all widgets (form fields), converting them to static text
            # PyMuPDF API: iterate through widgets and delete each one
            widgets = list(page.widgets())
            for widget in widgets:
                widget.update()  # Ensure widget value is rendered
            # Delete all form widgets to flatten the PDF
            for widget in widgets:
                page.delete_widget(widget)

        logger.info(f"[flatten_pdf_with_data] ✅ PDF flattened, form fields converted to static content")

        # 6. Save final PDF
        final_pdf_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'amlo_pdfs'
        )
        os.makedirs(final_pdf_dir, exist_ok=True)

        final_pdf_filename = f"AMLO-1-01_{report_no}USD.pdf"
        final_pdf_path = os.path.join(final_pdf_dir, final_pdf_filename)

        doc.save(final_pdf_path, garbage=4, deflate=True)
        doc.close()

        logger.info(f"[flatten_pdf_with_data] Final PDF saved: {final_pdf_path}")

        # 7. Update database with final form_data
        update_sql = text("""
            UPDATE Reserved_Transaction
            SET form_data = :form_data,
                pdf_path = :pdf_path
            WHERE id = :reservation_id
        """)
        session.execute(update_sql, {
            'form_data': json.dumps(form_data, ensure_ascii=False),
            'pdf_path': final_pdf_path,
            'reservation_id': reservation_id
        })
        session.commit()

        logger.info(f"[flatten_pdf_with_data] Database updated with final data")

        # 8. Return flattened PDF
        return send_file(
            final_pdf_path,
            mimetype='application/pdf',
            as_attachment=False,
            download_name=final_pdf_filename
        )

    except Exception as e:
        logger.error(f"[flatten_pdf_with_data] Error: {e}", exc_info=True)
        session.rollback()
        return jsonify({
            'success': False,
            'error': f'Failed to flatten PDF: {str(e)}'
        }), 500
    finally:
        session.close()


@app_amlo.route('/submit-modified-report', methods=['POST'])
@token_required
def submit_modified_report(current_user):
    """
    Submit modified report content with signature
    Saves all modifications to database and regenerates PDF
    """
    print("\n" + "="*100, flush=True)
    print("[submit_modified_report] 🚀 开始处理表单修改提交", flush=True)
    print(f"[submit_modified_report] 用户: {current_user.get('username')}", flush=True)
    print("="*100 + "\n", flush=True)
    logger.info(f"[submit_modified_report] User {current_user.get('username')} submitting modified report")

    session = SessionLocal()
    try:
        data = request.get_json() or {}
        print(f"[submit_modified_report] 📦 接收到的数据键:", list(data.keys()), flush=True)

        reservation_id = data.get('reservation_id')
        modified_data = data.get('modified_data', {})
        modified_fields = data.get('modified_fields', [])
        signature_data = data.get('signature', {})
        modifications_summary = data.get('modifications_summary', [])

        print(f"[submit_modified_report] - 预约ID: {reservation_id}", flush=True)
        print(f"[submit_modified_report] - 修改的字段: {modified_fields}", flush=True)
        print(f"[submit_modified_report] - modified_data键: {list(modified_data.keys())}", flush=True)
        print(f"[submit_modified_report] - modified_data.form_data键: {list(modified_data.get('form_data', {}).keys())}", flush=True)

        if not reservation_id:
            print("[submit_modified_report] ❌ 缺少reservation_id", flush=True)
            return jsonify({
                'success': False,
                'error': 'reservation_id is required'
            }), 400

        logger.info(f"[submit_modified_report] Processing reservation {reservation_id}, {len(modified_fields)} fields modified")
        print(f"\n[submit_modified_report] 📝 处理预约 {reservation_id}，修改了 {len(modified_fields)} 个字段", flush=True)

        # 1. Query original reservation
        from sqlalchemy import text
        original_reservation = session.execute(text("""
            SELECT * FROM Reserved_Transaction
            WHERE id = :id
        """), {'id': reservation_id}).fetchone()

        if not original_reservation:
            return jsonify({
                'success': False,
                'error': 'Reservation not found'
            }), 404

        # 2. Prepare audit log (record before/after comparison)
        import json
        old_data = {
            'customer_name': original_reservation.customer_name,
            'customer_id': original_reservation.customer_id,
            'local_amount': float(original_reservation.local_amount) if original_reservation.local_amount else 0,
            'amount': float(original_reservation.amount) if original_reservation.amount else 0,
            'form_data': json.loads(original_reservation.form_data) if original_reservation.form_data else {}
        }

        # 3. Update Reserved_Transaction table
        update_fields = []
        update_params = {'reservation_id': reservation_id}

        # Update structured fields
        if 'customer_name' in modified_fields:
            update_fields.append('customer_name = :customer_name')
            update_params['customer_name'] = modified_data.get('customer_name')

        if 'customer_id' in modified_fields:
            update_fields.append('customer_id = :customer_id')
            update_params['customer_id'] = modified_data.get('customer_id')

        if 'local_amount' in modified_fields:
            update_fields.append('local_amount = :local_amount')
            update_params['local_amount'] = modified_data.get('local_amount')

        if 'amount' in modified_fields:
            update_fields.append('amount = :amount')
            update_params['amount'] = modified_data.get('amount')

        # Update form_data (merge modifications)
        print(f"\n[submit_modified_report] 🔄 更新form_data...", flush=True)
        updated_form_data = json.loads(original_reservation.form_data) if original_reservation.form_data else {}
        print(f"[submit_modified_report] - 原始form_data字段数: {len(updated_form_data)}", flush=True)
        print(f"[submit_modified_report] - 原始form_data键: {list(updated_form_data.keys())[:20]}", flush=True)  # 只显示前20个

        if modified_data.get('form_data'):
            print(f"[submit_modified_report] - 要合并的新字段数: {len(modified_data['form_data'])}", flush=True)
            print(f"[submit_modified_report] - 要合并的新字段: {list(modified_data['form_data'].keys())}", flush=True)
            updated_form_data.update(modified_data['form_data'])
            print(f"[submit_modified_report] - 合并后form_data字段数: {len(updated_form_data)}", flush=True)
        else:
            print(f"[submit_modified_report] - 没有新的form_data需要合并", flush=True)

        update_fields.append('form_data = :form_data')
        update_params['form_data'] = json.dumps(updated_form_data, ensure_ascii=False)
        print(f"[submit_modified_report] ✅ form_data准备完成，JSON长度: {len(update_params['form_data'])} 字符", flush=True)

        # Update signatures
        if signature_data:
            if signature_data.get('reporter_signature'):
                update_fields.append('reporter_signature = :reporter_signature')
                update_params['reporter_signature'] = signature_data['reporter_signature']

            if signature_data.get('customer_signature'):
                update_fields.append('customer_signature = :customer_signature')
                update_params['customer_signature'] = signature_data['customer_signature']

            if signature_data.get('auditor_signature'):
                update_fields.append('auditor_signature = :auditor_signature')
                update_params['auditor_signature'] = signature_data['auditor_signature']

        # Execute update
        if update_fields:
            print(f"\n[submit_modified_report] 💾 执行数据库更新...", flush=True)
            print(f"[submit_modified_report] - 要更新的字段: {update_fields}", flush=True)
            print(f"[submit_modified_report] - 参数键: {list(update_params.keys())}", flush=True)

            update_sql = text(f"""
                UPDATE Reserved_Transaction
                SET {', '.join(update_fields)}
                WHERE id = :reservation_id
            """)
            print(f"[submit_modified_report] - SQL: UPDATE Reserved_Transaction SET {', '.join(update_fields)} WHERE id = {reservation_id}", flush=True)

            session.execute(update_sql, update_params)
            session.commit()
            print(f"[submit_modified_report] ✅ 数据库更新成功，更新了 {len(update_fields)} 个字段", flush=True)
            logger.info(f"[submit_modified_report] Updated {len(update_fields)} fields for reservation {reservation_id}")
        else:
            print(f"[submit_modified_report] ⚠️ 没有字段需要更新", flush=True)

        # 4. Record audit log
        audit_log_sql = text("""
            INSERT INTO audit_log (
                operation_type, module, entity_type, entity_id,
                action, old_value, new_value,
                operator_id, operator_name, branch_id, remarks, created_at
            ) VALUES (
                'UPDATE', 'AMLO', 'Reserved_Transaction', :entity_id,
                'MODIFY_REPORT_CONTENT', :old_value, :new_value,
                :operator_id, :operator_name, :branch_id, :remarks, NOW()
            )
        """)

        session.execute(audit_log_sql, {
            'entity_id': reservation_id,
            'old_value': json.dumps(old_data, ensure_ascii=False),
            'new_value': json.dumps(modified_data, ensure_ascii=False),
            'operator_id': current_user.get('id'),
            'operator_name': current_user.get('name') or current_user.get('username'),
            'branch_id': current_user.get('branch_id'),
            'remarks': f"Modified {len(modified_fields)} fields: {', '.join(modified_fields)}"
        })
        session.commit()
        logger.info(f"[submit_modified_report] Audit log recorded")

        # 5. Regenerate PDF with modified data
        pdf_result = {'success': False}
        report_no = None

        try:
            # Get report number
            report = session.execute(text("""
                SELECT report_no FROM AMLOReport WHERE reserved_id = :id
            """), {'id': reservation_id}).fetchone()

            report_no = report.report_no if report else None

            if report_no:
                # Regenerate PDF using the service
                from services.amlo.report_creation_service import ReportCreationService
                pdf_result = ReportCreationService._generate_pdf(
                    session, reservation_id, report_no
                )

                if pdf_result['success']:
                    logger.info(f"[submit_modified_report] PDF regenerated successfully: {pdf_result.get('pdf_path')}")
                else:
                    logger.warning(f"[submit_modified_report] PDF regeneration failed: {pdf_result.get('error')}")
            else:
                logger.warning(f"[submit_modified_report] No report number found for reservation {reservation_id}")

        except Exception as pdf_error:
            logger.error(f"[submit_modified_report] PDF regeneration error: {pdf_error}", exc_info=True)
            pdf_result = {'success': False, 'error': str(pdf_error)}

        # 6. Return result
        import time
        return jsonify({
            'success': True,
            'data': {
                'reservation_id': reservation_id,
                'report_no': report_no,
                'updated_fields': modified_fields,
                'pdf_regenerated': pdf_result.get('success', False),
                'new_pdf_path': f"/api/amlo/reservation/{reservation_id}/pdf?v={int(time.time())}"
            }
        })

    except Exception as e:
        logger.error(f"[submit_modified_report] Error: {e}", exc_info=True)
        session.rollback()
        return jsonify({
            'success': False,
            'error': f'Failed to submit modifications: {str(e)}'
        }), 500

    finally:
        session.close()


@app_amlo.route('/report-fields/<string:report_type>', methods=['GET'])
@token_required
def get_report_fields(current_user, report_type):
    """
    Get editable field configuration for a report type
    Returns field metadata including name, label, type, validation rules
    """
    logger.info(f"[get_report_fields] Getting fields for report type: {report_type}")

    session = SessionLocal()
    try:
        from sqlalchemy import text

        # Query report_fields table for the specific report type
        fields_result = session.execute(text("""
            SELECT
                field_name,
                field_type,
                field_cn_name,
                field_en_name,
                field_th_name,
                is_required,
                default_value,
                validation_rule,
                placeholder_cn,
                field_group
            FROM report_fields
            WHERE report_type = :report_type
              AND is_active = 1
            ORDER BY fill_order
        """), {'report_type': report_type}).fetchall()

        # Build field configuration
        fields = []
        for row in fields_result:
            field = {
                'name': row.field_name,
                'type': row.field_type.lower(),
                'label': row.field_cn_name,  # Default to Chinese
                'label_en': row.field_en_name,
                'label_th': row.field_th_name,
                'is_editable': row.field_name != 'report_no',  # Report number is not editable
                'is_required': bool(row.is_required),
                'default_value': row.default_value,
                'placeholder': row.placeholder_cn,
                'group': row.field_group
            }

            # Parse validation rules if exists
            if row.validation_rule:
                try:
                    import json
                    field['validation'] = json.loads(row.validation_rule)
                except:
                    field['validation'] = {}

            fields.append(field)

        logger.info(f"[get_report_fields] Found {len(fields)} fields for {report_type}")

        return jsonify({
            'success': True,
            'fields': fields
        })

    except Exception as e:
        logger.error(f"[get_report_fields] Error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Failed to get report fields: {str(e)}'
        }), 500

    finally:
        session.close()


@app_amlo.route('/reservation/<int:reservation_id>', methods=['GET'])
@token_required
def get_reservation_for_editing(current_user, reservation_id):
    """
    Get detailed reservation information for PDF editing
    Returns all data needed for PDF editing including form_data and report_no
    """
    logger.info(f"[get_reservation_for_editing] Getting details for reservation {reservation_id}")

    session = SessionLocal()
    try:
        from sqlalchemy import text

        # Query reservation with all fields
        reservation = session.execute(text("""
            SELECT
                rt.id,
                rt.reservation_no,
                rt.report_type,
                rt.customer_id,
                rt.customer_name,
                rt.customer_country_code,
                rt.direction,
                rt.amount,
                rt.local_amount,
                rt.rate,
                rt.form_data,
                rt.status,
                rt.created_at,
                rt.reporter_signature,
                rt.customer_signature,
                rt.auditor_signature,
                ar.report_no,
                c.currency_code
            FROM Reserved_Transaction rt
            LEFT JOIN AMLOReport ar ON rt.id = ar.reserved_id
            LEFT JOIN currencies c ON rt.currency_id = c.id
            WHERE rt.id = :id
        """), {'id': reservation_id}).fetchone()

        if not reservation:
            return jsonify({
                'success': False,
                'error': 'Reservation not found'
            }), 404

        # Parse form_data
        import json
        form_data = {}
        if reservation.form_data:
            try:
                form_data = json.loads(reservation.form_data) if isinstance(reservation.form_data, str) else reservation.form_data
            except:
                form_data = {}

        # Build response data
        data = {
            'id': reservation.id,
            'reservation_no': reservation.reservation_no,
            'report_no': reservation.report_no,
            'report_type': reservation.report_type,
            'customer_id': reservation.customer_id,
            'customer_name': reservation.customer_name,
            'customer_country_code': reservation.customer_country_code,
            'direction': reservation.direction,
            'amount': float(reservation.amount) if reservation.amount else 0,
            'local_amount': float(reservation.local_amount) if reservation.local_amount else 0,
            'rate': float(reservation.rate) if reservation.rate else 0,
            'currency_code': reservation.currency_code,
            'form_data': form_data,
            'status': reservation.status,
            'created_at': reservation.created_at.isoformat() if reservation.created_at else None,
            'has_reporter_signature': bool(reservation.reporter_signature),
            'has_customer_signature': bool(reservation.customer_signature),
            'has_auditor_signature': bool(reservation.auditor_signature)
        }

        logger.info(f"[get_reservation_for_editing] Retrieved reservation {reservation_id}")

        return jsonify({
            'success': True,
            'data': data
        })

    except Exception as e:
        logger.error(f"[get_reservation_for_editing] Error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Failed to get reservation detail: {str(e)}'
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
