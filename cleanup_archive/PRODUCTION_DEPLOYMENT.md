# Gary-Zero Production Deployment Guide

This document provides instructions for deploying the Gary-Zero fixes to production, addressing the critical LangChain Anthropic streaming bug and UI/UX improvements.

## Quick Start (Emergency Deployment)

For immediate production hotfix, set these environment variables:

```bash
# Railway CLI
railway variables set LANGCHAIN_ANTHROPIC_STREAM_USAGE=false
railway variables set ENABLE_DEV_FEATURES=false
railway variables set VSCODE_INTEGRATION_ENABLED=false

# Or via Railway Dashboard
LANGCHAIN_ANTHROPIC_STREAM_USAGE=false
ENABLE_DEV_FEATURES=false
VSCODE_INTEGRATION_ENABLED=false
```

## Issues Addressed

### 1. LangChain Anthropic Streaming Bug (Critical) ✅

- **Problem**: `TypeError: NoneType + int` errors in production conversations
- **Root Cause**: LangChain Anthropic streaming metadata bug (Issue #26348)
- **Solution**: Environment variable `LANGCHAIN_ANTHROPIC_STREAM_USAGE=false` to disable streaming usage metadata
- **Files Modified**: `models.py`, `.env.example`

### 2. Chat Input UX Limitations (High) ✅

- **Problem**: Fixed height chat input limiting user message composition
- **Solution**: Auto-expanding textarea with better constraints
- **Files Modified**: `webui/index.css`, `webui/js/chat-input-autoresize.js`, `webui/index.html`
- **Features**:
  - Auto-resize from 40px to 200px height
  - Manual vertical resize allowed
  - Smooth transitions and overflow handling

### 3. Development Features in Production (Medium) ✅

- **Problem**: VS Code integration consuming production resources
- **Solution**: Environment-based feature flags with production detection
- **Files Modified**: `webui/js/vscode-integration.js`, `run_ui.py`, `.env.example`
- **Features**:
  - Automatic production mode detection
  - Memory leak prevention
  - Clean feature flag system

### 4. Health Monitoring (Low) ✅

- **Enhancement**: Improved health check endpoint with environment status
- **Files Modified**: `run_ui.py`
- **New Scripts**: `validate_env.py`, `verify_fixes.py`

## Environment Variables

### Critical Production Variables

```bash
# LangChain Anthropic Fix (Critical)
LANGCHAIN_ANTHROPIC_STREAM_USAGE=false  # Disables streaming usage metadata

# Production Feature Flags (Recommended)
NODE_ENV=production
ENABLE_DEV_FEATURES=false               # Disables development features
VSCODE_INTEGRATION_ENABLED=false       # Disables VS Code integration
CHAT_AUTO_RESIZE_ENABLED=true          # Enables chat input auto-resize

# Web Server Configuration
WEB_UI_HOST=0.0.0.0                    # Allow external access
PORT=8000                              # Railway port (auto-set by Railway)
```

### Optional Configuration

```bash
# Authentication (Highly Recommended)
AUTH_LOGIN=admin
AUTH_PASSWORD=secure_password_here
API_KEY=your_secure_api_key

# Security
JWT_SECRET=your_32_character_jwt_secret_here
```

## Deployment Methods

### Method 1: Railway Dashboard (Recommended)

1. Go to your Gary-Zero project on Railway
2. Navigate to Variables tab
3. Add the environment variables listed above
4. Deploy the updated code

### Method 2: Railway CLI

```bash
# Set critical variables
railway variables set LANGCHAIN_ANTHROPIC_STREAM_USAGE=false
railway variables set NODE_ENV=production
railway variables set ENABLE_DEV_FEATURES=false
railway variables set VSCODE_INTEGRATION_ENABLED=false

# Deploy
railway up
```

### Method 3: Environment File

Create `.env` file in project root:

```bash
cp .env.example .env
# Edit .env with your values
```

## Verification Steps

### 1. Pre-Deployment Validation

```bash
# Validate environment configuration
python validate_env.py

# Verify all fixes are in place
python verify_fixes.py
```

### 2. Post-Deployment Health Check

```bash
# Check health endpoint
curl https://your-app.railway.app/health | jq

# Expected response includes:
# - "environment.langchain_stream_disabled": true
# - "environment.production_mode": true
# - "status": "healthy"
```

### 3. Monitor for Errors

```bash
# Railway logs monitoring
railway logs --tail 50 | grep -E "(TypeError|NoneType|streaming)"

# Should see no TypeErrors related to streaming
```

## Rollback Plan

If issues occur, immediately rollback:

```bash
# Revert critical variables
railway variables set LANGCHAIN_ANTHROPIC_STREAM_USAGE=true
railway variables set ENABLE_DEV_FEATURES=true
railway variables set VSCODE_INTEGRATION_ENABLED=true

# Monitor logs
railway logs --tail 20
```

## Success Metrics

### Critical Success Criteria

- ✅ Zero `TypeError: NoneType + int` errors in agent conversations
- ✅ Chat input auto-resizes for multi-line messages
- ✅ VS Code integration disabled in production
- ✅ Health check reports correct environment status

### Performance Indicators

- Memory usage stable (no message channel leaks)
- Faster page load times (reduced JS execution)
- Improved user experience with chat input
- No development console warnings in production

## Monitoring & Maintenance

### Regular Health Checks

```bash
# Automated health monitoring (add to cron/scheduler)
curl -f https://your-app.railway.app/health || alert "Gary-Zero health check failed"
```

### Log Monitoring Patterns

```bash
# Error patterns to monitor
grep -E "(TypeError.*NoneType|streaming.*metadata|failed.*conversation)" logs.txt

# Success patterns to verify
grep -E "(streaming.*disabled|production.*mode|auto-resize.*enabled)" logs.txt
```

### Environment Audit

```bash
# Run monthly environment validation
python validate_env.py > env-audit-$(date +%Y%m%d).log
```

## Troubleshooting

### LangChain Streaming Still Causing Errors

1. Verify `LANGCHAIN_ANTHROPIC_STREAM_USAGE=false` is set
2. Check health endpoint shows `langchain_stream_disabled: true`
3. Restart the application if needed

### Chat Input Not Auto-Resizing

1. Check browser console for JavaScript errors
2. Verify `CHAT_AUTO_RESIZE_ENABLED=true`
3. Clear browser cache and reload

### VS Code Integration Still Loading

1. Verify `VSCODE_INTEGRATION_ENABLED=false` is set
2. Check browser console for "VS Code integration disabled" message
3. Monitor memory usage for stability

### High Memory Usage

1. Check for message channel leaks in browser console
2. Verify production mode is active
3. Monitor VS Code integration is fully disabled

## Files Changed

### Backend Files

- `models.py` - LangChain Anthropic streaming fix
- `run_ui.py` - Health check enhancement and feature flag injection
- `.env.example` - New environment variables

### Frontend Files

- `webui/index.html` - Auto-resize script inclusion and feature flag placeholder
- `webui/index.css` - Chat input styling improvements
- `webui/js/chat-input-autoresize.js` - New auto-resize functionality
- `webui/js/vscode-integration.js` - Production mode detection and memory cleanup

### New Utilities

- `validate_env.py` - Environment validation script
- `verify_fixes.py` - Fix verification script
- `PRODUCTION_DEPLOYMENT.md` - This deployment guide

## Support

For deployment issues:
1. Check Railway logs: `railway logs`
2. Validate environment: `python validate_env.py`
3. Verify fixes: `python verify_fixes.py`
4. Monitor health: `curl /health`

Critical issues should be addressed by reverting to previous known-good environment variables while investigating.
