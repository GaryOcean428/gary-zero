# Code Quality and Linting Setup

This document describes the comprehensive linting and code formatting setup for the Zero project.

## Tools Installed

### Python Tools

- **Black** (25.1.0): Code formatter for consistent Python style
- **Ruff** (0.11.13): Fast Python linter and code fixer (replaces Flake8)
- **MyPy** (1.16.0): Static type checker
- **Pylint**: Additional static analysis
- **detect-secrets** (1.5.0): Prevents secrets from being committed

### Frontend Tools

- **Markdownlint**: Markdown linting and formatting
- **Stylelint**: CSS linting and formatting
- **HTMLHint**: HTML validation and linting
- **Prettier**: Code formatting for web files

## Quick Start

### Using the Lint Script

The project includes a comprehensive `lint.py` script with the following commands:

#### Python Linting

```bash
# Format and auto-fix code
python lint.py fix

# Check for issues
python lint.py check

# Show statistics
python lint.py stats

# Format code with Black
python lint.py black

# Run Ruff checks
python lint.py ruff

# Run MyPy type checking
python lint.py mypy

# Run Pylint checks
python lint.py pylint

# Run all Python tools
python lint.py all
```

#### Frontend Linting

```bash
# Check all frontend files
python lint.py frontend

# Check Markdown files
python lint.py markdown

# Check CSS files
python lint.py css

# Check HTML files
python lint.py html
```

### Manual Commands

You can also run the tools directly:

```bash
# Format code with Black
black python/

# Auto-fix issues with Ruff
ruff check python/ --fix --unsafe-fixes

# Check code with Ruff
ruff check python/

# Type check with MyPy
mypy python/

# Check for secrets
detect-secrets scan --all-files --baseline .secrets.baseline

# Run Pylint (if you want additional checks)
pylint python/
```

## Current Status

As of setup completion:

- **Started with**: 329 linting issues
- **Auto-fixed**: 109 issues (33% improvement)
- **Remaining**: 220 issues

### Issue Breakdown

- 191 line-too-long (E501) - mostly long comments and strings
- 12 module-import-not-at-top-of-file (E402)
- 7 raise-without-from-inside-except (B904)
- 2 bare-except (E722)
- Various minor style issues (SIM102, SIM115, etc.)

## Configuration Files

### Python Configuration

**pyproject.toml** - Central configuration for all Python tools:

- Black formatting (100 char line length)
- Ruff linting rules and import sorting
- MyPy type checking configuration
- Pylint settings (consolidated from .pylintrc)
- Project metadata and dependencies

**.flake8** - Flake8 disabled in favor of Ruff

### Frontend Configuration

**.markdownlint.json** - Markdown linting rules:

- 100 character line length
- ATX-style headers
- Allows HTML elements for documentation

**.stylelintrc.json** - CSS linting configuration:

- Standard CSS rules
- 100 character line length
- Double quotes for strings
- Proper spacing and formatting

**.htmlhintrc** - HTML validation rules:

- HTML5 doctype enforcement
- Attribute validation
- Accessibility checks (alt tags, etc.)

### VSCode Integration

**.vscode/settings.json** - IDE configuration:

- Python interpreter and tool paths
- Format on save enabled
- Line length rulers at 100 characters
- File exclusions for cleaner workspace

**.vscode/extensions.json** - Recommended extensions:

- Python toolchain (Black, Ruff, MyPy, Pylint)
- Frontend tools (Markdownlint, Stylelint, HTMLHint)
- Excludes conflicting extensions (Flake8)

## Integration with IDE

### VSCode Setup

The project is pre-configured for VSCode. Recommended extensions will be automatically suggested:

**Python Extensions:**

- Python (ms-python.python)
- Mypy Type Checker (ms-python.mypy-type-checker)
- Black Formatter (ms-python.black-formatter)
- Ruff (charliermarsh.ruff)
- Pylint (ms-python.pylint)

**Frontend Extensions:**

- Markdownlint (davidanson.vscode-markdownlint)
- Stylelint (stylelint.vscode-stylelint)
- HTMLHint (mkaufman.htmlhint)
- Prettier (esbenp.prettier-vscode)

### Pre-commit Hooks (Optional)

You can set up pre-commit hooks to run linting automatically:

```bash
# Install pre-commit
pip install pre-commit

# Set up hooks (if .pre-commit-config.yaml exists)
pre-commit install
```

## Best Practices

1. **Run `python lint.py fix` before committing** - This formats code and fixes auto-fixable issues
2. **Check `python lint.py check` status** - Ensure no new issues are introduced
3. **Focus on critical issues first** - Address bare excepts, import errors, and security issues
4. **Gradual improvement** - Fix issues in small batches rather than all at once

## Workflow

### Before Committing

```bash
# Format and fix
python lint.py fix

# Check remaining issues
python lint.py check

# Review and manually fix critical issues
```

### During Development

```bash
# Quick check on specific file
ruff check python/api/myfile.py --fix

# Format specific file
black python/api/myfile.py
```

## Ignoring Rules

### Temporary Ignores

For specific lines, use:

```python
# ruff: noqa: E501
very_long_line_that_cannot_be_shortened = "some very long string that exceeds the limit"

# pylint: disable=line-too-long
another_long_line = "another example"
```

### File-level Ignores

At the top of a file:

```python
# ruff: noqa: E402
# pylint: disable=wrong-import-position
```

## Future Improvements

1. **Reduce line-too-long issues** - Break up long strings and comments
2. **Fix import order** - Move imports to top of files where possible
3. **Improve exception handling** - Add proper exception chaining
4. **Add type hints** - Improve MyPy coverage
5. **Set up CI/CD** - Automate linting checks in continuous integration

## Troubleshooting

### Common Issues

#### "Command not found"

- Ensure tools are installed: `uv add --dev black ruff mypy`

#### "No module named 'python'"

- Run commands from project root directory

#### "Permission denied on lint.py"**

- Make executable: `chmod +x lint.py`

### Getting Help

Run any tool with `--help` for options:

```bash
black --help
ruff --help
mypy --help
python lint.py --help
