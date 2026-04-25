# Recording Checklist

## Pre-recording setup
- [ ] OBS or QuickTime open, 1080p, 30fps
- [ ] External mic or tested laptop mic (no echo)
- [ ] Browser zoom at 110% (View → Zoom In) for readability
- [ ] Close all notifications (macOS: Focus mode; Linux: Do Not Disturb)
- [ ] Close all browser tabs except the app
- [ ] `streamlit run app.py` already running and loaded in Chrome
- [ ] Sidebar: "Show bot reasoning" toggle ON so planner JSON is visible
- [ ] Sidebar: "Voice mode" ON for at least one persona run (Persona 2 recommended)
- [ ] ANTHROPIC_API_KEY confirmed in .env (run one test turn before recording)

## Dry runs (do before pressing record)
- [ ] Rehearse Persona 1 (Confused) once — timing ~90 sec
- [ ] Rehearse Persona 2 (Efficient) once — timing ~90 sec
- [ ] Rehearse Persona 3 (Chatty) once — timing ~2 min
- [ ] Rehearse Persona 4 (Edge cases) once — timing ~90 sec
- [ ] Run one full interview to the feedback report to confirm it renders

## During recording
- [ ] Speak clearly at normal pace; pause 1s before typing
- [ ] After each bot response, briefly point out what changed in the planner JSON
- [ ] Persona 3: visibly read the 3-paragraph answer so viewers understand the redirect reason
- [ ] Feedback section: scroll through all sections — scores, strengths (with quotes), improvements, breakdown

## Post-recording
- [ ] Trim dead air at start/end
- [ ] Verify total length < 10:00 (aim for 8:30–9:00)
- [ ] Upload to YouTube (unlisted) or Loom
- [ ] Paste link into README.md where it says `[LINK]`
- [ ] Paste Streamlit Cloud link into README.md if deployed

## Final submission checklist
- [ ] `git log --all --full-history -- .env` returns EMPTY (no .env committed)
- [ ] Repo is PUBLIC on GitHub
- [ ] README renders correctly on GitHub (check the raw GitHub page)
- [ ] Demo video link works (open in incognito)
- [ ] Google Form submitted with repo link + video link
- [ ] Submitted before 27 April 2026, 3:00 PM IST
