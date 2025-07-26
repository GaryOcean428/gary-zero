#!/bin/bash

# Unit Test Runner for Gary-Zero
# Ensures the three required test cases from Step 8 are executed

set -e

echo "🧪 Running Unit Tests for Step 8 Implementation"
echo "=============================================="

# Change to project root
cd "$(dirname "$0")/.."

echo "📋 Test Cases to Execute:"
echo "  ✓ test_settings_persist_across_instances()"
echo "  ✓ test_default_util_model()"
echo "  ✓ test_model_catalog_validation()"
echo ""

# Run the specific test cases we added
echo "🔍 Running settings persistence test..."
python -m pytest tests/unit/test_settings_manager.py::test_settings_persist_across_instances -v

echo ""
echo "🔍 Running default utility model test..."
python -m pytest tests/unit/test_settings_manager.py::test_default_util_model -v

echo ""
echo "🔍 Running model catalog validation test..."
python -m pytest tests/unit/test_settings_manager.py::test_model_catalog_validation -v

echo ""
echo "✅ All Step 8 unit tests completed successfully!"
