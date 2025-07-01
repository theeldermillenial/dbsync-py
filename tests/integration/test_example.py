"""
Example integration tests for dbsync-py.

This module demonstrates how to write integration tests that connect to
actual DBSync PostgreSQL databases. These tests only run when DBSync
environment variables are configured.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from tests.integration.base import BaseAsyncIntegrationTest, BaseIntegrationTest


@pytest.mark.integration
class TestDBSyncConnectionIntegration(BaseIntegrationTest):
    """Integration tests for DBSync database connections."""

    def test_sync_database_connection(self, dbsync_session: Session):
        """Test synchronous connection to DBSync database."""
        # Verify connection works
        assert self.verify_database_connection(dbsync_session)

        # Test basic query
        result = dbsync_session.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        assert "PostgreSQL" in version

    def test_dbsync_schema_exists(self, dbsync_session: Session):
        """Test that expected DBSync tables exist."""
        # Check for core DBSync tables
        core_tables = ["block", "tx", "epoch", "slot_leader"]

        for table_name in core_tables:
            assert self.verify_table_exists(dbsync_session, table_name), (
                f"Expected DBSync table '{table_name}' not found"
            )

    def test_block_table_has_data(self, dbsync_session: Session):
        """Test that block table contains data."""
        if self.verify_table_exists(dbsync_session, "block"):
            count = self.get_table_count(dbsync_session, "block")
            # DBSync should have at least some blocks
            assert count > 0, "Block table should contain data"


@pytest.mark.integration
@pytest.mark.async_test
class TestDBSyncAsyncConnectionIntegration(BaseAsyncIntegrationTest):
    """Integration tests for async DBSync database connections."""

    async def test_async_database_connection(self, dbsync_async_session: AsyncSession):
        """Test asynchronous connection to DBSync database."""
        # Verify connection works
        assert await self.verify_database_connection(dbsync_async_session)

        # Test basic query
        result = await dbsync_async_session.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        assert "PostgreSQL" in version

    async def test_async_dbsync_schema_exists(self, dbsync_async_session: AsyncSession):
        """Test that expected DBSync tables exist (async)."""
        # Check for core DBSync tables
        core_tables = ["block", "tx", "epoch", "slot_leader"]

        for table_name in core_tables:
            exists = await self.verify_table_exists(dbsync_async_session, table_name)
            assert exists, f"Expected DBSync table '{table_name}' not found"

    async def test_async_block_table_has_data(self, dbsync_async_session: AsyncSession):
        """Test that block table contains data (async)."""
        if await self.verify_table_exists(dbsync_async_session, "block"):
            count = await self.get_table_count(dbsync_async_session, "block")
            # DBSync should have at least some blocks
            assert count > 0, "Block table should contain data"


@pytest.mark.integration
class TestModelIntegrationExample(BaseIntegrationTest):
    """
    Example of how to write integration tests for SQLModel classes.

    This demonstrates the pattern that should be used when adding
    integration tests to model generation tasks.
    """

    def test_model_integration_pattern(self, dbsync_session: Session):
        """
        Example pattern for testing SQLModel classes against real data.

        This is the pattern to follow when adding integration tests
        to SCHEMA-XXX tasks that generate model classes.
        """
        # 1. Verify table exists
        assert self.verify_table_exists(dbsync_session, "block")

        # 2. Test basic query works
        result = dbsync_session.execute(text("SELECT id, hash FROM block LIMIT 1"))
        row = result.fetchone()

        if row:
            # 3. Verify data structure matches expectations
            assert row[0] is not None  # id should exist
            assert row[1] is not None  # hash should exist

            # 4. When you have SQLModel classes, test them here:
            # from dbsync.models.schema import Block
            # block = dbsync_session.get(Block, row[0])
            # assert block is not None
            # assert block.hash == row[1]
        else:
            pytest.skip("No block data available for integration testing")
