"""Unit tests for treasury and reserves models.

Tests SCHEMA-009: Treasury and Reserves Models including:
- Treasury payment model
- PotTransfer model
- AdaPots model
- ReserveUtxo model (from pools module)
"""

import pytest

from dbsync.models.pools import ReserveUtxo
from dbsync.models.treasury import (
    AdaPots,
    PotTransfer,
    Treasury,
)


class TestTreasury:
    """Test Treasury model."""

    def test_treasury_creation(self):
        """Test Treasury model creation."""
        treasury = Treasury(
            id_=1,
            addr_id=100,
            cert_index=0,
            amount=1000000000000,  # 1M ADA in lovelace
            tx_id=500,
        )

        assert treasury.id_ == 1
        assert treasury.addr_id == 100
        assert treasury.cert_index == 0
        assert treasury.amount == 1000000000000
        assert treasury.tx_id == 500

    def test_treasury_amount_ada_property(self):
        """Test Treasury amount_ada property."""
        treasury = Treasury(
            addr_id=100,
            cert_index=0,
            amount=5000000,  # 5 ADA in lovelace
            tx_id=500,
        )

        assert treasury.amount_ada == 5.0

    def test_treasury_is_large_payment_true(self):
        """Test Treasury is_large_payment property returns True for large payments."""
        treasury = Treasury(
            addr_id=100,
            cert_index=0,
            amount=2000000000000,  # 2M ADA in lovelace
            tx_id=500,
        )

        assert treasury.is_large_payment is True

    def test_treasury_is_large_payment_false(self):
        """Test Treasury is_large_payment property returns False for normal payments."""
        treasury = Treasury(
            addr_id=100,
            cert_index=0,
            amount=100000000,  # 100 ADA in lovelace
            tx_id=500,
        )

        assert treasury.is_large_payment is False

    def test_treasury_to_reward_record(self):
        """Test Treasury to_reward_record method."""
        treasury = Treasury(
            addr_id=100,
            cert_index=1,
            amount=5000000000,  # 5K ADA in lovelace
            tx_id=500,
        )

        record = treasury.to_reward_record()

        expected = {
            "type": "treasury",
            "address_id": 100,
            "amount": 5000000000,
            "amount_ada": 5000.0,
            "tx_id": 500,
            "cert_index": 1,
        }
        assert record == expected


class TestPotTransfer:
    """Test PotTransfer model."""

    def test_pot_transfer_creation(self):
        """Test PotTransfer model creation."""
        transfer = PotTransfer(
            id_=3,
            cert_index=0,
            treasury=1000000000000,  # 1M ADA gain
            reserves=-1000000000000,  # 1M ADA loss
            tx_id=700,
        )

        assert transfer.id_ == 3
        assert transfer.cert_index == 0
        assert transfer.treasury == 1000000000000
        assert transfer.reserves == -1000000000000
        assert transfer.tx_id == 700

    def test_pot_transfer_ada_properties(self):
        """Test PotTransfer ADA conversion properties."""
        transfer = PotTransfer(
            cert_index=0,
            treasury=-500000000,  # -500 ADA
            reserves=500000000,  # +500 ADA
            tx_id=700,
        )

        assert transfer.treasury_ada == -500.0
        assert transfer.reserves_ada == 500.0

    def test_pot_transfer_direction_treasury_to_reserves(self):
        """Test PotTransfer transfer_direction for treasury to reserves."""
        transfer = PotTransfer(
            cert_index=0,
            treasury=-1000000000,  # Treasury loses
            reserves=1000000000,  # Reserves gains
            tx_id=700,
        )

        assert transfer.transfer_direction == "treasury_to_reserves"

    def test_pot_transfer_direction_reserves_to_treasury(self):
        """Test PotTransfer transfer_direction for reserves to treasury."""
        transfer = PotTransfer(
            cert_index=0,
            treasury=2000000000,  # Treasury gains
            reserves=-2000000000,  # Reserves loses
            tx_id=700,
        )

        assert transfer.transfer_direction == "reserves_to_treasury"

    def test_pot_transfer_direction_balanced(self):
        """Test PotTransfer transfer_direction for balanced transfers."""
        transfer = PotTransfer(
            cert_index=0,
            treasury=0,
            reserves=0,
            tx_id=700,
        )

        assert transfer.transfer_direction == "balanced"

    def test_pot_transfer_total_amount_transferred(self):
        """Test PotTransfer total_amount_transferred property."""
        transfer = PotTransfer(
            cert_index=0,
            treasury=-750000000,  # -750 ADA
            reserves=750000000,  # +750 ADA
            tx_id=700,
        )

        assert transfer.total_amount_transferred == 750000000
        assert transfer.total_amount_transferred_ada == 750.0

    def test_pot_transfer_direction_methods(self):
        """Test PotTransfer direction checking methods."""
        # Treasury to reserves
        transfer1 = PotTransfer(
            cert_index=0,
            treasury=-1000000000,
            reserves=1000000000,
            tx_id=700,
        )
        assert transfer1.is_treasury_to_reserves() is True
        assert transfer1.is_reserves_to_treasury() is False

        # Reserves to treasury
        transfer2 = PotTransfer(
            cert_index=0,
            treasury=1000000000,
            reserves=-1000000000,
            tx_id=700,
        )
        assert transfer2.is_treasury_to_reserves() is False
        assert transfer2.is_reserves_to_treasury() is True


class TestAdaPots:
    """Test AdaPots model."""

    def test_ada_pots_creation(self):
        """Test AdaPots model creation."""
        ada_pots = AdaPots(
            id_=4,
            slot_no=12345678,
            epoch_no=200,
            treasury=5000000000000000,  # 5B ADA
            reserves=10000000000000000,  # 10B ADA
            rewards=500000000000000,  # 500M ADA
            utxo=20000000000000000,  # 20B ADA
            deposits_stake=100000000000000,  # 100M ADA
            deposits_drep=50000000000000,  # 50M ADA
            deposits_proposal=25000000000000,  # 25M ADA
            fees=10000000000000,  # 10M ADA
            block_id=1000,
        )

        assert ada_pots.id_ == 4
        assert ada_pots.slot_no == 12345678
        assert ada_pots.epoch_no == 200
        assert ada_pots.treasury == 5000000000000000
        assert ada_pots.reserves == 10000000000000000
        assert ada_pots.rewards == 500000000000000
        assert ada_pots.utxo == 20000000000000000
        assert ada_pots.deposits_stake == 100000000000000
        assert ada_pots.deposits_drep == 50000000000000
        assert ada_pots.deposits_proposal == 25000000000000
        assert ada_pots.fees == 10000000000000
        assert ada_pots.block_id == 1000

    def test_ada_pots_total_supply(self):
        """Test AdaPots total_supply property."""
        ada_pots = AdaPots(
            slot_no=12345678,
            epoch_no=200,
            treasury=1000000000000,  # 1M ADA
            reserves=2000000000000,  # 2M ADA
            rewards=3000000000000,  # 3M ADA
            utxo=4000000000000,  # 4M ADA
            deposits_stake=5000000000000,  # 5M ADA
            deposits_drep=6000000000000,  # 6M ADA
            deposits_proposal=7000000000000,  # 7M ADA
            fees=8000000000000,  # 8M ADA
            block_id=1000,
        )

        # Total: 36M ADA
        expected_total = 36000000000000
        assert ada_pots.total_supply == expected_total
        assert ada_pots.total_supply_ada == 36000000.0

    def test_ada_pots_get_distribution_summary(self):
        """Test AdaPots get_distribution_summary method."""
        ada_pots = AdaPots(
            slot_no=12345678,
            epoch_no=200,
            treasury=10000000000000,  # 10M ADA
            reserves=20000000000000,  # 20M ADA
            rewards=5000000000000,  # 5M ADA
            utxo=15000000000000,  # 15M ADA
            deposits_stake=2000000000000,
            deposits_drep=1000000000000,
            deposits_proposal=500000000000,
            fees=1500000000000,  # 1.5M ADA
            block_id=1000,
        )

        summary = ada_pots.get_distribution_summary()

        # Total: 55M ADA
        assert summary["total_supply_ada"] == 55000000.0
        assert summary["circulating_supply_ada"] == 20000000.0  # UTxO + rewards
        assert summary["treasury_ada"] == 10000000.0
        assert summary["reserves_ada"] == 20000000.0
        assert summary["treasury_percentage"] == pytest.approx(18.18, rel=1e-2)
        assert summary["reserves_percentage"] == pytest.approx(36.36, rel=1e-2)
        assert summary["utxo_percentage"] == pytest.approx(27.27, rel=1e-2)
        assert summary["epoch_no"] == 200
        assert summary["slot_no"] == 12345678


class TestReserveUtxoIntegration:
    """Test ReserveUtxo model integration (from pools module)."""

    def test_reserve_utxo_is_available(self):
        """Test that ReserveUtxo model is properly available."""
        # This tests that ReserveUtxo is the correct model for reserve table
        reserve = ReserveUtxo(
            addr_id=100,
            cert_index=0,
            amount=1000000000,  # 1000 ADA
            tx_id=500,
        )

        assert reserve.addr_id == 100
        assert reserve.cert_index == 0
        assert reserve.amount == 1000000000
        assert reserve.tx_id == 500

    def test_treasury_and_reserve_consistency(self):
        """Test that Treasury and ReserveUtxo models have consistent field structure."""
        treasury = Treasury(
            addr_id=100,
            cert_index=0,
            amount=1000000000,
            tx_id=500,
        )

        reserve = ReserveUtxo(
            addr_id=100,
            cert_index=0,
            amount=1000000000,
            tx_id=500,
        )

        # Both should have the same basic field structure
        assert treasury.addr_id == reserve.addr_id
        assert treasury.cert_index == reserve.cert_index
        assert treasury.amount == reserve.amount
        assert treasury.tx_id == reserve.tx_id
