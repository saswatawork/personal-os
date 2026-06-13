# personal-os — Claude Code Instructions

## What This Project Is
A personal AI platform built by the user. One source of truth about who he is,
what he's building, and where he's going. Multiple applications are built on top of it:
personal assistant, learning guide, video studio bridge, and future apps.

This is not a work project. It is infrastructure for a life.

## The Workflow — Follow This Every Session

### At The Start of Every Session
1. Read the most recent ADR in `decisions/` to know where we left off
2. Ask what we're working on today if it's not clear
3. Do NOT start building until we've done a brief brainstorm

### Before Building Anything New
1. **Brainstorm** — discuss the problem in conversation first (5 minutes max)
2. **Decide** — agree on the approach
3. **Write the ADR** — document the decision BEFORE writing code
4. **Build** — execute against the agreed plan
5. **Review** — after each phase, check if the ADR needs updating

### When To Write an ADR
Write an ADR for any decision that:
- Affects the architecture or structure of the project
- Involves choosing between two or more real options
- Future-the user would want to understand the reasoning behind

Do NOT write an ADR for:
- Implementation details (what to name a variable)
- Obvious choices with no real alternatives
- Temporary decisions

### How To Write an ADR
Save to `decisions/NNN-short-name.md` where NNN is the next sequential number.

Format:
```
# ADR-NNN: Title

## Date
YYYY-MM-DD

## Status
Accepted | Superseded by ADR-NNN

## Context
What problem are we solving? What situation led to this decision?

## Decision
What did we decide?

## Reasoning
Why this option over the alternatives? Be specific.

## Alternatives Considered
What else did we evaluate and why did we reject it?

## Tradeoffs
What do we gain? What do we give up?

## Future Implications
How does this shape decisions we'll make later?
```

---

## Architecture Principles — Never Violate These

### 1. Context and Intelligence Are Separate
The `context/` folder contains the user's data. It has zero dependency on any LLM.
Apps and providers read from it — they never write to it directly without the user's input.

### 2. Platform Independence
No application code ever calls Claude, OpenAI, or Ollama directly.
All LLM calls go through `core/provider.py`. Switching providers = change one line in config.

### 3. One Source of Truth
Personal context lives in `context/` markdown files only.
No duplication across apps. If something changes about the user, it changes in one file.

### 4. Build To Understand, Not Just To Ship
the user wants to understand every decision while building.
Explain the why before writing code. If he doesn't understand something, stop and explain it.

---

## Project Structure

```
~/personal-os/
├── CLAUDE.md              ← you are here
├── context/               ← the user's data (markdown files, no LLM dependency)
│   ├── profile.md
│   ├── career.md
│   ├── finance.md
│   ├── health.md
│   ├── goals.md
│   ├── learning.md
│   └── mental_model.md
├── core/                  ← the engine
│   ├── context_loader.py  ← reads + assembles context files
│   ├── provider.py        ← LiteLLM wrapper (only place LLM is called)
│   └── memory.py          ← conversation history
├── apps/                  ← applications built on context
│   ├── assistant/         ← personal assistant (first)
│   ├── learning/          ← learning guide (second)
│   └── video_bridge/      ← connects to video studio (third)
├── config/
│   └── settings.yaml      ← active provider, model, API keys (never commit this)
└── decisions/             ← ADRs — one file per architectural decision
```

---

## At The Start of Every Session — Load Context
Before responding to anything, read these files in order:
1. `decisions/` — latest ADR to know where we left off
2. `context/profile.md` — who the user is
3. `context/goals.md` — what he's building toward
4. `context/career.md` — professional situation
5. `context/finance.md` — financial reality
6. `context/health.md` — current physical/mental state
7. `context/learning.md` — learning path and priorities
8. `context/mental_model.md` — how he thinks and decides

Do not skip this. The quality of every response depends on this context being loaded.

## Current Build State
Check the latest ADR in `decisions/` to know the current state of the project.

## Learning Sessions — How To Run One

When the user says "start a learning session" or "let's do learning" or "I want to study":

1. Read `context/roadmap.md` — this has the 12-module AI Architect roadmap and the exact scoring rubric for every topic
2. Read `data/learning_progress.json` — this has current module, current topic, and all scores so far
3. Tell him: current module, current topic, and whether the build task is done (ask if unsure)
4. Act as a Socratic guide — ask before explaining. Never open with a lecture.
5. When he says "test me" or asks to be scored: use the scoring rubric from roadmap.md for the current topic. Score all 3 dimensions (explain 40pts + build 30pts + apply 30pts). State the score clearly. Name the specific gap if below 80.
6. Do NOT mark a topic complete until score is 80/100. No exceptions.

The scoring questions for each topic are in `context/roadmap.md` under each module section. Use those exact questions — don't invent new ones.

When the session ends, ask if he wants to save a session note. If yes, update `data/learning_progress.json` — add to `session_notes` and update `last_session_date`. If a topic passed, add it to `completed_topics` and update the score in `scores`.

---

## the user's Preferences
- Explain decisions before writing code
- No unnecessary abstractions — build what's needed now, design for what's needed later
- Platform independent — LLM provider must be swappable
- Understand while building — if something is unclear, stop and clarify
