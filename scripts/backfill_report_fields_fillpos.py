#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backfill report_fields.fillpos using docs/amlo_pdf_notes.md.

The script parses the PDF field inventory Markdown, extracts
`PDF Field` <-> `Mapped Field` pairs, and optionally applies
the mappings to the database.

Usage examples:
    # Dry-run (default) – show summary only
    python scripts/backfill_report_fields_fillpos.py --dry-run

    # Apply mappings to the database (requires pymysql)
    python scripts/backfill_report_fields_fillpos.py --apply

Database connection is resolved from environment variables
(.env / .env.local) – namely MYSQL_HOST, MYSQL_PORT, MYSQL_USER,
MYSQL_PASSWORD, MYSQL_DATABASE.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


PDF_NOTES_PATH = Path("docs/amlo_pdf_notes.md")
SUPPORTED_REPORTS = ("AMLO-1-01", "AMLO-1-02", "AMLO-1-03")


@dataclass
class FieldMapping:
    report_type: str
    field_name: str
    fillpos: str
    notes: str


def parse_pdf_notes(markdown_path: Path) -> Dict[str, List[FieldMapping]]:
    """
    Parse the Markdown table and return mappings per report type.
    """
    if not markdown_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {markdown_path}")

    report_mappings: Dict[str, List[FieldMapping]] = defaultdict(list)
    current_report = None

    # Simple state machine to parse Markdown tables.
    with markdown_path.open("r", encoding="utf-8") as md_file:
        for raw_line in md_file:
            line = raw_line.strip()

            # Detect report sections (## AMLO-1-01 (CTR))
            if line.startswith("## "):
                for report in SUPPORTED_REPORTS:
                    if report in line:
                        current_report = report
                        break
                else:
                    current_report = None
                continue

            if current_report is None:
                continue

            if not line.startswith("|"):
                continue  # skip non-table lines

            # Skip header separator line like | --- | --- |
            if set(line.replace("|", "").strip()) <= {"-", " "}:
                continue

            columns = [col.strip() for col in line.split("|")[1:-1]]
            if len(columns) < 4:
                continue  # not enough columns

            pdf_field, _, _, mapped_field, notes = columns[:5]
            if pdf_field.lower() == "pdf field":
                continue
            pdf_field = pdf_field.strip()
            mapped_field = mapped_field.strip()
            notes = notes.strip()

            if not pdf_field or not mapped_field:
                continue  # only keep entries with explicit mapping

            # Normalise `Mapped Field` to snake_case (just in case)
            normalized_field = re.sub(r"\s+", "_", mapped_field)
            normalized_field = normalized_field.replace("-", "_")

            report_mappings[current_report].append(
                FieldMapping(
                    report_type=current_report,
                    field_name=normalized_field,
                    fillpos=pdf_field,
                    notes=notes,
                )
            )

    return report_mappings


def summarize_mappings(mappings: Dict[str, List[FieldMapping]]) -> None:
    """
    Print mapping summary per report type.
    """
    print("== FillPos Mapping Summary ==")
    for report in SUPPORTED_REPORTS:
        items = mappings.get(report, [])
        print(f"- {report}: {len(items)} mapped fields")
        sample = ", ".join(f"{m.field_name}->{m.fillpos}" for m in items[:5])
        if sample:
            print(f"  sample: {sample}")
        else:
            print("  sample: (none)")
    print()


def read_env_file(env_file: Path) -> Dict[str, str]:
    """
    Load simple key=value pairs from an env file.
    """
    if not env_file.exists():
        return {}
    values = {}
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def resolve_db_credentials() -> Dict[str, str]:
    """
    Prefer environment variables; fall back to .env / .env.local.
    """
    env = dict(os.environ)
    # fallback to .env / .env.local
    for candidate in (Path(".env"), Path(".env.local")):
        env.update(read_env_file(candidate))

    creds = {
        "host": env.get("MYSQL_HOST") or env.get("DB_HOST") or "localhost",
        "port": int(env.get("MYSQL_PORT") or env.get("DB_PORT") or 3306),
        "user": env.get("MYSQL_USER") or env.get("DB_USER"),
        "password": env.get("MYSQL_PASSWORD") or env.get("DB_PASSWORD"),
        "database": env.get("MYSQL_DATABASE") or env.get("DB_NAME"),
    }

    missing = [k for k, v in creds.items() if v in (None, "")]
    if missing:
        raise RuntimeError(
            f"Missing database credentials for: {', '.join(missing)}. "
            "Set MYSQL_* or DB_* environment variables (or .env/.env.local)."
        )

    return creds


def apply_mappings_to_db(
    mappings: Dict[str, List[FieldMapping]],
    *,
    commit: bool = False,
) -> Tuple[int, List[FieldMapping]]:
    """
    Update report_fields.fillpos in the database.
    """
    try:
        import pymysql
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "pymysql package is required to update the database. "
            "Install it via `pip install pymysql`."
        ) from exc

    creds = resolve_db_credentials()
    connection = pymysql.connect(
        host=creds["host"],
        port=creds["port"],
        user=creds["user"],
        password=creds["password"],
        database=creds["database"],
        charset="utf8mb4",
        autocommit=False,
    )

    updated = 0
    missing: List[FieldMapping] = []

    try:
        with connection.cursor() as cursor:
            for report_type, items in mappings.items():
                for mapping in items:
                    sql = (
                        "UPDATE report_fields "
                        "SET fillpos = %s, updated_at = NOW() "
                        "WHERE report_type = %s AND field_name = %s"
                    )
                    affected = cursor.execute(
                        sql,
                        (mapping.fillpos, report_type, mapping.field_name),
                    )
                    if affected:
                        updated += affected
                    else:
                        missing.append(mapping)

        if commit:
            connection.commit()
            print(f"[OK] Updated {updated} rows (committed).")
        else:
            connection.rollback()
            print(f"[DRY-RUN] Would update {updated} rows (rolled back).")

    finally:
        connection.close()

    return updated, missing


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Backfill report_fields.fillpos from Markdown inventory."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply mappings to the database (default: dry-run).",
    )
    parser.add_argument(
        "--markdown",
        type=Path,
        default=PDF_NOTES_PATH,
        help=f"Path to Markdown file (default: {PDF_NOTES_PATH})",
    )
    parser.add_argument(
        "--print-mapping",
        action="store_true",
        help="Print detailed mapping after summary.",
    )

    args = parser.parse_args(argv)

    mappings = parse_pdf_notes(args.markdown)
    summarize_mappings(mappings)

    if args.print_mapping:
        for report, items in mappings.items():
            print(f"--- {report} ({len(items)} entries) ---")
            for item in items:
                print(f"{item.field_name:40s} -> {item.fillpos}")
            print()

    if not args.apply:
        print("Dry-run mode; no database changes were made.")
        return 0

    try:
        updated, missing = apply_mappings_to_db(mappings, commit=True)
    except RuntimeError as exc:
        print(f"[ERROR] {exc}")
        return 1

    if missing:
        print(
            f"[WARN] {len(missing)} fields were not found in report_fields. "
            "See details below:"
        )
        for m in missing[:20]:
            print(f"  - {m.report_type}.{m.field_name} (fillpos {m.fillpos})")
        if len(missing) > 20:
            print("  ... (truncated)")

    print(f"Completed. Rows updated: {updated}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
