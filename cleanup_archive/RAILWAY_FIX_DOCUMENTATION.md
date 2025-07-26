# Railway Deployment Fix - Complete Solution

## Problem Summary

Railway deployment had multiple issues:
1. Environment variables not properly resolved (literal `$PORT` strings)
2. UI template placeholders not being substituted (`{{version_no}}`, `{{version_time}}`, `{{feature_flags_config}}`)
3. Inconsistent startup commands across configuration files
4. No validation of configuration during deployment

## Solution Implemented

### 1. Unified Configuration Management

**New file**: `framework/helpers/config_loader.py`
- Centralized environment variable handling with Railway-specific logic
- Resolves literal `$PORT` strings and Railway placeholders like `${{service.VARIABLE}}`
- Provides sane defaults for missing variables
- Validates configuration and warns about unresolved placeholders

**New file**: `framework/helpers/template_helper.py`
- Consistent HTML template rendering across all entry points
- Ensures placeholders are substituted regardless of startup method
- Validates rendered content to prevent placeholder leakage

### 2. Template Substitution Fix

**Problem**: Template placeholders were only replaced when using Flask's `run_ui.py` route, but Railway might use other entry points.

**Solution**:
- Updated `run_ui.py`, `main.py` (FastAPI), and `start_uvicorn.py` to use unified template helper
- All entry points now properly substitute `{{version_no}}`, `{{version_time}}`, and `{{feature_flags_config}}`
- Added validation to detect and prevent placeholder leakage

### 3. Configuration File Consistency

**Files updated**:
- `railway.toml`: Uses `python start_uvicorn.py`, removed Railway placeholder variables that don't resolve
- `nixpacks.toml`: Consistent startup command
- `Procfile`: Consistent startup command
- `start_uvicorn.py`: Enhanced with configuration validation and template checking

**Environment Variables**: Simplified Railway configuration:

```toml
[services.variables]
WEB_UI_HOST = "0.0.0.0"
PYTHONUNBUFFERED = "1"
RAILWAY_ENVIRONMENT = "production"
NIXPACKS_PYTHON_VERSION = "3.13"

# Feature flags for Railway deployment
ENABLE_DEV_FEATURES = "false"
VSCODE_INTEGRATION_ENABLED = "false"
CHAT_AUTO_RESIZE_ENABLED = "true"

# Simplified service URLs (no Railway placeholders)
SEARXNG_URL = "http://searchxng:8080"
KALI_SHELL_URL = "http://kali-linux-docker:22"
SEARCH_PROVIDER = "searxng"
```

### 4. Startup Validation

**Enhanced file**: `startup_validation.py`
- Validates configuration during application startup
- Checks template rendering works correctly
- Verifies environment variables are properly set
- Validates Railway configuration consistency
- Provides detailed error reporting

**Integration**: `start_uvicorn.py` runs quick validation checks during startup.

## Required Environment Variables

### Critical Variables (Railway manages these automatically)

- `PORT` - Application port (Railway sets this automatically)
- `WEB_UI_HOST` - Host to bind to (set to "0.0.0.0" in railway.toml)

### Optional Variables (can be set in Railway dashboard)

- `E2B_API_KEY` - For secure code execution (set as Railway secret)
- `SEARXNG_URL` - Search service URL (defaults to internal service)
- `SEARCH_PROVIDER` - Search provider type (defaults to "searxng")

### Feature Flag Variables (set in railway.toml)

- `ENABLE_DEV_FEATURES` - Enable development features (default: "false")
- `VSCODE_INTEGRATION_ENABLED` - VSCode integration (default: "false")
- `CHAT_AUTO_RESIZE_ENABLED` - Auto-resize chat (default: "true")

## Testing Results

✅ **All tests passed** - Updated test suites covering:
- Configuration loader with Railway placeholder handling
- Template rendering with placeholder substitution
- Environment variable validation
- Configuration file consistency
- Template placeholder detection and resolution

## Deployment Commands

```bash
# Deploy to Railway
railway deploy

# Monitor deployment with detailed logs
railway logs --follow

# Check service status
railway status

# Verify environment variables
railway variables list

# Run startup validation locally
python startup_validation.py

# Test Railway deployment configuration
python test_railway_deployment.py
```

## Health Check

The application provides health endpoints:

**`/health`** - Detailed health information:

```json
{
  "status": "healthy",
  "timestamp": 1234567890.123,
  "version": "1.0.0",
  "memory_percent": 45.2,
  "uptime_seconds": 120.5,
  "server": "uvicorn"
}
```

**`/ready`** - Simple readiness check for Railway

## Template Variables

The following placeholders are automatically substituted in HTML templates:

- `{{version_no}}` - Git version (e.g., "C df99450")
- `{{version_time}}` - Build timestamp (e.g., "25-07-22 14:49")
- `{{feature_flags_config}}` - JavaScript configuration for feature flags

Example usage in HTML:

```html
<span>Version {{version_no}} {{version_time}}</span>
{{feature_flags_config}}
```

## Troubleshooting

### Template Placeholders Still Visible

If you see raw placeholders like `{{version_no}}` in the UI:
1. Check startup logs for template rendering errors
2. Run `python startup_validation.py` to validate configuration
3. Verify all entry points use the template helper

### Environment Variable Issues

If environment variables contain placeholders like `${{service.VAR}}`:
1. Check Railway service configuration
2. Use simplified variable names instead of Railway placeholders
3. Set variables directly in Railway dashboard

### Port Resolution Problems

If you see "PORT environment variable not properly resolved":
1. Railway should set PORT automatically
2. The application will fallback to port 8000
3. Check Railway deployment logs for PORT setting

### Startup Validation Failures

Run diagnostic commands:

```bash
# Full validation
python startup_validation.py

# Quick deployment test
python test_railway_deployment.py

# Check configuration
python -c "from framework.helpers.config_loader import get_config_loader; get_config_loader().log_startup_config()"
```

## Technical Details

- **Backwards Compatible**: Existing deployments continue to work
- **Performance Impact**: Minimal, only affects startup and template rendering
- **Security**: No security implications, only configuration management
- **Dependencies**: Added python-dotenv and GitPython for environment and version handling

## Important Notes for Contributors

⚠️ **Critical**: Do not modify these variables in automated commits:
- `PORT`, `WEB_UI_HOST`, `NIXPACKS_PYTHON_VERSION`
- `SEARXNG_URL`, `SEARCH_PROVIDER`, `E2B_API_KEY`
- `KALI_SHELL_*` variables

These variables are essential for Railway deployment and must remain intact.
