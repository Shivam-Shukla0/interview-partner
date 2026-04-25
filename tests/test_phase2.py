"""Tests for Phase 2 features: edge case handling, wrap-up logic, memory pruning."""
from unittest.mock import MagicMock

import pytest

import config
from agent.state import InterviewPhase, InterviewState, QAPair
from agent.responder import _EDGE_CASE_TYPE_INSTRUCTIONS


# --- helpers ---

def _make_agent():
    """InterviewAgent with all LLM dependencies stubbed out."""
    from agent.core import InterviewAgent
    agent = InterviewAgent.__new__(InterviewAgent)
    agent._llm = MagicMock()
    agent._planner = MagicMock()
    agent._responder = MagicMock()
    agent._feedback_engine = MagicMock()
    return agent


def _decision(**overrides) -> dict:
    base = {
        "next_action": "ask_main_question",
        "persona_signal": "normal",
        "last_answer_quality": "n/a",
        "difficulty_adjustment": "same",
        "should_wrap_up": False,
        "edge_case_type": None,
        "topic_to_probe": None,
        "internal_note": "test",
    }
    base.update(overrides)
    return base


# --- edge case type instructions ---

def test_edge_case_type_keys_complete():
    expected = {"out_of_scope_role", "hostile", "gibberish", "meta_question"}
    assert set(_EDGE_CASE_TYPE_INSTRUCTIONS.keys()) == expected


def test_edge_case_type_instructions_non_empty():
    for key, text in _EDGE_CASE_TYPE_INSTRUCTIONS.items():
        assert len(text) > 20, f"Instruction for {key!r} is too short"


# --- summary_note serialization ---

def test_summary_note_round_trip():
    state = InterviewState()
    state.summary_note = "The candidate is a fresher practicing for SDE."
    restored = InterviewState.from_dict(state.to_dict())
    assert restored.summary_note == state.summary_note


def test_summary_note_defaults_none():
    state = InterviewState()
    assert state.summary_note is None
    restored = InterviewState.from_dict(state.to_dict())
    assert restored.summary_note is None


# --- wrap-up logic ---

def test_should_wrap_up_triggers_wrapping_up():
    """should_wrap_up=True while INTERVIEWING must transition to WRAPPING_UP."""
    agent = _make_agent()
    state = InterviewState(phase=InterviewPhase.INTERVIEWING, question_count=3)
    result = agent._apply_decision(state, _decision(should_wrap_up=True), "answer")
    assert result.phase == InterviewPhase.WRAPPING_UP


def test_generate_feedback_action_sets_feedback_phase():
    agent = _make_agent()
    state = InterviewState(phase=InterviewPhase.WRAPPING_UP)
    result = agent._apply_decision(
        state, _decision(next_action="generate_feedback", should_wrap_up=False), "no questions"
    )
    assert result.phase == InterviewPhase.FEEDBACK


def test_should_wrap_up_false_stays_interviewing():
    """should_wrap_up=False with ask_main_question must NOT trigger wrap-up."""
    agent = _make_agent()
    state = InterviewState(phase=InterviewPhase.INTERVIEWING, question_count=2)
    result = agent._apply_decision(state, _decision(should_wrap_up=False), "answer")
    assert result.phase == InterviewPhase.INTERVIEWING


def test_max_question_count_forces_wrapping_up():
    """Hard cap: MAX_QUESTION_COUNT reached forces WRAPPING_UP regardless of planner."""
    agent = _make_agent()
    state = InterviewState(phase=InterviewPhase.INTERVIEWING, question_count=config.MAX_QUESTION_COUNT)
    result = agent._apply_decision(state, _decision(should_wrap_up=False), "answer")
    assert result.phase == InterviewPhase.WRAPPING_UP


def test_wrap_up_not_triggered_outside_interviewing():
    """should_wrap_up=True while NOT in INTERVIEWING phase must not clobber FEEDBACK."""
    agent = _make_agent()
    state = InterviewState(phase=InterviewPhase.FEEDBACK)
    result = agent._apply_decision(state, _decision(should_wrap_up=True), "thanks")
    assert result.phase == InterviewPhase.FEEDBACK


# --- memory pruning ---

def test_prune_trims_and_stores_summary():
    agent = _make_agent()
    agent._llm.complete.return_value = "Summary of earlier conversation."

    state = InterviewState()
    for i in range(11):
        state.messages.append({"role": "user", "content": f"user turn {i}"})
        state.messages.append({"role": "assistant", "content": f"bot turn {i}"})

    assert len(state.messages) == 22
    result = agent._prune_if_needed(state)

    assert len(result.messages) == 12
    assert result.summary_note == "Summary of earlier conversation."


def test_prune_not_triggered_under_threshold():
    agent = _make_agent()
    state = InterviewState()
    for i in range(10):
        state.messages.append({"role": "user", "content": f"u{i}"})

    result = agent._prune_if_needed(state)
    assert len(result.messages) == 10
    assert result.summary_note is None
    agent._llm.complete.assert_not_called()


def test_prune_incorporates_existing_summary():
    """When a summary already exists, the new LLM prompt should include it."""
    agent = _make_agent()
    agent._llm.complete.return_value = "Updated combined summary."

    state = InterviewState()
    state.summary_note = "Earlier summary."
    for i in range(11):
        state.messages.append({"role": "user", "content": f"u{i}"})
        state.messages.append({"role": "assistant", "content": f"b{i}"})

    agent._prune_if_needed(state)

    call_args = agent._llm.complete.call_args
    prompt_content = call_args[1]["messages"][0]["content"]
    assert "Earlier summary." in prompt_content
