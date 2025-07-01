"""
Integration test utilities and base classes for dbsync-py.

This module provides base classes and utilities for writing integration tests
that connect to actual DBSync PostgreSQL databases.
"""

from .base import BaseAsyncIntegrationTest, BaseIntegrationTest

__all__ = [
    "BaseAsyncIntegrationTest",
    "BaseIntegrationTest",
]
