from fastapi.testclient import TestClient

from app.main import app


def test_root_endpoint_returns_project_info() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["service"]
    assert payload["environment"]
    assert payload["docs_url"] == "/docs"
    assert payload["health_url"] == "/health"


def test_health_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"]
    assert payload["environment"]
