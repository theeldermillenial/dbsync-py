# Async Usage Guide

dbsync-py provides full async support for high-performance applications. This guide covers async patterns, session management, and best practices.

## Basic Async Setup

### Creating Async Sessions

```python
import asyncio
from dbsync.session import create_async_session
from dbsync.models import Block, Transaction

async def main():
    # Create async session
    async_session = create_async_session()

    try:
        # Use the session
        result = await async_session.execute(
            select(Block).order_by(Block.block_no.desc()).limit(1)
        )
        latest_block = result.scalar_one_or_none()

        if latest_block:
            print(f"Latest block: {latest_block.block_no}")

    finally:
        await async_session.close()

# Run the async function
asyncio.run(main())
```

### Using Async Context Managers

```python
from contextlib import asynccontextmanager
from dbsync.session import create_async_session

@asynccontextmanager
async def get_async_session():
    """Context manager for async database sessions."""
    session = create_async_session()
    try:
        yield session
    finally:
        await session.close()

async def query_latest_blocks():
    async with get_async_session() as session:
        result = await session.execute(
            select(Block).order_by(Block.block_no.desc()).limit(10)
        )
        blocks = result.scalars().all()
        return blocks

# Usage
blocks = await query_latest_blocks()
for block in blocks:
    print(f"Block {block.block_no}: {block.tx_count} transactions")
```

## Common Async Query Patterns

### Basic Entity Retrieval

```python
from sqlalchemy import select
from dbsync.models import Transaction, Block

async def get_transaction_by_hash(session, tx_hash: str):
    """Get a transaction by its hash."""
    stmt = select(Transaction).where(
        Transaction.hash == bytes.fromhex(tx_hash)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def get_block_transactions(session, block_id: int):
    """Get all transactions in a block."""
    stmt = select(Transaction).where(Transaction.block_id == block_id)
    result = await session.execute(stmt)
    return result.scalars().all()

# Usage
async with get_async_session() as session:
    tx = await get_transaction_by_hash(session, "a1b2c3d4...")
    if tx:
        transactions = await get_block_transactions(session, tx.block_id)
        print(f"Block has {len(transactions)} transactions")
```

### Relationship Loading

```python
from sqlalchemy.orm import selectinload, joinedload

async def get_block_with_transactions(session, block_no: int):
    """Get a block with all its transactions loaded."""
    stmt = select(Block).options(
        selectinload(Block.transactions)
    ).where(Block.block_no == block_no)

    result = await session.execute(stmt)
    block = result.scalar_one_or_none()

    if block:
        # Transactions are already loaded, no additional DB calls
        print(f"Block {block.block_no} has {len(block.transactions)} transactions")
        for tx in block.transactions:
            print(f"  Transaction: {tx.hash.hex()[:16]}...")

    return block

# Usage
async with get_async_session() as session:
    block = await get_block_with_transactions(session, 1000000)
```

### Aggregation Queries

```python
from sqlalchemy import func, and_

async def get_epoch_statistics(session, epoch_no: int):
    """Get comprehensive statistics for an epoch."""

    # Transaction statistics
    tx_stats_stmt = select(
        func.count(Transaction.id_).label('tx_count'),
        func.sum(Transaction.fee).label('total_fees'),
        func.avg(Transaction.fee).label('avg_fee'),
        func.sum(Transaction.size).label('total_size')
    ).select_from(
        Transaction.join(Block)
    ).where(Block.epoch_no == epoch_no)

    result = await session.execute(tx_stats_stmt)
    tx_stats = result.first()

    # Block statistics
    block_stats_stmt = select(
        func.count(Block.id_).label('block_count'),
        func.min(Block.time).label('epoch_start'),
        func.max(Block.time).label('epoch_end')
    ).where(Block.epoch_no == epoch_no)

    result = await session.execute(block_stats_stmt)
    block_stats = result.first()

    return {
        'epoch': epoch_no,
        'transactions': tx_stats.tx_count,
        'total_fees': tx_stats.total_fees,
        'average_fee': float(tx_stats.avg_fee) if tx_stats.avg_fee else 0,
        'total_size': tx_stats.total_size,
        'blocks': block_stats.block_count,
        'epoch_start': block_stats.epoch_start,
        'epoch_end': block_stats.epoch_end
    }

# Usage
async with get_async_session() as session:
    stats = await get_epoch_statistics(session, 123)
    print(f"Epoch {stats['epoch']}: {stats['transactions']} transactions in {stats['blocks']} blocks")
```

## Concurrent Operations

### Parallel Queries

```python
import asyncio
from sqlalchemy import select

async def get_multiple_blocks(session, block_numbers: list[int]):
    """Get multiple blocks concurrently."""

    async def get_single_block(block_no: int):
        stmt = select(Block).where(Block.block_no == block_no)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    # Execute all queries concurrently
    tasks = [get_single_block(block_no) for block_no in block_numbers]
    blocks = await asyncio.gather(*tasks)

    return [block for block in blocks if block is not None]

# Usage
async with get_async_session() as session:
    block_numbers = [1000000, 1000001, 1000002, 1000003, 1000004]
    blocks = await get_multiple_blocks(session, block_numbers)
    print(f"Retrieved {len(blocks)} blocks")
```

### Concurrent Session Operations

```python
async def process_epoch_range(start_epoch: int, end_epoch: int):
    """Process multiple epochs concurrently with separate sessions."""

    async def process_single_epoch(epoch_no: int):
        async with get_async_session() as session:
            stats = await get_epoch_statistics(session, epoch_no)
            return stats

    # Process epochs concurrently
    tasks = [
        process_single_epoch(epoch)
        for epoch in range(start_epoch, end_epoch + 1)
    ]

    results = await asyncio.gather(*tasks)
    return results

# Usage
epoch_stats = await process_epoch_range(100, 110)
for stats in epoch_stats:
    print(f"Epoch {stats['epoch']}: {stats['transactions']} transactions")
```

## Streaming Large Datasets

### Async Iteration

```python
from sqlalchemy.ext.asyncio import AsyncSession

async def stream_transactions_in_epoch(session: AsyncSession, epoch_no: int, batch_size: int = 1000):
    """Stream transactions from an epoch in batches."""

    offset = 0
    while True:
        stmt = select(Transaction).join(Block).where(
            Block.epoch_no == epoch_no
        ).offset(offset).limit(batch_size)

        result = await session.execute(stmt)
        transactions = result.scalars().all()

        if not transactions:
            break

        # Yield this batch
        for tx in transactions:
            yield tx

        offset += batch_size

# Usage
async with get_async_session() as session:
    transaction_count = 0
    total_fees = 0

    async for tx in stream_transactions_in_epoch(session, 123):
        transaction_count += 1
        total_fees += tx.fee

        if transaction_count % 1000 == 0:
            print(f"Processed {transaction_count} transactions...")

    print(f"Total: {transaction_count} transactions, {total_fees} Lovelace in fees")
```

### Async Generators for Complex Processing

```python
async def analyze_address_activity(session: AsyncSession, address_bech32: str):
    """Analyze all activity for an address using async generator."""

    # Get address
    addr_stmt = select(Address).where(Address.view == address_bech32)
    result = await session.execute(addr_stmt)
    addr = result.scalar_one_or_none()

    if not addr:
        return

    # Stream all outputs to this address
    offset = 0
    batch_size = 1000

    while True:
        outputs_stmt = select(TransactionOutput).where(
            TransactionOutput.address_id == addr.id_
        ).offset(offset).limit(batch_size)

        result = await session.execute(outputs_stmt)
        outputs = result.scalars().all()

        if not outputs:
            break

        for output in outputs:
            # Check if this output is spent
            spent_stmt = select(TransactionInput).where(
                TransactionInput.tx_out_id == output.id_
            )
            spent_result = await session.execute(spent_stmt)
            spent = spent_result.scalar_one_or_none()

            yield {
                'output': output,
                'is_spent': spent is not None,
                'spending_tx': spent.tx_id if spent else None
            }

        offset += batch_size

# Usage
async with get_async_session() as session:
    utxo_count = 0
    total_value = 0

    async for activity in analyze_address_activity(session, "addr1..."):
        if not activity['is_spent']:
            utxo_count += 1
            total_value += activity['output'].value

    print(f"Address has {utxo_count} UTXOs worth {total_value} Lovelace")
```

## Error Handling and Resilience

### Async Retry Logic

```python
import asyncio
from sqlalchemy.exc import OperationalError

async def execute_with_retry(async_func, max_retries: int = 3, delay: float = 1.0):
    """Execute an async function with retry logic."""

    for attempt in range(max_retries):
        try:
            return await async_func()
        except OperationalError as e:
            if attempt == max_retries - 1:
                raise e

            print(f"Database error on attempt {attempt + 1}, retrying in {delay}s...")
            await asyncio.sleep(delay)
            delay *= 2  # Exponential backoff

async def robust_query_example():
    """Example of robust async querying with retries."""

    async def query_function():
        async with get_async_session() as session:
            stmt = select(Block).order_by(Block.block_no.desc()).limit(1)
            result = await session.execute(stmt)
            return result.scalar_one()

    try:
        latest_block = await execute_with_retry(query_function)
        return latest_block
    except Exception as e:
        print(f"Failed to get latest block after retries: {e}")
        return None
```

### Connection Pool Management

```python
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import QueuePool

# Configure async engine with connection pooling
async_engine = create_async_engine(
    "postgresql+asyncpg://user:password@localhost/dbsync",
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,  # Validate connections
    pool_recycle=3600,   # Recycle connections after 1 hour
    echo=False  # Set to True for SQL debugging
)

async def get_pooled_session():
    """Get session from connection pool."""
    from sqlalchemy.ext.asyncio import AsyncSession

    return AsyncSession(async_engine)

# Usage with proper cleanup
async def main():
    session = get_pooled_session()
    try:
        # Your database operations
        stmt = select(Block).limit(10)
        result = await session.execute(stmt)
        blocks = result.scalars().all()

        for block in blocks:
            print(f"Block {block.block_no}")

    finally:
        await session.close()

# Clean up engine when done
await async_engine.dispose()
```

## FastAPI Integration

### Async Dependency Injection

```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()

async def get_async_db():
    """Dependency to provide async database session."""
    session = create_async_session()
    try:
        yield session
    finally:
        await session.close()

@app.get("/blocks/latest")
async def get_latest_blocks(
    limit: int = 10,
    db: AsyncSession = Depends(get_async_db)
):
    """Get latest blocks asynchronously."""
    stmt = select(Block).order_by(Block.block_no.desc()).limit(limit)
    result = await db.execute(stmt)
    blocks = result.scalars().all()

    return [
        {
            "block_no": block.block_no,
            "hash": block.hash.hex(),
            "time": block.time,
            "tx_count": block.tx_count
        }
        for block in blocks
    ]

@app.get("/transactions/{tx_hash}")
async def get_transaction(
    tx_hash: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Get transaction by hash asynchronously."""
    try:
        stmt = select(Transaction).where(
            Transaction.hash == bytes.fromhex(tx_hash)
        )
        result = await db.execute(stmt)
        tx = result.scalar_one_or_none()

        if not tx:
            raise HTTPException(status_code=404, detail="Transaction not found")

        return {
            "hash": tx.hash.hex(),
            "fee": tx.fee,
            "size": tx.size,
            "block_id": tx.block_id
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid transaction hash format")
```

## Performance Optimization

### Async Batch Operations

```python
async def batch_process_addresses(session: AsyncSession, addresses: list[str], batch_size: int = 100):
    """Process multiple addresses in batches."""

    results = []

    for i in range(0, len(addresses), batch_size):
        batch = addresses[i:i + batch_size]

        # Create queries for this batch
        tasks = []
        for address in batch:
            stmt = select(Address).where(Address.view == address)
            task = session.execute(stmt)
            tasks.append(task)

        # Execute batch concurrently
        batch_results = await asyncio.gather(*tasks)

        # Process results
        for result in batch_results:
            addr = result.scalar_one_or_none()
            if addr:
                results.append(addr)

    return results

# Usage
async with get_async_session() as session:
    addresses = ["addr1...", "addr2...", "addr3..."]  # Many addresses
    found_addresses = await batch_process_addresses(session, addresses)
    print(f"Found {len(found_addresses)} valid addresses")
```

### Memory-Efficient Streaming

```python
async def export_epoch_data(session: AsyncSession, epoch_no: int, output_file: str):
    """Export epoch data to file efficiently."""

    import json

    with open(output_file, 'w') as f:
        f.write('[\n')

        first_record = True
        offset = 0
        batch_size = 1000

        while True:
            stmt = select(Transaction).join(Block).where(
                Block.epoch_no == epoch_no
            ).offset(offset).limit(batch_size)

            result = await session.execute(stmt)
            transactions = result.scalars().all()

            if not transactions:
                break

            for tx in transactions:
                if not first_record:
                    f.write(',\n')

                tx_data = {
                    'hash': tx.hash.hex(),
                    'fee': tx.fee,
                    'size': tx.size
                }

                json.dump(tx_data, f)
                first_record = False

            offset += batch_size

            # Allow other tasks to run
            await asyncio.sleep(0)

        f.write('\n]')

# Usage
async with get_async_session() as session:
    await export_epoch_data(session, 123, 'epoch_123_transactions.json')
    print("Export completed")
```

This comprehensive async guide covers all major patterns for high-performance async operations with dbsync-py, from basic queries to complex concurrent processing scenarios.
