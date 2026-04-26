"""Chat message rendering — custom HTML bubbles."""
import html as _html

import streamlit as st


def render_chat(messages: list[dict], inline_audio: dict | None = None) -> None:
    """Render chat messages as styled bubbles.

    inline_audio: optional dict with keys msg_idx (int), bytes (bytes), autoplay (bool).
    When provided, renders an audio player immediately below the message at msg_idx.
    """
    for i, msg in enumerate(messages):
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

        if inline_audio and i == inline_audio.get("msg_idx"):
            st.audio(
                inline_audio["bytes"],
                format="audio/mp3",
                autoplay=inline_audio.get("autoplay", False),
            )
