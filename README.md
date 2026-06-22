# personal-os

A personal AI platform that knows who you are and gives advice accordingly.

You fill in your own context — career, finances, goals, health, learning path — and the system uses it to answer questions, guide decisions, and run structured learning sessions. All your data stays on your machine. Nothing is pushed to git or sent to a cloud storage service.

Built for a single user at a time. You own your data.

---

## What It Does

**Personal Assistant** — ask questions about your career, finances, learning, or life decisions. The assistant reads your context files before every response, so advice is grounded in your actual situation, not generic.

**Learning Guide** — a Socratic session manager for working through a structured curriculum. It asks before it tells. It scores your understanding. It doesn't let you move forward until you can explain the current thing.

**Provider flexibility** — runs on a local Ollama model (free, fully private), or any cloud provider (Claude, OpenAI, Gemini). Switch with one line in `config/settings.yaml`.

---

## Requirements

- Python 3.10+
- For local models: [Ollama](https://ollama.com) installed and running
- For cloud models: API key for Anthropic, OpenAI, or Google

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/saswatawork/personal-os.git
cd personal-os
```

### 2. Install dependencies

```bash
pip install pyyaml litellm
```

### 3. Fill in your context

Your personal context lives in `context/`. These files are gitignored — they stay on your machine only.

Copy the templates and fill them in:

```bash
cp context/templates/profile.md context/profile.md
cp context/templates/career.md context/career.md
cp context/templates/finance.md context/finance.md
cp context/templates/goals.md context/goals.md
cp context/templates/health.md context/health.md
cp context/templates/learning.md context/learning.md
cp context/templates/mental_model.md context/mental_model.md
```

Open each file and replace the bracketed prompts with your own information. The more honestly you fill these in, the more useful the system becomes. You do not need to fill in every field — start with `profile.md` and `goals.md` and add more over time.

### 4. Set up your AI provider

Open `config/settings.yaml` and set `active_provider` to one of: `ollama`, `claude_api`, `openai`, `gemini`, or `mock`.

**Option A — Local model (free, fully private, no API key needed)**

Install Ollama from [ollama.com](https://ollama.com), then pull a model:

```bash
ollama pull llama3.2        # 2GB, fast
ollama pull qwen2.5:7b      # 4.7GB, better reasoning
```

Set in `config/settings.yaml`:
```yaml
active_provider: ollama
```

**Option B — Claude (recommended for quality)**

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

Set in `config/settings.yaml`:
```yaml
active_provider: claude_api
```

**Option C — OpenAI**

```bash
export OPENAI_API_KEY=sk-...
```

```yaml
active_provider: openai
```

**Option D — Gemini**

```bash
export GEMINI_API_KEY=...
```

```yaml
active_provider: gemini
```

**Option E — Mock (no API key, for testing)**

```yaml
active_provider: mock
```

Returns a canned response. Use this to verify the setup is wired correctly before connecting a real provider.

### 5. Verify the setup

```bash
python -m apps.assistant.cli --once "What are my main goals right now?"
```

If it responds with something grounded in your context files, the setup is complete.

---

## Using the Personal Assistant

```bash
# Interactive session
python -m apps.assistant.cli

# Single question, no REPL
python -m apps.assistant.cli --once "Should I leave my job this year?"

# Auto-route each question to the cheapest model that can handle it
python -m apps.assistant.cli --route

# Light context (faster, uses fewer tokens)
python -m apps.assistant.cli --light
```

**Session commands:**

| Command | What it does |
|---|---|
| `/help` | Show available commands |
| `/status` | Show active provider and context loaded |
| `/light` | Switch to light context for this session |
| `/full` | Switch to full context for this session |
| `/quit` | Exit |

---

## Using the Learning Guide

The learning guide runs structured Socratic sessions through a curriculum you define in `context/roadmap.md`. It tracks your progress in `data/learning_progress.json` (gitignored — local only).

### Set up your roadmap

```bash
cp context/templates/roadmap.md context/roadmap.md
```

Edit `context/roadmap.md` to define your learning destination and the modules that get you there. The template has the full structure with scoring criteria.

Create the data directory and a blank progress file:

```bash
mkdir -p data
echo '{
  "current_module": 1,
  "current_topic": 0,
  "completed_topics": [],
  "scores": {},
  "session_notes": [],
  "last_session_date": null
}' > data/learning_progress.json
```

### Run a session

```bash
# Start a guided session (picks up where you left off)
python -m apps.learning.cli

# Check progress without starting a session
python -m apps.learning.cli --status

# Jump to a specific module
python -m apps.learning.cli --module 3
```

**Session commands:**

| Command | What it does |
|---|---|
| `/guide` | Return to guided session flow |
| `/ask` | Free Q&A — ask anything without session structure |
| `/test` | Feynman check — explain the current topic back; guide scores your understanding |
| `/complete` | Mark current topic as understood, advance to next |
| `/status` | Show current module, topic, and progress |
| `/note` | Add a manual note about this session |
| `/done` | Save session summary and exit |
| `/quit` | Exit without saving |

The guide won't let you mark a topic complete without a score of 80/100 on the `/test` check.

---

## Switching AI Providers

Change one line in `config/settings.yaml`:

```yaml
active_provider: ollama      # local, free, private
# active_provider: claude_api  # best quality, costs money
# active_provider: openai      # alternative cloud
# active_provider: gemini      # Google, has a free tier
```

Nothing else changes. All apps use this setting automatically.

---

## Project Structure

```
personal-os/
├── context/               ← your personal data (gitignored, stays local)
│   ├── profile.md
│   ├── career.md
│   ├── finance.md
│   ├── goals.md
│   ├── health.md
│   ├── learning.md
│   ├── mental_model.md
│   ├── roadmap.md
│   └── templates/         ← blank versions to copy from (committed to git)
├── core/
│   ├── context_loader.py  ← reads and assembles your context files
│   ├── provider.py        ← single place all LLM calls go through
│   └── router.py          ← cost-aware routing across model tiers
├── apps/
│   ├── assistant/         ← personal assistant CLI
│   └── learning/          ← learning guide CLI
├── data/                  ← progress tracking (gitignored, stays local)
│   └── learning_progress.json
├── config/
│   └── settings.yaml      ← active provider and model config
└── decisions/             ← architecture decision records
```

---

## Privacy

Your context files and learning data never leave your machine unless you explicitly push them. The `.gitignore` blocks `context/*.md` and `data/` from being committed.

If you use a cloud AI provider (Claude, OpenAI, Gemini), your context is sent to that provider's API as part of the prompt — that is the nature of how LLMs work. If full privacy is required, use `active_provider: ollama` and your data never leaves your machine at all.

---

## Adding More Apps

The platform is designed for extension. Any new app follows the same pattern:

1. Create `apps/your_app/cli.py`
2. Import `ContextLoader` to read context files
3. Import `Provider` or `Router` to call the LLM
4. Your personal data is automatically available — no setup needed in the new app

See `apps/assistant/cli.py` for a minimal working example.
