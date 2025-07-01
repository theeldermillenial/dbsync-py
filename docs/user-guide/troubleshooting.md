# Troubleshooting Guide

This guide covers common issues, solutions, and best practices when working with dbsync-py.

## Common Connection Issues

### Database Connection Failures

#### Problem: "Connection refused" or "Could not connect to server"

**Symptoms:**
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server: Connection refused
```

**Solutions:**

1. **Check Database Service**:
   ```bash
   # Check if PostgreSQL is running
   sudo systemctl status postgresql

   # Start if not running
   sudo systemctl start postgresql
   ```

2. **Verify Connection Parameters**:
   ```python
   from dbsync.utils.connection_test import test_connection

   # Test your connection string
   connection_string = "postgresql://user:password@localhost:5432/cexplorer"
   result = test_connection(connection_string)

   if not result["success"]:
       print(f"Connection failed: {result['error']}")
   ```

3. **Check Network Configuration**:
   ```bash
   # Test network connectivity
   telnet localhost 5432

   # Check if port is open
   netstat -tlnp | grep 5432
   ```

#### Problem: "Authentication failed"

**Symptoms:**
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) FATAL: password authentication failed for user
```

**Solutions:**

1. **Verify Credentials**:
   ```python
   import os
   from dbsync.config import Config

   # Check configuration
   config = Config()
   print(f"Database URL: {config.database_url}")

   # Test with explicit credentials
   test_url = "postgresql://correct_user:correct_password@localhost:5432/cexplorer"
   ```

2. **Check PostgreSQL Authentication**:
   ```bash
   # Edit pg_hba.conf if needed
   sudo nano /etc/postgresql/13/main/pg_hba.conf

   # Reload PostgreSQL configuration
   sudo systemctl reload postgresql
   ```

#### Problem: "Database does not exist"

**Symptoms:**
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) FATAL: database "cexplorer" does not exist
```

**Solutions:**

1. **Verify Database Name**:
   ```bash
   # List available databases
   psql -U postgres -l

   # Connect to correct database
   psql -U postgres -d cexplorer
   ```

2. **Check DB Sync Setup**:
   ```bash
   # Verify cardano-db-sync created the database
   sudo -u postgres psql -c "\l" | grep cexplorer
   ```

### SSL/TLS Connection Issues

#### Problem: SSL connection errors

**Solutions:**

1. **Disable SSL for Local Connections**:
   ```python
   # Add sslmode parameter
   database_url = "postgresql://user:password@localhost:5432/cexplorer?sslmode=disable"
   ```

2. **Configure SSL Properly**:
   ```python
   # For remote connections with SSL
   database_url = "postgresql://user:password@remote:5432/cexplorer?sslmode=require"
   ```

## Performance Issues

### Slow Query Performance

#### Problem: Queries taking too long

**Diagnosis:**

1. **Enable Query Logging**:
   ```python
   import logging

   # Enable SQLAlchemy query logging
   logging.basicConfig()
   logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

   # Your queries will now be logged
   ```

2. **Profile Query Execution**:
   ```python
   import time
   from dbsync.session import create_session
   from dbsync.models import Transaction

   session = create_session()

   start_time = time.time()
   result = session.query(Transaction).limit(1000).all()
   end_time = time.time()

   print(f"Query took {end_time - start_time:.2f} seconds")
   ```

**Solutions:**

1. **Use Proper Indexing**:
   ```python
   # Good: Use indexed columns
   tx = session.query(Transaction).filter(
       Transaction.hash == tx_hash  # hash is indexed
   ).first()

   # Avoid: Non-indexed column searches
   # tx = session.query(Transaction).filter(
   #     Transaction.size > 1000  # size is not indexed
   # ).first()
   ```

2. **Implement Pagination**:
   ```python
   def get_transactions_page(session, page=1, page_size=100):
       offset = (page - 1) * page_size
       return session.query(Transaction).offset(offset).limit(page_size).all()

   # Use pagination instead of loading all data
   page_1 = get_transactions_page(session, page=1)
   ```

3. **Use Eager Loading**:
   ```python
   from sqlalchemy.orm import joinedload, selectinload

   # Load related objects to avoid N+1 queries
   transactions = session.query(Transaction).options(
       joinedload(Transaction.block),
       selectinload(Transaction.outputs)
   ).limit(100).all()

   # Now accessing tx.block won't trigger additional queries
   for tx in transactions:
       print(f"Transaction in block {tx.block.block_no}")
   ```

### Memory Issues

#### Problem: High memory usage or out-of-memory errors

**Solutions:**

1. **Use Session Batching**:
   ```python
   def process_large_dataset(session, batch_size=1000):
       offset = 0
       while True:
           batch = session.query(Transaction).offset(offset).limit(batch_size).all()
           if not batch:
               break

           # Process batch
           for tx in batch:
               process_transaction(tx)

           # Clear session to free memory
           session.expunge_all()
           offset += batch_size
   ```

2. **Use Streaming Queries**:
   ```python
   def stream_transactions(session):
       """Stream transactions without loading all into memory."""
       query = session.query(Transaction)

       for tx in query.yield_per(1000):  # Yield in batches of 1000
           yield tx

   # Usage
   for tx in stream_transactions(session):
       process_transaction(tx)
   ```

3. **Close Sessions Properly**:
   ```python
   # Always close sessions
   session = create_session()
   try:
       # Your operations
       pass
   finally:
       session.close()

   # Or use context manager
   from contextlib import contextmanager

   @contextmanager
   def get_session():
       session = create_session()
       try:
           yield session
       finally:
           session.close()

   with get_session() as session:
       # Your operations
       pass
   ```

## Data Consistency Issues

### Stale Data Problems

#### Problem: Getting outdated information

**Solutions:**

1. **Check Database Sync Status**:
   ```python
   from dbsync.models import Block
   from sqlalchemy import func
   from datetime import datetime, timedelta

   def check_db_sync_status(session):
       # Get latest block
       latest_block = session.query(Block).order_by(Block.block_no.desc()).first()

       if latest_block:
           time_diff = datetime.utcnow() - latest_block.time
           print(f"Latest block: {latest_block.block_no}")
           print(f"Block time: {latest_block.time}")
           print(f"Time behind: {time_diff}")

           if time_diff > timedelta(minutes=10):
               print("WARNING: Database appears to be behind!")

       return latest_block
   ```

2. **Refresh Session Data**:
   ```python
   # Refresh object from database
   session.refresh(block_object)

   # Or start a new session for fresh data
   session.close()
   session = create_session()
   ```

### Foreign Key Constraint Errors

#### Problem: Referential integrity issues

**Solutions:**

1. **Check Data Integrity**:
   ```python
   def check_referential_integrity(session):
       """Check for common referential integrity issues."""

       # Check for orphaned transactions
       orphaned_txs = session.query(Transaction).filter(
           ~Transaction.block_id.in_(session.query(Block.id_))
       ).count()

       if orphaned_txs > 0:
           print(f"Found {orphaned_txs} orphaned transactions!")

       # Check for orphaned transaction outputs
       orphaned_outputs = session.query(TransactionOutput).filter(
           ~TransactionOutput.tx_id.in_(session.query(Transaction.id_))
       ).count()

       if orphaned_outputs > 0:
           print(f"Found {orphaned_outputs} orphaned outputs!")
   ```

## Model and Type Issues

### Type Conversion Errors

#### Problem: Bytes/hex conversion issues

**Symptoms:**
```
TypeError: expected bytes, got str
ValueError: non-hexadecimal number found in fromhex() arg
```

**Solutions:**

1. **Proper Hash Handling**:
   ```python
   # Converting hex string to bytes for database queries
   tx_hash_str = "a1b2c3d4e5f6..."
   tx_hash_bytes = bytes.fromhex(tx_hash_str)

   tx = session.query(Transaction).filter(
       Transaction.hash == tx_hash_bytes
   ).first()

   # Converting bytes back to hex for display
   if tx:
       print(f"Transaction hash: {tx.hash.hex()}")
   ```

2. **Handle None Values**:
   ```python
   def safe_hex_conversion(hash_bytes):
       """Safely convert hash bytes to hex string."""
       if hash_bytes is None:
           return None
       return hash_bytes.hex()

   # Usage
   tx_hash = safe_hex_conversion(transaction.hash)
   ```

3. **Validate Input Data**:
   ```python
   def validate_tx_hash(hash_str):
       """Validate transaction hash format."""
       if not hash_str:
           raise ValueError("Hash cannot be empty")

       if len(hash_str) != 64:
           raise ValueError("Transaction hash must be 64 characters")

       try:
           bytes.fromhex(hash_str)
       except ValueError:
           raise ValueError("Invalid hexadecimal characters in hash")

       return hash_str.lower()
   ```

### Model Relationship Issues

#### Problem: Lazy loading errors

**Symptoms:**
```
DetachedInstanceError: Instance is not bound to a Session
```

**Solutions:**

1. **Use Eager Loading**:
   ```python
   # Load related objects upfront
   from sqlalchemy.orm import joinedload

   transaction = session.query(Transaction).options(
       joinedload(Transaction.block),
       joinedload(Transaction.outputs)
   ).filter(Transaction.id_ == tx_id).first()

   # Now you can access relationships even after session closes
   session.close()
   print(f"Transaction in block {transaction.block.block_no}")
   ```

2. **Keep Session Open**:
   ```python
   # Keep session open while accessing relationships
   with get_session() as session:
       transaction = session.query(Transaction).get(tx_id)

       # Access relationships while session is active
       block_no = transaction.block.block_no
       output_count = len(transaction.outputs)
   ```

3. **Detach and Merge Objects**:
   ```python
   # Detach object from session
   session.expunge(transaction)

   # Later, merge back into new session
   new_session = create_session()
   transaction = new_session.merge(transaction)
   ```

## Async/Await Issues

### Async Session Problems

#### Problem: "RuntimeError: There is no current event loop"

**Solutions:**

1. **Proper Event Loop Management**:
   ```python
   import asyncio
   from dbsync.session import create_async_session

   async def main():
       session = create_async_session()
       try:
           # Your async operations
           pass
       finally:
           await session.close()

   # Run with proper event loop
   if __name__ == "__main__":
       asyncio.run(main())
   ```

2. **Avoid Mixing Sync and Async**:
   ```python
   # Wrong: Don't mix sync and async
   # session = create_session()  # Sync session
   # await session.execute(stmt)  # Async operation

   # Correct: Use async session for async operations
   async_session = create_async_session()
   result = await async_session.execute(stmt)
   ```

#### Problem: "coroutine was never awaited"

**Solutions:**

1. **Await All Async Operations**:
   ```python
   # Wrong: Forgetting await
   # result = session.execute(stmt)

   # Correct: Always await async operations
   result = await session.execute(stmt)
   data = result.scalars().all()
   ```

## Best Practices Summary

### Connection Management

1. **Use Connection Pooling**:
   ```python
   from sqlalchemy import create_engine
   from sqlalchemy.pool import QueuePool

   engine = create_engine(
       database_url,
       poolclass=QueuePool,
       pool_size=20,
       max_overflow=30,
       pool_pre_ping=True
   )
   ```

2. **Always Close Sessions**:
   ```python
   # Use context managers
   with get_session() as session:
       # Operations
       pass

   # Or explicit try/finally
   session = create_session()
   try:
       # Operations
       pass
   finally:
       session.close()
   ```

### Query Optimization

1. **Use Appropriate Loading Strategies**:
   ```python
   # For one-to-one/many-to-one: joinedload
   transactions = session.query(Transaction).options(
       joinedload(Transaction.block)
   ).all()

   # For one-to-many: selectinload
   blocks = session.query(Block).options(
       selectinload(Block.transactions)
   ).all()
   ```

2. **Implement Proper Pagination**:
   ```python
   def paginate_query(query, page, page_size):
       offset = (page - 1) * page_size
       return query.offset(offset).limit(page_size)
   ```

3. **Use Indexes Wisely**:
   ```python
   # Filter on indexed columns
   # Good: hash, id, foreign keys
   # Avoid: non-indexed columns for large datasets
   ```

### Error Handling

1. **Implement Retry Logic**:
   ```python
   import time
   from sqlalchemy.exc import OperationalError

   def retry_on_connection_error(func, max_retries=3):
       for attempt in range(max_retries):
           try:
               return func()
           except OperationalError as e:
               if attempt == max_retries - 1:
                   raise e
               time.sleep(2 ** attempt)  # Exponential backoff
   ```

2. **Validate Input Data**:
   ```python
   def validate_epoch_number(epoch_no):
       if not isinstance(epoch_no, int):
           raise TypeError("Epoch number must be an integer")
       if epoch_no < 0:
           raise ValueError("Epoch number cannot be negative")
       return epoch_no
   ```

### Monitoring and Debugging

1. **Enable Logging**:
   ```python
   import logging

   # Enable SQL query logging for debugging
   logging.basicConfig(level=logging.INFO)
   logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
   ```

2. **Monitor Performance**:
   ```python
   import time

   def time_query(func):
       start = time.time()
       result = func()
       end = time.time()
       print(f"Query took {end - start:.2f} seconds")
       return result
   ```

This troubleshooting guide should help resolve most common issues encountered when working with dbsync-py. For issues not covered here, check the project's GitHub issues or create a new issue with detailed information about your problem.
