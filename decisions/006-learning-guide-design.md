# ADR-006: Learning Guide App Design

## Date
2026-06-13

## Status
Accepted

## Context
The context/learning.md file defines a 9-module curriculum with 16-18 hours/week available.
The assistant CLI (apps/assistant/) handles life questions well, but it doesn't know which
module the user is on, what was covered last session, or how to guide depth-first learning.

The core problem the learning guide solves:
- The assistant gives reactive answers. The learning guide gives structured progression.
- Without explicit tracking, the "depth gap" (builds without understanding why) persists.
- Without session continuity, every session starts from scratch — no forward momentum.

Three design questions:
1. Where does curriculum state live (current module, what's been explained, what's next)?
2. What interaction model fits the "don't move until you can explain it" rule?
3. Which provider/model handles it, and does it need personal context?

## Decision

### 1. Curriculum state in data/learning_progress.json (separated from context/)
context/learning.md defines the curriculum and learning philosophy — who the user is
as a learner. It is identity, not state.

data/learning_progress.json tracks where he is today:
- current_module (1-9, maps to curriculum modules in learning.md)
- completed_topics (list of topic slugs that passed the "explain it" test)
- session_notes (last N session summaries — what was covered, what was stuck on)
- last_session_date

This separation means context/ stays stable (the curriculum doesn't change often)
while data/ changes every session. Git diffs on data/ show learning progress over time.

### 2. Two interaction modes: /guide (structured) and /ask (open)
The learning guide has two modes in a single REPL:

**/guide** — structured session flow
The app asks the first question. the user answers. The guide probes depth with follow-up
questions (Feynman technique). When depth is confirmed, marks the topic complete
and recommends the next. No forward movement until the current thing is explained.

**/ask** — open questions
For when the user wants to ask something specific ("explain context windows") without
going through the full guided session. Same session, same history — just different
entry point.

Default is /guide at session start. Session opens with:
"Last time we were on [module] — [topic]. You want to continue or shift?"

### 3. Use Router (Gemini 2.5 Flash for strong tier) — LIGHT context preset
Learning questions are complex by nature. The router will always classify them
as "strong" tier → Gemini 2.5 Flash.

The learning guide loads LIGHT context (profile + goals + mental_model) — not FULL.
Reason: learning sessions need to know who the user is and what he's working toward,
but they don't need finance or health context. The curriculum itself is loaded as a
separate context block appended to the system prompt.

The system prompt stack:
  1. LIGHT personal context (profile + goals + mental_model)
  2. Curriculum context (context/learning.md injected directly)
  3. Current progress (current module, last session summary from progress.json)
  4. Learning guide persona: Socratic, not explanatory. Ask before telling.

### 4. Progress saved to disk after each session (on /done or /quit)
In-session history stays in memory (same as assistant CLI).
On session end (/done or /quit), the app writes a session summary to progress.json:
- Updates last_session_date
- Prompts the user to confirm which topics he can now explain
- Saves a 1-2 sentence session summary (LLM-generated) to session_notes

This is the only point where disk write happens — not after every message.

### 5. /test mode — the "explain it" verification gate
/test triggers the Feynman check. The guide asks the user to explain the current topic
in plain words. The LLM evaluates the explanation and either:
- Confirms understanding → marks topic complete, moves forward
- Identifies the gap → asks one targeted question to fill it

The /test gate is how the "one rule" is enforced programmatically.

## Reasoning

**Why separate data/ from context/?**
context/ files are edited by hand to reflect who the user is. data/ files are written by
apps to track runtime state. Mixing them means context files accumulate session noise
that makes them harder to maintain. The separation is also visible in git — learning
progress shows up as data/ changes, curriculum updates show up as context/ changes.

**Why LIGHT context instead of FULL?**
A learning session about LLM token economics doesn't benefit from knowing the user's
home loan EMI. LIGHT is faster and focuses the model on the relevant slice.
The curriculum itself replaces what FULL would add — it's more specific than a general
profile section would be.

**Why Socratic persona, not explanatory?**
The depth gap is precisely that explanations are absorbed passively without real
understanding forming. A guide that explains things is a better textbook, not a better
learning partner. A Socratic guide forces active recall — "you tell me how it works"
is what makes understanding durable. This is the mechanism behind the "one rule."

**Why save on /done not on every message?**
Disk writes per message add complexity for no benefit. A session is one unit of work.
The summary on /done is intentional — the user decides what stuck, not the app.
This also means if a session gets interrupted before /done, no partial state is written.

**Why a separate learning guide instead of extending the assistant?**
The assistant is a reactive Q&A tool — you ask, it answers. The learning guide is
proactive — it drives the session, tracks state, enforces the gate. Different interaction
model, different system prompt, different state requirements. Sharing a codebase but
keeping them as separate apps under apps/ maintains the distinction.

## Alternatives Considered

**Single assistant app with /learn mode:**
Simpler — one app, not two. Rejected because the assistant's REPL and the guide's
session structure would need to share too much state, and the system prompts are
different enough that the same prompt would be a compromise for both.

**Progress tracking in context/learning.md directly:**
Simplest possible state — just edit the file to mark things complete.
Rejected because it mixes curriculum definition with runtime state. Also: the app
can't write to context/ files without risking corrupting the curriculum structure.
A JSON file in data/ is a cleaner write target for an app.

**Anki-style flashcard mode:**
Spaced repetition for retention. More powerful than Feynman checks for long-term memory.
Deferred: adds significant complexity (card scheduling, review queues) before the basic
session flow is proven. Can be added as /review mode in a future iteration.

**Persistent conversation history across sessions:**
Resume a conversation from where it left off — not just progress state, but the full
message history. Technically interesting but not the constraint. The constraint is
depth, not continuity of conversation. Progress state (what module, what's done) is
enough to restart productively. Full history persistence is deferred to core/memory.py.

## Tradeoffs
+ Socratic interaction model enforces the "one rule" programmatically
+ Progress state persists across sessions — learning has forward momentum
+ Gemini 2.5 Flash on strong tier gives genuine reasoning ability for Feynman checks
+ Clean separation from assistant app — different interaction model, different state
+ data/learning_progress.json is human-readable and git-trackable
- LIGHT context means finance/health not available during learning sessions (acceptable)
- Progress written only on /done — interrupted sessions lose that session's progress
- No spaced repetition — Feynman gate is binary (understood / not understood)

## Future Implications
When core/memory.py is built, the session_notes in progress.json can migrate to the
memory layer — making the learning guide's history available to the assistant as well.
("What did I learn last week?" asked in the assistant would draw from memory.)

MCP server for personal-os (Tier 2 curriculum item, ADR-007 when ready) will likely
expose /test and progress state as tools — so the guide can be invoked from Claude Code
directly without opening a separate REPL.
