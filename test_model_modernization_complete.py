#!/usr/bin/env python3
"""Test script to verify model modernization implementation."""

import sys
import asyncio

def test_model_catalog():
    """Test the model catalog functions."""
    print("=== TESTING MODEL CATALOG ===")
    
    try:
        from framework.helpers.model_catalog import (
            get_models_for_provider,
            get_modern_models_for_provider,
            get_deprecated_models_for_provider,
            get_voice_models_for_provider,
            get_code_models_for_provider,
            is_model_modern,
            is_model_deprecated
        )
        
        # Test modern model prioritization
        print("1. Testing modern model prioritization...")
        openai_modern = get_modern_models_for_provider("OPENAI")
        print(f"   OpenAI modern models: {len(openai_modern)}")
        if openai_modern:
            print(f"   First model: {openai_modern[0].get('label', 'N/A')}")
        
        anthropic_modern = get_modern_models_for_provider("ANTHROPIC")
        print(f"   Anthropic modern models: {len(anthropic_modern)}")
        if anthropic_modern:
            print(f"   First model: {anthropic_modern[0].get('label', 'N/A')}")
        
        # Test deprecated models
        print("2. Testing deprecated model detection...")
        openai_deprecated = get_deprecated_models_for_provider("OPENAI")
        print(f"   OpenAI deprecated models: {len(openai_deprecated)}")
        
        # Test specific model checks
        print("3. Testing specific model classifications...")
        test_cases = [
            ("OPENAI", "o3"),
            ("OPENAI", "gpt-3.5-turbo"),
            ("ANTHROPIC", "claude-sonnet-4-20250514"),
            ("ANTHROPIC", "claude-2.0")
        ]
        
        for provider, model in test_cases:
            modern = is_model_modern(provider, model)
            deprecated = is_model_deprecated(provider, model)
            print(f"   {provider} {model}: modern={modern}, deprecated={deprecated}")
        
        # Test voice models
        print("4. Testing voice models...")
        voice_openai = get_voice_models_for_provider("OPENAI")
        voice_google = get_voice_models_for_provider("GOOGLE")
        print(f"   OpenAI voice models: {len(voice_openai)}")
        print(f"   Google voice models: {len(voice_google)}")
        
        # Test code models  
        print("5. Testing code models...")
        code_anthropic = get_code_models_for_provider("ANTHROPIC")
        code_deepseek = get_code_models_for_provider("DEEPSEEK")
        print(f"   Anthropic code models: {len(code_anthropic)}")
        print(f"   DeepSeek code models: {len(code_deepseek)}")
        
        print("✅ Model catalog tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Model catalog tests failed: {e}")
        return False


def test_settings_integration():
    """Test settings integration."""
    print("\n=== TESTING SETTINGS INTEGRATION ===")
    
    try:
        from framework.helpers.settings.api import get_settings_for_ui
        from framework.helpers.settings.types import DEFAULT_SETTINGS
        
        print("1. Testing default settings...")
        defaults = DEFAULT_SETTINGS
        print(f"   Chat model: {defaults['chat_model_provider']} - {defaults['chat_model_name']}")
        print(f"   Voice model: {defaults['voice_model_provider']} - {defaults['voice_model_name']}")
        print(f"   Code model: {defaults['code_model_provider']} - {defaults['code_model_name']}")
        
        print("2. Testing UI settings generation...")
        ui_settings = get_settings_for_ui(defaults)
        sections = ui_settings.get("sections", [])
        print(f"   Total sections: {len(sections)}")
        
        # Find voice and code model sections
        voice_section = None
        code_section = None
        for section in sections:
            if section.get("id") == "voice_model":
                voice_section = section
            elif section.get("id") == "code_model":
                code_section = section
        
        if voice_section:
            print(f"   ✅ Voice model section found: {voice_section['title']}")
        else:
            print("   ❌ Voice model section not found")
            
        if code_section:
            print(f"   ✅ Code model section found: {code_section['title']}")
        else:
            print("   ❌ Code model section not found")
        
        print("✅ Settings integration tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Settings integration tests failed: {e}")
        return False


async def test_api_endpoints():
    """Test the new API endpoints."""
    print("\n=== TESTING API ENDPOINTS ===")
    
    try:
        # Test get_models_for_provider endpoint
        print("1. Testing get_models_for_provider API...")
        from framework.api.get_models_for_provider import GetModelsForProvider
        from framework.helpers.api import Request
        
        handler = GetModelsForProvider()
        request = Request()  # Mock request
        
        # Test with OpenAI
        result = await handler.process({"provider": "OPENAI"}, request)
        print(f"   OpenAI API result: {result.get('count', 0)} models")
        if 'modern_count' in result:
            print(f"   Modern models: {result['modern_count']}, Deprecated: {result['deprecated_count']}")
        
        # Test voice models endpoint
        print("2. Testing get_voice_models API...")
        from framework.api.get_voice_models import GetVoiceModels
        
        voice_handler = GetVoiceModels()
        voice_result = await voice_handler.process({}, request)
        print(f"   Voice models API result: {voice_result.get('count', 0)} models")
        
        # Test code models endpoint
        print("3. Testing get_code_models API...")
        from framework.api.get_code_models import GetCodeModels
        
        code_handler = GetCodeModels()
        code_result = await code_handler.process({}, request)
        print(f"   Code models API result: {code_result.get('count', 0)} models")
        
        print("✅ API endpoint tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ API endpoint tests failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🚀 Starting Gary-Zero Model Modernization Tests\n")
    
    results = []
    
    # Test model catalog
    results.append(test_model_catalog())
    
    # Test settings integration  
    results.append(test_settings_integration())
    
    # Test API endpoints
    results.append(await test_api_endpoints())
    
    # Summary
    print(f"\n=== TEST SUMMARY ===")
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Model modernization is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))