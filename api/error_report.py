"""
Error reporting API router for Gary-Zero FastAPI application.

This module provides an endpoint to receive and log error reports from the client
application, matching the client's POST request expectations.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel

# Create router with prefix and tags
router = APIRouter(prefix="/api", tags=["error"])

# Set up logger for error reporting
logger = logging.getLogger("error_report")

# Pydantic model for error report payload (optional for validation)
class ErrorReportPayload(BaseModel):
    id: int | None = None
    sessionId: str | None = None
    timestamp: str | None = None
    url: str | None = None
    userAgent: str | None = None
    error: Dict[str, Any] | None = None
    context: Dict[str, Any] | None = None

@router.post("/error_report")
async def error_report(request: Request) -> Response:
    """
    Receive client error reports and log them.
    
    This endpoint accepts error reports from the client-side error reporting system
    and logs them server-side for debugging and monitoring purposes.
    
    Args:
        request: The FastAPI request object
    
    Returns:
        Response with status code 204 (No Content) to indicate successful receipt
    """
    try:
        payload = {}
        
        # Try to get the content type
        content_type = request.headers.get("content-type", "").lower()
        
        if "application/json" in content_type:
            # Handle JSON payload
            try:
                payload = await request.json()
            except Exception as json_error:
                logger.warning(f"Failed to parse JSON payload: {json_error}")
                payload = {"error": "Invalid JSON payload"}
        elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
            # Handle form data
            try:
                form_data = await request.form()
                payload = dict(form_data)
            except Exception as form_error:
                logger.warning(f"Failed to parse form data: {form_error}")
                payload = {"error": "Invalid form data"}
        else:
            # Handle raw body or unknown content type
            try:
                body = await request.body()
                payload = {"raw_body": body.decode("utf-8") if body else "", "content_type": content_type}
            except Exception as body_error:
                logger.warning(f"Failed to read request body: {body_error}")
                payload = {"error": "Failed to read request body"}
        
        # Log the error report
        logger.error(f"Client error report: {payload}")
        
        # Log additional request context
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        logger.info(f"Error report received from {client_ip}, User-Agent: {user_agent}")
        
        # Return 204 No Content as specified
        return Response(status_code=status.HTTP_204_NO_CONTENT)
        
    except Exception as e:
        # Log any errors in processing the error report
        logger.error(f"Failed to process error report: {str(e)}")
        
        # Still return 204 to prevent client-side error reporting loops
        return Response(status_code=status.HTTP_204_NO_CONTENT)