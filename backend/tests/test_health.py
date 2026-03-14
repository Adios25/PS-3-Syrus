"""
FLOW-JR-002: Tests for the enhanced /health endpoint.
Uses dependency_overrides to bypass real DB, and unittest.mock to patch the
health-check service — so no live DB or greenlet is required.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_db

# ── Shared mock DB session ────────────────────────────────────────────────────

def _mock_db():
    """Yield a lightweight AsyncMock that satisfies the get_db dependency."""
    mock_session = MagicMock()
    yield mock_session

app.dependency_overrides[get_db] = _mock_db

# ── Fixtures ──────────────────────────────────────────────────────────────────

HEALTHY_RESULT = {
    "status": "healthy",
    "dependencies": {
        "postgresql": {"status": "healthy", "latency_ms": 3.1},
        "redis": {"status": "healthy", "latency_ms": 0},
        "kafka": {"status": "healthy", "latency_ms": 0},
    },
}

UNHEALTHY_RESULT = {
    "status": "unhealthy",
    "dependencies": {
        "postgresql": {"status": "unhealthy", "latency_ms": 5001.0},
        "redis": {"status": "healthy", "latency_ms": 0},
        "kafka": {"status": "healthy", "latency_ms": 0},
    },
}

client = TestClient(app)

# ── Tests ─────────────────────────────────────────────────────────────────────

@patch("app.main.get_health_status", new_callable=AsyncMock, return_value=HEALTHY_RESULT)
def test_health_all_dependencies_healthy(mock_health):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "dependencies" in data

    deps = data["dependencies"]
    assert deps["postgresql"]["status"] == "healthy"
    assert deps["redis"]["status"] == "healthy"
    assert deps["kafka"]["status"] == "healthy"
    assert isinstance(deps["postgresql"]["latency_ms"], (int, float))


@patch("app.main.get_health_status", new_callable=AsyncMock, return_value=UNHEALTHY_RESULT)
def test_health_postgresql_down_returns_unhealthy(mock_health):
    response = client.get("/health")
    assert response.status_code == 200  # endpoint always returns 200
    data = response.json()

    assert data["status"] == "unhealthy"
    assert data["dependencies"]["postgresql"]["status"] == "unhealthy"


@patch("app.main.get_health_status", new_callable=AsyncMock, return_value=HEALTHY_RESULT)
def test_health_response_contains_timestamp(mock_health):
    response = client.get("/health")
    assert response.status_code == 200
    assert "timestamp" in response.json()

