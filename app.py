"""
BugLens - Automated Bug Report Classification using Agentic AI.
Main Flask application entry point.
"""
import os
import logging
from flask import Flask, render_template, jsonify
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from services.database_service import DatabaseService
from services.groq_service import GroqService
from services.tavily_service import TavilyService
from agents.orchestrator import AgenticOrchestrator
from routes.analysis_routes import analysis_bp
from routes.history_routes import history_bp
from routes.dashboard_routes import dashboard_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("BugLens")


def create_app(test_config=None) -> Flask:
    """Factory function to create and configure the Flask app."""
    app = Flask(__name__, static_folder="static", template_folder="templates")

    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "buglens-development-secret-key"),
        DATABASE_PATH=os.getenv("DATABASE_PATH")
    )

    if test_config:
        app.config.update(test_config)

    # Initialize Services
    db_service = DatabaseService(db_path=app.config.get("DATABASE_PATH"))
    groq_service = GroqService(
        api_key=os.getenv("GROQ_API_KEY", ""),
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    )
    tavily_service = TavilyService(
        api_key=os.getenv("TAVILY_API_KEY", "")
    )

    demo_mode_env = os.getenv("DEMO_MODE", "true").lower() in ("true", "1", "yes")
    orchestrator = AgenticOrchestrator(
        groq_service=groq_service,
        tavily_service=tavily_service,
        database_service=db_service,
        demo_mode=demo_mode_env
    )

    # Store shared instances in app config
    app.config["DB_SERVICE"] = db_service
    app.config["GROQ_SERVICE"] = groq_service
    app.config["TAVILY_SERVICE"] = tavily_service
    app.config["ORCHESTRATOR"] = orchestrator

    # Register API Blueprints
    app.register_blueprint(analysis_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(dashboard_bp)

    # HTML Page Routes
    @app.route("/")
    def index_page():
        return render_template("index.html")

    @app.route("/analyze")
    def analyze_page():
        return render_template("analyze.html")

    @app.route("/result/<int:report_id>")
    def result_page(report_id: int):
        report = db_service.get_report_by_id(report_id)
        return render_template("result.html", report=report, report_id=report_id)

    @app.route("/history")
    def history_page():
        return render_template("history.html")

    @app.route("/about")
    def about_page():
        return render_template("about.html")

    # Global Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        if app.template_folder and os.path.exists(os.path.join(app.template_folder, "base.html")):
            return render_template("base.html", error_message="Page Not Found (404)"), 404
        return jsonify({"success": False, "error": "Endpoint not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error("Internal Server Error: %s", str(error))
        return jsonify({"success": False, "error": "Internal server error occurred."}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", 5000))
    logger.info("Starting BugLens on http://127.0.0.1:%d", port)
    app.run(host="127.0.0.1", port=port, debug=True)
