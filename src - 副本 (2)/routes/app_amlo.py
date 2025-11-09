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
        branch_id = g.current_user.get('branch_id')
        if not branch_id:
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

        # Use service
        result = ReservationService.list_reservations(
            session, branch_id, filters, page, page_size
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
    Update reservation form data
    """
    session = SessionLocal()
    try:
        request_data = request.get_json() or {}
        form_data = request_data.get('form_data')

        if not form_data:
            return jsonify({'success': False, 'message': 'Form data required'}), 400

        user_id = g.current_user.get('id')

        # Use service
        success, error = ReservationService.update_reservation_form_data(
            session, reservation_id, form_data, user_id
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
    Generate PDF directly from reservation ID (原来的方式)
    """
    from services.amlo.report_creation_service import ReportCreationService
    from sqlalchemy import text

    session = SessionLocal()
    try:
        logger.info(f"[generate_pdf_from_reservation] Generating PDF for reservation {reservation_id}")

        # 1. 查找该预约对应的报告
        report = session.execute(text("""
            SELECT id, report_no, pdf_path
            FROM AMLOReport
            WHERE reserved_id = :reservation_id
            ORDER BY created_at DESC
            LIMIT 1
        """), {'reservation_id': reservation_id}).fetchone()

        if not report:
            # 如果没有报告，尝试创建一个
            logger.info(f"[generate_pdf_from_reservation] No report found, creating new report for reservation {reservation_id}")

            result = ReportCreationService.create_report_for_reservation(session, reservation_id)

            if not result['success']:
                logger.error(f"[generate_pdf_from_reservation] Failed to create report: {result.get('error')}")
                return jsonify({
                    'success': False,
                    'message': f"无法创建报告: {result.get('error')}"
                }), 404

            pdf_path = result.get('pdf_path')
            report_no = result.get('report_no')
        else:
            # 使用已存在的报告
            report_id = report[0]
            report_no = report[1]
            pdf_path = report[2]

            logger.info(f"[generate_pdf_from_reservation] Found existing report {report_id}: {report_no}")

            # 检查PDF文件是否存在
            if not os.path.exists(pdf_path):
                logger.warning(f"[generate_pdf_from_reservation] PDF file not found, regenerating: {pdf_path}")

                # PDF文件不存在，重新生成
                result = ReportCreationService._generate_pdf(session, reservation_id, report_no)

                if not result['success']:
                    return jsonify({
                        'success': False,
                        'message': f"无法生成PDF: {result.get('error')}"
                    }), 500

                pdf_path = result.get('pdf_path')

        # 返回PDF文件
        if pdf_path and os.path.exists(pdf_path):
            logger.info(f"[generate_pdf_from_reservation] Sending PDF file: {pdf_path}")
            return send_file(
                pdf_path,
                mimetype='application/pdf',
                as_attachment=False,  # 在浏览器中显示而不是下载
                download_name=os.path.basename(pdf_path)
            )
        else:
            logger.error(f"[generate_pdf_from_reservation] PDF file does not exist: {pdf_path}")
            return jsonify({
                'success': False,
                'message': 'PDF文件不存在'
            }), 404

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

@app_amlo.route('/reservations/<int:reservation_id>/signatures', methods=['POST', 'PUT'])
@token_required
def save_signatures(current_user, reservation_id):
    """
    Save signature images for reservation
    """
    session = SessionLocal()
    try:
        request_data = request.get_json() or {}

        signatures = {
            'reporter_signature': request_data.get('reporter_signature'),
            'customer_signature': request_data.get('customer_signature'),
            'auditor_signature': request_data.get('auditor_signature')
        }

        storage_type = request_data.get('storage_type', 'base64')

        # Use service
        success, result_data, error = SignatureService.save_reservation_signatures(
            session, reservation_id, signatures, storage_type
        )

        if not success:
            return jsonify({'success': False, 'message': error}), 400

        return jsonify({
            'success': True,
            'message': 'Signatures saved successfully',
            'data': result_data
        })

    except Exception as e:
        logger.error(f"[save_signatures] Error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Failed to save signatures: {str(e)}'
        }), 500
    finally:
        session.close()


@app_amlo.route('/reservations/<int:reservation_id>/signatures', methods=['GET'])
@token_required
def get_signatures(current_user, reservation_id):
    """
    Get all signatures for reservation
    """
    session = SessionLocal()
    try:
        # Use service
        success, signatures_data, error = SignatureService.get_reservation_signatures(
            session, reservation_id
        )

        if not success:
            return jsonify({'success': False, 'message': error}), 404

        return jsonify({
            'success': True,
            'data': signatures_data
        })

    except Exception as e:
        logger.error(f"[get_signatures] Error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Failed to get signatures: {str(e)}'
        }), 500
    finally:
        session.close()


@app_amlo.route('/reservations/<int:reservation_id>/signatures/<signature_type>', methods=['DELETE'])
@token_required
def delete_signature(current_user, reservation_id, signature_type):
    """
    Delete specific signature
    """
    session = SessionLocal()
    try:
        # Use service
        success, error = SignatureService.delete_signature(
            session, reservation_id, signature_type
        )

        if not success:
            return jsonify({'success': False, 'message': error}), 400

        return jsonify({
            'success': True,
            'message': f'{signature_type.capitalize()} signature deleted successfully'
        })

    except Exception as e:
        logger.error(f"[delete_signature] Error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Failed to delete signature: {str(e)}'
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
