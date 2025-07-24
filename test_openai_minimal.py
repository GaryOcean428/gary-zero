#!/usr/bin/env python3
"""
Minimal test to debug ChatOpenAI instantiation issues
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.getcwd())

def test_direct_environment():
    """Test direct environment variable access."""
    print("🔍 DIRECT ENVIRONMENT TEST")
    print("=" * 30)
    
    openai_key = os.environ.get("OPENAI_API_KEY")
    api_key_openai = os.environ.get("API_KEY_OPENAI")
    
    print(f"OPENAI_API_KEY: {'✅ PRESENT' if openai_key else '❌ MISSING'}")
    print(f"API_KEY_OPENAI: {'✅ PRESENT' if api_key_openai else '❌ MISSING'}")
    
    if openai_key:
        print(f"OPENAI_API_KEY starts with: {openai_key[:15]}...")
    if api_key_openai:
        print(f"API_KEY_OPENAI starts with: {api_key_openai[:15]}...")
    
    return openai_key or api_key_openai

def test_langchain_openai_import():
    """Test if we can import and instantiate ChatOpenAI."""
    print("\n🔍 LANGCHAIN OPENAI IMPORT TEST")
    print("=" * 35)
    
    try:
        from langchain_openai import ChatOpenAI
        print("✅ Successfully imported ChatOpenAI")
        
        # Test with a known API key
        api_key = test_direct_environment()
        if not api_key:
            print("❌ No API key available for testing")
            return None
            
        print(f"\n🔧 Testing ChatOpenAI instantiation...")
        try:
            model = ChatOpenAI(
                api_key=api_key,
                model="gpt-4o-mini"
            )
            print("✅ ChatOpenAI instantiation successful")
            print(f"📋 Model type: {type(model)}")
            return model
        except Exception as e:
            print(f"❌ ChatOpenAI instantiation failed: {e}")
            import traceback
            traceback.print_exc()
            return None
            
    except Exception as e:
        print(f"❌ Failed to import ChatOpenAI: {e}")
        return None

def test_get_api_key_function():
    """Test our get_api_key function specifically."""
    print("\n🔍 GET_API_KEY FUNCTION TEST")
    print("=" * 30)
    
    try:
        # Import and test our function
        sys.path.insert(0, os.getcwd())
        from models import get_api_key
        
        print("✅ Successfully imported get_api_key")
        
        api_key = get_api_key("openai")
        if api_key:
            print(f"✅ get_api_key('openai') returned: {api_key[:15]}...")
            print(f"📋 Type: {type(api_key)}")
            print(f"📋 Length: {len(api_key)}")
            return api_key
        else:
            print("❌ get_api_key('openai') returned None")
            
            # Debug the internal logic
            from framework.helpers import dotenv
            
            print("\n🔍 Debugging internal lookups:")
            keys_to_check = ["API_KEY_OPENAI", "OPENAI_API_KEY", "OPENAI_API_TOKEN"]
            for key in keys_to_check:
                val = dotenv.get_dotenv_value(key)
                print(f"  {key}: {'✅ FOUND' if val else '❌ NOT FOUND'}")
                if val and len(val) > 10:
                    print(f"    └─ Value: {val[:10]}...{val[-5:]}")
            
            return None
        
    except Exception as e:
        print(f"❌ Failed to test get_api_key: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_openai_chat_function():
    """Test our get_openai_chat function specifically."""
    print("\n🔍 GET_OPENAI_CHAT FUNCTION TEST")
    print("=" * 35)
    
    try:
        from models import get_openai_chat
        print("✅ Successfully imported get_openai_chat")
        
        print("🔧 Calling get_openai_chat('gpt-4o-mini')...")
        model = get_openai_chat("gpt-4o-mini")
        
        if model:
            print("✅ get_openai_chat successful")
            print(f"📋 Model type: {type(model)}")
            print(f"📋 Model: {model}")
        else:
            print("❌ get_openai_chat returned None")
            
        return model
        
    except Exception as e:
        print(f"❌ get_openai_chat failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main test function."""
    print("🚀 OpenAI Minimal Debugging Test")
    print("=" * 40)
    
    # Test each component step by step
    api_key = test_direct_environment()
    if not api_key:
        print("\n❌ CRITICAL: No API key found in environment")
        return 1
    
    langchain_model = test_langchain_openai_import()
    if not langchain_model:
        print("\n❌ CRITICAL: Cannot instantiate ChatOpenAI directly")
        return 1
    
    our_api_key = test_get_api_key_function()
    if not our_api_key:
        print("\n❌ CRITICAL: Our get_api_key function is not working")
        return 1
    
    our_model = test_openai_chat_function()
    if not our_model:
        print("\n❌ CRITICAL: Our get_openai_chat function is not working")
        return 1
    
    print("\n🎉 ALL TESTS PASSED!")
    print("The OpenAI integration should be working correctly.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
