# Installation

## Requirements

- Python 3.12 or higher
- PostgreSQL database with Cardano DB Sync data
- pip or uv for package management

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
