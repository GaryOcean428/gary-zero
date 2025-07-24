import unittest
import sys
from pathlib import Path
from datetime import date

# Add parent directory to path to import our script
sys.path.insert(0, str(Path(__file__).parent.parent))

from sanitize_model_catalog import sanitize_model_catalog, load_allowed_models
from framework.helpers.model_catalog import MODEL_CATALOG


class TestModelCatalog(unittest.TestCase):
    def setUp(self):
        self.allowed_models = load_allowed_models()
        self.original_catalog = MODEL_CATALOG

    def test_no_duplicate_values_within_provider(self):
        """Verify that there are no duplicate model values within each provider."""
        sanitized_catalog = sanitize_model_catalog(self.original_catalog, self.allowed_models)
        
        for provider, models in sanitized_catalog.items():
            provider_values = [model["value"] for model in models]
            self.assertEqual(
                len(provider_values), len(set(provider_values)), 
                f"Duplicate model values found within provider {provider}"
            )

    def test_future_release_dates(self):
        """Ensure that all release dates are in the past or today."""
        today = date.today()
        sanitized_catalog = sanitize_model_catalog(self.original_catalog, self.allowed_models)
        for provider, models in sanitized_catalog.items():
            for model in models:
                release_date = model.get("release_date")
                if release_date:
                    release_date = date.fromisoformat(release_date)
                    self.assertLessEqual(release_date, today, f"Future release date found: {release_date} in {provider}")


if __name__ == "__main__":
    unittest.main()
