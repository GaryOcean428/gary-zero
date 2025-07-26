# Automated Issue Reporting Documentation

## Overview

This automated reporting system provides comprehensive checks for accessibility,
compatibility, security, and code quality issues in your web application. It leverages
Node.js and npm to run various linting and analysis tools.

## Prerequisites

✅ **Node.js v22.16.0** - Installed and verified
✅ **npm v10.9.2** - Installed and verified
✅ **All dependencies** - Installed via npm

## Tools Included

### 🔍 Code Quality & Security

- **ESLint** - JavaScript linting with security and accessibility rules
- **eslint-plugin-jsx-a11y** - Accessibility linting for web components
- **eslint-plugin-compat** - Browser compatibility checking

### 🔒 Security Analysis

- **npm audit** - Package vulnerability scanning
- **npm-audit-html** - HTML report generation for security issues

### ♿ Accessibility Testing

- **pa11y** - Automated accessibility testing
- **axe-core** - Accessibility rule engine

### 🌐 Performance & Compatibility

- **Lighthouse** - Performance and best practices auditing
- **Browserslist** - Browser compatibility configuration

## Quick Start

### 1. Run All Checks (Recommended)

```bash
# Run comprehensive automated reporting
node automated-reports.js

# Or use npm script
npm run check:all
```

### 2. Individual Check Commands

#### JavaScript Code Quality & Security

```bash
npm run lint           # Check for issues
npm run lint:fix       # Auto-fix issues
```

#### Security Vulnerabilities

```bash
npm run security       # Quick security check
npm run security:report # Generate HTML security report
```

#### Accessibility Testing

```bash
npm run accessibility:webui  # Test HTML files
npm run accessibility        # Test running web server
```

#### Performance Analysis

```bash
npm run lighthouse     # Full performance audit (requires running server)
npm run lighthouse:ci  # CI-friendly JSON output
```

### 3. Automated Fixes

```bash
npm run fix:all        # Run all available auto-fixes
```

## Report Output

### Generated Reports Location

All reports are saved in the `./reports/` directory with timestamps:

```tree
reports/
├── eslint-report-2025-06-25T13-13-34-000Z.json
├── security-audit-2025-06-25T13-13-34-000Z.json
├── html-validation-2025-06-25T13-13-34-000Z.txt
├── css-quality-2025-06-25T13-13-34-000Z.txt
└── summary-2025-06-25T13-13-34-000Z.json
```

### Report Types

#### 1. ESLint Report (JSON)

- JavaScript code quality issues
- Security vulnerabilities (eval, unsafe functions)
- Accessibility violations
- Browser compatibility issues

#### 2. Security Audit Report (JSON/HTML)

- Package vulnerabilities
- Severity levels (low, moderate, high, critical)
- Recommended fixes

#### 3. HTML Validation Report (Text)

- HTML markup errors
- Accessibility issues
- WCAG compliance violations

#### 4. CSS Quality Report (Text)

- CSS syntax errors
- Browser compatibility issues
- Performance recommendations

#### 5. Summary Report (JSON)

- Overall health status
- Quick issue overview
- Timestamp and metadata

## Configuration Files

### ESLint Configuration (`eslint.config.js`)

- Accessibility rules enabled
- Security best practices enforced
- Browser compatibility checking
- Modern JavaScript standards

### Browser Compatibility (`.browserslistrc`)

- Targets modern browsers with good accessibility support
- Excludes Internet Explorer
- Focuses on browsers with >1% usage

### Package Configuration (`package.json`)

- All necessary dependencies
- Comprehensive npm scripts
- Browser compatibility settings

## Integration with Existing Tools

This system complements your existing linting setup:

### Python Tools (Already Configured)

- **Black** - Python code formatting
- **Ruff** - Python linting
- **MyPy** - Type checking
- **Pylint** - Additional analysis

### Frontend Tools (Already Configured)

- **Markdownlint** - Markdown formatting
- **Stylelint** - CSS linting (enhanced with new config)
- **HTMLHint** - HTML validation (enhanced with new config)
- **Prettier** - Code formatting

## Command Reference

### Basic Commands

```bash
# Show help
node automated-reports.js --help

# Show version
node automated-reports.js --version

# Run all checks
node automated-reports.js
```

### NPM Scripts

```bash
npm run lint              # ESLint check
npm run lint:fix          # ESLint auto-fix
npm run security          # Security audit
npm run security:report   # Security HTML report
npm run accessibility:webui  # Accessibility check (HTML files)
npm run lighthouse        # Performance audit
npm run check:all         # Run lint + security + accessibility
npm run report:all        # Generate all reports
npm run fix:all           # Auto-fix all fixable issues
```

## Troubleshooting

### Common Issues

#### 1. "Command not found" errors

```bash
# Ensure dependencies are installed
npm install
```

#### 2. Permission denied for automated-reports.js

```bash
# Make script executable
chmod +x automated-reports.js
```

#### 3. Lighthouse requires running server

```bash
# Start your web server first, then run:
npm run lighthouse
```

#### 4. pa11y accessibility tests fail

```bash
# For local HTML files:
npm run accessibility:webui

# For running web server:
npm run accessibility
```

## Best Practices

### 1. Regular Checks

- Run `npm run check:all` before commits
- Use `npm run fix:all` for quick fixes
- Generate full reports weekly with `node automated-reports.js`

### 2. CI/CD Integration

```bash
# Add to your CI pipeline
npm run check:all
npm run security
```

### 3. Pre-commit Hooks

Consider adding these checks to Git pre-commit hooks for automatic validation.

### 4. Report Review

- Check the summary report for overall health
- Address high-severity security issues immediately
- Review accessibility violations for WCAG compliance

## Security Considerations

- **Never commit reports** containing sensitive information
- Review security audit findings promptly
- Update dependencies regularly
- Use `npm audit fix` carefully (test after fixes)

## Accessibility Standards

The system checks for:

- WCAG 2.1 compliance
- Keyboard navigation support
- Screen reader compatibility
- Color contrast ratios
- Alternative text for images
- Proper heading structure
- Form label associations

## Next Steps

1. **Run your first report**: `node automated-reports.js`
2. **Review generated reports** in the `./reports/` directory
3. **Fix critical issues** using auto-fix commands
4. **Set up regular reporting** schedule
5. **Integrate with your workflow** (CI/CD, pre-commit hooks)

For additional help or customization, refer to the individual tool documentation:

- [ESLint](https://eslint.org/docs/)
- [pa11y](https://pa11y.org/)
- [Lighthouse](https://developers.google.com/web/tools/lighthouse)
- [npm audit](https://docs.npmjs.com/cli/v8/commands/npm-audit)
