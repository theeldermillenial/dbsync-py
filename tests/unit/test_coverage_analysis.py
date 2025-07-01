"""Unit tests for coverage analysis system.

Tests all components of the comprehensive coverage analysis system including
analyzer, tracker, reporter, generator, and CI integration.
"""

import json
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from tests.coverage.analyzer import (
    CoverageAnalyzer,
    CoverageGap,
    CoverageQualityMetrics,
)
from tests.coverage.ci import CICoverageRunner, QualityGate, QualityGateResult
from tests.coverage.generator import TestGenerator, TestSuggestion
from tests.coverage.reporter import CoverageReporter
from tests.coverage.tracker import CoverageTracker, CoverageTrend


class TestCoverageAnalyzer:
    """Test cases for CoverageAnalyzer class."""

    def test_analyzer_initialization(self):
        """Test CoverageAnalyzer initialization."""
        analyzer = CoverageAnalyzer(Path("src"), ".coverage")

        assert analyzer.source_dir == Path("src")
        assert analyzer.coverage_file == ".coverage"
        assert analyzer.coverage_data is None
        assert analyzer.coverage_obj is None

    def test_load_coverage_data_success(self):
        """Test successful coverage data loading."""
        with patch("tests.coverage.analyzer.Coverage") as mock_coverage:
            mock_cov_obj = Mock()
            mock_cov_data = Mock()
            mock_coverage.return_value = mock_cov_obj
            mock_cov_obj.get_data.return_value = mock_cov_data

            analyzer = CoverageAnalyzer()
            result = analyzer.load_coverage_data()

            assert result is True
            assert analyzer.coverage_obj == mock_cov_obj
            assert analyzer.coverage_data == mock_cov_data

    def test_load_coverage_data_failure(self):
        """Test coverage data loading failure."""
        with patch("tests.coverage.analyzer.Coverage") as mock_coverage:
            mock_coverage.side_effect = Exception("Coverage file not found")

            analyzer = CoverageAnalyzer()
            result = analyzer.load_coverage_data()

            assert result is False
            assert analyzer.coverage_data is None

    def test_coverage_gap_creation(self):
        """Test CoverageGap creation and properties."""
        gap = CoverageGap(
            file_path="test.py",
            line_start=10,
            line_end=15,
            gap_type="missing_branch",
            severity="high",
            function_name="test_function",
            class_name="TestClass",
            complexity_score=3,
        )

        assert gap.file_path == "test.py"
        assert gap.line_start == 10
        assert gap.line_end == 15
        assert gap.gap_type == "missing_branch"
        assert gap.severity == "high"
        assert gap.function_name == "test_function"
        assert gap.class_name == "TestClass"
        assert gap.complexity_score == 3
        assert gap.suggested_tests == []  # Default value

    def test_coverage_quality_metrics_overall_score(self):
        """Test CoverageQualityMetrics overall score calculation."""
        metrics = CoverageQualityMetrics(
            line_coverage_percent=85.0,
            branch_coverage_percent=75.0,
            function_coverage_percent=90.0,
            effective_coverage_score=80.0,
            test_quality_score=85.0,
            coverage_density=0.8,
            critical_gaps=2,
            high_priority_gaps=5,
            total_gaps=15,
            coverage_trend="improving",
            trend_percentage=5.0,
            well_covered_files=20,
            poorly_covered_files=3,
            uncovered_files=1,
        )

        overall_score = metrics.overall_score

        # Should be a weighted average of different factors
        assert 0 <= overall_score <= 100
        assert overall_score > 70  # Should be reasonably high given good metrics

    def test_analyze_coverage_gaps_empty_data(self):
        """Test gap analysis with no coverage data."""
        analyzer = CoverageAnalyzer()
        gaps = analyzer.analyze_coverage_gaps()

        assert gaps == []

    def test_calculate_quality_metrics_no_data(self):
        """Test quality metrics calculation with no data."""
        analyzer = CoverageAnalyzer()
        metrics = analyzer.calculate_quality_metrics()

        # Should return empty metrics
        assert metrics.line_coverage_percent == 0.0
        assert metrics.branch_coverage_percent == 0.0
        assert metrics.function_coverage_percent == 0.0
        assert metrics.total_gaps == 0


class TestCoverageTracker:
    """Test cases for CoverageTracker class."""

    def test_tracker_initialization(self):
        """Test CoverageTracker initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)
            tracker = CoverageTracker(data_dir)

            assert tracker.data_dir == data_dir
            assert tracker.history_file == data_dir / "coverage_history.json"
            assert tracker.trends_file == data_dir / "coverage_trends.json"
            assert data_dir.exists()

    def test_coverage_trend_creation(self):
        """Test CoverageTrend creation and serialization."""
        trend = CoverageTrend(
            timestamp=datetime.now(UTC).isoformat(),
            line_coverage=85.5,
            branch_coverage=75.2,
            function_coverage=90.0,
            overall_score=82.5,
            test_count=150,
            commit_hash="abc123",
            branch_name="main",
        )

        # Test serialization
        trend_dict = trend.to_dict()
        assert trend_dict["line_coverage"] == 85.5
        assert trend_dict["commit_hash"] == "abc123"

        # Test deserialization
        new_trend = CoverageTrend.from_dict(trend_dict)
        assert new_trend.line_coverage == 85.5
        assert new_trend.commit_hash == "abc123"

    def test_record_coverage(self):
        """Test recording coverage data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = CoverageTracker(Path(temp_dir))

            trend = tracker.record_coverage(
                line_coverage=85.0,
                branch_coverage=75.0,
                function_coverage=90.0,
                overall_score=82.0,
                test_count=100,
                commit_hash="test123",
            )

            assert trend.line_coverage == 85.0
            assert trend.commit_hash == "test123"

            # Should be saved to file
            history = tracker.load_history()
            assert len(history) == 1
            assert history[0].line_coverage == 85.0

    def test_load_save_history(self):
        """Test loading and saving coverage history."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = CoverageTracker(Path(temp_dir))

            # Create test trends
            trends = [
                CoverageTrend(
                    timestamp=datetime.now(UTC).isoformat(),
                    line_coverage=80.0,
                    branch_coverage=70.0,
                    function_coverage=85.0,
                    overall_score=78.0,
                    test_count=90,
                ),
                CoverageTrend(
                    timestamp=datetime.now(UTC).isoformat(),
                    line_coverage=85.0,
                    branch_coverage=75.0,
                    function_coverage=90.0,
                    overall_score=82.0,
                    test_count=100,
                ),
            ]

            # Save and load
            tracker.save_history(trends)
            loaded_trends = tracker.load_history()

            assert len(loaded_trends) == 2
            assert loaded_trends[0].line_coverage == 80.0
            assert loaded_trends[1].line_coverage == 85.0

    def test_analyze_trend_direction(self):
        """Test trend direction analysis."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = CoverageTracker(Path(temp_dir))

            # Create improving trend
            base_time = datetime.now(UTC)
            trends = []
            for i in range(5):
                trend = CoverageTrend(
                    timestamp=(base_time + timedelta(days=i)).isoformat(),
                    line_coverage=70.0 + i * 5.0,  # Improving trend
                    branch_coverage=60.0,
                    function_coverage=80.0,
                    overall_score=70.0,
                    test_count=100,
                )
                trends.append(trend)

            tracker.save_history(trends)

            # Analyze trend
            trend_analysis = tracker.analyze_trend_direction("line_coverage", 7)

            assert trend_analysis["direction"] in ["improving", "stable"]
            assert trend_analysis["slope"] > 0  # Positive slope
            assert trend_analysis["current_value"] == 90.0  # Last value

    def test_detect_coverage_regression(self):
        """Test coverage regression detection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = CoverageTracker(Path(temp_dir))

            # Create trends with regression
            base_time = datetime.now(UTC)
            trends = []

            # Good historical coverage
            for i in range(8):
                trend = CoverageTrend(
                    timestamp=(base_time + timedelta(days=i)).isoformat(),
                    line_coverage=85.0,
                    branch_coverage=75.0,
                    function_coverage=90.0,
                    overall_score=82.0,
                    test_count=100,
                )
                trends.append(trend)

            # Regression in latest
            regression_trend = CoverageTrend(
                timestamp=(base_time + timedelta(days=8)).isoformat(),
                line_coverage=70.0,  # Significant drop
                branch_coverage=60.0,
                function_coverage=80.0,
                overall_score=70.0,
                test_count=100,
            )
            trends.append(regression_trend)

            tracker.save_history(trends)

            # Detect regression
            regression_info = tracker.detect_coverage_regression(
                threshold_percentage=10.0
            )

            assert regression_info["has_regression"] is True
            assert len(regression_info["regressions"]) > 0

            # Check line coverage regression
            line_regression = next(
                (
                    r
                    for r in regression_info["regressions"]
                    if r["metric"] == "line_coverage"
                ),
                None,
            )
            assert line_regression is not None
            assert line_regression["percentage_drop"] > 10.0


class TestCoverageReporter:
    """Test cases for CoverageReporter class."""

    def test_reporter_initialization(self):
        """Test CoverageReporter initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            reporter = CoverageReporter(output_dir)

            assert reporter.output_dir == output_dir
            assert output_dir.exists()

    def test_generate_ci_report(self):
        """Test CI report generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            reporter = CoverageReporter(Path(temp_dir))

            # Mock analyzer
            mock_analyzer = Mock()
            mock_analyzer.load_coverage_data.return_value = True
            mock_analyzer.calculate_quality_metrics.return_value = (
                CoverageQualityMetrics(
                    line_coverage_percent=85.0,
                    branch_coverage_percent=75.0,
                    function_coverage_percent=90.0,
                    effective_coverage_score=80.0,
                    test_quality_score=85.0,
                    coverage_density=0.8,
                    critical_gaps=2,
                    high_priority_gaps=5,
                    total_gaps=15,
                    coverage_trend="stable",
                    trend_percentage=0.0,
                    well_covered_files=20,
                    poorly_covered_files=3,
                    uncovered_files=1,
                )
            )

            quality_gates = {
                "line_coverage_percent": 80.0,
                "branch_coverage_percent": 70.0,
            }

            report = reporter.generate_ci_report(mock_analyzer, quality_gates)

            assert report["status"] == "pass"
            assert "quality_gates" in report
            assert "metrics" in report
            assert report["metrics"]["line_coverage"] == 85.0

    def test_generate_comprehensive_report(self):
        """Test comprehensive report generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            reporter = CoverageReporter(Path(temp_dir))

            # Mock analyzer
            mock_analyzer = Mock()
            mock_analyzer.load_coverage_data.return_value = True
            mock_analyzer.calculate_quality_metrics.return_value = (
                CoverageQualityMetrics(
                    line_coverage_percent=85.0,
                    branch_coverage_percent=75.0,
                    function_coverage_percent=90.0,
                    effective_coverage_score=80.0,
                    test_quality_score=85.0,
                    coverage_density=0.8,
                    critical_gaps=2,
                    high_priority_gaps=5,
                    total_gaps=15,
                    coverage_trend="stable",
                    trend_percentage=0.0,
                    well_covered_files=20,
                    poorly_covered_files=3,
                    uncovered_files=1,
                )
            )
            mock_analyzer.analyze_coverage_gaps.return_value = []
            mock_analyzer.get_coverage_summary.return_value = {"test": "data"}

            reports = reporter.generate_comprehensive_report(mock_analyzer)

            assert "html" in reports
            assert "json" in reports
            assert reports["html"].exists()
            assert reports["json"].exists()


class TestTestGenerator:
    """Test cases for TestGenerator class."""

    def test_generator_initialization(self):
        """Test TestGenerator initialization."""
        generator = TestGenerator(Path("src"), Path("tests"))

        assert generator.source_dir == Path("src")
        assert generator.test_dir == Path("tests")
        assert isinstance(generator.analyzer, CoverageAnalyzer)

    def test_test_suggestion_creation(self):
        """Test TestSuggestion creation and properties."""
        suggestion = TestSuggestion(
            file_path="test.py",
            function_name="test_function",
            class_name="TestClass",
            test_type="unit",
            priority="high",
            description="Test basic functionality",
            suggested_test_name="test_function_basic",
            test_template="def test_function_basic(): pass",
            coverage_lines=[10, 11, 12],
            complexity_score=3,
        )

        assert suggestion.file_path == "test.py"
        assert suggestion.function_name == "test_function"
        assert suggestion.class_name == "TestClass"
        assert suggestion.test_type == "unit"
        assert suggestion.priority == "high"
        assert suggestion.full_test_name == "test_testclass_test_function_basic"

    def test_generate_test_suggestions_no_data(self):
        """Test test suggestion generation with no coverage data."""
        generator = TestGenerator()

        # Mock analyzer to return no data
        generator.analyzer.load_coverage_data = Mock(return_value=False)

        suggestions = generator.generate_test_suggestions()

        assert suggestions == []

    def test_generate_missing_test_files(self):
        """Test identification of missing test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "src"
            test_dir = Path(temp_dir) / "tests"

            source_dir.mkdir()
            test_dir.mkdir()

            # Create a source file
            source_file = source_dir / "example.py"
            source_file.write_text("def example_function(): pass")

            generator = TestGenerator(source_dir, test_dir)
            missing_tests = generator.generate_missing_test_files()

            assert len(missing_tests) == 1
            assert missing_tests[0]["source_file"] == str(source_file)
            assert "test_example.py" in missing_tests[0]["expected_test_file"]


class TestQualityGate:
    """Test cases for QualityGate class."""

    def test_quality_gate_creation(self):
        """Test QualityGate creation."""
        gate = QualityGate(
            name="MinimumLineCoverage",
            metric="line_coverage_percent",
            threshold=80.0,
            operator="gte",
            enabled=True,
            severity="error",
        )

        assert gate.name == "MinimumLineCoverage"
        assert gate.metric == "line_coverage_percent"
        assert gate.threshold == 80.0
        assert gate.operator == "gte"
        assert gate.enabled is True
        assert gate.severity == "error"

    def test_quality_gate_evaluation_gte(self):
        """Test quality gate evaluation with gte operator."""
        gate = QualityGate("Test", "metric", 80.0, "gte")

        assert gate.evaluate(85.0) is True  # Above threshold
        assert gate.evaluate(80.0) is True  # Equal to threshold
        assert gate.evaluate(75.0) is False  # Below threshold

    def test_quality_gate_evaluation_lte(self):
        """Test quality gate evaluation with lte operator."""
        gate = QualityGate("Test", "metric", 5.0, "lte")

        assert gate.evaluate(3.0) is True  # Below threshold
        assert gate.evaluate(5.0) is True  # Equal to threshold
        assert gate.evaluate(7.0) is False  # Above threshold

    def test_quality_gate_evaluation_eq(self):
        """Test quality gate evaluation with eq operator."""
        gate = QualityGate("Test", "metric", 80.0, "eq")

        assert gate.evaluate(80.0) is True  # Equal
        assert gate.evaluate(80.005) is True  # Within tolerance
        assert gate.evaluate(85.0) is False  # Not equal

    def test_quality_gate_disabled(self):
        """Test disabled quality gate."""
        gate = QualityGate("Test", "metric", 80.0, "gte", enabled=False)

        assert gate.evaluate(0.0) is True  # Should pass when disabled


class TestCICoverageRunner:
    """Test cases for CICoverageRunner class."""

    def test_ci_runner_initialization(self):
        """Test CICoverageRunner initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            runner = CICoverageRunner(
                source_dir=Path("src"),
                coverage_file=".coverage",
                output_dir=Path(temp_dir),
            )

            assert runner.source_dir == Path("src")
            assert runner.coverage_file == ".coverage"
            assert runner.output_dir == Path(temp_dir)
            assert isinstance(runner.analyzer, CoverageAnalyzer)
            assert isinstance(runner.tracker, CoverageTracker)
            assert isinstance(runner.reporter, CoverageReporter)
            assert len(runner.quality_gates) > 0  # Should have default gates

    def test_run_quick_check_success(self):
        """Test quick coverage check success."""
        with tempfile.TemporaryDirectory() as temp_dir:
            runner = CICoverageRunner(output_dir=Path(temp_dir))

            # Mock analyzer
            mock_metrics = CoverageQualityMetrics(
                line_coverage_percent=85.0,
                branch_coverage_percent=75.0,
                function_coverage_percent=90.0,
                effective_coverage_score=80.0,
                test_quality_score=85.0,
                coverage_density=0.8,
                critical_gaps=2,
                high_priority_gaps=5,
                total_gaps=15,
                coverage_trend="stable",
                trend_percentage=0.0,
                well_covered_files=20,
                poorly_covered_files=3,
                uncovered_files=1,
            )

            runner.analyzer.load_coverage_data = Mock(return_value=True)
            runner.analyzer.calculate_quality_metrics = Mock(return_value=mock_metrics)

            passed, message = runner.run_quick_check(80.0)

            assert passed is True
            assert "85.0%" in message
            assert "passed" in message.lower()

    def test_run_quick_check_failure(self):
        """Test quick coverage check failure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            runner = CICoverageRunner(output_dir=Path(temp_dir))

            # Mock analyzer with low coverage
            mock_metrics = CoverageQualityMetrics(
                line_coverage_percent=75.0,  # Below threshold
                branch_coverage_percent=65.0,
                function_coverage_percent=80.0,
                effective_coverage_score=70.0,
                test_quality_score=75.0,
                coverage_density=0.7,
                critical_gaps=5,
                high_priority_gaps=8,
                total_gaps=20,
                coverage_trend="declining",
                trend_percentage=-5.0,
                well_covered_files=15,
                poorly_covered_files=8,
                uncovered_files=3,
            )

            runner.analyzer.load_coverage_data = Mock(return_value=True)
            runner.analyzer.calculate_quality_metrics = Mock(return_value=mock_metrics)

            passed, message = runner.run_quick_check(80.0)

            assert passed is False
            assert "75.0%" in message
            assert "failed" in message.lower()

    def test_quality_gate_result_creation(self):
        """Test QualityGateResult creation."""
        gate = QualityGate("Test", "metric", 80.0)
        result = QualityGateResult(
            gate=gate,
            current_value=85.0,
            passed=True,
            difference=5.0,
            message="Test passed",
        )

        assert result.gate == gate
        assert result.current_value == 85.0
        assert result.passed is True
        assert result.difference == 5.0
        assert result.message == "Test passed"
        assert result.status == "PASS"

    def test_generate_ci_summary(self):
        """Test CI summary generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            runner = CICoverageRunner(output_dir=Path(temp_dir))

            results = {
                "status": "success",
                "metrics": {
                    "line_coverage": 85.0,
                    "branch_coverage": 75.0,
                    "overall_score": 82.0,
                    "critical_gaps": 2,
                },
                "quality_gates": {"passed": 3, "total": 4},
            }

            summary = runner.generate_ci_summary(results)

            assert "✅" in summary
            assert "85.0%" in summary
            assert "3/4" in summary

    def test_export_junit_xml(self):
        """Test JUnit XML export."""
        with tempfile.TemporaryDirectory() as temp_dir:
            runner = CICoverageRunner(output_dir=Path(temp_dir))

            results = {
                "quality_gates": {
                    "results": [
                        {
                            "name": "MinimumLineCoverage",
                            "status": "PASS",
                            "message": "Coverage check passed",
                        },
                        {
                            "name": "MaximumCriticalGaps",
                            "status": "FAIL",
                            "message": "Too many critical gaps",
                        },
                    ]
                }
            }

            xml_file = Path(temp_dir) / "junit.xml"
            runner.export_junit_xml(results, xml_file)

            assert xml_file.exists()

            xml_content = xml_file.read_text()
            assert "testsuite" in xml_content
            assert "MinimumLineCoverage" in xml_content
            assert "MaximumCriticalGaps" in xml_content
            assert "failure" in xml_content  # Should have failure element


class TestCoverageIntegration:
    """Integration tests for coverage analysis system."""

    def test_end_to_end_coverage_analysis(self):
        """Test complete coverage analysis workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            # Create mock coverage data
            analyzer = CoverageAnalyzer()
            analyzer.coverage_data = Mock()
            analyzer.coverage_obj = Mock()

            # Mock methods to return test data
            analyzer.load_coverage_data = Mock(return_value=True)
            analyzer.calculate_quality_metrics = Mock(
                return_value=CoverageQualityMetrics(
                    line_coverage_percent=85.0,
                    branch_coverage_percent=75.0,
                    function_coverage_percent=90.0,
                    effective_coverage_score=80.0,
                    test_quality_score=85.0,
                    coverage_density=0.8,
                    critical_gaps=2,
                    high_priority_gaps=5,
                    total_gaps=15,
                    coverage_trend="stable",
                    trend_percentage=0.0,
                    well_covered_files=20,
                    poorly_covered_files=3,
                    uncovered_files=1,
                )
            )
            analyzer.analyze_coverage_gaps = Mock(return_value=[])
            analyzer.get_coverage_summary = Mock(return_value={"test": "data"})

            # Initialize other components
            tracker = CoverageTracker(output_dir / "history")
            reporter = CoverageReporter(output_dir)

            # Run analysis
            reports = reporter.generate_comprehensive_report(analyzer, tracker)

            # Verify results
            assert "html" in reports
            assert "json" in reports
            assert reports["html"].exists()
            assert reports["json"].exists()

            # Verify JSON content
            with open(reports["json"]) as f:
                json_data = json.load(f)

            assert "timestamp" in json_data
            assert "metrics" in json_data
            assert json_data["metrics"]["line_coverage"] == 85.0

    def test_ci_integration_workflow(self):
        """Test CI integration workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            runner = CICoverageRunner(output_dir=Path(temp_dir))

            # Mock analyzer
            mock_metrics = CoverageQualityMetrics(
                line_coverage_percent=85.0,
                branch_coverage_percent=75.0,
                function_coverage_percent=90.0,
                effective_coverage_score=80.0,
                test_quality_score=85.0,
                coverage_density=0.8,
                critical_gaps=2,
                high_priority_gaps=5,
                total_gaps=15,
                coverage_trend="stable",
                trend_percentage=0.0,
                well_covered_files=20,
                poorly_covered_files=3,
                uncovered_files=1,
            )

            runner.analyzer.load_coverage_data = Mock(return_value=True)
            runner.analyzer.calculate_quality_metrics = Mock(return_value=mock_metrics)
            runner.analyzer.analyze_coverage_gaps = Mock(return_value=[])
            runner._get_test_count = Mock(return_value=150)

            # Mock reporter
            runner.reporter.generate_comprehensive_report = Mock(
                return_value={"html": Path("test.html")}
            )

            # Run CI analysis
            results = runner.run_coverage_analysis(
                generate_reports=True,
                track_trends=True,
                commit_hash="test123",
                branch_name="main",
            )

            # Verify results
            assert results["status"] in [
                "success",
                "warning",
            ]  # May have warnings due to quality gates
            assert results["exit_code"] == 0
            assert results["commit_hash"] == "test123"
            assert results["branch_name"] == "main"
            assert "metrics" in results
            assert "quality_gates" in results
            assert results["metrics"]["line_coverage"] == 85.0

            # Verify quality gates
            gate_results = results["quality_gates"]
            assert gate_results["total"] > 0
            assert gate_results["passed"] >= 0
            assert gate_results["failed"] >= 0
