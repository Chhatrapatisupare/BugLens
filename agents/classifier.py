"""
Agent 2: Classification Agent.
Determines bug category, severity, priority, confidence score,
affected component, and forms the initial root-cause hypothesis.
"""
import json
import logging
from typing import Tuple
from models.schemas import (
    BugReportInput,
    BugUnderstandingResult,
    ClassificationResult,
    AgentTraceItem,
    sanitize_classification
)
from services.groq_service import GroqService
from agents.prompts import CLASSIFICATION_SYSTEM_PROMPT, CLASSIFICATION_USER_TEMPLATE

logger = logging.getLogger(__name__)


class ClassificationAgent:
    def __init__(self, groq_service: GroqService):
        self.groq_service = groq_service

    def run(
        self,
        bug_input: BugReportInput,
        understanding: BugUnderstandingResult
    ) -> Tuple[ClassificationResult, AgentTraceItem]:
        """
        Executes bug classification using Groq LLM reasoning.
        Returns a sanitized ClassificationResult and safe AgentTraceItem.
        """
        user_prompt = CLASSIFICATION_USER_TEMPLATE.format(
            understanding_json=json.dumps(understanding.to_dict(), indent=2),
            title=bug_input.title,
            actual_behavior=bug_input.actual_behavior,
            error_log=bug_input.error_log or "None",
            environment=bug_input.environment
        )

        try:
            raw_data = self.groq_service.generate_json_response(
                system_prompt=CLASSIFICATION_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.15
            )

            result = sanitize_classification(raw_data)

            trace = AgentTraceItem(
                agent="Classification Agent",
                status="completed",
                summary=f"Classified as '{result.category}' with {result.severity} severity, {result.priority} priority ({int(result.confidence * 100)}% confidence)."
            )
            return result, trace

        except Exception as e:
            logger.error("ClassificationAgent failed: %s", str(e))
            # Safe heuristic fallback
            fallback_result = ClassificationResult(
                category="Crash/Exception" if "trace" in (bug_input.stack_trace + bug_input.error_log).lower() else "Functional Bug",
                severity="High" if "error" in bug_input.actual_behavior.lower() else "Medium",
                priority="P1" if "error" in bug_input.actual_behavior.lower() else "P2",
                confidence=0.75,
                component=understanding.probable_component or "Application Logic",
                probable_root_cause=f"Potential defect in {understanding.probable_component} causing unexpected behavior."
            )
            trace = AgentTraceItem(
                agent="Classification Agent",
                status="warning",
                summary=f"Rule-based classification applied: '{fallback_result.category}', Severity: {fallback_result.severity}."
            )
            return fallback_result, trace
