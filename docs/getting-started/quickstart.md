# Quick Start

Get up and running with dbsync-py in minutes.

## Database Connection

First, ensure you have access to a Cardano DB Sync database:

```python
from dbsync_py import create_session

# Create a session
session = create_session("postgresql://user:password@localhost:5432/cardano_db")
```

## Your First Query

```python
from dbsync_py import Block

# Get the latest 5 blocks
latest_blocks = session.query(Block).order_by(Block.block_no.desc()).limit(5).all()

for block in latest_blocks:
    print(f"Block {block.block_no}: {block.hash.hex()}")
```

## Async Example

```python
import asyncio
from dbsync_py import create_async_session, Block
from sqlalchemy import select

async def main():
    async with create_async_session("postgresql+asyncpg://user:password@localhost:5432/cardano_db") as session:
        result = await session.execute(
            select(Block).order_by(Block.block_no.desc()).limit(5)
        )
        blocks = result.scalars().all()

        for block in blocks:
            print(f"Block {block.block_no}: {block.hash.hex()}")

asyncio.run(main())
```

## Next Steps

- [Configuration Guide](configuration.md) - Learn about database configuration
- [User Guide](../user-guide/connection.md) - Comprehensive usage guide
- [Examples](../examples/basic.md) - More practical examples
