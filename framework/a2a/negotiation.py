"""
A2A Negotiation Service

Handles protocol negotiation between agents to establish communication parameters.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum

from .agent_card import get_agent_card


class NegotiationStatus(str, Enum):
    """Negotiation status values"""
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


class ProtocolVersion(BaseModel):
    """Protocol version specification"""
    name: str = Field(description="Protocol name")
    version: str = Field(description="Protocol version")
    features: List[str] = Field(description="Supported features", default=[])


class NegotiationRequest(BaseModel):
    """A2A negotiation request model"""
    requester_id: str = Field(description="ID of the requesting agent")
    session_id: str = Field(description="Negotiation session ID")
    
    # Protocol preferences
    preferred_protocols: List[ProtocolVersion] = Field(description="Preferred protocols in order")
    required_capabilities: List[str] = Field(description="Required capabilities", default=[])
    optional_capabilities: List[str] = Field(description="Optional capabilities", default=[])
    
    # Communication preferences
    preferred_format: str = Field(description="Preferred message format", default="json")
    max_message_size: Optional[int] = Field(description="Maximum message size in bytes", default=None)
    timeout_seconds: Optional[int] = Field(description="Communication timeout", default=None)
    
    # Security preferences
    authentication_method: Optional[str] = Field(description="Preferred authentication method", default=None)
    encryption_required: bool = Field(description="Whether encryption is required", default=False)


class NegotiationResponse(BaseModel):
    """A2A negotiation response model"""
    success: bool = Field(description="Whether negotiation was successful")
    session_id: str = Field(description="Negotiation session ID")
    status: NegotiationStatus = Field(description="Negotiation status")
    
    # Agreed parameters
    agreed_protocol: Optional[ProtocolVersion] = Field(description="Agreed protocol", default=None)
    supported_capabilities: List[str] = Field(description="Supported capabilities", default=[])
    communication_params: Dict[str, Any] = Field(description="Communication parameters", default={})
    
    # Session information
    session_token: Optional[str] = Field(description="Session authentication token", default=None)
    expires_at: Optional[str] = Field(description="Session expiration time", default=None)
    
    # Error information
    error: Optional[str] = Field(description="Error message if negotiation failed", default=None)
    unsupported_capabilities: List[str] = Field(description="Unsupported capabilities", default=[])


class NegotiationService:
    """A2A Negotiation Service Implementation"""
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.supported_protocols = {
            "a2a": ProtocolVersion(name="a2a", version="1.0.0", features=["discovery", "negotiation", "messaging"]),
            "mcp": ProtocolVersion(name="mcp", version="1.0.0", features=["client", "server", "tools"]),
            "json-rpc": ProtocolVersion(name="json-rpc", version="2.0", features=["method_calls", "notifications"]),
            "websocket": ProtocolVersion(name="websocket", version="13", features=["streaming", "real_time"])
        }
    
    def negotiate(self, request: NegotiationRequest) -> NegotiationResponse:
        """
        Handle protocol negotiation request
        
        Args:
            request: Negotiation request with protocol preferences
            
        Returns:
            Negotiation response with agreed parameters
        """
        try:
            # Get current agent capabilities
            agent_card = get_agent_card()
            available_capabilities = [cap.name for cap in agent_card.capabilities if cap.enabled]
            
            # Find common protocol
            agreed_protocol = self._find_common_protocol(request.preferred_protocols)
            if not agreed_protocol:
                return NegotiationResponse(
                    success=False,
                    session_id=request.session_id,
                    status=NegotiationStatus.FAILED,
                    error="No compatible protocol found"
                )
            
            # Check required capabilities
            unsupported_capabilities = []
            supported_capabilities = []
            
            for capability in request.required_capabilities:
                if capability in available_capabilities:
                    supported_capabilities.append(capability)
                else:
                    unsupported_capabilities.append(capability)
            
            # If required capabilities are missing, reject negotiation
            if unsupported_capabilities:
                return NegotiationResponse(
                    success=False,
                    session_id=request.session_id,
                    status=NegotiationStatus.REJECTED,
                    error="Required capabilities not supported",
                    unsupported_capabilities=unsupported_capabilities
                )
            
            # Add optional capabilities that we support
            for capability in request.optional_capabilities:
                if capability in available_capabilities and capability not in supported_capabilities:
                    supported_capabilities.append(capability)
            
            # Set communication parameters
            communication_params = {
                "format": request.preferred_format if request.preferred_format == "json" else "json",
                "max_message_size": min(request.max_message_size or 1024*1024, 10*1024*1024),  # Max 10MB
                "timeout_seconds": min(request.timeout_seconds or 30, 300),  # Max 5 minutes
                "encryption_required": request.encryption_required
            }
            
            # Store session information
            session_info = {
                "requester_id": request.requester_id,
                "agreed_protocol": agreed_protocol,
                "supported_capabilities": supported_capabilities,
                "communication_params": communication_params,
                "created_at": self._get_current_timestamp()
            }
            self.active_sessions[request.session_id] = session_info
            
            return NegotiationResponse(
                success=True,
                session_id=request.session_id,
                status=NegotiationStatus.COMPLETED,
                agreed_protocol=agreed_protocol,
                supported_capabilities=supported_capabilities,
                communication_params=communication_params,
                session_token=self._generate_session_token(request.session_id),
                expires_at=self._get_expiration_timestamp(3600)  # 1 hour
            )
            
        except Exception as e:
            return NegotiationResponse(
                success=False,
                session_id=request.session_id,
                status=NegotiationStatus.FAILED,
                error=f"Negotiation failed: {str(e)}"
            )
    
    def _find_common_protocol(self, preferred_protocols: List[ProtocolVersion]) -> Optional[ProtocolVersion]:
        """Find the first supported protocol from the preferred list"""
        for protocol in preferred_protocols:
            if protocol.name in self.supported_protocols:
                supported = self.supported_protocols[protocol.name]
                # Check if versions are compatible (simplified - just check if exact match or we support higher)
                if protocol.version <= supported.version:
                    return supported
        return None
    
    def _generate_session_token(self, session_id: str) -> str:
        """Generate a session authentication token"""
        # In a real implementation, use proper cryptographic tokens
        import hashlib
        return hashlib.sha256(f"{session_id}:gary-zero:session".encode()).hexdigest()[:32]
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
    
    def _get_expiration_timestamp(self, seconds_from_now: int) -> str:
        """Get expiration timestamp"""
        from datetime import datetime, timedelta
        expiry = datetime.utcnow() + timedelta(seconds=seconds_from_now)
        return expiry.isoformat() + "Z"
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about an active session"""
        return self.active_sessions.get(session_id)
    
    def validate_session_token(self, session_id: str, token: str) -> bool:
        """Validate a session token"""
        expected_token = self._generate_session_token(session_id)
        return token == expected_token
    
    def cleanup_expired_sessions(self) -> None:
        """Remove expired sessions"""
        # In a real implementation, check expiration timestamps and remove expired sessions
        pass