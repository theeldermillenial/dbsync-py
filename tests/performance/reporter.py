"""Performance reporting and visualization utilities.

This module provides comprehensive performance reporting capabilities including
HTML reports, trend analysis, and performance dashboards.
"""

import json
import statistics
from datetime import UTC, datetime
from pathlib import Path

try:
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    import pandas as pd
    from matplotlib.figure import Figure

    VISUALIZATION_AVAILABLE = True
except ImportError:
    plt = None
    mdates = None
    Figure = None
    pd = None
    VISUALIZATION_AVAILABLE = False

from .baseline import PerformanceBaseline
from .monitor import PerformanceMetrics
from .regression import RegressionAlert


class PerformanceReporter:
    """Generates comprehensive performance reports and visualizations."""

    def __init__(self, output_dir: Path = None):
        """Initialize performance reporter.

        Args:
            output_dir: Directory to save reports and visualizations
        """
        self.output_dir = output_dir or Path("tests/performance/reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_html_report(
        self,
        metrics_list: list[PerformanceMetrics],
        baselines: dict[str, PerformanceBaseline] = None,
        regressions: list[RegressionAlert] = None,
        title: str = "Performance Report",
    ) -> Path:
        """Generate comprehensive HTML performance report.

        Args:
            metrics_list: List of performance metrics
            baselines: Dictionary of performance baselines
            regressions: List of regression results
            title: Report title

        Returns:
            Path to generated HTML report
        """
        # Group metrics by test name
        test_metrics = {}
        for metric in metrics_list:
            if metric.test_name not in test_metrics:
                test_metrics[metric.test_name] = []
            test_metrics[metric.test_name].append(metric)

        # Generate HTML content
        html_content = self._generate_html_content(
            test_metrics, baselines or {}, regressions or [], title
        )

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / f"performance_report_{timestamp}.html"

        with open(report_path, "w") as f:
            f.write(html_content)

        return report_path

    def _generate_html_content(
        self,
        test_metrics: dict[str, list[PerformanceMetrics]],
        baselines: dict[str, PerformanceBaseline],
        regressions: list[RegressionAlert],
        title: str,
    ) -> str:
        """Generate HTML content for the performance report."""

        # Calculate summary statistics
        total_tests = len(test_metrics)
        total_metrics = sum(len(metrics) for metrics in test_metrics.values())
        regression_count = sum(1 for r in regressions if r.has_regression)

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; border-bottom: 2px solid #007acc; padding-bottom: 20px; margin-bottom: 30px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .summary-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #007acc; }}
        .summary-card h3 {{ margin: 0 0 10px 0; color: #333; }}
        .summary-card .value {{ font-size: 2em; font-weight: bold; color: #007acc; }}
        .regression {{ border-left-color: #dc3545 !important; }}
        .regression .value {{ color: #dc3545; }}
        .section {{ margin-bottom: 40px; }}
        .section h2 {{ color: #333; border-bottom: 1px solid #ddd; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f8f9fa; font-weight: bold; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .regression-row {{ background-color: #fff5f5; }}
        .good {{ color: #28a745; }}
        .warning {{ color: #ffc107; }}
        .danger {{ color: #dc3545; }}
        .chart-container {{ margin: 20px 0; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <p>Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>

        <div class="summary">
            <div class="summary-card">
                <h3>Total Tests</h3>
                <div class="value">{total_tests}</div>
            </div>
            <div class="summary-card">
                <h3>Total Metrics</h3>
                <div class="value">{total_metrics}</div>
            </div>
            <div class="summary-card {"regression" if regression_count > 0 else ""}">
                <h3>Regressions</h3>
                <div class="value">{regression_count}</div>
            </div>
            <div class="summary-card">
                <h3>Baselines</h3>
                <div class="value">{len(baselines)}</div>
            </div>
        </div>
"""

        # Add regression section if there are regressions
        if regressions:
            html += self._generate_regression_section(regressions)

        # Add test performance section
        html += self._generate_test_performance_section(test_metrics, baselines)

        # Add baseline comparison section
        if baselines:
            html += self._generate_baseline_section(baselines)

        html += """
    </div>
</body>
</html>
"""
        return html

    def _generate_regression_section(self, regressions: list[RegressionAlert]) -> str:
        """Generate regression analysis section."""
        regression_items = [r for r in regressions if r.has_regression]

        if not regression_items:
            return ""

        html = """
        <div class="section">
            <h2>🚨 Performance Regressions Detected</h2>
            <table>
                <thead>
                    <tr>
                        <th>Test Name</th>
                        <th>Regression Type</th>
                        <th>Current Value</th>
                        <th>Baseline Value</th>
                        <th>Change (%)</th>
                        <th>Threshold</th>
                        <th>Message</th>
                    </tr>
                </thead>
                <tbody>
"""

        for regression in regression_items:
            change_class = (
                "danger" if abs(regression.deviation_percentage) > 50 else "warning"
            )
            html += f"""
                    <tr class="regression-row">
                        <td>{regression.test_name}</td>
                        <td><span class="danger">{regression.severity.value.title()}</span></td>
                        <td>{regression.current_value:.3f}</td>
                        <td>{regression.expected_value:.3f}</td>
                        <td><span class="{change_class}">{regression.deviation_percentage:+.1f}%</span></td>
                        <td>1.5x</td>
                        <td>{regression.message}</td>
                    </tr>
"""

        html += """
                </tbody>
            </table>
        </div>
"""
        return html

    def _generate_test_performance_section(
        self,
        test_metrics: dict[str, list[PerformanceMetrics]],
        baselines: dict[str, PerformanceBaseline],
    ) -> str:
        """Generate test performance analysis section."""
        html = """
        <div class="section">
            <h2>📊 Test Performance Analysis</h2>
            <table>
                <thead>
                    <tr>
                        <th>Test Name</th>
                        <th>Runs</th>
                        <th>Avg Duration (s)</th>
                        <th>Peak Memory (MB)</th>
                        <th>Avg CPU (%)</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
"""

        for test_name, metrics in test_metrics.items():
            avg_duration = statistics.mean(m.duration_seconds for m in metrics)
            peak_memory = max(m.memory_peak for m in metrics) / 1024 / 1024
            avg_cpu = statistics.mean(m.cpu_percent for m in metrics)

            # Determine status based on baseline comparison
            status = "✅ Good"
            status_class = "good"

            if test_name in baselines:
                baseline = baselines[test_name]
                if (
                    avg_duration
                    > baseline.duration_mean * baseline.duration_threshold_factor
                ):
                    status = "🐌 Slow"
                    status_class = "danger"
                elif (
                    peak_memory
                    > baseline.memory_peak_mean
                    * baseline.memory_threshold_factor
                    / 1024
                    / 1024
                ):
                    status = "🧠 Memory"
                    status_class = "warning"

            html += f"""
                    <tr>
                        <td>{test_name}</td>
                        <td>{len(metrics)}</td>
                        <td>{avg_duration:.3f}</td>
                        <td>{peak_memory:.1f}</td>
                        <td>{avg_cpu:.1f}</td>
                        <td><span class="{status_class}">{status}</span></td>
                    </tr>
"""

        html += """
                </tbody>
            </table>
        </div>
"""
        return html

    def _generate_baseline_section(
        self, baselines: dict[str, PerformanceBaseline]
    ) -> str:
        """Generate baseline information section."""
        html = """
        <div class="section">
            <h2>📈 Performance Baselines</h2>
            <table>
                <thead>
                    <tr>
                        <th>Test Name</th>
                        <th>Baseline Date</th>
                        <th>Samples</th>
                        <th>Duration (s)</th>
                        <th>Memory (MB)</th>
                        <th>CPU (%)</th>
                        <th>Thresholds</th>
                    </tr>
                </thead>
                <tbody>
"""

        for name, baseline in baselines.items():
            baseline_date = baseline.baseline_date.strftime("%Y-%m-%d")
            memory_mb = baseline.memory_peak_mean / 1024 / 1024

            html += f"""
                    <tr>
                        <td>{name}</td>
                        <td>{baseline_date}</td>
                        <td>{baseline.sample_count}</td>
                        <td>{baseline.duration_mean:.3f} ± {baseline.duration_std:.3f}</td>
                        <td>{memory_mb:.1f} ± {baseline.memory_peak_std / 1024 / 1024:.1f}</td>
                        <td>{baseline.cpu_percent_mean:.1f} ± {baseline.cpu_percent_std:.1f}</td>
                        <td>D:{baseline.duration_threshold_factor:.1f}x M:{baseline.memory_threshold_factor:.1f}x C:{baseline.cpu_threshold_factor:.1f}x</td>
                    </tr>
"""

        html += """
                </tbody>
            </table>
        </div>
"""
        return html

    def generate_json_report(
        self,
        metrics_list: list[PerformanceMetrics],
        baselines: dict[str, PerformanceBaseline] = None,
        regressions: list[RegressionAlert] = None,
    ) -> Path:
        """Generate JSON performance report.

        Args:
            metrics_list: List of performance metrics
            baselines: Dictionary of performance baselines
            regressions: List of regression results

        Returns:
            Path to generated JSON report
        """
        report_data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "summary": {
                "total_tests": len(set(m.test_name for m in metrics_list)),
                "total_metrics": len(metrics_list),
                "regressions_count": sum(
                    1 for r in (regressions or []) if r.has_regression
                ),
                "baselines_count": len(baselines or {}),
            },
            "metrics": [m.to_dict() for m in metrics_list],
            "baselines": {
                name: baseline.to_dict() for name, baseline in (baselines or {}).items()
            },
            "regressions": [
                {
                    "test_name": r.test_name,
                    "has_regression": r.has_regression,
                    "regression_type": r.severity.value,
                    "current_value": r.current_value,
                    "baseline_value": r.expected_value,
                    "percentage_change": r.deviation_percentage,
                    "threshold_exceeded": r.severity.value not in ["low"],
                    "metric_name": r.metric_name,
                    "threshold_factor": 1.5,  # Default threshold factor
                    "message": r.message,
                    "severity": r.severity.value,
                    "timestamp": r.timestamp.isoformat(),
                }
                for r in (regressions or [])
            ],
        }

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / f"performance_report_{timestamp}.json"

        with open(report_path, "w") as f:
            json.dump(report_data, f, indent=2)

        return report_path

    def generate_trend_charts(
        self, metrics_history: list[PerformanceMetrics], output_prefix: str = "trend"
    ) -> list[Path]:
        """Generate trend charts for performance metrics.

        Args:
            metrics_history: Historical performance metrics
            output_prefix: Prefix for output files

        Returns:
            List of paths to generated chart files
        """
        if not VISUALIZATION_AVAILABLE:
            print(
                "Warning: Visualization libraries not available. Install matplotlib and pandas."
            )
            return []

        if not metrics_history:
            return []

        # Group metrics by test name
        test_groups = {}
        for metric in metrics_history:
            if metric.test_name not in test_groups:
                test_groups[metric.test_name] = []
            test_groups[metric.test_name].append(metric)

        chart_paths = []

        for test_name, metrics in test_groups.items():
            if len(metrics) < 2:
                continue  # Need at least 2 points for a trend

            # Sort by start time
            metrics.sort(key=lambda m: m.start_time)

            # Create trend charts
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle(f"Performance Trends: {test_name}", fontsize=16)

            timestamps = [m.start_time for m in metrics]

            # Duration trend
            durations = [m.duration_seconds for m in metrics]
            ax1.plot(timestamps, durations, "b-o", linewidth=2, markersize=4)
            ax1.set_title("Execution Duration")
            ax1.set_ylabel("Seconds")
            ax1.grid(True, alpha=0.3)

            # Memory trend
            memory_mb = [m.memory_peak / 1024 / 1024 for m in metrics]
            ax2.plot(timestamps, memory_mb, "r-o", linewidth=2, markersize=4)
            ax2.set_title("Peak Memory Usage")
            ax2.set_ylabel("MB")
            ax2.grid(True, alpha=0.3)

            # CPU trend
            cpu_percents = [m.cpu_percent for m in metrics]
            ax3.plot(timestamps, cpu_percents, "g-o", linewidth=2, markersize=4)
            ax3.set_title("CPU Usage")
            ax3.set_ylabel("Percentage")
            ax3.grid(True, alpha=0.3)

            # Memory delta trend
            memory_deltas = [m.memory_delta / 1024 / 1024 for m in metrics]
            ax4.plot(timestamps, memory_deltas, "m-o", linewidth=2, markersize=4)
            ax4.set_title("Memory Delta")
            ax4.set_ylabel("MB")
            ax4.grid(True, alpha=0.3)

            # Format x-axis for all subplots
            for ax in [ax1, ax2, ax3, ax4]:
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d %H:%M"))
                ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

            plt.tight_layout()

            # Save chart
            safe_test_name = test_name.replace("/", "_").replace("::", "_")
            chart_path = self.output_dir / f"{output_prefix}_{safe_test_name}.png"
            plt.savefig(chart_path, dpi=300, bbox_inches="tight")
            plt.close()

            chart_paths.append(chart_path)

        return chart_paths

    def generate_performance_dashboard(
        self,
        metrics_list: list[PerformanceMetrics],
        baselines: dict[str, PerformanceBaseline] = None,
    ) -> Path:
        """Generate a comprehensive performance dashboard.

        Args:
            metrics_list: List of performance metrics
            baselines: Dictionary of performance baselines

        Returns:
            Path to generated dashboard HTML file
        """
        # Generate charts
        chart_paths = self.generate_trend_charts(metrics_list, "dashboard")

        # Generate HTML report with embedded charts
        html_report = self.generate_html_report(
            metrics_list, baselines, title="Performance Dashboard"
        )

        return html_report
