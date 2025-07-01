# Schema Validation Utilities

This module provides comprehensive utilities for validating `dbsync-py` model definitions against the official Cardano DB Sync schema.

## Overview

The schema validation system ensures that our Python models accurately represent the official Cardano DB Sync database schema by:

- Fetching the latest schema from the official repository
- Comparing field definitions, types, and constraints
- Reporting missing, extra, or mismatched fields
- Providing detailed validation reports and coverage statistics

## Components

### Core Classes

#### `SchemaValidator`
Main validation engine that:
- Fetches official schema from GitHub
- Loads all SQLModel classes from `dbsync.models`
- Performs comprehensive field-by-field validation
- Generates detailed reports and statistics

#### `FieldDefinition`
Represents a field definition from the official schema:
```python
@dataclass
class FieldDefinition:
    name: str
    type_: str
    nullable: bool = True
    primary_key: bool = False
    foreign_key: Optional[str] = None
    unique: bool = False
    index: bool = False
    description: Optional[str] = None
```

#### `ValidationResult`
Contains validation results for a single table:
```python
@dataclass
class ValidationResult:
    table_name: str
    model_class: Optional[type] = None
    is_valid: bool = True
    errors: List[str] = None
    warnings: List[str] = None
    missing_fields: List[str] = None
    extra_fields: List[str] = None
    type_mismatches: List[str] = None
```

### Validation Features

#### Field Validation
- **Missing Fields**: Identifies fields present in official schema but missing from models
- **Extra Fields**: Identifies fields in models not present in official schema (warnings)
- **Type Compatibility**: Validates PostgreSQL types against SQLAlchemy types
- **Constraint Validation**: Checks primary keys, foreign keys, uniqueness, and nullability

#### Type Mapping
Supports comprehensive type mapping between PostgreSQL and SQLAlchemy:

| PostgreSQL Type | SQLAlchemy Types |
|----------------|------------------|
| `bigint` | `BigInteger`, `bigint` |
| `integer` | `Integer`, `int` |
| `text` | `Text`, `String`, `varchar` |
| `bytea` | `LargeBinary`, `Hash28Type`, `Hash32Type` |
| `timestamp` | `DateTime`, `timestamp` |
| `jsonb` | `JSONB`, `JSON` |
| `lovelace` | `LovelaceType` |
| `word31` | `Word31Type` |
| `word63` | `Word63Type` |
| `word64` | `Word64Type` |
| `asset32` | `Asset32Type` |
| `int65` | `Int65Type` |

## Usage

### Programmatic Usage

```python
from tests.schema_validation.schema_validator import (
    SchemaValidator,
    validate_schema_compliance,
    generate_schema_report
)

# Quick validation
results = validate_schema_compliance()

# Generate text report
report = generate_schema_report()
print(report)

# Detailed validation
validator = SchemaValidator()
results = validator.validate_all_models()

# Get coverage statistics
coverage = validator.get_implementation_coverage(results)
print(f"Implementation Coverage: {coverage['implementation_coverage']:.1f}%")
print(f"Validation Success Rate: {coverage['validation_success_rate']:.1f}%")
```

### Command Line Usage

The `run_schema_validation.py` script provides a comprehensive CLI interface:

#### Basic Validation
```bash
python tests/schema_validation/run_schema_validation.py
```

#### Coverage Report Only
```bash
python tests/schema_validation/run_schema_validation.py --coverage-only
```

#### Errors Only (Verbose)
```bash
python tests/schema_validation/run_schema_validation.py --errors-only --verbose
```

#### JSON Output
```bash
python tests/schema_validation/run_schema_validation.py --format json --output validation_results.json
```

#### CLI Options
- `--format {text,json}`: Output format (default: text)
- `--output FILE`: Write output to file instead of stdout
- `--coverage-only`: Show only coverage statistics
- `--errors-only`: Show only validation errors
- `--verbose`: Include detailed field information
- `--help`: Show help message

## Integration with Testing

### Unit Tests
Run schema validation tests:
```bash
pytest tests/schema_validation/test_schema_validator.py -v
```

### Integration Tests
Run integration tests that validate against real models:
```bash
pytest tests/schema_validation/test_schema_validator.py::test_real_model_validation -v
```

### CI/CD Integration
Add to your CI pipeline:
```yaml
- name: Validate Schema Compliance
  run: |
    python tests/schema_validation/run_schema_validation.py --format json --output schema_validation.json
    # Process results or fail build if validation errors found
```

## Example Output

### Text Report
```
Schema Validation Report
==================================================

Total Tables: 79
Valid Tables: 79
Invalid Tables: 0
Validation Success Rate: 100.0%

Valid Tables:
--------------------
✅ ada_pots (AdaPots)
✅ address (Address)
✅ block (Block)
✅ committee (Committee)
✅ tx (Transaction)
✅ tx_out (TransactionOutput)
...
```

### Coverage Report
```
Schema Implementation Coverage Report
==================================================

📊 Total Tables in Official Schema: 79
✅ Implemented Tables: 79
🎯 Valid Implementations: 79
📈 Implementation Coverage: 100.0%
✨ Validation Success Rate: 100.0%
```

### Error Report (when issues exist)
```
Schema Validation Errors Report
==================================================
Found 2 tables with validation issues:

❌ example_table
   Model: ExampleTable
   Error: Missing field: new_field
   Missing Fields: new_field
   Type Issue: Field 'amount': Type mismatch: expected 'numeric', got 'INTEGER'

❌ missing_table
   Status: Not implemented
   Error: Model for table 'missing_table' not implemented
```

## Configuration

### Schema Source
The validator fetches the official schema from:
```
https://raw.githubusercontent.com/IntersectMBO/cardano-db-sync/refs/heads/master/doc/schema.md
```

### Custom Schema URL
You can modify the `OFFICIAL_SCHEMA_URL` constant in `SchemaValidator` to use a different schema source.

### Offline Testing
For offline testing, you can mock the schema by setting `validator.official_schema` directly:

```python
validator = SchemaValidator()
validator.official_schema = {
    "test_table": TableDefinition(
        name="test_table",
        fields=[
            FieldDefinition("id", "bigint", primary_key=True),
            FieldDefinition("name", "text")
        ]
    )
}
results = validator.validate_all_models()
```

## Best Practices

### Development Workflow
1. **Regular Validation**: Run schema validation regularly during development
2. **Pre-commit Hooks**: Add validation to pre-commit hooks
3. **CI Integration**: Include validation in continuous integration
4. **Documentation**: Update documentation when schema changes

### Handling Validation Issues
1. **Missing Fields**: Add missing fields to models
2. **Type Mismatches**: Update field types to match official schema
3. **Extra Fields**: Evaluate if extra fields are needed or should be removed
4. **New Tables**: Implement missing table models

### Performance Considerations
- Schema fetching involves network requests (cache results for repeated runs)
- Large schemas may take time to validate (use `--errors-only` for faster feedback)
- Integration tests are slower than unit tests (mark with `@pytest.mark.slow`)

## Troubleshooting

### Network Issues
If schema fetching fails:
```python
# Check network connectivity
validator = SchemaValidator()
success = validator.fetch_official_schema()
if not success:
    print("Failed to fetch schema - check network connection")
```

### Import Issues
If model loading fails:
```python
# Check model imports
validator = SchemaValidator()
print(f"Loaded {len(validator.model_registry)} models")
print("Available tables:", list(validator.model_registry.keys()))
```

### Type Mapping Issues
If type validation fails unexpectedly:
```python
# Debug type mapping
validator = SchemaValidator()
official_field = FieldDefinition("test", "custom_type")
model_column = Mock()
model_column.type = "CustomType"

is_valid, error = validator._validate_field_type(official_field, model_column)
print(f"Valid: {is_valid}, Error: {error}")
```

## Contributing

When adding new validation features:

1. **Add Tests**: Include comprehensive unit and integration tests
2. **Update Documentation**: Update this README with new features
3. **Type Mapping**: Add new type mappings as needed
4. **CLI Options**: Add relevant CLI options for new features
5. **Error Messages**: Provide clear, actionable error messages

## Related Files

- `schema_validator.py`: Core validation logic
- `test_schema_validator.py`: Comprehensive test suite
- `run_schema_validation.py`: CLI interface
- `__init__.py`: Package initialization
- `README.md`: This documentation

## Dependencies

- `requests`: For fetching official schema
- `sqlmodel`: For model introspection
- `sqlalchemy`: For database type handling
- `pytest`: For testing framework
- `pydantic`: For data validation (via SQLModel)
