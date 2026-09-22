"""
BugLens Sample Reports and Demo Mode Dataset.
Provides curated, realistic bug reports and full pre-computed agentic analyses
for zero-configuration demonstration and local offline testing.
"""
from typing import Dict, Any, List

SAMPLE_BUG_REPORTS = [
    {
        "id": "sample-sqlite-locked",
        "title": "Flask API returns database locked error under concurrent requests",
        "description": "The appointment booking API endpoint intermittently fails with a 500 status when multiple concurrent users attempt to reserve slots at the same time.",
        "expected_behavior": "All concurrent valid appointment requests should be processed sequentially or queued gracefully without database lock exceptions.",
        "actual_behavior": "Flask application raises 'sqlite3.OperationalError: database is locked' during peak booking times, aborting user requests.",
        "steps_to_reproduce": "1. Start the Flask application with SQLite backend.\n2. Execute a load test with 25 concurrent POST requests to /api/appointments.\n3. Observe intermittent 500 responses with SQLite lock errors in server logs.",
        "environment": "Windows 11, Python 3.11, Flask 3.0, SQLite 3.42, Gunicorn 21.2 (4 workers)",
        "error_log": "[2026-09-22 14:22:01] ERROR in app: Exception on /api/appointments [POST]\nTraceback (most recent call last):\n  File \"flask/app.py\", line 1477, in full_dispatch_request\n  File \"routes/appointments.py\", line 45, in book\n    cursor.execute('INSERT INTO appointments (user_id, slot_id) VALUES (?, ?)', (u_id, s_id))\nsqlite3.OperationalError: database is locked",
        "stack_trace": "sqlite3.OperationalError: database is locked\n  at cursor.execute() in appointments.py:45\n  at db_commit() in db.py:82",
        "component": "Database / Appointment Service",
        "existing_labels": "backend, database, concurrency, high-priority"
    },
    {
        "id": "sample-cors-auth",
        "title": "React frontend receives CORS 403 Forbidden on Token Refresh",
        "description": "After JWT access token expiration, the single-page application attempts to call /api/v1/auth/refresh with credentials, but the browser blocks the response due to missing Access-Control-Allow-Credentials header.",
        "expected_behavior": "The refresh endpoint should return 200 OK with refreshed tokens and allow cross-origin requests from the trusted frontend origin.",
        "actual_behavior": "Browser console displays: 'Access to fetch at http://api.internal/auth/refresh from origin http://localhost:3000 has been blocked by CORS policy: Response to preflight request doesn't pass access control check: It does not have HTTP ok status.'",
        "steps_to_reproduce": "1. Log into the web application.\n2. Wait 15 minutes for access token expiry.\n3. Trigger any authenticated background poll.\n4. Observe silent logout and CORS error in developer console.",
        "environment": "Ubuntu 22.04, Node.js 20.x, React 18, FastAPI backend with CORSMiddleware, Google Chrome 128",
        "error_log": "OPTIONS /api/v1/auth/refresh HTTP/1.1 403 Forbidden\nOrigin: http://localhost:3000\nAccess-Control-Request-Method: POST",
        "stack_trace": "FetchError: Failed to fetch\n  at refreshToken (authService.ts:64)\n  at interceptor (axiosInstance.ts:32)",
        "component": "Auth Gateway / API Middleware",
        "existing_labels": "security, api, cors, authentication"
    },
    {
        "id": "sample-null-pointer",
        "title": "Java NullPointerException in OrderProcessor ArrayList batch iteration",
        "description": "Processing a batch of customer orders crashes when an order contains a null discount item in the line items list during price recalculation.",
        "expected_behavior": "Order processor should handle absent discount items gracefully without throwing an unchecked NullPointerException.",
        "actual_behavior": "Batch processor stops abruptly, leaving 45 orders in 'PENDING_PAYMENT' state and failing the scheduled cron job.",
        "steps_to_reproduce": "1. Submit a cart checkout with a promo code that has no discount percentage attached.\n2. Trigger the batch processing job.\n3. Observe NullPointerException at OrderProcessor.java:114.",
        "environment": "Amazon Linux 2, OpenJDK 17.0.8, Spring Boot 3.1.5, PostgreSQL 15",
        "error_log": "java.lang.NullPointerException: Cannot invoke \"Discount.getAmount()\" because the return value of \"LineItem.getDiscount()\" is null\n\tat com.ecommerce.order.OrderProcessor.calculateTotals(OrderProcessor.java:114)\n\tat com.ecommerce.order.OrderProcessor.processBatch(OrderProcessor.java:82)",
        "stack_trace": "java.lang.NullPointerException: Cannot invoke \"Discount.getAmount()\"\n  at com.ecommerce.order.OrderProcessor.calculateTotals(OrderProcessor.java:114)\n  at java.base/java.util.ArrayList.forEach(ArrayList.java:1511)",
        "component": "Billing & Order Pipeline",
        "existing_labels": "java, crash, billing, bug"
    }
]


def get_sample_bug_reports() -> List[Dict[str, Any]]:
    return SAMPLE_BUG_REPORTS


def get_demo_analysis(bug_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns a comprehensive, realistic agentic analysis specifically tailored
    to the input bug for demo mode.
    """
    title = bug_input.get("title", "").lower()

    if "cors" in title or "auth" in title:
        return {
            "bug_summary": "Cross-Origin preflight request failure on authentication token refresh endpoint due to restrictive CORS middleware configuration.",
            "category": "Authentication/Authorization Bug",
            "severity": "High",
            "priority": "P1",
            "confidence": 0.94,
            "component": "Auth Gateway / CORS Middleware",
            "probable_root_cause": "Preflight OPTIONS request to /auth/refresh fails because CORS middleware does not permit credentialed origins or returns 403 before handling headers.",
            "key_symptoms": [
                "CORS preflight 403 Forbidden",
                "Access-Control-Allow-Credentials missing",
                "Token refresh failure",
                "Unexpected user logout",
                "Failed OPTIONS HTTP method"
            ],
            "technical_entities": [
                "FastAPI CORSMiddleware",
                "JWT refresh token",
                "React 18",
                "HTTP OPTIONS preflight",
                "Chrome browser security policy"
            ],
            "missing_information": [
                "Backend CORS configuration snippet (allow_origins list and allow_credentials flag)",
                "Whether cookies (HttpOnly) or Authorization headers are being used"
            ],
            "research": {
                "queries": [
                    "FastAPI CORSMiddleware 403 preflight OPTIONS credentials",
                    "React Axios token refresh CORS Access-Control-Allow-Credentials"
                ],
                "sources": [
                    {
                        "title": "FastAPI CORS (Cross-Origin Resource Sharing) Guide",
                        "url": "https://fastapi.tiangolo.com/tutorial/cors/",
                        "snippet": "When using CORSMiddleware with credentials (cookies or Authorization headers), allow_origins cannot be set to ['*']. You must specify exact origins and set allow_credentials=True.",
                        "domain": "fastapi.tiangolo.com",
                        "technical_relevance": "Official documentation on configuring credentials and allowed origins."
                    },
                    {
                        "title": "MDN Web Docs: Reason: Credential is not supported if the CORS header is '*'",
                        "url": "https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS/Errors/CORSNotSupportingCredentials",
                        "snippet": "When responding to a credentialed request, the server must specify an origin in the value of the Access-Control-Allow-Origin header instead of the wildcard character.",
                        "domain": "developer.mozilla.org",
                        "technical_relevance": "Explains browser preflight failure when credentials interact with wildcard origins."
                    },
                    {
                        "title": "Axios Interceptor Infinite Loop on 401 Refresh",
                        "url": "https://github.com/axios/axios/issues/3727",
                        "snippet": "Ensure your token refresh axios instance does not trigger the 401 interceptor recursively and includes withCredentials: true.",
                        "domain": "github.com",
                        "technical_relevance": "Prevents cascading refresh request loops during token renewal."
                    }
                ],
                "status": "completed"
            },
            "recommended_actions": [
                "Update backend CORSMiddleware to explicitly list 'http://localhost:3000' rather than wildcard '*', and enable allow_credentials=True.",
                "Ensure authentication dependencies on the backend do not enforce token checks on HTTP OPTIONS requests.",
                "Verify that the frontend request includes credentials: 'include' or withCredentials: true.",
                "Check server access logs for the preflight OPTIONS request status code (must return 200 or 204 OK).",
                "Add an automated integration test verifying preflight headers for all protected authentication endpoints."
            ],
            "testing_recommendations": [
                "Perform curl -X OPTIONS test with Origin and Access-Control-Request-Method headers.",
                "Simulate token expiration in browser with active session and inspect Network tab.",
                "Verify cross-origin behavior across Chromium, Firefox, and WebKit engines."
            ],
            "prevention": [
                "Centralize CORS policy configuration in an environment-driven security module.",
                "Introduce CI/CD linting rule to reject wildcard origins paired with credentialed routes.",
                "Monitor 403 response rates on preflight requests in production APM."
            ],
            "agent_trace": [
                {
                    "agent": "Bug Understanding Agent",
                    "status": "completed",
                    "summary": "Extracted 5 key symptoms relating to CORS preflight failure, token renewal, and HTTP 403 status."
                },
                {
                    "agent": "Classification Agent",
                    "status": "completed",
                    "summary": "Classified as 'Authentication/Authorization Bug' with High severity (P1 priority, 94% confidence)."
                },
                {
                    "agent": "Tavily Research Agent",
                    "status": "completed",
                    "summary": "Retrieved 3 authoritative sources from FastAPI official docs, MDN Web Docs, and GitHub issues."
                },
                {
                    "agent": "Evidence Analysis Agent",
                    "status": "completed",
                    "summary": "Corroborated browser preflight failure with missing credentials flag and wildcard origin collision."
                },
                {
                    "agent": "Recommendation Agent",
                    "status": "completed",
                    "summary": "Formulated 5 sequential debugging actions, 3 targeted verification tests, and 3 architectural safeguards."
                },
                {
                    "agent": "Final Report Generator",
                    "status": "completed",
                    "summary": "Synthesized full triage report and verified schema integrity [Demo Mode Active]."
                }
            ],
            "is_demo": True
        }

    # Default / SQLite concurrent write locked issue
    return {
        "bug_summary": "Concurrent write transactions in SQLite cause database locking under multi-worker Flask deployment.",
        "category": "Database Bug",
        "severity": "High",
        "priority": "P1",
        "confidence": 0.92,
        "component": "SQLite Database / Transaction Layer",
        "probable_root_cause": "Concurrent write operations across multiple Gunicorn worker processes exceed SQLite's single-writer concurrency limit, triggering busy timeout exceptions.",
        "key_symptoms": [
            "sqlite3.OperationalError: database is locked",
            "Intermittent 500 server errors under load",
            "Fails during concurrent POST requests",
            "Multi-worker deployment concurrency contention",
            "Transaction timeout at cursor.execute"
        ],
        "technical_entities": [
            "Flask 3.0",
            "SQLite 3.42",
            "Gunicorn 21.2",
            "Python sqlite3 module",
            "WAL (Write-Ahead Logging) mode"
        ],
        "missing_information": [
            "Current SQLite journal_mode setting (e.g., DELETE vs WAL)",
            "SQLite busy_timeout configuration value (default is often 0 or 5 seconds)",
            "Connection lifecycle pattern (per-request vs long-lived global connection)"
        ],
        "research": {
            "queries": [
                "Python Flask SQLite database is locked gunicorn concurrent workers",
                "SQLite write ahead logging WAL mode busy timeout python sqlite3"
            ],
            "sources": [
                {
                    "title": "SQLite Documentation: WAL (Write-Ahead Logging) Mode",
                    "url": "https://www.sqlite.org/wal.html",
                    "snippet": "WAL mode allows concurrent readers to continue operating while a write transaction is occurring. Furthermore, writing is significantly faster in WAL mode.",
                    "domain": "sqlite.org",
                    "technical_relevance": "Primary architectural fix enabling simultaneous reads alongside write transactions."
                },
                {
                    "title": "Python sqlite3 module documentation: OperationalError database is locked",
                    "url": "https://docs.python.org/3/library/sqlite3.html#sqlite3.connect",
                    "snippet": "When multiple threads or processes access the database, use sqlite3.connect(database, timeout=20.0) to give locked transactions time to release locks before throwing an error.",
                    "domain": "docs.python.org",
                    "technical_relevance": "Explains the busy timeout parameter to eliminate premature lock aborts."
                },
                {
                    "title": "Flask SQLAlchemy & SQLite Concurrency Best Practices",
                    "url": "https://flask.palletsprojects.com/en/3.0.x/patterns/sqlite3/",
                    "snippet": "Ensure SQLite database connections are opened per request with g._database and closed during teardown_appcontext.",
                    "domain": "flask.palletsprojects.com",
                    "technical_relevance": "Demonstrates proper connection lifecycle management per Flask request."
                }
            ],
            "status": "completed"
        },
        "recommended_actions": [
            "Enable Write-Ahead Logging (WAL) mode on the SQLite database: execute 'PRAGMA journal_mode=WAL;'.",
            "Increase the SQLite connection timeout parameter: set sqlite3.connect(db_path, timeout=30.0).",
            "Ensure connections are scoped per request using Flask's g object and closed in teardown_appcontext.",
            "If write concurrency exceeds SQLite capabilities, evaluate migration to PostgreSQL or MySQL for production workloads.",
            "Add transaction retry logic with exponential backoff around critical appointment reservation queries."
        ],
        "testing_recommendations": [
            "Execute a concurrent stress test using locust or Apache Bench (e.g. 50 parallel POST requests) to verify zero lock errors.",
            "Verify PRAGMA journal_mode returns 'wal' on application startup.",
            "Simulate connection contention with artificial sleep inside a write transaction to test busy_timeout behavior."
        ],
        "prevention": [
            "Standardize database initialization script to apply WAL mode and busy timeout automatically.",
            "Add health check probes that monitor SQLite lock wait times.",
            "Document database concurrency limits in the developer onboarding guide."
        ],
        "agent_trace": [
            {
                "agent": "Bug Understanding Agent",
                "status": "completed",
                "summary": "Extracted symptoms of database locking, multi-worker contention, and failure during concurrent writes."
            },
            {
                "agent": "Classification Agent",
                "status": "completed",
                "summary": "Classified as 'Database Bug' with High severity (P1 priority, 92% confidence)."
            },
            {
                "agent": "Tavily Research Agent",
                "status": "completed",
                "summary": "Retrieved 3 authoritative technical sources from SQLite.org, Python docs, and Pallets Projects."
            },
            {
                "agent": "Evidence Analysis Agent",
                "status": "completed",
                "summary": "Evaluated concurrent write locking patterns against SQLite default rollback journal behavior."
            },
            {
                "agent": "Recommendation Agent",
                "status": "completed",
                "summary": "Generated 5 step-by-step resolution actions (WAL mode, busy_timeout), testing, and prevention guidelines."
            },
            {
                "agent": "Final Report Generator",
                "status": "completed",
                "summary": "Assembled unified structured triage report with validated schema [Demo Mode Active]."
            }
        ],
        "is_demo": True
    }
