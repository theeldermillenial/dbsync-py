# Tests

This directory contains the test suite for dbsync-py.

## Structure

```
tests/
├── __init__.py          # Test package initialization
├── conftest.py          # Pytest configuration and shared fixtures  
├── test_package_import.py  # Basic package import tests
├── unit/                # Unit tests
│   └── __init__.py
├── integration/         # Integration tests  
│   └── __init__.py
└── README.md           # This file
```

## Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_package_import.py

# Run tests by marker
pytest -m unit
pytest -m integration
```

### Coverage Reports

```bash
# Run tests with coverage
pytest --cov=src --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

## Test Categories

- **unit**: Unit tests for individual components
- **integration**: Integration tests requiring database connections
- **async_test**: Tests requiring async support

## Test Configuration

The test suite includes:

- **Environment isolation**: Tests use mocked environment variables
- **Database fixtures**: SQLite in-memory database for testing
- **Async support**: pytest-asyncio for async database operations
- **Coverage reporting**: Code coverage metrics and reporting

## Writing Tests

### Test Structure

All tests should follow the pattern:

```python
import pytest
from dbsync_py import module_to_test

@pytest.mark.unit  # or integration, async_test
def test_function_name():
    """Test description."""
    # Test implementation
    assert expected == actual
```

### Fixtures

Common fixtures available in `conftest.py`:

- `test_database_url`: SQLite in-memory database URL
- `mock_env_vars`: Mocked environment variables
- `test_session`: SQLAlchemy test session

### Async Tests

```python
@pytest.mark.async_test
async def test_async_function():
    """Test async functionality."""
    result = await async_function()
    assert result is not None
```
