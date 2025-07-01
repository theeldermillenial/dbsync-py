"""dbsync-py: Python helper package for Cardano DB Sync.

This package provides SQLModel-based ORM models and utilities for interacting
with Cardano DB Sync PostgreSQL databases, enabling type-safe access to
Cardano blockchain data.

For query examples and implementations, see the dbsync.examples package.
"""

__version__ = "1.0.0-dev5"

# Import configuration utilities
# Import main modules when they are implemented
# from . import models
from . import (
    config,
    examples,  # Query examples and patterns
    queries,  # Available for utilities, examples are separate
    session,
    utils,
)

# Main exports (will be populated as modules are implemented)
__all__ = [
    "__version__",
    "config",
    "examples",  # Query examples
    "queries",  # Available for query utilities
    "session",
    "utils",
    # Future exports will be added here
    # "models",
]


def main() -> None:
    """Entry point for the dbsync-py CLI tool."""
    print(f"dbsync-py v{__version__}")
    print("Python helper package for Cardano DB Sync")
    print("Package structure initialized - ready for development!")

    # Quick connection test
    try:
        from .utils import quick_connection_check

        if quick_connection_check():
            print("✅ Database connection: Available")
        else:
            print("❌ Database connection: Not available (check configuration)")
    except Exception as e:
        print(f"⚠️  Database connection test failed: {e}")
