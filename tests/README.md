# Exchange System Unit Tests

This directory contains comprehensive unit tests for both frontend (Vue.js) and backend (Flask) components of the Exchange System, with a focus on AMLO and BOT compliance features.

## Test Structure

```
tests/
├── unit/                      # Frontend unit tests (Jest)
│   ├── views/
│   │   └── amlo/
│   │       └── ReportListView.spec.js
│   └── services/
│       └── api/
│           ├── amloService.spec.js
│           └── botService.spec.js
├── backend/                   # Backend unit tests (pytest)
│   ├── conftest.py           # Pytest fixtures and configuration
│   └── routes/
│       ├── test_app_amlo.py
│       └── test_app_bot.py
├── setup.js                  # Jest global setup
└── README.md                 # This file
```

## Frontend Tests (Jest)

### Prerequisites

Install the required testing packages:

```bash
npm install --save-dev @vue/test-utils@^2.3.0 @vue/vue3-jest@^29.0.0 jest@^29.0.0 babel-jest@^29.0.0 jest-environment-jsdom@^29.0.0 jest-transform-stub@^2.0.0 identity-obj-proxy@^3.0.0
```

### Test Files

1. **ReportListView.spec.js** - Tests for AMLO report list page
   - Overdue detection logic (>3 days)
   - Red highlighting for overdue reports
   - Batch selection and reporting
   - Filter and search functionality
   - Pagination
   - PDF download and modal interactions

2. **amloService.spec.js** - Tests for AMLO API service
   - Reservation queries and filtering
   - Audit and reverse-audit operations
   - Report listing with pagination
   - Batch reporting
   - Single and batch PDF generation
   - Error handling

3. **botService.spec.js** - Tests for BOT API service
   - T+1 Buy/Sell FX data retrieval
   - Excel export functionality
   - Multi-sheet Excel export
   - Trigger configuration management
   - Date parameter handling
   - Error handling

### Running Frontend Tests

```bash
# Run all frontend tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm test -- --coverage

# Run specific test file
npm test ReportListView.spec.js

# Run tests matching a pattern
npm test amlo
```

### Test Commands

Add these scripts to your `package.json`:

```json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:unit": "jest tests/unit"
  }
}
```

## Backend Tests (pytest)

### Prerequisites

Install the required testing packages:

```bash
pip install pytest pytest-cov pytest-mock
```

### Test Files

1. **test_app_amlo.py** - Tests for AMLO Flask routes
   - GET /api/amlo/reports - Report listing with filters
   - GET /api/amlo/reports/<id>/generate-pdf - Single PDF generation
   - POST /api/amlo/reports/batch-generate-pdf - Batch PDF (ZIP) generation
   - POST /api/amlo/reports/batch-report - Batch reporting
   - Overdue detection logic
   - Error handling and edge cases

2. **test_app_bot.py** - Tests for BOT Flask routes
   - GET /api/bot/t1-buy-fx - Buy FX data retrieval
   - GET /api/bot/t1-sell-fx - Sell FX data retrieval
   - GET /api/bot/export-buy-fx - Buy FX Excel export
   - GET /api/bot/export-sell-fx - Sell FX Excel export
   - POST /api/bot/save-buy-fx - Save buy FX report
   - POST /api/bot/save-sell-fx - Save sell FX report
   - GET/POST /api/bot/trigger-config - Config management
   - Date handling and formatting

### Running Backend Tests

```bash
# Run all backend tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/backend/routes/test_app_amlo.py

# Run specific test class
pytest tests/backend/routes/test_app_amlo.py::TestGetReports

# Run specific test function
pytest tests/backend/routes/test_app_amlo.py::TestGetReports::test_get_reports_success

# Run tests with markers
pytest -m amlo
pytest -m bot
pytest -m unit

# Run with coverage
pytest --cov=src --cov-report=html
pytest --cov=src --cov-report=term-missing

# Run tests matching a keyword
pytest -k "overdue"
pytest -k "pdf"
```

## Test Markers

Backend tests use markers to categorize tests:

- `@pytest.mark.unit` - Fast unit tests with mocked dependencies
- `@pytest.mark.integration` - Integration tests (may require database)
- `@pytest.mark.amlo` - AMLO compliance tests
- `@pytest.mark.bot` - BOT reporting tests
- `@pytest.mark.routes` - API route tests
- `@pytest.mark.services` - Service layer tests

Example usage:

```bash
# Run only unit tests
pytest -m unit

# Run only AMLO tests
pytest -m amlo

# Run AMLO unit tests
pytest -m "amlo and unit"
```

## Test Coverage

### Frontend Coverage

Generate coverage report:

```bash
npm test -- --coverage
```

Coverage report will be in `coverage/lcov-report/index.html`

### Backend Coverage

Generate coverage report:

```bash
pytest --cov=src --cov-report=html
```

Coverage report will be in `htmlcov/index.html`

## Key Test Scenarios

### AMLO Report List Tests

1. **Overdue Detection**
   - Reports created >3 days ago and not reported → Overdue
   - Reports created ≤3 days ago → Not overdue
   - Already reported reports → Never overdue (regardless of age)

2. **Red Highlighting**
   - Overdue rows have `table-danger` CSS class
   - Overdue badge with pulsing animation
   - Non-overdue and reported rows have normal styling

3. **Batch Operations**
   - Select/deselect individual reports
   - Select all (only unreported reports)
   - Batch report selected items
   - Checkboxes disabled for already-reported items

### AMLO API Tests

1. **PDF Generation**
   - Single report PDF with correct content type
   - Batch PDF generation (ZIP file)
   - Error handling for missing reports
   - Exception handling during generation

2. **Report Management**
   - Filtering by status, type, date range
   - Pagination (page, page_size)
   - Batch reporting updates is_reported flag
   - Transaction rollback on errors

### BOT API Tests

1. **Excel Export**
   - Buy FX Excel with proper formatting
   - Sell FX Excel with column widths
   - Empty data handling
   - Blob response with correct MIME type

2. **Data Retrieval**
   - T+1 reports with date filtering
   - Default to yesterday's date
   - Total count and amount calculations
   - Empty results handling

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
        with:
          node-version: '18'
      - run: npm install
      - run: npm test -- --coverage

  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-cov
      - run: pytest --cov=src
```

## Troubleshooting

### Frontend Tests

**Issue**: `Cannot find module '@vue/test-utils'`
```bash
npm install --save-dev @vue/test-utils@^2.3.0
```

**Issue**: `Unexpected token 'export'`
- Ensure `babel-jest` is installed
- Check `jest.config.js` transform configuration

**Issue**: Tests fail with "Not implemented: HTMLFormElement.prototype.submit"
- This is expected for JSDOM environment
- Mock form submissions in tests

### Backend Tests

**Issue**: `ModuleNotFoundError: No module named 'src'`
- Ensure `pythonpath = .` is set in `pytest.ini`
- Run pytest from project root directory

**Issue**: `fixture 'mock_db_session' not found`
- Ensure `conftest.py` is in the correct location
- Check fixture names match usage

**Issue**: Import errors in test files
- Mock imports at the top of test files
- Use `patch` decorator for dependencies

## Writing New Tests

### Frontend Test Template

```javascript
import { mount } from '@vue/test-utils';
import MyComponent from '@/components/MyComponent.vue';

describe('MyComponent.vue', () => {
  let wrapper;

  beforeEach(() => {
    wrapper = mount(MyComponent);
  });

  afterEach(() => {
    wrapper.unmount();
  });

  it('should do something', () => {
    // Arrange
    const expected = 'value';

    // Act
    wrapper.vm.myMethod();

    // Assert
    expect(wrapper.vm.myData).toBe(expected);
  });
});
```

### Backend Test Template

```python
import pytest
from unittest.mock import patch, MagicMock

@pytest.mark.unit
def test_my_function(mock_db_session):
    # Arrange
    mock_session = mock_db_session
    expected_result = {'success': True}

    # Act
    with patch('src.routes.my_module.DatabaseService') as mock_db:
        mock_db.get_session.return_value.__enter__.return_value = mock_session
        result = my_function()

    # Assert
    assert result == expected_result
    mock_session.commit.assert_called_once()
```

## Test Maintenance

- Run tests before committing code
- Update tests when changing business logic
- Maintain test coverage above 80%
- Keep test fixtures up to date
- Document complex test scenarios
- Review test failures in CI/CD

## Resources

- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [Vue Test Utils](https://test-utils.vuejs.org/)
- [pytest Documentation](https://docs.pytest.org/)
- [unittest.mock Guide](https://docs.python.org/3/library/unittest.mock.html)
