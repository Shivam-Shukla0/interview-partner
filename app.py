"""Streamlit entry point for Interview Practice Partner."""
import logging
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as _components

import config
from agent.core import InterviewAgent
from agent.state import InterviewPhase, InterviewState
from ui.chat_view import render_chat
from ui.feedback_view import render_feedback
from ui.styles import inject_styles

logging.basicConfig(level=logging.WARNING)

st.set_page_config(
    page_title="Interview Practice Partner",
    page_icon="🎯",
    layout="centered",
)
inject_styles()

# Declare proctoring component once at module level
_PROCTOR_COMPONENT = _components.declare_component(
    "lite_proctoring",
    path=str(Path(__file__).parent / "ui" / "proctoring_component"),
)

_PROCTOR_PHASES = {InterviewPhase.CALIBRATION, InterviewPhase.INTERVIEWING}


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
    audio_keys = [k for k in st.session_state if isinstance(k, str) and k.startswith("audio_")]
    for key in ["state_dict", "_last_voice_input", "focus_shifts", "_resume_text", "_resume_filename"] + audio_keys:
        st.session_state.pop(key, None)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<p style="font-size:1.1rem;font-weight:800;color:#111827;'
        'margin:0 0 0.75rem 0;letter-spacing:-0.01em">Interview Partner</p>',
        unsafe_allow_html=True,
    )

    state = _get_state()
    role = state.candidate_profile.role

    if role:
        persona = state.candidate_profile.detected_persona
        persona_card = (
            f'<div class="sidebar-card">'
            f'<div class="card-label">Persona</div>'
            f'<span class="badge badge-purple">{persona.replace("_", " ").title()}</span>'
            f'</div>'
        ) if persona else ""

        st.markdown(
            f'<div class="sidebar-cards">'
            f'  <div class="sidebar-card">'
            f'    <div class="card-label">Role</div>'
            f'    <span class="badge badge-indigo">{config.ROLE_DISPLAY_NAMES.get(role, role)}</span>'
            f'  </div>'
            f'  <div class="sidebar-card">'
            f'    <div class="card-label">Phase</div>'
            f'    <span class="badge badge-blue">{state.phase.value}</span>'
            f'  </div>'
            f'  <div class="sidebar-card">'
            f'    <div class="card-label">Questions</div>'
            f'    <span style="font-size:14px;font-weight:600;color:#374151">'
            f'      {state.question_count}&nbsp;/&nbsp;{config.TARGET_QUESTION_COUNT}'
            f'    </span>'
            f'  </div>'
            f'  {persona_card}'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Resume upload
    st.markdown('<p class="sidebar-section-label">Resume (optional)</p>', unsafe_allow_html=True)
    uploaded_pdf = st.file_uploader("Upload PDF for personalized questions", type=["pdf"], label_visibility="collapsed")
    if uploaded_pdf is not None and st.session_state.get("_resume_filename") != uploaded_pdf.name:
        try:
            import io
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(uploaded_pdf.read()))
            raw_text = "\n".join(page.extract_text() or "" for page in reader.pages)
            resume_text = raw_text[:3000].strip()
            st.session_state["_resume_text"] = resume_text
            st.session_state["_resume_filename"] = uploaded_pdf.name
        except Exception:
            st.session_state["_resume_text"] = None
            st.session_state["_resume_filename"] = uploaded_pdf.name

    if st.session_state.get("_resume_text"):
        st.caption("Resume loaded — questions will be personalized")
    elif uploaded_pdf is not None and not st.session_state.get("_resume_text"):
        st.caption("Could not read PDF — proceeding without resume context")

    # Sync resume text into interview state
    state = _get_state()
    resume_text_in_state = state.candidate_profile.resume_text
    resume_text_in_session = st.session_state.get("_resume_text")
    if resume_text_in_state != resume_text_in_session:
        state.candidate_profile.resume_text = resume_text_in_session
        _save_state(state)

    st.divider()

    st.markdown('<p class="sidebar-section-label">Settings</p>', unsafe_allow_html=True)
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
st.markdown(
    '<div class="app-header">'
    '<div class="app-header-title">Interview Practice Partner</div>'
    '<div class="app-header-subtitle">AI-powered mock interview agent</div>'
    '</div>',
    unsafe_allow_html=True,
)

state = _get_state()
agent = _get_agent()

# ── Lite proctoring — focus-shift detection (CALIBRATION + INTERVIEWING only) ─
_proctor_active = state.phase in _PROCTOR_PHASES
if _proctor_active:
    raw_shifts = _PROCTOR_COMPONENT(key="proctor_v1", default=0)
    if raw_shifts:
        st.session_state["focus_shifts"] = int(raw_shifts)

focus_shifts = st.session_state.get("focus_shifts", 0)
if focus_shifts > 0 and _proctor_active:
    st.markdown(
        f'<div style="position:fixed;top:64px;right:20px;z-index:9999;'
        f'background:#FEF2F2;border:1px solid #FECACA;color:#DC2626;'
        f'padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600;'
        f'box-shadow:0 1px 3px rgba(0,0,0,0.1)">'
        f'Focus Shifts: {focus_shifts}</div>',
        unsafe_allow_html=True,
    )

# ── Prepare inline audio before render so it appears below the right message ──
inline_audio = None
if voice_enabled and not voice_muted:
    bot_msg_indices = [i for i, m in enumerate(state.messages) if m["role"] == "assistant"]
    if bot_msg_indices:
        from ui.voice_component import text_to_speech_audio
        last_bot_idx = bot_msg_indices[-1]
        audio_key = f"audio_{last_bot_idx}"
        autoplay = audio_key not in st.session_state
        if audio_key not in st.session_state:
            with st.spinner("Generating voice…"):
                st.session_state[audio_key] = text_to_speech_audio(
                    state.messages[last_bot_idx]["content"]
                )
        inline_audio = {
            "msg_idx": last_bot_idx,
            "bytes": st.session_state[audio_key],
            "autoplay": autoplay,
        }

render_chat(state.messages, inline_audio=inline_audio)

# ── Feedback report ───────────────────────────────────────────────────────────
if state.phase == InterviewPhase.FEEDBACK and state.feedback_result:
    render_feedback(state.feedback_result, focus_shifts=focus_shifts)
    if "error" not in state.feedback_result:
        st.divider()
        if st.button("Start a new interview", use_container_width=True):
            _reset()
            st.rerun()

# ── Planner reasoning panel ───────────────────────────────────────────────────
if show_reasoning and state.planner_logs:
    with st.expander("Bot reasoning (last 3 turns)", expanded=False):
        for log in state.planner_logs[-3:]:
            st.json(log)

# ── Input handling ────────────────────────────────────────────────────────────
_active = state.phase not in (InterviewPhase.FEEDBACK, InterviewPhase.END)

if _active:
    if voice_enabled:
        from ui.voice_component import speech_input
        transcript = speech_input()
        if transcript and transcript != st.session_state.get("_last_voice_input"):
            st.session_state["_last_voice_input"] = transcript
            with st.spinner("Thinking…"):
                _, updated_state = agent.turn(state, transcript)
            _save_state(updated_state)
            st.rerun()

    user_input = st.chat_input("Type your message here…")
    if user_input:
        with st.spinner("Thinking…"):
            _, updated_state = agent.turn(state, user_input)
        _save_state(updated_state)
        st.rerun()
