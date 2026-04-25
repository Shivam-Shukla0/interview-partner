"""Voice input (STT) via streamlit-mic-recorder and output (TTS) via Web Speech API."""
import streamlit as st
import streamlit.components.v1 as components
from streamlit_mic_recorder import speech_to_text as _stt

_TTS_IDX_KEY = "_tts_last_index"


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

    Dedup is handled in Python (st.session_state), not sessionStorage, so it
    correctly resets when the interview is restarted. Picks the best available
    voice in priority order; waits for Chrome's lazy-loaded voices before speaking.
    """
    # --- Python-side dedup -------------------------------------------
    last = st.session_state.get(_TTS_IDX_KEY, -1)

    # If index went backward the interview was restarted — reset tracking.
    if message_index < last:
        last = -1

    if message_index <= last:
        return  # Already spoken this message.

    st.session_state[_TTS_IDX_KEY] = message_index
    # -----------------------------------------------------------------

    safe = (
        text.replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace("\n", " ")
            .replace("\r", "")
    )[:600]

    html = f"""
<script>
(function() {{
    if (!window.speechSynthesis) return;

    function pickVoice(voices) {{
        var i, v;
        // 1. Google US English
        for (i = 0; i < voices.length; i++) {{
            if (voices[i].name === 'Google US English') return voices[i];
        }}
        // 2. Microsoft Aria / Jenny
        for (i = 0; i < voices.length; i++) {{
            v = voices[i].name;
            if (v.indexOf('Microsoft Aria') !== -1 || v.indexOf('Microsoft Jenny') !== -1) return voices[i];
        }}
        // 3. Any voice with "Natural" in the name
        for (i = 0; i < voices.length; i++) {{
            if (voices[i].name.indexOf('Natural') !== -1) return voices[i];
        }}
        // 4. en-US cloud voice (localService === false)
        for (i = 0; i < voices.length; i++) {{
            if (voices[i].lang === 'en-US' && !voices[i].localService) return voices[i];
        }}
        // 5. Any en-US voice
        for (i = 0; i < voices.length; i++) {{
            if (voices[i].lang === 'en-US') return voices[i];
        }}
        // 6. Browser default
        return null;
    }}

    function speak() {{
        window.speechSynthesis.cancel();
        var voices = window.speechSynthesis.getVoices();
        var u = new SpeechSynthesisUtterance('{safe}');
        u.lang   = 'en-US';
        u.rate   = 1.0;
        u.pitch  = 1.0;
        u.volume = 1.0;
        var chosen = pickVoice(voices);
        if (chosen) u.voice = chosen;
        window.speechSynthesis.speak(u);
    }}

    // 100ms delay ensures the utterance isn't dropped on first call,
    // then check whether voices are already loaded.
    setTimeout(function() {{
        var voices = window.speechSynthesis.getVoices();
        if (voices.length > 0) {{
            speak();
        }} else {{
            window.speechSynthesis.onvoiceschanged = function() {{
                window.speechSynthesis.onvoiceschanged = null;
                speak();
            }};
        }}
    }}, 100);
}})();
</script>
"""
    components.html(html, height=0)
