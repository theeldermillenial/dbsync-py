"""Performance monitoring fixtures for pytest integration.

This module provides pytest fixtures that automatically collect performance metrics
during test execution, enabling seamless performance monitoring and regression detection.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from .baseline import BaselineManager
from .monitor import PerformanceMetrics, PerformanceMonitor, performance_monitor
from .profiler import ExecutionProfiler, MemoryProfiler
from .regression import RegressionAlert, RegressionDetector
from .reporter import PerformanceReporter


@pytest.fixture(scope="session")
def performance_output_dir(tmp_path_factory) -> Path:
    """Provide a temporary directory for performance monitoring output."""
    return tmp_path_factory.mktemp("performance")


@pytest.fixture(scope="session")
def baseline_manager(performance_output_dir) -> BaselineManager:
    """Provide a BaselineManager instance for the test session."""
    baseline_dir = performance_output_dir / "baselines"
    return BaselineManager(baseline_dir)


@pytest.fixture(scope="session")
def regression_detector() -> RegressionDetector:
    """Provide a RegressionDetector instance for the test session."""
    return RegressionDetector(sensitivity=1.0, min_samples=2)


@pytest.fixture(scope="session")
def performance_reporter(performance_output_dir) -> PerformanceReporter:
    """Provide a PerformanceReporter instance for the test session."""
    reports_dir = performance_output_dir / "reports"
    return PerformanceReporter(reports_dir)


@pytest.fixture
def performance_monitor_instance() -> PerformanceMonitor:
    """Provide a fresh PerformanceMonitor instance for each test."""
    return PerformanceMonitor(
        sample_interval=0.05,  # Faster sampling for tests
        enable_memory_tracking=True,
        enable_cpu_tracking=True,
        enable_io_tracking=True,
    )


@pytest.fixture
def memory_profiler() -> MemoryProfiler:
    """Provide a MemoryProfiler instance for detailed memory analysis."""
    return MemoryProfiler(enable_tracemalloc=True)


@pytest.fixture
def execution_profiler() -> ExecutionProfiler:
    """Provide an ExecutionProfiler instance for execution analysis."""
    return ExecutionProfiler()


@pytest.fixture(autouse=True)
def auto_performance_monitoring(request, performance_monitor_instance):
    """Automatically monitor performance for all tests.

    This fixture automatically starts performance monitoring at the beginning
    of each test and collects metrics at the end. Tests can opt out by using
    the 'no_performance_monitoring' marker.
    """
    # Check if test should skip performance monitoring
    if request.node.get_closest_marker("no_performance_monitoring"):
        yield
        return

    # Get test name
    test_name = request.node.nodeid

    # Start monitoring
    performance_monitor_instance.start_monitoring(test_name)

    try:
        yield performance_monitor_instance
    finally:
        # Stop monitoring and collect metrics
        try:
            metrics = performance_monitor_instance.stop_monitoring()

            # Store metrics in test node for later access
            if not hasattr(request.node, "performance_metrics"):
                request.node.performance_metrics = []
            request.node.performance_metrics.append(metrics)

        except Exception:
            # Don't fail tests due to monitoring issues
            pass


@pytest.fixture
def performance_context(
    request,
    performance_monitor_instance,
    baseline_manager,
    regression_detector,
    performance_reporter,
):
    """Provide a comprehensive performance monitoring context.

    This fixture provides access to all performance monitoring components
    and automatically handles baseline comparison and regression detection.
    """
    test_name = request.node.nodeid

    class PerformanceContext:
        def __init__(self):
            self.monitor = performance_monitor_instance
            self.baseline_manager = baseline_manager
            self.detector = regression_detector
            self.reporter = performance_reporter
            self.test_name = test_name
            self.metrics: PerformanceMetrics | None = None
            self.regressions: list[RegressionAlert] = []

        def start_monitoring(self):
            """Start performance monitoring."""
            self.monitor.start_monitoring(self.test_name)

        def stop_monitoring(self) -> PerformanceMetrics:
            """Stop monitoring and return metrics."""
            self.metrics = self.monitor.stop_monitoring()
            return self.metrics

        def check_regressions(self) -> list[RegressionAlert]:
            """Check for performance regressions."""
            if not self.metrics:
                return []

            baseline = self.baseline_manager.get_baseline(self.test_name)
            metrics_history = self.monitor.get_metrics_history()

            self.regressions = self.detector.detect_advanced_regressions(
                self.metrics, metrics_history, baseline
            )
            return self.regressions

        def create_baseline(self, metrics_list: list[PerformanceMetrics] | None = None):
            """Create or update baseline for this test."""
            metrics_to_use = metrics_list or [self.metrics] if self.metrics else []
            if metrics_to_use:
                return self.baseline_manager.create_baseline(
                    self.test_name, metrics_to_use
                )

        def add_custom_metric(self, name: str, value: Any):
            """Add a custom metric to the current monitoring session."""
            self.monitor.add_custom_metric(name, value)

    return PerformanceContext()


@pytest.fixture
def benchmark_performance(performance_context):
    """Fixture for benchmarking-focused performance monitoring.

    Automatically starts/stops monitoring and provides benchmarking utilities.
    """

    class BenchmarkContext:
        def __init__(self, perf_context):
            self.perf = perf_context
            self._benchmark_data = {}

        def benchmark_operation(
            self, operation_name: str, operation_func, *args, **kwargs
        ):
            """Benchmark a specific operation."""
            import time

            start_time = time.perf_counter()
            result = operation_func(*args, **kwargs)
            end_time = time.perf_counter()

            duration = end_time - start_time
            self._benchmark_data[operation_name] = duration
            self.perf.add_custom_metric(
                f"benchmark_{operation_name}_duration", duration
            )

            return result

        def get_benchmark_results(self) -> dict[str, float]:
            """Get all benchmark results."""
            return self._benchmark_data.copy()

        def compare_with_baseline(
            self, operation_name: str, expected_duration: float, tolerance: float = 0.1
        ):
            """Compare benchmark result with expected baseline."""
            if operation_name not in self._benchmark_data:
                pytest.fail(f"No benchmark data for operation '{operation_name}'")

            actual_duration = self._benchmark_data[operation_name]
            max_allowed = expected_duration * (1 + tolerance)

            if actual_duration > max_allowed:
                pytest.fail(
                    f"Performance regression in '{operation_name}': "
                    f"{actual_duration:.4f}s > {max_allowed:.4f}s "
                    f"(expected {expected_duration:.4f}s ± {tolerance * 100:.1f}%)"
                )

    performance_context.start_monitoring()

    try:
        yield BenchmarkContext(performance_context)
    finally:
        performance_context.stop_monitoring()
        regressions = performance_context.check_regressions()

        # Report any regressions as test failures
        if regressions:
            regression_messages = [r.message for r in regressions if r.has_regression]
            if regression_messages:
                pytest.fail(
                    "Performance regressions detected:\n"
                    + "\n".join(regression_messages)
                )


@pytest.fixture
def memory_monitoring(memory_profiler):
    """Fixture for detailed memory monitoring during tests."""

    class MemoryContext:
        def __init__(self, profiler):
            self.profiler = profiler
            self.snapshots = []

        def start_monitoring(self):
            """Start memory monitoring."""
            self.profiler.start_tracing()
            self.take_snapshot("start")

        def stop_monitoring(self):
            """Stop memory monitoring."""
            self.take_snapshot("end")
            self.profiler.stop_tracing()

        def take_snapshot(self, label: str = None):
            """Take a memory snapshot."""
            snapshot = self.profiler.take_snapshot()
            if label:
                snapshot.label = label
            self.snapshots.append(snapshot)
            return snapshot

        def get_memory_growth(self):
            """Get memory growth analysis."""
            return self.profiler.get_memory_growth()

        def assert_memory_limit(self, max_memory_mb: float):
            """Assert that memory usage stays below limit."""
            if self.snapshots:
                peak_memory = max(s.current_memory for s in self.snapshots)
                peak_memory_mb = peak_memory / 1024 / 1024

                if peak_memory_mb > max_memory_mb:
                    pytest.fail(
                        f"Memory limit exceeded: {peak_memory_mb:.1f}MB > {max_memory_mb:.1f}MB"
                    )

        def assert_no_memory_leaks(self, tolerance_mb: float = 1.0):
            """Assert that there are no significant memory leaks."""
            if len(self.snapshots) >= 2:
                start_memory = self.snapshots[0].current_memory / 1024 / 1024
                end_memory = self.snapshots[-1].current_memory / 1024 / 1024
                growth = end_memory - start_memory

                if growth > tolerance_mb:
                    pytest.fail(
                        f"Potential memory leak detected: {growth:.1f}MB growth"
                    )

    context = MemoryContext(memory_profiler)
    context.start_monitoring()

    try:
        yield context
    finally:
        context.stop_monitoring()


@pytest.fixture(scope="session", autouse=True)
def performance_session_teardown(request, performance_output_dir):
    """Session-level teardown for performance monitoring.

    Collects all performance metrics from the session and generates reports.
    """

    def teardown():
        try:
            # Collect all performance metrics from test nodes
            all_metrics = []
            for item in request.session.items:
                if hasattr(item, "performance_metrics"):
                    all_metrics.extend(item.performance_metrics)

            if not all_metrics:
                return

            # Save metrics to file
            metrics_file = (
                performance_output_dir
                / f"session_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )

            # Use global performance monitor to save metrics
            monitor = performance_monitor()
            monitor._metrics_history = all_metrics
            monitor.save_metrics(metrics_file)

            print("\nPerformance monitoring session completed:")
            print(
                f"  Total tests monitored: {len(set(m.test_name for m in all_metrics))}"
            )
            print(f"  Total metrics collected: {len(all_metrics)}")
            print(f"  Metrics saved to: {metrics_file}")

            # Generate summary report if requested
            if request.config.getoption("--performance-report", default=False):
                reporter = PerformanceReporter(performance_output_dir / "reports")
                report_path = reporter.generate_html_report(
                    all_metrics, title="Test Session Performance Report"
                )
                print(f"  Performance report: {report_path}")

        except Exception as e:
            print(f"Warning: Failed to generate performance session report: {e}")

    request.addfinalizer(teardown)


# Pytest configuration hooks
def pytest_addoption(parser):
    """Add performance monitoring options to pytest."""
    group = parser.getgroup("performance", "Performance monitoring options")

    group.addoption(
        "--performance-report",
        action="store_true",
        default=False,
        help="Generate performance report after test session",
    )

    group.addoption(
        "--performance-baseline",
        action="store_true",
        default=False,
        help="Create performance baselines from test results",
    )

    group.addoption(
        "--performance-regression-check",
        action="store_true",
        default=False,
        help="Check for performance regressions during tests",
    )


def pytest_configure(config):
    """Configure performance monitoring markers."""
    config.addinivalue_line(
        "markers",
        "no_performance_monitoring: disable automatic performance monitoring for this test",
    )
    config.addinivalue_line(
        "markers", "performance_baseline: mark test for baseline creation"
    )
    config.addinivalue_line(
        "markers",
        "performance_critical: mark test as performance-critical (stricter thresholds)",
    )


def pytest_runtest_teardown(item, nextitem):
    """Per-test teardown for performance monitoring."""
    # Check for performance regressions if enabled
    if item.config.getoption("--performance-regression-check") and hasattr(
        item, "performance_metrics"
    ):
        try:
            detector = RegressionDetector()
            baseline_manager = BaselineManager()

            for metrics in item.performance_metrics:
                baseline = baseline_manager.get_baseline(metrics.test_name)
                if baseline:
                    regressions = detector.detect_advanced_regressions(
                        metrics, [], baseline
                    )

                    critical_regressions = [r for r in regressions if r.has_regression]
                    if critical_regressions:
                        # Report regression as test failure
                        regression_msg = "\n".join(
                            r.message for r in critical_regressions
                        )
                        pytest.fail(
                            f"Performance regression detected:\n{regression_msg}"
                        )

        except Exception:
            # Don't fail tests due to regression detection issues
            pass
