import json
import re
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session


class ReportDataService:
    """报告数据服务类"""

    @staticmethod
    def save_reservation(
        db_session: Session,
        reservation_data: Dict[str, Any]
    ) -> int:
        """
        保存预约兑换记录

        Args:
            db_session: 数据库会话
            reservation_data: 预约数据，必须包含:
                - customer_id: 客户证件号
                - customer_name: 客户姓名
                - currency_id: 外币ID
                - direction: 方向 (buy/sell)
                - amount: 外币金额
                - local_amount: 本币金额
                - rate: 汇率
                - trigger_type: 触发类型 (CTR/ATR/STR)
                - report_type: 报告类型
                - form_data: 表单数据（JSON）
                - branch_id: 网点ID
                - operator_id: 操作员ID

        Returns:
            预约ID
        """
        try:
            # 优先使用前端已生成的报告编号（包含币种代码）
            form_data = reservation_data.get('form_data', {})

            # form_data可能是dict或JSON字符串
            if isinstance(form_data, str):
                try:
                    form_data = json.loads(form_data)
                except:
                    form_data = {}

            reservation_no = form_data.get('report_number')

            if reservation_no:
                print(f"[ReportDataService] 使用前端已生成的报告编号: {reservation_no}")
            else:
                # 如果前端没有提供，使用新的ReportNumberGenerator生成
                print(f"[ReportDataService] 前端未提供报告编号，使用ReportNumberGenerator生成...")
                print(f"[ReportDataService] form_data keys: {list(form_data.keys()) if isinstance(form_data, dict) else 'NOT_A_DICT'}")

                from services.report_number_generator import ReportNumberGenerator

                # 获取币种代码
                currency_code = reservation_data.get('currency_code')
                if not currency_code:
                    # 从currency_id查询币种代码
                    currency_id = reservation_data.get('currency_id')
                    if currency_id:
                        currency_query = text("SELECT code FROM currencies WHERE id = :currency_id")
                        result = db_session.execute(currency_query, {'currency_id': currency_id}).fetchone()
                        if result:
                            currency_code = result[0]

                if not currency_code:
                    currency_code = 'USD'  # 默认币种

                # 使用新的ReportNumberGenerator生成
                reservation_no = ReportNumberGenerator.generate_amlo_report_number(
                    session=db_session,
                    branch_id=reservation_data.get('branch_id'),
                    currency_code=currency_code,
                    operator_id=reservation_data.get('operator_id'),
                    transaction_id=reservation_data.get('transaction_id')
                )
                print(f"[ReportDataService] 使用ReportNumberGenerator生成的报告编号: {reservation_no}")

            # 准备SQL插入
            sql = text("""
                INSERT INTO Reserved_Transaction (
                    reservation_no,
                    customer_id,
                    customer_name,
                    customer_country_code,
                    currency_id,
                    direction,
                    amount,
                    local_amount,
                    rate,
                    trigger_type,
                    report_type,
                    form_data,
                    denomination_data,
                    exchange_type,
                    funding_source,
                    asset_details,
                    status,
                    branch_id,
                    operator_id,
                    created_at
                ) VALUES (
                    :reservation_no,
                    :customer_id,
                    :customer_name,
                    :customer_country_code,
                    :currency_id,
                    :direction,
                    :amount,
                    :local_amount,
                    :rate,
                    :trigger_type,
                    :report_type,
                    :form_data,
                    :denomination_data,
                    :exchange_type,
                    :funding_source,
                    :asset_details,
                    'pending',
                    :branch_id,
                    :operator_id,
                    NOW()
                )
            """)

            # 准备参数
            params = {
                'reservation_no': reservation_no,
                'customer_id': reservation_data['customer_id'],
                'customer_name': reservation_data['customer_name'],
                'customer_country_code': reservation_data.get('customer_country_code', 'TH'),
                'currency_id': reservation_data['currency_id'],
                'direction': reservation_data['direction'],
                'amount': reservation_data['amount'],
                'local_amount': reservation_data['local_amount'],
                'rate': reservation_data['rate'],
                'trigger_type': reservation_data['trigger_type'],
                'report_type': reservation_data['report_type'],
                'form_data': json.dumps(reservation_data.get('form_data', {}), ensure_ascii=False),
                'denomination_data': json.dumps(reservation_data.get('denomination_data', {}), ensure_ascii=False),
                'exchange_type': reservation_data.get('exchange_type', 'large_amount'),
                'funding_source': reservation_data.get('funding_source'),
                'asset_details': reservation_data.get('asset_details'),
                'branch_id': reservation_data['branch_id'],
                'operator_id': reservation_data['operator_id']
            }

            print(f"[DEBUG] 保存预约记录 - reservation_no: {params['reservation_no']}")
            print(f"[DEBUG] 保存预约记录 - branch_id: {params['branch_id']}")
            print(f"[DEBUG] 保存预约记录 - customer_id: {params['customer_id']}")
            print(f"[DEBUG] 保存预约记录 - report_type: {params['report_type']}")
            print(f"[DEBUG] 保存预约记录 - status: pending")

            result = db_session.execute(sql, params)
            db_session.commit()

            # 获取插入的ID
            reservation_id = result.lastrowid

            print(f"[DEBUG] 预约记录保存成功 - reservation_id: {reservation_id}")

            return reservation_id

        except Exception as e:
            db_session.rollback()
            print(f"Error saving reservation: {str(e)}")
            raise

    # ========== 旧的报告编号生成方法已删除 ==========
    # 统一使用 ReportNumberGenerator (src/services/report_number_generator.py)
    # 移除的方法:
    # - _sanitize_code
    # - _fetch_branch_codes
    # - _next_report_sequence
    # - _generate_reservation_no

    @staticmethod
    def update_reservation_status(
        db_session: Session,
        reservation_id: int,
        status: str,
        **kwargs
    ) -> bool:
        """
        更新预约状态

        Args:
            db_session: 数据库会话
            reservation_id: 预约ID
            status: 新状态 (pending/approved/rejected/completed/reported)
            **kwargs: 其他要更新的字段
                - auditor_id: 审核人ID
                - rejection_reason: 驳回原因
                - remarks: 备注

        Returns:
            是否成功
        """
        try:
            # 构建更新字段
            update_fields = ['status = :status']
            params = {'reservation_id': reservation_id, 'status': status}

            if status == 'approved':
                update_fields.append('audit_time = NOW()')
                if 'auditor_id' in kwargs:
                    update_fields.append('auditor_id = :auditor_id')
                    params['auditor_id'] = kwargs['auditor_id']

            elif status == 'rejected':
                update_fields.append('audit_time = NOW()')
                if 'auditor_id' in kwargs:
                    update_fields.append('auditor_id = :auditor_id')
                    params['auditor_id'] = kwargs['auditor_id']
                if 'rejection_reason' in kwargs:
                    update_fields.append('rejection_reason = :rejection_reason')
                    params['rejection_reason'] = kwargs['rejection_reason']

            elif status == 'completed':
                update_fields.append('complete_time = NOW()')
                if 'linked_transaction_id' in kwargs:
                    update_fields.append('linked_transaction_id = :linked_transaction_id')
                    params['linked_transaction_id'] = kwargs['linked_transaction_id']

            elif status == 'reported':
                update_fields.append('report_time = NOW()')
                if 'reporter_id' in kwargs:
                    update_fields.append('reporter_id = :reporter_id')
                    params['reporter_id'] = kwargs['reporter_id']

            if 'remarks' in kwargs:
                update_fields.append('remarks = :remarks')
                params['remarks'] = kwargs['remarks']

            # 执行更新
            sql = text(f"""
                UPDATE Reserved_Transaction
                SET {', '.join(update_fields)}
                WHERE id = :reservation_id
            """)

            db_session.execute(sql, params)
            db_session.commit()

            return True

        except Exception as e:
            db_session.rollback()
            print(f"Error updating reservation status: {str(e)}")
            return False

    @staticmethod
    def get_reservation_by_id(
        db_session: Session,
        reservation_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        根据ID获取预约记录

        Args:
            db_session: 数据库会话
            reservation_id: 预约ID

        Returns:
            预约记录字典，如果不存在返回None
        """
        try:
            sql = text("""
                SELECT * FROM Reserved_Transaction
                WHERE id = :reservation_id
            """)

            result = db_session.execute(sql, {'reservation_id': reservation_id})
            row = result.first()

            if row:
                reservation_dict = dict(row._mapping)

                # 解析form_data JSON
                if reservation_dict.get('form_data'):
                    try:
                        reservation_dict['form_data'] = json.loads(reservation_dict['form_data'])
                    except:
                        reservation_dict['form_data'] = {}

                return reservation_dict

            return None

        except Exception as e:
            print(f"Error getting reservation {reservation_id}: {str(e)}")
            return None

    @staticmethod
    def save_amlo_report(
        db_session: Session,
        report_data: Dict[str, Any]
    ) -> int:
        """
        保存AMLO报告记录

        Args:
            db_session: 数据库会话
            report_data: 报告数据

        Returns:
            报告ID
        """
        try:
            report_no = report_data.get('report_number')
            reserved_id = report_data.get('reserved_id')

            if not report_no and reserved_id:
                reserved_record = ReportDataService.get_reservation_by_id(db_session, reserved_id)
                if reserved_record and reserved_record.get('reservation_no'):
                    report_no = reserved_record['reservation_no']

            if not report_no:
                # 使用新的报告编号生成器
                from services.report_number_generator import ReportNumberGenerator
                
                # 获取币种代码
                currency_code = report_data.get('currency_code', 'USD')
                if not currency_code or len(currency_code) != 3:
                    currency_code = 'USD'  # 默认币种
                
                # 生成新的AMLO报告编号
                report_no = ReportNumberGenerator.generate_amlo_report_number(
                    session=db_session,
                    branch_id=report_data.get('branch_id'),
                    currency_code=currency_code,
                    operator_id=report_data.get('operator_id'),
                    transaction_id=report_data.get('transaction_id')
                )

            sql = text("""
                INSERT INTO AMLOReport (
                    report_no,
                    report_type,
                    report_format,
                    reserved_id,
                    transaction_id,
                    customer_id,
                    customer_name,
                    transaction_amount,
                    transaction_date,
                    pdf_filename,
                    pdf_path,
                    is_reported,
                    branch_id,
                    operator_id,
                    language,
                    created_at
                ) VALUES (
                    :report_no,
                    :report_type,
                    :report_format,
                    :reserved_id,
                    :transaction_id,
                    :customer_id,
                    :customer_name,
                    :transaction_amount,
                    :transaction_date,
                    :pdf_filename,
                    :pdf_path,
                    FALSE,
                    :branch_id,
                    :operator_id,
                    :language,
                    NOW()
                )
            """)

            params = {
                'report_no': report_no,
                'report_type': report_data['report_type'],
                'report_format': report_data.get('report_format', report_data['report_type']),
                'reserved_id': report_data.get('reserved_id'),
                'transaction_id': report_data.get('transaction_id'),
                'customer_id': report_data['customer_id'],
                'customer_name': report_data['customer_name'],
                'transaction_amount': report_data['transaction_amount'],
                'transaction_date': report_data['transaction_date'],
                'pdf_filename': report_data['pdf_filename'],
                'pdf_path': report_data['pdf_path'],
                'branch_id': report_data['branch_id'],
                'operator_id': report_data['operator_id'],
                'language': report_data.get('language', 'th')
            }

            result = db_session.execute(sql, params)
            db_session.commit()

            return result.lastrowid

        except Exception as e:
            db_session.rollback()
            print(f"Error saving AMLO report: {str(e)}")
            raise

    @staticmethod
    def _generate_report_no(
        db_session: Session,
        branch_id: int,
        report_type: str
    ) -> str:
        """
        生成报告编号
        格式: AMLO-YYYY-MMDD-XXX (所有类型共用序号)

        Args:
            db_session: 数据库会话
            branch_id: 网点ID
            report_type: 报告类型

        Returns:
            报告编号
        """
        try:
            today_str = datetime.now().strftime('%Y-%m%d')

            # 查询今天该网点所有类型报告的数量，共用序号
            sql = text("""
                SELECT COUNT(*) FROM AMLOReport
                WHERE DATE(created_at) = CURDATE()
                    AND branch_id = :branch_id
            """)

            result = db_session.execute(
                sql,
                {'branch_id': branch_id}
            )

            count = result.scalar() or 0
            next_seq = count + 1

            return f"AMLO-{today_str}-{next_seq:03d}"

        except:
            return f"AMLO-{today_str}-{datetime.now().microsecond:03d}"
