#!/usr/bin/env python3
"""
A2A Protocol Test Client

This script demonstrates A2A protocol compliance by connecting to Gary-Zero
and performing agent discovery, negotiation, and communication.
"""

import asyncio
import json
import requests
import uuid
from datetime import datetime
from typing import Dict, Any


class A2ATestClient:
    """Simple A2A protocol test client"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.agent_id = f"test-client-{str(uuid.uuid4())[:8]}"
        self.session_id = None
        self.session_token = None
    
    def test_agent_card_discovery(self) -> Dict[str, Any]:
        """Test 1: Discover agent card"""
        print("🔍 Testing Agent Card Discovery...")
        
        response = requests.get(f"{self.base_url}/.well-known/agent.json")
        
        if response.status_code == 200:
            agent_card = response.json()
            print(f"✅ Found agent: {agent_card['name']} (ID: {agent_card['id'][:12]}...)")
            print(f"   Capabilities: {len(agent_card['capabilities'])} available")
            print(f"   Protocols: {', '.join(agent_card['protocols'])}")
            return agent_card
        else:
            print(f"❌ Failed to get agent card: {response.status_code}")
            return {}
    
    def test_capability_discovery(self, target_capabilities: list) -> Dict[str, Any]:
        """Test 2: Discover specific capabilities"""
        print(f"🔍 Testing Capability Discovery for: {', '.join(target_capabilities)}")
        
        payload = {
            "requester_id": self.agent_id,
            "capabilities_filter": target_capabilities
        }
        
        response = requests.post(
            f"{self.base_url}/a2a/discover",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                found_capabilities = result.get("filtered_capabilities", [])
                print(f"✅ Discovery successful! Found {len(found_capabilities)} matching capabilities:")
                for cap in found_capabilities:
                    print(f"   - {cap}")
                return result
            else:
                print(f"❌ Discovery failed: {result.get('error')}")
        else:
            print(f"❌ Discovery request failed: {response.status_code}")
        
        return {}
    
    def test_protocol_negotiation(self) -> Dict[str, Any]:
        """Test 3: Negotiate A2A protocol"""
        print("🤝 Testing Protocol Negotiation...")
        
        self.session_id = str(uuid.uuid4())
        
        payload = {
            "requester_id": self.agent_id,
            "session_id": self.session_id,
            "preferred_protocols": [
                {
                    "name": "a2a",
                    "version": "1.0.0",
                    "features": ["discovery", "messaging"]
                },
                {
                    "name": "json-rpc",
                    "version": "2.0",
                    "features": ["method_calls"]
                }
            ],
            "required_capabilities": ["code_execution"],
            "optional_capabilities": ["web_browsing", "file_management"],
            "preferred_format": "json",
            "max_message_size": 1048576,  # 1MB
            "timeout_seconds": 60
        }
        
        response = requests.post(
            f"{self.base_url}/a2a/negotiate",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                agreed_protocol = result.get("agreed_protocol", {})
                supported_caps = result.get("supported_capabilities", [])
                self.session_token = result.get("session_token")
                
                print(f"✅ Negotiation successful!")
                print(f"   Agreed protocol: {agreed_protocol.get('name')} v{agreed_protocol.get('version')}")
                print(f"   Supported capabilities: {', '.join(supported_caps)}")
                print(f"   Session token: {self.session_token[:16]}..." if self.session_token else "   No session token")
                
                return result
            else:
                print(f"❌ Negotiation failed: {result.get('error')}")
        else:
            print(f"❌ Negotiation request failed: {response.status_code}")
        
        return {}
    
    def test_mcp_tools_discovery(self) -> Dict[str, Any]:
        """Test 4: Discover available MCP tools"""
        print("🛠️  Testing MCP Tools Discovery...")
        
        response = requests.get(f"{self.base_url}/a2a/mcp/tools")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                tools = result.get("tools", [])
                print(f"✅ Found {len(tools)} MCP tools:")
                for tool in tools:
                    print(f"   - {tool['name']}: {tool['description']}")
                return result
            else:
                print(f"❌ MCP tools discovery failed: {result.get('error')}")
        else:
            print(f"❌ MCP tools request failed: {response.status_code}")
        
        return {}
    
    def test_push_notification(self) -> Dict[str, Any]:
        """Test 5: Send push notification"""
        print("📢 Testing Push Notification...")
        
        payload = {
            "recipient_id": "gary-zero",
            "sender_id": self.agent_id,
            "notification_type": "test_message",
            "title": "A2A Test Notification",
            "message": "This is a test notification from the A2A test client",
            "data": {
                "test_parameter": "test_value",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            },
            "priority": "normal"
        }
        
        response = requests.post(
            f"{self.base_url}/a2a/notify",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"✅ Notification sent successfully!")
                print(f"   Message ID: {result.get('message_id')}")
                print(f"   Delivery method: {result.get('delivery_method')}")
                return result
            else:
                print(f"❌ Notification failed: {result.get('error')}")
        else:
            print(f"❌ Notification request failed: {response.status_code}")
        
        return {}
    
    def run_interoperability_test(self):
        """Run complete A2A interoperability test"""
        print("=" * 60)
        print("🚀 A2A Protocol Interoperability Test")
        print("=" * 60)
        print(f"Test Client ID: {self.agent_id}")
        print(f"Target Server: {self.base_url}")
        print()
        
        # Test 1: Agent Card Discovery
        agent_card = self.test_agent_card_discovery()
        print()
        
        if not agent_card:
            print("❌ Cannot proceed - agent card discovery failed")
            return False
        
        # Test 2: Capability Discovery
        target_capabilities = ["code_execution", "web_browsing", "file_management"]
        discovery_result = self.test_capability_discovery(target_capabilities)
        print()
        
        # Test 3: Protocol Negotiation
        negotiation_result = self.test_protocol_negotiation()
        print()
        
        # Test 4: MCP Tools Discovery
        mcp_result = self.test_mcp_tools_discovery()
        print()
        
        # Test 5: Push Notification
        notification_result = self.test_push_notification()
        print()
        
        # Summary
        print("=" * 60)
        print("📊 Test Summary")
        print("=" * 60)
        
        tests = [
            ("Agent Card Discovery", bool(agent_card)),
            ("Capability Discovery", discovery_result.get("success", False)),
            ("Protocol Negotiation", negotiation_result.get("success", False)),
            ("MCP Tools Discovery", mcp_result.get("success", False)),
            ("Push Notification", notification_result.get("success", False))
        ]
        
        passed = sum(1 for _, result in tests if result)
        total = len(tests)
        
        for test_name, result in tests:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:<25} {status}")
        
        print()
        print(f"Overall Result: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 A2A Protocol Compliance: SUCCESSFUL")
            print("   Gary-Zero successfully demonstrates A2A interoperability!")
        else:
            print("⚠️  A2A Protocol Compliance: PARTIAL")
            print("   Some tests failed - review implementation")
        
        return passed == total


def main():
    """Main test function"""
    import sys
    
    # Check if server is specified
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    # Create test client
    client = A2ATestClient(base_url)
    
    # Run interoperability test
    success = client.run_interoperability_test()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()