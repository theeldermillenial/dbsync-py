"""Database models for the dbsync-py package.

This module provides SQLModel-based models for working with
the Cardano DB Sync database schema.
"""

from __future__ import annotations

# Multi-asset models
from .assets import (
    MaTxMint,
    MaTxOut,
    MultiAsset,
    generate_cip14_fingerprint,
)

# Import base models that other models depend on
from .base import (
    DBSyncBase,
    NetworkModel,
    TimestampedModel,
)

# Import blockchain models
from .blockchain import (
    Address,
    Block,
    Epoch,
    EpochSyncTime,
    ReverseIndex,
    SchemaVersion,
    SlotLeader,
    StakeAddress,
    Transaction,
)

# Import foundation models
from .foundation import (
    ChainMeta,
    EventInfo,
    ExtraMigrations,
)

# Import governance models
from .governance import (
    Committee,
    CommitteeDeRegistration,
    CommitteeHash,
    CommitteeMember,
    CommitteeRegistration,
    Constitution,
    DrepDistr,
    DrepHash,
    DrepRegistration,
    EpochState,
    GovActionProposal,
    GovActionType,
    OffChainVoteAuthor,
    OffChainVoteData,
    OffChainVoteDrepData,
    OffChainVoteExternalUpdate,
    OffChainVoteFetchError,
    OffChainVoteGovActionData,
    OffChainVoteReference,
    TreasuryWithdrawal,
    VoteType,
    VotingAnchor,
    VotingProcedure,
)

# Pool management models
from .pools import (
    DelistedPool,
    OffchainPoolData,
    OffchainPoolFetchError,
    PoolHash,
    PoolMetadataRef,
    PoolOwner,
    PoolRelay,
    PoolRelayType,
    PoolRetire,
    PoolStat,
    PoolUpdate,
    ReservedPoolTicker,
    ReserveUtxo,
)

# Import protocol parameter models
from .protocol import (
    EpochParam,
    ParamProposal,
    RewardRest,
)

# Import script models
from .scripts import (
    CostModel,
    PlutusVersion,
    Redeemer,
    RedeemerData,
    RedeemerTag,
    Script,
    ScriptType,
)

# Import staking models
from .staking import (
    Delegation,
    DelegationVote,
    EpochStake,
    EpochStakeProgress,
    Reward,
    RewardType,
    StakeDeregistration,
    StakeRegistration,
)

# Import transaction models
from .transactions import (
    CollateralTransactionInput,
    CollateralTransactionOutput,
    Datum,
    ExtraKeyWitness,
    ReferenceTransactionInput,
    ScriptPurposeType,
    TransactionCbor,
    TransactionInput,
    TransactionOutput,
    TxMetadata,
    Withdrawal,
)

# Import treasury and reserves models
from .treasury import (
    AdaPots,
    PotTransfer,
    Treasury,
)

# Export all models in __all__
__all__ = [
    # Base models
    "DBSyncBase",
    "NetworkModel",
    "TimestampedModel",
    # Foundation models
    "ChainMeta",
    "EventInfo",
    "ExtraMigrations",
    # Blockchain models
    "Address",
    "Block",
    "Epoch",
    "EpochSyncTime",
    "ReverseIndex",
    "SchemaVersion",
    "SlotLeader",
    "StakeAddress",
    "Transaction",
    # Transaction models
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
    # Staking models
    "Delegation",
    "DelegationVote",
    "EpochStake",
    "EpochStakeProgress",
    "Reward",
    "RewardType",
    "StakeDeregistration",
    "StakeRegistration",
    # Pool management models
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
    "ReservedPoolTicker",
    "ReserveUtxo",
    # Multi-asset models
    "MaTxMint",
    "MaTxOut",
    "MultiAsset",
    "generate_cip14_fingerprint",
    # Script models
    "CostModel",
    "PlutusVersion",
    "Redeemer",
    "RedeemerData",
    "RedeemerTag",
    "Script",
    "ScriptType",
    # Treasury and reserves models
    "AdaPots",
    "PotTransfer",
    "Treasury",
    # Protocol parameter models
    "EpochParam",
    "ParamProposal",
    "RewardRest",
    # Conway era governance models
    "Committee",
    "CommitteeDeRegistration",
    "CommitteeHash",
    "CommitteeMember",
    "CommitteeRegistration",
    "Constitution",
    "DrepDistr",
    "DrepHash",
    "DrepRegistration",
    "EpochState",
    "GovActionProposal",
    "GovActionType",
    "OffChainVoteAuthor",
    "OffChainVoteData",
    "OffChainVoteDrepData",
    "OffChainVoteExternalUpdate",
    "OffChainVoteFetchError",
    "OffChainVoteGovActionData",
    "OffChainVoteReference",
    "TreasuryWithdrawal",
    "VoteType",
    "VotingAnchor",
    "VotingProcedure",
]

# Version information
__version__ = "0.1.0"

# Future model exports will be added here as they are implemented
# Example: from .core import Block, Transaction, TransactionOutput
# Example: from .staking import PoolHash, StakeAddress, Delegation
