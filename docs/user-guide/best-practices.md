# Best Practices Guide

This guide outlines best practices for developing applications with dbsync-py, covering performance, security, maintainability, and production deployment considerations.

## Application Architecture

### Layered Architecture Pattern

```python
# data_layer.py - Database access layer
from dbsync.session import create_session
from dbsync.models import Transaction, Block
from contextlib import contextmanager

class DataAccess:
    """Data access layer for database operations."""

    def __init__(self, database_url: str):
        self.database_url = database_url

    @contextmanager
    def get_session(self):
        session = create_session(self.database_url)
        try:
            yield session
        finally:
            session.close()

    def get_transaction_by_hash(self, tx_hash: str):
        with self.get_session() as session:
            return session.query(Transaction).filter(
                Transaction.hash == bytes.fromhex(tx_hash)
            ).first()

# business_layer.py - Business logic layer
from typing import Optional, Dict, Any

class TransactionService:
    """Business logic for transaction operations."""

    def __init__(self, data_access: DataAccess):
        self.data_access = data_access

    def get_transaction_summary(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Get a summary of transaction information."""
        tx = self.data_access.get_transaction_by_hash(tx_hash)

        if not tx:
            return None

        return {
            "hash": tx_hash,
            "fee_ada": tx.fee / 1_000_000,
            "size_kb": tx.size / 1024,
            "block_height": tx.block.block_no if tx.block else None
        }

# api_layer.py - API/presentation layer
from fastapi import FastAPI, HTTPException

app = FastAPI()
data_access = DataAccess("postgresql://...")
tx_service = TransactionService(data_access)

@app.get("/transaction/{tx_hash}")
async def get_transaction(tx_hash: str):
    summary = tx_service.get_transaction_summary(tx_hash)
    if not summary:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return summary
```

### Dependency Injection

```python
# config.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class DatabaseConfig:
    url: str
    pool_size: int = 20
    max_overflow: int = 30
    echo: bool = False

@dataclass
class AppConfig:
    database: DatabaseConfig
    cache_ttl: int = 300
    api_rate_limit: int = 100

# services.py
from abc import ABC, abstractmethod

class CacheService(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int) -> None:
        pass

class RedisCacheService(CacheService):
    def __init__(self, redis_url: str):
        import redis
        self.redis = redis.from_url(redis_url)

    def get(self, key: str) -> Optional[Any]:
        import json
        value = self.redis.get(key)
        return json.loads(value) if value else None

    def set(self, key: str, value: Any, ttl: int) -> None:
        import json
        self.redis.setex(key, ttl, json.dumps(value))

# dependency_container.py
class Container:
    def __init__(self, config: AppConfig):
        self.config = config
        self.data_access = DataAccess(config.database.url)
        self.cache_service = RedisCacheService("redis://localhost")
        self.transaction_service = TransactionService(
            self.data_access,
            self.cache_service
        )
```

## Performance Optimization

### Connection Pooling

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import sessionmaker

class OptimizedDataAccess:
    """Data access with optimized connection pooling."""

    def __init__(self, database_url: str):
        # Configure engine with proper pooling
        self.engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=20,          # Number of connections to maintain
            max_overflow=30,       # Additional connections when needed
            pool_pre_ping=True,    # Validate connections before use
            pool_recycle=3600,     # Recycle connections after 1 hour
            echo=False             # Set to True for SQL debugging
        )

        self.SessionLocal = sessionmaker(bind=self.engine)

    @contextmanager
    def get_session(self):
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()

    def close_all_connections(self):
        """Close all connections in the pool."""
        self.engine.dispose()
```

### Query Optimization Patterns

```python
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import and_, or_, func

class OptimizedQueryService:
    """Service with optimized query patterns."""

    def __init__(self, data_access: OptimizedDataAccess):
        self.data_access = data_access

    def get_transactions_with_details(self, block_id: int, limit: int = 100):
        """Get transactions with related data using eager loading."""

        with self.data_access.get_session() as session:
            return session.query(Transaction).options(
                joinedload(Transaction.block),  # One-to-one relationship
                selectinload(Transaction.inputs),  # One-to-many relationship
                selectinload(Transaction.outputs)
            ).filter(
                Transaction.block_id == block_id
            ).limit(limit).all()

    def get_address_utxos_optimized(self, address_ids: list[int]):
        """Optimized UTXO query for multiple addresses."""

        with self.data_access.get_session() as session:
            # Use a single query instead of multiple
            spent_output_ids = session.query(TransactionInput.tx_out_id).distinct()

            return session.query(TransactionOutput).filter(
                and_(
                    TransactionOutput.address_id.in_(address_ids),
                    ~TransactionOutput.id_.in_(spent_output_ids)
                )
            ).all()

    def get_epoch_statistics_batch(self, epoch_range: tuple):
        """Get statistics for multiple epochs efficiently."""

        start_epoch, end_epoch = epoch_range

        with self.data_access.get_session() as session:
            # Single query for all epochs
            return session.query(
                Block.epoch_no,
                func.count(Transaction.id_).label('tx_count'),
                func.sum(Transaction.fee).label('total_fees'),
                func.avg(Transaction.size).label('avg_size')
            ).join(Transaction).filter(
                Block.epoch_no.between(start_epoch, end_epoch)
            ).group_by(Block.epoch_no).all()
```

### Caching Strategies

```python
from functools import wraps
import hashlib
import json

def cache_result(cache_service: CacheService, ttl: int = 300):
    """Decorator for caching function results."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key_data = {
                'func': func.__name__,
                'args': args,
                'kwargs': kwargs
            }
            cache_key = hashlib.md5(
                json.dumps(key_data, sort_keys=True).encode()
            ).hexdigest()

            # Try to get from cache
            result = cache_service.get(cache_key)
            if result is not None:
                return result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_service.set(cache_key, result, ttl)
            return result

        return wrapper
    return decorator

class CachedTransactionService:
    """Transaction service with caching."""

    def __init__(self, data_access: DataAccess, cache_service: CacheService):
        self.data_access = data_access
        self.cache_service = cache_service

    @cache_result(cache_service, ttl=600)  # Cache for 10 minutes
    def get_transaction_summary(self, tx_hash: str):
        """Cached transaction summary."""
        return super().get_transaction_summary(tx_hash)

    @cache_result(cache_service, ttl=3600)  # Cache for 1 hour
    def get_epoch_statistics(self, epoch_no: int):
        """Cached epoch statistics."""
        with self.data_access.get_session() as session:
            return session.query(
                func.count(Transaction.id_),
                func.sum(Transaction.fee)
            ).join(Block).filter(
                Block.epoch_no == epoch_no
            ).first()
```

## Error Handling and Resilience

### Comprehensive Error Handling

```python
from sqlalchemy.exc import (
    OperationalError, IntegrityError, DataError,
    DatabaseError, TimeoutError
)
from typing import Optional, TypeVar, Callable
import logging
import time

T = TypeVar('T')

class DatabaseService:
    """Service with comprehensive error handling."""

    def __init__(self, data_access: DataAccess):
        self.data_access = data_access
        self.logger = logging.getLogger(__name__)

    def execute_with_retry(
        self,
        operation: Callable[[], T],
        max_retries: int = 3,
        base_delay: float = 1.0
    ) -> Optional[T]:
        """Execute database operation with retry logic."""

        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                return operation()

            except OperationalError as e:
                last_exception = e
                if "connection" in str(e).lower():
                    self.logger.warning(f"Connection error on attempt {attempt + 1}: {e}")
                else:
                    self.logger.error(f"Operational error: {e}")
                    break

            except (IntegrityError, DataError) as e:
                # Don't retry on data integrity issues
                self.logger.error(f"Data integrity error: {e}")
                break

            except TimeoutError as e:
                last_exception = e
                self.logger.warning(f"Timeout on attempt {attempt + 1}: {e}")

            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                break

            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)  # Exponential backoff
                self.logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)

        self.logger.error(f"Operation failed after {max_retries + 1} attempts")
        raise last_exception if last_exception else Exception("Operation failed")

    def safe_get_transaction(self, tx_hash: str) -> Optional[Transaction]:
        """Safely get transaction with error handling."""

        def operation():
            with self.data_access.get_session() as session:
                return session.query(Transaction).filter(
                    Transaction.hash == bytes.fromhex(tx_hash)
                ).first()

        try:
            return self.execute_with_retry(operation)
        except Exception as e:
            self.logger.error(f"Failed to get transaction {tx_hash}: {e}")
            return None
```

### Circuit Breaker Pattern

```python
from enum import Enum
import time

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    """Circuit breaker for database operations."""

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""

        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time < self.timeout:
                raise Exception("Circuit breaker is OPEN")
            else:
                self.state = CircuitState.HALF_OPEN

        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result

        except self.expected_exception as e:
            self.on_failure()
            raise e

    def on_success(self):
        """Handle successful operation."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def on_failure(self):
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

class ResilientDatabaseService:
    """Database service with circuit breaker."""

    def __init__(self, data_access: DataAccess):
        self.data_access = data_access
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            timeout=30,
            expected_exception=OperationalError
        )

    def get_transaction_with_protection(self, tx_hash: str):
        """Get transaction with circuit breaker protection."""

        def operation():
            with self.data_access.get_session() as session:
                return session.query(Transaction).filter(
                    Transaction.hash == bytes.fromhex(tx_hash)
                ).first()

        return self.circuit_breaker.call(operation)
```

## Security Best Practices

### Input Validation

```python
import re
from typing import Union

class ValidationError(Exception):
    """Custom validation error."""
    pass

class InputValidator:
    """Input validation utilities."""

    @staticmethod
    def validate_tx_hash(tx_hash: str) -> str:
        """Validate transaction hash format."""
        if not tx_hash:
            raise ValidationError("Transaction hash cannot be empty")

        # Remove any whitespace
        tx_hash = tx_hash.strip()

        # Check length (64 hex characters)
        if len(tx_hash) != 64:
            raise ValidationError("Transaction hash must be 64 characters long")

        # Check hex format
        if not re.match(r'^[0-9a-fA-F]{64}$', tx_hash):
            raise ValidationError("Transaction hash must contain only hexadecimal characters")

        return tx_hash.lower()

    @staticmethod
    def validate_epoch_number(epoch_no: Union[int, str]) -> int:
        """Validate epoch number."""
        try:
            epoch_int = int(epoch_no)
        except (ValueError, TypeError):
            raise ValidationError("Epoch number must be a valid integer")

        if epoch_int < 0:
            raise ValidationError("Epoch number cannot be negative")

        if epoch_int > 1000000:  # Reasonable upper bound
            raise ValidationError("Epoch number seems unreasonably large")

        return epoch_int

    @staticmethod
    def validate_address(address: str) -> str:
        """Validate Cardano address format."""
        if not address:
            raise ValidationError("Address cannot be empty")

        address = address.strip()

        # Basic format checks for bech32 addresses
        if not (address.startswith(('addr1', 'stake1', 'pool1', 'drep1')) or
                re.match(r'^[0-9a-fA-F]+$', address)):
            raise ValidationError("Invalid address format")

        return address

class SecureTransactionService:
    """Transaction service with input validation."""

    def __init__(self, data_access: DataAccess):
        self.data_access = data_access
        self.validator = InputValidator()

    def get_transaction(self, tx_hash: str):
        """Get transaction with validated input."""
        validated_hash = self.validator.validate_tx_hash(tx_hash)

        with self.data_access.get_session() as session:
            return session.query(Transaction).filter(
                Transaction.hash == bytes.fromhex(validated_hash)
            ).first()
```

### SQL Injection Prevention

```python
# ALWAYS use parameterized queries through SQLAlchemy ORM or text() with bound parameters

# ✅ GOOD: Using ORM (automatically parameterized)
def get_transactions_by_epoch_safe(session, epoch_no: int):
    return session.query(Transaction).join(Block).filter(
        Block.epoch_no == epoch_no  # Automatically parameterized
    ).all()

# ✅ GOOD: Using text() with bound parameters
from sqlalchemy import text

def get_custom_query_safe(session, epoch_no: int):
    sql = text("""
        SELECT t.id, t.hash, t.fee
        FROM tx t
        JOIN block b ON t.block_id = b.id
        WHERE b.epoch_no = :epoch_no
    """)
    return session.execute(sql, {"epoch_no": epoch_no}).fetchall()

# ❌ BAD: String interpolation (vulnerable to SQL injection)
def get_transactions_unsafe(session, epoch_no):
    # NEVER DO THIS
    sql = f"SELECT * FROM tx WHERE epoch_no = {epoch_no}"
    return session.execute(sql).fetchall()
```

## Production Deployment

### Configuration Management

```python
# config.py
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class DatabaseConfig:
    url: str
    pool_size: int = 20
    max_overflow: int = 30
    echo: bool = False

    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        return cls(
            url=os.getenv('DATABASE_URL', 'postgresql://localhost/cexplorer'),
            pool_size=int(os.getenv('DB_POOL_SIZE', '20')),
            max_overflow=int(os.getenv('DB_MAX_OVERFLOW', '30')),
            echo=os.getenv('DB_ECHO', 'false').lower() == 'true'
        )

@dataclass
class LoggingConfig:
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    @classmethod
    def from_env(cls) -> 'LoggingConfig':
        return cls(
            level=os.getenv('LOG_LEVEL', 'INFO'),
            format=os.getenv('LOG_FORMAT', cls.format)
        )

@dataclass
class AppConfig:
    database: DatabaseConfig
    logging: LoggingConfig
    debug: bool = False

    @classmethod
    def from_env(cls) -> 'AppConfig':
        return cls(
            database=DatabaseConfig.from_env(),
            logging=LoggingConfig.from_env(),
            debug=os.getenv('DEBUG', 'false').lower() == 'true'
        )
```

### Monitoring and Logging

```python
import logging
import time
from functools import wraps
from typing import Any, Callable

def setup_logging(config: LoggingConfig):
    """Configure application logging."""
    logging.basicConfig(
        level=getattr(logging, config.level.upper()),
        format=config.format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('app.log')
        ]
    )

def log_performance(logger: logging.Logger):
    """Decorator to log function performance."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"{func.__name__} completed in {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"{func.__name__} failed after {duration:.3f}s: {e}")
                raise
        return wrapper
    return decorator

class MetricsCollector:
    """Collect application metrics."""

    def __init__(self):
        self.query_count = 0
        self.total_query_time = 0.0
        self.error_count = 0

    def record_query(self, duration: float):
        """Record query execution metrics."""
        self.query_count += 1
        self.total_query_time += duration

    def record_error(self):
        """Record error occurrence."""
        self.error_count += 1

    def get_stats(self) -> dict:
        """Get current statistics."""
        avg_query_time = (
            self.total_query_time / self.query_count
            if self.query_count > 0 else 0
        )

        return {
            "query_count": self.query_count,
            "total_query_time": self.total_query_time,
            "avg_query_time": avg_query_time,
            "error_count": self.error_count
        }

class MonitoredDataAccess(OptimizedDataAccess):
    """Data access with monitoring."""

    def __init__(self, config: DatabaseConfig):
        super().__init__(config.url)
        self.logger = logging.getLogger(__name__)
        self.metrics = MetricsCollector()

    @contextmanager
    def get_session(self):
        start_time = time.time()
        session = self.SessionLocal()
        try:
            yield session
            duration = time.time() - start_time
            self.metrics.record_query(duration)
            self.logger.debug(f"Session completed in {duration:.3f}s")
        except Exception as e:
            self.metrics.record_error()
            self.logger.error(f"Session failed: {e}")
            raise
        finally:
            session.close()
```

### Health Checks

```python
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class HealthStatus:
    healthy: bool
    details: Dict[str, Any]

class HealthChecker:
    """Application health checker."""

    def __init__(self, data_access: MonitoredDataAccess):
        self.data_access = data_access

    def check_database(self) -> HealthStatus:
        """Check database connectivity and performance."""
        try:
            start_time = time.time()

            with self.data_access.get_session() as session:
                # Simple query to test connectivity
                result = session.execute("SELECT 1").scalar()

            duration = time.time() - start_time

            if duration > 5.0:  # Slow response
                return HealthStatus(
                    healthy=False,
                    details={
                        "status": "slow",
                        "response_time": duration,
                        "message": "Database response time is too slow"
                    }
                )

            return HealthStatus(
                healthy=True,
                details={
                    "status": "ok",
                    "response_time": duration
                }
            )

        except Exception as e:
            return HealthStatus(
                healthy=False,
                details={
                    "status": "error",
                    "error": str(e)
                }
            )

    def check_overall_health(self) -> Dict[str, Any]:
        """Comprehensive health check."""
        db_health = self.check_database()
        metrics = self.data_access.metrics.get_stats()

        overall_healthy = db_health.healthy

        return {
            "healthy": overall_healthy,
            "timestamp": time.time(),
            "checks": {
                "database": db_health.details
            },
            "metrics": metrics
        }

# Health check endpoint
from fastapi import FastAPI

app = FastAPI()
health_checker = HealthChecker(data_access)

@app.get("/health")
async def health_check():
    return health_checker.check_overall_health()
```

## Testing Best Practices

### Unit Testing

```python
import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

class TestTransactionService:
    """Unit tests for TransactionService."""

    @pytest.fixture
    def mock_data_access(self):
        return Mock(spec=DataAccess)

    @pytest.fixture
    def transaction_service(self, mock_data_access):
        return TransactionService(mock_data_access)

    def test_get_transaction_summary_success(self, transaction_service, mock_data_access):
        # Arrange
        mock_tx = Mock()
        mock_tx.fee = 150000
        mock_tx.size = 300
        mock_tx.block.block_no = 12345

        mock_session = Mock(spec=Session)
        mock_session.query().filter().first.return_value = mock_tx
        mock_data_access.get_session.return_value.__enter__.return_value = mock_session

        # Act
        result = transaction_service.get_transaction_summary("abc123")

        # Assert
        assert result is not None
        assert result["fee_ada"] == 0.15
        assert result["size_kb"] == 0.3
        assert result["block_height"] == 12345

    def test_get_transaction_summary_not_found(self, transaction_service, mock_data_access):
        # Arrange
        mock_session = Mock(spec=Session)
        mock_session.query().filter().first.return_value = None
        mock_data_access.get_session.return_value.__enter__.return_value = mock_session

        # Act
        result = transaction_service.get_transaction_summary("nonexistent")

        # Assert
        assert result is None
```

### Integration Testing

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

class TestDatabaseIntegration:
    """Integration tests with real database."""

    @pytest.fixture(scope="class")
    def postgres_container(self):
        with PostgresContainer("postgres:13") as postgres:
            yield postgres

    @pytest.fixture
    def test_session(self, postgres_container):
        engine = create_engine(postgres_container.get_connection_url())
        SessionLocal = sessionmaker(bind=engine)

        # Create tables (in real tests, you'd use migrations)
        # Base.metadata.create_all(bind=engine)

        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    def test_transaction_crud(self, test_session):
        # Test actual database operations
        pass
```

This comprehensive best practices guide provides a foundation for building robust, maintainable, and scalable applications with dbsync-py.
