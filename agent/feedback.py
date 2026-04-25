"""Feedback engine — generates structured end-of-interview report."""
import logging

from pydantic import BaseModel, ValidationError

import config
from agent.llm_client import LLMClient
from agent.state import InterviewState

logger = logging.getLogger(__name__)

FEEDBACK_TOOL = {
    "name": "record_feedback",
    "description": "Record the structured interview feedback report.",
    "input_schema": {
        "type": "object",
        "properties": {
            "overall": {"type": "string"},
            "scores": {
                "type": "object",
                "properties": {
                    "communication": {"type": "integer"},
                    "domain_depth": {"type": "integer"},
                    "problem_solving": {"type": "integer"},
                    "composure": {"type": "integer"},
                },
                "required": ["communication", "domain_depth", "problem_solving", "composure"],
            },
            "strengths": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "point": {"type": "string"},
                        "quote": {"type": "string"},
                    },
                    "required": ["point", "quote"],
                },
                "minItems": 3,
                "maxItems": 3,
            },
            "improvements": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "point": {"type": "string"},
                        "suggestion": {"type": "string"},
                    },
                    "required": ["point", "suggestion"],
                },
                "minItems": 3,
                "maxItems": 3,
            },
            "breakdown": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string"},
                        "answer_summary": {"type": "string"},
                        "rating": {"type": "string", "enum": ["weak", "medium", "strong"]},
                        "comment": {"type": "string"},
                    },
                    "required": ["question", "answer_summary", "rating", "comment"],
                },
            },
            "next_steps": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 3,
                "maxItems": 3,
            },
        },
        "required": ["overall", "scores", "strengths", "improvements", "breakdown", "next_steps"],
    },
}


class Scores(BaseModel):
    communication: int
    domain_depth: int
    problem_solving: int
    composure: int


class StrengthItem(BaseModel):
    point: str
    quote: str


class ImprovementItem(BaseModel):
    point: str
    suggestion: str


class BreakdownItem(BaseModel):
    question: str
    answer_summary: str
    rating: str
    comment: str


class FeedbackReport(BaseModel):
    overall: str
    scores: Scores
    strengths: list[StrengthItem]
    improvements: list[ImprovementItem]
    breakdown: list[BreakdownItem]
    next_steps: list[str]


class FeedbackEngine:
    def __init__(self, llm: LLMClient):
        self._llm = llm
        self._system = (config.PROMPTS_DIR / "feedback_system.txt").read_text()

    def generate(self, state: InterviewState) -> dict:
        """Generate structured feedback from the full Q&A history."""
        role = state.candidate_profile.role or "general"
        qa_text = self._format_qa(state)

        context = (
            f"ROLE: {config.ROLE_DISPLAY_NAMES.get(role, role)}\n\n"
            f"FULL Q&A HISTORY:\n{qa_text}"
        )
        messages = [{"role": "user", "content": context}]

        raw = self._llm.complete_structured(
            system=self._system,
            messages=messages,
            schema_tool=FEEDBACK_TOOL,
            max_tokens=config.FEEDBACK_MAX_TOKENS,
        )

        try:
            report = FeedbackReport(**raw)
        except ValidationError as exc:
            logger.warning("Feedback validation failed: %s", exc)
            raise

        return report.model_dump()

    def _format_qa(self, state: InterviewState) -> str:
        if state.qa_history:
            lines = []
            for i, qa in enumerate(state.qa_history, 1):
                lines.append(f"Q{i} [{qa.topic}]: {qa.question}")
                lines.append(f"A{i}: {qa.answer}")
                if qa.quality:
                    lines.append(f"Quality: {qa.quality}")
                lines.append("")
            return "\n".join(lines)

        # Fallback: reconstruct from raw messages if qa_history wasn't populated
        lines = []
        messages = state.messages
        for i, m in enumerate(messages):
            role = "INTERVIEWER" if m["role"] == "assistant" else "CANDIDATE"
            lines.append(f"{role}: {m['content']}")
        return "\n".join(lines)
