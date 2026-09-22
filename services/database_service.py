"""
BugLens SQLite Database Service.
Handles thread-safe SQLite connection and parameterized operations for bug reports.
Ensures connections are cleanly closed on Windows.
"""
import os
import json
import sqlite3
from datetime import datetime
from contextlib import contextmanager
from typing import List, Dict, Any, Optional

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database", "bug_reports.db")


class DatabaseService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.getenv("DATABASE_PATH", DEFAULT_DB_PATH)
        # Ensure database directory exists
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        self.init_db()

    @contextmanager
    def connection(self):
        """Yields an SQLite connection and guarantees closure even upon errors."""
        conn = sqlite3.connect(self.db_path, timeout=20.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def init_db(self):
        """Initializes the database schema if it doesn't already exist."""
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bug_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    expected_behavior TEXT,
                    actual_behavior TEXT,
                    steps_to_reproduce TEXT,
                    environment TEXT,
                    error_log TEXT,
                    stack_trace TEXT,
                    component TEXT,
                    category TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    summary TEXT,
                    root_cause TEXT,
                    result_json TEXT NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON bug_reports(category);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_severity ON bug_reports(severity);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON bug_reports(created_at);")
            conn.commit()

    def save_report(self, bug_input: Dict[str, Any], final_report: Dict[str, Any]) -> int:
        """Saves a new analysis result into SQLite and returns the inserted ID."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO bug_reports (
                    created_at, title, description, expected_behavior, actual_behavior,
                    steps_to_reproduce, environment, error_log, stack_trace, component,
                    category, severity, priority, confidence, summary, root_cause, result_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                now_str,
                bug_input.get("title", ""),
                bug_input.get("description", ""),
                bug_input.get("expected_behavior", ""),
                bug_input.get("actual_behavior", ""),
                bug_input.get("steps_to_reproduce", ""),
                bug_input.get("environment", ""),
                bug_input.get("error_log", ""),
                bug_input.get("stack_trace", ""),
                final_report.get("component", ""),
                final_report.get("category", "Other"),
                final_report.get("severity", "Medium"),
                final_report.get("priority", "P2"),
                float(final_report.get("confidence", 0.85)),
                final_report.get("bug_summary", ""),
                final_report.get("probable_root_cause", ""),
                json.dumps(final_report)
            ))
            report_id = cursor.lastrowid
            conn.commit()
            return report_id

    def get_report_by_id(self, report_id: int) -> Optional[Dict[str, Any]]:
        """Fetches a specific bug report and parses its stored result_json."""
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM bug_reports WHERE id = ?", (report_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_dict(row)

    def list_reports(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Lists bug reports with parameterized search query and category/severity filters."""
        query = "SELECT * FROM bug_reports WHERE 1=1"
        params: List[Any] = []

        if search:
            query += " AND (title LIKE ? OR description LIKE ? OR summary LIKE ? OR component LIKE ?)"
            search_param = f"%{search.strip()}%"
            params.extend([search_param, search_param, search_param, search_param])

        if category and category.strip():
            query += " AND category = ?"
            params.append(category.strip())

        if severity and severity.strip():
            query += " AND severity = ?"
            params.append(severity.strip())

        query += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]

    def delete_report(self, report_id: int) -> bool:
        """Deletes a report by ID."""
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM bug_reports WHERE id = ?", (report_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Aggregates metrics for the dashboard."""
        with self.connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM bug_reports")
            total = cursor.fetchone()[0]

            if total == 0:
                return {
                    "total": 0,
                    "critical_count": 0,
                    "high_priority_count": 0,
                    "most_common_category": "None",
                    "category_breakdown": {},
                    "severity_breakdown": {},
                    "recent_reports": []
                }

            cursor.execute("SELECT COUNT(*) FROM bug_reports WHERE severity = 'Critical'")
            critical = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM bug_reports WHERE priority IN ('P0', 'P1')")
            high_priority = cursor.fetchone()[0]

            cursor.execute("""
                SELECT category, COUNT(*) as count 
                FROM bug_reports 
                GROUP BY category 
                ORDER BY count DESC 
                LIMIT 1
            """)
            most_common_row = cursor.fetchone()
            most_common = most_common_row[0] if most_common_row else "None"

            cursor.execute("""
                SELECT category, COUNT(*) as count 
                FROM bug_reports 
                GROUP BY category 
                ORDER BY count DESC
            """)
            category_breakdown = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute("""
                SELECT severity, COUNT(*) as count 
                FROM bug_reports 
                GROUP BY severity 
                ORDER BY count DESC
            """)
            severity_breakdown = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute("SELECT * FROM bug_reports ORDER BY id DESC LIMIT 5")
            recent_rows = cursor.fetchall()
            recent_reports = [self._row_to_dict(r) for r in recent_rows]

            return {
                "total": total,
                "critical_count": critical,
                "high_priority_count": high_priority,
                "most_common_category": most_common,
                "category_breakdown": category_breakdown,
                "severity_breakdown": severity_breakdown,
                "recent_reports": recent_reports
            }

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Converts an SQLite row to a Python dictionary, deserializing result_json."""
        d = dict(row)
        if "result_json" in d and d["result_json"]:
            try:
                d["result"] = json.loads(d["result_json"])
            except Exception:
                d["result"] = {}
        return d
