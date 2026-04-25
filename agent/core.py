"""InterviewAgent — orchestrates planner, responder, and feedback engine."""
import logging

import config
from agent.feedback import FeedbackEngine
from agent.llm_client import LLMClient
from agent.planner import Planner
from agent.responder import Responder
from agent.state import CandidateProfile, InterviewPhase, InterviewState, QAPair

logger = logging.getLogger(__name__)

_DIFFICULTY_MAP = {
    "easier": {"easy": "easy", "medium": "easy", "hard": "medium"},
    "same": {"easy": "easy", "medium": "medium", "hard": "hard"},
    "harder": {"easy": "medium", "medium": "hard", "hard": "hard"},
}

_ROLE_KEYWORDS = {
    "sde": ["sde", "software", "developer", "engineer", "coding", "programming", "dev"],
    "data_analyst": ["data analyst", "data", "analyst", "sql", "analytics"],
    "sales": ["sales", "selling", "salesperson"],
    "retail": ["retail", "store", "shop", "cashier"],
    "marketing": ["marketing", "marketer", "campaign", "brand"],
}


def _infer_role(text: str) -> str | None:
    text_lower = text.lower()
    for role, keywords in _ROLE_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return role
    return None


class InterviewAgent:
    def __init__(self):
        self._llm = LLMClient()
        self._planner = Planner(self._llm)
        self._responder = Responder(self._llm)
        self._feedback_engine = FeedbackEngine(self._llm)

    def start(self) -> tuple[str, InterviewState]:
        """Return opening greeting and a fresh state."""
        state = InterviewState()
        greeting = (
            "Welcome! I'm your mock interview partner. "
            "I can help you practice for roles in Software Development (SDE), "
            "Data Analytics, Sales, Retail, or Marketing.\n\n"
            "Which role would you like to practice for today?"
        )
        state.messages.append({"role": "assistant", "content": greeting})
        state.phase = InterviewPhase.ROLE_SELECTION
        return greeting, state

    def turn(self, state: InterviewState, user_message: str) -> tuple[str, InterviewState]:
        """
        Process one user turn:
        1. Append user message to state
        2. Prune conversation if too long
        3. Call planner → decision
        4. Update state based on decision
        5. If FEEDBACK phase: call feedback engine
        6. Else: call responder → bot message
        7. Append bot message, return
        """
        state.messages.append({"role": "user", "content": user_message})
        state = self._prune_if_needed(state)

        decision = self._planner.decide(state, user_message)
        state = self._apply_decision(state, decision, user_message)

        if state.phase == InterviewPhase.FEEDBACK:
            bot_message = "Thank you for completing the interview! Generating your feedback report now..."
            state.messages.append({"role": "assistant", "content": bot_message})
            try:
                state.feedback_result = self._feedback_engine.generate(state)
            except Exception as exc:
                logger.error("Feedback generation failed: %s", exc)
                state.feedback_result = {"error": str(exc)}
            return bot_message, state

        bot_message = self._responder.respond(state, decision, user_message)
        state.messages.append({"role": "assistant", "content": bot_message})

        # Record Q&A pair when a main question was just asked or answered
        self._maybe_record_qa(state, decision, user_message, bot_message)

        return bot_message, state

    def _prune_if_needed(self, state: InterviewState) -> InterviewState:
        """When messages exceed 20, summarize older ones and keep the last 12 verbatim."""
        if len(state.messages) <= 20:
            return state

        keep = 12
        older = state.messages[:-keep]
        state.messages = state.messages[-keep:]

        lines = []
        for m in older:
            speaker = "CANDIDATE" if m["role"] == "user" else "INTERVIEWER"
            lines.append(f"{speaker}: {m['content'][:300]}")
        older_text = "\n".join(lines)

        existing_prefix = f"Previous summary:\n{state.summary_note}\n\n" if state.summary_note else ""
        prompt = (
            f"{existing_prefix}Summarise the following earlier interview conversation in 3-5 sentences. "
            "Capture: role discussed, candidate's background/experience level, and topics already covered.\n\n"
            f"{older_text}"
        )

        try:
            state.summary_note = self._llm.complete(
                system="You are a concise summariser. Output 3-5 sentences only. No headers.",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
            )
            logger.info("Conversation pruned; summary stored (%d chars)", len(state.summary_note))
        except Exception as exc:
            logger.warning("Memory pruning summary failed: %s", exc)

        return state

    def _apply_decision(
        self, state: InterviewState, decision: dict, user_message: str
    ) -> InterviewState:
        action = decision["next_action"]
        persona = decision["persona_signal"]
        quality = decision["last_answer_quality"]

        # Update persona
        if persona != "normal":
            state.candidate_profile.detected_persona = persona

        # Update difficulty
        adj = decision.get("difficulty_adjustment", "same")
        state.current_difficulty = _DIFFICULTY_MAP[adj][state.current_difficulty]

        # Infer role from user message if not yet set
        if state.candidate_profile.role is None:
            inferred = _infer_role(user_message)
            if inferred:
                state.candidate_profile.role = inferred

        # Phase transitions
        if action == "generate_feedback":
            state.phase = InterviewPhase.FEEDBACK

        elif action == "wrap_up" or (
            decision.get("should_wrap_up") and state.phase == InterviewPhase.INTERVIEWING
        ):
            state.phase = InterviewPhase.WRAPPING_UP

        elif action in ("ask_main_question", "follow_up"):
            if state.phase not in (InterviewPhase.INTERVIEWING, InterviewPhase.WRAPPING_UP):
                state.phase = InterviewPhase.INTERVIEWING
            if action == "ask_main_question":
                state.question_count += 1

        elif action == "calibrate":
            state.phase = InterviewPhase.CALIBRATION

        elif action == "elicit_role":
            state.phase = InterviewPhase.ROLE_SELECTION

        # Update answer quality on last QA pair
        if quality != "n/a" and state.qa_history:
            state.qa_history[-1].quality = quality

        # Hard cap: force wrap-up once MAX_QUESTION_COUNT is reached
        if (
            state.question_count >= config.MAX_QUESTION_COUNT
            and state.phase == InterviewPhase.INTERVIEWING
        ):
            state.phase = InterviewPhase.WRAPPING_UP

        return state

    def _maybe_record_qa(
        self,
        state: InterviewState,
        decision: dict,
        user_message: str,
        bot_message: str,
    ) -> None:
        """Record a QAPair when the bot just asked a main interview question."""
        action = decision["next_action"]
        if action in ("ask_main_question", "follow_up") and state.phase == InterviewPhase.INTERVIEWING:
            # The bot's message is the question; user_message is the previous answer
            # We record the upcoming question so we can capture the answer next turn
            topic = decision.get("topic_to_probe") or state.candidate_profile.role or "general"
            # Only add if the bot message looks like a new question (avoid duplicates)
            if not state.qa_history or state.qa_history[-1].question != bot_message:
                state.qa_history.append(
                    QAPair(
                        question=bot_message,
                        answer=user_message,  # user_message is the answer to the PREVIOUS question
                        topic=topic,
                        quality=decision.get("last_answer_quality"),
                    )
                )
