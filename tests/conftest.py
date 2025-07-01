"""
Pytest configuration and fixtures for dbsync-py tests.

This module provides shared fixtures and configuration for all test modules.
"""

import os
from collections.abc import Generator

import pytest

# Import all fixtures from fixtures module
from tests.fixtures import *

# Import performance monitoring fixtures
try:
    from tests.performance.fixtures import *
except ImportError:
    # Performance monitoring dependencies not available
    pass


def has_dbsync_env() -> bool:
    """
    Check if DBSync environment variables are configured.

    Returns:
        True if DBSync environment is available for integration testing
    """
    # Check if full database URL is available
    if os.getenv("DBSYNC_DATABASE_URL"):
        return True

    # Check if individual components are available (at minimum host, database, and username)
    host = os.getenv("DBSYNC_HOST")
    database = os.getenv("DBSYNC_DB_NAME")
    username = os.getenv("DBSYNC_USER")
    password = os.getenv("DBSYNC_PASS")

    # Need at minimum host, database, and username for integration tests
    return bool(host and database and username and password)


@pytest.fixture
def mock_env_vars() -> Generator[None, None, None]:
    """
    Mock environment variables for testing.

    Yields:
        None (context manager for mocked environment)
    """
    original_env = dict(os.environ)

    # Set test environment variables
    test_env = {
        "DBSYNC_HOST": "localhost",
        "DBSYNC_PORT": "5432",
        "DBSYNC_DB_NAME": "test_cexplorer",
        "DBSYNC_USER": "test_user",
        "DBSYNC_PASS": "test_password",
        "DBSYNC_DEFAULT_ASYNC_MODE": "false",
    }

    os.environ.update(test_env)

    try:
        yield
    finally:
        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)


@pytest.fixture
def dbsync_config():
    """
    Get DBSync database configuration for integration tests.

    Returns:
        DatabaseConfig instance using environment variables

    Raises:
        pytest.skip: If DBSync environment not available
    """
    if not has_dbsync_env():
        pytest.skip(
            "DBSync environment variables not available. "
            "Set DBSYNC_DATABASE_URL or DBSYNC_HOST/DBSYNC_DB_NAME/DBSYNC_USER/DBSYNC_PASS to run integration tests."
        )

    try:
        from dbsync.config import DatabaseConfig

        config = DatabaseConfig()

        # Validate the config can generate URLs
        sync_url = config.to_url(async_driver=False)
        async_url = config.to_url(async_driver=True)

        if not sync_url or not async_url:
            pytest.skip(
                "Invalid database configuration - cannot generate connection URLs"
            )

        return config

    except Exception as e:
        pytest.skip(f"Failed to create database configuration: {e}")


@pytest.fixture
def dbsync_session(dbsync_config):
    """
    Get synchronous DBSync database session for integration tests.

    Args:
        dbsync_config: Database configuration

    Yields:
        SQLModel Session connected to DBSync database with .exec() method
    """
    from sqlalchemy import text
    from sqlmodel import Session, create_engine

    try:
        # Create engine with SQLModel-compatible configuration
        engine = create_engine(
            dbsync_config.to_url(),
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False,  # Set to True for SQL debugging
        )

        with Session(engine) as session:
            # Test connection before yielding
            session.exec(text("SELECT 1"))
            yield session

    except Exception as e:
        pytest.skip(f"Database not available for integration tests: {e}")


@pytest.fixture
async def dbsync_async_session(dbsync_config):
    """
    Get asynchronous DBSync database session for integration tests.

    Args:
        dbsync_config: Database configuration

    Yields:
        SQLModel AsyncSession connected to DBSync database with .exec() method
    """
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlmodel.ext.asyncio.session import AsyncSession

    try:
        # Create async engine with proper async configuration
        engine = create_async_engine(
            dbsync_config.to_url(async_driver=True),
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False,  # Set to True for SQL debugging
        )

        async with AsyncSession(engine) as session:
            # Test connection before yielding
            await session.exec(text("SELECT 1"))
            yield session

    except Exception as e:
        pytest.skip(f"Async database not available for integration tests: {e}")


@pytest.fixture(autouse=True)
def clear_sqlmodel_metadata():
    """Clear SQLModel metadata between tests to prevent table redefinition errors."""
    from sqlmodel import SQLModel

    # Clear all tables from the metadata
    SQLModel.metadata.clear()

    yield

    # Clean up after test completes
    SQLModel.metadata.clear()


# Pytest configuration
def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest with custom settings."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line(
        "markers", "async_test: mark test as requiring async support"
    )


# Asyncio configuration for async tests
pytest_plugins = ("pytest_asyncio",)
