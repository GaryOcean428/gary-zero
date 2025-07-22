"""
A2A API Handler for Agent Card endpoint

Provides the /.well-known/agent.json endpoint required by A2A protocol.
"""

from typing import Dict, Any
from framework.a2a.agent_card import get_agent_card


class A2aAgentCard:
    """API handler for A2A agent card endpoint"""
    
    async def process(self, input_data: Dict[str, Any], request) -> Dict[str, Any]:
        """
        Return the A2A agent card for Gary-Zero
        
        Returns:
            Agent card as JSON following A2A specification
        """
        try:
            agent_card = get_agent_card()
            return {
                "success": True,
                "agent_card": agent_card.dict()
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to generate agent card: {str(e)}"
            }