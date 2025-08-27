# Contributing to Rust Patch Monitor

Thank you for your interest in contributing to the Rust Patch Monitor! This document outlines our development process and guidelines.

## Development Workflow

We use a strict Pull Request (PR) based workflow to ensure code quality and prevent regressions:

### 1. Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/your-username/rust-patch-monitor.git
cd rust-patch-monitor

# Install dependencies
pip install -r requirements.txt
pip install -r test_requirements.txt

# Install development tools
pip install black flake8 pre-commit
```

### 2. Create Feature Branch

Always create a new branch for your changes:

```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

### 3. Development Process

#### Code Changes
- Make your changes following the existing code style
- Add tests for any new functionality
- Update documentation as needed

#### Local Testing (Required Before Push)

**Run the full test suite:**
```bash
python -m pytest test_rust_patch_monitor.py test_golden_masters.py -v
```

**Check code formatting:**
```bash
black rust_patch_monitor.py test_rust_patch_monitor.py test_golden_masters.py --check --diff
```

**Run linting:**
```bash
flake8 rust_patch_monitor.py test_rust_patch_monitor.py test_golden_masters.py --max-line-length=120
```

**Test CLI functionality:**
```bash
python rust_patch_monitor.py --help
python rust_patch_monitor.py list-patches --help
python rust_patch_monitor.py analyze --help
```

#### Automatic Code Formatting
```bash
# Format code automatically
black rust_patch_monitor.py test_rust_patch_monitor.py test_golden_masters.py --line-length=120

# Fix any remaining linting issues manually
```

### 4. Commit Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/) specification:

```bash
git commit -m "feat: add new engagement analysis feature"
git commit -m "fix: resolve XML parsing edge case"
git commit -m "test: add golden master tests for prompt structure"
git commit -m "docs: update installation instructions"
```

**Commit types:**
- `feat`: New features
- `fix`: Bug fixes
- `test`: Adding or updating tests
- `docs`: Documentation changes
- `refactor`: Code refactoring without functional changes
- `style`: Code style changes (formatting, missing semicolons, etc.)
- `ci`: CI/CD pipeline changes

### 5. Pull Request Process

#### Before Creating PR
1. Ensure all tests pass locally
2. Verify code is properly formatted
3. Update documentation if needed
4. Rebase your branch on latest main if needed

#### Creating the PR
1. Push your branch: `git push origin feature/your-feature-name`
2. Create PR on GitHub with descriptive title and description
3. Link any related issues
4. Wait for CI checks to pass
5. Request review from maintainers

#### PR Requirements
- ✅ All CI checks must pass (tests, linting, security)
- ✅ At least one code review approval
- ✅ Branch must be up-to-date with main
- ✅ All conversations resolved
- ✅ Descriptive commit messages

## Code Style Guidelines

### Python Code Style
- Follow PEP 8 with 120 character line limit
- Use Black for automatic code formatting
- Type hints are encouraged for new code
- Docstrings for all public functions and classes

### Testing Guidelines
- All new features must include tests
- Maintain or improve test coverage
- Use descriptive test names and docstrings
- Mock external dependencies (API calls)
- Golden master tests for critical output formats

### Documentation
- Update README.md for user-facing changes
- Add docstrings for new functions/classes
- Update CHANGELOG.md for notable changes
- Include examples for new features

## Development Scripts

### Quick Commands

Create a `Makefile` for common operations:
```bash
# Run all tests
make test

# Format and lint code
make lint

# Clean temporary files
make clean

# Run specific test groups
make test-unit
make test-integration
```

### Pre-commit Hooks

Install pre-commit hooks to catch issues early:
```bash
pre-commit install

# Run on all files
pre-commit run --all-files
```

## Testing Strategy

### Test Categories
1. **Unit Tests**: Test individual functions and methods
2. **Integration Tests**: Test API interactions (mocked)
3. **Golden Master Tests**: Prevent regressions in output formats
4. **CLI Tests**: Test command-line interface

### Test Coverage
- Maintain minimum 80% test coverage
- Focus on high-risk areas (engagement analysis, XML generation)
- Test edge cases and error conditions
- Mock external dependencies for reliability

## Architecture Guidelines

### Code Organization
- Keep API clients separate from business logic
- Use dependency injection for testability
- Follow single responsibility principle
- Maintain clear separation of concerns

### Dependencies
- Minimize external dependencies
- Pin dependency versions in requirements.txt
- Document any new dependencies and their purpose
- Consider security implications of new packages

## Debugging and Troubleshooting

### Common Issues
- **Tests failing**: Check Python version compatibility
- **Import errors**: Verify virtual environment activation
- **API issues**: Check network connectivity and API keys
- **Formatting issues**: Run Black before committing

### Debug Tools
```bash
# Verbose test output
python -m pytest -v -s

# Run specific test
python -m pytest test_rust_patch_monitor.py::TestEngagementAnalysis::test_extract_version_from_series_name -v

# Debug CLI commands
python rust_patch_monitor.py debug-recent
```

## Release Process

1. Update version in `__version__` variable
2. Update CHANGELOG.md with release notes
3. Create release branch: `git checkout -b release/v1.x.x`
4. Tag release: `git tag v1.x.x`
5. Push tag: `git push origin v1.x.x`

## Getting Help

- Open an issue for bugs or feature requests
- Join discussions on existing issues
- Reach out to maintainers for questions
- Check existing documentation and tests for examples

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project.