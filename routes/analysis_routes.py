"""
Analysis and Health API Routes.
Provides endpoints for submitting bug reports, health diagnostics, and loading sample data.
"""
import os
import logging
from flask import Blueprint, request, jsonify, current_app
from models.schemas import validate_bug_input
from services.demo_data import get_sample_bug_reports

logger = logging.getLogger(__name__)

analysis_bp = Blueprint("analysis", __name__, url_prefix="/api")


@analysis_bp.route("/health", methods=["GET"])
def health_check():
    """Returns application status, API configuration states, and demo mode indicator."""
    orchestrator = current_app.config.get("ORCHESTRATOR")
    groq_service = orchestrator.groq_service if orchestrator else None
    tavily_service = orchestrator.tavily_service if orchestrator else None
    demo_mode = orchestrator.demo_mode if orchestrator else True

    return jsonify({
        "status": "ok",
        "groq_configured": groq_service.is_configured() if groq_service else False,
        "tavily_configured": tavily_service.is_configured() if tavily_service else False,
        "demo_mode": demo_mode,
        "groq_model": getattr(groq_service, "model", "llama-3.3-70b-versatile") if groq_service else "llama-3.3-70b-versatile"
    }), 200


@analysis_bp.route("/sample-bugs", methods=["GET"])
def get_sample_bugs():
    """Returns available sample bug reports for one-click form pre-filling."""
    samples = get_sample_bug_reports()
    return jsonify({
        "success": True,
        "samples": samples
    }), 200


@analysis_bp.route("/analyze", methods=["POST"])
def analyze_bug():
    """
    Submits a bug report to the Agentic AI Pipeline.
    Performs input validation and orchestrates the multi-agent classification.
    """
    if not request.is_json:
        return jsonify({
            "success": False,
            "error": "Request content must be application/json."
        }), 400

    data = request.get_json()
    bug_input, error_msg = validate_bug_input(data)
    if error_msg:
        return jsonify({
            "success": False,
            "error": error_msg
        }), 422

    orchestrator = current_app.config.get("ORCHESTRATOR")
    if not orchestrator:
        return jsonify({
            "success": False,
            "error": "Pipeline orchestrator is not initialized."
        }), 500

    try:
        result = orchestrator.analyze_bug(bug_input)
        return jsonify({
            "success": True,
            "data": result
        }), 200
    except Exception as e:
        logger.error("Analysis pipeline failure: %s", str(e), exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Analysis failed: {str(e)}"
        }), 500
