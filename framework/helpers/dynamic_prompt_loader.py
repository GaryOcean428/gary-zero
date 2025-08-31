"""
Dynamic prompt loading service with file system watching.
Monitors prompt directories for changes and reloads prompts dynamically.
"""

import json
import os
import time
from typing import Any

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from framework.helpers.files import get_data_path
from framework.helpers.print_style import PrintStyle


class PromptFileHandler(FileSystemEventHandler):
    """File system event handler for prompt files."""

    def __init__(self, prompt_loader):
        self.prompt_loader = prompt_loader
        self.print_style = PrintStyle()

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(
            (".txt", ".md", ".yaml", ".yml", ".json")
        ):
            self.print_style.debug(f"Prompt file modified: {event.src_path}")
            self.prompt_loader.reload_prompt_file(event.src_path)

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(
            (".txt", ".md", ".yaml", ".yml", ".json")
        ):
            self.print_style.success(f"New prompt file detected: {event.src_path}")
            self.prompt_loader.reload_prompt_file(event.src_path)

    def on_deleted(self, event):
        if not event.is_directory and event.src_path.endswith(
            (".txt", ".md", ".yaml", ".yml", ".json")
        ):
            self.print_style.warning(f"Prompt file deleted: {event.src_path}")
            self.prompt_loader.remove_prompt_file(event.src_path)


class DynamicPromptLoader:
    """Dynamic prompt loading system with file watching."""

    def __init__(self):
        self.print_style = PrintStyle()
        self.prompts_cache: dict[str, dict[str, Any]] = {}
        self.agent_registry: dict[str, dict[str, Any]] = {}
        self.observer: Observer | None = None
        self.prompts_dir = get_data_path("prompts")

        # Ensure prompts directory exists
        os.makedirs(self.prompts_dir, exist_ok=True)

        # Create subdirectories if they don't exist
        for subdir in ["system", "tools", "agents", "dynamic"]:
            subdir_path = os.path.join(self.prompts_dir, subdir)
            os.makedirs(subdir_path, exist_ok=True)

    def start_watching(self):
        """Start watching the prompts directory for changes."""
        if self.observer:
            return

        try:
            self.observer = Observer()
            handler = PromptFileHandler(self)

            # Watch the main prompts directory and all subdirectories
            self.observer.schedule(handler, self.prompts_dir, recursive=True)
            self.observer.start()

            # Initial load of all prompts
            self.load_all_prompts()

            self.print_style.success(
                f"Started watching prompts directory: {self.prompts_dir}"
            )

        except Exception as e:
            self.print_style.error(f"Failed to start prompt watcher: {e}")

    def stop_watching(self):
        """Stop watching the prompts directory."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            self.print_style.info("Stopped watching prompts directory")

    def load_all_prompts(self):
        """Load all prompts from the prompts directory."""
        self.print_style.info("Loading all prompts...")

        for root, dirs, files in os.walk(self.prompts_dir):
            for file in files:
                if file.endswith((".txt", ".md", ".yaml", ".yml", ".json")):
                    file_path = os.path.join(root, file)
                    self.reload_prompt_file(file_path)

    def reload_prompt_file(self, file_path: str):
        """Reload a specific prompt file."""
        try:
            # Get relative path from prompts directory
            rel_path = os.path.relpath(file_path, self.prompts_dir)

            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Parse the file based on extension
            prompt_data = self._parse_prompt_file(file_path, content)

            if prompt_data:
                self.prompts_cache[rel_path] = prompt_data
                self.print_style.debug(f"Loaded prompt: {rel_path}")

                # Update agent registry if this is an agent prompt
                if rel_path.startswith("agents/"):
                    self._update_agent_registry(rel_path, prompt_data)

        except Exception as e:
            self.print_style.error(f"Failed to load prompt file {file_path}: {e}")

    def remove_prompt_file(self, file_path: str):
        """Remove a prompt file from cache."""
        rel_path = os.path.relpath(file_path, self.prompts_dir)
        if rel_path in self.prompts_cache:
            del self.prompts_cache[rel_path]
            self.print_style.debug(f"Removed prompt from cache: {rel_path}")

            # Remove from agent registry if applicable
            if rel_path.startswith("agents/"):
                agent_id = os.path.splitext(os.path.basename(rel_path))[0]
                if agent_id in self.agent_registry:
                    del self.agent_registry[agent_id]
                    self.print_style.debug(f"Removed agent from registry: {agent_id}")

    def _parse_prompt_file(self, file_path: str, content: str) -> dict[str, Any] | None:
        """Parse prompt file content based on file extension."""
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".json":
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                self.print_style.error(f"Invalid JSON in {file_path}: {e}")
                return None

        elif ext in [".yaml", ".yml"]:
            try:
                import yaml

                return yaml.safe_load(content)
            except Exception as e:
                self.print_style.error(f"Invalid YAML in {file_path}: {e}")
                return None

        else:  # .txt, .md files
            return {
                "content": content,
                "file_path": file_path,
                "loaded_at": time.time(),
            }

    def _update_agent_registry(self, rel_path: str, prompt_data: dict[str, Any]):
        """Update the agent registry with new agent prompt data."""
        agent_id = os.path.splitext(os.path.basename(rel_path))[0]

        agent_info = {
            "id": agent_id,
            "prompt_path": rel_path,
            "prompt_data": prompt_data,
            "loaded_at": time.time(),
        }

        # Extract additional metadata if available
        if isinstance(prompt_data, dict):
            agent_info.update(
                {
                    "name": prompt_data.get("name", agent_id),
                    "description": prompt_data.get("description", ""),
                    "capabilities": prompt_data.get("capabilities", []),
                    "required_env_vars": prompt_data.get("required_env_vars", []),
                }
            )

        self.agent_registry[agent_id] = agent_info
        self.print_style.success(f"Updated agent registry: {agent_id}")

    def get_prompt(self, prompt_path: str) -> dict[str, Any] | None:
        """Get a prompt by its relative path."""
        return self.prompts_cache.get(prompt_path)

    def get_agent_prompt(self, agent_id: str) -> dict[str, Any] | None:
        """Get an agent's prompt data."""
        agent_info = self.agent_registry.get(agent_id)
        return agent_info.get("prompt_data") if agent_info else None

    def list_agents(self) -> list[dict[str, Any]]:
        """List all registered agents."""
        return list(self.agent_registry.values())

    def get_stats(self) -> dict[str, Any]:
        """Get prompt loader statistics."""
        return {
            "total_prompts": len(self.prompts_cache),
            "total_agents": len(self.agent_registry),
            "watching": self.observer is not None and self.observer.is_alive(),
            "prompts_dir": self.prompts_dir,
            "agent_list": list(self.agent_registry.keys()),
        }


# Global instance
dynamic_prompt_loader = DynamicPromptLoader()
