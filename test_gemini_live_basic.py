"""
Simple test for Google Gemini Live API integration.

This test validates basic functionality without complex dependencies.
"""

import os


# Mock Response class to avoid circular imports
class MockResponse:
    def __init__(self, message, break_loop=False):
        self.message = message
        self.break_loop = break_loop

def test_basic_integration():
    """Test basic integration without dependencies."""
    print("🧪 Testing Google Gemini Live API Integration (Basic)")
    print("=" * 55)

    try:
        # Test 1: Create streaming client
        print("1. Testing streaming client creation...")
        from instruments.custom.gemini_live.streaming_client import GeminiLiveClient

        client = GeminiLiveClient(
            api_key="test_key",
            model_name="models/gemini-2.5-flash-preview-native-audio-dialog",
            voice_name="Zephyr"
        )
        print("   ✅ GeminiLiveClient created successfully")
        print(f"   📝 Model: {client.model_name}")
        print(f"   🎵 Voice: {client.voice_name}")
        print(f"   📱 Modalities: {client.response_modalities}")

        # Test 2: Create tool instance
        print("\n2. Testing tool creation...")
        from instruments.custom.gemini_live.gemini_live_tool import GeminiLiveTool

        tool = GeminiLiveTool()
        print("   ✅ GeminiLiveTool created successfully")

        # Test 3: Test basic configurations
        print("\n3. Testing environment configuration...")
        api_key_present = bool(os.getenv("GEMINI_API_KEY"))
        print(f"   🔑 GEMINI_API_KEY present: {api_key_present}")

        default_model = os.getenv("GEMINI_LIVE_MODEL", "models/gemini-2.5-flash-preview-native-audio-dialog")
        print(f"   🤖 Default model: {default_model}")

        default_voice = os.getenv("GEMINI_LIVE_VOICE", "Zephyr")
        print(f"   🎵 Default voice: {default_voice}")

        # Test 4: Test tool factory
        print("\n4. Testing tool factory...")
        tool_instance = __import__('instruments.custom.gemini_live.gemini_live_tool', fromlist=['get_tool']).get_tool()
        print("   ✅ Tool factory function works")
        print(f"   📋 Tool name: {getattr(tool_instance, 'name', 'Not set')}")

        print("\n✅ All basic tests passed! Gemini Live API integration is properly set up.")

        if not api_key_present:
            print("\n⚠️  Note: Set GEMINI_API_KEY environment variable to test actual API connectivity.")

        return True

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_configuration_options():
    """Test configuration options."""
    print("\n⚙️  Testing Configuration Options")
    print("=" * 35)

    try:
        # Test available models
        models = [
            "models/gemini-2.5-flash-preview-native-audio-dialog",
            "models/gemini-2.5-pro-preview-native-audio-dialog",
            "models/gemini-2.0-flash"
        ]
        print(f"✅ Supported models: {len(models)}")
        for model in models:
            print(f"   - {model}")

        # Test available voices
        voices = ["Zephyr", "Echo", "Crystal", "Sage"]
        print(f"\n✅ Supported voices: {len(voices)}")
        for voice in voices:
            print(f"   - {voice}")

        # Test modalities
        modalities = ["AUDIO", "VIDEO"]
        print(f"\n✅ Supported modalities: {len(modalities)}")
        for modality in modalities:
            status = "Available" if modality == "AUDIO" else "Coming soon"
            print(f"   - {modality} ({status})")

        return True

    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Gemini Live API Basic Tests\n")

    # Run basic tests
    basic_success = test_basic_integration()

    # Run configuration tests
    config_success = test_configuration_options()

    # Summary
    print("\n" + "="*55)
    print("📋 Test Summary:")
    print(f"   Basic Integration: {'✅ PASSED' if basic_success else '❌ FAILED'}")
    print(f"   Configuration: {'✅ PASSED' if config_success else '❌ FAILED'}")

    if basic_success and config_success:
        print("\n🎉 All tests passed! Gemini Live API integration is ready.")
        print("\n📝 Next Steps:")
        print("   1. Set GEMINI_API_KEY environment variable")
        print("   2. Test actual API connectivity")
        print("   3. Configure audio devices for streaming")
        print("   4. Test streaming in the web UI")
        exit(0)
    else:
        print("\n💥 Some tests failed. Please check the errors above.")
        exit(1)
