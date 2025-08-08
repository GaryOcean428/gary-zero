"""API endpoint to get environment variable status for settings."""

from framework.helpers.api import ApiHandler, Input, Output, Request
from framework.helpers.settings.env_priority import get_env_var_status


class GetEnvStatus(ApiHandler):
    """Get environment variable status for settings."""
    
    async def process(self, input_data: Input, request: Request) -> Output:
        """Get the status of environment variables affecting settings.
        
        Returns:
            Dictionary containing:
            - overridden: Settings that are overridden by environment variables
            - available: Environment variables that are available
            - missing: Environment variables that could be set
        """
        try:
            env_status = get_env_var_status()
            return {
                "env_status": env_status,
                "message": "Environment variable status retrieved successfully"
            }
        except Exception as e:
            print(f"ERROR in GetEnvStatus: {e}")
            import traceback
            traceback.print_exc()
            raise