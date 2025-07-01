"""Schema validation utilities for comparing dbsync-py models against official schema."""

import inspect
import re
from dataclasses import dataclass
from typing import Any

import requests
from sqlalchemy import Column
from sqlmodel import SQLModel

# Import all models for validation
from dbsync.models import *


@dataclass
class FieldDefinition:
    """Represents a field definition from the official schema."""

    name: str
    type_: str
    nullable: bool = True
    primary_key: bool = False
    foreign_key: str | None = None
    unique: bool = False
    index: bool = False
    description: str | None = None


@dataclass
class TableDefinition:
    """Represents a table definition from the official schema."""

    name: str
    fields: list[FieldDefinition]
    description: str | None = None


@dataclass
class ValidationResult:
    """Result of schema validation."""

    table_name: str
    model_class: type | None = None
    is_valid: bool = True
    errors: list[str] = None
    warnings: list[str] = None
    missing_fields: list[str] = None
    extra_fields: list[str] = None
    type_mismatches: list[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.missing_fields is None:
            self.missing_fields = []
        if self.extra_fields is None:
            self.extra_fields = []
        if self.type_mismatches is None:
            self.type_mismatches = []


class SchemaValidator:
    """Validates dbsync-py models against official Cardano DB Sync schema."""

    OFFICIAL_SCHEMA_URL = "https://raw.githubusercontent.com/IntersectMBO/cardano-db-sync/refs/heads/master/doc/schema.md"

    def __init__(self):
        self.official_schema: dict[str, TableDefinition] = {}
        self.model_registry: dict[str, type] = {}
        self._load_model_registry()

    def _load_model_registry(self):
        """Load all SQLModel classes from dbsync.models, excluding base models."""
        import dbsync.models as models_module

        # Base models to exclude from validation
        excluded_base_models = {
            "d_b_sync_base",  # DBSyncBase - abstract base class
            "network_model",  # NetworkModel - configuration model
            "timestamped_model",  # TimestampedModel - abstract base class
        }

        for name in dir(models_module):
            obj = getattr(models_module, name)
            if (
                inspect.isclass(obj)
                and issubclass(obj, SQLModel)
                and hasattr(obj, "__tablename__")
                and obj != SQLModel
                and obj.__tablename__ not in excluded_base_models
            ):
                self.model_registry[obj.__tablename__] = obj

    def fetch_official_schema(self) -> bool:
        """Fetch and parse the official Cardano DB Sync schema."""
        try:
            response = requests.get(self.OFFICIAL_SCHEMA_URL, timeout=30)
            response.raise_for_status()

            schema_content = response.text
            self.official_schema = self._parse_schema_markdown(schema_content)
            return True

        except Exception as e:
            print(f"Error fetching official schema: {e}")
            return False

    def _parse_schema_markdown(self, content: str) -> dict[str, TableDefinition]:
        """Parse the schema markdown file to extract table definitions."""
        tables = {}

        # Find all table definitions - support both formats:
        # Official: ### `table_name`
        # Test: ### Table: `table_name`
        table_pattern = r"### (?:Table: )?`(\w+)`\n+(.*?)(?=\n### (?:Table: )?`|\Z)"
        table_matches = re.findall(table_pattern, content, re.DOTALL)

        for table_name, table_content in table_matches:
            fields = self._parse_table_fields(table_content)
            tables[table_name] = TableDefinition(
                name=table_name,
                fields=fields,
                description=self._extract_table_description(table_content),
            )

        return tables

    def _parse_table_fields(self, table_content: str) -> list[FieldDefinition]:
        """Parse field definitions from table content."""
        fields = []

        # Look for field definitions in markdown table format
        field_pattern = r"\| `(\w+)` \| `([^`]+)` \| ([^|]+) \| ([^|]+) \|"
        field_matches = re.findall(field_pattern, table_content)

        for field_name, field_type, nullable_str, description in field_matches:
            nullable = "NOT NULL" not in nullable_str.upper()
            primary_key = "PRIMARY KEY" in description.upper()
            unique = "UNIQUE" in description.upper()
            index = "INDEX" in description.upper()

            # Extract foreign key reference
            fk_match = re.search(r"REFERENCES `(\w+)`", description)
            foreign_key = fk_match.group(1) if fk_match else None

            fields.append(
                FieldDefinition(
                    name=field_name,
                    type_=field_type.strip(),
                    nullable=nullable,
                    primary_key=primary_key,
                    foreign_key=foreign_key,
                    unique=unique,
                    index=index,
                    description=description.strip(),
                )
            )

        return fields

    def _extract_table_description(self, content: str) -> str | None:
        """Extract table description from content."""
        desc_match = re.search(r"^([^|]+?)(?=\n\|)", content, re.MULTILINE)
        return desc_match.group(1).strip() if desc_match else None

    def validate_all_models(self) -> dict[str, ValidationResult]:
        """Validate all models against the official schema."""
        if not self.official_schema:
            if not self.fetch_official_schema():
                raise RuntimeError("Could not fetch official schema")

        results = {}

        # Validate existing models
        for table_name, model_class in self.model_registry.items():
            results[table_name] = self.validate_model(model_class)

        # Check for missing models
        for table_name in self.official_schema:
            if table_name not in self.model_registry:
                results[table_name] = ValidationResult(
                    table_name=table_name,
                    model_class=None,
                    is_valid=False,
                    errors=[f"Model for table '{table_name}' not implemented"],
                )

        return results

    def validate_model(self, model_class: type) -> ValidationResult:
        """Validate a single model against the official schema."""
        table_name = model_class.__tablename__
        result = ValidationResult(table_name=table_name, model_class=model_class)

        if table_name not in self.official_schema:
            result.is_valid = False
            result.errors.append(f"Table '{table_name}' not found in official schema")
            return result

        official_table = self.official_schema[table_name]
        model_fields = self._get_model_fields(model_class)

        # Check for missing fields
        official_field_names = {f.name for f in official_table.fields}
        model_field_names = set(model_fields.keys())

        missing = official_field_names - model_field_names
        extra = model_field_names - official_field_names

        result.missing_fields = list(missing)
        result.extra_fields = list(extra)

        if missing:
            result.errors.extend([f"Missing field: {field}" for field in missing])
            result.is_valid = False

        if extra:
            result.warnings.extend(
                [f"Extra field not in schema: {field}" for field in extra]
            )

        # Validate field types for common fields
        for field_name in official_field_names & model_field_names:
            official_field = next(
                f for f in official_table.fields if f.name == field_name
            )
            model_field = model_fields[field_name]

            type_validation = self._validate_field_type(official_field, model_field)
            if not type_validation[0]:
                result.type_mismatches.append(
                    f"Field '{field_name}': {type_validation[1]}"
                )
                result.is_valid = False

        return result

    def _get_model_fields(self, model_class: type) -> dict[str, Column]:
        """Extract field information from SQLModel class."""
        fields = {}

        if hasattr(model_class, "__table__"):
            for column in model_class.__table__.columns:
                fields[column.name] = column

        return fields

    def _validate_field_type(
        self, official_field: FieldDefinition, model_column: Column
    ) -> tuple[bool, str]:
        """Validate field type compatibility."""
        official_type = official_field.type_.lower()
        model_type = str(model_column.type).lower()

        # Type mapping for validation
        type_mappings = {
            "bigint": ["biginteger", "bigint"],
            "integer": ["integer", "int"],
            "text": ["text", "string", "varchar"],
            "bytea": ["bytea", "largeBinary", "hash28type", "hash32type"],
            "timestamp": ["datetime", "timestamp"],
            "boolean": ["boolean", "bool"],
            "numeric": ["numeric", "decimal"],
            "jsonb": ["jsonb", "json"],
            "double precision": ["double_precision", "float", "real"],
        }

        # Find compatible types
        for official_base, model_variants in type_mappings.items():
            if official_base in official_type:
                for variant in model_variants:
                    if variant in model_type:
                        return True, ""

        # Special cases for custom types
        custom_types = {
            "lovelace": "lovelacetype",
            "word31": "word31type",
            "word63": "word63type",
            "word64": "word64type",
            "asset32": "asset32type",
            "int65": "int65type",
        }

        for official_custom, model_custom in custom_types.items():
            if official_custom in official_type and model_custom in model_type:
                return True, ""

        return (
            False,
            f"Type mismatch: expected '{official_field.type_}', got '{model_column.type}'",
        )

    def generate_validation_report(self, results: dict[str, ValidationResult]) -> str:
        """Generate a comprehensive validation report."""
        report = ["Schema Validation Report", "=" * 50, ""]

        total_tables = len(results)
        valid_tables = sum(1 for r in results.values() if r.is_valid)
        invalid_tables = total_tables - valid_tables

        # Avoid division by zero
        success_rate = (valid_tables / total_tables * 100) if total_tables > 0 else 0.0

        report.extend(
            [
                f"Total Tables: {total_tables}",
                f"Valid Tables: {valid_tables}",
                f"Invalid Tables: {invalid_tables}",
                f"Validation Success Rate: {success_rate:.1f}%",
                "",
            ]
        )

        # Group results by status
        valid_results = {k: v for k, v in results.items() if v.is_valid}
        invalid_results = {k: v for k, v in results.items() if not v.is_valid}

        if invalid_results:
            report.extend(["Invalid Tables:", "-" * 20])
            for table_name, result in sorted(invalid_results.items()):
                report.append(f"\n❌ {table_name}")
                if result.model_class is None:
                    report.append("   Status: Not implemented")
                else:
                    report.append(f"   Model: {result.model_class.__name__}")

                if result.errors:
                    report.extend([f"   Error: {error}" for error in result.errors])

                if result.missing_fields:
                    report.append(
                        f"   Missing Fields: {', '.join(result.missing_fields)}"
                    )

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

        if valid_results:
            report.extend(["Valid Tables:", "-" * 20])
            for table_name in sorted(valid_results.keys()):
                result = valid_results[table_name]
                report.append(f"✅ {table_name} ({result.model_class.__name__})")
                if result.warnings:
                    report.extend(
                        [f"   Warning: {warning}" for warning in result.warnings]
                    )

        return "\n".join(report)

    def get_implementation_coverage(
        self, results: dict[str, ValidationResult]
    ) -> dict[str, Any]:
        """Get implementation coverage statistics."""
        total_tables = len(self.official_schema)
        implemented_tables = len(
            [r for r in results.values() if r.model_class is not None]
        )
        valid_tables = len([r for r in results.values() if r.is_valid])

        # Avoid division by zero
        implementation_coverage = (
            (implemented_tables / total_tables * 100) if total_tables > 0 else 0.0
        )
        validation_success_rate = (
            (valid_tables / total_tables * 100) if total_tables > 0 else 0.0
        )

        return {
            "total_tables_in_schema": total_tables,
            "implemented_tables": implemented_tables,
            "valid_implementations": valid_tables,
            "implementation_coverage": implementation_coverage,
            "validation_success_rate": validation_success_rate,
            "missing_tables": [
                table_name
                for table_name, result in results.items()
                if result.model_class is None
            ],
            "invalid_tables": [
                table_name
                for table_name, result in results.items()
                if not result.is_valid
            ],
        }


def validate_schema_compliance() -> dict[str, ValidationResult]:
    """Convenience function to validate all models against official schema."""
    validator = SchemaValidator()
    return validator.validate_all_models()


def generate_schema_report() -> str:
    """Generate a complete schema validation report."""
    validator = SchemaValidator()
    results = validator.validate_all_models()
    return validator.generate_validation_report(results)
