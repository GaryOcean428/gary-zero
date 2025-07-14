# Railway Deployment Fix - Issue #58

## Problem Summary

Railway deployment was failing with the error:
```
run_ui.py: error: argument --port: invalid int value: '$PORT'
```

**Root Cause**: Railway was passing the literal string `'$PORT'` instead of expanding the environment variable to its integer value.

## Solution Implemented

### 1. Port Argument Parsing Fix

Modified `framework/helpers/runtime.py` to handle Railway's literal `$PORT` string:

```python
def _parse_port_arg(value: str) -> int | None:
    """Parse port argument, handling Railway's literal '$PORT' string case."""
    # Handle Railway's literal '$PORT' string case
    if value == "$PORT":
        port_from_env = dotenv.get_dotenv_value("PORT")
        if port_from_env:
            try:
                return int(port_from_env)
            except ValueError:
                pass
        return None
    
    # Handle normal integer case
    try:
        return int(value)
    except ValueError:
        return None
```

### 2. Environment Variable Priority Fix

Fixed the priority order in `get_web_ui_port()`:
- CLI argument (`--port`)
- `PORT` environment variable (Railway standard)
- `WEB_UI_PORT` environment variable (application specific)
- Default port (5000)

### 3. Railway Configuration Updates

**railway.toml**:
```toml
[deploy]
startCommand = "python run_ui.py --port $PORT --host 0.0.0.0 --dockerized"
healthcheckPath = "/health"
```

**railway.json** (added):
```json
{
  "build": {
    "builder": "nixpacks"
  },
  "deploy": {
    "startCommand": "python run_ui.py --port $PORT --host 0.0.0.0 --dockerized",
    "healthcheckPath": "/health"
  }
}
```

## Testing Results

✅ **All tests passed** - 25+ test scenarios covering:
- Railway's literal `$PORT` string handling
- Normal integer port arguments
- Environment variable priority
- Edge cases and error handling
- Health endpoint functionality
- Backwards compatibility

## Deployment Commands

```bash
# Deploy to Railway
railway deploy

# Monitor deployment
railway logs --follow

# Check service status
railway status

# Verify environment variables
railway variables list
```

## Health Check

The application provides a health endpoint at `/health` that returns:
```json
{
  "status": "healthy",
  "timestamp": 1234567890.123,
  "version": "1.0.0"
}
```

## Environment Variables

Required for Railway deployment:
- `PORT` - Set automatically by Railway
- `WEB_UI_HOST` - Set to "0.0.0.0" in railway.toml

Optional:
- `WEB_UI_PORT` - Fallback if PORT not set
- `PYTHONUNBUFFERED` - Set to "1" for proper logging

## Troubleshooting

If you encounter issues:

1. **Check environment variables**:
   ```bash
   railway variables list
   ```

2. **Verify the PORT variable is set**:
   ```bash
   railway variables set PORT=8080
   ```

3. **Check deployment logs**:
   ```bash
   railway logs --follow
   ```

4. **Test locally**:
   ```bash
   PORT=8080 python run_ui.py --port '$PORT' --host 0.0.0.0
   ```

## Technical Details

- **Affected Files**: `framework/helpers/runtime.py`, `railway.toml`, `railway.json`
- **Backwards Compatible**: Yes, existing setups continue to work
- **Performance Impact**: Minimal, only affects argument parsing
- **Security**: No security implications

The fix ensures Railway deployments work correctly while maintaining full backwards compatibility with existing configurations.