#!/usr/bin/env python3
"""Query examples CLI commands for dbsync-py package.

Provides command-line interface for running query examples that demonstrate
how to use the dbsync-py package models and utilities.
"""

import json
import sys
from typing import Any

import click


@click.group()
@click.pass_context
def query(ctx: click.Context) -> None:
    """Run query examples demonstrating dbsync-py usage.

    These commands execute example implementations that show how to use
    the dbsync-py package models to query Cardano DB Sync databases.

    Examples are part of the installed package under dbsync.examples.queries
    and serve as educational demonstrations of common query patterns.
    """
    pass


@query.command()
@click.option(
    "--format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format (text or json)",
)
@click.option(
    "--individual",
    is_flag=True,
    help="Show individual query results instead of summary",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file (default: stdout)",
)
@click.pass_context
def chain_metadata(
    ctx: click.Context,
    format: str,
    individual: bool,
    output: str | None,
) -> None:
    """Run chain metadata query examples.

    Demonstrates fundamental blockchain data queries including:
    - Chain metadata and network information
    - Current ADA supply calculation
    - Latest slot number and sync progress
    - Database size analysis

    This executes the examples from dbsync.examples.queries.chain_metadata
    """
    verbose = ctx.obj.get("verbose", False)

    try:
        _run_chain_metadata_examples(
            format=format,
            individual=individual,
            output_file=output,
            verbose=verbose,
        )
    except Exception as e:
        if verbose:
            raise
        click.echo(f"Error running chain metadata examples: {e}", err=True)
        sys.exit(1)


def _run_chain_metadata_examples(
    format: str = "text",
    individual: bool = False,
    output_file: str | None = None,
    verbose: bool = False,
) -> None:
    """Run the chain metadata query examples."""
    try:
        from dbsync.config import DatabaseConfig
        from dbsync.examples.queries.chain_metadata import (
            ChainMetadataQueries,
            get_chain_info,
        )
        from dbsync.session import get_session
    except ImportError as e:
        raise click.ClickException(
            f"Failed to import required modules: {e}\n"
            "Make sure dbsync-py is properly installed and configured."
        )

    # Test configuration and connection
    try:
        config = DatabaseConfig()
        if verbose:
            click.echo(f"Connecting to {config.host}:{config.port}/{config.database}")

        with get_session() as session:
            # Test connection
            from sqlalchemy import text

            session.execute(text("SELECT 1")).scalar()

    except Exception as e:
        raise click.ClickException(
            f"Database connection failed: {e}\n"
            "Check your database configuration (see sample.env for setup)"
        )

    # Run the examples
    try:
        with get_session() as session:
            if individual:
                results = _get_individual_results(session, verbose)
            else:
                results = _get_summary_results(session, verbose)

            _output_results(results, format, output_file)

    except Exception as e:
        raise click.ClickException(f"Failed to execute queries: {e}")


def _get_individual_results(session, verbose: bool) -> dict[str, Any]:
    """Get individual query results."""
    from dbsync.examples.queries.chain_metadata import ChainMetadataQueries

    if verbose:
        click.echo("Running individual chain metadata queries...")

    queries = ChainMetadataQueries()
    results = {}

    # Chain metadata
    meta = queries.get_chain_metadata(session)
    results["chain_metadata"] = {
        "network": meta.network_name if meta else "Unknown",
        "start_time": str(meta.start_time) if meta and meta.start_time else None,
    }

    # Current supply
    supply_lovelace = queries.get_current_supply(session)
    results["current_supply"] = {
        "lovelace": supply_lovelace,
        "ada": float(supply_lovelace) / 1_000_000,
    }

    # Latest slot
    results["latest_slot"] = queries.get_latest_slot_number(session)

    # Database sizes
    results["database_size"] = queries.get_database_size_pretty(session)
    results["block_table_size"] = queries.get_table_size_pretty(session, "block")

    # Sync status
    results["sync_progress_percent"] = queries.get_sync_progress_percent(session)
    results["sync_behind"] = queries.get_sync_behind_duration(session)

    return {
        "type": "individual_results",
        "queries": results,
        "total_queries": 7,
    }


def _get_summary_results(session, verbose: bool) -> dict[str, Any]:
    """Get comprehensive summary results."""
    from dbsync.examples.queries.chain_metadata import get_chain_info

    if verbose:
        click.echo("Running comprehensive chain info query...")

    info = get_chain_info(session)

    return {
        "type": "summary_results",
        "chain_info": info,
    }


def _output_results(
    results: dict[str, Any], format: str, output_file: str | None
) -> None:
    """Output results in the specified format."""
    if format == "json":
        output = json.dumps(results, indent=2, default=str)
    else:
        output = _format_text_output(results)

    if output_file:
        with open(output_file, "w") as f:
            f.write(output)
        click.echo(f"Results written to {output_file}")
    else:
        click.echo(output)


def _format_text_output(results: dict[str, Any]) -> str:
    """Format results as human-readable text."""
    lines = []
    lines.append("Chain Metadata Query Examples")
    lines.append("=" * 40)

    if results["type"] == "individual_results":
        queries = results["queries"]

        lines.append("\n1. Chain Metadata:")
        lines.append(f"   Network: {queries['chain_metadata']['network']}")
        if queries["chain_metadata"]["start_time"]:
            lines.append(f"   Start time: {queries['chain_metadata']['start_time']}")

        lines.append("\n2. Current Supply:")
        lines.append(f"   Total: {queries['current_supply']['lovelace']:,} Lovelace")
        lines.append(f"   Total: {queries['current_supply']['ada']:,.2f} ADA")

        lines.append("\n3. Latest Slot:")
        if queries["latest_slot"]:
            lines.append(f"   Latest slot: {queries['latest_slot']:,}")
        else:
            lines.append("   Latest slot: Unknown")

        lines.append("\n4. Database Information:")
        lines.append(f"   Database size: {queries['database_size']}")
        lines.append(f"   Block table size: {queries['block_table_size']}")

        lines.append("\n5. Sync Status:")
        lines.append(f"   Progress: {queries['sync_progress_percent']:.2f}%")
        if queries["sync_behind"]:
            lines.append(f"   Behind by: {queries['sync_behind']}")
        else:
            lines.append("   Behind by: Unknown")

        lines.append(f"\nTotal queries executed: {results['total_queries']}")

    else:  # summary_results
        info = results["chain_info"]

        lines.append(f"Network: {info['network']}")
        if info["start_time"]:
            lines.append(f"Start time: {info['start_time']}")
        lines.append(
            f"Supply: {info['supply_ada']:,.2f} ADA ({info['supply_lovelace']:,} Lovelace)"
        )

        if info["latest_slot"]:
            lines.append(f"Latest slot: {info['latest_slot']:,}")
        else:
            lines.append("Latest slot: Unknown")

        lines.append(f"Database size: {info['database_size']}")
        lines.append(f"Block table size: {info['block_table_size']}")
        lines.append(f"Sync progress: {info['sync_progress_percent']:.2f}%")

        if info["sync_behind"]:
            lines.append(f"Sync behind by: {info['sync_behind']}")
        else:
            lines.append("Sync status: Up to date")

    lines.append("\n" + "=" * 40)
    lines.append("✅ Examples completed successfully!")
    lines.append("Source: dbsync.examples.queries.chain_metadata")

    return "\n".join(lines)


@query.command()
@click.option(
    "--format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format (text or json)",
)
@click.option(
    "--days",
    type=int,
    default=7,
    help="Number of days to analyze (default: 7)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file (default: stdout)",
)
@click.pass_context
def transaction_analysis(
    ctx: click.Context,
    format: str,
    days: int,
    output: str | None,
) -> None:
    """Run transaction analysis and UTxO operation examples.

    Demonstrates comprehensive transaction analysis queries including:
    - Transaction fee statistics and distribution
    - Address balance calculations using UTxO method
    - Transaction input/output analysis
    - Address transaction history
    - Hourly transaction throughput metrics
    - Large transaction identification
    - Transaction size distribution analysis

    This executes the examples from dbsync.examples.queries.transaction_analysis
    """
    verbose = ctx.obj.get("verbose", False)

    try:
        _run_transaction_analysis_examples(
            format=format,
            days=days,
            output_file=output,
            verbose=verbose,
        )
    except Exception as e:
        if verbose:
            raise
        click.echo(f"Error running transaction analysis examples: {e}", err=True)
        sys.exit(1)


def _run_transaction_analysis_examples(
    format: str = "text",
    days: int = 7,
    output_file: str | None = None,
    verbose: bool = False,
) -> None:
    """Run the transaction analysis query examples."""
    try:
        from dbsync.config import DatabaseConfig
        from dbsync.examples.queries.transaction_analysis import (
            get_comprehensive_transaction_analysis,
        )
        from dbsync.session import get_session
    except ImportError as e:
        raise click.ClickException(
            f"Failed to import required modules: {e}\n"
            "Make sure dbsync-py is properly installed and configured."
        )

    # Test configuration and connection
    try:
        config = DatabaseConfig()
        if verbose:
            click.echo(f"Connecting to {config.host}:{config.port}/{config.database}")

        with get_session() as session:
            # Test connection
            from sqlalchemy import text

            session.execute(text("SELECT 1")).scalar()

    except Exception as e:
        raise click.ClickException(
            f"Database connection failed: {e}\n"
            "Check your database configuration (see sample.env for setup)"
        )

    # Run the examples
    try:
        with get_session() as session:
            if verbose:
                click.echo(f"Running transaction analysis for {days} days...")

            results = get_comprehensive_transaction_analysis(session, days)
            _output_transaction_results(results, format, output_file)

    except Exception as e:
        raise click.ClickException(f"Failed to execute queries: {e}")


def _output_transaction_results(
    results: dict[str, Any], format: str, output_file: str | None
) -> None:
    """Output transaction analysis results in the specified format."""
    if format == "json":
        output = json.dumps(results, indent=2, default=str)
    else:
        output = _format_transaction_text_output(results)

    if output_file:
        with open(output_file, "w") as f:
            f.write(output)
        click.echo(f"Results written to {output_file}")
    else:
        click.echo(output)


def _format_transaction_text_output(results: dict[str, Any]) -> str:
    """Format transaction analysis results as human-readable text."""
    lines = []
    lines.append("Transaction Analysis Query Examples")
    lines.append("=" * 50)

    period = results["analysis_period_days"]
    fee_stats = results["fee_stats"]
    throughput = results["throughput"]
    size_dist = results["size_distribution"]
    large_txs = results["large_transactions"]
    summary = results["summary"]

    lines.append(f"\nAnalysis Period: {period} days")
    lines.append(f"Total Transactions: {fee_stats['tx_count']:,}")

    lines.append("\n1. Fee Statistics:")
    lines.append(f"   Average fee: {summary['avg_fee_ada']:.4f} ADA")
    lines.append(f"   Min fee: {fee_stats['min_fee'] / 1_000_000:.4f} ADA")
    lines.append(f"   Max fee: {fee_stats['max_fee'] / 1_000_000:.4f} ADA")
    lines.append(f"   Total fees: {fee_stats['total_fees'] / 1_000_000:,.2f} ADA")

    lines.append("\n2. Transaction Throughput:")
    lines.append(
        f"   Peak hourly: {throughput['peak_hour_transactions']:,} transactions"
    )
    lines.append(
        f"   Average per hour: {throughput['average_per_hour']:.1f} transactions"
    )

    lines.append("\n3. Transaction Size Distribution:")
    lines.append(f"   Average inputs per transaction: {size_dist['avg_inputs']:.2f}")
    lines.append(f"   Average outputs per transaction: {size_dist['avg_outputs']:.2f}")

    lines.append("\n4. Large Transactions (>1000 ADA):")
    lines.append(f"   Found: {large_txs['transaction_count']} transactions")
    if large_txs["transactions"]:
        largest = large_txs["transactions"][0]
        lines.append(f"   Largest: {largest['total_output_ada']:,.2f} ADA")

    lines.append("\n" + "=" * 50)
    lines.append("✅ Examples completed successfully!")
    lines.append("Source: dbsync.examples.queries.transaction_analysis")

    return "\n".join(lines)


@query.command()
@click.option(
    "--pool-id",
    required=True,
    help="Pool ID (bech32 format, e.g., pool1...)",
)
@click.option(
    "--format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format (text or json)",
)
@click.option(
    "--epochs",
    type=int,
    default=5,
    help="Number of recent epochs to analyze (default: 5)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file (default: stdout)",
)
@click.pass_context
def pool_management(
    ctx: click.Context,
    pool_id: str,
    format: str,
    epochs: int,
    output: str | None,
) -> None:
    """Run pool management and block production analysis examples.

    Demonstrates comprehensive pool analysis queries including:
    - Pool registration information and metadata
    - Block production statistics over recent epochs
    - Pool performance metrics (efficiency, luck)
    - Current delegation summary and delegator list
    - Reward distribution analysis
    - Operational status and configuration details

    This executes the examples from dbsync.examples.queries.pool_management
    """
    verbose = ctx.obj.get("verbose", False)

    try:
        _run_pool_management_examples(
            pool_id=pool_id,
            format=format,
            epochs=epochs,
            output_file=output,
            verbose=verbose,
        )
    except Exception as e:
        if verbose:
            raise
        click.echo(f"Error running pool management examples: {e}", err=True)
        sys.exit(1)


def _run_pool_management_examples(
    pool_id: str,
    format: str = "text",
    epochs: int = 5,
    output_file: str | None = None,
    verbose: bool = False,
) -> None:
    """Run the pool management query examples."""
    try:
        from dbsync.config import DatabaseConfig
        from dbsync.examples.queries.pool_management import (
            get_comprehensive_pool_analysis,
        )
        from dbsync.session import get_session
    except ImportError as e:
        raise click.ClickException(
            f"Failed to import required modules: {e}\n"
            "Make sure dbsync-py is properly installed and configured."
        )

    # Test configuration and connection
    try:
        config = DatabaseConfig()
        if verbose:
            click.echo(f"Connecting to {config.host}:{config.port}/{config.database}")

        with get_session() as session:
            # Test connection
            from sqlalchemy import text

            session.execute(text("SELECT 1")).scalar()

    except Exception as e:
        raise click.ClickException(
            f"Database connection failed: {e}\n"
            "Check your database configuration (see sample.env for setup)"
        )

    # Run the examples
    try:
        with get_session() as session:
            if verbose:
                click.echo(
                    f"Running pool analysis for {pool_id} over {epochs} epochs..."
                )

            results = get_comprehensive_pool_analysis(session, pool_id, epochs)
            _output_pool_results(results, format, output_file)

    except Exception as e:
        raise click.ClickException(f"Failed to execute queries: {e}")


def _output_pool_results(
    results: dict[str, Any], format: str, output_file: str | None
) -> None:
    """Output pool analysis results in the specified format."""
    if format == "json":
        output = json.dumps(results, indent=2, default=str)
    else:
        output = _format_pool_text_output(results)

    if output_file:
        with open(output_file, "w") as f:
            f.write(output)
        click.echo(f"Results written to {output_file}")
    else:
        click.echo(output)


def _format_pool_text_output(results: dict[str, Any]) -> str:
    """Format pool analysis results as human-readable text."""
    lines = []
    lines.append("Pool Management & Block Production Examples")
    lines.append("=" * 60)

    if not results["found"]:
        lines.append(f"\n❌ Pool {results['pool_id']} not found")
        lines.append(f"Error: {results.get('error', 'Unknown error')}")
        return "\n".join(lines)

    pool_id = results["pool_id"]
    epochs = results["analysis_epochs"]
    summary = results["summary"]
    registration = results["registration_info"]
    block_production = results["block_production"]
    results["delegation_summary"]
    rewards = results["rewards_analysis"]
    status = results["operational_status"]

    lines.append(f"\nPool ID: {pool_id}")
    lines.append(f"Analysis Period: {epochs} epochs")
    lines.append(f"Status: {summary['status'].upper()}")

    lines.append("\n1. Registration Information:")
    lines.append(f"   Pledge: {registration['pledge_ada']:,.2f} ADA")
    lines.append(f"   Margin: {registration['margin_percent']:.2f}%")
    lines.append(f"   Fixed Cost: {registration['fixed_cost_ada']:.2f} ADA")
    if registration["metadata"]:
        metadata = registration["metadata"]
        if metadata.get("ticker"):
            lines.append(f"   Ticker: {metadata['ticker']}")
        if metadata.get("name"):
            lines.append(f"   Name: {metadata['name']}")

    lines.append("\n2. Block Production:")
    lines.append(f"   Total blocks produced: {summary['total_blocks']:,}")
    if block_production["epochs_analyzed"] > 0:
        avg_blocks = summary["total_blocks"] / block_production["epochs_analyzed"]
        lines.append(f"   Average per epoch: {avg_blocks:.2f}")
    lines.append(f"   Epoch range: {block_production.get('epoch_range', 'N/A')}")

    lines.append("\n3. Current Delegation:")
    lines.append(f"   Total delegators: {summary['total_delegators']:,}")
    lines.append(f"   Total stake: {summary['total_stake_ada']:,.2f} ADA")

    lines.append("\n4. Rewards (Recent Epochs):")
    lines.append(
        f"   Total rewards distributed: {summary['total_rewards_ada']:,.2f} ADA"
    )
    if rewards["epochs_analyzed"] > 0:
        avg_rewards = summary["total_rewards_ada"] / rewards["epochs_analyzed"]
        lines.append(f"   Average per epoch: {avg_rewards:.2f} ADA")

    lines.append("\n5. Operational Details:")
    lines.append(f"   Current epoch: {status.get('current_epoch', 'Unknown')}")
    if status.get("pool_hash"):
        lines.append(f"   Pool hash: {status['pool_hash'][:16]}...")

    lines.append("\n" + "=" * 60)
    lines.append("✅ Examples completed successfully!")
    lines.append("Source: dbsync.examples.queries.pool_management")

    return "\n".join(lines)


@query.command()
@click.option(
    "--stake-address",
    required=True,
    help="Stake address (bech32 format, e.g., stake1...)",
)
@click.option(
    "--format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format (text or json)",
)
@click.option(
    "--epochs",
    type=int,
    default=5,
    help="Number of recent epochs to analyze (default: 5)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file (default: stdout)",
)
@click.pass_context
def staking_delegation(
    ctx: click.Context,
    stake_address: str,
    format: str,
    epochs: int,
    output: str | None,
) -> None:
    """Run staking and delegation pattern analysis examples.

    Demonstrates comprehensive staking analysis queries including:
    - Delegation history and changes over time
    - Stake distribution patterns across pools
    - Complete delegation lifecycle tracking
    - Reward earning patterns and history
    - Active stake monitoring and network metrics

    This executes the examples from dbsync.examples.queries.staking_delegation
    """
    verbose = ctx.obj.get("verbose", False)

    try:
        _run_staking_delegation_examples(
            stake_address=stake_address,
            format=format,
            epochs=epochs,
            output_file=output,
            verbose=verbose,
        )
    except Exception as e:
        if verbose:
            raise
        click.echo(f"Error running staking delegation examples: {e}", err=True)
        sys.exit(1)


def _run_staking_delegation_examples(
    stake_address: str,
    format: str = "text",
    epochs: int = 5,
    output_file: str | None = None,
    verbose: bool = False,
) -> None:
    """Run the staking delegation query examples."""
    try:
        from dbsync.config import DatabaseConfig
        from dbsync.examples.queries.staking_delegation import (
            get_comprehensive_staking_analysis,
        )
        from dbsync.session import get_session
    except ImportError as e:
        raise click.ClickException(
            f"Failed to import required modules: {e}\n"
            "Make sure dbsync-py is properly installed and configured."
        )

    # Test configuration and connection
    try:
        config = DatabaseConfig()
        if verbose:
            click.echo(f"Connecting to {config.host}:{config.port}/{config.database}")

        with get_session() as session:
            # Test connection
            from sqlalchemy import text

            session.execute(text("SELECT 1")).scalar()

    except Exception as e:
        raise click.ClickException(
            f"Database connection failed: {e}\n"
            "Check your database configuration (see sample.env for setup)"
        )

    # Run the examples
    try:
        with get_session() as session:
            if verbose:
                click.echo(
                    f"Running staking analysis for {stake_address} over {epochs} epochs..."
                )

            results = get_comprehensive_staking_analysis(session, stake_address, epochs)
            _output_staking_results(results, format, output_file)

    except Exception as e:
        raise click.ClickException(f"Failed to execute queries: {e}")


def _output_staking_results(
    results: dict[str, Any], format: str, output_file: str | None
) -> None:
    """Output staking analysis results in the specified format."""
    if format == "json":
        output = json.dumps(results, indent=2, default=str)
    else:
        output = _format_staking_text_output(results)

    if output_file:
        with open(output_file, "w") as f:
            f.write(output)
        click.echo(f"Results written to {output_file}")
    else:
        click.echo(output)


def _format_staking_text_output(results: dict[str, Any]) -> str:
    """Format staking analysis results as human-readable text."""
    lines = []
    lines.append("Staking & Delegation Pattern Examples")
    lines.append("=" * 60)

    if not results["found"]:
        lines.append(f"\n❌ Stake address {results['stake_address']} not found")
        lines.append(f"Error: {results.get('error', 'Unknown error')}")
        return "\n".join(lines)

    stake_address = results["stake_address"]
    summary = results["summary"]
    delegation_history = results["delegation_history"]
    lifecycle = results["lifecycle"]
    rewards = results["rewards"]
    network_context = results["network_context"]

    lines.append(f"\nStake Address: {stake_address}")
    lines.append(f"Status: {'ACTIVE' if summary['is_active'] else 'INACTIVE'}")

    lines.append("\n1. Current Status:")
    lines.append(f"   Current stake: {summary['current_stake_ada']:,.2f} ADA")
    lines.append(f"   Total rewards earned: {summary['total_rewards_ada']:,.2f} ADA")
    lines.append(f"   Total delegations: {summary['delegation_count']}")

    lines.append("\n2. Delegation Lifecycle:")
    if lifecycle["registration"]["tx_id"]:
        lines.append(f"   Registered: Yes (TX: {lifecycle['registration']['tx_id']})")
    else:
        lines.append("   Registered: No")

    if lifecycle["deregistration"]["tx_id"]:
        lines.append(
            f"   Deregistered: Yes (TX: {lifecycle['deregistration']['tx_id']})"
        )
    else:
        lines.append("   Deregistered: No")

    if lifecycle["current_delegation"]["pool_hash_id"]:
        lines.append(
            f"   Current pool: {lifecycle['current_delegation']['pool_hash_id']}"
        )
        lines.append(f"   Since epoch: {lifecycle['current_delegation']['epoch']}")

    lines.append("\n3. Delegation History:")
    if delegation_history["total_delegations"] > 0:
        lines.append(
            f"   Total delegation changes: {delegation_history['total_delegations']}"
        )
        # Show first few delegations
        history = delegation_history["delegation_history"][:5]
        for i, delegation in enumerate(history, 1):
            lines.append(
                f"   {i}. Epoch {delegation['epoch']} → Pool {delegation['pool_hash_id']}"
            )
        if len(delegation_history["delegation_history"]) > 5:
            remaining = len(delegation_history["delegation_history"]) - 5
            lines.append(f"   ... and {remaining} more delegation(s)")
    else:
        lines.append("   No delegation history found")

    lines.append("\n4. Reward History:")
    if rewards["total_rewards"] > 0:
        lines.append(f"   Epochs analyzed: {rewards['epochs_analyzed']}")
        lines.append(f"   Epoch range: {rewards['epoch_range']}")
        lines.append(f"   Total rewards: {rewards['total_rewards_ada']:,.2f} ADA")
        lines.append(
            f"   Average per epoch: {rewards['total_rewards_ada'] / rewards['epochs_analyzed']:,.2f} ADA"
        )

        # Show reward history
        if rewards["rewards_history"]:
            lines.append("   Recent epochs:")
            for epoch_reward in rewards["rewards_history"][-3:]:  # Last 3 epochs
                epoch = epoch_reward["epoch"]
                total = epoch_reward["total_rewards"] / 1_000_000
                types = list(epoch_reward["by_type"].keys())
                lines.append(
                    f"     Epoch {epoch}: {total:.2f} ADA ({', '.join(types)})"
                )
    else:
        lines.append("   No rewards found in analyzed period")

    lines.append("\n5. Network Context:")
    active_monitoring = network_context["active_monitoring"]
    if active_monitoring["found"]:
        lines.append(
            f"   Network active stake: {active_monitoring['total_active_stake_ada']:,.0f} ADA"
        )
        lines.append(
            f"   Active delegators: {active_monitoring['active_delegators']:,}"
        )
        lines.append(f"   Active pools: {active_monitoring['active_pools']:,}")
        lines.append(
            f"   Average stake per delegator: {active_monitoring['average_stake_per_delegator_ada']:,.0f} ADA"
        )

    lines.append("\n" + "=" * 60)
    lines.append("✅ Examples completed successfully!")
    lines.append("Source: dbsync.examples.queries.staking_delegation")

    return "\n".join(lines)


@query.command("smart-contracts")
@click.option("--script-hash", help="Optional script hash to analyze (hex format)")
@click.option(
    "--format", "output_format", default="text", help="Output format: text or json"
)
@click.option("--days", default=30, help="Number of days to analyze")
@click.option("--output", help="Output file path")
def smart_contracts_cmd(
    script_hash: str | None, output_format: str, days: int, output: str | None
) -> None:
    """Query smart contracts and script usage patterns."""
    from ..examples.queries.smart_contracts import (
        get_comprehensive_smart_contract_analysis,
    )
    from ..session import get_session

    try:
        session = get_session()
        if not session:
            raise click.ClickException("Could not connect to database")

        result = get_comprehensive_smart_contract_analysis(session, script_hash, days)

        if output_format == "json":
            output_text = json.dumps(result, indent=2, default=str)
        else:
            output_text = format_smart_contracts_output(result)

        if output:
            with open(output, "w") as f:
                f.write(output_text)
            click.echo(f"Results written to {output}")
        else:
            click.echo(output_text)

    except Exception as e:
        raise click.ClickException(f"Query failed: {e}")


@query.command("multi-asset")
@click.option("--policy-id", help="Optional policy ID to analyze (hex format)")
@click.option(
    "--format", "output_format", default="text", help="Output format: text or json"
)
@click.option(
    "--days", default=30, help="Number of days to analyze for transfer patterns"
)
@click.option("--output", help="Output file path")
def multi_asset_cmd(
    policy_id: str | None, output_format: str, days: int, output: str | None
) -> None:
    """Query multi-asset and token operations."""
    from ..examples.queries.multi_asset import get_comprehensive_multi_asset_analysis
    from ..session import get_session

    try:
        session = get_session()
        if not session:
            raise click.ClickException("Could not connect to database")

        result = get_comprehensive_multi_asset_analysis(session, policy_id, days)

        if output_format == "json":
            output_text = json.dumps(result, indent=2, default=str)
        else:
            output_text = format_multi_asset_output(result)

        if output:
            with open(output, "w") as f:
                f.write(output_text)
            click.echo(f"Results written to {output}")
        else:
            click.echo(output_text)

    except Exception as e:
        raise click.ClickException(f"Query failed: {e}")


def format_smart_contracts_output(results: dict[str, Any]) -> str:
    """Format smart contracts analysis results as human-readable text."""
    lines = []
    lines.append("Smart Contracts & Scripts Analysis")
    lines.append("=" * 50)

    if not results.get("found"):
        lines.append("\n❌ Analysis failed")
        lines.append(f"Error: {results.get('error', 'Unknown error')}")
        return "\n".join(lines)

    lines.append(
        f"\nAnalysis Period: {results.get('analysis_period_days', 'N/A')} days"
    )

    summary = results.get("summary", {})
    lines.append("\n📊 Network Summary:")
    lines.append(f"   Total scripts: {summary.get('total_scripts', 0):,}")
    lines.append(f"   Native scripts: {summary.get('native_scripts', 0):,}")
    lines.append(f"   Plutus scripts: {summary.get('plutus_scripts', 0):,}")
    lines.append(f"   Executions (period): {summary.get('total_executions', 0):,}")

    script_analysis = results.get("script_analysis", {})
    if script_analysis.get("found") and script_analysis.get("scripts"):
        lines.append("\n🔍 Script Analysis:")
        for i, script in enumerate(script_analysis["scripts"][:5], 1):
            hash_short = (
                script["script_hash"][:16] + "..." if script["script_hash"] else "N/A"
            )
            lines.append(
                f"   {i}. {hash_short} ({script['type']}) - {script['total_usage']} uses"
            )

    lines.append("\n" + "=" * 50)
    lines.append("✅ Analysis completed")
    return "\n".join(lines)


def format_multi_asset_output(results: dict[str, Any]) -> str:
    """Format multi-asset analysis results as human-readable text."""
    lines = []
    lines.append("Multi-Asset & Token Operations Analysis")
    lines.append("=" * 50)

    if not results.get("found"):
        lines.append("\n❌ Analysis failed")
        lines.append(f"Error: {results.get('error', 'Unknown error')}")
        return "\n".join(lines)

    lines.append(
        f"\nAnalysis Period: {results.get('analysis_period_days', 'N/A')} days"
    )
    if results.get("policy_id"):
        lines.append(f"Policy ID: {results['policy_id']}")

    summary = results.get("summary", {})
    lines.append("\n📊 Network Summary:")
    lines.append(f"   Total assets: {summary.get('total_assets', 0):,}")
    lines.append(f"   Total policies: {summary.get('total_policies', 0):,}")
    lines.append(
        f"   Active assets (period): {summary.get('active_assets_period', 0):,}"
    )
    lines.append(
        f"   Total transfers (period): {summary.get('total_transfers_period', 0):,}"
    )

    portfolio = results.get("portfolio_analysis", {})
    if portfolio.get("found") and portfolio.get("portfolio"):
        lines.append("\n💰 Top Token Holdings:")
        for i, token in enumerate(portfolio["portfolio"][:5], 1):
            name = token["asset_name"] if token["asset_name"] else "Unnamed"
            lines.append(
                f"   {i}. {name[:20]} - {token['total_quantity']:,} tokens, {token['holder_count']} holders"
            )

    metadata = results.get("metadata_tracking", {})
    if metadata.get("found") and metadata.get("assets"):
        lines.append("\n📝 Recent Asset Activity:")
        for i, asset in enumerate(metadata["assets"][:3], 1):
            name = asset["asset_name"] if asset["asset_name"] else "Unnamed"
            lines.append(f"   {i}. {name[:20]} - Minted: {asset['mint_quantity']:,}")

    transfers = results.get("transfer_patterns", {})
    if transfers.get("found") and transfers.get("top_patterns"):
        lines.append("\n🔄 Top Transfer Patterns:")
        for i, pattern in enumerate(transfers["top_patterns"][:3], 1):
            name = pattern["asset_name"] if pattern["asset_name"] else "Unnamed"
            lines.append(
                f"   {i}. {name[:20]} - {pattern['transfer_count']} transfers, {pattern['unique_recipients']} recipients"
            )

    lines.append("\n" + "=" * 50)
    lines.append("✅ Analysis completed")
    return "\n".join(lines)


@query.command("governance")
@click.option(
    "--proposal-id", type=int, help="Optional governance proposal ID to analyze"
)
@click.option("--drep-id", help="Optional DRep ID to analyze (bech32 format)")
@click.option(
    "--committee-member", help="Optional committee member cold key to analyze"
)
@click.option(
    "--format", "output_format", default="text", help="Output format: text or json"
)
@click.option(
    "--days", default=30, help="Number of days to analyze for activity patterns"
)
@click.option("--output", help="Output file path")
def governance_cmd(
    proposal_id: int | None,
    drep_id: str | None,
    committee_member: str | None,
    output_format: str,
    days: int,
    output: str | None,
) -> None:
    """Query Conway era governance operations and metrics."""
    from ..examples.queries.governance import get_comprehensive_governance_analysis
    from ..session import get_session

    try:
        session = get_session()
        if not session:
            raise click.ClickException("Could not connect to database")

        result = get_comprehensive_governance_analysis(
            session, proposal_id, drep_id, committee_member, days
        )

        if output_format == "json":
            output_text = json.dumps(result, indent=2, default=str)
        else:
            output_text = format_governance_output(result)

        if output:
            with open(output, "w") as f:
                f.write(output_text)
            click.echo(f"Results written to {output}")
        else:
            click.echo(output_text)

    except Exception as e:
        raise click.ClickException(f"Query failed: {e}")


def format_governance_output(results: dict[str, Any]) -> str:
    """Format governance analysis results as human-readable text."""
    lines = []
    lines.append("Conway Era Governance Analysis")
    lines.append("=" * 50)

    if not results.get("found"):
        lines.append("\n❌ Analysis failed")
        lines.append(f"Error: {results.get('error', 'Unknown error')}")
        return "\n".join(lines)

    params = results.get("analysis_parameters", {})
    lines.append(f"\nAnalysis Period: {params.get('analysis_period_days', 'N/A')} days")
    if params.get("proposal_id"):
        lines.append(f"Proposal ID: {params['proposal_id']}")
    if params.get("drep_id"):
        lines.append(f"DRep ID: {params['drep_id']}")
    if params.get("committee_member"):
        lines.append(f"Committee Member: {params['committee_member']}")

    summary = results.get("summary", {})
    lines.append("\n📊 Governance Summary:")
    lines.append(f"   Total Proposals: {summary.get('total_proposals', 0):,}")
    lines.append(f"   Total DReps: {summary.get('total_dreps', 0):,}")
    lines.append(
        f"   Active Committee Members: {summary.get('active_committee_members', 0):,}"
    )
    lines.append(f"   Treasury Withdrawals: {summary.get('treasury_withdrawals', 0):,}")
    lines.append(f"   Total Votes: {summary.get('total_votes', 0):,}")

    # Governance Proposals
    proposals = results.get("proposal_analysis", {})
    if proposals.get("found") and proposals.get("proposals"):
        lines.append("\n🏛️ Recent Governance Proposals:")
        for i, proposal in enumerate(proposals["proposals"][:5], 1):
            lines.append(
                f"   {i}. #{proposal['index']} ({proposal['action_type']}) - {proposal['status']}"
            )
            lines.append(f"      Deposit: {proposal['deposit_lovelace']:,} lovelace")

    # DRep Activity
    drep_activity = results.get("drep_activity", {})
    if drep_activity.get("found") and drep_activity.get("delegation_leaders"):
        lines.append("\n🗳️ Top DRep Delegation Leaders:")
        for i, drep in enumerate(drep_activity["delegation_leaders"][:3], 1):
            lines.append(
                f"   {i}. {drep['drep_id'][:20]}... - {drep['delegator_count']} delegators"
            )
            lines.append(
                f"      Total stake: {drep['total_stake_lovelace']:,} lovelace"
            )

    # Committee Operations
    committee = results.get("committee_operations", {})
    if committee.get("found"):
        stats = committee.get("statistics", {})
        lines.append("\n👥 Committee Operations:")
        lines.append(f"   Total Members: {stats.get('total_members', 0)}")
        lines.append(f"   Active Members: {stats.get('active_members', 0)}")
        lines.append(f"   Total Registrations: {stats.get('total_registrations', 0)}")

    # Treasury Activity
    treasury = results.get("treasury_analysis", {})
    if treasury.get("found"):
        stats = treasury.get("statistics", {})
        lines.append("\n💰 Treasury Activity:")
        lines.append(f"   Total Withdrawals: {stats.get('total_withdrawals', 0):,}")
        lines.append(
            f"   Total Amount: {stats.get('total_amount_lovelace', 0):,} lovelace"
        )
        lines.append(f"   Unique Recipients: {stats.get('unique_recipients', 0)}")

    # Voting Metrics
    voting = results.get("voting_metrics", {})
    if voting.get("found"):
        stats = voting.get("overall_statistics", {})
        lines.append("\n🗳️ Voting Participation:")
        lines.append(f"   Total Votes: {stats.get('total_votes', 0):,}")
        lines.append(f"   Proposals Voted On: {stats.get('proposals_voted_on', 0):,}")
        lines.append(f"   Active DRep Voters: {stats.get('unique_drep_voters', 0):,}")

    lines.append("\n" + "=" * 50)
    lines.append("✅ Conway Era Governance analysis completed")
    return "\n".join(lines)
