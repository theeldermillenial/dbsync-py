# Installation

## Requirements

- Python 3.12 or higher (including Python 3.13)
- PostgreSQL database with Cardano DB Sync data
- pip or uv for package management

## Python 3.13 Compatibility

dbsync-py fully supports Python 3.13. We've addressed compatibility issues with the pycardano dependency by configuring pytest to ignore `FutureWarning` messages that occur due to deprecated `functools.partial` usage in Enum definitions within the upstream library. This ensures smooth operation while waiting for upstream fixes.

## Install from PyPI

```bash
pip install dbsync-py
```

## Install from Source

```bash
git clone https://github.com/your-org/dbsync-py.git
cd dbsync-py
pip install -e .
```

## Optional Dependencies

### Async Support
```bash
pip install dbsync-py[async]
```

### Documentation
```bash
pip install dbsync-py[docs]
```

### Development
```bash
pip install dbsync-py[dev]
```

## Verify Installation

```python
import dbsync_py
print(dbsync_py.__version__)
```
