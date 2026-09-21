from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_documentation_is_available() -> None:
    docs_response = client.get("/api-docs")
    schema_response = client.get("/api/openapi.json")

    assert docs_response.status_code == 200
    assert schema_response.status_code == 200
    assert schema_response.json()["info"]["title"] == "Creditos API"
