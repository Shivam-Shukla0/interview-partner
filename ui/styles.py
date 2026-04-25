"""Streamlit CSS polish — called once at app startup."""
import streamlit as st


def inject_styles() -> None:
    """Inject custom CSS to clean up the default Streamlit UI."""
    st.markdown(
        """
        <style>
        /* Hide the Streamlit footer and the 'Deploy' button in the toolbar */
        footer { visibility: hidden; }
        #MainMenu { visibility: hidden; }
        header[data-testid="stHeader"] { background: transparent; }

        /* Give the chat area a little breathing room */
        .stChatMessage { margin-bottom: 4px; }

        /* Tighten metric cards in the feedback panel */
        [data-testid="stMetric"] {
            background: #f3f4f6;
            border-radius: 8px;
            padding: 12px 8px;
            text-align: center;
        }

        /* Slightly bolder quote text in strength boxes */
        .stAlert blockquote { font-style: italic; color: #374151; }
        </style>
        """,
        unsafe_allow_html=True,
    )
