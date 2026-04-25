"""Validate planner JSON schema contract."""
import pytest
from pydantic import ValidationError

from agent.planner import PlannerDecision


VALID_DECISION = {
    "persona_signal": "normal",
    "last_answer_quality": "medium",
    "next_action": "ask_main_question",
    "difficulty_adjustment": "same",
    "topic_to_probe": None,
    "should_wrap_up": False,
    "edge_case_type": None,
    "internal_note": "Candidate answered adequately; moving to next question.",
}


def test_valid_decision():
    decision = PlannerDecision(**VALID_DECISION)
    assert decision.persona_signal == "normal"
    assert decision.next_action == "ask_main_question"


def test_missing_required_field():
    bad = {k: v for k, v in VALID_DECISION.items() if k != "internal_note"}
    with pytest.raises(ValidationError):
        PlannerDecision(**bad)


def test_invalid_enum_value():
    bad = {**VALID_DECISION, "persona_signal": "angry"}
    with pytest.raises(ValidationError):
        PlannerDecision(**bad)


def test_all_next_actions():
    actions = [
        "greet", "elicit_role", "calibrate", "ask_main_question",
        "follow_up", "redirect", "handle_edge_case", "wrap_up", "generate_feedback",
    ]
    for action in actions:
        d = PlannerDecision(**{**VALID_DECISION, "next_action": action})
        assert d.next_action == action


def test_all_personas():
    personas = ["confused", "efficient", "chatty", "edge_case", "normal"]
    for p in personas:
        d = PlannerDecision(**{**VALID_DECISION, "persona_signal": p})
        assert d.persona_signal == p
