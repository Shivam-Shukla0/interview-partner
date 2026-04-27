"""Streamlit entry point for Interview Practice Partner."""
import base64 as _b64
import logging
import time as _time
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

# Declare custom components once at module level
_PROCTOR_COMPONENT = _components.declare_component(
    "lite_proctoring",
    path=str(Path(__file__).parent / "ui" / "proctoring_component"),
)

_SIM_COMPONENT = _components.declare_component(
    "sim_interview",
    path=str(Path(__file__).parent / "ui" / "simulation_component"),
)

_PROCTOR_PHASES = {InterviewPhase.CALIBRATION, InterviewPhase.INTERVIEWING}

# Read active mode early so sidebar can adapt
_mode_early = st.session_state.get("_active_mode", "Practice Mode")


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
    _sim_keys = [
        "_sim_audio_b64", "_sim_audio_seq", "_sim_last_mic_transcript",
        "_sim_last_spoken_idx", "_sim_start_time",
        "_sim_was_simulation", "_sim_duration_secs",
        "sim_focus_shifts", "sim_fullscreen_exits", "_mode_force",
    ]
    audio_keys = [k for k in st.session_state if isinstance(k, str) and k.startswith("audio_")]
    for key in [
        "state_dict", "_last_voice_input", "focus_shifts",
        "_resume_text", "_resume_filename",
    ] + _sim_keys + audio_keys:
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

    if _mode_early == "Real Simulation":
        # In sim mode voice is always on; only expose mute control
        voice_enabled = True
        voice_muted = st.toggle("Mute simulation voice", value=False, key="_sim_muted_toggle")
    else:
        voice_enabled = st.toggle("Voice mode", value=False)
        voice_muted = False
        if voice_enabled:
            voice_muted = st.toggle("Mute voice output", value=False)

    st.divider()

    if st.button("Restart", use_container_width=True):
        _reset()
        st.rerun()


# ── Mode toggle ───────────────────────────────────────────────────────────────
_MODES = ["Practice Mode", "Real Simulation"]
if "_active_mode" not in st.session_state:
    st.session_state["_active_mode"] = "Practice Mode"

# When a programmatic mode reset is needed (e.g. after Stop Interview), the code
# sets _mode_force = <target_mode> and calls st.rerun().  On that next run we
# apply the forced value *before* the widget renders (the only safe time to write
# a widget-bound key).  We do NOT do this on every run — doing so would silently
# swallow the user's own radio clicks.
_forced_mode = st.session_state.pop("_mode_force", None)
if _forced_mode is not None:
    st.session_state["interview_mode"] = _forced_mode

_selected_mode = st.radio(
    "Interview Mode",
    options=_MODES,
    horizontal=True,
    key="interview_mode",
    help="Practice Mode: chat-based, casual. Real Simulation: voice-only, camera, fullscreen, proctored.",
)

_active_mode = st.session_state.get("_active_mode", "Practice Mode")

if _selected_mode != _active_mode:
    _switch_state = _get_state()
    _mid_interview = _switch_state.phase in {
        InterviewPhase.CALIBRATION,
        InterviewPhase.INTERVIEWING,
        InterviewPhase.WRAPPING_UP,
    }
    if _mid_interview:
        st.warning("Switching modes will end the current interview. Continue?")
        _sc1, _sc2, _ = st.columns([1.6, 1, 8])
        with _sc1:
            if st.button("Yes, switch", type="primary", key="_mode_yes"):
                st.session_state["_active_mode"] = _selected_mode
                _reset()
                st.rerun()
        with _sc2:
            if st.button("Cancel", key="_mode_no"):
                # Force the radio back to the current active mode on next render
                st.session_state["_mode_force"] = _active_mode
                st.rerun()
    else:
        st.session_state["_active_mode"] = _selected_mode
        _reset()
        st.rerun()

_mode = st.session_state.get("_active_mode", "Practice Mode")

# ── Real Simulation Mode ──────────────────────────────────────────────────────
if _mode == "Real Simulation":
    # Track when this simulation session started
    if "_sim_start_time" not in st.session_state:
        st.session_state["_sim_start_time"] = _time.time()

    state = _get_state()

    # If the interview naturally reached FEEDBACK, switch to Practice Mode to display it
    if state.phase == InterviewPhase.FEEDBACK and state.feedback_result:
        _dur = int(_time.time() - st.session_state.get("_sim_start_time", _time.time()))
        st.session_state["_sim_was_simulation"] = True
        st.session_state["_sim_duration_secs"] = _dur
        st.session_state["_active_mode"] = "Practice Mode"
        st.session_state["_mode_force"]  = "Practice Mode"
        st.rerun()

    # ── Auto-greet: generate TTS for any new bot message not yet sent ────────
    # This fires on the first entry (greeting) and after every agent.turn()
    # that the transcript handler has not already processed.
    _all_bot_msgs = [m for m in state.messages if m["role"] == "assistant"]
    _last_spoken_idx = st.session_state.get("_sim_last_spoken_idx", -1)
    if _all_bot_msgs and (len(_all_bot_msgs) - 1) > _last_spoken_idx:
        _new_bot_idx  = len(_all_bot_msgs) - 1
        _new_bot_text = _all_bot_msgs[_new_bot_idx]["content"]
        st.session_state["_sim_last_spoken_idx"] = _new_bot_idx
        if not voice_muted:
            try:
                from ui.voice_component import text_to_speech_audio
                _ab = text_to_speech_audio(_new_bot_text)
                _seq = st.session_state.get("_sim_audio_seq", 0) + 1
                st.session_state["_sim_audio_b64"] = _b64.b64encode(_ab).decode("utf-8")
                st.session_state["_sim_audio_seq"] = _seq
            except Exception:
                st.session_state["_sim_audio_b64"] = None
        else:
            st.session_state["_sim_audio_b64"] = None
        st.rerun()

    # Render the simulation component, passing audio args
    _sim_data = _SIM_COMPONENT(
        key="sim_v1",
        audio_b64=st.session_state.get("_sim_audio_b64"),
        audio_seq=st.session_state.get("_sim_audio_seq", 0),
        muted=voice_muted,
        default={
            "focus_shifts": 0,
            "fullscreen_exits": 0,
            "stop_requested": False,
            "last_event": None,
        },
    )

    if _sim_data:
        # Persist live tracking data for feedback report
        st.session_state["sim_focus_shifts"]     = _sim_data.get("focus_shifts", 0)
        st.session_state["sim_fullscreen_exits"] = _sim_data.get("fullscreen_exits", 0)

        # ── Stop requested by user (confirmed dialog in JS) ──────────────────
        if _sim_data.get("stop_requested"):
            state = _get_state()
            _dur = int(_time.time() - st.session_state.get("_sim_start_time", _time.time()))

            # Generate feedback if there's Q&A history
            if state.qa_history and state.phase not in (InterviewPhase.FEEDBACK, InterviewPhase.END):
                try:
                    from agent.feedback import FeedbackEngine
                    from agent.llm_client import LLMClient
                    _engine = FeedbackEngine(LLMClient())
                    state.feedback_result = _engine.generate(state)
                    state.phase = InterviewPhase.FEEDBACK
                    _save_state(state)
                except Exception:
                    pass

            st.session_state["_sim_was_simulation"] = True
            st.session_state["_sim_duration_secs"]  = _dur
            st.session_state["_active_mode"]         = "Practice Mode"
            st.session_state["_mode_force"]          = "Practice Mode"
            st.rerun()

    # ── Voice input via streamlit-mic-recorder (rendered below the component) ─
    # The simulation component is the visual layer; actual STT happens here.
    from streamlit_mic_recorder import speech_to_text as _stt

    _sim_transcript = _stt(
        start_prompt="🎤 Speak",
        stop_prompt="⏹  Stop",
        just_once=False,
        use_container_width=True,
        language="en",
        key="sim_stt",
    )

    # Deduplicate: only process when a genuinely new transcript arrives
    if _sim_transcript and _sim_transcript != st.session_state.get("_sim_last_mic_transcript"):
        st.session_state["_sim_last_mic_transcript"] = _sim_transcript
        state = _get_state()
        agent = _get_agent()

        with st.spinner("Thinking…"):
            _, updated_state = agent.turn(state, _sim_transcript)
        _save_state(updated_state)

        # Generate TTS for the latest bot message and mark as spoken so the
        # auto-greet block above does not redundantly re-generate it.
        bot_msgs = [m for m in updated_state.messages if m["role"] == "assistant"]
        if bot_msgs:
            _spoken_idx = len(bot_msgs) - 1
            st.session_state["_sim_last_spoken_idx"] = _spoken_idx
            bot_text = bot_msgs[-1]["content"]
            if not voice_muted:
                try:
                    from ui.voice_component import text_to_speech_audio
                    with st.spinner("Generating voice…"):
                        _audio_bytes = text_to_speech_audio(bot_text)
                    _seq = st.session_state.get("_sim_audio_seq", 0) + 1
                    st.session_state["_sim_audio_b64"] = _b64.b64encode(_audio_bytes).decode("utf-8")
                    st.session_state["_sim_audio_seq"] = _seq
                except Exception:
                    st.session_state["_sim_audio_b64"] = None
            else:
                st.session_state["_sim_audio_b64"] = None

        # If interview finished naturally, flip to Practice Mode for feedback display
        if updated_state.phase == InterviewPhase.FEEDBACK and updated_state.feedback_result:
            _dur = int(_time.time() - st.session_state.get("_sim_start_time", _time.time()))
            st.session_state["_sim_was_simulation"] = True
            st.session_state["_sim_duration_secs"]  = _dur
            st.session_state["_active_mode"]         = "Practice Mode"
            st.session_state["_mode_force"]          = "Practice Mode"

        st.rerun()

    st.stop()

# ── Practice Mode ─────────────────────────────────────────────────────────────
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

# ── Prepare inline audio before render ────────────────────────────────────────
inline_audio = None
if voice_enabled and not voice_muted and _mode_early == "Practice Mode":
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
    _sim_was_sim    = bool(st.session_state.get("_sim_was_simulation"))
    _sim_shifts     = st.session_state.get("sim_focus_shifts", 0)
    _sim_fs_exits   = st.session_state.get("sim_fullscreen_exits", 0)
    _sim_dur        = st.session_state.get("_sim_duration_secs", 0)

    render_feedback(
        state.feedback_result,
        focus_shifts=focus_shifts,
        qa_history=state.qa_history,
        role=state.candidate_profile.role,
        persona=state.candidate_profile.detected_persona,
        sim_was_simulation=_sim_was_sim,
        sim_focus_shifts=_sim_shifts,
        sim_fullscreen_exits=_sim_fs_exits,
        sim_duration_secs=_sim_dur,
    )
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

# ── Input handling (Practice Mode only — no chat input in Real Simulation) ────
_active = state.phase not in (InterviewPhase.FEEDBACK, InterviewPhase.END)

if _active:
    if voice_enabled and _mode_early == "Practice Mode":
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
