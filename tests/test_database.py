"""
Unit tests for BugLens SQLite Database Service.
Tests table initialization, parameterized inserts, queries, filtering, and metric aggregations.
"""
import os
import shutil
import tempfile
import pytest
from services.database_service import DatabaseService


@pytest.fixture
def temp_db():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_bugs.db")
    service = DatabaseService(db_path=db_path)
    yield service
    # Clean up safely on Windows
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass


def test_db_initialization(temp_db):
    """Verify table creation and schema."""
    with temp_db.connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bug_reports';")
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == "bug_reports"


def test_save_and_get_report(temp_db):
    """Verify saving a bug report and retrieving it by ID."""
    bug_input = {
        "title": "Database connection refused",
        "description": "Postgres connection pool exhausted",
        "expected_behavior": "Connection established",
        "actual_behavior": "Timeout error",
        "steps_to_reproduce": "Spawn 100 threads",
        "environment": "Linux, Python 3.11",
        "error_log": "OperationalError: connection refused",
        "stack_trace": "Traceback...",
        "component": "Database Layer",
        "existing_labels": "backend, postgres"
    }

    final_report = {
        "bug_summary": "Postgres connection pool exhausted under high thread count",
        "category": "Database Bug",
        "severity": "High",
        "priority": "P1",
        "confidence": 0.95,
        "component": "Database Layer",
        "probable_root_cause": "Exceeding max connections in PostgreSQL pool",
        "key_symptoms": ["Connection refused", "Timeout error"],
        "technical_entities": ["PostgreSQL", "Python 3.11"],
        "missing_information": ["max_connections setting in postgresql.conf"],
        "research": {"queries": ["postgres connection pool exhausted"], "sources": []},
        "recommended_actions": ["Increase max_connections", "Implement pgbouncer"],
        "testing_recommendations": ["Run concurrent connection stress test"],
        "prevention": ["Monitor active connection counts"],
        "agent_trace": []
    }

    report_id = temp_db.save_report(bug_input, final_report)
    assert report_id > 0

    record = temp_db.get_report_by_id(report_id)
    assert record is not None
    assert record["title"] == "Database connection refused"
    assert record["category"] == "Database Bug"
    assert record["severity"] == "High"
    assert record["priority"] == "P1"
    assert record["confidence"] == 0.95
    assert "result" in record
    assert record["result"]["probable_root_cause"] == "Exceeding max connections in PostgreSQL pool"


def test_list_and_filter_reports(temp_db):
    """Verify parameterized search and category/severity filtering."""
    r1_input = {"title": "SQLite write lock error", "description": "DB locked", "environment": "Windows"}
    r1_final = {"category": "Database Bug", "severity": "Critical", "priority": "P0", "confidence": 0.9, "component": "SQLite"}
    temp_db.save_report(r1_input, r1_final)

    r2_input = {"title": "UI button alignment shifted", "description": "CSS issue", "environment": "Chrome"}
    r2_final = {"category": "UI/UX Bug", "severity": "Low", "priority": "P3", "confidence": 0.98, "component": "Navbar"}
    temp_db.save_report(r2_input, r2_final)

    # All
    all_reports = temp_db.list_reports()
    assert len(all_reports) == 2

    # Filter by category
    db_reports = temp_db.list_reports(category="Database Bug")
    assert len(db_reports) == 1
    assert db_reports[0]["title"] == "SQLite write lock error"

    # Filter by severity
    critical_reports = temp_db.list_reports(severity="Critical")
    assert len(critical_reports) == 1
    assert critical_reports[0]["severity"] == "Critical"

    # Search keyword
    search_reports = temp_db.list_reports(search="button")
    assert len(search_reports) == 1
    assert search_reports[0]["category"] == "UI/UX Bug"


def test_delete_report(temp_db):
    """Verify deleting a report by ID."""
    r_input = {"title": "Temp bug", "description": "To be deleted", "environment": "Dev"}
    r_final = {"category": "Other", "severity": "Low", "priority": "P3", "confidence": 0.5, "component": "Temp"}
    r_id = temp_db.save_report(r_input, r_final)

    assert temp_db.get_report_by_id(r_id) is not None
    deleted = temp_db.delete_report(r_id)
    assert deleted is True
    assert temp_db.get_report_by_id(r_id) is None


def test_dashboard_metrics(temp_db):
    """Verify metric calculations for total, critical, and high priority."""
    # Empty state
    m0 = temp_db.get_dashboard_metrics()
    assert m0["total"] == 0
    assert m0["critical_count"] == 0

    # Add records
    temp_db.save_report(
        {"title": "Bug 1", "description": "d"},
        {"category": "Security Bug", "severity": "Critical", "priority": "P0", "confidence": 0.9}
    )
    temp_db.save_report(
        {"title": "Bug 2", "description": "d"},
        {"category": "Security Bug", "severity": "High", "priority": "P1", "confidence": 0.88}
    )
    temp_db.save_report(
        {"title": "Bug 3", "description": "d"},
        {"category": "UI/UX Bug", "severity": "Low", "priority": "P3", "confidence": 0.95}
    )

    m = temp_db.get_dashboard_metrics()
    assert m["total"] == 3
    assert m["critical_count"] == 1
    assert m["high_priority_count"] == 2
    assert m["most_common_category"] == "Security Bug"
    assert m["category_breakdown"]["Security Bug"] == 2
