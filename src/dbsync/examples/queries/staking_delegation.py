"""Staking & Delegation Patterns Query Examples.

This example demonstrates how to use the dbsync-py package to implement
staking and delegation analysis queries.
"""

from typing import Any

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ...models import (
    Block,
    Delegation,
    EpochStake,
    Reward,
    StakeAddress,
    StakeDeregistration,
    StakeRegistration,
)


class StakingDelegationQueries:
    """Example staking and delegation pattern queries."""

    @staticmethod
    def get_delegation_history(
        session: Session | AsyncSession, stake_address: str, limit: int = 50
    ) -> dict[str, Any]:
        """Get delegation history for a specific stake address."""
        if isinstance(session, AsyncSession):
            raise NotImplementedError("Async version not yet implemented")

        # Get stake address record
        stake_addr = session.execute(
            select(StakeAddress).where(StakeAddress.view == stake_address)
        ).first()

        if not stake_addr:
            return {
                "found": False,
                "stake_address": stake_address,
                "error": "Stake address not found",
            }

        stake_addr = stake_addr[0]

        # Get delegation history
        delegation_stmt = (
            select(
                Delegation.active_epoch_no, Delegation.pool_hash_id, Delegation.tx_id
            )
            .where(Delegation.addr_id == stake_addr.id_)
            .order_by(desc(Delegation.active_epoch_no))
            .limit(limit)
        )

        delegations = session.execute(delegation_stmt).all()

        delegation_history = []
        for row in delegations:
            delegation_history.append(
                {
                    "epoch": row.active_epoch_no,
                    "pool_hash_id": row.pool_hash_id,
                    "tx_id": row.tx_id,
                }
            )

        return {
            "found": True,
            "stake_address": stake_address,
            "total_delegations": len(delegation_history),
            "delegation_history": delegation_history,
        }

    @staticmethod
    def get_stake_distribution_patterns(
        session: Session | AsyncSession, epoch_no: int | None = None, limit: int = 20
    ) -> dict[str, Any]:
        """Analyze stake distribution patterns across pools."""
        if isinstance(session, AsyncSession):
            raise NotImplementedError("Async version not yet implemented")

        # Get latest epoch if not specified
        if epoch_no is None:
            latest_epoch = session.execute(select(func.max(Block.epoch_no))).scalar()
            epoch_no = latest_epoch

        if not epoch_no:
            return {
                "found": False,
                "error": "No epoch data available",
            }

        # Get stake distribution
        stake_stmt = (
            select(
                EpochStake.pool_id,
                func.sum(EpochStake.amount).label("total_stake"),
                func.count(EpochStake.addr_id).label("delegator_count"),
            )
            .where(EpochStake.epoch_no == epoch_no)
            .group_by(EpochStake.pool_id)
            .order_by(desc(func.sum(EpochStake.amount)))
            .limit(limit)
        )

        stakes = session.execute(stake_stmt).all()

        # Calculate total stake for percentages
        total_stake = (
            session.execute(
                select(func.sum(EpochStake.amount)).where(
                    EpochStake.epoch_no == epoch_no
                )
            ).scalar()
            or 0
        )

        distribution = []
        for row in stakes:
            stake_amount = int(row.total_stake or 0)
            percentage = (stake_amount / total_stake * 100) if total_stake > 0 else 0

            distribution.append(
                {
                    "pool_id": row.pool_id,
                    "stake": stake_amount,
                    "stake_ada": stake_amount / 1_000_000,
                    "stake_percentage": percentage,
                    "delegator_count": int(row.delegator_count or 0),
                }
            )

        return {
            "found": True,
            "epoch": epoch_no,
            "total_stake": int(total_stake),
            "total_stake_ada": total_stake / 1_000_000,
            "pools_analyzed": len(distribution),
            "distribution": distribution,
        }

    @staticmethod
    def get_delegation_lifecycle(
        session: Session | AsyncSession, stake_address: str
    ) -> dict[str, Any]:
        """Track complete delegation lifecycle for a stake address."""
        if isinstance(session, AsyncSession):
            raise NotImplementedError("Async version not yet implemented")

        # Get stake address record
        stake_addr = session.execute(
            select(StakeAddress).where(StakeAddress.view == stake_address)
        ).first()

        if not stake_addr:
            return {
                "found": False,
                "stake_address": stake_address,
                "error": "Stake address not found",
            }

        stake_addr = stake_addr[0]

        # Get registration
        registration = session.execute(
            select(StakeRegistration.tx_id, StakeRegistration.cert_index)
            .where(StakeRegistration.addr_id == stake_addr.id_)
            .order_by(StakeRegistration.tx_id)
            .limit(1)
        ).first()

        # Get deregistration
        deregistration = session.execute(
            select(StakeDeregistration.tx_id, StakeDeregistration.cert_index)
            .where(StakeDeregistration.addr_id == stake_addr.id_)
            .order_by(desc(StakeDeregistration.tx_id))
            .limit(1)
        ).first()

        # Get current delegation
        current_delegation = session.execute(
            select(Delegation.active_epoch_no, Delegation.pool_hash_id)
            .where(Delegation.addr_id == stake_addr.id_)
            .order_by(desc(Delegation.active_epoch_no))
            .limit(1)
        ).first()

        # Get current stake
        current_stake = (
            session.execute(
                select(func.sum(EpochStake.amount))
                .where(EpochStake.addr_id == stake_addr.id_)
                .order_by(desc(EpochStake.epoch_no))
                .limit(1)
            ).scalar()
            or 0
        )

        return {
            "found": True,
            "stake_address": stake_address,
            "registration": {
                "tx_id": registration.tx_id if registration else None,
                "cert_index": registration.cert_index if registration else None,
            },
            "deregistration": {
                "tx_id": deregistration.tx_id if deregistration else None,
                "cert_index": deregistration.cert_index if deregistration else None,
            },
            "current_delegation": {
                "epoch": current_delegation.active_epoch_no
                if current_delegation
                else None,
                "pool_hash_id": current_delegation.pool_hash_id
                if current_delegation
                else None,
            },
            "current_stake": int(current_stake),
            "current_stake_ada": current_stake / 1_000_000,
            "is_active": current_delegation is not None and deregistration is None,
        }

    @staticmethod
    def get_reward_earning_patterns(
        session: Session | AsyncSession, stake_address: str, epochs: int = 10
    ) -> dict[str, Any]:
        """Analyze reward earning patterns for a stake address."""
        if isinstance(session, AsyncSession):
            raise NotImplementedError("Async version not yet implemented")

        # Get stake address record
        stake_addr = session.execute(
            select(StakeAddress).where(StakeAddress.view == stake_address)
        ).first()

        if not stake_addr:
            return {
                "found": False,
                "stake_address": stake_address,
                "error": "Stake address not found",
            }

        stake_addr = stake_addr[0]

        # Get latest epoch
        latest_epoch = session.execute(select(func.max(Block.epoch_no))).scalar()

        if not latest_epoch:
            return {
                "found": False,
                "error": "No epoch data available",
            }

        start_epoch = latest_epoch - epochs + 1

        # Get reward history
        rewards_stmt = (
            select(
                Reward.earned_epoch,
                Reward.type_,
                func.sum(Reward.amount).label("total_amount"),
            )
            .where(
                and_(
                    Reward.addr_id == stake_addr.id_, Reward.earned_epoch >= start_epoch
                )
            )
            .group_by(Reward.earned_epoch, Reward.type_)
            .order_by(Reward.earned_epoch, Reward.type_)
        )

        rewards_data = session.execute(rewards_stmt).all()

        # Process rewards by epoch
        rewards_by_epoch = {}
        total_rewards = 0

        for row in rewards_data:
            epoch = row.earned_epoch
            reward_type = row.type_
            amount = int(row.total_amount or 0)
            total_rewards += amount

            if epoch not in rewards_by_epoch:
                rewards_by_epoch[epoch] = {
                    "epoch": epoch,
                    "total_rewards": 0,
                    "by_type": {},
                }

            rewards_by_epoch[epoch]["total_rewards"] += amount
            rewards_by_epoch[epoch]["by_type"][reward_type] = amount

        # Convert to list
        rewards_history = list(rewards_by_epoch.values())
        rewards_history.sort(key=lambda x: x["epoch"])

        return {
            "found": True,
            "stake_address": stake_address,
            "epochs_analyzed": epochs,
            "epoch_range": f"{start_epoch}-{latest_epoch}",
            "total_rewards": total_rewards,
            "total_rewards_ada": total_rewards / 1_000_000,
            "average_per_epoch": total_rewards / epochs if epochs > 0 else 0,
            "rewards_history": rewards_history,
        }

    @staticmethod
    def get_active_stake_monitoring(
        session: Session | AsyncSession, epoch_no: int | None = None
    ) -> dict[str, Any]:
        """Monitor current active stake status and metrics."""
        if isinstance(session, AsyncSession):
            raise NotImplementedError("Async version not yet implemented")

        # Get latest epoch if not specified
        if epoch_no is None:
            epoch_no = session.execute(select(func.max(Block.epoch_no))).scalar()

        if not epoch_no:
            return {
                "found": False,
                "error": "No epoch data available",
            }

        # Get total active stake
        total_stake = (
            session.execute(
                select(func.sum(EpochStake.amount)).where(
                    EpochStake.epoch_no == epoch_no
                )
            ).scalar()
            or 0
        )

        # Get active delegator count
        active_delegators = (
            session.execute(
                select(func.count(func.distinct(EpochStake.addr_id))).where(
                    EpochStake.epoch_no == epoch_no
                )
            ).scalar()
            or 0
        )

        # Get active pools count
        active_pools = (
            session.execute(
                select(func.count(func.distinct(EpochStake.pool_id))).where(
                    EpochStake.epoch_no == epoch_no
                )
            ).scalar()
            or 0
        )

        # Get average stake per delegator
        avg_stake = total_stake / active_delegators if active_delegators > 0 else 0

        # Get largest single stake
        largest_stake = (
            session.execute(
                select(func.max(EpochStake.amount)).where(
                    EpochStake.epoch_no == epoch_no
                )
            ).scalar()
            or 0
        )

        return {
            "found": True,
            "epoch": epoch_no,
            "total_active_stake": int(total_stake),
            "total_active_stake_ada": total_stake / 1_000_000,
            "active_delegators": int(active_delegators),
            "active_pools": int(active_pools),
            "average_stake_per_delegator": int(avg_stake),
            "average_stake_per_delegator_ada": avg_stake / 1_000_000,
            "largest_single_stake": int(largest_stake),
            "largest_single_stake_ada": largest_stake / 1_000_000,
        }


# Convenience function
def get_comprehensive_staking_analysis(
    session: Session | AsyncSession, stake_address: str, epochs: int = 5
) -> dict[str, Any]:
    """Get comprehensive staking analysis in a single call."""
    queries = StakingDelegationQueries()

    try:
        # Get all analysis components
        delegation_history = queries.get_delegation_history(session, stake_address)
        lifecycle = queries.get_delegation_lifecycle(session, stake_address)
        rewards = queries.get_reward_earning_patterns(session, stake_address, epochs)

        # Get current epoch for stake distribution
        current_epoch = session.execute(select(func.max(Block.epoch_no))).scalar()
        stake_distribution = queries.get_stake_distribution_patterns(
            session, current_epoch, 10
        )
        active_monitoring = queries.get_active_stake_monitoring(session, current_epoch)

        return {
            "found": delegation_history.get("found", False),
            "stake_address": stake_address,
            "summary": {
                "is_active": lifecycle.get("is_active", False),
                "current_stake_ada": lifecycle.get("current_stake_ada", 0),
                "total_rewards_ada": rewards.get("total_rewards_ada", 0),
                "delegation_count": delegation_history.get("total_delegations", 0),
            },
            "delegation_history": delegation_history,
            "lifecycle": lifecycle,
            "rewards": rewards,
            "network_context": {
                "stake_distribution": stake_distribution,
                "active_monitoring": active_monitoring,
            },
        }
    except Exception as e:
        return {
            "found": False,
            "stake_address": stake_address,
            "error": f"Analysis failed: {e!s}",
        }


if __name__ == "__main__":
    """Example usage when run directly."""
    try:
        print("Staking & Delegation Queries Example")
        print("=" * 50)
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you have a configured database connection.")
