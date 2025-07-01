"""Database configuration management for dbsync-py.

This module provides configuration utilities for managing database connection
parameters and URLs for Cardano DB Sync PostgreSQL databases.
"""

import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlunparse

from dotenv import load_dotenv


def get_version() -> str:
    """Get the package version.

    Returns:
        Package version string
    """
    # Try to get version from package metadata
    try:
        from importlib.metadata import version

        return version("dbsync-py")
    except ImportError:
        # Fallback for older Python versions
        try:
            import pkg_resources

            return pkg_resources.get_distribution("dbsync-py").version
        except Exception:
            return "0.1.0"  # Fallback version


# Load environment variables from .env file if it exists
_env_loaded = False

# Global configuration state
_default_async_mode: bool | None = None


def _ensure_env_loaded() -> None:
    """Ensure .env file is loaded (only once)."""
    global _env_loaded
    if not _env_loaded:
        # Look for .env file in current directory, then parent directories
        env_path = Path.cwd() / ".env"
        if not env_path.exists():
            # Try parent directory (common for src/ structure)
            env_path = Path.cwd().parent / ".env"

        if env_path.exists():
            load_dotenv(env_path)
        else:
            # Try to load from any .env file in the path
            load_dotenv()

        _env_loaded = True


def set_default_async_mode(async_mode: bool) -> None:
    """Set the default async mode for unified sessions.

    Args:
        async_mode: True for async sessions by default, False for sync
    """
    global _default_async_mode
    _default_async_mode = async_mode


def get_default_async_mode() -> bool:
    """Get the current default async mode.

    Returns:
        Current default async mode (False if not set)
    """
    global _default_async_mode

    # Check if explicitly set
    if _default_async_mode is not None:
        return _default_async_mode

    # Check environment variable
    _ensure_env_loaded()
    env_async = os.getenv("DBSYNC_DEFAULT_ASYNC_MODE")
    if env_async is not None:
        return env_async.lower() in ("true", "1", "yes", "on")

    # Default to sync mode
    return False


def reset_default_async_mode() -> None:
    """Reset default async mode to None (will use environment or default to False)."""
    global _default_async_mode
    _default_async_mode = None


__all__ = [
    "DatabaseConfig",
    "get_async_database_url",
    "get_database_url",
    "get_default_async_mode",
    "get_version",
    "reset_default_async_mode",
    "set_default_async_mode",
    "validate_database_url",
]


class DatabaseConfig:
    """Database configuration container with validation."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        database: str | None = None,
        username: str | None = None,
        password: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize database configuration.

        Configuration is loaded from environment variables (including .env file)
        with the following precedence:
        1. Explicit parameters passed to this constructor
        2. Environment variables (DBSYNC_HOST, DBSYNC_PORT, etc.)
        3. Default values

        Args:
            host: PostgreSQL host (default: from DBSYNC_HOST or localhost)
            port: PostgreSQL port (default: from DBSYNC_PORT or 5432)
            database: Database name (default: from DBSYNC_DB_NAME or cexplorer)
            username: Database username (default: from DBSYNC_USER or None)
            password: Database password (default: from DBSYNC_PASS or None)
            **kwargs: Additional connection parameters
        """
        # Ensure environment variables are loaded
        _ensure_env_loaded()

        # Load configuration with precedence: params > env vars > defaults
        self.host = host or os.getenv("DBSYNC_HOST", "localhost")
        self.port = port or int(os.getenv("DBSYNC_PORT", "5432"))
        self.database = database or os.getenv("DBSYNC_DB_NAME", "cexplorer")
        self.username = username or os.getenv("DBSYNC_USER")
        self.password = password or os.getenv("DBSYNC_PASS")
        self.extra_params = kwargs

    def to_url(self, async_driver: bool = False) -> str:
        """Convert configuration to database URL.

        Args:
            async_driver: If True, use asyncpg driver scheme

        Returns:
            Database URL string
        """
        scheme = "postgresql+asyncpg" if async_driver else "postgresql+psycopg"

        # Build authority part (user:pass@host:port)
        authority = self.host
        if self.port != 5432:
            authority = f"{authority}:{self.port}"

        if self.username:
            if self.password:
                authority = f"{self.username}:{self.password}@{authority}"
            else:
                authority = f"{self.username}@{authority}"

        return f"{scheme}://{authority}/{self.database}"


def get_database_url(url: str | None = None) -> str:
    """Get synchronous database URL from environment or parameter.

    Configuration is loaded from environment variables (including .env file)
    with the following precedence:
    1. Explicit url parameter
    2. DBSYNC_DATABASE_URL environment variable
    3. Individual environment variables (DBSYNC_HOST, DBSYNC_PORT, etc.)
    4. Default values

    Args:
        url: Explicit database URL (optional)

    Returns:
        Database URL for synchronous connections

    Raises:
        ValueError: If URL format is invalid
    """
    # Ensure environment variables are loaded
    _ensure_env_loaded()

    if url:
        return validate_database_url(url)

    env_url = os.getenv("DBSYNC_DATABASE_URL")
    if env_url:
        return validate_database_url(env_url)

    # Build from individual environment variables or defaults
    config = DatabaseConfig()
    return config.to_url(async_driver=False)


def get_async_database_url(url: str | None = None) -> str:
    """Get asynchronous database URL from environment or parameter.

    Configuration is loaded from environment variables (including .env file)
    with the following precedence:
    1. Explicit url parameter
    2. DBSYNC_DATABASE_URL environment variable
    3. Individual environment variables (DBSYNC_HOST, DBSYNC_PORT, etc.)
    4. Default values

    Args:
        url: Explicit database URL (optional)

    Returns:
        Database URL for asynchronous connections

    Raises:
        ValueError: If URL format is invalid
    """
    # Ensure environment variables are loaded
    _ensure_env_loaded()

    if url:
        base_url = validate_database_url(url)
        # Convert to async scheme if needed
        parsed = urlparse(base_url)
        if not parsed.scheme.endswith("+asyncpg"):
            scheme = "postgresql+asyncpg"
            parsed = parsed._replace(scheme=scheme)
            return urlunparse(parsed)
        return base_url

    env_url = os.getenv("DBSYNC_DATABASE_URL")
    if env_url:
        return get_async_database_url(env_url)

    # Build from individual environment variables or defaults
    config = DatabaseConfig()
    return config.to_url(async_driver=True)


def validate_database_url(url: str) -> str:
    """Validate database URL format.

    Args:
        url: Database URL to validate

    Returns:
        Validated URL

    Raises:
        ValueError: If URL format is invalid
    """
    if not url:
        raise ValueError("Database URL cannot be empty")

    try:
        parsed = urlparse(url)

        # Check for valid PostgreSQL schemes
        valid_schemes = {
            "postgresql",
            "postgresql+psycopg",
            "postgresql+asyncpg",
            "postgres",
            "postgres+psycopg",
            "postgres+asyncpg",
        }

        if parsed.scheme not in valid_schemes:
            raise ValueError(
                f"Invalid scheme '{parsed.scheme}'. Must be one of: {valid_schemes}"
            )

        if not parsed.hostname:
            raise ValueError("Database URL must include hostname")

        if not parsed.path or parsed.path == "/":
            raise ValueError("Database URL must include database name")

        return url

    except Exception as e:
        raise ValueError(f"Invalid database URL format: {e}") from e
