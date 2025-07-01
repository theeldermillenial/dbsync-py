"""Tests for chain metadata query examples.

Tests the example implementations in dbsync.examples.queries.chain_metadata
to ensure they work correctly and return expected data types.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

# Add the src directory to path for importing the main package
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Add the examples directory to path for importing examples
sys.path.insert(0, str(Path(__file__).parent.parent))

from dbsync.examples.queries.chain_metadata import ChainMetadataQueries, get_chain_info
from dbsync.models import ChainMeta

# Lovelace is just an int in the application layer


class TestChainMetadataQueries:
    """Test cases for ChainMetadataQueries example class."""

    def test_get_chain_metadata_success(self):
        """Test successful chain metadata retrieval."""
        # Mock session and result
        mock_session = Mock(spec=Session)
        mock_meta = Mock(spec=ChainMeta)
        mock_meta.network_name = "mainnet"
        mock_meta.start_time = "2017-09-23 21:44:51"

        # Mock the query execution
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_meta
        mock_session.execute.return_value = mock_result

        # Test the query
        result = ChainMetadataQueries.get_chain_metadata(mock_session)

        # Verify results
        assert result == mock_meta
        assert result.network_name == "mainnet"
        mock_session.execute.assert_called_once()

    def test_get_chain_metadata_not_found(self):
        """Test chain metadata retrieval when no data exists."""
        # Mock session with no results
        mock_session = Mock(spec=Session)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Test the query
        result = ChainMetadataQueries.get_chain_metadata(mock_session)

        # Verify results
        assert result is None
        mock_session.execute.assert_called_once()

    def test_get_current_supply_success(self):
        """Test successful current supply calculation."""
        # Mock session and result
        mock_session = Mock(spec=Session)
        mock_result = Mock()
        mock_result.scalar.return_value = 45000000000000000  # 45B ADA in Lovelace
        mock_session.execute.return_value = mock_result

        # Test the query
        result = ChainMetadataQueries.get_current_supply(mock_session)

        # Verify results
        assert isinstance(result, int)
        assert result == 45000000000000000
        mock_session.execute.assert_called_once()

    def test_get_current_supply_no_data(self):
        """Test current supply calculation with no UTxO data."""
        # Mock session with null result
        mock_session = Mock(spec=Session)
        mock_result = Mock()
        mock_result.scalar.return_value = None
        mock_session.execute.return_value = mock_result

        # Test the query
        result = ChainMetadataQueries.get_current_supply(mock_session)

        # Verify results
        assert isinstance(result, int)
        assert result == 0
        mock_session.execute.assert_called_once()

    def test_get_latest_slot_number_success(self):
        """Test successful latest slot number retrieval."""
        # Mock session and result
        mock_session = Mock(spec=Session)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = 12345678
        mock_session.execute.return_value = mock_result

        # Test the query
        result = ChainMetadataQueries.get_latest_slot_number(mock_session)

        # Verify results
        assert result == 12345678
        mock_session.execute.assert_called_once()

    def test_get_latest_slot_number_no_blocks(self):
        """Test latest slot number retrieval when no blocks exist."""
        # Mock session with no results
        mock_session = Mock(spec=Session)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Test the query
        result = ChainMetadataQueries.get_latest_slot_number(mock_session)

        # Verify results
        assert result is None
        mock_session.execute.assert_called_once()

    def test_get_database_size_pretty_success(self):
        """Test successful database size retrieval."""
        # Mock session and result
        mock_session = Mock(spec=Session)
        mock_result = Mock()
        mock_result.scalar.return_value = "116 GB"
        mock_session.execute.return_value = mock_result

        # Test the query
        result = ChainMetadataQueries.get_database_size_pretty(mock_session)

        # Verify results
        assert result == "116 GB"
        mock_session.execute.assert_called_once()

    def test_get_database_size_pretty_no_data(self):
        """Test database size retrieval when no data available."""
        # Mock session with null result
        mock_session = Mock(spec=Session)
        mock_result = Mock()
        mock_result.scalar.return_value = None
        mock_session.execute.return_value = mock_result

        # Test the query
        result = ChainMetadataQueries.get_database_size_pretty(mock_session)

        # Verify results
        assert result == "Unknown"
        mock_session.execute.assert_called_once()

    def test_get_table_size_pretty_success(self):
        """Test successful table size retrieval."""
        # Mock session and result
        mock_session = Mock(spec=Session)
        mock_result = Mock()
        mock_result.scalar.return_value = "2760 MB"
        mock_session.execute.return_value = mock_result

        # Test the query
        result = ChainMetadataQueries.get_table_size_pretty(mock_session, "block")

        # Verify results
        assert result == "2760 MB"
        mock_session.execute.assert_called_once()

    def test_get_table_size_pretty_custom_table(self):
        """Test table size retrieval for custom table."""
        # Mock session and result
        mock_session = Mock(spec=Session)
        mock_result = Mock()
        mock_result.scalar.return_value = "50 GB"
        mock_session.execute.return_value = mock_result

        # Test the query
        result = ChainMetadataQueries.get_table_size_pretty(mock_session, "tx_out")

        # Verify results
        assert result == "50 GB"
        mock_session.execute.assert_called_once()

    def test_get_sync_progress_percent_success(self):
        """Test successful sync progress calculation."""
        # Mock session and result
        mock_session = Mock(spec=Session)
        mock_result = Mock()
        mock_result.scalar.return_value = 99.8
        mock_session.execute.return_value = mock_result

        # Test the query
        result = ChainMetadataQueries.get_sync_progress_percent(mock_session)

        # Verify results
        assert result == 99.8
        assert isinstance(result, float)
        mock_session.execute.assert_called_once()

    def test_get_sync_progress_percent_no_data(self):
        """Test sync progress calculation with no block data."""
        # Mock session with null result
        mock_session = Mock(spec=Session)
        mock_result = Mock()
        mock_result.scalar.return_value = None
        mock_session.execute.return_value = mock_result

        # Test the query
        result = ChainMetadataQueries.get_sync_progress_percent(mock_session)

        # Verify results
        assert result == 0.0
        assert isinstance(result, float)
        mock_session.execute.assert_called_once()

    def test_get_sync_behind_duration_success(self):
        """Test successful sync behind duration calculation."""
        # Mock session and result
        mock_session = Mock(spec=Session)
        mock_result = Mock()
        mock_result.scalar.return_value = "4 days 20:59:39.134497"
        mock_session.execute.return_value = mock_result

        # Test the query
        result = ChainMetadataQueries.get_sync_behind_duration(mock_session)

        # Verify results
        assert result == "4 days 20:59:39.134497"
        mock_session.execute.assert_called_once()

    def test_get_sync_behind_duration_no_data(self):
        """Test sync behind duration calculation with no block data."""
        # Mock session with null result
        mock_session = Mock(spec=Session)
        mock_result = Mock()
        mock_result.scalar.return_value = None
        mock_session.execute.return_value = mock_result

        # Test the query
        result = ChainMetadataQueries.get_sync_behind_duration(mock_session)

        # Verify results
        assert result is None
        mock_session.execute.assert_called_once()


class TestGetChainInfo:
    """Test cases for get_chain_info convenience function."""

    @patch.object(ChainMetadataQueries, "get_chain_metadata")
    @patch.object(ChainMetadataQueries, "get_current_supply")
    @patch.object(ChainMetadataQueries, "get_latest_slot_number")
    @patch.object(ChainMetadataQueries, "get_database_size_pretty")
    @patch.object(ChainMetadataQueries, "get_table_size_pretty")
    @patch.object(ChainMetadataQueries, "get_sync_progress_percent")
    @patch.object(ChainMetadataQueries, "get_sync_behind_duration")
    def test_get_chain_info_success(
        self,
        mock_sync_behind,
        mock_sync_progress,
        mock_table_size,
        mock_db_size,
        mock_latest_slot,
        mock_supply,
        mock_metadata,
    ):
        """Test successful comprehensive chain info retrieval."""
        # Mock all the individual query results
        mock_meta = Mock(spec=ChainMeta)
        mock_meta.network_name = "mainnet"
        mock_meta.start_time = "2017-09-23 21:44:51"

        mock_metadata.return_value = mock_meta
        mock_supply.return_value = 45000000000000000
        mock_latest_slot.return_value = 12345678
        mock_db_size.return_value = "116 GB"
        mock_table_size.return_value = "2760 MB"
        mock_sync_progress.return_value = 99.8
        mock_sync_behind.return_value = "4 days 20:59:39"

        # Mock session
        mock_session = Mock(spec=Session)

        # Test the function
        result = get_chain_info(mock_session)

        # Verify all methods were called
        mock_metadata.assert_called_once_with(mock_session)
        mock_supply.assert_called_once_with(mock_session)
        mock_latest_slot.assert_called_once_with(mock_session)
        mock_db_size.assert_called_once_with(mock_session)
        mock_table_size.assert_called_once_with(mock_session, "block")
        mock_sync_progress.assert_called_once_with(mock_session)
        mock_sync_behind.assert_called_once_with(mock_session)

        # Verify result structure
        expected_keys = {
            "network",
            "start_time",
            "supply_lovelace",
            "supply_ada",
            "latest_slot",
            "database_size",
            "block_table_size",
            "sync_progress_percent",
            "sync_behind",
        }
        assert set(result.keys()) == expected_keys

        # Verify specific values
        assert result["network"] == "mainnet"
        assert result["start_time"] == "2017-09-23 21:44:51"
        assert result["supply_lovelace"] == 45000000000000000
        assert result["supply_ada"] == 45000000000.0  # Lovelace to ADA conversion
        assert result["latest_slot"] == 12345678
        assert result["database_size"] == "116 GB"
        assert result["block_table_size"] == "2760 MB"
        assert result["sync_progress_percent"] == 99.8
        assert result["sync_behind"] == "4 days 20:59:39"

    @patch.object(ChainMetadataQueries, "get_chain_metadata")
    @patch.object(ChainMetadataQueries, "get_current_supply")
    @patch.object(ChainMetadataQueries, "get_latest_slot_number")
    @patch.object(ChainMetadataQueries, "get_database_size_pretty")
    @patch.object(ChainMetadataQueries, "get_table_size_pretty")
    @patch.object(ChainMetadataQueries, "get_sync_progress_percent")
    @patch.object(ChainMetadataQueries, "get_sync_behind_duration")
    def test_get_chain_info_no_metadata(
        self,
        mock_sync_behind,
        mock_sync_progress,
        mock_table_size,
        mock_db_size,
        mock_latest_slot,
        mock_supply,
        mock_metadata,
    ):
        """Test chain info retrieval when no metadata is available."""
        # Mock all the individual query results (no metadata)
        mock_metadata.return_value = None
        mock_supply.return_value = 0
        mock_latest_slot.return_value = None
        mock_db_size.return_value = "Unknown"
        mock_table_size.return_value = "Unknown"
        mock_sync_progress.return_value = 0.0
        mock_sync_behind.return_value = None

        # Mock session
        mock_session = Mock(spec=Session)

        # Test the function
        result = get_chain_info(mock_session)

        # Verify result handles missing metadata gracefully
        assert result["network"] == "Unknown"
        assert result["start_time"] is None
        assert result["supply_lovelace"] == 0
        assert result["supply_ada"] == 0.0
        assert result["latest_slot"] is None
        assert result["database_size"] == "Unknown"
        assert result["sync_progress_percent"] == 0.0
        assert result["sync_behind"] is None


class TestAsyncNotImplemented:
    """Test that async versions raise NotImplementedError."""

    def test_async_methods_not_implemented(self):
        """Test that all async versions raise NotImplementedError."""
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_async_session = Mock(spec=AsyncSession)

        # Test all methods raise NotImplementedError for async sessions
        with pytest.raises(NotImplementedError):
            ChainMetadataQueries.get_chain_metadata(mock_async_session)

        with pytest.raises(NotImplementedError):
            ChainMetadataQueries.get_current_supply(mock_async_session)

        with pytest.raises(NotImplementedError):
            ChainMetadataQueries.get_latest_slot_number(mock_async_session)

        with pytest.raises(NotImplementedError):
            ChainMetadataQueries.get_database_size_pretty(mock_async_session)

        with pytest.raises(NotImplementedError):
            ChainMetadataQueries.get_table_size_pretty(mock_async_session, "block")

        with pytest.raises(NotImplementedError):
            ChainMetadataQueries.get_sync_progress_percent(mock_async_session)

        with pytest.raises(NotImplementedError):
            ChainMetadataQueries.get_sync_behind_duration(mock_async_session)
