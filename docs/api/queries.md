# Query API Reference

This section documents query utilities, common patterns, and helper functions for working with dbsync-py models.

## Query Utilities

::: dbsync.queries
    options:
      show_submodules: true
      show_source: false
      members_order: alphabetical

## Common Query Patterns

### Basic Entity Retrieval

```python
from dbsync.session import create_session
from dbsync.models import Block, Transaction, StakeAddress

# Get a session
session = create_session()

# Basic entity retrieval by ID
block = session.get(Block, block_id)
tx = session.get(Transaction, tx_id)

# Query by unique fields
latest_block = session.query(Block).order_by(Block.block_no.desc()).first()
tx_by_hash = session.query(Transaction).filter(Transaction.hash == tx_hash).first()
```

### Relationship Navigation

```python
# Navigate relationships using SQLAlchemy patterns
block = session.get(Block, block_id)

# Get all transactions in a block
transactions = block.transactions

# Get the slot leader who produced the block
slot_leader = block.slot_leader

# Get the epoch this block belongs to
epoch = block.epoch
```

### Complex Queries with Joins

```python
from sqlalchemy import and_, or_, func
from dbsync.models import (
    Block, Transaction, TransactionOutput,
    StakeAddress, Delegation, Reward
)

# Find all transactions in the latest 100 blocks
latest_txs = session.query(Transaction).join(Block).filter(
    Block.block_no >= session.query(func.max(Block.block_no)).scalar() - 100
).all()

# Get stake delegation history for an address
delegations = session.query(Delegation).join(StakeAddress).filter(
    StakeAddress.view == stake_address_bech32
).order_by(Delegation.active_epoch_no.desc()).all()
```

### Aggregation Queries

```python
# Calculate total ADA in circulation
total_supply = session.query(func.sum(TransactionOutput.value)).scalar()

# Count transactions per epoch
tx_counts = session.query(
    Block.epoch_no,
    func.count(Transaction.id_).label('tx_count')
).join(Transaction).group_by(Block.epoch_no).all()

# Find top stake pools by delegation
top_pools = session.query(
    Delegation.pool_hash_id,
    func.count(Delegation.id_).label('delegator_count')
).group_by(Delegation.pool_hash_id).order_by(
    func.count(Delegation.id_).desc()
).limit(10).all()
```

### Time-Based Queries

```python
from datetime import datetime, timedelta

# Get blocks from the last 24 hours
yesterday = datetime.utcnow() - timedelta(days=1)
recent_blocks = session.query(Block).filter(
    Block.time >= yesterday
).order_by(Block.time.desc()).all()

# Get transactions in a specific epoch
epoch_txs = session.query(Transaction).join(Block).filter(
    Block.epoch_no == target_epoch
).all()
```

### Asset and Multi-Asset Queries

```python
from dbsync.models import MultiAsset, MaTxOut, MaTxMint

# Find all native tokens for a policy
policy_assets = session.query(MultiAsset).filter(
    MultiAsset.policy == policy_hex
).all()

# Get asset transaction history
asset_history = session.query(MaTxOut).join(MultiAsset).filter(
    and_(
        MultiAsset.policy == policy_hex,
        MultiAsset.name == asset_name_hex
    )
).all()
```

### Governance Queries

```python
from dbsync.models import GovActionProposal, VotingProcedure, DrepRegistration

# Get active governance proposals
active_proposals = session.query(GovActionProposal).filter(
    and_(
        GovActionProposal.ratified_epoch.is_(None),
        GovActionProposal.expired_epoch.is_(None),
        GovActionProposal.dropped_epoch.is_(None)
    )
).all()

# Get voting history for a DRep
drep_votes = session.query(VotingProcedure).join(DrepRegistration).filter(
    DrepRegistration.drep_hash_id == drep_id
).all()
```

## Performance Optimization

### Index Usage

```python
# Use indexed fields for filtering
# Good: Use indexed hash fields
tx = session.query(Transaction).filter(Transaction.hash == tx_hash).first()

# Good: Use indexed foreign keys
block_txs = session.query(Transaction).filter(Transaction.block_id == block_id).all()

# Less optimal: Non-indexed field searches
# Consider adding custom indices for frequently used patterns
```

### Pagination

```python
from sqlalchemy import desc

# Implement pagination for large result sets
def get_transactions_page(session, page=1, page_size=100):
    offset = (page - 1) * page_size
    return session.query(Transaction).order_by(
        desc(Transaction.id_)
    ).offset(offset).limit(page_size).all()

# Get total count for pagination metadata
total_count = session.query(Transaction).count()
```

### Lazy Loading vs Eager Loading

```python
from sqlalchemy.orm import joinedload, selectinload

# Eager load related objects to avoid N+1 queries
blocks_with_txs = session.query(Block).options(
    selectinload(Block.transactions)
).all()

# Use joinedload for single relationships
txs_with_blocks = session.query(Transaction).options(
    joinedload(Transaction.block)
).all()
```

### Bulk Operations

```python
# Bulk insert for large datasets (read-only typically)
# This is mainly for reference as dbsync-py is read-only

# Bulk updates (if needed for custom applications)
session.query(CustomModel).filter(
    CustomModel.status == 'pending'
).update({CustomModel.status: 'processed'})
```

## Query Builder Helpers

### Custom Query Functions

```python
def get_address_utxos(session, address_id: int):
    """Get all UTXOs for an address."""
    from dbsync.models import TransactionOutput, TransactionInput

    # Get all outputs to this address
    outputs = session.query(TransactionOutput).filter(
        TransactionOutput.address_id == address_id
    )

    # Exclude spent outputs
    spent_output_ids = session.query(TransactionInput.tx_out_id).distinct()

    return outputs.filter(
        ~TransactionOutput.id_.in_(spent_output_ids)
    ).all()

def get_pool_performance(session, pool_hash_id: int, epoch_range: tuple):
    """Calculate pool performance metrics."""
    from dbsync.models import Block, PoolHash

    start_epoch, end_epoch = epoch_range

    blocks_produced = session.query(func.count(Block.id_)).join(
        SlotLeader
    ).filter(
        and_(
            SlotLeader.pool_hash_id == pool_hash_id,
            Block.epoch_no.between(start_epoch, end_epoch)
        )
    ).scalar()

    return {
        'blocks_produced': blocks_produced,
        'epoch_range': epoch_range
    }
```

### Error Handling

```python
from sqlalchemy.exc import NoResultFound, MultipleResultsFound

def safe_get_transaction(session, tx_hash: str):
    """Safely get a transaction by hash with proper error handling."""
    try:
        return session.query(Transaction).filter(
            Transaction.hash == bytes.fromhex(tx_hash)
        ).one()
    except NoResultFound:
        return None
    except MultipleResultsFound:
        # This should not happen with proper database constraints
        raise ValueError(f"Multiple transactions found for hash: {tx_hash}")
```

## Query Performance Guidelines

### Best Practices

1. **Use Indexes**: Always filter on indexed columns when possible
2. **Limit Results**: Use `.limit()` for large result sets
3. **Eager Loading**: Use `joinedload()` or `selectinload()` to avoid N+1 queries
4. **Specific Columns**: Select only needed columns for large datasets
5. **Connection Pooling**: Reuse sessions appropriately

### Common Anti-Patterns

```python
# Anti-pattern: Loading all data then filtering in Python
all_txs = session.query(Transaction).all()
filtered = [tx for tx in all_txs if tx.fee > 1000000]  # Don't do this

# Better: Filter in database
high_fee_txs = session.query(Transaction).filter(
    Transaction.fee > 1000000
).all()

# Anti-pattern: N+1 queries
for tx in transactions:
    block = tx.block  # This hits the database for each transaction

# Better: Eager loading
transactions = session.query(Transaction).options(
    joinedload(Transaction.block)
).all()
```
