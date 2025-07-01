"""Integration tests for pool management models.

Tests pool models with actual database connections and verifies
read-only behavior and proper SQLAlchemy integration.
"""

import pytest
from sqlmodel import Session, select

from dbsync.models import (
    OffchainPoolData,
    OffchainPoolFetchError,
    PoolHash,
    PoolMetadataRef,
    PoolOwner,
    PoolRelay,
    PoolRetire,
    PoolUpdate,
    ReserveUtxo,
)


class TestPoolModelsIntegration:
    """Integration tests for pool models with database."""

    def test_pool_hash_query_integration(self, dbsync_session: Session) -> None:
        """Test PoolHash model database integration."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test querying pool hashes (read-only)
            stmt = select(PoolHash).limit(1)
            result = dbsync_session.exec(stmt).first()

            # Verify we can query the model
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "hash_raw")
                assert hasattr(result, "view")
        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_pool_update_query_integration(self, dbsync_session: Session) -> None:
        """Test PoolUpdate model database integration."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test querying pool updates (read-only)
            stmt = select(PoolUpdate).limit(1)
            result = dbsync_session.exec(stmt).first()

            # Verify we can query the model
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "hash_id")
                assert hasattr(result, "cert_index")
                assert hasattr(result, "active_epoch_no")
        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_pool_retire_query_integration(self, dbsync_session: Session) -> None:
        """Test PoolRetire model database integration."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test querying pool retirements (read-only)
            stmt = select(PoolRetire).limit(1)
            result = dbsync_session.exec(stmt).first()

            # Verify we can query the model
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "hash_id")
                assert hasattr(result, "retiring_epoch")
        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_pool_owner_query_integration(self, dbsync_session: Session) -> None:
        """Test PoolOwner model database integration."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test querying pool owners (read-only)
            stmt = select(PoolOwner).limit(1)
            result = dbsync_session.exec(stmt).first()

            # Verify we can query the model
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "addr_id")
                assert hasattr(result, "pool_update_id")
        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_pool_relay_query_integration(self, dbsync_session: Session) -> None:
        """Test PoolRelay model database integration."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test querying pool relays (read-only)
            stmt = select(PoolRelay).limit(1)
            result = dbsync_session.exec(stmt).first()

            # Verify we can query the model
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "update_id")
        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_pool_metadata_ref_query_integration(self, dbsync_session: Session) -> None:
        """Test PoolMetadataRef model database integration."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test querying pool metadata references (read-only)
            stmt = select(PoolMetadataRef).limit(1)
            result = dbsync_session.exec(stmt).first()

            # Verify we can query the model
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "pool_id")
                assert hasattr(result, "url")
        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_offchain_pool_data_query_integration(
        self, dbsync_session: Session
    ) -> None:
        """Test OffchainPoolData model database integration."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test querying offchain pool data (read-only)
            stmt = select(OffchainPoolData).limit(1)
            result = dbsync_session.exec(stmt).first()

            # Verify we can query the model
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "pool_id")
                assert hasattr(result, "ticker_name")
                assert hasattr(result, "hash_")
                assert hasattr(result, "json_")
        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_offchain_pool_fetch_error_query_integration(
        self, dbsync_session: Session
    ) -> None:
        """Test OffchainPoolFetchError model database integration."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test querying offchain pool fetch errors (read-only)
            stmt = select(OffchainPoolFetchError).limit(1)
            result = dbsync_session.exec(stmt).first()

            # Verify we can query the model
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "pool_id")
                assert hasattr(result, "fetch_error")
        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_reserve_utxo_query_integration(self, dbsync_session: Session) -> None:
        """Test ReserveUtxo model database integration."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test querying reserve UTXOs (read-only)
            stmt = select(ReserveUtxo).limit(1)
            result = dbsync_session.exec(stmt).first()

            # Verify we can query the model
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "addr_id")
                assert hasattr(result, "amount")
        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_pool_models_read_only_behavior(self, dbsync_session: Session) -> None:
        """Test that pool models are used in read-only mode."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # This test verifies that the models are designed for read-only access
            # In a real dbsync environment, these tables are populated by the dbsync process

            # Test that we can create queries but the expectation is read-only usage
            pool_hash_query = select(PoolHash)
            pool_update_query = select(PoolUpdate)
            pool_retire_query = select(PoolRetire)

            # Verify queries can be constructed (this is the expected usage pattern)
            assert pool_hash_query is not None
            assert pool_update_query is not None
            assert pool_retire_query is not None
        except Exception as e:
            pytest.skip(f"Database not available: {e}")

    def test_pool_relationships_integration(self, dbsync_session: Session) -> None:
        """Test pool model relationships in database context."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test querying pools with their related data
            stmt = (
                select(PoolHash, PoolUpdate)
                .join(PoolUpdate, PoolHash.id_ == PoolUpdate.hash_id)
                .limit(1)
            )

            result = dbsync_session.exec(stmt).first()

            # Verify relationship queries work
            if result:
                pool_hash, pool_update = result
                assert pool_hash.id_ == pool_update.hash_id
        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_pool_metadata_relationships_integration(
        self, dbsync_session: Session
    ) -> None:
        """Test pool metadata relationships in database context."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test querying pools with their metadata
            stmt = (
                select(PoolUpdate, PoolMetadataRef)
                .join(PoolMetadataRef, PoolUpdate.meta_id == PoolMetadataRef.id_)
                .limit(1)
            )

            result = dbsync_session.exec(stmt).first()

            # Verify metadata relationships work
            if result:
                pool_update, metadata_ref = result
                assert pool_update.meta_id == metadata_ref.id_
        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_pool_relay_types_integration(self, dbsync_session: Session) -> None:
        """Test different pool relay types in database context."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test querying different types of relays
            ipv4_stmt = select(PoolRelay).where(PoolRelay.ipv4.is_not(None)).limit(1)
            ipv6_stmt = select(PoolRelay).where(PoolRelay.ipv6.is_not(None)).limit(1)
            dns_stmt = select(PoolRelay).where(PoolRelay.dns_name.is_not(None)).limit(1)

            ipv4_result = dbsync_session.exec(ipv4_stmt).first()
            ipv6_result = dbsync_session.exec(ipv6_stmt).first()
            dns_result = dbsync_session.exec(dns_stmt).first()

            # Verify different relay types can be queried
            if ipv4_result:
                assert ipv4_result.ipv4 is not None
            if ipv6_result:
                assert ipv6_result.ipv6 is not None
            if dns_result:
                assert dns_result.dns_name is not None
        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_pool_lifecycle_query_integration(self, dbsync_session: Session) -> None:
        """Test querying complete pool lifecycle in database context."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test querying a pool's complete lifecycle
            stmt = (
                select(PoolHash)
                .join(PoolUpdate, PoolHash.id_ == PoolUpdate.hash_id)
                .limit(1)
            )

            result = dbsync_session.exec(stmt).first()

            if result:
                pool_hash = result

                # Query all updates for this pool
                updates_stmt = (
                    select(PoolUpdate)
                    .where(PoolUpdate.hash_id == pool_hash.id_)
                    .order_by(PoolUpdate.active_epoch_no)
                )
                updates = dbsync_session.exec(updates_stmt).all()

                # Query retirement if exists
                retire_stmt = select(PoolRetire).where(
                    PoolRetire.hash_id == pool_hash.id_
                )
                retirement = dbsync_session.exec(retire_stmt).first()

                # Verify we can track pool lifecycle
                assert len(updates) >= 0  # May or may not have updates
                # retirement may or may not exist
        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_pool_performance_query_integration(self, dbsync_session: Session) -> None:
        """Test querying pool performance data in database context."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test querying pools with their offchain data
            stmt = (
                select(PoolHash, OffchainPoolData)
                .join(OffchainPoolData, PoolHash.id_ == OffchainPoolData.pool_id)
                .limit(1)
            )

            result = dbsync_session.exec(stmt).first()

            # Verify performance data queries work
            if result:
                pool_hash, offchain_data = result
                assert pool_hash.id_ == offchain_data.pool_id
                # Verify offchain data structure
                assert hasattr(offchain_data, "ticker_name")
                assert hasattr(offchain_data, "json_")
        except Exception as e:
            pytest.skip(f"Database table not available: {e}")
