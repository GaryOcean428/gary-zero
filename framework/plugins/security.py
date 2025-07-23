"""Security manager for plugin system."""

import hashlib
import os

from .registry import PluginMetadata


class PluginSecurityManager:
    """Manages security checks for plugins."""

    def __init__(self):
        self.trusted_authors: set[str] = {"gary-zero-official", "system"}
        self.allowed_dependencies: set[str] = {
            "os", "sys", "json", "re", "datetime", "typing", "pathlib",
            "requests", "httpx", "aiohttp", "asyncio", "sqlite3",
            "framework.helpers.tool", "framework.helpers.response"
        }
        self.restricted_imports: set[str] = {
            "subprocess", "eval", "exec", "compile", "globals", "__import__"
        }

    def validate_plugin(self, metadata: PluginMetadata, plugin_path: str) -> bool:
        """Validate a plugin for security issues."""
        try:
            # Check metadata
            if not self._validate_metadata(metadata):
                return False

            # Check file permissions
            if not self._check_file_permissions(plugin_path):
                return False

            # Check for restricted imports (basic static analysis)
            if not self._check_imports(plugin_path, metadata.entry_point):
                return False

            # Validate dependencies
            if not self._validate_dependencies(metadata.dependencies):
                return False

            return True

        except Exception as e:
            print(f"Security validation failed for plugin {metadata.name}: {e}")
            return False

    def _validate_metadata(self, metadata: PluginMetadata) -> bool:
        """Validate plugin metadata."""
        # Check required fields
        if not all([metadata.name, metadata.version, metadata.author]):
            print(f"Plugin {metadata.name} missing required metadata fields")
            return False

        # Check name format (alphanumeric + underscore/dash)
        if not metadata.name.replace('_', '').replace('-', '').isalnum():
            print(f"Plugin name contains invalid characters: {metadata.name}")
            return False

        # Check version format (basic semver check)
        if not self._is_valid_version(metadata.version):
            print(f"Plugin version format invalid: {metadata.version}")
            return False

        return True

    def _is_valid_version(self, version: str) -> bool:
        """Check if version follows semver format."""
        parts = version.split('.')
        if len(parts) != 3:
            return False

        try:
            for part in parts:
                int(part)
            return True
        except ValueError:
            return False

    def _check_file_permissions(self, plugin_path: str) -> bool:
        """Check file permissions are appropriate."""
        try:
            # Check directory permissions
            stat = os.stat(plugin_path)
            if stat.st_mode & 0o002:  # World writable
                print(f"Plugin directory is world writable: {plugin_path}")
                return False

            return True
        except Exception as e:
            print(f"Failed to check file permissions: {e}")
            return False

    def _check_imports(self, plugin_path: str, entry_point: str) -> bool:
        """Basic static analysis to check for restricted imports."""
        entry_file = os.path.join(plugin_path, entry_point)

        if not os.path.exists(entry_file):
            return False

        try:
            with open(entry_file) as f:
                content = f.read()

            # Check for restricted imports
            for restricted in self.restricted_imports:
                if f"import {restricted}" in content or f"from {restricted}" in content:
                    print(f"Plugin contains restricted import: {restricted}")
                    return False

            return True

        except Exception as e:
            print(f"Failed to analyze plugin imports: {e}")
            return False

    def _validate_dependencies(self, dependencies: list[str]) -> bool:
        """Validate plugin dependencies are allowed."""
        for dep in dependencies:
            if dep not in self.allowed_dependencies:
                print(f"Plugin dependency not in whitelist: {dep}")
                return False
        return True

    def calculate_plugin_hash(self, plugin_path: str, entry_point: str) -> str | None:
        """Calculate hash of plugin files for integrity checking."""
        try:
            entry_file = os.path.join(plugin_path, entry_point)

            if not os.path.exists(entry_file):
                return None

            hasher = hashlib.sha256()

            with open(entry_file, 'rb') as f:
                hasher.update(f.read())

            return hasher.hexdigest()

        except Exception as e:
            print(f"Failed to calculate plugin hash: {e}")
            return None

    def verify_signature(self, metadata: PluginMetadata, plugin_path: str) -> bool:
        """Verify plugin signature (simplified implementation)."""
        if not metadata.signature:
            # Allow unsigned plugins from trusted authors for now
            return metadata.author in self.trusted_authors

        # Calculate current hash
        current_hash = self.calculate_plugin_hash(plugin_path, metadata.entry_point)

        if not current_hash:
            return False

        # Simple signature verification (in production, use proper crypto)
        return metadata.signature == current_hash

    def add_trusted_author(self, author: str):
        """Add a trusted author."""
        self.trusted_authors.add(author)

    def remove_trusted_author(self, author: str):
        """Remove a trusted author."""
        self.trusted_authors.discard(author)

    def add_allowed_dependency(self, dependency: str):
        """Add an allowed dependency."""
        self.allowed_dependencies.add(dependency)

    def remove_allowed_dependency(self, dependency: str):
        """Remove an allowed dependency."""
        self.allowed_dependencies.discard(dependency)
