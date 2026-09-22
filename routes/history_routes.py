"""
History API Routes.
Manages querying, fetching, and deleting saved bug analysis reports.
"""
from flask import Blueprint, request, jsonify, current_app

history_bp = Blueprint("history", __name__, url_prefix="/api")


@history_bp.route("/history", methods=["GET"])
def get_history():
    """Lists saved bug reports with optional search, category, and severity filtering."""
    db_service = current_app.config.get("DB_SERVICE")
    if not db_service:
        return jsonify({"success": False, "error": "Database service unavailable."}), 500

    search = request.args.get("search", "")
    category = request.args.get("category", "")
    severity = request.args.get("severity", "")
    limit = int(request.args.get("limit", 100))
    offset = int(request.args.get("offset", 0))

    reports = db_service.list_reports(
        search=search,
        category=category,
        severity=severity,
        limit=limit,
        offset=offset
    )

    return jsonify({
        "success": True,
        "count": len(reports),
        "reports": reports
    }), 200


@history_bp.route("/history/<int:report_id>", methods=["GET"])
def get_report(report_id: int):
    """Retrieves a single historical bug report by ID."""
    db_service = current_app.config.get("DB_SERVICE")
    if not db_service:
        return jsonify({"success": False, "error": "Database service unavailable."}), 500

    report = db_service.get_report_by_id(report_id)
    if not report:
        return jsonify({"success": False, "error": f"Report #{report_id} not found."}), 404

    return jsonify({
        "success": True,
        "report": report
    }), 200


@history_bp.route("/history/<int:report_id>", methods=["DELETE"])
def delete_report(report_id: int):
    """Deletes a bug report by ID."""
    db_service = current_app.config.get("DB_SERVICE")
    if not db_service:
        return jsonify({"success": False, "error": "Database service unavailable."}), 500

    success = db_service.delete_report(report_id)
    if not success:
        return jsonify({"success": False, "error": f"Report #{report_id} could not be deleted or not found."}), 404

    return jsonify({
        "success": True,
        "message": f"Report #{report_id} deleted successfully."
    }), 200
