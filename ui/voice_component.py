"""Voice input (STT) and output (TTS) using browser-native Web Speech API."""
from pathlib import Path

import streamlit.components.v1 as components

_COMPONENT_DIR = Path(__file__).parent / "speech_component"

# Registered once at import time; Streamlit serves the directory as a component frontend.
_stt = components.declare_component("interview_stt", path=str(_COMPONENT_DIR))


def speech_input() -> str | None:
    """Render a mic button.  Returns the transcript string when speech is detected, else None."""
    return _stt(default=None, key="interview_stt_widget")


def speech_output(text: str, message_index: int) -> None:
    """Speak `text` via browser TTS exactly once per message_index.

    Uses sessionStorage keyed by message_index so reruns don't re-speak the same message.
    Silently no-ops in browsers that don't support speechSynthesis.
    """
    safe = (
        text.replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace("\n", " ")
            .replace("\r", "")
    )[:600]

    html = f"""
<script>
(function() {{
    var key = 'spoken_{message_index}';
    if (sessionStorage.getItem(key)) return;
    sessionStorage.setItem(key, '1');
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    var u = new SpeechSynthesisUtterance('{safe}');
    u.lang = 'en-US';
    u.rate = 1.0;
    window.speechSynthesis.speak(u);
}})();
</script>
"""
    components.html(html, height=0)
