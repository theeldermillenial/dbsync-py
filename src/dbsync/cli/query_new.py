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
