"""Advanced regression detection and analysis.

This module provides sophisticated regression detection capabilities including
statistical analysis, trend detection, and automated alerting for performance
degradation.
"""

import statistics
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from .baseline import PerformanceBaseline
from .monitor import PerformanceMetrics


class RegressionSeverity(Enum):
    """Severity levels for performance regressions."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TrendDirection(Enum):
    """Trend direction for performance metrics."""

    IMPROVING = "improving"
    STABLE = "stable"
    DEGRADING = "degrading"
    VOLATILE = "volatile"


@dataclass
class TrendAnalysis:
    """Analysis of performance trends over time."""

    metric_name: str
    direction: TrendDirection
    slope: float  # Rate of change per unit time
    r_squared: float  # Correlation coefficient
    volatility: float  # Standard deviation of changes

    # Trend statistics
    recent_average: float
    historical_average: float
    percentage_change: float

    # Predictions
    predicted_next_value: float | None = None
    confidence_interval: tuple[float, float] | None = None


@dataclass
class RegressionAlert:
    """Alert for detected performance regression."""

    test_name: str
    severity: RegressionSeverity
    metric_name: str

    current_value: float
    expected_value: float
    deviation_percentage: float

    message: str
    timestamp: datetime
    has_regression: bool = True  # Whether this alert represents a regression

    # Context
    trend_analysis: TrendAnalysis | None = None
    historical_context: dict[str, Any] | None = None


class RegressionDetector:
    """Advanced regression detection with statistical analysis."""

    def __init__(
        self, sensitivity: float = 1.0, min_samples: int = 3, trend_window: int = 10
    ):
        """Initialize regression detector.

        Args:
            sensitivity: Detection sensitivity (0.5 = less sensitive, 2.0 = more sensitive)
            min_samples: Minimum samples needed for trend analysis
            trend_window: Number of recent samples to use for trend analysis
        """
        self.sensitivity = sensitivity
        self.min_samples = min_samples
        self.trend_window = trend_window

    def analyze_trends(
        self, metrics_history: list[PerformanceMetrics], test_name: str
    ) -> dict[str, TrendAnalysis]:
        """Analyze performance trends for a specific test.

        Args:
            metrics_history: Historical performance metrics
            test_name: Name of the test to analyze

        Returns:
            Dictionary of trend analyses by metric name
        """
        # Filter metrics for this test
        test_metrics = [m for m in metrics_history if m.test_name == test_name]
        test_metrics.sort(key=lambda m: m.start_time)

        if len(test_metrics) < self.min_samples:
            return {}

        trends = {}

        # Analyze duration trend
        durations = [m.duration_seconds for m in test_metrics]
        trends["duration"] = self._analyze_metric_trend(
            "duration_seconds", durations, test_metrics
        )

        # Analyze memory trend
        memory_peaks = [m.memory_peak for m in test_metrics]
        trends["memory_peak"] = self._analyze_metric_trend(
            "memory_peak", memory_peaks, test_metrics
        )

        # Analyze CPU trend
        cpu_percents = [m.cpu_percent for m in test_metrics]
        trends["cpu_percent"] = self._analyze_metric_trend(
            "cpu_percent", cpu_percents, test_metrics
        )

        # Analyze memory delta trend
        memory_deltas = [m.memory_delta for m in test_metrics]
        trends["memory_delta"] = self._analyze_metric_trend(
            "memory_delta", memory_deltas, test_metrics
        )

        return trends

    def _analyze_metric_trend(
        self, metric_name: str, values: list[float], metrics: list[PerformanceMetrics]
    ) -> TrendAnalysis:
        """Analyze trend for a specific metric.

        Args:
            metric_name: Name of the metric
            values: List of metric values
            metrics: Corresponding metrics objects

        Returns:
            TrendAnalysis object
        """
        n = len(values)
        if n < 2:
            return TrendAnalysis(
                metric_name=metric_name,
                direction=TrendDirection.STABLE,
                slope=0.0,
                r_squared=0.0,
                volatility=0.0,
                recent_average=values[0] if values else 0.0,
                historical_average=values[0] if values else 0.0,
                percentage_change=0.0,
            )

        # Calculate linear regression
        x_values = list(range(n))
        slope, r_squared = self._linear_regression(x_values, values)

        # Calculate volatility (standard deviation of changes)
        changes = [values[i] - values[i - 1] for i in range(1, n)]
        volatility = statistics.stdev(changes) if len(changes) > 1 else 0.0

        # Recent vs historical averages
        recent_window = min(self.trend_window, n // 2) if n > 4 else n // 2
        recent_values = values[-recent_window:] if recent_window > 0 else values
        historical_values = (
            values[:-recent_window]
            if recent_window > 0 and recent_window < n
            else values
        )

        recent_avg = statistics.mean(recent_values)
        historical_avg = (
            statistics.mean(historical_values) if historical_values else recent_avg
        )

        percentage_change = (
            ((recent_avg - historical_avg) / historical_avg * 100)
            if historical_avg != 0
            else 0.0
        )

        # Determine trend direction
        direction = self._determine_trend_direction(
            slope, r_squared, volatility, percentage_change
        )

        # Predict next value
        predicted_next = values[-1] + slope if slope != 0 else values[-1]

        # Calculate confidence interval (simple approach)
        residuals = [
            values[i]
            - (
                slope * i
                + (statistics.mean(values) - slope * statistics.mean(x_values))
            )
            for i in range(n)
        ]
        residual_std = statistics.stdev(residuals) if len(residuals) > 1 else 0.0
        confidence_interval = (
            predicted_next - 2 * residual_std,
            predicted_next + 2 * residual_std,
        )

        return TrendAnalysis(
            metric_name=metric_name,
            direction=direction,
            slope=slope,
            r_squared=r_squared,
            volatility=volatility,
            recent_average=recent_avg,
            historical_average=historical_avg,
            percentage_change=percentage_change,
            predicted_next_value=predicted_next,
            confidence_interval=confidence_interval,
        )

    def _linear_regression(
        self, x_values: list[float], y_values: list[float]
    ) -> tuple[float, float]:
        """Calculate linear regression slope and R-squared.

        Args:
            x_values: X coordinates
            y_values: Y coordinates

        Returns:
            Tuple of (slope, r_squared)
        """
        n = len(x_values)
        if n < 2:
            return 0.0, 0.0

        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(y_values)

        numerator = sum(
            (x_values[i] - x_mean) * (y_values[i] - y_mean) for i in range(n)
        )
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))

        slope = numerator / denominator if denominator != 0 else 0.0

        # Calculate R-squared
        y_pred = [slope * x + (y_mean - slope * x_mean) for x in x_values]
        ss_res = sum((y_values[i] - y_pred[i]) ** 2 for i in range(n))
        ss_tot = sum((y_values[i] - y_mean) ** 2 for i in range(n))

        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0

        return slope, max(0.0, r_squared)  # Ensure R-squared is non-negative

    def _determine_trend_direction(
        self,
        slope: float,
        r_squared: float,
        volatility: float,
        percentage_change: float,
    ) -> TrendDirection:
        """Determine trend direction based on statistical measures.

        Args:
            slope: Linear regression slope
            r_squared: Correlation coefficient
            volatility: Volatility measure
            percentage_change: Recent vs historical percentage change

        Returns:
            TrendDirection enum value
        """
        # High volatility indicates unstable performance
        if volatility > abs(slope) * 10:  # Volatility threshold
            return TrendDirection.VOLATILE

        # Low correlation indicates no clear trend
        if r_squared < 0.3:
            return TrendDirection.STABLE

        # Determine direction based on slope and percentage change
        if slope > 0 and percentage_change > 5:
            return TrendDirection.DEGRADING
        elif slope < 0 and percentage_change < -5:
            return TrendDirection.IMPROVING
        else:
            return TrendDirection.STABLE

    def detect_advanced_regressions(
        self,
        current_metrics: PerformanceMetrics,
        metrics_history: list[PerformanceMetrics],
        baseline: PerformanceBaseline | None = None,
    ) -> list[RegressionAlert]:
        """Detect regressions using advanced statistical analysis.

        Args:
            current_metrics: Current performance metrics
            metrics_history: Historical metrics for trend analysis
            baseline: Optional performance baseline

        Returns:
            List of RegressionAlert objects
        """
        alerts = []

        # Analyze trends
        trends = self.analyze_trends(
            metrics_history + [current_metrics], current_metrics.test_name
        )

        # Check duration regression
        if "duration" in trends:
            duration_alert = self._check_metric_regression(
                "duration_seconds",
                current_metrics.duration_seconds,
                trends["duration"],
                baseline.duration_mean if baseline else None,
                baseline.duration_threshold_factor if baseline else 1.5,
            )
            if duration_alert:
                duration_alert.test_name = current_metrics.test_name
                alerts.append(duration_alert)

        # Check memory regression
        if "memory_peak" in trends:
            memory_alert = self._check_metric_regression(
                "memory_peak",
                current_metrics.memory_peak,
                trends["memory_peak"],
                baseline.memory_peak_mean if baseline else None,
                baseline.memory_threshold_factor if baseline else 1.3,
            )
            if memory_alert:
                memory_alert.test_name = current_metrics.test_name
                alerts.append(memory_alert)

        # Check CPU regression
        if "cpu_percent" in trends:
            cpu_alert = self._check_metric_regression(
                "cpu_percent",
                current_metrics.cpu_percent,
                trends["cpu_percent"],
                baseline.cpu_percent_mean if baseline else None,
                baseline.cpu_threshold_factor if baseline else 1.4,
            )
            if cpu_alert:
                cpu_alert.test_name = current_metrics.test_name
                alerts.append(cpu_alert)

        return alerts

    def _check_metric_regression(
        self,
        metric_name: str,
        current_value: float,
        trend: TrendAnalysis,
        baseline_value: float | None,
        threshold_factor: float,
    ) -> RegressionAlert | None:
        """Check for regression in a specific metric.

        Args:
            metric_name: Name of the metric
            current_value: Current metric value
            trend: Trend analysis for the metric
            baseline_value: Baseline value (if available)
            threshold_factor: Threshold factor for regression detection

        Returns:
            RegressionAlert if regression detected, None otherwise
        """
        # Determine expected value
        expected_value = baseline_value if baseline_value else trend.historical_average

        if expected_value == 0:
            return None  # Cannot detect regression without reference

        # Calculate deviation
        deviation_percentage = ((current_value - expected_value) / expected_value) * 100

        # Adjust threshold based on sensitivity and trend direction
        adjusted_threshold = threshold_factor
        if trend.direction == TrendDirection.DEGRADING:
            adjusted_threshold *= (
                1 / self.sensitivity
            )  # More sensitive for degrading trends
        elif trend.direction == TrendDirection.IMPROVING:
            adjusted_threshold *= (
                self.sensitivity
            )  # Less sensitive for improving trends

        # Check if regression threshold is exceeded
        if current_value > expected_value * adjusted_threshold:
            severity = self._determine_severity(deviation_percentage, trend)

            message = f"{metric_name} regression: {current_value:.3f} vs expected {expected_value:.3f} ({deviation_percentage:+.1f}%)"
            if trend.direction != TrendDirection.STABLE:
                message += f" [Trend: {trend.direction.value}]"

            return RegressionAlert(
                test_name="",  # Will be set by caller
                severity=severity,
                metric_name=metric_name,
                current_value=current_value,
                expected_value=expected_value,
                deviation_percentage=deviation_percentage,
                message=message,
                timestamp=datetime.now(),
                trend_analysis=trend,
                historical_context={
                    "recent_average": trend.recent_average,
                    "historical_average": trend.historical_average,
                    "volatility": trend.volatility,
                    "r_squared": trend.r_squared,
                },
            )

        return None

    def _determine_severity(
        self, deviation_percentage: float, trend: TrendAnalysis
    ) -> RegressionSeverity:
        """Determine severity of regression.

        Args:
            deviation_percentage: Percentage deviation from expected
            trend: Trend analysis

        Returns:
            RegressionSeverity enum value
        """
        # Base severity on deviation percentage
        abs_deviation = abs(deviation_percentage)

        if abs_deviation >= 100:  # 100%+ deviation
            base_severity = RegressionSeverity.CRITICAL
        elif abs_deviation >= 50:  # 50-100% deviation
            base_severity = RegressionSeverity.HIGH
        elif abs_deviation >= 25:  # 25-50% deviation
            base_severity = RegressionSeverity.MEDIUM
        else:  # <25% deviation
            base_severity = RegressionSeverity.LOW

        # Adjust based on trend direction
        if trend.direction == TrendDirection.DEGRADING:
            # Upgrade severity for degrading trends
            if base_severity == RegressionSeverity.LOW:
                return RegressionSeverity.MEDIUM
            elif base_severity == RegressionSeverity.MEDIUM:
                return RegressionSeverity.HIGH
        elif trend.direction == TrendDirection.VOLATILE:
            # Downgrade severity for volatile trends (less reliable)
            if base_severity == RegressionSeverity.CRITICAL:
                return RegressionSeverity.HIGH
            elif base_severity == RegressionSeverity.HIGH:
                return RegressionSeverity.MEDIUM

        return base_severity

    def generate_regression_summary(
        self, alerts: list[RegressionAlert]
    ) -> dict[str, Any]:
        """Generate summary of regression alerts.

        Args:
            alerts: List of regression alerts

        Returns:
            Dictionary with regression summary
        """
        if not alerts:
            return {
                "total_alerts": 0,
                "by_severity": {},
                "by_metric": {},
                "most_critical": None,
            }

        # Count by severity
        severity_counts = {}
        for alert in alerts:
            severity = alert.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        # Count by metric
        metric_counts = {}
        for alert in alerts:
            metric = alert.metric_name
            metric_counts[metric] = metric_counts.get(metric, 0) + 1

        # Find most critical alert
        critical_alerts = [
            a for a in alerts if a.severity == RegressionSeverity.CRITICAL
        ]
        high_alerts = [a for a in alerts if a.severity == RegressionSeverity.HIGH]

        most_critical = None
        if critical_alerts:
            most_critical = max(
                critical_alerts, key=lambda a: abs(a.deviation_percentage)
            )
        elif high_alerts:
            most_critical = max(high_alerts, key=lambda a: abs(a.deviation_percentage))
        elif alerts:
            most_critical = max(alerts, key=lambda a: abs(a.deviation_percentage))

        return {
            "total_alerts": len(alerts),
            "by_severity": severity_counts,
            "by_metric": metric_counts,
            "most_critical": {
                "test_name": most_critical.test_name,
                "metric": most_critical.metric_name,
                "severity": most_critical.severity.value,
                "deviation": most_critical.deviation_percentage,
                "message": most_critical.message,
            }
            if most_critical
            else None,
        }
