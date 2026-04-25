"""Chat message rendering helpers."""
import streamlit as st


def render_chat(messages: list[dict]) -> None:
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        with st.chat_message(role):
            st.write(content)
