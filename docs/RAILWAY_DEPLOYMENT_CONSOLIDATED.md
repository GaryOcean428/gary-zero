# Railway Deployment Guide - Consolidated

This document consolidates all Railway deployment guidance for Gary-Zero, replacing multiple fragmented files with a single authoritative source.

## Overview

Gary-Zero is designed for cloud-native deployment on Railway.com, providing:
- Automatic service discovery and private networking
- Integrated build and deployment pipeline
- Health checking and monitoring
- Scalable multi-service architecture

## Current Deployment Status

✅ **Fully Operational** - All critical 405 Method Not Allowed issues have been resolved.

### Services Architecture

- **Primary App**: FastAPI/Flask hybrid application
- **Redis**: Session storage and caching
- **SearchXNG**: Search engine integration
- **Computer-Use**: Anthropic computer use service
- **Workflows**: Multi-agent workflow orchestration

## Configuration Files

### railway.toml

The main Railway configuration specifies:
- Build commands for both Node.js and Python dependencies
- Start command using the web UI
- Health check configuration
- Environment variable mapping

### nixpacks.toml

Explicitly specifies Python 3.13 as the provider to prevent Railway from misidentifying the project as Node.js.

```toml
[providers]
python = "3.13"
```

### Procfile

Defines how Railway should start the web application:

```
web: python start_uvicorn.py
```

## Environment Variables

### Essential
- `OPENAI_API_KEY` - OpenAI API key for LLM access
- `ANTHROPIC_API_KEY` - Anthropic API key for Claude models  
- `DATABASE_URL` - PostgreSQL connection string
- `NODE_ENV=production`

### Optional (Recommended)
- `GROQ_API_KEY` - Groq API for faster inference
- `GOOGLE_API_KEY` - Google/Gemini API access
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_ANON_KEY` - Supabase anonymous key

## Volume Setup

Gary-Zero uses Railway volumes for persistent data storage:

```bash
railway volumes create gary-zero-data --size 10
```

Mount path: `/app/data`

## Health Checks

- **Endpoint**: `/health`
- **Timeout**: 30 seconds
- **Interval**: 60 seconds
- **Retries**: 3

## Deployment Process

1. Connect GitHub repository to Railway
2. Configure environment variables in Railway dashboard
3. Deploy using the `railway.toml` configuration
4. Monitor logs for successful startup

### Manual Deployment

```bash
# Deploy to Railway
git push origin main

# Monitor deployment
railway logs --tail

# Test production endpoints
curl https://your-railway-domain.up.railway.app/health
```

## Troubleshooting

### Common Issues

1. **405 Method Not Allowed** - Resolved via comprehensive HTTP method support
2. **Port Binding** - Use Railway-provided `PORT` environment variable
3. **Database Connection** - Ensure `DATABASE_URL` is properly configured
4. **Build Timeouts** - Check build command efficiency

### Diagnostics

```bash
# Check Railway configuration
railway status

# View application logs
railway logs

# Test endpoints
python test_flask_routes.py https://your-railway-domain.up.railway.app
```

## Performance Optimization

- Use gunicorn for production WSGI serving
- Enable Railway's auto-scaling features
- Implement proper caching strategies
- Monitor resource usage in Railway dashboard

## Security

- All environment variables are encrypted at rest
- Private networking between services
- HTTPS by default for all Railway domains
- Regular security updates via Railway platform

## Monitoring

- Built-in Railway metrics dashboard
- Application logs via `railway logs`
- Health check monitoring
- Custom metrics via application endpoints

---

**Last Updated**: July 24, 2025  
**Status**: Production Ready  
**Railway Services**: 5 active services  
**Deployment**: Automated via GitHub integration

This document replaces all previous Railway deployment files and serves as the single source of truth for deployment procedures.
