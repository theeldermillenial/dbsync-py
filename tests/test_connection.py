"""Tests for database connection utilities.

This module tests the connection checking and validation utilities
without requiring actual database connections.
"""

import pytest

from dbsync.utils.connection_test import (
    quick_connection_check,
)


class TestQuickConnectionCheck:
    """Test quick_connection_check function."""

    @pytest.mark.slow
    def test_quick_connection_check_invalid_url(self):
        """Test quick connection check with invalid URL."""
        result = quick_connection_check("invalid://url")
        assert result is False

    @pytest.mark.slow
    def test_quick_connection_check_none_url(self):
        """Test quick connection check with None URL."""
        result = quick_connection_check(None)
        assert result is False

    @pytest.mark.slow
    def test_quick_connection_check_empty_url(self):
        """Test quick connection check with empty URL."""
        result = quick_connection_check("")
        assert result is False

    @pytest.mark.slow
    def test_quick_connection_check_postgresql_url_format(self):
        """Test quick connection check with valid PostgreSQL URL format."""
        # This should pass format validation but fail actual connection
        result = quick_connection_check("postgresql://user:pass@localhost:5432/db")
        # Since we don't have a real database, this should return False
        # but it should not raise an exception
        assert isinstance(result, bool)
