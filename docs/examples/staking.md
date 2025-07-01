# Staking Analysis Examples

This section provides comprehensive examples for analyzing Cardano's staking ecosystem using dbsync-py.

## Stake Address Analysis

### Basic Stake Address Information

```python
from dbsync.session import create_session
from dbsync.models import (
    StakeAddress, StakeRegistration, StakeDeregistration,
    Delegation, Reward, Withdrawal
)
from sqlalchemy import desc, func, and_

def get_stake_address_info(session, stake_addr_bech32: str):
    """Get comprehensive information about a stake address."""

    stake_addr = session.query(StakeAddress).filter(
        StakeAddress.view == stake_addr_bech32
    ).first()

    if not stake_addr:
        return {"error": "Stake address not found"}

    # Get registration info
    registration = session.query(StakeRegistration).filter(
        StakeRegistration.addr_id == stake_addr.id_
    ).order_by(desc(StakeRegistration.epoch_no)).first()

    # Check for deregistration
    deregistration = session.query(StakeDeregistration).filter(
        StakeDeregistration.addr_id == stake_addr.id_
    ).order_by(desc(StakeDeregistration.epoch_no)).first()

    # Get current delegation
    current_delegation = session.query(Delegation).filter(
        Delegation.addr_id == stake_addr.id_
    ).order_by(desc(Delegation.active_epoch_no)).first()

    # Get reward statistics
    total_rewards = session.query(func.sum(Reward.amount)).filter(
        Reward.addr_id == stake_addr.id_
    ).scalar() or 0

    reward_count = session.query(func.count(Reward.id_)).filter(
        Reward.addr_id == stake_addr.id_
    ).scalar() or 0

    # Get withdrawal statistics  
    total_withdrawals = session.query(func.sum(Withdrawal.amount)).filter(
        Withdrawal.addr_id == stake_addr.id_
    ).scalar() or 0

    return {
        "stake_address": stake_addr_bech32,
        "hash_raw": stake_addr.hash_raw.hex(),
        "registered": registration is not None,
        "registration_epoch": registration.epoch_no if registration else None,
        "deregistered": deregistration is not None,
        "deregistration_epoch": deregistration.epoch_no if deregistration else None,
        "current_pool": current_delegation.pool_hash_id if current_delegation else None,
        "delegation_epoch": current_delegation.active_epoch_no if current_delegation else None,
        "rewards": {
            "total_earned": total_rewards,
            "reward_count": reward_count,
            "total_withdrawn": total_withdrawals,
            "available": total_rewards - total_withdrawals
        }
    }

# Usage
session = create_session()
addr_info = get_stake_address_info(session, "stake1ux3g2c9dx2nhhehyrezyxpkstartcqmu9hk63qgfkccw5rqttygt7")
print(f"Address registered: {addr_info['registered']}")
print(f"Total rewards: {addr_info['rewards']['total_earned'] / 1_000_000:.2f} ADA")
```

### Delegation History Analysis

```python
from dbsync.models import PoolHash

def get_delegation_history(session, stake_addr_bech32: str):
    """Get complete delegation history for a stake address."""

    stake_addr = session.query(StakeAddress).filter(
        StakeAddress.view == stake_addr_bech32
    ).first()

    if not stake_addr:
        return []

    # Get all delegations with pool information
    delegations = session.query(Delegation, PoolHash).join(
        PoolHash, Delegation.pool_hash_id == PoolHash.id_
    ).filter(
        Delegation.addr_id == stake_addr.id_
    ).order_by(desc(Delegation.active_epoch_no)).all()

    delegation_history = []

    for delegation, pool in delegations:
        # Get pool registration for metadata
        pool_reg = session.query(PoolRegistration).filter(
            PoolRegistration.hash_id == pool.id_
        ).order_by(desc(PoolRegistration.active_epoch_no)).first()

        # Calculate rewards earned while delegated to this pool
        # This is simplified - more complex logic needed for accurate calculation
        pool_rewards = session.query(func.sum(Reward.amount)).filter(
            and_(
                Reward.addr_id == stake_addr.id_,
                Reward.spendable_epoch >= delegation.active_epoch_no
            )
        ).scalar() or 0

        delegation_info = {
            "active_epoch": delegation.active_epoch_no,
            "pool_id": pool.view,
            "pool_hash": pool.hash_raw.hex(),
            "pool_name": pool_reg.meta_json.get("name") if pool_reg else None,
            "pool_ticker": pool_reg.meta_json.get("ticker") if pool_reg else None,
            "cert_index": delegation.cert_index,
            "estimated_rewards": pool_rewards
        }

        delegation_history.append(delegation_info)

    return delegation_history

# Usage
history = get_delegation_history(session, "stake1ux3g2c9dx2nhhehyrezyxpkstartcqmu9hk63qgfkccw5rqttygt7")
for entry in history:
    print(f"Epoch {entry['active_epoch']}: Delegated to {entry['pool_ticker']} ({entry['pool_id']})")
```

### Reward Analysis

```python
from datetime import datetime

def analyze_staking_rewards(session, stake_addr_bech32: str, epoch_range: tuple = None):
    """Analyze staking rewards for a stake address."""

    stake_addr = session.query(StakeAddress).filter(
        StakeAddress.view == stake_addr_bech32
    ).first()

    if not stake_addr:
        return {"error": "Stake address not found"}

    # Build base query
    rewards_query = session.query(Reward).filter(
        Reward.addr_id == stake_addr.id_
    )

    # Apply epoch range filter if provided
    if epoch_range:
        start_epoch, end_epoch = epoch_range
        rewards_query = rewards_query.filter(
            Reward.spendable_epoch.between(start_epoch, end_epoch)
        )

    rewards = rewards_query.order_by(Reward.spendable_epoch).all()

    # Analyze reward patterns
    reward_analysis = {
        "total_rewards": 0,
        "reward_count": len(rewards),
        "epochs_with_rewards": set(),
        "by_type": {"member": 0, "leader": 0, "refund": 0},
        "by_epoch": {},
        "average_per_epoch": 0,
        "highest_reward": 0,
        "lowest_reward": float('inf') if rewards else 0
    }

    for reward in rewards:
        amount = reward.amount
        reward_analysis["total_rewards"] += amount
        reward_analysis["epochs_with_rewards"].add(reward.spendable_epoch)

        # Track by type
        reward_type = reward.type_
        if reward_type in reward_analysis["by_type"]:
            reward_analysis["by_type"][reward_type] += amount

        # Track by epoch
        epoch = reward.spendable_epoch
        if epoch not in reward_analysis["by_epoch"]:
            reward_analysis["by_epoch"][epoch] = 0
        reward_analysis["by_epoch"][epoch] += amount

        # Track min/max
        if amount > reward_analysis["highest_reward"]:
            reward_analysis["highest_reward"] = amount
        if amount < reward_analysis["lowest_reward"]:
            reward_analysis["lowest_reward"] = amount

    # Calculate averages
    unique_epochs = len(reward_analysis["epochs_with_rewards"])
    if unique_epochs > 0:
        reward_analysis["average_per_epoch"] = reward_analysis["total_rewards"] / unique_epochs

    # Convert set to count for serialization
    reward_analysis["unique_epochs_with_rewards"] = unique_epochs
    del reward_analysis["epochs_with_rewards"]

    if not rewards:
        reward_analysis["lowest_reward"] = 0

    return reward_analysis

# Usage
rewards = analyze_staking_rewards(session, "stake1ux3g2c9dx2nhhehyrezyxpkstartcqmu9hk63qgfkccw5rqttygt7", (350, 400))
print(f"Total rewards in epochs 350-400: {rewards['total_rewards'] / 1_000_000:.2f} ADA")
print(f"Average per epoch: {rewards['average_per_epoch'] / 1_000_000:.2f} ADA")
```

## Stake Pool Analysis

### Pool Performance Metrics

```python
from dbsync.models import Block, SlotLeader, Epoch

def analyze_pool_performance(session, pool_bech32: str, epoch_range: tuple):
    """Analyze stake pool performance metrics."""

    pool = session.query(PoolHash).filter(PoolHash.view == pool_bech32).first()
    if not pool:
        return {"error": "Pool not found"}

    start_epoch, end_epoch = epoch_range

    # Get blocks produced by this pool
    blocks_produced = session.query(Block).join(SlotLeader).filter(
        and_(
            SlotLeader.pool_hash_id == pool.id_,
            Block.epoch_no.between(start_epoch, end_epoch)
        )
    ).order_by(Block.epoch_no, Block.slot_no).all()

    # Get epoch statistics for comparison
    epoch_stats = session.query(
        Block.epoch_no,
        func.count(Block.id_).label('total_blocks'),
        func.count(func.distinct(SlotLeader.pool_hash_id)).label('active_pools')
    ).join(SlotLeader).filter(
        Block.epoch_no.between(start_epoch, end_epoch)
    ).group_by(Block.epoch_no).all()

    # Analyze performance by epoch
    performance_by_epoch = {}

    for epoch_stat in epoch_stats:
        epoch_no = epoch_stat.epoch_no
        epoch_blocks = [b for b in blocks_produced if b.epoch_no == epoch_no]

        performance_by_epoch[epoch_no] = {
            "blocks_produced": len(epoch_blocks),
            "total_blocks_in_epoch": epoch_stat.total_blocks,
            "market_share": len(epoch_blocks) / epoch_stat.total_blocks * 100 if epoch_stat.total_blocks > 0 else 0,
            "active_pools": epoch_stat.active_pools
        }

    # Calculate overall statistics
    total_blocks_produced = len(blocks_produced)
    total_blocks_possible = sum(stat.total_blocks for stat in epoch_stats)

    # Get delegator count (simplified)
    current_delegators = session.query(func.count(func.distinct(Delegation.addr_id))).filter(
        Delegation.pool_hash_id == pool.id_
    ).scalar() or 0

    return {
        "pool_id": pool_bech32,
        "epoch_range": epoch_range,
        "overall_performance": {
            "total_blocks_produced": total_blocks_produced,
            "total_blocks_possible": total_blocks_possible,
            "overall_market_share": total_blocks_produced / total_blocks_possible * 100 if total_blocks_possible > 0 else 0,
            "current_delegators": current_delegators
        },
        "by_epoch": performance_by_epoch,
        "consistency": {
            "epochs_with_blocks": len([e for e in performance_by_epoch.values() if e["blocks_produced"] > 0]),
            "total_epochs": len(performance_by_epoch),
            "production_ratio": len([e for e in performance_by_epoch.values() if e["blocks_produced"] > 0]) / len(performance_by_epoch) * 100 if performance_by_epoch else 0
        }
    }
```

### Pool Reward Distribution Analysis

```python
def analyze_pool_reward_distribution(session, pool_bech32: str, epoch_no: int):
    """Analyze how rewards are distributed to pool delegators."""

    pool = session.query(PoolHash).filter(PoolHash.view == pool_bech32).first()
    if not pool:
        return {"error": "Pool not found"}

    # Get all delegators to this pool
    delegators = session.query(Delegation, StakeAddress).join(
        StakeAddress, Delegation.addr_id == StakeAddress.id_
    ).filter(
        and_(
            Delegation.pool_hash_id == pool.id_,
            Delegation.active_epoch_no <= epoch_no
        )
    ).all()

    # Get rewards for delegators in this epoch
    delegator_rewards = []
    total_rewards = 0

    for delegation, stake_addr in delegators:
        rewards = session.query(func.sum(Reward.amount)).filter(
            and_(
                Reward.addr_id == stake_addr.id_,
                Reward.spendable_epoch == epoch_no
            )
        ).scalar() or 0

        if rewards > 0:
            delegator_rewards.append({
                "stake_address": stake_addr.view,
                "delegation_epoch": delegation.active_epoch_no,
                "rewards": rewards
            })
            total_rewards += rewards

    # Sort by reward amount
    delegator_rewards.sort(key=lambda x: x["rewards"], reverse=True)

    # Calculate distribution statistics
    if delegator_rewards:
        reward_amounts = [d["rewards"] for d in delegator_rewards]

        distribution_stats = {
            "total_delegators_rewarded": len(delegator_rewards),
            "total_rewards_distributed": total_rewards,
            "average_reward": total_rewards / len(delegator_rewards),
            "median_reward": sorted(reward_amounts)[len(reward_amounts) // 2],
            "highest_reward": max(reward_amounts),
            "lowest_reward": min(reward_amounts),
            "top_10_percent_share": sum(reward_amounts[:len(reward_amounts)//10]) / total_rewards * 100 if total_rewards > 0 else 0
        }
    else:
        distribution_stats = {
            "total_delegators_rewarded": 0,
            "total_rewards_distributed": 0,
            "average_reward": 0,
            "median_reward": 0,
            "highest_reward": 0,
            "lowest_reward": 0,
            "top_10_percent_share": 0
        }

    return {
        "pool_id": pool_bech32,
        "epoch": epoch_no,
        "distribution_stats": distribution_stats,
        "top_delegators": delegator_rewards[:10],  # Top 10 by reward amount
        "reward_histogram": create_reward_histogram(reward_amounts) if delegator_rewards else []
    }

def create_reward_histogram(amounts, bins=10):
    """Create a histogram of reward amounts."""
    if not amounts:
        return []

    min_amount = min(amounts)
    max_amount = max(amounts)
    bin_size = (max_amount - min_amount) / bins

    histogram = []
    for i in range(bins):
        bin_start = min_amount + i * bin_size
        bin_end = min_amount + (i + 1) * bin_size

        count = len([a for a in amounts if bin_start <= a < bin_end])
        if i == bins - 1:  # Include max value in last bin
            count = len([a for a in amounts if bin_start <= a <= bin_end])

        histogram.append({
            "bin_start": bin_start,
            "bin_end": bin_end,
            "count": count
        })

    return histogram
```

## Ecosystem Analysis

### Delegation Trends

```python
def analyze_delegation_trends(session, epoch_range: tuple):
    """Analyze delegation trends across the ecosystem."""

    start_epoch, end_epoch = epoch_range

    # Get delegation data for each epoch
    delegation_trends = {}

    for epoch in range(start_epoch, end_epoch + 1):
        # Count active delegations in this epoch
        active_delegations = session.query(func.count(Delegation.id_)).filter(
            Delegation.active_epoch_no <= epoch
        ).scalar() or 0

        # Count unique pools with delegations
        active_pools = session.query(func.count(func.distinct(Delegation.pool_hash_id))).filter(
            Delegation.active_epoch_no <= epoch
        ).scalar() or 0

        # New delegations in this epoch
        new_delegations = session.query(func.count(Delegation.id_)).filter(
            Delegation.active_epoch_no == epoch
        ).scalar() or 0

        delegation_trends[epoch] = {
            "total_active_delegations": active_delegations,
            "active_pools": active_pools,
            "new_delegations": new_delegations,
            "avg_delegations_per_pool": active_delegations / active_pools if active_pools > 0 else 0
        }

    return {
        "epoch_range": epoch_range,
        "trends": delegation_trends,
        "growth": {
            "delegation_growth": delegation_trends[end_epoch]["total_active_delegations"] - delegation_trends[start_epoch]["total_active_delegations"],
            "pool_growth": delegation_trends[end_epoch]["active_pools"] - delegation_trends[start_epoch]["active_pools"]
        }
    }
```

### Pool Saturation Analysis

```python
def analyze_pool_saturation(session, epoch_no: int, k_parameter: int = 500):
    """Analyze pool saturation levels across the ecosystem."""

    # Get all pools with delegations
    pool_delegations = session.query(
        PoolHash.view,
        func.count(Delegation.id_).label('delegator_count')
    ).join(Delegation).filter(
        Delegation.active_epoch_no <= epoch_no
    ).group_by(PoolHash.view).all()

    # Calculate total active stake (simplified)
    total_stake = session.query(func.count(Delegation.id_)).filter(
        Delegation.active_epoch_no <= epoch_no
    ).scalar() or 0

    # Calculate optimal pool stake (total_stake / k_parameter)
    optimal_stake = total_stake / k_parameter if k_parameter > 0 else 0

    saturation_analysis = {
        "oversaturated": [],
        "optimal": [],
        "undersaturated": [],
        "statistics": {
            "total_pools": len(pool_delegations),
            "total_stake": total_stake,
            "optimal_stake_per_pool": optimal_stake,
            "k_parameter": k_parameter
        }
    }

    for pool_id, delegator_count in pool_delegations:
        saturation_ratio = delegator_count / optimal_stake if optimal_stake > 0 else 0

        pool_info = {
            "pool_id": pool_id,
            "delegator_count": delegator_count,
            "saturation_ratio": saturation_ratio,
            "status": "optimal" if 0.8 <= saturation_ratio <= 1.2 else
                     "oversaturated" if saturation_ratio > 1.2 else "undersaturated"
        }

        if saturation_ratio > 1.2:
            saturation_analysis["oversaturated"].append(pool_info)
        elif 0.8 <= saturation_ratio <= 1.2:
            saturation_analysis["optimal"].append(pool_info)
        else:
            saturation_analysis["undersaturated"].append(pool_info)

    # Sort by saturation ratio
    for category in ["oversaturated", "optimal", "undersaturated"]:
        saturation_analysis[category].sort(key=lambda x: x["saturation_ratio"], reverse=True)

    return saturation_analysis

# Usage examples
session = create_session()

# Analyze specific stake address
stake_info = get_stake_address_info(session, "stake1ux3g2c9dx2nhhehyrezyxpkstartcqmu9hk63qgfkccw5rqttygt7")
print(f"Available rewards: {stake_info['rewards']['available'] / 1_000_000:.2f} ADA")

# Analyze pool performance
pool_performance = analyze_pool_performance(session, "pool1...", (350, 360))
print(f"Pool produced {pool_performance['overall_performance']['total_blocks_produced']} blocks")

# Check ecosystem delegation trends
trends = analyze_delegation_trends(session, (300, 350))
print(f"Delegation growth: {trends['growth']['delegation_growth']} new delegations")

# Analyze pool saturation
saturation = analyze_pool_saturation(session, 400)
print(f"Oversaturated pools: {len(saturation['oversaturated'])}")
```

This comprehensive staking analysis guide provides tools for understanding all aspects of Cardano's staking ecosystem, from individual stake address behavior to ecosystem-wide trends and pool performance metrics.
