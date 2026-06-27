from pathlib import Path

# Presets — which files to load for different use cases
LIGHT: list[str] = ["profile", "goals", "mental_model"]
FULL:  list[str] = ["profile", "goals", "career", "finance", "health", "learning", "mental_model"]


class ContextLoader:
    """
    Reads personal context files and assembles them into LLM-ready system prompts.
    Context files live in context/ as markdown — one file per life dimension.
    """

    def __init__(self, context_dir: Path | str | None = None) -> None:
        if context_dir is None:
            context_dir = Path(__file__).parent.parent / "context"
        self.context_dir = Path(context_dir)

    def load(self, files: list[str] | None = None) -> dict[str, str]:
        """
        Load context files into a dict keyed by section name.

        Args:
            files: names without extension e.g. ["profile", "goals"].
                   Defaults to FULL if not provided.

        Returns:
            {"profile": "...content...", "goals": "...content...", ...}
            Missing files are silently skipped — context grows over time.
        """
        if files is None:
            files = FULL

        result: dict[str, str] = {}
        for name in files:
            path = self.context_dir / f"{name}.md"
            if path.exists():
                result[name] = path.read_text(encoding="utf-8").strip()
        return result

    def as_system_prompt(self, files: list[str] | None = None) -> str:
        """Assemble context files into a single system prompt string for LLM injection."""
        sections = self.load(files)

        if not sections:
            return "No personal context available."

        parts = [
            "You are a personal advisor to the user.",
            "Below is their full personal context. Use it to give specific, grounded advice.",
            "Speak directly to them — not to a generic person, to them specifically.",
            "",
        ]
        for name, content in sections.items():
            header = name.replace("_", " ").title()
            parts.append(f"## {header}")
            parts.append(content)
            parts.append("")

        return "\n".join(parts)

    def summary(self) -> str:
        """One-line summary of available context files — useful for debugging."""
        available = [f.stem for f in sorted(self.context_dir.glob("*.md"))]
        return f"Context files available: {', '.join(available)}"


if __name__ == "__main__":
    loader = ContextLoader()

    print(loader.summary())
    print("\n--- LIGHT context (profile + goals + mental_model) ---\n")
    print(loader.as_system_prompt(LIGHT))
    print("\n--- FULL context ---\n")
    print(loader.as_system_prompt(FULL))
