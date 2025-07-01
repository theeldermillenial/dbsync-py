"""Unit tests for staking delegation query examples."""

from unittest.mock import Mock, patch

import pytest

from dbsync.examples.queries.staking_delegation import (
    StakingDelegationQueries,
    get_comprehensive_staking_analysis,
)


class TestStakingDelegationQueries:
    """Test suite for StakingDelegationQueries class."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = Mock()
        session.execute.return_value.first.return_value = None
        session.execute.return_value.all.return_value = []
        session.execute.return_value.scalar.return_value = 0
        return session

    @pytest.fixture
    def sample_stake_address(self):
        """Sample stake address for testing."""
        return "stake1ux5c8n5p7rz4e0l2r8xgmp4dkzfcq3q8s6m9t2k5w8h3e7d"

    def test_get_delegation_history_not_found(self, mock_session, sample_stake_address):
        """Test delegation history query when stake address not found."""
        # Mock stake address not found
        mock_session.execute.return_value.first.return_value = None

        queries = StakingDelegationQueries()
        result = queries.get_delegation_history(mock_session, sample_stake_address)

        assert result["found"] is False
        assert result["stake_address"] == sample_stake_address
        assert "not found" in result["error"]

    def test_get_delegation_history_found(self, mock_session, sample_stake_address):
        """Test delegation history query when stake address found."""
        # Mock stake address found
        mock_stake_addr = Mock()
        mock_stake_addr.id_ = 1
        mock_session.execute.return_value.first.return_value = [mock_stake_addr]

        # Mock delegation history
        mock_delegation = Mock()
        mock_delegation.active_epoch_no = 350
        mock_delegation.pool_hash_id = 1001
        mock_delegation.tx_id = 12345

        # Configure execute to return different results for different calls
        execute_results = [
            [mock_stake_addr],  # Stake address lookup
            [mock_delegation],  # Delegation history
        ]
        mock_session.execute.return_value.first.side_effect = execute_results
        mock_session.execute.return_value.all.return_value = [mock_delegation]

        queries = StakingDelegationQueries()
        result = queries.get_delegation_history(mock_session, sample_stake_address)

        assert result["found"] is True
        assert result["stake_address"] == sample_stake_address
        assert result["total_delegations"] == 1
        assert len(result["delegation_history"]) == 1
        assert result["delegation_history"][0]["epoch"] == 350

    def test_get_stake_distribution_patterns_no_epoch(self, mock_session):
        """Test stake distribution patterns when no epoch data."""
        # Mock no epoch data
        mock_session.execute.return_value.scalar.return_value = None

        queries = StakingDelegationQueries()
        result = queries.get_stake_distribution_patterns(mock_session)

        assert result["found"] is False
        assert "No epoch data available" in result["error"]

    def test_get_stake_distribution_patterns_found(self, mock_session):
        """Test stake distribution patterns with data."""
        # Mock latest epoch
        mock_session.execute.return_value.scalar.side_effect = [
            350,
            100000000000,
        ]  # epoch, total stake

        # Mock stake distribution
        mock_stake = Mock()
        mock_stake.pool_id = 1
        mock_stake.total_stake = 50000000000  # 50k ADA in lovelace
        mock_stake.delegator_count = 100

        mock_session.execute.return_value.all.return_value = [mock_stake]

        queries = StakingDelegationQueries()
        result = queries.get_stake_distribution_patterns(mock_session)

        assert result["found"] is True
        assert result["epoch"] == 350
        assert result["total_stake"] == 100000000000
        assert len(result["distribution"]) == 1
        assert result["distribution"][0]["pool_id"] == 1
        assert result["distribution"][0]["stake_percentage"] == 50.0  # 50% of total

    def test_get_delegation_lifecycle_not_found(
        self, mock_session, sample_stake_address
    ):
        """Test delegation lifecycle when stake address not found."""
        # Mock stake address not found
        mock_session.execute.return_value.first.return_value = None

        queries = StakingDelegationQueries()
        result = queries.get_delegation_lifecycle(mock_session, sample_stake_address)

        assert result["found"] is False
        assert result["stake_address"] == sample_stake_address

    def test_get_delegation_lifecycle_found(self, mock_session, sample_stake_address):
        """Test delegation lifecycle with data."""
        # Mock stake address found
        mock_stake_addr = Mock()
        mock_stake_addr.id_ = 1

        # Mock registration
        mock_registration = Mock()
        mock_registration.tx_id = 11111
        mock_registration.cert_index = 0

        # Mock current delegation
        mock_delegation = Mock()
        mock_delegation.active_epoch_no = 350
        mock_delegation.pool_hash_id = 1001

        # Configure execute to return different results for different calls
        execute_results = [
            [mock_stake_addr],  # Stake address lookup
            mock_registration,  # Registration
            None,  # Deregistration (not found)
            mock_delegation,  # Current delegation
        ]
        mock_session.execute.return_value.first.side_effect = execute_results
        mock_session.execute.return_value.scalar.return_value = (
            100000000  # 100 ADA stake
        )

        queries = StakingDelegationQueries()
        result = queries.get_delegation_lifecycle(mock_session, sample_stake_address)

        assert result["found"] is True
        assert result["stake_address"] == sample_stake_address
        assert result["registration"]["tx_id"] == 11111
        assert result["deregistration"]["tx_id"] is None
        assert result["current_delegation"]["epoch"] == 350
        assert result["current_stake"] == 100000000
        assert result["is_active"] is True

    def test_get_reward_earning_patterns_not_found(
        self, mock_session, sample_stake_address
    ):
        """Test reward earning patterns when stake address not found."""
        # Mock stake address not found
        mock_session.execute.return_value.first.return_value = None

        queries = StakingDelegationQueries()
        result = queries.get_reward_earning_patterns(mock_session, sample_stake_address)

        assert result["found"] is False
        assert result["stake_address"] == sample_stake_address

    def test_get_reward_earning_patterns_found(
        self, mock_session, sample_stake_address
    ):
        """Test reward earning patterns with data."""
        # Mock stake address found
        mock_stake_addr = Mock()
        mock_stake_addr.id_ = 1

        # Mock latest epoch
        latest_epoch = 350

        # Mock reward data
        mock_reward = Mock()
        mock_reward.earned_epoch = 349
        mock_reward.type_ = "member"
        mock_reward.total_amount = 2000000  # 2 ADA in lovelace

        # Configure execute to return different results for different calls
        mock_session.execute.return_value.first.side_effect = [
            [mock_stake_addr],  # Stake address lookup
        ]
        mock_session.execute.return_value.scalar.side_effect = [
            latest_epoch,  # Latest epoch
        ]
        mock_session.execute.return_value.all.return_value = [mock_reward]

        queries = StakingDelegationQueries()
        result = queries.get_reward_earning_patterns(
            mock_session, sample_stake_address, epochs=5
        )

        assert result["found"] is True
        assert result["stake_address"] == sample_stake_address
        assert result["epochs_analyzed"] == 5
        assert result["total_rewards"] == 2000000
        assert result["total_rewards_ada"] == 2.0
        assert len(result["rewards_history"]) == 1

    def test_get_active_stake_monitoring_no_epoch(self, mock_session):
        """Test active stake monitoring when no epoch data."""
        # Mock no epoch data
        mock_session.execute.return_value.scalar.return_value = None

        queries = StakingDelegationQueries()
        result = queries.get_active_stake_monitoring(mock_session)

        assert result["found"] is False
        assert "No epoch data available" in result["error"]

    def test_get_active_stake_monitoring_found(self, mock_session):
        """Test active stake monitoring with data."""
        # Mock scalar returns for different queries
        scalar_results = [
            350,  # Latest epoch
            100000000000,  # Total active stake (100k ADA)
            1000,  # Active delegators
            50,  # Active pools
            50000000000,  # Largest single stake (50k ADA)
        ]
        mock_session.execute.return_value.scalar.side_effect = scalar_results

        queries = StakingDelegationQueries()
        result = queries.get_active_stake_monitoring(mock_session)

        assert result["found"] is True
        assert result["epoch"] == 350
        assert result["total_active_stake"] == 100000000000
        assert result["active_delegators"] == 1000
        assert result["active_pools"] == 50
        assert result["average_stake_per_delegator"] == 100000000  # 100 ADA
        assert result["largest_single_stake"] == 50000000000

    def test_async_session_not_implemented(self, sample_stake_address):
        """Test that AsyncSession raises NotImplementedError."""
        from sqlalchemy.ext.asyncio import AsyncSession

        async_session = Mock(spec=AsyncSession)

        queries = StakingDelegationQueries()

        with pytest.raises(NotImplementedError):
            queries.get_delegation_history(async_session, sample_stake_address)

        with pytest.raises(NotImplementedError):
            queries.get_stake_distribution_patterns(async_session)

        with pytest.raises(NotImplementedError):
            queries.get_delegation_lifecycle(async_session, sample_stake_address)

        with pytest.raises(NotImplementedError):
            queries.get_reward_earning_patterns(async_session, sample_stake_address)

        with pytest.raises(NotImplementedError):
            queries.get_active_stake_monitoring(async_session)


class TestComprehensiveStakingAnalysis:
    """Test suite for comprehensive staking analysis function."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = Mock()
        return session

    @pytest.fixture
    def sample_stake_address(self):
        """Sample stake address for testing."""
        return "stake1ux5c8n5p7rz4e0l2r8xgmp4dkzfcq3q8s6m9t2k5w8h3e7d"

    @patch("dbsync.examples.queries.staking_delegation.StakingDelegationQueries")
    def test_comprehensive_analysis_success(
        self, mock_queries_class, mock_session, sample_stake_address
    ):
        """Test comprehensive staking analysis success case."""
        # Mock the queries instance and its methods
        mock_queries = Mock()
        mock_queries_class.return_value = mock_queries

        # Mock individual query results
        mock_queries.get_delegation_history.return_value = {
            "found": True,
            "total_delegations": 3,
        }
        mock_queries.get_delegation_lifecycle.return_value = {
            "is_active": True,
            "current_stake_ada": 1000.0,
        }
        mock_queries.get_reward_earning_patterns.return_value = {
            "total_rewards_ada": 50.0,
        }
        mock_queries.get_stake_distribution_patterns.return_value = {
            "found": True,
        }
        mock_queries.get_active_stake_monitoring.return_value = {
            "found": True,
        }

        # Mock session.execute for current epoch
        mock_session.execute.return_value.scalar.return_value = 350

        result = get_comprehensive_staking_analysis(
            mock_session, sample_stake_address, epochs=5
        )

        assert result["found"] is True
        assert result["stake_address"] == sample_stake_address
        assert result["summary"]["is_active"] is True
        assert result["summary"]["current_stake_ada"] == 1000.0
        assert result["summary"]["total_rewards_ada"] == 50.0
        assert result["summary"]["delegation_count"] == 3

    @patch("dbsync.examples.queries.staking_delegation.StakingDelegationQueries")
    def test_comprehensive_analysis_exception(
        self, mock_queries_class, mock_session, sample_stake_address
    ):
        """Test comprehensive staking analysis exception handling."""
        # Mock the queries instance to raise an exception
        mock_queries = Mock()
        mock_queries_class.return_value = mock_queries
        mock_queries.get_delegation_history.side_effect = Exception("Database error")

        result = get_comprehensive_staking_analysis(mock_session, sample_stake_address)

        assert result["found"] is False
        assert result["stake_address"] == sample_stake_address
        assert "Analysis failed" in result["error"]
        assert "Database error" in result["error"]
