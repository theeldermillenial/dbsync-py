# Database Connection

Comprehensive guide to connecting to Cardano DB Sync databases.

## Basic Connection

```python
from dbsync_py import create_session

session = create_session("postgresql://user:pass@localhost/cardano_db")
```

## Async Connection

```python
from dbsync_py import create_async_session

async with create_async_session("postgresql+asyncpg://user:pass@localhost/cardano_db") as session:
    # Your async code here
    pass
```

## Connection Management

### Session Context Managers

```python
from dbsync_py import DBSyncSession

with DBSyncSession("postgresql://user:pass@localhost/cardano_db") as session:
    # Session automatically closed
    pass
```

### Connection Testing

```python
from dbsync_py.utils import test_connection

# Test connection
is_connected = test_connection("postgresql://user:pass@localhost/cardano_db")
print(f"Connection successful: {is_connected}")
```

## Error Handling

```python
from dbsync_py import create_session
from sqlalchemy.exc import SQLAlchemyError

try:
    session = create_session("postgresql://user:pass@localhost/cardano_db")
    # Your database operations
except SQLAlchemyError as e:
    print(f"Database error: {e}")
```

## Best Practices

- Use connection pooling for production applications
- Always close sessions properly
- Use environment variables for connection strings
- Test connections before running queries
- Handle connection errors gracefully
