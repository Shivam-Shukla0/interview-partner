"""Voice input (STT) via streamlit-mic-recorder and output (TTS) via Web Speech API."""
import streamlit as st
import streamlit.components.v1 as components
from streamlit_mic_recorder import speech_to_text as _stt


def speech_input() -> str | None:
    """Render mic button. Returns transcript string when speech is detected, else None.

    Uses streamlit-mic-recorder to capture audio in the browser and transcribe via
    Google Speech Recognition server-side. Works in Chrome; shows a fallback note
    in unsupported browsers automatically.
    """
    transcript = _stt(
        start_prompt="🎤 Click to speak",
        stop_prompt="⏹ Stop",
        just_once=False,
        use_container_width=False,
        language="en",
        key="interview_stt_widget",
    )
    st.caption("Voice available in Chrome.")
    return transcript


def speech_output(text: str, message_index: int) -> None:
    """Speak `text` via browser speechSynthesis exactly once per message_index.

    Uses sessionStorage keyed by message_index so Streamlit reruns don't re-speak
    the same message. Silently no-ops in browsers without speechSynthesis support.
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
