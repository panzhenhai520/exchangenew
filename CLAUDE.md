# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Currency Exchange Management System** with a Vue 3 frontend and Flask (Python) backend. The system manages foreign currency exchanges, transactions, reporting, and compliance (AMLO/BOT) for currency exchange businesses. It supports multi-branch operations, multi-language (Chinese, Thai, English), role-based access control, and comprehensive end-of-day (EOD) reporting.

## Technology Stack

- **Frontend**: Vue 3, Vue Router, Pinia/Vuex, Ant Design Vue, Chart.js, Vue I18n
- **Backend**: Flask 2.3.3, SQLAlchemy 2.0.23, Flask-JWT-Extended, ReportLab (PDF generation)
- **Database**: MySQL (default) or SQLite (configurable via `.env`)
- **Python**: 3.11.5
- **Node.js**: 18.20.4

## Development Commands

### Frontend (Vue)
```bash
# Start development server (with network access)
npm run serve
# or use the batch file:
start-dev.bat

# Build for production
npm run build

# Lint code
npm run lint
```

**Dev Server Details:**
- Frontend runs on: `http://192.168.13.56:8080` (configurable)
- Proxies `/api` requests to backend at `http://192.168.13.56:5001`
- Build output: `src/static/dist_frontend/`

### Backend (Flask)
```bash
# Install dependencies
pip install -r requirements.txt

# Run backend server
python src/main.py
```

**Backend Details:**
- Default port: `5001` (configurable in `.env`)
- Main entry point: `src/main.py`
- Database migrations: `src/migrations/migrate.py`

### Database Setup
```bash
# Initialize database with schema
python src/init_db.py

# Run migrations
python run_migration.py

# Initialize countries data
python init_countries_simple.py
```

### Environment Configuration
```bash
# Setup environment (creates .env file)
python setup_environment.py
# or
setup_environment.bat
```

**Key Environment Variables** (in `.env`):
- `DB_TYPE`: `mysql` or `sqlite`
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`: MySQL connection details
- `LOG_MODE`: `production` or `debug`

## Architecture

### Backend Structure

**Core Directories:**
- `src/routes/`: Flask blueprints for API endpoints (40+ route files)
- `src/models/`: SQLAlchemy ORM models
  - `exchange_models.py`: Core models (Branch, Currency, ExchangeTransaction, Operator, Role, etc.)
  - `denomination_models.py`: Denomination/rate publishing models
  - `report_models.py`: Reporting models
- `src/services/`: Business logic layer
  - `db_service.py`: Database connection and session management
  - `auth_service.py`: JWT authentication, token validation, permissions
  - `pdf_service.py`: PDF receipt generation
  - `balance_service.py`: Currency balance tracking
  - `eod_step_service.py`: End-of-day process orchestration
  - `log_service.py`, `multilingual_log_service.py`: Logging with i18n
- `src/migrations/`: Database migration scripts
- `src/utils/`: Helper utilities
- `src/config/`: Configuration files (log_config.py, features.py)
- `src/data/`: Static data (ISO countries, currency templates)

**Key Backend Patterns:**
1. **Blueprint Registration**: All routes are Flask blueprints registered in `src/main.py`
2. **Database Sessions**: Use `DatabaseService.get_session()` context managers for all DB operations
3. **Authentication**: `@token_required` decorator from `auth_service.py`
4. **Permissions**: `@has_permission('permission_name')` decorator for authorization
5. **Error Handling**: Use `safe_error_response()` from `utils/safe_error_handler.py`

### Frontend Structure

**Core Directories:**
- `src/views/`: Vue page components (40+ views)
  - App* views: Mobile-optimized views for "App" role users
  - Standard views: Desktop-optimized views for "System" role users
- `src/components/`: Reusable Vue components
  - `eod/`: End-of-day workflow components (8 steps)
  - `amlo/`: AMLO compliance form components
  - `PrintSettings/`: Receipt customization components
- `src/router/`: Vue Router configuration
- `src/stores/`: Pinia stores for state management
- `src/services/api/`: API service modules (typed wrappers for backend endpoints)
- `src/i18n/`: Internationalization files
  - Modular structure: `modules/{feature}/{locale}.js`
  - Supported: `en-US`, `zh-CN`, `th-TH`
- `src/utils/`: Frontend utilities

**Key Frontend Patterns:**
1. **Role-Based Routing**: Two layout systems:
   - `/app/*`: Mobile layout for "App" role (teller operations)
   - `/system/*`: Desktop layout for "System" role (management)
2. **API Services**: Centralized in `src/services/api/*Service.js` (e.g., `authService.js`, `transactionService.js`)
3. **I18n**: Use `$t('module.key')` for translations (e.g., `$t('transaction.buy')`)
4. **Permission Checking**: `hasPermission(permission)` util from `src/utils/permissions.js`

## Key Business Logic

### Transaction Flow
1. User selects currencies and enters amount
2. System calculates exchange using current rates from `exchange_rates` table
3. Transaction is validated against balance limits and purpose limits
4. Transaction is recorded in `exchange_transactions` table
5. Currency balances are updated in `currency_balances` table
6. PDF receipt is generated via `pdf_service.py`
7. System logs are created via `log_service.py`

### End-of-Day (EOD) Process
The EOD workflow is an 8-step process managed by `eod_step_service.py`:

1. **Start**: Initialize EOD session, lock the branch
2. **Balance Input**: Tellers enter physical currency counts
3. **Calculate**: System compares physical vs. system balances
4. **Verify**: Review differences and approve/reject
5. **Result**: Generate difference report
6. **Cash Out**: Record cash deposits/withdrawals
7. **Report**: Generate comprehensive EOD PDF report
8. **Complete**: Finalize EOD, unlock branch

**Critical**: EOD creates a session lock to prevent concurrent operations. See `src/utils/cleanup_eod_session.py` for emergency unlock.

### AMLO/BOT Compliance
- Dynamic form generation based on `amlo_101_corrected_layout.json`
- Components in `src/components/amlo/DynamicForm/`
- Forms are versioned and auditable
- Routes: `src/routes/app_amlo.py`, `app_bot.py`, `app_compliance.py`

### PDF Generation
Two systems exist:
1. **ReportLab-based** (`pdf_service.py`): Legacy receipt generation
2. **HTML-to-PDF** (`html_pdf_service.py`): Modern, template-based generation using layout definitions

Print settings are customizable per branch via `PrintSettings` model.

## Database Models

**Core Tables:**
- `branches`: Branch/location information
- `currencies`: Currency master data (USD, THB, EUR, etc.)
- `exchange_rates`: Daily exchange rates per branch/currency
- `exchange_transactions`: All exchange transactions
- `currency_balances`: Current balance per currency/branch
- `operators`: User accounts
- `roles` / `permissions` / `role_permissions`: RBAC system
- `system_logs`: Audit trail with multilingual support
- `eod_sessions`: End-of-day session tracking
- `print_settings`: Per-branch receipt customization

**Relationships:**
- Branches have many: operators, transactions, rates, balances
- Transactions belong to: branch, operator, currencies (buy/sell)
- EOD sessions contain: balance snapshots, cash operations, difference reports

## Multi-Language Support

The system supports 3 languages with a modular i18n structure:
- **Locales**: `en-US`, `zh-CN`, `th-TH`
- **Frontend**: Vue I18n with modules in `src/i18n/modules/`
- **Backend**: Multilingual logging via `multilingual_log_service.py`

**Important Scripts:**
- `scripts/i18n_fix_missing_keys.js`: Fix missing translation keys
- `scripts/verify_translations.js`: Validate translation completeness
- `src/utils/i18n_checker.py`: Backend translation checker

## Testing & Debugging

**Debug Pages:**
- `src/main.py` contains embedded HTML debug pages at `/debug`
- Test authentication: Admin credentials are `admin` / `admin123`

**Data Validation:**
```bash
# Check database integrity
python check_data.py
python db_check.py
python comprehensive_check.py
```

**Log Management:**
- Logs in: Project root (configured via `LogConfig`)
- Switch modes: `python src/switch_log_mode.py`
- Cleanup: `src/scripts/log_cleanup.py`

## Common Workflows

### Adding a New Currency
1. Add to `currencies` table via UI or migration
2. Update `currency_templates` if using denomination tracking
3. Initialize exchange rates in `exchange_rates`
4. Add translations to i18n files

### Creating a New Route
1. Create blueprint in `src/routes/app_*.py`
2. Import and register in `src/main.py`
3. Add frontend route in `src/router/index.js`
4. Create view component in `src/views/`
5. Add API service method in `src/services/api/`

### Modifying Print Receipts
1. Edit layout in `PrintSettings` via UI
2. Or modify templates in `pdf_service.py` or `html_pdf_service.py`
3. Test with `src/services/pdf/test_pdf_generator.py` scripts

## Critical Files

- **Backend Entry**: `src/main.py`
- **Frontend Entry**: `src/main.js` (Vue app initialization)
- **Router**: `src/router/index.js`
- **DB Models**: `src/models/exchange_models.py`
- **Auth**: `src/services/auth_service.py`
- **Config**: `.env`, `environment_config.json`, `config.js`

## Known Issues & Maintenance

- **Windows File Locking**: The logging system uses `create_safe_file_handler` to avoid Windows file lock issues
- **EOD Session Locks**: If EOD gets stuck, run `python src/scripts/cleanup_stuck_eod.py`
- **Migration Order**: Always check dependency order in `src/migrations/migrate.py`
- **CORS**: Configured in `environment_config.json` with regex patterns

## Deployment Notes

- Frontend builds to `src/static/dist_frontend/`
- Flask serves frontend static files in production
- Use `gunicorn` for production (included in requirements.txt)
- Database migrations must be run manually on deployment
- Feature flags managed via `src/routes/app_feature_flags.py`
