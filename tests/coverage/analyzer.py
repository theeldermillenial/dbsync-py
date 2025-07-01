"""Advanced Coverage Analysis.

This module provides sophisticated coverage analysis capabilities including:
- Detailed coverage gap identification
- Quality metrics calculation
- Code complexity analysis
- Coverage effectiveness scoring
"""

import ast
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from coverage import Coverage
from coverage.data import CoverageData


@dataclass
class CoverageGap:
    """Represents a gap in test coverage."""

    file_path: str
    line_start: int
    line_end: int
    gap_type: str  # 'uncovered_lines', 'missing_branch', 'complex_function'
    severity: str  # 'low', 'medium', 'high', 'critical'
    function_name: str | None = None
    class_name: str | None = None
    complexity_score: int | None = None
    suggested_tests: list[str] = None

    def __post_init__(self):
        if self.suggested_tests is None:
            self.suggested_tests = []


@dataclass
class CoverageQualityMetrics:
    """Quality metrics for test coverage."""

    # Basic coverage metrics
    line_coverage_percent: float
    branch_coverage_percent: float
    function_coverage_percent: float

    # Advanced metrics
    effective_coverage_score: float  # Weighted score considering complexity
    test_quality_score: float  # Quality of existing tests
    coverage_density: float  # Coverage per line of code

    # Gap analysis
    critical_gaps: int
    high_priority_gaps: int
    total_gaps: int

    # Trend metrics
    coverage_trend: str  # 'improving', 'stable', 'declining'
    trend_percentage: float

    # File-level metrics
    well_covered_files: int
    poorly_covered_files: int
    uncovered_files: int

    @property
    def overall_score(self) -> float:
        """Calculate overall coverage quality score (0-100)."""
        # Weight different aspects
        coverage_weight = 0.4
        quality_weight = 0.3
        gaps_weight = 0.2
        trend_weight = 0.1

        coverage_score = (self.line_coverage_percent + self.branch_coverage_percent) / 2
        quality_score = self.test_quality_score
        gaps_score = max(
            0, 100 - (self.critical_gaps * 10 + self.high_priority_gaps * 5)
        )
        trend_score = 50 + self.trend_percentage  # Normalize to 0-100

        return (
            coverage_score * coverage_weight
            + quality_score * quality_weight
            + gaps_score * gaps_weight
            + trend_score * trend_weight
        )


class CoverageAnalyzer:
    """Advanced coverage analyzer with gap detection and quality metrics."""

    def __init__(
        self, source_dir: Path = Path("src"), coverage_file: str = ".coverage"
    ):
        """Initialize coverage analyzer.

        Args:
            source_dir: Directory containing source code
            coverage_file: Path to coverage data file
        """
        self.source_dir = Path(source_dir)
        self.coverage_file = coverage_file
        self.coverage_data: CoverageData | None = None
        self.coverage_obj: Coverage | None = None

    def load_coverage_data(self) -> bool:
        """Load coverage data from file.

        Returns:
            True if data loaded successfully
        """
        try:
            self.coverage_obj = Coverage(data_file=self.coverage_file)
            self.coverage_obj.load()
            self.coverage_data = self.coverage_obj.get_data()
            return True
        except Exception as e:
            print(f"Failed to load coverage data: {e}")
            return False

    def analyze_coverage_gaps(self) -> list[CoverageGap]:
        """Analyze coverage data to identify gaps.

        Returns:
            List of coverage gaps found
        """
        if not self.coverage_data:
            return []

        gaps = []

        # Analyze each source file
        for file_path in self.coverage_data.measured_files():
            if not self._is_source_file(file_path):
                continue

            gaps.extend(self._analyze_file_gaps(file_path))

        # Sort gaps by severity and complexity
        gaps.sort(
            key=lambda g: (
                {"critical": 4, "high": 3, "medium": 2, "low": 1}[g.severity],
                g.complexity_score or 0,
            ),
            reverse=True,
        )

        return gaps

    def calculate_quality_metrics(
        self, historical_data: list[dict] | None = None
    ) -> CoverageQualityMetrics:
        """Calculate comprehensive coverage quality metrics.

        Args:
            historical_data: Optional historical coverage data for trend analysis

        Returns:
            Coverage quality metrics
        """
        if not self.coverage_data or not self.coverage_obj:
            return self._empty_metrics()

        # Basic coverage metrics
        line_coverage = self.coverage_obj.report(show_missing=False, file=None)
        branch_coverage = self._calculate_branch_coverage()
        function_coverage = self._calculate_function_coverage()

        # Advanced metrics
        effective_score = self._calculate_effective_coverage()
        quality_score = self._calculate_test_quality()
        density = self._calculate_coverage_density()

        # Gap analysis
        gaps = self.analyze_coverage_gaps()
        critical_gaps = len([g for g in gaps if g.severity == "critical"])
        high_gaps = len([g for g in gaps if g.severity == "high"])

        # Trend analysis
        trend, trend_pct = (
            self._analyze_trend(historical_data) if historical_data else ("stable", 0.0)
        )

        # File-level analysis
        well_covered, poorly_covered, uncovered = self._analyze_file_coverage()

        return CoverageQualityMetrics(
            line_coverage_percent=line_coverage,
            branch_coverage_percent=branch_coverage,
            function_coverage_percent=function_coverage,
            effective_coverage_score=effective_score,
            test_quality_score=quality_score,
            coverage_density=density,
            critical_gaps=critical_gaps,
            high_priority_gaps=high_gaps,
            total_gaps=len(gaps),
            coverage_trend=trend,
            trend_percentage=trend_pct,
            well_covered_files=well_covered,
            poorly_covered_files=poorly_covered,
            uncovered_files=uncovered,
        )

    def get_coverage_summary(self) -> dict[str, Any]:
        """Get comprehensive coverage summary.

        Returns:
            Dictionary with coverage summary data
        """
        if not self.coverage_data:
            return {}

        metrics = self.calculate_quality_metrics()
        gaps = self.analyze_coverage_gaps()

        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "line_coverage": metrics.line_coverage_percent,
                "branch_coverage": metrics.branch_coverage_percent,
                "function_coverage": metrics.function_coverage_percent,
                "overall_score": metrics.overall_score,
                "effective_coverage": metrics.effective_coverage_score,
                "test_quality": metrics.test_quality_score,
            },
            "gaps": {
                "total": len(gaps),
                "critical": metrics.critical_gaps,
                "high": metrics.high_priority_gaps,
                "by_type": self._group_gaps_by_type(gaps),
            },
            "files": {
                "well_covered": metrics.well_covered_files,
                "poorly_covered": metrics.poorly_covered_files,
                "uncovered": metrics.uncovered_files,
            },
            "trend": {
                "direction": metrics.coverage_trend,
                "percentage": metrics.trend_percentage,
            },
        }

    def _is_source_file(self, file_path: str) -> bool:
        """Check if file is a source file to analyze."""
        path = Path(file_path)
        return (
            path.suffix == ".py"
            and str(path).startswith(str(self.source_dir))
            and "__pycache__" not in str(path)
            and not path.name.startswith("test_")
        )

    def _analyze_file_gaps(self, file_path: str) -> list[CoverageGap]:
        """Analyze coverage gaps in a specific file."""
        gaps = []

        try:
            # Get coverage info for file
            missing_lines = self.coverage_data.lines_missing(file_path)
            if not missing_lines:
                return gaps

            # Parse AST to understand code structure
            with open(file_path, encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)

            # Analyze missing lines in context
            for line_num in missing_lines:
                gap = self._analyze_missing_line(file_path, line_num, tree, source)
                if gap:
                    gaps.append(gap)

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")

        return gaps

    def _analyze_missing_line(
        self, file_path: str, line_num: int, tree: ast.AST, source: str
    ) -> CoverageGap | None:
        """Analyze a specific missing line to create a coverage gap."""
        lines = source.split("\n")
        if line_num > len(lines):
            return None

        line_content = lines[line_num - 1].strip()

        # Skip empty lines and comments
        if not line_content or line_content.startswith("#"):
            return None

        # Find containing function/class
        function_name, class_name = self._find_containing_scope(tree, line_num)

        # Determine gap type and severity
        gap_type = self._classify_gap_type(line_content)
        severity = self._determine_severity(line_content, function_name, class_name)
        complexity = self._calculate_line_complexity(line_content)

        return CoverageGap(
            file_path=file_path,
            line_start=line_num,
            line_end=line_num,
            gap_type=gap_type,
            severity=severity,
            function_name=function_name,
            class_name=class_name,
            complexity_score=complexity,
            suggested_tests=self._suggest_tests_for_line(
                line_content, function_name, class_name
            ),
        )

    def _find_containing_scope(
        self, tree: ast.AST, line_num: int
    ) -> tuple[str | None, str | None]:
        """Find the function and class containing a line number."""
        function_name = None
        class_name = None

        for node in ast.walk(tree):
            if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
                if node.lineno <= line_num <= (node.end_lineno or node.lineno):
                    if isinstance(node, ast.FunctionDef):
                        function_name = node.name
                    elif isinstance(node, ast.ClassDef):
                        class_name = node.name

        return function_name, class_name

    def _classify_gap_type(self, line_content: str) -> str:
        """Classify the type of coverage gap."""
        if "if " in line_content or "elif " in line_content:
            return "missing_branch"
        elif "except " in line_content:
            return "exception_handling"
        elif "def " in line_content:
            return "uncovered_function"
        elif "class " in line_content:
            return "uncovered_class"
        elif "raise " in line_content:
            return "error_path"
        else:
            return "uncovered_lines"

    def _determine_severity(
        self, line_content: str, function_name: str | None, class_name: str | None
    ) -> str:
        """Determine severity of coverage gap."""
        # Critical: Error handling, security-related code
        if any(
            keyword in line_content.lower()
            for keyword in ["raise", "except", "assert", "auth", "password", "token"]
        ):
            return "critical"

        # High: Business logic, data validation
        if any(
            keyword in line_content
            for keyword in ["if ", "elif ", "validate", "check", "verify"]
        ):
            return "high"

        # Medium: Utility functions, formatting
        if function_name and any(
            keyword in function_name.lower()
            for keyword in ["format", "convert", "parse", "util"]
        ):
            return "medium"

        # Low: Simple assignments, logging
        return "low"

    def _calculate_line_complexity(self, line_content: str) -> int:
        """Calculate complexity score for a line of code."""
        complexity = 1

        # Add complexity for control structures
        complexity += line_content.count("if ")
        complexity += line_content.count("elif ")
        complexity += line_content.count("for ")
        complexity += line_content.count("while ")
        complexity += line_content.count("try ")
        complexity += line_content.count("except ")

        # Add complexity for operators
        complexity += line_content.count(" and ")
        complexity += line_content.count(" or ")
        complexity += line_content.count(" not ")

        return complexity

    def _suggest_tests_for_line(
        self, line_content: str, function_name: str | None, class_name: str | None
    ) -> list[str]:
        """Suggest test cases for uncovered line."""
        suggestions = []

        if "if " in line_content:
            suggestions.append(
                f"Test both true and false conditions for: {line_content.strip()}"
            )

        if "except " in line_content:
            suggestions.append(f"Test exception handling: {line_content.strip()}")

        if function_name:
            suggestions.append(f"Test function '{function_name}' with edge cases")

        if "raise " in line_content:
            suggestions.append(
                f"Test error condition that triggers: {line_content.strip()}"
            )

        return suggestions

    def _calculate_branch_coverage(self) -> float:
        """Calculate branch coverage percentage."""
        try:
            # Use coverage.py's branch analysis
            total_branches = 0
            covered_branches = 0

            for file_path in self.coverage_data.measured_files():
                if not self._is_source_file(file_path):
                    continue

                branch_lines = self.coverage_data.branch_lines(file_path)
                if branch_lines:
                    total_branches += len(branch_lines)

                    # Count covered branches
                    missing_branches = self.coverage_data.missing_branch_arcs(file_path)
                    covered_branches += len(branch_lines) - len(missing_branches or [])

            return (
                (covered_branches / total_branches * 100) if total_branches > 0 else 0.0
            )

        except Exception:
            return 0.0

    def _calculate_function_coverage(self) -> float:
        """Calculate function coverage percentage."""
        total_functions = 0
        covered_functions = 0

        for file_path in self.coverage_data.measured_files():
            if not self._is_source_file(file_path):
                continue

            try:
                with open(file_path, encoding="utf-8") as f:
                    tree = ast.parse(f.read())

                executed_lines = set(self.coverage_data.lines_executed(file_path) or [])

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        total_functions += 1
                        if node.lineno in executed_lines:
                            covered_functions += 1

            except Exception:
                continue

        return (
            (covered_functions / total_functions * 100) if total_functions > 0 else 0.0
        )

    def _calculate_effective_coverage(self) -> float:
        """Calculate effective coverage score considering code complexity."""
        total_weighted_lines = 0
        covered_weighted_lines = 0

        for file_path in self.coverage_data.measured_files():
            if not self._is_source_file(file_path):
                continue

            try:
                with open(file_path, encoding="utf-8") as f:
                    lines = f.readlines()

                executed_lines = set(self.coverage_data.lines_executed(file_path) or [])

                for i, line in enumerate(lines, 1):
                    if line.strip() and not line.strip().startswith("#"):
                        weight = self._calculate_line_complexity(line)
                        total_weighted_lines += weight

                        if i in executed_lines:
                            covered_weighted_lines += weight

            except Exception:
                continue

        return (
            (covered_weighted_lines / total_weighted_lines * 100)
            if total_weighted_lines > 0
            else 0.0
        )

    def _calculate_test_quality(self) -> float:
        """Calculate test quality score based on test patterns."""
        # This is a simplified implementation
        # In practice, you'd analyze test files for quality indicators
        return 75.0  # Placeholder score

    def _calculate_coverage_density(self) -> float:
        """Calculate coverage density (coverage per line of code)."""
        total_lines = 0
        covered_lines = 0

        for file_path in self.coverage_data.measured_files():
            if not self._is_source_file(file_path):
                continue

            try:
                with open(file_path, encoding="utf-8") as f:
                    file_lines = len(
                        [
                            line
                            for line in f
                            if line.strip() and not line.strip().startswith("#")
                        ]
                    )

                total_lines += file_lines
                covered_lines += len(self.coverage_data.lines_executed(file_path) or [])

            except Exception:
                continue

        return (covered_lines / total_lines) if total_lines > 0 else 0.0

    def _analyze_trend(self, historical_data: list[dict]) -> tuple[str, float]:
        """Analyze coverage trend from historical data."""
        if len(historical_data) < 2:
            return "stable", 0.0

        # Get recent coverage percentages
        recent_coverage = [
            data.get("line_coverage", 0) for data in historical_data[-5:]
        ]

        if len(recent_coverage) < 2:
            return "stable", 0.0

        # Calculate trend
        trend_slope = (recent_coverage[-1] - recent_coverage[0]) / len(recent_coverage)

        if trend_slope > 1.0:
            return "improving", trend_slope
        elif trend_slope < -1.0:
            return "declining", trend_slope
        else:
            return "stable", trend_slope

    def _analyze_file_coverage(self) -> tuple[int, int, int]:
        """Analyze coverage at file level."""
        well_covered = 0  # >90% coverage
        poorly_covered = 0  # <50% coverage
        uncovered = 0  # 0% coverage

        for file_path in self.coverage_data.measured_files():
            if not self._is_source_file(file_path):
                continue

            try:
                executed_lines = len(self.coverage_data.lines_executed(file_path) or [])
                missing_lines = len(self.coverage_data.lines_missing(file_path) or [])
                total_lines = executed_lines + missing_lines

                if total_lines == 0:
                    continue

                coverage_pct = (executed_lines / total_lines) * 100

                if coverage_pct == 0:
                    uncovered += 1
                elif coverage_pct < 50:
                    poorly_covered += 1
                elif coverage_pct >= 90:
                    well_covered += 1

            except Exception:
                continue

        return well_covered, poorly_covered, uncovered

    def _group_gaps_by_type(self, gaps: list[CoverageGap]) -> dict[str, int]:
        """Group coverage gaps by type."""
        gap_types = {}
        for gap in gaps:
            gap_types[gap.gap_type] = gap_types.get(gap.gap_type, 0) + 1
        return gap_types

    def _empty_metrics(self) -> CoverageQualityMetrics:
        """Return empty metrics when no data available."""
        return CoverageQualityMetrics(
            line_coverage_percent=0.0,
            branch_coverage_percent=0.0,
            function_coverage_percent=0.0,
            effective_coverage_score=0.0,
            test_quality_score=0.0,
            coverage_density=0.0,
            critical_gaps=0,
            high_priority_gaps=0,
            total_gaps=0,
            coverage_trend="stable",
            trend_percentage=0.0,
            well_covered_files=0,
            poorly_covered_files=0,
            uncovered_files=0,
        )
