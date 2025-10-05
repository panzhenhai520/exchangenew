#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Run database migration script
"""

import sys
import os
import pymysql
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join('src', '.env')
load_dotenv(env_path)

# Get database config
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'Exchange')

def run_migration():
    """Execute migration SQL script"""
    migration_file = os.path.join('src', 'migrations', '005_add_receipt_payment_country_fields.sql')

    if not os.path.exists(migration_file):
        print(f"❌ Migration file not found: {migration_file}")
        return False

    print("=== Database Migration ===")
    print(f"Migration file: {migration_file}")
    print(f"Database: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    print("=" * 60)

    try:
        # Read SQL file
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        # Connect to database
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4'
        )

        print("Connected to database successfully")

        # Execute SQL statements one by one
        cursor = connection.cursor()

        # Remove comment lines starting with --
        lines = [line for line in sql_content.split('\n') if not line.strip().startswith('--')]
        cleaned_content = '\n'.join(lines)

        # Split by semicolon and filter empty statements
        statements = [s.strip() for s in cleaned_content.split(';') if s.strip()]

        print(f"Found {len(statements)} SQL statements to execute\n")

        for i, statement in enumerate(statements, 1):
            # Skip comments
            if statement.startswith('--'):
                continue

            # Show first 80 chars of statement
            preview = statement[:80].replace('\n', ' ')
            print(f"[{i}/{len(statements)}] Executing: {preview}...")

            try:
                cursor.execute(statement)
                connection.commit()
                print(f"  Success")
            except pymysql.err.OperationalError as e:
                error_code = e.args[0]
                error_msg = e.args[1]

                # Check if error is "column already exists" or "table already exists"
                if error_code == 1060:  # Duplicate column name
                    print(f"  WARNING: Column already exists, skipping")
                    continue
                elif error_code == 1050:  # Table already exists
                    print(f"  WARNING: Table already exists, skipping")
                    continue
                else:
                    print(f"  ERROR: {error_msg}")
                    raise

        cursor.close()
        connection.close()

        print("\nMigration completed successfully!")
        return True

    except Exception as e:
        print(f"\nERROR: Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("Database Migration Script")
    print("=" * 60)
    success = run_migration()
    if success:
        print("\nAll migrations applied successfully!")
    else:
        print("\nMigration failed!")
    print("=" * 60)
