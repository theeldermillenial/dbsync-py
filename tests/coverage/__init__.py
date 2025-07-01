"""Test Coverage Analysis Package.

This package provides comprehensive test coverage analysis capabilities including:
- Advanced coverage analysis beyond basic line/branch coverage
- Coverage trend tracking and regression detection
- Quality gate enforcement and CI/CD integration
- Test generation suggestions for uncovered code paths
- Professional reporting with visualizations
"""

from .analyzer import CoverageAnalyzer, CoverageGap, CoverageQualityMetrics
from .ci import CICoverageRunner, QualityGate, QualityGateResult
from .generator import TestGenerator, TestSuggestion
from .reporter import CoverageReporter
from .tracker import CoverageTracker, CoverageTrend

__all__ = [
    "CICoverageRunner",
    "CoverageAnalyzer",
    "CoverageGap",
    "CoverageQualityMetrics",
    "CoverageReporter",
    "CoverageTracker",
    "CoverageTrend",
    "QualityGate",
    "QualityGateResult",
    "TestGenerator",
    "TestSuggestion",
]
