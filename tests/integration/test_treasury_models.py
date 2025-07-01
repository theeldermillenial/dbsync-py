"""Integration tests for treasury and reserves models.

Tests SCHEMA-009: Treasury and Reserves Models integration with database.
"""

from sqlmodel import select

from dbsync.models.pools import ReserveUtxo
from dbsync.models.treasury import (
    AdaPots,
    PotTransfer,
    Treasury,
)


class TestTreasuryIntegration:
    """Integration tests for Treasury model."""

    def test_treasury_query_integration(self, dbsync_session):
        """Test Treasury model database integration."""
        # Test querying treasury payments (read-only)
        stmt = select(Treasury).limit(1)
        result = dbsync_session.exec(stmt)

        # Should not raise an exception (table may be empty)
        treasury_list = result.all()
        assert isinstance(treasury_list, list)

    def test_treasury_model_structure(self, dbsync_session):
        """Test Treasury model has correct structure."""
        # Test that Treasury model can be instantiated
        treasury = Treasury(
            addr_id=1,
            cert_index=0,
            amount=1000000000,
            tx_id=1,
        )

        # Check all required fields are present
        assert hasattr(treasury, "id_")
        assert hasattr(treasury, "addr_id")
        assert hasattr(treasury, "cert_index")
        assert hasattr(treasury, "amount")
        assert hasattr(treasury, "tx_id")

        # Check computed properties work
        assert treasury.amount_ada == 1000.0
        assert not treasury.is_large_payment


class TestPotTransferIntegration:
    """Integration tests for PotTransfer model."""

    def test_pot_transfer_query_integration(self, dbsync_session):
        """Test PotTransfer model database integration."""
        # Test querying pot transfers (read-only)
        stmt = select(PotTransfer).limit(1)
        result = dbsync_session.exec(stmt)

        # Should not raise an exception (table may be empty)
        transfer_list = result.all()
        assert isinstance(transfer_list, list)

    def test_pot_transfer_model_structure(self, dbsync_session):
        """Test PotTransfer model has correct structure."""
        # Test that PotTransfer model can be instantiated
        transfer = PotTransfer(
            cert_index=0,
            treasury=-1000000000,  # 1000 ADA from treasury
            reserves=1000000000,  # 1000 ADA to reserves
            tx_id=1,
        )

        # Check all required fields are present
        assert hasattr(transfer, "id_")
        assert hasattr(transfer, "cert_index")
        assert hasattr(transfer, "treasury")
        assert hasattr(transfer, "reserves")
        assert hasattr(transfer, "tx_id")

        # Check computed properties work
        assert transfer.treasury_ada == -1000.0
        assert transfer.reserves_ada == 1000.0
        assert transfer.transfer_direction == "treasury_to_reserves"


class TestAdaPotsIntegration:
    """Integration tests for AdaPots model."""

    def test_ada_pots_query_integration(self, dbsync_session):
        """Test AdaPots model database integration."""
        # Test querying ADA pots (read-only)
        stmt = select(AdaPots).limit(1)
        result = dbsync_session.exec(stmt)

        # Should not raise an exception (table may be empty)
        pots_list = result.all()
        assert isinstance(pots_list, list)

    def test_ada_pots_model_structure(self, dbsync_session):
        """Test AdaPots model has correct structure."""
        # Test that AdaPots model can be instantiated
        ada_pots = AdaPots(
            slot_no=1000000,
            epoch_no=100,
            treasury=1000000000000000,  # 1B ADA
            reserves=2000000000000000,  # 2B ADA
            rewards=100000000000000,  # 100M ADA
            utxo=30000000000000000,  # 30B ADA
            deposits_stake=50000000000000,
            deposits_drep=10000000000000,
            deposits_proposal=5000000000000,
            fees=1000000000000,
            block_id=1000,
        )

        # Check all required fields are present
        assert hasattr(ada_pots, "id_")
        assert hasattr(ada_pots, "slot_no")
        assert hasattr(ada_pots, "epoch_no")
        assert hasattr(ada_pots, "treasury")
        assert hasattr(ada_pots, "reserves")
        assert hasattr(ada_pots, "rewards")
        assert hasattr(ada_pots, "utxo")
        assert hasattr(ada_pots, "deposits_stake")
        assert hasattr(ada_pots, "deposits_drep")
        assert hasattr(ada_pots, "deposits_proposal")
        assert hasattr(ada_pots, "fees")
        assert hasattr(ada_pots, "block_id")

        # Check computed properties work
        assert ada_pots.total_supply_ada > 30000000000  # Over 30B ADA
        assert ada_pots.circulating_supply_ada > 25000000000  # Over 25B ADA


class TestReserveUtxoIntegration:
    """Integration tests for ReserveUtxo model (from pools module)."""

    def test_reserve_utxo_query_integration(self, dbsync_session):
        """Test ReserveUtxo model database integration."""
        # Test querying reserve UTXOs (read-only)
        stmt = select(ReserveUtxo).limit(1)
        result = dbsync_session.exec(stmt)

        # Should not raise an exception (table may be empty)
        reserve_list = result.all()
        assert isinstance(reserve_list, list)

    def test_reserve_utxo_model_structure(self, dbsync_session):
        """Test ReserveUtxo model has correct structure."""
        # Test that ReserveUtxo model can be instantiated
        reserve = ReserveUtxo(
            addr_id=1,
            cert_index=0,
            amount=1000000000,
            tx_id=1,
        )

        # Check all required fields are present
        assert hasattr(reserve, "id_")
        assert hasattr(reserve, "addr_id")
        assert hasattr(reserve, "cert_index")
        assert hasattr(reserve, "amount")
        assert hasattr(reserve, "tx_id")


class TestTreasuryEcosystemIntegration:
    """Integration tests for the complete treasury ecosystem."""

    def test_all_treasury_models_importable(self):
        """Test that all treasury-related models can be imported together."""
        # This test ensures no circular imports or conflicts
        from dbsync.models.pools import ReserveUtxo
        from dbsync.models.treasury import AdaPots, PotTransfer, Treasury

        # All models should be classes
        assert isinstance(Treasury, type)
        assert isinstance(PotTransfer, type)
        assert isinstance(AdaPots, type)
        assert isinstance(ReserveUtxo, type)

    def test_treasury_ecosystem_consistency(self, dbsync_session):
        """Test consistency across treasury ecosystem models."""
        # Create instances of all treasury-related models
        treasury = Treasury(
            addr_id=1,
            cert_index=0,
            amount=1000000000,
            tx_id=1,
        )

        reserve = ReserveUtxo(
            addr_id=1,
            cert_index=1,
            amount=500000000,
            tx_id=1,
        )

        transfer = PotTransfer(
            cert_index=2,
            treasury=-1000000000,
            reserves=1000000000,
            tx_id=1,
        )

        ada_pots = AdaPots(
            slot_no=1000000,
            epoch_no=100,
            treasury=10000000000000000,  # 10B ADA
            reserves=15000000000000000,  # 15B ADA
            rewards=100000000000000,
            utxo=20000000000000000,
            deposits_stake=50000000000000,
            deposits_drep=10000000000000,
            deposits_proposal=5000000000000,
            fees=1000000000000,
            block_id=1000,
        )

        # All models should reference the same transaction
        assert treasury.tx_id == reserve.tx_id == transfer.tx_id

        # Treasury and reserve should have consistent field types
        assert type(treasury.addr_id) == type(reserve.addr_id)
        assert type(treasury.amount) == type(reserve.amount)

        # PotTransfer should balance (conservation test)
        assert transfer.treasury + transfer.reserves == 0

        # AdaPots should have realistic total supply
        assert ada_pots.total_supply > 0
        assert ada_pots.circulating_supply > 0
