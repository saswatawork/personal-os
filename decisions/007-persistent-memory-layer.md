# ADR-007: Persistent Memory Layer for Cross-Session Context

## Date
2026-06-15

## Status
Accepted

## Context
The personal-os platform holds the user's static context in `context/` markdown files —
profile, career, finance, goals, health, learning, mental model. These files capture
who he is and what he's building toward.

But they do not capture decisions already made, live situations in progress, or
context that changes faster than the files are updated. As conversations happen,
significant decisions get made — Bangalore relocation plan, wife's employment situation,
Kolkata flat locked — that should not need to be re-explained in every future session.

Without a memory layer, every session starts cold. The AI gives advice that may
contradict settled decisions or miss critical live context. That is not an intelligent system.

## Decision
Add a file-based memory layer at:
`~/.claude/projects/-Users-saswatapal-personal-os/memory/`

Structure:
- `MEMORY.md` — index file, always auto-loaded, one line per memory pointing to its file
- Individual memory files — one per topic, with frontmatter (name, description, type)

Memory types: user, feedback, project, reference.

Auto-load instruction added to `~/.claude/CLAUDE.md` so memory is read before
any life-aware response — no manual prompting required.

## Reasoning
The context files answer "who is the user." Memory answers "what has been decided."
These are different layers. Context is relatively stable. Memory is dynamic.

Keeping them separate maintains the architecture principle: one source of truth per
type of information. Context files are not polluted with transient decisions.
Memory files are not burdened with static profile data.

Auto-loading from CLAUDE.md makes the system intelligent by default — the user
does not manage the AI's awareness, the system manages it.

## Alternatives Considered

**Update context files directly with decisions:**
Rejected. Context files capture who the user is, not what was decided last Tuesday.
Mixing these creates files that are hard to maintain and reason about.

**Manual memory loading per session:**
Rejected. Requires the user to manage the AI's awareness explicitly. That is not
an intelligent system — it is a manual system with extra steps.

**No memory — rely on conversation context alone:**
Rejected. Conversation context resets every session. Critical live decisions
(wife's employment deadline, Bangalore move trigger conditions) would need
re-explaining every time. High friction, high error surface.

## Tradeoffs

**Gain:**
- Settled decisions are known without re-explanation
- Advice does not contradict prior decisions
- System gets more useful over time as memory accumulates
- User can talk to the AI as a continuous collaborator, not a stateless service

**Give up:**
- Memory files can go stale — require occasional review and cleanup
- More files to maintain in the memory directory
- Risk of acting on outdated memory if not verified against current reality

## Future Implications
- Memory should be reviewed periodically — stale decisions removed or updated
- As the platform grows, memory categories may expand
- The memory layer is the foundation for the personal-os becoming a genuine
  persistent AI collaborator rather than a session-scoped assistant
