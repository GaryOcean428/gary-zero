# SearchXNG Integration Fix Summary

This document summarizes the code updates made to fix SearchXNG integration issues in Gary-Zero on Railway.

## Issues Identified

1. **Unresolved Reference Variables**: `SEARXNG_URL` contained unresolved Railway reference variables (`${{searchxng.PORT}}`)
2. **405 Method Not Allowed**: Health check endpoints were receiving incorrect HTTP methods
3. **Missing Diagnostics**: No easy way to test SearchXNG connectivity from deployed application

## Code Updates Made

### 1. Enhanced Validation Script

**File**: `scripts/validate_integrations.py`
- Added detection for unresolved reference variables
- Improved error messages with helpful hints
- Added Railway environment context checking
- Better SearchXNG connectivity testing

### 2. Fixed WSGI Emergency Endpoints

**File**: `wsgi.py`
- Added explicit `methods=['GET']` to emergency health and ready endpoints
- Prevents 405 errors during startup failures

### 3. Added Diagnostics API

**File**: `framework/api/diagnostics.py` (NEW)
- New API endpoint for testing integrations
- Tests SearchXNG connectivity with detailed results
- Shows relevant environment variables (with sensitive data masked)
- Accessible at `/diagnostics` with authentication

### 4. Improved SearchXNG Tool

**File**: `framework/tools/searchxng.py`
- Better fallback handling for Railway deployments
- Automatically tries `http://searchxng.railway.internal:8080` if reference variables fail
- Improved error messages with connection hints
- Logs the actual URL being used

### 5. Added Test Scripts

**Files**:
- `scripts/test_searchxng.py` - Standalone SearchXNG connectivity test
- `scripts/health_check.sh` - Quick health check for deployed services

### 6. Updated Configuration

**File**: `railway.json`
- Added `healthcheckMethod: "GET"`
- Added `healthcheckTimeout: 30`
- Added proper restart policies
- Set execution mode environment variables

### 7. Documentation

**File**: `docs/SEARCHXNG_INTEGRATION.md` (NEW)
- Complete setup guide for SearchXNG on Railway
- Troubleshooting common issues
- Manual configuration options
- Verification steps

## Environment Variables Required

### On SearchXNG Service

```bash
PORT=8080  # Required for reference variables to work
```

### On Gary-Zero Service

```bash
# Automatic (via railway.toml):
SEARXNG_URL=http://${{searchxng.RAILWAY_PRIVATE_DOMAIN}}:${{searchxng.PORT}}

# OR Manual fallback:
SEARXNG_URL=http://searchxng.railway.internal:8080

# Search provider
SEARCH_PROVIDER=searxng
```

## Testing

1. **Run validation script**:

   ```bash
   python scripts/validate_integrations.py
   ```

2. **Test SearchXNG directly**:

   ```bash
   python scripts/test_searchxng.py
   ```

3. **Check health endpoints**:

   ```bash
   ./scripts/health_check.sh https://your-gary-zero-url
   ```

4. **Use diagnostics endpoint**:

   ```
   POST /diagnostics
   {"test": "searchxng"}
   ```

## Next Steps

1. Ensure SearchXNG service has `PORT=8080` environment variable
2. Redeploy both services to pick up latest changes
3. Verify connectivity using the test scripts
4. Monitor logs for any remaining issues

## Troubleshooting

If issues persist after these updates:

1. **Check service names**: Must be exactly `searchxng` (case-sensitive)
2. **Verify same environment**: Both services in same Railway environment
3. **Check logs**: Look for SearchXNG URL being logged on startup
4. **Use manual URL**: Set `SEARXNG_URL=http://searchxng.railway.internal:8080` directly

The code is now more robust and will handle Railway's reference variable system better, with proper fallbacks and helpful error messages.
