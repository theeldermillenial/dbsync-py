"""Chain Metadata Queries - Example Implementation.

This example demonstrates how to use the dbsync-py package to implement
common chain metadata and fundamental blockchain data queries.

This file converts SQL examples from the Cardano DB Sync documentation
to SQLAlchemy implementations using the dbsync-py models.

Based on SQL examples from:
https://github.com/IntersectMBO/cardano-db-sync/blob/master/doc/interesting-queries.md

Usage:
    from dbsync.examples.queries.chain_metadata import ChainMetadataQueries, get_chain_info
    from dbsync.session import get_session

    with get_session() as session:
        info = get_chain_info(session)
        print(f"Current supply: {info['supply_ada']:.2f} ADA")
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ...models import Block, ChainMeta, TransactionInput, TransactionOutput

# Lovelace is just an int in the application layer


class ChainMetadataQueries:
    """Example chain metadata and fundamental blockchain data queries.

    This class demonstrates SQLAlchemy implementations of common chain metadata
    queries, including supply calculations, sync progress, and basic chain info.

    These are example implementations showing how to use the dbsync-py package
    models to build useful queries.
    """

    @staticmethod
    def get_chain_metadata(session: Session | AsyncSession) -> ChainMeta | None:
        """Get chain metadata information.

        SQL equivalent:
            SELECT * FROM meta;

        Returns:
            ChainMeta object with network information, or None if not found

        Example:
            >>> from dbsync.session import get_session
            >>> with get_session() as session:
            ...     meta = ChainMetadataQueries.get_chain_metadata(session)
            ...     print(f"Network: {meta.network_name}")
            ...     print(f"Start time: {meta.start_time}")
        """
        stmt = select(ChainMeta)

        if isinstance(session, AsyncSession):
            raise NotImplementedError("Async version not yet implemented")
        else:
            result = session.execute(stmt).scalar_one_or_none()
            return result

    @staticmethod
    def get_current_supply(session: Session | AsyncSession) -> int:
        """Calculate the current total on-chain supply of Ada.

        Note: 1 ADA == 1,000,000 Lovelace

        This queries the UTxO set for unspent transaction outputs. It does not
        include staking rewards that have not yet been withdrawn. Before being
        withdrawn, rewards exist in ledger state and not on-chain.

        SQL equivalent:
            SELECT sum(value) FROM tx_out AS tx_outer WHERE
                NOT EXISTS (
                    SELECT tx_out.id FROM tx_out
                    INNER JOIN tx_in ON tx_out.tx_id = tx_in.tx_out_id
                        AND tx_out.index = tx_in.tx_out_index
                    WHERE tx_outer.id = tx_out.id
                );

        Returns:
            Total supply in Lovelace

        Example:
            >>> from dbsync.session import get_session
            >>> with get_session() as session:
            ...     supply = ChainMetadataQueries.get_current_supply(session)
            ...     print(f"Current supply: {supply / 1_000_000:.2f} ADA")
        """
        if isinstance(session, AsyncSession):
            raise NotImplementedError("Async version not yet implemented")

        # Create subquery for spent outputs
        spent_outputs = select(TransactionOutput.id_).select_from(
            TransactionOutput.__table__.join(
                TransactionInput.__table__,
                (TransactionOutput.tx_id == TransactionInput.tx_out_id)
                & (TransactionOutput.index == TransactionInput.tx_out_index),
            )
        )

        # Main query for unspent outputs
        stmt = select(func.sum(TransactionOutput.value)).where(
            ~TransactionOutput.id_.in_(spent_outputs)
        )

        result = session.execute(stmt).scalar()
        return int(result or 0)

    @staticmethod
    def get_latest_slot_number(session: Session | AsyncSession) -> int | None:
        """Get the slot number of the most recent block.

        SQL equivalent:
            SELECT slot_no FROM block WHERE block_no IS NOT NULL
            ORDER BY block_no DESC LIMIT 1;

        Returns:
            Latest slot number, or None if no blocks found

        Example:
            >>> from dbsync.session import get_session
            >>> with get_session() as session:
            ...     slot = ChainMetadataQueries.get_latest_slot_number(session)
            ...     print(f"Latest slot: {slot}")
        """
        stmt = (
            select(Block.slot_no)
            .where(Block.block_no.is_not(None))
            .order_by(Block.block_no.desc())
            .limit(1)
        )

        if isinstance(session, AsyncSession):
            raise NotImplementedError("Async version not yet implemented")
        else:
            result = session.execute(stmt).scalar_one_or_none()
            return result

    @staticmethod
    def get_database_size_pretty(session: Session | AsyncSession) -> str:
        """Get the human-readable size of the database.

        SQL equivalent:
            SELECT pg_size_pretty(pg_database_size(current_database()));

        Returns:
            Human-readable database size (e.g., "116 GB")

        Example:
            >>> from dbsync.session import get_session
            >>> with get_session() as session:
            ...     size = ChainMetadataQueries.get_database_size_pretty(session)
            ...     print(f"Database size: {size}")
        """
        stmt = text("SELECT pg_size_pretty(pg_database_size(current_database()))")

        if isinstance(session, AsyncSession):
            raise NotImplementedError("Async version not yet implemented")
        else:
            result = session.execute(stmt).scalar()
            return result or "Unknown"

    @staticmethod
    def get_table_size_pretty(
        session: Session | AsyncSession, table_name: str = "block"
    ) -> str:
        """Get the human-readable size of a specific database table.

        SQL equivalent:
            SELECT pg_size_pretty(pg_total_relation_size('block'));

        Args:
            table_name: Name of the table to check (default: 'block')

        Returns:
            Human-readable table size (e.g., "2760 MB")

        Example:
            >>> from dbsync.session import get_session
            >>> with get_session() as session:
            ...     size = ChainMetadataQueries.get_table_size_pretty(session, "tx_out")
            ...     print(f"tx_out table size: {size}")
        """
        stmt = text("SELECT pg_size_pretty(pg_total_relation_size(:table_name))")

        if isinstance(session, AsyncSession):
            raise NotImplementedError("Async version not yet implemented")
        else:
            result = session.execute(stmt, {"table_name": table_name}).scalar()
            return result or "Unknown"

    @staticmethod
    def get_sync_progress_percent(session: Session | AsyncSession) -> float:
        """Get rough estimate of sync progress as a percentage.

        To get a rough estimate of how close to fully synced the database is,
        we use the timestamps on the blocks.

        Note: This value can be misleading as it operates on block timestamps
        and early epochs contain much less data (e.g., Byron era did not have
        staking) and much fewer transactions.

        SQL equivalent:
            SELECT 100 * (
                extract(epoch from (max(time) at time zone 'UTC')) -
                extract(epoch from (min(time) at time zone 'UTC'))
            ) / (
                extract(epoch from (now() at time zone 'UTC')) -
                extract(epoch from (min(time) at time zone 'UTC'))
            ) AS sync_percent
            FROM block;

        Returns:
            Sync progress percentage (0.0 to 100.0)

        Example:
            >>> from dbsync.session import get_session
            >>> with get_session() as session:
            ...     progress = ChainMetadataQueries.get_sync_progress_percent(session)
            ...     print(f"Sync progress: {progress:.2f}%")
        """
        stmt = select(
            100.0
            * (
                func.extract("epoch", func.max(Block.time))
                - func.extract("epoch", func.min(Block.time))
            )
            / (
                func.extract("epoch", func.now())
                - func.extract("epoch", func.min(Block.time))
            )
        )

        if isinstance(session, AsyncSession):
            raise NotImplementedError("Async version not yet implemented")
        else:
            result = session.execute(stmt).scalar()
            return float(result or 0.0)

    @staticmethod
    def get_sync_behind_duration(session: Session | AsyncSession) -> str | None:
        """Get how far behind the sync is from current time.

        SQL equivalent:
            SELECT now() - max(time) AS behind_by FROM block;

        Returns:
            Time duration string (e.g., "4 days 20:59:39.134497") or None

        Example:
            >>> from dbsync.session import get_session
            >>> with get_session() as session:
            ...     behind = ChainMetadataQueries.get_sync_behind_duration(session)
            ...     print(f"Sync is behind by: {behind}")
        """
        stmt = select(func.now() - func.max(Block.time))

        if isinstance(session, AsyncSession):
            raise NotImplementedError("Async version not yet implemented")
        else:
            result = session.execute(stmt).scalar()
            return str(result) if result else None


# Convenience functions for direct usage
def get_chain_info(session: Session | AsyncSession) -> dict[str, Any]:
    """Get comprehensive chain information in a single call.

    Returns a dictionary with all basic chain metadata including:
    - Chain metadata (network, start time)
    - Current supply in ADA and Lovelace
    - Latest slot number
    - Database size information
    - Sync progress information

    Args:
        session: Database session (sync or async)

    Returns:
        Dictionary containing all chain information

    Example:
        >>> from dbsync.session import get_session
        >>> with get_session() as session:
        ...     info = get_chain_info(session)
        ...     print(f"Network: {info['network']}")
        ...     print(f"Supply: {info['supply_ada']:.2f} ADA")
        ...     print(f"Latest slot: {info['latest_slot']}")
    """
    queries = ChainMetadataQueries()

    # Get chain metadata
    meta = queries.get_chain_metadata(session)

    # Get supply information
    supply_lovelace = queries.get_current_supply(session)
    supply_ada = float(supply_lovelace) / 1_000_000

    # Get latest slot
    latest_slot = queries.get_latest_slot_number(session)

    # Get database size info
    db_size = queries.get_database_size_pretty(session)
    block_table_size = queries.get_table_size_pretty(session, "block")

    # Get sync progress
    sync_progress = queries.get_sync_progress_percent(session)
    sync_behind = queries.get_sync_behind_duration(session)

    return {
        "network": meta.network_name if meta else "Unknown",
        "start_time": meta.start_time if meta else None,
        "supply_lovelace": supply_lovelace,
        "supply_ada": supply_ada,
        "latest_slot": latest_slot,
        "database_size": db_size,
        "block_table_size": block_table_size,
        "sync_progress_percent": sync_progress,
        "sync_behind": sync_behind,
    }


if __name__ == "__main__":
    """Example usage when run directly."""
    try:
        from ...session import get_session

        print("Chain Metadata Queries Example")
        print("=" * 40)

        with get_session() as session:
            info = get_chain_info(session)

            print(f"Network: {info['network']}")
            print(f"Supply: {info['supply_ada']:,.2f} ADA")
            print(f"Latest slot: {info['latest_slot']:,}")
            print(f"Database size: {info['database_size']}")
            print(f"Sync progress: {info['sync_progress_percent']:.2f}%")

    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you have a configured database connection.")
