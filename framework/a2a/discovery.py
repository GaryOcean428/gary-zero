"""
A2A Discovery Service

Handles agent discovery and capability advertisement for the A2A protocol.
"""

from typing import Any

from pydantic import BaseModel, Field

from .agent_card import AgentCard, get_agent_card


class DiscoveryRequest(BaseModel):
    """A2A discovery request model"""

    requester_id: str = Field(description="ID of the requesting agent")
    capabilities_filter: list[str] | None = Field(
        description="Filter by capabilities", default=None
    )
    protocols_filter: list[str] | None = Field(
        description="Filter by protocols", default=None
    )


class DiscoveryResponse(BaseModel):
    """A2A discovery response model"""

    success: bool = Field(description="Whether discovery was successful")
    agent_card: AgentCard | None = Field(
        description="Agent card information", default=None
    )
    filtered_capabilities: list[str] | None = Field(
        description="Filtered capabilities", default=None
    )
    available_services: list[str] | None = Field(
        description="Available services", default=None
    )
    error: str | None = Field(
        description="Error message if discovery failed", default=None
    )


class DiscoveryService:
    """A2A Discovery Service Implementation"""

    def __init__(self):
        self.agent_card = get_agent_card()

    def discover(self, request: DiscoveryRequest) -> DiscoveryResponse:
        """
        Handle agent discovery request

        Args:
            request: Discovery request with filters

        Returns:
            Discovery response with agent card and filtered information
        """
        try:
            # Get current agent card
            agent_card = get_agent_card()

            # Apply capability filters if provided
            filtered_capabilities = None
            if request.capabilities_filter:
                available_caps = [
                    cap.name for cap in agent_card.capabilities if cap.enabled
                ]
                filtered_capabilities = [
                    cap for cap in request.capabilities_filter if cap in available_caps
                ]

            # Apply protocol filters if provided
            available_protocols = agent_card.protocols
            if request.protocols_filter:
                available_protocols = [
                    proto
                    for proto in agent_card.protocols
                    if proto in request.protocols_filter
                ]

            # Get available services based on endpoints
            available_services = [endpoint.name for endpoint in agent_card.endpoints]

            return DiscoveryResponse(
                success=True,
                agent_card=agent_card,
                filtered_capabilities=filtered_capabilities,
                available_services=available_services,
            )

        except Exception as e:
            return DiscoveryResponse(success=False, error=f"Discovery failed: {str(e)}")

    def get_capability_details(self, capability_name: str) -> dict[str, Any] | None:
        """
        Get detailed information about a specific capability

        Args:
            capability_name: Name of the capability

        Returns:
            Capability details or None if not found
        """
        agent_card = get_agent_card()

        for capability in agent_card.capabilities:
            if capability.name == capability_name and capability.enabled:
                return {
                    "name": capability.name,
                    "description": capability.description,
                    "version": capability.version,
                    "enabled": capability.enabled,
                    "endpoints": [
                        endpoint.dict()
                        for endpoint in agent_card.endpoints
                        if capability_name in endpoint.description.lower()
                        or capability_name in endpoint.name.lower()
                    ],
                }

        return None

    def get_protocol_details(self, protocol_name: str) -> dict[str, Any] | None:
        """
        Get detailed information about a specific protocol

        Args:
            protocol_name: Name of the protocol

        Returns:
            Protocol details or None if not supported
        """
        agent_card = get_agent_card()

        if protocol_name not in agent_card.protocols:
            return None

        protocol_details = {"name": protocol_name, "supported": True, "endpoints": []}

        # Add relevant endpoints for this protocol
        for endpoint in agent_card.endpoints:
            if protocol_name in endpoint.protocols:
                protocol_details["endpoints"].append(endpoint.dict())

        # Add protocol-specific information
        if protocol_name == "a2a":
            protocol_details["version"] = "1.0.0"
            protocol_details["features"] = [
                "discovery",
                "negotiation",
                "messaging",
                "streaming",
            ]
        elif protocol_name == "mcp":
            protocol_details["version"] = "1.0.0"
            protocol_details["features"] = ["client", "server", "tools", "resources"]
        elif protocol_name == "json-rpc":
            protocol_details["version"] = "2.0"
            protocol_details["features"] = [
                "method_calls",
                "notifications",
                "batch_requests",
            ]
        elif protocol_name == "websocket":
            protocol_details["version"] = "13"
            protocol_details["features"] = ["streaming", "real_time", "bidirectional"]

        return protocol_details

    def refresh_agent_card(self) -> None:
        """Refresh the cached agent card"""
        self.agent_card = get_agent_card()
