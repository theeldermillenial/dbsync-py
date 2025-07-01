"""Info command implementation.

Provides CLI interface for showing package information and configuration.
"""

import importlib.util
import sys

import click

from ..config import DatabaseConfig, get_version


def show_info(
    check_connection: bool = False,
    show_config: bool = False,
    verbose: bool = False,
) -> None:
    """Show information about the dbsync-py installation and configuration.

    Args:
        check_connection: Test database connection
        show_config: Show current configuration
        verbose: Enable verbose output
    """
    lines = []

    # Package information
    lines.append("=" * 60)
    lines.append("DBSYNC-PY PACKAGE INFORMATION")
    lines.append("=" * 60)
    lines.append(f"Version: {get_version()}")
    lines.append(f"Python: {sys.version.split()[0]}")
    lines.append(f"Platform: {sys.platform}")
    lines.append("")

    # Configuration information
    if show_config:
        lines.append("CONFIGURATION")
        lines.append("-" * 30)
        try:
            config = DatabaseConfig()
            lines.append(f"Database Host: {config.host}")
            lines.append(f"Database Port: {config.port}")
            lines.append(f"Database Name: {config.database}")
            lines.append(f"Database User: {config.user}")
            lines.append(f"SSL Mode: {config.sslmode}")
            lines.append(f"Pool Size: {config.pool_size}")
            lines.append(f"Max Overflow: {config.max_overflow}")
            lines.append("")
        except Exception as e:
            lines.append(f"❌ Configuration Error: {e}")
            lines.append("")

    # Connection test
    if check_connection:
        lines.append("CONNECTION TEST")
        lines.append("-" * 30)
        try:
            from ..session import get_session

            if verbose:
                click.echo("Testing database connection...")

            with get_session() as session:
                # Simple test query
                from sqlalchemy import text

                result = session.execute(text("SELECT 1 as test")).fetchone()
                if result and result[0] == 1:
                    lines.append("✅ Database connection successful")
                else:
                    lines.append("❌ Database connection failed: Invalid response")
        except ImportError:
            lines.append(
                "❌ Database connection test unavailable: Missing dependencies"
            )
        except Exception as e:
            lines.append(f"❌ Database connection failed: {e}")
        lines.append("")

    # Feature availability
    lines.append("FEATURE AVAILABILITY")
    lines.append("-" * 30)

    # Check for optional dependencies
    features = [
        ("Schema Validation", _has_schema_validation),
        ("Performance Benchmarks", _has_benchmark_utils),
        ("Database Connection", _has_database_functionality),
        ("Async Support", _has_async_functionality),
    ]

    for feature_name, check_func in features:
        try:
            available = check_func()
            status = "✅ Available" if available else "❌ Unavailable"
        except Exception as e:
            status = f"❌ Error: {e}"

        lines.append(f"{feature_name}: {status}")

    lines.append("")

    # Usage examples
    lines.append("USAGE EXAMPLES")
    lines.append("-" * 30)
    lines.append("dbsync-py validate              # Validate schema")
    lines.append("dbsync-py validate --coverage-only  # Show coverage only")
    lines.append("dbsync-py benchmark             # Run benchmarks")
    lines.append("dbsync-py benchmark --quick     # Quick benchmarks")
    lines.append("dbsync-py info --check-connection  # Test connection")
    lines.append("dbsync-py --help                # Show help")

    click.echo("\n".join(lines))


def _has_schema_validation() -> bool:
    """Check if schema validation functionality is available."""
    return importlib.util.find_spec("schema_validation.schema_validator") is not None


def _has_benchmark_utils() -> bool:
    """Check if benchmark utilities are available."""
    return importlib.util.find_spec("benchmarks.benchmark_utils") is not None


def _has_database_functionality() -> bool:
    """Check if database functionality is available."""
    return importlib.util.find_spec("dbsync.session") is not None


def _has_async_functionality() -> bool:
    """Check if async functionality is available."""
    return importlib.util.find_spec("dbsync.session") is not None
