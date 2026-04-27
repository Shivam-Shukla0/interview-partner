# Interview Practice Partner

An agentic AI that conducts mock job interviews across 5 roles, adapts to candidate skill and behavior, asks genuine follow-ups, and produces structured feedback grounded in the candidate's actual answers.

**Built for**: Eightfold.ai AI Agent Building assignment (April 2026)

**Live demo**: https://interview-partner-0.streamlit.app/

---

## Supported roles
- Software Development Engineer (SDE)
- Data Analyst
- Sales
- Retail Associate
- Marketing

---

## Key features
- **Two-LLM agentic architecture**: a hidden planner LLM makes decisions (persona, difficulty, next action) as structured JSON; a responder LLM produces the user-facing message.
- **4 persona handling**: bot visibly adapts to Confused, Efficient, Chatty, and Edge-case users.
- **Evidence-based feedback**: final report quotes the candidate's own answers for every strength/improvement.
- **Voice mode**: browser-native STT + TTS via Web Speech API (Chrome recommended).
- **Reasoning panel**: dev toggle shows the planner's JSON for transparency.

---

## Setup (under 5 minutes)

Prerequisites: Python 3.11+, an Anthropic API key.

```bash
git clone https://github.com/Shivam-Shukla0/interview-partner.git
cd interview-partner
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Open .env and paste your ANTHROPIC_API_KEY
streamlit run app.py
```

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

### The two-LLM pattern

Every user turn triggers two LLM calls:

1. **Planner** — returns structured JSON (persona signal, answer quality, next action, difficulty, etc.). Hidden from user. The agent's "brain."
2. **Responder** — takes the planner's decision + role-specific prompt + conversation history, produces the user-facing message.

This separation is what makes the agent genuinely adaptive instead of a glorified Q&A bot. Toggle the "reasoning panel" in the sidebar to see the planner's decision each turn.

---

## Design decisions

| Decision | Chose | Why |
|---|---|---|
| Frontend | Streamlit | Chat UI solved in 20 lines; 3-day timeline made React+FastAPI split wasteful |
| LLM | Claude Sonnet 4.5 | Strong reasoning; reliable structured output via tool-use |
| Two-LLM pattern | Planner + Responder | Separates decision-making from response generation |
| Voice | Web Speech API | Browser-native, zero cost, zero API latency |
| State | st.session_state | Session-scoped interview doesn't need a DB |
| Persona detection | LLM-based | Keyword rules are brittle and evaluators spot them immediately |

---

## Persona handling

| Persona | Detection signals | Response strategy |
|---|---|---|
| **Confused** | "idk", vague short answers, asks what to do | Suggest role, start easy, offer guidance without being condescending |
| **Efficient** | Short direct answers, "next", "skip intro", no chitchat | Drop preamble, pure question flow, terse acknowledgments |
| **Chatty** | Long tangential answers, off-topic stories, personal anecdotes | Acknowledge briefly, redirect: "Great context — back to [topic]" |
| **Edge case** | Gibberish, abuse, out-of-scope role, jailbreak attempts | Graceful decline, suggest alternative, stay in character |

---

## Known limitations
- Voice quality depends on browser (Chrome best)
- Interviews are session-scoped (no history across reloads)
- Only 5 roles supported (intentional scope)
- English primary for voice

---

## Future work
- Resume-aware question generation (parse uploaded PDF)
- Multi-session progress tracking
- Company-specific prep (upload JD)
- Video mode with body-language cues

---

