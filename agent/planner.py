"""
Planner LLM call — returns structured decision JSON per turn.
This is the 'brain' that decides what the bot should do next.
"""
import logging

from typing import Literal

from pydantic import BaseModel, ValidationError

import config
from agent.llm_client import LLMClient
from agent.state import InterviewState

logger = logging.getLogger(__name__)

PLANNER_TOOL = {
    "name": "record_decision",
    "description": "Record the planner's structured decision for this turn.",
    "input_schema": {
        "type": "object",
        "properties": {
            "persona_signal": {
                "type": "string",
                "enum": ["confused", "efficient", "chatty", "edge_case", "normal"],
            },
            "last_answer_quality": {
                "type": "string",
                "enum": ["weak", "medium", "strong", "n/a"],
            },
            "next_action": {
                "type": "string",
                "enum": [
                    "greet",
                    "elicit_role",
                    "calibrate",
                    "ask_main_question",
                    "follow_up",
                    "redirect",
                    "handle_edge_case",
                    "wrap_up",
                    "generate_feedback",
                ],
            },
            "difficulty_adjustment": {
                "type": "string",
                "enum": ["easier", "same", "harder"],
            },
            "topic_to_probe": {
                "type": ["string", "null"],
                "description": "If next_action is 'follow_up', specific point to probe",
            },
            "should_wrap_up": {"type": "boolean"},
            "edge_case_type": {
                "type": ["string", "null"],
                "enum": ["out_of_scope_role", "hostile", "gibberish", "meta_question", None],
            },
            "internal_note": {
                "type": "string",
                "description": "One sentence reasoning",
            },
        },
        "required": [
            "persona_signal",
            "last_answer_quality",
            "next_action",
            "difficulty_adjustment",
            "should_wrap_up",
            "internal_note",
        ],
    },
}


class PlannerDecision(BaseModel):
    persona_signal: Literal["confused", "efficient", "chatty", "edge_case", "normal"]
    last_answer_quality: Literal["weak", "medium", "strong", "n/a"]
    next_action: Literal[
        "greet", "elicit_role", "calibrate", "ask_main_question",
        "follow_up", "redirect", "handle_edge_case", "wrap_up", "generate_feedback"
    ]
    difficulty_adjustment: Literal["easier", "same", "harder"]
    topic_to_probe: str | None = None
    should_wrap_up: bool
    edge_case_type: Literal["out_of_scope_role", "hostile", "gibberish", "meta_question"] | None = None
    internal_note: str


class Planner:
    def __init__(self, llm: LLMClient):
        self._llm = llm
        self._system = (config.PROMPTS_DIR / "planner_system.txt").read_text()

    def decide(self, state: InterviewState, user_message: str) -> dict:
        """Analyze current state + user message and return a structured decision."""
        context = self._build_context(state, user_message)
        messages = [{"role": "user", "content": context}]

        raw = self._llm.complete_structured(
            system=self._system,
            messages=messages,
            schema_tool=PLANNER_TOOL,
            max_tokens=config.PLANNER_MAX_TOKENS,
        )

        try:
            decision = PlannerDecision(**raw)
        except ValidationError as exc:
            logger.warning("Planner validation failed: %s — retrying with stricter prompt", exc)
            raw = self._llm.complete_structured(
                system=self._system + "\nCRITICAL: You must use the record_decision tool and populate ALL required fields.",
                messages=messages,
                schema_tool=PLANNER_TOOL,
                max_tokens=config.PLANNER_MAX_TOKENS,
            )
            decision = PlannerDecision(**raw)

        result = decision.model_dump()
        state.planner_logs.append(result)
        logger.debug("Planner decision: %s", result)
        return result

    def _build_context(self, state: InterviewState, user_message: str) -> str:
        role = state.candidate_profile.role or "not yet selected"
        phase = state.phase.value
        q_count = state.question_count

        # Last 2 answer qualities for wrap-up decision
        recent_qualities = [qa.quality for qa in state.qa_history[-2:] if qa.quality]
        qualities_str = ", ".join(recent_qualities) if recent_qualities else "none yet"

        # last 6 turns to keep tokens low
        recent = state.messages[-6:] if len(state.messages) > 6 else state.messages
        history_lines = []
        for m in recent:
            prefix = "CANDIDATE" if m["role"] == "user" else "INTERVIEWER"
            history_lines.append(f"{prefix}: {m['content']}")
        history = "\n".join(history_lines)

        wrap_hint = ""
        if q_count >= config.TARGET_QUESTION_COUNT:
            wrap_hint = (
                f"\nWRAP-UP SIGNAL: {q_count} questions asked (target is {config.TARGET_QUESTION_COUNT}). "
                f"If the last 2 answer qualities are both 'strong', set should_wrap_up=true and next_action='wrap_up'. "
                f"If {q_count} >= {config.MAX_QUESTION_COUNT}, always set should_wrap_up=true."
            )
        elif q_count >= config.MAX_QUESTION_COUNT:
            wrap_hint = f"\nWRAP-UP SIGNAL: Maximum question count ({config.MAX_QUESTION_COUNT}) reached — set should_wrap_up=true and next_action='wrap_up'."

        summary_section = ""
        if state.summary_note:
            summary_section = f"\nEARLIER CONVERSATION SUMMARY:\n{state.summary_note}\n"

        resume_section = ""
        if state.candidate_profile.resume_text:
            truncated = state.candidate_profile.resume_text[:2000]
            resume_section = (
                f"\nRESUME CONTEXT (use this to ask personalized questions about projects, "
                f"skills, and experience the candidate has actually listed):\n{truncated}\n"
            )

        return (
            f"CURRENT PHASE: {phase}\n"
            f"ROLE: {role}\n"
            f"QUESTIONS ASKED SO FAR: {q_count} (target: {config.TARGET_QUESTION_COUNT}, max: {config.MAX_QUESTION_COUNT})\n"
            f"CURRENT DIFFICULTY: {state.current_difficulty}\n"
            f"DETECTED PERSONA SO FAR: {state.candidate_profile.detected_persona or 'unknown'}\n"
            f"RECENT ANSWER QUALITIES: {qualities_str}"
            f"{wrap_hint}"
            f"{summary_section}"
            f"{resume_section}\n"
            f"RECENT CONVERSATION:\n{history}\n\n"
            f"LATEST USER MESSAGE: {user_message}"
        )
