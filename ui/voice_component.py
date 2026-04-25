"""Voice input (STT) via streamlit-mic-recorder; output (TTS) via edge-tts."""
import asyncio

import edge_tts
import streamlit as st
from streamlit_mic_recorder import speech_to_text as _stt

VOICE = "en-IN-NeerjaNeural"


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


async def _generate_audio_async(text: str) -> bytes:
    communicate = edge_tts.Communicate(text, VOICE)
    chunks = []
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            chunks.append(chunk["data"])
    return b"".join(chunks)


def text_to_speech_audio(text: str) -> bytes:
    """Generate MP3 audio bytes for text using edge-tts (en-IN-NeerjaNeural voice).

    Calls Microsoft's free edge-tts endpoint; requires internet. ~1-2s latency.
    """
    return asyncio.run(_generate_audio_async(text))
