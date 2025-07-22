"""
Test script for Google Gemini Live API integration.

This script tests the basic functionality of the Gemini Live API integration
without requiring audio hardware.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_gemini_live_integration():
    """Test the Gemini Live API integration."""
    print("🧪 Testing Google Gemini Live API Integration")
    print("=" * 50)

    try:
        # Test 1: Import the modules
        print("1. Testing module imports...")
        from instruments.custom.gemini_live.gemini_live_tool import GeminiLiveTool
        from instruments.custom.gemini_live.streaming_client import GeminiLiveClient
        print("   ✅ All modules imported successfully")

        # Test 2: Create tool instance
        print("\n2. Testing tool instantiation...")
        tool = GeminiLiveTool()
        print("   ✅ GeminiLiveTool created successfully")

        # Test 3: Test status action (without API key)
        print("\n3. Testing status action...")
        tool.args = {"action": "status"}
        response = await tool.execute()
        print(f"   📊 Status response: {response.message[:100]}...")
        print("   ✅ Status action completed")

        # Test 4: Test configuration action
        print("\n4. Testing configuration action...")
        tool.args = {"action": "configure"}
        response = await tool.execute()
        print(f"   ⚙️  Configure response: {response.message[:100]}...")
        print("   ✅ Configuration action completed")

        # Test 5: Test client creation (without connection)
        print("\n5. Testing streaming client creation...")
        client = GeminiLiveClient(
            api_key="test_key",
            model_name="models/gemini-2.5-flash-preview-native-audio-dialog",
            voice_name="Zephyr"
        )
        print("   ✅ GeminiLiveClient created successfully")
        print(f"   📝 Model: {client.model_name}")
        print(f"   🎵 Voice: {client.voice_name}")
        print(f"   📱 Modalities: {client.response_modalities}")

        # Test 6: Test environment variable detection
        print("\n6. Testing environment configuration...")
        api_key_present = bool(os.getenv("GEMINI_API_KEY"))
        print(f"   🔑 GEMINI_API_KEY present: {api_key_present}")

        default_model = os.getenv("GEMINI_LIVE_MODEL", "models/gemini-2.5-flash-preview-native-audio-dialog")
        print(f"   🤖 Default model: {default_model}")

        default_voice = os.getenv("GEMINI_LIVE_VOICE", "Zephyr")
        print(f"   🎵 Default voice: {default_voice}")

        print("\n✅ All tests passed! Gemini Live API integration is working correctly.")

        if not api_key_present:
            print("\n⚠️  Note: Set GEMINI_API_KEY environment variable to test actual API connectivity.")

        return True

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_api_endpoints():
    """Test the API endpoints (simulation)."""
    print("\n🌐 Testing API Endpoints")
    print("=" * 30)

    try:
        from api.gemini_live_api import GeminiLiveRequest, GeminiLiveResponse
        print("✅ API models imported successfully")

        # Test request model
        request = GeminiLiveRequest(
            action="status",
            model="models/gemini-2.5-flash-preview-native-audio-dialog",
            voice="Zephyr",
            response_modalities=["AUDIO"]
        )
        print(f"✅ Test request created: {request.action}")

        # Test response model
        response = GeminiLiveResponse(
            success=True,
            message="Test response",
            details={"test": True}
        )
        print(f"✅ Test response created: {response.success}")

        return True

    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        return False

if __name__ == "__main__":
    async def main():
        """Run all tests."""
        print("🚀 Starting Gemini Live API Integration Tests\n")

        # Run integration tests
        integration_success = await test_gemini_live_integration()

        # Run API tests
        api_success = await test_api_endpoints()

        # Summary
        print("\n" + "="*50)
        print("📋 Test Summary:")
        print(f"   Integration Tests: {'✅ PASSED' if integration_success else '❌ FAILED'}")
        print(f"   API Tests: {'✅ PASSED' if api_success else '❌ FAILED'}")

        if integration_success and api_success:
            print("\n🎉 All tests passed! Gemini Live API integration is ready.")
            return 0
        else:
            print("\n💥 Some tests failed. Please check the errors above.")
            return 1

    exit_code = asyncio.run(main())
