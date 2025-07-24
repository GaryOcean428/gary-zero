# Gary-Zero CI/CD Deployment Guide


## 🚀 Quick Start

The new CI/CD architecture is now fully implemented with 4 reusable composite workflows. Here's how to use it:

### Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Secrets**: Configure the following secrets in your repository:

   ```
   RAILWAY_TOKEN=your_railway_api_token
   DOCKER_USERNAME=your_docker_hub_username (optional)
   DOCKER_PASSWORD=your_docker_hub_password (optional)
   CODECOV_TOKEN=your_codecov_token (optional)
   ```

### Development Workflow

1. **Feature Development**:

   ```bash
   git checkout -b feature/my-new-feature
   git push origin feature/my-new-feature
   ```

   - Triggers: Static checks + Tests (workflows A + B)
   - Duration: ~10-15 minutes
   - Coverage threshold: 75%

2. **Pull Request**:
   - Creates PR to main branch
   - Same checks as feature branch
   - Automated PR comment with results

3. **Main Branch Deployment**:

   ```bash
   git checkout main
   git merge feature/my-new-feature
   git push origin main
   ```

   - Triggers: Full CI/CD pipeline (workflows A + B + C + D)
   - Duration: ~25-35 minutes
   - Coverage threshold: 80%
   - Automatic deployment to Railway

### Manual Deployment

Use workflow dispatch for manual deployments:

1. Go to GitHub Actions tab
2. Select "Main Branch CI/CD" workflow
3. Click "Run workflow"
4. Configure options:
   - Skip security audit (optional)
   - Skip deployment (optional)
   - Choose environment (production/staging)


## 🧩 Composite Workflows Overview

### A. Static Checks (`_static-checks.yml`)

**Tools**: Ruff, Black, MyPy, ESLint, Prettier, TypeScript, detect-secrets

```yaml
uses: ./.github/workflows/_static-checks.yml
with:
  python-version: "3.13"
  node-version: "22"
  skip-secret-scan: false
```

### B. Tests (`_tests.yml`)

**Coverage**: Unit, Integration, E2E, Performance, Coverage merge

```yaml
uses: ./.github/workflows/_tests.yml
with:
  python-version: "3.13"
  node-version: "22"
  coverage-threshold: 75
  skip-e2e: false
```

### C. Security Audit (`_security-audit.yml`)

**Tools**: Bandit, Safety, npm audit, Trivy, OSSF Scorecard

```yaml
uses: ./.github/workflows/_security-audit.yml
with:
  python-version: "3.13"
  node-version: "22"
  fail-on-security-issues: true
  ossf-scorecard: true
```

### D. Deploy (`_deploy.yml`)

**Process**: Railway validation, Docker build, CLI deployment

```yaml
uses: ./.github/workflows/_deploy.yml
with:
  environment: "production"
  docker-tag: "latest"
  skip-docker: false
secrets:
  RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
  DOCKER_USERNAME: ${{ secrets.DOCKER_USERNAME }}
  DOCKER_PASSWORD: ${{ secrets.DOCKER_PASSWORD }}
```


## 🚪 Quality Gate

The quality gate ensures all checks pass before deployment:

- ✅ Static checks must pass
- ✅ Tests must pass with minimum coverage
- ✅ Security audit must pass (or be explicitly skipped)
- ✅ All validations complete successfully

If any check fails, deployment is blocked until issues are resolved.


## 🚂 Railway Configuration

The `railway.toml` file is configured following Railway best practices:

```toml
[build]
builder = "NIXPACKS"
buildCommand = "bash scripts/build.sh"

[deploy]
startCommand = "bash scripts/start.sh"
healthcheckPath = "/health"

[environment]
PORT = { default = "8000" }
WEB_UI_HOST = { default = "0.0.0.0" }
```

### Port Configuration ✅

- Uses `process.env.PORT` in application
- Binds to `0.0.0.0` for Railway compatibility
- Health endpoint at `/health`


## 📊 Monitoring & Reporting

### GitHub Integration

- **Status Checks**: Required for branch protection
- **PR Comments**: Automated result summaries
- **Security Alerts**: SARIF integration
- **Releases**: Automatic creation on successful deployment

### Artifacts & Reports

- **Coverage Reports**: Combined XML uploaded to Codecov
- **Security Reports**: JSON artifacts with detailed findings
- **Performance Metrics**: Benchmark results
- **Deployment Logs**: Complete audit trail


## 🔧 Troubleshooting

### Common Issues

1. **Build Failures**:
   - Check Python/Node.js version compatibility
   - Verify requirements.txt is up to date
   - Review build logs in GitHub Actions

2. **Test Failures**:
   - Run tests locally: `pytest tests/`
   - Check coverage: `pytest --cov=framework`
   - Review test matrix configuration

3. **Security Issues**:
   - Review Bandit report for Python issues
   - Check npm audit for Node.js vulnerabilities
   - Update dependencies as needed

4. **Deploy Failures**:
   - Verify Railway token is valid
   - Check railway.toml configuration
   - Ensure health endpoint returns 200

### Local Testing

Test the deployment process locally:

```bash
# Test build script
bash scripts/build.sh

# Test start script
bash scripts/start.sh

# Test health endpoint
curl http://localhost:8000/health
```


## 🎯 Next Steps

1. **Configure Secrets**: Add required secrets to GitHub repository
2. **Test Pipeline**: Create a test branch and push changes
3. **Monitor Deployment**: Watch the Railway deployment process
4. **Set Branch Protection**: Require status checks before merge

The CI/CD architecture is now fully implemented and ready for production use! 🚀
