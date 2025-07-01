"""Coverage Trend Tracking.

This module provides functionality to track coverage trends over time,
detect regressions, and maintain historical coverage data.
"""

import json
import statistics
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class CoverageTrend:
    """Represents coverage trend data over time."""

    timestamp: str
    line_coverage: float
    branch_coverage: float
    function_coverage: float
    overall_score: float
    test_count: int
    commit_hash: str | None = None
    branch_name: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CoverageTrend":
        """Create CoverageTrend from dictionary."""
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class CoverageTracker:
    """Tracks coverage trends and maintains historical data."""

    def __init__(self, data_dir: Path = Path("coverage_history")):
        """Initialize coverage tracker.

        Args:
            data_dir: Directory to store historical coverage data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.history_file = self.data_dir / "coverage_history.json"
        self.trends_file = self.data_dir / "coverage_trends.json"

    def record_coverage(
        self,
        line_coverage: float,
        branch_coverage: float,
        function_coverage: float,
        overall_score: float,
        test_count: int,
        commit_hash: str | None = None,
        branch_name: str | None = None,
    ) -> CoverageTrend:
        """Record new coverage data point.

        Args:
            line_coverage: Line coverage percentage
            branch_coverage: Branch coverage percentage
            function_coverage: Function coverage percentage
            overall_score: Overall coverage quality score
            test_count: Number of tests
            commit_hash: Git commit hash
            branch_name: Git branch name

        Returns:
            Created CoverageTrend object
        """
        trend = CoverageTrend(
            timestamp=datetime.now(UTC).isoformat(),
            line_coverage=line_coverage,
            branch_coverage=branch_coverage,
            function_coverage=function_coverage,
            overall_score=overall_score,
            test_count=test_count,
            commit_hash=commit_hash,
            branch_name=branch_name,
        )

        # Load existing history
        history = self.load_history()
        history.append(trend)

        # Keep only last 100 entries to prevent file growth
        if len(history) > 100:
            history = history[-100:]

        # Save updated history
        self.save_history(history)

        # Update trend analysis
        self._update_trend_analysis(history)

        return trend

    def load_history(self) -> list[CoverageTrend]:
        """Load coverage history from file.

        Returns:
            List of historical coverage trends
        """
        if not self.history_file.exists():
            return []

        try:
            with open(self.history_file) as f:
                data = json.load(f)

            return [CoverageTrend.from_dict(item) for item in data]

        except Exception as e:
            print(f"Error loading coverage history: {e}")
            return []

    def save_history(self, history: list[CoverageTrend]) -> None:
        """Save coverage history to file.

        Args:
            history: List of coverage trends to save
        """
        try:
            with open(self.history_file, "w") as f:
                json.dump([trend.to_dict() for trend in history], f, indent=2)

        except Exception as e:
            print(f"Error saving coverage history: {e}")

    def get_recent_trends(self, days: int = 30) -> list[CoverageTrend]:
        """Get coverage trends from recent period.

        Args:
            days: Number of days to look back

        Returns:
            List of recent coverage trends
        """
        history = self.load_history()
        cutoff_time = datetime.now(UTC).timestamp() - (days * 24 * 60 * 60)

        recent_trends = []
        for trend in history:
            try:
                trend_time = datetime.fromisoformat(
                    trend.timestamp.replace("Z", "+00:00")
                ).timestamp()
                if trend_time >= cutoff_time:
                    recent_trends.append(trend)
            except Exception:
                continue

        return recent_trends

    def analyze_trend_direction(
        self, metric: str = "line_coverage", period_days: int = 7
    ) -> dict[str, Any]:
        """Analyze trend direction for a specific metric.

        Args:
            metric: Metric to analyze ('line_coverage', 'branch_coverage', etc.)
            period_days: Period in days to analyze

        Returns:
            Dictionary with trend analysis
        """
        recent_trends = self.get_recent_trends(period_days)

        if len(recent_trends) < 2:
            return {
                "direction": "insufficient_data",
                "slope": 0.0,
                "confidence": 0.0,
                "current_value": 0.0,
                "change_percentage": 0.0,
            }

        # Extract metric values
        values = []
        for trend in recent_trends:
            if hasattr(trend, metric):
                values.append(getattr(trend, metric))

        if len(values) < 2:
            return {
                "direction": "no_data",
                "slope": 0.0,
                "confidence": 0.0,
                "current_value": 0.0,
                "change_percentage": 0.0,
            }

        # Calculate linear regression slope
        n = len(values)
        x_values = list(range(n))

        # Calculate slope using least squares
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(values)

        numerator = sum(
            (x - x_mean) * (y - y_mean) for x, y in zip(x_values, values, strict=False)
        )
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        slope = numerator / denominator if denominator != 0 else 0.0

        # Calculate R-squared for confidence
        y_pred = [y_mean + slope * (x - x_mean) for x in x_values]
        ss_res = sum(
            (y - y_pred) ** 2 for y, y_pred in zip(values, y_pred, strict=False)
        )
        ss_tot = sum((y - y_mean) ** 2 for y in values)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0

        # Determine direction
        if abs(slope) < 0.1:
            direction = "stable"
        elif slope > 0:
            direction = "improving"
        else:
            direction = "declining"

        # Calculate percentage change
        change_pct = (
            ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0.0
        )

        return {
            "direction": direction,
            "slope": slope,
            "confidence": r_squared,
            "current_value": values[-1],
            "change_percentage": change_pct,
            "data_points": len(values),
        }

    def detect_coverage_regression(
        self, threshold_percentage: float = 5.0
    ) -> dict[str, Any]:
        """Detect significant coverage regressions.

        Args:
            threshold_percentage: Minimum percentage drop to consider regression

        Returns:
            Dictionary with regression analysis
        """
        history = self.load_history()

        if len(history) < 2:
            return {
                "has_regression": False,
                "message": "Insufficient data for regression analysis",
            }

        # Compare current with recent average
        current = history[-1]
        recent_history = history[-10:-1] if len(history) > 10 else history[:-1]

        regressions = []

        # Check each coverage metric
        metrics = [
            "line_coverage",
            "branch_coverage",
            "function_coverage",
            "overall_score",
        ]

        for metric in metrics:
            current_value = getattr(current, metric)
            recent_values = [getattr(trend, metric) for trend in recent_history]

            if not recent_values:
                continue

            recent_avg = statistics.mean(recent_values)

            if recent_avg > 0:
                percentage_drop = ((recent_avg - current_value) / recent_avg) * 100

                if percentage_drop > threshold_percentage:
                    regressions.append(
                        {
                            "metric": metric,
                            "current_value": current_value,
                            "recent_average": recent_avg,
                            "percentage_drop": percentage_drop,
                            "severity": "high" if percentage_drop > 10 else "medium",
                        }
                    )

        return {
            "has_regression": len(regressions) > 0,
            "regressions": regressions,
            "timestamp": current.timestamp,
            "commit_hash": current.commit_hash,
            "message": f"Found {len(regressions)} coverage regressions"
            if regressions
            else "No regressions detected",
        }

    def get_coverage_statistics(self, period_days: int = 30) -> dict[str, Any]:
        """Get coverage statistics for a period.

        Args:
            period_days: Period in days to analyze

        Returns:
            Dictionary with coverage statistics
        """
        trends = self.get_recent_trends(period_days)

        if not trends:
            return {"error": "No data available for the specified period"}

        # Calculate statistics for each metric
        metrics = [
            "line_coverage",
            "branch_coverage",
            "function_coverage",
            "overall_score",
        ]
        stats = {}

        for metric in metrics:
            values = [getattr(trend, metric) for trend in trends]

            if values:
                stats[metric] = {
                    "current": values[-1],
                    "average": statistics.mean(values),
                    "median": statistics.median(values),
                    "min": min(values),
                    "max": max(values),
                    "std_dev": statistics.stdev(values) if len(values) > 1 else 0.0,
                    "trend": self.analyze_trend_direction(metric, period_days),
                }

        return {
            "period_days": period_days,
            "data_points": len(trends),
            "first_timestamp": trends[0].timestamp,
            "last_timestamp": trends[-1].timestamp,
            "statistics": stats,
        }

    def _update_trend_analysis(self, history: list[CoverageTrend]) -> None:
        """Update trend analysis file with latest data.

        Args:
            history: Complete coverage history
        """
        if len(history) < 2:
            return

        # Analyze trends for different periods
        trend_analysis = {
            "last_updated": datetime.now(UTC).isoformat(),
            "total_data_points": len(history),
            "periods": {},
        }

        for period in [7, 30, 90]:
            period_trends = self.get_recent_trends(period)

            if len(period_trends) >= 2:
                trend_analysis["periods"][f"{period}_days"] = {
                    "line_coverage": self.analyze_trend_direction(
                        "line_coverage", period
                    ),
                    "branch_coverage": self.analyze_trend_direction(
                        "branch_coverage", period
                    ),
                    "function_coverage": self.analyze_trend_direction(
                        "function_coverage", period
                    ),
                    "overall_score": self.analyze_trend_direction(
                        "overall_score", period
                    ),
                }

        # Save trend analysis
        try:
            with open(self.trends_file, "w") as f:
                json.dump(trend_analysis, f, indent=2)
        except Exception as e:
            print(f"Error saving trend analysis: {e}")

    def export_trends_csv(self, output_file: Path) -> None:
        """Export coverage trends to CSV file.

        Args:
            output_file: Path to output CSV file
        """
        import csv

        history = self.load_history()

        if not history:
            return

        try:
            with open(output_file, "w", newline="") as csvfile:
                fieldnames = [
                    "timestamp",
                    "line_coverage",
                    "branch_coverage",
                    "function_coverage",
                    "overall_score",
                    "test_count",
                    "commit_hash",
                    "branch_name",
                ]

                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for trend in history:
                    writer.writerow(trend.to_dict())

        except Exception as e:
            print(f"Error exporting trends to CSV: {e}")

    def cleanup_old_data(self, keep_days: int = 365) -> None:
        """Clean up old coverage data.

        Args:
            keep_days: Number of days of data to keep
        """
        history = self.load_history()
        cutoff_time = datetime.now(UTC).timestamp() - (keep_days * 24 * 60 * 60)

        filtered_history = []
        for trend in history:
            try:
                trend_time = datetime.fromisoformat(
                    trend.timestamp.replace("Z", "+00:00")
                ).timestamp()
                if trend_time >= cutoff_time:
                    filtered_history.append(trend)
            except Exception:
                continue

        if len(filtered_history) != len(history):
            self.save_history(filtered_history)
            print(
                f"Cleaned up coverage history: {len(history) - len(filtered_history)} old entries removed"
            )
