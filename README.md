# dbsync-py

[![Test Suite](https://github.com/TheElderMillenial/dbsync-py/actions/workflows/test.yml/badge.svg)](https://github.com/TheElderMillenial/dbsync-py/actions/workflows/test.yml)
[![Documentation](https://github.com/TheElderMillenial/dbsync-py/actions/workflows/docs.yml/badge.svg)](https://github.com/TheElderMillenial/dbsync-py/actions/workflows/docs.yml)
[![PyPI version](https://badge.fury.io/py/dbsync-py.svg)](https://badge.fury.io/py/dbsync-py)
[![Python Support](https://img.shields.io/pypi/pyversions/dbsync-py.svg)](https://pypi.org/project/dbsync-py/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Python helper package for interacting with Cardano DB Sync databases.

This package provides SQLModel-based ORM models and utilities for interacting with Cardano DB Sync PostgreSQL databases, enabling type-safe access to Cardano blockchain data.

## Installation

```bash
pip install dbsync-py
```

## Configuration

dbsync-py supports multiple ways to configure database connections:

### Option 1: Environment File (.env)

Copy `sample.env` to `.env` and modify the values:

```bash
cp sample.env .env
# Edit .env with your database configuration
```

### Option 2: Environment Variables

Set environment variables directly:

```bash
export DBSYNC_HOST=localhost
export DBSYNC_PORT=5432
export DBSYNC_DATABASE=cexplorer
export DBSYNC_USERNAME=your_username
export DBSYNC_PASSWORD=your_password
```

### Option 3: Complete Database URL

```bash
export DBSYNC_DATABASE_URL=postgresql://username:password@localhost:5432/cexplorer
```

## Quick Start

```python
import dbsync_py

# Test database connection
from dbsync_py.utils import quick_connection_check
if quick_connection_check():
    print("✅ Database connection successful!")
else:
    print("❌ Database connection failed")

# Use database sessions
from dbsync_py.session import get_session_context
with get_session_context() as session:
    result = session.execute("SELECT version()")
    print(result.scalar())
```

## Development Status

This project is currently in development. Core database connection utilities are implemented.

## License

Apache-2.0
