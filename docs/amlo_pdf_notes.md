# AMLO PDF Mapping Notes

This document tracks the mapping between dynamic AMLO report fields and the annotated form controls in the interactive PDF templates (`1-01-fill.pdf`, `1-02-fill.pdf`, `1-03-fill.pdf`). The new `report_fields.fillpos` column stores the exact PDF field identifier (e.g. `fill_42`, `Check Box5`). These identifiers are required so the HTML form data can be merged into the PDF templates without relying on brittle coordinate overlays.

## Mapping Summary

### AMLO-1-01 (CTR)
| Field name (`report_fields`) | PDF logical field | FillPos | Notes |
| --- | --- | --- | --- |
| `customer_id` | `maker_id_card` | `comb_1` | 13 digit ID entry boxes |
| `customer_name` | `maker_full_name` | `fill_13` | Full customer name |
| `customer_address` | `maker_address_line1` | `fill_13` | Current address block (same text control as name in template) |
| `customer_phone` | `maker_phone` | `fill_57` | Primary contact phone |
| `customer_occupation` | `maker_occupation` | `fill_13` | Occupation (shares address/name text area in legacy form) |
| `transaction_purpose` | `transaction_purpose` | `fill_42` | Free text purpose description |
| `beneficiary_name` | `transaction_beneficiary_name` | `fill_50` | Beneficiary name / narrative amount |

### AMLO-1-02 (ATR)
| Field name (`report_fields`) | PDF logical field | FillPos | Notes |
| --- | --- | --- | --- |
| `customer_id` | `maker_id_card` | `fill_7` | ID boxes below header |
| `customer_name` | `maker_full_name` | `fill_11` | Main name line |
| `customer_address` | `maker_address_line1` | `fill_11` | Address line (shares text area with name) |
| `customer_phone` | `maker_phone` | `fill_68` | Contact phone |
| `customer_occupation` | `maker_occupation` | `fill_11` | Occupation line |
| `transaction_purpose` | `transaction_purpose` | `fill_44` | Purpose narrative |
| `beneficiary_name` | `transaction_beneficiary_name` | `fill_44` | Beneficiary narrative (shared field) |

### AMLO-1-03 (STR)
| Field name (`report_fields`) | PDF logical field | FillPos | Notes |
| --- | --- | --- | --- |
| `customer_id` | `maker_id_card` | `comb_1` | ID entry boxes |
| `customer_name` | `maker_full_name` | `fill_7` | Customer name |
| `customer_address` | `maker_address_line1` | `fill_11` | Address line |
| `customer_phone` | `maker_phone` | `fill_56` | Contact phone |
| `customer_occupation` | `maker_occupation` | `fill_11` | Occupation line |
| `transaction_purpose` | `transaction_purpose` | `fill_42` | Purpose summary |
| `beneficiary_name` | `transaction_beneficiary_name` | `comb_4` | Beneficiary account / owner name |

> ℹ️  The interactive templates reuse a limited set of text inputs for multiple logical values. Where the official PDF combines several pieces of information in a single block, the same `fillpos` is recorded above.

## How the Mapping Was Derived
- Parsed the annotated templates with `PyPDF2` to list interactive field names (`fill_XX`, `comb_XX`, `Check BoxYY`).
- Matched each logical field in `services/pdf/amlo_field_mappings.py` to the nearest interactive control by geometry.
- Verified the matches with the PDF `/TU` alternate text and manual inspection.
- Stored the canonical identifier in `report_fields.fillpos` via migration `011_add_report_field_fillpos.py`.

When adding new AMLO fields:
1. Annotate the fillable PDF template with a unique control name.
2. Update `report_fields.fillpos` (and translations) for the new field.
3. Extend `amlo_field_mappings.py`/`AMLOFormFiller` if additional logic is required.

This ensures dynamic AMLO forms can render HTML inputs and regenerate the official PDF with consistent field placement.
