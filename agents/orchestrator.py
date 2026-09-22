"""
BugLens Agentic Pipeline Orchestrator.
Manages the sequential execution of all 6 agents, coordinates input validation,
tracks workflow traces, handles demo-mode branching, and persists results.
"""
import os
import logging
from typing import Dict, Any, List, Optional
from models.schemas import BugReportInput, AgentTraceItem, FinalBugReport
from services.groq_service import GroqService
from services.tavily_service import TavilyService
from services.database_service import DatabaseService
from services.demo_data import get_demo_analysis
from agents.bug_understanding import BugUnderstandingAgent
from agents.classifier import ClassificationAgent
from agents.researcher import ResearchAgent
from agents.evidence_analyzer import EvidenceAnalysisAgent
from agents.recommender import RecommendationAgent
from agents.report_generator import ReportGeneratorAgent

logger = logging.getLogger(__name__)


class AgenticOrchestrator:
    def __init__(
        self,
        groq_service: Optional[GroqService] = None,
        tavily_service: Optional[TavilyService] = None,
        database_service: Optional[DatabaseService] = None,
        demo_mode: Optional[bool] = None
    ):
        self.groq_service = groq_service or GroqService()
        self.tavily_service = tavily_service or TavilyService()
        self.database_service = database_service or DatabaseService()

        # Check demo mode setting from arg or env
        if demo_mode is not None:
            self.demo_mode = demo_mode
        else:
            env_val = os.getenv("DEMO_MODE", "false").lower()
            self.demo_mode = env_val in ("true", "1", "yes")

        # Initialize individual agents
        self.understanding_agent = BugUnderstandingAgent(self.groq_service)
        self.classifier_agent = ClassificationAgent(self.groq_service)
        self.research_agent = ResearchAgent(self.tavily_service, self.groq_service)
        self.evidence_agent = EvidenceAnalysisAgent(self.groq_service)
        self.recommendation_agent = RecommendationAgent(self.groq_service)
        self.report_agent = ReportGeneratorAgent()

    def analyze_bug(self, bug_input: BugReportInput) -> Dict[str, Any]:
        """
        Executes the full agent pipeline for an incoming bug report.
        Persists the result to SQLite and returns the full report dictionary.
        """
        # If demo mode is active or Groq is not configured, use realistic demo analysis
        if self.demo_mode or not self.groq_service.is_configured():
            logger.info("Running in DEMO_MODE or without Groq API key. Using calibrated demo analysis.")
            demo_data = get_demo_analysis(bug_input.to_dict())
            demo_data["is_demo"] = True

            # Save demo report to database
            report_id = self.database_service.save_report(bug_input.to_dict(), demo_data)
            demo_data["id"] = report_id
            saved_record = self.database_service.get_report_by_id(report_id)
            if saved_record:
                demo_data["created_at"] = saved_record.get("created_at")
            return demo_data

        # Live Multi-Agent Pipeline Execution
        traces: List[AgentTraceItem] = []

        # Stage 1: Bug Understanding
        understanding, trace_1 = self.understanding_agent.run(bug_input)
        traces.append(trace_1)

        # Stage 2: Bug Classification
        classification, trace_2 = self.classifier_agent.run(bug_input, understanding)
        traces.append(trace_2)

        # Stage 3: Technical Research (Tavily)
        research, trace_3 = self.research_agent.run(bug_input, understanding, classification)
        traces.append(trace_3)

        # Stage 4: Evidence Analysis
        evidence, trace_4 = self.evidence_agent.run(bug_input, understanding, classification, research)
        traces.append(trace_4)

        # Stage 5: Recommendations
        recommendations, trace_5 = self.recommendation_agent.run(
            bug_input, understanding, classification, evidence
        )
        traces.append(trace_5)

        # Stage 6: Final Report Synthesis
        final_report, _ = self.report_agent.run(
            bug_input=bug_input,
            understanding=understanding,
            classification=classification,
            research=research,
            evidence=evidence,
            recommendation=recommendations,
            traces=traces,
            is_demo=False
        )

        final_dict = final_report.to_dict()

        # Save to database
        report_id = self.database_service.save_report(bug_input.to_dict(), final_dict)
        final_dict["id"] = report_id
        saved_record = self.database_service.get_report_by_id(report_id)
        if saved_record:
            final_dict["created_at"] = saved_record.get("created_at")

        return final_dict
