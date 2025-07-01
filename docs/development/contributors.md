# Contributors Guide

Welcome to the dbsync-py project! This guide explains our development workflow, versioning system, and contribution requirements.

## 🚀 Quick Start for Contributors

1. **Fork** the repository
2. **Clone** your fork locally
3. **Create a feature branch** following our naming conventions
4. **Make your changes** with proper tests and documentation
5. **Submit a pull request** to the `dev` branch

## 🌿 Branch Strategy & Workflow

We use an **automated GitFlow-style workflow** with strict branch naming conventions and automated versioning.

### Branch Structure

- **`master`**: Production-ready releases only
- **`dev`**: Integration branch for all development work
- **Feature branches**: Individual features/fixes (merged into `dev`)

### Critical Workflow Rules

!!! warning "Important"
    - **Never push directly to `master`** - it's protected and managed by automation
    - **All pull requests must target `dev`** - never target `master` directly
    - **Follow branch naming conventions** - they control automatic versioning

## 🏷️ Branch Naming Conventions

Our automated versioning system uses branch names to determine version bump types. **You must follow these conventions:**

### Feature Branches (Minor Version Bump)

For new features that add functionality:

```
feat/feature-name
feature/feature-name
```

**Examples:**
- `feat/add-staking-queries`
- `feature/governance-models`
- `feat/async-connection-pooling`

### Bug Fix & Other Branches (Patch Version Bump)

For bug fixes, documentation, refactoring, etc.:

```
fix/issue-description
docs/documentation-update
refactor/code-improvement
chore/maintenance-task
test/test-improvements
```

**Examples:**
- `fix/connection-timeout-handling`
- `docs/update-installation-guide`
- `refactor/optimize-query-performance`
- `chore/update-dependencies`
- `test/add-integration-tests`

### Branch Naming Rules

- Use **lowercase** with **hyphens** (kebab-case)
- Be **descriptive** but **concise**
- Include **issue numbers** when applicable: `fix/issue-123-connection-error`
- Avoid special characters except hyphens

## 🔢 Automated Versioning System

Our project uses **fully automated semantic versioning** with the following rules:

### Version Format

- **Release versions**: `1.2.3` (on master)
- **Development versions**: `1.2.3-dev1`, `1.2.3-dev2` (on dev)

### Automatic Version Bumps

| Branch Type | Version Bump | Example |
|-------------|--------------|---------|
| `feat/` or `feature/` | Minor | `1.0.0` → `1.1.0-dev1` |
| All other branches | Patch | `1.0.0` → `1.0.1-dev1` |
| Subsequent dev commits | Dev increment | `1.0.1-dev1` → `1.0.1-dev2` |
| Master release | Release | `1.0.1-dev5` → `1.0.1` |

### How It Works

1. **Feature Branch → Dev**: When your PR is merged to `dev`, version is automatically bumped
2. **Dev Sync**: If `dev` is synced from `master`, no version bump occurs (smart detection)
3. **Master Release**: When `dev` is merged to `master`, creates a release version
4. **Dev Reset**: After master release, `dev` is automatically reset to match `master`

## 🛠️ Development Setup

### Prerequisites

- **Python 3.12+**
- **Git** with proper configuration
- **PostgreSQL** with Cardano DB Sync data (for testing)

### Initial Setup

```bash
# Fork and clone the repository
git clone https://github.com/YOUR-USERNAME/dbsync-py.git
cd dbsync-py

# Install development dependencies
pip install -e ".[dev]"

# Set up pre-commit hooks
pre-commit install

# Create your feature branch
git checkout dev
git pull origin dev
git checkout -b feat/your-feature-name
```

### Development Workflow

```bash
# Make your changes
# ... edit files ...

# Run quality checks locally
ruff check .
ruff format .
mypy src/
pytest

# Commit and push
git add .
git commit -m "feat: add new feature description"
git push origin feat/your-feature-name

# Create pull request targeting 'dev' branch
```

## ✅ Code Quality Standards

### Required Checks

All contributions must pass:

- **Ruff linting**: Code style and quality
- **Ruff formatting**: Consistent code formatting
- **MyPy**: Type checking
- **Pytest**: All tests must pass
- **Coverage**: Maintain or improve test coverage

### Code Style

- Follow **Google Python Style Guide**
- Use **type hints** for all functions and methods
- Write **docstrings** in Google format
- Keep **line length** under 88 characters
- Use **snake_case** for functions/variables, **PascalCase** for classes

### Testing Requirements

- **Write tests** for new features
- **Maintain coverage** above current levels
- **Use pytest fixtures** for common setup
- **Mock external dependencies**
- **Test both sync and async** code paths where applicable

## 📝 Commit Message Guidelines

Use **conventional commit** format for clear history:

```
type(scope): description

[optional body]

[optional footer]
```

### Commit Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```bash
feat(models): add governance model classes
fix(connection): handle timeout errors gracefully
docs(api): update session management documentation
test(queries): add integration tests for staking queries
```

## 🔍 Pull Request Process

### Before Submitting

1. **Sync with dev**: Ensure your branch is up-to-date
2. **Run all checks**: Ensure all quality checks pass locally
3. **Update documentation**: Add/update relevant documentation
4. **Add tests**: Include tests for new functionality
5. **Check coverage**: Ensure test coverage is maintained

### PR Requirements

- **Target `dev` branch** (never `master`)
- **Descriptive title** following conventional commit format
- **Clear description** explaining the changes
- **Link related issues** using GitHub keywords
- **All CI checks** must pass
- **Code review** approval required

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] Coverage maintained/improved

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

## 🚨 Important Automation Notes

### What Happens Automatically

- **Version bumping** based on branch name
- **Git tagging** for all versions
- **Dev branch reset** after master releases
- **CI/CD pipeline** runs on all changes

### What NOT to Do

- ❌ Don't manually edit version numbers
- ❌ Don't push directly to `master` or `dev`
- ❌ Don't force push to shared branches
- ❌ Don't ignore branch naming conventions
- ❌ Don't merge without PR review

### If Something Goes Wrong

1. **Contact maintainers** immediately
2. **Don't try to fix** version issues manually
3. **Provide details** about what happened
4. **Wait for guidance** before making changes

## 🤝 Code Review Guidelines

### For Contributors

- **Respond promptly** to review feedback
- **Ask questions** if feedback is unclear
- **Make requested changes** in new commits
- **Squash commits** before final merge (if requested)

### For Reviewers

- **Be constructive** and helpful
- **Focus on code quality** and maintainability
- **Check test coverage** and documentation
- **Verify branch naming** conventions
- **Ensure CI passes** before approval

## 📞 Getting Help

### Documentation

- **API Reference**: Auto-generated from docstrings
- **User Guide**: Comprehensive usage examples
- **Examples**: Practical code patterns

### Community

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and community help
- **Pull Requests**: Code review and collaboration

### Maintainer Contact

For urgent issues or questions about the automated workflow:

1. **Open an issue** with the `question` label
2. **Tag maintainers** in your issue or PR
3. **Provide context** about your specific situation

## 🎯 Contribution Opportunities

### Good First Issues

Look for issues labeled:
- `good first issue`
- `help wanted`
- `documentation`

### Areas Needing Help

- **Model implementations** for new DB Sync schema tables
- **Query examples** for common use cases
- **Documentation improvements**
- **Test coverage** expansion
- **Performance optimizations**

---

Thank you for contributing to dbsync-py! Your contributions help make Cardano data more accessible to Python developers. 🚀
