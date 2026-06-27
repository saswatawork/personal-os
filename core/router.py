"""
Cost-aware model router.

Routes each question to the cheapest model that can handle it well.
Routing is based on question complexity — no API call needed to decide.

Tiers (cheapest to most capable):
  fast   → ollama/llama3.2       — quick factual, status, simple queries
  local  → ollama/qwen2.5:7b    — context-aware advice, default local
  strong → ollama/qwen2.5:14b   — deep reasoning (if pulled)
  cloud  → gemini/gemini-2.0-flash-lite or claude_api (if key set)

Usage:
    router = Router()
    provider = router.route("What is my biggest career risk?")
    response = provider.chat(question, system_prompt)

Or to see which tier was selected:
    tier, provider = router.route_with_tier(question)
    print(f"Using tier: {tier}")
"""

import logging
import os
import re
from pathlib import Path
from typing import Any, Generator

import yaml

from core.provider import ProviderError, check_api_key, build_messages, stream_tokens

log = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent.parent / "config" / "settings.yaml"

# Words that signal a complex question — matched on whole words only.
_COMPLEX_SIGNALS: list[str] = [
    "career", "promotion", "salary", "job", "resign", "leave", "hire",
    "invest", "financial", "money", "loan", "emi", "corpus", "sip",
    "should i", "what should", "help me decide", "advice",
    "risk", "strategy", "plan", "roadmap", "how do i",
    "health", "stress", "sleep", "family", "daughter",
    "goal", "future", "next year", "long term",
]

# Words that signal a simple question — fast model is fine.
_SIMPLE_SIGNALS: list[str] = [
    "what is", "define", "explain", "how does", "status", "list",
    "show me", "what are", "tell me about", "summarize",
]

# Pre-compiled patterns to avoid re-compiling on every classify() call.
_COMPLEX_RE = [re.compile(r"\b" + re.escape(s) + r"\b") for s in _COMPLEX_SIGNALS]
_SIMPLE_RE  = [re.compile(r"\b" + re.escape(s) + r"\b") for s in _SIMPLE_SIGNALS]


def classify(question: str) -> str:
    """
    Classify a question into a complexity tier.

    Returns: "fast" | "local" | "strong"
    """
    q = question.lower().strip()
    word_count = len(q.split())

    if word_count <= 5:
        return "fast"

    complex_hits = sum(1 for pattern in _COMPLEX_RE if pattern.search(q))
    simple_hits  = sum(1 for pattern in _SIMPLE_RE  if pattern.search(q))

    if complex_hits >= 2:
        return "strong"
    if complex_hits >= 1:
        return "local"
    if simple_hits >= 1 and word_count < 15:
        return "fast"

    return "local"


class RouterConfig:
    """Reads provider config and maps tiers to providers."""

    def __init__(self, config_path: Path = CONFIG_PATH) -> None:
        if not config_path.exists():
            raise ProviderError(f"Config file not found: {config_path}")
        with open(config_path) as f:
            self._config: dict[str, Any] = yaml.safe_load(f)
        self._providers: dict[str, Any] = self._config.get("providers", {})
        self._routing: dict[str, Any] = self._config.get("routing", self._default_routing())

    def _default_routing(self) -> dict[str, Any]:
        """Fallback routing when no [routing] section exists in settings.yaml."""
        return {
            "fast":   {"provider": "ollama", "model": "ollama/llama3.2"},
            "local":  {"provider": "ollama", "model": "ollama/qwen2.5:7b"},
            "strong": {"provider": "ollama", "model": "ollama/qwen2.5:7b"},
        }

    def get(self, tier: str) -> dict[str, Any]:
        return self._routing.get(tier, self._routing["local"])

    def provider_config(self, provider_name: str) -> dict[str, Any]:
        return self._providers.get(provider_name, {})


class Router:
    """
    Routes a question to the right provider based on complexity.

    Returns a RoutedProvider configured for the selected tier, so it can be
    used as a drop-in replacement for Provider.
    """

    def __init__(self, config_path: Path = CONFIG_PATH) -> None:
        self._rc = RouterConfig(config_path)

    def route(self, question: str) -> "RoutedProvider":
        """Return a configured RoutedProvider for the right tier."""
        _, provider = self.route_with_tier(question)
        return provider

    def route_with_tier(self, question: str) -> tuple[str, "RoutedProvider"]:
        """
        Return (tier_name, provider).

        Falls back to the local tier if the strong tier needs a cloud key that
        isn't set — avoids crashing mid-session.
        """
        tier = classify(question)
        routing = self._rc.get(tier)
        provider_name = routing["provider"]
        model = routing["model"]

        if tier == "strong" and not _key_available(provider_name):
            fallback = self._rc.get("local")
            log.warning(
                "No API key for '%s' — falling back to local: %s",
                provider_name,
                fallback["model"],
            )
            provider_name = fallback["provider"]
            model = fallback["model"]
            tier = "local (fallback)"

        provider_config = self._rc.provider_config(provider_name)
        return tier, RoutedProvider(
            provider_name=provider_name,
            model=model,
            provider_config=provider_config,
        )

    def explain(self, question: str) -> str:
        """Return a human-readable routing decision — useful for debugging."""
        tier = classify(question)
        routing = self._rc.get(tier)
        return (
            f"Question: '{question[:60]}...'\n"
            f"Tier: {tier}\n"
            f"Provider: {routing['provider']}\n"
            f"Model: {routing['model']}"
        )


class RoutedProvider:
    """
    A thin provider configured by the Router for a specific tier.

    Same interface as Provider (satisfies ProviderProtocol) — apps don't
    need to know whether they're talking to Provider or RoutedProvider.
    """

    def __init__(
        self,
        provider_name: str,
        model: str,
        provider_config: dict[str, Any],
    ) -> None:
        self._provider_name = provider_name
        self._model = model
        self._provider_config = provider_config

    @property
    def active_provider(self) -> str:
        return self._provider_name

    @property
    def active_model(self) -> str:
        return self._model

    def status(self) -> str:
        return f"Provider: {self._provider_name} | Model: {self._model}"

    def chat(
        self,
        user_message: str,
        system_prompt: str | None = None,
        stream: bool = False,
        history: list[dict[str, str]] | None = None,
    ) -> str | Generator[str, None, None]:
        try:
            import litellm
        except ImportError:
            raise ProviderError("litellm is not installed. Run: pip install litellm")

        messages = build_messages(user_message, system_prompt, history)
        kwargs: dict[str, Any] = {"model": self._model, "messages": messages, "stream": stream}
        if "base_url" in self._provider_config:
            kwargs["api_base"] = self._provider_config["base_url"]

        check_api_key(self._provider_name)

        try:
            response = litellm.completion(**kwargs)
        except Exception as e:
            raise ProviderError(f"LLM call failed ({self._provider_name}): {e}") from e

        return stream_tokens(response) if stream else response.choices[0].message.content


def _key_available(provider_name: str) -> bool:
    """Return True if the API key for this provider is set (or not needed)."""
    from core.provider import _API_KEY_MAP
    env_var = _API_KEY_MAP.get(provider_name)
    if env_var is None:
        return True  # ollama and mock need no key
    return bool(os.getenv(env_var))


if __name__ == "__main__":
    router = Router()

    test_questions = [
        "status",
        "What is a neural network?",
        "Should I leave my job if I don't get promoted this year?",
        "What is my biggest financial risk and what should I do this week?",
        "How does SIP work?",
        "Help me plan my career for the next 3 years given my current situation",
    ]

    print("Routing decisions:\n")
    for q in test_questions:
        tier = classify(q)
        routing = router._rc.get(tier)
        print(f"[{tier:6}] {routing['model']:30} ← {q}")
