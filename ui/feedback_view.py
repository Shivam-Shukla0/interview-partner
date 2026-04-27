"""Feedback report rendering — color-coded, evidence-anchored."""
import html as _html
from datetime import datetime
from typing import Optional

import streamlit as st


def _score_class(score: int) -> str:
    if score >= 8:
        return "score-high"
    if score >= 5:
        return "score-mid"
    return "score-low"


def _build_transcript_md(
    feedback: dict,
    qa_history: list,
    role: Optional[str],
    persona: Optional[str],
    focus_shifts: int,
    sim_was_simulation: bool = False,
    sim_focus_shifts: int = 0,
    sim_fullscreen_exits: int = 0,
    sim_duration_secs: int = 0,
) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    scores = feedback.get("scores", {})
    lines = [
        "# Interview Transcript",
        "",
        f"**Date:** {now}",
        f"**Role:** {role or 'Not specified'}",
        f"**Detected Persona:** {persona or 'N/A'}",
        f"**Total Questions:** {len(qa_history)}",
    ]

    if sim_was_simulation:
        mins = sim_duration_secs // 60
        secs = sim_duration_secs % 60
        lines += [
            "",
            "## Simulation Summary",
            "",
            f"- **Mode:** Real Simulation",
            f"- **Focus Shifts:** {sim_focus_shifts}",
            f"- **Fullscreen Exits:** {sim_fullscreen_exits}",
            f"- **Duration:** {mins:02d}:{secs:02d}",
        ]
    else:
        lines.append(f"**Focus Shifts:** {focus_shifts}")

    lines += [
        "",
        "---",
        "",
        "## Questions & Answers",
        "",
    ]
    for i, qa in enumerate(qa_history, 1):
        lines += [
            f"### Q{i}: {qa.question}",
            "",
            f"**Answer:** {qa.answer}",
            "",
            f"*Quality: {qa.quality or 'N/A'} | Topic: {qa.topic}*",
            "",
        ]

    lines += [
        "---",
        "",
        "## Feedback Summary",
        "",
        f"**Overall:** {feedback.get('overall', '')}",
        "",
        "### Scores",
        "",
        f"- Communication: {scores.get('communication', 'N/A')}/10",
        f"- Domain Depth: {scores.get('domain_depth', 'N/A')}/10",
        f"- Problem-Solving: {scores.get('problem_solving', 'N/A')}/10",
        f"- Composure: {scores.get('composure', 'N/A')}/10",
        "",
        "### Top Strengths",
        "",
    ]
    for s in feedback.get("strengths", []):
        lines += [f"- **{s.get('point', '')}**", f'  > "{s.get("quote", "")}"', ""]

    lines += ["### Areas to Improve", ""]
    for imp in feedback.get("improvements", []):
        lines += [f"- **{imp.get('point', '')}:** {imp.get('suggestion', '')}", ""]

    lines += ["### Recommended Next Steps", ""]
    for step in feedback.get("next_steps", []):
        lines.append(f"- {step}")

    lines += ["", "---", ""]
    if sim_was_simulation:
        lines.append(f"*Simulation — Focus Shifts: {sim_focus_shifts} | Fullscreen Exits: {sim_fullscreen_exits}*")
    else:
        lines.append(f"*Focus Shifts: {focus_shifts}*")
    return "\n".join(lines)


def render_feedback(
    feedback: dict,
    focus_shifts: int = 0,
    qa_history: Optional[list] = None,
    role: Optional[str] = None,
    persona: Optional[str] = None,
    sim_was_simulation: bool = False,
    sim_focus_shifts: int = 0,
    sim_fullscreen_exits: int = 0,
    sim_duration_secs: int = 0,
) -> None:
    if "error" in feedback:
        st.error(f"Feedback generation failed: {feedback['error']}")
        return

    st.divider()
    st.markdown(
        '<h2 style="font-size:1.35rem;font-weight:800;color:#111827;margin-bottom:0.75rem">'
        "Interview Feedback Report"
        "</h2>",
        unsafe_allow_html=True,
    )

    # ── Simulation Summary (shown at top when interview ran in Real Simulation) ──
    if sim_was_simulation:
        mins = sim_duration_secs // 60
        secs = sim_duration_secs % 60
        dur_str = f"{mins:02d}:{secs:02d}"

        if sim_focus_shifts == 0:
            shift_color = "#10B981"
        elif sim_focus_shifts <= 5:
            shift_color = "#F59E0B"
        else:
            shift_color = "#EF4444"

        st.markdown(
            f'<div style="background:#0F0E17;border:1px solid rgba(79,70,229,0.45);'
            f'border-radius:12px;padding:18px 22px;margin-bottom:1.25rem;">'
            f'<div style="font-size:10px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;'
            f'color:rgba(255,255,255,0.45);margin-bottom:12px">Simulation Summary</div>'
            f'<div style="display:flex;gap:32px;flex-wrap:wrap;">'
            f'  <div>'
            f'    <div style="color:rgba(255,255,255,0.5);font-size:11px;margin-bottom:4px">Focus Shifts</div>'
            f'    <div style="font-size:24px;font-weight:800;color:{shift_color}">{sim_focus_shifts}</div>'
            f'  </div>'
            f'  <div>'
            f'    <div style="color:rgba(255,255,255,0.5);font-size:11px;margin-bottom:4px">Fullscreen Exits</div>'
            f'    <div style="font-size:24px;font-weight:800;color:#A78BFA">{sim_fullscreen_exits}</div>'
            f'  </div>'
            f'  <div>'
            f'    <div style="color:rgba(255,255,255,0.5);font-size:11px;margin-bottom:4px">Duration</div>'
            f'    <div style="font-size:24px;font-weight:800;color:#60A5FA">{dur_str}</div>'
            f'  </div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Overall impression
    overall = _html.escape(feedback.get("overall", ""))
    st.markdown(
        f'<div class="overall-box">{overall}</div>',
        unsafe_allow_html=True,
    )

    # Score cards — color-coded by band
    scores = feedback.get("scores", {})
    labels = {
        "communication": "Communication",
        "domain_depth": "Domain Depth",
        "problem_solving": "Problem-Solving",
        "composure": "Composure",
    }
    cols = st.columns(4)
    for col, (key, label) in zip(cols, labels.items()):
        score = scores.get(key, 0)
        cls = _score_class(score)
        with col:
            st.markdown(
                f'<div class="score-card">'
                f'<div class="score-label">{label}</div>'
                f'<div class="score-value {cls}">{score}'
                f'<span class="score-denom">/10</span></div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # Strengths
    st.markdown(
        '<h3 style="font-size:1rem;font-weight:700;color:#065F46;margin-bottom:0.6rem">✓ Top Strengths</h3>',
        unsafe_allow_html=True,
    )
    for item in feedback.get("strengths", []):
        point = _html.escape(item.get("point", ""))
        quote = _html.escape(item.get("quote", ""))
        st.markdown(
            f'<div class="strength-box">'
            f'<div class="strength-title">{point}</div>'
            f'<span class="strength-quote">"{quote}"</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Improvements
    st.markdown(
        '<h3 style="font-size:1rem;font-weight:700;color:#92400E;margin-bottom:0.6rem">⚠ Areas to Improve</h3>',
        unsafe_allow_html=True,
    )
    for item in feedback.get("improvements", []):
        point = _html.escape(item.get("point", ""))
        suggestion = _html.escape(item.get("suggestion", ""))
        st.markdown(
            f'<div class="improvement-box">'
            f'<div class="improvement-title">{point}</div>'
            f'<div class="improvement-suggestion">{suggestion}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Question-by-question breakdown
    with st.expander("Question-by-Question Breakdown"):
        for i, item in enumerate(feedback.get("breakdown", []), 1):
            rating = item.get("rating", "medium")
            icon = {"weak": "🔴", "medium": "🟡", "strong": "🟢"}.get(rating, "⚪")
            q = _html.escape(item.get("question", ""))
            a_sum = _html.escape(item.get("answer_summary", ""))
            comment = _html.escape(item.get("comment", ""))
            row_cls = "breakdown-odd" if i % 2 == 1 else "breakdown-even"
            st.markdown(
                f'<div class="breakdown-row {row_cls}">'
                f'<div class="breakdown-q">Q{i}: {q}</div>'
                f'<div class="breakdown-a">{a_sum}</div>'
                f'<div class="breakdown-rating">{icon} {rating.capitalize()} — {comment}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # Next steps
    st.markdown(
        '<h3 style="font-size:1rem;font-weight:700;color:#1E40AF;margin-bottom:0.6rem">🎯 Recommended Next Steps</h3>',
        unsafe_allow_html=True,
    )
    for step in feedback.get("next_steps", []):
        step_esc = _html.escape(step)
        st.markdown(
            f'<div class="next-step-item">'
            f'<span class="next-step-arrow">→</span>'
            f'<span>{step_esc}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Proctoring summary (Practice Mode focus-shift count)
    if not sim_was_simulation:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            '<h3 style="font-size:1rem;font-weight:700;color:#374151;margin-bottom:0.6rem">'
            "Proctoring Summary</h3>",
            unsafe_allow_html=True,
        )
        if focus_shifts == 0:
            st.markdown(
                '<div style="background:#F0FDF4;border-left:4px solid #10B981;border-radius:0 8px 8px 0;'
                'padding:10px 16px;color:#065F46;font-size:14px">'
                '✓ Perfect focus throughout the interview — 0 focus shifts detected.'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div style="background:#FFFBEB;border-left:4px solid #F59E0B;border-radius:0 8px 8px 0;'
                f'padding:10px 16px;color:#92400E;font-size:14px">'
                f'Note: focus shifted {focus_shifts} time{"s" if focus_shifts != 1 else ""} during the interview.'
                f'</div>',
                unsafe_allow_html=True,
            )

    # Transcript export
    if qa_history is not None:
        st.markdown("<br>", unsafe_allow_html=True)
        transcript_md = _build_transcript_md(
            feedback, qa_history, role, persona, focus_shifts,
            sim_was_simulation=sim_was_simulation,
            sim_focus_shifts=sim_focus_shifts,
            sim_fullscreen_exits=sim_fullscreen_exits,
            sim_duration_secs=sim_duration_secs,
        )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            label="Download interview transcript",
            data=transcript_md,
            file_name=f"interview_transcript_{timestamp}.md",
            mime="text/markdown",
            use_container_width=True,
        )
