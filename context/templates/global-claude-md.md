# Global Claude Code Instructions — Setup Template

## What this file is
This is your global `~/.claude/CLAUDE.md` file. Claude Code loads it automatically
at the start of every session, in every project on your machine.

It tells Claude where your personal context lives and when to load it.

## How to set it up
1. Copy this file to `~/.claude/CLAUDE.md` on your machine
2. Update the paths if you cloned personal-os somewhere other than `~/personal-os/`
3. Fill in your context files in `~/personal-os/context/` (copy from `context/templates/`)

---

# Global Context — the user

## Personal Context
My full personal profile lives at `~/personal-os/context/`.
When I need life-aware advice (career, finance, health, learning, goals),
read these files before responding:

- `~/personal-os/context/profile.md`
- `~/personal-os/context/goals.md`
- `~/personal-os/context/career.md`
- `~/personal-os/context/finance.md`
- `~/personal-os/context/health.md`
- `~/personal-os/context/learning.md`
- `~/personal-os/context/mental_model.md`

## Memory — Always Load First
Before responding to any life-aware question, read all memory files in:
`~/.claude/projects/-Users-YOUR_USERNAME-personal-os/memory/`

Start with `MEMORY.md` (the index), then read each file listed there.
Memory contains decisions already made, live situations in progress, and context
that overrides or extends what is in the context files above.
Do not give advice that contradicts a settled memory decision.

## When To Load Personal Context
Load it when the question is about:
- Career decisions, promotion, job change
- Financial decisions, investments, independence
- Learning priorities, what to study next
- Health, stress, energy
- Life decisions of any kind

Do NOT load it for pure technical questions (fix this bug, write this function) —
it adds unnecessary context for work that doesn't need it.

## My Projects
- `~/personal-os/` — personal AI platform (this project)
