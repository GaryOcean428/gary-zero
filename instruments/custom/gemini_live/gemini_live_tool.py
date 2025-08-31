"""
Google Gemini Live API integration tool.

This module provides a tool for interacting with Google's Gemini Live API.
"""

import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass

from .streaming_client import GeminiLiveClient


@dataclass
class Response:
    """Response object for tool operations."""

    message: str
    break_loop: bool = False


class GeminiLiveTool:
    """Tool for Google Gemini Live API integration."""

    def __init__(self):
        """Initialize the Gemini Live tool."""
        self.args: Dict[str, Any] = {}
        self.client: Optional[GeminiLiveClient] = None
        self.is_streaming: bool = False

    async def execute(self) -> Response:
        """Execute the tool based on the configured arguments.

        Returns:
            Response object with execution results
        """
        action = self.args.get("action", "").lower().strip()

        try:
            if action == "status":
                return await self._handle_status()
            elif action == "configure":
                return await self._handle_configure()
            elif action == "start":
                return await self._handle_start_streaming()
            elif action == "stop":
                return await self._handle_stop_streaming()
            elif action == "send_audio":
                return await self._handle_send_audio()
            else:
                return Response(
                    message=f"❌ Unknown action: {action}. Available actions: status, configure, start, stop, send_audio",
                    break_loop=False,
                )
        except Exception as e:
            return Response(
                message=f"❌ Error executing action '{action}': {str(e)}",
                break_loop=False,
            )

    async def _handle_status(self) -> Response:
        """Handle status check."""
        api_key = self.args.get("api_key") or os.getenv("GEMINI_API_KEY")
        model = self.args.get(
            "model", "models/gemini-2.5-flash-preview-native-audio-dialog"
        )

        status_info = {
            "api_key_configured": bool(api_key),
            "model": model,
            "streaming_active": self.is_streaming,
            "client_connected": self.client.is_connected if self.client else False,
        }

        message = f"**Gemini Live API Status**\n"
        message += f"• API Key: {'✅ Configured' if status_info['api_key_configured'] else '❌ Not configured'}\n"
        message += f"• Model: {status_info['model']}\n"
        message += f"• Streaming: {'🟢 Active' if status_info['streaming_active'] else '🔴 Inactive'}\n"
        message += f"• Client: {'🟢 Connected' if status_info['client_connected'] else '🔴 Disconnected'}"

        return Response(message=message, break_loop=False)

    async def _handle_configure(self) -> Response:
        """Handle configuration."""
        voice = self.args.get("voice")
        response_modalities = self.args.get("response_modalities")
        model = self.args.get("model")

        config_changes = []

        if voice:
            config_changes.append(f"Voice: {voice}")
        if response_modalities:
            config_changes.append(f"Modalities: {', '.join(response_modalities)}")
        if model:
            config_changes.append(f"Model: {model}")

        if self.client:
            await self.client.configure(
                voice=voice, response_modalities=response_modalities, model=model
            )

        if config_changes:
            message = f"**Configuration Updated**\n" + "\n".join(
                f"• {change}" for change in config_changes
            )
        else:
            message = f"**Current Configuration**\n"
            message += f"• Available Voices: Zephyr, Echo, Crystal, Sage\n"
            message += f"• Available Modalities: AUDIO, VIDEO (coming soon)\n"
            message += (
                f"• Default Model: models/gemini-2.5-flash-preview-native-audio-dialog"
            )

        return Response(message=message, break_loop=False)

    async def _handle_start_streaming(self) -> Response:
        """Handle starting streaming session."""
        api_key = self.args.get("api_key") or os.getenv("GEMINI_API_KEY")

        if not api_key:
            return Response(
                message="❌ Cannot start streaming: GEMINI_API_KEY not configured",
                break_loop=False,
            )

        if self.is_streaming:
            return Response(
                message="⚠️ Streaming session already active", break_loop=False
            )

        # Create client if needed
        if not self.client:
            model = self.args.get(
                "model", "models/gemini-2.5-flash-preview-native-audio-dialog"
            )
            voice = self.args.get("voice", "Zephyr")
            response_modalities = self.args.get("response_modalities", ["AUDIO"])

            self.client = GeminiLiveClient(
                api_key=api_key,
                model_name=model,
                voice_name=voice,
                response_modalities=response_modalities,
            )

        # Connect client
        connected = await self.client.connect()
        if connected:
            self.is_streaming = True
            return Response(
                message="🟢 Streaming session started successfully", break_loop=False
            )
        else:
            return Response(
                message="❌ Failed to start streaming session", break_loop=False
            )

    async def _handle_stop_streaming(self) -> Response:
        """Handle stopping streaming session."""
        if not self.is_streaming:
            return Response(
                message="⚠️ No active streaming session to stop", break_loop=False
            )

        if self.client:
            await self.client.disconnect()

        self.is_streaming = False

        return Response(message="🔴 Streaming session stopped", break_loop=False)

    async def _handle_send_audio(self) -> Response:
        """Handle sending audio data."""
        if not self.is_streaming:
            return Response(
                message="❌ Cannot send audio: No active streaming session",
                break_loop=False,
            )

        audio_data = self.args.get("audio_data")
        if not audio_data:
            return Response(message="❌ No audio data provided", break_loop=False)

        if self.client:
            # Convert base64 audio data to bytes if needed
            try:
                if isinstance(audio_data, str):
                    import base64

                    audio_bytes = base64.b64decode(audio_data)
                else:
                    audio_bytes = audio_data

                success = await self.client.send_audio(audio_bytes)
                if success:
                    return Response(
                        message="🎵 Audio data sent successfully", break_loop=False
                    )
                else:
                    return Response(
                        message="❌ Failed to send audio data", break_loop=False
                    )
            except Exception as e:
                return Response(
                    message=f"❌ Error processing audio data: {str(e)}",
                    break_loop=False,
                )

        return Response(
            message="❌ No client available to send audio", break_loop=False
        )


def get_tool() -> GeminiLiveTool:
    """Factory function to create a new GeminiLiveTool instance."""
    return GeminiLiveTool()
