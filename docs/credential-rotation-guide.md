# Credential Rotation Guide - Gary-Zero Security Update

## 🚨 Breaking Change Notice

Gary-Zero has implemented enhanced security measures that **require immediate action** from existing users. Default hardcoded credentials have been removed and authentication now requires explicit environment variable configuration.

## What Changed?

### Before (Insecure)
```python
# Hardcoded credentials in source code - SECURITY RISK
"auth_login": "admin",
"auth_password": hashlib.sha256(b"admin").hexdigest()
```

### After (Secure)
```python
# Environment variable-based authentication
"auth_login": os.getenv("DEFAULT_AUTH_LOGIN", "admin"),
"auth_password": hashlib.sha256(os.getenv("DEFAULT_AUTH_PASSWORD", "admin").encode()).hexdigest()
```

## 🛡️ Security Impact

- **Eliminated hardcoded credentials** from codebase
- **Mandatory environment variable configuration** for production deployments
- **Enhanced secret scanning** prevents accidental credential commits
- **Separation of concerns** between code and configuration

## Migration Instructions

### Step 1: Immediate Action Required

**For Docker/Container Users:**
```bash
# Stop current Gary-Zero instance
docker stop gary-zero

# Set new secure credentials
export DEFAULT_AUTH_LOGIN="your-secure-username"
export DEFAULT_AUTH_PASSWORD="your-secure-password-123"

# Restart with new credentials
docker start gary-zero
```

**For Railway/Cloud Deployments:**
```bash
# Set environment variables in Railway dashboard
DEFAULT_AUTH_LOGIN=your-secure-username
DEFAULT_AUTH_PASSWORD=your-secure-password-123
AUTH_LOGIN=runtime-admin
AUTH_PASSWORD=runtime-secure-password-456
```

**For Local Development:**
```bash
# Create/update .env file
echo "DEFAULT_AUTH_LOGIN=developer" >> .env
echo "DEFAULT_AUTH_PASSWORD=dev-secure-123" >> .env
echo "AUTH_LOGIN=admin" >> .env
echo "AUTH_PASSWORD=runtime-secure-456" >> .env
```

### Step 2: Credential Types

#### Web UI Authentication
```bash
# Default credentials (fallback)
export DEFAULT_AUTH_LOGIN="admin"
export DEFAULT_AUTH_PASSWORD="secure-default-password"

# Runtime credentials (override defaults)
export AUTH_LOGIN="runtime-admin"  
export AUTH_PASSWORD="runtime-secure-password"
```

#### Container Access (Optional)
```bash
# Root password for SSH/container access
export DEFAULT_ROOT_PASSWORD="secure-container-password"
```

#### AI Provider API Keys
```bash
# OpenAI
export OPENAI_API_KEY="sk-your-openai-key"

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-your-anthropic-key"

# Google
export GOOGLE_API_KEY="your-google-api-key"

# Additional providers as needed
```

#### Kali Integration (If Used)
```bash
# Kali Linux service credentials
export KALI_USERNAME="kali-user"
export KALI_PASSWORD="kali-secure-password"
```

### Step 3: Deployment-Specific Instructions

#### 🐳 Docker Compose
```yaml
# docker-compose.yml
version: '3.8'
services:
  gary-zero:
    image: your-gary-zero-image
    environment:
      - DEFAULT_AUTH_LOGIN=secure-admin
      - DEFAULT_AUTH_PASSWORD=secure-password-123
      - AUTH_LOGIN=runtime-admin
      - AUTH_PASSWORD=runtime-password-456
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    ports:
      - "7860:7860"
```

#### 🚂 Railway Deployment
1. Go to Railway dashboard → Your Project → Variables
2. Add environment variables:
```
DEFAULT_AUTH_LOGIN=your-username
DEFAULT_AUTH_PASSWORD=your-secure-password
AUTH_LOGIN=runtime-username
AUTH_PASSWORD=runtime-secure-password
```

#### ☁️ Cloud Platforms (AWS/GCP/Azure)
```bash
# Using cloud secret management
export DEFAULT_AUTH_LOGIN="$(aws secretsmanager get-secret-value --secret-id gary-zero/auth-login --query SecretString --output text)"
export DEFAULT_AUTH_PASSWORD="$(aws secretsmanager get-secret-value --secret-id gary-zero/auth-password --query SecretString --output text)"
```

#### 🏠 Local Development
```bash
# Create secure .env file
cat > .env << EOF
DEFAULT_AUTH_LOGIN=developer
DEFAULT_AUTH_PASSWORD=dev-secure-password-123
AUTH_LOGIN=local-admin
AUTH_PASSWORD=local-secure-password-456
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
EOF

# Secure the file
chmod 600 .env
```

## 🔄 Credential Rotation Best Practices

### 1. Regular Rotation Schedule
```bash
#!/bin/bash
# rotate-credentials.sh - Run monthly

# Generate new secure passwords
NEW_DEFAULT_PASSWORD=$(openssl rand -base64 32)
NEW_RUNTIME_PASSWORD=$(openssl rand -base64 32)

# Update environment variables
export DEFAULT_AUTH_PASSWORD="$NEW_DEFAULT_PASSWORD"
export AUTH_PASSWORD="$NEW_RUNTIME_PASSWORD"

# Log rotation event
echo "$(date): Credentials rotated" >> /var/log/gary-zero-rotation.log

# Restart Gary-Zero
systemctl restart gary-zero
```

### 2. Password Requirements
- **Minimum 12 characters**
- **Mix of uppercase, lowercase, numbers, symbols**
- **No dictionary words**
- **Unique across services**

### 3. Secret Storage
```bash
# Good: Environment variables
export AUTH_PASSWORD="secure-password-123"

# Better: Secret management systems
export AUTH_PASSWORD="$(vault kv get -field=password secret/gary-zero/auth)"

# Best: Cloud-native secret management
export AUTH_PASSWORD="$(gcloud secrets versions access latest --secret=gary-zero-auth-password)"
```

## 🚨 Troubleshooting

### Issue 1: Authentication Failures
```
Error: Invalid credentials
```

**Solution:**
```bash
# Verify environment variables are set
echo $DEFAULT_AUTH_LOGIN
echo $AUTH_LOGIN

# Check if variables are loaded in Gary-Zero
python -c "import os; print('LOGIN:', os.getenv('DEFAULT_AUTH_LOGIN', 'NOT SET'))"
```

### Issue 2: Empty/Missing Credentials
```
Error: No authentication credentials configured
```

**Solution:**
```bash
# Set missing credentials
export DEFAULT_AUTH_LOGIN="admin"
export DEFAULT_AUTH_PASSWORD="temp-password-change-me"

# Restart Gary-Zero
systemctl restart gary-zero
```

### Issue 3: Container Access Issues
```
Error: SSH connection refused
```

**Solution:**
```bash
# Set root password for container access
export DEFAULT_ROOT_PASSWORD="container-access-password"

# Rebuild container with new credentials
docker build --build-arg ROOT_PASSWORD="$DEFAULT_ROOT_PASSWORD" .
```

### Issue 4: API Key Authentication
```
Error: Invalid API key for provider OPENAI
```

**Solution:**
```bash
# Verify API key format and validity
echo $OPENAI_API_KEY | grep -E "^sk-[a-zA-Z0-9]+"

# Test API key directly
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
```

## 📋 Migration Checklist

### Pre-Migration (⚠️ Do This First)
- [ ] **Backup current configuration** and data
- [ ] **Document current access credentials** for reference
- [ ] **Test new credentials** in development environment
- [ ] **Notify team members** about upcoming authentication changes

### Migration Steps
- [ ] **Set environment variables** for authentication
- [ ] **Configure AI provider API keys** in environment
- [ ] **Update deployment scripts** with new credential handling
- [ ] **Test login functionality** with new credentials
- [ ] **Verify API integrations** work with new keys

### Post-Migration
- [ ] **Remove old hardcoded credentials** from documentation
- [ ] **Update team access procedures** with new credential requirements
- [ ] **Schedule regular credential rotation** (monthly recommended)
- [ ] **Monitor authentication logs** for any issues
- [ ] **Update backup procedures** to include credential recovery

## 🔒 Security Verification

### Run Security Scan
```bash
# Check for accidentally committed secrets
detect-secrets scan --baseline .secrets.baseline --all-files

# Verify no hardcoded credentials exist
grep -r "password.*=" --include="*.py" framework/ | grep -v "getenv"
```

### Validate Configuration
```bash
# Test authentication endpoint
curl -X POST http://localhost:7860/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"'"$DEFAULT_AUTH_LOGIN"'","password":"'"$DEFAULT_AUTH_PASSWORD"'"}'

# Verify environment variables
env | grep -E "(AUTH_|DEFAULT_)" | sort
```

## 📞 Support

### Getting Help
- **Documentation**: [CREDENTIALS_MANAGEMENT.md](../CREDENTIALS_MANAGEMENT.md)
- **Security Issues**: Report via GitHub Security tab
- **General Support**: GitHub Issues with `[credential-rotation]` tag

### Emergency Access
If you're locked out after migration:

```bash
# Temporary emergency access (development only)
export DEFAULT_AUTH_LOGIN="emergency"
export DEFAULT_AUTH_PASSWORD="temp-access-123"

# Start Gary-Zero with emergency credentials
python main.py --emergency-access

# IMPORTANT: Change credentials immediately after access is restored
```

---

**⚠️ Action Required By**: January 31, 2025  
**Security Level**: Critical  
**Downtime Risk**: High if not completed  

**Questions?** Check [CREDENTIALS_MANAGEMENT.md](../CREDENTIALS_MANAGEMENT.md) or create a GitHub issue.
