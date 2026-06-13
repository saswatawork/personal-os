# ADR-001: Architecture Foundation

## Date
2026-06-13

## Status
Accepted

## Context
the user wants to build a personal AI platform that:
- Knows him deeply across all life dimensions (career, finance, health, goals, etc.)
- Powers multiple applications: personal assistant, learning guide, video studio, future apps
- Works across devices (laptop, mobile, browser)
- Is not locked to any single AI provider
- Is designed to be understood while being built, not just shipped

The starting constraint: use Claude Code during development (no API costs), but
design so the system can upgrade to Claude API, OpenAI, Ollama, or any future provider
without changing application code.

---

## Decision 1: Standalone Directory at ~/personal-os/

### Decision
The platform lives at `~/personal-os/` — completely independent of any other project.

### Reasoning
The video studio, learning guide, and personal assistant all need the same personal context.
Tying this platform to any one project (like video-studio/) would make it a dependency
of that project rather than a foundation beneath all of them.

### Alternatives Considered
- **Inside video-studio/**: Rejected. Ties the platform's lifecycle to one project.
  When video-studio changes or is archived, the platform shouldn't be affected.
- **Cloud-only storage**: Rejected as the primary store. Adds external dependency,
  latency, and requires internet. Files on disk work offline and are portable.

### Tradeoffs
+ Independent lifecycle — survives any individual project
+ Any future project can connect to it without inheriting video-studio's context
- Requires its own git repo and maintenance discipline

---

## Decision 2: Markdown Files as the Context Layer

### Decision
Personal context is stored as markdown files in `context/`. One file per life dimension.
No database, no API, no LLM dependency in this layer.

### Reasoning
Markdown files are:
- Human-readable — the user can edit them directly without any tool
- Git-friendly — full history of how his context evolved over time
- Portable — readable on any device, in any editor, in any future system
- Simple — no schema migrations, no connection strings, no dependencies

Designed for upgrade: the file structure is clean enough that a SQLite index
can be generated from it later without changing the files themselves.

### Alternatives Considered
- **SQLite from the start**: Rejected for now. Queryable, but not human-readable
  or directly editable. Adds complexity before we know what queries we need.
- **JSON files**: Rejected. Less readable than markdown for prose-heavy personal context.
- **Notion / external tool**: Rejected. External dependency, not self-hosted, API changes.

### Tradeoffs
+ Zero dependencies — works with nothing but a text editor
+ Readable and editable by the user directly
+ Portable across any future system
- Not queryable without loading into memory
- Manual updates (no auto-sync from external sources yet)

---

## Decision 3: LiteLLM for Provider Abstraction

### Decision
All LLM calls go through `core/provider.py` which wraps LiteLLM.
No application code ever imports anthropic, openai, or any provider SDK directly.
Active provider is set in `config/settings.yaml`.

### Reasoning
the user explicitly wants provider independence. He may use:
- Claude Code (now, free, interactive)
- Claude API (when automating)
- Ollama (local, free, private)
- OpenAI (if cost/capability shifts)
- Future models we can't predict today

LiteLLM already solved this problem — one interface for 100+ providers.
Building a custom abstraction would mean maintaining it forever.

### Alternatives Considered
- **Custom abstraction layer**: Rejected. We'd be maintaining something LiteLLM
  already does better, with more providers and active maintenance.
- **LangChain**: Rejected. Does provider abstraction but is 10x heavier.
  More than needed for this project, harder to understand, more magic.
- **Lock to one provider**: Rejected by design requirement.

### Tradeoffs
+ Swap providers by changing one config line — zero code changes
+ 100+ providers supported including local Ollama
+ Actively maintained, not our problem to maintain
- Adds one dependency we don't control
- If LiteLLM breaks or changes API, we're affected (low risk — it's stable)

### Switching Provider (how it works)
```yaml
# config/settings.yaml
active_provider: ollama        # change this one line
model: llama3.2
base_url: http://localhost:11434
```

---

## Decision 4: No Compound Engineering Plugin

### Decision
We adopt the compound engineering *philosophy* but do not use the plugin.

### Reasoning
the user used and explored the compound engineering plugin and observed it consumes
disproportionate tokens for simple tasks. Analysis confirmed: the plugin has 37 skills
and 51 agents with fixed overhead per task, regardless of task complexity.

For a solo developer on a personal project, this overhead rarely pays back.
The philosophy (brainstorm → plan → execute → review → compound) is valuable.
The plugin's agent infrastructure is not.

Our lightweight equivalent:
- Brainstorm in conversation before building (5 min max)
- Write ADR before writing code
- Build against the agreed plan
- Review after each phase, update ADR if needed

### Tradeoffs
+ Full reasoning captured at fraction of token cost
+ the user understands every decision (no agent black boxes)
+ Sustainable for a long-running personal project
- Less structured than the plugin (requires discipline to follow)
- No automated enforcement — relies on CLAUDE.md instructions

---

## Decision 5: CLAUDE.md as Workflow Persistence

### Decision
The workflow, architecture principles, and project state are documented in
`~/personal-os/CLAUDE.md`. This file is read by Claude Code at the start of
every session automatically.

### Reasoning
Claude Code doesn't have persistent memory between sessions. The CLAUDE.md file
is the mechanism by which workflow, principles, and context survive session boundaries.
This is the same mechanism used in the video-studio project successfully.

### Tradeoffs
+ Workflow is never lost between sessions
+ Claude Code follows it automatically — no reminding needed
+ Full decision history in decisions/ gives any new session complete context
- Requires keeping CLAUDE.md updated as the project evolves
- Only works in Claude Code sessions (not claude.ai browser or mobile)

---

## Future Implications
These five decisions define the foundation. Every subsequent decision should:
1. Respect provider independence (never couple app code to a specific LLM)
2. Keep context/ as pure data (no LLM dependencies in that layer)
3. Be documented in an ADR before implementation
4. Prioritize the user understanding over speed of delivery
