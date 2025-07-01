"""Connection testing utilities for dbsync-py.

This module provides simple utilities to test database connectivity and
validate Cardano DB Sync database configurations.
"""

import asyncio
from typing import Any

from ..config import get_async_database_url, get_database_url, validate_database_url
from ..session.async_ import check_async_connection
from ..session.sync import check_connection, validate_connection

__all__ = [
    "check_all_connections",
    "check_async_connection_wrapper",
    "check_sync_connection",
    "format_connection_results",
    "quick_connection_check",
]


def check_sync_connection(database_url: str | None = None) -> dict[str, Any]:
    """Test synchronous database connection with detailed reporting.

    Args:
        database_url: Database URL to test (uses config if None)

    Returns:
        Dictionary with test results and connection information
    """
    try:
        # Validate URL format first
        url = database_url or get_database_url()
        validate_database_url(url)

        # Test connection
        result = check_connection(url)
        result["connection_type"] = "synchronous"
        return result

    except Exception as e:
        return {
            "status": "failed",
            "connection_type": "synchronous",
            "error": str(e),
            "url": database_url or "default_config",
        }


def check_async_connection_wrapper(
    database_url: str | None = None,
) -> dict[str, Any]:
    """Test asynchronous database connection with detailed reporting.

    Args:
        database_url: Database URL to test (uses config if None)

    Returns:
        Dictionary with test results and connection information
    """
    try:
        # Validate URL format first
        url = database_url or get_async_database_url()
        validate_database_url(url)

        # Run async test
        result = asyncio.run(check_async_connection(url))
        result["connection_type"] = "asynchronous"
        return result

    except Exception as e:
        return {
            "status": "failed",
            "connection_type": "asynchronous",
            "error": str(e),
            "url": database_url or "default_config",
        }


def check_all_connections(
    database_url: str | None = None,
) -> dict[str, dict[str, Any]]:
    """Test both synchronous and asynchronous database connections.

    Args:
        database_url: Database URL to test (uses config if None)

    Returns:
        Dictionary with results for both connection types
    """
    return {
        "sync": check_sync_connection(database_url),
        "async": check_async_connection_wrapper(database_url),
    }


def quick_connection_check(database_url: str | None = None) -> bool:
    """Quick boolean check for database connectivity.

    Args:
        database_url: Database URL to test (uses config if None)

    Returns:
        True if connection successful, False otherwise
    """
    try:
        return validate_connection(database_url)
    except Exception:
        return False


def format_connection_results(results: dict[str, Any]) -> None:
    """Pretty print connection test results.

    Args:
        results: Results from test_sync_connection or test_async_connection_wrapper
    """
    print(f"\n=== {results['connection_type'].title()} Connection Test ===")

    if results["status"] == "success":
        print("✅ Connection: SUCCESS")
        print(f"📊 PostgreSQL Version: {results.get('postgres_version', 'unknown')}")
        print(
            f"🗄️  DB Sync Schema: {'✅ Found' if results.get('has_dbsync_schema') == 'True' else '❌ Not Found'}"
        )
        print(f"🔗 URL: {results.get('url', 'unknown')}")
    else:
        print("❌ Connection: FAILED")
        print(f"💥 Error: {results.get('error', 'unknown')}")
        print(f"🔗 URL: {results.get('url', 'unknown')}")
