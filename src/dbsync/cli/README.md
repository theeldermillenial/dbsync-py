# dbsync-py CLI Interface

The `dbsync-py` package provides a comprehensive command-line interface for schema validation, performance benchmarking, and database operations.

## Installation

The CLI is automatically available after installing the package:

```bash
pip install dbsync-py
# or
uv add dbsync-py
```

## Commands Overview

### Global Options

- `--version`: Show package version
- `--verbose, -v`: Enable verbose output
- `--help`: Show help message

### Available Commands

1. **`validate`** - Schema validation against official Cardano DB Sync schema
2. **`benchmark`** - Performance benchmarking of models and operations
3. **`info`** - Package and configuration information

## Command Reference

### `dbsync-py validate`

Validates database schema against the official Cardano DB Sync schema.

**Usage:**
```bash
dbsync-py validate [OPTIONS]
```

**Options:**
- `--format [text|json]`: Output format (default: text)
- `--coverage-only`: Show only coverage statistics
- `--errors-only`: Show only validation errors
- `-o, --output PATH`: Output file (default: stdout)

**Examples:**
```bash
# Basic validation
dbsync-py validate

# Show only coverage statistics
dbsync-py validate --coverage-only

# Show only errors
dbsync-py validate --errors-only

# JSON output to file
dbsync-py validate --format json -o validation_report.json

# Verbose validation
dbsync-py validate --verbose
```

### `dbsync-py benchmark`

Runs performance benchmarks on database models and operations.

**Usage:**
```bash
dbsync-py benchmark [OPTIONS]
```

**Options:**
- `-o, --output PATH`: Output file for results (default: stdout)
- `--format [text|json]`: Output format (default: text)
- `--quick`: Run quick benchmarks only

**Examples:**
```bash
# Full benchmark suite
dbsync-py benchmark

# Quick benchmarks only
dbsync-py benchmark --quick

# JSON output to file
dbsync-py benchmark --format json -o benchmark_results.json

# Verbose benchmarking
dbsync-py benchmark --verbose
```

### `dbsync-py info`

Shows information about the package installation and configuration.

**Usage:**
```bash
dbsync-py info [OPTIONS]
```

**Options:**
- `--check-connection`: Test database connection
- `--show-config`: Show current configuration

**Examples:**
```bash
# Basic package info
dbsync-py info

# Test database connection
dbsync-py info --check-connection

# Show configuration details
dbsync-py info --show-config

# Full information
dbsync-py info --check-connection --show-config
```

## Output Formats

### Text Format (Default)

Human-readable output with formatting, colors, and clear section headers.

### JSON Format

Machine-readable JSON output suitable for automation and integration with other tools.

**Example JSON structure for validation:**
```json
{
  "summary": {
    "total_tables": 79,
    "valid_tables": 79,
    "invalid_tables": 0,
    "coverage_percentage": 100.0
  },
  "results": {
    "table_name": {
      "is_valid": true,
      "missing_fields": [],
      "extra_fields": [],
      "type_mismatches": {},
      "errors": []
    }
  }
}
```

## Integration Examples

### CI/CD Pipeline

```yaml
# GitHub Actions example
- name: Validate Schema
  run: |
    dbsync-py validate --format json -o validation_report.json
    if [ $? -ne 0 ]; then
      echo "Schema validation failed"
      exit 1
    fi

- name: Run Benchmarks
  run: |
    dbsync-py benchmark --format json -o benchmark_results.json
```

### Scripting

```bash
#!/bin/bash

# Check if schema is valid
if dbsync-py validate --errors-only --quiet; then
    echo "Schema validation passed"
    # Run benchmarks
    dbsync-py benchmark --quick
else
    echo "Schema validation failed"
    exit 1
fi
```

### Python Integration

```python
import subprocess
import json

# Run validation and get JSON results
result = subprocess.run(
    ["dbsync-py", "validate", "--format", "json"],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    validation_data = json.loads(result.stdout)
    print(f"Coverage: {validation_data['summary']['coverage_percentage']:.1f}%")
else:
    print(f"Validation failed: {result.stderr}")
```

## Configuration

The CLI respects the same environment variables as the library:

- `DBSYNC_HOST`: Database host
- `DBSYNC_PORT`: Database port
- `DBSYNC_DATABASE`: Database name
- `DBSYNC_USERNAME`: Database username
- `DBSYNC_PASSWORD`: Database password
- `DBSYNC_DATABASE_URL`: Complete database URL

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the package is properly installed
2. **Connection Errors**: Check database configuration and connectivity
3. **Permission Errors**: Ensure proper database permissions

### Debug Mode

Use the `--verbose` flag for detailed debugging information:

```bash
dbsync-py --verbose validate
```

### Getting Help

```bash
# General help
dbsync-py --help

# Command-specific help
dbsync-py validate --help
dbsync-py benchmark --help
dbsync-py info --help
```
