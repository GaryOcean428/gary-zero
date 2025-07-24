"""
Example: Modernizing Existing Tools to Use Secret Store

This example shows how to update existing Gary-Zero tools to use the secret store
while maintaining backward compatibility with environment variables.
"""

import os
import sys

# Add current directory to path for imports
sys.path.append(".")

from framework.security import (
    SecretStoreIntegration,
    get_anthropic_api_key,
    require_api_key,
)


# =============================================================================
# BEFORE: Legacy Tool Implementation
# =============================================================================
class LegacyAnthropicTool:
    """
    Example of how tools currently work - direct environment variable access.
    This is the pattern we want to migrate away from.
    """

    def __init__(self):
        """Initialize with direct environment variable access."""
        self.api_key = os.getenv("ANTHROPIC_API_KEY")

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")

        print(f"🔧 Legacy tool initialized with API key: {self.api_key[:10]}...")

    def make_request(self, prompt: str) -> str:
        """Make a request using the API key."""
        # Simulate API request
        return f"Anthropic response to: {prompt} (using key: {self.api_key[:10]}...)"


# =============================================================================
# AFTER: Modernized Tool Implementation
# =============================================================================
class ModernAnthropicTool:
    """
    Example of how tools should work - using the secret store with fallback.
    This provides better security and centralized management.
    """

    def __init__(self, tool_name: str = "anthropic_tool"):
        """Initialize with secret store integration."""
        # Use SecretStoreIntegration for consistent secret management
        self.secrets = SecretStoreIntegration(tool_name)

        # Get API key with automatic fallback to environment variable
        self.api_key = self.secrets.get_api_key("anthropic", required=True)

        print(f"🔧 Modern tool initialized with API key: {self.api_key[:10]}...")

    def make_request(self, prompt: str) -> str:
        """Make a request using the API key."""
        # Simulate API request
        return f"Anthropic response to: {prompt} (using key: {self.api_key[:10]}...)"

    def rotate_api_key(self, new_key: str):
        """Rotate the API key (example of advanced functionality)."""

        from framework.security import (
            AccessLevel,
            SecretMetadata,
            SecretType,
            store_secret,
        )

        # Store new key with rotation metadata
        metadata = SecretMetadata(
            name="anthropic_api_key",
            secret_type=SecretType.API_KEY,
            access_level=AccessLevel.RESTRICTED,
            description="Anthropic API key (rotated)",
            rotation_interval_days=30,
            tags=["anthropic", "rotated"],
        )

        store_secret("anthropic_api_key", new_key, metadata, overwrite=True)
        self.api_key = new_key

        print(f"🔄 API key rotated successfully: {new_key[:10]}...")


# =============================================================================
# PATTERN 3: Decorator-Based Approach
# =============================================================================
@require_api_key("anthropic", "ANTHROPIC_API_KEY")
def anthropic_chat_completion(
    prompt: str, model: str = "claude-3-sonnet", api_key: str = None
) -> str:
    """
    Function that requires Anthropic API key using decorator pattern.
    The API key is automatically injected by the decorator.
    """
    print(f"🤖 Making Anthropic request with key: {api_key[:10]}...")
    # Simulate API request
    return f"Claude response ({model}): {prompt}"


# =============================================================================
# PATTERN 4: Helper Function Approach
# =============================================================================
def simple_anthropic_request(prompt: str) -> str:
    """
    Simple function using helper functions for API key management.
    """
    api_key = get_anthropic_api_key()

    if not api_key:
        raise ValueError("Anthropic API key not found in secret store or environment")

    print(f"🤖 Simple request with key: {api_key[:10]}...")
    return f"Simple Claude response: {prompt}"


# =============================================================================
# PATTERN 5: Class with Multiple Services
# =============================================================================
class MultiServiceTool:
    """
    Example tool that uses multiple services with the secret store.
    """

    def __init__(self):
        """Initialize with multiple service integrations."""
        self.secrets = SecretStoreIntegration("multi_service_tool")

        # Initialize multiple service connections
        self.anthropic_key = self.secrets.get_api_key("anthropic", required=False)
        self.openai_key = self.secrets.get_api_key("openai", required=False)
        self.gemini_key = self.secrets.get_api_key("gemini", required=False)

        # Report available services
        services = []
        if self.anthropic_key:
            services.append("Anthropic")
        if self.openai_key:
            services.append("OpenAI")
        if self.gemini_key:
            services.append("Gemini")

        print(
            f"🔧 Multi-service tool initialized with: {', '.join(services) if services else 'No services'}"
        )

    def make_request(self, prompt: str, service: str = "auto") -> str:
        """Make a request using the specified or best available service."""
        if service == "auto":
            # Choose first available service
            if self.anthropic_key:
                service = "anthropic"
            elif self.openai_key:
                service = "openai"
            elif self.gemini_key:
                service = "gemini"
            else:
                raise ValueError("No API keys available for any service")

        if service == "anthropic" and self.anthropic_key:
            return f"Anthropic response: {prompt}"
        elif service == "openai" and self.openai_key:
            return f"OpenAI response: {prompt}"
        elif service == "gemini" and self.gemini_key:
            return f"Gemini response: {prompt}"
        else:
            raise ValueError(f"Service '{service}' not available or no API key found")


# =============================================================================
# MIGRATION UTILITY
# =============================================================================
def migrate_tool_to_secret_store():
    """
    Utility function to help migrate existing tools to use the secret store.
    """
    print("🔄 Migration Utility for Secret Store Integration")
    print("=" * 50)

    # Check current environment variables
    env_keys = {
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
    }

    print("\n📋 Current Environment Variables:")
    for key, value in env_keys.items():
        status = "✓ Found" if value else "✗ Not found"
        print(f"  {key}: {status}")

    # Import available keys to secret store
    print("\n📦 Importing to Secret Store...")
    from framework.security import migrate_environment_secrets

    migrated_count = migrate_environment_secrets()
    print(f"   Migrated {migrated_count} secrets to store")

    # Show what's available in secret store
    print("\n🔐 Available in Secret Store:")
    from framework.security import get_secret_store

    store = get_secret_store()
    secrets = store.list_secrets(include_metadata=False)

    for secret_name in secrets:
        if "api_key" in secret_name:
            print(f"  ✓ {secret_name}")

    print("\n✅ Migration complete! Tools can now use SecretStoreIntegration.")


# =============================================================================
# DEMONSTRATION
# =============================================================================
def demonstrate_tool_modernization():
    """Demonstrate the modernization of tools."""
    print("🚀 Tool Modernization Demo")
    print("=" * 40)

    # Set consistent encryption key for demo
    os.environ["SECRET_STORE_KEY"] = "demo-key-for-tool-modernization"

    # First, migrate any available secrets
    migrate_tool_to_secret_store()

    print("\n" + "=" * 40)
    print("🔄 Comparing Tool Patterns")
    print("=" * 40)

    # Test Pattern 1: Legacy Tool (if API key available)
    print("\n1️⃣ Legacy Tool Pattern:")
    try:
        if os.getenv("ANTHROPIC_API_KEY"):
            legacy_tool = LegacyAnthropicTool()
            result = legacy_tool.make_request("Hello, world!")
            print(f"   Result: {result}")
        else:
            print("   ⚠️ Skipped - no ANTHROPIC_API_KEY environment variable")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test Pattern 2: Modern Tool
    print("\n2️⃣ Modern Tool Pattern (SecretStoreIntegration):")
    try:
        modern_tool = ModernAnthropicTool("demo_anthropic_tool")
        result = modern_tool.make_request("Hello, world!")
        print(f"   Result: {result}")

        # Demonstrate rotation capability
        # modern_tool.rotate_api_key("new-rotated-key-example")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test Pattern 3: Decorator Pattern
    print("\n3️⃣ Decorator Pattern:")
    try:
        result = anthropic_chat_completion("Hello, world!")
        print(f"   Result: {result}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test Pattern 4: Helper Function Pattern
    print("\n4️⃣ Helper Function Pattern:")
    try:
        result = simple_anthropic_request("Hello, world!")
        print(f"   Result: {result}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test Pattern 5: Multi-Service Tool
    print("\n5️⃣ Multi-Service Tool Pattern:")
    try:
        multi_tool = MultiServiceTool()
        result = multi_tool.make_request("Hello, world!", "auto")
        print(f"   Result: {result}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n" + "=" * 40)
    print("📊 Summary of Patterns")
    print("=" * 40)

    patterns = [
        ("Legacy Tool", "Direct env vars", "❌ Insecure, hard to manage"),
        (
            "SecretStoreIntegration",
            "Class-based integration",
            "✅ Recommended for components",
        ),
        (
            "Decorator Pattern",
            "Function decorators",
            "✅ Great for individual functions",
        ),
        ("Helper Functions", "Direct helper calls", "✅ Simple use cases"),
        ("Multi-Service", "Multiple API management", "✅ Complex integrations"),
    ]

    for pattern, method, recommendation in patterns:
        print(f"  {pattern}:")
        print(f"    Method: {method}")
        print(f"    Status: {recommendation}")
        print()

    print("🎯 Migration Recommendations:")
    print("  1. Use SecretStoreIntegration for new components")
    print("  2. Use decorators for functions requiring specific APIs")
    print("  3. Use helper functions for simple cases")
    print("  4. Maintain backward compatibility during transition")
    print("  5. Remove environment variable dependencies gradually")


if __name__ == "__main__":
    demonstrate_tool_modernization()
