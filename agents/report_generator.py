"""
Agent 6: Final Report Generator Agent.
Synthesizes all individual agent outputs into a unified, strictly structured
triage document ready for storage and presentation on the developer dashboard.
"""
from typing import List, Dict, Any, Tuple
from models.schemas import (
    BugReportInput,
    BugUnderstandingResult,
    ClassificationResult,
    ResearchResult,
    EvidenceAnalysisResult,
    RecommendationResult,
    AgentTraceItem,
    FinalBugReport
)


class ReportGeneratorAgent:
    def run(
        self,
        bug_input: BugReportInput,
        understanding: BugUnderstandingResult,
        classification: ClassificationResult,
        research: ResearchResult,
        evidence: EvidenceAnalysisResult,
        recommendation: RecommendationResult,
        traces: List[AgentTraceItem],
        is_demo: bool = False
    ) -> Tuple[FinalBugReport, AgentTraceItem]:
        """
        Consolidates all intermediate agent outputs into a standardized FinalBugReport.
        """
        # Build generator's own trace item
        my_trace = AgentTraceItem(
            agent="Final Report Generator",
            status="completed",
            summary=f"Synthesized comprehensive triage report with {len(traces) + 1} agent workflow checkpoints."
        )

        all_traces = [t.to_dict() for t in traces] + [my_trace.to_dict()]

        # Clean, cohesive root cause reflecting evidence analysis
        root_cause = evidence.synthesized_root_cause or classification.probable_root_cause

        report = FinalBugReport(
            bug_summary=understanding.summary or bug_input.title,
            category=classification.category,
            severity=classification.severity,
            priority=classification.priority,
            confidence=classification.confidence,
            component=classification.component,
            probable_root_cause=root_cause,
            key_symptoms=understanding.symptoms,
            technical_entities=understanding.technical_entities,
            missing_information=understanding.missing_information,
            research=research.to_dict(),
            recommended_actions=recommendation.recommended_actions,
            testing_recommendations=recommendation.testing_recommendations,
            prevention=recommendation.prevention,
            agent_trace=all_traces,
            is_demo=is_demo
        )

        return report, my_trace
