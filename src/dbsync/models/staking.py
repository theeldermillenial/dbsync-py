"""Staking and delegation models for Cardano DB Sync.

This module contains the staking and delegation models including stake registrations,
delegations, epoch stake distribution, and rewards.
"""

from __future__ import annotations

from enum import Enum

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
)
from sqlmodel import Field, Relationship

from ..utils.types import LovelaceType
from .base import DBSyncBase

__all__ = [
    "Delegation",
    "DelegationVote",
    "EpochStake",
    "EpochStakeProgress",
    "Reward",
    "RewardType",
    "StakeDeregistration",
    "StakeRegistration",
]


class RewardType(str, Enum):
    """Enum for reward types in the Cardano protocol."""

    LEADER = "leader"  # Block production rewards
    MEMBER = "member"  # Delegation rewards
    POOL_DEPOSIT_REFUND = "pool_deposit_refund"  # Pool deposit refunds
    REFUND = "refund"  # General refunds
    RESERVES = "reserves"  # Reserves distribution
    TREASURY = "treasury"  # Treasury distribution


class StakeRegistration(DBSyncBase, table=True):
    """Stake registration model for the stake_registration table.

    Represents stake key registration certificates that enable an address
    to participate in the staking protocol.
    """

    __tablename__ = "stake_registration"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    addr_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("stake_address.id"), index=True),
        description="Stake address being registered",
    )

    cert_index: int | None = Field(
        default=None,
        sa_column=Column(Integer),
        description="Certificate index within the transaction",
    )

    epoch_no: int | None = Field(
        default=None,
        sa_column=Column(Integer),
        description="Epoch when the registration becomes active",
    )

    tx_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("tx.id"), index=True),
        description="Transaction containing this registration certificate",
    )


class StakeDeregistration(DBSyncBase, table=True):
    """Stake deregistration model for the stake_deregistration table.

    Represents stake key deregistration certificates that remove an address
    from participation in the staking protocol and refund the deposit.
    """

    __tablename__ = "stake_deregistration"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    addr_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("stake_address.id"), index=True),
        description="Stake address being deregistered",
    )

    cert_index: int | None = Field(
        default=None,
        sa_column=Column(Integer),
        description="Certificate index within the transaction",
    )

    epoch_no: int | None = Field(
        default=None,
        sa_column=Column(Integer),
        description="Epoch when the deregistration becomes active",
    )

    tx_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("tx.id"), index=True),
        description="Transaction containing this deregistration certificate",
    )

    redeemer_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("redeemer.id")),
        description="Redeemer for script-based stake addresses",
    )


class Delegation(DBSyncBase, table=True):
    """Delegation model for the delegation table.

    Represents stake delegation certificates that delegate stake to a specific
    stake pool for block production and rewards.
    """

    __tablename__ = "delegation"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    addr_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("stake_address.id"), index=True),
        description="Stake address delegating",
    )

    cert_index: int | None = Field(
        default=None,
        sa_column=Column(Integer),
        description="Certificate index within the transaction",
    )

    pool_hash_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("pool_hash.id"), index=True),
        description="Pool being delegated to",
    )

    active_epoch_no: int | None = Field(
        default=None,
        sa_column=Column(Integer, index=True),
        description="Epoch when the delegation becomes active",
    )

    tx_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("tx.id"), index=True),
        description="Transaction containing this delegation certificate",
    )

    slot_no: int | None = Field(
        default=None,
        sa_column=Column(BigInteger),
        description="Slot number when the delegation was submitted",
    )

    redeemer_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("redeemer.id")),
        description="Redeemer for script-based stake addresses",
    )


class DelegationVote(DBSyncBase, table=True):
    """Delegation vote model for the delegation_vote table.

    Represents vote delegation certificates from the Conway era that delegate
    voting power to DReps (Delegated Representatives) for governance.
    """

    __tablename__ = "delegation_vote"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    addr_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("stake_address.id"), index=True),
        description="Stake address delegating voting power",
    )

    cert_index: int | None = Field(
        default=None,
        sa_column=Column(Integer),
        description="Certificate index within the transaction",
    )

    drep_hash_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("drep_hash.id"), index=True),
        description="DRep being delegated to for voting",
    )

    tx_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("tx.id"), index=True),
        description="Transaction containing this vote delegation certificate",
    )

    redeemer_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("redeemer.id")),
        description="Redeemer for script-based stake addresses",
    )


class EpochStake(DBSyncBase, table=True):
    """Epoch stake model for the epoch_stake table.

    Represents the historical stake distribution for each epoch, showing
    how much stake each address had delegated to each pool.
    """

    __tablename__ = "epoch_stake"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    addr_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("stake_address.id"), index=True),
        description="Stake address with delegated stake",
    )

    pool_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("pool_hash.id"), index=True),
        description="Pool receiving the delegated stake",
    )

    amount: int | None = Field(
        default=None,
        sa_column=Column(LovelaceType),
        description="Amount of stake delegated (lovelace)",
    )

    epoch_no: int | None = Field(
        default=None,
        sa_column=Column(Integer, index=True),
        description="Epoch number for this stake snapshot",
    )


class EpochStakeProgress(DBSyncBase, table=True):
    """Epoch stake progress model for the epoch_stake_progress table.

    Tracks the progress of stake calculation for each epoch to monitor
    synchronization status and performance.
    """

    __tablename__ = "epoch_stake_progress"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    epoch_no: int | None = Field(
        default=None,
        sa_column=Column(Integer, unique=True, index=True),
        description="Epoch number being calculated",
    )

    completed: bool | None = Field(
        default=None,
        sa_column=Column(Boolean),
        description="Whether stake calculation is completed for this epoch",
    )


class Reward(DBSyncBase, table=True):
    """Reward model for the reward table.

    Represents staking rewards earned by stake addresses, including
    block production rewards, delegation rewards, and treasury distributions.

    Note: This table has no primary key and uses a composite structure.
    """

    __tablename__ = "reward"

    addr_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("stake_address.id"), primary_key=True),
        description="Stake address receiving the reward",
    )

    type_: str | None = Field(
        default=None,
        sa_column=Column(String(15), name="type", primary_key=True),
        description="Type of reward (leader, member, reserves, treasury, etc.)",
    )

    amount: int | None = Field(
        default=None,
        sa_column=Column(LovelaceType),
        description="Reward amount (lovelace)",
    )

    earned_epoch: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True),
        description="Epoch when the reward was earned",
    )

    spendable_epoch: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, index=True),
        description="Epoch when the reward becomes spendable",
    )

    pool_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("pool_hash.id"), primary_key=True),
        description="Pool associated with this reward (for delegation rewards)",
    )


# Relationships (defined at the end to avoid circular imports)
StakeRegistration.stake_address = Relationship()
StakeRegistration.transaction = Relationship()

StakeDeregistration.stake_address = Relationship()
StakeDeregistration.transaction = Relationship()
StakeDeregistration.redeemer = Relationship()

Delegation.stake_address = Relationship()
Delegation.pool_hash = Relationship()
Delegation.transaction = Relationship()
Delegation.redeemer = Relationship()

DelegationVote.stake_address = Relationship()
DelegationVote.drep_hash = Relationship()
DelegationVote.transaction = Relationship()
DelegationVote.redeemer = Relationship()

EpochStake.stake_address = Relationship()
EpochStake.pool_hash = Relationship()

Reward.stake_address = Relationship()
Reward.pool_hash = Relationship()
