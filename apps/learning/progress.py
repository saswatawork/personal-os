"""
Learning progress tracker — reads and writes data/learning_progress.json.

Keeps module/topic state separate from the curriculum definition in context/learning.md.
State is written only at session end (/done or /quit) — not after every message.
"""

import json
from datetime import date
from pathlib import Path
from typing import Optional, List

PROGRESS_PATH = Path(__file__).parent.parent.parent / "data" / "learning_progress.json"


class Progress:
    def __init__(self, path: Path = PROGRESS_PATH):
        self._path = path
        self._data = self._load()

    def _load(self) -> dict:
        if self._path.exists():
            with open(self._path) as f:
                return json.load(f)
        return {"current_module": 1, "current_topic": None, "completed_topics": [], "session_notes": [], "last_session_date": None, "modules": {}}

    def save(self) -> None:
        with open(self._path, "w") as f:
            json.dump(self._data, f, indent=2)

    @property
    def current_module(self) -> int:
        return self._data.get("current_module", 1)

    @property
    def current_topic(self) -> Optional[str]:
        return self._data.get("current_topic")

    @property
    def completed_topics(self) -> List[str]:
        return self._data.get("completed_topics", [])

    @property
    def last_session_date(self) -> Optional[str]:
        return self._data.get("last_session_date")

    @property
    def session_notes(self) -> list:
        return self._data.get("session_notes", [])

    def module_name(self, module_num: Optional[int] = None) -> str:
        n = str(module_num or self.current_module)
        modules = self._data.get("modules", {})
        return modules.get(n, {}).get("name", f"Module {n}")

    def module_topics(self, module_num: Optional[int] = None) -> list:
        n = str(module_num or self.current_module)
        modules = self._data.get("modules", {})
        return modules.get(n, {}).get("topics", [])

    def next_topic(self) -> Optional[str]:
        """Return the next uncompleted topic in the current module."""
        topics = self.module_topics()
        done = set(self.completed_topics)
        for t in topics:
            if t not in done:
                return t
        return None

    def all_module_topics_done(self) -> bool:
        topics = set(self.module_topics())
        done = set(self.completed_topics)
        return topics.issubset(done)

    def mark_topic_complete(self, topic: str) -> None:
        if topic not in self._data["completed_topics"]:
            self._data["completed_topics"].append(topic)
        next_t = self.next_topic()
        self._data["current_topic"] = next_t

    def advance_module(self) -> bool:
        """Move to the next module. Returns False if already at last module."""
        modules = self._data.get("modules", {})
        next_module = self.current_module + 1
        if str(next_module) not in modules:
            return False
        self._data["current_module"] = next_module
        self._data["current_topic"] = self.module_topics(next_module)[0] if self.module_topics(next_module) else None
        return True

    def add_session_note(self, summary: str) -> None:
        notes = self._data.setdefault("session_notes", [])
        notes.append({"date": str(date.today()), "summary": summary})
        if len(notes) > 10:
            notes.pop(0)
        self._data["last_session_date"] = str(date.today())

    def status_summary(self) -> str:
        topic = self.current_topic or self.next_topic() or "all done"
        topic_display = topic.replace("_", " ") if topic else "all done"
        module_display = self.module_name()
        completed_count = len(self.completed_topics)
        last = self.last_session_date or "never"
        lines = [
            f"Module {self.current_module}: {module_display}",
            f"Current topic: {topic_display}",
            f"Topics completed: {completed_count}",
            f"Last session: {last}",
        ]
        if self.session_notes:
            lines.append(f"Last note: {self.session_notes[-1]['summary']}")
        return "\n".join(lines)
