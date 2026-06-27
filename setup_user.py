"""
personal-os setup script — run once after cloning.

    python setup_user.py

What it does:
  1. Copies context templates → context/ (skips files that already exist)
  2. Generates ~/.claude/CLAUDE.md with correct paths for this machine
  3. Runs pip install -e .
  4. Tells you what still needs manual attention
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
CONTEXT_DIR = PROJECT_ROOT / "context"
TEMPLATES_DIR = CONTEXT_DIR / "templates"
CLAUDE_DIR = Path.home() / ".claude"
GLOBAL_CLAUDE_MD = CLAUDE_DIR / "CLAUDE.md"

CONTEXT_TEMPLATES = [
    "profile.md",
    "goals.md",
    "career.md",
    "finance.md",
    "health.md",
    "learning.md",
    "mental_model.md",
]


def step(msg: str) -> None:
    print(f"\n  → {msg}")


def ok(msg: str) -> None:
    print(f"    ✓ {msg}")


def skip(msg: str) -> None:
    print(f"    – {msg} (already exists, skipped)")


def warn(msg: str) -> None:
    print(f"    ! {msg}")


def copy_context_templates() -> list[str]:
    """Copy templates to context/. Returns list of files still needing content."""
    step("Copying context templates")
    needs_filling: list[str] = []

    for filename in CONTEXT_TEMPLATES:
        src = TEMPLATES_DIR / filename
        dst = CONTEXT_DIR / filename

        if not src.exists():
            warn(f"Template not found: {src} — skipping")
            continue

        if dst.exists():
            skip(filename)
        else:
            dst.write_text(src.read_text())
            ok(f"Copied {filename}")
            needs_filling.append(filename)

    return needs_filling


def _build_memory_path() -> str:
    """Derive the Claude memory path from the project's absolute location."""
    # Claude stores memory at ~/.claude/projects/<path-with-slashes-as-dashes>/memory/
    # e.g. /Users/alice/personal-os → -Users-alice-personal-os
    return str(PROJECT_ROOT).replace("/", "-")


def generate_global_claude_md() -> bool:
    """
    Generate ~/.claude/CLAUDE.md with paths correct for this machine.
    Returns True if written, False if skipped.
    """
    step("Setting up ~/.claude/CLAUDE.md")

    context_path = PROJECT_ROOT / "context"
    memory_path = f"~/.claude/projects/{_build_memory_path()}/memory/"

    content = f"""# Global Claude Code Instructions

## Personal Context
My full personal profile lives at `{context_path}`.
When I need life-aware advice (career, finance, health, learning, goals),
read these files before responding:

- `{context_path}/profile.md`
- `{context_path}/goals.md`
- `{context_path}/career.md`
- `{context_path}/finance.md`
- `{context_path}/health.md`
- `{context_path}/learning.md`
- `{context_path}/mental_model.md`

## Memory — Always Load First
Before responding to any life-aware question, read all memory files in:
`{memory_path}`

Start with `MEMORY.md` (the index), then read each file listed there.
Memory contains decisions already made, live situations in progress, and context
that overrides or extends what is in the context files above.
Do not give advice that contradicts a settled memory decision.

## When To Load Personal Context
Load it when the question is about:
- Career decisions, promotion, job change
- Financial decisions, investments, independence
- Learning priorities, what to study next
- Health, stress, energy
- Life decisions of any kind

Do NOT load it for pure technical questions (fix this bug, write this function) —
it adds unnecessary context for work that doesn't need it.

## My Projects
- `{PROJECT_ROOT}` — personal AI platform (this project)
"""

    if GLOBAL_CLAUDE_MD.exists():
        answer = input(
            f"    ~/.claude/CLAUDE.md already exists. Overwrite? [y/N]: "
        ).strip().lower()
        if answer != "y":
            skip("~/.claude/CLAUDE.md")
            return False

    CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
    GLOBAL_CLAUDE_MD.write_text(content)
    ok(f"Written to {GLOBAL_CLAUDE_MD}")
    ok(f"Memory path: {memory_path}")
    return True


def install_package() -> bool:
    """Run pip install -e . Returns True on success."""
    step("Installing package (pip install -e .)")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", ".", "--quiet"],
        cwd=PROJECT_ROOT,
    )
    if result.returncode == 0:
        ok("Package installed")
        return True
    else:
        warn("pip install failed — run manually: pip install -e .")
        return False


def print_summary(needs_filling: list[str]) -> None:
    print("\n" + "─" * 60)
    print("  Setup complete.\n")

    if needs_filling:
        print("  Still to do — fill in your personal context:")
        for f in needs_filling:
            print(f"    • context/{f}")
        print()
        print("  Open each file and replace the placeholder content")
        print("  with your own information. Be honest — this is what")
        print("  Claude uses to give you relevant advice.")
    else:
        print("  All context files already exist.")
        print("  If they still have placeholder content, fill them in.")

    print()
    print("  Then open this project in Claude Code and start working.")
    print("─" * 60 + "\n")


def main() -> None:
    print("\npersonal-os setup")
    print("─" * 60)
    print(f"  Project: {PROJECT_ROOT}")

    needs_filling = copy_context_templates()
    generate_global_claude_md()
    install_package()
    print_summary(needs_filling)


if __name__ == "__main__":
    main()
