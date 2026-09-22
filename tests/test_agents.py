"""
Unit tests for BugLens Agentic Models and Pipeline Orchestration.
Tests schema validation, classification sanitization, and demo-mode orchestration.
"""
import os
import shutil
import tempfile
import pytest
from models.schemas import (
    validate_bug_input,
    sanitize_classification,
    BugReportInput,
    BugUnderstandingResult,
    ClassificationResult,
    ResearchResult,
    EvidenceAnalysisResult,
    RecommendationResult,
    AgentTraceItem
)
from agents.report_generator import ReportGeneratorAgent
from agents.orchestrator import AgenticOrchestrator
from services.database_service import DatabaseService


def test_validate_bug_input_valid():
    """Verify valid input converts cleanly into dataclass."""
    payload = {
        "title": "CORS preflight request blocked on auth endpoint",
        "description": "Cross-origin requests fail with 403 on refresh",
        "expected_behavior": "Return 200 with refreshed token",
        "actual_behavior": "Browser blocks preflight OPTIONS request",
        "steps_to_reproduce": "1. Login\n2. Wait for token expiry\n3. Call /refresh",
        "environment": "Ubuntu 22.04, React, FastAPI",
        "error_log": "403 Forbidden",
        "stack_trace": "FetchError...",
        "component": "Auth Gateway",
        "existing_labels": "cors, security"
    }
    input_obj, err = validate_bug_input(payload)
    assert err is None
    assert isinstance(input_obj, BugReportInput)
    assert input_obj.title == payload["title"]
    assert input_obj.component == "Auth Gateway"


def test_validate_bug_input_missing_fields():
    """Verify validation catches empty mandatory fields."""
    _, err = validate_bug_input({"title": "", "description": "some desc"})
    assert err is not None
    assert "Title is required" in err

    _, err2 = validate_bug_input({"title": "bug", "description": "desc"})
    assert err2 is not None
    assert "at least 5 characters" in err2


def test_sanitize_classification():
    """Verify normalization of arbitrary LLM strings into standard enums."""
    raw = {
        "category": "database bug",
        "severity": "CRITICAL",
        "priority": "p0",
        "confidence": 0.95,
        "component": "PostgreSQL layer",
        "probable_root_cause": "Deadlock during batch update"
    }
    cleaned = sanitize_classification(raw)
    assert cleaned.category == "Database Bug"
    assert cleaned.severity == "Critical"
    assert cleaned.priority == "P0"
    assert cleaned.confidence == 0.95

    raw_bad = {
        "category": "Unknown Random",
        "severity": "SuperFatal",
        "priority": "P9",
        "confidence": 1.5
    }
    cleaned_bad = sanitize_classification(raw_bad)
    assert cleaned_bad.category == "Other"
    assert cleaned_bad.severity == "Medium"
    assert cleaned_bad.priority == "P2"
    assert cleaned_bad.confidence == 1.0


def test_report_generator():
    """Verify final report generator consolidates all agent fields."""
    bug_input = BugReportInput(
        title="Test Bug",
        description="Test Desc",
        expected_behavior="Expected",
        actual_behavior="Actual",
        steps_to_reproduce="Steps",
        environment="Linux"
    )
    understanding = BugUnderstandingResult(
        summary="Test summary",
        symptoms=["s1", "s2"],
        technical_entities=["e1"],
        probable_component="Core"
    )
    classification = ClassificationResult(
        category="Logic Bug",
        severity="Medium",
        priority="P2",
        confidence=0.85,
        component="Core",
        probable_root_cause="Boundary check issue"
    )
    research = ResearchResult(queries=["test query"], sources=[], status="unavailable")
    evidence = EvidenceAnalysisResult(
        synthesized_root_cause="Boundary check issue",
        comparison_notes="Notes",
        supporting_evidence=["Evidence 1"]
    )
    recommendation = RecommendationResult(
        recommended_actions=["Fix condition"],
        testing_recommendations=["Add test"],
        prevention=["Linting rule"]
    )
    traces = [
        AgentTraceItem(agent="Bug Understanding Agent", status="completed", summary="Understood")
    ]

    gen = ReportGeneratorAgent()
    final_report, my_trace = gen.run(
        bug_input=bug_input,
        understanding=understanding,
        classification=classification,
        research=research,
        evidence=evidence,
        recommendation=recommendation,
        traces=traces,
        is_demo=False
    )

    assert final_report.category == "Logic Bug"
    assert len(final_report.agent_trace) == 2
    assert final_report.recommended_actions == ["Fix condition"]


def test_orchestrator_demo_mode():
    """Verify orchestrator runs seamlessly in demo mode and persists to SQLite."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_orch.db")
    db_service = DatabaseService(db_path=db_path)

    orchestrator = AgenticOrchestrator(
        database_service=db_service,
        demo_mode=True
    )

    bug_input = BugReportInput(
        title="Flask API returns database locked error",
        description="Under high concurrent requests",
        expected_behavior="Sequential write execution",
        actual_behavior="sqlite3.OperationalError: database is locked",
        steps_to_reproduce="Run concurrent threads",
        environment="Windows, Flask, SQLite"
    )

    result = orchestrator.analyze_bug(bug_input)
    assert result is not None
    assert "id" in result
    assert result["id"] > 0
    assert result["category"] == "Database Bug"
    assert result["is_demo"] is True
    assert len(result["agent_trace"]) >= 5

    # Verify persisted in database
    db_record = db_service.get_report_by_id(result["id"])
    assert db_record is not None
    assert db_record["title"] == bug_input.title

    # Clean up safely on Windows
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass
