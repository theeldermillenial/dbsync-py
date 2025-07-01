# Integration Testing Guide

This directory contains integration tests for dbsync-py that connect to actual DBSync PostgreSQL databases.

## Overview

Integration tests are designed to:
- Test against real DBSync database instances
- Validate SQLModel classes work with actual data
- Ensure database connections and queries function correctly
- Only run when DBSync environment variables are configured

## Environment Setup

### Option 1: Database URL
Set the complete database URL:
```bash
export DBSYNC_DATABASE_URL="postgresql://username:password@host:port/database"
```

### Option 2: Individual Variables
Set individual connection parameters:
```bash
export DBSYNC_HOST="localhost"
export DBSYNC_PORT="5432"
export DBSYNC_DB_NAME="cexplorer"
export DBSYNC_USER="your_username"
export DBSYNC_PASS="your_password"
```

### Using .env File
Create a `.env` file in the project root with your DBSync connection details:
```env
DBSYNC_HOST=your-dbsync-host
DBSYNC_PORT=5432
DBSYNC_DB_NAME=cexplorer
DBSYNC_USER=your_username
DBSYNC_PASS=your_password
```

**Note:** The environment variable names shown above match the authoritative `sample.env` file. Always use these exact variable names for consistency.

## Running Tests

### Run Only Unit Tests (Default)
```bash
# Run all unit tests (skips integration tests if no DBSync env)
pytest tests/unit/

# Run unit tests with explicit marker
pytest -m "unit"
```

### Run Only Integration Tests
```bash
# Run only integration tests (requires DBSync environment)
pytest -m "integration"

# Run integration tests in specific directory
pytest tests/integration/
```

### Run All Tests
```bash
# Run all tests (integration tests will be skipped if no DBSync env)
pytest

# Run all tests with verbose output
pytest -v
```

### Check Integration Test Status
```bash
# See which tests would be skipped
pytest --collect-only -m "integration"
```

## Writing Integration Tests

### Basic Integration Test Pattern

```python
import pytest
from tests.integration.base import BaseIntegrationTest

@pytest.mark.integration
class TestMyModelIntegration(BaseIntegrationTest):
    """Integration tests for MyModel class."""

    def test_model_with_real_data(self, dbsync_session):
        """Test model against real DBSync data."""
        # Your test code here
        pass
```

### Async Integration Test Pattern

```python
import pytest
from tests.integration.base import BaseAsyncIntegrationTest

@pytest.mark.integration
@pytest.mark.async_test
class TestMyAsyncModelIntegration(BaseAsyncIntegrationTest):
    """Async integration tests for MyModel class."""

    async def test_async_model_with_real_data(self, dbsync_async_session):
        """Test async model against real DBSync data."""
        # Your async test code here
        pass
```

### Available Fixtures

- `dbsync_config`: DatabaseConfig instance with environment settings
- `dbsync_session`: Synchronous database session
- `dbsync_async_session`: Asynchronous database session

### Base Class Utilities

Both `BaseIntegrationTest` and `BaseAsyncIntegrationTest` provide:

- `verify_database_connection(session)`: Check if database connection works
- `get_table_count(session, table_name)`: Get record count for a table
- `verify_table_exists(session, table_name)`: Check if table exists

## Integration Test Guidelines

### When to Add Integration Tests

Add integration tests when:
- Creating new SQLModel classes (SCHEMA-XXX tasks)
- Implementing complex database queries
- Adding database-specific functionality
- Testing type conversions with real data

### What to Test

- Model instantiation with real data
- Database queries and relationships
- Type conversions and validations
- Foreign key relationships
- Custom database types and functions

### What NOT to Test

- Basic Python functionality (use unit tests)
- Mocked database interactions (use unit tests)
- Configuration logic without database access

### Example Integration Test for Model Generation

```python
@pytest.mark.integration
class TestBlockModelIntegration(BaseIntegrationTest):
    """Integration tests for Block model with real DBSync data."""

    def test_block_model_creation(self, dbsync_session):
        """Test Block model with real database data."""
        from dbsync.models import Block

        # Verify table exists
        assert self.verify_table_exists(dbsync_session, "block")

        # Get a real block from database
        block = dbsync_session.query(Block).first()

        if block:
            # Test model properties
            assert block.id_ is not None
            assert block.hash_ is not None
            assert block.block_no is not None

            # Test relationships if any
            if hasattr(block, 'transactions'):
                assert isinstance(block.transactions, list)
        else:
            pytest.skip("No block data available for testing")
```

## Troubleshooting

### Integration Tests Being Skipped

If integration tests are being skipped, check:

1. **Environment variables are set correctly** - Use the exact variable names from `sample.env`
2. **Database is accessible** from test environment
3. **User has proper permissions** to access the DBSync database
4. **Database contains expected DBSync schema** and data

### Connection Errors

Common issues:
- **Incorrect host/port configuration** - Verify `DBSYNC_HOST` and `DBSYNC_PORT`
- **Authentication failures** - Check `DBSYNC_USER` and `DBSYNC_PASS`
- **Network connectivity issues** - Ensure database server is accessible
- **Database not running** or accessible

### Test Failures

If tests fail:
1. **Verify database contains expected data** - DBSync must be synchronized
2. **Check DBSync version compatibility** - Ensure compatible schema version
3. **Ensure database schema is up to date** - DBSync must have latest schema
4. **Review test expectations** against actual data patterns

## Best Practices

1. **Mark all integration tests**: Use `@pytest.mark.integration` decorator
2. **Use base classes**: Inherit from `BaseIntegrationTest` or `BaseAsyncIntegrationTest`
3. **Check data availability**: Use `pytest.skip()` if required data is missing
4. **Test real scenarios**: Use actual DBSync data patterns and relationships
5. **Keep tests focused**: Test specific model/functionality, not entire system
6. **Document requirements**: Note any specific DBSync data requirements
7. **Use correct imports**: Import models from `dbsync.models`, not legacy paths
8. **Follow field naming**: Use underscore field names (`id_`, `hash_`, etc.) for consistency
