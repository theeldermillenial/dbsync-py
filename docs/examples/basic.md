# Basic Query Examples

Simple examples to get you started with dbsync-py.

## Latest Blocks

```python
from dbsync_py import create_session, Block

session = create_session("postgresql://user:pass@localhost/cardano_db")

# Get the 10 most recent blocks
latest_blocks = session.query(Block).order_by(Block.block_no.desc()).limit(10).all()

for block in latest_blocks:
    print(f"Block {block.block_no}: {block.hash.hex()} ({block.tx_count} transactions)")
```

## Block by Number

```python
# Get a specific block by number
block = session.query(Block).filter(Block.block_no == 1000000).first()

if block:
    print(f"Block 1,000,000 hash: {block.hash.hex()}")
    print(f"Block time: {block.time}")
    print(f"Slot: {block.slot_no}")
    print(f"Epoch: {block.epoch_no}")
```

## Epoch Statistics

```python
from dbsync_py import Epoch

# Get epoch statistics
epoch = session.query(Epoch).filter(Epoch.no == 400).first()

if epoch:
    print(f"Epoch {epoch.no}:")
    print(f"  Blocks: {epoch.blk_count:,}")
    print(f"  Transactions: {epoch.tx_count:,}")
    print(f"  Total Output: {epoch.out_sum:,} lovelace")
    print(f"  Total Fees: {epoch.fees:,} lovelace")
    print(f"  Duration: {epoch.start_time} to {epoch.end_time}")
```

## Transaction Details

```python
from dbsync_py import Transaction

# Get transaction with enhanced details
tx = session.query(Transaction).filter(Transaction.hash == bytes.fromhex("abc123...")).first()

if tx:
    print(f"Transaction {tx.hash.hex()}:")
    print(f"  Fee: {tx.fee:,} lovelace")
    print(f"  Output Sum: {tx.out_sum:,} lovelace")
    print(f"  Deposit: {tx.deposit:,} lovelace" if tx.deposit else "  No deposit")
    print(f"  Size: {tx.size} bytes")
    print(f"  Valid from slot: {tx.invalid_before}")
    print(f"  Valid until slot: {tx.invalid_hereafter}")
```

## Transaction Count by Epoch

```python
from dbsync_py import Transaction, Epoch
from sqlalchemy import func

# Count transactions per epoch
tx_counts = (
    session.query(
        Epoch.no.label('epoch'),
        func.count(Transaction.id).label('tx_count')
    )
    .join(Block, Block.epoch_no == Epoch.no)
    .join(Transaction, Transaction.block_id == Block.id)
    .group_by(Epoch.no)
    .order_by(Epoch.no.desc())
    .limit(10)
    .all()
)

for epoch, count in tx_counts:
    print(f"Epoch {epoch}: {count:,} transactions")
```

## Slot Leader Analysis

```python
from dbsync_py import SlotLeader, Block
from sqlalchemy import func

# Find most active slot leaders
active_leaders = (
    session.query(
        SlotLeader.description,
        func.count(Block.id).label('blocks_produced')
    )
    .join(Block, Block.slot_leader_id == SlotLeader.id)
    .group_by(SlotLeader.id, SlotLeader.description)
    .order_by(func.count(Block.id).desc())
    .limit(10)
    .all()
)

for leader, block_count in active_leaders:
    print(f"{leader}: {block_count:,} blocks")
```

## Address Balance

```python
from dbsync_py import TransactionOutput
from sqlalchemy import func

# Get current balance for an address
address = "addr1..."  # Your address here

balance = (
    session.query(func.sum(TransactionOutput.value))
    .filter(TransactionOutput.address == address)
    .filter(TransactionOutput.consumed_by_tx_id.is_(None))  # Unspent only
    .scalar()
)

print(f"Address balance: {balance} lovelace")
```
