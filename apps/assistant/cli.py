"""
Personal assistant CLI.

Usage:
    python -m apps.assistant.cli                          # interactive, provider from settings.yaml
    python -m apps.assistant.cli --route                  # auto-routes each question to cheapest model
    python -m apps.assistant.cli --light                  # LIGHT context preset
    python -m apps.assistant.cli --once "your question"   # single question, no REPL
    python -m apps.assistant.cli --route --once "..."     # single question with auto-routing

With --route, simple questions use llama3.2 (fast/free), complex questions use qwen2.5:7b
or a cloud model. The tier is shown before each response.
"""

import argparse
import sys

from core.context_loader import FULL, LIGHT, ContextLoader
from core.provider import Provider, ProviderError, ProviderProtocol
from core.router import Router

HELP_TEXT = """
Commands:
  /help       Show this help
  /status     Show active provider and context loaded
  /light      Switch to LIGHT context for this session
  /full       Switch to FULL context for this session
  /clear      Clear conversation history
  /quit       Exit
"""

SEPARATOR = "─" * 60


def build_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Personal AI assistant — knows you from context/*.md"
    )
    parser.add_argument(
        "--light",
        action="store_true",
        help="Use LIGHT context preset (profile + goals + mental_model)",
    )
    parser.add_argument(
        "--once",
        metavar="QUESTION",
        help="Ask a single question and exit (non-interactive)",
    )
    parser.add_argument(
        "--route",
        action="store_true",
        help="Auto-route each question to cheapest capable model (cost optimization)",
    )
    return parser.parse_args()


def run_once(
    provider: ProviderProtocol,
    loader: ContextLoader,
    context_preset: list[str],
    question: str,
) -> None:
    system_prompt = loader.as_system_prompt(context_preset)
    try:
        response = provider.chat(question, system_prompt)
        print(response)
    except ProviderError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def run_interactive(
    provider: ProviderProtocol,
    loader: ContextLoader,
    context_preset: list[str],
    use_routing: bool = False,
) -> None:
    preset_name = "FULL" if context_preset is FULL else "LIGHT"
    history: list[dict[str, str]] = []

    print(SEPARATOR)
    print("  Personal Assistant")
    print(f"  Provider: {provider.active_provider}  |  Model: {provider.active_model}")
    print(f"  Context: {preset_name}")
    print("  Type /help for commands, /quit to exit")
    print(SEPARATOR)
    print()

    system_prompt = loader.as_system_prompt(context_preset)

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            cmd = user_input.lower()
            if cmd in ("/quit", "/exit", "/q"):
                print("Goodbye.")
                break
            elif cmd == "/help":
                print(HELP_TEXT)
            elif cmd == "/status":
                print(f"Provider: {provider.active_provider} | Model: {provider.active_model}")
                print(f"Context: {preset_name} ({len(loader.load(context_preset))} sections)")
                print(f"History: {len(history) // 2} exchanges")
            elif cmd == "/clear":
                history.clear()
                print("History cleared.")
            elif cmd == "/light":
                context_preset = LIGHT
                preset_name = "LIGHT"
                system_prompt = loader.as_system_prompt(context_preset)
                print("Switched to LIGHT context (profile + goals + mental_model).")
            elif cmd == "/full":
                context_preset = FULL
                preset_name = "FULL"
                system_prompt = loader.as_system_prompt(context_preset)
                print("Switched to FULL context (all 7 sections).")
            else:
                print(f"Unknown command: {user_input}. Type /help for available commands.")
            print()
            continue

        try:
            if use_routing:
                router = Router()
                tier, routed = router.route_with_tier(user_input)
                print(f"[routing → {tier}: {routed.active_model}]")
                response = routed.chat(user_input, system_prompt, history=history)
            else:
                response = provider.chat(user_input, system_prompt, history=history)
        except (ProviderError, RuntimeError) as e:
            print(f"\nError: {e}\n")
            continue

        print(f"\nAssistant: {response}\n")

        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": str(response)})


def main() -> None:
    args = build_args()
    context_preset = LIGHT if args.light else FULL

    try:
        loader = ContextLoader()
        if args.route:
            router = Router()
            tier, provider = router.route_with_tier(args.once or "")
            if args.once:
                print(f"[routing → {tier}: {provider.active_model}]")
        else:
            provider: ProviderProtocol = Provider()
    except (ProviderError, Exception) as e:
        print(f"Startup error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.once:
        run_once(provider, loader, context_preset, args.once)
    else:
        run_interactive(provider, loader, context_preset, use_routing=args.route)


if __name__ == "__main__":
    main()
