"""Feedback report rendering."""
import streamlit as st


def render_feedback(feedback: dict) -> None:
    if "error" in feedback:
        st.error(f"Feedback generation failed: {feedback['error']}")
        return

    st.divider()
    st.header("Interview Feedback Report")

    # Overall impression
    st.info(feedback.get("overall", ""))

    # Score cards
    scores = feedback.get("scores", {})
    cols = st.columns(4)
    labels = {
        "communication": "Communication",
        "domain_depth": "Domain Depth",
        "problem_solving": "Problem-Solving",
        "composure": "Composure",
    }
    for col, (key, label) in zip(cols, labels.items()):
        with col:
            st.metric(label, f"{scores.get(key, 0)}/10")

    st.divider()

    # Strengths
    st.subheader("Top Strengths")
    for strength in feedback.get("strengths", []):
        with st.container():
            st.success(f"**{strength['point']}**\n\n> \"{strength['quote']}\"")

    # Improvements
    st.subheader("Areas to Improve")
    for improvement in feedback.get("improvements", []):
        with st.container():
            st.warning(f"**{improvement['point']}**\n\n{improvement['suggestion']}")

    # Question-by-question breakdown
    with st.expander("Question-by-Question Breakdown"):
        for i, item in enumerate(feedback.get("breakdown", []), 1):
            rating = item.get("rating", "medium")
            color = {"weak": "🔴", "medium": "🟡", "strong": "🟢"}.get(rating, "⚪")
            st.markdown(f"**Q{i}:** {item['question']}")
            st.markdown(f"**Summary:** {item['answer_summary']}")
            st.markdown(f"**Rating:** {color} {rating.capitalize()} — {item['comment']}")
            st.divider()

    # Next steps
    st.subheader("Recommended Next Steps")
    for step in feedback.get("next_steps", []):
        st.markdown(f"- {step}")
