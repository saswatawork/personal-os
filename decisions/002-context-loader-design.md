# ADR-002: Context Loader Design

## Date
2026-06-13

## Status
Accepted

## Context
The context/ directory has 7 markdown files representing the user's personal profile
across all life dimensions. The context_loader.py module needs to make these files
usable by any app in the system — personal assistant, learning guide, video bridge.

The core question: what does "loading context" actually mean for an LLM-powered app?
It means assembling the right files into a system prompt string that gets sent to
the LLM before the user's question. The LLM then answers knowing the user's full context.

## Decision
Build a ContextLoader class with three capabilities:
1. Load individual or all context files into a Python dict
2. Assemble loaded files into a formatted system prompt string
3. Support named presets (FULL, LIGHT) for different use cases

## Reasoning

**Why a class, not functions?**
The loader needs to know where context files live (the context_dir path).
A class holds that state cleanly. Functions would require passing the path every time.

**Why both dict and string output?**
- Dict: for apps that want to inspect, filter, or modify context programmatically
- String: for direct injection into LLM system prompts — the most common use case
- Both from the same loaded data — no duplication

**Why presets (FULL vs LIGHT)?**
Not every question needs all 7 files. Loading all context for "what's 2+2" wastes tokens.
Presets let apps choose the right level of context without thinking about which files.
- LIGHT: profile + goals + mental_model — who he is and where he's going (always relevant)
- FULL: all 7 files — for deep life advice

**Why keep it simple (no chunking, no vector search)?**
7 markdown files, total size ~20-30KB. Well within any LLM context window.
Chunking and vector search add complexity without benefit at this scale.
If files grow significantly, upgrade then — not now.

## Alternatives Considered

**Flat function approach (load_context(path) → string):**
Simpler but inflexible. Can't selectively load files without rewriting the function.
Rejected in favor of the class approach.

**JSON instead of markdown for context files:**
More structured, easier to parse programmatically.
Rejected because markdown is human-readable and directly editable — the user
can update context files without any tooling. Human editability is more important
than machine parseability at this stage.

**Vector database for semantic retrieval:**
Load only the most relevant context chunks based on the question.
Overengineered for 7 files. Revisit when context grows beyond a single context window.

## Tradeoffs
+ Simple — easy to understand, easy to modify
+ Works with the markdown files as-is — no migration needed
+ Presets make it easy to use correctly from any app
- No semantic filtering — always loads whole files
- If context files grow very large, will need to add compression/summarization

## Future Implications
When we build apps/assistant/ and apps/learning/, they import ContextLoader
and call as_system_prompt() — that's the only interface they need.
If we later add vector search or compression, only context_loader.py changes.
App code stays the same. This is why the abstraction is worth having.
