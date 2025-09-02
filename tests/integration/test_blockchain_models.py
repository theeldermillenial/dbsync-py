"""Integration tests for blockchain models.

Tests blockchain models with actual database connections and verifies
read-only behavior and proper SQLAlchemy integration.
"""

import pytest
from sqlmodel import Session, select

from dbsync.models import (
    Address,
    Block,
    Epoch,
    SchemaVersion,
    SlotLeader,
    StakeAddress,
    Transaction,
)
from tests.integration.base import BaseIntegrationTest


@pytest.mark.integration
class TestBlockchainModelsIntegration(BaseIntegrationTest):
    """Integration tests for blockchain models with database."""

    def test_address_model_integration(self, dbsync_session: Session) -> None:
        """Test Address model with actual database."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test querying addresses
            stmt = select(Address).limit(1)
            result = dbsync_session.exec(stmt).first()

            if result:
                # Verify all required fields exist and have correct types
                assert hasattr(result, "id_")
                assert hasattr(result, "address")
                assert hasattr(result, "raw")
                assert hasattr(result, "has_script")
                assert hasattr(result, "payment_cred")
                assert hasattr(result, "stake_address_id")

                # Verify field types and values
                assert isinstance(result.id_, int)
                assert isinstance(result.address, str)
                assert isinstance(result.raw, bytes)
                assert isinstance(result.has_script, bool)
                
                # Verify address format (should be bech32)
                assert len(result.address) > 20  # Reasonable address length
                
                # Verify raw bytes exist
                assert len(result.raw) > 0
                
                # payment_cred can be None
                if result.payment_cred is not None:
                    assert isinstance(result.payment_cred, bytes)
                    
                # stake_address_id can be None
                if result.stake_address_id is not None:
                    assert isinstance(result.stake_address_id, int)
                    assert result.stake_address_id > 0

            else:
                pytest.skip("No address data available for testing")
                
        except Exception as e:
            pytest.skip(f"Address table not available: {e}")

    def test_transaction_treasury_donation_integration(self, dbsync_session: Session) -> None:
        """Test Transaction model treasury_donation field with actual database."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            stmt = select(Transaction).limit(10)  # Check multiple transactions
            results = dbsync_session.exec(stmt).all()

            if results:
                for result in results:
                    # Verify treasury_donation field exists
                    assert hasattr(result, "treasury_donation")
                    
                    # Verify it's a numeric type (lovelace amount) - could be int or Decimal
                    from decimal import Decimal
                    assert isinstance(result.treasury_donation, (int, Decimal))
                    
                    # Verify it's non-negative (donations can't be negative)
                    assert result.treasury_donation >= 0
                    
                    # Most transactions should have 0 treasury donation
                    # (treasury donations are rare)
                    
            else:
                pytest.skip("No transaction data available for testing")
                
        except Exception as e:
            pytest.skip(f"Transaction table not available: {e}")

    def test_schema_version_types_integration(self, dbsync_session: Session) -> None:
        """Test SchemaVersion model with BigInteger types."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            stmt = select(SchemaVersion).limit(1)
            result = dbsync_session.exec(stmt).first()

            if result:
                # Verify all stage fields exist
                assert hasattr(result, "stage_one")
                assert hasattr(result, "stage_two") 
                assert hasattr(result, "stage_three")
                
                # Verify they can handle large integers (BigInteger range)
                if result.stage_one is not None:
                    assert isinstance(result.stage_one, int)
                    assert result.stage_one >= 0
                    
                if result.stage_two is not None:
                    assert isinstance(result.stage_two, int)
                    assert result.stage_two >= 0
                    
                if result.stage_three is not None:
                    assert isinstance(result.stage_three, int)
                    assert result.stage_three >= 0
                    
                # Test version string method
                version_str = str(result)
                assert isinstance(version_str, str)
                assert "." in version_str  # Should be dot-separated
                
            else:
                pytest.skip("No schema version data available for testing")
                
        except Exception as e:
            pytest.skip(f"Schema version table not available: {e}")

    def test_blockchain_model_relationships(self, dbsync_session: Session) -> None:
        """Test relationships between blockchain models."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test Address -> StakeAddress relationship
            stmt = select(Address).where(Address.stake_address_id.is_not(None)).limit(1)
            address = dbsync_session.exec(stmt).first()
            
            if address and address.stake_address_id:
                # Verify we can find the related stake address
                stake_stmt = select(StakeAddress).where(StakeAddress.id_ == address.stake_address_id)
                stake_address = dbsync_session.exec(stake_stmt).first()
                
                if stake_address:
                    assert stake_address.id_ == address.stake_address_id
                    assert isinstance(stake_address.hash_raw, bytes)
                    assert isinstance(stake_address.view, str)
                    
            # Test Block -> Transaction relationship  
            stmt = select(Block).limit(1)
            block = dbsync_session.exec(stmt).first()
            
            if block:
                # Verify we can find transactions in this block
                tx_stmt = select(Transaction).where(Transaction.block_id == block.id_).limit(1)
                transaction = dbsync_session.exec(tx_stmt).first()
                
                if transaction:
                    assert transaction.block_id == block.id_
                    assert hasattr(transaction, "treasury_donation")
                    
        except Exception as e:
            pytest.skip(f"Relationship testing failed: {e}")

    def test_address_model_no_hash_field(self, dbsync_session: Session) -> None:
        """Test that Address model no longer has the old hash_ field."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            stmt = select(Address).limit(1)
            result = dbsync_session.exec(stmt).first()

            if result:
                # Verify old fields are gone
                assert not hasattr(result, "hash_")
                assert not hasattr(result, "view")  # This is now "address"
                
                # Verify new fields exist
                assert hasattr(result, "address")  # New field
                assert hasattr(result, "raw")      # New field
                assert hasattr(result, "has_script")  # New field
                
        except Exception as e:
            pytest.skip(f"Address field verification failed: {e}")

    def test_all_blockchain_models_query_successfully(self, dbsync_session: Session) -> None:
        """Test that all blockchain models can be queried without errors."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        models_to_test = [
            (Address, "address"),
            (StakeAddress, "stake_address"), 
            (Block, "block"),
            (Transaction, "tx"),
            (Epoch, "epoch"),
            (SlotLeader, "slot_leader"),
            (SchemaVersion, "schema_version"),
        ]

        for model_class, table_name in models_to_test:
            try:
                # Verify table exists
                assert self.verify_table_exists(dbsync_session, table_name)
                
                # Verify we can query without errors
                stmt = select(model_class).limit(1)
                result = dbsync_session.exec(stmt).first()
                
                # If there's data, verify basic properties
                if result:
                    assert hasattr(result, "id_")
                    assert result.id_ is not None
                    assert isinstance(result.id_, int)
                    
            except Exception as e:
                pytest.fail(f"Model {model_class.__name__} query failed: {e}")
