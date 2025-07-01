#!/usr/bin/env python3
"""CLI script for running dbsync-py benchmarks."""

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from benchmark_utils import ModelBenchmarkSuite

from dbsync.models import Block, MultiAsset, Transaction


def run_model_benchmarks():
    """Run comprehensive model benchmarks."""
    print("Running dbsync-py Model Benchmarks")
    print("=" * 50)

    suite = ModelBenchmarkSuite()

    # Sample data for benchmarks
    block_data = {
        "id_": 1,
        "hash_": b"a" * 32,
        "epoch_no": 100,
        "slot_no": 1000000,
        "block_no": 500000,
        "time": "2023-01-01T12:00:00",
        "tx_count": 10,
    }

    tx_data = {
        "id_": 1,
        "hash_": b"b" * 32,
        "block_id": 1,
        "block_index": 0,
        "out_sum": 1000000,
        "fee": 170000,
    }

    asset_data = {
        "id_": 1,
        "policy": b"c" * 28,
        "name": b"TestToken",
        "fingerprint": "asset1abc123def456",
    }

    print("Benchmarking model creation...")
    suite.benchmark_model_creation(Block, block_data)
    suite.benchmark_model_creation(Transaction, tx_data)
    suite.benchmark_model_creation(MultiAsset, asset_data)

    print("Benchmarking bulk creation...")
    suite.benchmark_bulk_creation(Block, block_data, 100)
    suite.benchmark_bulk_creation(Transaction, tx_data, 100)

    print("Benchmarking serialization...")
    block = Block(**block_data)
    tx = Transaction(**tx_data)
    suite.benchmark_serialization(block)
    suite.benchmark_serialization(tx)

    # Generate and display report
    print("\n" + suite.generate_report())

    # Save results
    results_file = "benchmark_results.json"
    suite.save_results(results_file)
    print(f"\nResults saved to {results_file}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Run dbsync-py benchmarks")
    parser.add_argument(
        "--type",
        choices=["models", "queries", "all"],
        default="models",
        help="Type of benchmarks to run",
    )
    parser.add_argument("--output", help="Output file for results (JSON format)")
    parser.add_argument(
        "--rounds", type=int, default=10, help="Number of benchmark rounds"
    )

    args = parser.parse_args()

    try:
        if args.type in ["models", "all"]:
            run_model_benchmarks()

        if args.type in ["queries", "all"]:
            print("\nQuery benchmarks require database connection - run with pytest")

    except KeyboardInterrupt:
        print("\nBenchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error running benchmarks: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
