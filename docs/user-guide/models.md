# Models Overview

Overview of the SQLModel classes available in dbsync-py.

## Core Models

### Block
Represents a block in the Cardano blockchain.

### Transaction
Represents a transaction within a block.

### TransactionOutput
Represents a transaction output (UTXO).

### TransactionInput
Represents a transaction input.

## Staking Models

### StakePool
Represents a stake pool.

### Delegation
Represents stake delegation.

### Reward
Represents staking rewards.

### Epoch
Represents an epoch.

## Usage Examples

```python
from dbsync_py import Block, Transaction

# Query blocks with transactions
blocks_with_txs = session.query(Block).join(Transaction).limit(10).all()
```

*More detailed model documentation will be available in the API Reference section.*
