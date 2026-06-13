# ADR-003: Provider Layer Design

## Date
2026-06-13

## Status
Accepted

## Context
The personal-os needs to send context + user questions to an LLM and get answers.
The LLM provider must be swappable without changing any application code.
During development, no API keys are available — the system must be testable without cost.
This is the most critical architectural decision in the project after the context layer.

## Decision

### 1. Use LiteLLM as the underlying library
One Python library that speaks to Claude API, OpenAI, Ollama, Gemini, and 100+ others
with an identical interface. We wrap it in our own Provider class so apps never
import litellm directly — they only import our Provider.

### 2. Provider class with one primary method
```python
provider = Provider()
response = provider.chat(user_message, system_prompt)
```
That's the entire interface apps need. Everything else is internal.

### 3. Configuration via config/settings.yaml + environment variables
- settings.yaml: which provider is active, model names, base URLs
- Environment variables: API keys only — never in yaml, never in code
- Switching LLM = change `active_provider` in settings.yaml, nothing else

### 4. Mock provider for development
A built-in mock that returns a canned response without any API call.
Default active provider is `mock` — the system works out of the box with zero setup.
Upgrading to a real LLM = change one line in settings.yaml.

### 5. Support streaming as an option
`provider.chat(..., stream=True)` yields tokens one by one.
Default is non-streaming (simpler). Streaming is there when the UI needs it.

## Reasoning

**Why wrap LiteLLM instead of using it directly?**
If litellm ever changes its API or we want to add logging, caching, or retry logic,
we change one file (provider.py). Apps are never affected.
The wrapper costs 50 lines. The flexibility is permanent.

**Why YAML for config, not Python or JSON?**
YAML is readable and editable without knowing Python.
the user can switch providers by editing one line without opening code.
JSON is less readable for humans. Python config requires code changes.

**Why env vars for API keys?**
Keys in YAML get committed to git accidentally. Keys in env vars never do.
Industry standard. No exceptions.

**Why mock provider as default?**
The entire pipeline — context loading, prompt assembly, app logic — can be tested
without an API key or internet connection. Development doesn't cost money.
Real providers are opt-in by changing one line.

**Why keep streaming optional?**
For a CLI tool, streaming is nice but not required.
For a web interface (future), streaming is essential.
Making it optional now means it's ready when needed without complicating the core.

## Alternatives Considered

**Direct litellm calls in each app:**
Simpler in the short term. Rejected because every app would need to handle
provider configuration, API keys, error handling, and model strings independently.
One change (switch to Ollama) would require touching every app.

**LangChain instead of LiteLLM:**
LangChain does provider abstraction too. Rejected because it's 10x heavier,
has more magic, and is harder to understand. LiteLLM is transparent — you can
see exactly what it's doing. This project prioritizes understanding over convenience.

**Environment-only config (no YAML):**
Everything as env vars. Simpler in one sense — no YAML to parse.
Rejected because you'd need to set 10+ env vars every time you switch providers.
YAML gives a clear, editable view of the full configuration in one place.

## Tradeoffs
+ One line to switch providers — zero app code changes
+ Testable without API keys or internet (mock provider)
+ API keys are safe — never in code or yaml
+ Streaming ready when the UI needs it
- Adds a dependency (litellm) — if it breaks, we're affected
- YAML parsing adds a tiny amount of startup overhead (negligible)

## Future Implications
**Update 2026-06-13:** apps/assistant/ is now built and working. apps/learning/ is next.

The assistant uses Provider.chat() for single-turn and direct litellm for multi-turn history
(see ADR-004 for why, and the open seam that still exists there).

A cost-aware Router was also built on top of the provider layer (see ADR-005).
The Router wraps RoutedProvider which mirrors the Provider interface exactly —
apps that use routing don't need to know the difference.

The provider switching still works exactly as designed:
```yaml
# config/settings.yaml — change one line to switch
active_provider: ollama   # or gemini, claude_api, openai
```
