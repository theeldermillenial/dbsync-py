"""CI/CD Integration for Coverage Analysis.

This module provides quality gate enforcement, automated coverage analysis,
and CI/CD pipeline integration capabilities.
"""

import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .analyzer import CoverageAnalyzer, CoverageQualityMetrics
from .reporter import CoverageReporter
from .tracker import CoverageTracker


@dataclass
class QualityGate:
    """Represents a quality gate for coverage analysis."""

    name: str
    metric: str  # 'line_coverage', 'branch_coverage', 'overall_score', etc.
    threshold: float
    operator: str = "gte"  # 'gte', 'lte', 'eq'
    enabled: bool = True
    severity: str = "error"  # 'error', 'warning'

    def evaluate(self, value: float) -> bool:
        """Evaluate if the quality gate passes.

        Args:
            value: Current metric value

        Returns:
            True if gate passes, False otherwise
        """
        if not self.enabled:
            return True

        if self.operator == "gte":
            return value >= self.threshold
        elif self.operator == "lte":
            return value <= self.threshold
        elif self.operator == "eq":
            return (
                abs(value - self.threshold) < 0.01
            )  # Allow small floating point differences
        else:
            return True


@dataclass
class QualityGateResult:
    """Result of quality gate evaluation."""

    gate: QualityGate
    current_value: float
    passed: bool
    difference: float
    message: str

    @property
    def status(self) -> str:
        """Get status string for the result."""
        return "PASS" if self.passed else "FAIL"


class CICoverageRunner:
    """Runs coverage analysis in CI/CD environments with quality gates."""

    def __init__(
        self,
        source_dir: Path = Path("src"),
        coverage_file: str = ".coverage",
        output_dir: Path = Path("coverage_reports"),
    ):
        """Initialize CI coverage runner.

        Args:
            source_dir: Source code directory
            coverage_file: Coverage data file
            output_dir: Output directory for reports
        """
        self.source_dir = Path(source_dir)
        self.coverage_file = coverage_file
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Initialize components
        self.analyzer = CoverageAnalyzer(source_dir, coverage_file)
        self.tracker = CoverageTracker(self.output_dir / "history")
        self.reporter = CoverageReporter(output_dir)

        # Default quality gates
        self.quality_gates = self._create_default_quality_gates()

    def run_coverage_analysis(
        self,
        quality_gates: list[QualityGate] | None = None,
        generate_reports: bool = True,
        track_trends: bool = True,
        fail_on_regression: bool = True,
        commit_hash: str | None = None,
        branch_name: str | None = None,
    ) -> dict[str, Any]:
        """Run comprehensive coverage analysis for CI/CD.

        Args:
            quality_gates: Custom quality gates to evaluate
            generate_reports: Whether to generate HTML/JSON reports
            track_trends: Whether to track coverage trends
            fail_on_regression: Whether to fail on coverage regression
            commit_hash: Git commit hash
            branch_name: Git branch name

        Returns:
            Dictionary with analysis results and exit status
        """
        results = {
            "timestamp": datetime.now(UTC).isoformat(),
            "status": "success",
            "exit_code": 0,
            "commit_hash": commit_hash,
            "branch_name": branch_name,
        }

        try:
            # Load coverage data
            if not self.analyzer.load_coverage_data():
                return {
                    "status": "error",
                    "exit_code": 1,
                    "message": "Failed to load coverage data",
                    "timestamp": datetime.now(UTC).isoformat(),
                }

            # Get coverage metrics
            metrics = self.analyzer.calculate_quality_metrics()
            gaps = self.analyzer.analyze_coverage_gaps()

            # Evaluate quality gates
            gates_to_use = quality_gates or self.quality_gates
            gate_results = self._evaluate_quality_gates(gates_to_use, metrics)

            # Check for regressions if tracking enabled
            regression_info = {}
            if track_trends:
                # Record current metrics
                test_count = self._get_test_count()
                self.tracker.record_coverage(
                    metrics.line_coverage_percent,
                    metrics.branch_coverage_percent,
                    metrics.function_coverage_percent,
                    metrics.overall_score,
                    test_count,
                    commit_hash,
                    branch_name,
                )

                # Check for regressions
                regression_info = self.tracker.detect_coverage_regression()

                if fail_on_regression and regression_info.get("has_regression", False):
                    results["status"] = "failure"
                    results["exit_code"] = 1

            # Generate reports if requested
            report_files = {}
            if generate_reports:
                report_files = self.reporter.generate_comprehensive_report(
                    self.analyzer, self.tracker, title="CI Coverage Analysis"
                )

            # Determine overall status
            failed_gates = [
                r for r in gate_results if not r.passed and r.gate.severity == "error"
            ]
            warning_gates = [
                r for r in gate_results if not r.passed and r.gate.severity == "warning"
            ]

            if failed_gates:
                results["status"] = "failure"
                results["exit_code"] = 1
            elif warning_gates:
                results["status"] = "warning"
                # Don't set exit_code to 1 for warnings

            # Compile results
            results.update(
                {
                    "metrics": {
                        "line_coverage": metrics.line_coverage_percent,
                        "branch_coverage": metrics.branch_coverage_percent,
                        "function_coverage": metrics.function_coverage_percent,
                        "overall_score": metrics.overall_score,
                        "critical_gaps": metrics.critical_gaps,
                        "high_priority_gaps": metrics.high_priority_gaps,
                        "total_gaps": len(gaps),
                    },
                    "quality_gates": {
                        "total": len(gate_results),
                        "passed": len([r for r in gate_results if r.passed]),
                        "failed": len(failed_gates),
                        "warnings": len(warning_gates),
                        "results": [
                            {
                                "name": r.gate.name,
                                "metric": r.gate.metric,
                                "threshold": r.gate.threshold,
                                "current": r.current_value,
                                "status": r.status,
                                "difference": r.difference,
                                "severity": r.gate.severity,
                                "message": r.message,
                            }
                            for r in gate_results
                        ],
                    },
                    "regression_check": regression_info,
                    "reports": {str(k): str(v) for k, v in report_files.items()},
                    "summary": self._generate_summary_message(
                        gate_results, regression_info, metrics
                    ),
                }
            )

        except Exception as e:
            results = {
                "status": "error",
                "exit_code": 1,
                "message": f"Coverage analysis failed: {e!s}",
                "timestamp": datetime.now(UTC).isoformat(),
            }

        return results

    def run_quick_check(self, min_coverage: float = 80.0) -> tuple[bool, str]:
        """Run quick coverage check with minimal overhead.

        Args:
            min_coverage: Minimum line coverage percentage required

        Returns:
            Tuple of (passed, message)
        """
        try:
            if not self.analyzer.load_coverage_data():
                return False, "Failed to load coverage data"

            metrics = self.analyzer.calculate_quality_metrics()

            if metrics.line_coverage_percent >= min_coverage:
                return (
                    True,
                    f"Coverage check passed: {metrics.line_coverage_percent:.1f}% >= {min_coverage}%",
                )
            else:
                return (
                    False,
                    f"Coverage check failed: {metrics.line_coverage_percent:.1f}% < {min_coverage}%",
                )

        except Exception as e:
            return False, f"Coverage check error: {e!s}"

    def generate_ci_summary(self, results: dict[str, Any]) -> str:
        """Generate CI-friendly summary message.

        Args:
            results: Results from run_coverage_analysis

        Returns:
            Formatted summary message
        """
        if results["status"] == "error":
            return (
                f"❌ Coverage Analysis Error: {results.get('message', 'Unknown error')}"
            )

        metrics = results.get("metrics", {})
        gates = results.get("quality_gates", {})

        status_emoji = {"success": "✅", "warning": "⚠️", "failure": "❌"}.get(
            results["status"], "❓"
        )

        summary_lines = [
            f"{status_emoji} Coverage Analysis: {results['status'].upper()}",
            f"📊 Line Coverage: {metrics.get('line_coverage', 0):.1f}%",
            f"🌿 Branch Coverage: {metrics.get('branch_coverage', 0):.1f}%",
            f"⭐ Overall Score: {metrics.get('overall_score', 0):.1f}",
            f"🚨 Critical Gaps: {metrics.get('critical_gaps', 0)}",
            f"🚪 Quality Gates: {gates.get('passed', 0)}/{gates.get('total', 0)} passed",
        ]

        if results.get("regression_check", {}).get("has_regression"):
            summary_lines.append("📉 Regression detected!")

        return "\n".join(summary_lines)

    def export_junit_xml(self, results: dict[str, Any], output_file: Path) -> None:
        """Export results as JUnit XML for CI integration.

        Args:
            results: Results from run_coverage_analysis
            output_file: Path to output XML file
        """
        gate_results = results.get("quality_gates", {}).get("results", [])

        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="Coverage Analysis" tests="{len(gate_results)}" failures="{len([r for r in gate_results if r["status"] == "FAIL"])}" time="0">
"""

        for gate_result in gate_results:
            test_name = f"QualityGate.{gate_result['name']}"

            if gate_result["status"] == "PASS":
                xml_content += (
                    f'    <testcase name="{test_name}" classname="CoverageAnalysis"/>\n'
                )
            else:
                xml_content += f"""    <testcase name="{test_name}" classname="CoverageAnalysis">
        <failure message="{gate_result["message"]}">{gate_result["message"]}</failure>
    </testcase>
"""

        xml_content += "</testsuite>\n"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(xml_content)

    def set_quality_gates(self, gates: list[QualityGate]) -> None:
        """Set custom quality gates.

        Args:
            gates: List of quality gates to use
        """
        self.quality_gates = gates

    def add_quality_gate(self, gate: QualityGate) -> None:
        """Add a quality gate.

        Args:
            gate: Quality gate to add
        """
        self.quality_gates.append(gate)

    def _create_default_quality_gates(self) -> list[QualityGate]:
        """Create default quality gates."""
        return [
            QualityGate(
                name="MinimumLineCoverage",
                metric="line_coverage_percent",
                threshold=80.0,
                severity="error",
            ),
            QualityGate(
                name="MinimumBranchCoverage",
                metric="branch_coverage_percent",
                threshold=70.0,
                severity="warning",
            ),
            QualityGate(
                name="MaximumCriticalGaps",
                metric="critical_gaps",
                threshold=5.0,
                operator="lte",
                severity="error",
            ),
            QualityGate(
                name="MinimumOverallScore",
                metric="overall_score",
                threshold=75.0,
                severity="warning",
            ),
        ]

    def _evaluate_quality_gates(
        self, gates: list[QualityGate], metrics: CoverageQualityMetrics
    ) -> list[QualityGateResult]:
        """Evaluate quality gates against metrics.

        Args:
            gates: Quality gates to evaluate
            metrics: Coverage metrics

        Returns:
            List of quality gate results
        """
        results = []

        for gate in gates:
            # Get current value for the metric
            if hasattr(metrics, gate.metric):
                current_value = getattr(metrics, gate.metric)
            else:
                # Handle special cases
                current_value = 0.0

            passed = gate.evaluate(current_value)
            difference = current_value - gate.threshold

            if passed:
                message = f"{gate.name} passed: {current_value:.1f} {gate.operator} {gate.threshold}"
            else:
                message = f"{gate.name} failed: {current_value:.1f} not {gate.operator} {gate.threshold} (diff: {difference:.1f})"

            results.append(
                QualityGateResult(
                    gate=gate,
                    current_value=current_value,
                    passed=passed,
                    difference=difference,
                    message=message,
                )
            )

        return results

    def _get_test_count(self) -> int:
        """Get total number of tests."""
        try:
            # Try to get test count from pytest
            result = subprocess.run(
                ["python", "-m", "pytest", "--collect-only", "-q"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                # Parse output to count tests
                lines = result.stdout.split("\n")
                for line in lines:
                    if "tests collected" in line:
                        # Extract number from line like "123 tests collected"
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part.isdigit():
                                return int(part)

        except Exception:
            pass

        return 0  # Default if unable to determine

    def _generate_summary_message(
        self,
        gate_results: list[QualityGateResult],
        regression_info: dict[str, Any],
        metrics: CoverageQualityMetrics,
    ) -> str:
        """Generate summary message for results."""
        failed_gates = [
            r for r in gate_results if not r.passed and r.gate.severity == "error"
        ]
        warning_gates = [
            r for r in gate_results if not r.passed and r.gate.severity == "warning"
        ]

        if failed_gates:
            return (
                f"Coverage analysis failed: {len(failed_gates)} quality gate(s) failed"
            )
        elif regression_info.get("has_regression"):
            return f"Coverage regression detected: {len(regression_info.get('regressions', []))} metric(s) regressed"
        elif warning_gates:
            return f"Coverage analysis passed with warnings: {len(warning_gates)} quality gate(s) have warnings"
        else:
            return (
                f"Coverage analysis passed: {metrics.overall_score:.1f} overall score"
            )


def main():
    """CLI entry point for CI coverage analysis."""
    import argparse

    parser = argparse.ArgumentParser(description="Run coverage analysis for CI/CD")
    parser.add_argument(
        "--min-coverage",
        type=float,
        default=80.0,
        help="Minimum line coverage percentage (default: 80.0)",
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=Path("src"),
        help="Source code directory (default: src)",
    )
    parser.add_argument(
        "--coverage-file",
        default=".coverage",
        help="Coverage data file (default: .coverage)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("coverage_reports"),
        help="Output directory for reports (default: coverage_reports)",
    )
    parser.add_argument(
        "--quick", action="store_true", help="Run quick coverage check only"
    )
    parser.add_argument(
        "--no-reports", action="store_true", help="Skip report generation"
    )
    parser.add_argument(
        "--no-tracking", action="store_true", help="Skip trend tracking"
    )
    parser.add_argument(
        "--junit-xml", type=Path, help="Export JUnit XML to specified file"
    )
    parser.add_argument("--commit-hash", help="Git commit hash")
    parser.add_argument("--branch-name", help="Git branch name")

    args = parser.parse_args()

    runner = CICoverageRunner(
        source_dir=args.source_dir,
        coverage_file=args.coverage_file,
        output_dir=args.output_dir,
    )

    if args.quick:
        # Quick check mode
        passed, message = runner.run_quick_check(args.min_coverage)
        print(message)
        sys.exit(0 if passed else 1)

    # Full analysis
    results = runner.run_coverage_analysis(
        generate_reports=not args.no_reports,
        track_trends=not args.no_tracking,
        commit_hash=args.commit_hash,
        branch_name=args.branch_name,
    )

    # Print summary
    summary = runner.generate_ci_summary(results)
    print(summary)

    # Export JUnit XML if requested
    if args.junit_xml:
        runner.export_junit_xml(results, args.junit_xml)
        print(f"JUnit XML exported to: {args.junit_xml}")

    # Output JSON results for further processing
    print("\n" + "=" * 50)
    print("DETAILED RESULTS:")
    print(json.dumps(results, indent=2))

    sys.exit(results["exit_code"])


if __name__ == "__main__":
    main()
