"""Core performance monitoring functionality.

This module provides the main PerformanceMonitor class and related utilities
for tracking test execution performance, memory usage, and system resources.
"""

import json
import threading
import time
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psutil


@dataclass
class PerformanceMetrics:
    """Container for performance metrics collected during test execution."""

    test_name: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float

    # Memory metrics (in bytes)
    memory_start: int
    memory_peak: int
    memory_end: int
    memory_delta: int

    # CPU metrics
    cpu_percent: float
    cpu_time_user: float
    cpu_time_system: float

    # System metrics
    disk_io_read: int = 0
    disk_io_write: int = 0
    network_io_sent: int = 0
    network_io_recv: int = 0

    # Custom metrics
    custom_metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary for serialization."""
        return {
            "test_name": self.test_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_seconds": self.duration_seconds,
            "memory_start": self.memory_start,
            "memory_peak": self.memory_peak,
            "memory_end": self.memory_end,
            "memory_delta": self.memory_delta,
            "cpu_percent": self.cpu_percent,
            "cpu_time_user": self.cpu_time_user,
            "cpu_time_system": self.cpu_time_system,
            "disk_io_read": self.disk_io_read,
            "disk_io_write": self.disk_io_write,
            "network_io_sent": self.network_io_sent,
            "network_io_recv": self.network_io_recv,
            "custom_metrics": self.custom_metrics,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PerformanceMetrics":
        """Create metrics from dictionary."""
        data = data.copy()
        data["start_time"] = datetime.fromisoformat(data["start_time"])
        data["end_time"] = datetime.fromisoformat(data["end_time"])
        return cls(**data)


class PerformanceMonitor:
    """Main performance monitoring class.

    Provides comprehensive monitoring of test execution including memory usage,
    CPU utilization, I/O operations, and custom metrics collection.
    """

    def __init__(
        self,
        sample_interval: float = 0.1,
        enable_memory_tracking: bool = True,
        enable_cpu_tracking: bool = True,
        enable_io_tracking: bool = True,
    ):
        """Initialize performance monitor.

        Args:
            sample_interval: Interval in seconds for sampling system metrics
            enable_memory_tracking: Whether to track memory usage
            enable_cpu_tracking: Whether to track CPU usage
            enable_io_tracking: Whether to track I/O operations
        """
        self.sample_interval = sample_interval
        self.enable_memory_tracking = enable_memory_tracking
        self.enable_cpu_tracking = enable_cpu_tracking
        self.enable_io_tracking = enable_io_tracking

        self._monitoring = False
        self._monitor_thread: threading.Thread | None = None
        self._metrics_history: list[PerformanceMetrics] = []

        # Current monitoring state
        self._current_test: str | None = None
        self._start_time: datetime | None = None
        self._memory_samples: list[int] = []
        self._cpu_samples: list[float] = []

        # System baseline
        self._process = psutil.Process()
        self._baseline_memory = self._process.memory_info().rss
        self._baseline_cpu_times = self._process.cpu_times()
        self._baseline_io = (
            self._process.io_counters() if self.enable_io_tracking else None
        )

    def start_monitoring(self, test_name: str) -> None:
        """Start monitoring for a specific test.

        Args:
            test_name: Name of the test being monitored
        """
        if self._monitoring:
            self.stop_monitoring()

        self._current_test = test_name
        self._start_time = datetime.now(UTC)
        self._memory_samples = []
        self._cpu_samples = []
        self._monitoring = True

        # Reset baseline measurements
        self._baseline_memory = self._process.memory_info().rss
        self._baseline_cpu_times = self._process.cpu_times()
        if self.enable_io_tracking:
            self._baseline_io = self._process.io_counters()

        # Start monitoring thread
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop_monitoring(self) -> PerformanceMetrics:
        """Stop monitoring and return collected metrics.

        Returns:
            PerformanceMetrics object with collected data
        """
        if not self._monitoring:
            raise RuntimeError("Monitoring not active")

        self._monitoring = False

        # Wait for monitor thread to finish
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1.0)

        end_time = datetime.now(UTC)
        duration = (end_time - self._start_time).total_seconds()

        # Calculate final metrics
        current_memory = self._process.memory_info().rss
        current_cpu_times = self._process.cpu_times()

        memory_peak = (
            max(self._memory_samples) if self._memory_samples else current_memory
        )
        cpu_avg = (
            sum(self._cpu_samples) / len(self._cpu_samples)
            if self._cpu_samples
            else 0.0
        )

        # I/O metrics
        disk_read = disk_write = net_sent = net_recv = 0
        if self.enable_io_tracking and self._baseline_io:
            current_io = self._process.io_counters()
            disk_read = current_io.read_bytes - self._baseline_io.read_bytes
            disk_write = current_io.write_bytes - self._baseline_io.write_bytes
            # Network I/O would require additional system-level monitoring

        # Get custom metrics for this session
        custom_metrics = getattr(self, "_current_custom_metrics", {})

        metrics = PerformanceMetrics(
            test_name=self._current_test,
            start_time=self._start_time,
            end_time=end_time,
            duration_seconds=duration,
            memory_start=self._baseline_memory,
            memory_peak=memory_peak,
            memory_end=current_memory,
            memory_delta=current_memory - self._baseline_memory,
            cpu_percent=cpu_avg,
            cpu_time_user=current_cpu_times.user - self._baseline_cpu_times.user,
            cpu_time_system=current_cpu_times.system - self._baseline_cpu_times.system,
            disk_io_read=disk_read,
            disk_io_write=disk_write,
            network_io_sent=net_sent,
            network_io_recv=net_recv,
            custom_metrics=custom_metrics.copy(),
        )

        # Clear custom metrics for next session
        self._current_custom_metrics = {}

        self._metrics_history.append(metrics)
        return metrics

    def _monitor_loop(self) -> None:
        """Background monitoring loop that samples system metrics."""
        while self._monitoring:
            try:
                if self.enable_memory_tracking:
                    memory_info = self._process.memory_info()
                    self._memory_samples.append(memory_info.rss)

                if self.enable_cpu_tracking:
                    cpu_percent = self._process.cpu_percent()
                    self._cpu_samples.append(cpu_percent)

                time.sleep(self.sample_interval)
            except Exception:
                # Continue monitoring even if individual samples fail
                pass

    def add_custom_metric(self, name: str, value: Any) -> None:
        """Add a custom metric to the current monitoring session.

        Args:
            name: Metric name
            value: Metric value
        """
        if not self._monitoring:
            raise RuntimeError("Monitoring not active")

        # Store custom metrics in a temporary dict for the current session
        if not hasattr(self, "_current_custom_metrics"):
            self._current_custom_metrics = {}
        self._current_custom_metrics[name] = value

    def get_metrics_history(self) -> list[PerformanceMetrics]:
        """Get all collected metrics history.

        Returns:
            List of PerformanceMetrics objects
        """
        return self._metrics_history.copy()

    def clear_history(self) -> None:
        """Clear all collected metrics history."""
        self._metrics_history.clear()

    def save_metrics(self, filepath: Path) -> None:
        """Save metrics history to JSON file.

        Args:
            filepath: Path to save metrics file
        """
        data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "metrics": [m.to_dict() for m in self._metrics_history],
        }

        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def load_metrics(self, filepath: Path) -> list[PerformanceMetrics]:
        """Load metrics history from JSON file.

        Args:
            filepath: Path to metrics file

        Returns:
            List of loaded PerformanceMetrics objects
        """
        with open(filepath) as f:
            data = json.load(f)

        return [PerformanceMetrics.from_dict(m) for m in data["metrics"]]

    @contextmanager
    def monitor_test(self, test_name: str):
        """Context manager for monitoring a test.

        Args:
            test_name: Name of the test to monitor

        Yields:
            PerformanceMonitor instance during monitoring
        """
        self.start_monitoring(test_name)
        try:
            yield self
        finally:
            self.stop_monitoring()


# Global performance monitor instance
_global_monitor = PerformanceMonitor()


def performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance.

    Returns:
        Global PerformanceMonitor instance
    """
    return _global_monitor


# Decorator for automatic performance monitoring
def monitor_performance(test_name: str | None = None):
    """Decorator to automatically monitor test performance.

    Args:
        test_name: Optional test name (defaults to function name)

    Returns:
        Decorated function with performance monitoring
    """
    from functools import wraps

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            name = test_name or func.__name__
            monitor = performance_monitor()

            monitor.start_monitoring(name)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                metrics = monitor.stop_monitoring()
                # Store metrics in wrapper function for later access
                if not hasattr(wrapper, "_performance_metrics"):
                    wrapper._performance_metrics = []
                wrapper._performance_metrics.append(metrics)

        return wrapper

    return decorator
