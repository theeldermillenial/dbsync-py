"""Coverage analysis CLI commands.

This module provides CLI commands for comprehensive test coverage analysis
including gap analysis, quality metrics, trend tracking, and CI integration.
"""

import json
import sys
from pathlib import Path

import click

from tests.coverage.analyzer import CoverageAnalyzer
from tests.coverage.ci import CICoverageRunner, QualityGate
from tests.coverage.generator import TestGenerator
from tests.coverage.reporter import CoverageReporter
from tests.coverage.tracker import CoverageTracker


@click.group()
def coverage():
    """Test coverage analysis and reporting commands."""
    pass


@coverage.command()
@click.option(
    "--source-dir",
    type=click.Path(exists=True, path_type=Path),
    default=Path("src"),
    help="Source code directory",
)
@click.option("--coverage-file", default=".coverage", help="Coverage data file path")
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file path (default: stdout)",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.option("--detailed", is_flag=True, help="Include detailed gap analysis")
def analyze(source_dir, coverage_file, output, output_format, detailed):
    """Analyze test coverage and identify gaps."""
    try:
        analyzer = CoverageAnalyzer(source_dir, coverage_file)

        if not analyzer.load_coverage_data():
            click.echo("❌ Failed to load coverage data", err=True)
            click.echo(
                "Make sure to run tests with coverage first: pytest --cov=src", err=True
            )
            sys.exit(1)

        # Get coverage analysis
        metrics = analyzer.calculate_quality_metrics()
        summary = analyzer.get_coverage_summary()

        if detailed:
            gaps = analyzer.analyze_coverage_gaps()
            summary["gaps_detail"] = [
                {
                    "file": gap.file_path,
                    "lines": f"{gap.line_start}-{gap.line_end}",
                    "type": gap.gap_type,
                    "severity": gap.severity,
                    "function": gap.function_name,
                    "class": gap.class_name,
                    "suggestions": gap.suggested_tests,
                }
                for gap in gaps[:20]  # Top 20 gaps
            ]

        # Format output
        if output_format == "json":
            output_text = json.dumps(summary, indent=2)
        else:
            output_text = _format_analysis_text(metrics, summary, detailed)

        # Write output
        if output:
            with open(output, "w") as f:
                f.write(output_text)
            click.echo(f"✅ Coverage analysis saved to: {output}")
        else:
            click.echo(output_text)

    except Exception as e:
        click.echo(f"❌ Coverage analysis failed: {e}", err=True)
        sys.exit(1)


@coverage.command()
@click.option(
    "--source-dir",
    type=click.Path(exists=True, path_type=Path),
    default=Path("src"),
    help="Source code directory",
)
@click.option("--coverage-file", default=".coverage", help="Coverage data file path")
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=Path("coverage_reports"),
    help="Output directory for reports",
)
@click.option("--title", default="Coverage Analysis Report", help="Report title")
@click.option("--include-trends", is_flag=True, help="Include coverage trends analysis")
@click.option(
    "--include-suggestions", is_flag=True, help="Include test generation suggestions"
)
def report(
    source_dir, coverage_file, output_dir, title, include_trends, include_suggestions
):
    """Generate comprehensive coverage reports."""
    try:
        # Initialize components
        analyzer = CoverageAnalyzer(source_dir, coverage_file)
        tracker = CoverageTracker(output_dir / "history") if include_trends else None
        generator = TestGenerator(source_dir) if include_suggestions else None
        reporter = CoverageReporter(output_dir)

        if not analyzer.load_coverage_data():
            click.echo("❌ Failed to load coverage data", err=True)
            sys.exit(1)

        # Generate reports
        with click.progressbar(length=100, label="Generating reports") as bar:
            bar.update(20)
            reports = reporter.generate_comprehensive_report(
                analyzer, tracker, generator, title
            )
            bar.update(80)

        # Display results
        click.echo("✅ Coverage reports generated:")
        for report_type, file_path in reports.items():
            if report_type != "error":
                click.echo(f"  📄 {report_type.upper()}: {file_path}")

        if "html" in reports:
            click.echo(f"\n🌐 Open HTML report: file://{reports['html'].absolute()}")

    except Exception as e:
        click.echo(f"❌ Report generation failed: {e}", err=True)
        sys.exit(1)


@coverage.command()
@click.option(
    "--source-dir",
    type=click.Path(exists=True, path_type=Path),
    default=Path("src"),
    help="Source code directory",
)
@click.option(
    "--test-dir",
    type=click.Path(exists=True, path_type=Path),
    default=Path("tests"),
    help="Test directory",
)
@click.option("--coverage-file", default=".coverage", help="Coverage data file path")
@click.option(
    "--max-suggestions",
    type=int,
    default=25,
    help="Maximum number of suggestions to generate",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file for suggestions",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
def suggest(
    source_dir, test_dir, coverage_file, max_suggestions, output, output_format
):
    """Generate test suggestions based on coverage gaps."""
    try:
        generator = TestGenerator(source_dir, test_dir)

        # Generate suggestions
        with click.progressbar(length=100, label="Analyzing coverage gaps") as bar:
            bar.update(50)
            suggestions = generator.generate_test_suggestions(max_suggestions)
            bar.update(50)

        if not suggestions:
            click.echo("✅ No test suggestions needed - coverage looks good!")
            return

        # Format output
        if output_format == "json":
            suggestions_data = [
                {
                    "file": s.file_path,
                    "function": s.function_name,
                    "class": s.class_name,
                    "type": s.test_type,
                    "priority": s.priority,
                    "description": s.description,
                    "test_name": s.full_test_name,
                    "template": s.test_template,
                }
                for s in suggestions
            ]
            output_text = json.dumps(suggestions_data, indent=2)
        else:
            output_text = _format_suggestions_text(suggestions)

        # Write output
        if output:
            with open(output, "w") as f:
                f.write(output_text)
            click.echo(f"✅ Test suggestions saved to: {output}")
        else:
            click.echo(output_text)

    except Exception as e:
        click.echo(f"❌ Test suggestion generation failed: {e}", err=True)
        sys.exit(1)


@coverage.command()
@click.option(
    "--data-dir",
    type=click.Path(path_type=Path),
    default=Path("coverage_history"),
    help="Coverage history directory",
)
@click.option("--period", type=int, default=30, help="Period in days to analyze")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
def trends(data_dir, period, output_format):
    """Analyze coverage trends over time."""
    try:
        tracker = CoverageTracker(data_dir)

        # Get trend statistics
        stats = tracker.get_coverage_statistics(period)

        if "error" in stats:
            click.echo(f"❌ {stats['error']}", err=True)
            sys.exit(1)

        # Check for regressions
        regression_info = tracker.detect_coverage_regression()

        if output_format == "json":
            output_data = {"statistics": stats, "regression_check": regression_info}
            click.echo(json.dumps(output_data, indent=2))
        else:
            _display_trends_text(stats, regression_info)

    except Exception as e:
        click.echo(f"❌ Trend analysis failed: {e}", err=True)
        sys.exit(1)


@coverage.command()
@click.option(
    "--source-dir",
    type=click.Path(exists=True, path_type=Path),
    default=Path("src"),
    help="Source code directory",
)
@click.option("--coverage-file", default=".coverage", help="Coverage data file path")
@click.option(
    "--min-coverage", type=float, default=80.0, help="Minimum line coverage threshold"
)
@click.option(
    "--min-branch", type=float, default=70.0, help="Minimum branch coverage threshold"
)
@click.option(
    "--max-critical-gaps", type=int, default=5, help="Maximum critical gaps allowed"
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=Path("coverage_reports"),
    help="Output directory",
)
@click.option(
    "--junit-xml", type=click.Path(path_type=Path), help="Export JUnit XML results"
)
@click.option("--commit-hash", help="Git commit hash")
@click.option("--branch-name", help="Git branch name")
def ci(
    source_dir,
    coverage_file,
    min_coverage,
    min_branch,
    max_critical_gaps,
    output_dir,
    junit_xml,
    commit_hash,
    branch_name,
):
    """Run coverage analysis for CI/CD pipelines."""
    try:
        runner = CICoverageRunner(source_dir, coverage_file, output_dir)

        # Set up quality gates
        quality_gates = [
            QualityGate(
                "MinimumLineCoverage",
                "line_coverage_percent",
                min_coverage,
                severity="error",
            ),
            QualityGate(
                "MinimumBranchCoverage",
                "branch_coverage_percent",
                min_branch,
                severity="warning",
            ),
            QualityGate(
                "MaximumCriticalGaps",
                "critical_gaps",
                max_critical_gaps,
                operator="lte",
                severity="error",
            ),
        ]

        # Run analysis
        results = runner.run_coverage_analysis(
            quality_gates=quality_gates,
            commit_hash=commit_hash,
            branch_name=branch_name,
        )

        # Display summary
        summary = runner.generate_ci_summary(results)
        click.echo(summary)

        # Export JUnit XML if requested
        if junit_xml:
            runner.export_junit_xml(results, junit_xml)
            click.echo(f"📄 JUnit XML exported to: {junit_xml}")

        # Exit with appropriate code
        sys.exit(results["exit_code"])

    except Exception as e:
        click.echo(f"❌ CI coverage analysis failed: {e}", err=True)
        sys.exit(1)


@coverage.command()
@click.option(
    "--data-dir",
    type=click.Path(path_type=Path),
    default=Path("coverage_history"),
    help="Coverage history directory",
)
@click.option(
    "--keep-days", type=int, default=365, help="Number of days of history to keep"
)
@click.confirmation_option(
    prompt="Are you sure you want to clean up old coverage data?"
)
def clean(data_dir, keep_days):
    """Clean up old coverage data."""
    try:
        tracker = CoverageTracker(data_dir)
        tracker.cleanup_old_data(keep_days)
        click.echo(f"✅ Cleaned up coverage data older than {keep_days} days")

    except Exception as e:
        click.echo(f"❌ Cleanup failed: {e}", err=True)
        sys.exit(1)


def _format_analysis_text(metrics, summary, detailed):
    """Format coverage analysis as text."""
    lines = [
        "=" * 60,
        "COVERAGE ANALYSIS REPORT",
        "=" * 60,
        "",
        "📊 COVERAGE METRICS",
        "-" * 30,
        f"Line Coverage:      {metrics.line_coverage_percent:6.1f}%",
        f"Branch Coverage:    {metrics.branch_coverage_percent:6.1f}%",
        f"Function Coverage:  {metrics.function_coverage_percent:6.1f}%",
        f"Overall Score:      {metrics.overall_score:6.1f}",
        f"Effective Coverage: {metrics.effective_coverage_score:6.1f}%",
        f"Test Quality:       {metrics.test_quality_score:6.1f}",
        "",
        "🚨 COVERAGE GAPS",
        "-" * 30,
        f"Total Gaps:         {metrics.total_gaps}",
        f"Critical Gaps:      {metrics.critical_gaps}",
        f"High Priority:      {metrics.high_priority_gaps}",
        "",
        "📈 TREND ANALYSIS",
        "-" * 30,
        f"Trend Direction:    {metrics.coverage_trend.title()}",
        f"Trend Change:       {metrics.trend_percentage:+.1f}%",
        "",
        "📁 FILE ANALYSIS",
        "-" * 30,
        f"Well Covered:       {metrics.well_covered_files} files (≥90%)",
        f"Poorly Covered:     {metrics.poorly_covered_files} files (<50%)",
        f"Uncovered:          {metrics.uncovered_files} files (0%)",
    ]

    if detailed and "gaps_detail" in summary:
        lines.extend(["", "🔍 DETAILED GAPS (Top 20)", "-" * 30])

        for gap in summary["gaps_detail"]:
            lines.append(
                f"• {Path(gap['file']).name}:{gap['lines']} - {gap['type']} ({gap['severity']})"
            )
            if gap["function"]:
                lines.append(f"  Function: {gap['function']}")
            if gap["suggestions"]:
                lines.append(f"  Suggestion: {gap['suggestions'][0]}")
            lines.append("")

    return "\n".join(lines)


def _format_suggestions_text(suggestions):
    """Format test suggestions as text."""
    lines = [
        "=" * 60,
        "TEST SUGGESTIONS",
        "=" * 60,
        "",
        f"Generated {len(suggestions)} test suggestions to improve coverage:",
        "",
    ]

    # Group by priority
    high_priority = [s for s in suggestions if s.priority == "high"]
    medium_priority = [s for s in suggestions if s.priority == "medium"]
    low_priority = [s for s in suggestions if s.priority == "low"]

    for priority_name, priority_suggestions in [
        ("HIGH PRIORITY", high_priority),
        ("MEDIUM PRIORITY", medium_priority),
        ("LOW PRIORITY", low_priority),
    ]:
        if not priority_suggestions:
            continue

        lines.extend(
            [f"🔥 {priority_name} ({len(priority_suggestions)} suggestions)", "-" * 50]
        )

        for suggestion in priority_suggestions:
            file_name = Path(suggestion.file_path).name
            function_info = suggestion.function_name or "module level"
            if suggestion.class_name:
                function_info = f"{suggestion.class_name}.{function_info}"

            lines.extend(
                [
                    f"• {file_name} - {function_info}",
                    f"  Type: {suggestion.test_type.replace('_', ' ').title()}",
                    f"  Description: {suggestion.description}",
                    f"  Suggested test: {suggestion.full_test_name}",
                    "",
                ]
            )

    return "\n".join(lines)


def _display_trends_text(stats, regression_info):
    """Display trend analysis as formatted text."""
    click.echo("=" * 60)
    click.echo("COVERAGE TRENDS ANALYSIS")
    click.echo("=" * 60)
    click.echo()

    click.echo(f"📊 ANALYSIS PERIOD: {stats['period_days']} days")
    click.echo(f"📈 DATA POINTS: {stats['data_points']}")
    click.echo(f"📅 PERIOD: {stats['first_timestamp']} to {stats['last_timestamp']}")
    click.echo()

    # Display statistics for each metric
    for metric, data in stats.get("statistics", {}).items():
        metric_name = metric.replace("_", " ").title()
        trend = data.get("trend", {})

        click.echo(f"📊 {metric_name.upper()}")
        click.echo("-" * 30)
        click.echo(f"Current:    {data['current']:.1f}%")
        click.echo(f"Average:    {data['average']:.1f}%")
        click.echo(f"Range:      {data['min']:.1f}% - {data['max']:.1f}%")
        click.echo(f"Trend:      {trend.get('direction', 'unknown').title()}")
        click.echo(f"Change:     {trend.get('change_percentage', 0):+.1f}%")
        click.echo()

    # Display regression information
    if regression_info.get("has_regression"):
        click.echo("🚨 REGRESSION DETECTED")
        click.echo("-" * 30)
        for regression in regression_info.get("regressions", []):
            click.echo(f"• {regression['metric'].replace('_', ' ').title()}")
            click.echo(f"  Current: {regression['current_value']:.1f}")
            click.echo(f"  Average: {regression['recent_average']:.1f}")
            click.echo(f"  Drop: {regression['percentage_drop']:.1f}%")
            click.echo(f"  Severity: {regression['severity'].upper()}")
            click.echo()
    else:
        click.echo("✅ No regressions detected")


if __name__ == "__main__":
    coverage()
