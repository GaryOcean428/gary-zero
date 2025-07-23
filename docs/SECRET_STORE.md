# Secret Store Documentation

## Overview

The Gary-Zero Internal Secret Store provides secure, encrypted storage for API keys, passwords, and other sensitive information. It replaces hard-coded secrets and insecure environment variable usage with a centralized, auditable secret management system.

## Features

- **🔒 Encryption at Rest**: All secrets encrypted using Fernet/AES
- **🔑 Access Control**: Configurable access levels and permissions
- **📝 Audit Logging**: Complete audit trail for all secret operations
- **🔄 Automatic Migration**: Import existing secrets from environment variables
- **⏰ Rotation & Expiration**: Configurable secret rotation and expiration policies
- **🖥️ CLI Management**: Full command-line interface for secret operations
- **🔌 Easy Integration**: Helper functions for seamless component integration
- **⚡ Thread Safe**: Concurrent access with proper locking
- **🔙 Backward Compatible**: Automatic fallback to environment variables

## Quick Start

### 1. Basic Usage

```python
from framework.security import get_secret, store_secret

# Store a secret
store_secret("my_api_key", "sk-1234567890")

# Retrieve a secret
api_key = get_secret("my_api_key")
```

### 2. CLI Usage

```bash
# Add a secret
python -m framework.security.secret_cli add openai_api_key --value "sk-..." --type api_key

# List all secrets
python -m framework.security.secret_cli list

# Get a secret
python -m framework.security.secret_cli get openai_api_key

# Import from environment variables
python -m framework.security.secret_cli import-env
```

### 3. Component Integration

```python
from framework.security import SecretStoreIntegration

class MyTool:
    def __init__(self):
        self.secrets = SecretStoreIntegration("my_tool")
        self.api_key = self.secrets.get_api_key("openai", required=True)
```

## Core Components

### SecretStore Class

The main `InternalSecretStore` class provides all secret management functionality:

```python
from framework.security import InternalSecretStore, SecretStoreConfig

# Create store with custom configuration
config = SecretStoreConfig(
    store_path=Path("custom/secrets.encrypted"),
    enable_audit_logging=True,
    max_secrets=1000
)
store = InternalSecretStore(config)

# CRUD operations
store.store_secret("name", "value", metadata)
value = store.get_secret("name")
store.update_metadata("name", new_metadata)
store.delete_secret("name")
```

### Secret Metadata

Secrets can have rich metadata for organization and management:

```python
from framework.security import SecretMetadata, SecretType, AccessLevel

metadata = SecretMetadata(
    name="openai_api_key",
    secret_type=SecretType.API_KEY,
    access_level=AccessLevel.RESTRICTED,
    description="OpenAI API key for GPT models",
    expires_at=datetime.utcnow() + timedelta(days=90),
    rotation_interval_days=30,
    tags=["ai", "openai", "production"],
    owner="admin"
)
```

### Integration Helpers

Helper functions make it easy to integrate with existing components:

```python
from framework.security import (
    get_openai_api_key,
    get_anthropic_api_key,
    get_database_url,
    get_auth_credentials
)

# Service-specific helpers
openai_key = get_openai_api_key()
anthropic_key = get_anthropic_api_key()

# Database configuration
db_url = get_database_url()

# Authentication credentials
creds = get_auth_credentials("kali")  # {"username": "...", "password": "..."}
```

## CLI Reference

### Add Secret
```bash
python -m framework.security.secret_cli add <name> [options]

Options:
  --value VALUE          Secret value (prompts if not provided)
  --type TYPE           Secret type (api_key, password, token, etc.)
  --access LEVEL        Access level (public, restricted, admin)
  --description TEXT    Description of the secret
  --expires DAYS        Expiration in days
  --rotation DAYS       Rotation interval in days
  --tags TAGS           Comma-separated tags
  --overwrite           Overwrite existing secret
```

### Get Secret
```bash
python -m framework.security.secret_cli get <name> [options]

Options:
  --metadata            Show metadata along with value
```

### List Secrets
```bash
python -m framework.security.secret_cli list [options]

Options:
  --values              Show secret values (dangerous!)
  --format FORMAT       Output format (table, json)
```

### Update Secret
```bash
python -m framework.security.secret_cli update <name> [options]

Options:
  --value VALUE         New secret value
  --description TEXT    New description
  --expires DAYS        New expiration in days
  --rotation DAYS       New rotation interval
  --tags TAGS           New tags
```

### Delete Secret
```bash
python -m framework.security.secret_cli delete <name> [options]

Options:
  --force               Skip confirmation prompt
```

### Import from Environment
```bash
python -m framework.security.secret_cli import-env [options]

Options:
  --prefix PREFIX       Only import variables with this prefix
  --overwrite           Overwrite existing secrets
```

### Utilities
```bash
# Export metadata (without values)
python -m framework.security.secret_cli export [--output FILE]

# Clean up expired secrets
python -m framework.security.secret_cli cleanup

# Check secrets needing rotation
python -m framework.security.secret_cli rotation
```

## Integration Patterns

### Pattern 1: SecretStoreIntegration Class

The recommended pattern for new components:

```python
from framework.security import SecretStoreIntegration

class MyComponent:
    def __init__(self, component_name: str):
        self.secrets = SecretStoreIntegration(component_name)
    
    def connect_to_api(self):
        # Automatically handles fallback to environment variables
        api_key = self.secrets.get_api_key("openai", required=True)
        return OpenAIClient(api_key=api_key)
    
    def get_database(self):
        db_url = self.secrets.get_secret(
            "database_url", 
            env_fallback="DATABASE_URL",
            required=True
        )
        return Database(db_url)
```

### Pattern 2: Decorator Pattern

For functions that require specific API keys:

```python
from framework.security import require_api_key

@require_api_key("openai", "OPENAI_API_KEY")
def chat_completion(prompt: str, api_key: str = None):
    # api_key is automatically injected
    client = OpenAI(api_key=api_key)
    return client.chat.completions.create(...)

@require_api_key("anthropic", "ANTHROPIC_API_KEY")
def claude_completion(prompt: str, api_key: str = None):
    client = Anthropic(api_key=api_key)
    return client.messages.create(...)
```

### Pattern 3: Direct Helper Functions

For simple use cases:

```python
from framework.security import get_openai_api_key, get_database_url

def setup_services():
    # Helper functions handle fallback automatically
    openai_key = get_openai_api_key()
    db_url = get_database_url()
    
    if not openai_key:
        raise ValueError("OpenAI API key required")
    
    return {
        "openai": OpenAI(api_key=openai_key),
        "database": Database(db_url)
    }
```

## Migration Guide

### Step 1: Install and Initialize

1. The secret store is automatically available in the security framework
2. Set the `SECRET_STORE_KEY` environment variable for persistence:
   ```bash
   export SECRET_STORE_KEY="your-base64-encoded-key"
   ```

### Step 2: Migrate Existing Secrets

```bash
# Import all common API keys from environment
python -m framework.security.secret_cli import-env

# Or import with custom prefix
python -m framework.security.secret_cli import-env --prefix "MY_APP_"
```

### Step 3: Update Components

Replace direct environment variable access:

```python
# Before (Legacy)
import os
api_key = os.getenv("OPENAI_API_KEY")

# After (Modern)
from framework.security import get_openai_api_key
api_key = get_openai_api_key()
```

Or use the integration class:

```python
# Before (Legacy)
class MyTool:
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.db_url = os.getenv("DATABASE_URL")

# After (Modern)
class MyTool:
    def __init__(self):
        self.secrets = SecretStoreIntegration("my_tool")
        self.openai_key = self.secrets.get_api_key("openai")
        self.db_url = self.secrets.get_secret("database_url", env_fallback="DATABASE_URL")
```

### Step 4: Remove Hard-coded Secrets

1. Identify hard-coded secrets in your codebase
2. Move them to the secret store:
   ```bash
   python -m framework.security.secret_cli add my_secret --value "hard-coded-value"
   ```
3. Update code to use secret store
4. Remove hard-coded values

### Step 5: Set Up Rotation Policies

```bash
# Add secrets with rotation intervals
python -m framework.security.secret_cli add api_key --rotation 30 --expires 90

# Check which secrets need rotation
python -m framework.security.secret_cli rotation
```

## Security Considerations

### Encryption

- All secrets are encrypted at rest using Fernet (AES 128)
- Encryption key can be provided via `SECRET_STORE_KEY` environment variable
- Keys are derived securely using SHA-256 if string keys are provided

### Access Control

- Three access levels: `public`, `restricted`, `admin`
- Component-level access control (future enhancement)
- Audit logging for all secret access

### Key Management

```bash
# Generate a secure key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Set as environment variable
export SECRET_STORE_KEY="your-generated-key"
```

### Audit Logging

All secret operations are logged with:
- Operation type (create, read, update, delete)
- User/component requesting access
- Timestamp and success/failure status
- IP address and user agent (when available)

## Configuration

### Environment Variables

- `SECRET_STORE_KEY`: Encryption key for the secret store
- `SECRET_STORE_PATH`: Custom path for the encrypted store file
- `SECRET_STORE_AUDIT`: Enable/disable audit logging (default: true)

### Store Configuration

```python
from framework.security import SecretStoreConfig

config = SecretStoreConfig(
    store_path=Path("secrets/store.encrypted"),  # Store file location
    enable_audit_logging=True,                   # Enable audit logging
    auto_backup=True,                           # Enable automatic backups
    backup_retention_days=30,                   # Backup retention period
    max_secrets=1000                            # Maximum number of secrets
)
```

## Troubleshooting

### Common Issues

1. **"Fernet key must be 32 url-safe base64-encoded bytes"**
   - Generate a proper key: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
   - Set as `SECRET_STORE_KEY` environment variable

2. **"Failed to load secret store"**
   - Check file permissions on the store directory
   - Verify the encryption key is correct
   - Check if the store file is corrupted

3. **"Secret not found"**
   - Verify the secret name is correct
   - Check if environment variable fallback is needed
   - Use `secret_cli list` to see available secrets

4. **Audit logging warnings**
   - The audit logger is async; warnings about unawaited coroutines are normal
   - This doesn't affect functionality

### Debug Mode

```python
import logging
logging.getLogger('framework.security.secret_store').setLevel(logging.DEBUG)
```

## Best Practices

1. **Use descriptive secret names**: `openai_api_key` not `key1`
2. **Set appropriate metadata**: types, descriptions, expiration dates
3. **Use access levels**: Restrict sensitive secrets to admin-only
4. **Regular rotation**: Set rotation intervals for API keys
5. **Monitor audit logs**: Review access patterns regularly
6. **Backup your store**: Keep encrypted backups of the store file
7. **Use environment fallback**: Maintain backward compatibility
8. **Validate inputs**: Always check if secrets are found before using

## Future Enhancements

- **Remote storage backends**: Support for cloud key management services
- **Fine-grained permissions**: Role-based access control
- **Secret templates**: Common configurations for different services
- **Integration with CI/CD**: Automated secret injection for deployments
- **Secret scanning**: Integration with GitGuardian and similar tools
- **Multi-tenant support**: Namespace isolation for different components
- **Secret sharing**: Secure sharing between components with permissions

## Examples

See `demo_secret_store_integration.py` for a complete working example that demonstrates:
- Migration from environment variables
- Legacy vs modern tool patterns
- Helper function usage
- Decorator patterns
- Configuration management
- Security features

Run the demo:
```bash
python demo_secret_store_integration.py
```