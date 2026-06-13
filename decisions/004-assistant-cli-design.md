# ADR-004: Personal Assistant CLI Design

## Date
2026-06-13

## Status
Accepted

## Context
With context_loader.py and provider.py working, the platform needs a usable interface.
The first app is a CLI personal assistant — a REPL where the user asks life questions
and gets context-aware answers. This is the integration point: context + provider → useful tool.

Three design questions:
1. How should conversation history be handled?
2. What's the right interface for a daily-use CLI tool?
3. Where does the system prompt get assembled?

## Decision

### 1. Multi-turn conversation history in memory (not on disk)
The CLI keeps a list of {"role": "user/assistant", "content": "..."} dicts in memory.
Each question sends the full history + new message to the LLM.
History clears on /clear or session exit. No persistence to disk yet.

### 2. Two modes: interactive REPL and --once single-shot
- Default: interactive session with a prompt loop
- `--once "question"`: single question, prints response, exits — for scripting or quick checks
- `--light` flag: load LIGHT context preset instead of FULL

### 3. Slash commands for in-session control
/help, /status, /light, /full, /clear, /quit
These let the user switch context depth mid-session without restarting.

### 4. System prompt assembled once per session (or on /light //full switch)
Loading all 7 context files on every message would be wasteful.
The system prompt is assembled at startup and reused. Rebuilt only if context preset changes.

### 5. Provider's chat() method bypassed for multi-turn (provider._provider_config accessed directly)
The existing Provider.chat() is designed for single-turn: system_prompt + one message.
Multi-turn requires sending the full history. The CLI calls litellm directly for real providers,
using the provider's config. Mock still goes through Provider.chat().
This is a known seam — ADR-005 will decide whether to extend Provider.chat() to accept history.

## Reasoning

**Why no disk persistence for history?**
The use case is daily conversational sessions, not a searchable archive.
Storing everything adds complexity without clear benefit right now.
If a conversation produces something worth keeping, the user saves it manually.
Revisit when the need is clear — not before.

**Why --once mode?**
Useful for scripting: `python -m apps.assistant.cli --once "what's my biggest financial risk"`
Also useful for testing during development. Costs nothing to support.

**Why FULL as default, not LIGHT?**
Life questions often need the full picture. The LLM handles 30KB of context fine.
LIGHT exists for speed when the question is simple — it's opt-in via --light or /light.

**Why slash commands instead of a menu?**
REPL tools with text commands are faster than navigating a menu.
Developers already know this pattern from git, vim, psql.
The set is small enough (/help covers it in 6 lines) that it's not a burden to learn.

## Alternatives Considered

**Persistent history to disk (append-only log or SQLite):**
More powerful — searchable, resumable across sessions.
Deferred: adds complexity and file management before the core use case is proven.
This is the right next step *after* the basic REPL is being used daily.

**Web UI instead of CLI:**
More accessible, better formatting, possible on mobile.
Rejected for now: adds a web server dependency before the core is validated.
The context files are on this laptop. The CLI is the fastest path to a working tool.
Web UI is phase 2 (see apps/ planned structure in CLAUDE.md).

**Extend Provider.chat() to accept history:**
Cleaner architecture — apps never touch litellm directly.
Deferred to ADR-005: it's the right decision but requires changing the provider interface,
which affects any future apps. Better to decide it deliberately rather than as a side effect
of building the assistant.

## Tradeoffs
+ Working multi-turn conversation in ~150 lines
+ Context-aware from session start (7 files, full personal profile)
+ Two modes cover 95% of use cases (interactive + scripting)
+ No new dependencies beyond what provider.py already requires
- Direct litellm access for multi-turn is a seam (Provider.chat() is still single-turn only)
- No history persistence — valuable conversations are ephemeral unless user saves them

## Future Implications
**Update 2026-06-13:** RoutedProvider.chat() now accepts a `history=[]` parameter,
so --route mode has full multi-turn conversation support. The seam in Provider.chat()
(single-turn only) still exists but is lower priority — the router handles most real use.

Provider.chat() history support is deferred until apps/learning/ has a clear need for it.
apps/learning/ will use the Router as its provider interface, not Provider directly.
