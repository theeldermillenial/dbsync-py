"""Smart Contracts & Scripts Query Examples.

This example demonstrates how to use the dbsync-py package to implement
smart contract and script analysis queries.
"""

from typing import Any

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ...models import (
    Block,
    Redeemer,
    Script,
)


class SmartContractsQueries:
    """Example smart contracts and scripts queries."""

    @staticmethod
    def get_script_analysis(
        session: Session | AsyncSession, script_hash: str | None = None, limit: int = 50
    ) -> dict[str, Any]:
        """Analyze native scripts and Plutus scripts usage."""
        if isinstance(session, AsyncSession):
            raise NotImplementedError("Async version not yet implemented")

        # Base query for scripts
        script_stmt = select(
            Script.hash,
            Script.type_,
            Script.serialised_size,
            func.count(TxOut.id_).label("output_count"),
            func.count(TxIn.id_).label("input_count"),
        ).select_from(
            Script.__table__.outerjoin(
                TxOut.__table__, TxOut.payment_cred == Script.hash
            ).outerjoin(TxIn.__table__, TxIn.tx_out_id == TxOut.tx_id)
        )

        if script_hash:
            script_stmt = script_stmt.where(Script.hash == script_hash.encode())

        script_stmt = (
            script_stmt.group_by(Script.hash, Script.type_, Script.serialised_size)
            .order_by(desc(func.count(TxOut.id_)))
            .limit(limit)
        )

        scripts = session.execute(script_stmt).all()

        if script_hash and not scripts:
            return {
                "found": False,
                "script_hash": script_hash,
                "error": "Script hash not found",
            }

        # Get overall statistics
        total_scripts = session.execute(select(func.count(Script.hash))).scalar() or 0

        native_scripts = (
            session.execute(
                select(func.count(Script.hash)).where(Script.type_ == "timelock")
            ).scalar()
            or 0
        )

        plutus_scripts = (
            session.execute(
                select(func.count(Script.hash)).where(Script.type_ == "plutusV1")
            ).scalar()
            or 0
        )

        script_list = []
        for row in scripts:
            script_list.append(
                {
                    "script_hash": row.hash.hex() if row.hash else None,
                    "type": row.type_,
                    "size_bytes": int(row.serialised_size or 0),
                    "output_usage": int(row.output_count or 0),
                    "input_usage": int(row.input_count or 0),
                    "total_usage": int(row.output_count or 0)
                    + int(row.input_count or 0),
                }
            )

        return {
            "found": True,
            "script_hash": script_hash,
            "total_scripts": int(total_scripts),
            "native_scripts": int(native_scripts),
            "plutus_scripts": int(plutus_scripts),
            "scripts_analyzed": len(script_list),
            "scripts": script_list,
        }

    @staticmethod
    def get_contract_usage_patterns(
        session: Session | AsyncSession, days: int = 30, limit: int = 20
    ) -> dict[str, Any]:
        """Track smart contract execution patterns over time."""
        if isinstance(session, AsyncSession):
            raise NotImplementedError("Async version not yet implemented")

        # Get latest block timestamp for date filtering
        latest_block = session.execute(
            select(Block.time).order_by(desc(Block.time)).limit(1)
        ).scalar()

        if not latest_block:
            return {
                "found": False,
                "error": "No block data available",
            }

        # Calculate date range (simplified - using block slots as proxy for time)
        latest_slot = session.execute(select(func.max(Block.slot_no))).scalar() or 0

        # Approximate slots per day (86400 seconds per day / 20 seconds per slot)
        slots_per_day = 4320
        start_slot = latest_slot - (days * slots_per_day)

        # Get contract usage patterns
        usage_stmt = (
            select(
                Script.hash,
                Script.type_,
                func.count(Redeemer.id_).label("execution_count"),
                func.sum(Redeemer.fee).label("total_fees"),
                func.avg(Redeemer.fee).label("avg_fee"),
                func.sum(Redeemer.mem).label("total_memory"),
                func.sum(Redeemer.steps).label("total_steps"),
            )
            .select_from(
                Redeemer.__table__.join(Tx.__table__, Redeemer.tx_id == Tx.id_)
                .join(Block.__table__, Tx.block_id == Block.id_)
                .join(Script.__table__, Redeemer.script_hash == Script.hash)
            )
            .where(Block.slot_no >= start_slot)
            .group_by(Script.hash, Script.type_)
            .order_by(desc(func.count(Redeemer.id_)))
            .limit(limit)
        )

        usage_data = session.execute(usage_stmt).all()

        # Process usage patterns
        patterns = []
        total_executions = 0
        total_fees = 0

        for row in usage_data:
            execution_count = int(row.execution_count or 0)
            total_fees_script = int(row.total_fees or 0)
            avg_fee = int(row.avg_fee or 0)
            total_memory = int(row.total_memory or 0)
            total_steps = int(row.total_steps or 0)

            total_executions += execution_count
            total_fees += total_fees_script

            patterns.append(
                {
                    "script_hash": row.hash.hex() if row.hash else None,
                    "script_type": row.type_,
                    "executions": execution_count,
                    "total_fees": total_fees_script,
                    "total_fees_ada": total_fees_script / 1_000_000,
                    "avg_fee": avg_fee,
                    "avg_fee_ada": avg_fee / 1_000_000,
                    "total_memory": total_memory,
                    "total_steps": total_steps,
                    "avg_memory": total_memory / execution_count
                    if execution_count > 0
                    else 0,
                    "avg_steps": total_steps / execution_count
                    if execution_count > 0
                    else 0,
                }
            )

        return {
            "found": True,
            "analysis_period_days": days,
            "latest_slot": latest_slot,
            "start_slot": start_slot,
            "total_executions": total_executions,
            "total_fees": total_fees,
            "total_fees_ada": total_fees / 1_000_000,
            "avg_fee_per_execution": total_fees / total_executions
            if total_executions > 0
            else 0,
            "patterns": patterns,
        }

    @staticmethod
    def get_script_hash_tracking(
        session: Session | AsyncSession, script_hash: str
    ) -> dict[str, Any]:
        """Monitor specific script hash usage and redeemer details."""
        if isinstance(session, AsyncSession):
            raise NotImplementedError("Async version not yet implemented")

        # Get script information
        script_info = session.execute(
            select(Script.hash, Script.type_, Script.serialised_size).where(
                Script.hash == script_hash.encode()
            )
        ).first()

        if not script_info:
            return {
                "found": False,
                "script_hash": script_hash,
                "error": "Script hash not found",
            }

        # Get redeemer usage
        redeemer_stmt = (
            select(
                Redeemer.purpose,
                Redeemer.index,
                Redeemer.fee,
                Redeemer.mem,
                Redeemer.steps,
                Tx.hash.label("tx_hash"),
                Block.time.label("block_time"),
                Block.epoch_no,
            )
            .select_from(
                Redeemer.__table__.join(Tx.__table__, Redeemer.tx_id == Tx.id_).join(
                    Block.__table__, Tx.block_id == Block.id_
                )
            )
            .where(Redeemer.script_hash == script_hash.encode())
            .order_by(desc(Block.time))
            .limit(100)
        )

        redeemers = session.execute(redeemer_stmt).all()

        # Process redeemer data
        redeemer_list = []
        total_fee = 0
        total_memory = 0
        total_steps = 0

        for row in redeemers:
            fee = int(row.fee or 0)
            memory = int(row.mem or 0)
            steps = int(row.steps or 0)

            total_fee += fee
            total_memory += memory
            total_steps += steps

            redeemer_list.append(
                {
                    "purpose": row.purpose,
                    "index": row.index,
                    "fee": fee,
                    "fee_ada": fee / 1_000_000,
                    "memory": memory,
                    "steps": steps,
                    "tx_hash": row.tx_hash.hex() if row.tx_hash else None,
                    "block_time": str(row.block_time) if row.block_time else None,
                    "epoch": row.epoch_no,
                }
            )

        # Get usage statistics by purpose
        purpose_stats = {}
        for redeemer in redeemer_list:
            purpose = redeemer["purpose"]
            if purpose not in purpose_stats:
                purpose_stats[purpose] = {
                    "count": 0,
                    "total_fee": 0,
                    "total_memory": 0,
                    "total_steps": 0,
                }

            purpose_stats[purpose]["count"] += 1
            purpose_stats[purpose]["total_fee"] += redeemer["fee"]
            purpose_stats[purpose]["total_memory"] += redeemer["memory"]
            purpose_stats[purpose]["total_steps"] += redeemer["steps"]

        return {
            "found": True,
            "script_hash": script_hash,
            "script_info": {
                "hash": script_info.hash.hex() if script_info.hash else None,
                "type": script_info.type_,
                "size_bytes": int(script_info.serialised_size or 0),
            },
            "usage_summary": {
                "total_executions": len(redeemer_list),
                "total_fee": total_fee,
                "total_fee_ada": total_fee / 1_000_000,
                "total_memory": total_memory,
                "total_steps": total_steps,
                "avg_fee": total_fee / len(redeemer_list) if redeemer_list else 0,
                "avg_memory": total_memory / len(redeemer_list) if redeemer_list else 0,
                "avg_steps": total_steps / len(redeemer_list) if redeemer_list else 0,
            },
            "by_purpose": purpose_stats,
            "recent_executions": redeemer_list[:10],  # Show 10 most recent
            "total_executions_shown": len(redeemer_list),
        }

    @staticmethod
    def get_contract_value_tracking(
        session: Session | AsyncSession, epoch_no: int | None = None, limit: int = 20
    ) -> dict[str, Any]:
        """Track value locked in smart contracts."""
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

        # Get script-locked UTxOs
        script_value_stmt = (
            select(
                TxOut.payment_cred,
                Script.type_.label("script_type"),
                func.sum(TxOut.value).label("total_value"),
                func.count(TxOut.id_).label("utxo_count"),
                func.avg(TxOut.value).label("avg_value"),
                func.max(TxOut.value).label("max_value"),
            )
            .select_from(
                TxOut.__table__.join(Tx.__table__, TxOut.tx_id == Tx.id_)
                .join(Block.__table__, Tx.block_id == Block.id_)
                .join(Script.__table__, TxOut.payment_cred == Script.hash)
            )
            .where(
                and_(
                    Block.epoch_no == epoch_no,
                    TxOut.payment_cred.isnot(None),  # Script-locked outputs
                )
            )
            .group_by(TxOut.payment_cred, Script.type_)
            .order_by(desc(func.sum(TxOut.value)))
            .limit(limit)
        )

        script_values = session.execute(script_value_stmt).all()

        # Get overall script-locked value statistics
        total_script_value = (
            session.execute(
                select(func.sum(TxOut.value))
                .select_from(
                    TxOut.__table__.join(Tx.__table__, TxOut.tx_id == Tx.id_).join(
                        Block.__table__, Tx.block_id == Block.id_
                    )
                )
                .where(
                    and_(
                        Block.epoch_no == epoch_no,
                        TxOut.payment_cred.isnot(None),
                    )
                )
            ).scalar()
            or 0
        )

        total_script_utxos = (
            session.execute(
                select(func.count(TxOut.id_))
                .select_from(
                    TxOut.__table__.join(Tx.__table__, TxOut.tx_id == Tx.id_).join(
                        Block.__table__, Tx.block_id == Block.id_
                    )
                )
                .where(
                    and_(
                        Block.epoch_no == epoch_no,
                        TxOut.payment_cred.isnot(None),
                    )
                )
            ).scalar()
            or 0
        )

        # Process script value data
        script_values_list = []
        for row in script_values:
            total_value = int(row.total_value or 0)
            utxo_count = int(row.utxo_count or 0)
            avg_value = int(row.avg_value or 0)
            max_value = int(row.max_value or 0)

            script_values_list.append(
                {
                    "script_hash": row.payment_cred.hex() if row.payment_cred else None,
                    "script_type": row.script_type,
                    "total_value": total_value,
                    "total_value_ada": total_value / 1_000_000,
                    "utxo_count": utxo_count,
                    "avg_value": avg_value,
                    "avg_value_ada": avg_value / 1_000_000,
                    "max_value": max_value,
                    "max_value_ada": max_value / 1_000_000,
                }
            )

        return {
            "found": True,
            "epoch": epoch_no,
            "network_totals": {
                "total_script_locked_value": int(total_script_value),
                "total_script_locked_value_ada": total_script_value / 1_000_000,
                "total_script_locked_utxos": int(total_script_utxos),
                "avg_value_per_utxo": total_script_value / total_script_utxos
                if total_script_utxos > 0
                else 0,
                "avg_value_per_utxo_ada": (total_script_value / total_script_utxos)
                / 1_000_000
                if total_script_utxos > 0
                else 0,
            },
            "scripts_analyzed": len(script_values_list),
            "script_values": script_values_list,
        }


# Convenience function
def get_comprehensive_smart_contract_analysis(
    session: Session | AsyncSession, script_hash: str | None = None, days: int = 30
) -> dict[str, Any]:
    """Get comprehensive smart contract analysis in a single call."""
    queries = SmartContractsQueries()

    try:
        # Get all analysis components
        script_analysis = queries.get_script_analysis(session, script_hash, 20)
        usage_patterns = queries.get_contract_usage_patterns(session, days, 10)

        # Get current epoch for value tracking
        current_epoch = session.execute(select(func.max(Block.epoch_no))).scalar()
        value_tracking = queries.get_contract_value_tracking(session, current_epoch, 10)

        # If specific script hash provided, get detailed tracking
        script_tracking = None
        if script_hash:
            script_tracking = queries.get_script_hash_tracking(session, script_hash)

        return {
            "found": script_analysis.get("found", False),
            "script_hash": script_hash,
            "analysis_period_days": days,
            "summary": {
                "total_scripts": script_analysis.get("total_scripts", 0),
                "native_scripts": script_analysis.get("native_scripts", 0),
                "plutus_scripts": script_analysis.get("plutus_scripts", 0),
                "total_executions": usage_patterns.get("total_executions", 0),
                "total_script_value_ada": value_tracking.get("network_totals", {}).get(
                    "total_script_locked_value_ada", 0
                ),
            },
            "script_analysis": script_analysis,
            "usage_patterns": usage_patterns,
            "value_tracking": value_tracking,
            "script_tracking": script_tracking,
        }
    except Exception as e:
        return {
            "found": False,
            "script_hash": script_hash,
            "error": f"Analysis failed: {e!s}",
        }


if __name__ == "__main__":
    """Example usage when run directly."""
    try:
        print("Smart Contracts & Scripts Query Examples")
        print("=" * 50)
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you have a configured database connection.")
