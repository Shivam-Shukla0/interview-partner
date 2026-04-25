"""Chat message rendering — custom HTML bubbles."""
import html as _html

import streamlit as st


def render_chat(messages: list[dict]) -> None:
    for msg in messages:
        content = _html.escape(msg["content"]).replace("\n", "<br>")
        if msg["role"] == "user":
            st.markdown(
                f'<div class="chat-row user-row">'
                f'<div class="chat-bubble user-bubble">{content}</div>'
                f'<div class="chat-avatar user-avatar">You</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="chat-row bot-row">'
                f'<div class="chat-avatar bot-avatar">AI</div>'
                f'<div class="chat-bubble bot-bubble">{content}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
