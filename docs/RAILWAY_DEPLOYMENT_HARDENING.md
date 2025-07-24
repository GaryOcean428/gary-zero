# Railway Deployment Hardening Guide


## Overview

This document outlines the security hardening measures implemented for Gary-Zero deployment on Railway.app, following security best practices and Railway deployment standards.


## Implemented Security Measures

### 1. Health Check Endpoints

✅ **Added `/healthz` endpoint** - Railway-specific health check
- **Location**: Both FastAPI (`main.py`) and Flask (`run_ui.py`)
- **Purpose**: Railway health monitoring and deployment verification
- **URL**: `GET /healthz`
- **Response**: JSON with status, metrics, and environment information

✅ **Updated `railway.toml`** - Changed health check path
- **Before**: `healthcheckPath = "/health"`
- **After**: `healthcheckPath = "/healthz"`

### 2. Network Security Hardening

✅ **PORT Binding with 0.0.0.0** - Ensures Railway compatibility
- **Docker**: `EXPOSE ${PORT}` with build argument
- **Flask**: Updated fallback host from `localhost` to `0.0.0.0`
- **FastAPI**: Already configured with `0.0.0.0`
- **Entry Scripts**: All use `0.0.0.0:${PORT}` binding

✅ **Docker Configuration** - Production-ready container setup
- **ARG PORT**: Build-time port argument
- **EXPOSE ${PORT}**: Dynamic port exposure
- **Environment Variables**: Non-sensitive defaults only

### 3. Authentication Security

✅ **Removed Default Credentials** - Eliminated insecure defaults
- **Removed**: `DEFAULT_AUTH_LOGIN=admin` and `DEFAULT_AUTH_PASSWORD=admin`
- **Location**: `.env.example` file
- **Security**: Forces secure credential configuration

✅ **Database-Backed Authentication** - Enhanced security system
- **Primary**: Database-backed user authentication
- **Fallback**: Environment-based with security checks
- **Protection**: Blocks insecure default credentials (admin/admin)

### 4. Environment Variable Security

⚠️ **Required Railway Environment Variables**

Set these in Railway dashboard → Service → Variables:

#### Critical Authentication Variables

```bash
AUTH_LOGIN=your_secure_admin_username
AUTH_PASSWORD=your_secure_password_32_chars_min
```

#### API Keys (Set as needed)

```bash
OPENAI_API_KEY=sk-your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
GOOGLE_API_KEY=your-google-api-key
GROQ_API_KEY=your-groq-api-key
PERPLEXITY_API_KEY=your-perplexity-api-key
```

#### Database Connection (if using external database)

```bash
DATABASE_URL=postgres://user:pass@host:port/db?sslmode=require
POSTGRES_URL=postgres://user:pass@host:port/db?sslmode=require
```

#### Additional Security Variables

```bash
JWT_SECRET=your-jwt-secret-key-256-bits
ENCRYPTION_KEY=your-encryption-key-256-bits
SESSION_SECRET=your-session-secret-key
API_KEY=your_api_key_here
```

### 5. Security Headers

✅ **Comprehensive Security Headers** - Applied to all responses
- **X-Frame-Options**: SAMEORIGIN
- **X-Content-Type-Options**: nosniff
- **X-XSS-Protection**: 1; mode=block
- **Referrer-Policy**: strict-origin-when-cross-origin
- **Strict-Transport-Security**: HTTPS only (when secure)
- **Content-Security-Policy**: Configured for Alpine.js and external resources

### 6. Error Handling

✅ **Enhanced Error Responses** - Detailed diagnostics without information leakage
- **404 Errors**: Enhanced diagnostics with available endpoints
- **405 Errors**: Method not allowed with detailed debugging
- **500 Errors**: Custom error pages with logging
- **Global Exception Handler**: Centralized error handling


## Railway Deployment Checklist

### Pre-Deployment Security Verification

- [ ] **Change Default Credentials**: Never use admin/admin
- [ ] **Set Strong Passwords**: Minimum 32 characters for AUTH_PASSWORD
- [ ] **Configure API Keys**: Set all required API keys in Railway variables
- [ ] **Database Security**: Use secure connection strings with SSL
- [ ] **Environment Variables**: Review all variables for sensitive data
- [ ] **Remove Debug Features**: Set `ENABLE_DEV_FEATURES=false` in production

### Deployment Steps

1. **Clone/Update Repository**

   ```bash
   git pull origin main
   ```

2. **Railway Project Setup**

   ```bash
   railway login
   railway init
   railway link [project-id]
   ```

3. **Set Environment Variables**

   ```bash
   # Use Railway dashboard → Variables tab
   # Or use Railway CLI:
   railway variables set AUTH_LOGIN=your_secure_username
   railway variables set AUTH_PASSWORD=your_secure_password
   railway variables set OPENAI_API_KEY=sk-your-key
   # ... add all required variables
   ```

4. **Deploy Application**

   ```bash
   railway up
   ```

5. **Verify Deployment**
   - Check health endpoint: `https://your-app.up.railway.app/healthz`
   - Test authentication: `https://your-app.up.railway.app/`
   - Monitor logs: `railway logs`

### Post-Deployment Security Verification

- [ ] **Health Check**: Verify `/healthz` endpoint returns healthy status
- [ ] **Authentication**: Confirm admin/admin credentials are blocked
- [ ] **API Access**: Test API endpoints require proper authentication
- [ ] **Security Headers**: Verify security headers are present
- [ ] **Error Handling**: Confirm error pages don't leak sensitive information
- [ ] **HTTPS**: Ensure all traffic uses HTTPS (Railway auto-provides)


## Security Best Practices

### 1. Password Security

- **Minimum Length**: 32 characters for production passwords
- **Complexity**: Use mix of letters, numbers, and special characters
- **Rotation**: Regularly rotate credentials using `/api/rotate_credentials`
- **Storage**: Never commit credentials to version control

### 2. API Key Management

- **Principle of Least Privilege**: Only set API keys that are actually used
- **Environment Variables**: Store in Railway environment variables only
- **Monitoring**: Monitor API key usage for unusual activity
- **Rotation**: Regularly rotate API keys

### 3. Database Security

- **SSL/TLS**: Always use `sslmode=require` in connection strings
- **Credentials**: Use strong database passwords
- **Network**: Restrict database access to Railway services only
- **Backups**: Ensure database backups are encrypted

### 4. Monitoring and Logging

- **Health Monitoring**: Use `/healthz` for uptime monitoring
- **Error Logging**: Monitor application logs for security events
- **Access Logs**: Review authentication attempts
- **Performance**: Monitor resource usage through health endpoint


## Troubleshooting

### Common Security Issues

1. **Default Credentials Error**

   ```
   SECURITY CRITICAL: Default insecure credentials detected
   ```

   **Solution**: Set secure `AUTH_LOGIN` and `AUTH_PASSWORD` in Railway variables

2. **Database Authentication Failed**

   ```
   Failed to initialize database authentication
   ```

   **Solution**: Check `DATABASE_URL` or set secure fallback credentials

3. **API Key Missing**

   ```
   API key required
   ```

   **Solution**: Set required API keys in Railway environment variables

4. **Health Check Failing**

   ```
   Health check timeout
   ```

   **Solution**: Verify `/healthz` endpoint and server startup

### Security Contact

For security issues or questions:
- Review logs: `railway logs`
- Check service status: `https://your-app.up.railway.app/healthz`
- Debug routes: `https://your-app.up.railway.app/debug/routes`


## Version History

- **v1.0** - Initial hardening implementation
- **v1.1** - Added `/healthz` endpoint and security headers
- **v1.2** - Enhanced authentication and removed default credentials

---

**⚠️ Security Notice**: This deployment has been hardened according to security best practices. Always keep credentials secure and monitor the application for security events.
