# Backend Tests

This directory contains comprehensive tests for the document checking system backend.

## Test Structure

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── test_rule_engine.py     # Rule engine tests
│   ├── test_docx_parser.py     # Document parser tests
│   ├── test_structure_checker.py  # Structure checker tests
│   ├── test_ai_checker.py      # AI checker tests
│   └── test_models.py          # Database model tests
├── integration/            # Integration tests for APIs
│   ├── test_auth_api.py       # Authentication API tests
│   └── test_checks_api.py     # Document check API tests
├── template_tests/         # Template accuracy tests
│   ├── scripts/            # Test scripts
│   ├── documents/          # Test documents
│   ├── reports/            # Test reports
│   └── README.md           # Template testing guide
└── fixtures/               # Test fixtures and sample data

```

## Running Tests

### Prerequisites

Install test dependencies:

```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
# Run pytest tests (unit + integration)
pytest

# Run template accuracy tests (格式检测)
python tests/template_tests/scripts/test_template_accuracy.py

# Run complete template tests (格式 + AI检测)
python tests/template_tests/scripts/test_template_with_ai.py
```

### Run Specific Test Categories

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only service tests
pytest -m service

# Run only API tests
pytest -m api

# Run only model tests
pytest -m model
```

### Run Specific Test Files

```bash
# Run rule engine tests
pytest tests/unit/test_rule_engine.py

# Run auth API tests
pytest tests/integration/test_auth_api.py
```

### Run with Coverage

```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html  # On macOS
xdg-open htmlcov/index.html  # On Linux
start htmlcov/index.html  # On Windows
```

### Run with Verbose Output

```bash
pytest -v
```

### Run Specific Test Function

```bash
pytest tests/unit/test_rule_engine.py::TestRuleEngine::test_init
```

## Template Tests

The template_tests directory contains end-to-end tests for template accuracy:

### Format Testing (格式检测)

Test format rule detection without AI:

```bash
python tests/template_tests/scripts/test_template_accuracy.py
```

**Tests:**
- Page margins and paper size
- Font and font size
- Paragraph formatting (line spacing, indentation)
- Heading styles

**Expected Result:** 100% accuracy

### Complete Testing (完整测试)

Test format rules + AI content detection:

```bash
python tests/template_tests/scripts/test_template_with_ai.py
```

**Tests:**
- All format rules (above)
- AI spell checking (错别字检测)
- AI cross-reference checking (交叉引用检测)

**Expected Result:** 100% accuracy (AI allows ±1 tolerance)

### Import Templates (导入模板)

Import new templates from .docx files:

```bash
python tests/template_tests/scripts/import_templates.py
```

See `tests/template_tests/README.md` for detailed documentation.

## Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.service` - Service layer tests
- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.model` - Database model tests
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.asyncio` - Async tests

## Test Fixtures

Common fixtures are defined in `conftest.py`:

- `db` - Database session for each test
- `client` - FastAPI test client
- `test_user` - Sample test user
- `guest_user` - Sample guest user
- `auth_token` - Authentication token
- `auth_headers` - Authorization headers
- `sample_docx_path` - Path to sample DOCX file
- `sample_doc_data` - Sample parsed document data
- `sample_rules` - Sample checking rules
- `sample_rule_template` - Sample rule template
- `sample_check` - Sample check record

## Writing New Tests

### Unit Test Template

```python
import pytest
from app.services.your_service import YourService


@pytest.mark.unit
@pytest.mark.service
class TestYourService:
    """Test cases for YourService."""

    def test_functionality(self):
        """Test specific functionality."""
        service = YourService()
        result = service.do_something()
        assert result is not None
```

### Integration Test Template

```python
import pytest


@pytest.mark.integration
@pytest.mark.api
class TestYourAPI:
    """Test cases for your API endpoints."""

    def test_endpoint(self, client, auth_headers):
        """Test API endpoint."""
        response = client.get("/api/endpoint", headers=auth_headers)
        assert response.status_code == 200
```

### Async Test Template

```python
import pytest


@pytest.mark.asyncio
async def test_async_function():
    """Test async functionality."""
    result = await async_function()
    assert result is not None
```

## Test Coverage Goals

- Overall coverage: > 80%
- Service layer: > 90%
- API layer: > 85%
- Model layer: > 85%

## Continuous Integration

Tests are automatically run in CI/CD pipelines:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Troubleshooting

### Database Issues

If you encounter database issues:

```bash
# Remove test database
rm test.db

# Run tests again
pytest
```

### Import Errors

Make sure you're running tests from the backend directory:

```bash
cd backend
pytest
```

### Async Test Issues

Ensure pytest-asyncio is installed:

```bash
pip install pytest-asyncio
```

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Clear Names**: Use descriptive test function names
3. **AAA Pattern**: Arrange, Act, Assert structure
4. **Mock External Services**: Use mocks for external APIs
5. **Test Edge Cases**: Include both happy and error paths
6. **Keep Tests Fast**: Use mocks to avoid slow operations
7. **Clean Up**: Ensure tests clean up after themselves

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html)
