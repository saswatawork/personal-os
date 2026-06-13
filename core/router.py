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

Or let it auto-select:
    tier, provider = router.route_with_tier(question)
    print(f"Using tier: {tier}")
"""

import os
import re
from typing import Tuple

import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config" / "settings.yaml"

# Keywords that signal a complex question needing a stronger model
COMPLEX_SIGNALS = [
    "career", "promotion", "salary", "job", "resign", "leave", "hire",
    "invest", "financial", "money", "loan", "emi", "corpus", "sip",
    "should i", "what should", "help me decide", "advice",
    "risk", "strategy", "plan", "roadmap", "how do i",
    "health", "stress", "sleep", "family", "daughter",
    "goal", "future", "next year", "long term",
]

# Keywords that signal a simple question — fast model is fine
SIMPLE_SIGNALS = [
    "what is", "define", "explain", "how does", "status", "list",
    "show me", "what are", "tell me about", "summarize",
]


def classify(question: str) -> str:
    """
    Classify a question into a complexity tier.

    Returns: "fast" | "local" | "strong"
    """
    q = question.lower().strip()
    word_count = len(q.split())

    # Very short questions → fast
    if word_count <= 5:
        return "fast"

    # Check for complex signals first — they override simple signals
    complex_hits = sum(1 for sig in COMPLEX_SIGNALS if sig in q)
    simple_hits = sum(1 for sig in SIMPLE_SIGNALS if sig in q)

    if complex_hits >= 2:
        return "strong"
    if complex_hits >= 1:
        return "local"
    if simple_hits >= 1 and word_count < 15:
        return "fast"

    # Default: local — good balance of quality and cost
    return "local"


class RouterConfig:
    """Reads provider config and maps tiers to providers."""

    def __init__(self, config_path: Path = CONFIG_PATH):
        with open(config_path) as f:
            self._config = yaml.safe_load(f)
        self._providers = self._config.get("providers", {})
        self._routing = self._config.get("routing", self._default_routing())

    def _default_routing(self) -> dict:
        """
        Fallback routing if no [routing] section in settings.yaml.
        Prefers local models — no API key needed.
        """
        return {
            "fast":   {"provider": "ollama", "model": "ollama/llama3.2"},
            "local":  {"provider": "ollama", "model": "ollama/qwen2.5:7b"},
            "strong": {"provider": "ollama", "model": "ollama/qwen2.5:7b"},
        }

    def get(self, tier: str) -> dict:
        return self._routing.get(tier, self._routing["local"])

    def provider_config(self, provider_name: str) -> dict:
        return self._providers.get(provider_name, {})


class Router:
    """
    Routes a question to the right provider based on complexity.

    The router creates a lightweight Provider-like object for each tier
    so it can be used as a drop-in replacement for Provider.
    """

    def __init__(self, config_path: Path = CONFIG_PATH):
        self._rc = RouterConfig(config_path)

    def route(self, question: str):
        """
        Returns a configured Provider for the right tier.
        Use like: provider = router.route(question); provider.chat(...)
        """
        _, provider = self.route_with_tier(question)
        return provider

    def route_with_tier(self, question: str) -> Tuple[str, "RoutedProvider"]:
        """
        Returns (tier_name, provider) so the caller can log which tier was used.
        Falls back to local tier if the strong tier needs an API key that isn't set.
        """
        tier = classify(question)
        routing = self._rc.get(tier)
        provider_name = routing["provider"]
        model = routing["model"]

        # Graceful fallback: if strong tier needs a cloud key and it's missing,
        # drop back to local rather than crashing mid-session
        if tier == "strong" and not self._key_available(provider_name):
            fallback = self._rc.get("local")
            print(
                f"[router] No API key for '{provider_name}' — "
                f"falling back to local: {fallback['model']}"
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

    def _key_available(self, provider_name: str) -> bool:
        key_map = {
            "claude_api": "ANTHROPIC_API_KEY",
            "openai":     "OPENAI_API_KEY",
            "gemini":     "GEMINI_API_KEY",
        }
        env_var = key_map.get(provider_name)
        if env_var is None:
            return True  # ollama and mock need no key
        return bool(os.getenv(env_var))

    def explain(self, question: str) -> str:
        """
        Explain the routing decision for a question — useful for debugging.
        """
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
    A thin provider that uses the model/config the Router selected.
    Same interface as Provider — apps don't need to know the difference.
    """

    def __init__(self, provider_name: str, model: str, provider_config: dict):
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
        system_prompt: str = None,
        stream: bool = False,
        history: list = None,
    ) -> str:
        try:
            import litellm
        except ImportError:
            raise RuntimeError("litellm is not installed. Run: /usr/bin/python3 -m pip install litellm")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        kwargs = {"model": self._model, "messages": messages, "stream": stream}
        if "base_url" in self._provider_config:
            kwargs["api_base"] = self._provider_config["base_url"]

        self._check_api_key()

        response = litellm.completion(**kwargs)
        if stream:
            return self._stream_tokens(response)
        return response.choices[0].message.content

    def _stream_tokens(self, response):
        for chunk in response:
            token = chunk.choices[0].delta.content
            if token:
                yield token

    def _check_api_key(self):
        key_map = {
            "claude_api": "ANTHROPIC_API_KEY",
            "openai":     "OPENAI_API_KEY",
            "gemini":     "GEMINI_API_KEY",
        }
        env_var = key_map.get(self._provider_name)
        if env_var and not os.getenv(env_var):
            raise RuntimeError(
                f"Missing API key for '{self._provider_name}'. "
                f"Set: export {env_var}=your_key_here"
            )


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
