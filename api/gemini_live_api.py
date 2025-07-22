"""
API endpoints for Google Gemini Live API integration.

This module provides FastAPI endpoints for managing Gemini Live API
streaming sessions and configuration.
"""

import os
import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import logging

from instruments.custom.gemini_live.gemini_live_tool import GeminiLiveTool

logger = logging.getLogger(__name__)

# Create router for Gemini Live API endpoints
router = APIRouter(prefix="/api/gemini-live", tags=["gemini-live"])

# Global tool instance
gemini_live_tool: Optional[GeminiLiveTool] = None


class GeminiLiveRequest(BaseModel):
    """Request model for Gemini Live API operations."""
    action: str
    api_key: Optional[str] = None
    model: Optional[str] = None
    voice: Optional[str] = None
    response_modalities: Optional[list] = None
    audio_config: Optional[Dict[str, Any]] = None
    audio_data: Optional[str] = None


class GeminiLiveResponse(BaseModel):
    """Response model for Gemini Live API operations."""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


def get_gemini_live_tool() -> GeminiLiveTool:
    """Get or create the Gemini Live tool instance."""
    global gemini_live_tool
    if gemini_live_tool is None:
        gemini_live_tool = GeminiLiveTool()
    return gemini_live_tool


@router.post("/test", response_model=GeminiLiveResponse)
async def test_connection(request: GeminiLiveRequest):
    """Test connection to Gemini Live API."""
    try:
        tool = get_gemini_live_tool()
        
        # Prepare arguments for the tool
        tool.args = {
            "action": "status",
            "api_key": request.api_key or os.getenv("GEMINI_API_KEY"),
            "model": request.model or "models/gemini-2.5-flash-preview-native-audio-dialog"
        }
        
        # Execute the tool
        response = await tool.execute()
        
        return GeminiLiveResponse(
            success=True,
            message="Connection test successful",
            details={
                "api_key_present": bool(request.api_key or os.getenv("GEMINI_API_KEY")),
                "model": request.model or "models/gemini-2.5-flash-preview-native-audio-dialog",
                "tool_response": response.message
            }
        )
        
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return GeminiLiveResponse(
            success=False,
            error=str(e),
            details={"error_type": type(e).__name__}
        )


@router.post("/stream", response_model=GeminiLiveResponse)
async def manage_streaming(request: GeminiLiveRequest):
    """Start or stop streaming session."""
    try:
        tool = get_gemini_live_tool()
        
        # Prepare arguments for the tool
        tool.args = {
            "action": request.action,
            "api_key": request.api_key or os.getenv("GEMINI_API_KEY"),
            "model": request.model or os.getenv("GEMINI_LIVE_MODEL", "models/gemini-2.5-flash-preview-native-audio-dialog"),
            "voice": request.voice or os.getenv("GEMINI_LIVE_VOICE", "Zephyr"),
            "response_modalities": request.response_modalities or ["AUDIO"]
        }
        
        # Add audio configuration if provided
        if request.audio_config:
            tool.args.update(request.audio_config)
        
        # Execute the tool
        response = await tool.execute()
        
        return GeminiLiveResponse(
            success=True,
            message=response.message,
            details={
                "action": request.action,
                "streaming_active": tool.is_streaming if hasattr(tool, 'is_streaming') else False
            }
        )
        
    except Exception as e:
        logger.error(f"Streaming management failed: {e}")
        return GeminiLiveResponse(
            success=False,
            error=str(e),
            details={"error_type": type(e).__name__}
        )


@router.post("/audio", response_model=GeminiLiveResponse)
async def send_audio(request: GeminiLiveRequest):
    """Send audio data to the streaming session."""
    try:
        if not request.audio_data:
            raise ValueError("No audio data provided")
        
        tool = get_gemini_live_tool()
        
        # Prepare arguments for the tool
        tool.args = {
            "action": "send_audio",
            "audio_data": request.audio_data
        }
        
        # Execute the tool
        response = await tool.execute()
        
        return GeminiLiveResponse(
            success=True,
            message=response.message
        )
        
    except Exception as e:
        logger.error(f"Audio sending failed: {e}")
        return GeminiLiveResponse(
            success=False,
            error=str(e),
            details={"error_type": type(e).__name__}
        )


@router.post("/configure", response_model=GeminiLiveResponse)
async def configure_streaming(request: GeminiLiveRequest):
    """Configure streaming parameters."""
    try:
        tool = get_gemini_live_tool()
        
        # Prepare arguments for the tool
        tool.args = {"action": "configure"}
        
        if request.voice:
            tool.args["voice"] = request.voice
        if request.response_modalities:
            tool.args["response_modalities"] = request.response_modalities
        if request.model:
            tool.args["model"] = request.model
        
        # Execute the tool
        response = await tool.execute()
        
        return GeminiLiveResponse(
            success=True,
            message=response.message
        )
        
    except Exception as e:
        logger.error(f"Configuration failed: {e}")
        return GeminiLiveResponse(
            success=False,
            error=str(e),
            details={"error_type": type(e).__name__}
        )


@router.get("/status", response_model=GeminiLiveResponse)
async def get_status():
    """Get current streaming status."""
    try:
        tool = get_gemini_live_tool()
        
        # Prepare arguments for the tool
        tool.args = {"action": "status"}
        
        # Execute the tool
        response = await tool.execute()
        
        return GeminiLiveResponse(
            success=True,
            message="Status retrieved successfully",
            details={
                "tool_response": response.message,
                "streaming_active": tool.is_streaming if hasattr(tool, 'is_streaming') else False
            }
        )
        
    except Exception as e:
        logger.error(f"Status retrieval failed: {e}")
        return GeminiLiveResponse(
            success=False,
            error=str(e),
            details={"error_type": type(e).__name__}
        )


@router.get("/config")
async def get_configuration():
    """Get current configuration options."""
    try:
        config = {
            "models": [
                {
                    "value": "models/gemini-2.5-flash-preview-native-audio-dialog",
                    "label": "Gemini 2.5 Flash (Audio Dialog)",
                    "default": True
                },
                {
                    "value": "models/gemini-2.5-pro-preview-native-audio-dialog", 
                    "label": "Gemini 2.5 Pro (Audio Dialog)",
                    "default": False
                },
                {
                    "value": "models/gemini-2.0-flash",
                    "label": "Gemini 2.0 Flash",
                    "default": False
                }
            ],
            "voices": [
                {"value": "Zephyr", "label": "Zephyr (Default)", "default": True},
                {"value": "Echo", "label": "Echo", "default": False},
                {"value": "Crystal", "label": "Crystal", "default": False},
                {"value": "Sage", "label": "Sage", "default": False}
            ],
            "modalities": [
                {"value": "AUDIO", "label": "Audio", "supported": True},
                {"value": "VIDEO", "label": "Video", "supported": False, "note": "Coming soon"}
            ],
            "environment": {
                "api_key_configured": bool(os.getenv("GEMINI_API_KEY")),
                "default_model": os.getenv("GEMINI_LIVE_MODEL", "models/gemini-2.5-flash-preview-native-audio-dialog"),
                "default_voice": os.getenv("GEMINI_LIVE_VOICE", "Zephyr"),
                "default_modalities": os.getenv("GEMINI_LIVE_RESPONSE_MODALITIES", "AUDIO").split(",")
            }
        }
        
        return config
        
    except Exception as e:
        logger.error(f"Configuration retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))