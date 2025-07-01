## Description

Brief description of the changes made in this pull request.

## Type of Change

Please select the type of change this PR represents:

- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 📚 Documentation update
- [ ] 🔧 Refactoring (code changes that neither fix bugs nor add features)
- [ ] 🧪 Tests (adding or updating tests)
- [ ] 🔨 Chore (maintenance tasks, dependency updates, etc.)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)

## Related Issues

Closes #(issue number)
Fixes #(issue number)
Resolves #(issue number)

## Branch Naming Verification

- [ ] My branch name follows the required conventions:
  - `feat/` or `feature/` for new features (triggers minor version bump)
  - `fix/`, `docs/`, `refactor/`, `chore/`, `test/` for other changes (triggers patch version bump)

## Testing

- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] I have tested both sync and async code paths (where applicable)
- [ ] Test coverage is maintained or improved

## Code Quality

- [ ] My code follows the project's style guidelines (Google Python Style Guide)
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added type hints to all new functions and methods

## Local Verification

Please confirm you have run these commands locally and they all pass:

- [ ] `ruff check .` - Linting passes
- [ ] `ruff format .` - Formatting is correct
- [ ] `mypy src/` - Type checking passes
- [ ] `pytest` - All tests pass

## Documentation

- [ ] I have updated the documentation accordingly
- [ ] I have added docstrings to new functions/classes in Google format
- [ ] I have updated the changelog (if applicable)

## Deployment Considerations

- [ ] This change requires a documentation update
- [ ] This change requires a database migration
- [ ] This change has dependencies that need to be installed
- [ ] This change affects the public API

## Screenshots (if applicable)

If your changes include UI modifications or visual improvements, please add screenshots here.

## Additional Notes

Add any other context about the pull request here.

---

**Reminder**: This PR should target the `dev` branch, not `master`. The automated versioning system will handle version bumps based on your branch name.
