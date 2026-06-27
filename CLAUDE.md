# personal-os — Claude Code Instructions

## What This Project Is
A personal AI platform — one source of truth about who the user is, what they're building,
and where they're going. Applications are built on top of it: personal assistant, learning
guide, video studio bridge, and future apps.

This is not a work project. It is infrastructure for a life.

## Every Session — Follow This First
1. Read the most recent ADR in `decisions/` to know where we left off
2. Ask what we're working on today if it's not clear
3. Do NOT start building until we've done a brief brainstorm

## Before Building Anything New — ADR Workflow
1. **Brainstorm** — discuss the problem first (5 minutes max)
2. **Decide** — agree on the approach
3. **Write the ADR** — document BEFORE writing code
4. **Build** — execute against the agreed plan
5. **Review** — check if the ADR needs updating after each phase

### When To Write an ADR
- Affects architecture or project structure
- Involves a real choice between two or more options
- Future-you would want to understand the reasoning

### ADR Format
Save to `decisions/NNN-short-name.md`:
- Date, Status, Context, Decision, Reasoning, Alternatives Considered, Tradeoffs, Future Implications

---

## Architecture Principles — Never Violate

1. **Context and intelligence are separate** — `context/` has zero LLM dependency.
   Apps read from it; nothing writes to it without the user's explicit input.

2. **Platform independence** — no app ever calls an LLM directly.
   All LLM calls go through `core/provider.py`. Switching providers = one line in config.

3. **One source of truth** — personal context lives in `context/` only.
   No duplication across apps.

4. **Build to understand** — explain the why before writing code.
   If something is unclear, stop and clarify before proceeding.

---

## Project Structure

```
~/personal-os/
├── CLAUDE.md              ← you are here
├── context/               ← personal data (markdown, no LLM dependency)
├── core/                  ← the engine (provider, context_loader, memory)
├── apps/                  ← applications built on context
│   ├── assistant/
│   ├── learning/
│   ├── job_search/
│   └── video_bridge/
├── config/settings.yaml   ← provider + API keys (never commit)
├── decisions/             ← ADRs
└── .claude/commands/      ← session skills (see below)
```

---

## Skills — Run These to Start Each Session

| Command     | When to use                               |
|-------------|-------------------------------------------|
| `/py-start` | Before writing or editing any Python code |
| `/job-prep` | Job search and interview prep sessions    |
| `/learn`    | AI Architect curriculum sessions          |

---

## Preferences
- Explain decisions before writing code
- No unnecessary abstractions — build what's needed now
- Platform independent — LLM provider must always be swappable
- If something is unclear, stop and ask before writing
