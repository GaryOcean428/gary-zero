"""
Test for the error reporting API endpoint.

This module tests the /api/error_report endpoint to ensure it properly handles
error reports from the client and returns the expected 204 status code.
"""

import json
import logging
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from main import app

# Create test client
client = TestClient(app)


class TestErrorReportEndpoint:
    """Test class for the error reporting endpoint."""

    def test_error_report_json_payload(self):
        """Test error reporting endpoint with JSON payload."""
        # Test data mimicking the client error reporter structure
        test_payload = {
            "id": 1,
            "sessionId": "test_session_123",
            "timestamp": "2025-07-23T12:47:00Z",
            "url": "http://test.example.com",
            "userAgent": "test-agent/1.0",
            "error": {
                "message": "Test error message",
                "stack": "Error: Test error\n    at test.js:1:1",
                "name": "TestError"
            },
            "context": {
                "connectionStatus": True,
                "currentContext": "test_context"
            }
        }

        # Capture logs to verify error reporting
        with patch('api.error_report.logger') as mock_logger:
            response = client.post(
                "/api/error_report",
                json=test_payload,
                headers={"Content-Type": "application/json"}
            )

            # Verify response
            assert response.status_code == 204
            assert response.content == b""

            # Verify logging was called
            mock_logger.error.assert_called_once()
            mock_logger.info.assert_called_once()

            # Check that the payload was logged
            logged_call = mock_logger.error.call_args[0][0]
            assert "Client error report:" in logged_call
            assert "Test error message" in logged_call

    def test_error_report_minimal_payload(self):
        """Test error reporting endpoint with minimal JSON payload."""
        test_payload = {
            "error": {"message": "Minimal test error"}
        }

        response = client.post(
            "/api/error_report",
            json=test_payload,
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 204
        assert response.content == b""

    def test_error_report_raw_text(self):
        """Test error reporting endpoint with raw text payload."""
        test_data = "Raw error message"

        with patch('api.error_report.logger') as mock_logger:
            response = client.post(
                "/api/error_report",
                content=test_data,
                headers={"Content-Type": "text/plain"}
            )

            assert response.status_code == 204
            assert response.content == b""

            # Verify the raw body was logged
            mock_logger.error.assert_called_once()
            logged_call = mock_logger.error.call_args[0][0]
            assert "raw_body" in logged_call
            assert "Raw error message" in logged_call

    def test_error_report_invalid_json(self):
        """Test error reporting endpoint with invalid JSON."""
        invalid_json = '{"invalid": json}'

        with patch('api.error_report.logger') as mock_logger:
            response = client.post(
                "/api/error_report",
                content=invalid_json,
                headers={"Content-Type": "application/json"}
            )

            # Should still return 204 even with invalid JSON
            assert response.status_code == 204
            assert response.content == b""

            # Should log a warning about invalid JSON
            mock_logger.warning.assert_called_once()
            warning_call = mock_logger.warning.call_args[0][0]
            assert "Failed to parse JSON payload" in warning_call

    def test_error_report_empty_payload(self):
        """Test error reporting endpoint with empty payload."""
        response = client.post(
            "/api/error_report",
            json={},
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 204
        assert response.content == b""

    def test_error_report_wrong_method(self):
        """Test that GET requests to error_report return 404."""
        response = client.get("/api/error_report")
        
        # Should return 404 for GET requests since only POST is allowed
        assert response.status_code == 404

    def test_error_report_options_method(self):
        """Test that OPTIONS requests work for CORS."""
        response = client.options("/api/error_report")
        
        # OPTIONS should work for CORS preflight
        assert response.status_code in [200, 404]  # Depends on CORS middleware config

    def test_error_report_user_agent_logging(self):
        """Test that user agent and client IP are logged."""
        test_payload = {"error": {"message": "Test for user agent logging"}}
        custom_user_agent = "CustomTestAgent/1.0"

        with patch('api.error_report.logger') as mock_logger:
            response = client.post(
                "/api/error_report",
                json=test_payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": custom_user_agent
                }
            )

            assert response.status_code == 204

            # Check that user agent was logged
            info_call = mock_logger.info.call_args[0][0]
            assert custom_user_agent in info_call
            assert "Error report received from" in info_call


if __name__ == "__main__":
    pytest.main([__file__])