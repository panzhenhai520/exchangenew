# -*- coding: utf-8 -*-
"""
Utilities for mapping between PDF AcroForm field names and database fields.

The mapping is derived from the AMLO CSV definitions located under Re/*.csv
and is used when parsing user-uploaded editable PDFs back into structured data.
"""

# NOTE: This mapping was auto-generated from src/utils/amloFieldMapping.js

AMLO_101_FIELD_MAP = {'amendment_count': 'fill_3',
 'amendment_date': 'fill_1',
 'beneficiary_name': 'fill_46',
 'customer_no_signature': 'Check Box33',
 'deposit_account': 'comb_3',
 'deposit_cash': 'Check Box19',
 'deposit_check': 'Check Box20',
 'deposit_currency_amount': 'fill_48_5',
 'deposit_draft': 'Check Box21',
 'deposit_other_instrument': 'Check Box22',
 'deposit_other_text': 'fill_40',
 'deposit_related_account': 'comb_5',
 'deposit_thb_amount': 'fill_48',
 'deposit_total': 'fill_50',
 'exchange_buy_currency': 'Check Box23',
 'exchange_other_description': 'fill43_2',
 'exchange_other_transaction': 'Check Box31',
 'exchange_purpose': 'fill_47',
 'exchange_sell_currency': 'Check Box30',
 'foreign_currency_buy': 'fill_42',
 'foreign_currency_sell': 'fill_43',
 'has_joint_party': None,
 'institution_records_fact': 'Check Box32',
 'is_amendment_report': 'Check Box3',
 'is_first_report': 'Check Box2',
 'joint_party_address': 'fill_21',
 'joint_party_address_line2': 'fill_22',
 'joint_party_business_type': 'fill_28',
 'joint_party_contact_address': 'fill_29',
 'joint_party_contact_fax': 'fill_32',
 'joint_party_contact_phone': 'fill_31',
 'joint_party_employer': 'fill_26',
 'joint_party_fax': 'fill_24',
 'joint_party_id_expiry_date': 'fill_36',
 'joint_party_id_issued_by': 'fill_34',
 'joint_party_id_issued_date': 'fill_35',
 'joint_party_id_number': 'comb_2',
 'joint_party_id_type_alien_cert': 'Check Box15',
 'joint_party_id_type_id_card': 'Check Box13',
 'joint_party_id_type_other': 'Check Box17',
 'joint_party_id_type_other_text': 'fill_56',
 'joint_party_id_type_passport': 'Check Box14',
 'joint_party_id_type_registry': 'Check Box16',
 'joint_party_name': 'fill_20',
 'joint_party_occupation': 'fill_25',
 'joint_party_phone': 'fill_23',
 'joint_party_type_agent': 'Check Box12',
 'joint_party_type_delegator': 'Check Box11',
 'joint_party_type_joint': 'Check Box10',
 'joint_party_work_phone': 'fill_27',
 'left_amount': 'left_amount',
 'maker_address': 'fill_5',
 'maker_address_line1': 'fill_5',
 'maker_address_line2': 'fill_5_2',
 'maker_contact_address': 'fill_12',
 'maker_contact_fax': 'fill_15',
 'maker_contact_phone': 'fill_14',
 'maker_fax': 'fill_8',
 'maker_full_name': 'fill_4',
 'maker_id_expiry_date': 'fill_19',
 'maker_id_issued_by': 'fill_17',
 'maker_id_issued_date': 'fill_18',
 'maker_id_number': 'comb_1',
 'maker_id_type_alien_cert': 'Check Box8',
 'maker_id_type_id_card': 'Check Box6',
 'maker_id_type_other': 'Check Box9',
 'maker_id_type_other_text': 'fill_6',
 'maker_id_type_passport': 'Check Box7',
 'maker_is_proxy': 'Check Box5',
 'maker_name': 'fill_4',
 'maker_occupation': 'fill_9',
 'maker_occupation_employer': 'fill_10',
 'maker_phone': 'fill_7',
 'maker_transaction_by_self': 'Check Box4',
 'maker_transaction_on_behalf': 'Check Box5',
 'maker_work_phone': 'fill_11',
 'report_no': 'fill_52',
 'report_number': 'fill_52',
 'reporter_date': 'reporter_date',
 'reporter_signature': 'sig_reporter',
 'right_amount': 'right_amount',
 'total_pages': 'fill_2',
 'transaction_date_day': 'fill_37',
 'transaction_date_month': 'fill_38',
 'transaction_date_year': 'fill_39',
 'transaction_purpose': 'fill_47',
 'transactor_date': 'transactor_date',
 'transactor_signature': 'sig_transactor',
 'withdrawal_account': 'comb_4',
 'withdrawal_cash': 'Check Box25',
 'withdrawal_check': 'Check Box27',
 'withdrawal_currency_amount': 'fill_49_5',
 'withdrawal_draft': 'Check Box28',
 'withdrawal_other': 'Check Box29',
 'withdrawal_other_text': 'fill_41',
 'withdrawal_related_account': 'comb_6',
 'withdrawal_thb_amount': 'fill_49',
 'withdrawal_total': 'fill_51',
 'withdrawal_transfer': 'Check Box26'}

AMLO_101_PDF_TO_DB = {v: k for k, v in AMLO_101_FIELD_MAP.items() if v}

# AMLO-1-02 specific helper fields
AMLO_102_TRANSACTION_TYPE_FIELDS = {
    'Check Box50': 'mortgage',
    'Check Box51': 'sale',
    'Check Box52': 'transfer',
    'Check Box53': 'other'
}

AMLO_102_ASSET_TYPE_FIELDS = {
    'Check Box54': 'land',
    'Check Box55': 'land_building',
    'Check Box56': 'building',
    'Check Box57': 'other'
}

AMLO_102_ASSET_DETAIL_FIELDS = ['fill_38', 'fill_38_1', 'fill_38_2']

# AMLO-1-03 suspicious reason paragraph fields
AMLO_103_SUSPICIOUS_REASON_FIELDS = [f'm_{idx}' for idx in range(1, 14)]


def normalize_pdf_value(value):
    """Normalize PDF field values (checkbox states, whitespace, etc.)."""
    if isinstance(value, bool):
        return value
    if value is None:
        return ''
    if isinstance(value, (int, float)):
        return value
    text = str(value).strip()
    if text.lower() in ('yes', 'on', 'true'):
        return True
    if text.lower() in ('off', 'no', 'false'):
        return False
    return text


def map_pdf_fields_to_db(report_type, pdf_fields):
    """
    Convert PDF field dict (fill_*, Check Box*) to database field names as defined
    in AMLO_101_FIELD_MAP. Currently all AMLO-1-0X types share the base mapping.
    """
    mapping = AMLO_101_PDF_TO_DB
    result = {}
    for pdf_field, raw_value in pdf_fields.items():
        db_field = mapping.get(pdf_field)
        if not db_field:
            continue
        result[db_field] = normalize_pdf_value(raw_value)

    if report_type == 'AMLO-1-02':
        result.update(_map_amlo_102_special_fields(pdf_fields))
    elif report_type == 'AMLO-1-03':
        result.update(_map_amlo_103_special_fields(pdf_fields))

    return result


def _map_amlo_102_special_fields(pdf_fields):
    """Extract AMLO-1-02 specific fields such as asset types and values."""
    result = {}

    # Transaction type (single choice)
    for field_name, option_value in AMLO_102_TRANSACTION_TYPE_FIELDS.items():
        if normalize_pdf_value(pdf_fields.get(field_name)):
            result['asset_transaction_type'] = option_value
            break

    other_text = normalize_pdf_value(pdf_fields.get('fill_53'))
    if isinstance(other_text, str) and other_text.strip():
        result['asset_transaction_type_other_text'] = other_text.strip()

    # Asset type (single choice)
    for field_name, option_value in AMLO_102_ASSET_TYPE_FIELDS.items():
        if normalize_pdf_value(pdf_fields.get(field_name)):
            result['asset_type'] = option_value
            break

    asset_type_other = normalize_pdf_value(pdf_fields.get('fill_57'))
    if isinstance(asset_type_other, str) and asset_type_other.strip():
        result['asset_type_other_text'] = asset_type_other.strip()

    # Asset description (multi-line)
    detail_lines = []
    for field_name in AMLO_102_ASSET_DETAIL_FIELDS:
        text = normalize_pdf_value(pdf_fields.get(field_name))
        if isinstance(text, str):
            text = text.strip()
            if text:
                detail_lines.append(text)
    if detail_lines:
        result['asset_details'] = '\n'.join(detail_lines)

    # Asset value (THB)
    asset_value = normalize_pdf_value(pdf_fields.get('fill_41'))
    if isinstance(asset_value, (int, float)) or (isinstance(asset_value, str) and asset_value.strip()):
        result['asset_value'] = asset_value

    # Asset value (foreign currency)
    foreign_value = normalize_pdf_value(pdf_fields.get('fill_42'))
    if isinstance(foreign_value, str) and foreign_value.strip():
        result['asset_value_foreign'] = foreign_value.strip()

    # Asset value in words
    asset_value_text = normalize_pdf_value(pdf_fields.get('fill_66'))
    if isinstance(asset_value_text, str) and asset_value_text.strip():
        result['asset_value_text'] = asset_value_text.strip()

    return result


def _map_amlo_103_special_fields(pdf_fields):
    """Extract AMLO-1-03 specific fields such as suspicious reason blocks."""
    result = {}

    reason_lines = []
    for field_name in AMLO_103_SUSPICIOUS_REASON_FIELDS:
        value = normalize_pdf_value(pdf_fields.get(field_name))
        if isinstance(value, str):
            text = value.strip()
            if text:
                reason_lines.append(text)
    if reason_lines:
        result['suspicious_reason'] = '\n'.join(reason_lines)

    related_report = normalize_pdf_value(pdf_fields.get('fill_49'))
    if isinstance(related_report, str) and related_report.strip():
        result['related_report_number'] = related_report.strip()

    return result

