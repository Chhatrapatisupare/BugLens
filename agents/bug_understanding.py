"""
Agent 1: Bug Understanding Agent.
Parses and interprets raw bug reports, extracting factual symptoms, technical entities,
environment parameters, and identifying critical missing triage details.
"""
import json
import logging
from typing import Tuple
from models.schemas import BugReportInput, BugUnderstandingResult, AgentTraceItem
from services.groq_service import GroqService
from agents.prompts import BUG_UNDERSTANDING_SYSTEM_PROMPT, BUG_UNDERSTANDING_USER_TEMPLATE

logger = logging.getLogger(__name__)


class BugUnderstandingAgent:
    def __init__(self, groq_service: GroqService):
        self.groq_service = groq_service

    def run(self, bug_input: BugReportInput) -> Tuple[BugUnderstandingResult, AgentTraceItem]:
        """
        Executes bug understanding using Groq LLM reasoning.
        Returns a structured BugUnderstandingResult and a safe agent trace item.
        """
        user_prompt = BUG_UNDERSTANDING_USER_TEMPLATE.format(
            title=bug_input.title,
            description=bug_input.description,
            expected_behavior=bug_input.expected_behavior,
            actual_behavior=bug_input.actual_behavior,
            steps_to_reproduce=bug_input.steps_to_reproduce,
            environment=bug_input.environment,
            error_log=bug_input.error_log or "None provided",
            stack_trace=bug_input.stack_trace or "None provided",
            component=bug_input.component or "Not specified",
            existing_labels=bug_input.existing_labels or "None"
        )

        try:
            data = self.groq_service.generate_json_response(
                system_prompt=BUG_UNDERSTANDING_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.1
            )

            result = BugUnderstandingResult(
                summary=data.get("summary", bug_input.title),
                symptoms=data.get("symptoms", []),
                technical_entities=data.get("technical_entities", []),
                probable_component=data.get("probable_component", bug_input.component or "General System"),
                missing_information=data.get("missing_information", [])
            )

            # Fallback if empty symptoms
            if not result.symptoms:
                result.symptoms = [bug_input.actual_behavior[:100]]

            trace = AgentTraceItem(
                agent="Bug Understanding Agent",
                status="completed",
                summary=f"Extracted {len(result.symptoms)} symptoms and {len(result.technical_entities)} technical entities. Identified probable module: {result.probable_component}."
            )
            return result, trace

        except Exception as e:
            logger.error("BugUnderstandingAgent failed: %s", str(e))
            # Graceful local fallback if Groq call errors
            fallback_result = BugUnderstandingResult(
                summary=bug_input.description[:150],
                symptoms=[bug_input.actual_behavior],
                technical_entities=[e.strip() for e in bug_input.environment.split(",") if e.strip()],
                probable_component=bug_input.component or "General Module",
                missing_information=["Automated deep extraction unavailable due to service error."]
            )
            trace = AgentTraceItem(
                agent="Bug Understanding Agent",
                status="warning",
                summary="Fallback extraction applied due to reasoning service unavailability."
            )
            return fallback_result, trace
