"""Tests for custom database types.

This tests the custom SQLAlchemy types used for PostgreSQL without requiring database creation.
"""

from decimal import Decimal

import pytest

from dbsync.utils.types import (
    Asset32Type,
    Hash28Type,
    Hash32Type,
    Int65Type,
    LovelaceType,
    TxIndexType,
    Word31Type,
    Word63Type,
    Word64Type,
    to_pycardano_address,
    to_pycardano_asset_name,
    to_pycardano_policy_id,
    to_pycardano_transaction_id,
)


class TestHash28Type:
    """Test Hash28Type custom type."""

    def test_process_bind_param_bytes(self):
        """Test processing bytes input."""
        type_instance = Hash28Type()
        test_bytes = bytes([0x12] * 28)
        result = type_instance.process_bind_param(test_bytes, None)
        assert result == test_bytes

    def test_process_bind_param_hex_string(self):
        """Test processing hex string input."""
        type_instance = Hash28Type()
        test_hex = "12" * 28
        result = type_instance.process_bind_param(test_hex, None)
        assert result == bytes.fromhex(test_hex)

    def test_process_bind_param_none(self):
        """Test processing None input."""
        type_instance = Hash28Type()
        result = type_instance.process_bind_param(None, None)
        assert result is None

    def test_process_bind_param_invalid_length(self):
        """Test processing invalid length input."""
        type_instance = Hash28Type()
        with pytest.raises(ValueError, match="Hash28 must be exactly .* bytes"):
            type_instance.process_bind_param(bytes([0x12] * 27), None)

    def test_process_result_value_bytes(self):
        """Test processing bytes result."""
        type_instance = Hash28Type()
        test_bytes = bytes([0x12] * 28)
        result = type_instance.process_result_value(test_bytes, None)
        assert result == test_bytes

    def test_process_result_value_none(self):
        """Test processing None result."""
        type_instance = Hash28Type()
        result = type_instance.process_result_value(None, None)
        assert result is None


class TestHash32Type:
    """Test Hash32Type custom type."""

    def test_process_bind_param_bytes(self):
        """Test processing bytes input."""
        type_instance = Hash32Type()
        test_bytes = bytes([0x12] * 32)
        result = type_instance.process_bind_param(test_bytes, None)
        assert result == test_bytes

    def test_process_bind_param_hex_string(self):
        """Test processing hex string input."""
        type_instance = Hash32Type()
        test_hex = "12" * 32
        result = type_instance.process_bind_param(test_hex, None)
        assert result == bytes.fromhex(test_hex)

    def test_process_bind_param_invalid_length(self):
        """Test processing invalid length input."""
        type_instance = Hash32Type()
        with pytest.raises(ValueError, match="Hash32 must be exactly 32 bytes"):
            type_instance.process_bind_param(bytes([0x12] * 31), None)


class TestLovelaceType:
    """Test LovelaceType custom type."""

    def test_process_bind_param_int(self):
        """Test processing integer input."""
        type_instance = LovelaceType()
        result = type_instance.process_bind_param(1000000, None)
        assert result == 1000000

    def test_process_bind_param_decimal(self):
        """Test processing Decimal input."""
        type_instance = LovelaceType()
        test_decimal = Decimal("1000000")
        result = type_instance.process_bind_param(test_decimal, None)
        assert result == 1000000

    def test_process_bind_param_negative(self):
        """Test processing negative input."""
        type_instance = LovelaceType()
        with pytest.raises(ValueError, match="Lovelace amount cannot be negative"):
            type_instance.process_bind_param(-1, None)

    def test_process_result_value_int(self):
        """Test processing integer result."""
        type_instance = LovelaceType()
        result = type_instance.process_result_value(1000000, None)
        assert result == 1000000
        assert isinstance(result, int)


class TestWordTypes:
    """Test Word31Type, Word63Type, and Word64Type."""

    def test_word31_valid_range(self):
        """Test Word31Type with valid values."""
        type_instance = Word31Type()

        # Test minimum value
        result = type_instance.process_bind_param(0, None)
        assert result == 0

        # Test maximum value
        max_val = (2**31) - 1
        result = type_instance.process_bind_param(max_val, None)
        assert result == max_val

    def test_word31_invalid_range(self):
        """Test Word31Type with invalid values."""
        type_instance = Word31Type()

        # Test negative value
        with pytest.raises(ValueError, match="Word31 value must be in range"):
            type_instance.process_bind_param(-1, None)

        # Test value too large
        with pytest.raises(ValueError, match="Word31 value must be in range"):
            type_instance.process_bind_param(2**31, None)

    def test_word63_valid_range(self):
        """Test Word63Type with valid values."""
        type_instance = Word63Type()

        # Test minimum value
        result = type_instance.process_bind_param(0, None)
        assert result == 0

        # Test maximum value
        max_val = (2**63) - 1
        result = type_instance.process_bind_param(max_val, None)
        assert result == max_val

    def test_word64_valid_range(self):
        """Test Word64Type with valid values."""
        type_instance = Word64Type()

        # Test minimum value
        result = type_instance.process_bind_param(0, None)
        assert result == 0

        # Test maximum value
        max_val = (2**64) - 1
        result = type_instance.process_bind_param(max_val, None)
        assert result == max_val


class TestInt65Type:
    """Test Int65Type custom type."""

    def test_valid_range(self):
        """Test Int65Type with valid values."""
        type_instance = Int65Type()

        # Test minimum value
        min_val = -(2**64)
        result = type_instance.process_bind_param(min_val, None)
        assert result == str(min_val)  # Int65Type returns strings

        # Test maximum value
        max_val = (2**64) - 1
        result = type_instance.process_bind_param(max_val, None)
        assert result == str(max_val)  # Int65Type returns strings

    def test_invalid_range(self):
        """Test Int65Type with invalid values."""
        type_instance = Int65Type()

        # Test value too small
        with pytest.raises(ValueError, match="Int65 value must be in range"):
            type_instance.process_bind_param(-(2**64) - 1, None)

        # Test value too large
        with pytest.raises(ValueError, match="Int65 value must be in range"):
            type_instance.process_bind_param(2**64, None)


class TestAsset32Type:
    """Test Asset32Type custom type."""

    def test_process_bind_param_bytes(self):
        """Test processing bytes input."""
        type_instance = Asset32Type()
        test_bytes = bytes([0x12] * 32)
        result = type_instance.process_bind_param(test_bytes, None)
        assert result == test_bytes

    def test_process_bind_param_hex_string(self):
        """Test processing hex string input."""
        type_instance = Asset32Type()
        test_hex = "12" * 32
        result = type_instance.process_bind_param(test_hex, None)
        assert result == bytes.fromhex(test_hex)

    def test_process_bind_param_invalid_length(self):
        """Test processing invalid length input."""
        type_instance = Asset32Type()
        with pytest.raises(ValueError, match="Asset32 must be exactly 32 bytes"):
            type_instance.process_bind_param(bytes([0x12] * 31), None)


class TestTxIndexType:
    """Test TxIndexType custom type."""

    def test_valid_range(self):
        """Test TxIndexType with valid values."""
        type_instance = TxIndexType()

        # Test minimum value
        result = type_instance.process_bind_param(0, None)
        assert result == 0

        # Test maximum value
        max_val = (2**16) - 1
        result = type_instance.process_bind_param(max_val, None)
        assert result == max_val

    def test_invalid_range(self):
        """Test TxIndexType with invalid values."""
        type_instance = TxIndexType()

        # Test negative value
        with pytest.raises(ValueError, match="TxIndex value must be in range"):
            type_instance.process_bind_param(-1, None)

        # Test value too large
        with pytest.raises(ValueError, match="TxIndex value must be in range"):
            type_instance.process_bind_param(2**16, None)


class TestPyCardanoConversions:
    """Test PyCardano conversion helper functions."""

    @pytest.mark.skip("Address conversion requires complex setup")
    def test_to_pycardano_address_valid(self):
        """Test converting valid address bytes to PyCardano Address."""
        # This would require setting up a proper address bytes sequence
        # Skip for now as it requires complex setup
        pass

    def test_to_pycardano_address_none(self):
        """Test converting None address to PyCardano Address."""
        result = to_pycardano_address(None)
        assert result is None

    def test_to_pycardano_transaction_id_valid(self):
        """Test converting valid transaction hash to PyCardano TransactionId."""
        # Test with 32-byte hash
        test_hash = bytes([0x12] * 32)
        result = to_pycardano_transaction_id(test_hash)

        # Should return a PyCardano TransactionId object
        from pycardano import TransactionId

        assert isinstance(result, TransactionId)
        assert str(result) == test_hash.hex()

    def test_to_pycardano_transaction_id_hex(self):
        """Test converting hex string transaction hash to PyCardano TransactionId."""
        test_hex = "12" * 32
        result = to_pycardano_transaction_id(test_hex)

        # Should convert hex to PyCardano TransactionId
        from pycardano import TransactionId

        assert isinstance(result, TransactionId)
        assert str(result) == test_hex

    def test_to_pycardano_transaction_id_bytes(self):
        """Test converting bytes transaction hash to PyCardano TransactionId."""
        test_bytes = bytes([0xAB] * 32)
        result = to_pycardano_transaction_id(test_bytes)

        # Should return PyCardano TransactionId
        from pycardano import TransactionId

        assert isinstance(result, TransactionId)
        assert str(result) == test_bytes.hex()

    def test_to_pycardano_transaction_id_none(self):
        """Test converting None transaction hash to PyCardano TransactionId."""
        result = to_pycardano_transaction_id(None)
        assert result is None

    def test_to_pycardano_asset_name_valid(self):
        """Test converting valid asset name to PyCardano AssetName."""
        test_name = b"TestAsset"
        result = to_pycardano_asset_name(test_name)

        # Should return a PyCardano AssetName object
        from pycardano import AssetName

        assert isinstance(result, AssetName)
        assert bytes(result) == test_name

    def test_to_pycardano_asset_name_none(self):
        """Test converting None asset name to PyCardano AssetName."""
        result = to_pycardano_asset_name(None)
        assert result is None

    def test_to_pycardano_policy_id_valid(self):
        """Test converting valid policy ID to PyCardano ScriptHash."""
        test_policy = bytes([0x34] * 28)
        result = to_pycardano_policy_id(test_policy)

        # Should return a PyCardano PolicyId object
        from pycardano import PolicyId

        assert isinstance(result, PolicyId)
        assert str(result) == test_policy.hex()

    def test_to_pycardano_policy_id_none(self):
        """Test converting None policy ID to PyCardano ScriptHash."""
        result = to_pycardano_policy_id(None)
        assert result is None
