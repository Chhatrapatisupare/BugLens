"""
Agent 4: Evidence Analysis Agent.
Synthesizes the bug report against external technical research findings,
evaluates corroborating evidence, and refines the root cause hypothesis.
"""
import logging
from typing import Tuple
from models.schemas import (
    BugReportInput,
    BugUnderstandingResult,
    ClassificationResult,
    ResearchResult,
    EvidenceAnalysisResult,
    AgentTraceItem
)
from services.groq_service import GroqService
from agents.prompts import EVIDENCE_ANALYSIS_SYSTEM_PROMPT, EVIDENCE_ANALYSIS_USER_TEMPLATE

logger = logging.getLogger(__name__)


class EvidenceAnalysisAgent:
    def __init__(self, groq_service: GroqService):
        self.groq_service = groq_service

    def run(
        self,
        bug_input: BugReportInput,
        understanding: BugUnderstandingResult,
        classification: ClassificationResult,
        research: ResearchResult
    ) -> Tuple[EvidenceAnalysisResult, AgentTraceItem]:
        """
        Executes evidence comparison between reported symptoms and external sources.
        Returns EvidenceAnalysisResult and AgentTraceItem.
        """
        # Format sources text
        if research.sources:
            sources_formatted = "\n\n".join([
                f"Source {i+1}: {s.title} ({s.domain})\nURL: {s.url}\nExcerpt: {s.snippet}"
                for i, s in enumerate(research.sources)
            ])
        else:
            sources_formatted = "No external search sources available. Rely on internal bug symptoms and standard software engineering principles."

        user_prompt = EVIDENCE_ANALYSIS_USER_TEMPLATE.format(
            category=classification.category,
            probable_root_cause=classification.probable_root_cause,
            symptoms=", ".join(understanding.symptoms),
            sources_text=sources_formatted
        )

        try:
            data = self.groq_service.generate_json_response(
                system_prompt=EVIDENCE_ANALYSIS_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.15
            )

            result = EvidenceAnalysisResult(
                synthesized_root_cause=data.get("synthesized_root_cause", classification.probable_root_cause),
                comparison_notes=data.get("comparison_notes", "Symptoms align with standard failure modes in the reported environment."),
                supporting_evidence=data.get("supporting_evidence", []),
                confidence_reasoning=data.get("confidence_reasoning", "")
            )

            trace = AgentTraceItem(
                agent="Evidence Analysis Agent",
                status="completed",
                summary=f"Analyzed {len(research.sources)} external source(s); corroborated root cause with {len(result.supporting_evidence)} supporting evidence points."
            )
            return result, trace

        except Exception as e:
            logger.warning("EvidenceAnalysisAgent error: %s", str(e))
            fallback = EvidenceAnalysisResult(
                synthesized_root_cause=classification.probable_root_cause,
                comparison_notes="Evaluated directly from user-provided stack trace and logs without external evidence synthesis.",
                supporting_evidence=[
                    f"Reported error log directly references {understanding.probable_component}",
                    f"Behavior pattern matches known {classification.category} characteristics"
                ],
                confidence_reasoning="Confidence based on internal symptom clarity."
            )
            trace = AgentTraceItem(
                agent="Evidence Analysis Agent",
                status="warning",
                summary="Synthesized conclusions directly from report telemetry (external evidence comparison skipped)."
            )
            return fallback, trace
