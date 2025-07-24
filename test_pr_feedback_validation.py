#!/usr/bin/env python3
"""Test script to validate PR feedback fixes."""


def test_pr_feedback_fixes():
    """Test all the specific issues mentioned in PR feedback."""
    print("🔍 VALIDATING PR FEEDBACK FIXES")
    print("=" * 50)

    try:
        from framework.helpers.model_catalog import get_models_for_provider
        from framework.helpers.settings.types import DEFAULT_SETTINGS

        all_passed = True

        # 1. Test that Claude Sonnet 3.7 is present
        print("1. Testing Claude Sonnet 3.7 presence...")
        anthropic_models = get_models_for_provider("ANTHROPIC")
        claude_37_present = any(
            "claude-3-7-sonnet" in m["value"] or "3.7" in m["label"]
            for m in anthropic_models
        )
        print(f"   ✅ Claude Sonnet 3.7 present: {claude_37_present}")
        if not claude_37_present:
            all_passed = False

        # 2. Test that Google Gemini CLI models are present
        print("2. Testing Google Gemini CLI models...")
        google_models = get_models_for_provider("GOOGLE")
        cli_models = [m for m in google_models if "cli" in m["value"].lower()]
        print(f"   ✅ Google CLI models found: {len(cli_models)}")
        for cli_model in cli_models:
            print(f"      - {cli_model['label']}")
        if len(cli_models) == 0:
            all_passed = False

        # 3. Test that Qwen 3 Coder is present
        print("3. Testing Qwen 3 Coder presence...")
        qwen_models = get_models_for_provider("QWEN")
        qwen_3_coder = any(m["value"] == "qwen-3-coder" for m in qwen_models)
        print(f"   ✅ Qwen 3 Coder present: {qwen_3_coder}")
        if not qwen_3_coder:
            all_passed = False

        # 4. Test that Kimi K2 Instruct is present
        print("4. Testing Kimi K2 Instruct presence...")
        groq_models = get_models_for_provider("GROQ")
        kimi_k2 = any(m["value"] == "kimi-k2-instruct" for m in groq_models)
        print(f"   ✅ Kimi K2 Instruct present: {kimi_k2}")
        if not kimi_k2:
            all_passed = False

        # 5. Test that gpt-4.1-embeddings is removed
        print("5. Testing gpt-4.1-embeddings removal...")
        openai_models = get_models_for_provider("OPENAI")
        bad_embedding_removed = not any(
            m["value"] == "gpt-4.1-embeddings" for m in openai_models
        )
        print(f"   ✅ gpt-4.1-embeddings removed: {bad_embedding_removed}")
        if not bad_embedding_removed:
            all_passed = False

        # 6. Test that valid embedding model is used in defaults
        print("6. Testing valid embedding model in defaults...")
        embed_model = DEFAULT_SETTINGS["embed_model_name"]
        valid_embedding = embed_model in [m["value"] for m in openai_models]
        print(
            f"   ✅ Default embedding model '{embed_model}' is valid: {valid_embedding}"
        )
        if not valid_embedding:
            all_passed = False

        # 7. Test model counts and integrity
        print("7. Testing model catalog integrity...")
        from framework.helpers.model_catalog import (
            get_all_deprecated_models,
            get_all_models,
            get_all_modern_models,
        )

        all_models = get_all_models()
        modern_models = get_all_modern_models()
        deprecated_models = get_all_deprecated_models()

        # Check no model is both modern and deprecated
        conflicts = []
        for model in all_models:
            if model.get("modern", False) and model.get("deprecated", False):
                conflicts.append(model["value"])

        print(f"   Total models: {len(all_models)}")
        print(f"   Modern models: {len(modern_models)}")
        print(f"   Deprecated models: {len(deprecated_models)}")
        print(f"   ✅ No modern/deprecated conflicts: {len(conflicts) == 0}")
        if len(conflicts) > 0:
            print(f"      Conflicts found: {conflicts}")
            all_passed = False

        # 8. Test code model coverage
        print("8. Testing code model coverage...")
        from framework.helpers.model_catalog import get_all_code_models

        code_models = get_all_code_models()
        print(f"   ✅ Total code models: {len(code_models)}")
        for code_model in code_models:
            print(f"      - {code_model['label']}")
        if len(code_models) < 5:  # Should have at least 5 code models now
            print("   ⚠️  Warning: Expected more code models")

        print("\n" + "=" * 50)
        if all_passed:
            print("🎉 ALL PR FEEDBACK FIXES VALIDATED SUCCESSFULLY!")
            return True
        else:
            print("❌ SOME PR FEEDBACK FIXES FAILED VALIDATION")
            return False

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False


if __name__ == "__main__":
    success = test_pr_feedback_fixes()
    exit(0 if success else 1)
