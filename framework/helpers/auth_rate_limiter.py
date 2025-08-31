"""
Authentication rate limiter to prevent auth spam and excessive logging.
"""

import time
from collections import defaultdict


class AuthRateLimiter:
    """Rate limiter specifically for authentication requests to prevent spam."""

    def __init__(self, max_auth_per_minute: int = 10, max_logs_per_minute: int = 5):
        """Initialize the authentication rate limiter.

        Args:
            max_auth_per_minute: Maximum authentication attempts per IP per minute
            max_logs_per_minute: Maximum success log messages per IP per minute
        """
        self.max_auth_per_minute = max_auth_per_minute
        self.max_logs_per_minute = max_logs_per_minute
        self.auth_attempts: dict[str, list] = defaultdict(list)
        self.success_logs: dict[str, list] = defaultdict(list)

    def _cleanup_old_entries(self, tracking_dict: dict[str, list], window: int = 60):
        """Remove entries older than the specified window (in seconds)."""
        current_time = time.time()
        cutoff_time = current_time - window

        for ip in list(tracking_dict.keys()):
            tracking_dict[ip] = [t for t in tracking_dict[ip] if t > cutoff_time]
            if not tracking_dict[ip]:
                del tracking_dict[ip]

    def is_auth_allowed(self, ip_address: str) -> bool:
        """Check if authentication attempt should be allowed for this IP.

        Args:
            ip_address: The IP address attempting authentication

        Returns:
            True if auth attempt is allowed, False if rate limited
        """
        self._cleanup_old_entries(self.auth_attempts)

        current_attempts = len(self.auth_attempts.get(ip_address, []))
        if current_attempts >= self.max_auth_per_minute:
            return False

        # Record this attempt
        self.auth_attempts[ip_address].append(time.time())
        return True

    def should_log_success(self, ip_address: str) -> bool:
        """Check if successful authentication should be logged for this IP.

        Args:
            ip_address: The IP address that authenticated successfully

        Returns:
            True if should log, False if logging is rate limited
        """
        self._cleanup_old_entries(self.success_logs)

        current_logs = len(self.success_logs.get(ip_address, []))
        if current_logs >= self.max_logs_per_minute:
            return False

        # Record this log
        self.success_logs[ip_address].append(time.time())
        return True

    def get_stats(self) -> dict[str, dict[str, int]]:
        """Get current rate limiting statistics."""
        self._cleanup_old_entries(self.auth_attempts)
        self._cleanup_old_entries(self.success_logs)

        return {
            "auth_attempts": {
                ip: len(times) for ip, times in self.auth_attempts.items()
            },
            "success_logs": {ip: len(times) for ip, times in self.success_logs.items()},
        }


# Global instance for the application
auth_rate_limiter = AuthRateLimiter()
