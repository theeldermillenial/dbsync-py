"""Asynchronous database session management for dbsync-py.

This module provides asynchronous database session factories and connection
utilities for Cardano DB Sync PostgreSQL databases using asyncpg.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ..config import get_async_database_url

__all__ = [
    "check_async_connection",
    "create_engine_async",
    "get_async_session",
    "get_async_session_factory",
    "validate_async_connection",
]


def create_engine_async(
    database_url: str | None = None,
    echo: bool = False,
    pool_size: int = 5,
    max_overflow: int = 10,
    **kwargs,
) -> AsyncEngine:
    """Create asynchronous SQLAlchemy engine for Cardano DB Sync.

    Args:
        database_url: Database URL (uses config if None)
        echo: Enable SQL logging (default: False)
        pool_size: Connection pool size (default: 5)
        max_overflow: Maximum overflow connections (default: 10)
        **kwargs: Additional engine parameters

    Returns:
        Configured async SQLAlchemy engine

    Raises:
        SQLAlchemyError: If engine creation fails
    """
    url = database_url or get_async_database_url()

    try:
        engine = create_async_engine(
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
        raise SQLAlchemyError(f"Failed to create async database engine: {e}") from e


def get_async_session_factory(
    database_url: str | None = None, **engine_kwargs
) -> async_sessionmaker[AsyncSession]:
    """Create async session factory for asynchronous database operations.

    Args:
        database_url: Database URL (uses config if None)
        **engine_kwargs: Additional engine parameters

    Returns:
        Configured async session factory

    Raises:
        SQLAlchemyError: If session factory creation fails
    """
    engine = create_engine_async(database_url, **engine_kwargs)

    return async_sessionmaker(
        bind=engine,
        autoflush=False,  # Manual transaction control
        autocommit=False,
        expire_on_commit=False,  # Keep objects accessible after commit
    )


def get_async_session(database_url: str | None = None, **engine_kwargs) -> AsyncSession:
    """Create single asynchronous database session.

    Args:
        database_url: Database URL (uses config if None)
        **engine_kwargs: Additional engine parameters

    Returns:
        Configured async database session

    Raises:
        SQLAlchemyError: If session creation fails

    Note:
        Caller is responsible for closing the session.
        Consider using get_async_session_context() for automatic cleanup.
    """
    factory = get_async_session_factory(database_url, **engine_kwargs)
    return factory()


@asynccontextmanager
async def get_async_session_context(
    database_url: str | None = None, **engine_kwargs
) -> AsyncGenerator[AsyncSession, None]:
    """Async context manager for database sessions with automatic cleanup.

    Args:
        database_url: Database URL (uses config if None)
        **engine_kwargs: Additional engine parameters

    Yields:
        Configured async database session

    Raises:
        SQLAlchemyError: If session operations fail

    Example:
        async with get_async_session_context() as session:
            result = await session.execute(text("SELECT version()"))
            print(result.scalar())
    """
    session = get_async_session(database_url, **engine_kwargs)
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def validate_async_connection(database_url: str | None = None) -> bool:
    """Validate async database connection without raising exceptions.

    Args:
        database_url: Database URL to validate (uses config if None)

    Returns:
        True if connection successful, False otherwise
    """
    try:
        async with get_async_session_context(database_url) as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def check_async_connection(database_url: str | None = None) -> dict[str, str]:
    """Check async database connection and return detailed information.

    Args:
        database_url: Database URL to test (uses config if None)

    Returns:
        Dictionary with connection test results

    Raises:
        SQLAlchemyError: If connection test fails
    """
    try:
        async with get_async_session_context(database_url) as session:
            # Test basic connectivity
            version_result = await session.execute(text("SELECT version()"))
            postgres_version = version_result.scalar()

            # Test DB Sync specific table (should exist in any DB Sync instance)
            schema_result = await session.execute(
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
                "url": database_url or get_async_database_url(),
            }

    except Exception as e:
        raise SQLAlchemyError(f"Async database connection test failed: {e}") from e
