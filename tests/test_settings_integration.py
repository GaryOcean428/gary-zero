"""Tests for settings integration with new tools."""

from framework.helpers.settings import convert_out
from framework.helpers.settings.types import DEFAULT_SETTINGS


class TestSettingsIntegration:
    """Test settings integration for new tools."""

    def test_default_settings_include_new_tools(self):
        """Test that default settings include Computer Use and Claude Code settings."""
        defaults = DEFAULT_SETTINGS

        # Computer Use settings
        assert "computer_use_enabled" in defaults
        assert (
            defaults["computer_use_enabled"] is False
        )  # Should be disabled by default
        assert "computer_use_require_approval" in defaults
        assert defaults["computer_use_require_approval"] is True
        assert "computer_use_screenshot_interval" in defaults
        assert defaults["computer_use_screenshot_interval"] == 1.0
        assert "computer_use_max_actions_per_session" in defaults
        assert defaults["computer_use_max_actions_per_session"] == 50

        # Claude Code settings
        assert "claude_code_enabled" in defaults
        assert defaults["claude_code_enabled"] is False  # Should be disabled by default
        assert "claude_code_max_file_size" in defaults
        assert defaults["claude_code_max_file_size"] == 1048576  # 1MB
        assert "claude_code_enable_git_ops" in defaults
        assert defaults["claude_code_enable_git_ops"] is True
        assert "claude_code_enable_terminal" in defaults
        assert defaults["claude_code_enable_terminal"] is True

    def test_settings_sections_include_new_tools(self):
        """Test that settings sections include Computer Use and Claude Code."""
        settings_output = convert_out(DEFAULT_SETTINGS)

        # Find Computer Use section
        computer_use_section = None
        claude_code_section = None

        for section in settings_output["sections"]:
            if section["id"] == "computer_use":
                computer_use_section = section
            elif section["id"] == "claude_code":
                claude_code_section = section

        # Verify Computer Use section exists
        assert computer_use_section is not None
        assert computer_use_section["title"] == "Computer Use"
        assert computer_use_section["tab"] == "tools"
        assert len(computer_use_section["fields"]) == 4

        # Check Computer Use fields
        field_ids = [field["id"] for field in computer_use_section["fields"]]
        assert "computer_use_enabled" in field_ids
        assert "computer_use_require_approval" in field_ids
        assert "computer_use_screenshot_interval" in field_ids
        assert "computer_use_max_actions_per_session" in field_ids

        # Verify Claude Code section exists
        assert claude_code_section is not None
        assert claude_code_section["title"] == "Claude Code"
        assert claude_code_section["tab"] == "tools"
        assert len(claude_code_section["fields"]) == 4

        # Check Claude Code fields
        field_ids = [field["id"] for field in claude_code_section["fields"]]
        assert "claude_code_enabled" in field_ids
        assert "claude_code_max_file_size" in field_ids
        assert "claude_code_enable_git_ops" in field_ids
        assert "claude_code_enable_terminal" in field_ids

    def test_computer_use_field_properties(self):
        """Test Computer Use field properties."""
        settings_output = convert_out(DEFAULT_SETTINGS)

        computer_use_section = next(
            section
            for section in settings_output["sections"]
            if section["id"] == "computer_use"
        )

        # Test enabled field
        enabled_field = next(
            field
            for field in computer_use_section["fields"]
            if field["id"] == "computer_use_enabled"
        )
        assert enabled_field["type"] == "switch"
        assert enabled_field["value"] is False

        # Test screenshot interval field
        interval_field = next(
            field
            for field in computer_use_section["fields"]
            if field["id"] == "computer_use_screenshot_interval"
        )
        assert interval_field["type"] == "number"
        assert interval_field["min"] == 0.1
        assert interval_field["max"] == 10.0
        assert interval_field["step"] == 0.1

        # Test max actions field
        max_actions_field = next(
            field
            for field in computer_use_section["fields"]
            if field["id"] == "computer_use_max_actions_per_session"
        )
        assert max_actions_field["type"] == "number"
        assert max_actions_field["min"] == 1
        assert max_actions_field["max"] == 1000

    def test_claude_code_field_properties(self):
        """Test Claude Code field properties."""
        settings_output = convert_out(DEFAULT_SETTINGS)

        claude_code_section = next(
            section
            for section in settings_output["sections"]
            if section["id"] == "claude_code"
        )

        # Test enabled field
        enabled_field = next(
            field
            for field in claude_code_section["fields"]
            if field["id"] == "claude_code_enabled"
        )
        assert enabled_field["type"] == "switch"
        assert enabled_field["value"] is False

        # Test max file size field
        file_size_field = next(
            field
            for field in claude_code_section["fields"]
            if field["id"] == "claude_code_max_file_size"
        )
        assert file_size_field["type"] == "number"
        assert file_size_field["min"] == 1024
        assert file_size_field["max"] == 10485760  # 10MB

        # Test git ops field
        git_field = next(
            field
            for field in claude_code_section["fields"]
            if field["id"] == "claude_code_enable_git_ops"
        )
        assert git_field["type"] == "switch"

        # Test terminal field
        terminal_field = next(
            field
            for field in claude_code_section["fields"]
            if field["id"] == "claude_code_enable_terminal"
        )
        assert terminal_field["type"] == "switch"

    def test_tools_tab_existence(self):
        """Test that the tools tab exists for the new sections."""
        settings_output = convert_out(DEFAULT_SETTINGS)

        # Check that we have sections with "tools" tab
        tools_sections = [
            section
            for section in settings_output["sections"]
            if section.get("tab") == "tools"
        ]

        assert len(tools_sections) >= 2  # At least Computer Use and Claude Code

        section_ids = [section["id"] for section in tools_sections]
        assert "computer_use" in section_ids
        assert "claude_code" in section_ids

    def test_settings_descriptions(self):
        """Test that settings have appropriate descriptions."""
        settings_output = convert_out(DEFAULT_SETTINGS)

        # Computer Use section
        computer_use_section = next(
            section
            for section in settings_output["sections"]
            if section["id"] == "computer_use"
        )
        assert "desktop automation" in computer_use_section["description"].lower()
        assert "keyboard" in computer_use_section["description"].lower()
        assert "mouse" in computer_use_section["description"].lower()

        # Claude Code section
        claude_code_section = next(
            section
            for section in settings_output["sections"]
            if section["id"] == "claude_code"
        )
        assert "editing" in claude_code_section["description"].lower()
        assert "git" in claude_code_section["description"].lower()
        assert "terminal" in claude_code_section["description"].lower()

    def test_default_safety_settings(self):
        """Test that default settings prioritize safety."""
        defaults = DEFAULT_SETTINGS

        # Both tools should be disabled by default for safety
        assert defaults["computer_use_enabled"] is False
        assert defaults["claude_code_enabled"] is False

        # Computer Use should require approval by default
        assert defaults["computer_use_require_approval"] is True

        # File size limits should be reasonable
        assert defaults["claude_code_max_file_size"] <= 10 * 1024 * 1024  # Max 10MB

        # Action limits should be reasonable
        assert defaults["computer_use_max_actions_per_session"] <= 1000
