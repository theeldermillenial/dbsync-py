# Advanced Examples

This section provides comprehensive examples for advanced usage patterns and complex queries with dbsync-py.

## Complex Multi-Table Queries

### Stake Pool Analysis

```python
from dbsync.session import create_session
from dbsync.models import (
    PoolHash, PoolRegistration, PoolRetirement, Delegation,
    Block, SlotLeader, Reward, StakeAddress
)
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta

def analyze_stake_pool(session, pool_bech32: str):
    """Comprehensive stake pool analysis."""

    # Get pool hash record
    pool = session.query(PoolHash).filter(
        PoolHash.view == pool_bech32
    ).first()

    if not pool:
        return {"error": "Pool not found"}

    # Get latest registration
    latest_registration = session.query(PoolRegistration).filter(
        PoolRegistration.hash_id == pool.id_
    ).order_by(desc(PoolRegistration.active_epoch_no)).first()

    # Get retirement (if any)
    retirement = session.query(PoolRetirement).filter(
        PoolRetirement.hash_id == pool.id_
    ).first()

    # Calculate current delegator count
    active_delegations = session.query(Delegation).filter(
        and_(
            Delegation.pool_hash_id == pool.id_,
            # Add logic to exclude superseded delegations
        )
    ).count()

    # Get blocks produced in last 10 epochs
    current_epoch = session.query(func.max(Block.epoch_no)).scalar()
    recent_blocks = session.query(func.count(Block.id_)).join(
        SlotLeader
    ).filter(
        and_(
            SlotLeader.pool_hash_id == pool.id_,
            Block.epoch_no >= current_epoch - 10
        )
    ).scalar()

    # Calculate total rewards distributed
    total_rewards = session.query(func.sum(Reward.amount)).join(
        StakeAddress
    ).join(Delegation).filter(
        Delegation.pool_hash_id == pool.id_
    ).scalar() or 0

    return {
        "pool_id": pool.view,
        "pool_name": latest_registration.meta_json.get("name") if latest_registration else None,
        "active_epoch": latest_registration.active_epoch_no if latest_registration else None,
        "retirement_epoch": retirement.retiring_epoch if retirement else None,
        "current_delegators": active_delegations,
        "blocks_last_10_epochs": recent_blocks,
        "total_rewards_distributed": total_rewards,
        "is_active": retirement is None or retirement.retiring_epoch > current_epoch
    }

# Usage
session = create_session()
pool_analysis = analyze_stake_pool(session, "pool1...")
print(f"Pool {pool_analysis['pool_name']} has {pool_analysis['current_delegators']} delegators")
```

### Multi-Asset Transaction Analysis

```python
from dbsync.models import (
    Transaction, TransactionOutput, MaTxOut, MaTxMint,
    MultiAsset, Block, Address
)

def analyze_native_token_transaction(session, tx_hash: str):
    """Analyze a transaction involving native tokens."""

    # Get the transaction
    tx = session.query(Transaction).filter(
        Transaction.hash == bytes.fromhex(tx_hash)
    ).first()

    if not tx:
        return {"error": "Transaction not found"}

    # Get all outputs with native assets
    asset_outputs = session.query(
        TransactionOutput, MaTxOut, MultiAsset
    ).join(MaTxOut).join(MultiAsset).filter(
        TransactionOutput.tx_id == tx.id_
    ).all()

    # Get all minting/burning in this transaction
    minting_burning = session.query(MaTxMint, MultiAsset).join(
        MultiAsset
    ).filter(MaTxMint.tx_id == tx.id_).all()

    # Analyze outputs by asset
    assets_transferred = {}
    for tx_out, ma_out, asset in asset_outputs:
        asset_id = f"{asset.policy.hex()}.{asset.name.hex()}"
        if asset_id not in assets_transferred:
            assets_transferred[asset_id] = {
                "policy_id": asset.policy.hex(),
                "asset_name": asset.name.hex(),
                "fingerprint": asset.fingerprint,
                "total_transferred": 0,
                "recipients": []
            }

        assets_transferred[asset_id]["total_transferred"] += ma_out.quantity
        assets_transferred[asset_id]["recipients"].append({
            "address_id": tx_out.address_id,
            "quantity": ma_out.quantity
        })

    # Analyze minting/burning
    minting_burning_summary = {}
    for mint, asset in minting_burning:
        asset_id = f"{asset.policy.hex()}.{asset.name.hex()}"
        minting_burning_summary[asset_id] = {
            "policy_id": asset.policy.hex(),
            "asset_name": asset.name.hex(),
            "fingerprint": asset.fingerprint,
            "quantity": mint.quantity,  # Positive = mint, Negative = burn
            "action": "mint" if mint.quantity > 0 else "burn"
        }

    return {
        "transaction_hash": tx_hash,
        "block_height": session.query(Block.block_no).filter(
            Block.id_ == tx.block_id
        ).scalar(),
        "assets_transferred": assets_transferred,
        "minting_burning": minting_burning_summary,
        "total_fee": tx.fee,
        "ada_outputs": session.query(func.sum(TransactionOutput.value)).filter(
            TransactionOutput.tx_id == tx.id_
        ).scalar()
    }
```

### Governance Activity Analysis

```python
from dbsync.models import (
    GovActionProposal, VotingProcedure, DrepRegistration,
    CommitteeRegistration, Transaction, Block
)

def analyze_governance_activity(session, epoch_range: tuple):
    """Analyze governance activity in a specific epoch range."""

    start_epoch, end_epoch = epoch_range

    # Get all governance proposals in the epoch range
    proposals = session.query(GovActionProposal).join(
        Transaction
    ).join(Block).filter(
        Block.epoch_no.between(start_epoch, end_epoch)
    ).all()

    # Analyze proposals by type
    proposal_types = {}
    for proposal in proposals:
        prop_type = proposal.type_
        if prop_type not in proposal_types:
            proposal_types[prop_type] = {
                "count": 0,
                "total_deposit": 0,
                "ratified": 0,
                "expired": 0,
                "dropped": 0
            }

        proposal_types[prop_type]["count"] += 1
        proposal_types[prop_type]["total_deposit"] += proposal.deposit

        if proposal.ratified_epoch:
            proposal_types[prop_type]["ratified"] += 1
        elif proposal.expired_epoch:
            proposal_types[prop_type]["expired"] += 1
        elif proposal.dropped_epoch:
            proposal_types[prop_type]["dropped"] += 1

    # Get voting activity
    votes = session.query(VotingProcedure).join(
        Transaction
    ).join(Block).filter(
        Block.epoch_no.between(start_epoch, end_epoch)
    ).all()

    # Analyze votes by role and outcome
    voting_summary = {
        "total_votes": len(votes),
        "by_role": {},
        "by_outcome": {"Yes": 0, "No": 0, "Abstain": 0}
    }

    for vote in votes:
        # Count by voter role
        if vote.committee_voter:
            role = "Committee"
        elif vote.drep_voter:
            role = "DRep"
        elif vote.pool_voter:
            role = "Pool"
        else:
            role = "Unknown"

        if role not in voting_summary["by_role"]:
            voting_summary["by_role"][role] = 0
        voting_summary["by_role"][role] += 1

        # Count by outcome
        voting_summary["by_outcome"][vote.vote] += 1

    # Get new DRep registrations
    new_dreps = session.query(DrepRegistration).join(
        Transaction
    ).join(Block).filter(
        Block.epoch_no.between(start_epoch, end_epoch)
    ).count()

    # Get new committee registrations
    new_committee = session.query(CommitteeRegistration).join(
        Transaction
    ).join(Block).filter(
        Block.epoch_no.between(start_epoch, end_epoch)
    ).count()

    return {
        "epoch_range": epoch_range,
        "governance_proposals": {
            "total_count": len(proposals),
            "by_type": proposal_types
        },
        "voting_activity": voting_summary,
        "new_registrations": {
            "dreps": new_dreps,
            "committee_members": new_committee
        }
    }
```

## Performance Optimization Examples

### Efficient Large Dataset Processing

```python
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import text

def process_large_transaction_dataset(session, start_epoch: int, end_epoch: int):
    """Efficiently process large transaction datasets."""

    # Use raw SQL for initial filtering to improve performance
    tx_ids_query = text("""
        SELECT t.id
        FROM tx t
        JOIN block b ON t.block_id = b.id
        WHERE b.epoch_no BETWEEN :start_epoch AND :end_epoch
        ORDER BY b.block_no, t.block_index
    """)

    # Execute in batches to manage memory
    batch_size = 1000
    offset = 0

    while True:
        # Get batch of transaction IDs
        tx_ids_result = session.execute(
            tx_ids_query.params(
                start_epoch=start_epoch,
                end_epoch=end_epoch
            ).limit(batch_size).offset(offset)
        ).fetchall()

        if not tx_ids_result:
            break

        tx_ids = [row[0] for row in tx_ids_result]

        # Load transactions with eager loading for related data
        transactions = session.query(Transaction).options(
            joinedload(Transaction.block),
            selectinload(Transaction.inputs),
            selectinload(Transaction.outputs),
            selectinload(Transaction.metadata)
        ).filter(Transaction.id_.in_(tx_ids)).all()

        # Process this batch
        for tx in transactions:
            process_transaction(tx)

        offset += batch_size

        # Clear session to prevent memory buildup
        session.expunge_all()

def process_transaction(tx):
    """Process individual transaction."""
    # Your transaction processing logic here
    print(f"Processing tx {tx.hash.hex()[:16]}... in block {tx.block.block_no}")
```

### Optimized Aggregation Queries

```python
def calculate_epoch_statistics(session, epoch_no: int):
    """Calculate comprehensive epoch statistics efficiently."""

    # Use single query with multiple aggregations
    stats_query = session.query(
        func.count(Transaction.id_).label('tx_count'),
        func.sum(Transaction.fee).label('total_fees'),
        func.avg(Transaction.fee).label('avg_fee'),
        func.sum(Transaction.size).label('total_size'),
        func.count(func.distinct(Transaction.block_id)).label('block_count'),
        func.min(Block.time).label('epoch_start'),
        func.max(Block.time).label('epoch_end')
    ).join(Block).filter(Block.epoch_no == epoch_no)

    result = stats_query.first()

    # Calculate additional metrics with separate optimized queries
    # UTXO changes
    utxo_created = session.query(func.count(TransactionOutput.id_)).join(
        Transaction
    ).join(Block).filter(Block.epoch_no == epoch_no).scalar()

    utxo_consumed = session.query(func.count(TransactionInput.id_)).join(
        Transaction
    ).join(Block).filter(Block.epoch_no == epoch_no).scalar()

    # Staking activity
    new_delegations = session.query(func.count(Delegation.id_)).filter(
        Delegation.active_epoch_no == epoch_no
    ).scalar()

    return {
        "epoch": epoch_no,
        "transactions": result.tx_count,
        "total_fees_lovelace": result.total_fees,
        "average_fee_lovelace": float(result.avg_fee) if result.avg_fee else 0,
        "total_size_bytes": result.total_size,
        "blocks": result.block_count,
        "epoch_start": result.epoch_start,
        "epoch_end": result.epoch_end,
        "utxo_created": utxo_created,
        "utxo_consumed": utxo_consumed,
        "net_utxo_change": utxo_created - utxo_consumed,
        "new_delegations": new_delegations
    }
```

## Integration Examples

### PyCardano Integration

```python
from pycardano import (
    TransactionBuilder, TransactionOutput, Address,
    PlutusScript, ScriptHash, Redeemer
)
from dbsync.models import Script, Datum, RedeemerData

def build_transaction_from_db_script(session, script_hash: str):
    """Build a PyCardano transaction using script data from database."""

    # Get script from database
    script = session.query(Script).filter(
        Script.hash_ == bytes.fromhex(script_hash)
    ).first()

    if not script:
        raise ValueError(f"Script not found: {script_hash}")

    # Convert database script to PyCardano script
    if script.type_ == "plutusv1":
        plutus_script = PlutusScript(script.bytes_)
    elif script.type_ == "plutusv2":
        plutus_script = PlutusScript(script.bytes_, language_version=2)
    else:
        raise ValueError(f"Unsupported script type: {script.type_}")

    # Get recent successful redeemer for reference
    recent_redeemer = session.query(RedeemerData).join(
        Redeemer
    ).filter(Redeemer.script_hash == script.hash_).order_by(
        Redeemer.id_.desc()
    ).first()

    # Build transaction (example structure)
    builder = TransactionBuilder()

    # Add script reference
    script_hash = ScriptHash.from_primitive(script.hash_)

    return {
        "script": plutus_script,
        "script_hash": script_hash,
        "recent_redeemer_data": recent_redeemer.data if recent_redeemer else None,
        "builder": builder
    }
```

### Custom API Integration

```python
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from dbsync.session import create_session

app = FastAPI(title="Cardano Analytics API")

def get_db():
    """Dependency to get database session."""
    session = create_session()
    try:
        yield session
    finally:
        session.close()

@app.get("/api/v1/address/{address}/balance")
def get_address_balance(address: str, db: Session = Depends(get_db)):
    """Get current balance for an address."""

    try:
        # Get address record
        addr_record = db.query(Address).filter(
            Address.view == address
        ).first()

        if not addr_record:
            raise HTTPException(status_code=404, detail="Address not found")

        # Calculate UTXO balance
        unspent_outputs = db.query(
            func.sum(TransactionOutput.value).label('total_ada'),
            func.count(TransactionOutput.id_).label('utxo_count')
        ).filter(
            and_(
                TransactionOutput.address_id == addr_record.id_,
                ~TransactionOutput.id_.in_(
                    db.query(TransactionInput.tx_out_id).distinct()
                )
            )
        ).first()

        # Get native assets
        native_assets = db.query(
            MultiAsset.policy,
            MultiAsset.name,
            MultiAsset.fingerprint,
            func.sum(MaTxOut.quantity).label('total_quantity')
        ).join(MaTxOut).join(TransactionOutput).filter(
            and_(
                TransactionOutput.address_id == addr_record.id_,
                ~TransactionOutput.id_.in_(
                    db.query(TransactionInput.tx_out_id).distinct()
                )
            )
        ).group_by(
            MultiAsset.policy, MultiAsset.name, MultiAsset.fingerprint
        ).all()

        return {
            "address": address,
            "ada_balance": unspent_outputs.total_ada or 0,
            "utxo_count": unspent_outputs.utxo_count or 0,
            "native_assets": [
                {
                    "policy_id": asset.policy.hex(),
                    "asset_name": asset.name.hex(),
                    "fingerprint": asset.fingerprint,
                    "quantity": asset.total_quantity
                }
                for asset in native_assets
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/pool/{pool_id}/delegators")
def get_pool_delegators(pool_id: str, db: Session = Depends(get_db)):
    """Get current delegators for a stake pool."""

    # Get pool
    pool = db.query(PoolHash).filter(PoolHash.view == pool_id).first()
    if not pool:
        raise HTTPException(status_code=404, detail="Pool not found")

    # Get current delegations (simplified - would need more complex logic for real implementation)
    delegators = db.query(
        StakeAddress.view,
        func.max(Delegation.active_epoch_no).label('latest_epoch')
    ).join(Delegation).filter(
        Delegation.pool_hash_id == pool.id_
    ).group_by(StakeAddress.view).having(
        func.max(Delegation.active_epoch_no) == db.query(
            func.max(Delegation.active_epoch_no)
        ).filter(Delegation.addr_id == StakeAddress.id_).scalar_subquery()
    ).all()

    return {
        "pool_id": pool_id,
        "delegator_count": len(delegators),
        "delegators": [
            {
                "stake_address": delegator.view,
                "active_since_epoch": delegator.latest_epoch
            }
            for delegator in delegators
        ]
    }
```

## Error Handling and Resilience

### Robust Query Patterns

```python
from sqlalchemy.exc import OperationalError, DatabaseError
from typing import Optional, List
import time

class RobustQueryExecutor:
    """Resilient query execution with retries and error handling."""

    def __init__(self, session, max_retries: int = 3, retry_delay: float = 1.0):
        self.session = session
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def execute_with_retry(self, query_func, *args, **kwargs):
        """Execute a query function with automatic retries."""

        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return query_func(*args, **kwargs)

            except (OperationalError, DatabaseError) as e:
                last_exception = e

                if attempt < self.max_retries:
                    print(f"Query failed (attempt {attempt + 1}), retrying in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)

                    # Try to rollback and reconnect
                    try:
                        self.session.rollback()
                    except:
                        pass
                else:
                    print(f"Query failed after {self.max_retries + 1} attempts")
                    raise last_exception

    def safe_get_transaction(self, tx_hash: str) -> Optional[Transaction]:
        """Safely retrieve a transaction with error handling."""

        def _query():
            return self.session.query(Transaction).filter(
                Transaction.hash == bytes.fromhex(tx_hash)
            ).first()

        try:
            return self.execute_with_retry(_query)
        except Exception as e:
            print(f"Failed to retrieve transaction {tx_hash}: {e}")
            return None

    def safe_get_address_utxos(self, address: str) -> List[TransactionOutput]:
        """Safely get UTXOs for an address."""

        def _query():
            addr = self.session.query(Address).filter(
                Address.view == address
            ).first()

            if not addr:
                return []

            return self.session.query(TransactionOutput).filter(
                and_(
                    TransactionOutput.address_id == addr.id_,
                    ~TransactionOutput.id_.in_(
                        self.session.query(TransactionInput.tx_out_id).distinct()
                    )
                )
            ).all()

        try:
            return self.execute_with_retry(_query)
        except Exception as e:
            print(f"Failed to retrieve UTXOs for address {address}: {e}")
            return []

# Usage
session = create_session()
executor = RobustQueryExecutor(session)

# Safe transaction retrieval
tx = executor.safe_get_transaction("a1b2c3...")
if tx:
    print(f"Transaction found: {tx.hash.hex()}")
else:
    print("Transaction not found or query failed")
```

This comprehensive documentation provides advanced examples covering complex multi-table queries, performance optimization, integration patterns, and robust error handling - essential for professional use of dbsync-py.
