"""Settings migration utilities to handle model updates and deprecations."""

from typing import Any

# Map of deprecated model names to their modern replacements
MODEL_MIGRATIONS = {
    # Anthropic models
    "claude-3-5-sonnet-20241022": "claude-3-5-sonnet-latest",
    "claude-3-5-haiku-20241022": "claude-3-5-haiku-latest",
    "claude-3.5-sonnet": "claude-3-5-sonnet-latest",
    "claude-3.5-haiku": "claude-3-5-haiku-latest",
    "claude-3-opus": "claude-opus-4-0",
    "claude-3-sonnet": "claude-sonnet-4-0",
    # OpenAI models
    "gpt-4": "gpt-4.1",
    "gpt-4-turbo": "gpt-4.1",
    "gpt-4-turbo-preview": "gpt-4.1",
    "gpt-3.5-turbo": "gpt-4.1-mini",
    # Google models
    "gemini-1.5-pro": "gemini-2.5-pro",
    "gemini-1.5-flash": "gemini-2.5-flash",
    "gemini-pro": "gemini-2.5-pro",
    # xAI models
    "grok-2": "grok-3",
    "grok-2-mini": "grok-3-mini",
    "grok-beta": "grok-3",
}


def migrate_settings(settings: dict[str, Any]) -> dict[str, Any]:
    """Migrate settings to use modern model names.

    Args:
        settings: The settings dictionary to migrate

    Returns:
        The migrated settings dictionary
    """
    # List of model fields to check and migrate
    model_fields = [
        "chat_model_name",
        "util_model_name",
        "embed_model_name",
        "browser_model_name",
        "voice_model_name",
        "code_model_name",
        "coding_agent_name",
        "supervisor_agent_name",
    ]

    # Create a copy of settings to avoid modifying the original
    migrated = settings.copy()

    # Track if any migrations were performed
    migrations_performed = []

    for field in model_fields:
        if field in migrated:
            old_value = migrated[field]
            if old_value in MODEL_MIGRATIONS:
                new_value = MODEL_MIGRATIONS[old_value]
                migrated[field] = new_value
                migrations_performed.append(f"{field}: {old_value} -> {new_value}")

    # Log migrations if any were performed
    if migrations_performed:
        print(f"Migrated {len(migrations_performed)} model settings:")
        for migration in migrations_performed:
            print(f"  - {migration}")

    return migrated


def needs_migration(settings: dict[str, Any]) -> bool:
    """Check if settings need migration.

    Args:
        settings: The settings dictionary to check

    Returns:
        True if migration is needed, False otherwise
    """
    model_fields = [
        "chat_model_name",
        "util_model_name",
        "embed_model_name",
        "browser_model_name",
        "voice_model_name",
        "code_model_name",
        "coding_agent_name",
        "supervisor_agent_name",
    ]

    for field in model_fields:
        if field in settings and settings[field] in MODEL_MIGRATIONS:
            return True

    return False
