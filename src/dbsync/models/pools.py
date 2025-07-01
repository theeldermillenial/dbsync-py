"""Stake pool management models for Cardano DB Sync.

This module contains the stake pool management models including pool registration,
retirement, metadata, relays, and performance tracking.
Stake Pool Management Models.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field

from ..utils.types import Hash28Type, Hash32Type, LovelaceType
from .base import DBSyncBase

__all__ = [
    "DelistedPool",
    "OffchainPoolData",
    "OffchainPoolFetchError",
    "PoolHash",
    "PoolMetadataRef",
    "PoolOwner",
    "PoolRelay",
    "PoolRelayType",
    "PoolRetire",
    "PoolStat",
    "PoolUpdate",
    "ReserveUtxo",
    "ReservedPoolTicker",
]


class PoolRelayType(str, Enum):
    """Enum for pool relay types in the Cardano protocol."""

    SINGLE_HOST_ADDR = "single_host_addr"  # Single host with IPv4/IPv6 address
    SINGLE_HOST_NAME = "single_host_name"  # Single host with DNS name
    MULTI_HOST_NAME = "multi_host_name"  # Multiple hosts with DNS name


class PoolHash(DBSyncBase, table=True):
    """Pool hash model for the pool_hash table.

    Represents unique pool identifiers (pool IDs) used throughout the system.
    """

    __tablename__ = "pool_hash"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    hash_raw: bytes | None = Field(
        default=None,
        sa_column=Column(Hash28Type, unique=True, index=True),
        description="Raw pool hash (28 bytes)",
    )

    view: str | None = Field(
        default=None,
        sa_column=Column(String(63)),
        description="Human-readable pool ID (bech32 encoded)",
    )


class PoolUpdate(DBSyncBase, table=True):
    """Pool update model for the pool_update table.

    Represents pool registration and update certificates that define
    pool parameters, metadata, and operational details.
    """

    __tablename__ = "pool_update"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    hash_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("pool_hash.id"), index=True),
        description="Pool hash ID being updated",
    )

    cert_index: int | None = Field(
        default=None,
        sa_column=Column(Integer),
        description="Certificate index within the transaction",
    )

    vrf_key_hash: bytes | None = Field(
        default=None,
        sa_column=Column(Hash32Type),
        description="VRF verification key hash",
    )

    pledge: int | None = Field(
        default=None,
        sa_column=Column(LovelaceType),
        description="Pool pledge amount (lovelace)",
    )

    reward_addr_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("stake_address.id"), index=True),
        description="Reward address for the pool",
    )

    active_epoch_no: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, index=True),
        description="Epoch when the update becomes active",
    )

    meta_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("pool_metadata_ref.id")),
        description="Pool metadata reference",
    )

    margin: float | None = Field(
        default=None,
        description="Pool margin (as a fraction, e.g., 0.05 for 5%)",
    )

    fixed_cost: int | None = Field(
        default=None,
        sa_column=Column(LovelaceType),
        description="Fixed cost per epoch (lovelace)",
    )

    registered_tx_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("tx.id"), index=True),
        description="Transaction containing this registration",
    )


class PoolRetire(DBSyncBase, table=True):
    """Pool retire model for the pool_retire table.

    Represents pool retirement certificates that schedule pools for deregistration.
    """

    __tablename__ = "pool_retire"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    hash_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("pool_hash.id"), index=True),
        description="Pool hash ID being retired",
    )

    cert_index: int | None = Field(
        default=None,
        sa_column=Column(Integer),
        description="Certificate index within the transaction",
    )

    retiring_epoch: int | None = Field(
        default=None,
        sa_column=Column(Integer, index=True),
        description="Epoch when the pool will be retired",
    )

    announced_tx_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("tx.id"), index=True),
        description="Transaction containing this retirement announcement",
    )


class PoolOwner(DBSyncBase, table=True):
    """Pool owner model for the pool_owner table.

    Represents the ownership relationship between stake addresses and pools.
    """

    __tablename__ = "pool_owner"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    addr_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("stake_address.id"), index=True),
        description="Stake address that owns the pool",
    )

    pool_update_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("pool_update.id"), index=True),
        description="Pool update this ownership applies to",
    )


class PoolRelay(DBSyncBase, table=True):
    """Pool relay model for the pool_relay table.

    Represents network relay configuration for stake pools,
    defining how other nodes can connect to the pool.
    """

    __tablename__ = "pool_relay"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    update_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("pool_update.id"), index=True),
        description="Pool update this relay configuration applies to",
    )

    ipv4: str | None = Field(
        default=None,
        sa_column=Column(String(45)),
        description="IPv4 address for single host address relay",
    )

    ipv6: str | None = Field(
        default=None,
        sa_column=Column(String(45)),
        description="IPv6 address for single host address relay",
    )

    dns_name: str | None = Field(
        default=None,
        sa_column=Column(String(255)),
        description="DNS name for single/multi host name relay",
    )

    dns_srv_name: str | None = Field(
        default=None,
        sa_column=Column(String(255)),
        description="DNS SRV record name for multi host name relay",
    )

    port: int | None = Field(
        default=None,
        sa_column=Column(Integer),
        description="Port number for the relay",
    )


class PoolMetadataRef(DBSyncBase, table=True):
    """Pool metadata reference model for the pool_metadata_ref table.

    Represents references to pool metadata URLs and hashes,
    used for fetching and validating pool information.
    """

    __tablename__ = "pool_metadata_ref"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    pool_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("pool_hash.id"), index=True),
        description="Pool this metadata refers to",
    )

    url: str | None = Field(
        default=None,
        sa_column=Column(String(255)),
        description="URL where pool metadata can be fetched",
    )

    hash_: bytes | None = Field(
        default=None,
        sa_column=Column(Hash32Type, name="hash"),
        description="Expected hash of the metadata",
    )

    registered_tx_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("tx.id"), index=True),
        description="Transaction that registered this metadata reference",
    )


class OffchainPoolData(DBSyncBase, table=True):
    """Offchain pool data model for the off_chain_pool_data table.

    Represents cached pool metadata that has been fetched from external URLs.
    """

    __tablename__ = "off_chain_pool_data"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    pool_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("pool_hash.id"), index=True),
        description="Pool this metadata belongs to",
    )

    ticker_name: str | None = Field(
        default=None,
        sa_column=Column(String(5)),
        description="Pool ticker name (up to 5 characters)",
    )

    hash_: bytes | None = Field(
        default=None,
        sa_column=Column(Hash32Type, name="hash"),
        description="Hash of the offchain data",
    )

    json_: dict | None = Field(
        default=None,
        sa_column=Column(JSONB, name="json"),
        description="The payload as JSON",
    )

    bytes_: bytes | None = Field(
        default=None,
        sa_column=Column(LargeBinary, name="bytes"),
        description="Raw bytes of the payload",
    )

    pmr_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("pool_metadata_ref.id"), index=True),
        description="Pool metadata reference used for fetching",
    )


class OffchainPoolFetchError(DBSyncBase, table=True):
    """Offchain pool fetch error model for the off_chain_pool_fetch_error table.

    Represents errors encountered when trying to fetch pool metadata from external URLs.
    """

    __tablename__ = "off_chain_pool_fetch_error"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    pool_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("pool_hash.id"), index=True),
        description="Pool for which metadata fetch failed",
    )

    fetch_time: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True)),
        description="When the fetch was attempted",
    )

    pmr_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("pool_metadata_ref.id"), index=True),
        description="Pool metadata reference that failed to fetch",
    )

    fetch_error: str | None = Field(
        default=None,
        sa_column=Column(Text),
        description="Error message describing the fetch failure",
    )

    retry_count: int | None = Field(
        default=None,
        sa_column=Column(Integer),
        description="Number of times fetch has been retried",
    )


class ReserveUtxo(DBSyncBase, table=True):
    """Reserve UTXO model for the reserve table.

    Represents UTXOs in the reserve pot, used for treasury and reserve distributions.
    """

    __tablename__ = "reserve"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    addr_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("stake_address.id"), index=True),
        description="Stake address receiving from reserves",
    )

    cert_index: int | None = Field(
        default=None,
        sa_column=Column(Integer),
        description="Certificate index within the transaction",
    )

    amount: int | None = Field(
        default=None,
        sa_column=Column(LovelaceType),
        description="Amount transferred from reserves (lovelace)",
    )

    tx_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("tx.id"), index=True),
        description="Transaction containing this reserve distribution",
    )


class PoolStat(DBSyncBase, table=True):
    """Pool statistics model for the pool_stat table.

    Represents pool performance statistics calculated per epoch.
    """

    __tablename__ = "pool_stat"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    pool_hash_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("pool_hash.id"), index=True),
        description="Pool for which statistics are calculated",
    )

    epoch_no: int | None = Field(
        default=None,
        sa_column=Column(Integer, index=True),
        description="Epoch number for these statistics",
    )

    number_of_blocks: int | None = Field(
        default=None,
        sa_column=Column(Integer),
        description="Number of blocks produced by this pool in the epoch",
    )

    number_of_delegators: int | None = Field(
        default=None,
        sa_column=Column(Integer),
        description="Number of delegators to this pool in the epoch",
    )

    stake: int | None = Field(
        default=None,
        sa_column=Column(LovelaceType),
        description="Total stake delegated to this pool (lovelace)",
    )

    voting_power: float | None = Field(
        default=None,
        description="Voting power of this pool for governance",
    )


class ReservedPoolTicker(DBSyncBase, table=True):
    """Reserved pool ticker model for the reserved_pool_ticker table.

    Represents ticker names that are reserved and cannot be used by pools.
    """

    __tablename__ = "reserved_pool_ticker"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    name: str | None = Field(
        default=None,
        sa_column=Column(String(32)),
        description="Reserved ticker name",
    )

    pool_hash: bytes | None = Field(
        default=None,
        sa_column=Column(Hash28Type),
        description="Pool hash that owns this reserved ticker",
    )


class DelistedPool(DBSyncBase, table=True):
    """Delisted pool model for the delisted_pool table.

    Represents pools that have been delisted from SMASH or other registries.
    """

    __tablename__ = "delisted_pool"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    hash_raw: bytes | None = Field(
        default=None,
        sa_column=Column(Hash28Type, unique=True, index=True),
        description="Raw hash of the delisted pool",
    )
