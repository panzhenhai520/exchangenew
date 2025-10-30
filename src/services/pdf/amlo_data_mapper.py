# -*- coding: utf-8 -*-
"""
AMLO业务数据到PDF字段映射服务
根据CSV中的nearby_th_label标注，将业务数据映射到PDF表单字段

支持的报告类型:
- AMLO-1-01 (CTR - 现金交易报告)
- AMLO-1-02 (ATR - 资产交易报告)
- AMLO-1-03 (STR - 可疑交易报告)
"""

import os
import re
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

try:
    from .amlo_csv_field_loader import get_csv_field_loader
except ImportError:
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from amlo_csv_field_loader import get_csv_field_loader


class AMLODataMapper:
    """AMLO业务数据映射器"""

    def __init__(self):
        """初始化映射器"""
        self.csv_loader = get_csv_field_loader()
        print("[AMLODataMapper] Initialized")

    def map_reservation_to_pdf_fields(
        self,
        report_type: str,
        reservation_data: Dict[str, Any],
        form_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        将预约数据映射到PDF表单字段

        Args:
            report_type: 报告类型 ('AMLO-1-01', 'AMLO-1-02', 'AMLO-1-03')
            reservation_data: 预约记录数据 (来自Reserved_Transaction表)
            form_data: 表单JSON数据 (来自form_data字段)

        Returns:
            PDF字段字典 {field_name: value}
        """
        if report_type == 'AMLO-1-01':
            return self._map_101_fields(reservation_data, form_data)
        elif report_type == 'AMLO-1-02':
            return self._map_102_fields(reservation_data, form_data)
        elif report_type == 'AMLO-1-03':
            return self._map_103_fields(reservation_data, form_data)
        else:
            raise ValueError(f"Unsupported report type: {report_type}")

    def _map_101_fields(self, reservation_data: Dict, form_data: Dict) -> Dict:
        """映射AMLO-1-01 (CTR) 字段"""
        pdf_fields = {}

        # 报告编号 (fill_52)
        report_number = reservation_data.get('reservation_no') or form_data.get('report_number', '')
        pdf_fields['fill_52'] = report_number

        # 报告类型 (Check Box2=原报告, Check Box3=修订报告)
        is_amendment = self._normalize_bool(form_data.get('is_amendment_report'))
        pdf_fields['Check Box2'] = not is_amendment  # 原报告
        pdf_fields['Check Box3'] = is_amendment  # 修订报告

        if is_amendment:
            # 修订次数 (fill_3)
            pdf_fields['fill_3'] = form_data.get('amendment_count', '1')
            # 修订日期 (fill_1)
            pdf_fields['fill_1'] = self._format_date(form_data.get('amendment_date'))

        # 总页数 (fill_2)
        pdf_fields['fill_2'] = form_data.get('total_pages', '1')

        # ===== 第1部分: 交易办理人信息 =====

        # 身份证号 (comb_1)
        maker_id = form_data.get('maker_id_number') or reservation_data.get('customer_id', '')
        pdf_fields['comb_1'] = maker_id

        # 姓名 (fill_4)
        maker_name = self._combine_name(form_data, 'maker', reservation_data.get('customer_name', ''))
        pdf_fields['fill_4'] = maker_name

        # 办理方式 (Check Box4=本人办理, Check Box5=代理办理)
        is_proxy = self._normalize_bool(form_data.get('maker_is_proxy'))
        pdf_fields['Check Box4'] = not is_proxy
        pdf_fields['Check Box5'] = is_proxy

        # 地址 (fill_5, fill_5_2)
        maker_address = self._combine_address(form_data, 'maker_address')
        if not maker_address:
            maker_address = reservation_data.get('customer_address', '')
        # 分割地址到两个字段
        addr_parts = self._split_text(maker_address, 80)
        pdf_fields['fill_5'] = addr_parts[0] if len(addr_parts) > 0 else ''
        if len(addr_parts) > 1:
            pdf_fields['fill_5_2'] = addr_parts[1]

        # 电话 (fill_7)
        pdf_fields['fill_7'] = form_data.get('maker_phone') or form_data.get('maker_mobile', '')

        # 传真 (fill_8)
        pdf_fields['fill_8'] = form_data.get('maker_fax', '')

        # 职业 (fill_9)
        pdf_fields['fill_9'] = form_data.get('maker_occupation') or form_data.get('maker_occupation_type', '')

        # 工作单位 (fill_10)
        pdf_fields['fill_10'] = form_data.get('maker_occupation_employer', '')

        # 工作单位电话 (fill_11)
        pdf_fields['fill_11'] = form_data.get('maker_work_phone', '')

        # 联系地址 (fill_12, fill_13)
        contact_address = form_data.get('maker_contact_address', '')
        if contact_address:
            addr_parts = self._split_text(contact_address, 80)
            pdf_fields['fill_12'] = addr_parts[0] if len(addr_parts) > 0 else ''
            if len(addr_parts) > 1:
                pdf_fields['fill_13'] = addr_parts[1]

        # 联系地址电话 (fill_14)
        pdf_fields['fill_14'] = form_data.get('maker_contact_phone', '')

        # 联系地址传真 (fill_15)
        pdf_fields['fill_15'] = form_data.get('maker_contact_fax', '')

        # 证件类型 (Check Box6-9)
        id_type = form_data.get('maker_id_type', 'id_card')
        pdf_fields['Check Box6'] = (id_type == 'id_card')  # 身份证
        pdf_fields['Check Box7'] = (id_type == 'passport')  # 护照
        pdf_fields['Check Box8'] = (id_type == 'alien_cert')  # 外国人证
        pdf_fields['Check Box9'] = (id_type == 'other')  # 其他

        if id_type == 'other':
            pdf_fields['fill_6'] = form_data.get('maker_id_type_other', '')

        # 证件号码 (fill_16)
        pdf_fields['fill_16'] = maker_id

        # 签发机构 (fill_17)
        pdf_fields['fill_17'] = form_data.get('maker_id_issued_by', '')

        # 签发日期 (fill_18)
        pdf_fields['fill_18'] = self._format_date(form_data.get('maker_id_issued_date'))

        # 过期日期 (fill_19)
        pdf_fields['fill_19'] = self._format_date(form_data.get('maker_id_expiry_date'))

        # ===== 第2部分: 共同交易人/代理人信息 =====

        has_joint_party = self._normalize_bool(form_data.get('has_joint_party'))
        # 检查是否有实际的共同交易人数据（姓名或身份证）
        has_joint_data = bool(
            form_data.get('joint_party_name') or
            form_data.get('joint_party_id_number') or
            form_data.get('joint_party_first_name') or
            form_data.get('joint_party_last_name')
        )

        if has_joint_party or is_proxy or has_joint_data:
            print(f"[AMLODataMapper] Processing joint party data (has_joint_party={has_joint_party}, has_joint_data={has_joint_data})")

            # 关系类型 (Check Box10-12)
            joint_type = form_data.get('joint_party_type', 'joint')
            pdf_fields['Check Box10'] = (joint_type == 'joint')  # 共同交易人
            pdf_fields['Check Box11'] = (joint_type == 'delegator')  # 委托人
            pdf_fields['Check Box12'] = (joint_type == 'agent')  # 代理人

            # 身份证号 (comb_2)
            joint_id = form_data.get('joint_party_id_number', '')
            pdf_fields['comb_2'] = joint_id
            print(f"[AMLODataMapper] Joint party ID (comb_2): {joint_id}")

            # 姓名 (fill_20)
            joint_name = self._combine_name(form_data, 'joint_party', form_data.get('joint_party_name', ''))
            pdf_fields['fill_20'] = joint_name
            print(f"[AMLODataMapper] Joint party name (fill_20): {joint_name}")

            # 地址 (fill_21, fill_22)
            joint_address = self._combine_address(form_data, 'joint_party_address')
            addr_parts = self._split_text(joint_address, 80)
            pdf_fields['fill_21'] = addr_parts[0] if len(addr_parts) > 0 else ''
            if len(addr_parts) > 1:
                pdf_fields['fill_22'] = addr_parts[1]
            print(f"[AMLODataMapper] Joint party address (fill_21/22): {joint_address[:50]}...")

            # 电话 (fill_23)
            pdf_fields['fill_23'] = form_data.get('joint_party_phone', '')

            # 传真 (fill_24)
            pdf_fields['fill_24'] = form_data.get('joint_party_fax', '')

            # 职业 (fill_25)
            pdf_fields['fill_25'] = form_data.get('joint_party_occupation', '')

            # 工作单位 (fill_26)
            pdf_fields['fill_26'] = form_data.get('joint_party_employer', '')

            # 工作单位电话 (fill_27)
            pdf_fields['fill_27'] = form_data.get('joint_party_work_phone', '')

            # 企业类型 (fill_28) - 如果是法人
            pdf_fields['fill_28'] = form_data.get('joint_party_business_type', '')

            # 联系地址 (fill_29, fill_30)
            joint_contact = form_data.get('joint_party_contact_address', '')
            if joint_contact:
                addr_parts = self._split_text(joint_contact, 80)
                pdf_fields['fill_29'] = addr_parts[0] if len(addr_parts) > 0 else ''
                if len(addr_parts) > 1:
                    pdf_fields['fill_30'] = addr_parts[1]

            # 联系地址电话 (fill_31)
            pdf_fields['fill_31'] = form_data.get('joint_party_contact_phone', '')

            # 联系地址传真 (fill_32)
            pdf_fields['fill_32'] = form_data.get('joint_party_contact_fax', '')

            # 证件类型 (Check Box13-17)
            joint_id_type = form_data.get('joint_party_id_type', 'id_card')
            pdf_fields['Check Box13'] = (joint_id_type == 'id_card')
            pdf_fields['Check Box14'] = (joint_id_type == 'passport')
            pdf_fields['Check Box15'] = (joint_id_type == 'alien_cert')
            pdf_fields['Check Box16'] = (joint_id_type == 'registry')  # 登记证明
            pdf_fields['Check Box17'] = (joint_id_type == 'other')

            if joint_id_type == 'other':
                pdf_fields['fill_56'] = form_data.get('joint_party_id_type_other', '')

            # 证件号码 (fill_33)
            pdf_fields['fill_33'] = joint_id

            # 签发机构 (fill_34)
            pdf_fields['fill_34'] = form_data.get('joint_party_id_issued_by', '')

            # 签发日期 (fill_35)
            pdf_fields['fill_35'] = self._format_date(form_data.get('joint_party_id_issued_date'))

            # 过期日期 (fill_36)
            pdf_fields['fill_36'] = self._format_date(form_data.get('joint_party_id_expiry_date'))

        # ===== 第3部分: 交易信息 =====

        # 交易日期 (fill_37=日, fill_38=月, fill_39=年)
        transaction_date = self._parse_date(reservation_data.get('transaction_date')) or datetime.now()
        pdf_fields['fill_37'] = str(transaction_date.day)
        pdf_fields['fill_38'] = str(transaction_date.month)
        pdf_fields['fill_39'] = str(transaction_date.year + 543)  # 转换为佛历

        # 交易方向: 判断是买入还是卖出
        direction = reservation_data.get('direction', '').lower()

        # ⚠️ CRITICAL: direction字段已经是【网点视角】，无需转换
        # direction='buy'  = 网点买入外币 = 外币流入 = 左栏 (fill_48, fill_50)
        # direction='sell' = 网点卖出外币 = 外币流出 = 右栏 (fill_49, fill_51)

        is_buy = (direction == 'buy')    # 网点买入 = 左栏
        is_sell = (direction == 'sell')  # 网点卖出 = 右栏

        print(f"[AMLODataMapper] Direction (institution): {direction}")
        print(f"[AMLODataMapper] Mapping: buy={is_buy} (LEFT), sell={is_sell} (RIGHT)")

        # 左栏 - 外币流入（网点买入外币）
        if is_buy:
            local_amount = float(reservation_data.get('local_amount') or reservation_data.get('amount_thb') or 0)

            # 左栏金额 (fill_48)
            pdf_fields['fill_48'] = f"{local_amount:.2f}"
            # 左栏合计 (fill_50)
            pdf_fields['fill_50'] = f"{local_amount:.2f}"

            print(f"[AMLODataMapper] LEFT column (buy): fill_48/fill_50 = {local_amount:.2f}")

            # 存款 (Check Box18)
            pdf_fields['Check Box18'] = False

            # 存入账号 (comb_3)
            pdf_fields['comb_3'] = form_data.get('account_number', '')

            # 关联账号 (comb_5)
            pdf_fields['comb_5'] = form_data.get('related_account', '')

            # 买入票据 (Check Box19-22)
            instrument_type = form_data.get('instrument_type', 'none')
            pdf_fields['Check Box19'] = (instrument_type in ['check', 'draft', 'other_instrument'])
            pdf_fields['Check Box20'] = (instrument_type == 'check')
            pdf_fields['Check Box21'] = (instrument_type == 'draft')
            pdf_fields['Check Box22'] = (instrument_type == 'other_instrument')

            if instrument_type == 'other_instrument':
                pdf_fields['fill_40'] = form_data.get('instrument_type_other', '')

            # 买入外币 (Check Box23) - 左栏
            pdf_fields['Check Box23'] = True

            # 外币币种 (fill_42 - 左栏币种说明)
            currency_code = reservation_data.get('currency_code') or form_data.get('currency_code', '')
            pdf_fields['fill_42'] = currency_code
            if currency_code:
                pdf_fields['fill42_2'] = f"({currency_code})"

            # 其他交易 (Check Box24)
            has_other_tx = self._normalize_bool(form_data.get('has_other_transaction'))
            pdf_fields['Check Box24'] = has_other_tx
            if has_other_tx:
                pdf_fields['fill42_2'] = form_data.get('other_transaction_desc', '')

        # 右栏 - 外币流出（网点卖出外币）
        elif is_sell:
            local_amount = float(reservation_data.get('local_amount') or reservation_data.get('amount_thb') or 0)

            # 右栏金额 (fill_49)
            pdf_fields['fill_49'] = f"{local_amount:.2f}"
            # 右栏合计 (fill_51)
            pdf_fields['fill_51'] = f"{local_amount:.2f}"

            print(f"[AMLODataMapper] RIGHT column (sell): fill_49/fill_51 = {local_amount:.2f}")

            # 取款 (Check Box25) - 右栏
            pdf_fields['Check Box25'] = False

            # 取款账号 (comb_4)
            pdf_fields['comb_4'] = form_data.get('account_number', '')

            # 关联账号 (comb_6)
            pdf_fields['comb_6'] = form_data.get('related_account', '')

            # 卖出票据 (Check Box26-29)
            instrument_type = form_data.get('instrument_type', 'none')
            pdf_fields['Check Box26'] = (instrument_type in ['check', 'draft', 'other_instrument'])
            pdf_fields['Check Box27'] = (instrument_type == 'check')
            pdf_fields['Check Box28'] = (instrument_type == 'draft')
            pdf_fields['Check Box29'] = (instrument_type == 'other_instrument')

            if instrument_type == 'other_instrument':
                pdf_fields['fill_41'] = form_data.get('instrument_type_other', '')

            # 卖出外币 (Check Box30)
            pdf_fields['Check Box30'] = True

            # 外币币种
            currency_code = reservation_data.get('currency_code') or form_data.get('currency_code', '')
            pdf_fields['fill_43'] = currency_code
            if currency_code:
                pdf_fields['fill_43_2'] = f"({currency_code})"

            # 其他交易 (Check Box31)
            has_other_tx = self._normalize_bool(form_data.get('has_other_transaction'))
            pdf_fields['Check Box31'] = has_other_tx
            if has_other_tx:
                pdf_fields['fill43_2'] = form_data.get('other_transaction_desc', '')

        # 受益人 (fill_46)
        beneficiary = form_data.get('beneficiary_name', '')
        if not beneficiary:
            beneficiary = form_data.get('joint_party_name', '')
        pdf_fields['fill_46'] = beneficiary

        # 交易目的 (fill_47)
        purpose = form_data.get('transaction_purpose') or form_data.get('exchange_purpose', '')
        pdf_fields['fill_47'] = purpose

        # ===== 第4部分: 签名区域 =====

        # 机构记录事实 (Check Box32)
        pdf_fields['Check Box32'] = self._normalize_bool(form_data.get('institution_records_fact'))

        # 客户未签名 (Check Box33)
        pdf_fields['Check Box33'] = self._normalize_bool(form_data.get('customer_no_signature'))

        return pdf_fields

    def _map_102_fields(self, reservation_data: Dict, form_data: Dict) -> Dict:
        """映射AMLO-1-02 (ATR) 字段"""
        # TODO: 实现1-02表单映射
        # 资产交易报告字段映射逻辑类似101,但关注资产类型
        return {}

    def _map_103_fields(self, reservation_data: Dict, form_data: Dict) -> Dict:
        """映射AMLO-1-03 (STR) 字段"""
        # TODO: 实现1-03表单映射
        # 可疑交易报告字段映射逻辑类似101
        return {}

    # ===== 辅助方法 =====

    def _normalize_bool(self, value: Any) -> bool:
        """规范化布尔值"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in ('1', 'true', 'yes', 'y', 'on')
        if isinstance(value, (int, float)):
            return value != 0
        return False

    def _combine_name(self, form_data: Dict, prefix: str, fallback: str = '') -> str:
        """组合姓名"""
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

    def _combine_address(self, form_data: Dict, prefix: str) -> str:
        """组合地址"""
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

    def _format_date(self, date_value: Any) -> str:
        """格式化日期为 DD/MM/YYYY"""
        if not date_value:
            return ''

        if isinstance(date_value, datetime):
            return date_value.strftime('%d/%m/%Y')

        if isinstance(date_value, str):
            # 尝试解析字符串
            try:
                dt = datetime.strptime(date_value, '%Y-%m-%d')
                return dt.strftime('%d/%m/%Y')
            except:
                return date_value

        return str(date_value)

    def _parse_date(self, date_value: Any) -> Optional[datetime]:
        """解析日期"""
        if isinstance(date_value, datetime):
            return date_value

        if isinstance(date_value, str):
            try:
                return datetime.strptime(date_value, '%Y-%m-%d')
            except:
                try:
                    return datetime.strptime(date_value, '%d/%m/%Y')
                except:
                    pass

        return None

    def _split_text(self, text: str, max_len: int = 80) -> list:
        """分割长文本"""
        if not text or len(text) <= max_len:
            return [text] if text else []

        parts = []
        while text:
            parts.append(text[:max_len])
            text = text[max_len:]

        return parts


# 测试代码
if __name__ == '__main__':
    mapper = AMLODataMapper()

    # 测试数据
    reservation_data = {
        'reservation_no': 'FI-001-68-001',
        'customer_id': '1234567890123',
        'customer_name': 'นายสมชาย ใจดี',
        'customer_address': '123 ถนนสุขุมวิท แขวงคลองเตย เขตคลองเตย กรุงเทพมหานคร 10110',
        'direction': 'buy',  # 买入外币
        'currency_code': 'USD',
        'local_amount': 2500000,  # THB
        'amount': 75000,  # USD
        'transaction_date': datetime(2025, 10, 18)
    }

    form_data = {
        'maker_phone': '02-1234567',
        'maker_occupation': 'ธุรกิจส่วนตัว',
        'maker_id_type': 'id_card',
        'transaction_purpose': 'เพื่อการท่องเที่ยว',
        'is_amendment_report': False,
    }

    print("="*60)
    print("Testing AMLO-1-01 Data Mapping")
    print("="*60)

    pdf_fields = mapper.map_reservation_to_pdf_fields('AMLO-1-01', reservation_data, form_data)

    print(f"\nGenerated {len(pdf_fields)} PDF fields:")
    for key, value in sorted(pdf_fields.items())[:20]:
        print(f"  {key}: {value}")
