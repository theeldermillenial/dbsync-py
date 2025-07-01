"""Coverage Reporting and Visualization.

This module provides comprehensive coverage reporting capabilities including:
- HTML reports with interactive visualizations
- JSON reports for CI/CD integration
- Coverage trend charts and analysis
- Quality metrics dashboard
"""

import json
import statistics
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    import matplotlib

    matplotlib.use("Agg")  # Use non-interactive backend
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from .analyzer import CoverageAnalyzer, CoverageGap, CoverageQualityMetrics
from .generator import TestGenerator, TestSuggestion
from .tracker import CoverageTracker, CoverageTrend


class CoverageReporter:
    """Generates comprehensive coverage reports with visualizations."""

    def __init__(self, output_dir: Path = Path("coverage_reports")):
        """Initialize coverage reporter.

        Args:
            output_dir: Directory to store generated reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def generate_comprehensive_report(
        self,
        analyzer: CoverageAnalyzer,
        tracker: CoverageTracker | None = None,
        generator: TestGenerator | None = None,
        title: str = "Coverage Analysis Report",
    ) -> dict[str, Path]:
        """Generate comprehensive coverage report with all components.

        Args:
            analyzer: Coverage analyzer instance
            tracker: Optional coverage tracker for trends
            generator: Optional test generator for suggestions
            title: Report title

        Returns:
            Dictionary mapping report type to file path
        """
        reports = {}

        # Load coverage data
        if not analyzer.load_coverage_data():
            return {"error": "Failed to load coverage data"}

        # Get coverage metrics and gaps
        metrics = analyzer.calculate_quality_metrics()
        gaps = analyzer.analyze_coverage_gaps()
        summary = analyzer.get_coverage_summary()

        # Get historical trends if tracker available
        trends = []
        if tracker:
            trends = tracker.get_recent_trends(30)

        # Get test suggestions if generator available
        suggestions = []
        if generator:
            suggestions = generator.generate_test_suggestions(25)

        # Generate HTML report
        html_file = (
            self.output_dir
            / f"coverage_report_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.html"
        )
        self._generate_html_report(
            html_file, title, metrics, gaps, trends, suggestions, summary
        )
        reports["html"] = html_file

        # Generate JSON report
        json_file = (
            self.output_dir
            / f"coverage_data_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json"
        )
        self._generate_json_report(
            json_file, metrics, gaps, trends, suggestions, summary
        )
        reports["json"] = json_file

        # Generate trend charts if matplotlib available and trends exist
        if MATPLOTLIB_AVAILABLE and trends:
            charts_dir = self.output_dir / "charts"
            charts_dir.mkdir(exist_ok=True)
            chart_files = self._generate_trend_charts(charts_dir, trends)
            reports.update(chart_files)

        return reports

    def generate_ci_report(
        self,
        analyzer: CoverageAnalyzer,
        quality_gates: dict[str, float],
        tracker: CoverageTracker | None = None,
    ) -> dict[str, Any]:
        """Generate CI-friendly coverage report with pass/fail status.

        Args:
            analyzer: Coverage analyzer instance
            quality_gates: Dictionary of metric thresholds
            tracker: Optional coverage tracker for regression detection

        Returns:
            Dictionary with CI report data
        """
        if not analyzer.load_coverage_data():
            return {"status": "error", "message": "Failed to load coverage data"}

        metrics = analyzer.calculate_quality_metrics()

        # Check quality gates
        gate_results = {}
        overall_pass = True

        for metric, threshold in quality_gates.items():
            if hasattr(metrics, metric):
                current_value = getattr(metrics, metric)
                passed = current_value >= threshold
                gate_results[metric] = {
                    "current": current_value,
                    "threshold": threshold,
                    "passed": passed,
                    "difference": current_value - threshold,
                }
                if not passed:
                    overall_pass = False

        # Check for regressions if tracker available
        regression_info = {}
        if tracker:
            regression_info = tracker.detect_coverage_regression()

        return {
            "status": "pass" if overall_pass else "fail",
            "overall_score": metrics.overall_score,
            "timestamp": datetime.now(UTC).isoformat(),
            "quality_gates": gate_results,
            "regression_check": regression_info,
            "metrics": {
                "line_coverage": metrics.line_coverage_percent,
                "branch_coverage": metrics.branch_coverage_percent,
                "function_coverage": metrics.function_coverage_percent,
                "critical_gaps": metrics.critical_gaps,
                "high_priority_gaps": metrics.high_priority_gaps,
            },
        }

    def _generate_html_report(
        self,
        output_file: Path,
        title: str,
        metrics: CoverageQualityMetrics,
        gaps: list[CoverageGap],
        trends: list[CoverageTrend],
        suggestions: list[TestSuggestion],
        summary: dict[str, Any],
    ) -> None:
        """Generate comprehensive HTML report."""
        html_content = self._create_html_template(title)

        # Add summary section
        html_content += self._generate_summary_section(metrics, summary)

        # Add metrics dashboard
        html_content += self._generate_metrics_dashboard(metrics)

        # Add coverage gaps section
        html_content += self._generate_gaps_section(gaps)

        # Add trends section if available
        if trends:
            html_content += self._generate_trends_section(trends)

        # Add test suggestions section
        if suggestions:
            html_content += self._generate_suggestions_section(suggestions)

        # Close HTML
        html_content += """
        </div>
    </body>
</html>"""

        # Write to file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

    def _generate_json_report(
        self,
        output_file: Path,
        metrics: CoverageQualityMetrics,
        gaps: list[CoverageGap],
        trends: list[CoverageTrend],
        suggestions: list[TestSuggestion],
        summary: dict[str, Any],
    ) -> None:
        """Generate JSON report for automation."""
        report_data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "summary": summary,
            "metrics": {
                "line_coverage": metrics.line_coverage_percent,
                "branch_coverage": metrics.branch_coverage_percent,
                "function_coverage": metrics.function_coverage_percent,
                "overall_score": metrics.overall_score,
                "effective_coverage": metrics.effective_coverage_score,
                "test_quality": metrics.test_quality_score,
                "coverage_density": metrics.coverage_density,
                "trend": metrics.coverage_trend,
                "trend_percentage": metrics.trend_percentage,
            },
            "gaps": {
                "total": len(gaps),
                "critical": metrics.critical_gaps,
                "high": metrics.high_priority_gaps,
                "by_severity": self._group_gaps_by_severity(gaps),
                "by_type": self._group_gaps_by_type(gaps),
                "details": [
                    {
                        "file": gap.file_path,
                        "lines": f"{gap.line_start}-{gap.line_end}",
                        "type": gap.gap_type,
                        "severity": gap.severity,
                        "function": gap.function_name,
                        "class": gap.class_name,
                        "complexity": gap.complexity_score,
                        "suggestions": gap.suggested_tests,
                    }
                    for gap in gaps[:20]  # Limit to top 20 gaps
                ],
            },
            "trends": [
                {
                    "timestamp": trend.timestamp,
                    "line_coverage": trend.line_coverage,
                    "branch_coverage": trend.branch_coverage,
                    "function_coverage": trend.function_coverage,
                    "overall_score": trend.overall_score,
                    "test_count": trend.test_count,
                }
                for trend in trends[-30:]  # Last 30 data points
            ],
            "test_suggestions": [
                {
                    "file": suggestion.file_path,
                    "function": suggestion.function_name,
                    "class": suggestion.class_name,
                    "type": suggestion.test_type,
                    "priority": suggestion.priority,
                    "description": suggestion.description,
                    "test_name": suggestion.full_test_name,
                    "complexity": suggestion.complexity_score,
                }
                for suggestion in suggestions[:15]  # Top 15 suggestions
            ],
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)

    def _generate_trend_charts(
        self, charts_dir: Path, trends: list[CoverageTrend]
    ) -> dict[str, Path]:
        """Generate trend visualization charts."""
        if not MATPLOTLIB_AVAILABLE:
            return {}

        chart_files = {}

        # Prepare data
        timestamps = [
            datetime.fromisoformat(t.timestamp.replace("Z", "+00:00")) for t in trends
        ]
        line_coverage = [t.line_coverage for t in trends]
        branch_coverage = [t.branch_coverage for t in trends]
        function_coverage = [t.function_coverage for t in trends]
        overall_scores = [t.overall_score for t in trends]

        # Coverage trends chart
        plt.figure(figsize=(12, 8))
        plt.plot(
            timestamps, line_coverage, label="Line Coverage", marker="o", linewidth=2
        )
        plt.plot(
            timestamps,
            branch_coverage,
            label="Branch Coverage",
            marker="s",
            linewidth=2,
        )
        plt.plot(
            timestamps,
            function_coverage,
            label="Function Coverage",
            marker="^",
            linewidth=2,
        )

        plt.title("Coverage Trends Over Time", fontsize=16, fontweight="bold")
        plt.xlabel("Date", fontsize=12)
        plt.ylabel("Coverage Percentage", fontsize=12)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        plt.gca().xaxis.set_major_locator(
            mdates.DayLocator(interval=max(1, len(timestamps) // 10))
        )
        plt.xticks(rotation=45)
        plt.tight_layout()

        coverage_chart = charts_dir / "coverage_trends.png"
        plt.savefig(coverage_chart, dpi=300, bbox_inches="tight")
        plt.close()
        chart_files["coverage_trends"] = coverage_chart

        # Overall quality score chart
        plt.figure(figsize=(10, 6))
        plt.plot(
            timestamps,
            overall_scores,
            label="Overall Quality Score",
            marker="o",
            linewidth=3,
            color="purple",
        )

        plt.title("Overall Coverage Quality Score", fontsize=16, fontweight="bold")
        plt.xlabel("Date", fontsize=12)
        plt.ylabel("Quality Score", fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        plt.gca().xaxis.set_major_locator(
            mdates.DayLocator(interval=max(1, len(timestamps) // 10))
        )
        plt.xticks(rotation=45)
        plt.tight_layout()

        quality_chart = charts_dir / "quality_score.png"
        plt.savefig(quality_chart, dpi=300, bbox_inches="tight")
        plt.close()
        chart_files["quality_score"] = quality_chart

        return chart_files

    def _create_html_template(self, title: str) -> str:
        """Create HTML template with styling."""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f7fa;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header .subtitle {{
            margin-top: 10px;
            font-size: 1.1em;
            opacity: 0.9;
        }}
        .content {{
            padding: 30px;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .section h2 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
            font-size: 1.8em;
            font-weight: 400;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            border-left: 5px solid #3498db;
            transition: transform 0.2s;
        }}
        .metric-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .metric-card h3 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
            font-size: 1.1em;
        }}
        .metric-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #3498db;
            margin: 10px 0;
        }}
        .metric-trend {{
            font-size: 0.9em;
            color: #7f8c8d;
        }}
        .critical {{ border-left-color: #e74c3c; }}
        .critical .metric-value {{ color: #e74c3c; }}
        .warning {{ border-left-color: #f39c12; }}
        .warning .metric-value {{ color: #f39c12; }}
        .success {{ border-left-color: #27ae60; }}
        .success .metric-value {{ color: #27ae60; }}
        .gaps-table, .suggestions-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .gaps-table th, .gaps-table td,
        .suggestions-table th, .suggestions-table td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ecf0f1;
        }}
        .gaps-table th, .suggestions-table th {{
            background: #34495e;
            color: white;
            font-weight: 600;
        }}
        .gaps-table tr:hover, .suggestions-table tr:hover {{
            background: #f8f9fa;
        }}
        .severity-critical {{ background: #ffebee; color: #c62828; }}
        .severity-high {{ background: #fff3e0; color: #ef6c00; }}
        .severity-medium {{ background: #f3e5f5; color: #7b1fa2; }}
        .severity-low {{ background: #e8f5e8; color: #2e7d32; }}
        .priority-high {{ font-weight: bold; color: #d32f2f; }}
        .priority-medium {{ color: #f57c00; }}
        .priority-low {{ color: #388e3c; }}
        .chart-container {{
            text-align: center;
            margin: 20px 0;
        }}
        .chart-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .summary-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-item {{
            background: #ecf0f1;
            padding: 15px;
            border-radius: 6px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 1.5em;
            font-weight: bold;
            color: #2c3e50;
        }}
        .stat-label {{
            color: #7f8c8d;
            font-size: 0.9em;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <div class="subtitle">Generated on {datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")}</div>
        </div>
        <div class="content">
"""

    def _generate_summary_section(
        self, metrics: CoverageQualityMetrics, summary: dict[str, Any]
    ) -> str:
        """Generate summary section of the report."""
        return f"""
        <div class="section">
            <h2>📊 Coverage Summary</h2>
            <div class="summary-stats">
                <div class="stat-item">
                    <div class="stat-value">{metrics.overall_score:.1f}</div>
                    <div class="stat-label">Overall Score</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{metrics.line_coverage_percent:.1f}%</div>
                    <div class="stat-label">Line Coverage</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{metrics.branch_coverage_percent:.1f}%</div>
                    <div class="stat-label">Branch Coverage</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{metrics.function_coverage_percent:.1f}%</div>
                    <div class="stat-label">Function Coverage</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{metrics.total_gaps}</div>
                    <div class="stat-label">Coverage Gaps</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{metrics.coverage_trend.title()}</div>
                    <div class="stat-label">Trend Direction</div>
                </div>
            </div>
        </div>
"""

    def _generate_metrics_dashboard(self, metrics: CoverageQualityMetrics) -> str:
        """Generate metrics dashboard section."""

        # Determine card classes based on values
        def get_card_class(value: float, thresholds: dict[str, float]) -> str:
            if value >= thresholds.get("success", 90):
                return "success"
            elif value >= thresholds.get("warning", 70):
                return "warning"
            else:
                return "critical"

        coverage_class = get_card_class(
            metrics.line_coverage_percent, {"success": 90, "warning": 70}
        )
        branch_class = get_card_class(
            metrics.branch_coverage_percent, {"success": 85, "warning": 65}
        )
        quality_class = get_card_class(
            metrics.overall_score, {"success": 85, "warning": 70}
        )

        return f"""
        <div class="section">
            <h2>📈 Quality Metrics</h2>
            <div class="metrics-grid">
                <div class="metric-card {coverage_class}">
                    <h3>Line Coverage</h3>
                    <div class="metric-value">{metrics.line_coverage_percent:.1f}%</div>
                    <div class="metric-trend">Effective: {metrics.effective_coverage_score:.1f}%</div>
                </div>
                <div class="metric-card {branch_class}">
                    <h3>Branch Coverage</h3>
                    <div class="metric-value">{metrics.branch_coverage_percent:.1f}%</div>
                    <div class="metric-trend">Decision Points</div>
                </div>
                <div class="metric-card">
                    <h3>Function Coverage</h3>
                    <div class="metric-value">{metrics.function_coverage_percent:.1f}%</div>
                    <div class="metric-trend">Callable Functions</div>
                </div>
                <div class="metric-card {quality_class}">
                    <h3>Overall Quality</h3>
                    <div class="metric-value">{metrics.overall_score:.1f}</div>
                    <div class="metric-trend">Composite Score</div>
                </div>
                <div class="metric-card">
                    <h3>Test Quality</h3>
                    <div class="metric-value">{metrics.test_quality_score:.1f}</div>
                    <div class="metric-trend">Test Effectiveness</div>
                </div>
                <div class="metric-card">
                    <h3>Coverage Density</h3>
                    <div class="metric-value">{metrics.coverage_density:.2f}</div>
                    <div class="metric-trend">Coverage per LOC</div>
                </div>
            </div>
        </div>
"""

    def _generate_gaps_section(self, gaps: list[CoverageGap]) -> str:
        """Generate coverage gaps section."""
        if not gaps:
            return """
        <div class="section">
            <h2>✅ Coverage Gaps</h2>
            <p>No significant coverage gaps detected. Excellent work!</p>
        </div>
"""

        # Show top 20 gaps
        top_gaps = gaps[:20]

        gaps_html = """
        <div class="section">
            <h2>🚨 Coverage Gaps</h2>
            <table class="gaps-table">
                <thead>
                    <tr>
                        <th>File</th>
                        <th>Function/Class</th>
                        <th>Lines</th>
                        <th>Type</th>
                        <th>Severity</th>
                        <th>Complexity</th>
                        <th>Suggestions</th>
                    </tr>
                </thead>
                <tbody>
"""

        for gap in top_gaps:
            function_info = gap.function_name or ""
            if gap.class_name:
                function_info = (
                    f"{gap.class_name}.{function_info}"
                    if function_info
                    else gap.class_name
                )

            suggestions_text = (
                "; ".join(gap.suggested_tests[:2]) if gap.suggested_tests else "None"
            )
            if len(suggestions_text) > 100:
                suggestions_text = suggestions_text[:97] + "..."

            gaps_html += f"""
                    <tr>
                        <td>{Path(gap.file_path).name}</td>
                        <td>{function_info}</td>
                        <td>{gap.line_start}-{gap.line_end}</td>
                        <td>{gap.gap_type.replace("_", " ").title()}</td>
                        <td><span class="severity-{gap.severity}">{gap.severity.upper()}</span></td>
                        <td>{gap.complexity_score or 1}</td>
                        <td title="{"; ".join(gap.suggested_tests) if gap.suggested_tests else "None"}">{suggestions_text}</td>
                    </tr>
"""

        gaps_html += """
                </tbody>
            </table>
        </div>
"""

        return gaps_html

    def _generate_trends_section(self, trends: list[CoverageTrend]) -> str:
        """Generate trends section."""
        if len(trends) < 2:
            return ""

        # Calculate trend statistics
        recent_trends = trends[-10:]  # Last 10 data points
        line_coverage_values = [t.line_coverage for t in recent_trends]

        trend_direction = "stable"
        if len(line_coverage_values) >= 2:
            slope = (line_coverage_values[-1] - line_coverage_values[0]) / len(
                line_coverage_values
            )
            if slope > 0.5:
                trend_direction = "improving"
            elif slope < -0.5:
                trend_direction = "declining"

        return f"""
        <div class="section">
            <h2>📈 Coverage Trends</h2>
            <div class="summary-stats">
                <div class="stat-item">
                    <div class="stat-value">{len(trends)}</div>
                    <div class="stat-label">Data Points</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{trend_direction.title()}</div>
                    <div class="stat-label">Trend Direction</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{statistics.mean(line_coverage_values):.1f}%</div>
                    <div class="stat-label">Average Coverage</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{max(line_coverage_values) - min(line_coverage_values):.1f}%</div>
                    <div class="stat-label">Coverage Range</div>
                </div>
            </div>
            <div class="chart-container">
                <p>Trend charts available in the charts directory if matplotlib is installed.</p>
            </div>
        </div>
"""

    def _generate_suggestions_section(self, suggestions: list[TestSuggestion]) -> str:
        """Generate test suggestions section."""
        if not suggestions:
            return ""

        # Show top 15 suggestions
        top_suggestions = suggestions[:15]

        suggestions_html = """
        <div class="section">
            <h2>💡 Test Suggestions</h2>
            <table class="suggestions-table">
                <thead>
                    <tr>
                        <th>File</th>
                        <th>Function/Class</th>
                        <th>Test Type</th>
                        <th>Priority</th>
                        <th>Description</th>
                        <th>Suggested Test Name</th>
                    </tr>
                </thead>
                <tbody>
"""

        for suggestion in top_suggestions:
            function_info = suggestion.function_name or ""
            if suggestion.class_name:
                function_info = (
                    f"{suggestion.class_name}.{function_info}"
                    if function_info
                    else suggestion.class_name
                )

            suggestions_html += f"""
                    <tr>
                        <td>{Path(suggestion.file_path).name}</td>
                        <td>{function_info}</td>
                        <td>{suggestion.test_type.replace("_", " ").title()}</td>
                        <td><span class="priority-{suggestion.priority}">{suggestion.priority.upper()}</span></td>
                        <td>{suggestion.description}</td>
                        <td><code>{suggestion.full_test_name}</code></td>
                    </tr>
"""

        suggestions_html += """
                </tbody>
            </table>
        </div>
"""

        return suggestions_html

    def _group_gaps_by_severity(self, gaps: list[CoverageGap]) -> dict[str, int]:
        """Group gaps by severity."""
        severity_counts = {}
        for gap in gaps:
            severity_counts[gap.severity] = severity_counts.get(gap.severity, 0) + 1
        return severity_counts

    def _group_gaps_by_type(self, gaps: list[CoverageGap]) -> dict[str, int]:
        """Group gaps by type."""
        type_counts = {}
        for gap in gaps:
            type_counts[gap.gap_type] = type_counts.get(gap.gap_type, 0) + 1
        return type_counts
