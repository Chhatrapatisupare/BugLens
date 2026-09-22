"""
Agent 3: Technical Research Agent.
Constructs precision technical search queries and leverages Tavily Search API
to discover external documentation, known bugs, and official resolution guides.
"""
import logging
from typing import Tuple, Optional
from models.schemas import (
    BugReportInput,
    BugUnderstandingResult,
    ClassificationResult,
    ResearchResult,
    AgentTraceItem
)
from services.tavily_service import TavilyService
from services.groq_service import GroqService
from agents.prompts import SEARCH_QUERY_SYSTEM_PROMPT, SEARCH_QUERY_USER_TEMPLATE

logger = logging.getLogger(__name__)


class ResearchAgent:
    def __init__(self, tavily_service: TavilyService, groq_service: Optional[GroqService] = None):
        self.tavily_service = tavily_service
        self.groq_service = groq_service

    def run(
        self,
        bug_input: BugReportInput,
        understanding: BugUnderstandingResult,
        classification: ClassificationResult
    ) -> Tuple[ResearchResult, AgentTraceItem]:
        """
        Executes external technical research. Formulates search query and calls Tavily.
        Returns ResearchResult and safe AgentTraceItem.
        """
        query = self._build_query(bug_input, understanding, classification)

        if not self.tavily_service.is_configured():
            trace = AgentTraceItem(
                agent="Tavily Research Agent",
                status="warning",
                summary="External technical search skipped (Tavily API key not configured)."
            )
            return ResearchResult(queries=[query], sources=[], status="unavailable"), trace

        try:
            research_result = self.tavily_service.search_technical_context(query, max_results=4)

            if research_result.sources:
                trace = AgentTraceItem(
                    agent="Tavily Research Agent",
                    status="completed",
                    summary=f"Retrieved {len(research_result.sources)} technical sources for query: \"{query}\"."
                )
            else:
                trace = AgentTraceItem(
                    agent="Tavily Research Agent",
                    status="warning",
                    summary=f"Executed search query \"{query}\", but no external matches were retrieved."
                )

            return research_result, trace

        except Exception as e:
            logger.warning("ResearchAgent error: %s", str(e))
            trace = AgentTraceItem(
                agent="Tavily Research Agent",
                status="warning",
                summary="External research unavailable due to search service error."
            )
            return ResearchResult(queries=[query], sources=[], status="unavailable"), trace

    def _build_query(
        self,
        bug_input: BugReportInput,
        understanding: BugUnderstandingResult,
        classification: ClassificationResult
    ) -> str:
        """Constructs a high-precision query using Groq if available, or domain heuristics."""
        if self.groq_service and self.groq_service.is_configured():
            try:
                user_prompt = SEARCH_QUERY_USER_TEMPLATE.format(
                    category=classification.category,
                    component=classification.component,
                    probable_root_cause=classification.probable_root_cause,
                    error_log=bug_input.error_log[:200] if bug_input.error_log else "None",
                    symptoms=", ".join(understanding.symptoms[:3]),
                    environment=bug_input.environment
                )
                data = self.groq_service.generate_json_response(
                    system_prompt=SEARCH_QUERY_SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    temperature=0.1
                )
                queries = data.get("queries", [])
                if queries and isinstance(queries, list) and isinstance(queries[0], str) and queries[0].strip():
                    return queries[0].strip()
            except Exception as e:
                logger.debug("Groq query formulation fallback: %s", str(e))

        # Heuristic fallback query
        env_keywords = [w for w in bug_input.environment.replace(",", " ").split() if len(w) > 2][:3]
        env_str = " ".join(env_keywords)
        symptom_str = understanding.symptoms[0] if understanding.symptoms else bug_input.title
        # Filter special chars
        clean_symptom = " ".join(symptom_str.replace(":", " ").replace("'", " ").split()[:6])
        return f"{env_str} {classification.component} {clean_symptom}".strip()
