"""Test InterviewState serialization and phase transitions."""
import pytest

from agent.state import (
    CandidateProfile,
    InterviewPhase,
    InterviewState,
    QAPair,
)


def test_default_state():
    state = InterviewState()
    assert state.phase == InterviewPhase.GREETING
    assert state.question_count == 0
    assert state.messages == []
    assert state.qa_history == []


def test_round_trip_serialization():
    state = InterviewState(
        phase=InterviewPhase.INTERVIEWING,
        candidate_profile=CandidateProfile(role="sde", inferred_level="mid", detected_persona="efficient"),
        question_count=3,
        current_difficulty="medium",
    )
    state.messages.append({"role": "user", "content": "Hello"})
    state.qa_history.append(QAPair(question="What is a HashMap?", answer="Key-value structure", topic="data_structures", quality="medium"))

    d = state.to_dict()
    restored = InterviewState.from_dict(d)

    assert restored.phase == InterviewPhase.INTERVIEWING
    assert restored.candidate_profile.role == "sde"
    assert restored.candidate_profile.detected_persona == "efficient"
    assert restored.question_count == 3
    assert restored.current_difficulty == "medium"
    assert len(restored.messages) == 1
    assert len(restored.qa_history) == 1
    assert restored.qa_history[0].question == "What is a HashMap?"


def test_phase_enum_values():
    phases = [
        "GREETING", "ROLE_SELECTION", "CALIBRATION",
        "INTERVIEWING", "WRAPPING_UP", "FEEDBACK", "END",
    ]
    for p in phases:
        phase = InterviewPhase(p)
        assert phase.value == p


def test_feedback_result_round_trip():
    state = InterviewState()
    state.feedback_result = {"overall": "Good job!", "scores": {"communication": 7}}
    restored = InterviewState.from_dict(state.to_dict())
    assert restored.feedback_result["overall"] == "Good job!"
