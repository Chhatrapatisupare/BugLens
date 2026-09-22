"""
Agent 5: Recommendation Agent.
Generates prioritized debugging steps, verification tests, and long-term architectural
prevention guidelines based on synthesized evidence and classification.
"""
import logging
from typing import Tuple
from models.schemas import (
    BugReportInput,
    BugUnderstandingResult,
    ClassificationResult,
    EvidenceAnalysisResult,
    RecommendationResult,
    AgentTraceItem
)
from services.groq_service import GroqService
from agents.prompts import RECOMMENDATION_SYSTEM_PROMPT, RECOMMENDATION_USER_TEMPLATE

logger = logging.getLogger(__name__)


class RecommendationAgent:
    def __init__(self, groq_service: GroqService):
        self.groq_service = groq_service

    def run(
        self,
        bug_input: BugReportInput,
        understanding: BugUnderstandingResult,
        classification: ClassificationResult,
        evidence: EvidenceAnalysisResult
    ) -> Tuple[RecommendationResult, AgentTraceItem]:
        """
        Generates actionable debugging and testing recommendations.
        """
        user_prompt = RECOMMENDATION_USER_TEMPLATE.format(
            category=classification.category,
            synthesized_root_cause=evidence.synthesized_root_cause,
            symptoms=", ".join(understanding.symptoms),
            environment=bug_input.environment,
            comparison_notes=evidence.comparison_notes
        )

        try:
            data = self.groq_service.generate_json_response(
                system_prompt=RECOMMENDATION_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.2
            )

            actions = data.get("recommended_actions", [])
            testing = data.get("testing_recommendations", [])
            prevention = data.get("prevention", [])

            if not actions:
                actions = [
                    f"Inspect configuration and logging around {classification.component}.",
                    "Reproduce issue in isolated staging environment with verbose telemetry.",
                    "Verify dependent service availability and connection lifecycle."
                ]

            result = RecommendationResult(
                recommended_actions=actions,
                testing_recommendations=testing,
                prevention=prevention
            )

            trace = AgentTraceItem(
                agent="Recommendation Agent",
                status="completed",
                summary=f"Formulated {len(result.recommended_actions)} actionable debugging steps, {len(result.testing_recommendations)} verification tests, and {len(result.prevention)} prevention policies."
            )
            return result, trace

        except Exception as e:
            logger.warning("RecommendationAgent error: %s", str(e))
            fallback = RecommendationResult(
                recommended_actions=[
                    f"1. Inspect active connection handles and error logs for {classification.component}.",
                    "2. Enable debug-level logging around the failing execution boundary.",
                    "3. Attempt controlled local reproduction following the reported steps.",
                    "4. Apply regression tests before deploying updates to production."
                ],
                testing_recommendations=[
                    "Execute unit test suite targeting the affected module.",
                    "Perform load or edge-case testing under matching runtime environment conditions."
                ],
                prevention=[
                    "Implement proactive alerts and telemetry thresholds for unexpected errors.",
                    "Document known environment constraints and dependencies."
                ]
            )
            trace = AgentTraceItem(
                agent="Recommendation Agent",
                status="warning",
                summary="Standard diagnostic recommendations applied due to reasoning fallback."
            )
            return fallback, trace
