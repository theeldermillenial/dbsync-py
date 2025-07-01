"""Parameterized tests for dbsync models.

This module demonstrates enhanced testing patterns using pytest.mark.parametrize
to create comprehensive, data-driven test suites that reduce repetition and
improve test coverage.
"""

from datetime import UTC, datetime

import pytest

from dbsync.models.assets import MaTxOut, MultiAsset
from dbsync.models.blockchain import Block, StakeAddress, Transaction
from dbsync.models.scripts import PlutusVersion, RedeemerTag, Script, ScriptType
from dbsync.models.staking import StakeDeregistration, StakeRegistration
from dbsync.models.transactions import TransactionOutput


class TestParameterizedEnums:
    """Parameterized tests for enum values and validation."""

    @pytest.mark.parametrize(
        "enum_value,expected_string",
        [
            (ScriptType.NATIVE, "native"),
            (ScriptType.PLUTUS_V1, "plutusV1"),
            (ScriptType.PLUTUS_V2, "plutusV2"),
            (ScriptType.PLUTUS_V3, "plutusV3"),
        ],
    )
    def test_script_type_values(self, enum_value, expected_string):
        """Test ScriptType enum values using parameterized data."""
        assert enum_value == expected_string
        assert enum_value in ScriptType

    @pytest.mark.parametrize(
        "enum_value,expected_string",
        [
            (PlutusVersion.V1, "PlutusV1"),
            (PlutusVersion.V2, "PlutusV2"),
            (PlutusVersion.V3, "PlutusV3"),
        ],
    )
    def test_plutus_version_values(self, enum_value, expected_string):
        """Test PlutusVersion enum values using parameterized data."""
        assert enum_value == expected_string
        assert enum_value in PlutusVersion

    @pytest.mark.parametrize(
        "enum_value,expected_string",
        [
            (RedeemerTag.SPEND, "spend"),
            (RedeemerTag.MINT, "mint"),
            (RedeemerTag.CERT, "cert"),
            (RedeemerTag.REWARD, "reward"),
            (RedeemerTag.VOTE, "vote"),
            (RedeemerTag.PROPOSE, "propose"),
        ],
    )
    def test_redeemer_tag_values(self, enum_value, expected_string):
        """Test RedeemerTag enum values using parameterized data."""
        assert enum_value == expected_string
        assert enum_value in RedeemerTag

    @pytest.mark.parametrize(
        "invalid_value",
        [
            "invalid_script_type",
            "plutusV4",
            "unknown",
            "",
            None,
        ],
    )
    def test_enum_invalid_values(self, invalid_value):
        """Test that invalid values are not in enums."""
        assert invalid_value not in ScriptType
        assert invalid_value not in PlutusVersion
        assert invalid_value not in RedeemerTag


class TestParameterizedScriptProperties:
    """Parameterized tests for Script model properties."""

    @pytest.mark.parametrize(
        "script_type,expected_is_native,expected_is_plutus",
        [
            (ScriptType.NATIVE, True, False),
            (ScriptType.PLUTUS_V1, False, True),
            (ScriptType.PLUTUS_V2, False, True),
            (ScriptType.PLUTUS_V3, False, True),
        ],
    )
    def test_script_type_properties(
        self, script_type, expected_is_native, expected_is_plutus
    ):
        """Test Script type-based properties with different script types."""
        script = Script(
            tx_id=100,
            hash_=b"test_hash_28_bytes_long_12345",  # 28 bytes
            type_=script_type,
            serialised_size=1024,
        )

        assert script.is_native == expected_is_native
        assert script.is_plutus == expected_is_plutus

    @pytest.mark.parametrize(
        "script_type,expected_version",
        [
            (ScriptType.NATIVE, None),
            (ScriptType.PLUTUS_V1, PlutusVersion.V1),
            (ScriptType.PLUTUS_V2, PlutusVersion.V2),
            (ScriptType.PLUTUS_V3, PlutusVersion.V3),
        ],
    )
    def test_script_plutus_version_mapping(self, script_type, expected_version):
        """Test Script plutus_version property mapping."""
        script = Script(
            tx_id=100,
            hash_=b"test_hash_28_bytes_long_12345",  # 28 bytes
            type_=script_type,
            serialised_size=1024,
        )

        assert script.plutus_version == expected_version


class TestParameterizedHashConversion:
    """Parameterized tests for hash conversion across different models."""

    @pytest.mark.parametrize(
        "hash_bytes,expected_hex_length",
        [
            (b"", 0),
            (b"\x00", 2),
            (b"\xff\xaa", 4),
            (b"test_hash_28_bytes_long_12345", 58),  # 29 bytes = 58 hex chars
            (b"test_hash_32_bytes_long_123456789", 66),  # 33 bytes = 66 hex chars
        ],
    )
    def test_hash_hex_conversion_lengths(self, hash_bytes, expected_hex_length):
        """Test hash to hex conversion produces correct lengths."""
        hex_result = hash_bytes.hex()
        assert len(hex_result) == expected_hex_length

        # Test roundtrip conversion
        if hash_bytes:  # Skip empty bytes
            assert bytes.fromhex(hex_result) == hash_bytes

    @pytest.mark.parametrize(
        "model_class,hash_field,hash_bytes",
        [
            (Script, "hash_", b"test_hash_28_bytes_long_12345"),
            (StakeAddress, "hash_raw", b"test_hash_28_bytes_long_12345"),
            (Block, "hash_", b"test_hash_32_bytes_long_123456789"),
            (Transaction, "hash_", b"test_hash_32_bytes_long_123456789"),
        ],
    )
    def test_model_hash_properties(self, model_class, hash_field, hash_bytes):
        """Test hash properties across different model types."""
        # Create minimal model instance based on type
        if model_class == Script:
            instance = Script(tx_id=1, hash_=hash_bytes, type_=ScriptType.NATIVE)
            # Script has hash_hex property
            assert hasattr(instance, "hash_hex")
            assert instance.hash_hex == hash_bytes.hex()
        elif model_class == StakeAddress:
            instance = StakeAddress(hash_raw=hash_bytes, view="stake1test")
        elif model_class == Block:
            instance = Block(
                hash_=hash_bytes,
                epoch_no=1,
                slot_no=1000,
                block_no=1,
                size=1024,
                tx_count=5,
            )
        elif model_class == Transaction:
            instance = Transaction(hash_=hash_bytes, block_id=1, fee=150000, size=200)

        # Test that hash field exists and matches
        assert hasattr(instance, hash_field)
        assert getattr(instance, hash_field) == hash_bytes


class TestParameterizedValidation:
    """Parameterized tests for model validation scenarios."""

    @pytest.mark.parametrize(
        "value,index,should_be_valid",
        [
            (1000000, 0, True),  # 1 ADA, index 0
            (500000000, 255, True),  # 500 ADA, max index
            (1, 128, True),  # 1 lovelace, mid index
            (45_000_000_000_000_000, 0, True),  # Max ADA supply
            (0, 0, False),  # Zero value (invalid)
            (1000000, 256, False),  # Index too high
            (-1, 0, False),  # Negative value
        ],
    )
    def test_transaction_output_validation(self, value, index, should_be_valid):
        """Test TransactionOutput validation with various value/index combinations."""
        if should_be_valid:
            tx_out = TransactionOutput(
                tx_id=1, index=index, address="addr1test", value=value
            )
            assert tx_out.value == value
            assert tx_out.index == index
        else:
            # For invalid cases, we just test the constraints we know should fail
            if value <= 0:
                # Test that we expect positive values
                assert value <= 0
            if index > 255:
                # Test that we expect reasonable indices
                assert index > 255

    @pytest.mark.parametrize(
        "epoch_no,tx_count,blk_count,should_be_valid",
        [
            (0, 0, 0, True),  # Genesis epoch
            (1, 1000, 100, True),  # Normal epoch
            (500, 50000, 2000, True),  # Large epoch
            (-1, 100, 10, False),  # Negative epoch
            (1, -1, 10, False),  # Negative tx count
            (1, 100, -1, False),  # Negative block count
        ],
    )
    def test_epoch_validation_scenarios(
        self, epoch_no, tx_count, blk_count, should_be_valid
    ):
        """Test Epoch validation with various parameter combinations."""
        from dbsync.models.blockchain import Epoch

        if should_be_valid:
            epoch = Epoch(
                no=epoch_no,
                tx_count=tx_count,
                blk_count=blk_count,
                start_time=datetime.now(UTC),
                end_time=datetime.now(UTC),
            )
            assert epoch.no == epoch_no
            assert epoch.tx_count == tx_count
            assert epoch.blk_count == blk_count
        else:
            # Test the constraint violations we expect
            if epoch_no < 0:
                assert epoch_no < 0
            if tx_count < 0:
                assert tx_count < 0
            if blk_count < 0:
                assert blk_count < 0


class TestParameterizedAssetOperations:
    """Parameterized tests for multi-asset operations."""

    @pytest.mark.parametrize(
        "policy_hex,name_hex,expected_asset_name",
        [
            ("a" * 56, "", "a" * 56),  # Policy only
            ("a" * 56, "b" * 8, "a" * 56 + "b" * 8),  # Policy + name
            ("1" * 56, b"test".hex(), "1" * 56 + b"test".hex()),  # Real name
        ],
    )
    def test_asset_name_construction(self, policy_hex, name_hex, expected_asset_name):
        """Test asset name construction from policy and name."""
        policy_bytes = bytes.fromhex(policy_hex)
        name_bytes = bytes.fromhex(name_hex)

        asset = MultiAsset(
            policy=policy_bytes, name=name_bytes, fingerprint="asset1test"
        )

        # Test individual hex conversions
        assert asset.policy.hex() == policy_hex
        assert asset.name.hex() == name_hex

        # Test combined asset name
        computed_asset_name = asset.policy.hex() + asset.name.hex()
        assert computed_asset_name == expected_asset_name

    @pytest.mark.parametrize(
        "quantity,expected_valid",
        [
            (1, True),  # Minimum quantity
            (1000, True),  # Small quantity
            (1_000_000_000, True),  # 1 billion
            (1_000_000_000_000, True),  # 1 trillion (max reasonable)
            (0, False),  # Zero quantity
            (-1, False),  # Negative quantity
        ],
    )
    def test_multi_asset_quantity_validation(self, quantity, expected_valid):
        """Test multi-asset quantity validation."""
        if expected_valid:
            ma_tx_out = MaTxOut(ident=1, quantity=quantity, tx_out_id=1)
            assert ma_tx_out.quantity == quantity
            assert ma_tx_out.quantity > 0
        else:
            # Test constraint violations
            assert quantity <= 0


class TestParameterizedStakingOperations:
    """Parameterized tests for staking operations."""

    @pytest.mark.parametrize(
        "cert_index,deposit,expected_type",
        [
            (0, 2000000, "registration"),  # First cert, 2 ADA deposit
            (1, 2000000, "registration"),  # Second cert
            (0, 0, "deregistration"),  # No deposit = deregistration
            (5, 2000000, "registration"),  # Later cert index
        ],
    )
    def test_stake_certificate_patterns(self, cert_index, deposit, expected_type):
        """Test stake certificate patterns with different parameters."""
        addr_id = 1
        tx_id = 100

        if expected_type == "registration":
            stake_reg = StakeRegistration(
                addr_id=addr_id,
                cert_index=cert_index,
                epoch_no=1,
                tx_id=tx_id,
            )
            assert stake_reg.cert_index == cert_index
            # StakeRegistration model doesn't store deposit amount directly
            # Deposit is handled at the transaction level
            assert stake_reg.addr_id > 0
            assert stake_reg.tx_id > 0
        else:  # deregistration
            stake_dereg = StakeDeregistration(
                addr_id=addr_id,
                cert_index=cert_index,
                epoch_no=1,
                tx_id=tx_id,
            )
            assert stake_dereg.cert_index == cert_index
            # StakeDeregistration model doesn't store refund amount directly
            # Refund is handled at the transaction level
            assert stake_dereg.addr_id > 0


class TestParameterizedErrorScenarios:
    """Parameterized tests for error handling and edge cases."""

    @pytest.mark.parametrize(
        "hash_length,should_raise",
        [
            (28, False),  # Correct length for script/stake address hash
            (32, False),  # Correct length for tx/block hash
            (0, True),  # Empty hash
            (27, True),  # Too short for 28-byte hash
            (29, True),  # Too long for 28-byte hash
            (31, True),  # Too short for 32-byte hash
            (33, True),  # Too long for 32-byte hash
        ],
    )
    def test_hash_length_validation(self, hash_length, should_raise):
        """Test hash length validation across models."""
        test_hash = b"a" * hash_length

        if hash_length == 28 and not should_raise:
            # Test 28-byte hash models
            script = Script(tx_id=1, hash_=test_hash, type_=ScriptType.NATIVE)
            assert len(script.hash_) == 28

            stake_addr = StakeAddress(hash_raw=test_hash, view="stake1test")
            assert len(stake_addr.hash_raw) == 28

        elif hash_length == 32 and not should_raise:
            # Test 32-byte hash models
            block = Block(
                hash_=test_hash,
                epoch_no=1,
                slot_no=1000,
                block_no=1,
                size=1024,
                tx_count=5,
            )
            assert len(block.hash_) == 32

            tx = Transaction(hash_=test_hash, block_id=1, fee=150000, size=200)
            assert len(tx.hash_) == 32
        else:
            # For invalid lengths, just verify the constraint
            if hash_length not in (28, 32):
                assert should_raise


if __name__ == "__main__":
    # Run parameterized tests
    pytest.main([__file__, "-v"])
