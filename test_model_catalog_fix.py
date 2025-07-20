#!/usr/bin/env python3
"""Test script to validate the model catalog fix for issue #134."""

from framework.helpers.model_catalog import get_models_for_provider, is_valid_model_for_provider


def test_missing_xai_models():
    """Test that the previously missing XAI models are now available."""
    print("Testing XAI model availability...")
    
    # Test the models that were specifically missing according to the issue
    missing_models = [
        "grok-3-fast",
        "grok-3-mini-fast", 
        "grok-4-0709"
    ]
    
    xai_models = get_models_for_provider("XAI")
    xai_model_values = [m["value"] for m in xai_models]
    
    for model in missing_models:
        assert model in xai_model_values, f"Model {model} not found in XAI catalog"
        assert is_valid_model_for_provider("XAI", model), f"Model {model} not valid for XAI provider"
        print(f"  ✅ {model} - Available")
    
    print(f"XAI provider now has {len(xai_models)} models total")


def test_missing_openai_models():
    """Test that the previously missing OpenAI models are now available."""
    print("\nTesting OpenAI model availability...")
    
    missing_models = [
        "gpt-4.1-mini",
        "gpt-4.1-nano", 
        "o3-mini-2025-01-31",
        "o3-pro",
        "gpt-4o-audio",
        "gpt-4o-mini-audio",
        "computer-use-preview",
        "gpt-4o-search-preview",
        "gpt-4o-mini-search-preview"
    ]
    
    openai_models = get_models_for_provider("OPENAI")
    openai_model_values = [m["value"] for m in openai_models]
    
    for model in missing_models:
        assert model in openai_model_values, f"Model {model} not found in OPENAI catalog"
        assert is_valid_model_for_provider("OPENAI", model), f"Model {model} not valid for OPENAI provider"
        print(f"  ✅ {model} - Available")
    
    print(f"OPENAI provider now has {len(openai_models)} models total")


def test_missing_google_models():
    """Test that the previously missing Google models are now available."""
    print("\nTesting Google model availability...")
    
    missing_models = [
        "gemini-2.0-flash",
        "gemini-2.0-flash-thinking-exp",
        "gemini-2.0-pro-experimental", 
        "gemini-2.0-flash-lite"
    ]
    
    google_models = get_models_for_provider("GOOGLE")
    google_model_values = [m["value"] for m in google_models]
    
    for model in missing_models:
        assert model in google_model_values, f"Model {model} not found in GOOGLE catalog"
        assert is_valid_model_for_provider("GOOGLE", model), f"Model {model} not valid for GOOGLE provider"
        print(f"  ✅ {model} - Available")
    
    print(f"GOOGLE provider now has {len(google_models)} models total")


def test_existing_models_still_work():
    """Test that existing models still work after the update."""
    print("\nTesting existing models still work...")
    
    # Test some key existing models
    existing_tests = [
        ("XAI", "grok-4-latest"),
        ("OPENAI", "gpt-4o"),
        ("GOOGLE", "gemini-1.5-pro"),
        ("ANTHROPIC", "claude-3-5-sonnet-latest")
    ]
    
    for provider, model in existing_tests:
        assert is_valid_model_for_provider(provider, model), f"Existing model {model} broken for {provider}"
        print(f"  ✅ {provider}: {model} - Still working")


if __name__ == "__main__":
    print("🧪 Running model catalog validation tests for issue #134...\n")
    
    try:
        test_missing_xai_models()
        test_missing_openai_models() 
        test_missing_google_models()
        test_existing_models_still_work()
        
        print("\n🎉 All tests passed! The model catalog fix is working correctly.")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        exit(1)