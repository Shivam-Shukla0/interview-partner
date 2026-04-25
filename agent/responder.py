"""Responder LLM call — produces the user-facing interviewer message."""
import logging

import config
from agent.llm_client import LLMClient
from agent.state import InterviewState

logger = logging.getLogger(__name__)

_PERSONA_INSTRUCTIONS = {
    "confused": (
        "The candidate is exhibiting the CONFUSED persona — they seem unsure or hesitant. "
        "Be gentle, encouraging, and start with easier content. Offer clear guidance."
    ),
    "efficient": (
        "The candidate is exhibiting the EFFICIENT persona. "
        "Skip all preamble. Ask the question directly. Keep acknowledgments to one sentence max."
    ),
    "chatty": (
        "The candidate is exhibiting the CHATTY persona — they tend to go off-topic. "
        "Keep your response focused. If redirecting, acknowledge their point in one sentence only."
    ),
    "edge_case": (
        "The candidate has sent an out-of-scope or problematic message. "
        "Remain calm and professional. Decline gracefully if needed. Offer a supported alternative."
    ),
    "normal": "",
}

_EDGE_CASE_TYPE_INSTRUCTIONS = {
    "out_of_scope_role": (
        "The candidate asked to practice for a role you do not support. "
        "Politely explain you specialise in exactly these five roles: SDE, Data Analyst, Sales, "
        "Retail Associate, and Marketing. Suggest the closest supported role if there is an obvious "
        "match (e.g. medical sales → Sales). Do not apologise excessively — one brief explanation is enough."
    ),
    "hostile": (
        "The candidate sent hostile, abusive, or inappropriate content. "
        "Do NOT acknowledge or repeat it. Stay completely in character as a professional interviewer. "
        "Respond with a single calm sentence that redirects: "
        "'Let's keep our session focused on the interview.' Then continue normally."
    ),
    "gibberish": (
        "The candidate's message was unreadable or clearly random input. "
        "Do not mock or call it out harshly. Ask them politely to rephrase in one short sentence, "
        "e.g. 'Could you rephrase that? I want to make sure I understand you correctly.'"
    ),
    "meta_question": (
        "The candidate is asking whether you are an AI or about your underlying technology. "
        "Give a single honest sentence confirming you are an AI interview assistant, "
        "then immediately return to the interview without dwelling on it."
    ),
}

_ACTION_INSTRUCTIONS = {
    "greet": "Greet the candidate warmly and set expectations for the interview session.",
    "elicit_role": "Ask the candidate which role they want to practice for.",
    "calibrate": "Ask a soft calibration question to gauge the candidate's level and background.",
    "ask_main_question": "Ask the next main interview question appropriate to the role and current difficulty.",
    "follow_up": "Ask a targeted follow-up question based specifically on what the candidate just said.",
    "redirect": "Acknowledge the candidate's last point in one sentence, then redirect them back to the interview topic.",
    "handle_edge_case": "Handle the candidate's message gracefully — stay in character, decline if needed, offer alternatives.",
    "wrap_up": "Transition to the wrap-up phase. Ask if the candidate has any questions for you.",
    "generate_feedback": "Tell the candidate the interview is complete and you are preparing their feedback report.",
}


class Responder:
    def __init__(self, llm: LLMClient):
        self._llm = llm
        self._base_system = (config.PROMPTS_DIR / "responder_system.txt").read_text()

    def respond(
        self,
        state: InterviewState,
        planner_decision: dict,
        user_message: str,
    ) -> str:
        system = self._build_system(state, planner_decision)
        messages = self._build_messages(state, user_message)

        return self._llm.complete(
            system=system,
            messages=messages,
            max_tokens=config.RESPONDER_MAX_TOKENS,
        )

    def _build_system(self, state: InterviewState, decision: dict) -> str:
        role = state.candidate_profile.role
        role_prompt = ""
        if role:
            role_file = config.PROMPTS_DIR / "roles" / f"{role}.txt"
            if role_file.exists():
                role_prompt = role_file.read_text()

        persona = decision.get("persona_signal", "normal")
        edge_case_type = decision.get("edge_case_type")
        # Use specific edge-case instruction when available; fall back to generic persona note
        if edge_case_type and edge_case_type in _EDGE_CASE_TYPE_INSTRUCTIONS:
            persona_note = _EDGE_CASE_TYPE_INSTRUCTIONS[edge_case_type]
        else:
            persona_note = _PERSONA_INSTRUCTIONS.get(persona, "")

        action = decision.get("next_action", "ask_main_question")
        action_note = _ACTION_INSTRUCTIONS.get(action, "")

        topic_to_probe = decision.get("topic_to_probe")
        follow_up_note = ""
        if action == "follow_up" and topic_to_probe:
            follow_up_note = f'\nSpecifically probe this point from their answer: "{topic_to_probe}"'

        difficulty = state.current_difficulty
        diff_note = f"Current difficulty level: {difficulty}."

        summary_section = ""
        if state.summary_note:
            summary_section = f"=== EARLIER CONVERSATION SUMMARY ===\n{state.summary_note}"

        parts = [
            self._base_system,
            "",
            "=== ROLE-SPECIFIC GUIDANCE ===",
            role_prompt,
            "",
            summary_section,
            "=== PLANNER INSTRUCTIONS FOR THIS TURN ===",
            f"Action: {action_note}",
            follow_up_note,
            diff_note,
            "",
            "=== PERSONA ADJUSTMENT ===",
            persona_note,
        ]
        return "\n".join(p for p in parts if p is not None)

    def _build_messages(self, state: InterviewState, user_message: str) -> list[dict]:
        messages = list(state.messages)
        # Append current user message if not already there
        if not messages or messages[-1]["role"] != "user" or messages[-1]["content"] != user_message:
            messages = messages + [{"role": "user", "content": user_message}]
        return messages
