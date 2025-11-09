"""
AMLO Form Field Mapping Configuration
Maps database fields to Adobe PDF form fields for AMLO-1-01, AMLO-1-02, AMLO-1-03

Created: 2025-10-18
Version: 1.0
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Callable


class AMLOFieldMapper:
    """Maps database data to Adobe PDF form fields for AMLO reports"""

    @staticmethod
    def gregorian_to_buddhist_year(date_obj: datetime) -> int:
        """Convert Gregorian year to Buddhist Era year"""
        return date_obj.year + 543

    @staticmethod
    def split_into_boxes(text: str, box_count: int) -> Dict[str, str]:
        """
        Split a string into individual character boxes
        Example: "1234567890123" -> {customer_id_1: "1", customer_id_2: "2", ...}
        """
        result = {}
        text_str = str(text).strip()
        for i in range(box_count):
            if i < len(text_str):
                result[i + 1] = text_str[i]
            else:
                result[i + 1] = ""
        return result

    @staticmethod
    def thai_number_to_text(amount: Decimal) -> str:
        """
        Convert number to Thai text format
        Example: 2500000.00 -> "สองล้านห้าแสนบาทถ้วน"
        """
        # Thai digit names
        thai_digits = {
            0: "ศูนย์", 1: "หนึ่ง", 2: "สอง", 3: "สาม", 4: "สี่",
            5: "ห้า", 6: "หก", 7: "เจ็ด", 8: "แปด", 9: "เก้า"
        }

        # Thai place names
        thai_places = {
            1: "", 2: "สิบ", 3: "ร้อย", 4: "พัน", 5: "หมื่น", 6: "แสน",
            7: "ล้าน"
        }

        # Basic implementation - should be enhanced for production use
        # For now, return empty string as placeholder
        # TODO: Implement full Thai number conversion
        return f"{amount:,.2f} บาท"

    @staticmethod
    def format_date_buddhist(date_obj: datetime) -> Dict[str, int]:
        """
        Format date into Buddhist calendar components
        Returns: {day: DD, month: MM, year: YYYY (Buddhist)}
        """
        return {
            'day': date_obj.day,
            'month': date_obj.month,
            'year': date_obj.year + 543
        }


# AMLO-1-01 Field Mapping Configuration
AMLO_101_FIELD_MAPPING = {
    # Header Section
    'header': {
        'institution_code': {
            'source': 'branch.amlo_institution_code',
            'type': 'text_boxes',
            'box_count': 3,
            'prefix': 'institution_code_'
        },
        'branch_code': {
            'source': 'branch.amlo_branch_code',
            'type': 'text_boxes',
            'box_count': 3,
            'prefix': 'branch_code_'
        },
        'report_year': {
            'source': 'created_at',
            'type': 'text_boxes',
            'box_count': 2,
            'prefix': 'report_year_',
            'transform': lambda date: str((date.year + 543) % 100).zfill(2)
        },
        'report_sequence': {
            'source': 'reservation_no',
            'type': 'text',
            'field_name': 'report_sequence'
        },
        'report_type_original': {
            'source': 'static',
            'value': True,
            'type': 'checkbox',
            'field_name': 'report_type_original'
        },
        'report_type_amendment': {
            'source': 'static',
            'value': False,
            'type': 'checkbox',
            'field_name': 'report_type_amendment'
        }
    },

    # Section 1: Customer Information
    'section_1': {
        'customer_id': {
            'source': 'customer_id',
            'type': 'text_boxes',
            'box_count': 13,
            'prefix': 'customer_id_'
        },
        'customer_name': {
            'source': 'customer_name',
            'type': 'text',
            'field_name': 'customer_name'
        },
        'transaction_self': {
            'source': 'static',
            'value': True,
            'type': 'checkbox',
            'field_name': 'transaction_self'
        },
        'transaction_behalf': {
            'source': 'static',
            'value': False,
            'type': 'checkbox',
            'field_name': 'transaction_behalf'
        },
        'customer_address': {
            'source': 'customer_address',
            'type': 'text',
            'field_name': 'customer_address'
        },
        'customer_phone': {
            'source': 'customer_phone',
            'type': 'text',
            'field_name': 'customer_phone'
        },
        'customer_fax': {
            'source': 'customer_fax',
            'type': 'text',
            'field_name': 'customer_fax',
            'optional': True
        },
        'customer_occupation': {
            'source': 'customer_occupation',
            'type': 'text',
            'field_name': 'customer_occupation',
            'optional': True
        },
        'customer_workplace': {
            'source': 'customer_workplace',
            'type': 'text',
            'field_name': 'customer_workplace',
            'optional': True
        },
        'customer_work_phone': {
            'source': 'customer_work_phone',
            'type': 'text',
            'field_name': 'customer_work_phone',
            'optional': True
        },
        'id_type': {
            'source': 'id_type',
            'type': 'checkbox_group',
            'options': {
                'national': 'id_type_national',
                'passport': 'id_type_passport',
                'alien': 'id_type_alien',
                'other': 'id_type_other'
            }
        }
    },

    # Section 2: Co-Customer Information
    'section_2': {
        'co_customer_id': {
            'source': 'co_customer_id',
            'type': 'text_boxes',
            'box_count': 13,
            'prefix': 'co_customer_id_',
            'optional': True
        },
        'co_customer_name': {
            'source': 'co_customer_name',
            'type': 'text',
            'field_name': 'co_customer_name',
            'optional': True
        },
        'co_customer_address': {
            'source': 'co_customer_address',
            'type': 'text',
            'field_name': 'co_customer_address',
            'optional': True
        },
        'co_customer_phone': {
            'source': 'co_customer_phone',
            'type': 'text',
            'field_name': 'co_customer_phone',
            'optional': True
        }
    },

    # Section 3: Transaction Details
    'section_3': {
        'transaction_date': {
            'source': 'created_at',
            'type': 'date_fields',
            'fields': {
                'day': 'transaction_date_day',
                'month': 'transaction_date_month',
                'year': 'transaction_date_year'
            },
            'transform': 'buddhist_date'
        },
        'buy_foreign_currency': {
            'source': 'transaction_type',
            'type': 'checkbox',
            'field_name': 'buy_foreign_currency',
            'condition': lambda val: val == 'buy'
        },
        'sell_foreign_currency': {
            'source': 'transaction_type',
            'type': 'checkbox',
            'field_name': 'sell_foreign_currency',
            'condition': lambda val: val == 'sell'
        },
        'buy_foreign_currency_code': {
            'source': 'foreign_currency',
            'type': 'text',
            'field_name': 'buy_foreign_currency_code',
            'condition': lambda tx_type: tx_type == 'buy',
            'condition_field': 'transaction_type'
        },
        'sell_foreign_currency_code': {
            'source': 'foreign_currency',
            'type': 'text',
            'field_name': 'sell_foreign_currency_code',
            'condition': lambda tx_type: tx_type == 'sell',
            'condition_field': 'transaction_type'
        },
        'buy_total_amount': {
            'source': 'local_amount',
            'type': 'text',
            'field_name': 'buy_total_amount',
            'condition': lambda tx_type: tx_type == 'buy',
            'condition_field': 'transaction_type',
            'format': lambda val: f"{val:,.2f}"
        },
        'sell_total_amount': {
            'source': 'local_amount',
            'type': 'text',
            'field_name': 'sell_total_amount',
            'condition': lambda tx_type: tx_type == 'sell',
            'condition_field': 'transaction_type',
            'format': lambda val: f"{val:,.2f}"
        },
        'buy_total_amount_text': {
            'source': 'local_amount',
            'type': 'text',
            'field_name': 'buy_total_amount_text',
            'condition': lambda tx_type: tx_type == 'buy',
            'condition_field': 'transaction_type',
            'transform': 'thai_number_text'
        },
        'sell_total_amount_text': {
            'source': 'local_amount',
            'type': 'text',
            'field_name': 'sell_total_amount_text',
            'condition': lambda tx_type: tx_type == 'sell',
            'condition_field': 'transaction_type',
            'transform': 'thai_number_text'
        },
        'beneficiary_name': {
            'source': 'beneficiary_name',
            'type': 'text',
            'field_name': 'beneficiary_name',
            'optional': True
        },
        'transaction_purpose': {
            'source': 'transaction_purpose',
            'type': 'text',
            'field_name': 'transaction_purpose',
            'optional': True
        }
    },

    # Section 4: Signature Area
    'section_4': {
        'customer_signature_checkbox_1': {
            'source': 'static',
            'value': True,
            'type': 'checkbox',
            'field_name': 'customer_signature_checkbox_1'
        },
        'customer_signature_checkbox_2': {
            'source': 'static',
            'value': False,
            'type': 'checkbox',
            'field_name': 'customer_signature_checkbox_2'
        },
        'record_date': {
            'source': 'created_at',
            'type': 'text',
            'field_name': 'record_date',
            'format': lambda date: date.strftime('%d/%m/%Y')
        },
        'report_date': {
            'source': 'reported_at',
            'type': 'text',
            'field_name': 'report_date',
            'format': lambda date: date.strftime('%d/%m/%Y') if date else ''
        }
    }
}


# Field extraction functions
def get_field_value(data: Dict[str, Any], field_config: Dict[str, Any]) -> Any:
    """
    Extract field value from data based on configuration

    Args:
        data: Transaction and related data
        field_config: Field mapping configuration

    Returns:
        The extracted and transformed value
    """
    source = field_config.get('source')

    # Static value
    if source == 'static':
        return field_config.get('value')

    # Extract from data using dot notation (e.g., 'branch.amlo_institution_code')
    keys = source.split('.')
    value = data
    for key in keys:
        value = value.get(key) if isinstance(value, dict) else getattr(value, key, None)
        if value is None:
            return None

    # Apply transformation if specified
    transform = field_config.get('transform')
    if transform:
        if transform == 'buddhist_date':
            mapper = AMLOFieldMapper()
            return mapper.format_date_buddhist(value)
        elif transform == 'thai_number_text':
            mapper = AMLOFieldMapper()
            return mapper.thai_number_to_text(value)
        elif callable(transform):
            value = transform(value)

    # Apply formatting if specified
    format_func = field_config.get('format')
    if format_func and callable(format_func):
        value = format_func(value)

    # Check condition
    condition = field_config.get('condition')
    if condition and callable(condition):
        condition_field = field_config.get('condition_field', 'transaction_type')
        condition_value = data.get(condition_field)
        if not condition(condition_value):
            return None

    return value


def build_pdf_field_dict(transaction_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Build a complete dictionary of PDF field names -> values for AMLO-1-01

    Args:
        transaction_data: Dictionary containing transaction, branch, operator data

    Returns:
        Dictionary mapping PDF field names to their values
    """
    pdf_fields = {}
    mapper = AMLOFieldMapper()

    for section_name, section_config in AMLO_101_FIELD_MAPPING.items():
        for field_key, field_config in section_config.items():
            field_type = field_config.get('type')
            value = get_field_value(transaction_data, field_config)

            if value is None and not field_config.get('optional', False):
                continue

            # Handle different field types
            if field_type == 'text_boxes':
                # Split into individual character boxes
                box_count = field_config.get('box_count')
                prefix = field_config.get('prefix')
                boxes = mapper.split_into_boxes(value, box_count)
                for box_num, box_value in boxes.items():
                    pdf_fields[f"{prefix}{box_num}"] = box_value

            elif field_type == 'date_fields':
                # Split date into day/month/year fields
                date_fields = field_config.get('fields')
                if isinstance(value, dict):
                    for date_part, field_name in date_fields.items():
                        pdf_fields[field_name] = str(value.get(date_part, ''))

            elif field_type == 'checkbox':
                # Checkbox field (True/False or 'Yes'/'Off')
                field_name = field_config.get('field_name')
                pdf_fields[field_name] = 'Yes' if value else 'Off'

            elif field_type == 'checkbox_group':
                # Multiple checkboxes (only one checked)
                options = field_config.get('options')
                for option_key, option_field in options.items():
                    pdf_fields[option_field] = 'Yes' if value == option_key else 'Off'

            elif field_type == 'text':
                # Regular text field
                field_name = field_config.get('field_name')
                pdf_fields[field_name] = str(value) if value else ''

    return pdf_fields
