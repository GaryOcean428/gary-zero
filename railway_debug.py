#!/usr/bin/env python3
"""
Railway Environment Debug Script

This script will help diagnose API key issues in the Railway deployment
by checking environment variables and model initialization step by step.
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, "/app" if os.path.exists("/app") else os.getcwd())


def check_environment_variables():
    """Check all relevant environment variables."""
    print("🔍 ENVIRONMENT VARIABLES CHECK")
    print("=" * 50)

    # Check OpenAI keys
    openai_keys = ["OPENAI_API_KEY", "API_KEY_OPENAI"]
    print("OpenAI Keys:")
    for key in openai_keys:
        value = os.environ.get(key)
        if value:
            print(
                f"  ✅ {key}: {value[:10]}...{value[-10:] if len(value) > 20 else '***'}"
            )
        else:
            print(f"  ❌ {key}: NOT SET")

    # Check Anthropic keys
    anthropic_keys = ["ANTHROPIC_API_KEY", "API_KEY_ANTHROPIC"]
    print("\nAnthropic Keys:")
    for key in anthropic_keys:
        value = os.environ.get(key)
        if value:
            print(
                f"  ✅ {key}: {value[:10]}...{value[-10:] if len(value) > 20 else '***'}"
            )
        else:
            print(f"  ❌ {key}: NOT SET")

    print()


def test_dotenv_function():
    """Test the dotenv helper function."""
    print("🔍 DOTENV FUNCTION TEST")
    print("=" * 30)

    try:
        from framework.helpers.dotenv import get_dotenv_value

        keys_to_test = [
            "OPENAI_API_KEY",
            "API_KEY_OPENAI",
            "ANTHROPIC_API_KEY",
            "API_KEY_ANTHROPIC",
        ]

        for key in keys_to_test:
            value = get_dotenv_value(key)
            if value:
                print(
                    f"  ✅ get_dotenv_value('{key}'): {value[:10]}...{value[-10:] if len(value) > 20 else '***'}"
                )
            else:
                print(f"  ❌ get_dotenv_value('{key}'): None")

        print()

    except Exception as e:
        print(f"  ❌ Error importing or using dotenv: {e}")
        print()


def test_get_api_key():
    """Test the get_api_key function."""
    print("🔍 GET_API_KEY FUNCTION TEST")
    print("=" * 35)

    try:
        from models import get_api_key

        # Test OpenAI
        print("Testing OpenAI:")
        openai_key = get_api_key("openai")
        if openai_key:
            print(
                f"  ✅ get_api_key('openai'): {openai_key[:10]}...{openai_key[-10:] if len(openai_key) > 20 else '***'}"
            )
        else:
            print("  ❌ get_api_key('openai'): None")
            # Debug what it's looking for
            from framework.helpers.dotenv import get_dotenv_value

            check_keys = ["API_KEY_OPENAI", "OPENAI_API_KEY", "OPENAI_API_TOKEN"]
            print("    Checking individual keys:")
            for check_key in check_keys:
                val = get_dotenv_value(check_key)
                if val:
                    print(f"      ✅ {check_key}: FOUND")
                else:
                    print(f"      ❌ {check_key}: NOT FOUND")

        # Test Anthropic
        print("\nTesting Anthropic:")
        anthropic_key = get_api_key("anthropic")
        if anthropic_key:
            print(
                f"  ✅ get_api_key('anthropic'): {anthropic_key[:10]}...{anthropic_key[-10:] if len(anthropic_key) > 20 else '***'}"
            )
        else:
            print("  ❌ get_api_key('anthropic'): None")

        print()

    except Exception as e:
        print(f"  ❌ Error testing get_api_key: {e}")
        import traceback

        traceback.print_exc()
        print()


def test_openai_model_creation():
    """Test OpenAI model creation step by step."""
    print("🔍 OPENAI MODEL CREATION TEST")
    print("=" * 40)

    try:
        # Step 1: Test get_api_key
        from models import get_api_key

        api_key = get_api_key("openai")

        if not api_key:
            print("  ❌ Cannot proceed - no API key found")
            return

        print(f"  ✅ API key found: {api_key[:10]}...")

        # Step 2: Test direct ChatOpenAI import
        try:
            from langchain_openai import ChatOpenAI

            print("  ✅ ChatOpenAI import successful")
        except Exception as e:
            print(f"  ❌ ChatOpenAI import failed: {e}")
            return

        # Step 3: Test direct ChatOpenAI instantiation
        try:
            model = ChatOpenAI(api_key=api_key, model="gpt-4.1-mini")
            print("  ✅ Direct ChatOpenAI instantiation successful")
            print(f"    Model type: {type(model)}")
        except Exception as e:
            print(f"  ❌ Direct ChatOpenAI instantiation failed: {e}")
            import traceback

            traceback.print_exc()
            return

        # Step 4: Test our get_openai_chat function
        try:
            from models import get_openai_chat

            our_model = get_openai_chat("gpt-4.1-mini")

            if our_model:
                print("  ✅ get_openai_chat() successful")
                print(f"    Model type: {type(our_model)}")
            else:
                print("  ❌ get_openai_chat() returned None")

        except Exception as e:
            print(f"  ❌ get_openai_chat() failed: {e}")
            import traceback

            traceback.print_exc()

        print()

    except Exception as e:
        print(f"  ❌ Error in OpenAI model creation test: {e}")
        import traceback

        traceback.print_exc()
        print()


def test_model_get_function():
    """Test the main get_model function."""
    print("🔍 MODELS.GET_MODEL FUNCTION TEST")
    print("=" * 40)

    try:
        import models

        # Test utility model
        print("Testing utility model (gpt-4.1-mini):")
        try:
            model = models.get_model(
                models.ModelType.CHAT, models.ModelProvider.OPENAI, "gpt-4.1-mini"
            )

            if model:
                print("  ✅ models.get_model() successful")
                print(f"    Model type: {type(model)}")
            else:
                print("  ❌ models.get_model() returned None")

        except Exception as e:
            print(f"  ❌ models.get_model() failed: {e}")
            import traceback

            traceback.print_exc()

        print()

    except Exception as e:
        print(f"  ❌ Error testing models.get_model: {e}")
        import traceback

        traceback.print_exc()
        print()


def main():
    """Main debug function."""
    print("🚀 Railway Environment Debug Script")
    print("=" * 50)
    print(f"Running in: {os.getcwd()}")
    print(f"Python path: {sys.path[:3]}...")
    print()

    check_environment_variables()
    test_dotenv_function()
    test_get_api_key()
    test_openai_model_creation()
    test_model_get_function()

    print("🎯 DEBUG COMPLETE")
    print("=" * 20)
    print("Review the output above to identify the exact failure point.")


if __name__ == "__main__":
    main()
