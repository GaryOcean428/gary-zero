"""
Agent2Agent (A2A) Protocol Implementation for Gary-Zero

This module provides A2A protocol compliance for multi-agent interoperability,
enabling communication with external agents across different vendors.
"""

from .agent_card import AgentCard, get_agent_card
from .discovery import DiscoveryService
from .negotiation import NegotiationService

__all__ = [
    'AgentCard',
    'get_agent_card',
    'DiscoveryService', 
    'NegotiationService'
]