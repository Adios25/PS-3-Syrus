import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.api.deps import get_db

# Override the DB dependency so no real connection (or greenlet) is needed
def _mock_db():
    yield MagicMock()

app.dependency_overrides[get_db] = _mock_db

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ps03-backend"}

@patch(
    "app.main.get_health_status",
    new_callable=AsyncMock,
    return_value={"status": "healthy", "dependencies": {}},
)
def test_health_check(mock_health):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data

