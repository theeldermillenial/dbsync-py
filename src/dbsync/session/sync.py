"""Synchronous database session management for dbsync-py.

This module provides synchronous database session factories and connection
utilities for Cardano DB Sync PostgreSQL databases using psycopg.
"""

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from ..config import get_database_url

__all__ = [
    "check_connection",
    "create_engine_sync",
    "get_session",
    "get_session_factory",
    "validate_connection",
]


def create_engine_sync(
    database_url: str | None = None,
    echo: bool = False,
    pool_size: int = 5,
    max_overflow: int = 10,
    **kwargs,
) -> Engine:
    """Create synchronous SQLAlchemy engine for Cardano DB Sync.

    Args:
        database_url: Database URL (uses config if None)
        echo: Enable SQL logging (default: False)
        pool_size: Connection pool size (default: 5)
        max_overflow: Maximum overflow connections (default: 10)
        **kwargs: Additional engine parameters

    Returns:
        Configured SQLAlchemy engine

    Raises:
        SQLAlchemyError: If engine creation fails
    """
    url = database_url or get_database_url()

    try:
        engine = create_engine(
            url,
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,  # Validate connections before use
            pool_recycle=3600,  # Recycle connections after 1 hour
            **kwargs,
        )
        return engine

    except Exception as e:
        raise SQLAlchemyError(f"Failed to create database engine: {e}") from e


def get_session_factory(
    database_url: str | None = None, **engine_kwargs
) -> sessionmaker[Session]:
    """Create session factory for synchronous database operations.

    Args:
        database_url: Database URL (uses config if None)
        **engine_kwargs: Additional engine parameters

    Returns:
        Configured session factory

    Raises:
        SQLAlchemyError: If session factory creation fails
    """
    engine = create_engine_sync(database_url, **engine_kwargs)

    return sessionmaker(
        bind=engine,
        autoflush=False,  # Manual transaction control
        autocommit=False,
        expire_on_commit=False,  # Keep objects accessible after commit
    )


def get_session(database_url: str | None = None, **engine_kwargs) -> Session:
    """Create single synchronous database session.

    Args:
        database_url: Database URL (uses config if None)
        **engine_kwargs: Additional engine parameters

    Returns:
        Configured database session

    Raises:
        SQLAlchemyError: If session creation fails

    Note:
        Caller is responsible for closing the session.
        Consider using get_session_context() for automatic cleanup.
    """
    factory = get_session_factory(database_url, **engine_kwargs)
    return factory()


@contextmanager
def get_session_context(
    database_url: str | None = None, **engine_kwargs
) -> Generator[Session, None, None]:
    """Context manager for synchronous database sessions with automatic cleanup.

    Args:
        database_url: Database URL (uses config if None)
        **engine_kwargs: Additional engine parameters

    Yields:
        Configured database session

    Raises:
        SQLAlchemyError: If session operations fail

    Example:
        with get_session_context() as session:
            result = session.execute(text("SELECT version()"))
            print(result.scalar())
    """
    session = get_session(database_url, **engine_kwargs)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def validate_connection(database_url: str | None = None) -> bool:
    """Validate database connection without raising exceptions.

    Args:
        database_url: Database URL to validate (uses config if None)

    Returns:
        True if connection successful, False otherwise
    """
    try:
        with get_session_context(database_url) as session:
            session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def check_connection(database_url: str | None = None) -> dict[str, str]:
    """Check database connection and return detailed information.

    Args:
        database_url: Database URL to test (uses config if None)

    Returns:
        Dictionary with connection test results

    Raises:
        SQLAlchemyError: If connection test fails
    """
    try:
        with get_session_context(database_url) as session:
            # Test basic connectivity
            version_result = session.execute(text("SELECT version()"))
            postgres_version = version_result.scalar()

            # Test DB Sync specific table (should exist in any DB Sync instance)
            schema_result = session.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_name = 'schema_version'"
                )
            )
            has_dbsync_schema = schema_result.scalar() is not None

            return {
                "status": "success",
                "postgres_version": postgres_version or "unknown",
                "has_dbsync_schema": str(has_dbsync_schema),
                "url": database_url or get_database_url(),
            }

    except Exception as e:
        raise SQLAlchemyError(f"Database connection test failed: {e}") from e
