"""Test Generation Suggestions.

This module analyzes uncovered code paths and generates suggestions
for test cases to improve coverage.
"""

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .analyzer import CoverageAnalyzer, CoverageGap


@dataclass
class TestSuggestion:
    """Represents a suggested test case."""

    file_path: str
    function_name: str | None
    class_name: str | None
    test_type: str  # 'unit', 'integration', 'edge_case', 'error_handling'
    priority: str  # 'high', 'medium', 'low'
    description: str
    suggested_test_name: str
    test_template: str
    coverage_lines: list[int]
    complexity_score: int = 1

    @property
    def full_test_name(self) -> str:
        """Generate full test name with class prefix if applicable."""
        if self.class_name:
            return f"test_{self.class_name.lower()}_{self.suggested_test_name}"
        return f"test_{self.suggested_test_name}"


class TestGenerator:
    """Generates test suggestions based on coverage analysis."""

    def __init__(self, source_dir: Path = Path("src"), test_dir: Path = Path("tests")):
        """Initialize test generator.

        Args:
            source_dir: Directory containing source code
            test_dir: Directory containing test files
        """
        self.source_dir = Path(source_dir)
        self.test_dir = Path(test_dir)
        self.analyzer = CoverageAnalyzer(source_dir)

    def generate_test_suggestions(
        self, max_suggestions: int = 50
    ) -> list[TestSuggestion]:
        """Generate test suggestions based on coverage gaps.

        Args:
            max_suggestions: Maximum number of suggestions to generate

        Returns:
            List of test suggestions
        """
        if not self.analyzer.load_coverage_data():
            return []

        gaps = self.analyzer.analyze_coverage_gaps()
        suggestions = []

        # Group gaps by file for better analysis
        gaps_by_file = {}
        for gap in gaps:
            if gap.file_path not in gaps_by_file:
                gaps_by_file[gap.file_path] = []
            gaps_by_file[gap.file_path].append(gap)

        # Generate suggestions for each file
        for file_path, file_gaps in gaps_by_file.items():
            file_suggestions = self._generate_file_suggestions(file_path, file_gaps)
            suggestions.extend(file_suggestions)

        # Sort by priority and complexity
        suggestions.sort(
            key=lambda s: (
                {"high": 3, "medium": 2, "low": 1}[s.priority],
                s.complexity_score,
            ),
            reverse=True,
        )

        return suggestions[:max_suggestions]

    def generate_missing_test_files(self) -> list[dict[str, Any]]:
        """Identify source files that don't have corresponding test files.

        Returns:
            List of missing test file information
        """
        missing_tests = []

        # Find all Python source files
        for source_file in self.source_dir.rglob("*.py"):
            if source_file.name.startswith("__"):
                continue

            # Determine expected test file path
            relative_path = source_file.relative_to(self.source_dir)
            test_file_name = f"test_{source_file.stem}.py"
            expected_test_path = (
                self.test_dir / "unit" / relative_path.parent / test_file_name
            )

            if not expected_test_path.exists():
                # Analyze source file to suggest test structure
                test_structure = self._analyze_source_for_tests(source_file)

                missing_tests.append(
                    {
                        "source_file": str(source_file),
                        "expected_test_file": str(expected_test_path),
                        "test_structure": test_structure,
                        "priority": self._determine_test_file_priority(
                            source_file, test_structure
                        ),
                    }
                )

        return missing_tests

    def generate_test_template(self, suggestion: TestSuggestion) -> str:
        """Generate a complete test template for a suggestion.

        Args:
            suggestion: Test suggestion to generate template for

        Returns:
            Complete test template as string
        """
        # Determine imports needed
        imports = self._generate_imports(suggestion)

        # Generate test class if needed
        if suggestion.class_name:
            class_template = self._generate_class_test_template(suggestion)
        else:
            class_template = self._generate_function_test_template(suggestion)

        template = f"""\"\"\"Test cases for {suggestion.file_path}.

Generated test suggestions based on coverage analysis.
\"\"\"

{imports}


{class_template}
"""

        return template

    def _generate_file_suggestions(
        self, file_path: str, gaps: list[CoverageGap]
    ) -> list[TestSuggestion]:
        """Generate test suggestions for a specific file.

        Args:
            file_path: Path to source file
            gaps: Coverage gaps in the file

        Returns:
            List of test suggestions for the file
        """
        suggestions = []

        try:
            # Parse source file to understand structure
            with open(file_path, encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)

            # Group gaps by function/class
            gaps_by_scope = self._group_gaps_by_scope(gaps)

            # Generate suggestions for each scope
            for scope, scope_gaps in gaps_by_scope.items():
                scope_suggestions = self._generate_scope_suggestions(
                    file_path, scope, scope_gaps, tree, source
                )
                suggestions.extend(scope_suggestions)

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")

        return suggestions

    def _group_gaps_by_scope(
        self, gaps: list[CoverageGap]
    ) -> dict[tuple[str | None, str | None], list[CoverageGap]]:
        """Group coverage gaps by function/class scope.

        Args:
            gaps: List of coverage gaps

        Returns:
            Dictionary mapping (class_name, function_name) to gaps
        """
        gaps_by_scope = {}

        for gap in gaps:
            scope_key = (gap.class_name, gap.function_name)
            if scope_key not in gaps_by_scope:
                gaps_by_scope[scope_key] = []
            gaps_by_scope[scope_key].append(gap)

        return gaps_by_scope

    def _generate_scope_suggestions(
        self,
        file_path: str,
        scope: tuple[str | None, str | None],
        gaps: list[CoverageGap],
        tree: ast.AST,
        source: str,
    ) -> list[TestSuggestion]:
        """Generate test suggestions for a specific scope.

        Args:
            file_path: Path to source file
            scope: (class_name, function_name) tuple
            gaps: Coverage gaps in this scope
            tree: AST of source file
            source: Source code

        Returns:
            List of test suggestions
        """
        class_name, function_name = scope
        suggestions = []

        # Analyze function/method signature if available
        function_info = self._analyze_function_signature(
            tree, function_name, class_name
        )

        # Generate suggestions based on gap types
        gap_types = set(gap.gap_type for gap in gaps)

        for gap_type in gap_types:
            type_gaps = [g for g in gaps if g.gap_type == gap_type]
            suggestion = self._create_suggestion_for_gap_type(
                file_path, gap_type, type_gaps, function_info, class_name, function_name
            )
            if suggestion:
                suggestions.append(suggestion)

        # Generate edge case suggestions
        if function_info and function_info.get("parameters"):
            edge_case_suggestion = self._create_edge_case_suggestion(
                file_path, function_info, class_name, function_name
            )
            if edge_case_suggestion:
                suggestions.append(edge_case_suggestion)

        return suggestions

    def _analyze_function_signature(
        self, tree: ast.AST, function_name: str | None, class_name: str | None
    ) -> dict[str, Any]:
        """Analyze function signature to understand parameters and return type.

        Args:
            tree: AST of source file
            function_name: Name of function to analyze
            class_name: Name of containing class

        Returns:
            Dictionary with function information
        """
        if not function_name:
            return {}

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                # Check if it's in the right class
                if class_name:
                    parent_class = self._find_parent_class(tree, node)
                    if not parent_class or parent_class.name != class_name:
                        continue

                # Extract parameter information
                parameters = []
                for arg in node.args.args:
                    param_info = {
                        "name": arg.arg,
                        "annotation": ast.unparse(arg.annotation)
                        if arg.annotation
                        else None,
                        "has_default": False,
                    }
                    parameters.append(param_info)

                # Mark parameters with defaults
                default_count = len(node.args.defaults)
                if default_count > 0:
                    for i in range(default_count):
                        parameters[-(i + 1)]["has_default"] = True

                return {
                    "name": function_name,
                    "parameters": parameters,
                    "return_annotation": ast.unparse(node.returns)
                    if node.returns
                    else None,
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "decorators": [ast.unparse(d) for d in node.decorator_list],
                    "docstring": ast.get_docstring(node),
                }

        return {}

    def _find_parent_class(
        self, tree: ast.AST, function_node: ast.FunctionDef
    ) -> ast.ClassDef | None:
        """Find the parent class of a function node."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for child in ast.walk(node):
                    if child is function_node:
                        return node
        return None

    def _create_suggestion_for_gap_type(
        self,
        file_path: str,
        gap_type: str,
        gaps: list[CoverageGap],
        function_info: dict[str, Any],
        class_name: str | None,
        function_name: str | None,
    ) -> TestSuggestion | None:
        """Create test suggestion for a specific gap type.

        Args:
            file_path: Path to source file
            gap_type: Type of coverage gap
            gaps: List of gaps of this type
            function_info: Function signature information
            class_name: Name of containing class
            function_name: Name of function

        Returns:
            Test suggestion or None
        """
        if gap_type == "missing_branch":
            return self._create_branch_test_suggestion(
                file_path, gaps, function_info, class_name, function_name
            )
        elif gap_type == "exception_handling":
            return self._create_exception_test_suggestion(
                file_path, gaps, function_info, class_name, function_name
            )
        elif gap_type == "uncovered_function":
            return self._create_function_test_suggestion(
                file_path, gaps, function_info, class_name, function_name
            )
        elif gap_type == "error_path":
            return self._create_error_path_suggestion(
                file_path, gaps, function_info, class_name, function_name
            )
        else:
            return self._create_generic_test_suggestion(
                file_path, gaps, function_info, class_name, function_name
            )

    def _create_branch_test_suggestion(
        self,
        file_path: str,
        gaps: list[CoverageGap],
        function_info: dict[str, Any],
        class_name: str | None,
        function_name: str | None,
    ) -> TestSuggestion:
        """Create suggestion for branch coverage gaps."""
        priority = (
            "high"
            if any(g.severity in ["critical", "high"] for g in gaps)
            else "medium"
        )

        test_name = (
            f"{function_name}_branch_coverage" if function_name else "branch_coverage"
        )

        description = f"Test branch conditions in {function_name or 'code'}"
        if len(gaps) > 1:
            description += f" ({len(gaps)} uncovered branches)"

        template = self._generate_branch_test_template(
            function_info, class_name, function_name
        )

        return TestSuggestion(
            file_path=file_path,
            function_name=function_name,
            class_name=class_name,
            test_type="unit",
            priority=priority,
            description=description,
            suggested_test_name=test_name,
            test_template=template,
            coverage_lines=[g.line_start for g in gaps],
            complexity_score=sum(g.complexity_score or 1 for g in gaps),
        )

    def _create_exception_test_suggestion(
        self,
        file_path: str,
        gaps: list[CoverageGap],
        function_info: dict[str, Any],
        class_name: str | None,
        function_name: str | None,
    ) -> TestSuggestion:
        """Create suggestion for exception handling gaps."""
        test_name = (
            f"{function_name}_exception_handling"
            if function_name
            else "exception_handling"
        )

        description = f"Test exception handling in {function_name or 'code'}"

        template = self._generate_exception_test_template(
            function_info, class_name, function_name
        )

        return TestSuggestion(
            file_path=file_path,
            function_name=function_name,
            class_name=class_name,
            test_type="error_handling",
            priority="high",  # Exception handling is always high priority
            description=description,
            suggested_test_name=test_name,
            test_template=template,
            coverage_lines=[g.line_start for g in gaps],
            complexity_score=sum(g.complexity_score or 1 for g in gaps),
        )

    def _create_function_test_suggestion(
        self,
        file_path: str,
        gaps: list[CoverageGap],
        function_info: dict[str, Any],
        class_name: str | None,
        function_name: str | None,
    ) -> TestSuggestion:
        """Create suggestion for uncovered function."""
        test_name = (
            f"{function_name}_basic_functionality"
            if function_name
            else "basic_functionality"
        )

        description = f"Test basic functionality of {function_name or 'function'}"

        template = self._generate_function_test_template(
            function_info, class_name, function_name
        )

        return TestSuggestion(
            file_path=file_path,
            function_name=function_name,
            class_name=class_name,
            test_type="unit",
            priority="medium",
            description=description,
            suggested_test_name=test_name,
            test_template=template,
            coverage_lines=[g.line_start for g in gaps],
            complexity_score=sum(g.complexity_score or 1 for g in gaps),
        )

    def _create_error_path_suggestion(
        self,
        file_path: str,
        gaps: list[CoverageGap],
        function_info: dict[str, Any],
        class_name: str | None,
        function_name: str | None,
    ) -> TestSuggestion:
        """Create suggestion for error path coverage."""
        test_name = (
            f"{function_name}_error_conditions" if function_name else "error_conditions"
        )

        description = (
            f"Test error conditions and edge cases in {function_name or 'code'}"
        )

        template = self._generate_error_path_template(
            function_info, class_name, function_name
        )

        return TestSuggestion(
            file_path=file_path,
            function_name=function_name,
            class_name=class_name,
            test_type="edge_case",
            priority="high",
            description=description,
            suggested_test_name=test_name,
            test_template=template,
            coverage_lines=[g.line_start for g in gaps],
            complexity_score=sum(g.complexity_score or 1 for g in gaps),
        )

    def _create_generic_test_suggestion(
        self,
        file_path: str,
        gaps: list[CoverageGap],
        function_info: dict[str, Any],
        class_name: str | None,
        function_name: str | None,
    ) -> TestSuggestion:
        """Create generic test suggestion."""
        test_name = f"{function_name}_coverage" if function_name else "coverage"

        description = f"Improve test coverage for {function_name or 'code'}"

        template = self._generate_generic_test_template(
            function_info, class_name, function_name
        )

        return TestSuggestion(
            file_path=file_path,
            function_name=function_name,
            class_name=class_name,
            test_type="unit",
            priority="low",
            description=description,
            suggested_test_name=test_name,
            test_template=template,
            coverage_lines=[g.line_start for g in gaps],
            complexity_score=sum(g.complexity_score or 1 for g in gaps),
        )

    def _create_edge_case_suggestion(
        self,
        file_path: str,
        function_info: dict[str, Any],
        class_name: str | None,
        function_name: str | None,
    ) -> TestSuggestion | None:
        """Create suggestion for edge case testing."""
        if not function_info.get("parameters"):
            return None

        test_name = f"{function_name}_edge_cases" if function_name else "edge_cases"

        description = f"Test edge cases for {function_name or 'function'} parameters"

        template = self._generate_edge_case_template(
            function_info, class_name, function_name
        )

        return TestSuggestion(
            file_path=file_path,
            function_name=function_name,
            class_name=class_name,
            test_type="edge_case",
            priority="medium",
            description=description,
            suggested_test_name=test_name,
            test_template=template,
            coverage_lines=[],
            complexity_score=len(function_info["parameters"]),
        )

    def _generate_imports(self, suggestion: TestSuggestion) -> str:
        """Generate import statements for test template."""
        imports = ["import pytest"]

        # Add imports based on test type
        if suggestion.test_type == "integration":
            imports.append("from tests.integration.base import BaseIntegrationTest")

        if suggestion.test_type == "error_handling":
            imports.append("from unittest.mock import Mock, patch")

        # Add source imports
        file_path = Path(suggestion.file_path)
        if file_path.is_relative_to(self.source_dir):
            relative_path = file_path.relative_to(self.source_dir)
            module_path = str(relative_path.with_suffix("")).replace("/", ".")

            if suggestion.class_name:
                imports.append(f"from {module_path} import {suggestion.class_name}")
            elif suggestion.function_name:
                imports.append(f"from {module_path} import {suggestion.function_name}")
            else:
                imports.append(f"import {module_path}")

        return "\n".join(imports)

    def _generate_branch_test_template(
        self,
        function_info: dict[str, Any],
        class_name: str | None,
        function_name: str | None,
    ) -> str:
        """Generate test template for branch coverage."""
        if not function_name:
            return "# TODO: Add branch coverage tests"

        params = function_info.get("parameters", [])
        param_names = [p["name"] for p in params if p["name"] != "self"]

        test_cases = []

        # Generate test cases for different conditions
        test_cases.append(
            f"""
    def test_{function_name}_true_condition(self):
        \"\"\"Test {function_name} when condition is true.\"\"\"
        # TODO: Set up test data for true condition
        # TODO: Call function and assert expected behavior
        pass"""
        )

        test_cases.append(
            f"""
    def test_{function_name}_false_condition(self):
        \"\"\"Test {function_name} when condition is false.\"\"\"
        # TODO: Set up test data for false condition
        # TODO: Call function and assert expected behavior
        pass"""
        )

        return "\n".join(test_cases)

    def _generate_exception_test_template(
        self,
        function_info: dict[str, Any],
        class_name: str | None,
        function_name: str | None,
    ) -> str:
        """Generate test template for exception handling."""
        if not function_name:
            return "# TODO: Add exception handling tests"

        return f"""
    def test_{function_name}_handles_exceptions(self):
        \"\"\"Test {function_name} exception handling.\"\"\"
        # TODO: Set up conditions that trigger exceptions
        with pytest.raises(Exception):  # TODO: Specify expected exception type
            # TODO: Call function with invalid parameters
            pass

    def test_{function_name}_recovers_from_errors(self):
        \"\"\"Test {function_name} error recovery.\"\"\"
        # TODO: Test graceful error handling and recovery
        pass"""

    def _generate_function_test_template(
        self,
        function_info: dict[str, Any],
        class_name: str | None,
        function_name: str | None,
    ) -> str:
        """Generate basic function test template."""
        if not function_name:
            return "# TODO: Add function tests"

        return f"""
    def test_{function_name}_basic_functionality(self):
        \"\"\"Test basic functionality of {function_name}.\"\"\"
        # TODO: Set up test data
        # TODO: Call function
        # TODO: Assert expected results
        pass"""

    def _generate_error_path_template(
        self,
        function_info: dict[str, Any],
        class_name: str | None,
        function_name: str | None,
    ) -> str:
        """Generate error path test template."""
        if not function_name:
            return "# TODO: Add error path tests"

        return f"""
    def test_{function_name}_error_conditions(self):
        \"\"\"Test error conditions in {function_name}.\"\"\"
        # TODO: Test invalid input handling
        # TODO: Test boundary conditions
        # TODO: Test resource exhaustion scenarios
        pass"""

    def _generate_generic_test_template(
        self,
        function_info: dict[str, Any],
        class_name: str | None,
        function_name: str | None,
    ) -> str:
        """Generate generic test template."""
        if not function_name:
            return "# TODO: Add coverage tests"

        return f"""
    def test_{function_name}_coverage(self):
        \"\"\"Improve test coverage for {function_name}.\"\"\"
        # TODO: Add tests to cover uncovered lines
        pass"""

    def _generate_edge_case_template(
        self,
        function_info: dict[str, Any],
        class_name: str | None,
        function_name: str | None,
    ) -> str:
        """Generate edge case test template."""
        if not function_name:
            return "# TODO: Add edge case tests"

        params = function_info.get("parameters", [])
        edge_tests = []

        for param in params:
            if param["name"] == "self":
                continue

            edge_tests.append(
                f"""
    def test_{function_name}_{param["name"]}_edge_cases(self):
        \"\"\"Test edge cases for {param["name"]} parameter.\"\"\"
        # TODO: Test None values
        # TODO: Test empty values
        # TODO: Test boundary values
        # TODO: Test invalid types
        pass"""
            )

        return (
            "\n".join(edge_tests)
            if edge_tests
            else f"""
    def test_{function_name}_edge_cases(self):
        \"\"\"Test edge cases for {function_name}.\"\"\"
        # TODO: Add edge case tests
        pass"""
        )

    def _generate_class_test_template(self, suggestion: TestSuggestion) -> str:
        """Generate test class template."""
        class_name = suggestion.class_name

        return f"""
class Test{class_name}:
    \"\"\"Test cases for {class_name} class.\"\"\"

    def setup_method(self):
        \"\"\"Set up test fixtures.\"\"\"
        # TODO: Initialize test objects
        pass

{suggestion.test_template}"""

    def _generate_function_test_template(self, suggestion: TestSuggestion) -> str:
        """Generate function test template."""
        return suggestion.test_template

    def _analyze_source_for_tests(self, source_file: Path) -> dict[str, Any]:
        """Analyze source file to suggest test structure."""
        try:
            with open(source_file, encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)

            classes = []
            functions = []

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(
                        {
                            "name": node.name,
                            "methods": [
                                n.name
                                for n in node.body
                                if isinstance(n, ast.FunctionDef)
                            ],
                            "line": node.lineno,
                        }
                    )
                elif isinstance(node, ast.FunctionDef) and not any(
                    isinstance(parent, ast.ClassDef)
                    for parent in ast.walk(tree)
                    if any(child is node for child in ast.walk(parent))
                ):
                    functions.append(
                        {
                            "name": node.name,
                            "line": node.lineno,
                            "is_async": isinstance(node, ast.AsyncFunctionDef),
                        }
                    )

            return {
                "classes": classes,
                "functions": functions,
                "total_lines": len(source.split("\n")),
                "complexity": len(classes) + len(functions),
            }

        except Exception:
            return {"classes": [], "functions": [], "total_lines": 0, "complexity": 0}

    def _determine_test_file_priority(
        self, source_file: Path, test_structure: dict[str, Any]
    ) -> str:
        """Determine priority for creating test file."""
        complexity = test_structure.get("complexity", 0)

        # High priority for complex files or files with many classes/functions
        if complexity > 10:
            return "high"
        elif complexity > 5:
            return "medium"
        else:
            return "low"
