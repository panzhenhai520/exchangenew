import os
import importlib.util
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_migration_module(file_path):
    """Load a migration module from file path"""
    spec = importlib.util.spec_from_file_location("migration", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def run_migrations(direction='upgrade'):
    """Run all migration scripts in order"""
    migrations_dir = os.path.dirname(os.path.abspath(__file__))
    migration_files = [f for f in os.listdir(migrations_dir) 
                      if f.endswith('.py') and f != 'migrate.py']
    
    # Sort migration files to ensure order
    migration_files.sort()
    
    for migration_file in migration_files:
        try:
            logger.info(f"Running migration: {migration_file}")
            file_path = os.path.join(migrations_dir, migration_file)
            migration = load_migration_module(file_path)
            
            if direction == 'upgrade':
                migration.upgrade()
            else:
                migration.downgrade()
                
            logger.info(f"Successfully completed migration: {migration_file}")
            
        except Exception as e:
            logger.error(f"Error in migration {migration_file}: {str(e)}")
            raise

if __name__ == "__main__":
    import sys
    direction = sys.argv[1] if len(sys.argv) > 1 else 'upgrade'
    run_migrations(direction) 