"""Tests for transaction analysis query examples.

Tests the example implementations in dbsync.examples.queries.transaction_analysis
to ensure they work correctly and return expected data types.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

# Add the src directory to path for importing the main package
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from dbsync.examples.queries.transaction_analysis import (
    TransactionAnalysisQueries,
    get_comprehensive_transaction_analysis,
)


class TestTransactionAnalysisQueries:
    """Test cases for TransactionAnalysisQueries example class."""

    def test_get_transaction_fee_stats_success(self):
        """Test successful transaction fee statistics retrieval."""
        # Mock session and result
        mock_session = Mock(spec=Session)
        mock_result = Mock()
        mock_result.tx_count = 1000
        mock_result.avg_fee = 200000  # 0.2 ADA in lovelace
        mock_result.min_fee = 150000  # 0.15 ADA
        mock_result.max_fee = 500000  # 0.5 ADA
        mock_result.total_fees = 200000000  # 200 ADA

        mock_session.execute.return_value.first.return_value = mock_result

        # Test the query
        result = TransactionAnalysisQueries.get_transaction_fee_stats(
            mock_session, days=7
        )

        # Verify results
        assert result["tx_count"] == 1000
        assert result["avg_fee"] == 200000
        assert result["period_days"] == 7
        mock_session.execute.assert_called_once()

    def test_get_transaction_fee_stats_no_data(self):
        """Test transaction fee statistics with no data."""
        mock_session = Mock(spec=Session)
        mock_session.execute.return_value.first.return_value = None

        result = TransactionAnalysisQueries.get_transaction_fee_stats(mock_session)

        assert result["tx_count"] == 0
        assert result["avg_fee"] == 0
        assert result["min_fee"] == 0
        assert result["max_fee"] == 0
        assert result["total_fees"] == 0
        assert result["period_days"] == 7

    def test_get_address_balance_success(self):
        """Test successful address balance calculation."""
        mock_session = Mock(spec=Session)
        mock_result = Mock()
        mock_result.utxo_count = 5
        mock_result.total_balance = 10000000  # 10 ADA

        mock_session.execute.return_value.first.return_value = mock_result

        result = TransactionAnalysisQueries.get_address_balance(
            mock_session, "addr1test123"
        )

        assert result["address"] == "addr1test123"
        assert result["utxo_count"] == 5
        assert result["total_balance"] == 10000000
        assert result["balance_ada"] == 10.0
        assert result["found"] is True

    def test_get_address_balance_not_found(self):
        """Test address balance calculation for non-existent address."""
        mock_session = Mock(spec=Session)
        mock_result = Mock()
        mock_result.total_balance = None

        mock_session.execute.return_value.first.return_value = mock_result

        result = TransactionAnalysisQueries.get_address_balance(
            mock_session, "addr1notfound"
        )

        assert result["address"] == "addr1notfound"
        assert result["utxo_count"] == 0
        assert result["total_balance"] == 0
        assert result["balance_ada"] == 0.0
        assert result["found"] is False

    def test_get_transaction_inputs_outputs_success(self):
        """Test successful transaction input/output analysis."""
        mock_session = Mock(spec=Session)

        # Mock transaction lookup
        tx_result = Mock()
        tx_result.id_ = 123
        tx_result.fee = 180000  # 0.18 ADA
        mock_session.execute.side_effect = [
            Mock(first=lambda: tx_result),  # Transaction lookup
            [  # Inputs
                Mock(tx_out_index=0, value=5000000, address="addr1input1"),
                Mock(tx_out_index=1, value=3000000, address="addr1input2"),
            ],
            [  # Outputs
                Mock(index=0, value=7500000, address="addr1output1"),
                Mock(index=1, value=320000, address="addr1output2"),
            ],
        ]

        result = TransactionAnalysisQueries.get_transaction_inputs_outputs(
            mock_session, "abc123def456789012345678901234567890123456789012345678901234"
        )

        assert (
            result["transaction_hash"]
            == "abc123def456789012345678901234567890123456789012345678901234"
        )
        assert result["found"] is True
        assert result["fee"] == 180000
        assert result["fee_ada"] == 0.18
        assert result["input_count"] == 2
        assert result["output_count"] == 2
        assert result["total_input"] == 8000000  # 5M + 3M
        assert result["total_output"] == 7820000  # 7.5M + 320K
        assert len(result["inputs"]) == 2
        assert len(result["outputs"]) == 2

    def test_get_transaction_inputs_outputs_not_found(self):
        """Test transaction analysis for non-existent transaction."""
        mock_session = Mock(spec=Session)
        mock_session.execute.return_value.first.return_value = None

        result = TransactionAnalysisQueries.get_transaction_inputs_outputs(
            mock_session,
            "a1b2c3d4e5f67890123456789012345678901234567890123456789012345678",
        )

        assert (
            result["transaction_hash"]
            == "a1b2c3d4e5f67890123456789012345678901234567890123456789012345678"
        )
        assert result["found"] is False
        assert result["inputs"] == []
        assert result["outputs"] == []
        assert result["fee"] == 0

    def test_get_address_transaction_history_success(self):
        """Test successful address transaction history retrieval."""
        mock_session = Mock(spec=Session)

        # Mock transaction results
        tx_rows = [
            Mock(
                hash_=bytes.fromhex(
                    "abc123def456789012345678901234567890123456789012345678901234"
                ),
                block_no=1000,
                time=Mock(isoformat=lambda: "2023-01-01T12:00:00"),
                fee=180000,
                value=5000000,
                output_index=0,
            ),
            Mock(
                hash_=bytes.fromhex(
                    "def456abc123789012345678901234567890123456789012345678901234"
                ),
                block_no=999,
                time=Mock(isoformat=lambda: "2023-01-01T11:00:00"),
                fee=170000,
                value=3000000,
                output_index=1,
            ),
        ]

        mock_session.execute.return_value = tx_rows

        result = TransactionAnalysisQueries.get_address_transaction_history(
            mock_session, "addr1test", limit=5
        )

        assert result["address"] == "addr1test"
        assert result["transaction_count"] == 2
        assert len(result["transactions"]) == 2
        assert (
            result["transactions"][0]["hash"]
            == "abc123def456789012345678901234567890123456789012345678901234"
        )
        assert result["transactions"][0]["block_number"] == 1000
        assert result["transactions"][0]["fee_ada"] == 0.18

    def test_get_hourly_transaction_throughput(self):
        """Test hourly transaction throughput calculation."""
        mock_session = Mock(spec=Session)

        # Mock hourly data
        hourly_rows = [
            Mock(
                hour=Mock(isoformat=lambda: "2023-01-01T10:00:00"),
                tx_count=500,
                avg_fee=200000,
            ),
            Mock(
                hour=Mock(isoformat=lambda: "2023-01-01T11:00:00"),
                tx_count=750,
                avg_fee=180000,
            ),
            Mock(
                hour=Mock(isoformat=lambda: "2023-01-01T12:00:00"),
                tx_count=600,
                avg_fee=190000,
            ),
        ]

        mock_session.execute.return_value = hourly_rows

        result = TransactionAnalysisQueries.get_hourly_transaction_throughput(
            mock_session, hours=24
        )

        assert result["period_hours"] == 24
        assert result["total_transactions"] == 1850  # 500 + 750 + 600
        assert result["peak_hour_transactions"] == 750
        assert result["average_per_hour"] == 1850 / 3
        assert len(result["hourly_data"]) == 3

    def test_get_large_transactions(self):
        """Test large transaction identification."""
        mock_session = Mock(spec=Session)

        # Mock large transaction data
        large_tx_rows = [
            Mock(
                hash_=bytes.fromhex(
                    "a1b2c3d4e5f67890123456789012345678901234567890123456789012345678"
                ),
                time=Mock(isoformat=lambda: "2023-01-01T12:00:00"),
                block_no=1000,
                total_output=50000000000,  # 50,000 ADA
                output_count=2,
            ),
            Mock(
                hash_=bytes.fromhex(
                    "b2c3d4e5f67890123456789012345678901234567890123456789012345678a1"
                ),
                time=Mock(isoformat=lambda: "2023-01-01T11:00:00"),
                block_no=999,
                total_output=25000000000,  # 25,000 ADA
                output_count=3,
            ),
        ]

        mock_session.execute.return_value = large_tx_rows

        result = TransactionAnalysisQueries.get_large_transactions(
            mock_session, min_ada=1000.0, limit=10
        )

        assert result["min_ada_threshold"] == 1000.0
        assert result["transaction_count"] == 2
        assert len(result["transactions"]) == 2
        assert (
            result["transactions"][0]["hash"]
            == "a1b2c3d4e5f67890123456789012345678901234567890123456789012345678"
        )
        assert result["transactions"][0]["total_output_ada"] == 50000.0

    def test_get_transaction_size_distribution(self):
        """Test transaction size distribution analysis."""
        mock_session = Mock(spec=Session)
        mock_result = Mock()
        mock_result.total_transactions = 10000
        mock_result.avg_inputs = 2.3
        mock_result.avg_outputs = 2.1

        mock_session.execute.return_value.first.return_value = mock_result

        result = TransactionAnalysisQueries.get_transaction_size_distribution(
            mock_session, days=7
        )

        assert result["period_days"] == 7
        assert result["total_transactions"] == 10000
        assert result["avg_inputs"] == 2.3
        assert result["avg_outputs"] == 2.1

    def test_async_not_implemented(self):
        """Test that async sessions raise NotImplementedError."""
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_async_session = Mock(spec=AsyncSession)

        with pytest.raises(NotImplementedError):
            TransactionAnalysisQueries.get_transaction_fee_stats(mock_async_session)

        with pytest.raises(NotImplementedError):
            TransactionAnalysisQueries.get_address_balance(mock_async_session, "addr1")


class TestComprehensiveTransactionAnalysis:
    """Test cases for comprehensive transaction analysis function."""

    @patch("dbsync.examples.queries.transaction_analysis.TransactionAnalysisQueries")
    def test_comprehensive_analysis_success(self, mock_queries_class):
        """Test successful comprehensive transaction analysis."""
        mock_session = Mock(spec=Session)
        mock_queries = mock_queries_class.return_value

        # Mock all the query results
        mock_queries.get_transaction_fee_stats.return_value = {
            "tx_count": 1000,
            "avg_fee": 200000,
            "min_fee": 150000,
            "max_fee": 500000,
            "total_fees": 200000000,
        }

        mock_queries.get_hourly_transaction_throughput.return_value = {
            "peak_hour_transactions": 150,
            "average_per_hour": 42.0,
            "hourly_data": [],
        }

        mock_queries.get_transaction_size_distribution.return_value = {
            "avg_inputs": 2.3,
            "avg_outputs": 2.1,
        }

        mock_queries.get_large_transactions.return_value = {
            "transaction_count": 5,
            "transactions": [{"total_output_ada": 50000.0}],
        }

        result = get_comprehensive_transaction_analysis(mock_session, days=7)

        # Verify structure and content
        assert result["analysis_period_days"] == 7
        assert "fee_stats" in result
        assert "throughput" in result
        assert "size_distribution" in result
        assert "large_transactions" in result
        assert "summary" in result

        # Verify summary calculations
        summary = result["summary"]
        assert summary["total_transactions"] == 1000
        assert summary["avg_fee_ada"] == 0.2  # 200000 / 1_000_000
        assert summary["peak_hourly_throughput"] == 150

    def test_comprehensive_analysis_query_calls(self):
        """Test that comprehensive analysis calls all expected queries."""
        mock_session = Mock(spec=Session)

        with patch(
            "dbsync.examples.queries.transaction_analysis.TransactionAnalysisQueries"
        ) as mock_class:
            mock_queries = mock_class.return_value

            # Set up minimal return values
            mock_queries.get_transaction_fee_stats.return_value = {
                "tx_count": 0,
                "avg_fee": 0,
            }
            mock_queries.get_hourly_transaction_throughput.return_value = {
                "peak_hour_transactions": 0
            }
            mock_queries.get_transaction_size_distribution.return_value = {
                "avg_inputs": 0,
                "avg_outputs": 0,
            }
            mock_queries.get_large_transactions.return_value = {
                "transaction_count": 0,
                "transactions": [],
            }

            get_comprehensive_transaction_analysis(mock_session, days=3)

            # Verify all queries were called
            mock_queries.get_transaction_fee_stats.assert_called_once_with(
                mock_session, 3
            )
            mock_queries.get_hourly_transaction_throughput.assert_called_once_with(
                mock_session, hours=72
            )  # 3 * 24
            mock_queries.get_transaction_size_distribution.assert_called_once_with(
                mock_session, 3
            )
            mock_queries.get_large_transactions.assert_called_once_with(
                mock_session, min_ada=1000.0, limit=5
            )


if __name__ == "__main__":
    pytest.main([__file__])
