"""Unit tests for smart contracts query examples."""

from unittest.mock import Mock, patch

import pytest

from dbsync.examples.queries.smart_contracts import (
    SmartContractsQueries,
    get_comprehensive_smart_contract_analysis,
)


class TestSmartContractsQueries:
    """Test suite for SmartContractsQueries class."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = Mock()
        session.execute.return_value.first.return_value = None
        session.execute.return_value.all.return_value = []
        session.execute.return_value.scalar.return_value = 0
        return session

    @pytest.fixture
    def sample_script_hash(self):
        """Sample script hash for testing."""
        return "a1b2c3d4e5f6789012345678901234567890abcdef"

    def test_get_script_analysis_general(self, mock_session):
        """Test general script analysis without specific hash."""
        # Mock script data
        mock_script = Mock()
        mock_script.hash_ = b"script_hash_bytes"  # Note: corrected field name
        mock_script.type_ = "plutusV1"
        mock_script.serialised_size = 1024
        mock_script.output_count = 5
        mock_script.input_count = 3

        # Mock scalar returns for statistics
        scalar_results = [100, 60, 30]  # total, native, plutus scripts
        mock_session.execute.return_value.scalar.side_effect = scalar_results
        mock_session.execute.return_value.all.return_value = [mock_script]

        queries = SmartContractsQueries()
        result = queries.get_script_analysis(mock_session)

        assert result["found"] is True
        assert result["total_scripts"] == 100
        assert result["native_scripts"] == 60
        assert result["plutus_scripts"] == 30
        assert len(result["scripts"]) == 1
        assert result["scripts"][0]["type"] == "plutusV1"
        assert result["scripts"][0]["total_usage"] == 0  # Simplified implementation

    def test_get_script_analysis_specific_not_found(
        self, mock_session, sample_script_hash
    ):
        """Test script analysis for specific hash that doesn't exist."""
        # Mock no scripts found
        mock_session.execute.return_value.all.return_value = []

        queries = SmartContractsQueries()
        result = queries.get_script_analysis(mock_session, sample_script_hash)

        assert result["found"] is False
        assert result["script_hash"] == sample_script_hash
        assert "not found" in result["error"]

    def test_get_contract_usage_patterns_no_data(self, mock_session):
        """Test contract usage patterns when no block data available."""
        # Mock no block data
        mock_session.execute.return_value.scalar.return_value = None

        queries = SmartContractsQueries()
        result = queries.get_contract_usage_patterns(mock_session)

        assert result["found"] is False
        assert "No block data available" in result["error"]

    def test_async_session_not_implemented(self, sample_script_hash):
        """Test that AsyncSession raises NotImplementedError."""
        from sqlalchemy.ext.asyncio import AsyncSession

        async_session = Mock(spec=AsyncSession)

        queries = SmartContractsQueries()

        with pytest.raises(NotImplementedError):
            queries.get_script_analysis(async_session)

        with pytest.raises(NotImplementedError):
            queries.get_contract_usage_patterns(async_session)

        with pytest.raises(NotImplementedError):
            queries.get_script_hash_tracking(async_session, sample_script_hash)

        with pytest.raises(NotImplementedError):
            queries.get_contract_value_tracking(async_session)


class TestComprehensiveSmartContractAnalysis:
    """Test suite for comprehensive smart contract analysis function."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = Mock()
        return session

    @pytest.fixture
    def sample_script_hash(self):
        """Sample script hash for testing."""
        return "a1b2c3d4e5f6789012345678901234567890abcdef"

    @patch("dbsync.examples.queries.smart_contracts.SmartContractsQueries")
    def test_comprehensive_analysis_success(
        self, mock_queries_class, mock_session, sample_script_hash
    ):
        """Test comprehensive smart contract analysis success case."""
        # Mock the queries instance and its methods
        mock_queries = Mock()
        mock_queries_class.return_value = mock_queries

        # Mock individual query results
        mock_queries.get_script_analysis.return_value = {
            "found": True,
            "total_scripts": 1000,
            "native_scripts": 600,
            "plutus_scripts": 400,
        }
        mock_queries.get_contract_usage_patterns.return_value = {
            "found": True,
            "total_executions": 150,
        }
        mock_queries.get_contract_value_tracking.return_value = {
            "found": True,
            "network_totals": {
                "total_script_locked_value_ada": 500000.0,
            },
        }
        mock_queries.get_script_hash_tracking.return_value = {
            "found": True,
            "usage_summary": {
                "total_executions": 25,
            },
        }

        # Mock session.execute for current epoch
        mock_session.execute.return_value.scalar.return_value = 350

        result = get_comprehensive_smart_contract_analysis(
            mock_session, sample_script_hash, days=30
        )

        assert result["found"] is True
        assert result["script_hash"] == sample_script_hash
        assert result["analysis_period_days"] == 30
        assert result["summary"]["total_scripts"] == 1000
        assert result["summary"]["native_scripts"] == 600
        assert result["summary"]["plutus_scripts"] == 400
        assert result["summary"]["total_executions"] == 150
        assert result["summary"]["total_script_value_ada"] == 500000.0

    @patch("dbsync.examples.queries.smart_contracts.SmartContractsQueries")
    def test_comprehensive_analysis_exception(
        self, mock_queries_class, mock_session, sample_script_hash
    ):
        """Test comprehensive smart contract analysis exception handling."""
        # Mock the queries instance to raise an exception
        mock_queries = Mock()
        mock_queries_class.return_value = mock_queries
        mock_queries.get_script_analysis.side_effect = Exception("Database error")

        result = get_comprehensive_smart_contract_analysis(
            mock_session, sample_script_hash
        )

        assert result["found"] is False
        assert result["script_hash"] == sample_script_hash
        assert "Analysis failed" in result["error"]
        assert "Database error" in result["error"]
