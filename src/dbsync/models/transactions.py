"""Transaction detail models for Cardano DB Sync.

This module contains detailed transaction models including inputs, outputs,
scripts, redeemers, and other transaction components.
Transaction input, output, and metadata models.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    BigInteger,
    Column,
    ForeignKey,
    LargeBinary,
)
from sqlmodel import Field, Relationship

from ..utils.types import Hash28Type, Hash32Type, LovelaceType, TxIndexType, Word64Type
from .base import DBSyncBase

if TYPE_CHECKING:
    pass

__all__ = [
    "CollateralTransactionInput",
    "CollateralTransactionOutput",
    "Datum",
    "ExtraKeyWitness",
    "ReferenceTransactionInput",
    "ScriptPurposeType",
    "TransactionCbor",
    "TransactionInput",
    "TransactionOutput",
    "TxMetadata",
    "Withdrawal",
]


class ScriptPurposeType(str, Enum):
    """Enumeration of script purpose types in Cardano."""

    SPEND = "spend"
    MINT = "mint"
    CERT = "cert"
    REWARD = "reward"
    VOTING = "voting"
    PROPOSING = "proposing"


class TransactionInput(DBSyncBase, table=True):
    """Transaction input model for the tx_in table.

    Represents transaction inputs that spend previous transaction outputs.
    """

    __tablename__ = "tx_in"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    tx_in_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("tx.id"), index=True),
        description="Transaction that contains this input",
    )

    tx_out_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("tx_out.id"), index=True),
        description="Transaction output being spent",
    )

    tx_out_index: int | None = Field(
        default=None,
        sa_column=Column(TxIndexType),
        description="Index of the output being spent",
    )

    redeemer_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("redeemer.id")),
        description="Redeemer used to unlock this input (for script inputs)",
    )


class TransactionOutput(DBSyncBase, table=True):
    """Transaction output model for the tx_out table.

    Represents transaction outputs that can be spent as inputs.
    """

    __tablename__ = "tx_out"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    tx_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("tx.id"), index=True),
        description="Transaction that created this output",
    )

    index: int | None = Field(
        default=None,
        sa_column=Column(TxIndexType),
        description="Index of this output within the transaction",
    )

    address_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("address.id"), index=True),
        description="Address ID reference",
    )

    stake_address_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("stake_address.id")),
        description="Stake address associated with this output",
    )

    value: int | None = Field(
        default=None,
        sa_column=Column(LovelaceType),
        description="ADA value of this output (in lovelace)",
    )

    data_hash: bytes | None = Field(
        default=None,
        sa_column=Column(Hash32Type),
        description="Hash of datum associated with this output",
    )

    inline_datum_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("datum.id")),
        description="Inline datum associated with this output",
    )

    reference_script_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("script.id")),
        description="Reference script associated with this output",
    )


class CollateralTransactionInput(DBSyncBase, table=True):
    """Collateral transaction input model for the collateral_tx_in table.

    Represents collateral inputs used for script validation in smart contract transactions.
    """

    __tablename__ = "collateral_tx_in"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    tx_in_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("tx.id"), index=True),
        description="Transaction that contains this collateral input",
    )

    tx_out_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("tx_out.id"), index=True),
        description="Transaction output being used as collateral",
    )

    tx_out_index: int | None = Field(
        default=None,
        sa_column=Column(TxIndexType),
        description="Index of the output being used as collateral",
    )


class ReferenceTransactionInput(DBSyncBase, table=True):
    """Reference transaction input model for the reference_tx_in table.

    Represents reference inputs (CIP-31) that are read but not consumed.
    """

    __tablename__ = "reference_tx_in"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    tx_in_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("tx.id"), index=True),
        description="Transaction that references this input",
    )

    tx_out_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("tx_out.id"), index=True),
        description="Transaction output being referenced",
    )

    tx_out_index: int | None = Field(
        default=None,
        sa_column=Column(TxIndexType),
        description="Index of the output being referenced",
    )


class CollateralTransactionOutput(DBSyncBase, table=True):
    """Collateral transaction output model for the collateral_tx_out table.

    Represents collateral outputs that are created only if script validation fails.
    """

    __tablename__ = "collateral_tx_out"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    tx_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("tx.id"), index=True),
        description="Transaction that would create this collateral output",
    )

    index: int | None = Field(
        default=None,
        sa_column=Column(TxIndexType),
        description="Index of this collateral output within the transaction",
    )

    address_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("address.id"), index=True),
        description="Address ID reference",
    )

    stake_address_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("stake_address.id")),
        description="Stake address associated with this collateral output",
    )

    value: int | None = Field(
        default=None,
        sa_column=Column(LovelaceType),
        description="ADA value of this collateral output (in lovelace)",
    )

    data_hash: bytes | None = Field(
        default=None,
        sa_column=Column(Hash32Type),
        description="Hash of datum associated with this collateral output",
    )

    inline_datum_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("datum.id")),
        description="Inline datum associated with this collateral output",
    )

    reference_script_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("script.id")),
        description="Reference script associated with this collateral output",
    )


class TransactionCbor(DBSyncBase, table=True):
    """Transaction CBOR model for the tx_cbor table.

    Stores the raw CBOR-encoded transaction data.
    """

    __tablename__ = "tx_cbor"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    tx_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("tx.id"), unique=True, index=True),
        description="Transaction this CBOR data belongs to",
    )

    cbor_bytes: bytes | None = Field(
        default=None,
        sa_column=Column(LargeBinary, name="bytes"),
        description="Raw CBOR-encoded transaction data",
    )


class Datum(DBSyncBase, table=True):
    """Datum model for the datum table.

    Represents Plutus datum found in transaction witnesses or inlined in outputs.
    """

    __tablename__ = "datum"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    hash_: bytes | None = Field(
        default=None,
        sa_column=Column(Hash32Type, unique=True, index=True, name="hash"),
        description="Hash of the datum",
    )

    tx_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("tx.id"), index=True),
        description="Transaction that first introduced this datum",
    )

    value: dict | None = Field(
        default=None,
        sa_column=Column(JSON),
        description="JSON representation of the datum value",
    )

    cbor_bytes: bytes | None = Field(
        default=None,
        sa_column=Column(LargeBinary, name="bytes"),
        description="Raw CBOR-encoded datum data",
    )


class ExtraKeyWitness(DBSyncBase, table=True):
    """Extra key witness model for the extra_key_witness table.

    Represents additional key witness hashes in transactions.
    """

    __tablename__ = "extra_key_witness"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    hash_: bytes | None = Field(
        default=None,
        sa_column=Column(Hash28Type, index=True, name="hash"),
        description="Hash of the extra key witness",
    )

    tx_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("tx.id"), index=True),
        description="Transaction that contains this extra key witness",
    )


class Withdrawal(DBSyncBase, table=True):
    """Withdrawal model for the withdrawal table.

    Represents withdrawals from reward accounts in transactions.
    """

    __tablename__ = "withdrawal"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    addr_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("stake_address.id"), index=True),
        description="Stake address from which rewards are withdrawn",
    )

    amount: int | None = Field(
        default=None,
        sa_column=Column(LovelaceType),
        description="Amount withdrawn (in lovelace)",
    )

    redeemer_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("redeemer.id")),
        description="Redeemer used for script-controlled withdrawals",
    )

    tx_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("tx.id"), index=True),
        description="Transaction that contains this withdrawal",
    )


class TxMetadata(DBSyncBase, table=True):
    """Transaction metadata model for the tx_metadata table.

    Represents metadata attached to a transaction. Transaction metadata
    allows arbitrary data to be attached to transactions using a key-value
    structure where keys are unsigned 64-bit integers.
    """

    __tablename__ = "tx_metadata"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    key: int | None = Field(
        default=None,
        sa_column=Column(Word64Type, index=True),
        description="The metadata key (a Word64/unsigned 64 bit number)",
    )

    json_: dict | None = Field(
        default=None,
        sa_column=Column(JSON, name="json"),
        description="The JSON payload if it can be decoded as JSON",
    )

    cbor_bytes: bytes | None = Field(
        default=None,
        sa_column=Column(LargeBinary, name="bytes"),
        description="The raw bytes of the payload",
    )

    tx_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("tx.id"), index=True),
        description="The Tx table index of the transaction where this metadata was included",
    )


# Add relationships after class definitions to avoid SQLModel annotation issues
TransactionInput.transaction = Relationship(
    sa_relationship_kwargs={"foreign_keys": "[TransactionInput.tx_in_id]"}
)
TransactionInput.transaction_output = Relationship()
TransactionInput.redeemer = Relationship()
TransactionOutput.transaction = Relationship()
TransactionOutput.inline_datum = Relationship()
TransactionOutput.reference_script = Relationship()

CollateralTransactionInput.transaction = Relationship(
    sa_relationship_kwargs={"foreign_keys": "[CollateralTransactionInput.tx_in_id]"}
)
CollateralTransactionInput.transaction_output = Relationship()

ReferenceTransactionInput.transaction = Relationship(
    sa_relationship_kwargs={"foreign_keys": "[ReferenceTransactionInput.tx_in_id]"}
)
ReferenceTransactionInput.transaction_output = Relationship()

CollateralTransactionOutput.transaction = Relationship()
CollateralTransactionOutput.inline_datum = Relationship()
CollateralTransactionOutput.reference_script = Relationship()

TransactionCbor.transaction = Relationship()

Datum.transaction = Relationship()

ExtraKeyWitness.transaction = Relationship()

Withdrawal.transaction = Relationship()
Withdrawal.redeemer = Relationship()

TxMetadata.transaction = Relationship()
