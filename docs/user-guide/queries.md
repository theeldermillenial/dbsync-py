# Query Patterns and Migration Guide

This guide shows you how to perform common Cardano blockchain queries using dbsync-py and provides migration examples from raw SQL to Python.

## Common Query Patterns

### Basic Blockchain Queries

#### Latest Block Information

=== "dbsync-py"
    ```python
    from dbsync.session import create_session
    from dbsync.models import Block
    from sqlalchemy import desc

    session = create_session()

    # Get the latest block
    latest_block = session.query(Block).order_by(desc(Block.block_no)).first()

    print(f"Latest block: {latest_block.block_no}")
    print(f"Block hash: {latest_block.hash.hex()}")
    print(f"Timestamp: {latest_block.time}")
    print(f"Transactions: {latest_block.tx_count}")
    ```

=== "Raw SQL"
    ```sql
    SELECT block_no, encode(hash, 'hex') as hash, time, tx_count
    FROM block
    ORDER BY block_no DESC
    LIMIT 1;
    ```

#### Transaction by Hash

=== "dbsync-py"
    ```python
    from dbsync.models import Transaction

    tx_hash = "a1b2c3d4e5f6..."  # Your transaction hash

    transaction = session.query(Transaction).filter(
        Transaction.hash == bytes.fromhex(tx_hash)
    ).first()

    if transaction:
        print(f"Fee: {transaction.fee} Lovelace")
        print(f"Size: {transaction.size} bytes")
        print(f"Block: {transaction.block.block_no}")
    ```

=== "Raw SQL"
    ```sql
    SELECT t.fee, t.size, b.block_no
    FROM tx t
    JOIN block b ON t.block_id = b.id
    WHERE t.hash = decode('a1b2c3d4e5f6...', 'hex');
    ```

### Address and UTXO Queries

#### Address Balance

=== "dbsync-py"
    ```python
    from dbsync.models import Address, TransactionOutput, TransactionInput
    from sqlalchemy import func, and_

    def get_address_balance(session, address_bech32: str):
        # Get address record
        addr = session.query(Address).filter(
            Address.view == address_bech32
        ).first()

        if not addr:
            return 0

        # Calculate unspent outputs
        balance = session.query(func.sum(TransactionOutput.value)).filter(
            and_(
                TransactionOutput.address_id == addr.id_,
                ~TransactionOutput.id_.in_(
                    session.query(TransactionInput.tx_out_id).distinct()
                )
            )
        ).scalar()

        return balance or 0

    # Usage
    balance = get_address_balance(session, "addr1qx2fxv2umyhttkxyxp8x0dlpdt3k6cwng5pxj3jhsydzer3jcu5d8ps7zex2k2xt3uqxgjqnnj83ws8lhrn493txdh6gx34hs")
    print(f"Balance: {balance / 1_000_000} ADA")
    ```

=== "Raw SQL"
    ```sql
    WITH unspent_outputs AS (
        SELECT tx_out.value
        FROM tx_out
        JOIN address ON tx_out.address_id = address.id
        LEFT JOIN tx_in ON tx_out.id = tx_in.tx_out_id
        WHERE address.view = 'addr1qx2fxv2umyhttkxyxp8x0dlpdt3k6cwng5pxj3jhsydzer3jcu5d8ps7zex2k2xt3uqxgjqnnj83ws8lhrn493txdh6gx34hs'
        AND tx_in.tx_out_id IS NULL
    )
    SELECT COALESCE(SUM(value), 0) as balance
    FROM unspent_outputs;
    ```

#### UTXO Set for Address

=== "dbsync-py"
    ```python
    from dbsync.models import Address, TransactionOutput, TransactionInput, Transaction

    def get_address_utxos(session, address_bech32: str):
        addr = session.query(Address).filter(
            Address.view == address_bech32
        ).first()

        if not addr:
            return []

        # Get unspent outputs
        utxos = session.query(TransactionOutput).filter(
            and_(
                TransactionOutput.address_id == addr.id_,
                ~TransactionOutput.id_.in_(
                    session.query(TransactionInput.tx_out_id).distinct()
                )
            )
        ).all()

        # Enrich with transaction information
        result = []
        for utxo in utxos:
            tx = session.query(Transaction).filter(
                Transaction.id_ == utxo.tx_id
            ).first()

            result.append({
                "tx_hash": tx.hash.hex(),
                "tx_index": utxo.index,
                "value": utxo.value,
                "address": address_bech32
            })

        return result
    ```

=== "Raw SQL"
    ```sql
    SELECT
        encode(tx.hash, 'hex') as tx_hash,
        tx_out.index as tx_index,
        tx_out.value,
        address.view as address
    FROM tx_out
    JOIN address ON tx_out.address_id = address.id
    JOIN tx ON tx_out.tx_id = tx.id
    LEFT JOIN tx_in ON tx_out.id = tx_in.tx_out_id
    WHERE address.view = 'addr1qx2fxv2umyhttkxyxp8x0dlpdt3k6cwng5pxj3jhsydzer3jcu5d8ps7zex2k2xt3uqxgjqnnj83ws8lhrn493txdh6gx34hs'
    AND tx_in.tx_out_id IS NULL
    ORDER BY tx.id, tx_out.index;
    ```

### Staking Queries

#### Stake Pool Information

=== "dbsync-py"
    ```python
    from dbsync.models import PoolHash, PoolRegistration, PoolRetirement
    from sqlalchemy import desc

    def get_pool_info(session, pool_bech32: str):
        pool = session.query(PoolHash).filter(
            PoolHash.view == pool_bech32
        ).first()

        if not pool:
            return None

        # Get latest registration
        latest_reg = session.query(PoolRegistration).filter(
            PoolRegistration.hash_id == pool.id_
        ).order_by(desc(PoolRegistration.active_epoch_no)).first()

        # Check for retirement
        retirement = session.query(PoolRetirement).filter(
            PoolRetirement.hash_id == pool.id_
        ).first()

        return {
            "pool_id": pool.view,
            "pool_hash": pool.hash_raw.hex(),
            "ticker": latest_reg.meta_json.get("ticker") if latest_reg else None,
            "name": latest_reg.meta_json.get("name") if latest_reg else None,
            "margin": latest_reg.margin if latest_reg else None,
            "fixed_cost": latest_reg.fixed_cost if latest_reg else None,
            "active_epoch": latest_reg.active_epoch_no if latest_reg else None,
            "retirement_epoch": retirement.retiring_epoch if retirement else None
        }
    ```

=== "Raw SQL"
    ```sql
    SELECT
        ph.view as pool_id,
        encode(ph.hash_raw, 'hex') as pool_hash,
        pr.meta_json->>'ticker' as ticker,
        pr.meta_json->>'name' as name,
        pr.margin,
        pr.fixed_cost,
        pr.active_epoch_no,
        pret.retiring_epoch
    FROM pool_hash ph
    LEFT JOIN pool_registration pr ON ph.id = pr.hash_id
    LEFT JOIN pool_retirement pret ON ph.id = pret.hash_id
    WHERE ph.view = 'pool1...'
    ORDER BY pr.active_epoch_no DESC
    LIMIT 1;
    ```

#### Delegation History

=== "dbsync-py"
    ```python
    from dbsync.models import StakeAddress, Delegation, PoolHash

    def get_delegation_history(session, stake_address: str):
        stake_addr = session.query(StakeAddress).filter(
            StakeAddress.view == stake_address
        ).first()

        if not stake_addr:
            return []

        delegations = session.query(Delegation, PoolHash).join(
            PoolHash, Delegation.pool_hash_id == PoolHash.id_
        ).filter(
            Delegation.addr_id == stake_addr.id_
        ).order_by(desc(Delegation.active_epoch_no)).all()

        return [
            {
                "epoch": delegation.active_epoch_no,
                "pool_id": pool.view,
                "cert_index": delegation.cert_index
            }
            for delegation, pool in delegations
        ]
    ```

=== "Raw SQL"
    ```sql
    SELECT
        d.active_epoch_no as epoch,
        ph.view as pool_id,
        d.cert_index
    FROM delegation d
    JOIN stake_address sa ON d.addr_id = sa.id
    JOIN pool_hash ph ON d.pool_hash_id = ph.id
    WHERE sa.view = 'stake1ux3g2c9dx2nhhehyrezyxpkstartcqmu9hk63qgfkccw5rqttygt7'
    ORDER BY d.active_epoch_no DESC;
    ```

### Native Assets Queries

#### Asset Holdings by Address

=== "dbsync-py"
    ```python
    from dbsync.models import Address, TransactionOutput, MaTxOut, MultiAsset

    def get_address_native_assets(session, address_bech32: str):
        addr = session.query(Address).filter(
            Address.view == address_bech32
        ).first()

        if not addr:
            return []

        # Get native asset holdings
        assets = session.query(
            MultiAsset.policy,
            MultiAsset.name,
            MultiAsset.fingerprint,
            func.sum(MaTxOut.quantity).label('total_quantity')
        ).join(MaTxOut).join(TransactionOutput).filter(
            and_(
                TransactionOutput.address_id == addr.id_,
                ~TransactionOutput.id_.in_(
                    session.query(TransactionInput.tx_out_id).distinct()
                )
            )
        ).group_by(
            MultiAsset.policy, MultiAsset.name, MultiAsset.fingerprint
        ).all()

        return [
            {
                "policy_id": asset.policy.hex(),
                "asset_name": asset.name.hex(),
                "fingerprint": asset.fingerprint,
                "quantity": asset.total_quantity
            }
            for asset in assets
        ]
    ```

=== "Raw SQL"
    ```sql
    SELECT
        encode(ma.policy, 'hex') as policy_id,
        encode(ma.name, 'hex') as asset_name,
        ma.fingerprint,
        SUM(mto.quantity) as quantity
    FROM ma_tx_out mto
    JOIN multi_asset ma ON mto.ident = ma.id
    JOIN tx_out ON mto.tx_out_id = tx_out.id
    JOIN address ON tx_out.address_id = address.id
    LEFT JOIN tx_in ON tx_out.id = tx_in.tx_out_id
    WHERE address.view = 'addr1...'
    AND tx_in.tx_out_id IS NULL
    GROUP BY ma.policy, ma.name, ma.fingerprint;
    ```

#### Token Supply and Distribution

=== "dbsync-py"
    ```python
    from dbsync.models import MultiAsset, MaTxMint, MaTxOut

    def get_token_stats(session, policy_id: str, asset_name: str = ""):
        # Find the asset
        query = session.query(MultiAsset).filter(
            MultiAsset.policy == bytes.fromhex(policy_id)
        )

        if asset_name:
            query = query.filter(MultiAsset.name == bytes.fromhex(asset_name))

        assets = query.all()

        result = []
        for asset in assets:
            # Calculate total minted
            total_minted = session.query(func.sum(MaTxMint.quantity)).filter(
                MaTxMint.ident == asset.id_
            ).scalar() or 0

            # Calculate current circulation (in UTXOs)
            in_circulation = session.query(func.sum(MaTxOut.quantity)).join(
                TransactionOutput
            ).filter(
                and_(
                    MaTxOut.ident == asset.id_,
                    ~TransactionOutput.id_.in_(
                        session.query(TransactionInput.tx_out_id).distinct()
                    )
                )
            ).scalar() or 0

            # Count holders
            holder_count = session.query(func.count(func.distinct(
                TransactionOutput.address_id
            ))).join(MaTxOut).filter(
                and_(
                    MaTxOut.ident == asset.id_,
                    ~TransactionOutput.id_.in_(
                        session.query(TransactionInput.tx_out_id).distinct()
                    )
                )
            ).scalar() or 0

            result.append({
                "policy_id": asset.policy.hex(),
                "asset_name": asset.name.hex(),
                "fingerprint": asset.fingerprint,
                "total_minted": total_minted,
                "in_circulation": in_circulation,
                "burned": total_minted - in_circulation,
                "holder_count": holder_count
            })

        return result
    ```

### Governance Queries (Conway Era)

#### Active Governance Proposals

=== "dbsync-py"
    ```python
    from dbsync.models import GovActionProposal, Transaction, Block

    def get_active_proposals(session):
        """Get all currently active governance proposals."""

        proposals = session.query(GovActionProposal).filter(
            and_(
                GovActionProposal.ratified_epoch.is_(None),
                GovActionProposal.expired_epoch.is_(None),
                GovActionProposal.dropped_epoch.is_(None)
            )
        ).all()

        result = []
        for proposal in proposals:
            # Get submission transaction info
            tx = session.query(Transaction).filter(
                Transaction.id_ == proposal.tx_id
            ).first()

            block = session.query(Block).filter(
                Block.id_ == tx.block_id
            ).first()

            result.append({
                "proposal_id": proposal.id_,
                "type": proposal.type_,
                "description": proposal.description,
                "deposit": proposal.deposit,
                "return_address": proposal.return_address,
                "expiration": proposal.expiration,
                "submitted_epoch": block.epoch_no,
                "tx_hash": tx.hash.hex()
            })

        return result
    ```

#### DRep Voting Power

=== "dbsync-py"
    ```python
    from dbsync.models import DrepRegistration, DrepHash, Delegation

    def get_drep_voting_power(session, drep_id: str):
        """Calculate voting power for a DRep."""

        # Find DRep registration
        drep = session.query(DrepHash).filter(
            DrepHash.view == drep_id
        ).first()

        if not drep:
            return None

        # Get latest registration
        latest_reg = session.query(DrepRegistration).filter(
            DrepRegistration.drep_hash_id == drep.id_
        ).order_by(desc(DrepRegistration.active_epoch_no)).first()

        # Calculate delegated stake (simplified)
        # Note: This would need more complex logic for accurate calculation
        delegated_stake = session.query(func.sum(StakeAddress.balance)).join(
            # Join logic for DRep delegations would go here
        ).scalar() or 0

        return {
            "drep_id": drep_id,
            "anchor_url": latest_reg.voting_anchor.url if latest_reg and latest_reg.voting_anchor else None,
            "deposit": latest_reg.deposit if latest_reg else 0,
            "delegated_stake": delegated_stake,
            "active": latest_reg is not None
        }
    ```

## Migration Patterns

### From cardano-db-sync SQL to dbsync-py

#### Pattern 1: Simple SELECT with WHERE

**SQL**:
```sql
SELECT block_no, tx_count, time
FROM block
WHERE epoch_no = 123;
```

**dbsync-py**:
```python
from dbsync.models import Block

blocks = session.query(Block.block_no, Block.tx_count, Block.time).filter(
    Block.epoch_no == 123
).all()

for block in blocks:
    print(f"Block {block.block_no}: {block.tx_count} txs at {block.time}")
```

#### Pattern 2: JOINs with Aggregation

**SQL**:
```sql
SELECT
    b.epoch_no,
    COUNT(t.id) as tx_count,
    SUM(t.fee) as total_fees
FROM block b
JOIN tx t ON b.id = t.block_id
WHERE b.epoch_no BETWEEN 100 AND 110
GROUP BY b.epoch_no
ORDER BY b.epoch_no;
```

**dbsync-py**:
```python
from sqlalchemy import func

epoch_stats = session.query(
    Block.epoch_no,
    func.count(Transaction.id_).label('tx_count'),
    func.sum(Transaction.fee).label('total_fees')
).join(Transaction).filter(
    Block.epoch_no.between(100, 110)
).group_by(Block.epoch_no).order_by(Block.epoch_no).all()

for stat in epoch_stats:
    print(f"Epoch {stat.epoch_no}: {stat.tx_count} txs, {stat.total_fees} fees")
```

#### Pattern 3: Complex Subqueries

**SQL**:
```sql
SELECT DISTINCT sa.view
FROM stake_address sa
WHERE sa.id IN (
    SELECT d.addr_id
    FROM delegation d
    JOIN pool_hash ph ON d.pool_hash_id = ph.id
    WHERE ph.view = 'pool1...'
);
```

**dbsync-py**:
```python
# Method 1: Using subquery
subquery = session.query(Delegation.addr_id).join(PoolHash).filter(
    PoolHash.view == 'pool1...'
).subquery()

delegator_addresses = session.query(StakeAddress.view).filter(
    StakeAddress.id_.in_(subquery)
).distinct().all()

# Method 2: Using exists()
from sqlalchemy import exists

delegator_addresses = session.query(StakeAddress.view).filter(
    exists().where(
        and_(
            Delegation.addr_id == StakeAddress.id_,
            Delegation.pool_hash_id == PoolHash.id_,
            PoolHash.view == 'pool1...'
        )
    )
).distinct().all()
```

## Performance Best Practices

### 1. Use Indexes Effectively

```python
# Good: Filter on indexed columns
transactions = session.query(Transaction).filter(
    Transaction.hash == tx_hash  # hash is indexed
).all()

# Good: Use foreign keys
block_txs = session.query(Transaction).filter(
    Transaction.block_id == block_id  # Foreign key, indexed
).all()
```

### 2. Limit Large Result Sets

```python
# Always use limit() for potentially large results
recent_blocks = session.query(Block).order_by(
    desc(Block.block_no)
).limit(100).all()

# Use pagination for UI applications
def get_transactions_page(session, page=1, page_size=50):
    offset = (page - 1) * page_size
    return session.query(Transaction).offset(offset).limit(page_size).all()
```

### 3. Use Eager Loading

```python
from sqlalchemy.orm import joinedload, selectinload

# Load related objects to avoid N+1 queries
transactions = session.query(Transaction).options(
    joinedload(Transaction.block),  # One-to-one/many-to-one
    selectinload(Transaction.outputs)  # One-to-many
).limit(100).all()

# Now accessing tx.block or tx.outputs won't hit the database
for tx in transactions:
    print(f"Tx in block {tx.block.block_no} has {len(tx.outputs)} outputs")
```

### 4. Use Raw SQL for Complex Queries

```python
from sqlalchemy import text

# For very complex queries, raw SQL can be more efficient
result = session.execute(text("""
    WITH epoch_stats AS (
        SELECT
            b.epoch_no,
            COUNT(t.id) as tx_count,
            SUM(t.fee) as total_fees
        FROM block b
        JOIN tx t ON b.id = t.block_id
        GROUP BY b.epoch_no
    )
    SELECT epoch_no, tx_count, total_fees,
           LAG(tx_count) OVER (ORDER BY epoch_no) as prev_tx_count
    FROM epoch_stats
    ORDER BY epoch_no DESC
    LIMIT 10
""")).fetchall()

for row in result:
    print(f"Epoch {row.epoch_no}: {row.tx_count} txs (prev: {row.prev_tx_count})")
```

This migration guide provides practical examples for transitioning from raw SQL queries to dbsync-py, while maintaining performance and readability.
