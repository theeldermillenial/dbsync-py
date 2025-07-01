"""Treasury and reserves models for Cardano DB Sync.

This module contains models for treasury operations, reserve payments,
pot transfers, and ADA distribution tracking.
"""

from __future__ import annotations

from sqlalchemy import BigInteger, Column, ForeignKey, Integer
from sqlmodel import Field

from ..utils.types import Int65Type, LovelaceType, Word31Type, Word63Type
from .base import DBSyncBase

__all__ = [
    "AdaPots",
    "PotTransfer",
    "Treasury",
]


class Treasury(DBSyncBase, table=True):
    """Treasury payment model representing payments from the treasury to stake addresses.

    Maps to the 'treasury' table in Cardano DB Sync.
    Tracks treasury payments to stake addresses for protocol governance rewards.

    Note: Before protocol version 5.0 (Alonzo), if more than one payment was made
    to a stake address in a single epoch, only the last payment was kept and
    earlier ones removed. For protocol version 5.0 and later, they are summed
    and produce a single reward with type 'treasury'.

    Attributes:
        id_: Primary key
        addr_id: Foreign key to StakeAddress table
        cert_index: Index of payment certificate within transaction certificates
        amount: Payment amount in Lovelace (can be large, uses int65type)
        tx_id: Foreign key to transaction containing this payment

    References:
        - Cardano Ledger: Treasury management and payments
        - Governance: Protocol treasury distributions
    """

    __tablename__ = "treasury"

    id_: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, name="id")
    )
    addr_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("stake_address.id"), nullable=False)
    )
    cert_index: int = Field(sa_column=Column(Integer, nullable=False))
    amount: int = Field(sa_column=Column(Int65Type, nullable=False))
    tx_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("tx.id"), nullable=False)
    )

    @property
    def amount_ada(self) -> float:
        """Get treasury payment amount in ADA."""
        return self.amount / 1_000_000

    @property
    def is_large_payment(self) -> bool:
        """Check if this is a large treasury payment (>1M ADA)."""
        return self.amount > 1_000_000_000_000  # 1M ADA in lovelace

    def to_reward_record(self) -> dict:
        """Convert to reward record format.

        Returns:
            Dictionary with reward record information
        """
        return {
            "type": "treasury",
            "address_id": self.addr_id,
            "amount": self.amount,
            "amount_ada": self.amount_ada,
            "tx_id": self.tx_id,
            "cert_index": self.cert_index,
        }


class PotTransfer(DBSyncBase, table=True):
    """Pot transfer model representing transfers between treasury and reserves pots.

    Maps to the 'pot_transfer' table in Cardano DB Sync.
    Tracks transfers of ADA between the treasury pot and reserves pot,
    typically used for protocol governance operations.

    Attributes:
        id_: Primary key
        cert_index: Index of transfer certificate within transaction certificates
        treasury: Amount the treasury balance changes by (can be positive or negative)
        reserves: Amount the reserves balance changes by (can be positive or negative)
        tx_id: Foreign key to transaction containing this transfer

    References:
        - Cardano Ledger: Treasury and reserves pot management
        - Governance: Protocol fund transfers and allocations
    """

    __tablename__ = "pot_transfer"

    id_: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, name="id")
    )
    cert_index: int = Field(sa_column=Column(Integer, nullable=False))
    treasury: int = Field(sa_column=Column(Int65Type, nullable=False))
    reserves: int = Field(sa_column=Column(Int65Type, nullable=False))
    tx_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("tx.id"), nullable=False)
    )

    @property
    def treasury_ada(self) -> float:
        """Get treasury change amount in ADA."""
        return self.treasury / 1_000_000

    @property
    def reserves_ada(self) -> float:
        """Get reserves change amount in ADA."""
        return self.reserves / 1_000_000

    @property
    def transfer_direction(self) -> str:
        """Get transfer direction as string.

        Returns:
            "treasury_to_reserves", "reserves_to_treasury", or "balanced"
        """
        if self.treasury > 0 and self.reserves < 0:
            return "reserves_to_treasury"
        elif self.treasury < 0 and self.reserves > 0:
            return "treasury_to_reserves"
        else:
            return "balanced"

    @property
    def total_amount_transferred(self) -> int:
        """Get the absolute amount transferred (always positive)."""
        return max(abs(self.treasury), abs(self.reserves))

    @property
    def total_amount_transferred_ada(self) -> float:
        """Get the absolute amount transferred in ADA."""
        return self.total_amount_transferred / 1_000_000

    def is_treasury_to_reserves(self) -> bool:
        """Check if this is a transfer from treasury to reserves."""
        return self.treasury < 0 and self.reserves > 0

    def is_reserves_to_treasury(self) -> bool:
        """Check if this is a transfer from reserves to treasury."""
        return self.treasury > 0 and self.reserves < 0


class AdaPots(DBSyncBase, table=True):
    """ADA pots model representing the distribution of all ADA across different protocol pots.

    Maps to the 'ada_pots' table in Cardano DB Sync.
    Provides a snapshot of ADA distribution across treasury, reserves, rewards, UTxO,
    deposits, and fees at specific blocks/epochs.

    The treasury and rewards fields are correct for the whole epoch, but all other
    fields change block by block during Shelley and later eras.

    Attributes:
        id_: Primary key
        slot_no: Slot number where this snapshot was taken
        epoch_no: Epoch number where this snapshot was taken
        treasury: Amount in Lovelace in the treasury pot
        reserves: Amount in Lovelace in the reserves pot
        rewards: Amount in Lovelace in the rewards pot
        utxo: Amount in Lovelace in the UTxO set
        deposits_stake: Amount in Lovelace from stake key and pool deposits
        deposits_drep: Amount in Lovelace from DRep registration deposits (Conway era)
        deposits_proposal: Amount in Lovelace from governance proposal deposits (Conway era)
        fees: Amount in Lovelace in the fee pot
        block_id: Foreign key to block where this snapshot was taken

    References:
        - Cardano Ledger: ADA supply tracking and accounting
        - Protocol: Treasury, reserves, and rewards management
        - Conway Era: Governance deposit tracking
    """

    __tablename__ = "ada_pots"

    id_: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, name="id")
    )
    slot_no: int = Field(sa_column=Column(Word63Type, nullable=False))
    epoch_no: int = Field(sa_column=Column(Word31Type, nullable=False))
    treasury: int = Field(sa_column=Column(LovelaceType, nullable=False))
    reserves: int = Field(sa_column=Column(LovelaceType, nullable=False))
    rewards: int = Field(sa_column=Column(LovelaceType, nullable=False))
    utxo: int = Field(sa_column=Column(LovelaceType, nullable=False))
    deposits_stake: int = Field(sa_column=Column(LovelaceType, nullable=False))
    deposits_drep: int = Field(sa_column=Column(LovelaceType, nullable=False))
    deposits_proposal: int = Field(sa_column=Column(LovelaceType, nullable=False))
    fees: int = Field(sa_column=Column(LovelaceType, nullable=False))
    block_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("block.id"), nullable=False)
    )

    @property
    def total_supply(self) -> int:
        """Calculate total ADA supply from all pots.

        Returns:
            Total ADA supply in Lovelace
        """
        return (
            self.treasury
            + self.reserves
            + self.rewards
            + self.utxo
            + self.deposits_stake
            + self.deposits_drep
            + self.deposits_proposal
            + self.fees
        )

    @property
    def total_supply_ada(self) -> float:
        """Calculate total ADA supply in ADA units."""
        return self.total_supply / 1_000_000

    @property
    def circulating_supply(self) -> int:
        """Calculate circulating ADA supply (UTxO + rewards).

        Returns:
            Circulating supply in Lovelace (excludes treasury, reserves, deposits, fees)
        """
        return self.utxo + self.rewards

    @property
    def circulating_supply_ada(self) -> float:
        """Calculate circulating ADA supply in ADA units."""
        return self.circulating_supply / 1_000_000

    @property
    def total_deposits(self) -> int:
        """Calculate total deposits across all deposit types.

        Returns:
            Total deposits in Lovelace
        """
        return self.deposits_stake + self.deposits_drep + self.deposits_proposal

    @property
    def total_deposits_ada(self) -> float:
        """Calculate total deposits in ADA units."""
        return self.total_deposits / 1_000_000

    def get_distribution_summary(self) -> dict:
        """Get ADA distribution summary across all pots.

        Returns:
            Dictionary with ADA distribution information
        """
        total = self.total_supply
        if total == 0:
            return {}

        return {
            "total_supply_ada": self.total_supply_ada,
            "circulating_supply_ada": self.circulating_supply_ada,
            "treasury_ada": self.treasury / 1_000_000,
            "reserves_ada": self.reserves / 1_000_000,
            "rewards_ada": self.rewards / 1_000_000,
            "utxo_ada": self.utxo / 1_000_000,
            "total_deposits_ada": self.total_deposits_ada,
            "fees_ada": self.fees / 1_000_000,
            "treasury_percentage": (self.treasury / total) * 100,
            "reserves_percentage": (self.reserves / total) * 100,
            "utxo_percentage": (self.utxo / total) * 100,
            "epoch_no": self.epoch_no,
            "slot_no": self.slot_no,
        }

    def get_pot_balance(self, pot_name: str) -> int:
        """Get balance for a specific pot by name.

        Args:
            pot_name: Name of the pot ("treasury", "reserves", "rewards", etc.)

        Returns:
            Balance in Lovelace, or 0 if pot name is invalid
        """
        pot_mapping = {
            "treasury": self.treasury,
            "reserves": self.reserves,
            "rewards": self.rewards,
            "utxo": self.utxo,
            "deposits_stake": self.deposits_stake,
            "deposits_drep": self.deposits_drep,
            "deposits_proposal": self.deposits_proposal,
            "fees": self.fees,
        }
        return pot_mapping.get(pot_name, 0)

    def get_pot_balance_ada(self, pot_name: str) -> float:
        """Get balance for a specific pot by name in ADA units.

        Args:
            pot_name: Name of the pot

        Returns:
            Balance in ADA
        """
        return self.get_pot_balance(pot_name) / 1_000_000


# Relationships will be added when circular import issues are resolved
