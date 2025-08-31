"""
Tests for authentication rate limiter functionality.
"""

import unittest

from framework.helpers.auth_rate_limiter import AuthRateLimiter


class TestAuthRateLimiter(unittest.TestCase):

    def setUp(self):
        self.limiter = AuthRateLimiter(max_auth_per_minute=3, max_logs_per_minute=2)

    def test_auth_rate_limiting(self):
        """Test authentication request rate limiting."""
        ip = "127.0.0.1"

        # First 3 attempts should be allowed
        for i in range(3):
            self.assertTrue(
                self.limiter.is_auth_allowed(ip),
                f"Auth attempt {i+1} should be allowed",
            )

        # 4th attempt should be blocked
        self.assertFalse(
            self.limiter.is_auth_allowed(ip), "4th auth attempt should be blocked"
        )

    def test_success_log_rate_limiting(self):
        """Test success log rate limiting."""
        ip = "127.0.0.1"

        # First 2 logs should be allowed
        for i in range(2):
            self.assertTrue(
                self.limiter.should_log_success(ip),
                f"Success log {i+1} should be allowed",
            )

        # 3rd log should be blocked
        self.assertFalse(
            self.limiter.should_log_success(ip), "3rd success log should be blocked"
        )

    def test_different_ips_isolated(self):
        """Test that different IPs are isolated from each other."""
        ip1 = "127.0.0.1"
        ip2 = "192.168.1.1"

        # Use up limit for ip1
        for _ in range(3):
            self.assertTrue(self.limiter.is_auth_allowed(ip1))
        self.assertFalse(self.limiter.is_auth_allowed(ip1))

        # ip2 should still work
        self.assertTrue(self.limiter.is_auth_allowed(ip2))

    def test_stats_collection(self):
        """Test statistics collection."""
        ip = "127.0.0.1"

        self.limiter.is_auth_allowed(ip)
        self.limiter.is_auth_allowed(ip)
        self.limiter.should_log_success(ip)

        stats = self.limiter.get_stats()

        self.assertIn("auth_attempts", stats)
        self.assertIn("success_logs", stats)
        self.assertEqual(stats["auth_attempts"][ip], 2)
        self.assertEqual(stats["success_logs"][ip], 1)


if __name__ == "__main__":
    unittest.main()
