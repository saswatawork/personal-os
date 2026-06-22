# ADR-008: Personal Data Stays Local — Never in Git

## Date
2026-06-23

## Status
Accepted

## Context
The original repo committed personal context files (`context/*.md`) and learning
progress (`data/`) directly to git. This included financial details, health data,
career situation, and goals — all pushed to GitHub.

Two problems surfaced:
1. Even a private repo can be accidentally made public, forked, or leaked.
2. The project needs to be usable by other people. Hardcoding one person's life
   data into the repo makes it impossible to share or clone cleanly.

Additionally, `core/context_loader.py` and `apps/learning/cli.py` had the owner's
name hardcoded in system prompts, making the code non-generic.

## Decision

**Personal data never enters git.** The boundary is strict:

- `context/*.md` — gitignored. Lives on the user's machine only.
- `data/` — gitignored. Learning progress, session notes, local only.
- `resume.md`, `resume.pdf` — gitignored.
- `context/templates/` — committed. Blank question-driven versions of every
  context file. New users copy these, fill them in locally.

System prompts in code use `"the user"` generically — never a hardcoded name.
The context files themselves tell the AI who they are advising.

Git history was rewritten (`git-filter-repo --replace-text`) to remove the name
from all historical commits, and force-pushed to the remote.

## Reasoning

**Local-first is the right default for personal data.**
The context files contain financial numbers, health state, and career frustrations.
That data has no reason to leave the machine. The AI reads it locally. No cloud
storage is needed for this to work.

**Templates solve the multi-user problem without any architecture change.**
A new user clones the repo, copies templates, fills them in locally. Their data
never touches the remote. Same pattern whether it's Saswata, Writuparna, or anyone else.

**Generic code is better code.**
Hardcoding a name in a system prompt is a bug, not a feature. The context files
already identify the user to the AI — the system prompt doesn't need to repeat it.

## Alternatives Considered

**Encrypt context files and commit them:**
Rejected. Adds key management complexity. The files are not useful to anyone
without the key, but the risk of mismanaging the key is real. Local-only is simpler
and strictly safer.

**Store personal data in a database (SQLite, etc.):**
Rejected for now. Markdown files are human-readable, directly editable, and work
with the existing ContextLoader without any change. A database adds complexity
for no gain at this stage. Revisit if the data model becomes relational.

**Separate repo for personal data:**
Rejected. Adds friction. A gitignore rule achieves the same isolation without
requiring the user to manage two repositories.

## Tradeoffs

**Gain:**
- Personal data is fully local — no exposure risk from git or GitHub
- Repo is clean and shareable — anyone can clone and fill in their own context
- System prompts are generic — apps work for any user without code changes

**Give up:**
- Context files are not version-controlled — no history of how the profile changed
- No automatic backup — user is responsible for backing up their `context/` directory
- Cloud sync (future feature) requires a separate mechanism — git is no longer the transport

## Future Implications
- Cloud sync of context files will need a separate encrypted store (not git)
- Any new app or feature that needs personal data must read from `context/` locally
- New users need to know to copy from `context/templates/` — this is documented in README.md
