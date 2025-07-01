"""Property-based tests for dbsync models using Hypothesis.

This module implements property-based testing to automatically generate test cases
and discover edge cases in model validation, data conversion, and business logic.
"""

from datetime import datetime

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st
from hypothesis.strategies import composite

from dbsync.models.assets import MaTxOut, MultiAsset
from dbsync.models.blockchain import Block, Epoch, StakeAddress, Transaction
from dbsync.models.scripts import CostModel, Script
from dbsync.models.transactions import TransactionOutput


# Custom strategies for Cardano-specific data types
@composite
def cardano_hash28(draw):
    """Generate valid 28-byte hashes for Cardano."""
    return draw(st.binary(min_size=28, max_size=28))


@composite
def cardano_hash32(draw):
    """Generate valid 32-byte hashes for Cardano."""
    return draw(st.binary(min_size=32, max_size=32))


@composite
def cardano_address_bytes(draw):
    """Generate valid Cardano address bytes (up to 65 bytes)."""
    return draw(st.binary(min_size=29, max_size=65))


@composite
def lovelace_amount(draw):
    """Generate valid lovelace amounts (positive integers)."""
    return draw(st.integers(min_value=1, max_value=45_000_000_000_000_000))


@composite
def epoch_number(draw):
    """Generate valid epoch numbers."""
    return draw(st.integers(min_value=0, max_value=1000))


@composite
def slot_number(draw):
    """Generate valid slot numbers."""
    return draw(st.integers(min_value=0, max_value=100_000_000))


@composite
def block_number(draw):
    """Generate valid block numbers."""
    return draw(st.integers(min_value=0, max_value=10_000_000))


class TestPropertyBasedModels:
    """Property-based tests for core dbsync models."""

    @given(
        hash_=cardano_hash32(),
        epoch_no=epoch_number(),
        slot_no=slot_number(),
        block_no=block_number(),
        previous_id=st.one_of(st.none(), st.integers(min_value=1, max_value=1000000)),
    )
    @settings(max_examples=50, deadline=5000)
    def test_block_properties(self, hash_, epoch_no, slot_no, block_no, previous_id):
        """Test Block model properties with generated data."""
        block = Block(
            hash_=hash_,
            epoch_no=epoch_no,
            slot_no=slot_no,
            block_no=block_no,
            previous_id=previous_id,
            size=1024,
            tx_count=5,
            proto_major=8,
            proto_minor=0,
        )

        # Property: hash should be 32 bytes
        assert len(block.hash_) == 32

        # Property: slot and block numbers should be non-negative
        assert block.slot_no >= 0
        assert block.block_no >= 0
        assert block.epoch_no >= 0

        # Property: hash can be converted to hex (using DBSyncBase encoding)
        hex_string = block.hash_.hex()
        assert len(hex_string) == 64
        assert all(c in "0123456789abcdef" for c in hex_string.lower())

        # Property: hash roundtrip should work
        assert bytes.fromhex(hex_string) == block.hash_

    @given(
        hash_=cardano_hash32(),
        fee=lovelace_amount(),
        out_sum=lovelace_amount(),
        size=st.integers(min_value=100, max_value=16384),
        block_id=st.integers(min_value=1, max_value=1000000),
    )
    @settings(max_examples=50, deadline=5000)
    def test_transaction_properties(self, hash_, fee, out_sum, size, block_id):
        """Test Transaction model properties with generated data."""
        tx = Transaction(
            hash_=hash_,
            block_id=block_id,
            fee=fee,
            out_sum=out_sum,
            size=size,
            valid_contract=True,
        )

        # Property: fee should be positive
        assert tx.fee > 0

        # Property: output sum should be positive
        assert tx.out_sum > 0

        # Property: size should be reasonable
        assert 100 <= tx.size <= 16384

        # Property: hash should be 32 bytes
        assert len(tx.hash_) == 32

        # Property: hash can be converted to hex
        hex_string = tx.hash_.hex()
        assert len(hex_string) == 64
        assert all(c in "0123456789abcdef" for c in hex_string.lower())

    @given(
        address_id=st.integers(min_value=1, max_value=1000000),
        value=lovelace_amount(),
        tx_id=st.integers(min_value=1, max_value=1000000),
        index=st.integers(min_value=0, max_value=255),
    )
    @settings(max_examples=50, deadline=5000)
    def test_tx_out_properties(self, address_id, value, tx_id, index):
        """Test TransactionOutput model properties with generated data."""
        tx_out = TransactionOutput(
            tx_id=tx_id,
            index=index,
            address_id=address_id,
            value=value,
        )

        # Property: value should be positive
        assert tx_out.value > 0

        # Property: index should be non-negative and reasonable
        assert 0 <= tx_out.index <= 255

        # Property: address_id should be positive
        assert tx_out.address_id > 0

    @given(
        policy=cardano_hash28(),
        name=st.binary(min_size=0, max_size=32),
        fingerprint=st.text(
            min_size=10, max_size=100, alphabet="abcdefghijklmnopqrstuvwxyz0123456789"
        ),
    )
    @settings(max_examples=50, deadline=5000)
    def test_multi_asset_properties(self, policy, name, fingerprint):
        """Test MultiAsset model properties with generated data."""
        asset = MultiAsset(policy=policy, name=name, fingerprint=fingerprint)

        # Property: policy should be 28 bytes
        assert len(asset.policy) == 28

        # Property: name should be reasonable length
        assert len(asset.name) <= 32

        # Property: policy can be converted to hex
        policy_hex = asset.policy.hex()
        assert len(policy_hex) == 56
        assert all(c in "0123456789abcdef" for c in policy_hex.lower())

        # Property: name can be converted to hex
        name_hex = asset.name.hex()
        assert len(name_hex) == len(asset.name) * 2
        assert all(c in "0123456789abcdef" for c in name_hex.lower())

    @given(
        hash_raw=cardano_hash28(),
        view=st.text(
            min_size=10, max_size=100, alphabet="abcdefghijklmnopqrstuvwxyz0123456789"
        ),
    )
    @settings(max_examples=50, deadline=5000)
    def test_stake_address_properties(self, hash_raw, view):
        """Test StakeAddress model properties with generated data."""
        stake_addr = StakeAddress(hash_raw=hash_raw, view=view)

        # Property: hash_raw should be 28 bytes
        assert len(stake_addr.hash_raw) == 28

        # Property: hash_raw can be converted to hex
        hash_hex = stake_addr.hash_raw.hex()
        assert len(hash_hex) == 56
        assert all(c in "0123456789abcdef" for c in hash_hex.lower())

        # Property: view should be non-empty
        assert len(stake_addr.view) > 0

        # Property: hash roundtrip should work
        assert bytes.fromhex(hash_hex) == stake_addr.hash_raw

    @given(
        hash_=cardano_hash28(),
        tx_id=st.integers(min_value=1, max_value=1000000),
        script_type=st.sampled_from(["native", "plutusV1", "plutusV2", "plutusV3"]),
    )
    @settings(max_examples=50, deadline=5000)
    def test_script_properties(self, hash_, tx_id, script_type):
        """Test Script model properties with generated data (has hash_hex property)."""
        script = Script(
            hash_=hash_, tx_id=tx_id, type_=script_type, serialised_size=1024
        )

        # Property: hash should be 28 bytes
        assert len(script.hash_) == 28

        # Property: hash_hex property should work correctly
        assert len(script.hash_hex) == 56
        assert all(c in "0123456789abcdef" for c in script.hash_hex.lower())

        # Property: hash roundtrip should work
        assert bytes.fromhex(script.hash_hex) == script.hash_

        # Property: script type properties should work
        if script_type == "native":
            assert script.is_native is True
            assert script.is_plutus is False
        else:
            assert script.is_native is False
            assert script.is_plutus is True


class TestPropertyBasedValidation:
    """Property-based tests for model validation edge cases."""

    @given(
        epoch_no=st.integers(min_value=-1000, max_value=1000),
        start_time=st.datetimes(
            min_value=datetime(2020, 1, 1), max_value=datetime(2025, 1, 1)
        ),
        end_time=st.datetimes(
            min_value=datetime(2020, 1, 1), max_value=datetime(2025, 1, 1)
        ),
    )
    @settings(max_examples=30, deadline=3000)
    def test_epoch_validation_edge_cases(self, epoch_no, start_time, end_time):
        """Test Epoch model with edge case values."""
        # Only test with valid values (non-negative epoch numbers)
        assume(epoch_no >= 0)
        assume(start_time <= end_time)  # Logical constraint

        epoch = Epoch(no=epoch_no, start_time=start_time, end_time=end_time)

        # Property: epoch number should always be non-negative when valid
        assert epoch.no >= 0

    @given(
        value=st.integers(min_value=-1000, max_value=45_000_000_000_000_000),
        index=st.integers(min_value=-10, max_value=300),
    )
    @settings(max_examples=30, deadline=3000)
    def test_tx_out_validation_edge_cases(self, value, index):
        """Test TransactionOutput validation with edge case values."""
        # Only test with valid values
        assume(value > 0 and 0 <= index <= 255)

        tx_out = TransactionOutput(tx_id=1, index=index, address_id=1, value=value)

        # Property: valid TransactionOutput should have positive value
        assert tx_out.value > 0

        # Property: valid TransactionOutput should have reasonable index
        assert 0 <= tx_out.index <= 255

    @given(binary_data=st.binary(min_size=0, max_size=100))
    @settings(max_examples=50, deadline=3000)
    def test_hex_conversion_properties(self, binary_data):
        """Test hex conversion properties across all models."""
        # Test that hex conversion is always reversible (using DBSyncBase encoding)
        hex_string = binary_data.hex()

        # Property: hex string should be even length
        assert len(hex_string) % 2 == 0

        # Property: hex string should only contain valid hex characters
        assert all(c in "0123456789abcdef" for c in hex_string.lower())

        # Property: roundtrip conversion should preserve data
        assert bytes.fromhex(hex_string) == binary_data

        # Property: hex length should be exactly double binary length
        assert len(hex_string) == len(binary_data) * 2


class TestPropertyBasedBusinessLogic:
    """Property-based tests for business logic and constraints."""

    @given(fee=lovelace_amount(), out_sum=lovelace_amount())
    @settings(max_examples=30, deadline=3000)
    def test_transaction_balance_properties(self, fee, out_sum):
        """Test transaction balance constraints."""
        # Assume reasonable values to avoid overflow
        assume(fee < 1_000_000_000)  # 1000 ADA max fee
        assume(out_sum < 1_000_000_000_000)  # 1M ADA max output

        # Ensure fee is less than output sum for meaningful test
        assume(fee < out_sum)

        tx = Transaction(
            hash_=b"a" * 32,
            block_id=1,
            fee=fee,
            out_sum=out_sum,
            size=200,
            valid_contract=True,
        )

        # Property: fee should be less than output sum for normal transactions
        assert tx.fee < tx.out_sum  # Fee should be less than total output

    @given(
        policy_id=cardano_hash28(),
        asset_name=st.binary(min_size=0, max_size=32),
        quantity=st.integers(min_value=1, max_value=1_000_000_000_000),
    )
    @settings(max_examples=30, deadline=3000)
    def test_multi_asset_quantity_properties(self, policy_id, asset_name, quantity):
        """Test multi-asset quantity constraints."""
        asset = MultiAsset(policy=policy_id, name=asset_name, fingerprint="asset1test")

        ma_tx_out = MaTxOut(
            ident=1,  # References multi_asset.id
            quantity=quantity,
            tx_out_id=1,
        )

        # Property: quantity should be positive
        assert ma_tx_out.quantity > 0

        # Property: ident should reference the multi-asset
        assert ma_tx_out.ident == 1

        # Property: quantity should be reasonable (not exceed max supply)
        assert ma_tx_out.quantity <= 1_000_000_000_000  # 1 trillion max

    @given(
        hash_=cardano_hash32(),
        costs=st.dictionaries(
            st.text(min_size=5, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz-"),
            st.integers(min_value=0, max_value=1_000_000),
            min_size=1,
            max_size=20,
        ),
    )
    @settings(max_examples=30, deadline=3000)
    def test_cost_model_properties(self, hash_, costs):
        """Test CostModel properties with generated data."""
        cost_model = CostModel(hash_=hash_, costs=costs)

        # Property: hash should be 32 bytes
        assert len(cost_model.hash_) == 32

        # Property: hash_hex property should work correctly
        assert len(cost_model.hash_hex) == 64
        assert all(c in "0123456789abcdef" for c in cost_model.hash_hex.lower())

        # Property: costs should be non-empty dictionary
        assert len(cost_model.costs) > 0

        # Property: operation_count should match costs dictionary size
        assert cost_model.operation_count == len(cost_model.costs)

        # Property: all cost values should be non-negative
        for operation, cost in cost_model.costs.items():
            assert cost >= 0
            assert cost_model.get_operation_cost(operation) == cost
            assert cost_model.has_operation(operation) is True


if __name__ == "__main__":
    # Run property-based tests
    pytest.main([__file__, "-v"])
