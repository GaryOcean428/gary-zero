"""Plugin metadata and registry system for Gary-Zero."""

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime

from framework.helpers.files import get_abs_path


@dataclass
class PluginMetadata:
    """Metadata for a plugin."""

    name: str
    version: str
    description: str
    author: str
    capabilities: list[str]
    dependencies: list[str] = None
    entry_point: str = "plugin.py"
    enabled: bool = True
    install_date: str | None = None
    last_updated: str | None = None
    signature: str | None = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.install_date is None:
            self.install_date = datetime.now().isoformat()
        if self.last_updated is None:
            self.last_updated = self.install_date


class PluginRegistry:
    """Registry for managing plugins and their metadata."""

    def __init__(self, plugins_dir: str = "plugins", db_file: str = "plugins.db"):
        self.plugins_dir = get_abs_path(plugins_dir)
        self.db_file = get_abs_path(db_file)
        self._ensure_plugins_dir()
        self._init_database()

    def _ensure_plugins_dir(self):
        """Ensure the plugins directory exists."""
        os.makedirs(self.plugins_dir, exist_ok=True)

    def _init_database(self):
        """Initialize the plugin database."""
        with sqlite3.connect(self.db_file) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS plugins (
                    name TEXT PRIMARY KEY,
                    version TEXT NOT NULL,
                    description TEXT,
                    author TEXT,
                    capabilities TEXT,  -- JSON array
                    dependencies TEXT,  -- JSON array
                    entry_point TEXT,
                    enabled BOOLEAN DEFAULT 1,
                    install_date TEXT,
                    last_updated TEXT,
                    signature TEXT
                )
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_enabled ON plugins(enabled)
            """
            )
            conn.commit()

    def register_plugin(self, metadata: PluginMetadata) -> bool:
        """Register a plugin with the registry."""
        try:
            with sqlite3.connect(self.db_file) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO plugins 
                    (name, version, description, author, capabilities, dependencies, 
                     entry_point, enabled, install_date, last_updated, signature)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        metadata.name,
                        metadata.version,
                        metadata.description,
                        metadata.author,
                        json.dumps(metadata.capabilities),
                        json.dumps(metadata.dependencies),
                        metadata.entry_point,
                        metadata.enabled,
                        metadata.install_date,
                        metadata.last_updated,
                        metadata.signature,
                    ),
                )
                conn.commit()
            return True
        except Exception as e:
            print(f"Failed to register plugin {metadata.name}: {e}")
            return False

    def get_plugin(self, name: str) -> PluginMetadata | None:
        """Get plugin metadata by name."""
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM plugins WHERE name = ?", (name,))
            row = cursor.fetchone()

            if row:
                return PluginMetadata(
                    name=row["name"],
                    version=row["version"],
                    description=row["description"],
                    author=row["author"],
                    capabilities=json.loads(row["capabilities"]),
                    dependencies=json.loads(row["dependencies"]),
                    entry_point=row["entry_point"],
                    enabled=bool(row["enabled"]),
                    install_date=row["install_date"],
                    last_updated=row["last_updated"],
                    signature=row["signature"],
                )
        return None

    def list_plugins(self, enabled_only: bool = False) -> list[PluginMetadata]:
        """List all plugins."""
        query = "SELECT * FROM plugins"
        if enabled_only:
            query += " WHERE enabled = 1"

        plugins = []
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query)

            for row in cursor:
                plugins.append(
                    PluginMetadata(
                        name=row["name"],
                        version=row["version"],
                        description=row["description"],
                        author=row["author"],
                        capabilities=json.loads(row["capabilities"]),
                        dependencies=json.loads(row["dependencies"]),
                        entry_point=row["entry_point"],
                        enabled=bool(row["enabled"]),
                        install_date=row["install_date"],
                        last_updated=row["last_updated"],
                        signature=row["signature"],
                    )
                )

        return plugins

    def enable_plugin(self, name: str) -> bool:
        """Enable a plugin."""
        try:
            with sqlite3.connect(self.db_file) as conn:
                conn.execute("UPDATE plugins SET enabled = 1 WHERE name = ?", (name,))
                conn.commit()
                return conn.total_changes > 0
        except Exception as e:
            print(f"Failed to enable plugin {name}: {e}")
            return False

    def disable_plugin(self, name: str) -> bool:
        """Disable a plugin."""
        try:
            with sqlite3.connect(self.db_file) as conn:
                conn.execute("UPDATE plugins SET enabled = 0 WHERE name = ?", (name,))
                conn.commit()
                return conn.total_changes > 0
        except Exception as e:
            print(f"Failed to disable plugin {name}: {e}")
            return False

    def unregister_plugin(self, name: str) -> bool:
        """Unregister a plugin."""
        try:
            with sqlite3.connect(self.db_file) as conn:
                conn.execute("DELETE FROM plugins WHERE name = ?", (name,))
                conn.commit()
                return conn.total_changes > 0
        except Exception as e:
            print(f"Failed to unregister plugin {name}: {e}")
            return False

    def discover_plugins(self) -> list[PluginMetadata]:
        """Discover plugins in the plugins directory."""
        discovered = []

        if not os.path.exists(self.plugins_dir):
            return discovered

        for item in os.listdir(self.plugins_dir):
            plugin_path = os.path.join(self.plugins_dir, item)

            if os.path.isdir(plugin_path):
                metadata_file = os.path.join(plugin_path, "plugin.json")

                if os.path.exists(metadata_file):
                    try:
                        with open(metadata_file) as f:
                            data = json.load(f)
                            metadata = PluginMetadata(**data)
                            discovered.append(metadata)
                    except Exception as e:
                        print(
                            f"Failed to load plugin metadata from {metadata_file}: {e}"
                        )

        return discovered

    def get_plugin_path(self, name: str) -> str | None:
        """Get the filesystem path for a plugin."""
        plugin_path = os.path.join(self.plugins_dir, name)
        if os.path.exists(plugin_path):
            return plugin_path
        return None

    def sync_discovered_plugins(self):
        """Sync discovered plugins with the registry."""
        discovered = self.discover_plugins()

        for metadata in discovered:
            existing = self.get_plugin(metadata.name)
            if not existing:
                # New plugin, register it
                self.register_plugin(metadata)
            elif existing.version != metadata.version:
                # Updated plugin, update metadata
                metadata.last_updated = datetime.now().isoformat()
                self.register_plugin(metadata)
