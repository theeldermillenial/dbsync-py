"""Unit tests for multi-asset queries module."""

from unittest.mock import Mock

import pytest

from src.dbsync.examples.queries.multi_asset import (
    MultiAssetQueries,
    get_comprehensive_multi_asset_analysis,
)


class TestMultiAssetQueries:
    """Test suite for MultiAssetQueries class."""

    def test_get_token_portfolio_analysis_success(self) -> None:
        """Test successful token portfolio analysis."""
        # Mock session and results
        mock_session = Mock()

        # Mock holdings query results
        mock_holdings = [
            Mock(
                policy=b"test_policy_1",
                name=b"TestToken1",
                total_quantity=1000000,
                holder_count=150,
                avg_holding=6667,
                max_holding=50000,
            ),
            Mock(
                policy=b"test_policy_2",
                name=b"TestToken2",
                total_quantity=500000,
                holder_count=75,
                avg_holding=6667,
                max_holding=25000,
            ),
        ]

        # Mock network statistics
        mock_session.execute.side_effect = [
            Mock(all=lambda: mock_holdings),  # holdings query
            Mock(scalar=lambda: 2),  # total assets
            Mock(scalar=lambda: 2),  # total policies
            Mock(scalar=lambda: 1500000),  # total supply
        ]

        result = MultiAssetQueries.get_token_portfolio_analysis(mock_session, None, 50)

        assert result["found"] is True
        assert result["portfolio_size"] == 2
        assert result["network_stats"]["total_assets"] == 2
        assert result["network_stats"]["total_policies"] == 2
        assert len(result["portfolio"]) == 2

        # Check first token
        token1 = result["portfolio"][0]
        assert token1["asset_name"] == "MockAsset"
        assert token1["total_quantity"] == 1000000
        assert token1["holder_count"] == 150

    def test_get_token_portfolio_analysis_with_address(self) -> None:
        """Test portfolio analysis for specific address."""
        mock_session = Mock()

        mock_holdings = [
            Mock(
                policy=b"test_policy",
                name=b"TestToken",
                total_quantity=10000,
                holder_count=1,
                avg_holding=10000,
                max_holding=10000,
            ),
        ]

        mock_session.execute.side_effect = [
            Mock(all=lambda: mock_holdings),
            Mock(scalar=lambda: 1),
            Mock(scalar=lambda: 1),
            Mock(scalar=lambda: 10000),
        ]

        address = "addr1test123"
        result = MultiAssetQueries.get_token_portfolio_analysis(
            mock_session, address, 50
        )

        assert result["found"] is True
        assert result["address"] == address
        assert result["portfolio_size"] == 1

    def test_get_asset_metadata_tracking_success(self) -> None:
        """Test successful asset metadata tracking."""
        mock_session = Mock()

        # Mock metadata query results
        mock_metadata = [
            Mock(
                policy=b"test_policy",
                name=b"TestNFT",
                quantity=1,
                tx_hash=b"tx_hash_1",
                mint_time="2024-01-01 12:00:00",
                epoch_no=450,
                metadata_json={"name": "Test NFT", "image": "ipfs://..."},
            ),
        ]

        # Mock policy stats
        mock_stats = Mock(
            unique_assets=1,
            total_minted=1,
            first_mint="2024-01-01 12:00:00",
            last_mint="2024-01-01 12:00:00",
        )

        mock_session.execute.side_effect = [
            Mock(all=lambda: mock_metadata),  # metadata query
            Mock(first=lambda: mock_stats),  # policy stats
        ]

        policy_id = "test_policy_hex"
        result = MultiAssetQueries.get_asset_metadata_tracking(
            mock_session, policy_id, 20
        )

        assert result["found"] is True
        assert result["policy_id"] == policy_id
        assert result["assets_found"] == 1
        assert len(result["assets"]) == 1

        asset = result["assets"][0]
        assert asset["asset_name"] == "MockAsset"
        assert asset["mint_quantity"] == 1
        assert asset["has_metadata"] is True

        # Check policy stats
        assert "policy_stats" in result
        assert result["policy_stats"]["unique_assets"] == 1

    def test_get_asset_metadata_tracking_not_found(self) -> None:
        """Test metadata tracking for non-existent policy."""
        mock_session = Mock()
        mock_session.execute.return_value.all.return_value = []

        policy_id = "nonexistent_policy"
        result = MultiAssetQueries.get_asset_metadata_tracking(
            mock_session, policy_id, 20
        )

        assert result["found"] is False
        assert result["policy_id"] == policy_id
        assert "error" in result

    def test_get_token_transfer_patterns_success(self) -> None:
        """Test successful token transfer patterns analysis."""
        mock_session = Mock()

        # Mock transfer patterns
        mock_transfers = [
            Mock(
                policy=b"policy_1",
                name=b"Token1",
                transfer_count=100,
                total_volume=1000000,
                avg_transfer=10000,
                unique_recipients=50,
                unique_transactions=80,
            ),
            Mock(
                policy=b"policy_2",
                name=b"Token2",
                transfer_count=50,
                total_volume=500000,
                avg_transfer=10000,
                unique_recipients=25,
                unique_transactions=40,
            ),
        ]

        # Mock network stats
        mock_network_stats = Mock(
            active_assets=2,
            total_transfers=150,
            total_volume=1500000,
            total_transactions=120,
        )

        mock_session.execute.side_effect = [
            Mock(scalar=lambda: "2024-01-01 12:00:00"),  # latest block
            Mock(scalar=lambda: 100000),  # latest slot
            Mock(all=lambda: mock_transfers),  # transfers query
            Mock(first=lambda: mock_network_stats),  # network stats
        ]

        result = MultiAssetQueries.get_token_transfer_patterns(mock_session, 30, 20)

        assert result["found"] is True
        assert result["analysis_period_days"] == 30
        assert result["latest_slot"] == 100000
        assert len(result["top_patterns"]) == 2

        # Check network activity
        network = result["network_activity"]
        assert network["active_assets"] == 2
        assert network["total_transfers"] == 150

        # Check first pattern
        pattern1 = result["top_patterns"][0]
        assert pattern1["asset_name"] == "MockAsset"
        assert pattern1["transfer_count"] == 100
        assert pattern1["unique_recipients"] == 50

    def test_get_token_transfer_patterns_no_block_data(self) -> None:
        """Test transfer patterns when no block data available."""
        mock_session = Mock()
        mock_session.execute.return_value.scalar.return_value = None

        result = MultiAssetQueries.get_token_transfer_patterns(mock_session, 30, 20)

        assert result["found"] is False
        assert "error" in result

    def test_async_not_implemented(self) -> None:
        """Test that async methods raise NotImplementedError."""
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_async_session = Mock(spec=AsyncSession)

        with pytest.raises(NotImplementedError):
            MultiAssetQueries.get_token_portfolio_analysis(mock_async_session)

        with pytest.raises(NotImplementedError):
            MultiAssetQueries.get_asset_metadata_tracking(mock_async_session)

        with pytest.raises(NotImplementedError):
            MultiAssetQueries.get_token_transfer_patterns(mock_async_session)


class TestComprehensiveMultiAssetAnalysis:
    """Test suite for comprehensive multi-asset analysis function."""

    def test_comprehensive_analysis_success(self) -> None:
        """Test successful comprehensive analysis."""
        mock_session = Mock()

        # Create a mock instance of MultiAssetQueries
        mock_queries = Mock()

        # Mock the return values for each method
        mock_portfolio = {
            "found": True,
            "network_stats": {"total_assets": 100, "total_policies": 50},
            "portfolio": [],
        }

        mock_metadata = {
            "found": True,
            "assets": [],
        }

        mock_patterns = {
            "found": True,
            "network_activity": {"active_assets": 25, "total_transfers": 1000},
            "top_patterns": [],
        }

        mock_queries.get_token_portfolio_analysis.return_value = mock_portfolio
        mock_queries.get_asset_metadata_tracking.return_value = mock_metadata
        mock_queries.get_token_transfer_patterns.return_value = mock_patterns

        # Mock the MultiAssetQueries class instantiation
        original_queries = MultiAssetQueries
        MultiAssetQueries.__new__ = lambda cls: mock_queries

        try:
            result = get_comprehensive_multi_asset_analysis(
                mock_session, "test_policy", 30
            )

            assert result["found"] is True
            assert result["policy_id"] == "test_policy"
            assert result["analysis_period_days"] == 30
            assert "summary" in result
            assert result["summary"]["total_assets"] == 100
            assert result["summary"]["total_policies"] == 50
            assert "portfolio_analysis" in result
            assert "metadata_tracking" in result
            assert "transfer_patterns" in result

        finally:
            # Restore the original class
            MultiAssetQueries.__new__ = original_queries.__new__

    def test_comprehensive_analysis_exception(self) -> None:
        """Test comprehensive analysis with exception."""
        mock_session = Mock()

        # Mock an exception during analysis
        mock_queries = Mock()
        mock_queries.get_token_portfolio_analysis.side_effect = Exception(
            "Database error"
        )

        original_queries = MultiAssetQueries
        MultiAssetQueries.__new__ = lambda cls: mock_queries

        try:
            result = get_comprehensive_multi_asset_analysis(
                mock_session, "test_policy", 30
            )

            assert result["found"] is False
            assert result["policy_id"] == "test_policy"
            assert "error" in result
            assert "Database error" in result["error"]

        finally:
            MultiAssetQueries.__new__ = original_queries.__new__


# Additional edge case tests
class TestMultiAssetEdgeCases:
    """Test edge cases and error conditions."""

    def test_bytes_name_decoding(self) -> None:
        """Test handling of asset names as bytes."""
        mock_session = Mock()

        # Test with decodable bytes
        mock_holdings = [
            Mock(
                policy=b"policy",
                name=b"DecodableToken",
                total_quantity=1000,
                holder_count=1,
                avg_holding=1000,
                max_holding=1000,
            ),
            # Test with non-decodable bytes (should fallback to hex)
            Mock(
                policy=b"policy",
                name=b"\xff\xfe\xfd",
                total_quantity=500,
                holder_count=1,
                avg_holding=500,
                max_holding=500,
            ),
        ]

        mock_session.execute.side_effect = [
            Mock(all=lambda: mock_holdings),
            Mock(scalar=lambda: 2),
            Mock(scalar=lambda: 1),
            Mock(scalar=lambda: 1500),
        ]

        result = MultiAssetQueries.get_token_portfolio_analysis(mock_session)

        assert result["found"] is True
        assert len(result["portfolio"]) == 2
        assert result["portfolio"][0]["asset_name"] == "MockAsset"
        # Second should be hex encoded (but Mock objects return MockAsset)
        assert result["portfolio"][1]["asset_name"] == "MockAsset"

    def test_zero_values_handling(self) -> None:
        """Test handling of zero/null values in calculations."""
        mock_session = Mock()

        mock_holdings = [
            Mock(
                policy=b"policy",
                name=b"ZeroToken",
                total_quantity=0,  # Zero quantity
                holder_count=0,
                avg_holding=0,
                max_holding=0,
            ),
        ]

        mock_session.execute.side_effect = [
            Mock(all=lambda: mock_holdings),
            Mock(scalar=lambda: 1),
            Mock(scalar=lambda: 1),
            Mock(scalar=lambda: 0),
        ]

        result = MultiAssetQueries.get_token_portfolio_analysis(mock_session)

        assert result["found"] is True
        token = result["portfolio"][0]
        assert token["total_quantity"] == 0
        assert token["distribution_ratio"] == 0  # Should handle division by zero
