# Gary-Zero Startup Troubleshooting Guide

This document provides solutions for common startup issues encountered with the Gary-Zero application.

## 🔧 Restart Loop Fix (Issue #296)

### Problem Description
The application was experiencing restart loops during Railway deployment with the error:
```
bash: scripts/start.sh: No such file or directory
```

### Root Cause
The issue was **not** a missing `scripts/start.sh` file, but rather overly strict configuration validation that required the `WEB_UI_HOST` environment variable to be explicitly set, even though it has a sensible default.

### Solution Applied
Fixed the configuration validation in `framework/helpers/config_loader.py`:
```python
# Before (causing failures):
required_vars = ["PORT", "WEB_UI_HOST"]

# After (fixed):
required_vars = ["PORT"]  # WEB_UI_HOST has a default, not strictly required
```

### Verification
The fix has been validated with comprehensive tests:
- ✅ Configuration validation passes
- ✅ Application starts successfully
- ✅ Health endpoint responds correctly
- ✅ All startup scripts work properly

## 🚀 Deployment Modes

Gary-Zero supports two deployment modes:

### 1. Docker Container Mode
- Uses: `docker-entrypoint.sh` → gunicorn
- Configuration: Dockerfile `ENTRYPOINT ["/app/docker-entrypoint.sh"]`
- Port handling: Gunicorn with PORT environment variable

### 2. Railway Platform Mode
- Uses: `scripts/start.sh` → `start_uvicorn.py` → uvicorn
- Configuration: `railpack.json` with `"startCommand": "bash scripts/start.sh"`
- Port handling: Uvicorn with Railway-compatible PORT resolution

## 🧪 Testing Your Deployment

Run the validation script to ensure your environment is properly configured:

```bash
python test_startup_fix.py
```

This will test:
- Import functionality
- Configuration validation
- Startup script integrity
- Uvicorn startup process
- Health endpoint accessibility

## 🔍 Common Issues and Solutions

### Issue: Configuration validation fails
**Symptoms:**
```
❌ Required environment variable WEB_UI_HOST is not set
❌ Configuration validation failed
```

**Solution:**
- Ensure you're using the latest version with the configuration fix
- Set `WEB_UI_HOST=0.0.0.0` explicitly if needed
- Check that `railpack.json` includes `"WEB_UI_HOST": "0.0.0.0"`

### Issue: ModuleNotFoundError during startup
**Symptoms:**
```
ModuleNotFoundError: No module named 'uvicorn'
ModuleNotFoundError: No module named 'git'
```

**Solution:**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- For development: `pip install uvicorn fastapi GitPython psutil python-dotenv webcolors`

### Issue: Health check timeout
**Symptoms:**
```
Health check timeout after 300 seconds
Service unavailable
```

**Solution:**
- Verify the health endpoint is accessible: `curl http://localhost:8000/health`
- Check that the PORT environment variable is set correctly
- Ensure no firewall issues blocking the port

## 🌐 Environment Variables

### Required Variables
- `PORT`: Application port (default: 8000)

### Optional Variables (with defaults)
- `WEB_UI_HOST`: Host binding (default: 0.0.0.0)
- `RAILWAY_ENVIRONMENT`: Deployment environment
- `NODE_ENV`: Node environment (default: production)
- `PYTHONUNBUFFERED`: Python output buffering (default: 1)

### Railway-Specific Variables
These are automatically provided by Railway:
- `DATABASE_URL`: PostgreSQL connection
- `REDIS_URL`: Redis connection

## 📞 Support

If you continue to experience issues:

1. Run the diagnostic test: `python test_startup_fix.py`
2. Check application logs for specific error messages
3. Verify environment variables are set correctly
4. Ensure all dependencies are installed

The startup process should complete with:
```
✅ Configuration validation passed
🚀 Starting uvicorn on 0.0.0.0:8000
INFO: Application startup complete.
✅ Service is healthy
```