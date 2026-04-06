from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_app_starts():
    # Attempting to hit the healthcheck endpoint doesn't require DB (assuming health check doesn't ping db or we catch it)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] in ["healthy", "degraded"]


def test_all_routes_registered():
    routes = [route.path for route in app.routes]

    # Check auth
    assert any("/api/v1/auth/login" in path for path in routes)
    # Check users
    assert any("/api/v1/users" in path for path in routes)
    # Check records
    assert any("/api/v1/records" in path for path in routes)
    # Check dashboard
    assert any("/api/v1/dashboard/summary" in path for path in routes)
