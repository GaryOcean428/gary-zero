"""
A2A API Handler for Discovery endpoint

Handles agent discovery requests from other A2A-compliant agents.
"""

from typing import Any

from pydantic import ValidationError

from framework.a2a.discovery import DiscoveryRequest, DiscoveryService


class A2aDiscover:
    """API handler for A2A discovery endpoint"""

    def __init__(self):
        self.discovery_service = DiscoveryService()

    async def process(self, input_data: dict[str, Any], request) -> dict[str, Any]:
        """
        Handle A2A discovery request
        
        Args:
            input_data: Request input containing discovery parameters
            request: HTTP request object
            
        Returns:
            Discovery response with agent capabilities and endpoints
        """
        try:
            # Parse discovery request
            requester_id = input_data.get("requester_id")
            if not requester_id:
                return {
                    "success": False,
                    "error": "requester_id is required"
                }

            # Create discovery request
            discovery_request = DiscoveryRequest(
                requester_id=requester_id,
                capabilities_filter=input_data.get("capabilities_filter"),
                protocols_filter=input_data.get("protocols_filter")
            )

            # Process discovery
            response = self.discovery_service.discover(discovery_request)

            return response.dict()

        except ValidationError as e:
            return {
                "success": False,
                "error": f"Invalid discovery request: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Discovery failed: {str(e)}"
            }
