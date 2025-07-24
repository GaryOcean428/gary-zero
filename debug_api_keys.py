#!/usr/bin/env python3
"""
Detailed API Key Debugging Script for Railway Deployment

This script checks exactly what's happening with API key retrieval
and model initialization in the Railway environment.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.getcwd())

def debug_environment():
    """Debug environment variables."""
    print("🔍 ENVIRONMENT VARIABLE DEBUG")
    print("=" * 50)
    
    # Key environment variables to check
    key_vars = [
        "OPENAI_API_KEY",
        "API_KEY_OPENAI", 
        "ANTHROPIC_API_KEY",
        "API_KEY_ANTHROPIC",
        "GOOGLE_API_KEY",
        "API_KEY_GOOGLE",
        "GROQ_API_KEY",
        "API_KEY_GROQ"
    ]
    
    for var in key_vars:
        value = os.environ.get(var)
        if value:
            # Show first and last 10 chars for security
            masked = f"{value[:10]}...{value[-10:]}" if len(value) > 20 else "***PRESENT***"
            print(f"✅ {var}: {masked}")
        else:
            print(f"❌ {var}: NOT SET")
    
    print()

def debug_dotenv():
    """Debug dotenv functionality."""
    print("🔍 DOTENV DEBUG")
    print("=" * 30)
    
    try:
        from framework.helpers import dotenv
        
        # Test dotenv retrieval
        test_keys = ["OPENAI_API_KEY", "API_KEY_OPENAI", "ANTHROPIC_API_KEY", "API_KEY_ANTHROPIC"]
        
        for key in test_keys:
            value = dotenv.get_dotenv_value(key)
            if value:
                masked = f"{value[:10]}...{value[-10:]}" if len(value) > 20 else "***PRESENT***"
                print(f"✅ dotenv.get_dotenv_value('{key}'): {masked}")
            else:
                print(f"❌ dotenv.get_dotenv_value('{key}'): None")
        
        print()
        
    except Exception as e:
        print(f"❌ Failed to import or use dotenv: {e}")

def debug_get_api_key():
    """Debug the get_api_key function."""
    print("🔍 GET_API_KEY DEBUG")
    print("=" * 30)
    
    try:
        from models import get_api_key
        
        # Test different services
        services = ["openai", "anthropic", "google", "groq"]
        
        for service in services:
            print(f"\n🔧 Testing service: {service}")
            try:
                api_key = get_api_key(service)
                if api_key:
                    masked = f"{api_key[:10]}...{api_key[-10:]}" if len(api_key) > 20 else "***PRESENT***"
                    print(f"  ✅ get_api_key('{service}'): {masked}")
                else:
                    print(f"  ❌ get_api_key('{service}'): None")
                    # Debug what the function is looking for
                    from framework.helpers import dotenv
                    check_keys = [
                        f"API_KEY_{service.upper()}",
                        f"{service.upper()}_API_KEY", 
                        f"{service.upper()}_API_TOKEN"
                    ]
                    print(f"  🔍 Checking for these keys:")
                    for check_key in check_keys:
                        val = dotenv.get_dotenv_value(check_key)
                        status = "✅ FOUND" if val else "❌ NOT FOUND"
                        print(f"    - {check_key}: {status}")
                        
            except Exception as e:
                print(f"  ❌ Error calling get_api_key('{service}'): {e}")
        
        print()
        
    except Exception as e:
        print(f"❌ Failed to import get_api_key: {e}")

def debug_model_initialization():
    """Debug model initialization."""
    print("🔍 MODEL INITIALIZATION DEBUG")
    print("=" * 40)
    
    try:
        import models
        
        # Test utility model (the one that's failing)
        print("🔧 Testing utility model (gpt-4o-mini)...")
        try:
            model = models.get_model(
                models.ModelType.CHAT,
                models.ModelProvider.OPENAI,
                "gpt-4o-mini"
            )
            if model:
                print("  ✅ Successfully initialized gpt-4o-mini")
                print(f"  📋 Model type: {type(model)}")
            else:
                print("  ❌ Model initialization returned None")
        except Exception as e:
            print(f"  ❌ Model initialization failed: {e}")
            
        # Test chat model
        print("\n🔧 Testing chat model (claude-3-5-sonnet-20241022)...")
        try:
            model = models.get_model(
                models.ModelType.CHAT,
                models.ModelProvider.ANTHROPIC,
                "claude-3-5-sonnet-20241022"
            )
            if model:
                print("  ✅ Successfully initialized claude-3-5-sonnet-20241022")
                print(f"  📋 Model type: {type(model)}")
            else:
                print("  ❌ Model initialization returned None")
        except Exception as e:
            print(f"  ❌ Model initialization failed: {e}")
            
    except Exception as e:
        print(f"❌ Failed to import models or test initialization: {e}")

def debug_openai_function_directly():
    """Debug OpenAI function directly."""
    print("🔍 DIRECT OPENAI FUNCTION DEBUG")
    print("=" * 40)
    
    try:
        from models import get_openai_chat, get_api_key
        
        print("🔧 Testing get_openai_chat directly...")
        
        # First check if we can get the API key
        api_key = get_api_key("openai")
        if api_key:
            masked = f"{api_key[:10]}...{api_key[-10:]}"
            print(f"  ✅ API key found: {masked}")
        else:
            print("  ❌ No API key found")
            return
            
        # Try to call the function
        try:
            model = get_openai_chat("gpt-4o-mini")
            if model:
                print("  ✅ get_openai_chat() succeeded")
                print(f"  📋 Model type: {type(model)}")
                print(f"  📋 Model details: {model}")
            else:
                print("  ❌ get_openai_chat() returned None")
        except Exception as e:
            print(f"  ❌ get_openai_chat() failed: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Failed to test OpenAI function directly: {e}")

def main():
    """Main debugging function."""
    print("🚀 Gary-Zero API Key Debugging Script")
    print("=" * 50)
    
    debug_environment()
    debug_dotenv()
    debug_get_api_key()
    debug_openai_function_directly()
    debug_model_initialization()
    
    print("\n📊 DEBUGGING COMPLETE")
    print("Check the output above to identify the exact failure point.")

if __name__ == "__main__":
    main()
