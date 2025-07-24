"""
Diagnostic API handler for testing integrations.
Provides endpoints to verify SearchXNG and other service connectivity.
"""

import os

import aiohttp
from flask import jsonify

from framework.helpers.api import ApiHandler


class Diagnostics(ApiHandler):
    """API handler for diagnostic endpoints."""

    async def handle_request(self, request):
        """Handle diagnostic requests."""

        # Get the specific diagnostic test requested
        test = request.json.get("test", "all") if request.is_json else "all"

        results = {
            "timestamp": os.popen("date").read().strip(),
            "environment": {
                "railway_env": os.getenv("RAILWAY_ENVIRONMENT"),
                "railway_project": os.getenv("RAILWAY_PROJECT_NAME"),
                "node_env": os.getenv("NODE_ENV", "development"),
            },
        }

        if test in ["all", "searchxng"]:
            results["searchxng"] = await self._test_searchxng()

        if test in ["all", "env"]:
            results["env_vars"] = self._get_relevant_env_vars()

        if test in ["all", "e2b"]:
            results["e2b"] = self._test_e2b()

        return jsonify(results)

    async def _test_searchxng(self):
        """Test SearchXNG connectivity."""
        searxng_url = os.getenv("SEARXNG_URL")

        result = {
            "configured_url": searxng_url,
            "resolved": "${{" not in str(searxng_url) if searxng_url else False,
            "status": "not_configured",
        }

        if not searxng_url:
            result["error"] = "SEARXNG_URL not set"
            return result

        if "${{" in searxng_url:
            result["error"] = "SEARXNG_URL contains unresolved reference variables"
            result["hint"] = (
                "Ensure searchxng service has PORT environment variable set"
            )
            return result

        # Test connectivity
        try:
            async with aiohttp.ClientSession() as session:
                test_url = f"{searxng_url}/search"
                params = {"q": "test", "format": "json"}

                async with session.get(test_url, params=params, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        result["status"] = "connected"
                        result["response_status"] = response.status
                        result["results_count"] = len(data.get("results", []))
                    else:
                        result["status"] = "error"
                        result["response_status"] = response.status
                        result["error"] = f"HTTP {response.status}"

        except aiohttp.ClientError as e:
            result["status"] = "connection_failed"
            result["error"] = str(e)
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

        return result

    def _test_e2b(self):
        """Test E2B configuration."""
        e2b_api_key = os.getenv("E2B_API_KEY")

        return {
            "configured": bool(e2b_api_key),
            "key_length": len(e2b_api_key) if e2b_api_key else 0,
            "code_execution_mode": os.getenv("CODE_EXECUTION_MODE", "ssh"),
            "ssh_disabled": os.getenv("DISABLE_SSH_EXECUTION", "false").lower()
            == "true",
        }

    def _get_relevant_env_vars(self):
        """Get relevant environment variables for debugging."""
        relevant_vars = [
            "SEARXNG_URL",
            "SEARCH_PROVIDER",
            "CODE_EXECUTION_MODE",
            "DISABLE_SSH_EXECUTION",
            "USE_E2B_EXECUTION",
            "RAILWAY_ENVIRONMENT",
            "RAILWAY_PROJECT_NAME",
            "RAILWAY_SERVICE_NAME",
            "RAILWAY_SERVICE_SEARXNG_URL",
            "PORT",
            "WEB_UI_HOST",
        ]

        env_vars = {}
        for var in relevant_vars:
            value = os.getenv(var)
            if value:
                # Mask sensitive values
                if "KEY" in var or "TOKEN" in var:
                    value = value[:8] + "..." if len(value) > 8 else "***"
                env_vars[var] = value

        return env_vars

    @staticmethod
    def requires_auth():
        """Diagnostics require authentication."""
        return True
