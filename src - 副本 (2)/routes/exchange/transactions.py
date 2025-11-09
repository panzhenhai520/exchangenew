import base64
import os
from datetime import date, datetime

from flask import jsonify, request, send_file
from sqlalchemy import func

from models.exchange_models import (
    Branch,
    Currency,
    ExchangeTransaction,
    Operator,
    SystemLog,
)
from services.auth_service import has_permission, token_required
from services.db_service import DatabaseService

from . import exchange_bp, logger


@exchange_bp.route('/transactions/today', methods=['GET'])
@token_required
@has_permission('transaction_execute')
def get_today_transactions(*args):
    """获取今日交易列表"""
    current_user = args[0]
    session = DatabaseService.get_session()
    try:
        today = date.today()

        # 查询今日所有交易
        transactions = session.query(
            ExchangeTransaction,
            Currency.currency_code,
            Currency.currency_name,
            func.concat(Operator.name, ' (', Operator.login_code, ')').label('operator_name')
        ).join(
            Currency, ExchangeTransaction.currency_id == Currency.id
        ).join(
            Operator, ExchangeTransaction.operator_id == Operator.id
        ).filter(
            ExchangeTransaction.branch_id == current_user['branch_id'],
            ExchangeTransaction.transaction_date == today,
            # 只显示买入、卖出和冲减类型的交易
            ExchangeTransaction.type.in_(['buy', 'sell', 'reversal'])
        ).order_by(
            ExchangeTransaction.created_at.desc()
        ).all()

        result = []
        for tx, currency_code, currency_name, operator_name in transactions:
            # 检查是否已被冲减
            is_reversed = session.query(ExchangeTransaction).filter(
                ExchangeTransaction.type == 'reversal',
                ExchangeTransaction.original_transaction_no == tx.transaction_no
            ).first() is not None

            result.append({
                'id': tx.id,
                'transaction_no': tx.transaction_no,
                'type': tx.type,
                'currency_code': currency_code,
                'currency_name': currency_name,
                'amount': float(tx.amount),
                'rate': float(tx.rate),
                'local_amount': float(tx.local_amount),
                'customer_name': tx.customer_name,
                'operator_name': operator_name,
                'transaction_time': tx.transaction_time,
                'is_reversed': is_reversed,
                'original_transaction_no': tx.original_transaction_no
            })

        return jsonify({
            'success': True,
            'transactions': result
        })

    except Exception as exc:
        logger.error("Error in get_today_transactions: %s", str(exc))
        return jsonify({'success': False, 'message': str(exc)}), 500
    finally:
        DatabaseService.close_session(session)


@exchange_bp.route('/transactions/<int:transaction_id>/print-receipt', methods=['POST'])
@token_required
@has_permission('transaction_execute')
def print_receipt(*args, **kwargs):
    """生成并打印交易票据PDF"""
    # 修复参数顺序问题：从装饰器获取current_user，从路径获取transaction_id
    current_user = args[0] if len(args) > 0 else kwargs.get('current_user')
    transaction_id = args[1] if len(args) > 1 else kwargs.get('transaction_id')

    logger.info("=== 开始打印票据 ===")
    logger.info("transaction_id: %s", transaction_id)
    logger.info("current_user: %s", current_user)

    if not current_user:
        logger.error("用户信息获取失败")
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401

    if not transaction_id:
        logger.error("交易ID参数缺失")
        return jsonify({'success': False, 'message': '交易ID参数缺失'}), 400

    # 获取请求数据，包括语言参数
    request_data = request.get_json() or {}
    language = request_data.get('language', 'zh')  # 默认中文
    logger.info("请求语言: %s", language)

    session = DatabaseService.get_session()

    try:
        logger.info("=== 步骤1：获取交易记录 ===")
        # 获取交易记录
        transaction = session.query(ExchangeTransaction).filter_by(
            id=transaction_id,
            branch_id=current_user['branch_id']
        ).first()

        if not transaction:
            logger.error("交易记录不存在: transaction_id=%s, branch_id=%s", transaction_id, current_user['branch_id'])
            return jsonify({'success': False, 'message': '交易记录不存在'}), 404

        logger.info("找到交易记录: %s", transaction.transaction_no)

        logger.info("=== 步骤2：获取相关信息 ===")
        # 获取相关信息
        currency = session.query(Currency).filter_by(id=transaction.currency_id).first()
        branch = session.query(Branch).filter_by(id=transaction.branch_id).first()
        base_currency = session.query(Currency).filter_by(id=branch.base_currency_id).first()

        logger.info("货币: %s", currency.currency_code if currency else 'None')
        logger.info("网点: %s", branch.branch_name if branch else 'None')
        logger.info("基础货币: %s", base_currency.currency_code if base_currency else 'None')

        # 准备PDF数据
        logger.info("=== 步骤3：导入PDF服务 ===")
        try:
            # 已改用SimplePDFService，无需PDFReceiptService
            logger.info("PDF服务导入成功")
        except ImportError as err:
            logger.error("PDF服务导入失败: %s", err)
            return jsonify({'success': False, 'message': 'PDF服务不可用'}), 500

        # 格式化交易时间
        def format_transaction_time(transaction_date, transaction_time):
            """格式化交易时间显示"""
            try:
                if isinstance(transaction_date, date):
                    date_str = transaction_date.strftime('%Y-%m-%d')
                else:
                    date_str = str(transaction_date)

                if transaction_time:
                    return f"{date_str} {transaction_time}"
                return date_str
            except Exception as err:
                logger.error("格式化交易时间失败: %s", err)
                return f"{transaction_date} {transaction_time or ''}"

        logger.info("=== 步骤4：准备PDF数据 ===")
        # 确定交易类型描述
        if transaction.type == 'buy':
            transaction_type_desc = '买入'
        elif transaction.type == 'sell':
            transaction_type_desc = '卖出'
        else:
            transaction_type_desc = transaction.type

        # 确定金额显示
        if transaction.type == 'buy':
            # 银行买入外币，客户卖出外币
            from_amount = abs(float(transaction.amount))
            from_currency = currency.currency_code
            to_amount = abs(float(transaction.local_amount))
            to_currency = base_currency.currency_code
        else:
            # 银行卖出外币，客户买入外币
            from_amount = abs(float(transaction.local_amount))
            from_currency = base_currency.currency_code
            to_amount = abs(float(transaction.amount))
            to_currency = currency.currency_code

        pdf_data = {
            'transaction_no': transaction.transaction_no,
            'branch_name': branch.branch_name,
            'branch_code': branch.branch_code,
            'transaction_type_desc': transaction_type_desc,
            'currency_code': currency.currency_code,
            'formatted_datetime': format_transaction_time(transaction.transaction_date, transaction.transaction_time),
            'from_amount': from_amount,
            'from_currency': from_currency,
            'to_amount': to_amount,
            'to_currency': to_currency,
            'rate': float(transaction.rate),
            'foreign_currency': currency.currency_code,
            'base_currency': base_currency.currency_code,
            'customer_name': transaction.customer_name or '',
            'customer_id': transaction.customer_id or '',
            'purpose': transaction.purpose or '',
            'remarks': transaction.remarks or ''
        }

        logger.info("PDF数据准备完成: %s", pdf_data)

        logger.info("=== 步骤5：生成PDF文件路径 ===")
        from services.simple_pdf_service import SimplePDFService
        file_path = SimplePDFService.get_receipt_file_path(
            transaction.transaction_no,
            transaction.transaction_date
        )
        logger.info("PDF文件路径: %s", file_path)

        logger.info("=== 步骤6：生成PDF ===")
        try:
            # 使用SimplePDFService生成PDF（返回base64内容），传递语言参数
            reprint_time = datetime.now() if transaction.print_count and transaction.print_count > 0 else None
            pdf_content = SimplePDFService.generate_exchange_receipt(transaction, session, reprint_time, language)

            # 将base64内容保存到文件系统（用于下载）
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'wb') as file_obj:
                file_obj.write(base64.b64decode(pdf_content))

            logger.info("PDF文件已保存到: %s", file_path)
            success = True

        except Exception as pdf_error:
            logger.error("PDF生成过程中发生异常: %s", str(pdf_error))
            import traceback
            logger.error("PDF生成异常详情: %s", traceback.format_exc())
            return jsonify({'success': False, 'message': f'PDF生成异常: {str(pdf_error)}'}), 500

        if not success:
            logger.error("PDF生成失败")
            return jsonify({'success': False, 'message': 'PDF生成失败'}), 500

        logger.info("=== 步骤7：更新交易记录 ===")
        # 更新交易记录中的票据文件名和打印次数
        transaction.receipt_filename = os.path.basename(file_path)
        transaction.print_count = (transaction.print_count or 0) + 1
        session.commit()

        logger.info("=== 步骤8：记录系统日志 ===")
        log = SystemLog(
            operation='PRINT_RECEIPT',
            operator_id=current_user['id'],
            log_type='exchange',
            action=f"打印交易票据 {transaction.transaction_no}",
            details=f"文件: {transaction.receipt_filename}, 打印次数: {transaction.print_count}",
            ip_address=request.remote_addr,
            created_at=datetime.now()
        )
        session.add(log)
        session.commit()

        logger.info("=== 票据生成成功 ===")
        return jsonify({
            'success': True,
            'message': '票据生成成功',
            'transaction_no': transaction.transaction_no,
            'file_path': file_path,
            'pdf_base64': pdf_content,
            'print_count': transaction.print_count
        })

    except Exception as exc:
        logger.error("Print receipt failed: %s", str(exc))
        import traceback
        logger.error("详细错误信息: %s", traceback.format_exc())
        session.rollback()
        return jsonify({'success': False, 'message': str(exc)}), 500
    finally:
        DatabaseService.close_session(session)


@exchange_bp.route('/transactions/<transaction_no>/download-receipt', methods=['GET'])
@token_required
@has_permission('transaction_execute')
def download_receipt(*args, transaction_no):
    """下载交易票据PDF"""
    current_user = args[0] if args else None
    if not current_user:
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401

    session = DatabaseService.get_session()
    try:
        transaction = session.query(ExchangeTransaction).filter_by(
            transaction_no=transaction_no,
            branch_id=current_user['branch_id']
        ).first()

        if not transaction:
            return jsonify({'success': False, 'message': '交易记录不存在'}), 404

        if not transaction.receipt_filename:
            return jsonify({'success': False, 'message': '交易尚未生成票据'}), 400

        from services.simple_pdf_service import SimplePDFService
        file_path = SimplePDFService.get_receipt_file_path(
            transaction.transaction_no,
            transaction.transaction_date
        )

        if not os.path.exists(file_path):
            return jsonify({'success': False, 'message': '票据文件不存在'}), 404

        return send_file(
            file_path,
            as_attachment=True,
            download_name=transaction.receipt_filename,
            mimetype='application/pdf'
        )

    except Exception as exc:
        logger.error("Download receipt failed: %s", str(exc))
        return jsonify({'success': False, 'message': str(exc)}), 500
    finally:
        DatabaseService.close_session(session)


@exchange_bp.route('/business-group/<business_group_id>/print-receipt', methods=['POST'])
@token_required
@has_permission('transaction_execute')
def print_dual_direction_receipt(*args, **kwargs):
    """生成并打印双向交易业务组PDF票据"""
    # 修复参数顺序问题：从装饰器获取current_user，从路径获取business_group_id
    current_user = args[0] if len(args) > 0 else kwargs.get('current_user')
    business_group_id = args[1] if len(args) > 1 else kwargs.get('business_group_id')

    logger.info("=== 开始打印双向交易票据 ===")
    logger.info("business_group_id: %s", business_group_id)
    logger.info("current_user: %s", current_user)

    if not current_user:
        logger.error("用户信息获取失败")
        return jsonify({'success': False, 'message': '用户信息获取失败'}), 401

    if not business_group_id:
        logger.error("业务组ID参数缺失")
        return jsonify({'success': False, 'message': '业务组ID参数缺失'}), 400

    # 获取请求数据，包括语言参数
    request_data = request.get_json() or {}
    language = request_data.get('language', 'zh')  # 默认中文
    logger.info("请求语言: %s", language)

    session = DatabaseService.get_session()

    try:
        logger.info("=== 步骤1：获取业务组交易记录 ===")
        transactions = session.query(ExchangeTransaction).filter_by(
            business_group_id=business_group_id,
            branch_id=current_user['branch_id']
        ).order_by(ExchangeTransaction.group_sequence).all()

        if not transactions:
            logger.error(
                "业务组交易记录不存在: business_group_id=%s, branch_id=%s",
                business_group_id,
                current_user['branch_id'],
            )
            return jsonify({'success': False, 'message': '业务组交易记录不存在'}), 404

        logger.info("找到 %s 条交易记录", len(transactions))

        logger.info("=== 步骤2：获取相关信息 ===")
        first_transaction = transactions[0]

        currencies = {}
        for tx in transactions:
            if tx.currency_id not in currencies:
                currency = session.query(Currency).filter_by(id=tx.currency_id).first()
                if currency:
                    currencies[tx.currency_id] = currency

        branch = session.query(Branch).filter_by(id=first_transaction.branch_id).first()
        operator = session.query(Operator).filter_by(id=first_transaction.operator_id).first()

        logger.info("涉及币种数量: %s", len(currencies))
        logger.info("网点: %s", branch.branch_name if branch else 'None')
        logger.info("操作员: %s", operator.name if operator else 'None')

        logger.info("=== 步骤3：构建业务组数据 ===")
        business_group_data = {
            'business_group_id': business_group_id,
            'branch_id': current_user['branch_id'],
            'operator_id': first_transaction.operator_id,
            'transaction_date': first_transaction.transaction_date,
            'transaction_time': first_transaction.transaction_time,
            'customer_info': {
                'name': first_transaction.customer_name or '',
                'id_number': first_transaction.customer_id or '',
                'country_code': getattr(first_transaction, 'customer_country_code', '') or '',
                'address': getattr(first_transaction, 'customer_address', '') or '',
                'remarks': first_transaction.remarks or ''
            },
            'payment_method': getattr(first_transaction, 'payment_method', 'cash') or 'cash',
            'payment_method_note': getattr(first_transaction, 'payment_method_note', '') or '',
            'transactions': [],
            'denomination_details': []
        }

        for tx in transactions:
            currency = currencies.get(tx.currency_id)
            currency_code = currency.currency_code if currency else 'UNKNOWN'

            business_group_data['transactions'].append({
                'id': tx.id,
                'transaction_no': tx.transaction_no,
                'currency_id': tx.currency_id,
                'currency_code': currency_code,
                'direction': getattr(tx, 'transaction_direction', 'sell') or 'sell',
                'amount': tx.amount,
                'local_amount': tx.local_amount,
                'rate': tx.rate,
                'type': tx.type
            })

        for tx in transactions:
            currency = currencies.get(tx.currency_id)
            if currency:
                business_group_data['denomination_details'].append({
                    'denomination_value': abs(float(tx.amount)),
                    'denomination_type': 'bill',
                    'quantity': 1,
                    'direction': getattr(tx, 'transaction_direction', 'sell') or 'sell',
                    'currency_code': currency.currency_code,
                    'subtotal': abs(float(tx.amount))
                })

        logger.info(
            "业务组数据准备完成: %s 条交易, %s 个面值详情",
            len(business_group_data['transactions']),
            len(business_group_data['denomination_details']),
        )

        logger.info("=== 步骤4：生成PDF ===")
        try:
            from services.simple_pdf_service import SimplePDFService

            pdf_content = SimplePDFService.generate_dual_direction_receipt(
                business_group_data,
                session,
                language
            )

            logger.info("双向交易PDF生成成功")
            success = True

        except Exception as pdf_error:
            logger.error("PDF生成过程中发生异常: %s", str(pdf_error))
            import traceback
            logger.error("PDF生成异常详情: %s", traceback.format_exc())
            return jsonify({'success': False, 'message': f'PDF生成异常: {str(pdf_error)}'}), 500

        if not success:
            logger.error("PDF生成失败")
            return jsonify({'success': False, 'message': 'PDF生成失败'}), 500

        logger.info("=== 步骤5：生成文件路径 ===")
        from services.simple_pdf_service import SimplePDFService

        file_path = SimplePDFService.get_receipt_file_path(
            f"{first_transaction.transaction_no}_MULTI",
            first_transaction.transaction_date
        )

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'wb') as file_obj:
            file_obj.write(base64.b64decode(pdf_content))

        logger.info("PDF文件已保存到: %s", file_path)

        logger.info("=== 步骤6：记录系统日志 ===")
        log = SystemLog(
            operation='PRINT_DUAL_RECEIPT',
            operator_id=current_user['id'],
            log_type='exchange',
            action=f"打印双向交易票据 {business_group_id}",
            details=f"业务组包含 {len(transactions)} 条交易记录，文件: {os.path.basename(file_path)}",
            ip_address=request.remote_addr,
            created_at=datetime.now()
        )
        session.add(log)

        session.commit()

        logger.info("=== 双向交易票据生成成功 ===")

        messages = {
            'zh': f'双向交易票据生成成功，业务组: {business_group_id}',
            'en': f'Dual-direction transaction receipt generated successfully, Group: {business_group_id}',
            'th': f'สร้างใบเสร็จธุรกรรมสองทิศทางสำเร็จ กลุ่ม: {business_group_id}'
        }
        success_message = messages.get(language, messages['zh'])

        return jsonify({
            'success': True,
            'message': success_message,
            'business_group_id': business_group_id,
            'transaction_count': len(transactions),
            'file_path': file_path,
            'pdf_base64': pdf_content
        })

    except Exception as exc:
        logger.error("Print dual direction receipt failed: %s", str(exc))
        import traceback
        logger.error("详细错误信息: %s", traceback.format_exc())
        session.rollback()
        return jsonify({'success': False, 'message': str(exc)}), 500
    finally:
        DatabaseService.close_session(session)
