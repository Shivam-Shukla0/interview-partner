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
    for key in ["state_dict", "_last_voice_input"]:
        st.session_state.pop(key, None)


# ── Sidebar ───────────────────────────────────────────────────────────────────
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
    voice_enabled = st.toggle("Voice mode", value=False)
    voice_muted = False
    if voice_enabled:
        voice_muted = st.toggle("Mute voice output", value=False)

    st.divider()

    if st.button("Restart", use_container_width=True):
        _reset()
        st.rerun()

# ── Main ──────────────────────────────────────────────────────────────────────
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

# ── Input handling ────────────────────────────────────────────────────────────
_active = state.phase not in (InterviewPhase.FEEDBACK, InterviewPhase.END)

if _active:
    # Voice input — mic button rendered above the text input
    if voice_enabled:
        from ui.voice_component import speech_input
        transcript = speech_input()
        if transcript and transcript != st.session_state.get("_last_voice_input"):
            st.session_state["_last_voice_input"] = transcript
            with st.spinner("Thinking…"):
                _, updated_state = agent.turn(state, transcript)
            _save_state(updated_state)
            st.rerun()

    # Text input (always available)
    user_input = st.chat_input("Type your message here…")
    if user_input:
        with st.spinner("Thinking…"):
            _, updated_state = agent.turn(state, user_input)
        _save_state(updated_state)
        st.rerun()

# ── Voice output (TTS) ────────────────────────────────────────────────────────
if voice_enabled and not voice_muted:
    bot_msgs = [m for m in state.messages if m["role"] == "assistant"]
    if bot_msgs:
        from ui.voice_component import speech_output
        # Use total message count as a stable key so only new messages get spoken
        speech_output(bot_msgs[-1]["content"], len(state.messages))
