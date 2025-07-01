# dbsync-py

**Python helper package for Cardano DB Sync databases**

[![PyPI version](https://badge.fury.io/py/dbsync-py.svg)](https://badge.fury.io/py/dbsync-py)
[![Python Support](https://img.shields.io/pypi/pyversions/dbsync-py.svg)](https://pypi.org/project/dbsync-py/)
[![License](https://img.shields.io/github/license/your-org/dbsync-py.svg)](https://github.com/your-org/dbsync-py/blob/main/LICENSE)

## Overview

`dbsync-py` is a modern Python package that provides a convenient interface for working with [Cardano DB Sync](https://github.com/IntersectMBO/cardano-db-sync) databases. It offers:

- **Type-safe database models** using SQLModel (SQLAlchemy + Pydantic)
- **Both synchronous and asynchronous** database operations
- **Comprehensive schema coverage** of Cardano DB Sync tables
- **Query utilities and examples** for common Cardano data analysis tasks
- **Modern Python practices** with full type hints and documentation

## Key Features

### 🏗️ **Modern Architecture**
Built with SQLModel for the best of both SQLAlchemy and Pydantic, providing excellent developer experience with full type safety.

### 🔄 **Sync & Async Support**
Choose between synchronous and asynchronous database operations based on your application needs.

### 📊 **Complete Schema Coverage**
Models for all major Cardano DB Sync tables including blocks, transactions, UTXOs, staking, governance, and more.

### 🎯 **Query Examples**
Practical examples for common Cardano blockchain analysis tasks, from basic queries to complex staking analytics.

### 🔧 **Developer Friendly**
Comprehensive documentation, type hints, and testing make it easy to build reliable Cardano applications.

## Quick Start

### Installation

```bash
pip install dbsync-py
```

### Basic Usage

```python
from dbsync_py import create_session, Block

# Create a database session
session = create_session("postgresql://user:pass@localhost/cardano_db")

# Query the latest blocks
latest_blocks = session.query(Block).order_by(Block.block_no.desc()).limit(10).all()

for block in latest_blocks:
    print(f"Block {block.block_no}: {block.hash.hex()}")
```

### Async Usage

```python
import asyncio
from dbsync_py import create_async_session, Block

async def get_latest_blocks():
    async with create_async_session("postgresql+asyncpg://user:pass@localhost/cardano_db") as session:
        result = await session.execute(
            select(Block).order_by(Block.block_no.desc()).limit(10)
        )
        blocks = result.scalars().all()

        for block in blocks:
            print(f"Block {block.block_no}: {block.hash.hex()}")

asyncio.run(get_latest_blocks())
```

## What's Included

### Database Models
- **Core Models**: Block, Transaction, TransactionOutput, TransactionInput
- **Staking Models**: StakePool, Delegation, Reward, Epoch
- **Governance Models**: Proposal, Vote, DrepRegistration
- **Metadata Models**: TransactionMetadata, PoolMetadata
- **And many more...**

### Query Utilities
- Connection management and configuration
- Query builders for common patterns
- Pagination and filtering helpers
- Type conversion utilities

### Examples & Tutorials
- Basic blockchain queries
- Staking pool analysis
- Transaction tracking
- DeFi protocol analysis
- Custom query patterns

## Documentation Structure

- **[Getting Started](getting-started/installation.md)**: Installation and basic setup
- **[User Guide](user-guide/connection.md)**: Comprehensive usage guide
- **[API Reference](api/models.md)**: Complete API documentation
- **[Examples](examples/basic.md)**: Practical code examples
- **[Development](development/contributing.md)**: Contributing and development info

## Requirements

- **Python**: 3.12+
- **PostgreSQL**: Compatible with Cardano DB Sync schema
- **Cardano DB Sync**: Any recent version (tested with v13.6+)

## Community & Support

- **GitHub**: [Report issues and contribute](https://github.com/your-org/dbsync-py)
- **PyPI**: [Package releases](https://pypi.org/project/dbsync-py/)
- **Documentation**: [Full documentation](https://dbsync-py.readthedocs.io/)

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/your-org/dbsync-py/blob/main/LICENSE) file for details.

---

!!! tip "Getting Started"
    Ready to dive in? Start with the [Installation Guide](getting-started/installation.md) or jump straight to the [Quick Start](getting-started/quickstart.md) tutorial.

!!! info "About Cardano DB Sync"
    This package is designed to work with databases created by [Cardano DB Sync](https://github.com/IntersectMBO/cardano-db-sync), the official Cardano blockchain indexer maintained by IOG and the Cardano community.
