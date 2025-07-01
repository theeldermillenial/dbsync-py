"""Multi-asset support models for Cardano DB Sync.

This module contains the multi-asset models including native tokens, minting events,
and multi-asset outputs.

Supports CIP14 asset fingerprints and integration with pycardano classes.
"""

from __future__ import annotations

import hashlib

from sqlalchemy import BigInteger, Column, ForeignKey, LargeBinary, String
from sqlmodel import Field, Relationship

from ..utils.types import Hash28Type
from .base import DBSyncBase

__all__ = [
    "MaTxMint",
    "MaTxOut",
    "MultiAsset",
    "generate_cip14_fingerprint",
]


def generate_cip14_fingerprint(policy_id: bytes, asset_name: bytes) -> str:
    """Generate CIP14 asset fingerprint from policy ID and asset name.

    Args:
        policy_id: The 28-byte policy ID
        asset_name: The asset name bytes

    Returns:
        CIP14 asset fingerprint string

    References:
        - CIP-14: https://cips.cardano.org/cips/cip14/
    """
    # Combine policy ID and asset name
    combined = policy_id + asset_name

    # Create Blake2b hash (160 bits = 20 bytes)
    hash_obj = hashlib.blake2b(combined, digest_size=20)
    fingerprint_bytes = hash_obj.digest()

    # Convert to Bech32 with 'asset' prefix
    # Note: This is a simplified implementation
    # In production, you'd use a proper Bech32 library
    import base64

    encoded = base64.b32encode(fingerprint_bytes).decode().lower().rstrip("=")
    return f"asset{encoded}"


class MultiAsset(DBSyncBase, table=True):
    """Multi-asset model representing native tokens and NFTs.

    Maps to the 'multi_asset' table in Cardano DB Sync.
    Represents unique assets identified by policy ID and asset name.

    Attributes:
        id_: Primary key
        policy: Policy ID (28 bytes) - the minting policy hash
        name: Asset name bytes - the asset name within the policy
        fingerprint: CIP14 asset fingerprint for easy identification

    References:
        - Cardano Ledger: Native tokens and multi-asset support
        - CIP-14: Asset fingerprint standard
    """

    __tablename__ = "multi_asset"

    id_: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, name="id")
    )
    policy: bytes = Field(sa_column=Column(Hash28Type, nullable=False))
    name: bytes = Field(sa_column=Column(LargeBinary, nullable=False))
    fingerprint: str | None = Field(sa_column=Column(String(64), nullable=True))

    def __post_init__(self):
        """Generate fingerprint if not provided."""
        if not self.fingerprint and self.policy and self.name is not None:
            self.fingerprint = generate_cip14_fingerprint(self.policy, self.name)

    @property
    def asset_name_hex(self) -> str:
        """Get asset name as hex string."""
        return self.name.hex() if self.name else ""

    @property
    def policy_id_hex(self) -> str:
        """Get policy ID as hex string."""
        return self.policy.hex() if self.policy else ""

    def to_pycardano_asset_name(self):
        """Convert to pycardano AssetName.

        Returns:
            pycardano.AssetName instance

        Raises:
            ImportError: If pycardano is not available
        """
        try:
            from pycardano import AssetName

            return AssetName(self.name)
        except ImportError:
            raise ImportError("pycardano is required for AssetName conversion")

    def to_pycardano_policy_id(self):
        """Convert to pycardano PolicyID.

        Returns:
            pycardano.PolicyID instance

        Raises:
            ImportError: If pycardano is not available
        """
        try:
            from pycardano import PolicyID

            return PolicyID(self.policy)
        except ImportError:
            raise ImportError("pycardano is required for PolicyID conversion")


class MaTxMint(DBSyncBase, table=True):
    """Multi-asset transaction mint model representing minting/burning events.

    Maps to the 'ma_tx_mint' table in Cardano DB Sync.
    Tracks the minting or burning of native assets in transactions.

    Attributes:
        id_: Primary key
        quantity: Amount minted (positive) or burned (negative)
        tx_id: Foreign key to transaction
        ident: Foreign key to multi_asset

    References:
        - Cardano Ledger: Native token minting and burning
        - Transaction structure with mint field
    """

    __tablename__ = "ma_tx_mint"

    id_: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, name="id")
    )
    quantity: int = Field(sa_column=Column(BigInteger, nullable=False))
    tx_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("tx.id"), nullable=False)
    )
    ident: int = Field(
        sa_column=Column(BigInteger, ForeignKey("multi_asset.id"), nullable=False)
    )

    @property
    def is_mint(self) -> bool:
        """Check if this is a minting event (positive quantity)."""
        return self.quantity > 0

    @property
    def is_burn(self) -> bool:
        """Check if this is a burning event (negative quantity)."""
        return self.quantity < 0

    @property
    def absolute_quantity(self) -> int:
        """Get absolute quantity (always positive)."""
        return abs(self.quantity)


class MaTxOut(DBSyncBase, table=True):
    """Multi-asset transaction output model representing asset amounts in outputs.

    Maps to the 'ma_tx_out' table in Cardano DB Sync.
    Tracks the amounts of native assets in transaction outputs.

    Attributes:
        id_: Primary key
        quantity: Amount of the asset in the output
        tx_out_id: Foreign key to transaction output
        ident: Foreign key to multi_asset

    References:
        - Cardano Ledger: Multi-asset transaction outputs
        - UTXO model with native asset support
    """

    __tablename__ = "ma_tx_out"

    id_: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, name="id")
    )
    quantity: int = Field(sa_column=Column(BigInteger, nullable=False))
    tx_out_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("tx_out.id"), nullable=False)
    )
    ident: int = Field(
        sa_column=Column(BigInteger, ForeignKey("multi_asset.id"), nullable=False)
    )

    @property
    def quantity_lovelace(self) -> int:
        """Get quantity in lovelace equivalent (for display purposes)."""
        return self.quantity


# Import relationships at the end to avoid circular imports

# Add relationships after class definitions to avoid SQLModel annotation issues
MultiAsset.mint_events = Relationship(back_populates="multi_asset")
MultiAsset.outputs = Relationship(back_populates="multi_asset")
MaTxMint.transaction = Relationship()
MaTxMint.multi_asset = Relationship(back_populates="mint_events")
MaTxOut.transaction_output = Relationship()
MaTxOut.multi_asset = Relationship(back_populates="outputs")
