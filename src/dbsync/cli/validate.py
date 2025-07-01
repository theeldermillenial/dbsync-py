"""Schema validation command implementation.

Provides CLI interface for validating database schema against official Cardano DB Sync schema.
"""

import json

# Import the existing schema validation functionality
import sys
from pathlib import Path

import click

# Add tests directory to path to import schema validation
tests_path = Path(__file__).parent.parent.parent.parent / "tests"
sys.path.insert(0, str(tests_path))

from schema_validation.schema_validator import (
    SchemaValidator,
    ValidationResult,
)


def run_validation(
    format: str = "text",
    coverage_only: bool = False,
    errors_only: bool = False,
    output_file: str | None = None,
    verbose: bool = False,
) -> None:
    """Run schema validation with the specified options.

    Args:
        format: Output format ("text" or "json")
        coverage_only: Show only coverage statistics
        errors_only: Show only validation errors
        output_file: Output file path (None for stdout)
        verbose: Enable verbose output
    """
    if verbose:
        click.echo("Initializing schema validator...")

    # Initialize the validator
    validator = SchemaValidator()

    if verbose:
        click.echo("Fetching official schema...")

    # Fetch the official schema
    try:
        validator.fetch_official_schema()
    except Exception as e:
        raise click.ClickException(f"Failed to fetch official schema: {e}")

    if verbose:
        click.echo("Validating models...")

    # Run validation
    try:
        results = validator.validate_all_models()
    except Exception as e:
        raise click.ClickException(f"Validation failed: {e}")

    # Generate output
    if format == "json":
        output = _generate_json_output(results, coverage_only, errors_only)
    else:
        output = _generate_text_output(results, coverage_only, errors_only, verbose)

    # Write output
    if output_file:
        try:
            with open(output_file, "w") as f:
                f.write(output)
            if verbose:
                click.echo(f"Results written to {output_file}")
        except Exception as e:
            raise click.ClickException(f"Failed to write output file: {e}")
    else:
        click.echo(output)


def _generate_text_output(
    results: dict[str, ValidationResult],
    coverage_only: bool,
    errors_only: bool,
    verbose: bool,
) -> str:
    """Generate text format output."""
    lines = []

    if not coverage_only:
        lines.append("=" * 80)
        lines.append("CARDANO DB SYNC SCHEMA VALIDATION REPORT")
        lines.append("=" * 80)
        lines.append("")

    # Calculate statistics
    total_tables = len(results)
    valid_tables = sum(1 for r in results.values() if r.is_valid)
    invalid_tables = total_tables - valid_tables

    if coverage_only or not errors_only:
        lines.append("COVERAGE STATISTICS")
        lines.append("-" * 50)
        lines.append(f"Total Tables: {total_tables}")
        lines.append(f"Valid Tables: {valid_tables}")
        lines.append(f"Invalid Tables: {invalid_tables}")
        lines.append(f"Coverage: {(valid_tables / total_tables) * 100:.1f}%")
        lines.append("")

    if coverage_only:
        return "\n".join(lines)

    if not errors_only:
        # Show valid tables
        valid_results = {k: v for k, v in results.items() if v.is_valid}
        if valid_results:
            lines.append("VALID TABLES")
            lines.append("-" * 50)
            for table_name in sorted(valid_results.keys()):
                lines.append(f"✅ {table_name}")
            lines.append("")

    # Show invalid tables
    invalid_results = {k: v for k, v in results.items() if not v.is_valid}
    if invalid_results:
        lines.append("VALIDATION ERRORS" if errors_only else "INVALID TABLES")
        lines.append("-" * 50)

        for table_name in sorted(invalid_results.keys()):
            result = invalid_results[table_name]
            lines.append(f"❌ {table_name}")

            if result.missing_fields:
                lines.append(f"   Missing fields: {', '.join(result.missing_fields)}")
            if result.extra_fields:
                lines.append(f"   Extra fields: {', '.join(result.extra_fields)}")
            if result.type_mismatches:
                lines.append("   Type mismatches:")
                for field, (expected, actual) in result.type_mismatches.items():
                    lines.append(f"     {field}: expected {expected}, got {actual}")
            if result.errors:
                lines.append(f"   Errors: {', '.join(result.errors)}")
            lines.append("")

    if not invalid_results and errors_only:
        lines.append("🎉 No validation errors found!")
        lines.append("")

    return "\n".join(lines)


def _generate_json_output(
    results: dict[str, ValidationResult],
    coverage_only: bool,
    errors_only: bool,
) -> str:
    """Generate JSON format output."""
    # Calculate statistics
    total_tables = len(results)
    valid_tables = sum(1 for r in results.values() if r.is_valid)
    invalid_tables = total_tables - valid_tables

    output = {
        "summary": {
            "total_tables": total_tables,
            "valid_tables": valid_tables,
            "invalid_tables": invalid_tables,
            "coverage_percentage": (valid_tables / total_tables) * 100
            if total_tables > 0
            else 0,
        }
    }

    if coverage_only:
        return json.dumps(output, indent=2)

    # Add detailed results
    if errors_only:
        # Only include invalid tables
        output["validation_errors"] = {
            table_name: {
                "missing_fields": result.missing_fields,
                "extra_fields": result.extra_fields,
                "type_mismatches": result.type_mismatches,
                "errors": result.errors,
            }
            for table_name, result in results.items()
            if not result.is_valid
        }
    else:
        # Include all results
        output["results"] = {
            table_name: {
                "is_valid": result.is_valid,
                "missing_fields": result.missing_fields,
                "extra_fields": result.extra_fields,
                "type_mismatches": result.type_mismatches,
                "errors": result.errors,
            }
            for table_name, result in results.items()
        }

    return json.dumps(output, indent=2)
