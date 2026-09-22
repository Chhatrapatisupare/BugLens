"""Routes package for BugLens."""
from .analysis_routes import analysis_bp
from .history_routes import history_bp
from .dashboard_routes import dashboard_bp

__all__ = [
    "analysis_bp",
    "history_bp",
    "dashboard_bp"
]
