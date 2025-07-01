"""Unit tests for performance monitoring system.

Tests all components of the performance monitoring framework including
PerformanceMonitor, BaselineManager, RegressionDetector, and PerformanceReporter.
"""

import json
import tempfile
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

from tests.performance.baseline import (
    BaselineManager,
    PerformanceBaseline,
)
from tests.performance.monitor import (
    PerformanceMetrics,
    PerformanceMonitor,
    monitor_performance,
    performance_monitor,
)
from tests.performance.profiler import ExecutionProfiler, MemoryProfiler
from tests.performance.regression import (
    RegressionDetector,
    RegressionSeverity,
    TrendAnalysis,
    TrendDirection,
)
from tests.performance.reporter import PerformanceReporter


class TestPerformanceMonitor:
    """Test cases for PerformanceMonitor class."""

    def test_monitor_initialization(self):
        """Test PerformanceMonitor initialization."""
        monitor = PerformanceMonitor(
            sample_interval=0.1,
            enable_memory_tracking=True,
            enable_cpu_tracking=True,
            enable_io_tracking=False,
        )

        assert monitor.sample_interval == 0.1
        assert monitor.enable_memory_tracking is True
        assert monitor.enable_cpu_tracking is True
        assert monitor.enable_io_tracking is False
        assert monitor._monitoring is False
        assert len(monitor._metrics_history) == 0

    def test_start_stop_monitoring(self):
        """Test starting and stopping monitoring."""
        monitor = PerformanceMonitor(sample_interval=0.01)
        test_name = "test_example"

        # Start monitoring
        monitor.start_monitoring(test_name)
        assert monitor._monitoring is True
        assert monitor._current_test == test_name
        assert monitor._start_time is not None

        # Let it run briefly
        time.sleep(0.05)

        # Stop monitoring
        metrics = monitor.stop_monitoring()
        assert monitor._monitoring is False
        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.test_name == test_name
        assert metrics.duration_seconds > 0
        assert metrics.memory_start > 0
        assert metrics.memory_end > 0

    def test_monitoring_context_manager(self):
        """Test monitoring using context manager."""
        monitor = PerformanceMonitor()
        test_name = "test_context"

        with monitor.monitor_test(test_name) as ctx:
            assert monitor._monitoring is True
            time.sleep(0.01)

        assert monitor._monitoring is False
        assert len(monitor._metrics_history) == 1
        assert monitor._metrics_history[0].test_name == test_name

    def test_custom_metrics(self):
        """Test adding custom metrics."""
        monitor = PerformanceMonitor()

        monitor.start_monitoring("test_custom")
        monitor.add_custom_metric("custom_value", 42)
        monitor.add_custom_metric("custom_string", "test")
        metrics = monitor.stop_monitoring()

        assert "custom_value" in metrics.custom_metrics
        assert metrics.custom_metrics["custom_value"] == 42
        assert metrics.custom_metrics["custom_string"] == "test"

    def test_metrics_serialization(self):
        """Test metrics serialization and deserialization."""
        monitor = PerformanceMonitor()

        monitor.start_monitoring("test_serialization")
        time.sleep(0.01)
        metrics = monitor.stop_monitoring()

        # Test to_dict
        metrics_dict = metrics.to_dict()
        assert isinstance(metrics_dict, dict)
        assert "test_name" in metrics_dict
        assert "duration_seconds" in metrics_dict
        assert "memory_start" in metrics_dict

        # Test from_dict
        restored_metrics = PerformanceMetrics.from_dict(metrics_dict)
        assert restored_metrics.test_name == metrics.test_name
        assert restored_metrics.duration_seconds == metrics.duration_seconds
        assert restored_metrics.memory_start == metrics.memory_start

    def test_global_monitor_instance(self):
        """Test global monitor instance."""
        monitor1 = performance_monitor()
        monitor2 = performance_monitor()

        assert monitor1 is monitor2  # Should be the same instance

    def test_monitor_performance_decorator(self):
        """Test performance monitoring decorator."""

        @monitor_performance("decorated_test")
        def test_function():
            time.sleep(0.01)
            return "result"

        result = test_function()
        assert result == "result"
        assert hasattr(test_function, "_performance_metrics")
        assert len(test_function._performance_metrics) == 1
        assert test_function._performance_metrics[0].test_name == "decorated_test"

    def test_save_load_metrics(self):
        """Test saving and loading metrics to/from file."""
        monitor = PerformanceMonitor()

        # Generate some metrics
        monitor.start_monitoring("test_save_load")
        time.sleep(0.01)
        metrics = monitor.stop_monitoring()

        with tempfile.TemporaryDirectory() as temp_dir:
            metrics_file = Path(temp_dir) / "test_metrics.json"

            # Save metrics
            monitor.save_metrics(metrics_file)
            assert metrics_file.exists()

            # Load metrics
            loaded_metrics = monitor.load_metrics(metrics_file)
            assert len(loaded_metrics) == 1
            assert loaded_metrics[0].test_name == "test_save_load"


class TestBaselineManager:
    """Test cases for BaselineManager class."""

    def test_baseline_manager_initialization(self):
        """Test BaselineManager initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            baseline_dir = Path(temp_dir) / "baselines"
            manager = BaselineManager(baseline_dir)

            assert manager.baseline_dir == baseline_dir
            assert baseline_dir.exists()
            assert len(manager._baselines) == 0

    def test_create_baseline(self):
        """Test creating performance baseline."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = BaselineManager(Path(temp_dir))

            # Create sample metrics
            metrics = [
                PerformanceMetrics(
                    test_name="test_baseline",
                    start_time=datetime.now(UTC),
                    end_time=datetime.now(UTC) + timedelta(seconds=1),
                    duration_seconds=1.0,
                    memory_start=1000000,
                    memory_peak=1500000,
                    memory_end=1200000,
                    memory_delta=200000,
                    cpu_percent=25.0,
                    cpu_time_user=0.5,
                    cpu_time_system=0.1,
                ),
                PerformanceMetrics(
                    test_name="test_baseline",
                    start_time=datetime.now(UTC),
                    end_time=datetime.now(UTC) + timedelta(seconds=1.2),
                    duration_seconds=1.2,
                    memory_start=1000000,
                    memory_peak=1600000,
                    memory_end=1300000,
                    memory_delta=300000,
                    cpu_percent=30.0,
                    cpu_time_user=0.6,
                    cpu_time_system=0.15,
                ),
            ]

            baseline = manager.create_baseline("test_baseline", metrics)

            assert isinstance(baseline, PerformanceBaseline)
            assert baseline.test_name == "test_baseline"
            assert baseline.sample_count == 2
            assert baseline.duration_mean == 1.1  # Average of 1.0 and 1.2
            assert (
                baseline.memory_peak_mean == 1550000
            )  # Average of 1500000 and 1600000
            assert baseline.cpu_percent_mean == 27.5  # Average of 25.0 and 30.0

    def test_baseline_persistence(self):
        """Test baseline persistence to disk."""
        with tempfile.TemporaryDirectory() as temp_dir:
            baseline_dir = Path(temp_dir)

            # Create baseline
            manager1 = BaselineManager(baseline_dir)
            metrics = [
                PerformanceMetrics(
                    test_name="test_persistence",
                    start_time=datetime.now(UTC),
                    end_time=datetime.now(UTC) + timedelta(seconds=1),
                    duration_seconds=1.0,
                    memory_start=1000000,
                    memory_peak=1500000,
                    memory_end=1200000,
                    memory_delta=200000,
                    cpu_percent=25.0,
                    cpu_time_user=0.5,
                    cpu_time_system=0.1,
                )
            ]

            baseline = manager1.create_baseline("test_persistence", metrics)
            assert "test_persistence" in manager1._baselines

            # Create new manager instance and verify baseline is loaded
            manager2 = BaselineManager(baseline_dir)
            assert "test_persistence" in manager2._baselines

            loaded_baseline = manager2.get_baseline("test_persistence")
            assert loaded_baseline.test_name == baseline.test_name
            assert loaded_baseline.duration_mean == baseline.duration_mean

    def test_regression_detection(self):
        """Test regression detection against baseline."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = BaselineManager(Path(temp_dir))

            # Create baseline with good performance
            baseline_metrics = [
                PerformanceMetrics(
                    test_name="test_regression",
                    start_time=datetime.now(UTC),
                    end_time=datetime.now(UTC) + timedelta(seconds=1),
                    duration_seconds=1.0,
                    memory_start=1000000,
                    memory_peak=1500000,
                    memory_end=1200000,
                    memory_delta=200000,
                    cpu_percent=25.0,
                    cpu_time_user=0.5,
                    cpu_time_system=0.1,
                )
            ]

            manager.create_baseline("test_regression", baseline_metrics)

            # Create metrics with regression (2x duration)
            current_metrics = PerformanceMetrics(
                test_name="test_regression",
                start_time=datetime.now(UTC),
                end_time=datetime.now(UTC) + timedelta(seconds=2),
                duration_seconds=2.0,  # 2x slower
                memory_start=1000000,
                memory_peak=1500000,
                memory_end=1200000,
                memory_delta=200000,
                cpu_percent=25.0,
                cpu_time_user=0.5,
                cpu_time_system=0.1,
            )

            regressions = manager.detect_regression(current_metrics)

            # Should detect duration regression
            duration_regressions = [
                r for r in regressions if r.metric_name == "duration_seconds"
            ]
            assert len(duration_regressions) == 1
            assert duration_regressions[0].has_regression is True
            assert duration_regressions[0].percentage_change > 0


class TestRegressionDetector:
    """Test cases for RegressionDetector class."""

    def test_detector_initialization(self):
        """Test RegressionDetector initialization."""
        detector = RegressionDetector(sensitivity=1.5, min_samples=5, trend_window=15)

        assert detector.sensitivity == 1.5
        assert detector.min_samples == 5
        assert detector.trend_window == 15

    def test_trend_analysis(self):
        """Test trend analysis functionality."""
        detector = RegressionDetector()

        # Create metrics with degrading trend
        metrics = []
        for i in range(10):
            metrics.append(
                PerformanceMetrics(
                    test_name="test_trend",
                    start_time=datetime.now(UTC) + timedelta(minutes=i),
                    end_time=datetime.now(UTC)
                    + timedelta(minutes=i, seconds=1 + i * 0.1),
                    duration_seconds=1.0 + i * 0.1,  # Increasing duration
                    memory_start=1000000,
                    memory_peak=1500000 + i * 50000,  # Increasing memory
                    memory_end=1200000,
                    memory_delta=200000,
                    cpu_percent=25.0 + i * 2,  # Increasing CPU
                    cpu_time_user=0.5,
                    cpu_time_system=0.1,
                )
            )

        trends = detector.analyze_trends(metrics, "test_trend")

        assert "duration" in trends
        assert "memory_peak" in trends
        assert "cpu_percent" in trends

        # Should detect degrading trends
        duration_trend = trends["duration"]
        assert duration_trend.direction in [
            TrendDirection.DEGRADING,
            TrendDirection.STABLE,
        ]
        assert duration_trend.slope > 0  # Positive slope indicates increase

    def test_advanced_regression_detection(self):
        """Test advanced regression detection with statistical analysis."""
        detector = RegressionDetector(sensitivity=1.0)

        # Create historical metrics
        historical_metrics = []
        for i in range(5):
            historical_metrics.append(
                PerformanceMetrics(
                    test_name="test_advanced",
                    start_time=datetime.now(UTC) + timedelta(minutes=i),
                    end_time=datetime.now(UTC) + timedelta(minutes=i, seconds=1),
                    duration_seconds=1.0,
                    memory_start=1000000,
                    memory_peak=1500000,
                    memory_end=1200000,
                    memory_delta=200000,
                    cpu_percent=25.0,
                    cpu_time_user=0.5,
                    cpu_time_system=0.1,
                )
            )

        # Create current metrics with significant regression
        current_metrics = PerformanceMetrics(
            test_name="test_advanced",
            start_time=datetime.now(UTC),
            end_time=datetime.now(UTC) + timedelta(seconds=3),
            duration_seconds=3.0,  # 3x slower
            memory_start=1000000,
            memory_peak=3000000,  # 2x more memory
            memory_end=1200000,
            memory_delta=200000,
            cpu_percent=75.0,  # 3x more CPU
            cpu_time_user=0.5,
            cpu_time_system=0.1,
        )

        alerts = detector.detect_advanced_regressions(
            current_metrics, historical_metrics
        )

        # Should detect multiple regressions
        assert len(alerts) > 0

        # Check for duration regression
        duration_alerts = [a for a in alerts if a.metric_name == "duration_seconds"]
        if duration_alerts:
            assert duration_alerts[0].has_regression is True
            assert duration_alerts[0].severity in [
                RegressionSeverity.HIGH,
                RegressionSeverity.CRITICAL,
            ]

    def test_regression_severity_determination(self):
        """Test regression severity determination logic."""
        detector = RegressionDetector()

        # Create a simple trend for testing
        trend = TrendAnalysis(
            metric_name="test_metric",
            direction=TrendDirection.DEGRADING,
            slope=0.1,
            r_squared=0.8,
            volatility=0.05,
            recent_average=2.0,
            historical_average=1.0,
            percentage_change=100.0,
        )

        # Test different deviation levels
        severity_low = detector._determine_severity(20.0, trend)  # 20% deviation
        severity_medium = detector._determine_severity(40.0, trend)  # 40% deviation
        severity_high = detector._determine_severity(80.0, trend)  # 80% deviation
        severity_critical = detector._determine_severity(150.0, trend)  # 150% deviation

        assert severity_low in [RegressionSeverity.LOW, RegressionSeverity.MEDIUM]
        assert severity_medium in [RegressionSeverity.MEDIUM, RegressionSeverity.HIGH]
        assert severity_high in [RegressionSeverity.HIGH, RegressionSeverity.CRITICAL]
        assert severity_critical == RegressionSeverity.CRITICAL


class TestPerformanceReporter:
    """Test cases for PerformanceReporter class."""

    def test_reporter_initialization(self):
        """Test PerformanceReporter initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            reporter = PerformanceReporter(output_dir)

            assert reporter.output_dir == output_dir
            assert output_dir.exists()

    def test_json_report_generation(self):
        """Test JSON report generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            reporter = PerformanceReporter(Path(temp_dir))

            # Create sample metrics
            metrics = [
                PerformanceMetrics(
                    test_name="test_json_report",
                    start_time=datetime.now(UTC),
                    end_time=datetime.now(UTC) + timedelta(seconds=1),
                    duration_seconds=1.0,
                    memory_start=1000000,
                    memory_peak=1500000,
                    memory_end=1200000,
                    memory_delta=200000,
                    cpu_percent=25.0,
                    cpu_time_user=0.5,
                    cpu_time_system=0.1,
                )
            ]

            report_path = reporter.generate_json_report(metrics)

            assert report_path.exists()
            assert report_path.suffix == ".json"

            # Verify report content
            with open(report_path) as f:
                report_data = json.load(f)

            assert "timestamp" in report_data
            assert "summary" in report_data
            assert "metrics" in report_data
            assert len(report_data["metrics"]) == 1
            assert report_data["metrics"][0]["test_name"] == "test_json_report"

    def test_html_report_generation(self):
        """Test HTML report generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            reporter = PerformanceReporter(Path(temp_dir))

            # Create sample metrics
            metrics = [
                PerformanceMetrics(
                    test_name="test_html_report",
                    start_time=datetime.now(UTC),
                    end_time=datetime.now(UTC) + timedelta(seconds=1),
                    duration_seconds=1.0,
                    memory_start=1000000,
                    memory_peak=1500000,
                    memory_end=1200000,
                    memory_delta=200000,
                    cpu_percent=25.0,
                    cpu_time_user=0.5,
                    cpu_time_system=0.1,
                )
            ]

            report_path = reporter.generate_html_report(
                metrics, title="Test HTML Report"
            )

            assert report_path.exists()
            assert report_path.suffix == ".html"

            # Verify HTML content
            with open(report_path) as f:
                html_content = f.read()

            assert "Test HTML Report" in html_content
            assert "test_html_report" in html_content
            assert "Performance Analysis" in html_content


class TestMemoryProfiler:
    """Test cases for MemoryProfiler class."""

    def test_memory_profiler_initialization(self):
        """Test MemoryProfiler initialization."""
        profiler = MemoryProfiler(enable_tracemalloc=True)

        assert profiler.enable_tracemalloc is True
        assert len(profiler._snapshots) == 0
        assert profiler._tracing_started is False

    def test_memory_snapshot(self):
        """Test taking memory snapshots."""
        profiler = MemoryProfiler(enable_tracemalloc=False)  # Disable for simpler test

        snapshot = profiler.take_snapshot()

        assert snapshot.current_memory > 0
        assert snapshot.timestamp > 0
        assert len(profiler._snapshots) == 1

    def test_memory_profiling_context(self):
        """Test memory profiling context manager."""
        profiler = MemoryProfiler()

        with profiler.profile_memory(take_snapshots=True):
            # Allocate some memory
            data = [i for i in range(1000)]
            time.sleep(0.01)

        assert len(profiler._snapshots) >= 2  # Start and end snapshots
        growth_analysis = profiler.get_memory_growth()
        assert "total_growth_bytes" in growth_analysis


class TestExecutionProfiler:
    """Test cases for ExecutionProfiler class."""

    def test_execution_profiler_initialization(self):
        """Test ExecutionProfiler initialization."""
        profiler = ExecutionProfiler()

        assert profiler._profiler is None
        assert profiler._stats is None

    def test_execution_profiling_context(self):
        """Test execution profiling context manager."""
        profiler = ExecutionProfiler()

        def test_function():
            time.sleep(0.01)
            return sum(i for i in range(100))

        with profiler.profile_execution():
            result = test_function()

        assert result == sum(i for i in range(100))

        # Get profiling results
        summary = profiler.get_profile_summary()
        assert "total_calls" in summary
        assert "total_time_seconds" in summary
        assert "top_functions" in summary
        assert summary["total_calls"] > 0


class TestIntegration:
    """Integration tests for the complete performance monitoring system."""

    def test_end_to_end_monitoring(self):
        """Test complete end-to-end performance monitoring workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Initialize components
            monitor = PerformanceMonitor()
            baseline_manager = BaselineManager(temp_path / "baselines")
            detector = RegressionDetector()
            reporter = PerformanceReporter(temp_path / "reports")

            # Step 1: Collect baseline metrics
            baseline_metrics = []
            for i in range(3):
                monitor.start_monitoring("test_integration")
                time.sleep(0.01)
                metrics = monitor.stop_monitoring()
                baseline_metrics.append(metrics)

            # Step 2: Create baseline
            baseline = baseline_manager.create_baseline(
                "test_integration", baseline_metrics
            )
            assert baseline.sample_count == 3

            # Step 3: Collect current metrics (with slight regression)
            monitor.start_monitoring("test_integration")
            time.sleep(0.02)  # Slightly slower
            current_metrics = monitor.stop_monitoring()

            # Step 4: Detect regressions
            regressions = detector.detect_advanced_regressions(
                current_metrics, baseline_metrics, baseline
            )

            # Step 5: Generate reports
            all_metrics = baseline_metrics + [current_metrics]

            json_report = reporter.generate_json_report(
                all_metrics, {baseline.test_name: baseline}, regressions
            )

            html_report = reporter.generate_html_report(
                all_metrics,
                {baseline.test_name: baseline},
                regressions,
                "Integration Test Report",
            )

            # Verify outputs
            assert json_report.exists()
            assert html_report.exists()

            # Verify report content
            with open(json_report) as f:
                json_data = json.load(f)

            assert json_data["summary"]["total_metrics"] == 4
            assert json_data["summary"]["baselines_count"] == 1
            assert len(json_data["metrics"]) == 4
            assert len(json_data["baselines"]) == 1
