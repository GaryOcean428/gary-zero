"""
A2A API Handler for Negotiation endpoint

Handles protocol negotiation requests from other A2A-compliant agents.
"""

from typing import Any

from pydantic import ValidationError

from framework.a2a.negotiation import NegotiationRequest, NegotiationService


class A2aNegotiate:
    """API handler for A2A negotiation endpoint"""

    def __init__(self):
        self.negotiation_service = NegotiationService()

    async def process(self, input_data: dict[str, Any], request) -> dict[str, Any]:
        """
        Handle A2A negotiation request

        Args:
            input_data: Request input containing negotiation parameters
            request: HTTP request object

        Returns:
            Negotiation response with agreed protocol and parameters
        """
        try:
            # Validate required fields
            requester_id = input_data.get("requester_id")
            session_id = input_data.get("session_id")

            if not requester_id:
                return {"success": False, "error": "requester_id is required"}

            if not session_id:
                return {"success": False, "error": "session_id is required"}

            # Create negotiation request
            negotiation_request = NegotiationRequest(
                requester_id=requester_id,
                session_id=session_id,
                preferred_protocols=input_data.get("preferred_protocols", []),
                required_capabilities=input_data.get("required_capabilities", []),
                optional_capabilities=input_data.get("optional_capabilities", []),
                preferred_format=input_data.get("preferred_format", "json"),
                max_message_size=input_data.get("max_message_size"),
                timeout_seconds=input_data.get("timeout_seconds"),
                authentication_method=input_data.get("authentication_method"),
                encryption_required=input_data.get("encryption_required", False),
            )

            # Process negotiation
            response = self.negotiation_service.negotiate(negotiation_request)

            return response.dict()

        except ValidationError as e:
            return {"success": False, "error": f"Invalid negotiation request: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Negotiation failed: {str(e)}"}
