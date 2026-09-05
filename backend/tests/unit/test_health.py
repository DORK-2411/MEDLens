"""Health endpoint tests."""

from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Verify the /api/health endpoint."""

    def test_health_returns_200(self, client: TestClient) -> None:
        """Health check returns 200 with expected payload."""
        response = client.get("/api/health")

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "medlens-api"

    def test_health_response_has_no_phi(self, client: TestClient) -> None:
        """Health response must never contain patient data."""
        response = client.get("/api/health")
        data = response.json()

        # Only allowed keys
        assert set(data.keys()) == {"status", "service"}
