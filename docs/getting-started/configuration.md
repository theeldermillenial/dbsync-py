# Configuration

## Database Connection

### Connection String Format

```python
# PostgreSQL connection string format
DATABASE_URL = "postgresql://username:password@host:port/database_name"

# For async operations
DATABASE_URL = "postgresql+asyncpg://username:password@host:port/database_name"
```

### Environment Variables

Create a `.env` file in your project root:

```bash
DATABASE_URL=postgresql://cardano:password@localhost:5432/cardano_db
```

Load in your application:

```python
import os
from dotenv import load_dotenv
from dbsync_py import create_session

load_dotenv()
session = create_session(os.getenv("DATABASE_URL"))
```

## Connection Options

### Pool Configuration

```python
from dbsync_py import create_session

session = create_session(
    database_url="postgresql://user:pass@localhost/cardano_db",
    pool_size=10,
    max_overflow=20,
    pool_timeout=30
)
```

### SSL Configuration

```python
session = create_session(
    database_url="postgresql://user:pass@host/db?sslmode=require"
)
```

## Advanced Configuration

### Custom Session Configuration

```python
from dbsync_py.config import DatabaseConfig

config = DatabaseConfig(
    database_url="postgresql://user:pass@localhost/cardano_db",
    echo=True,  # Enable SQL logging
    pool_pre_ping=True,  # Validate connections
    pool_recycle=3600  # Recycle connections every hour
)

session = create_session(config=config)
```

## Testing Configuration

For testing, you might want to use a separate test database:

```python
# In your test configuration
TEST_DATABASE_URL = "postgresql://test_user:test_pass@localhost/test_cardano_db"
```
