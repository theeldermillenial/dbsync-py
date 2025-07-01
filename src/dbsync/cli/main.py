#!/usr/bin/env python3
"""Main CLI entry point for dbsync-py package.

Provides command-line interface for schema validation, benchmarking, and other utilities.
"""

import sys

import click

from ..config import get_version


@click.group()
@click.version_option(version=get_version(), prog_name="dbsync-py")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def main(ctx: click.Context, verbose: bool) -> None:
    """dbsync-py: Python helper package for Cardano DB Sync databases.

    Provides tools for schema validation, performance benchmarking, database operations,
    and query examples demonstrating package usage.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


@main.command()
@click.option(
    "--format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format (text or json)",
)
@click.option("--coverage-only", is_flag=True, help="Show only coverage statistics")
@click.option("--errors-only", is_flag=True, help="Show only validation errors")
@click.option("--output", "-o", type=click.Path(), help="Output file (default: stdout)")
@click.pass_context
def validate(
    ctx: click.Context,
    format: str,
    coverage_only: bool,
    errors_only: bool,
    output: str | None,
) -> None:
    """Validate database schema against official Cardano DB Sync schema.

    Downloads the latest schema from the official repository and validates
    all implemented models against it, reporting any discrepancies.
    """
    from .validate import run_validation

    verbose = ctx.obj.get("verbose", False)

    try:
        run_validation(
            format=format,
            coverage_only=coverage_only,
            errors_only=errors_only,
            output_file=output,
            verbose=verbose,
        )
    except Exception as e:
        if verbose:
            raise
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file for benchmark results (default: stdout)",
)
@click.option(
    "--format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format (text or json)",
)
@click.option("--quick", is_flag=True, help="Run quick benchmarks only")
@click.pass_context
def benchmark(ctx: click.Context, output: str | None, format: str, quick: bool) -> None:
    """Run performance benchmarks on database models and operations.

    Measures performance of model creation, serialization, and database operations
    to establish baselines and detect performance regressions.
    """
    from .benchmark import run_benchmarks

    verbose = ctx.obj.get("verbose", False)

    try:
        run_benchmarks(output_file=output, format=format, quick=quick, verbose=verbose)
    except Exception as e:
        if verbose:
            raise
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option("--check-connection", is_flag=True, help="Test database connection")
@click.option("--show-config", is_flag=True, help="Show current configuration")
@click.pass_context
def info(ctx: click.Context, check_connection: bool, show_config: bool) -> None:
    """Show information about the dbsync-py installation and configuration."""
    from .info import show_info

    verbose = ctx.obj.get("verbose", False)

    try:
        show_info(
            check_connection=check_connection, show_config=show_config, verbose=verbose
        )
    except Exception as e:
        if verbose:
            raise
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


# Add query examples commands
try:
    from .query import query

    main.add_command(query)
except ImportError:
    pass  # Query examples not available

# Add performance monitoring commands if available
try:
    from .performance import performance

    main.add_command(performance)
except ImportError:
    pass  # Performance monitoring dependencies not available

# Add coverage analysis commands if available
try:
    from .coverage import coverage

    main.add_command(coverage)
except ImportError:
    pass  # Coverage analysis dependencies not available


if __name__ == "__main__":
    main()
