"""Utility functions for type conversion, validation, and helpers.

This module contains utility functions for converting between PostgreSQL
custom types and Python types, validation helpers, and other common
functionality used throughout the package.
"""

# Connection testing utilities
from .connection_test import (
    check_all_connections,
    check_async_connection_wrapper,
    check_sync_connection,
    format_connection_results,
    quick_connection_check,
)

__all__ = [
    "check_all_connections",
    "check_async_connection_wrapper",
    # Connection testing utilities
    "check_sync_connection",
    "format_connection_results",
    "quick_connection_check",
    # Future utility functions will be added here
    # Type conversion utilities (to be implemented)
    # "hex_to_bytes",
    # "bytes_to_hex",
    # "lovelace_to_ada",
    # Validation utilities (to be implemented)
    # "validate_hash",
    # "validate_address",
]
