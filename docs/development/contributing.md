# Contributing

We welcome contributions to dbsync-py! This guide provides basic development setup information.

!!! info "Complete Contributors Guide"
    For comprehensive information about our automated versioning system, branch naming conventions, and detailed contribution workflow, please see our **[Contributors Guide](contributors.md)**.

## Quick Overview

## Development Setup

### Prerequisites

- Python 3.12+
- PostgreSQL with Cardano DB Sync data
- Git

### Clone the Repository

```bash
git clone https://github.com/your-org/dbsync-py.git
cd dbsync-py
```

### Install Development Dependencies

```bash
pip install -e ".[dev]"
```

### Set Up Pre-commit Hooks

```bash
pre-commit install
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=dbsync_py

# Run specific test file
pytest tests/test_connection.py
```

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking
mypy src/
```

### Documentation

```bash
# Serve documentation locally
mkdocs serve

# Build documentation
mkdocs build
```

## Contribution Guidelines

### Code Style

- Follow PEP 8 and Google Python Style Guide
- Use type hints for all functions and methods
- Write docstrings in Google format
- Keep line length under 88 characters

### Testing

- Write tests for new features
- Maintain test coverage above 80%
- Use pytest fixtures for common setup
- Mock external dependencies

### Documentation

- Update documentation for new features
- Include code examples in docstrings
- Update API reference as needed

## Submitting Changes

!!! warning "Important Workflow Requirements"
    Our project uses automated versioning based on branch names. Please read the [Contributors Guide](contributors.md) for detailed requirements.

**Quick Steps:**
1. Fork the repository
2. Create a feature branch following naming conventions:
   - `feat/feature-name` for new features (minor version bump)
   - `fix/bug-description` for bug fixes (patch version bump)
3. Make your changes with proper tests
4. Run all quality checks locally
5. Submit a pull request targeting the `dev` branch

## Branch Naming Requirements

- **Feature branches**: `feat/` or `feature/` (triggers minor version bump)
- **Other branches**: `fix/`, `docs/`, `refactor/`, `chore/`, `test/` (triggers patch version bump)
- **Target**: All PRs must target `dev` branch, never `master`

## Reporting Issues

Please report bugs and feature requests using our issue templates:
- [Bug Report Template](https://github.com/your-org/dbsync-py/issues/new?template=bug_report.md)
- [Feature Request Template](https://github.com/your-org/dbsync-py/issues/new?template=feature_request.md)
