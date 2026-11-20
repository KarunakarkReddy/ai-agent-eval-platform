
from fastapi.testclient import TestClient

from ..main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert "message" in response.json()


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_chat_rejects_empty_query():
    response = client.post(
        "/chat",
        json={"query": ""}
    )

    assert response.status_code == 422


def test_monitoring_runs_endpoint():
    response = client.get("/monitoring/runs")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
