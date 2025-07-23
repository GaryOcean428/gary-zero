#!/usr/bin/env python3
"""
Demo: Integrating Secret Store with Existing Tools

This demo shows how to integrate the secret store with existing Gary-Zero
tools and components while maintaining backward compatibility.
"""

import sys
import os

# Add current directory to path for imports
sys.path.append('.')

from framework.security import (
    get_secret_store,
    get_openai_api_key,
    get_anthropic_api_key,
    get_gemini_api_key,
    SecretStoreIntegration,
    migrate_environment_secrets
)


class ModernizedTool:
    """
    Example of how to modernize an existing tool to use the secret store.
    
    This demonstrates the pattern for updating existing Gary-Zero tools
    to use the secret store while maintaining backward compatibility.
    """
    
    def __init__(self, tool_name: str = "example_tool"):
        """Initialize the tool with secret store integration."""
        # Use SecretStoreIntegration for consistent secret management
        self.secrets = SecretStoreIntegration(tool_name)
        self.tool_name = tool_name
        
        # Initialize with required API keys
        self._initialize_api_keys()
    
    def _initialize_api_keys(self):
        """Initialize API keys using the secret store."""
        # Get API keys with automatic fallback to environment variables
        self.openai_api_key = self.secrets.get_api_key("openai", required=False)
        self.anthropic_api_key = self.secrets.get_api_key("anthropic", required=False)
        self.gemini_api_key = self.secrets.get_api_key("gemini", required=False)
        
        # Report what we found
        print(f"🔧 {self.tool_name} initialization:")
        print(f"  OpenAI API Key: {'✓ Found' if self.openai_api_key else '✗ Not found'}")
        print(f"  Anthropic API Key: {'✓ Found' if self.anthropic_api_key else '✗ Not found'}")
        print(f"  Gemini API Key: {'✓ Found' if self.gemini_api_key else '✗ Not found'}")
    
    def get_database_config(self):
        """Get database configuration."""
        # Use helper method for database URL
        db_url = self.secrets.get_secret("database_url", env_fallback="DATABASE_URL", required=False)
        return {"database_url": db_url} if db_url else None
    
    def get_auth_config(self):
        """Get authentication configuration."""
        # Get JWT and session secrets
        jwt_secret = self.secrets.get_secret("jwt_secret", env_fallback="JWT_SECRET", required=False)
        session_secret = self.secrets.get_secret("session_secret", env_fallback="SESSION_SECRET", required=False)
        
        return {
            "jwt_secret": jwt_secret,
            "session_secret": session_secret
        }


class LegacyTool:
    """
    Example of a legacy tool that uses environment variables directly.
    
    This shows the old pattern that we want to migrate away from.
    """
    
    def __init__(self):
        """Initialize with direct environment variable access."""
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.database_url = os.getenv("DATABASE_URL")
        
        print("🔧 Legacy tool initialization:")
        print(f"  OpenAI API Key: {'✓ Found' if self.openai_api_key else '✗ Not found'}")
        print(f"  Anthropic API Key: {'✓ Found' if self.anthropic_api_key else '✗ Not found'}")
        print(f"  Database URL: {'✓ Found' if self.database_url else '✗ Not found'}")


def demonstrate_secret_store_integration():
    """Demonstrate secret store integration patterns."""
    print("🚀 Secret Store Integration Demo")
    print("=" * 50)
    
    # Step 1: Migrate existing environment secrets
    print("\n📦 Step 1: Migrating environment secrets to store...")
    migrated_count = migrate_environment_secrets()
    print(f"   Migrated {migrated_count} secrets from environment variables")
    
    # Step 2: Show store contents
    print("\n📋 Step 2: Current secrets in store...")
    store = get_secret_store()
    secrets_list = store.list_secrets(include_metadata=False)
    for secret_name in secrets_list:
        print(f"   - {secret_name}")
    
    # Step 3: Compare legacy vs modern approaches
    print("\n🔄 Step 3: Comparing legacy vs modern tools...")
    print("\n--- Legacy Tool (Environment Variables) ---")
    legacy_tool = LegacyTool()
    
    print("\n--- Modern Tool (Secret Store) ---")
    modern_tool = ModernizedTool("demo_tool")
    
    # Step 4: Show configuration access
    print("\n⚙️ Step 4: Configuration access patterns...")
    print("\n--- Database Configuration ---")
    db_config = modern_tool.get_database_config()
    print(f"   Database config: {db_config}")
    
    print("\n--- Authentication Configuration ---")
    auth_config = modern_tool.get_auth_config()
    print(f"   Auth config: {auth_config}")
    
    # Step 5: Demonstrate helper functions
    print("\n🔑 Step 5: Using convenience helper functions...")
    openai_key = get_openai_api_key()
    anthropic_key = get_anthropic_api_key()
    gemini_key = get_gemini_api_key()
    
    print(f"   OpenAI: {'✓' if openai_key else '✗'}")
    print(f"   Anthropic: {'✓' if anthropic_key else '✗'}")
    print(f"   Gemini: {'✓' if gemini_key else '✗'}")
    
    # Step 6: Show audit and security features
    print("\n🔒 Step 6: Security features...")
    print("   ✓ Secrets encrypted at rest")
    print("   ✓ Access logging enabled")
    print("   ✓ Audit trail maintained")
    print("   ✓ Environment variable fallback")
    print("   ✓ Automatic migration support")
    
    print("\n✅ Demo complete!")
    print("\nBenefits of Secret Store Integration:")
    print("  • Centralized secret management")
    print("  • Encrypted storage at rest")
    print("  • Audit logging for compliance")
    print("  • Backward compatibility with environment variables")
    print("  • Automatic secret discovery and migration")
    print("  • CLI management interface")
    print("  • Access control and permissions")


def demonstrate_decorator_pattern():
    """Demonstrate the decorator pattern for API key requirements."""
    print("\n🎯 Decorator Pattern Demo")
    print("=" * 30)
    
    from framework.security import require_api_key
    
    @require_api_key("openai", "OPENAI_API_KEY")
    def openai_chat_completion(prompt: str, api_key: str = None):
        """Example function that requires OpenAI API key."""
        print(f"   Making OpenAI request with key: {api_key[:10]}..." if api_key else "No API key")
        return f"Response to: {prompt}"
    
    @require_api_key("gemini", "GEMINI_API_KEY")
    def gemini_generate(prompt: str, api_key: str = None):
        """Example function that requires Gemini API key."""
        print(f"   Making Gemini request with key: {api_key[:10]}..." if api_key else "No API key")
        return f"Gemini response to: {prompt}"
    
    # Test the decorators
    try:
        print("\n🤖 Testing OpenAI decorator...")
        result = openai_chat_completion("Hello, world!")
        print(f"   Result: {result}")
    except ValueError as e:
        print(f"   Error: {e}")
    
    try:
        print("\n🤖 Testing Gemini decorator...")
        result = gemini_generate("Hello, world!")
        print(f"   Result: {result}")
    except ValueError as e:
        print(f"   Error: {e}")


if __name__ == "__main__":
    # Set a consistent key for the demo
    os.environ["SECRET_STORE_KEY"] = "demo-key-for-development"
    
    # Run the demonstration
    demonstrate_secret_store_integration()
    demonstrate_decorator_pattern()
    
    print("\n" + "=" * 50)
    print("🎓 Integration Complete!")
    print("\nNext steps for production:")
    print("1. Set SECRET_STORE_KEY environment variable")
    print("2. Update existing tools to use SecretStoreIntegration")
    print("3. Migrate secrets using: python -m framework.security.secret_cli import-env")
    print("4. Remove hard-coded secrets from code")
    print("5. Set up secret rotation policies")
    print("6. Configure audit logging destinations")