"""Tests for app/routers/health.py — health check endpoint."""


class TestHealthCheck:
    def test_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_returns_status_ok(self, client):
        response = client.get("/")
        data = response.json()
        assert data["status"] == "ok"

    def test_returns_service_name(self, client):
        response = client.get("/")
        data = response.json()
        assert "service" in data
