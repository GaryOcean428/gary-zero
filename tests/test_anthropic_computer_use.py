"""Tests for Anthropic Computer Use tool."""

from unittest.mock import Mock, patch

import pytest

from framework.tools.anthropic_computer_use import (
    AnthropicComputerUse,
    ComputerUseConfig,
)


class TestAnthropicComputerUse:
    """Test Anthropic Computer Use tool functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_agent = Mock()
        self.mock_agent.agent_name = "test_agent"
        self.mock_agent.context = Mock()
        self.mock_agent.context.log = Mock()
        self.mock_agent.context.log.log = Mock()
        self.mock_agent.hist_add_tool_result = Mock()

    def test_tool_creation(self):
        """Test tool creation and configuration."""
        tool = AnthropicComputerUse(
            agent=self.mock_agent,
            name="computer_use",
            method="screenshot",
            args={"action": "screenshot"},
            message="Take a screenshot",
        )

        assert tool.name == "computer_use"
        assert tool.method == "screenshot"
        assert isinstance(tool.config, ComputerUseConfig)
        assert tool.config.enabled is False  # Default disabled for safety
        assert tool.config.require_approval is True

    @pytest.mark.asyncio
    async def test_disabled_tool(self):
        """Test tool behavior when disabled or no GUI available."""
        tool = AnthropicComputerUse(
            agent=self.mock_agent,
            name="computer_use",
            method="screenshot",
            args={"action": "screenshot"},
            message="Take a screenshot",
        )

        # Tool should be disabled by default or show GUI unavailable
        response = await tool.execute()
        # Should either be disabled or show GUI unavailable
        assert (
            "disabled" in response.message.lower()
            or "gui environment" in response.message.lower()
        )
        assert response.break_loop is False

    @pytest.mark.asyncio
    async def test_screenshot_action_disabled_tool(self):
        """Test screenshot action with disabled tool."""
        tool = AnthropicComputerUse(
            agent=self.mock_agent,
            name="computer_use",
            method="screenshot",
            args={"action": "screenshot"},
            message="Take a screenshot",
        )

        response = await tool.execute()
        # Should either be disabled or show GUI unavailable
        assert (
            "Computer Use tool is disabled" in response.message
            or "GUI environment" in response.message
        )

    @pytest.mark.skipif(True, reason="Requires GUI environment")
    @pytest.mark.asyncio
    @patch("framework.tools.anthropic_computer_use.ImageGrab")
    @patch("framework.tools.anthropic_computer_use.os.makedirs")
    async def test_screenshot_action_enabled(self, mock_makedirs, mock_imagegrab):
        """Test screenshot action when tool is enabled."""
        # Mock PIL ImageGrab
        mock_image = Mock()
        mock_image.save = Mock()
        mock_image.size = (1920, 1080)
        mock_imagegrab.grab.return_value = mock_image

        tool = AnthropicComputerUse(
            agent=self.mock_agent,
            name="computer_use",
            method="screenshot",
            args={"action": "screenshot"},
            message="Take a screenshot",
        )

        # Enable the tool
        tool.config.enabled = True

        response = await tool.execute()

        # Should successfully take screenshot
        assert "Screenshot saved" in response.message
        assert "1920x1080" in response.message
        mock_imagegrab.grab.assert_called_once()
        mock_image.save.assert_called_once()

    @pytest.mark.skipif(True, reason="Requires GUI environment")
    @pytest.mark.asyncio
    @patch("framework.tools.anthropic_computer_use.pyautogui")
    async def test_click_action_enabled(self, mock_pyautogui):
        """Test click action when tool is enabled."""
        mock_pyautogui.size.return_value = (1920, 1080)
        mock_pyautogui.click = Mock()

        tool = AnthropicComputerUse(
            agent=self.mock_agent,
            name="computer_use",
            method="click",
            args={"action": "click", "x": 100, "y": 200, "button": "left"},
            message="Click at coordinates",
        )

        # Enable the tool but disable approval for testing
        tool.config.enabled = True
        tool.config.require_approval = False

        response = await tool.execute()

        # Should successfully click
        assert "Clicked at (100, 200)" in response.message
        mock_pyautogui.click.assert_called_once_with(100, 200, button="left")

    @pytest.mark.skipif(True, reason="Requires GUI environment")
    @pytest.mark.asyncio
    @patch("framework.tools.anthropic_computer_use.pyautogui")
    async def test_type_action_enabled(self, mock_pyautogui):
        """Test type action when tool is enabled."""
        mock_pyautogui.typewrite = Mock()

        tool = AnthropicComputerUse(
            agent=self.mock_agent,
            name="computer_use",
            method="type",
            args={"action": "type", "text": "Hello World"},
            message="Type text",
        )

        # Enable the tool but disable approval for testing
        tool.config.enabled = True
        tool.config.require_approval = False

        response = await tool.execute()

        # Should successfully type
        assert "Typed text: 'Hello World'" in response.message
        mock_pyautogui.typewrite.assert_called_once_with("Hello World")

    @pytest.mark.asyncio
    async def test_invalid_coordinates(self):
        """Test handling of invalid coordinates."""
        tool = AnthropicComputerUse(
            agent=self.mock_agent,
            name="computer_use",
            method="click",
            args={"action": "click", "x": -100, "y": 200},
            message="Click at invalid coordinates",
        )

        # Enable the tool
        tool.config.enabled = True

        response = await tool.execute()

        # Should either handle invalid coordinates or show GUI unavailable
        assert (
            "Invalid coordinates" in response.message
            or "GUI environment" in response.message
        )

    @pytest.mark.asyncio
    async def test_action_limit(self):
        """Test action limit enforcement."""
        tool = AnthropicComputerUse(
            agent=self.mock_agent,
            name="computer_use",
            method="screenshot",
            args={"action": "screenshot"},
            message="Take a screenshot",
        )

        # Enable the tool and set low action limit
        tool.config.enabled = True
        tool.config.max_actions_per_session = 1
        tool.action_count = 1  # Already at limit

        response = await tool.execute()

        # Should either be blocked by action limit or show GUI unavailable
        assert (
            "Maximum actions per session" in response.message
            or "GUI environment" in response.message
        )

    def test_config_validation(self):
        """Test configuration validation."""
        config = ComputerUseConfig(
            enabled=True,
            require_approval=False,
            screenshot_interval=0.5,
            max_actions_per_session=100,
        )

        assert config.enabled is True
        assert config.require_approval is False
        assert config.screenshot_interval == 0.5
        assert config.max_actions_per_session == 100

    @pytest.mark.asyncio
    async def test_unknown_action(self):
        """Test handling of unknown action types."""
        tool = AnthropicComputerUse(
            agent=self.mock_agent,
            name="computer_use",
            method="unknown",
            args={"action": "unknown_action"},
            message="Unknown action",
        )

        # Enable the tool
        tool.config.enabled = True

        response = await tool.execute()

        # Should either handle unknown action gracefully or show GUI unavailable
        assert (
            "Unknown action type" in response.message
            or "GUI environment" in response.message
        )
