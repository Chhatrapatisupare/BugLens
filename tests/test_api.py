"""
Integration tests for BugLens Flask API endpoints.
Tests health checks, validation errors, demo-mode analysis execution, and history CRUD.
"""
import os
import shutil
import tempfile
import pytest
from app import create_app


@pytest.fixture
def client():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_api.db")

    app = create_app(test_config={
        "TESTING": True,
        "DATABASE_PATH": db_path,
        "DEMO_MODE": True
    })

    with app.test_client() as test_client:
        yield test_client

    # Safe teardown on Windows
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass


def test_health_endpoint(client):
    """Verify GET /api/health returns valid system status."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ok"
    assert "groq_configured" in data
    assert "tavily_configured" in data
    assert "demo_mode" in data


def test_sample_bugs_endpoint(client):
    """Verify GET /api/sample-bugs returns pre-configured examples."""
    res = client.get("/api/sample-bugs")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert len(data["samples"]) >= 2


def test_dashboard_endpoint(client):
    """Verify GET /api/dashboard returns metrics structure."""
    res = client.get("/api/dashboard")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "metrics" in data
    assert data["metrics"]["total"] == 0


def test_analyze_empty_payload(client):
    """Verify POST /api/analyze handles empty payload gracefully with 422."""
    res = client.post("/api/analyze", json={})
    assert res.status_code == 422
    data = res.get_json()
    assert data["success"] is False
    assert "Bug Title is required" in data["error"]


def test_analyze_valid_demo_mode(client):
    """Verify POST /api/analyze executes demo analysis and persists report."""
    payload = {
        "title": "Flask API returns database locked error",
        "description": "Fails under high concurrent write workload",
        "expected_behavior": "Queue appointments successfully",
        "actual_behavior": "Returns 500 sqlite3.OperationalError",
        "steps_to_reproduce": "1. Run load test\n2. Inspect 500 error",
        "environment": "Windows 11, Flask 3.0, SQLite",
        "error_log": "sqlite3.OperationalError: database is locked",
        "stack_trace": "File app.py line 45",
        "component": "Database Layer",
        "existing_labels": "backend, database"
    }

    res = client.post("/api/analyze", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    report = data["data"]
    assert report["id"] > 0
    assert report["category"] == "Database Bug"
    assert report["severity"] == "High"
    assert report["is_demo"] is True

    # Check dashboard updated
    d_res = client.get("/api/dashboard")
    d_data = d_res.get_json()
    assert d_data["metrics"]["total"] == 1
    assert d_data["metrics"]["most_common_category"] == "Database Bug"

    # Check history contains the report
    h_res = client.get("/api/history")
    h_data = h_res.get_json()
    assert h_data["count"] == 1
    assert h_data["reports"][0]["id"] == report["id"]

    # Check single report retrieval
    r_res = client.get(f"/api/history/{report['id']}")
    assert r_res.status_code == 200
    r_data = r_res.get_json()
    assert r_data["report"]["title"] == payload["title"]

    # Check delete report
    del_res = client.delete(f"/api/history/{report['id']}")
    assert del_res.status_code == 200

    # Ensure deleted
    del_check = client.get(f"/api/history/{report['id']}")
    assert del_check.status_code == 404
