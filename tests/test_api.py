"""
Tests for Address Cleanser API endpoints.

These tests verify the REST API functionality.
"""

import sys

import pytest
from fastapi.testclient import TestClient

# Skip API tests on Python 3.8 due to anyio/TestClient ExceptionGroup issues
# These are known incompatibilities with TestClient's async cleanup on Python < 3.9
pytestmark = pytest.mark.skipif(
    sys.version_info < (3, 9),
    reason="TestClient has ExceptionGroup issues with anyio on Python 3.8",
)


@pytest.fixture
def api_client():
    """Create a test client for the API."""
    try:
        from api_server import app

        return TestClient(app)
    except ImportError:
        pytest.skip("FastAPI dependencies not installed")


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self, api_client):
        """Test that health endpoint returns healthy status."""
        response = api_client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_root_endpoint(self, api_client):
        """Test root endpoint returns API info."""
        response = api_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data


class TestValidateEndpoint:
    """Test single address validation endpoint."""

    def test_validate_single_address(self, api_client):
        """Test validating a single address."""
        response = api_client.post(
            "/api/v1/validate",
            json={"address": "123 Main St, Austin, TX 78701"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "formatted" in data
        assert "valid" in data
        assert "errors" in data
        assert isinstance(data["valid"], dict)

    def test_validate_with_options(self, api_client):
        """Test validation with options."""
        response = api_client.post(
            "/api/v1/validate",
            json={
                "address": "123 Main St Apt 5, Austin, TX 78701",
                "options": {
                    "return_parsed": True,
                    "return_confidence": True,
                    "return_original": True,
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "formatted" in data
        assert "parsed" in data
        assert "confidence" in data
        assert "original" in data

    def test_validate_invalid_address(self, api_client):
        """Test validation with invalid input."""
        response = api_client.post(
            "/api/v1/validate",
            json={"address": ""},
        )
        assert response.status_code == 200
        data = response.json()
        assert "errors" in data
        assert len(data["errors"]) > 0


class TestBatchEndpoint:
    """Test batch processing endpoint."""

    def test_batch_process(self, api_client):
        """Test batch processing multiple addresses."""
        response = api_client.post(
            "/api/v1/batch",
            json={
                "addresses": [
                    "123 Main St, Austin, TX 78701",
                    "456 Oak Ave, Dallas, TX 75201",
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "summary" in data
        assert len(data["results"]) == 2
        assert data["summary"]["total"] == 2

    def test_batch_with_options(self, api_client):
        """Test batch processing with options."""
        response = api_client.post(
            "/api/v1/batch",
            json={
                "addresses": ["123 Main St, Austin, TX 78701"],
                "return_parsed": True,
                "return_confidence": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1
        result = data["results"][0]
        assert "parsed" in result or "confidence" in result


class TestStatsEndpoint:
    """Test statistics endpoint."""

    def test_stats_endpoint(self, api_client):
        """Test getting processing statistics."""
        # First process some addresses to generate stats
        api_client.post(
            "/api/v1/validate",
            json={"address": "123 Main St, Austin, TX 78701"},
        )

        response = api_client.get("/api/v1/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_processed" in data
        assert "total_valid" in data
        assert "total_invalid" in data
        assert "average_confidence" in data


class TestRateLimiting:
    """Test rate limiting middleware."""

    def test_rate_limit_not_exceeded(self, api_client):
        """Test that normal usage doesn't trigger rate limit."""
        for _ in range(10):
            response = api_client.get("/api/v1/health")
            assert response.status_code == 200
