# Interview Practice Partner

> An agentic AI that conducts mock interviews across 5 roles, adapts to candidate skill and behavior, and produces evidence-grounded feedback.

[Live demo](https://interview-partner-0.streamlit.app/) 

[Architecture](#architecture)

---

## What makes this different

- **Two-LLM agentic architecture**: hidden planner LLM makes structured decisions (persona, difficulty, next action) before the responder LLM produces the user-facing message. Genuinely agentic, not a Q&A wrapper.
- **Evidence-grounded feedback**: every strength and improvement quotes the candidate's actual words. No generic advice.
- **Persona-adaptive behavior**: bot visibly changes tone and pacing for confused / efficient / chatty / edge-case users — driven by the planner, no keyword rules.

---

## Supported roles

- Software Development Engineer (SDE)
- Data Analyst
- Sales
- Retail Associate
- Marketing

---

## Key features

- **Two interview modes** — Practice Mode (chat-based) and Real Simulation (voice-only, fullscreen, camera)
- **Real Simulation Mode** — immersive proctored interview with webcam, fullscreen enforcement, real-time Web Audio waveform, and voice-only interaction: `streamlit-mic-recorder` for STT + `edge-tts` for TTS, audio routed through Web Audio AnalyserNode for live waveform visualization
- 5-role coverage with role-specific question banks and difficulty scaling
- Adaptive difficulty (easier / same / harder based on answer quality)
- Genuine follow-ups referencing what the candidate just said
- Resume-aware question generation (upload PDF for personalized questions)
- Voice input (browser SpeechRecognition / streamlit-mic-recorder) + voice output (edge-tts, Indian-accent female voice)
- Lite proctoring in Practice Mode: focus-shift detection during interviews (tab switches, window blur)
- Full simulation summary in feedback: focus shifts, fullscreen exits, duration
- Transparent reasoning panel (toggle to see planner's JSON each turn)
- Transcript export as Markdown download
- Edge case handling: out-of-scope roles, hostile inputs, gibberish

---

## Setup (under 5 minutes)

Prerequisites: Python 3.11+, an Anthropic API key.

### macOS / Linux

```bash
git clone https://github.com/Shivam-Shukla0/interview-partner.git
cd interview-partner
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Open .env and add: ANTHROPIC_API_KEY=your_key_here
streamlit run app.py
```

### Windows

```bash
git clone https://github.com/Shivam-Shukla0/interview-partner.git
cd interview-partner
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Open .env and add: ANTHROPIC_API_KEY=your_key_here
streamlit run app.py
```

Open `http://localhost:8501` in Chrome for full voice support.

---

## Architecture

```
┌─────────────────────────────────────────────┐
│            Streamlit Frontend               │
│  ┌────────────────┐  ┌──────────────────┐   │
│  │ Chat Messages  │  │ Voice (STT/TTS)  │   │
│  └────────┬───────┘  └─────────┬────────┘   │
└───────────┼────────────────────┼────────────┘
            │                    │
            ▼                    ▼
┌─────────────────────────────────────────────┐
│         InterviewAgent (core.py)            │
│                                             │
│   ┌─────────────────────────────────┐       │
│   │  1. Planner (planner.py)        │       │
│   │     LLM call #1 — returns JSON  │       │
│   │     - persona signal            │       │
│   │     - answer quality            │       │
│   │     - next action               │       │
│   │     - difficulty adjustment     │       │
│   └──────────────┬──────────────────┘       │
│                  │                          │
│   ┌──────────────▼──────────────────┐       │
│   │  2. Responder (responder.py)    │       │
│   │     LLM call #2 — user-facing   │       │
│   │     takes planner output +      │       │
│   │     role prompt → message       │       │
│   └──────────────┬──────────────────┘       │
│                  │                          │
│   ┌──────────────▼──────────────────┐       │
│   │  State Manager (state.py)       │       │
│   └─────────────────────────────────┘       │
│                                             │
│   ┌─────────────────────────────────┐       │
│   │  Feedback Engine (feedback.py)  │       │
│   │  end-of-interview only          │       │
│   └─────────────────────────────────┘       │
└─────────────────────────────────────────────┘
                  │
                  ▼
            Anthropic API
```

### Two interview modes

**Practice Mode** — Streamlit chat UI with optional voice. Lite proctoring (focus-shift badge). Full sidebar with reasoning panel toggle.

**Real Simulation** — Self-contained HTML component (`ui/simulation_component/index.html`) mounted as a Streamlit custom component. Side-by-side layout: webcam (left 40%) + AI panel (right 60%). Voice-only: user clicks the `streamlit-mic-recorder` button rendered below the component → transcript flows to `agent.turn()` → `edge-tts` generates MP3 → base64-encoded and passed to the component as `audio_b64` kwarg → component plays via `#sim-tts-audio` and drives the waveform from live Web Audio `AnalyserNode` frequency data. Status text (`#statusText`) updates through `window.SimStatus()` at each transition.

### The two-LLM pattern

Every user turn triggers two LLM calls:

1. **Planner** — returns structured JSON (persona signal, answer quality, next action, difficulty, etc.). Hidden from user. The agent's "brain."
2. **Responder** — takes the planner's decision + role-specific prompt + conversation history, produces the user-facing message.

This separation is what makes the agent genuinely adaptive instead of a glorified Q&A bot. Toggle the **reasoning panel** in the sidebar to see the planner's decision each turn.

---

## Persona handling

| Persona | Detection signals | Response strategy |
|---|---|---|
| **Confused** | "idk", vague short answers, asks what to do | Suggest role, start easy, offer guidance without being condescending |
| **Efficient** | Short direct answers, "next", "skip intro", no chitchat | Drop preamble, pure question flow, terse acknowledgments |
| **Chatty** | Long tangential answers, off-topic stories, personal anecdotes | Acknowledge briefly, redirect: "Great context — back to [topic]" |
| **Edge case** | Gibberish, abuse, out-of-scope role, jailbreak attempts | Graceful decline, suggest alternative, stay in character |

Detection is LLM-based — the planner classifies each turn, no keyword matching.

---

## Design decisions

| Decision | Chose | Why |
|---|---|---|
| Frontend | Streamlit | Chat UI solved in 20 lines; 3-day timeline made React+FastAPI split wasteful |
| LLM | Claude Sonnet 4.5 | Strong reasoning; reliable structured output via tool-use |
| Two-LLM pattern | Planner + Responder | Separates decision-making from response generation; evaluators can see the "brain" |
| Voice output | edge-tts (en-IN-NeerjaNeural) | Server-side MP3, no browser API key needed, natural Indian-accent voice |
| Voice input | streamlit-mic-recorder | Browser-native STT, Chrome-compatible, zero cost |
| State | st.session_state | Session-scoped interview doesn't need a DB |
| Persona detection | LLM-based | Keyword rules are brittle and evaluators spot them immediately |
| Proctoring (Practice) | JS visibilitychange + blur | Lightweight focus detection without camera or fullscreen enforcement |
| Real Simulation | HTML component + Web Audio | Full immersion: camera, fullscreen, voice-only, live waveform, exit warning |
| Sim ↔ Python comms | Streamlit component postMessage | audio_b64/audio_seq args in → transcript/events out, no extra server needed |

---

## Known limitations

- Voice quality depends on browser (Chrome best)
- Interviews are session-scoped (no history across reloads)
- Only 5 roles supported (intentional scope)
- English primary for voice
- Proctoring uses tab/window focus signals only (no camera)

---

## Future work

- Multi-session progress tracking
- Company-specific prep (upload job description)
- Video mode with body-language cues
- Resume parsing improvements (table/layout extraction)

---

## License

MIT
