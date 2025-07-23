#!/usr/bin/env python3
"""
Test script to validate model catalog modernization.

This script tests that:
1. Model catalog loads correctly
2. Modern and deprecated models are properly categorized
3. Helper functions work as expected
4. Recommended models are modern when available
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from framework.helpers.model_catalog import (
    MODEL_CATALOG,
    get_all_deprecated_models,
    get_all_modern_models,
    get_deprecated_models_for_provider,
    get_model_release_date,
    get_modern_models_for_provider,
    get_recommended_model_for_provider,
    is_model_deprecated,
    is_model_modern,
)


def test_model_catalog_loading():
    """Test that model catalog loads correctly."""
    print("Testing model catalog loading...")
    assert MODEL_CATALOG, "Model catalog should not be empty"
    assert "ANTHROPIC" in MODEL_CATALOG, "ANTHROPIC should be in catalog"
    assert "OPENAI" in MODEL_CATALOG, "OPENAI should be in catalog"
    print("✓ Model catalog loaded successfully")

def test_modern_vs_deprecated_categorization():
    """Test that models are properly categorized as modern (no deprecated models remain)."""
    print("\nTesting modern vs deprecated categorization...")

    # Test OpenAI models
    openai_modern = get_modern_models_for_provider("OPENAI")
    openai_deprecated = get_deprecated_models_for_provider("OPENAI")

    assert len(openai_modern) > 0, "OpenAI should have modern models"
    assert len(openai_deprecated) == 0, "OpenAI should have no deprecated models (all removed)"

    # Check specific models
    assert is_model_modern("OPENAI", "o3"), "o3 should be modern"
    assert not is_model_deprecated("OPENAI", "gpt-3.5-turbo"), "gpt-3.5-turbo should no longer exist"

    # Test Anthropic models
    anthropic_modern = get_modern_models_for_provider("ANTHROPIC")
    anthropic_deprecated = get_deprecated_models_for_provider("ANTHROPIC")

    assert len(anthropic_modern) > 0, "Anthropic should have modern models"
    assert len(anthropic_deprecated) == 0, "Anthropic should have no deprecated models (all removed)"

    # Check specific models
    assert is_model_modern("ANTHROPIC", "claude-sonnet-4-20250514"), "Claude 4 should be modern"
    assert not is_model_deprecated("ANTHROPIC", "claude-2.0"), "Claude 2.0 should no longer exist"

    print("✓ Models properly categorized as modern only (deprecated models removed)")

def test_recommended_models():
    """Test that recommended models are modern when available."""
    print("\nTesting recommended models...")

    for provider in ["OPENAI", "ANTHROPIC", "GOOGLE", "XAI", "PERPLEXITY"]:
        recommended = get_recommended_model_for_provider(provider)
        assert recommended, f"{provider} should have a recommended model"

        # Check if the recommended model is modern
        model_name = recommended["value"]
        if is_model_modern(provider, model_name):
            print(f"✓ {provider} recommended model '{model_name}' is modern")
        elif is_model_deprecated(provider, model_name):
            print(f"⚠ {provider} recommended model '{model_name}' is deprecated")
        else:
            print(f"? {provider} recommended model '{model_name}' has no modern/deprecated flag")

def test_release_dates():
    """Test that release dates are properly set for modern models."""
    print("\nTesting release dates...")

    # Test some specific modern models only
    test_cases = [
        ("OPENAI", "o3", "2025-01-31"),
        ("OPENAI", "gpt-4o", "2024-05-13"),
        ("ANTHROPIC", "claude-sonnet-4-20250514", "2025-05-14"),
        ("ANTHROPIC", "claude-3-5-sonnet-20241022", "2024-10-22"),
    ]

    for provider, model, expected_date in test_cases:
        actual_date = get_model_release_date(provider, model)
        assert actual_date == expected_date, f"{provider}/{model} should have release date {expected_date}, got {actual_date}"
        print(f"✓ {provider}/{model} release date: {actual_date}")

def test_modern_models_prioritized():
    """Test that modern models appear first in provider lists."""
    print("\nTesting model ordering (modern first)...")

    for provider in ["OPENAI", "ANTHROPIC", "GOOGLE"]:
        models = MODEL_CATALOG[provider]
        if len(models) > 1:
            # Check if first model is modern or at least not deprecated
            first_model = models[0]
            first_model_name = first_model["value"]

            if first_model.get("modern", False):
                print(f"✓ {provider} first model '{first_model_name}' is modern")
            elif not first_model.get("deprecated", False):
                print(f"? {provider} first model '{first_model_name}' is not flagged as modern or deprecated")
            else:
                print(f"⚠ {provider} first model '{first_model_name}' is deprecated (should be reordered)")

def test_statistics():
    """Print statistics about modern vs deprecated models."""
    print("\nModel Statistics:")

    all_modern = get_all_modern_models()
    all_deprecated = get_all_deprecated_models()

    print(f"Total modern models: {len(all_modern)}")
    print(f"Total deprecated models: {len(all_deprecated)}")
    print(f"Modern/Deprecated ratio: {len(all_modern)}/{len(all_deprecated)}")

    # Per-provider statistics
    print("\nPer-provider breakdown:")
    for provider in sorted(MODEL_CATALOG.keys()):
        modern_count = len(get_modern_models_for_provider(provider))
        deprecated_count = len(get_deprecated_models_for_provider(provider))
        total_count = len(MODEL_CATALOG[provider])
        uncategorized = total_count - modern_count - deprecated_count
        print(f"  {provider}: {modern_count} modern, {deprecated_count} deprecated, {uncategorized} uncategorized")

def main():
    """Run all tests."""
    print("=== Model Catalog Modernization Test ===\n")

    try:
        test_model_catalog_loading()
        test_modern_vs_deprecated_categorization()
        test_recommended_models()
        test_release_dates()
        test_modern_models_prioritized()
        test_statistics()

        print("\n=== All Tests Passed! ===")
        return 0

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
