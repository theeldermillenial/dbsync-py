#!/usr/bin/env python3
"""CLI script for running schema validation against official Cardano DB Sync schema."""

import argparse
import json
import sys
from pathlib import Path

from schema_validator import (
    SchemaValidator,
)


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Validate dbsync-py models against official Cardano DB Sync schema"
    )

    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    parser.add_argument(
        "--output", "-o", type=Path, help="Output file (default: stdout)"
    )

    parser.add_argument(
        "--coverage-only", action="store_true", help="Show only coverage statistics"
    )

    parser.add_argument(
        "--errors-only", action="store_true", help="Show only validation errors"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output with detailed field information",
    )

    args = parser.parse_args()

    try:
        # Run validation
        print(
            "🔍 Validating dbsync-py models against official schema...", file=sys.stderr
        )
        validator = SchemaValidator()
        results = validator.validate_all_models()

        # Generate output based on format
        if args.format == "json":
            output_data = generate_json_output(validator, results, args)
        else:
            output_data = generate_text_output(validator, results, args)

        # Write output
        if args.output:
            with open(args.output, "w") as f:
                f.write(output_data)
            print(f"✅ Results written to {args.output}", file=sys.stderr)
        else:
            print(output_data)

        # Exit with error code if validation failed
        valid_tables = sum(1 for r in results.values() if r.is_valid)
        total_tables = len(results)

        if valid_tables < total_tables:
            print(
                f"❌ Validation failed: {total_tables - valid_tables} tables have issues",
                file=sys.stderr,
            )
            sys.exit(1)
        else:
            print("✅ All tables passed validation!", file=sys.stderr)
            sys.exit(0)

    except Exception as e:
        print(f"❌ Error during validation: {e}", file=sys.stderr)
        sys.exit(1)


def generate_json_output(validator: SchemaValidator, results: dict, args) -> str:
    """Generate JSON output."""
    coverage = validator.get_implementation_coverage(results)

    output = {"summary": coverage, "validation_results": {}}

    for table_name, result in results.items():
        result_data = {
            "table_name": result.table_name,
            "model_class": result.model_class.__name__ if result.model_class else None,
            "is_valid": result.is_valid,
            "errors": result.errors,
            "warnings": result.warnings,
            "missing_fields": result.missing_fields,
            "extra_fields": result.extra_fields,
            "type_mismatches": result.type_mismatches,
        }

        # Filter based on args
        if args.errors_only and result.is_valid:
            continue

        output["validation_results"][table_name] = result_data

    return json.dumps(output, indent=2)


def generate_text_output(validator: SchemaValidator, results: dict, args) -> str:
    """Generate text output."""
    if args.coverage_only:
        return generate_coverage_report(validator, results)
    elif args.errors_only:
        return generate_errors_report(validator, results, args.verbose)
    else:
        return validator.generate_validation_report(results)


def generate_coverage_report(validator: SchemaValidator, results: dict) -> str:
    """Generate coverage-only report."""
    coverage = validator.get_implementation_coverage(results)

    report = [
        "Schema Implementation Coverage Report",
        "=" * 50,
        "",
        f"📊 Total Tables in Official Schema: {coverage['total_tables_in_schema']}",
        f"✅ Implemented Tables: {coverage['implemented_tables']}",
        f"🎯 Valid Implementations: {coverage['valid_implementations']}",
        f"📈 Implementation Coverage: {coverage['implementation_coverage']:.1f}%",
        f"✨ Validation Success Rate: {coverage['validation_success_rate']:.1f}%",
        "",
    ]

    if coverage["missing_tables"]:
        report.extend(
            [
                f"❌ Missing Tables ({len(coverage['missing_tables'])}):",
                *[f"   - {table}" for table in sorted(coverage["missing_tables"])],
                "",
            ]
        )

    if coverage["invalid_tables"]:
        report.extend(
            [
                f"⚠️  Invalid Tables ({len(coverage['invalid_tables'])}):",
                *[f"   - {table}" for table in sorted(coverage["invalid_tables"])],
                "",
            ]
        )

    return "\n".join(report)


def generate_errors_report(
    validator: SchemaValidator, results: dict, verbose: bool
) -> str:
    """Generate errors-only report."""
    invalid_results = {k: v for k, v in results.items() if not v.is_valid}

    if not invalid_results:
        return "✅ No validation errors found!"

    report = [
        "Schema Validation Errors Report",
        "=" * 50,
        f"Found {len(invalid_results)} tables with validation issues:",
        "",
    ]

    for table_name, result in sorted(invalid_results.items()):
        report.append(f"❌ {table_name}")

        if result.model_class is None:
            report.append("   Status: Not implemented")
        else:
            report.append(f"   Model: {result.model_class.__name__}")

        if result.errors:
            report.extend([f"   Error: {error}" for error in result.errors])

        if verbose:
            if result.missing_fields:
                report.append(f"   Missing Fields: {', '.join(result.missing_fields)}")

            if result.extra_fields:
                report.append(f"   Extra Fields: {', '.join(result.extra_fields)}")

            if result.type_mismatches:
                report.extend(
                    [
                        f"   Type Issue: {mismatch}"
                        for mismatch in result.type_mismatches
                    ]
                )

        report.append("")

    return "\n".join(report)


if __name__ == "__main__":
    main()
