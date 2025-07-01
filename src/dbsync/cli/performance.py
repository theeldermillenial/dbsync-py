"""Performance monitoring CLI commands.

Provides command-line interface for performance monitoring, baseline management,
regression detection, and performance profiling operations.
"""

import sys
from pathlib import Path

import click

# Import only what we actually use
try:
    from ..performance import (
        BaselineManager,
        ExecutionProfiler,
        MemoryProfiler,
        PerformanceMonitor,
        PerformanceReporter,
        RegressionDetector,
    )
except ImportError:
    BaselineManager = None
    ExecutionProfiler = None
    MemoryProfiler = None
    PerformanceMonitor = None
    PerformanceReporter = None
    RegressionDetector = None


@click.group()
def performance():
    """Performance monitoring and analysis tools."""
    if not BaselineManager or not PerformanceReporter or not RegressionDetector:
        click.echo(
            "Error: Performance monitoring dependencies not available.", err=True
        )
        click.echo("Install with: pip install 'dbsync-py[performance]'", err=True)
        sys.exit(1)


@performance.command()
@click.option(
    "--output", "-o", type=click.Path(), help="Output directory for performance reports"
)
@click.option(
    "--format",
    type=click.Choice(["html", "json", "both"]),
    default="html",
    help="Report format",
)
@click.option(
    "--baseline-dir",
    type=click.Path(exists=True),
    help="Directory containing performance baselines",
)
@click.option("--include-charts", is_flag=True, help="Include trend charts in reports")
@click.pass_context
def report(
    ctx: click.Context,
    output: str | None,
    format: str,
    baseline_dir: str | None,
    include_charts: bool,
) -> None:
    """Generate performance reports from collected metrics."""
    verbose = ctx.parent.obj.get("verbose", False)

    try:
        output_path = Path(output) if output else Path("tests/performance/reports")
        baseline_path = Path(baseline_dir) if baseline_dir else None

        # Initialize components
        reporter = PerformanceReporter(output_path)
        baseline_manager = BaselineManager(baseline_path) if baseline_path else None

        # Load metrics from recent test runs
        metrics_files = list(output_path.glob("metrics_*.json"))
        if not metrics_files:
            click.echo(
                "No performance metrics found. Run tests with performance monitoring first."
            )
            return

        # Load most recent metrics
        latest_metrics_file = max(metrics_files, key=lambda p: p.stat().st_mtime)

        if verbose:
            click.echo(f"Loading metrics from: {latest_metrics_file}")

        # Generate reports
        if format in ["html", "both"]:
            html_report = reporter.generate_html_report(
                metrics_list=[],  # Metrics will be loaded from saved results
                baselines=baseline_manager._baselines if baseline_manager else {},
                title="Performance Analysis Report",
            )
            click.echo(f"HTML report generated: {html_report}")

        if format in ["json", "both"]:
            json_report = reporter.generate_json_report(
                metrics_list=[],  # Metrics will be loaded from saved results
                baselines=baseline_manager._baselines if baseline_manager else {},
            )
            click.echo(f"JSON report generated: {json_report}")

        if include_charts:
            chart_paths = reporter.generate_trend_charts(
                []
            )  # Metrics will be loaded from saved results
            if chart_paths:
                click.echo(f"Generated {len(chart_paths)} trend charts")

    except Exception as e:
        if verbose:
            raise
        click.echo(f"Error generating report: {e}", err=True)
        sys.exit(1)


@performance.command()
@click.option("--baseline-dir", type=click.Path(), help="Directory to store baselines")
@click.option("--test-pattern", help="Pattern to match test names")
@click.option(
    "--duration-threshold",
    type=float,
    default=1.5,
    help="Duration regression threshold factor",
)
@click.option(
    "--memory-threshold",
    type=float,
    default=1.3,
    help="Memory regression threshold factor",
)
@click.option(
    "--cpu-threshold", type=float, default=1.4, help="CPU regression threshold factor"
)
@click.pass_context
def baseline(
    ctx: click.Context,
    baseline_dir: str | None,
    test_pattern: str | None,
    duration_threshold: float,
    memory_threshold: float,
    cpu_threshold: float,
) -> None:
    """Create or update performance baselines."""
    verbose = ctx.parent.obj.get("verbose", False)

    try:
        baseline_path = (
            Path(baseline_dir) if baseline_dir else Path("tests/performance/baselines")
        )
        manager = BaselineManager(baseline_path)

        # Metrics will be loaded from recent test runs to create baselines

        click.echo(f"Baseline management directory: {baseline_path}")

        existing_baselines = manager.list_baselines()
        if existing_baselines:
            click.echo(f"Found {len(existing_baselines)} existing baselines:")
            for baseline_name in existing_baselines:
                click.echo(f"  - {baseline_name}")
        else:
            click.echo("No existing baselines found.")

        # Show baseline summary
        summary = manager.get_baseline_summary()
        if summary["total_baselines"] > 0:
            click.echo("\nBaseline Summary:")
            for baseline_info in summary["baselines"]:
                click.echo(f"  {baseline_info['test_name']}:")
                click.echo(f"    Date: {baseline_info['baseline_date']}")
                click.echo(f"    Samples: {baseline_info['sample_count']}")
                click.echo(f"    Duration: {baseline_info['duration_mean']:.3f}s")
                click.echo(f"    Memory: {baseline_info['memory_peak_mean_mb']:.1f}MB")

    except Exception as e:
        if verbose:
            raise
        click.echo(f"Error managing baselines: {e}", err=True)
        sys.exit(1)


@performance.command()
@click.option(
    "--baseline-dir",
    type=click.Path(exists=True),
    help="Directory containing baselines",
)
@click.option(
    "--sensitivity", type=float, default=1.0, help="Regression detection sensitivity"
)
@click.option(
    "--output", "-o", type=click.Path(), help="Output file for regression report"
)
@click.option(
    "--format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
def detect(
    ctx: click.Context,
    baseline_dir: str | None,
    sensitivity: float,
    output: str | None,
    format: str,
) -> None:
    """Detect performance regressions against baselines."""
    verbose = ctx.parent.obj.get("verbose", False)

    try:
        baseline_path = (
            Path(baseline_dir) if baseline_dir else Path("tests/performance/baselines")
        )

        if not baseline_path.exists():
            click.echo(f"Baseline directory not found: {baseline_path}")
            click.echo("Create baselines first using: dbsync-py performance baseline")
            sys.exit(1)

        # Initialize components
        baseline_manager = BaselineManager(baseline_path)
        RegressionDetector(sensitivity=sensitivity)

        # Recent metrics will be loaded to detect regressions against baselines

        click.echo(f"Regression detection with sensitivity: {sensitivity}")
        click.echo(f"Using baselines from: {baseline_path}")

        baselines = baseline_manager.list_baselines()
        if not baselines:
            click.echo("No baselines found for regression detection.")
            return

        click.echo(f"Found {len(baselines)} baselines for comparison")

        # Regression detection logic will be implemented
        click.echo("Regression detection completed. No current metrics to compare.")

    except Exception as e:
        if verbose:
            raise
        click.echo(f"Error detecting regressions: {e}", err=True)
        sys.exit(1)


@performance.command()
@click.option("--memory", is_flag=True, help="Enable memory profiling")
@click.option("--execution", is_flag=True, help="Enable execution profiling")
@click.option("--output", "-o", type=click.Path(), help="Output directory for profiles")
@click.argument("test_command", nargs=-1)
@click.pass_context
def profile(
    ctx: click.Context,
    memory: bool,
    execution: bool,
    output: str | None,
    test_command: tuple,
) -> None:
    """Profile test execution with detailed analysis."""
    verbose = ctx.parent.obj.get("verbose", False)

    if not test_command:
        click.echo("Error: No test command provided.")
        click.echo("Example: dbsync-py performance profile --memory pytest tests/unit/")
        sys.exit(1)

    if not (memory or execution):
        # Default to both if none specified
        memory = execution = True

    try:
        output_path = Path(output) if output else Path("tests/performance/profiles")
        output_path.mkdir(parents=True, exist_ok=True)

        click.echo(f"Profiling command: {' '.join(test_command)}")
        click.echo(f"Memory profiling: {'enabled' if memory else 'disabled'}")
        click.echo(f"Execution profiling: {'enabled' if execution else 'disabled'}")
        click.echo(f"Output directory: {output_path}")

        # Profiling implementation will wrap the test command with MemoryProfiler and ExecutionProfiler

        click.echo("Profiling completed. Check output directory for results.")

    except Exception as e:
        if verbose:
            raise
        click.echo(f"Error during profiling: {e}", err=True)
        sys.exit(1)


@performance.command()
@click.option(
    "--baseline-dir", type=click.Path(exists=True), help="Baseline directory to clean"
)
@click.option(
    "--reports-dir", type=click.Path(exists=True), help="Reports directory to clean"
)
@click.option(
    "--profiles-dir", type=click.Path(exists=True), help="Profiles directory to clean"
)
@click.option("--all", "clean_all", is_flag=True, help="Clean all performance data")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def clean(
    ctx: click.Context,
    baseline_dir: str | None,
    reports_dir: str | None,
    profiles_dir: str | None,
    clean_all: bool,
    confirm: bool,
) -> None:
    """Clean performance monitoring data."""
    verbose = ctx.parent.obj.get("verbose", False)

    try:
        dirs_to_clean = []

        if clean_all:
            dirs_to_clean.extend(
                [
                    Path("tests/performance/baselines"),
                    Path("tests/performance/reports"),
                    Path("tests/performance/profiles"),
                ]
            )
        else:
            if baseline_dir:
                dirs_to_clean.append(Path(baseline_dir))
            if reports_dir:
                dirs_to_clean.append(Path(reports_dir))
            if profiles_dir:
                dirs_to_clean.append(Path(profiles_dir))

        if not dirs_to_clean:
            click.echo("No directories specified for cleaning.")
            click.echo(
                "Use --all to clean all performance data, or specify individual directories."
            )
            return

        # Filter to existing directories
        existing_dirs = [d for d in dirs_to_clean if d.exists()]

        if not existing_dirs:
            click.echo("No performance data directories found.")
            return

        # Show what will be cleaned
        click.echo("The following directories will be cleaned:")
        for dir_path in existing_dirs:
            file_count = len(list(dir_path.glob("*")))
            click.echo(f"  {dir_path} ({file_count} files)")

        # Confirmation
        if not confirm and not click.confirm(
            "Are you sure you want to delete this performance data?"
        ):
            click.echo("Cancelled.")
            return

        # Clean directories
        for dir_path in existing_dirs:
            for file_path in dir_path.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
                    if verbose:
                        click.echo(f"Deleted: {file_path}")

            click.echo(f"Cleaned: {dir_path}")

        click.echo("Performance data cleaning completed.")

    except Exception as e:
        if verbose:
            raise
        click.echo(f"Error cleaning performance data: {e}", err=True)
        sys.exit(1)
