# AMLO PDF FillPos Roadmap

## Phase 0 - Preparation & Backup
- Backup original PDFs to `backup/pdf_templates/YYYYMMDD/`.
- Snapshot `report_fields` schema/data (CSV export).
- Implement `scripts/pdf_field_inventory.py` for current field inventory.

## Phase 1 - Checkbox Form Fields
- Generate PNG previews via `pdftoppm` for manual layout notes.
- Script `scripts/pdf_add_checkboxes.py` to inject `/Btn` fields named `check_XX` (left-to-right, top-to-bottom).
- Validate with `PdfReader.get_fields()`; create unit test `tests/pdf/test_checkbox_fields.py`.

## Phase 2 - Schema Extension
- Migration `011_add_report_field_fillpos.py` adding `fillpos VARCHAR(64)` to `report_fields`.
- Update backend models if necessary; add `tests/backend/test_report_fields_schema.py`.

## Phase 3 - FillPos Mapping Script
- Build `scripts/map_fillpos_from_pdf.py` to assign `fillpos` from PDF field names.
- Support dry-run/apply, with audit log; unit test `tests/backend/test_fillpos_mapping.py`.

## Phase 4 - PDF Fill Logic
- Update `services/pdf/amlo_form_filler.py` to use `fillpos` for text & checkbox fields.
- Log missing mappings; add regression test `tests/pdf/test_amlo_fill.py`.

## Phase 5 - AMLO Audit Integration
- Ensure AMLO report view/download routes call updated filler.
- Manual end-to-end verification for 1-01/1-02/1-03 PDFs.

## Phase 6 - Regression & Documentation
- Run focused pytest suites (`tests/pdf`, mapping/schema tests).
- Document mappings in `docs/AMLO_fillpos_migration.md`.
- Maintain backups & remove temporary artefacts.
