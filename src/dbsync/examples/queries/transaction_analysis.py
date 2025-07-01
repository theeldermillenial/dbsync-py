"""Transaction Analysis Queries - Example Implementation.

This example demonstrates how to use the dbsync-py package to implement
transaction analysis and UTxO operation queries.

This file converts common transaction analysis patterns to SQLAlchemy
implementations using the dbsync-py models.

Based on common patterns for Cardano transaction analysis and UTxO operations.

Usage:
    from dbsync.examples.queries.transaction_analysis import TransactionAnalysisQueries
    from dbsync.session import get_session

    with get_session() as session:
        fee_stats = TransactionAnalysisQueries.get_transaction_fee_stats(session)
        print(f"Average fee: {fee_stats['avg_fee'] / 1_000_000:.2f} ADA")
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ...models import (
    Address,
    Block,
    Transaction,
    TransactionInput,
    TransactionOutput,
)


class TransactionAnalysisQueries:
    """Example transaction analysis and UTxO operation queries.

    This class demonstrates SQLAlchemy implementations of common transaction
    analysis patterns, including fee analysis, UTxO calculations, and address
    transaction history.

    These are example implementations showing how to use the dbsync-py package
    models to build useful transaction analysis queries.
    """

    @staticmethod
    def get_transaction_fee_stats(
        session: Session | AsyncSession, days: int = 7
    ) -> dict[str, Any]:
        """Get transaction fee statistics for the specified time period.

        SQL equivalent:
            SELECT
                COUNT(*) as tx_count,
                AVG(fee) as avg_fee,
                MIN(fee) as min_fee,
                MAX(fee) as max_fee,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY fee) as median_fee,
                SUM(fee) as total_fees
            FROM tx
            INNER JOIN block ON tx.block_id = block.id
            WHERE block.time > NOW() - INTERVAL '%s days';

        Args:
            session: Database session (sync or async)
            days: Number of days to analyze (default: 7)

        Returns:
            Dictionary with fee statistics

        Example:
            >>> from dbsync.session import get_session
            >>> with get_session() as session:
            ...     stats = TransactionAnalysisQueries.get_transaction_fee_stats(session)
            ...     print(f"Average fee: {stats['avg_fee'] / 1_000_000:.2f} ADA")
        """
        if isinstance(session, AsyncSession):
            raise NotImplementedError("Async version not yet implemented")

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        stmt = (
            select(
                func.count(Transaction.id_).label("tx_count"),
                func.avg(Transaction.fee).label("avg_fee"),
                func.min(Transaction.fee).label("min_fee"),
                func.max(Transaction.fee).label("max_fee"),
                func.sum(Transaction.fee).label("total_fees"),
            )
            .select_from(Transaction.__table__.join(Block.__table__))
            .where(Block.time > cutoff_date)
        )

        result = session.execute(stmt).first()

        if not result:
            return {
                "tx_count": 0,
                "avg_fee": 0,
                "min_fee": 0,
                "max_fee": 0,
                "total_fees": 0,
                "period_days": days,
            }

        return {
            "tx_count": int(result.tx_count or 0),
            "avg_fee": int(result.avg_fee or 0),
            "min_fee": int(result.min_fee or 0),
            "max_fee": int(result.max_fee or 0),
            "total_fees": int(result.total_fees or 0),
            "period_days": days,
        }

    @staticmethod
    def get_address_balance(
        session: Session | AsyncSession, address: str
    ) -> dict[str, Any]:
        """Calculate current balance for a given address using UTxO method.

        This calculates the balance by finding all unspent transaction outputs
        (UTxOs) for the address and summing their values.

        SQL equivalent:
            SELECT
                addr.address,
                COUNT(utxo.id) as utxo_count,
                SUM(utxo.value) as total_balance
            FROM address addr
            INNER JOIN tx_out utxo ON addr.id = utxo.address_id
            LEFT JOIN tx_in spent ON utxo.id = spent.tx_out_id
                AND utxo.index = spent.tx_out_index
            WHERE addr.address = %s AND spent.id IS NULL
            GROUP BY addr.address;

        Args:
            session: Database session (sync or async)
            address: Cardano address to check

        Returns:
            Dictionary with balance information

        Example:
            >>> with get_session() as session:
            ...     balance = TransactionAnalysisQueries.get_address_balance(
            ...         session, "addr1..."
            ...     )
            ...     print(f"Balance: {balance['balance_ada']:.2f} ADA")
        """
        if isinstance(session, AsyncSession):
            raise NotImplementedError("Async version not yet implemented")

        # Find unspent outputs for the address
        stmt = (
            select(
                func.count(TransactionOutput.id_).label("utxo_count"),
                func.sum(TransactionOutput.value).label("total_balance"),
            )
            .select_from(TransactionOutput.__table__.join(Address.__table__))
            .outerjoin(
                TransactionInput.__table__,
                and_(
                    TransactionOutput.id_ == TransactionInput.tx_out_id,
                    TransactionOutput.index == TransactionInput.tx_out_index,
                ),
            )
            .where(
                and_(
                    Address.view == address,
                    TransactionInput.id_.is_(None),  # Not spent
                )
            )
        )

        result = session.execute(stmt).first()

        if not result or result.total_balance is None:
            return {
                "address": address,
                "utxo_count": 0,
                "total_balance": 0,
                "balance_ada": 0.0,
                "found": False,
            }

        total_balance = int(result.total_balance)
        return {
            "address": address,
            "utxo_count": int(result.utxo_count or 0),
            "total_balance": total_balance,
            "balance_ada": total_balance / 1_000_000,
            "found": True,
        }

    @staticmethod
    def get_transaction_inputs_outputs(
        session: Session | AsyncSession, tx_hash: str
    ) -> dict[str, Any]:
        """Get detailed input and output information for a transaction.

        Args:
            session: Database session (sync or async)
            tx_hash: Transaction hash to analyze

        Returns:
            Dictionary with input and output details

        Example:
            >>> with get_session() as session:
            ...     details = TransactionAnalysisQueries.get_transaction_inputs_outputs(
            ...         session, "abc123..."
            ...     )
            ...     print(f"Inputs: {len(details['inputs'])}, Outputs: {len(details['outputs'])}")
        """
        if isinstance(session, AsyncSession):
            raise NotImplementedError("Async version not yet implemented")

        # Get transaction ID from hash
        tx_stmt = select(Transaction.id_, Transaction.fee).where(
            Transaction.hash_ == bytes.fromhex(tx_hash)
        )
        tx_result = session.execute(tx_stmt).first()

        if not tx_result:
            return {
                "transaction_hash": tx_hash,
                "found": False,
                "inputs": [],
                "outputs": [],
                "fee": 0,
            }

        tx_id = tx_result.id_
        fee = tx_result.fee or 0

        # Get inputs with their source addresses
        inputs_stmt = (
            select(TransactionInput.tx_out_index, TransactionOutput.value, Address.view)
            .select_from(
                TransactionInput.__table__.join(
                    TransactionOutput.__table__,
                    TransactionInput.tx_out_id == TransactionOutput.id_,
                ).join(Address.__table__, TransactionOutput.address_id == Address.id_)
            )
            .where(TransactionInput.tx_in_id == tx_id)
        )

        inputs = []
        for row in session.execute(inputs_stmt):
            inputs.append(
                {
                    "index": row.tx_out_index,
                    "value": int(row.value or 0),
                    "value_ada": (row.value or 0) / 1_000_000,
                    "address": row.address,
                }
            )

        # Get outputs
        outputs_stmt = (
            select(TransactionOutput.index, TransactionOutput.value, Address.view)
            .select_from(
                TransactionOutput.__table__.join(
                    Address.__table__, TransactionOutput.address_id == Address.id_
                )
            )
            .where(TransactionOutput.tx_id == tx_id)
        )

        outputs = []
        for row in session.execute(outputs_stmt):
            outputs.append(
                {
                    "index": row.index,
                    "value": int(row.value or 0),
                    "value_ada": (row.value or 0) / 1_000_000,
                    "address": row.address,
                }
            )

        return {
            "transaction_hash": tx_hash,
            "found": True,
            "inputs": inputs,
            "outputs": outputs,
            "fee": int(fee),
            "fee_ada": fee / 1_000_000,
            "input_count": len(inputs),
            "output_count": len(outputs),
            "total_input": sum(inp["value"] for inp in inputs),
            "total_output": sum(out["value"] for out in outputs),
        }

    @staticmethod
    def get_address_transaction_history(
        session: Session | AsyncSession, address: str, limit: int = 10
    ) -> dict[str, Any]:
        """Get recent transaction history for an address.

        Args:
            session: Database session (sync or async)
            address: Address to analyze
            limit: Maximum number of transactions to return

        Returns:
            Dictionary with transaction history

        Example:
            >>> with get_session() as session:
            ...     history = TransactionAnalysisQueries.get_address_transaction_history(
            ...         session, "addr1...", limit=5
            ...     )
            ...     print(f"Recent transactions: {len(history['transactions'])}")
        """
        if isinstance(session, AsyncSession):
            raise NotImplementedError("Async version not yet implemented")

        # Get transactions where address appears in outputs
        stmt = (
            select(
                Transaction.hash_,
                Transaction.fee,
                Block.time,
                Block.block_no,
                TransactionOutput.value,
                TransactionOutput.index.label("output_index"),
            )
            .select_from(
                Transaction.__table__.join(Block.__table__)
                .join(TransactionOutput.__table__)
                .join(Address.__table__)
            )
            .where(Address.view == address)
            .order_by(desc(Block.time))
            .limit(limit)
        )

        transactions = []
        for row in session.execute(stmt):
            transactions.append(
                {
                    "hash": row.hash_.hex() if row.hash_ else None,
                    "block_number": row.block_no,
                    "time": row.time.isoformat() if row.time else None,
                    "fee": int(row.fee or 0),
                    "fee_ada": (row.fee or 0) / 1_000_000,
                    "output_value": int(row.value or 0),
                    "output_value_ada": (row.value or 0) / 1_000_000,
                    "output_index": row.output_index,
                }
            )

        return {
            "address": address,
            "transaction_count": len(transactions),
            "transactions": transactions,
        }

    @staticmethod
    def get_hourly_transaction_throughput(
        session: Session | AsyncSession, hours: int = 24
    ) -> dict[str, Any]:
        """Get transaction throughput statistics by hour.

        Args:
            session: Database session (sync or async)
            hours: Number of hours to analyze

        Returns:
            Dictionary with hourly throughput data

        Example:
            >>> with get_session() as session:
            ...     throughput = TransactionAnalysisQueries.get_hourly_transaction_throughput(session)
            ...     print(f"Peak hour: {throughput['peak_hour_transactions']} transactions")
        """
        if isinstance(session, AsyncSession):
            raise NotImplementedError("Async version not yet implemented")

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        # Define the hour expression once to avoid SQL issues
        hour_expr = func.date_trunc("hour", Block.time)

        stmt = (
            select(
                hour_expr.label("hour"),
                func.count(Transaction.id_).label("tx_count"),
                func.avg(Transaction.fee).label("avg_fee"),
            )
            .select_from(Transaction.__table__.join(Block.__table__))
            .where(Block.time > cutoff_time)
            .group_by(hour_expr)
            .order_by(hour_expr)
        )

        hourly_data = []
        total_transactions = 0
        peak_hour_transactions = 0

        for row in session.execute(stmt):
            tx_count = int(row.tx_count or 0)
            total_transactions += tx_count
            peak_hour_transactions = max(peak_hour_transactions, tx_count)

            hourly_data.append(
                {
                    "hour": row.hour.isoformat() if row.hour else None,
                    "transaction_count": tx_count,
                    "avg_fee": int(row.avg_fee or 0),
                    "avg_fee_ada": (row.avg_fee or 0) / 1_000_000,
                }
            )

        return {
            "period_hours": hours,
            "total_transactions": total_transactions,
            "hourly_data": hourly_data,
            "peak_hour_transactions": peak_hour_transactions,
            "average_per_hour": total_transactions / max(len(hourly_data), 1),
        }

    @staticmethod
    def get_large_transactions(
        session: Session | AsyncSession, min_ada: float = 1000.0, limit: int = 10
    ) -> dict[str, Any]:
        """Get transactions with large ADA amounts.

        Args:
            session: Database session (sync or async)
            min_ada: Minimum ADA amount to consider "large"
            limit: Maximum number of transactions to return

        Returns:
            Dictionary with large transaction data

        Example:
            >>> with get_session() as session:
            ...     large_txs = TransactionAnalysisQueries.get_large_transactions(
            ...         session, min_ada=10000.0
            ...     )
            ...     print(f"Found {len(large_txs['transactions'])} large transactions")
        """
        if isinstance(session, AsyncSession):
            raise NotImplementedError("Async version not yet implemented")

        min_lovelace = int(min_ada * 1_000_000)

        stmt = (
            select(
                Transaction.hash_,
                Block.time,
                Block.block_no,
                func.sum(TransactionOutput.value).label("total_output"),
                func.count(TransactionOutput.id_).label("output_count"),
            )
            .select_from(
                Transaction.__table__.join(Block.__table__).join(
                    TransactionOutput.__table__
                )
            )
            .group_by(Transaction.id_, Transaction.hash_, Block.time, Block.block_no)
            .having(func.sum(TransactionOutput.value) >= min_lovelace)
            .order_by(desc(func.sum(TransactionOutput.value)))
            .limit(limit)
        )

        transactions = []
        for row in session.execute(stmt):
            total_output = int(row.total_output or 0)
            transactions.append(
                {
                    "hash": row.hash_.hex() if row.hash_ else None,
                    "block_number": row.block_no,
                    "time": row.time.isoformat() if row.time else None,
                    "total_output": total_output,
                    "total_output_ada": total_output / 1_000_000,
                    "output_count": int(row.output_count or 0),
                }
            )

        return {
            "min_ada_threshold": min_ada,
            "transaction_count": len(transactions),
            "transactions": transactions,
        }

    @staticmethod
    def get_transaction_size_distribution(
        session: Session | AsyncSession, days: int = 7
    ) -> dict[str, Any]:
        """Get transaction size distribution statistics.

        This analyzes transaction sizes by counting inputs and outputs.

        Args:
            session: Database session (sync or async)
            days: Number of days to analyze

        Returns:
            Dictionary with size distribution data

        Example:
            >>> with get_session() as session:
            ...     distribution = TransactionAnalysisQueries.get_transaction_size_distribution(session)
            ...     print(f"Average inputs: {distribution['avg_inputs']:.2f}")
        """
        if isinstance(session, AsyncSession):
            raise NotImplementedError("Async version not yet implemented")

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Analyze input/output counts
        stmt = (
            select(
                func.avg(
                    func.coalesce(
                        select(func.count(TransactionInput.id_))
                        .where(TransactionInput.tx_in_id == Transaction.id_)
                        .scalar_subquery(),
                        0,
                    )
                ).label("avg_inputs"),
                func.avg(
                    func.coalesce(
                        select(func.count(TransactionOutput.id_))
                        .where(TransactionOutput.tx_id == Transaction.id_)
                        .scalar_subquery(),
                        0,
                    )
                ).label("avg_outputs"),
                func.count(Transaction.id_).label("total_transactions"),
            )
            .select_from(Transaction.__table__.join(Block.__table__))
            .where(Block.time > cutoff_date)
        )

        result = session.execute(stmt).first()

        if not result:
            return {
                "period_days": days,
                "total_transactions": 0,
                "avg_inputs": 0.0,
                "avg_outputs": 0.0,
            }

        return {
            "period_days": days,
            "total_transactions": int(result.total_transactions or 0),
            "avg_inputs": float(result.avg_inputs or 0.0),
            "avg_outputs": float(result.avg_outputs or 0.0),
        }


# Convenience functions for direct usage
def get_comprehensive_transaction_analysis(
    session: Session | AsyncSession, days: int = 7
) -> dict[str, Any]:
    """Get comprehensive transaction analysis in a single call.

    Returns a dictionary with various transaction analysis metrics including:
    - Fee statistics
    - Transaction throughput
    - Size distribution
    - Large transaction analysis

    Args:
        session: Database session (sync or async)
        days: Number of days to analyze

    Returns:
        Dictionary containing comprehensive analysis

    Example:
        >>> from dbsync.session import get_session
        >>> with get_session() as session:
        ...     analysis = get_comprehensive_transaction_analysis(session)
        ...     print(f"Total transactions: {analysis['fee_stats']['tx_count']:,}")
        ...     print(f"Average fee: {analysis['fee_stats']['avg_fee'] / 1_000_000:.4f} ADA")
    """
    print("Starting comprehensive transaction analysis...")
    queries = TransactionAnalysisQueries()

    # Get fee statistics
    print("Getting fee statistics...")
    fee_stats = queries.get_transaction_fee_stats(session, days)

    # Get throughput data
    print("Getting throughput data...")
    throughput = queries.get_hourly_transaction_throughput(session, hours=days * 24)

    # Get size distribution
    print("Getting size distribution...")
    size_distribution = queries.get_transaction_size_distribution(session, days)

    # Get large transactions
    print("Getting large transactions (this may take a while)...")
    large_transactions = queries.get_large_transactions(
        session, min_ada=1000.0, limit=5
    )

    return {
        "analysis_period_days": days,
        "fee_stats": fee_stats,
        "throughput": throughput,
        "size_distribution": size_distribution,
        "large_transactions": large_transactions,
        "summary": {
            "total_transactions": fee_stats["tx_count"],
            "avg_fee_ada": (
                fee_stats["avg_fee"] / 1_000_000 if fee_stats["avg_fee"] else 0
            ),
            "peak_hourly_throughput": throughput["peak_hour_transactions"],
            "avg_transaction_size": f"{size_distribution['avg_inputs']:.1f} inputs, {size_distribution['avg_outputs']:.1f} outputs",
        },
    }


if __name__ == "__main__":
    """Example usage when run directly."""
    try:
        from ...session import get_session

        print("Transaction Analysis Queries Example")
        print("=" * 50)

        with get_session() as session:
            analysis = get_comprehensive_transaction_analysis(session)

            print(f"Analysis Period: {analysis['analysis_period_days']} days")
            print(f"Total Transactions: {analysis['fee_stats']['tx_count']:,}")
            print(f"Average Fee: {analysis['summary']['avg_fee_ada']:.4f} ADA")
            print(
                f"Peak Hourly Throughput: {analysis['summary']['peak_hourly_throughput']:,} transactions"
            )
            print(
                f"Average Transaction Size: {analysis['summary']['avg_transaction_size']}"
            )

    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you have a configured database connection.")
