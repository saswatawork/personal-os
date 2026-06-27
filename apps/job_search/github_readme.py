"""
GitHub Profile README Auto-Updater

Reads personal context, generates a profile README using the LLM,
and pushes it to your GitHub profile repo (username/username).

Usage:
    python -m apps.job_search.github_readme
    python -m apps.job_search.github_readme --dry-run   # preview without pushing
    python -m apps.job_search.github_readme --repo saswatapal/saswatapal

Requirements:
    pip install PyGithub
    export GITHUB_TOKEN=ghp_your_token_here
"""

import argparse
import os
import subprocess
import sys

from core.context_loader import ContextLoader
from core.provider import ProviderError
from core.router import Router

CONTEXT_FILES = ["profile", "career", "goals"]

# Sentinel question — complex enough to route to the strongest available model.
_ROUTING_SIGNAL = "generate my github profile readme based on my career goals and context"

README_PROMPT = """
You are writing a GitHub profile README for the person described in the context above.

This README will be the first thing recruiters, hiring managers, and engineers see when
they visit the profile. It needs to be clear, honest, and easy to read quickly.

Rules for writing this README:
- Write in simple, plain English. No buzzwords, no jargon.
- If you use a technical term, explain it in one short phrase after it.
- Every sentence should be something a non-engineer could understand.
- Don't list skills like a resume. Explain what you actually build and why.
- Don't use phrases like "passionate about", "leverage", "synergy", "cutting-edge".
- Be specific. "I built a system that runs 4 YouTube channels automatically" beats
  "I work with AI and automation".
- Reason about what matters most from the context. Don't dump everything — pick the
  3-4 things that best represent who this person is and where they're going.
- Tone: direct, calm, confident. Not salesy, not humble-braggy.

Structure to follow (use these exact markdown headers):

## Who I am
2-3 sentences. What they do, how long they've been doing it, what makes them different.
Focus on the combination of skills that's unusual — frontend engineering + AI pipeline
architecture is rare. Name that.

## What I'm building
2-3 things they're actively working on. Link to repos if they exist.
For each: one line on what it is, one line on the interesting problem it solves.
Keep it concrete. No fluff.

## What I'm learning
1-2 sentences. What they're deepening right now and why.
This shows forward motion — hiring managers want to see someone who keeps growing.

## What I'm looking for
1 paragraph. What kind of work, team, and problem space they want to be in.
This is the signal for the right recruiter to reach out. Be specific enough to
filter — vague = no inbound.

---

Generate the README now. Return only the markdown. No preamble, no explanation.
"""


def generate_readme(loader: ContextLoader) -> str:
    system_prompt = loader.as_system_prompt(CONTEXT_FILES)
    print("Generating README via LLM...")

    # Prefer the claude CLI (no API key needed when running inside Claude Code).
    try:
        return _generate_via_claude_cli(system_prompt)
    except Exception as e:
        print(f"[claude-cli] failed: {e} — falling back to configured provider...")

    # Fallback: use whatever provider is configured in settings.yaml.
    router = Router()
    _, provider = router.route_with_tier(_ROUTING_SIGNAL)
    print(f"Trying: {provider.status()}")
    try:
        return str(provider.chat(README_PROMPT, system_prompt=system_prompt)).strip()
    except Exception as e:
        raise RuntimeError(f"All providers failed: {e}") from e


def _generate_via_claude_cli(system_prompt: str) -> str:
    full_prompt = f"{system_prompt}\n\n{README_PROMPT}"
    print("Generating via claude CLI...")
    result = subprocess.run(
        ["claude", "-p", full_prompt],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "claude CLI returned non-zero exit code")
    return result.stdout.strip()


def push_to_github(content: str, repo_name: str) -> None:
    try:
        from github import Github, GithubException
    except ImportError:
        print("ERROR: PyGithub not installed. Run: pip install PyGithub")
        sys.exit(1)

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN environment variable not set.")
        print("Create a token at https://github.com/settings/tokens")
        print("Required scope: repo (or public_repo for public repos)")
        sys.exit(1)

    from github import Auth
    g = Github(auth=Auth.Token(token))

    try:
        repo = g.get_repo(repo_name)
    except GithubException as e:
        print(f"ERROR: Could not access repo '{repo_name}': {e}")
        print("Make sure the repo exists and your token has access to it.")
        sys.exit(1)

    try:
        existing = repo.get_contents("README.md")
        repo.update_file(
            path="README.md",
            message="docs: auto-update profile README from personal context",
            content=content,
            sha=existing.sha,
        )
        print(f"Updated README.md in {repo_name}")
    except GithubException:
        repo.create_file(
            path="README.md",
            message="docs: create profile README from personal context",
            content=content,
        )
        print(f"Created README.md in {repo_name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate and push GitHub profile README")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate and print README without pushing to GitHub",
    )
    parser.add_argument(
        "--repo",
        default=None,
        help="GitHub repo to push to (default: inferred from GITHUB_TOKEN)",
    )
    args = parser.parse_args()

    loader = ContextLoader()
    print(f"Loading context: {', '.join(CONTEXT_FILES)}")
    print()

    try:
        readme = generate_readme(loader)
    except (ProviderError, RuntimeError) as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print(readme)
    print("=" * 60 + "\n")

    if args.dry_run:
        print("Dry run — not pushing to GitHub.")
        return

    repo_name = args.repo
    if not repo_name:
        try:
            from github import Github, Auth
            token = os.getenv("GITHUB_TOKEN")
            if token:
                g = Github(auth=Auth.Token(token))
                username = g.get_user().login
                repo_name = f"{username}/{username}"
                print(f"Inferred profile repo: {repo_name}")
            else:
                print("Set GITHUB_TOKEN or pass --repo username/username")
                sys.exit(1)
        except Exception as e:
            print(f"Could not infer repo: {e}")
            print("Pass --repo username/username explicitly.")
            sys.exit(1)

    push_to_github(readme, repo_name)
    print(f"\nDone. View at: https://github.com/{repo_name.split('/')[0]}")


if __name__ == "__main__":
    main()
