"""Feedback report rendering — color-coded, evidence-anchored."""
import html as _html

import streamlit as st


def _score_class(score: int) -> str:
    if score >= 8:
        return "score-high"
    if score >= 5:
        return "score-mid"
    return "score-low"


def render_feedback(feedback: dict) -> None:
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
