# ADR-011: User Onboarding Setup Script

## Date
2026-06-27

## Status
Accepted

## Context
New users cloning personal-os faced 5 manual steps to get a working setup:
1. Clone the repo
2. Copy context templates to context/ manually
3. Locate their machine username, edit a path in global-claude-md.md, copy it to ~/.claude/CLAUDE.md
4. Run pip install -e .
5. Open in Claude Code

Steps 2–4 are error-prone. Step 3 in particular requires the user to know the exact
memory path format (`-Users-USERNAME-personal-os`) and edit it correctly. A wrong path
means personal context silently never loads — no error, just a worse experience.

## Decision
A single Python script `setup_user.py` at the project root handles steps 2–4
automatically. Onboarding becomes:

1. Clone personal-os
2. `python setup_user.py`
3. Fill in your context files (script tells you which ones and what to put in them)

## Reasoning
- Username and memory path are derivable from the machine — no manual editing needed
- Template copying is mechanical — a script does it more reliably than a human
- pip install is a single subprocess call
- Idempotent: safe to run multiple times — never overwrites filled-in context files
- Python is already the project language — no new tooling required

## Alternatives Considered

**Makefile (`make setup`)** — shell-based alternative. Rejected: less portable across
macOS/Linux/Windows, harder to detect username and build paths correctly.

**README-only** — just document the steps clearly. Rejected: documentation reduces
errors but doesn't eliminate them. The path editing step is still manual and fragile.

**Interactive CLI that fills in context files** — ask the user questions and write
their answers into context files. Rejected: too much scope. Context files need
thoughtful personal writing, not form-filling. Script handles mechanics; human handles content.

## Tradeoffs

Gained:
- One command replaces four manual steps
- Memory path is generated correctly every time — no silent misconfiguration
- Idempotent — safe to re-run after pulling updates

Given up:
- One more file to maintain at the project root
- Script touches ~/.claude/ on the user's machine — needs to handle the case where
  ~/.claude/CLAUDE.md already exists without silently overwriting it

## Future Implications
- If new setup steps are added (e.g. config/settings.yaml template), they go in this script
- Script should remain the single source of truth for "how to set up personal-os"
- README should reference this script, not duplicate its steps
