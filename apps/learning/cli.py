"""
Learning guide CLI — Socratic session manager for the 9-module curriculum.

Usage:
    python -m apps.learning.cli               # guided session, picks up where you left off
    python -m apps.learning.cli --status      # show progress without starting a session
    python -m apps.learning.cli --module 3    # jump to a specific module

Modes (slash commands during session):
    /guide      Return to guided session flow (default)
    /ask        Ask anything freely (open Q&A, no session structure)
    /test       Feynman check — explain current topic back; guide verifies depth
    /complete   Mark current topic as understood, move to next
    /status     Show current module/topic/progress
    /note       Add a manual note about this session
    /done       Save session summary and exit
    /quit       Exit without saving session progress

The guide is Socratic: it asks before it tells. /test enforces the one rule:
don't move forward until you can explain the current thing.
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.context_loader import ContextLoader, LIGHT
from core.router import Router
from apps.learning.progress import Progress

SEPARATOR = "─" * 60

HELP_TEXT = """
Commands:
  /guide      Guided session — the guide drives (default mode)
  /ask        Free Q&A — ask anything without session structure
  /test       Feynman check — explain current topic back to the guide
  /complete   Mark current topic as understood, advance to next
  /status     Show module/topic/progress
  /note       Add a session note manually
  /done       Save session summary and exit
  /quit       Exit without saving
  /help       Show this help
"""

LEARNING_GUIDE_PERSONA = """
You are a Socratic learning guide for the user, a senior frontend engineer (12 years)
moving toward an AI Architect role. You know his curriculum, his progress, and how he learns.

Your job is NOT to explain things. Your job is to ask questions that reveal whether he
understands the current topic, and to fill only the specific gap you find.

Rules:
1. Ask before you tell. Never open with a lecture. Open with a question.
2. If he can explain it correctly, confirm it and move on. Don't pad.
3. If his explanation has a gap, ask exactly one follow-up question targeting that gap.
4. When he gets it right, say so clearly. Ambiguity about whether he passed is frustrating.
5. Keep answers short when he's got it right. Go longer only when there's a real gap.
6. Use concrete examples tied to his actual work: video-studio, personal-os, Cimpress bootcamp.
7. Never say "great question" or "excellent". Just engage with the content.

The one rule he's committed to: don't move to the next topic until he can explain
the current one. You enforce this by asking, not by gatekeeping with words.
"""


def build_system_prompt(loader: ContextLoader, progress: Progress) -> str:
    light_context = loader.as_system_prompt(LIGHT)

    with open(Path(__file__).parent.parent.parent / "context" / "learning.md") as f:
        curriculum = f.read()

    roadmap_path = Path(__file__).parent.parent.parent / "context" / "roadmap.md"
    roadmap = roadmap_path.read_text() if roadmap_path.exists() else ""

    topic = progress.current_topic or progress.next_topic() or "all topics in current module"
    topic_display = topic.replace("_", " ") if topic else "all topics"
    last_note = progress.session_notes[-1]["summary"] if progress.session_notes else "No previous sessions."

    progress_block = f"""
Current learning state:
- Module {progress.current_module}: {progress.module_name()}
- Current topic: {topic_display}
- Topics completed: {', '.join(progress.completed_topics) or 'none yet'}
- Last session: {progress.last_session_date or 'first session'}
- Last session note: {last_note}
"""

    parts = [
        LEARNING_GUIDE_PERSONA,
        "## Personal Context\n" + light_context,
        "## Curriculum\n" + curriculum,
        "## Progress\n" + progress_block,
    ]
    if roadmap:
        parts.append("## AI Architect Roadmap (Scoring Rubric)\n" + roadmap)
    return "\n\n".join(parts)


def opening_message(progress: Progress) -> str:
    topic = progress.current_topic or progress.next_topic()
    topic_display = topic.replace("_", " ") if topic else None
    module_name = progress.module_name()

    if progress.last_session_date:
        note = progress.session_notes[-1]["summary"] if progress.session_notes else ""
        base = f"Last session was {progress.last_session_date}."
        if note:
            base += f" You noted: \"{note}\""
        if topic_display:
            return f"{base}\n\nWe're on Module {progress.current_module} ({module_name}), topic: {topic_display}.\n\nWant to continue, or is there something specific you want to work through today?"
        else:
            return f"{base}\n\nAll topics in Module {progress.current_module} are done. Ready to move to Module {progress.current_module + 1}?"
    else:
        return (
            f"First session. Starting Module {progress.current_module}: {module_name}.\n\n"
            f"{'Current topic: ' + topic_display + chr(10) + chr(10) if topic_display else ''}"
            "Before I explain anything — tell me what you already know about this topic. "
            "Even rough is fine. What have you heard or read?"
        )


def generate_session_summary(routed_provider, system_prompt: str, history: list) -> str:
    if not history:
        return "Session had no exchanges."
    summary_request = (
        "In 1-2 sentences, summarize what was covered and learned in this session. "
        "Focus on what the user demonstrated understanding of, or what gap was identified. "
        "Be specific — name the topic and the insight or gap. No filler."
    )
    try:
        return routed_provider.chat(summary_request, system_prompt, history=history)
    except Exception:
        return "Session completed — summary unavailable."


def run_feynman_test(routed_provider, system_prompt: str, history: list, progress: Progress) -> list:
    topic = progress.current_topic or progress.next_topic()
    topic_display = topic.replace("_", " ") if topic else "current topic"
    prompt = (
        f"Feynman check on: {topic_display}.\n\n"
        "Ask the user to explain this topic in plain words, as if to a smart non-technical person. "
        "Listen to his answer. Then either: confirm genuine understanding and say so clearly, "
        "or identify the single most important gap and ask one targeted question about it. "
        "Do not explain the topic yourself yet."
    )
    print(f"\nGuide: ", end="", flush=True)
    try:
        response = routed_provider.chat(prompt, system_prompt, history=history)
        print(response)
    except Exception as e:
        print(f"Error: {e}")
        return history
    history.append({"role": "user", "content": f"[/test — Feynman check on {topic_display}]"})
    history.append({"role": "assistant", "content": response})
    return history


def build_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Learning guide — Socratic sessions for your curriculum")
    parser.add_argument("--status", action="store_true", help="Show progress and exit")
    parser.add_argument("--module", type=int, metavar="N", help="Jump to module N")
    return parser.parse_args()


def main() -> None:
    args = build_args()
    progress = Progress()

    if args.status:
        print(progress.status_summary())
        return

    if args.module:
        modules = progress._data.get("modules", {})
        if str(args.module) not in modules:
            print(f"Module {args.module} not found. Available: {', '.join(modules.keys())}")
            sys.exit(1)
        progress._data["current_module"] = args.module
        topics = progress.module_topics(args.module)
        progress._data["current_topic"] = topics[0] if topics else None
        print(f"Jumped to Module {args.module}: {progress.module_name(args.module)}")

    try:
        loader = ContextLoader()
    except Exception as e:
        print(f"Failed to load context: {e}", file=sys.stderr)
        sys.exit(1)

    system_prompt = build_system_prompt(loader, progress)

    router = Router()
    # Learning questions are always complex — use strong tier directly
    _, routed = router.route_with_tier("should I learn this topic in depth for my career")

    history: list = []
    mode = "guide"

    print(SEPARATOR)
    print(f"  Learning Guide")
    print(f"  Module {progress.current_module}: {progress.module_name()}")
    print(f"  Model: {routed.active_model}")
    print(f"  Type /help for commands")
    print(SEPARATOR)
    print()

    opening = opening_message(progress)
    print(f"Guide: {opening}\n")
    history.append({"role": "assistant", "content": opening})

    while True:
        try:
            label = f"[{mode}] You" if mode != "guide" else "You"
            user_input = input(f"{label}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting without saving.")
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            cmd = user_input.lower().split()[0]

            if cmd in ("/quit", "/exit", "/q"):
                print("Exiting without saving session progress.")
                break

            elif cmd == "/done":
                print("\nGenerating session summary...")
                summary = generate_session_summary(routed, system_prompt, history)
                print(f"Summary: {summary}")
                confirm = input("Save this summary? [Y/n]: ").strip().lower()
                if confirm != "n":
                    progress.add_session_note(summary)
                    progress.save()
                    print("Session saved.")
                else:
                    print("Not saved.")
                break

            elif cmd == "/help":
                print(HELP_TEXT)

            elif cmd == "/status":
                print(progress.status_summary())

            elif cmd == "/guide":
                mode = "guide"
                print("Guide mode — I'll drive the session.")

            elif cmd == "/ask":
                mode = "ask"
                print("Ask mode — open Q&A. Type /guide to return to structured session.")

            elif cmd == "/test":
                history = run_feynman_test(routed, system_prompt, history, progress)

            elif cmd == "/complete":
                topic = progress.current_topic or progress.next_topic()
                if not topic:
                    print("No current topic to mark complete.")
                else:
                    progress.mark_topic_complete(topic)
                    next_t = progress.next_topic()
                    if next_t:
                        print(f"Marked '{topic.replace('_', ' ')}' complete.")
                        print(f"Next topic: {next_t.replace('_', ' ')}")
                    elif progress.all_module_topics_done():
                        print(f"All topics in Module {progress.current_module} done.")
                        if progress.advance_module():
                            print(f"Moved to Module {progress.current_module}: {progress.module_name()}")
                        else:
                            print("Curriculum complete.")

            elif cmd == "/note":
                note_text = user_input[len("/note"):].strip()
                if not note_text:
                    note_text = input("Note: ").strip()
                if note_text:
                    progress.add_session_note(note_text)
                    progress.save()
                    print("Note saved.")

            else:
                print(f"Unknown command: {user_input}. Type /help.")

            print()
            continue

        # Regular message
        if mode == "guide":
            # In guide mode, prepend a soft instruction so the LLM stays Socratic
            guided_input = user_input
        else:
            guided_input = user_input

        try:
            response = routed.chat(guided_input, system_prompt, history=history)
        except Exception as e:
            print(f"\nError: {e}\n")
            continue

        print(f"\nGuide: {response}\n")
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    main()
