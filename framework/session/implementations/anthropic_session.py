"""
Anthropic Computer Use Session Implementation.

Provides session management for Anthropic Computer Use GUI automation.
"""

import os
import time
import uuid
from typing import Any

from ..session_interface import (
    SessionInterface,
    SessionMessage,
    SessionResponse,
    SessionState,
    SessionType,
)

# Import GUI dependencies conditionally
try:
    import pyautogui
    from PIL import Image, ImageGrab

    GUI_AVAILABLE = True
except (ImportError, Exception) as e:
    GUI_AVAILABLE = False
    GUI_IMPORT_ERROR = str(e)


class AnthropicSession(SessionInterface):
    """Session implementation for Anthropic Computer Use GUI automation."""

    def __init__(self, config: dict[str, Any]):
        """
        Initialize Anthropic Computer Use session.

        Args:
            config: Configuration dictionary with Anthropic settings
        """
        session_id = str(uuid.uuid4())
        super().__init__(session_id, SessionType.GUI, config)

        self.require_approval = config.get("require_approval", True)
        self.screenshot_interval = config.get("screenshot_interval", 1.0)
        self.max_actions_per_session = config.get("max_actions_per_session", 50)

        # State tracking
        self.action_count = 0
        self._gui_available = GUI_AVAILABLE

        if self._gui_available:
            # Configure PyAutoGUI settings
            pyautogui.FAILSAFE = True
            pyautogui.PAUSE = 0.1

    async def connect(self) -> SessionResponse:
        """
        Establish connection to GUI environment.

        Returns:
            SessionResponse indicating connection success or failure
        """
        try:
            await self.update_state(SessionState.INITIALIZING)

            if not self._gui_available:
                await self.update_state(
                    SessionState.ERROR, f"GUI not available: {GUI_IMPORT_ERROR}"
                )
                return SessionResponse(
                    success=False,
                    message="GUI environment not available",
                    error=f"Missing dependencies: {GUI_IMPORT_ERROR}",
                    session_id=self.session_id,
                )

            # Test basic GUI operations
            try:
                screen_size = pyautogui.size()
                await self.update_state(SessionState.CONNECTED)

                return SessionResponse(
                    success=True,
                    message=f"Connected to GUI environment: {screen_size[0]}x{screen_size[1]}",
                    data={
                        "screen_size": {
                            "width": screen_size[0],
                            "height": screen_size[1],
                        }
                    },
                    session_id=self.session_id,
                )
            except Exception as gui_error:
                await self.update_state(SessionState.ERROR, str(gui_error))
                return SessionResponse(
                    success=False,
                    message="GUI environment test failed",
                    error=str(gui_error),
                    session_id=self.session_id,
                )

        except Exception as e:
            await self.update_state(SessionState.ERROR, str(e))
            return SessionResponse(
                success=False,
                message=f"Connection failed: {str(e)}",
                error=str(e),
                session_id=self.session_id,
            )

    async def disconnect(self) -> SessionResponse:
        """
        Disconnect from GUI environment.

        Returns:
            SessionResponse indicating disconnection status
        """
        await self.update_state(SessionState.DISCONNECTED)
        return SessionResponse(
            success=True,
            message="Disconnected from GUI environment",
            session_id=self.session_id,
        )

    async def execute(self, message: SessionMessage) -> SessionResponse:
        """
        Execute a GUI automation action.

        Args:
            message: Message containing the action to execute

        Returns:
            SessionResponse with action results
        """
        try:
            if not self._gui_available:
                return SessionResponse(
                    success=False,
                    message="GUI environment not available",
                    error="GUI dependencies not installed",
                    session_id=self.session_id,
                )

            # Check action limit
            if self.action_count >= self.max_actions_per_session:
                return SessionResponse(
                    success=False,
                    message=f"Maximum actions per session ({self.max_actions_per_session}) reached",
                    error="Action limit exceeded",
                    session_id=self.session_id,
                )

            await self.update_state(SessionState.ACTIVE)

            action = message.payload.get("action", "screenshot")

            if action == "screenshot":
                result = await self._take_screenshot(message.payload)
            elif action == "click":
                result = await self._perform_click(message.payload)
            elif action == "type":
                result = await self._perform_type(message.payload)
            elif action == "key":
                result = await self._perform_key(message.payload)
            elif action == "move":
                result = await self._perform_move(message.payload)
            elif action == "scroll":
                result = await self._perform_scroll(message.payload)
            else:
                return SessionResponse(
                    success=False,
                    message=f"Unknown action: {action}",
                    error=f"Unsupported action: {action}",
                    session_id=self.session_id,
                )

            self.action_count += 1
            return result

        except Exception as e:
            await self.update_state(SessionState.ERROR, str(e))
            return SessionResponse(
                success=False,
                message=f"Execution failed: {str(e)}",
                error=str(e),
                session_id=self.session_id,
            )
        finally:
            await self.update_state(SessionState.IDLE)

    async def health_check(self) -> SessionResponse:
        """
        Check if the GUI session is healthy.

        Returns:
            SessionResponse indicating session health
        """
        try:
            if not self._gui_available:
                return SessionResponse(
                    success=False,
                    message="GUI not available",
                    session_id=self.session_id,
                )

            # Test basic GUI operation
            screen_size = pyautogui.size()

            return SessionResponse(
                success=True,
                message="Session healthy",
                data={
                    "screen_size": {"width": screen_size[0], "height": screen_size[1]}
                },
                session_id=self.session_id,
            )

        except Exception as e:
            return SessionResponse(
                success=False,
                message=f"Health check failed: {str(e)}",
                error=str(e),
                session_id=self.session_id,
            )

    async def _take_screenshot(self, payload: dict[str, Any]) -> SessionResponse:
        """Take a screenshot of the current screen."""
        try:
            screenshot = ImageGrab.grab()

            # Save to tmp directory
            timestamp = int(time.time())
            filename = f"screenshot_{self.session_id}_{timestamp}.png"
            filepath = os.path.join("tmp", filename)

            # Ensure tmp directory exists
            os.makedirs("tmp", exist_ok=True)

            screenshot.save(filepath)

            # Get screen dimensions
            width, height = screenshot.size

            return SessionResponse(
                success=True,
                message=f"Screenshot saved as {filepath}",
                data={
                    "filepath": filepath,
                    "filename": filename,
                    "dimensions": {"width": width, "height": height},
                },
                session_id=self.session_id,
            )

        except Exception as e:
            return SessionResponse(
                success=False,
                message=f"Screenshot failed: {str(e)}",
                error=str(e),
                session_id=self.session_id,
            )

    async def _perform_click(self, payload: dict[str, Any]) -> SessionResponse:
        """Perform mouse click."""
        try:
            x = int(payload.get("x", 0))
            y = int(payload.get("y", 0))
            button = payload.get("button", "left")
            double_click = payload.get("double_click", False)

            # Validate coordinates
            screen_width, screen_height = pyautogui.size()
            if x < 0 or x > screen_width or y < 0 or y > screen_height:
                return SessionResponse(
                    success=False,
                    message=f"Invalid coordinates: ({x}, {y}). Screen size: {screen_width}x{screen_height}",
                    error="Coordinates out of bounds",
                    session_id=self.session_id,
                )

            # Perform click
            if double_click:
                pyautogui.doubleClick(x, y, button=button)
                action_desc = f"Double-clicked at ({x}, {y}) with {button} button"
            else:
                pyautogui.click(x, y, button=button)
                action_desc = f"Clicked at ({x}, {y}) with {button} button"

            return SessionResponse(
                success=True,
                message=action_desc,
                data={"action": action_desc, "coordinates": {"x": x, "y": y}},
                session_id=self.session_id,
            )

        except Exception as e:
            return SessionResponse(
                success=False,
                message=f"Click failed: {str(e)}",
                error=str(e),
                session_id=self.session_id,
            )

    async def _perform_type(self, payload: dict[str, Any]) -> SessionResponse:
        """Type text."""
        try:
            text = payload.get("text", "")
            if not text:
                return SessionResponse(
                    success=False,
                    message="No text provided to type",
                    error="Missing text parameter",
                    session_id=self.session_id,
                )

            pyautogui.typewrite(text)

            return SessionResponse(
                success=True,
                message=f"Typed text: '{text}'",
                data={"text": text},
                session_id=self.session_id,
            )

        except Exception as e:
            return SessionResponse(
                success=False,
                message=f"Type failed: {str(e)}",
                error=str(e),
                session_id=self.session_id,
            )

    async def _perform_key(self, payload: dict[str, Any]) -> SessionResponse:
        """Press keyboard keys."""
        try:
            keys = payload.get("keys", "")
            if not keys:
                return SessionResponse(
                    success=False,
                    message="No keys provided",
                    error="Missing keys parameter",
                    session_id=self.session_id,
                )

            # Handle key combinations
            if "+" in keys:
                key_combo = [k.strip() for k in keys.split("+")]
                pyautogui.hotkey(*key_combo)
                action_desc = f"Pressed key combination: {keys}"
            else:
                pyautogui.press(keys)
                action_desc = f"Pressed key: {keys}"

            return SessionResponse(
                success=True,
                message=action_desc,
                data={"keys": keys},
                session_id=self.session_id,
            )

        except Exception as e:
            return SessionResponse(
                success=False,
                message=f"Key press failed: {str(e)}",
                error=str(e),
                session_id=self.session_id,
            )

    async def _perform_move(self, payload: dict[str, Any]) -> SessionResponse:
        """Move mouse cursor."""
        try:
            x = int(payload.get("x", 0))
            y = int(payload.get("y", 0))

            # Validate coordinates
            screen_width, screen_height = pyautogui.size()
            if x < 0 or x > screen_width or y < 0 or y > screen_height:
                return SessionResponse(
                    success=False,
                    message=f"Invalid coordinates: ({x}, {y}). Screen size: {screen_width}x{screen_height}",
                    error="Coordinates out of bounds",
                    session_id=self.session_id,
                )

            pyautogui.moveTo(x, y)

            return SessionResponse(
                success=True,
                message=f"Moved mouse to ({x}, {y})",
                data={"coordinates": {"x": x, "y": y}},
                session_id=self.session_id,
            )

        except Exception as e:
            return SessionResponse(
                success=False,
                message=f"Mouse move failed: {str(e)}",
                error=str(e),
                session_id=self.session_id,
            )

    async def _perform_scroll(self, payload: dict[str, Any]) -> SessionResponse:
        """Perform scroll action."""
        try:
            x = int(payload.get("x", 0))
            y = int(payload.get("y", 0))
            direction = payload.get("direction", "down")
            clicks = int(payload.get("clicks", 3))

            # Move to position and scroll
            pyautogui.moveTo(x, y)

            if direction in ["up", "down"]:
                scroll_amount = clicks if direction == "up" else -clicks
                pyautogui.scroll(scroll_amount, x, y)
                action_desc = f"Scrolled {direction} {clicks} clicks at ({x}, {y})"
            else:
                return SessionResponse(
                    success=False,
                    message=f"Unsupported scroll direction: {direction}",
                    error="Invalid scroll direction",
                    session_id=self.session_id,
                )

            return SessionResponse(
                success=True,
                message=action_desc,
                data={"action": action_desc, "coordinates": {"x": x, "y": y}},
                session_id=self.session_id,
            )

        except Exception as e:
            return SessionResponse(
                success=False,
                message=f"Scroll failed: {str(e)}",
                error=str(e),
                session_id=self.session_id,
            )
