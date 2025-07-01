"""Performance baseline management for regression detection.

This module provides functionality to store, load, and compare performance baselines
to detect performance regressions in tests and benchmarks.
"""

import json
import statistics
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .monitor import PerformanceMetrics


@dataclass
class PerformanceBaseline:
    """Performance baseline data for a specific test."""

    test_name: str
    baseline_date: datetime
    sample_count: int

    # Statistical metrics (in appropriate units)
    duration_mean: float
    duration_std: float
    duration_min: float
    duration_max: float

    memory_peak_mean: int
    memory_peak_std: float
    memory_delta_mean: int
    memory_delta_std: float

    cpu_percent_mean: float
    cpu_percent_std: float

    # Thresholds for regression detection
    duration_threshold_factor: float = 1.5  # 50% increase triggers regression
    memory_threshold_factor: float = 1.3  # 30% increase triggers regression
    cpu_threshold_factor: float = 1.4  # 40% increase triggers regression

    def to_dict(self) -> dict[str, Any]:
        """Convert baseline to dictionary for serialization."""
        data = asdict(self)
        data["baseline_date"] = self.baseline_date.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PerformanceBaseline":
        """Create baseline from dictionary."""
        data = data.copy()
        data["baseline_date"] = datetime.fromisoformat(data["baseline_date"])
        return cls(**data)


@dataclass
class RegressionResult:
    """Result of regression detection analysis."""

    test_name: str
    has_regression: bool
    regression_type: str  # 'duration', 'memory', 'cpu', or 'none'

    # Current vs baseline comparison
    current_value: float
    baseline_value: float
    percentage_change: float
    threshold_exceeded: bool

    # Details
    metric_name: str
    threshold_factor: float
    message: str


class BaselineManager:
    """Manages performance baselines for regression detection."""

    def __init__(self, baseline_dir: Path = None):
        """Initialize baseline manager.

        Args:
            baseline_dir: Directory to store baseline files
        """
        self.baseline_dir = baseline_dir or Path("tests/performance/baselines")
        self.baseline_dir.mkdir(parents=True, exist_ok=True)

        self._baselines: dict[str, PerformanceBaseline] = {}
        self._load_baselines()

    def _load_baselines(self) -> None:
        """Load all existing baselines from disk."""
        for baseline_file in self.baseline_dir.glob("*.json"):
            try:
                with open(baseline_file) as f:
                    data = json.load(f)

                baseline = PerformanceBaseline.from_dict(data)
                self._baselines[baseline.test_name] = baseline
            except Exception as e:
                print(f"Warning: Failed to load baseline {baseline_file}: {e}")

    def create_baseline(
        self,
        test_name: str,
        metrics_list: list[PerformanceMetrics],
        duration_threshold: float = 1.5,
        memory_threshold: float = 1.3,
        cpu_threshold: float = 1.4,
    ) -> PerformanceBaseline:
        """Create a new performance baseline from metrics data.

        Args:
            test_name: Name of the test
            metrics_list: List of performance metrics to analyze
            duration_threshold: Threshold factor for duration regression
            memory_threshold: Threshold factor for memory regression
            cpu_threshold: Threshold factor for CPU regression

        Returns:
            Created PerformanceBaseline object
        """
        if not metrics_list:
            raise ValueError("Cannot create baseline from empty metrics list")

        # Filter metrics for this test
        test_metrics = [m for m in metrics_list if m.test_name == test_name]
        if not test_metrics:
            raise ValueError(f"No metrics found for test '{test_name}'")

        # Calculate statistical measures
        durations = [m.duration_seconds for m in test_metrics]
        memory_peaks = [m.memory_peak for m in test_metrics]
        memory_deltas = [m.memory_delta for m in test_metrics]
        cpu_percents = [m.cpu_percent for m in test_metrics]

        baseline = PerformanceBaseline(
            test_name=test_name,
            baseline_date=datetime.now(UTC),
            sample_count=len(test_metrics),
            # Duration statistics
            duration_mean=statistics.mean(durations),
            duration_std=statistics.stdev(durations) if len(durations) > 1 else 0.0,
            duration_min=min(durations),
            duration_max=max(durations),
            # Memory statistics
            memory_peak_mean=int(statistics.mean(memory_peaks)),
            memory_peak_std=statistics.stdev(memory_peaks)
            if len(memory_peaks) > 1
            else 0.0,
            memory_delta_mean=int(statistics.mean(memory_deltas)),
            memory_delta_std=statistics.stdev(memory_deltas)
            if len(memory_deltas) > 1
            else 0.0,
            # CPU statistics
            cpu_percent_mean=statistics.mean(cpu_percents),
            cpu_percent_std=statistics.stdev(cpu_percents)
            if len(cpu_percents) > 1
            else 0.0,
            # Thresholds
            duration_threshold_factor=duration_threshold,
            memory_threshold_factor=memory_threshold,
            cpu_threshold_factor=cpu_threshold,
        )

        # Store baseline
        self._baselines[test_name] = baseline
        self._save_baseline(baseline)

        return baseline

    def _save_baseline(self, baseline: PerformanceBaseline) -> None:
        """Save baseline to disk.

        Args:
            baseline: Baseline to save
        """
        filename = f"{baseline.test_name.replace('/', '_').replace('::', '_')}.json"
        filepath = self.baseline_dir / filename

        with open(filepath, "w") as f:
            json.dump(baseline.to_dict(), f, indent=2)

    def get_baseline(self, test_name: str) -> PerformanceBaseline | None:
        """Get baseline for a specific test.

        Args:
            test_name: Name of the test

        Returns:
            PerformanceBaseline if exists, None otherwise
        """
        return self._baselines.get(test_name)

    def update_baseline(
        self,
        test_name: str,
        new_metrics: list[PerformanceMetrics],
        merge_with_existing: bool = True,
    ) -> PerformanceBaseline:
        """Update existing baseline with new metrics data.

        Args:
            test_name: Name of the test
            new_metrics: New metrics to incorporate
            merge_with_existing: Whether to merge with existing baseline

        Returns:
            Updated PerformanceBaseline object
        """
        if merge_with_existing and test_name in self._baselines:
            # TODO: Implement merging logic with existing baseline
            # For now, just replace the baseline
            pass

        return self.create_baseline(test_name, new_metrics)

    def detect_regression(
        self, current_metrics: PerformanceMetrics
    ) -> list[RegressionResult]:
        """Detect performance regressions against baseline.

        Args:
            current_metrics: Current test metrics to compare

        Returns:
            List of RegressionResult objects
        """
        results = []
        baseline = self.get_baseline(current_metrics.test_name)

        if not baseline:
            # No baseline exists - not a regression
            results.append(
                RegressionResult(
                    test_name=current_metrics.test_name,
                    has_regression=False,
                    regression_type="none",
                    current_value=0.0,
                    baseline_value=0.0,
                    percentage_change=0.0,
                    threshold_exceeded=False,
                    metric_name="no_baseline",
                    threshold_factor=0.0,
                    message=f"No baseline found for test '{current_metrics.test_name}'",
                )
            )
            return results

        # Check duration regression
        duration_change = (
            current_metrics.duration_seconds - baseline.duration_mean
        ) / baseline.duration_mean
        duration_regression = current_metrics.duration_seconds > (
            baseline.duration_mean * baseline.duration_threshold_factor
        )

        results.append(
            RegressionResult(
                test_name=current_metrics.test_name,
                has_regression=duration_regression,
                regression_type="duration" if duration_regression else "none",
                current_value=current_metrics.duration_seconds,
                baseline_value=baseline.duration_mean,
                percentage_change=duration_change * 100,
                threshold_exceeded=duration_regression,
                metric_name="duration_seconds",
                threshold_factor=baseline.duration_threshold_factor,
                message=f"Duration: {current_metrics.duration_seconds:.3f}s vs baseline {baseline.duration_mean:.3f}s ({duration_change * 100:+.1f}%)",
            )
        )

        # Check memory regression
        memory_change = (
            current_metrics.memory_peak - baseline.memory_peak_mean
        ) / baseline.memory_peak_mean
        memory_regression = current_metrics.memory_peak > (
            baseline.memory_peak_mean * baseline.memory_threshold_factor
        )

        results.append(
            RegressionResult(
                test_name=current_metrics.test_name,
                has_regression=memory_regression,
                regression_type="memory" if memory_regression else "none",
                current_value=current_metrics.memory_peak,
                baseline_value=baseline.memory_peak_mean,
                percentage_change=memory_change * 100,
                threshold_exceeded=memory_regression,
                metric_name="memory_peak",
                threshold_factor=baseline.memory_threshold_factor,
                message=f"Memory: {current_metrics.memory_peak / 1024 / 1024:.1f}MB vs baseline {baseline.memory_peak_mean / 1024 / 1024:.1f}MB ({memory_change * 100:+.1f}%)",
            )
        )

        # Check CPU regression
        cpu_change = (current_metrics.cpu_percent - baseline.cpu_percent_mean) / max(
            baseline.cpu_percent_mean, 0.1
        )
        cpu_regression = current_metrics.cpu_percent > (
            baseline.cpu_percent_mean * baseline.cpu_threshold_factor
        )

        results.append(
            RegressionResult(
                test_name=current_metrics.test_name,
                has_regression=cpu_regression,
                regression_type="cpu" if cpu_regression else "none",
                current_value=current_metrics.cpu_percent,
                baseline_value=baseline.cpu_percent_mean,
                percentage_change=cpu_change * 100,
                threshold_exceeded=cpu_regression,
                metric_name="cpu_percent",
                threshold_factor=baseline.cpu_threshold_factor,
                message=f"CPU: {current_metrics.cpu_percent:.1f}% vs baseline {baseline.cpu_percent_mean:.1f}% ({cpu_change * 100:+.1f}%)",
            )
        )

        return results

    def list_baselines(self) -> list[str]:
        """List all available baseline test names.

        Returns:
            List of test names with baselines
        """
        return list(self._baselines.keys())

    def delete_baseline(self, test_name: str) -> bool:
        """Delete a baseline.

        Args:
            test_name: Name of the test baseline to delete

        Returns:
            True if baseline was deleted, False if not found
        """
        if test_name not in self._baselines:
            return False

        # Remove from memory
        del self._baselines[test_name]

        # Remove from disk
        filename = f"{test_name.replace('/', '_').replace('::', '_')}.json"
        filepath = self.baseline_dir / filename
        if filepath.exists():
            filepath.unlink()

        return True

    def get_baseline_summary(self) -> dict[str, Any]:
        """Get summary of all baselines.

        Returns:
            Dictionary with baseline summary information
        """
        if not self._baselines:
            return {"total_baselines": 0, "baselines": []}

        baseline_info = []
        for name, baseline in self._baselines.items():
            baseline_info.append(
                {
                    "test_name": name,
                    "baseline_date": baseline.baseline_date.isoformat(),
                    "sample_count": baseline.sample_count,
                    "duration_mean": baseline.duration_mean,
                    "memory_peak_mean_mb": baseline.memory_peak_mean / 1024 / 1024,
                    "cpu_percent_mean": baseline.cpu_percent_mean,
                }
            )

        return {"total_baselines": len(self._baselines), "baselines": baseline_info}
