#!/usr/bin/env python3
"""
Script to sanitize ModelCatalog: deduplicate & correct metadata.

This script performs the following operations:
1. Removes duplicate models (same 'value' key)
2. Fixes impossible future dates (keeps only dates <= today)
3. Normalizes keys and metadata
4. Validates against ALLOWED_MODELS allow-list
"""

import json
from datetime import date, datetime
from typing import Any


def load_allowed_models(file_path: str = "allowed_models.json") -> list[str]:
    """Load the allowed models from JSON file."""
    try:
        with open(file_path) as f:
            data = json.load(f)
            return data.get("allowed_models", [])
    except FileNotFoundError:
        print(
            f"Warning: {file_path} not found. Proceeding without allow-list filtering."
        )
        return []


def is_valid_date(date_str: str, today: date = None) -> bool:
    """Check if a date string is valid and not in the future."""
    if today is None:
        today = date.today()

    try:
        release_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        return release_date <= today
    except (ValueError, TypeError):
        return False


def normalize_model_keys(model: dict[str, Any]) -> dict[str, Any]:
    """Normalize model keys and ensure required fields exist."""
    normalized = {}

    # Required fields
    normalized["value"] = model.get("value", "").strip()
    normalized["label"] = model.get("label", "").strip()

    # Optional fields with defaults
    normalized["modern"] = model.get("modern", False)

    # Only include release_date if it's valid
    release_date = model.get("release_date")
    if release_date and is_valid_date(release_date):
        normalized["release_date"] = release_date

    # Optional capability flags
    for capability in ["voice", "code"]:
        if model.get(capability):
            normalized[capability] = True

    return normalized


def deduplicate_models(models: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove duplicate models based on 'value' key, keeping the first occurrence."""
    seen_values = set()
    deduplicated = []

    for model in models:
        value = model.get("value", "").strip()
        if value and value not in seen_values:
            seen_values.add(value)
            deduplicated.append(model)
        else:
            print(f"Removing duplicate model: {value}")

    return deduplicated


def sanitize_provider_models(
    provider_models: list[dict[str, Any]], allowed_models: list[str] = None
) -> list[dict[str, Any]]:
    """Sanitize models for a single provider."""
    # Step 1: Normalize all models
    normalized_models = [normalize_model_keys(model) for model in provider_models]

    # Step 2: Remove duplicates
    deduplicated_models = deduplicate_models(normalized_models)

    # Step 3: Filter by allowed models if provided
    if allowed_models:
        filtered_models = [
            model
            for model in deduplicated_models
            if model.get("value") in allowed_models
        ]
        if len(filtered_models) != len(deduplicated_models):
            removed_count = len(deduplicated_models) - len(filtered_models)
            print(f"Filtered out {removed_count} models not in allow-list")
        return filtered_models

    return deduplicated_models


def sanitize_model_catalog(
    catalog: dict[str, list[dict[str, Any]]], allowed_models: list[str] = None
) -> dict[str, list[dict[str, Any]]]:
    """Sanitize the entire model catalog."""
    sanitized_catalog = {}

    for provider, models in catalog.items():
        print(f"Sanitizing {provider} models...")
        sanitized_models = sanitize_provider_models(models, allowed_models)
        sanitized_catalog[provider] = sanitized_models
        print(f"  {len(models)} -> {len(sanitized_models)} models")

    return sanitized_catalog


def main():
    """Main function to sanitize the model catalog."""
    # Load allowed models
    allowed_models = load_allowed_models()
    print(f"Loaded {len(allowed_models)} allowed models")

    # Import the current model catalog
    try:
        from framework.helpers.model_catalog import MODEL_CATALOG
    except ImportError:
        print("Error: Could not import MODEL_CATALOG")
        return

    print(f"Original catalog has {len(MODEL_CATALOG)} providers")

    # Sanitize the catalog
    sanitized_catalog = sanitize_model_catalog(MODEL_CATALOG, allowed_models)

    # Save sanitized catalog to a new file for review
    output_file = "sanitized_model_catalog.json"
    with open(output_file, "w") as f:
        json.dump(sanitized_catalog, f, indent=2)

    print(f"Sanitized catalog saved to {output_file}")

    # Print summary statistics
    original_total = sum(len(models) for models in MODEL_CATALOG.values())
    sanitized_total = sum(len(models) for models in sanitized_catalog.values())

    print("\nSummary:")
    print(f"  Original models: {original_total}")
    print(f"  Sanitized models: {sanitized_total}")
    print(f"  Removed: {original_total - sanitized_total}")


if __name__ == "__main__":
    main()
