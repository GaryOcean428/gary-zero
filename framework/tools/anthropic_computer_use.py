"""
Anthropic Computer Use Tool for Desktop and GUI Automation.

This tool integrates Anthropic's computer-use capabilities to enable 
agent automation of desktop tasks through keyboard, mouse, and window control.
"""

import asyncio
import base64
import io
import os
import time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from framework.helpers.tool import Response, Tool
from framework.helpers.print_style import PrintStyle

# Import GUI dependencies conditionally
try:
    from PIL import Image, ImageGrab
    import pyautogui
    GUI_AVAILABLE = True
except (ImportError, Exception) as e:
    GUI_AVAILABLE = False
    GUI_IMPORT_ERROR = str(e)


class ComputerUseConfig(BaseModel):
    """Configuration for Computer Use tool."""
    enabled: bool = Field(default=False, description="Enable computer use functionality")
    require_approval: bool = Field(default=True, description="Require approval for actions")
    screenshot_interval: float = Field(default=1.0, description="Interval between screenshots")
    max_actions_per_session: int = Field(default=50, description="Maximum actions per session")


class ScreenshotAction(BaseModel):
    """Take a screenshot of the current screen."""
    action: str = "screenshot"


class ClickAction(BaseModel):
    """Click at specified coordinates."""
    action: str = "click"
    x: int = Field(description="X coordinate to click")
    y: int = Field(description="Y coordinate to click")
    button: str = Field(default="left", description="Mouse button: left, right, middle")
    double_click: bool = Field(default=False, description="Perform double click")


class TypeAction(BaseModel):
    """Type text at current cursor position."""
    action: str = "type"
    text: str = Field(description="Text to type")


class KeyAction(BaseModel):
    """Press keyboard keys."""
    action: str = "key"
    keys: str = Field(description="Key combination (e.g., 'ctrl+c', 'enter', 'tab')")


class MoveAction(BaseModel):
    """Move mouse to coordinates."""
    action: str = "move"
    x: int = Field(description="X coordinate to move to")
    y: int = Field(description="Y coordinate to move to")


class ScrollAction(BaseModel):
    """Scroll at coordinates."""
    action: str = "scroll"
    x: int = Field(description="X coordinate to scroll at")
    y: int = Field(description="Y coordinate to scroll at")
    direction: str = Field(description="Scroll direction: up, down, left, right")
    clicks: int = Field(default=3, description="Number of scroll clicks")


class AnthropicComputerUse(Tool):
    """Anthropic Computer Use tool for desktop automation."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.action_count = 0
        self.config = ComputerUseConfig()
        self.setup_pyautogui()

    def setup_pyautogui(self):
        """Configure PyAutoGUI settings."""
        if not GUI_AVAILABLE:
            return
        # Disable PyAutoGUI's fail-safe
        pyautogui.FAILSAFE = True
        # Set pause between actions
        pyautogui.PAUSE = 0.1

    async def execute(self, **kwargs) -> Response:
        """Execute computer use action."""
        try:
            # Check if GUI is available
            if not GUI_AVAILABLE:
                return Response(
                    message=f"Computer Use tool requires GUI environment. Error: {GUI_IMPORT_ERROR}",
                    break_loop=False
                )

            # Check if tool is enabled
            if not self.config.enabled:
                return Response(
                    message="Computer Use tool is disabled. Enable it in settings to use desktop automation.",
                    break_loop=False
                )

            # Check action limit
            if self.action_count >= self.config.max_actions_per_session:
                return Response(
                    message=f"Maximum actions per session ({self.config.max_actions_per_session}) reached.",
                    break_loop=False
                )

            action_type = self.args.get("action", "screenshot")
            
            # Handle different action types
            if action_type == "screenshot":
                result = await self.take_screenshot()
            elif action_type == "click":
                result = await self.perform_click()
            elif action_type == "type":
                result = await self.perform_type()
            elif action_type == "key":
                result = await self.perform_key()
            elif action_type == "move":
                result = await self.perform_move()
            elif action_type == "scroll":
                result = await self.perform_scroll()
            else:
                result = f"Unknown action type: {action_type}"

            self.action_count += 1
            return Response(message=result, break_loop=False)

        except Exception as e:
            error_msg = f"Computer Use error: {str(e)}"
            PrintStyle(font_color="red").print(error_msg)
            return Response(message=error_msg, break_loop=False)

    async def take_screenshot(self) -> str:
        """Take and save a screenshot."""
        try:
            # Take screenshot
            screenshot = ImageGrab.grab()
            
            # Save to tmp directory
            timestamp = int(time.time())
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join("tmp", filename)
            
            # Ensure tmp directory exists
            os.makedirs("tmp", exist_ok=True)
            
            screenshot.save(filepath)
            
            # Get screen dimensions
            width, height = screenshot.size
            
            return f"Screenshot saved as {filepath}. Screen dimensions: {width}x{height}"
            
        except Exception as e:
            return f"Failed to take screenshot: {str(e)}"

    async def perform_click(self) -> str:
        """Perform mouse click."""
        try:
            x = int(self.args.get("x", 0))
            y = int(self.args.get("y", 0))
            button = self.args.get("button", "left")
            double_click = self.args.get("double_click", False)

            # Validate coordinates
            screen_width, screen_height = pyautogui.size()
            if x < 0 or x > screen_width or y < 0 or y > screen_height:
                return f"Invalid coordinates: ({x}, {y}). Screen size: {screen_width}x{screen_height}"

            # Request approval if required
            if self.config.require_approval:
                action_desc = f"{'Double-click' if double_click else 'Click'} at ({x}, {y}) with {button} button"
                if not await self.request_approval(action_desc):
                    return "Action cancelled by user"

            # Perform click
            if double_click:
                pyautogui.doubleClick(x, y, button=button)
                return f"Double-clicked at ({x}, {y}) with {button} button"
            else:
                pyautogui.click(x, y, button=button)
                return f"Clicked at ({x}, {y}) with {button} button"

        except Exception as e:
            return f"Click failed: {str(e)}"

    async def perform_type(self) -> str:
        """Type text."""
        try:
            text = self.args.get("text", "")
            if not text:
                return "No text provided to type"

            # Request approval if required
            if self.config.require_approval:
                action_desc = f"Type text: '{text[:50]}{'...' if len(text) > 50 else ''}'"
                if not await self.request_approval(action_desc):
                    return "Action cancelled by user"

            # Type text
            pyautogui.typewrite(text)
            return f"Typed text: '{text}'"

        except Exception as e:
            return f"Type failed: {str(e)}"

    async def perform_key(self) -> str:
        """Press keyboard keys."""
        try:
            keys = self.args.get("keys", "")
            if not keys:
                return "No keys provided"

            # Request approval if required
            if self.config.require_approval:
                action_desc = f"Press keys: '{keys}'"
                if not await self.request_approval(action_desc):
                    return "Action cancelled by user"

            # Handle key combinations
            if "+" in keys:
                key_combo = [k.strip() for k in keys.split("+")]
                pyautogui.hotkey(*key_combo)
                return f"Pressed key combination: {keys}"
            else:
                pyautogui.press(keys)
                return f"Pressed key: {keys}"

        except Exception as e:
            return f"Key press failed: {str(e)}"

    async def perform_move(self) -> str:
        """Move mouse cursor."""
        try:
            x = int(self.args.get("x", 0))
            y = int(self.args.get("y", 0))

            # Validate coordinates
            screen_width, screen_height = pyautogui.size()
            if x < 0 or x > screen_width or y < 0 or y > screen_height:
                return f"Invalid coordinates: ({x}, {y}). Screen size: {screen_width}x{screen_height}"

            # Move mouse
            pyautogui.moveTo(x, y)
            return f"Moved mouse to ({x}, {y})"

        except Exception as e:
            return f"Mouse move failed: {str(e)}"

    async def perform_scroll(self) -> str:
        """Perform scroll action."""
        try:
            x = int(self.args.get("x", 0))
            y = int(self.args.get("y", 0))
            direction = self.args.get("direction", "down")
            clicks = int(self.args.get("clicks", 3))

            # Move to position and scroll
            pyautogui.moveTo(x, y)
            
            if direction in ["up", "down"]:
                scroll_amount = clicks if direction == "up" else -clicks
                pyautogui.scroll(scroll_amount, x, y)
            else:
                return f"Unsupported scroll direction: {direction}"

            return f"Scrolled {direction} {clicks} clicks at ({x}, {y})"

        except Exception as e:
            return f"Scroll failed: {str(e)}"

    async def request_approval(self, action_description: str) -> bool:
        """Request user approval for an action."""
        # This would typically integrate with the agent's intervention system
        # For now, we'll implement a simple approval mechanism
        
        PrintStyle(font_color="yellow", bold=True).print(
            f"⚠️  Computer Use Action Requires Approval: {action_description}"
        )
        
        # In a real implementation, this would pause execution and wait for user input
        # For now, we'll assume approval is granted
        # TODO: Integrate with agent intervention system
        
        return True

    async def before_execution(self, **kwargs):
        """Pre-execution setup."""
        await super().before_execution(**kwargs)
        
        # Display safety warning
        PrintStyle(font_color="yellow", bold=True).print(
            "⚠️  Computer Use tool can control your desktop. Use with caution!"
        )