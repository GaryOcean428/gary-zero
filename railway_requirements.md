# Railway Requirements Knowledge Base

## 1. Workflow Analysis & Job Mapping

### GitHub Workflows Overview

Based on analysis of `.github/workflows/`, the project has 3 workflow files with the following job mapping:

#### Dependency Validation (`dependency-validation.yml`)

- **Job**: `validate-dependencies`
  - **Purpose**: Validate Python dependencies sync between requirements.in and requirements.txt
  - **Triggers**: Push/PR changes to requirements files
  - **Duplicated Logic**: Python setup, dependency installation patterns (repeated across workflows)

#### Python Package (`python-package.yml`) - Comprehensive CI/CD

- **Job**: `git-workflow-check`
  - **Purpose**: Git workflow validation and commit history checks
  - **Duplicated Logic**: Git checkout with fetch-depth (shared with railway-deployment)
  
- **Job**: `code-quality`
  - **Purpose**: Code quality, security scanning (ruff, mypy, bandit, safety)
  - **Duplicated Logic**: Python setup, dependency installation
  
- **Job**: `python-tests` (Matrix: unit, integration, performance)
  - **Purpose**: Parallel test execution with coverage reporting
  - **Duplicated Logic**: Python setup, dependency installation, environment variables
  
- **Job**: `e2e-tests`
  - **Purpose**: End-to-end testing with Playwright
  - **Duplicated Logic**: Python + Node.js setup patterns
  
- **Job**: `deployment-validation`
  - **Purpose**: Port configuration, Docker build, health check simulation
  - **Duplicated Logic**: Port binding tests, Docker build verification
  
- **Job**: `coverage-report`, `performance-analysis`
  - **Purpose**: Coverage consolidation and performance analysis
  - **Duplicated Logic**: Artifact handling patterns

#### Railway Deployment (`railway-deployment.yml`)

- **Job**: `git-workflow-check`
  - **Purpose**: Git validation for deployment (EXACT DUPLICATE of python-package.yml)
  - **Duplicated Logic**: Complete duplication - should be consolidated
  
- **Job**: `test`
  - **Purpose**: Railway-specific testing (linting, build scripts, port config)
  - **Duplicated Logic**: Python setup, port binding tests, script validation
  
- **Job**: `docker-test`
  - **Purpose**: Docker build testing and health endpoint validation
  - **Duplicated Logic**: Docker build patterns
  
- **Job**: `railway-validation`
  - **Purpose**: Railway configuration validation (railway.toml, scripts)
  - **Duplicated Logic**: File existence checks, configuration validation
  
- **Job**: `security-scan`
  - **Purpose**: Security audit with safety tool
  - **Duplicated Logic**: Security scanning patterns (overlaps with code-quality)

### Key Duplication Issues Identified

1. **Git workflow validation**: Exact duplication between workflows
2. **Python environment setup**: Repeated across all workflows
3. **Port configuration testing**: Multiple implementations
4. **Docker build validation**: Similar patterns across jobs
5. **Security scanning**: Overlapping tools (bandit vs safety)

## 2. Railway Configuration Schema Analysis

### Current File Structure

- ✅ **`railpack.json`**: Present (Railpack configuration)
- ❌ **`railway.toml`**: MISSING (should be primary Railway config)
- ✅ **`Dockerfile`**: Present (multi-stage build)
- ✅ **Start scripts**: `start_uvicorn.py`, `scripts/start.sh`
- ✅ **Build scripts**: `scripts/build.sh`

### Railpack.json Schema Fields (Current)

```json
{
  "platform": {
    "os": "linux",
    "arch": "amd64"
  },
  "runtime": {
    "name": "python", 
    "version": "3.13",
    "package_manager": "uv"
  },
  "build": {
    "steps": [...],
    "cache": {...}
  },
  "deploy": {
    "start_command": "python start_uvicorn.py",
    "health_check": {
      "path": "/health",
      "timeout": 30
    },
    "environment": {...}
  },
  "volumes": [...]
}
```

### Required Railway Reference Variables Found

- ✅ `PORT`: Properly used in main.py, start scripts
- ✅ `RAILWAY_ENVIRONMENT`: Used for environment detection
- ❌ `RAILWAY_PUBLIC_DOMAIN`: Referenced in CORS but missing railway.toml
- ❌ `RAILWAY_PRIVATE_DOMAIN`: Referenced in patterns but no config
- ❌ `RAILWAY_STATIC_OUTBOUND_IPS`: Not configured
- ❌ Railway service-to-service variables: Not configured

## 3. Mandatory Railway Configuration Requirements

### Required Files

1. **`railway.toml`** (PRIMARY - MISSING)
   - Should replace or complement railpack.json
   - Service definitions, build/start commands
   - Environment variables and secrets
   - Health check configuration

2. **`railpack.json`** (Optional, currently present)
   - Platform-specific build configuration
   - Caching and optimization settings

3. **`Dockerfile`** (Optional, present)
   - Multi-stage build configuration
   - Runtime dependencies

### Port Binding & Host Rules (✅ COMPLIANT)

- **Host**: `0.0.0.0` (correctly configured in main.py, start scripts)
- **Port**: Dynamic `$PORT` environment variable (properly resolved)
- **Implementation**:

  ```python
  port = int(os.getenv("PORT", 8000))
  host = os.getenv("WEB_UI_HOST", "0.0.0.0")
  ```

### Health Check Configuration (✅ COMPLIANT)

- **Endpoint**: `/health` (implemented in main.py)
- **Timeout**: 30 seconds (configured in railpack.json)
- **Response**: JSON with status, timestamp, system metrics
- **CORS**: Properly configured for preflight requests

## 4. Service-to-Service URL Conventions

### Current CORS Configuration

```python
allowed_origins = [
    f"https://{os.getenv('RAILWAY_PUBLIC_DOMAIN')}" if os.getenv('RAILWAY_PUBLIC_DOMAIN') else None,
    os.getenv("FRONTEND_URL", "*"),
    "http://localhost:3000",
    "http://localhost:5173",
]
```

### Missing Service Communication Patterns

- **Internal Service URLs**: Should use `${{service.RAILWAY_PRIVATE_DOMAIN}}`
- **Database Connection**: Should use Railway internal hostnames
- **Inter-service Communication**: Missing Railway-specific networking config

### Secret Handling (⚠️ NEEDS IMPROVEMENT)

- **Current**: Basic environment variables
- **Missing**: Railway secrets integration
- **Required**: Use Railway's secret management for API keys, database credentials

## 5. Configuration Gaps & Issues

### Critical Gaps

1. **Missing `railway.toml`**: Primary Railway configuration file absent
2. **Service Discovery**: No Railway service-to-service configuration
3. **Database Integration**: Missing Railway database variable patterns
4. **Secrets Management**: Not using Railway secrets API
5. **Environment Separation**: Limited environment-specific configuration

### Current vs Required Railway Spec

| Component | Current Status | Railway Requirement | Gap |
|-----------|---------------|-------------------|-----|
| Config File | `railpack.json` only | `railway.toml` primary | ❌ Missing railway.toml |
| Port Binding | ✅ `0.0.0.0:$PORT` | `0.0.0.0:$PORT` | ✅ Compliant |
| Health Check | ✅ `/health` endpoint | `/health` or custom | ✅ Compliant |
| Start Command | ✅ `python start_uvicorn.py` | Configurable | ✅ Compliant |
| Build Command | ✅ `scripts/build.sh` | Configurable | ✅ Compliant |
| Environment Variables | ⚠️ Basic support | Railway variables | ⚠️ Partial |
| Service Discovery | ❌ None | Railway internal DNS | ❌ Missing |
| Secrets | ❌ Basic env vars | Railway secrets | ❌ Missing |
| Volumes | ✅ `/app/data` | Railway volumes | ✅ Configured |

### Environment Variable Analysis

- **Found in Code**: `PORT`, `RAILWAY_ENVIRONMENT`, `RAILWAY_PUBLIC_DOMAIN`
- **Referenced but Not Configured**: `RAILWAY_PRIVATE_DOMAIN`, service-specific variables
- **Missing Railway Patterns**: `${{service.VARIABLE}}`, `${{secrets.NAME}}`

## 6. Recommended Actions

### Immediate Priorities

1. **Create `railway.toml`**: Primary Railway configuration
2. **Service Discovery**: Configure inter-service communication
3. **Secrets Management**: Integrate Railway secrets API
4. **Consolidate Workflows**: Eliminate duplicate job logic
5. **Database Integration**: Add Railway database variable patterns

### Railway.toml Template Needed

```toml
[services.gary-zero]
build = { builder = "NIXPACKS" }
buildCommand = "scripts/build.sh"
startCommand = "python start_uvicorn.py"
healthcheckPath = "/health"
healthcheckTimeout = 30

[services.gary-zero.env]
PORT = { default = 8000 }
PYTHONUNBUFFERED = 1
RAILWAY_ENVIRONMENT = "$RAILWAY_ENVIRONMENT"

[services.gary-zero.volumes]
data = { mountPath = "/app/data" }
```

This knowledge base provides a comprehensive analysis of the current state versus Railway requirements, identifying critical gaps that need to be addressed for proper Railway deployment.
