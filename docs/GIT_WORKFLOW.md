# Git Workflow and Release Process

This document outlines the standardized Git workflow and release process for the Gary-Zero project to prevent deployment of uncommitted changes.

## 🎯 Overview

The Gary-Zero project implements a comprehensive Git workflow validation system to ensure:
- All code changes are properly committed before deployment
- No uncommitted modifications reach production environments
- Consistent quality checks across all branches
- Clear documentation of the release process

## 🔧 Workflow Components

### 1. Pre-commit Hooks (Husky)

Automated checks run before each commit:
- ESLint critical error checks
- Python syntax validation (Ruff)
- Security vulnerability scanning
- Test execution
- Git status validation

**Location**: `.husky/pre-commit`

### 2. CI/CD Pipeline Validation

GitHub Actions workflows include Git status checks:
- **python-package.yml**: Comprehensive CI with Git workflow validation
- **railway-deployment.yml**: Deployment-specific Git checks
- **dependency-validation.yml**: Dependency synchronization validation

### 3. Manual Validation Scripts

#### Quick Git Status Check

```bash
npm run check:git
# or
./scripts/git-status-check.sh
```

#### Comprehensive Workflow Validation

```bash
npm run check:git-workflow
# or
./scripts/validate-git-workflow.sh
```

## 📋 Standard Release Process

### 1. Development Phase

```bash
# Make your changes
git add .
git commit -m "feat: add new feature"

# Pre-commit hooks automatically run validation
```

### 2. Pre-deployment Validation

```bash
# Run comprehensive checks
npm run check:comprehensive

# Validate Git workflow
npm run check:git-workflow

# Ensure all changes are committed
git status
```

### 3. Push to Remote

```bash
# Push to your feature branch
git push origin feature-branch

# Create PR or merge to main
# CI/CD will run additional validation
```

### 4. Deployment

- **Railway**: Automatic deployment on main branch push (after CI validation)
- **Manual**: Only after Git workflow validation passes

## 🚨 Common Issues and Solutions

### Issue: "Uncommitted changes detected"

**Root Cause**: Files were modified but not committed to Git.

**Solution**:

```bash
# Check what files are modified
git status

# Add and commit changes
git add .
git commit -m "fix: describe your changes"

# Push to remote
git push origin your-branch
```

### Issue: "Local branch ahead of remote"

**Root Cause**: Commits exist locally but haven't been pushed.

**Solution**:

```bash
# Push your commits
git push origin your-branch
```

### Issue: "Untracked files detected"

**Root Cause**: New files created but not added to Git.

**Solution**:

```bash
# Review untracked files
git status

# Add needed files
git add file1 file2

# Or add to .gitignore if not needed
echo "temp-file.log" >> .gitignore
```

## 🔍 Validation Levels

### Level 1: Pre-commit (Local)

- ✅ ESLint critical errors
- ✅ Python syntax (F821)
- ✅ Security vulnerabilities (critical)
- ✅ Basic tests

### Level 2: CI Pipeline

- ✅ All Level 1 checks
- ✅ Git workflow validation
- ✅ Comprehensive testing
- ✅ Security scanning
- ✅ Code coverage

### Level 3: Deployment

- ✅ All Level 1 & 2 checks
- ✅ Final Git status validation
- ✅ Environment-specific checks
- ✅ Health endpoint validation

## 📊 Available Commands

### Git-Specific Checks

```bash
npm run check:git              # Quick Git status check
npm run check:git-workflow     # Comprehensive Git validation
```

### Combined Validation

```bash
npm run check:all              # Standard quality checks + Git
npm run check:comprehensive    # Full validation including Git workflow
```

### Individual Components

```bash
npm run lint:clean             # ESLint errors only
npm run security               # Security audit
npm run test:run               # Run tests
npm run tsc:check              # TypeScript validation
```

## 🛡️ Prevention Mechanisms

### 1. Automated Checks

- Pre-commit hooks prevent commits with critical issues
- CI/CD blocks deployment if Git workflow violations exist
- Automatic validation on every push

### 2. Manual Validation

- Scripts available for developers to run locally
- Clear error messages with suggested fixes
- Integration with npm scripts for ease of use

### 3. Documentation

- Clear workflow documentation
- Common issues and solutions
- Step-by-step release process

## 🔄 Continuous Improvement

The Git workflow system is designed to evolve:

1. **Monitor**: Track workflow violations and common issues
2. **Improve**: Enhance validation scripts based on real-world usage
3. **Document**: Update documentation with new edge cases
4. **Automate**: Add more automation to reduce manual errors

## 🚀 Quick Start for New Contributors

1. **Clone the repository**:

   ```bash
   git clone https://github.com/GaryOcean428/gary-zero.git
   cd gary-zero
   ```

2. **Install dependencies**:

   ```bash
   npm install
   ```

3. **Run validation**:

   ```bash
   npm run check:git-workflow
   ```

4. **Make changes and commit**:

   ```bash
   # Edit files
   git add .
   git commit -m "your message"  # Pre-commit hooks run automatically
   git push origin your-branch
   ```

5. **Before deployment**:

   ```bash
   npm run check:comprehensive
   ```

## 📞 Support

If you encounter issues with the Git workflow:

1. Check this documentation for common solutions
2. Run `npm run check:git-workflow` for detailed diagnostics
3. Review the CI/CD logs for specific error messages
4. Ensure all dependencies are installed: `npm install`

## 🔗 Related Files

- `.husky/pre-commit` - Pre-commit hook configuration
- `.github/workflows/` - CI/CD pipeline definitions
- `scripts/git-status-check.sh` - Quick Git status validation
- `scripts/validate-git-workflow.sh` - Comprehensive Git workflow validation
- `package.json` - npm scripts for validation commands
