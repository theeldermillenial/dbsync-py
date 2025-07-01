"""Conway era governance models for Cardano DB Sync.

This module contains models for Conway era governance functionality including
DReps (Delegated Representatives), Constitutional Committee, Governance Actions,
Voting, and offchain governance metadata.

Key Conway Era Features:
- DRep registration and voting power delegation
- Constitutional committee with hot/cold key setup
- Governance action proposals and lifecycle management
- Voting procedures for all governance bodies
- Treasury withdrawals and constitution management
- Offchain governance metadata (CIP-100, CIP-108, CIP-119)
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship

from ..utils.types import Hash28Type, Hash32Type, LovelaceType, Word31Type
from .base import DBSyncBase

__all__ = [
    # DRep models
    "DrepHash",
    "DrepRegistration",
    "DrepDistr",
    # Committee models
    "CommitteeHash",
    "CommitteeRegistration",
    "CommitteeDeRegistration",
    "Committee",
    "CommitteeMember",
    # Governance action models
    "GovActionProposal",
    "TreasuryWithdrawal",
    "Constitution",
    "VotingAnchor",
    "VotingProcedure",
    "EpochState",
    # Offchain governance metadata models
    "OffChainVoteData",
    "OffChainVoteGovActionData",
    "OffChainVoteDrepData",
    "OffChainVoteAuthor",
    "OffChainVoteReference",
    "OffChainVoteExternalUpdate",
    "OffChainVoteFetchError",
    # Enums
    "GovActionType",
    "VoteType",
    "CommitteeState",
]


class GovActionType(str, Enum):
    """Governance action types in Conway era."""

    PARAMETER_CHANGE = "ParameterChange"
    HARD_FORK_INITIATION = "HardForkInitiation"
    TREASURY_WITHDRAWALS = "TreasuryWithdrawals"
    NO_CONFIDENCE = "NoConfidence"
    UPDATE_COMMITTEE = "UpdateCommittee"
    NEW_CONSTITUTION = "NewConstitution"
    INFO_ACTION = "InfoAction"


class VoteType(str, Enum):
    """Vote types for governance actions."""

    YES = "Yes"
    NO = "No"
    ABSTAIN = "Abstain"


class CommitteeState(str, Enum):
    """Constitutional committee states."""

    AUTHORIZED = "Authorized"
    RESIGNED = "Resigned"
    EXPIRED = "Expired"


# DRep Models


class DrepHash(DBSyncBase, table=True):
    """DRep hash model for the drep_hash table.

    Stores the hash identifiers for Delegated Representatives (DReps).
    DReps are entities that can receive voting power delegation from Ada holders
    for governance decisions in the Conway era.
    """

    __tablename__ = "drep_hash"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    raw: bytes | None = Field(
        default=None,
        sa_column=Column(Hash28Type, unique=True, nullable=False),
        description="Raw DRep credential hash (28 bytes)",
    )

    view: str | None = Field(
        default=None,
        sa_column=Column(String(255)),
        description="Human-readable DRep ID (bech32 encoded)",
    )

    has_script: bool | None = Field(
        default=None,
        sa_column=Column(Boolean, nullable=False, default=False),
        description="Whether this DRep uses a script credential",
    )


class DrepRegistration(DBSyncBase, table=True):
    """DRep registration model for the drep_registration table.

    Tracks DRep registration certificates including deposits, anchors,
    and voting metadata for Conway era governance.
    """

    __tablename__ = "drep_registration"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    tx_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("tx.id"), nullable=False, index=True),
        description="Transaction containing this DRep registration",
    )

    cert_index: int | None = Field(
        default=None,
        sa_column=Column(Integer, nullable=False),
        description="Certificate index within the transaction",
    )

    drep_hash_id: int | None = Field(
        default=None,
        sa_column=Column(
            BigInteger, ForeignKey("drep_hash.id"), nullable=False, index=True
        ),
        description="DRep hash being registered",
    )

    deposit: int | None = Field(
        default=None,
        sa_column=Column(LovelaceType),
        description="Registration deposit amount (Lovelace)",
    )

    voting_anchor_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("voting_anchor.id")),
        description="Optional voting anchor for DRep metadata",
    )


class DrepDistr(DBSyncBase, table=True):
    """DRep distribution model for the drep_distr table.

    Tracks the stake distribution delegated to each DRep for voting power
    calculations in Conway era governance.
    """

    __tablename__ = "drep_distr"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    hash_id: int | None = Field(
        default=None,
        sa_column=Column(
            BigInteger, ForeignKey("drep_hash.id"), nullable=False, index=True
        ),
        description="DRep receiving delegated stake",
    )

    amount: int | None = Field(
        default=None,
        sa_column=Column(LovelaceType, nullable=False),
        description="Amount of stake delegated to this DRep (Lovelace)",
    )

    epoch_no: int | None = Field(
        default=None,
        sa_column=Column(Word31Type, nullable=False, index=True),
        description="Epoch when this distribution was calculated",
    )

    active_until: int | None = Field(
        default=None,
        sa_column=Column(Word31Type),
        description="Epoch until which this DRep is considered active",
    )


# Committee Models


class CommitteeHash(DBSyncBase, table=True):
    """Committee hash model for the committee_hash table.

    Stores hash identifiers for Constitutional Committee members.
    The Constitutional Committee ensures governance actions comply with
    the Cardano Constitution.
    """

    __tablename__ = "committee_hash"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    raw: bytes | None = Field(
        default=None,
        sa_column=Column(Hash28Type, unique=True, nullable=False),
        description="Raw committee member credential hash (28 bytes)",
    )

    has_script: bool | None = Field(
        default=None,
        sa_column=Column(Boolean, nullable=False, default=False),
        description="Whether this committee member uses a script credential",
    )


class CommitteeRegistration(DBSyncBase, table=True):
    """Committee registration model for the committee_registration table.

    Tracks Constitutional Committee member registrations including
    hot key delegation for Conway era governance.
    """

    __tablename__ = "committee_registration"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    tx_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("tx.id"), nullable=False, index=True),
        description="Transaction containing this committee registration",
    )

    cert_index: int | None = Field(
        default=None,
        sa_column=Column(Integer, nullable=False),
        description="Certificate index within the transaction",
    )

    cold_key_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("committee_hash.id"), nullable=False),
        description="Cold key hash for committee member",
    )

    hot_key_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("committee_hash.id")),
        description="Hot key hash for committee member voting",
    )


class CommitteeDeRegistration(DBSyncBase, table=True):
    """Committee de-registration model for the committee_de_registration table.

    Tracks Constitutional Committee member resignations and de-registrations
    in Conway era governance.
    """

    __tablename__ = "committee_de_registration"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    tx_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("tx.id"), nullable=False, index=True),
        description="Transaction containing this committee de-registration",
    )

    cert_index: int | None = Field(
        default=None,
        sa_column=Column(Integer, nullable=False),
        description="Certificate index within the transaction",
    )

    cold_key_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("committee_hash.id"), nullable=False),
        description="Cold key hash of resigning committee member",
    )

    voting_anchor_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("voting_anchor.id")),
        description="Optional voting anchor for resignation metadata",
    )


class Committee(DBSyncBase, table=True):
    """Committee model for the committee table.

    Represents the current Constitutional Committee composition and thresholds
    for Conway era governance.
    """

    __tablename__ = "committee"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    gov_action_proposal_id: int | None = Field(
        default=None,
        sa_column=Column(
            BigInteger, ForeignKey("gov_action_proposal.id"), nullable=False
        ),
        description="Governance action that established this committee",
    )

    quorum_numerator: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, nullable=False),
        description="Committee quorum threshold numerator",
    )

    quorum_denominator: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, nullable=False),
        description="Committee quorum threshold denominator",
    )


class CommitteeMember(DBSyncBase, table=True):
    """Committee member model for the committee_member table.

    Tracks individual Constitutional Committee members, their terms,
    and expiration dates for Conway era governance.
    """

    __tablename__ = "committee_member"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    committee_id: int | None = Field(
        default=None,
        sa_column=Column(
            BigInteger, ForeignKey("committee.id"), nullable=False, index=True
        ),
        description="Committee this member belongs to",
    )

    committee_hash_id: int | None = Field(
        default=None,
        sa_column=Column(
            BigInteger, ForeignKey("committee_hash.id"), nullable=False, index=True
        ),
        description="Committee member hash identifier",
    )

    expiration_epoch: int | None = Field(
        default=None,
        sa_column=Column(Word31Type, nullable=False),
        description="Epoch when this member's term expires",
    )


# Governance Action Models


class GovActionProposal(DBSyncBase, table=True):
    """Governance action proposal model for the gov_action_proposal table.

    Represents all types of governance action proposals in Conway era,
    including parameter changes, hard forks, treasury withdrawals, etc.
    """

    __tablename__ = "gov_action_proposal"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    tx_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("tx.id"), nullable=False, index=True),
        description="Transaction containing this governance action",
    )

    index: int | None = Field(
        default=None,
        sa_column=Column(Integer, nullable=False),
        description="Index of this action within the transaction",
    )

    prev_gov_action_proposal: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("gov_action_proposal.id")),
        description="Previous governance action of the same type (for ordering)",
    )

    deposit: int | None = Field(
        default=None,
        sa_column=Column(LovelaceType, nullable=False),
        description="Deposit amount for this governance action (Lovelace)",
    )

    return_address: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("stake_address.id"), nullable=False),
        description="Address to return deposit to",
    )

    expiration: int | None = Field(
        default=None,
        sa_column=Column(Word31Type),
        description="Epoch when this action expires if not ratified",
    )

    voting_anchor_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("voting_anchor.id")),
        description="Optional voting anchor for action metadata",
    )

    type_: GovActionType | None = Field(
        default=None,
        sa_column=Column(String(32), nullable=False, name="type"),
        description="Type of governance action",
    )

    description: str | None = Field(
        default=None,
        sa_column=Column(Text),
        description="Optional description of the governance action",
    )

    param_proposal: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("param_proposal.id")),
        description="Associated parameter proposal (for parameter change actions)",
    )

    ratified_epoch: int | None = Field(
        default=None,
        sa_column=Column(Word31Type),
        description="Epoch when this action was ratified (if applicable)",
    )

    enacted_epoch: int | None = Field(
        default=None,
        sa_column=Column(Word31Type),
        description="Epoch when this action was enacted (if applicable)",
    )

    dropped_epoch: int | None = Field(
        default=None,
        sa_column=Column(Word31Type),
        description="Epoch when this action was dropped (if applicable)",
    )

    expired_epoch: int | None = Field(
        default=None,
        sa_column=Column(Word31Type),
        description="Epoch when this action expired (if applicable)",
    )


class TreasuryWithdrawal(DBSyncBase, table=True):
    """Treasury withdrawal model for the treasury_withdrawal table.

    Represents treasury withdrawal governance actions that move Ada
    from the treasury to specified stake addresses.
    """

    __tablename__ = "treasury_withdrawal"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    gov_action_proposal_id: int | None = Field(
        default=None,
        sa_column=Column(
            BigInteger, ForeignKey("gov_action_proposal.id"), nullable=False, index=True
        ),
        description="Governance action proposing this withdrawal",
    )

    stake_address_id: int | None = Field(
        default=None,
        sa_column=Column(
            BigInteger, ForeignKey("stake_address.id"), nullable=False, index=True
        ),
        description="Stake address receiving the withdrawal",
    )

    amount: int | None = Field(
        default=None,
        sa_column=Column(LovelaceType, nullable=False),
        description="Amount to withdraw (Lovelace)",
    )


class Constitution(DBSyncBase, table=True):
    """Constitution model for the constitution table.

    Represents the Cardano Constitution and its updates through
    governance actions in the Conway era.
    """

    __tablename__ = "constitution"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    gov_action_proposal_id: int | None = Field(
        default=None,
        sa_column=Column(
            BigInteger, ForeignKey("gov_action_proposal.id"), nullable=False, index=True
        ),
        description="Governance action that established this constitution",
    )

    voting_anchor_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("voting_anchor.id"), nullable=False),
        description="Voting anchor containing constitution text hash",
    )

    script_hash: bytes | None = Field(
        default=None,
        sa_column=Column(Hash28Type),
        description="Optional guardrails script hash",
    )


class VotingAnchor(DBSyncBase, table=True):
    """Voting anchor model for the voting_anchor table.

    Stores metadata anchors for governance actions, votes, and other
    Conway era governance artifacts following CIP-100 standard.
    """

    __tablename__ = "voting_anchor"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    url: str | None = Field(
        default=None,
        sa_column=Column(String(2048), nullable=False),
        description="URL to the metadata content",
    )

    data_hash: bytes | None = Field(
        default=None,
        sa_column=Column(Hash32Type, nullable=False),
        description="Hash of the metadata content (32 bytes)",
    )

    type_: str | None = Field(
        default=None,
        sa_column=Column(String(32), name="type"),
        description="Type of anchor (action, vote, drep, etc.)",
    )


class VotingProcedure(DBSyncBase, table=True):
    """Voting procedure model for the voting_procedure table.

    Tracks votes cast by Constitutional Committee members, DReps, and SPOs
    on governance actions in Conway era.
    """

    __tablename__ = "voting_procedure"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    tx_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("tx.id"), nullable=False, index=True),
        description="Transaction containing this vote",
    )

    index: int | None = Field(
        default=None,
        sa_column=Column(Integer, nullable=False),
        description="Index of this vote within the transaction",
    )

    gov_action_proposal_id: int | None = Field(
        default=None,
        sa_column=Column(
            BigInteger, ForeignKey("gov_action_proposal.id"), nullable=False, index=True
        ),
        description="Governance action being voted on",
    )

    committee_voter: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("committee_hash.id")),
        description="Committee member casting this vote (if applicable)",
    )

    drep_voter: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("drep_hash.id")),
        description="DRep casting this vote (if applicable)",
    )

    pool_voter: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("pool_hash.id")),
        description="SPO casting this vote (if applicable)",
    )

    voter_role: str | None = Field(
        default=None,
        sa_column=Column(String(16), nullable=False),
        description="Role of the voter (ConstitutionalCommittee, DRep, SPO)",
    )

    vote: VoteType | None = Field(
        default=None,
        sa_column=Column(String(16), nullable=False),
        description="Vote cast (Yes, No, Abstain)",
    )

    voting_anchor_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("voting_anchor.id")),
        description="Optional voting anchor for vote justification",
    )


class EpochState(DBSyncBase, table=True):
    """Epoch state model for the epoch_state table.

    Captures governance state snapshots at epoch boundaries including
    committee composition, DRep distributions, and active proposals.
    """

    __tablename__ = "epoch_state"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    committee_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("committee.id")),
        description="Active committee at this epoch",
    )

    no_confidence_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("gov_action_proposal.id")),
        description="Governance action that put system in no confidence state",
    )

    constitution_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("constitution.id")),
        description="Active constitution at this epoch",
    )

    epoch_no: int | None = Field(
        default=None,
        sa_column=Column(Word31Type, nullable=False, unique=True, index=True),
        description="Epoch number for this state snapshot",
    )


# Offchain Governance Metadata Models


class OffChainVoteData(DBSyncBase, table=True):
    """Off-chain vote data model for the off_chain_vote_data table.

    Stores metadata for governance votes following CIP-100 and CIP-119 standards.
    """

    __tablename__ = "off_chain_vote_data"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    voting_anchor_id: int | None = Field(
        default=None,
        sa_column=Column(
            BigInteger, ForeignKey("voting_anchor.id"), nullable=False, unique=True
        ),
        description="Voting anchor containing this metadata",
    )

    hash_: bytes | None = Field(
        default=None,
        sa_column=Column(Hash32Type, nullable=False, name="hash"),
        description="Hash of the vote metadata",
    )

    json_: dict | None = Field(
        default=None,
        sa_column=Column(JSONB, name="json"),
        description="JSON metadata content",
    )

    bytes_: bytes | None = Field(
        default=None,
        sa_column=Column(LargeBinary, name="bytes"),
        description="Raw metadata bytes",
    )

    warning: str | None = Field(
        default=None,
        sa_column=Column(Text),
        description="Validation warnings for this metadata",
    )

    language: str | None = Field(
        default=None,
        sa_column=Column(String(10)),
        description="Language of the metadata content",
    )

    comment: str | None = Field(
        default=None,
        sa_column=Column(Text),
        description="Additional comments about this metadata",
    )

    is_valid: bool | None = Field(
        default=None,
        sa_column=Column(Boolean, default=True),
        description="Whether this metadata is valid according to standards",
    )


class OffChainVoteGovActionData(DBSyncBase, table=True):
    """Off-chain vote governance action data model for the off_chain_vote_gov_action_data table.

    Links governance actions to their associated off-chain metadata.
    """

    __tablename__ = "off_chain_vote_gov_action_data"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    off_chain_vote_data_id: int | None = Field(
        default=None,
        sa_column=Column(
            BigInteger, ForeignKey("off_chain_vote_data.id"), nullable=False, index=True
        ),
        description="Associated off-chain vote data",
    )

    title: str | None = Field(
        default=None,
        sa_column=Column(String(255)),
        description="Title of the governance action",
    )

    abstract: str | None = Field(
        default=None,
        sa_column=Column(Text),
        description="Abstract or summary of the governance action",
    )

    motivation: str | None = Field(
        default=None,
        sa_column=Column(Text),
        description="Motivation for the governance action",
    )

    rationale: str | None = Field(
        default=None,
        sa_column=Column(Text),
        description="Rationale behind the governance action",
    )


class OffChainVoteDrepData(DBSyncBase, table=True):
    """Off-chain vote DRep data model for the off_chain_vote_drep_data table.

    Links DReps to their associated off-chain metadata following CIP-119.
    """

    __tablename__ = "off_chain_vote_drep_data"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    off_chain_vote_data_id: int | None = Field(
        default=None,
        sa_column=Column(
            BigInteger, ForeignKey("off_chain_vote_data.id"), nullable=False, index=True
        ),
        description="Associated off-chain vote data",
    )

    payment_address: str | None = Field(
        default=None,
        sa_column=Column(String(255)),
        description="DRep payment address",
    )

    given_name: str | None = Field(
        default=None,
        sa_column=Column(String(255)),
        description="DRep given name",
    )

    objectives: str | None = Field(
        default=None,
        sa_column=Column(Text),
        description="DRep objectives and goals",
    )

    motivations: str | None = Field(
        default=None,
        sa_column=Column(Text),
        description="DRep motivations for participation",
    )

    qualifications: str | None = Field(
        default=None,
        sa_column=Column(Text),
        description="DRep qualifications and experience",
    )

    image_url: str | None = Field(
        default=None,
        sa_column=Column(String(2048)),
        description="URL to DRep profile image",
    )

    image_hash: str | None = Field(
        default=None,
        sa_column=Column(String(128)),
        description="Hash of DRep profile image",
    )


class OffChainVoteAuthor(DBSyncBase, table=True):
    """Off-chain vote author model for the off_chain_vote_author table.

    Stores author information for governance metadata.
    """

    __tablename__ = "off_chain_vote_author"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    off_chain_vote_data_id: int | None = Field(
        default=None,
        sa_column=Column(
            BigInteger, ForeignKey("off_chain_vote_data.id"), nullable=False, index=True
        ),
        description="Associated off-chain vote data",
    )

    name: str | None = Field(
        default=None,
        sa_column=Column(String(255)),
        description="Author name",
    )

    witness_algorithm: str | None = Field(
        default=None,
        sa_column=Column(String(255)),
        description="Cryptographic algorithm used for witness",
    )

    public_key: str | None = Field(
        default=None,
        sa_column=Column(String(255)),
        description="Public key for author verification",
    )

    signature: str | None = Field(
        default=None,
        sa_column=Column(String(255)),
        description="Cryptographic signature for author verification",
    )

    warning: str | None = Field(
        default=None,
        sa_column=Column(String(255)),
        description="Validation warnings for author information",
    )


class OffChainVoteReference(DBSyncBase, table=True):
    """Off-chain vote reference model for the off_chain_vote_reference table.

    Stores references and citations in governance metadata.
    """

    __tablename__ = "off_chain_vote_reference"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    off_chain_vote_data_id: int | None = Field(
        default=None,
        sa_column=Column(
            BigInteger, ForeignKey("off_chain_vote_data.id"), nullable=False, index=True
        ),
        description="Associated off-chain vote data",
    )

    label: str | None = Field(
        default=None,
        sa_column=Column(String(255), nullable=False),
        description="Reference label or title",
    )

    uri: str | None = Field(
        default=None,
        sa_column=Column(String(2048), nullable=False),
        description="Reference URI",
    )

    hash_digest: bytes | None = Field(
        default=None,
        sa_column=Column(Hash32Type),
        description="Hash of referenced content",
    )

    hash_algorithm: str | None = Field(
        default=None,
        sa_column=Column(String(16)),
        description="Hash algorithm used",
    )


class OffChainVoteExternalUpdate(DBSyncBase, table=True):
    """Off-chain vote external update model for the off_chain_vote_external_update table.

    Tracks external updates and corrections to governance metadata.
    """

    __tablename__ = "off_chain_vote_external_update"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    off_chain_vote_data_id: int | None = Field(
        default=None,
        sa_column=Column(
            BigInteger, ForeignKey("off_chain_vote_data.id"), nullable=False, index=True
        ),
        description="Associated off-chain vote data",
    )

    title: str | None = Field(
        default=None,
        sa_column=Column(String(255)),
        description="Update title",
    )

    uri: str | None = Field(
        default=None,
        sa_column=Column(String(2048)),
        description="URI to update content",
    )


class OffChainVoteFetchError(DBSyncBase, table=True):
    """Off-chain vote fetch error model for the off_chain_vote_fetch_error table.

    Tracks errors encountered when fetching governance metadata from external URLs.
    Committee hash model for tracking constitutional committee members.
    """

    __tablename__ = "off_chain_vote_fetch_error"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    voting_anchor_id: int | None = Field(
        default=None,
        sa_column=Column(
            BigInteger, ForeignKey("voting_anchor.id"), nullable=False, index=True
        ),
        description="Voting anchor that failed to fetch",
    )

    fetch_error: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=False),
        description="Error message describing the fetch failure",
    )

    fetch_time: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=False),
        description="When the fetch was attempted",
    )

    retry_count: int | None = Field(
        default=None,
        sa_column=Column(Integer, nullable=False, default=0),
        description="Number of retry attempts",
    )


# Relationships (defined at the end to avoid circular imports)
DrepHash.registrations = Relationship(back_populates="drep_hash")
DrepHash.distributions = Relationship(back_populates="drep_hash")

DrepRegistration.drep_hash = Relationship(back_populates="registrations")
DrepRegistration.transaction = Relationship()
DrepRegistration.voting_anchor = Relationship()

DrepDistr.drep_hash = Relationship(back_populates="distributions")

CommitteeHash.registrations = Relationship(back_populates="committee_hash")
CommitteeHash.members = Relationship(back_populates="committee_hash")

CommitteeRegistration.committee_hash = Relationship(back_populates="registrations")
CommitteeRegistration.transaction = Relationship()

CommitteeDeRegistration.transaction = Relationship()
CommitteeDeRegistration.voting_anchor = Relationship()

Committee.gov_action_proposal = Relationship()
Committee.members = Relationship(back_populates="committee")
Committee.epoch_states = Relationship(back_populates="committee")

CommitteeMember.committee = Relationship(back_populates="members")
CommitteeMember.committee_hash = Relationship(back_populates="members")

GovActionProposal.transaction = Relationship()
GovActionProposal.return_stake_address = Relationship()
GovActionProposal.voting_anchor = Relationship()
GovActionProposal.param_proposal_ref = Relationship()
GovActionProposal.treasury_withdrawals = Relationship(
    back_populates="gov_action_proposal"
)
GovActionProposal.voting_procedures = Relationship(back_populates="gov_action_proposal")

TreasuryWithdrawal.gov_action_proposal = Relationship(
    back_populates="treasury_withdrawals"
)
TreasuryWithdrawal.stake_address = Relationship()

Constitution.gov_action_proposal = Relationship()
Constitution.voting_anchor = Relationship()
Constitution.epoch_states = Relationship(back_populates="constitution")

VotingAnchor.drep_registrations = Relationship(back_populates="voting_anchor")
VotingAnchor.committee_deregistrations = Relationship(back_populates="voting_anchor")
VotingAnchor.gov_action_proposals = Relationship(back_populates="voting_anchor")
VotingAnchor.voting_procedures = Relationship(back_populates="voting_anchor")
VotingAnchor.constitutions = Relationship(back_populates="voting_anchor")
VotingAnchor.off_chain_vote_data = Relationship(back_populates="voting_anchor")
VotingAnchor.fetch_errors = Relationship(back_populates="voting_anchor")

VotingProcedure.transaction = Relationship()
VotingProcedure.gov_action_proposal = Relationship(back_populates="voting_procedures")
VotingProcedure.committee_voter_ref = Relationship()
VotingProcedure.drep_voter_ref = Relationship()
VotingProcedure.pool_voter_ref = Relationship()
VotingProcedure.voting_anchor = Relationship(back_populates="voting_procedures")

EpochState.committee = Relationship(back_populates="epoch_states")
EpochState.constitution = Relationship(back_populates="epoch_states")

OffChainVoteData.voting_anchor = Relationship(back_populates="off_chain_vote_data")
OffChainVoteData.gov_action_data = Relationship(back_populates="off_chain_vote_data")
OffChainVoteData.drep_data = Relationship(back_populates="off_chain_vote_data")
OffChainVoteData.authors = Relationship(back_populates="off_chain_vote_data")
OffChainVoteData.references = Relationship(back_populates="off_chain_vote_data")
OffChainVoteData.external_updates = Relationship(back_populates="off_chain_vote_data")

OffChainVoteGovActionData.off_chain_vote_data = Relationship(
    back_populates="gov_action_data"
)
OffChainVoteGovActionData.gov_action_proposal = Relationship()

OffChainVoteDrepData.off_chain_vote_data = Relationship(back_populates="drep_data")
OffChainVoteDrepData.drep_hash = Relationship()

OffChainVoteAuthor.off_chain_vote_data = Relationship(back_populates="authors")

OffChainVoteReference.off_chain_vote_data = Relationship(back_populates="references")

OffChainVoteExternalUpdate.off_chain_vote_data = Relationship(
    back_populates="external_updates"
)

OffChainVoteFetchError.voting_anchor = Relationship()
