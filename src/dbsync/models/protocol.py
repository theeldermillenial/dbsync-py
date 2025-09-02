"""Protocol parameter models for Cardano DB Sync.

This module contains models for protocol parameter management including parameter
proposals, active epoch parameters, and reward calculations.
Protocol parameter and epoch configuration models.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import BigInteger, Column, Double, Enum, ForeignKey, Integer, Numeric
from sqlmodel import Field

from ..utils.types import Hash32Type
from .base import DBSyncBase

__all__ = [
    "EpochParam",
    "ParamProposal",
    "RewardRest",
]

# Define the rewardtype enum values
REWARD_TYPES = ["leader", "member", "reserves", "treasury", "refund", "proposal_refund"]


class ParamProposal(DBSyncBase, table=True):
    """Parameter proposal model for the param_proposal table.

    Represents protocol parameter change proposals submitted to the network.
    """

    __tablename__ = "param_proposal"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    epoch_no: int | None = Field(
        default=None,
        sa_column=Column(Integer, index=True),
        description="Epoch number when proposal was submitted",
    )

    key: bytes | None = Field(
        default=None,
        sa_column=Column(Hash32Type, index=True),
        description="Genesis key hash that submitted this proposal",
    )

    min_fee_a: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="Proposed minimum fee coefficient A",
    )

    min_fee_b: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="Proposed minimum fee coefficient B",
    )

    max_block_size: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="Proposed maximum block size",
    )

    max_tx_size: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="Proposed maximum transaction size",
    )

    max_bh_size: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="Proposed maximum block header size",
    )

    key_deposit: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="Proposed key deposit amount",
    )

    pool_deposit: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="Proposed pool deposit amount",
    )

    max_epoch: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="Proposed maximum epoch for pool retirement",
    )

    optimal_pool_count: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="Proposed optimal number of pools (k parameter)",
    )

    influence: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="Proposed influence factor (a0 parameter)",
    )

    monetary_expand_rate: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="Proposed monetary expansion rate (rho parameter)",
    )

    treasury_growth_rate: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="Proposed treasury growth rate (tau parameter)",
    )

    decentralisation: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="Proposed decentralisation parameter",
    )

    entropy: bytes | None = Field(
        default=None,
        sa_column=Column(Hash32Type),
        description="Proposed extra entropy for randomness",
    )

    protocol_major: int | None = Field(
        default=None,
        sa_column=Column(Integer),
        description="Proposed protocol major version",
    )

    protocol_minor: int | None = Field(
        default=None,
        sa_column=Column(Integer),
        description="Proposed protocol minor version",
    )

    min_utxo_value: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="Proposed minimum UTxO value",
    )

    min_pool_cost: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="Proposed minimum pool cost",
    )

    # Cost model parameters (Alonzo era and later)
    cost_model_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("cost_model.id")),
        description="Reference to cost model for script execution",
    )

    price_mem: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="Proposed price per unit of memory",
    )

    price_step: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="Proposed price per execution step",
    )

    max_tx_ex_mem: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="Proposed maximum transaction execution memory",
    )

    max_tx_ex_steps: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="Proposed maximum transaction execution steps",
    )

    max_block_ex_mem: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="Proposed maximum block execution memory",
    )

    max_block_ex_steps: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="Proposed maximum block execution steps",
    )

    max_val_size: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="Proposed maximum value size",
    )

    collateral_percent: int | None = Field(
        default=None,
        sa_column=Column(Integer),
        description="Proposed collateral percentage",
    )

    max_collateral_inputs: int | None = Field(
        default=None,
        sa_column=Column(Integer),
        description="Proposed maximum collateral inputs",
    )

    registered_tx_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("tx.id"), nullable=False, index=True),
        description="Transaction that registered this proposal",
    )

    # Conway era governance fields
    coins_per_utxo_size: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="Proposed coins per UTxO size",
    )

    pvt_motion_no_confidence: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="Pool voting threshold for motion of no confidence",
    )

    pvt_committee_normal: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="Pool voting threshold for committee normal",
    )

    pvt_committee_no_confidence: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="Pool voting threshold for committee no confidence",
    )

    pvt_hard_fork_initiation: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="Pool voting threshold for hard fork initiation",
    )

    dvt_motion_no_confidence: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="DRep voting threshold for motion of no confidence",
    )

    dvt_committee_normal: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="DRep voting threshold for committee normal",
    )

    dvt_committee_no_confidence: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="DRep voting threshold for committee no confidence",
    )

    dvt_update_to_constitution: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="DRep voting threshold for constitution update",
    )

    dvt_hard_fork_initiation: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="DRep voting threshold for hard fork initiation",
    )

    dvt_p_p_network_group: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="DRep voting threshold for protocol parameter network group",
    )

    dvt_p_p_economic_group: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="DRep voting threshold for protocol parameter economic group",
    )

    dvt_p_p_technical_group: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="DRep voting threshold for protocol parameter technical group",
    )

    dvt_p_p_gov_group: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="DRep voting threshold for protocol parameter governance group",
    )

    dvt_treasury_withdrawal: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="DRep voting threshold for treasury withdrawal",
    )

    committee_min_size: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="Proposed minimum committee size",
    )

    committee_max_term_length: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="Proposed maximum committee term length",
    )

    gov_action_lifetime: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="Proposed governance action lifetime",
    )

    gov_action_deposit: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="Proposed governance action deposit",
    )

    drep_deposit: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="Proposed DRep deposit amount",
    )

    drep_activity: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="Proposed DRep activity period",
    )

    pvtpp_security_group: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="Pool voting threshold for protocol parameter security group",
    )

    min_fee_ref_script_cost_per_byte: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="Proposed minimum fee reference script cost per byte",
    )

    def get_proposal_summary(self) -> dict[str, Any]:
        """Get a summary of the proposed parameter changes.

        Returns:
            Dictionary containing non-null proposed parameters
        """
        summary = {}

        # Core fee parameters
        if self.min_fee_a is not None:
            summary["min_fee_a"] = self.min_fee_a
        if self.min_fee_b is not None:
            summary["min_fee_b"] = self.min_fee_b

        # Size limits
        if self.max_block_size is not None:
            summary["max_block_size"] = self.max_block_size
        if self.max_tx_size is not None:
            summary["max_tx_size"] = self.max_tx_size

        # Deposits
        if self.key_deposit is not None:
            summary["key_deposit"] = self.key_deposit
        if self.pool_deposit is not None:
            summary["pool_deposit"] = self.pool_deposit

        # Staking parameters
        if self.optimal_pool_count is not None:
            summary["optimal_pool_count"] = self.optimal_pool_count
        if self.influence is not None:
            summary["influence"] = float(self.influence)
        if self.min_pool_cost is not None:
            summary["min_pool_cost"] = self.min_pool_cost

        # Protocol version
        if self.protocol_major is not None or self.protocol_minor is not None:
            summary["protocol_version"] = {
                "major": self.protocol_major,
                "minor": self.protocol_minor,
            }

        return summary

    def is_hard_fork_proposal(self) -> bool:
        """Check if this proposal includes a hard fork (major protocol version change).

        Returns:
            True if this proposal changes the major protocol version
        """
        return self.protocol_major is not None


class EpochParam(DBSyncBase, table=True):
    """Epoch parameter model for the epoch_param table.

    Represents the active protocol parameters for each epoch.
    """

    __tablename__ = "epoch_param"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    epoch_no: int | None = Field(
        default=None,
        sa_column=Column(Integer, unique=True, nullable=False, index=True),
        description="Epoch number",
    )

    min_fee_a: int | None = Field(
        default=None,
        sa_column=Column(Integer, nullable=False),
        description="Minimum fee coefficient A",
    )

    min_fee_b: int | None = Field(
        default=None,
        sa_column=Column(Integer, nullable=False),
        description="Minimum fee coefficient B",
    )

    max_block_size: int | None = Field(
        default=None,
        sa_column=Column(Integer, nullable=False),
        description="Maximum block size",
    )

    max_tx_size: int | None = Field(
        default=None,
        sa_column=Column(Integer, nullable=False),
        description="Maximum transaction size",
    )

    max_bh_size: int | None = Field(
        default=None,
        sa_column=Column(Integer, nullable=False),
        description="Maximum block header size",
    )

    key_deposit: int | None = Field(
        default=None,
        sa_column=Column(Numeric, nullable=False),
        description="Key deposit amount",
    )

    pool_deposit: int | None = Field(
        default=None,
        sa_column=Column(Numeric, nullable=False),
        description="Pool deposit amount",
    )

    max_epoch: int | None = Field(
        default=None,
        sa_column=Column(Integer, nullable=False),
        description="Maximum epoch for pool retirement",
    )

    optimal_pool_count: int | None = Field(
        default=None,
        sa_column=Column(Integer, nullable=False),
        description="Optimal number of pools (k parameter)",
    )

    influence: Decimal | None = Field(
        default=None,
        sa_column=Column(Double, nullable=False),
        description="Influence factor (a0 parameter)",
    )

    monetary_expand_rate: Decimal | None = Field(
        default=None,
        sa_column=Column(Double, nullable=False),
        description="Monetary expansion rate (rho parameter)",
    )

    treasury_growth_rate: Decimal | None = Field(
        default=None,
        sa_column=Column(Double, nullable=False),
        description="Treasury growth rate (tau parameter)",
    )

    decentralisation: Decimal | None = Field(
        default=None,
        sa_column=Column(Double, nullable=False),
        description="Decentralisation parameter",
    )

    nonce: bytes | None = Field(
        default=None,
        sa_column=Column(Hash32Type),
        description="Nonce for randomness",
    )

    extra_entropy: bytes | None = Field(
        default=None,
        sa_column=Column(Hash32Type),
        description="Additional entropy for randomness",
    )

    protocol_major: int | None = Field(
        default=None,
        sa_column=Column(Integer, nullable=False),
        description="Protocol major version",
    )

    protocol_minor: int | None = Field(
        default=None,
        sa_column=Column(Integer, nullable=False),
        description="Protocol minor version",
    )

    min_utxo_value: int | None = Field(
        default=None,
        sa_column=Column(Numeric, nullable=False),
        description="Minimum UTxO value",
    )

    min_pool_cost: int | None = Field(
        default=None,
        sa_column=Column(Numeric, nullable=False),
        description="Minimum pool cost",
    )

    # Cost model parameters (Alonzo era and later)
    cost_model_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("cost_model.id")),
        description="Reference to cost model for script execution",
    )

    price_mem: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="Price per unit of memory",
    )

    price_step: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="Price per execution step",
    )

    max_tx_ex_mem: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="Maximum transaction execution memory",
    )

    max_tx_ex_steps: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="Maximum transaction execution steps",
    )

    max_block_ex_mem: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="Maximum block execution memory",
    )

    max_block_ex_steps: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="Maximum block execution steps",
    )

    max_val_size: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="Maximum value size",
    )

    collateral_percent: int | None = Field(
        default=None,
        sa_column=Column(Integer),
        description="Collateral percentage",
    )

    max_collateral_inputs: int | None = Field(
        default=None,
        sa_column=Column(Integer),
        description="Maximum collateral inputs",
    )

    block_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("block.id"), nullable=False, index=True),
        description="Block where these parameters became active",
    )

    # Conway era governance fields
    coins_per_utxo_size: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="Coins per UTxO size",
    )

    pvt_motion_no_confidence: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="Pool voting threshold for motion of no confidence",
    )

    pvt_committee_normal: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="Pool voting threshold for committee normal",
    )

    pvt_committee_no_confidence: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="Pool voting threshold for committee no confidence",
    )

    pvt_hard_fork_initiation: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="Pool voting threshold for hard fork initiation",
    )

    dvt_motion_no_confidence: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="DRep voting threshold for motion of no confidence",
    )

    dvt_committee_normal: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="DRep voting threshold for committee normal",
    )

    dvt_committee_no_confidence: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="DRep voting threshold for committee no confidence",
    )

    dvt_update_to_constitution: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="DRep voting threshold for constitution update",
    )

    dvt_hard_fork_initiation: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="DRep voting threshold for hard fork initiation",
    )

    dvt_p_p_network_group: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="DRep voting threshold for protocol parameter network group",
    )

    dvt_p_p_economic_group: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="DRep voting threshold for protocol parameter economic group",
    )

    dvt_p_p_technical_group: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="DRep voting threshold for protocol parameter technical group",
    )

    dvt_p_p_gov_group: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="DRep voting threshold for protocol parameter governance group",
    )

    dvt_treasury_withdrawal: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="DRep voting threshold for treasury withdrawal",
    )

    committee_min_size: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="Minimum committee size",
    )

    committee_max_term_length: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="Maximum committee term length",
    )

    gov_action_lifetime: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="Governance action lifetime",
    )

    gov_action_deposit: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="Governance action deposit",
    )

    drep_deposit: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="DRep deposit amount",
    )

    drep_activity: int | None = Field(
        default=None,
        sa_column=Column(Numeric),
        description="DRep activity period",
    )

    pvtpp_security_group: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="Pool voting threshold for protocol parameter security group",
    )

    min_fee_ref_script_cost_per_byte: Decimal | None = Field(
        default=None,
        sa_column=Column(Double),
        description="Minimum fee reference script cost per byte",
    )

    def calculate_min_fee(self, tx_size: int) -> int:
        """Calculate minimum fee for a transaction of given size.

        Args:
            tx_size: Transaction size in bytes

        Returns:
            Minimum fee in lovelace
        """
        if self.min_fee_a is None or self.min_fee_b is None:
            raise ValueError("Fee parameters not set")

        return self.min_fee_a * tx_size + self.min_fee_b

    def get_protocol_version(self) -> dict[str, int | None]:
        """Get protocol version information.

        Returns:
            Dictionary with major and minor version numbers
        """
        return {"major": self.protocol_major, "minor": self.protocol_minor}

    def get_size_limits(self) -> dict[str, int | None]:
        """Get size limit parameters.

        Returns:
            Dictionary with size limits
        """
        return {
            "max_block_size": self.max_block_size,
            "max_tx_size": self.max_tx_size,
            "max_bh_size": self.max_bh_size,
            "max_val_size": self.max_val_size,
        }

    def get_economic_params(self) -> dict[str, Any]:
        """Get economic parameters.

        Returns:
            Dictionary with economic parameters
        """
        return {
            "monetary_expand_rate": (
                float(self.monetary_expand_rate)
                if self.monetary_expand_rate is not None
                else None
            ),
            "treasury_growth_rate": (
                float(self.treasury_growth_rate)
                if self.treasury_growth_rate is not None
                else None
            ),
            "influence": float(self.influence) if self.influence is not None else None,
            "optimal_pool_count": self.optimal_pool_count,
            "min_pool_cost": self.min_pool_cost,
            "decentralisation": (
                float(self.decentralisation)
                if self.decentralisation is not None
                else None
            ),
        }

    def is_fully_decentralized(self) -> bool:
        """Check if the network is fully decentralized.

        Returns:
            True if decentralisation parameter is 0
        """
        return self.decentralisation is not None and self.decentralisation == 0


class RewardRest(DBSyncBase, table=True):
    """Reward rest model for the reward_rest table.

    Represents remaining reward calculations and distributions.
    Note: This table has no primary key in the database schema.
    """

    __tablename__ = "reward_rest"

    addr_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("stake_address.id"), nullable=False, primary_key=True),
        description="Stake address receiving the reward",
    )

    type_: str | None = Field(
        default=None,
        sa_column=Column(
            Enum(*REWARD_TYPES, name="rewardtype"), nullable=False, name="type", primary_key=True
        ),
        description="Type of reward rest calculation",
    )

    amount: int | None = Field(
        default=None,
        sa_column=Column(Numeric, nullable=False),
        description="Remaining reward amount (lovelace)",
    )

    earned_epoch: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, nullable=False, primary_key=True),
        description="Epoch when the reward was earned",
    )

    spendable_epoch: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, nullable=False, primary_key=True),
        description="Epoch when the reward becomes spendable",
    )

    # Conversion properties
    @property
    def amount_ada(self) -> float:
        """Get reward amount in ADA.

        Returns:
            Amount in ADA (amount / 1,000,000)
        """
        if self.amount is None:
            return 0.0
        return float(self.amount) / 1_000_000

    def is_spendable_in_epoch(self, epoch_no: int) -> bool:
        """Check if reward is spendable in given epoch.

        Args:
            epoch_no: Epoch number to check

        Returns:
            True if reward is spendable in the given epoch
        """
        if self.spendable_epoch is None:
            return False
        return epoch_no >= self.spendable_epoch

    def epochs_until_spendable(self, current_epoch: int) -> int:
        """Calculate epochs until reward becomes spendable.

        Args:
            current_epoch: Current epoch number

        Returns:
            Number of epochs until spendable (0 if already spendable)
        """
        if self.spendable_epoch is None:
            return 0
        epochs_remaining = self.spendable_epoch - current_epoch
        return max(0, epochs_remaining)

    def get_reward_info(self) -> dict[str, Any]:
        """Get comprehensive reward information.

        Returns:
            Dictionary with reward details
        """
        return {
            "type": self.type_,
            "amount_lovelace": self.amount,
            "amount_ada": self.amount_ada,
            "earned_epoch": self.earned_epoch,
            "spendable_epoch": self.spendable_epoch,
            "addr_id": self.addr_id,
        }
