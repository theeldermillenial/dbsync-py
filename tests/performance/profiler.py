"""Profiling utilities for detailed performance analysis.

This module provides memory profiling and execution profiling capabilities
for in-depth analysis of test performance characteristics.
"""

import cProfile
import io
import pstats
import time
import tracemalloc
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from memory_profiler import LineProfiler
    from memory_profiler import profile as memory_profile

    MEMORY_PROFILER_AVAILABLE = True
except ImportError:
    MEMORY_PROFILER_AVAILABLE = False
    memory_profile = None
    LineProfiler = None


@dataclass
class MemorySnapshot:
    """Memory usage snapshot at a specific point in time."""

    timestamp: float
    current_memory: int  # bytes
    peak_memory: int  # bytes
    memory_blocks: int  # number of allocated blocks

    # Top memory allocations (if tracemalloc is used)
    top_allocations: list[dict[str, Any]] = None


@dataclass
class ExecutionProfile:
    """Execution profiling results."""

    function_name: str
    total_time: float
    cumulative_time: float
    call_count: int
    per_call_time: float
    filename: str
    line_number: int


class MemoryProfiler:
    """Memory profiling utilities for tracking memory usage patterns."""

    def __init__(self, enable_tracemalloc: bool = True):
        """Initialize memory profiler.

        Args:
            enable_tracemalloc: Whether to enable detailed memory tracing
        """
        self.enable_tracemalloc = enable_tracemalloc
        self._snapshots: list[MemorySnapshot] = []
        self._tracing_started = False

    def start_tracing(self) -> None:
        """Start memory tracing."""
        if self.enable_tracemalloc and not self._tracing_started:
            tracemalloc.start()
            self._tracing_started = True
        self._snapshots.clear()

    def stop_tracing(self) -> None:
        """Stop memory tracing."""
        if self._tracing_started:
            tracemalloc.stop()
            self._tracing_started = False

    def take_snapshot(self) -> MemorySnapshot:
        """Take a memory usage snapshot.

        Returns:
            MemorySnapshot with current memory state
        """
        import psutil

        process = psutil.Process()
        memory_info = process.memory_info()

        top_allocations = None
        memory_blocks = 0

        if self._tracing_started:
            snapshot = tracemalloc.take_snapshot()
            memory_blocks = len(snapshot.traces)

            # Get top 10 memory allocations
            top_stats = snapshot.statistics("lineno")[:10]
            top_allocations = []
            for stat in top_stats:
                top_allocations.append(
                    {
                        "filename": stat.traceback.format()[0]
                        if stat.traceback.format()
                        else "unknown",
                        "size_bytes": stat.size,
                        "count": stat.count,
                        "size_mb": stat.size / 1024 / 1024,
                    }
                )

        snapshot = MemorySnapshot(
            timestamp=time.time(),
            current_memory=memory_info.rss,
            peak_memory=memory_info.peak_wset
            if hasattr(memory_info, "peak_wset")
            else memory_info.rss,
            memory_blocks=memory_blocks,
            top_allocations=top_allocations,
        )

        self._snapshots.append(snapshot)
        return snapshot

    def get_snapshots(self) -> list[MemorySnapshot]:
        """Get all memory snapshots.

        Returns:
            List of MemorySnapshot objects
        """
        return self._snapshots.copy()

    def get_memory_growth(self) -> dict[str, Any]:
        """Analyze memory growth pattern.

        Returns:
            Dictionary with memory growth analysis
        """
        if len(self._snapshots) < 2:
            return {"error": "Need at least 2 snapshots for growth analysis"}

        first = self._snapshots[0]
        last = self._snapshots[-1]

        total_growth = last.current_memory - first.current_memory
        time_span = last.timestamp - first.timestamp
        growth_rate = total_growth / time_span if time_span > 0 else 0

        # Find peak memory usage
        peak_memory = max(s.current_memory for s in self._snapshots)
        peak_snapshot = next(
            s for s in self._snapshots if s.current_memory == peak_memory
        )

        return {
            "total_growth_bytes": total_growth,
            "total_growth_mb": total_growth / 1024 / 1024,
            "growth_rate_bytes_per_sec": growth_rate,
            "growth_rate_mb_per_sec": growth_rate / 1024 / 1024,
            "peak_memory_bytes": peak_memory,
            "peak_memory_mb": peak_memory / 1024 / 1024,
            "peak_timestamp": peak_snapshot.timestamp,
            "snapshots_count": len(self._snapshots),
            "time_span_seconds": time_span,
        }

    @contextmanager
    def profile_memory(
        self, take_snapshots: bool = True, snapshot_interval: float = 0.5
    ):
        """Context manager for memory profiling.

        Args:
            take_snapshots: Whether to automatically take snapshots
            snapshot_interval: Interval between automatic snapshots
        """
        self.start_tracing()

        if take_snapshots:
            self.take_snapshot()  # Initial snapshot

        try:
            yield self
        finally:
            if take_snapshots:
                self.take_snapshot()  # Final snapshot

            self.stop_tracing()


class ExecutionProfiler:
    """Execution profiling utilities for analyzing function call performance."""

    def __init__(self):
        """Initialize execution profiler."""
        self._profiler: cProfile.Profile | None = None
        self._stats: pstats.Stats | None = None

    def start_profiling(self) -> None:
        """Start execution profiling."""
        self._profiler = cProfile.Profile()
        self._profiler.enable()

    def stop_profiling(self) -> None:
        """Stop execution profiling."""
        if self._profiler:
            self._profiler.disable()

            # Create stats from profiler
            stats_stream = io.StringIO()
            self._stats = pstats.Stats(self._profiler, stream=stats_stream)

    def get_top_functions(self, count: int = 20) -> list[ExecutionProfile]:
        """Get top functions by execution time.

        Args:
            count: Number of top functions to return

        Returns:
            List of ExecutionProfile objects
        """
        if not self._stats:
            return []

        # Sort by cumulative time
        self._stats.sort_stats("cumulative")

        profiles = []
        for func_info, (call_count, _, total_time, cumulative_time, callers) in list(
            self._stats.stats.items()
        )[:count]:
            filename, line_number, function_name = func_info

            per_call_time = total_time / call_count if call_count > 0 else 0

            profiles.append(
                ExecutionProfile(
                    function_name=function_name,
                    total_time=total_time,
                    cumulative_time=cumulative_time,
                    call_count=call_count,
                    per_call_time=per_call_time,
                    filename=filename,
                    line_number=line_number,
                )
            )

        return profiles

    def save_profile(self, filepath: Path) -> None:
        """Save profile data to file.

        Args:
            filepath: Path to save profile data
        """
        if not self._stats:
            raise RuntimeError("No profile data available")

        filepath.parent.mkdir(parents=True, exist_ok=True)
        self._stats.dump_stats(str(filepath))

    def get_profile_summary(self) -> dict[str, Any]:
        """Get summary of profiling results.

        Returns:
            Dictionary with profile summary
        """
        if not self._stats:
            return {"error": "No profile data available"}

        # Get basic stats
        total_calls = self._stats.total_calls
        total_time = sum(stat[2] for stat in self._stats.stats.values())  # total time

        # Get top functions
        top_functions = self.get_top_functions(10)

        return {
            "total_calls": total_calls,
            "total_time_seconds": total_time,
            "top_functions": [
                {
                    "function": f.function_name,
                    "filename": f.filename,
                    "line": f.line_number,
                    "total_time": f.total_time,
                    "cumulative_time": f.cumulative_time,
                    "call_count": f.call_count,
                    "per_call_time": f.per_call_time,
                }
                for f in top_functions
            ],
        }

    @contextmanager
    def profile_execution(self):
        """Context manager for execution profiling."""
        self.start_profiling()
        try:
            yield self
        finally:
            self.stop_profiling()


# Decorator for automatic memory profiling
def profile_memory_usage(func: Callable = None, *, line_by_line: bool = False):
    """Decorator for automatic memory profiling.

    Args:
        func: Function to decorate
        line_by_line: Whether to profile line by line (requires memory_profiler)

    Returns:
        Decorated function with memory profiling
    """

    def decorator(f: Callable) -> Callable:
        if line_by_line and MEMORY_PROFILER_AVAILABLE:
            # Use line-by-line memory profiler
            return memory_profile(f)
        else:
            # Use our custom memory profiler
            def wrapper(*args, **kwargs):
                profiler = MemoryProfiler()
                with profiler.profile_memory():
                    result = f(*args, **kwargs)

                # Store profiling results in function
                if not hasattr(f, "_memory_profiles"):
                    f._memory_profiles = []
                f._memory_profiles.append(profiler.get_memory_growth())

                return result

            return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


# Decorator for automatic execution profiling
def profile_execution_time(func: Callable) -> Callable:
    """Decorator for automatic execution profiling.

    Args:
        func: Function to decorate

    Returns:
        Decorated function with execution profiling
    """

    def wrapper(*args, **kwargs):
        profiler = ExecutionProfiler()
        with profiler.profile_execution():
            result = func(*args, **kwargs)

        # Store profiling results in function
        if not hasattr(func, "_execution_profiles"):
            func._execution_profiles = []
        func._execution_profiles.append(profiler.get_profile_summary())

        return result

    return wrapper
