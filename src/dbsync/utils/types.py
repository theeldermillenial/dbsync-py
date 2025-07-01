"""PostgreSQL type mapping utilities for Cardano DB Sync.

This module provides custom type handlers and conversion utilities for PostgreSQL
custom types used in Cardano DB Sync database schema.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, TypeVar

from pycardano import Address, AssetName, PolicyId, TransactionId
from pycardano.hash import TRANSACTION_HASH_SIZE
from sqlalchemy import BigInteger, Integer, String, TypeDecorator
from sqlalchemy.dialects.postgresql import BYTEA

__all__ = [
    "AddressType",
    "Asset32Type",
    "Hash28Type",
    "Hash32Type",
    "Int65Type",
    "LovelaceType",
    "TxIndexType",
    "Word31Type",
    "Word63Type",
    "Word64Type",
    "convert_from_pycardano",
    "convert_to_pycardano",
    "to_pycardano_address",
    "to_pycardano_asset_name",
    "to_pycardano_policy_id",
    "to_pycardano_transaction_id",
]

T = TypeVar("T")

# Define missing constants
SCRIPT_HASH_SIZE = 28  # Script hashes are 28 bytes in Cardano


class Hash28Type(TypeDecorator):
    """28-byte hash type for Cardano script data hashes."""

    impl = BYTEA
    cache_ok = True

    def process_bind_param(self, value: bytes | str | None, dialect) -> bytes | None:
        """Convert input to 28-byte hash."""
        if value is None:
            return None
        if isinstance(value, str):
            # Handle hex string input
            if value.startswith("\\x"):
                value = value[2:]
            try:
                value = bytes.fromhex(value)
            except ValueError as e:
                raise ValueError(f"Invalid hex string for hash28: {value}") from e
        if isinstance(value, bytes):
            if len(value) != SCRIPT_HASH_SIZE:
                raise ValueError(
                    f"Hash28 must be exactly {SCRIPT_HASH_SIZE} bytes, got {len(value)}"
                )
            return value
        raise TypeError(f"Hash28 value must be bytes or hex string, got {type(value)}")

    def process_result_value(self, value: bytes | None, dialect) -> bytes | None:
        """Return raw bytes for hash28."""
        return value


class Hash32Type(TypeDecorator):
    """32-byte hash type for Cardano transaction hashes and other 32-byte hashes."""

    impl = BYTEA
    cache_ok = True

    def process_bind_param(
        self, value: bytes | str | TransactionId | None, dialect
    ) -> bytes | None:
        """Convert input to 32-byte hash."""
        if value is None:
            return None
        if isinstance(value, TransactionId):
            return value.payload
        if isinstance(value, str):
            # Handle hex string input
            if value.startswith("\\x"):
                value = value[2:]
            try:
                value = bytes.fromhex(value)
            except ValueError as e:
                raise ValueError(f"Invalid hex string for hash32: {value}") from e
        if isinstance(value, bytes):
            if len(value) != TRANSACTION_HASH_SIZE:
                raise ValueError(
                    f"Hash32 must be exactly {TRANSACTION_HASH_SIZE} bytes, got {len(value)}"
                )
            return value
        raise TypeError(
            f"Hash32 value must be bytes, hex string, or TransactionId, got {type(value)}"
        )

    def process_result_value(self, value: bytes | None, dialect) -> bytes | None:
        """Return raw bytes for hash32."""
        return value


class LovelaceType(TypeDecorator):
    """Lovelace amount type with proper handling of ADA amounts."""

    impl = BigInteger
    cache_ok = True

    def process_bind_param(
        self, value: int | Decimal | str | None, dialect
    ) -> int | None:
        """Convert input to lovelace integer."""
        if value is None:
            return None
        if isinstance(value, str):
            try:
                value = Decimal(value)
            except ValueError as e:
                raise ValueError(f"Invalid string for lovelace: {value}") from e
        if isinstance(value, Decimal):
            # Convert to integer
            if value < 0:
                raise ValueError("Lovelace amount cannot be negative")
            return int(value)
        if isinstance(value, int):
            if value < 0:
                raise ValueError("Lovelace amount cannot be negative")
            return value
        raise TypeError(
            f"Lovelace value must be int, Decimal, or string, got {type(value)}"
        )

    def process_result_value(self, value: int | None, dialect) -> int | None:
        """Return lovelace as integer."""
        return value


class Word31Type(TypeDecorator):
    """31-bit unsigned integer type."""

    impl = Integer
    cache_ok = True

    def process_bind_param(self, value: int | None, dialect) -> int | None:
        """Validate and convert 31-bit unsigned integer."""
        if value is None:
            return None
        if not isinstance(value, int):
            raise TypeError(f"Word31 value must be int, got {type(value)}")
        if value < 0 or value >= 2**31:
            raise ValueError(f"Word31 value must be in range [0, 2^31), got {value}")
        return value

    def process_result_value(self, value: int | None, dialect) -> int | None:
        """Return word31 as integer."""
        return value


class Word63Type(TypeDecorator):
    """63-bit unsigned integer type."""

    impl = BigInteger
    cache_ok = True

    def process_bind_param(self, value: int | None, dialect) -> int | None:
        """Validate and convert 63-bit unsigned integer."""
        if value is None:
            return None
        if not isinstance(value, int):
            raise TypeError(f"Word63 value must be int, got {type(value)}")
        if value < 0 or value >= 2**63:
            raise ValueError(f"Word63 value must be in range [0, 2^63), got {value}")
        return value

    def process_result_value(self, value: int | None, dialect) -> int | None:
        """Return word63 as integer."""
        return value


class Word64Type(TypeDecorator):
    """64-bit unsigned integer type."""

    impl = BigInteger
    cache_ok = True

    def process_bind_param(self, value: int | None, dialect) -> int | None:
        """Validate and convert 64-bit unsigned integer."""
        if value is None:
            return None
        if not isinstance(value, int):
            raise TypeError(f"Word64 value must be int, got {type(value)}")
        if value < 0 or value >= 2**64:
            raise ValueError(f"Word64 value must be in range [0, 2^64), got {value}")
        return value

    def process_result_value(self, value: int | None, dialect) -> int | None:
        """Return word64 as integer."""
        return value


class Int65Type(TypeDecorator):
    """65-bit signed integer type (stored as string in PostgreSQL)."""

    impl = String
    cache_ok = True

    def process_bind_param(self, value: int | None, dialect) -> str | None:
        """Convert 65-bit signed integer to string."""
        if value is None:
            return None
        if not isinstance(value, int):
            raise TypeError(f"Int65 value must be int, got {type(value)}")
        if value < -(2**64) or value >= 2**64:
            raise ValueError(
                f"Int65 value must be in range [-(2^64), 2^64), got {value}"
            )
        return str(value)

    def process_result_value(self, value: str | None, dialect) -> int | None:
        """Convert string back to 65-bit signed integer."""
        if value is None:
            return None
        try:
            return int(value)
        except ValueError as e:
            raise ValueError(f"Invalid int65 string: {value}") from e


class Asset32Type(TypeDecorator):
    """32-byte asset identifier type."""

    impl = BYTEA
    cache_ok = True

    def process_bind_param(
        self, value: bytes | str | PolicyId | AssetName | None, dialect
    ) -> bytes | None:
        """Convert input to 32-byte asset identifier."""
        if value is None:
            return None
        if isinstance(value, (PolicyId, AssetName)):
            return value.payload
        if isinstance(value, str):
            # Handle hex string input
            if value.startswith("\\x"):
                value = value[2:]
            try:
                value = bytes.fromhex(value)
            except ValueError as e:
                raise ValueError(f"Invalid hex string for asset32: {value}") from e
        if isinstance(value, bytes):
            if len(value) != 32:
                raise ValueError(f"Asset32 must be exactly 32 bytes, got {len(value)}")
            return value
        raise TypeError(
            f"Asset32 value must be bytes, hex string, PolicyId, or AssetName, got {type(value)}"
        )

    def process_result_value(self, value: bytes | None, dialect) -> bytes | None:
        """Return raw bytes for asset32."""
        return value


class TxIndexType(TypeDecorator):
    """Transaction index type (16-bit unsigned integer)."""

    impl = Integer
    cache_ok = True

    def process_bind_param(self, value: int | None, dialect) -> int | None:
        """Validate and convert transaction index."""
        if value is None:
            return None
        if not isinstance(value, int):
            raise TypeError(f"TxIndex value must be int, got {type(value)}")
        if value < 0 or value >= 2**16:
            raise ValueError(f"TxIndex value must be in range [0, 2^16), got {value}")
        return value

    def process_result_value(self, value: int | None, dialect) -> int | None:
        """Return txindex as integer."""
        return value


class AddressType(TypeDecorator):
    """Cardano address type with pycardano integration."""

    impl = String
    cache_ok = True

    def process_bind_param(self, value: str | Address | None, dialect) -> str | None:
        """Convert address to string representation."""
        if value is None:
            return None
        if isinstance(value, Address):
            return str(value)
        if isinstance(value, str):
            # Validate address format
            try:
                Address.from_bech32(value)
                return value
            except Exception:
                try:
                    Address.from_primitive(bytes.fromhex(value))
                    return value
                except Exception as e:
                    raise ValueError(f"Invalid address format: {value}") from e
        raise TypeError(f"Address value must be string or Address, got {type(value)}")

    def process_result_value(self, value: str | None, dialect) -> str | None:
        """Return address as string."""
        return value


def convert_to_pycardano(value: Any, target_type: type[T]) -> T | None:
    """Convert database value to pycardano type.

    Args:
        value: Database value to convert
        target_type: Target pycardano type

    Returns:
        Converted pycardano object or None

    Raises:
        ValueError: If conversion fails
        TypeError: If target type is not supported
    """
    if value is None:
        return None

    try:
        if target_type == TransactionId:
            if isinstance(value, bytes) and len(value) == 32:
                return TransactionId(value)
            elif isinstance(value, str):
                # Convert hex string to bytes then create TransactionId
                return TransactionId(bytes.fromhex(value))
        elif target_type == Address:
            if isinstance(value, bytes):
                # Handle raw bytes
                return Address.from_primitive(value)
            elif isinstance(value, str):
                try:
                    # Use decode instead of from_bech32
                    return Address.decode(value)
                except Exception:
                    # Try as hex string
                    return Address.from_primitive(bytes.fromhex(value))
        elif target_type == PolicyId:
            if isinstance(value, bytes) and len(value) == 28:
                return PolicyId(value)
            elif isinstance(value, str):
                # Convert hex string to bytes then create PolicyId
                return PolicyId(bytes.fromhex(value))
        elif target_type == AssetName:
            if isinstance(value, bytes):
                return AssetName(value)
            elif isinstance(value, str):
                return AssetName(value.encode("utf-8"))
        else:
            raise TypeError(f"Unsupported target type: {target_type}")
    except Exception as e:
        raise ValueError(f"Failed to convert {value} to {target_type}: {e}") from e

    return None


def convert_from_pycardano(value: Any) -> Any:
    """Convert pycardano object to database-compatible value.

    Args:
        value: Pycardano object to convert

    Returns:
        Database-compatible value

    Raises:
        TypeError: If value type is not supported
    """
    if value is None:
        return None

    if isinstance(value, TransactionId):
        return value.payload
    elif isinstance(value, Address):
        return str(value)
    elif isinstance(value, (PolicyId, AssetName)):
        return value.payload
    elif isinstance(value, (int, str, bytes, Decimal)):
        return value
    else:
        raise TypeError(f"Unsupported pycardano type: {type(value)}")


def to_pycardano_address(value: str | bytes | None) -> Address | None:
    """Convert address string or bytes to pycardano.Address.

    Args:
        value: Address string (bech32 or hex) or bytes

    Returns:
        Address object or None if input is None
    """
    return convert_to_pycardano(value, Address)


def to_pycardano_transaction_id(value: str | bytes | None) -> TransactionId | None:
    """Convert transaction ID string or bytes to pycardano.TransactionId.

    Args:
        value: Transaction ID string (hex) or bytes

    Returns:
        TransactionId object or None if input is None
    """
    return convert_to_pycardano(value, TransactionId)


def to_pycardano_asset_name(value: str | bytes | None) -> AssetName | None:
    """Convert asset name string or bytes to pycardano.AssetName.

    Args:
        value: Asset name string or bytes

    Returns:
        AssetName object or None if input is None
    """
    return convert_to_pycardano(value, AssetName)


def to_pycardano_policy_id(value: str | bytes | None) -> PolicyId | None:
    """Convert policy ID string or bytes to pycardano.PolicyId.

    Args:
        value: Policy ID string (hex) or bytes

    Returns:
        PolicyId object or None if input is None
    """
    return convert_to_pycardano(value, PolicyId)
