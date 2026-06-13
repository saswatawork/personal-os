# ADR-005: Cost-Aware Model Routing

## Date
2026-06-13

## Status
Accepted

## Context
The personal assistant runs on a local Ollama setup with no API costs today.
But as usage grows — or when cloud models are added for quality — routing every
question to the strongest model is wasteful. A "status" question doesn't need
qwen2.5:7b. A career decision does. The system should pick the cheapest model
that can handle each question well, automatically.

This also teaches the AI Architect skill directly: cost governance via intelligent
model selection is exactly what the user wants to build for engineering teams at scale.
The personal-os is the proof of concept.

## Decision

### 1. Three complexity tiers
- **fast** — short/simple questions → llama3.2 (2GB, near-instant)
- **local** — context-aware advice, default → qwen2.5:7b (4.7GB, good reasoning)
- **strong** — deep career/finance decisions → qwen2.5:7b now, cloud model later

### 2. Keyword-based classifier (no LLM call for routing)
Routing is done by pattern matching on the question — no API call, no latency, no cost.
Classifies in microseconds before any LLM call is made.

Life/career/finance keywords → strong tier.
Simple factual patterns + short word count → fast tier.
Everything else → local (safe default).

### 3. Router maps tiers to providers from config
`routing:` section in settings.yaml maps each tier to a provider+model.
Swapping the "strong" tier from ollama to claude_api = edit one line in yaml.
No code changes.

### 4. RoutedProvider mirrors Provider interface exactly
Apps that use the router get back a RoutedProvider with the same .chat() method.
They don't need to know a router was involved.

### 5. --route flag in CLI (opt-in, not default)
Default behavior: use fixed active_provider from settings.yaml (predictable).
--route flag: enable auto-routing (optimized).
This way the user can always force a specific model if the routing is wrong.

## Reasoning

**Why keyword classification instead of a lightweight LLM classifier?**
Using an LLM to decide which LLM to call adds latency and cost — defeats the purpose.
Keywords are fast, transparent, and debuggable. The `router.explain(question)` method
shows exactly why a routing decision was made. If the classification is wrong,
you add a keyword — not retrain a model.

**Why three tiers and not two (fast/slow)?**
Three tiers gives a natural slot for "local default" which is the right answer
for most questions — good quality, free, no internet needed. Two tiers (fast/strong)
would push medium questions to the expensive model unnecessarily.

**Why put routing config in settings.yaml?**
The same reason provider config lives there: one place to change behavior without
touching code. Upgrading the strong tier to Claude API when a key is available
= two lines in yaml. No Python edits.

## Cost Model (why this matters)

| Tier | Model | Cost per query | Quality |
|---|---|---|---|
| fast | llama3.2 | $0 (local) | Good for simple |
| local | qwen2.5:7b | $0 (local) | Good for advice |
| strong (now) | qwen2.5:7b | $0 (local) | Best local available |
| strong (future) | claude-haiku | ~$0.001 | Best quality |
| strong (future) | claude-sonnet | ~$0.01 | Overkill for most |

At scale (engineering team using this pattern):
- Routing 80% of queries to fast/local models = 80% cost reduction with no quality loss
- Only deep architecture decisions go to the expensive model
- This is exactly what AI cost governance looks like in practice

## Alternatives Considered

**Always use the strongest model:**
Simplest. Rejected because cost compounds. At 100 queries/day, even cheap cloud
models add up. Local models for routine queries is the correct default.

**Vector similarity to classify questions:**
Semantically smarter than keywords. Rejected for now — adds a vector DB dependency
for marginal gain over keywords at this question volume. Revisit at 1000+ queries/day.

**Let the user pick tier manually:**
More control but more friction. The router should make the right call automatically.
Manual override exists via settings.yaml or by disabling --route.

## Tradeoffs
+ Zero cost for 100% of current usage (all local models)
+ Routing decision is transparent and debuggable (explain() method)
+ Upgrading strong tier to cloud = one yaml edit, no code change
+ Teaches AI cost governance pattern directly (applicable to teams at scale)
- Keyword classifier will misroute edge cases (solvable by adding keywords)
- No conversation history in routed mode yet (each question re-routed independently)

## Future Implications
When personal-os serves multiple apps (assistant, learning, video_bridge),
each app can declare its default tier. The learning app always uses local.
The career advisor uses strong. The video bridge uses fast for metadata, strong for scripts.
The routing config in settings.yaml scales to this naturally.
