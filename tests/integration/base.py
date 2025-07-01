"""
Base classes and utilities for DBSync integration tests.

This module provides base test classes and common utilities for writing
integration tests against actual DBSync PostgreSQL databases.
"""

import logging
import re

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

# Set up logger for integration tests
logger = logging.getLogger(__name__)


def _validate_table_name(table_name: str) -> bool:
    """
    Validate table name to prevent SQL injection.

    Args:
        table_name: Name of the table to validate

    Returns:
        True if table name is safe to use in SQL queries
    """
    # Allow only alphanumeric characters, underscores, and periods
    # This covers standard table names and schema.table format
    pattern = r"^[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?$"
    return bool(re.match(pattern, table_name)) and len(table_name) <= 63


class BaseIntegrationTest:
    """
    Base class for synchronous integration tests.

    Provides common utilities and setup for testing against real DBSync databases.
    """

    def verify_database_connection(self, session: Session) -> bool:
        """
        Verify that database connection is working.

        Args:
            session: Database session

        Returns:
            True if connection is working
        """
        try:
            result = session.execute(text("SELECT 1 as test"))
            return result.fetchone()[0] == 1
        except Exception as e:
            logger.debug(f"Database connection verification failed: {e}")
            return False

    def get_table_count(self, session: Session, table_name: str) -> int:
        """
        Get count of records in a specific table.

        Args:
            session: Database session
            table_name: Name of the table to count

        Returns:
            Number of records in the table

        Raises:
            ValueError: If table name is invalid
            RuntimeError: If query execution fails
        """
        if not _validate_table_name(table_name):
            raise ValueError(f"Invalid table name: {table_name}")

        try:
            # Use parameterized query with identifier quoting
            # Note: SQLAlchemy's text() doesn't support identifier parameters,
            # so we validate the table name and use it directly
            result = session.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
            return result.fetchone()[0]
        except Exception as e:
            logger.error(f"Failed to get table count for {table_name}: {e}")
            raise RuntimeError(f"Failed to count records in table {table_name}") from e

    def verify_table_exists(self, session: Session, table_name: str) -> bool:
        """
        Verify that a table exists in the database.

        Args:
            session: Database session
            table_name: Name of the table to check

        Returns:
            True if table exists
        """
        try:
            result = session.execute(
                text(
                    "SELECT EXISTS ("
                    "SELECT FROM information_schema.tables "
                    "WHERE table_name = :table_name"
                    ")"
                ),
                {"table_name": table_name},
            )
            return result.fetchone()[0]
        except Exception as e:
            logger.debug(f"Failed to check if table {table_name} exists: {e}")
            return False


class BaseAsyncIntegrationTest:
    """
    Base class for asynchronous integration tests.

    Provides common utilities and setup for async testing against real DBSync databases.
    """

    async def verify_database_connection(self, session: AsyncSession) -> bool:
        """
        Verify that database connection is working.

        Args:
            session: Async database session

        Returns:
            True if connection is working
        """
        try:
            result = await session.execute(text("SELECT 1 as test"))
            return result.fetchone()[0] == 1
        except Exception as e:
            logger.debug(f"Async database connection verification failed: {e}")
            return False

    async def get_table_count(self, session: AsyncSession, table_name: str) -> int:
        """
        Get count of records in a specific table.

        Args:
            session: Async database session
            table_name: Name of the table to count

        Returns:
            Number of records in the table

        Raises:
            ValueError: If table name is invalid
            RuntimeError: If query execution fails
        """
        if not _validate_table_name(table_name):
            raise ValueError(f"Invalid table name: {table_name}")

        try:
            # Use parameterized query with identifier quoting
            # Note: SQLAlchemy's text() doesn't support identifier parameters,
            # so we validate the table name and use it directly
            result = await session.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
            return result.fetchone()[0]
        except Exception as e:
            logger.error(f"Failed to get async table count for {table_name}: {e}")
            raise RuntimeError(f"Failed to count records in table {table_name}") from e

    async def verify_table_exists(self, session: AsyncSession, table_name: str) -> bool:
        """
        Verify that a table exists in the database.

        Args:
            session: Async database session
            table_name: Name of the table to check

        Returns:
            True if table exists
        """
        try:
            result = await session.execute(
                text(
                    "SELECT EXISTS ("
                    "SELECT FROM information_schema.tables "
                    "WHERE table_name = :table_name"
                    ")"
                ),
                {"table_name": table_name},
            )
            return result.fetchone()[0]
        except Exception as e:
            logger.debug(f"Failed to check if table {table_name} exists (async): {e}")
            return False
