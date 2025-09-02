"""Blockchain models for Cardano DB Sync.

This module contains the core blockchain models including blocks, transactions,
epochs, and addresses.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
)
from sqlmodel import Field, Relationship

from ..utils.types import Hash28Type, Hash32Type, LovelaceType
from .base import DBSyncBase

__all__ = [
    "Address",
    "Block",
    "Epoch",
    "EpochSyncTime",
    "ReverseIndex",
    "SchemaVersion",
    "SlotLeader",
    "StakeAddress",
    "Transaction",
]


class Address(DBSyncBase, table=True):
    """Address model for the address table.

    Represents Cardano addresses (payment and stake addresses).
    """

    __tablename__: str = "address"

    id_: int | None = Field(
        default=None,
        sa_column=Column(
            BigInteger, primary_key=True, autoincrement=True, name="id"
        ),
        description="Auto-incrementing primary key",
    )

    address: str = Field(
        sa_column=Column(String, nullable=False),
        description="Human-readable address (bech32 encoded)",
    )

    raw: bytes = Field(
        sa_column=Column(LargeBinary, nullable=False),
        description="Raw address bytes",
    )

    has_script: bool = Field(
        sa_column=Column(Boolean, nullable=False),
        description="Whether this address contains a script",
    )

    payment_cred: bytes | None = Field(
        default=None,
        sa_column=Column(LargeBinary, nullable=True),
        description="Payment credential hash",
    )

    stake_address_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("stake_address.id")),
        description="Associated stake address ID",
    )


class StakeAddress(DBSyncBase, table=True):
    """Stake address model for the stake_address table.

    Represents Cardano stake addresses used for delegation and rewards.
    """

    __tablename__: str = "stake_address"

    id_: int | None = Field(
        default=None,
        sa_column=Column(
            BigInteger, primary_key=True, autoincrement=True, name="id"
        ),
        description="Auto-incrementing primary key",
    )

    hash_raw: bytes = Field(
        sa_column=Column(Hash28Type, unique=True, index=True, name="hash_raw", nullable=False),
        description="Stake address hash (raw bytes)",
    )

    view: str = Field(
        sa_column=Column(String, nullable=False),
        description="Human-readable stake address (bech32 encoded)",
    )

    script_hash: bytes | None = Field(
        default=None,
        sa_column=Column(Hash28Type),
        description="Script hash if this is a script-based stake address",
    )


class SlotLeader(DBSyncBase, table=True):
    """Slot leader model for the slot_leader table.

    Represents entities that can produce blocks (stake pools).
    """

    __tablename__: str = "slot_leader"

    id_: int | None = Field(
        default=None,
        sa_column=Column(
            BigInteger, primary_key=True, autoincrement=True, name="id"
        ),
        description="Auto-incrementing primary key",
    )

    hash_: bytes = Field(
        sa_column=Column(Hash28Type, unique=True, index=True, name="hash", nullable=False),
        description="Slot leader hash (pool ID)",
    )

    pool_hash_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger),
        description="Reference to pool hash",
    )

    description: str = Field(
        sa_column=Column(String, nullable=False),
        description="Description of the slot leader",
    )


class Epoch(DBSyncBase, table=True):
    """Epoch model for the epoch table.

    Represents Cardano epochs with their metrics and timing.
    """

    __tablename__: str = "epoch"

    id_: int | None = Field(
        default=None,
        sa_column=Column(
            BigInteger, primary_key=True, autoincrement=True, name="id"
        ),
        description="Auto-incrementing primary key",
    )

    out_sum: int = Field(
        sa_column=Column(LovelaceType, nullable=False),
        description="Total output in this epoch (lovelace)",
    )

    fees: int = Field(
        sa_column=Column(LovelaceType, nullable=False),
        description="Total fees collected in this epoch (lovelace)",
    )

    tx_count: int = Field(
        sa_column=Column(Integer, nullable=False),
        description="Number of transactions in this epoch",
    )

    blk_count: int = Field(
        sa_column=Column(Integer, nullable=False),
        description="Number of blocks in this epoch",
    )

    no: int = Field(
        sa_column=Column(Integer, unique=True, index=True, nullable=False),
        description="Epoch number",
    )

    start_time: datetime = Field(
        sa_column=Column(DateTime(timezone=False), nullable=False),
        description="Epoch start time",
    )

    end_time: datetime = Field(
        sa_column=Column(DateTime(timezone=False), nullable=False),
        description="Epoch end time",
    )


class Block(DBSyncBase, table=True):
    """Block model for the block table.

    Represents Cardano blocks with their metadata and relationships.
    """

    __tablename__: str = "block"

    id_: int | None = Field(
        default=None,
        sa_column=Column(
            BigInteger, primary_key=True, autoincrement=True, name="id"
        ),
        description="Auto-incrementing primary key",
    )

    hash_: bytes = Field(
        sa_column=Column(Hash32Type, unique=True, index=True, name="hash", nullable=False),
        description="Block hash",
    )

    epoch_no: int | None = Field(
        default=None,
        sa_column=Column(Integer, index=True),
        description="Epoch number this block belongs to",
    )

    slot_no: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, index=True),
        description="Absolute slot number",
    )

    epoch_slot_no: int | None = Field(
        default=None,
        sa_column=Column(Integer),
        description="Slot number within the epoch",
    )

    block_no: int | None = Field(
        default=None,
        sa_column=Column(Integer, unique=True, index=True),
        description="Block number (height)",
    )

    previous_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("block.id"), index=True),
        description="Previous block ID",
    )

    slot_leader_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("slot_leader.id"), index=True, nullable=False),
        description="Slot leader who produced this block",
    )

    size: int = Field(
        sa_column=Column(Integer, nullable=False),
        description="Block size in bytes",
    )

    time: datetime = Field(
        sa_column=Column(DateTime(timezone=False), nullable=False),
        description="Block timestamp",
    )

    tx_count: int = Field(
        sa_column=Column(BigInteger, nullable=False),
        description="Number of transactions in this block",
    )

    proto_major: int = Field(
        sa_column=Column(Integer, nullable=False),
        description="Protocol major version",
    )

    proto_minor: int = Field(
        sa_column=Column(Integer, nullable=False),
        description="Protocol minor version",
    )

    vrf_key: str | None = Field(
        default=None,
        sa_column=Column(Text),
        description="VRF verification key",
    )

    op_cert: bytes | None = Field(
        default=None,
        sa_column=Column(LargeBinary),
        description="Operational certificate",
    )

    op_cert_counter: int | None = Field(
        default=None,
        sa_column=Column(BigInteger),
        description="Operational certificate counter",
    )


class Transaction(DBSyncBase, table=True):
    """Transaction model for the tx table.

    Represents Cardano transactions with their basic metadata.
    """

    __tablename__: str = "tx"

    id_: int | None = Field(
        default=None,
        sa_column=Column(
            BigInteger, primary_key=True, autoincrement=True, name="id"
        ),
        description="Auto-incrementing primary key",
    )

    hash_: bytes = Field(
        sa_column=Column(Hash32Type, unique=True, index=True, name="hash", nullable=False),
        description="Transaction hash",
    )

    block_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("block.id"), index=True, nullable=False),
        description="Block containing this transaction",
    )

    block_index: int = Field(
        sa_column=Column(Integer, nullable=False),
        description="Index of transaction within the block",
    )

    out_sum: int = Field(
        sa_column=Column(LovelaceType, nullable=False),
        description="Total output amount (lovelace)",
    )

    fee: int = Field(
        sa_column=Column(LovelaceType, nullable=False),
        description="Transaction fee (lovelace)",
    )

    deposit: int | None = Field(
        default=None,
        sa_column=Column(BigInteger),
        description="Total deposit amount (lovelace)",
    )

    size: int = Field(
        sa_column=Column(Integer, nullable=False),
        description="Transaction size in bytes",
    )

    invalid_before: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="Invalid before slot",
    )

    invalid_hereafter: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="Invalid after slot",
    )

    valid_contract: bool = Field(
        sa_column=Column(Boolean, nullable=False),
        description="Whether smart contracts in this transaction are valid",
    )

    script_size: int = Field(
        sa_column=Column(Integer, nullable=False),
        description="Total size of scripts in bytes",
    )

    treasury_donation: int = Field(
        default=0,
        sa_column=Column(LovelaceType, nullable=False, default=0),
        description="Treasury donation amount (lovelace)",
    )


class SchemaVersion(DBSyncBase, table=True):
    """Schema version model for the schema_version table.

    Tracks the database schema version for migration purposes.
    """

    __tablename__: str = "schema_version"

    id_: int | None = Field(
        default=None,
        sa_column=Column(
            BigInteger, primary_key=True, autoincrement=True, name="id"
        ),
        description="Auto-incrementing primary key",
    )

    stage_one: int = Field(
        sa_column=Column(BigInteger, nullable=False),
        description="Stage one schema version",
    )

    stage_two: int = Field(
        sa_column=Column(BigInteger, nullable=False),
        description="Stage two schema version",
    )

    stage_three: int = Field(
        sa_column=Column(BigInteger, nullable=False),
        description="Stage three schema version",
    )

    def __str__(self) -> str:
        """Return version as dot-separated string."""
        s1 = self.stage_one or 0
        s2 = self.stage_two or 0
        s3 = self.stage_three or 0
        return f"{s1}.{s2}.{s3}"

    def is_compatible(self, required_version: tuple[int, int, int]) -> bool:
        """Check if this schema version is compatible with a required version.

        Args:
            required_version: Tuple of (major, minor, patch) version numbers

        Returns:
            True if this version is greater than or equal to the required version
        """
        if any(v is None for v in [self.stage_one, self.stage_two, self.stage_three]):
            return False

        current = (self.stage_one or 0, self.stage_two or 0, self.stage_three or 0)
        return current >= required_version


class EpochSyncTime(DBSyncBase, table=True):
    """Epoch sync time model for the epoch_sync_time table.

    Tracks synchronization timing for epochs.
    """

    __tablename__: str = "epoch_sync_time"

    id_: int | None = Field(
        default=None,
        sa_column=Column(
            BigInteger, primary_key=True, autoincrement=True, name="id"
        ),
        description="Auto-incrementing primary key",
    )

    no: int = Field(
        sa_column=Column(BigInteger, unique=True, index=True, nullable=False),
        description="Epoch number",
    )

    seconds: int = Field(
        sa_column=Column(BigInteger, nullable=False),
        description="Synchronization time in seconds",
    )

    state: str = Field(
        sa_column=Column(Enum("lagging", "following", name="syncstatetype"), nullable=False),
        description="Sync state description",
    )


class ReverseIndex(DBSyncBase, table=True):
    """Reverse index model for the reverse_index table.

    Provides reverse indexing capabilities for efficient queries.
    """

    __tablename__: str = "reverse_index"

    id_: int | None = Field(
        default=None,
        sa_column=Column(
            BigInteger, primary_key=True, autoincrement=True, name="id"
        ),
        description="Auto-incrementing primary key",
    )

    block_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("block.id"), index=True, nullable=False),
        description="Block ID for reverse indexing",
    )

    min_ids: str = Field(
        sa_column=Column(String, nullable=False),
        description="Minimum IDs for reverse indexing",
    )


# Add relationships after class definitions to avoid SQLModel annotation issues
Address.stake_address = Relationship(back_populates="addresses")
StakeAddress.addresses = Relationship(back_populates="stake_address")
SlotLeader.blocks = Relationship(back_populates="slot_leader")
Epoch.blocks = Relationship(back_populates="epoch")
Block.slot_leader = Relationship(back_populates="blocks")
Block.epoch = Relationship(back_populates="blocks")
Block.previous_block = Relationship(sa_relationship_kwargs={"remote_side": "Block.id"})
Block.next_blocks = Relationship(
    sa_relationship_kwargs={"remote_side": "Block.previous_id"}
)
Block.transactions = Relationship(back_populates="block")
Transaction.block = Relationship(back_populates="transactions")
ReverseIndex.block = Relationship()
