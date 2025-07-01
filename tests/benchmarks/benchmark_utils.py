"""Benchmark utilities and helper functions."""

import os
import statistics
import time
from collections.abc import Callable
from contextlib import contextmanager
from typing import Any

import psutil


class BenchmarkRunner:
    """Custom benchmark runner for detailed performance analysis."""

    def __init__(self, warmup_rounds: int = 3, test_rounds: int = 10):
        self.warmup_rounds = warmup_rounds
        self.test_rounds = test_rounds

    def run_benchmark(self, func: Callable, *args, **kwargs) -> dict[str, Any]:
        """Run a benchmark with detailed statistics."""
        # Warmup rounds
        for _ in range(self.warmup_rounds):
            func(*args, **kwargs)

        # Actual benchmark rounds
        times = []
        memory_usage = []

        for _ in range(self.test_rounds):
            with self._measure_resources() as resources:
                start_time = time.perf_counter()
                result = func(*args, **kwargs)
                end_time = time.perf_counter()

            times.append(end_time - start_time)
            memory_usage.append(resources["peak_memory"])

        return {
            "result": result,
            "times": times,
            "mean_time": statistics.mean(times),
            "median_time": statistics.median(times),
            "stdev_time": statistics.stdev(times) if len(times) > 1 else 0,
            "min_time": min(times),
            "max_time": max(times),
            "memory_usage": memory_usage,
            "mean_memory": statistics.mean(memory_usage),
            "peak_memory": max(memory_usage),
            "rounds": self.test_rounds,
        }

    @contextmanager
    def _measure_resources(self):
        """Context manager to measure resource usage."""
        process = psutil.Process(os.getpid())
        start_memory = process.memory_info().rss
        peak_memory = start_memory

        resources = {"peak_memory": peak_memory}

        try:
            yield resources
        finally:
            current_memory = process.memory_info().rss
            resources["peak_memory"] = max(peak_memory, current_memory)


class ModelBenchmarkSuite:
    """Comprehensive benchmark suite for model operations."""

    def __init__(self):
        self.runner = BenchmarkRunner()
        self.results = {}

    def benchmark_model_creation(
        self, model_class, sample_data: dict[str, Any], name: str = None
    ) -> dict[str, Any]:
        """Benchmark model instantiation."""
        if name is None:
            name = f"{model_class.__name__}_creation"

        def create_model():
            return model_class(**sample_data)

        results = self.runner.run_benchmark(create_model)
        self.results[name] = results
        return results

    def benchmark_bulk_creation(
        self,
        model_class,
        sample_data: dict[str, Any],
        count: int = 100,
        name: str = None,
    ) -> dict[str, Any]:
        """Benchmark bulk model creation."""
        if name is None:
            name = f"{model_class.__name__}_bulk_creation_{count}"

        def create_bulk():
            models = []
            for i in range(count):
                data = sample_data.copy()
                if "id_" in data:
                    data["id_"] = i + 1
                models.append(model_class(**data))
            return models

        results = self.runner.run_benchmark(create_bulk)
        self.results[name] = results
        return results

    def benchmark_serialization(
        self, model_instance, name: str = None
    ) -> dict[str, Any]:
        """Benchmark model serialization."""
        if name is None:
            name = f"{model_instance.__class__.__name__}_serialization"

        def serialize():
            return model_instance.model_dump()

        results = self.runner.run_benchmark(serialize)
        self.results[name] = results
        return results

    def benchmark_validation(
        self,
        model_class,
        valid_data: dict[str, Any],
        invalid_data: dict[str, Any],
        name: str = None,
    ) -> dict[str, Any]:
        """Benchmark model validation with both valid and invalid data."""
        if name is None:
            name = f"{model_class.__name__}_validation"

        def validate():
            # Test valid data
            valid_model = model_class(**valid_data)

            # Test invalid data (expect validation error)
            try:
                invalid_model = model_class(**invalid_data)
            except Exception:
                pass  # Expected validation error

            return valid_model

        results = self.runner.run_benchmark(validate)
        self.results[name] = results
        return results

    def generate_report(self) -> str:
        """Generate a formatted benchmark report."""
        if not self.results:
            return "No benchmark results available."

        report = ["Benchmark Results", "=" * 50, ""]

        for name, result in self.results.items():
            report.extend(
                [
                    f"Test: {name}",
                    f"  Mean Time: {result['mean_time']:.6f}s",
                    f"  Median Time: {result['median_time']:.6f}s",
                    f"  Std Dev: {result['stdev_time']:.6f}s",
                    f"  Min Time: {result['min_time']:.6f}s",
                    f"  Max Time: {result['max_time']:.6f}s",
                    f"  Mean Memory: {result['mean_memory'] / 1024 / 1024:.2f}MB",
                    f"  Peak Memory: {result['peak_memory'] / 1024 / 1024:.2f}MB",
                    f"  Rounds: {result['rounds']}",
                    "",
                ]
            )

        return "\n".join(report)

    def save_results(self, filename: str):
        """Save benchmark results to a file."""
        import json

        # Convert results to JSON-serializable format
        json_results = {}
        for name, result in self.results.items():
            json_results[name] = {
                k: v
                for k, v in result.items()
                if k != "result"  # Exclude the actual result object
            }

        with open(filename, "w") as f:
            json.dump(json_results, f, indent=2)


def compare_benchmarks(
    results1: dict[str, Any],
    results2: dict[str, Any],
    name1: str = "Benchmark 1",
    name2: str = "Benchmark 2",
) -> str:
    """Compare two benchmark results."""
    if not results1 or not results2:
        return "Cannot compare: missing benchmark results"

    comparison = [f"Benchmark Comparison: {name1} vs {name2}", "=" * 60, ""]

    # Find common tests
    common_tests = set(results1.keys()) & set(results2.keys())

    if not common_tests:
        return "No common tests found for comparison"

    for test in sorted(common_tests):
        r1, r2 = results1[test], results2[test]

        time_diff = ((r2["mean_time"] - r1["mean_time"]) / r1["mean_time"]) * 100
        memory_diff = (
            (r2["mean_memory"] - r1["mean_memory"]) / r1["mean_memory"]
        ) * 100

        comparison.extend(
            [
                f"Test: {test}",
                f"  Time - {name1}: {r1['mean_time']:.6f}s, {name2}: {r2['mean_time']:.6f}s",
                f"  Time Difference: {time_diff:+.2f}%",
                f"  Memory - {name1}: {r1['mean_memory'] / 1024 / 1024:.2f}MB, {name2}: {r2['mean_memory'] / 1024 / 1024:.2f}MB",
                f"  Memory Difference: {memory_diff:+.2f}%",
                "",
            ]
        )

    return "\n".join(comparison)


def performance_regression_check(
    baseline_results: dict[str, Any],
    current_results: dict[str, Any],
    time_threshold: float = 0.1,
    memory_threshold: float = 0.1,
) -> tuple[bool, list[str]]:
    """Check for performance regressions against baseline."""
    regressions = []

    for test_name in current_results:
        if test_name not in baseline_results:
            continue

        baseline = baseline_results[test_name]
        current = current_results[test_name]

        # Check time regression
        time_increase = (current["mean_time"] - baseline["mean_time"]) / baseline[
            "mean_time"
        ]
        if time_increase > time_threshold:
            regressions.append(
                f"{test_name}: Time regression {time_increase:.2%} "
                f"(threshold: {time_threshold:.2%})"
            )

        # Check memory regression
        memory_increase = (current["mean_memory"] - baseline["mean_memory"]) / baseline[
            "mean_memory"
        ]
        if memory_increase > memory_threshold:
            regressions.append(
                f"{test_name}: Memory regression {memory_increase:.2%} "
                f"(threshold: {memory_threshold:.2%})"
            )

    return len(regressions) == 0, regressions
