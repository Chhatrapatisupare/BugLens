"""
BugLens Data Schemas and Validation.
Defines strictly typed models and utility sanitizers for the Agentic pipeline.
"""
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse

# Standard Enumerations
CATEGORIES = [
    "Functional Bug",
    "UI/UX Bug",
    "Performance Bug",
    "Security Bug",
    "Compatibility Bug",
    "Database Bug",
    "Network/API Bug",
    "Authentication/Authorization Bug",
    "Logic Bug",
    "Configuration Bug",
    "Crash/Exception",
    "Other"
]

SEVERITIES = ["Critical", "High", "Medium", "Low"]
PRIORITIES = ["P0", "P1", "P2", "P3"]


@dataclass
class BugReportInput:
    title: str
    description: str
    expected_behavior: str
    actual_behavior: str
    steps_to_reproduce: str
    environment: str
    error_log: str = ""
    stack_trace: str = ""
    component: str = ""
    existing_labels: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BugUnderstandingResult:
    summary: str
    symptoms: List[str] = field(default_factory=list)
    technical_entities: List[str] = field(default_factory=list)
    environment_details: Dict[str, str] = field(default_factory=dict)
    probable_component: str = "General System"
    missing_information: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ClassificationResult:
    category: str
    severity: str
    priority: str
    confidence: float
    component: str
    probable_root_cause: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ResearchSource:
    title: str
    url: str
    snippet: str
    domain: str = ""
    technical_relevance: str = ""

    def __post_init__(self):
        if not self.domain and self.url:
            try:
                parsed = urlparse(self.url)
                self.domain = parsed.netloc or "external"
            except Exception:
                self.domain = "external"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ResearchResult:
    queries: List[str] = field(default_factory=list)
    sources: List[ResearchSource] = field(default_factory=list)
    status: str = "completed"  # 'completed' or 'unavailable'

    def to_dict(self) -> Dict[str, Any]:
        return {
            "queries": self.queries,
            "sources": [s.to_dict() if isinstance(s, ResearchSource) else s for s in self.sources],
            "status": self.status
        }


@dataclass
class EvidenceAnalysisResult:
    synthesized_root_cause: str
    comparison_notes: str
    supporting_evidence: List[str] = field(default_factory=list)
    confidence_reasoning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RecommendationResult:
    recommended_actions: List[str] = field(default_factory=list)
    testing_recommendations: List[str] = field(default_factory=list)
    prevention: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentTraceItem:
    agent: str
    status: str  # 'completed', 'warning', 'skipped', 'failed'
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FinalBugReport:
    bug_summary: str
    category: str
    severity: str
    priority: str
    confidence: float
    component: str
    probable_root_cause: str
    key_symptoms: List[str]
    technical_entities: List[str]
    missing_information: List[str]
    research: Dict[str, Any]
    recommended_actions: List[str]
    testing_recommendations: List[str]
    prevention: List[str]
    agent_trace: List[Dict[str, Any]]
    id: Optional[int] = None
    created_at: Optional[str] = None
    is_demo: bool = False

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        return data


def validate_bug_input(data: Dict[str, Any]) -> tuple[Optional[BugReportInput], Optional[str]]:
    """Validates raw request data and converts to BugReportInput dataclass."""
    if not isinstance(data, dict):
        return None, "Invalid JSON payload received."

    title = str(data.get("title", "")).strip()
    description = str(data.get("description", "")).strip()
    expected = str(data.get("expected_behavior", "")).strip()
    actual = str(data.get("actual_behavior", "")).strip()
    steps = str(data.get("steps_to_reproduce", "")).strip()
    environment = str(data.get("environment", "")).strip()

    if not title:
        return None, "Bug Title is required."
    if len(title) < 5:
        return None, "Bug Title must be at least 5 characters long."
    if not description:
        return None, "Bug Description is required."
    if not expected:
        return None, "Expected Behavior is required."
    if not actual:
        return None, "Actual Behavior is required."
    if not steps:
        return None, "Steps to Reproduce are required."
    if not environment:
        return None, "Environment information is required (OS, language, runtime, etc.)."

    input_obj = BugReportInput(
        title=title,
        description=description,
        expected_behavior=expected,
        actual_behavior=actual,
        steps_to_reproduce=steps,
        environment=environment,
        error_log=str(data.get("error_log", "")).strip(),
        stack_trace=str(data.get("stack_trace", "")).strip(),
        component=str(data.get("component", "")).strip(),
        existing_labels=str(data.get("existing_labels", "")).strip()
    )
    return input_obj, None


def sanitize_classification(raw: Dict[str, Any]) -> ClassificationResult:
    """Sanitizes and normalizes LLM classification outputs."""
    raw_cat = str(raw.get("category", "")).strip()
    # Normalize category
    category = "Other"
    for cat in CATEGORIES:
        if raw_cat.lower() == cat.lower():
            category = cat
            break
        elif raw_cat.lower() in cat.lower():
            category = cat
            break

    # Normalize severity
    raw_sev = str(raw.get("severity", "")).strip().capitalize()
    severity = raw_sev if raw_sev in SEVERITIES else "Medium"

    # Normalize priority
    raw_pri = str(raw.get("priority", "")).strip().upper()
    priority = raw_pri if raw_pri in PRIORITIES else "P2"

    # Normalize confidence
    try:
        confidence = float(raw.get("confidence", 0.85))
        confidence = max(0.1, min(1.0, confidence))
    except (ValueError, TypeError):
        confidence = 0.85

    component = str(raw.get("component", "General Module")).strip() or "General Module"
    root_cause = str(raw.get("probable_root_cause", "Unspecified issue requiring further investigation.")).strip()

    return ClassificationResult(
        category=category,
        severity=severity,
        priority=priority,
        confidence=round(confidence, 2),
        component=component,
        probable_root_cause=root_cause
    )
