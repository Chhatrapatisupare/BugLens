"""
Dashboard API Routes.
Provides aggregate metrics and statistics for the BugLens overview screen.
"""
from flask import Blueprint, jsonify, current_app

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api")


@dashboard_bp.route("/dashboard", methods=["GET"])
def get_dashboard_data():
    """Retrieves live metrics, category breakdown, and recent analyses."""
    db_service = current_app.config.get("DB_SERVICE")
    if not db_service:
        return jsonify({"success": False, "error": "Database service unavailable."}), 500

    metrics = db_service.get_dashboard_metrics()
    return jsonify({
        "success": True,
        "metrics": metrics
    }), 200
