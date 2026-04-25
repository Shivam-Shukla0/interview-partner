"""Streamlit CSS — injected once at app startup."""
import streamlit as st

_CSS = """
<style>

/* ── Base cleanup ──────────────────────────────────────────────────────────── */
footer { visibility: hidden; }
#MainMenu { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }
.main .block-container {
    padding-top: 1.25rem;
    padding-bottom: 3rem;
    max-width: 780px;
}

/* ── App header ────────────────────────────────────────────────────────────── */
.app-header {
    padding-bottom: 0.85rem;
    border-bottom: 3px solid #4F46E5;
    margin-bottom: 1.1rem;
}
.app-header-title {
    font-size: 1.75rem;
    font-weight: 800;
    color: #111827;
    margin: 0;
    line-height: 1.2;
}
.app-header-subtitle {
    font-size: 0.85rem;
    color: #6B7280;
    margin-top: 3px;
    font-weight: 400;
}

/* ── Chat bubbles ──────────────────────────────────────────────────────────── */
.chat-row {
    display: flex;
    align-items: flex-end;
    margin-bottom: 14px;
    gap: 8px;
}
.user-row { flex-direction: row-reverse; }

.chat-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.03em;
    flex-shrink: 0;
    text-transform: uppercase;
}
.user-avatar { background: #4F46E5; color: #fff; }
.bot-avatar  { background: #E5E7EB; color: #374151; }

.chat-bubble {
    max-width: 70%;
    padding: 11px 16px;
    border-radius: 18px;
    font-size: 14.5px;
    line-height: 1.55;
    word-wrap: break-word;
    white-space: pre-wrap;
}
.user-bubble {
    background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%);
    color: #fff;
    border-bottom-right-radius: 4px;
    box-shadow: 0 2px 10px rgba(79, 70, 229, 0.22);
}
.bot-bubble {
    background: #F3F4F6;
    color: #111827;
    border: 1px solid #E5E7EB;
    border-bottom-left-radius: 4px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

/* ── Sidebar info cards ────────────────────────────────────────────────────── */
.sidebar-cards { display: flex; flex-direction: column; gap: 8px; margin-bottom: 8px; }
.sidebar-card {
    background: #fff;
    border-radius: 10px;
    padding: 10px 14px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    border: 1px solid #F3F4F6;
}
.card-label {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #9CA3AF;
    margin-bottom: 5px;
}
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 99px;
    font-size: 12px;
    font-weight: 500;
}
.badge-indigo { background: #EEF2FF; color: #4338CA; }
.badge-blue   { background: #EFF6FF; color: #2563EB; }
.badge-purple { background: #F5F3FF; color: #7C3AED; }
.sidebar-section-label {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #9CA3AF;
    margin: 10px 0 4px 0;
}

/* ── Audio player ──────────────────────────────────────────────────────────── */
[data-testid="stAudio"] { margin: 2px 0 10px 44px; }
[data-testid="stAudio"] audio {
    height: 34px;
    border-radius: 17px;
    max-width: 300px;
}

/* ── Feedback: score cards ─────────────────────────────────────────────────── */
.score-card {
    background: #F9FAFB;
    border-radius: 10px;
    padding: 14px 10px;
    text-align: center;
    border: 1px solid #E5E7EB;
}
.score-label {
    font-size: 10px;
    color: #6B7280;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 6px;
}
.score-value {
    font-size: 28px;
    font-weight: 800;
    line-height: 1;
}
.score-denom { font-size: 13px; font-weight: 500; color: #9CA3AF; }
.score-high  { color: #10B981; }
.score-mid   { color: #F59E0B; }
.score-low   { color: #EF4444; }

/* ── Feedback: strength / improvement boxes ────────────────────────────────── */
.strength-box {
    background: #F0FDF4;
    border-left: 4px solid #10B981;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin-bottom: 10px;
}
.strength-title { font-weight: 600; color: #065F46; margin-bottom: 6px; font-size: 14px; }
.strength-quote {
    font-style: italic;
    color: #374151;
    font-size: 13.5px;
    padding: 6px 10px;
    border-left: 2px solid #6EE7B7;
    background: rgba(167, 243, 208, 0.25);
    border-radius: 0 4px 4px 0;
    display: block;
}

.improvement-box {
    background: #FFFBEB;
    border-left: 4px solid #F59E0B;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin-bottom: 10px;
}
.improvement-title { font-weight: 600; color: #92400E; margin-bottom: 6px; font-size: 14px; }
.improvement-suggestion { color: #374151; font-size: 13.5px; }

/* ── Feedback: breakdown rows ──────────────────────────────────────────────── */
.breakdown-row {
    padding: 10px 12px;
    border-radius: 6px;
    margin-bottom: 6px;
    font-size: 13.5px;
}
.breakdown-odd  { background: #F9FAFB; }
.breakdown-even { background: #fff; border: 1px solid #F3F4F6; }
.breakdown-q    { font-weight: 600; color: #111827; margin-bottom: 4px; }
.breakdown-a    { color: #4B5563; margin-bottom: 4px; font-style: italic; }
.breakdown-rating { font-size: 12px; font-weight: 500; }

/* ── Feedback: next steps ──────────────────────────────────────────────────── */
.next-step-item {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 10px 14px;
    background: #EFF6FF;
    border-radius: 8px;
    margin-bottom: 8px;
    font-size: 14px;
    color: #1E40AF;
    border: 1px solid #DBEAFE;
}
.next-step-arrow { font-size: 14px; flex-shrink: 0; margin-top: 1px; font-weight: 700; }

/* ── Overall impression box override ──────────────────────────────────────── */
.overall-box {
    background: #EEF2FF;
    border-left: 4px solid #4F46E5;
    border-radius: 0 8px 8px 0;
    padding: 14px 18px;
    color: #1E1B4B;
    font-size: 14.5px;
    line-height: 1.6;
    margin-bottom: 1.25rem;
}

</style>
"""


def inject_styles() -> None:
    """Inject custom CSS into the Streamlit app."""
    st.markdown(_CSS, unsafe_allow_html=True)
