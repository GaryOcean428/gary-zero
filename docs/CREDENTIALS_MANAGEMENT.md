# Credentials Management

This document outlines how credentials are managed in Gary-Zero to ensure security and avoid hardcoded secrets.

## Overview

Gary-Zero has been updated to eliminate hardcoded credentials and use environment variables for all authentication settings. This ensures that sensitive information is not stored in the codebase and can be properly managed in deployment environments.

## Environment Variables

### Default Authentication

The following environment variables control default authentication settings:

- `DEFAULT_AUTH_LOGIN`: Default username for web UI authentication (fallback: "admin")
- `DEFAULT_AUTH_PASSWORD`: Default password for web UI authentication (fallback: "admin")
- `DEFAULT_ROOT_PASSWORD`: Default root password for container access (fallback: empty)

### Runtime Authentication

- `AUTH_LOGIN`: Current username for web UI (overrides default)
- `AUTH_PASSWORD`: Current password for web UI (overrides default)

### Kali Service Credentials

- `KALI_USERNAME`: Username for Kali Linux service connection
- `KALI_PASSWORD`: Password for Kali Linux service connection

## Security Features

### No Hardcoded Credentials

✅ All default credentials are now loaded from environment variables
✅ No passwords or secrets are hardcoded in the source code
✅ Password hashes are generated dynamically from environment values

### Secret Scanning

- **detect-secrets** is configured to scan for accidentally committed secrets
- CI/CD pipeline includes automatic secret detection
- Baseline file (`.secrets.baseline`) tracks known non-secret patterns

## Usage Examples

### Development Environment

```bash
# Set custom default credentials
export DEFAULT_AUTH_LOGIN="developer"
export DEFAULT_AUTH_PASSWORD="dev-password-123"

# Set runtime credentials
export AUTH_LOGIN="admin"
export AUTH_PASSWORD="secure-runtime-password"
```

### Production Deployment

```bash
# Use strong credentials from secret management system
export DEFAULT_AUTH_LOGIN="${SECRET_DEFAULT_USER}"
export DEFAULT_AUTH_PASSWORD="${SECRET_DEFAULT_PASSWORD}"
export AUTH_LOGIN="${SECRET_RUNTIME_USER}"
export AUTH_PASSWORD="${SECRET_RUNTIME_PASSWORD}"
```

### Container Environment

```bash
# Set root password for SSH access
export DEFAULT_ROOT_PASSWORD="secure-container-password"
```

## Migration Notes

### Before (Insecure)

```python
# Hardcoded in source code - SECURITY RISK
"auth_password": hashlib.sha256(b"admin").hexdigest()
```

### After (Secure)

```python
# Environment variable with secure fallback
"auth_password": hashlib.sha256(os.getenv("DEFAULT_AUTH_PASSWORD", "admin").encode()).hexdigest()
```

## Validation

To verify that no hardcoded credentials exist:

```bash
# Run secret detection scan
detect-secrets scan --baseline .secrets.baseline --all-files

# Check dependencies are synchronized
uv pip compile requirements.in -o requirements.check.txt
diff requirements.txt requirements.check.txt
```

## Best Practices

1. **Never commit credentials** to version control
2. **Use environment variables** for all sensitive configuration
3. **Rotate credentials regularly** in production environments
4. **Use strong passwords** with sufficient entropy
5. **Monitor secret detection** in CI/CD pipelines
6. **Document credential requirements** for deployment teams

## Related Files

- `.env.example` - Template with all supported environment variables
- `framework/helpers/settings.py` - Settings loader with environment integration
- `.secrets.baseline` - detect-secrets configuration and baseline
- `.github/workflows/python-package.yml` - CI pipeline with secret scanning
