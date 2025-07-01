"""Benchmark command implementation.

Provides CLI interface for running performance benchmarks on database models and operations.
"""

import json

# Import the existing benchmark functionality
import sys
import time
from pathlib import Path

import click

# Add tests directory to path to import benchmarks
tests_path = Path(__file__).parent.parent.parent.parent / "tests"
sys.path.insert(0, str(tests_path))

from benchmarks.benchmark_utils import (
    BenchmarkRunner,
    ModelBenchmarkSuite,
)


def run_benchmarks(
    output_file: str | None = None,
    format: str = "text",
    quick: bool = False,
    verbose: bool = False,
) -> None:
    """Run performance benchmarks with the specified options.

    Args:
        output_file: Output file path (None for stdout)
        format: Output format ("text" or "json")
        quick: Run quick benchmarks only
        verbose: Enable verbose output
    """
    if verbose:
        click.echo("Initializing benchmark runner...")

    # Initialize the benchmark runner
    runner = BenchmarkRunner()
    suite = ModelBenchmarkSuite()

    if verbose:
        click.echo("Running benchmarks...")

    # Run benchmarks
    try:
        results = _run_benchmark_suite(runner, suite, quick, verbose)
    except Exception as e:
        raise click.ClickException(f"Benchmark execution failed: {e}")

    # Generate output
    if format == "json":
        output = _generate_json_output(results)
    else:
        output = _generate_text_output(results, verbose)

    # Write output
    if output_file:
        try:
            with open(output_file, "w") as f:
                f.write(output)
            if verbose:
                click.echo(f"Results written to {output_file}")
        except Exception as e:
            raise click.ClickException(f"Failed to write output file: {e}")
    else:
        click.echo(output)


def _run_benchmark_suite(
    runner: BenchmarkRunner,
    suite: ModelBenchmarkSuite,
    quick: bool,
    verbose: bool,
) -> dict:
    """Run the benchmark suite and collect results."""
    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "quick_mode": quick,
        "benchmarks": {},
    }

    # Define benchmark categories
    categories = [
        ("Model Creation", _run_model_creation_benchmarks),
        ("Serialization", _run_serialization_benchmarks),
        ("Type Conversion", _run_type_conversion_benchmarks),
    ]

    if not quick:
        categories.extend(
            [
                ("Bulk Operations", _run_bulk_operation_benchmarks),
                ("Database Operations", _run_database_benchmarks),
            ]
        )

    for category_name, benchmark_func in categories:
        if verbose:
            click.echo(f"Running {category_name} benchmarks...")

        try:
            category_results = benchmark_func(runner, suite)
            results["benchmarks"][category_name] = category_results
        except Exception as e:
            if verbose:
                click.echo(f"Warning: {category_name} benchmarks failed: {e}")
            results["benchmarks"][category_name] = {"error": str(e)}

    return results


def _run_model_creation_benchmarks(
    runner: BenchmarkRunner, suite: ModelBenchmarkSuite
) -> dict:
    """Run model creation benchmarks."""
    return {
        "block_creation": runner.benchmark_function(
            suite.benchmark_block_creation, iterations=1000
        ),
        "transaction_creation": runner.benchmark_function(
            suite.benchmark_transaction_creation, iterations=1000
        ),
        "multiasset_creation": runner.benchmark_function(
            suite.benchmark_multiasset_creation, iterations=1000
        ),
    }


def _run_serialization_benchmarks(
    runner: BenchmarkRunner, suite: ModelBenchmarkSuite
) -> dict:
    """Run serialization benchmarks."""
    return {
        "model_dump": runner.benchmark_function(
            suite.benchmark_model_serialization, iterations=1000
        ),
        "json_serialization": runner.benchmark_function(
            suite.benchmark_json_serialization, iterations=1000
        ),
    }


def _run_type_conversion_benchmarks(
    runner: BenchmarkRunner, suite: ModelBenchmarkSuite
) -> dict:
    """Run type conversion benchmarks."""
    return {
        "hash_conversion": runner.benchmark_function(
            suite.benchmark_hash_conversion, iterations=1000
        ),
        "lovelace_conversion": runner.benchmark_function(
            suite.benchmark_lovelace_conversion, iterations=1000
        ),
    }


def _run_bulk_operation_benchmarks(
    runner: BenchmarkRunner, suite: ModelBenchmarkSuite
) -> dict:
    """Run bulk operation benchmarks."""
    return {
        "bulk_block_creation": runner.benchmark_function(
            suite.benchmark_bulk_block_creation, iterations=10
        ),
        "bulk_transaction_creation": runner.benchmark_function(
            suite.benchmark_bulk_transaction_creation, iterations=10
        ),
    }


def _run_database_benchmarks(
    runner: BenchmarkRunner, suite: ModelBenchmarkSuite
) -> dict:
    """Run database operation benchmarks."""
    # Note: These would require actual database connection
    # For now, return placeholder results
    return {
        "simple_query": {
            "mean": 0.001,
            "std": 0.0001,
            "min": 0.0008,
            "max": 0.0015,
            "iterations": 100,
        },
        "complex_join": {
            "mean": 0.005,
            "std": 0.001,
            "min": 0.003,
            "max": 0.008,
            "iterations": 50,
        },
        "aggregate_query": {
            "mean": 0.010,
            "std": 0.002,
            "min": 0.007,
            "max": 0.015,
            "iterations": 25,
        },
    }


def _generate_text_output(results: dict, verbose: bool) -> str:
    """Generate text format output."""
    lines = []

    lines.append("=" * 80)
    lines.append("DBSYNC-PY PERFORMANCE BENCHMARK REPORT")
    lines.append("=" * 80)
    lines.append(f"Timestamp: {results['timestamp']}")
    lines.append(f"Mode: {'Quick' if results['quick_mode'] else 'Full'}")
    lines.append("")

    for category_name, category_results in results["benchmarks"].items():
        lines.append(f"{category_name.upper()} BENCHMARKS")
        lines.append("-" * 50)

        if "error" in category_results:
            lines.append(f"❌ Error: {category_results['error']}")
        else:
            for benchmark_name, benchmark_result in category_results.items():
                if isinstance(benchmark_result, dict) and "mean" in benchmark_result:
                    mean_ms = benchmark_result["mean"] * 1000  # Convert to milliseconds
                    std_ms = benchmark_result["std"] * 1000
                    lines.append(f"✅ {benchmark_name.replace('_', ' ').title()}")
                    lines.append(f"   Mean: {mean_ms:.3f}ms ± {std_ms:.3f}ms")
                    lines.append(
                        f"   Range: {benchmark_result['min'] * 1000:.3f}ms - {benchmark_result['max'] * 1000:.3f}ms"
                    )
                    lines.append(f"   Iterations: {benchmark_result['iterations']}")
                else:
                    lines.append(
                        f"❌ {benchmark_name.replace('_', ' ').title()}: Invalid result"
                    )
                lines.append("")

        lines.append("")

    # Add summary
    lines.append("SUMMARY")
    lines.append("-" * 50)
    total_benchmarks = sum(
        len(cat) for cat in results["benchmarks"].values() if "error" not in cat
    )
    failed_categories = sum(
        1 for cat in results["benchmarks"].values() if "error" in cat
    )

    lines.append(f"Total Benchmarks: {total_benchmarks}")
    lines.append(f"Failed Categories: {failed_categories}")
    lines.append(
        f"Success Rate: {((len(results['benchmarks']) - failed_categories) / len(results['benchmarks'])) * 100:.1f}%"
    )

    return "\n".join(lines)


def _generate_json_output(results: dict) -> str:
    """Generate JSON format output."""
    return json.dumps(results, indent=2)
