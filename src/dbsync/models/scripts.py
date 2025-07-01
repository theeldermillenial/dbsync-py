"""Script and smart contract models for Cardano DB Sync.

This module contains the script models including Plutus scripts, redeemer data,
and script execution context.

Supports Plutus script versioning and integration with pycardano classes.
"""

from __future__ import annotations

from enum import Enum

from sqlalchemy import (
    JSON,
    BigInteger,
    Column,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
)
from sqlmodel import Field, Relationship

from ..utils.types import Hash28Type, Hash32Type, LovelaceType
from .base import DBSyncBase

__all__ = [
    "CostModel",
    "PlutusVersion",
    "Redeemer",
    "RedeemerData",
    "RedeemerTag",
    "Script",
    "ScriptType",
]


class ScriptType(str, Enum):
    """Script type enumeration for different script languages."""

    NATIVE = "native"
    PLUTUS_V1 = "plutusV1"
    PLUTUS_V2 = "plutusV2"
    PLUTUS_V3 = "plutusV3"


class PlutusVersion(str, Enum):
    """Plutus script version enumeration."""

    V1 = "PlutusV1"
    V2 = "PlutusV2"
    V3 = "PlutusV3"


class RedeemerTag(str, Enum):
    """Redeemer tag enumeration for script execution context."""

    SPEND = "spend"
    MINT = "mint"
    CERT = "cert"
    REWARD = "reward"
    VOTE = "vote"
    PROPOSE = "propose"


class Script(DBSyncBase, table=True):
    """Script model representing all types of Cardano scripts.

    Maps to the 'script' table in Cardano DB Sync.
    Represents both native scripts and Plutus scripts with their metadata.

    Attributes:
        id_: Primary key
        tx_id: Foreign key to transaction that registered this script
        hash_: Script hash (28 bytes)
        script_type: Script type (native, plutusV1, plutusV2, plutusV3)
        script_json: Native script JSON representation (for native scripts)
        script_bytes: Script bytes (for Plutus scripts)
        serialised_size: Size of serialized script in bytes

    References:
        - Cardano Ledger: Script validation and execution
        - Plutus: Smart contract platform for Cardano
    """

    __tablename__ = "script"

    id_: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, name="id")
    )
    tx_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("tx.id"), nullable=False)
    )
    hash_: bytes = Field(
        sa_column=Column(Hash28Type, unique=True, nullable=False, name="hash")
    )
    type_: str = Field(sa_column=Column(String(20), name="type", nullable=False))
    json_: dict | None = Field(
        default=None, sa_column=Column(JSON, name="json", nullable=True)
    )
    bytes_: bytes | None = Field(
        default=None, sa_column=Column(LargeBinary, name="bytes", nullable=True)
    )
    serialised_size: int | None = Field(
        default=None, sa_column=Column(Integer, nullable=True)
    )

    @property
    def hash_hex(self) -> str:
        """Get script hash as hex string."""
        return self.hash_.hex() if self.hash_ else ""

    @property
    def is_native(self) -> bool:
        """Check if this is a native script."""
        return self.type_ == ScriptType.NATIVE.value

    @property
    def is_plutus(self) -> bool:
        """Check if this is a Plutus script."""
        return self.type_ in (
            ScriptType.PLUTUS_V1.value,
            ScriptType.PLUTUS_V2.value,
            ScriptType.PLUTUS_V3.value,
        )

    @property
    def plutus_version(self) -> PlutusVersion | None:
        """Get Plutus version if this is a Plutus script."""
        if self.type_ == ScriptType.PLUTUS_V1.value:
            return PlutusVersion.V1
        elif self.type_ == ScriptType.PLUTUS_V2.value:
            return PlutusVersion.V2
        elif self.type_ == ScriptType.PLUTUS_V3.value:
            return PlutusVersion.V3
        return None

    def to_pycardano_script_hash(self):
        """Convert to pycardano ScriptHash.

        Returns:
            pycardano.ScriptHash instance

        Raises:
            ImportError: If pycardano is not available
        """
        try:
            from pycardano import ScriptHash

            return ScriptHash(self.hash_)
        except ImportError:
            raise ImportError("pycardano is required for ScriptHash conversion")


class RedeemerData(DBSyncBase, table=True):
    """Redeemer data model representing script execution parameters.

    Maps to the 'redeemer_data' table in Cardano DB Sync.
    Stores the data provided to scripts during execution.

    Attributes:
        id: Primary key
        hash: Hash of the redeemer data (32 bytes)
        tx_id: Foreign key to transaction containing this redeemer data
        value: CBOR-encoded redeemer data
        data_bytes: Raw bytes of the redeemer data

    References:
        - Plutus: Script execution and redeemer data
        - CBOR: Concise Binary Object Representation
    """

    __tablename__ = "redeemer_data"

    id_: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, name="id")
    )
    hash_: bytes = Field(
        sa_column=Column(Hash32Type, unique=True, nullable=False, name="hash")
    )
    tx_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("tx.id"), nullable=False)
    )
    value: dict | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    bytes_: bytes | None = Field(
        default=None, sa_column=Column(LargeBinary, name="bytes", nullable=True)
    )

    @property
    def hash_hex(self) -> str:
        """Get redeemer data hash as hex string."""
        return self.hash_.hex() if self.hash_ else ""

    @property
    def size_bytes(self) -> int:
        """Get size of redeemer data in bytes."""
        return len(self.bytes_) if self.bytes_ else 0

    def to_pycardano_redeemer_data(self):
        """Convert to pycardano redeemer data.

        Returns:
            Decoded redeemer data object

        Raises:
            ImportError: If pycardano is not available
        """
        try:
            import cbor2

            if self.bytes_:
                return cbor2.loads(self.bytes_)
            return None
        except ImportError:
            raise ImportError("cbor2 is required for redeemer data conversion")


class Redeemer(DBSyncBase, table=True):
    """Redeemer model representing script execution context.

    Maps to the 'redeemer' table in Cardano DB Sync.
    Links redeemer data to specific script executions with execution costs.

    Attributes:
        id: Primary key
        tx_id: Foreign key to transaction containing this redeemer
        unit_mem: Memory units consumed during script execution
        unit_steps: CPU steps consumed during script execution
        fee: Fee charged for script execution (lovelace)
        purpose: Purpose of script execution (spend, mint, cert, reward, vote, propose)
        index: Index within the transaction for this purpose
        script_hash: Hash of the script being executed
        redeemer_data_id: Foreign key to redeemer data

    References:
        - Plutus: Script execution and cost model
        - Cardano Ledger: Transaction validation and fees
    """

    __tablename__ = "redeemer"

    id_: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, name="id")
    )
    tx_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("tx.id"), nullable=False)
    )
    unit_mem: int = Field(sa_column=Column(BigInteger, nullable=False))
    unit_steps: int = Field(sa_column=Column(BigInteger, nullable=False))
    fee: int | None = Field(default=None, sa_column=Column(LovelaceType, nullable=True))
    purpose: str = Field(sa_column=Column(String(20), nullable=False))
    index: int = Field(sa_column=Column(Integer, nullable=False))
    script_hash: bytes | None = Field(
        default=None, sa_column=Column(Hash28Type, nullable=True)
    )
    redeemer_data_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("redeemer_data.id"), nullable=True),
    )

    @property
    def total_execution_units(self) -> int:
        """Get total execution units (memory + steps)."""
        return self.unit_mem + self.unit_steps

    @property
    def execution_cost_ratio(self) -> float:
        """Get ratio of memory to CPU units."""
        if self.unit_steps == 0:
            return float("inf") if self.unit_mem > 0 else 0.0
        return self.unit_mem / self.unit_steps

    @property
    def script_hash_hex(self) -> str:
        """Get script hash as hex string."""
        return self.script_hash.hex() if self.script_hash else ""

    @property
    def is_spending_redeemer(self) -> bool:
        """Check if this redeemer is for spending a UTXO."""
        return self.purpose == RedeemerTag.SPEND.value

    @property
    def is_minting_redeemer(self) -> bool:
        """Check if this redeemer is for minting/burning assets."""
        return self.purpose == RedeemerTag.MINT.value

    @property
    def is_certificate_redeemer(self) -> bool:
        """Check if this redeemer is for certificate validation."""
        return self.purpose == RedeemerTag.CERT.value

    @property
    def is_reward_redeemer(self) -> bool:
        """Check if this redeemer is for reward withdrawal."""
        return self.purpose == RedeemerTag.REWARD.value

    def to_pycardano_execution_units(self):
        """Convert to pycardano ExecutionUnits.

        Returns:
            pycardano.ExecutionUnits instance

        Raises:
            ImportError: If pycardano is not available
        """
        try:
            from pycardano import ExecutionUnits

            return ExecutionUnits(memory=self.unit_mem, steps=self.unit_steps)
        except ImportError:
            raise ImportError("pycardano is required for ExecutionUnits conversion")


# Import relationships at the end to avoid circular imports
# from .blockchain import Transaction

# Uncomment and add the relationship definitions at the end of the file
Script.transaction = Relationship()
RedeemerData.transaction = Relationship()
RedeemerData.redeemers = Relationship(back_populates="redeemer_data")
Redeemer.transaction = Relationship()
Redeemer.redeemer_data = Relationship(back_populates="redeemers")


class CostModel(DBSyncBase, table=True):
    """Cost model for Plutus script execution.

    Maps to the 'cost_model' table in Cardano DB Sync.
    Stores execution cost parameters for different Plutus script operations.

    Attributes:
        id_: Primary key
        hash_: Hash of the cost model (32 bytes) - ensures uniqueness
        costs: JSON object containing the actual cost parameters

    References:
        - Plutus: Script execution cost model
        - Cardano Ledger: Protocol parameter cost models
    """

    __tablename__ = "cost_model"

    id_: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, name="id")
    )
    hash_: bytes = Field(
        sa_column=Column(Hash32Type, unique=True, nullable=False, name="hash")
    )
    costs: dict = Field(sa_column=Column(JSON, nullable=False))

    @property
    def hash_hex(self) -> str:
        """Get cost model hash as hex string."""
        return self.hash_.hex() if self.hash_ else ""

    @property
    def operation_count(self) -> int:
        """Get number of operations defined in this cost model."""
        return len(self.costs)

    @property
    def is_valid(self) -> bool:
        """Check if cost model has valid structure."""
        return isinstance(self.costs, dict) and len(self.costs) > 0

    def get_operation_cost(self, operation: str) -> int | None:
        """Get cost for a specific operation.

        Args:
            operation: The operation name to get cost for

        Returns:
            Cost for the operation, or None if not found
        """
        return self.costs.get(operation)

    def has_operation(self, operation: str) -> bool:
        """Check if cost model includes a specific operation.

        Args:
            operation: The operation name to check

        Returns:
            True if operation is defined in cost model
        """
        return operation in self.costs
