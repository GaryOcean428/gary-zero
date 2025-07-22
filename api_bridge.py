"""
API bridge to integrate existing Flask API handlers with FastAPI.

This module provides backward compatibility by allowing existing Flask-style 
API handlers to work with the new FastAPI application.
"""

import json
import time
import logging
from typing import Dict, Any, Optional, Type
from fastapi import FastAPI, Request, HTTPException, Depends, File, UploadFile, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import threading

# Set up logger
logger = logging.getLogger(__name__)

try:
    from framework.helpers.api import ApiHandler as FlaskApiHandler
except ImportError as e:
    logger.warning(f"Could not import Flask API handler: {e}")
    FlaskApiHandler = None
from security.validator import validate_code, SecurityLevel, is_code_safe

try:
    from framework.helpers.extract_tools import load_classes_from_folder
except ImportError:
    logger.warning("Could not import extract_tools, API bridge will be limited")
    def load_classes_from_folder(*args, **kwargs):
        return []

logger = logging.getLogger(__name__)

# Lock for thread-safe operations with existing agent system
_thread_lock = threading.Lock()

class ApiRequest(BaseModel):
    """Pydantic model for API requests."""
    text: Optional[str] = None
    context: Optional[str] = None
    message_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class ApiResponse(BaseModel):
    """Standard API response model."""
    success: bool = True
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: float = time.time()

class FlaskApiWrapper:
    """Wrapper to adapt Flask API handlers for FastAPI."""
    
    def __init__(self, handler_class: Type):
        self.handler_class = handler_class
        self.handler_name = handler_class.__module__.split('.')[-1] if handler_class else "unknown"
    
    async def handle_request(self, request_data: Dict[str, Any], 
                           fastapi_request: Request) -> Dict[str, Any]:
        """Handle the API request using the Flask handler."""
        
        # Create a mock Flask app for compatibility
        from flask import Flask
        mock_app = Flask(__name__)
        
        # Create handler instance
        handler = self.handler_class(mock_app, _thread_lock)
        
        # Create mock Flask request object
        class MockFlaskRequest:
            def __init__(self, data: Dict[str, Any], fastapi_req: Request):
                self.json_data = data
                self.fastapi_request = fastapi_req
                self.content_type = "application/json"
                
            def get_json(self):
                return self.json_data
            
            @property
            def is_json(self):
                return True
                
            def get_data(self, as_text=True):
                return json.dumps(self.json_data) if as_text else json.dumps(self.json_data).encode()
        
        mock_request = MockFlaskRequest(request_data, fastapi_request)
        
        try:
            # Process the request using the Flask handler
            result = await handler.process(request_data, mock_request)
            return result
        except Exception as e:
            logger.error(f"Error processing {self.handler_name}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

def create_api_bridge(app: FastAPI) -> None:
    """Create API bridge to integrate Flask handlers with FastAPI."""
    
    if FlaskApiHandler is None:
        logger.warning("Flask API handler not available, skipping API bridge")
        return
    
    # Load existing Flask API handlers
    try:
        handlers = load_classes_from_folder("framework/api", "*.py", FlaskApiHandler)
        logger.info(f"Found {len(handlers)} API handlers to bridge")
        
        # Create FastAPI endpoints for each Flask handler
        for handler_class in handlers:
            handler_name = handler_class.__module__.split('.')[-1]
            wrapper = FlaskApiWrapper(handler_class)
            
            # Create a basic endpoint that returns a placeholder
            def create_placeholder_endpoint(name=handler_name):
                async def endpoint(request: Request, api_request: Optional[ApiRequest] = None):
                    return ApiResponse(
                        success=False,
                        error=f"Handler {name} not fully integrated yet",
                        timestamp=time.time()
                    )
                return endpoint
            
            endpoint_func = create_placeholder_endpoint()
            
            # Register the endpoint with FastAPI
            app.post(
                f"/{handler_name}",
                response_model=ApiResponse,
                tags=["Legacy API (Limited)"],
                summary=f"Legacy {handler_name} endpoint (limited functionality)"
            )(endpoint_func)
            
            logger.info(f"Registered placeholder FastAPI endpoint: /{handler_name}")
            
    except Exception as e:
        logger.warning(f"Could not load Flask API handlers: {e}")
        logger.info("Continuing with enhanced API endpoints only")

def add_enhanced_endpoints(app: FastAPI) -> None:
    """Add enhanced API endpoints specific to FastAPI."""
    
    @app.post("/api/validate-code", tags=["Security"])
    async def validate_code_endpoint(code: str, security_level: SecurityLevel = SecurityLevel.STRICT):
        """Validate code for security issues."""
        try:
            result = validate_code(code, security_level)
            return {
                "is_valid": result.is_valid,
                "security_level": result.security_level,
                "errors": result.errors,
                "warnings": result.warnings,
                "blocked_items": result.blocked_items
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/api/models", tags=["AI Models"])
    async def list_models():
        """List all available AI models."""
        from models.registry import get_registry
        registry = get_registry()
        models = registry.list_models()
        return {
            "models": [
                {
                    "name": model.model_name,
                    "display_name": model.display_name,
                    "provider": model.provider,
                    "capabilities": model.capabilities,
                    "cost_per_1k_input": model.cost_per_1k_input_tokens,
                    "context_window": model.context_window,
                    "recommended_for": model.recommended_for
                }
                for model in models
            ]
        }
    
    @app.get("/api/models/{model_name}", tags=["AI Models"])
    async def get_model_details(model_name: str):
        """Get details for a specific model."""
        from models.registry import get_model
        model = get_model(model_name)
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        return {
            "name": model.model_name,
            "display_name": model.display_name,
            "provider": model.provider,
            "capabilities": model.capabilities,
            "cost_per_1k_input": model.cost_per_1k_input_tokens,
            "cost_per_1k_output": model.cost_per_1k_output_tokens,
            "context_window": model.context_window,
            "max_tokens": model.max_tokens,
            "recommended_for": model.recommended_for,
            "description": model.description,
            "is_available": model.is_available,
            "rate_limit_rpm": model.rate_limit_rpm,
            "rate_limit_tpm": model.rate_limit_tpm
        }
    
    @app.post("/api/models/recommend", tags=["AI Models"])
    async def recommend_model(use_case: str, max_cost: Optional[float] = None):
        """Get model recommendation for a specific use case."""
        from models.registry import get_recommended_model
        model = get_recommended_model(use_case, max_cost)
        if not model:
            raise HTTPException(status_code=404, detail="No suitable model found")
        
        return {
            "recommended_model": model.model_name,
            "display_name": model.display_name,
            "provider": model.provider,
            "cost_per_1k_input": model.cost_per_1k_input_tokens,
            "reason": f"Optimized for {use_case}"
        }

# Message endpoint with file upload support
async def enhanced_message_endpoint(
    text: str = Form(...),
    context: str = Form(""),
    message_id: Optional[str] = Form(None),
    attachments: Optional[list[UploadFile]] = File(None)
):
    """Enhanced message endpoint with file upload support."""
    try:
        # Handle file uploads
        attachment_paths = []
        if attachments:
            import os
            import tempfile
            
            # Create temporary directory for uploads
            upload_folder = tempfile.mkdtemp(prefix="gary_zero_uploads_")
            
            for attachment in attachments:
                if attachment.filename:
                    # Basic filename sanitization
                    filename = "".join(c for c in attachment.filename if c.isalnum() or c in ('_', '.', '-'))
                    file_path = os.path.join(upload_folder, filename)
                    with open(file_path, "wb") as f:
                        content = await attachment.read()
                        f.write(content)
                    attachment_paths.append(file_path)
        
        # Security validation for code content
        if any(keyword in text.lower() for keyword in ['exec', 'eval', 'import os', 'subprocess']):
            if not is_code_safe(text, SecurityLevel.MODERATE):
                raise HTTPException(
                    status_code=400,
                    detail="Message contains potentially unsafe code"
                )
        
        # Return basic response for now
        # TODO: Integrate with actual agent processing
        return ApiResponse(
            success=True,
            data={
                "message": "Message received and processed",
                "text": text,
                "context": context,
                "message_id": message_id,
                "attachments_count": len(attachment_paths),
                "note": "Full agent integration pending"
            },
            timestamp=time.time()
        )
        
    except Exception as e:
        logger.error(f"Error in enhanced message endpoint: {e}")
        return ApiResponse(
            success=False,
            error=str(e),
            timestamp=time.time()
        )