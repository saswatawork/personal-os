# ADR-010: CLAUDE.md as Constitution + Session Skills Architecture

## Date
2026-06-27

## Status
Accepted

## Context
CLAUDE.md had grown to 218 lines mixing three different concerns:
- Permanent rules (architecture principles, ADR workflow) — always relevant
- Session-specific instructions (job prep, learning, Python coding) — relevant only some of the time
- Reference documentation (Python standards detail) — better consulted on demand

Every Claude Code session loaded all of it regardless of what work was being done.
A job prep session loaded Python standards noise. A Python coding session loaded
learning guide instructions. The more the project grows, the worse this gets.

A second problem: Python standards were written as passive reference ("follow these")
rather than active constraints ("verify before you write"). This meant they informed
but didn't enforce.

## Decision
Split CLAUDE.md into two layers:

**Layer 1 — Constitution (`CLAUDE.md`):** ~70 lines of permanent, always-on rules.
Architecture principles, ADR workflow, project structure, and a skills index.
This never grows. Adding a new session type does not touch this file.

**Layer 2 — Skills (`.claude/commands/`):** One file per session type, loaded on demand
by invoking the skill at the start of a session.

| Skill | File | Purpose |
|---|---|---|
| `/py-start` | `.claude/commands/py-start.md` | Python coding mode — standards as active constraints |
| `/job-prep` | `.claude/commands/job-prep.md` | Job search session mode |
| `/learn` | `.claude/commands/learn.md` | Socratic learning guide mode |

## Reasoning
- Session-specific context should be loaded when that session starts, not on every session
- Python standards are more effective as a pre-write checklist than as a reference section
- CLAUDE.md growing with the project is a smell — the constitution should be stable
- New session types (e.g. video-bridge work, finance review) get a new skill file, not a longer CLAUDE.md

## Alternatives Considered

**Do nothing** — standards were already in CLAUDE.md. Rejected: the noise problem gets
worse as the project grows, not better.

**Tighten CLAUDE.md only, no skills** — rewrite the standards section to be more
forceful without creating skills. Rejected: still loads job prep instructions during
Python sessions and vice versa. Doesn't solve the context noise problem.

**Single giant skill** — one `/start` skill that loads everything. Rejected: same
noise problem in a different file.

## Tradeoffs

Gained:
- CLAUDE.md is stable — adding apps or session types doesn't require editing it
- Each session has focused context — no irrelevant instructions in scope
- Python standards are now active constraints, not passive reference
- Skills are independently evolvable — update `/py-start` without touching the constitution

Given up:
- One more thing to remember (run `/py-start` at the start of a coding session)
- Skills index in CLAUDE.md can go stale if a skill is added without updating it

## Future Implications
- New apps (video_bridge, finance) should get their own skill if they have session-specific
  behaviour (e.g. `/video-start` for video pipeline work)
- If the skills index in CLAUDE.md becomes the wrong place for discovery, consider a
  `README.md` in `.claude/commands/` instead
- Python standards in `/py-start` should be the single source of truth — don't let
  them drift back into CLAUDE.md
