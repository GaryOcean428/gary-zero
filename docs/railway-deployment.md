# Railway Deployment Guide

This document provides comprehensive guidance for deploying Gary Zero to Railway.

## Overview

Gary Zero is configured for Railway deployment using the `railway.toml` configuration file in the project root.

## Prerequisites

1. [Railway CLI](https://docs.railway.app/develop/cli) installed
2. Railway account and project created
3. Node.js >=22.0.0 environment (specified in package.json)
4. Python 3.9+ environment (specified in pyproject.toml)

## Configuration

### Railway Configuration (`railway.toml`)

The project includes a pre-configured `railway.toml` file with the following settings:

```toml
[build]
builder = "NIXPACKS"
buildCommand = "npm install && pip install -r requirements.txt"

[deploy]
startCommand = "python run_ui.py --port $PORT"
healthcheckPath = "/"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

[[services]]
name = "gary-zero"

[services.source]
repo = "GaryOcean428/gary-zero"
branch = "main"

[services.variables]
NODE_ENV = "production"
WEB_UI_HOST = "0.0.0.0"
PYTHONUNBUFFERED = "1"
```

### Environment Variables

Based on `.env.example`, you'll need to configure the following environment variables in Railway:

#### Required Database Configuration
- `POSTGRES_URL`
- `POSTGRES_PRISMA_URL`
- `POSTGRES_URL_NON_POOLING`
- `DATABASE_URL`

#### Required API Keys
- `OPENAI_API_KEY` (if using OpenAI models)
- `ANTHROPIC_API_KEY` (if using Anthropic models)
- `GOOGLE_API_KEY` (if using Google/Gemini models)

#### Optional but Recommended
- `JWT_SECRET`
- `ENCRYPTION_KEY`
- `SESSION_SECRET`
- `AUTH_LOGIN`
- `AUTH_PASSWORD`

## Deployment Steps

### 1. Initial Setup

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize in your project directory
cd /path/to/gary-zero
railway init
```

### 2. Environment Configuration

```bash
# Set environment variables
railway variables set NODE_ENV=production
railway variables set PYTHONUNBUFFERED=1

# Set your API keys (replace with actual values)
railway variables set OPENAI_API_KEY=your-key-here
railway variables set ANTHROPIC_API_KEY=your-key-here

# Set database URL (if using Railway PostgreSQL)
railway variables set DATABASE_URL=your-postgres-url
```

### 3. Deploy

```bash
# Deploy to Railway
railway up
```

## Build Process

Railway will automatically:

1. **Build Phase**: Run `npm install && pip install -r requirements.txt`
2. **Deploy Phase**: Start the application with `python run_ui.py --port $PORT`

## Health Checks

- **Health Check Path**: `/`
- **Timeout**: 300 seconds
- **Restart Policy**: On failure with max 10 retries

## Port Configuration

- Railway automatically provides a `$PORT` environment variable
- The application is configured to bind to `0.0.0.0:$PORT` via the startCommand
- The application's port resolution logic automatically uses Railway's `$PORT` variable
- No additional `WEB_UI_PORT` configuration is needed in railway.toml
- Default fallback port is 5000 (defined in application code)

## Monitoring

Monitor your deployment:

```bash
# View logs
railway logs

# Check service status
railway status

# View environment variables
railway variables
```

## Troubleshooting

### Common Issues

1. **Node.js Version Mismatch**
   - Ensure your Railway environment supports Node.js >=22.0.0
   - Check build logs for version conflicts

2. **Python Dependencies**
   - Verify all requirements.txt dependencies are installable
   - Check for platform-specific package issues

3. **Environment Variables**
   - Ensure all required API keys are set
   - Verify database connection strings

4. **Port Binding**
   - Application must bind to `0.0.0.0:$PORT`
   - Don't hardcode port numbers

### Debug Commands

```bash
# View deployment logs
railway logs --follow

# Check build logs
railway logs --deployment

# Test environment variables
railway shell
echo $PORT
echo $NODE_ENV
```

## Additional Resources

- [Railway Documentation](https://docs.railway.app/)
- [Railway Environment Variables](https://docs.railway.app/develop/variables)
- [Railway Deployment Guide](https://docs.railway.app/deploy/railway-up)

## Security Considerations

1. Never commit API keys or secrets to version control
2. Use Railway's environment variables for all sensitive data
3. Enable appropriate authentication (AUTH_LOGIN/AUTH_PASSWORD)
4. Consider using Railway's private networking for database connections

## Performance Optimization

1. Use Railway's built-in PostgreSQL for optimal database performance
2. Configure appropriate restart policies for high availability
3. Monitor resource usage through Railway dashboard
4. Consider enabling Railway's autoscaling features for production workloads