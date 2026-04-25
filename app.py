"""Streamlit entry point for Interview Practice Partner."""
import logging

import streamlit as st

from agent.core import InterviewAgent
from agent.state import InterviewPhase, InterviewState
from ui.chat_view import render_chat
from ui.feedback_view import render_feedback

logging.basicConfig(level=logging.WARNING)

st.set_page_config(
    page_title="Interview Practice Partner",
    page_icon="🎯",
    layout="centered",
)


def _get_agent() -> InterviewAgent:
    if "agent" not in st.session_state:
        st.session_state.agent = InterviewAgent()
    return st.session_state.agent


def _get_state() -> InterviewState:
    if "state_dict" not in st.session_state:
        agent = _get_agent()
        greeting, state = agent.start()
        st.session_state.state_dict = state.to_dict()
    return InterviewState.from_dict(st.session_state.state_dict)


def _save_state(state: InterviewState) -> None:
    st.session_state.state_dict = state.to_dict()


def _reset() -> None:
    for key in ["state_dict"]:
        st.session_state.pop(key, None)


# --- Sidebar ---
with st.sidebar:
    st.title("Interview Partner")

    state = _get_state()
    role = state.candidate_profile.role
    if role:
        from config import ROLE_DISPLAY_NAMES
        st.markdown(f"**Role:** {ROLE_DISPLAY_NAMES.get(role, role)}")
        st.markdown(f"**Phase:** {state.phase.value}")
        st.markdown(f"**Questions:** {state.question_count}")
        persona = state.candidate_profile.detected_persona
        if persona:
            st.markdown(f"**Persona:** {persona}")

    st.divider()

    show_reasoning = st.toggle("Show bot reasoning", value=False)

    if st.button("Restart", use_container_width=True):
        _reset()
        st.rerun()

# --- Main ---
st.title("Interview Practice Partner")

state = _get_state()
agent = _get_agent()

render_chat(state.messages)

# Show feedback report if in FEEDBACK phase
if state.phase == InterviewPhase.FEEDBACK and state.feedback_result:
    render_feedback(state.feedback_result)
    if "error" not in state.feedback_result:
        st.divider()
        if st.button("Start a new interview", use_container_width=True):
            _reset()
            st.rerun()

# Show planner reasoning panel
if show_reasoning and state.planner_logs:
    with st.expander("Bot reasoning (last 3 turns)", expanded=False):
        for log in state.planner_logs[-3:]:
            st.json(log)

# Chat input — disabled during feedback
if state.phase not in (InterviewPhase.FEEDBACK, InterviewPhase.END):
    user_input = st.chat_input("Type your message here…")
    if user_input:
        with st.spinner("Thinking…"):
            _, updated_state = agent.turn(state, user_input)
        _save_state(updated_state)
        st.rerun()
