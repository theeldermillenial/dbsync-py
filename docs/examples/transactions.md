# Transaction Analysis Examples

This section provides comprehensive examples for analyzing Cardano transactions using dbsync-py.

## Basic Transaction Analysis

### Transaction Details and Structure

```python
from dbsync.session import create_session
from dbsync.models import (
    Transaction, TransactionInput, TransactionOutput,
    TxMetadata, Block, Address, MultiAsset, MaTxOut
)
from sqlalchemy import func

def analyze_transaction(session, tx_hash: str):
    """Comprehensive transaction analysis."""

    # Get the transaction
    tx = session.query(Transaction).filter(
        Transaction.hash == bytes.fromhex(tx_hash)
    ).first()

    if not tx:
        return {"error": "Transaction not found"}

    # Get block information
    block = session.query(Block).filter(Block.id_ == tx.block_id).first()

    # Get inputs
    inputs = session.query(TransactionInput, TransactionOutput, Address).join(
        TransactionOutput, TransactionInput.tx_out_id == TransactionOutput.id_
    ).join(
        Address, TransactionOutput.address_id == Address.id_
    ).filter(TransactionInput.tx_id == tx.id_).all()

    # Get outputs
    outputs = session.query(TransactionOutput, Address).join(
        Address, TransactionOutput.address_id == Address.id_
    ).filter(TransactionOutput.tx_id == tx.id_).all()

    # Get metadata (if any)
    metadata = session.query(TxMetadata).filter(
        TxMetadata.tx_id == tx.id_
    ).all()

    # Calculate input/output totals
    total_input = sum(inp[1].value for inp in inputs)
    total_output = sum(out[0].value for out in outputs)

    # Analyze inputs
    input_analysis = []
    for tx_input, prev_output, prev_address in inputs:
        input_analysis.append({
            "previous_tx_index": tx_input.tx_out_index,
            "value": prev_output.value,
            "address": prev_address.view,
            "redeemer_index": tx_input.redeemer_id
        })

    # Analyze outputs
    output_analysis = []
    for tx_output, address in outputs:
        # Check for native assets
        native_assets = session.query(MaTxOut, MultiAsset).join(
            MultiAsset, MaTxOut.ident == MultiAsset.id_
        ).filter(MaTxOut.tx_out_id == tx_output.id_).all()

        assets = []
        for ma_out, asset in native_assets:
            assets.append({
                "policy_id": asset.policy.hex(),
                "asset_name": asset.name.hex(),
                "fingerprint": asset.fingerprint,
                "quantity": ma_out.quantity
            })

        output_analysis.append({
            "index": tx_output.index,
            "value": tx_output.value,
            "address": address.view,
            "native_assets": assets,
            "datum_hash": tx_output.data_hash.hex() if tx_output.data_hash else None,
            "script_ref": tx_output.reference_script_id is not None
        })

    # Parse metadata
    metadata_analysis = []
    for meta in metadata:
        metadata_analysis.append({
            "label": meta.label,
            "json_metadata": meta.json_,
            "bytes_metadata": meta.bytes_.hex() if meta.bytes_ else None
        })

    return {
        "transaction": {
            "hash": tx_hash,
            "fee": tx.fee,
            "size": tx.size,
            "invalid_before": tx.invalid_before,
            "invalid_hereafter": tx.invalid_hereafter,
            "script_size": tx.script_size
        },
        "block": {
            "number": block.block_no,
            "hash": block.hash.hex(),
            "slot": block.slot_no,
            "epoch": block.epoch_no,
            "time": block.time
        },
        "inputs": {
            "count": len(inputs),
            "total_value": total_input,
            "details": input_analysis
        },
        "outputs": {
            "count": len(outputs),
            "total_value": total_output,
            "details": output_analysis
        },
        "balancing": {
            "input_total": total_input,
            "output_total": total_output,
            "fee": tx.fee,
            "difference": total_input - total_output - tx.fee  # Should be 0
        },
        "metadata": metadata_analysis
    }

# Usage
session = create_session()
analysis = analyze_transaction(session, "a1b2c3d4e5f6...")
print(f"Transaction fee: {analysis['transaction']['fee'] / 1_000_000:.2f} ADA")
print(f"Inputs: {analysis['inputs']['count']}, Outputs: {analysis['outputs']['count']}")
```

### Multi-Asset Transaction Analysis

```python
from dbsync.models import MaTxMint

def analyze_native_token_transaction(session, tx_hash: str):
    """Analyze a transaction involving native tokens."""

    tx = session.query(Transaction).filter(
        Transaction.hash == bytes.fromhex(tx_hash)
    ).first()

    if not tx:
        return {"error": "Transaction not found"}

    # Get all minting/burning in this transaction
    minting_burning = session.query(MaTxMint, MultiAsset).join(
        MultiAsset, MaTxMint.ident == MultiAsset.id_
    ).filter(MaTxMint.tx_id == tx.id_).all()

    # Get all native asset outputs
    asset_outputs = session.query(
        TransactionOutput, MaTxOut, MultiAsset, Address
    ).join(MaTxOut, TransactionOutput.id_ == MaTxOut.tx_out_id).join(
        MultiAsset, MaTxOut.ident == MultiAsset.id_
    ).join(Address, TransactionOutput.address_id == Address.id_).filter(
        TransactionOutput.tx_id == tx.id_
    ).all()

    # Analyze minting/burning
    minting_analysis = {}
    total_minted = 0
    total_burned = 0

    for mint, asset in minting_burning:
        asset_id = f"{asset.policy.hex()}.{asset.name.hex()}"

        if asset_id not in minting_analysis:
            minting_analysis[asset_id] = {
                "policy_id": asset.policy.hex(),
                "asset_name": asset.name.hex(),
                "fingerprint": asset.fingerprint,
                "quantity": 0,
                "action": None
            }

        minting_analysis[asset_id]["quantity"] += mint.quantity

        if mint.quantity > 0:
            total_minted += 1
            minting_analysis[asset_id]["action"] = "mint"
        else:
            total_burned += 1
            minting_analysis[asset_id]["action"] = "burn"

    # Analyze asset distribution
    distribution_analysis = {}

    for tx_out, ma_out, asset, address in asset_outputs:
        asset_id = f"{asset.policy.hex()}.{asset.name.hex()}"

        if asset_id not in distribution_analysis:
            distribution_analysis[asset_id] = {
                "policy_id": asset.policy.hex(),
                "asset_name": asset.name.hex(),
                "fingerprint": asset.fingerprint,
                "total_distributed": 0,
                "recipients": []
            }

        distribution_analysis[asset_id]["total_distributed"] += ma_out.quantity
        distribution_analysis[asset_id]["recipients"].append({
            "address": address.view,
            "quantity": ma_out.quantity,
            "output_index": tx_out.index
        })

    return {
        "transaction_hash": tx_hash,
        "minting_burning": {
            "total_assets_minted": total_minted,
            "total_assets_burned": total_burned,
            "details": list(minting_analysis.values())
        },
        "asset_distribution": {
            "unique_assets": len(distribution_analysis),
            "total_recipients": sum(len(dist["recipients"]) for dist in distribution_analysis.values()),
            "details": list(distribution_analysis.values())
        }
    }
```

### Smart Contract Transaction Analysis

```python
from dbsync.models import Script, Redeemer, Datum

def analyze_smart_contract_transaction(session, tx_hash: str):
    """Analyze a transaction involving smart contracts."""

    tx = session.query(Transaction).filter(
        Transaction.hash == bytes.fromhex(tx_hash)
    ).first()

    if not tx:
        return {"error": "Transaction not found"}

    # Get all redeemers in this transaction
    redeemers = session.query(Redeemer, Script).join(
        Script, Redeemer.script_hash == Script.hash_
    ).filter(Redeemer.tx_id == tx.id_).all()

    # Get all datum references
    datum_refs = session.query(TransactionOutput, Datum).join(
        Datum, TransactionOutput.data_hash == Datum.hash_
    ).filter(TransactionOutput.tx_id == tx.id_).all()

    # Analyze script execution
    script_analysis = {}

    for redeemer, script in redeemers:
        script_hash = script.hash_.hex()

        if script_hash not in script_analysis:
            script_analysis[script_hash] = {
                "script_type": script.type_,
                "script_size": script.serialised_size,
                "executions": []
            }

        execution_info = {
            "purpose": redeemer.purpose,
            "index": redeemer.index,
            "execution_units": {
                "memory": redeemer.unit_mem,
                "steps": redeemer.unit_steps
            },
            "redeemer_data_size": len(redeemer.data.bytes_) if redeemer.data else 0
        }

        script_analysis[script_hash]["executions"].append(execution_info)

    # Analyze datum usage
    datum_analysis = []

    for output, datum in datum_refs:
        datum_analysis.append({
            "output_index": output.index,
            "datum_hash": datum.hash_.hex(),
            "datum_size": len(datum.bytes_) if datum.bytes_ else 0,
            "datum_json": datum.value  # If available
        })

    # Calculate total execution costs
    total_memory = sum(
        sum(exec_["execution_units"]["memory"] for exec_ in script["executions"])
        for script in script_analysis.values()
    )

    total_steps = sum(
        sum(exec_["execution_units"]["steps"] for exec_ in script["executions"])
        for script in script_analysis.values()
    )

    return {
        "transaction_hash": tx_hash,
        "script_execution": {
            "scripts_executed": len(script_analysis),
            "total_executions": sum(len(script["executions"]) for script in script_analysis.values()),
            "total_execution_units": {
                "memory": total_memory,
                "steps": total_steps
            },
            "script_details": script_analysis
        },
        "datum_usage": {
            "outputs_with_datums": len(datum_analysis),
            "details": datum_analysis
        },
        "efficiency_metrics": {
            "script_fee_ratio": (tx.script_size or 0) / tx.size if tx.size > 0 else 0,
            "avg_memory_per_execution": total_memory / max(1, sum(len(script["executions"]) for script in script_analysis.values())),
            "avg_steps_per_execution": total_steps / max(1, sum(len(script["executions"]) for script in script_analysis.values()))
        }
    }
```

## Transaction Pattern Analysis

### Address Transaction History

```python
def get_address_transaction_history(session, address_bech32: str, limit: int = 100):
    """Get transaction history for an address."""

    address = session.query(Address).filter(
        Address.view == address_bech32
    ).first()

    if not address:
        return {"error": "Address not found"}

    # Get transactions where this address appears in outputs
    output_txs = session.query(Transaction, TransactionOutput, Block).join(
        TransactionOutput, Transaction.id_ == TransactionOutput.tx_id
    ).join(Block, Transaction.block_id == Block.id_).filter(
        TransactionOutput.address_id == address.id_
    ).order_by(Block.time.desc()).limit(limit).all()

    # Get transactions where this address appears in inputs (spent from)
    input_txs = session.query(Transaction, TransactionInput, TransactionOutput, Block).join(
        TransactionInput, Transaction.id_ == TransactionInput.tx_id
    ).join(
        TransactionOutput, TransactionInput.tx_out_id == TransactionOutput.id_
    ).join(Block, Transaction.block_id == Block.id_).filter(
        TransactionOutput.address_id == address.id_
    ).order_by(Block.time.desc()).limit(limit).all()

    # Combine and analyze
    all_transactions = {}

    # Process received transactions
    for tx, output, block in output_txs:
        tx_hash = tx.hash.hex()
        if tx_hash not in all_transactions:
            all_transactions[tx_hash] = {
                "hash": tx_hash,
                "timestamp": block.time,
                "block_no": block.block_no,
                "fee": tx.fee,
                "received": 0,
                "sent": 0,
                "native_assets_received": [],
                "native_assets_sent": []
            }

        all_transactions[tx_hash]["received"] += output.value

        # Check for native assets received
        native_assets = session.query(MaTxOut, MultiAsset).join(
            MultiAsset, MaTxOut.ident == MultiAsset.id_
        ).filter(MaTxOut.tx_out_id == output.id_).all()

        for ma_out, asset in native_assets:
            all_transactions[tx_hash]["native_assets_received"].append({
                "policy_id": asset.policy.hex(),
                "asset_name": asset.name.hex(),
                "fingerprint": asset.fingerprint,
                "quantity": ma_out.quantity
            })

    # Process sent transactions
    for tx, tx_input, prev_output, block in input_txs:
        tx_hash = tx.hash.hex()
        if tx_hash not in all_transactions:
            all_transactions[tx_hash] = {
                "hash": tx_hash,
                "timestamp": block.time,
                "block_no": block.block_no,
                "fee": tx.fee,
                "received": 0,
                "sent": 0,
                "native_assets_received": [],
                "native_assets_sent": []
            }

        all_transactions[tx_hash]["sent"] += prev_output.value

    # Sort by timestamp
    transaction_list = list(all_transactions.values())
    transaction_list.sort(key=lambda x: x["timestamp"], reverse=True)

    return {
        "address": address_bech32,
        "transaction_count": len(transaction_list),
        "transactions": transaction_list[:limit]
    }
```

### Fee Analysis

```python
def analyze_transaction_fees(session, epoch_range: tuple):
    """Analyze transaction fee patterns across epochs."""

    start_epoch, end_epoch = epoch_range

    # Get fee statistics by epoch
    fee_stats = session.query(
        Block.epoch_no,
        func.count(Transaction.id_).label('tx_count'),
        func.sum(Transaction.fee).label('total_fees'),
        func.avg(Transaction.fee).label('avg_fee'),
        func.min(Transaction.fee).label('min_fee'),
        func.max(Transaction.fee).label('max_fee'),
        func.avg(Transaction.size).label('avg_size')
    ).join(Block, Transaction.block_id == Block.id_).filter(
        Block.epoch_no.between(start_epoch, end_epoch)
    ).group_by(Block.epoch_no).order_by(Block.epoch_no).all()

    # Analyze fee patterns
    fee_analysis = {}

    for stat in fee_stats:
        epoch = stat.epoch_no
        avg_fee_per_byte = stat.avg_fee / stat.avg_size if stat.avg_size > 0 else 0

        fee_analysis[epoch] = {
            "transaction_count": stat.tx_count,
            "total_fees": stat.total_fees,
            "average_fee": float(stat.avg_fee),
            "min_fee": stat.min_fee,
            "max_fee": stat.max_fee,
            "average_size": float(stat.avg_size),
            "avg_fee_per_byte": avg_fee_per_byte
        }

    # Calculate trends
    epochs = sorted(fee_analysis.keys())
    if len(epochs) >= 2:
        first_epoch = fee_analysis[epochs[0]]
        last_epoch = fee_analysis[epochs[-1]]

        trends = {
            "fee_trend": (last_epoch["average_fee"] - first_epoch["average_fee"]) / first_epoch["average_fee"] * 100,
            "volume_trend": (last_epoch["transaction_count"] - first_epoch["transaction_count"]) / first_epoch["transaction_count"] * 100,
            "efficiency_trend": (last_epoch["avg_fee_per_byte"] - first_epoch["avg_fee_per_byte"]) / first_epoch["avg_fee_per_byte"] * 100
        }
    else:
        trends = {"fee_trend": 0, "volume_trend": 0, "efficiency_trend": 0}

    return {
        "epoch_range": epoch_range,
        "by_epoch": fee_analysis,
        "trends": trends,
        "summary": {
            "total_transactions": sum(stats["transaction_count"] for stats in fee_analysis.values()),
            "total_fees_collected": sum(stats["total_fees"] for stats in fee_analysis.values()),
            "overall_avg_fee": sum(stats["total_fees"] for stats in fee_analysis.values()) / sum(stats["transaction_count"] for stats in fee_analysis.values()) if sum(stats["transaction_count"] for stats in fee_analysis.values()) > 0 else 0
        }
    }
```

### Transaction Size and Complexity Analysis

```python
def analyze_transaction_complexity(session, epoch_no: int):
    """Analyze transaction complexity patterns in an epoch."""

    # Get all transactions in the epoch
    transactions = session.query(
        Transaction.id_,
        Transaction.size,
        Transaction.fee,
        Transaction.script_size,
        func.count(TransactionInput.id_).label('input_count'),
        func.count(TransactionOutput.id_).label('output_count')
    ).join(Block, Transaction.block_id == Block.id_).outerjoin(
        TransactionInput, Transaction.id_ == TransactionInput.tx_id
    ).outerjoin(
        TransactionOutput, Transaction.id_ == TransactionOutput.tx_id
    ).filter(
        Block.epoch_no == epoch_no
    ).group_by(
        Transaction.id_, Transaction.size, Transaction.fee, Transaction.script_size
    ).all()

    # Categorize transactions
    categories = {
        "simple": [],      # 1-2 inputs, 1-2 outputs, no scripts
        "moderate": [],    # 3-10 inputs/outputs, may have scripts
        "complex": [],     # 10+ inputs/outputs or large scripts
        "script_heavy": [] # Significant script component
    }

    for tx in transactions:
        total_ios = tx.input_count + tx.output_count
        script_ratio = (tx.script_size or 0) / tx.size if tx.size > 0 else 0

        if script_ratio > 0.3:
            categories["script_heavy"].append(tx)
        elif total_ios >= 20 or tx.size > 10000:
            categories["complex"].append(tx)
        elif total_ios >= 6 or (tx.script_size or 0) > 0:
            categories["moderate"].append(tx)
        else:
            categories["simple"].append(tx)

    # Calculate statistics for each category
    complexity_stats = {}

    for category, txs in categories.items():
        if txs:
            sizes = [tx.size for tx in txs]
            fees = [tx.fee for tx in txs]

            complexity_stats[category] = {
                "count": len(txs),
                "avg_size": sum(sizes) / len(sizes),
                "avg_fee": sum(fees) / len(fees),
                "avg_fee_per_byte": sum(f/s for f, s in zip(fees, sizes)) / len(fees),
                "total_size": sum(sizes),
                "total_fees": sum(fees)
            }
        else:
            complexity_stats[category] = {
                "count": 0, "avg_size": 0, "avg_fee": 0,
                "avg_fee_per_byte": 0, "total_size": 0, "total_fees": 0
            }

    return {
        "epoch": epoch_no,
        "total_transactions": len(transactions),
        "complexity_breakdown": complexity_stats,
        "efficiency_metrics": {
            "avg_transaction_size": sum(tx.size for tx in transactions) / len(transactions) if transactions else 0,
            "script_adoption_rate": len(categories["script_heavy"]) / len(transactions) * 100 if transactions else 0,
            "complex_transaction_rate": len(categories["complex"]) / len(transactions) * 100 if transactions else 0
        }
    }

# Usage examples
session = create_session()

# Analyze a specific transaction
tx_analysis = analyze_transaction(session, "a1b2c3d4e5f6...")
print(f"Transaction has {tx_analysis['inputs']['count']} inputs and {tx_analysis['outputs']['count']} outputs")

# Analyze native token transaction
token_analysis = analyze_native_token_transaction(session, "a1b2c3d4e5f6...")
print(f"Assets minted: {token_analysis['minting_burning']['total_assets_minted']}")

# Get address history
history = get_address_transaction_history(session, "addr1qx2fxv2umyhttkxyxp8x0dlpdt3k6cwng5pxj3jhsydzer3jcu5d8ps7zex2k2xt3uqxgjqnnj83ws8lhrn493txdh6gx34hs")
print(f"Address has {history['transaction_count']} transactions")

# Analyze fee trends
fee_trends = analyze_transaction_fees(session, (300, 310))
print(f"Average fee trend: {fee_trends['trends']['fee_trend']:.2f}%")

# Analyze transaction complexity
complexity = analyze_transaction_complexity(session, 400)
print(f"Script adoption rate: {complexity['efficiency_metrics']['script_adoption_rate']:.1f}%")
```

This comprehensive transaction analysis guide provides tools for understanding all aspects of Cardano transactions, from basic structure and native assets to smart contract execution and ecosystem-wide patterns.
