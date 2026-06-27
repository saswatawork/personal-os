"""
LLM provider abstraction — the only place in the project that talks to an LLM.

All apps import Provider or ProviderProtocol from here.
To switch LLM providers, change active_provider in config/settings.yaml — nothing else.
"""

import logging
import os
from pathlib import Path
from typing import Any, Generator, Protocol

import yaml

log = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent.parent / "config" / "settings.yaml"

MOCK_RESPONSE = (
    "[mock provider] Context loaded successfully. "
    "Switch active_provider in config/settings.yaml to use a real LLM."
)

# Maps provider names to their expected environment variable.
_API_KEY_MAP: dict[str, str] = {
    "claude_api": "ANTHROPIC_API_KEY",
    "openai":     "OPENAI_API_KEY",
    "gemini":     "GEMINI_API_KEY",
}


class ProviderError(Exception):
    pass


# --------------------------------------------------------------------------- #
# Shared utilities — used by both Provider and RoutedProvider (in router.py)   #
# --------------------------------------------------------------------------- #

def check_api_key(provider_name: str) -> None:
    """Raise ProviderError early if the required API key env-var is missing."""
    env_var = _API_KEY_MAP.get(provider_name)
    if env_var and not os.getenv(env_var):
        raise ProviderError(
            f"Missing API key for '{provider_name}'. "
            f"Set environment variable: export {env_var}=your_key_here"
        )


def stream_tokens(response: Any) -> Generator[str, None, None]:
    """Yield text tokens from a litellm streaming response."""
    for chunk in response:
        token = chunk.choices[0].delta.content
        if token:
            yield token


def build_messages(
    user_message: str,
    system_prompt: str | None,
    history: list[dict[str, str]] | None,
) -> list[dict[str, str]]:
    """Assemble the message list that litellm expects."""
    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})
    return messages


# --------------------------------------------------------------------------- #
# Protocol — the shared interface for Provider and RoutedProvider               #
# --------------------------------------------------------------------------- #

class ProviderProtocol(Protocol):
    """
    Structural interface that Provider and RoutedProvider both satisfy.
    Use this as the type annotation whenever code accepts either class.
    """

    @property
    def active_provider(self) -> str: ...
    @property
    def active_model(self) -> str: ...

    def status(self) -> str: ...

    def chat(
        self,
        user_message: str,
        system_prompt: str | None = None,
        stream: bool = False,
        history: list[dict[str, str]] | None = None,
    ) -> str | Generator[str, None, None]: ...


# --------------------------------------------------------------------------- #
# Provider — reads active_provider from settings.yaml                           #
# --------------------------------------------------------------------------- #

class Provider:
    """
    Unified LLM interface. All apps use this — never litellm or provider SDKs directly.
    Active provider and model are set in config/settings.yaml.
    API keys come from environment variables only.

    Usage:
        provider = Provider()
        response = provider.chat("What should I focus on this week?", system_prompt)
    """

    def __init__(self, config_path: Path | str = CONFIG_PATH) -> None:
        self._config = self._load_config(Path(config_path))
        self._active: str = self._config["active_provider"]
        self._provider_config: dict[str, Any] = self._config["providers"][self._active]

    # ------------------------------------------------------------------ #
    # Public interface                                                      #
    # ------------------------------------------------------------------ #

    def chat(
        self,
        user_message: str,
        system_prompt: str | None = None,
        stream: bool = False,
        history: list[dict[str, str]] | None = None,
    ) -> str | Generator[str, None, None]:
        """
        Send a message and get a response.

        Args:
            user_message:  the user's question or input
            system_prompt: context injected before the conversation (from ContextLoader)
            stream:        yield tokens one by one instead of returning a full string
            history:       prior turns — [{"role": "user"/"assistant", "content": "..."}]

        Returns:
            str when stream=False, Generator[str] when stream=True
        """
        if self._active == "mock":
            return self._mock_response(stream)

        messages = build_messages(user_message, system_prompt, history)
        return self._call_litellm(messages, stream)

    @property
    def active_provider(self) -> str:
        return self._active

    @property
    def active_model(self) -> str:
        return self._provider_config.get("model", "unknown")

    def status(self) -> str:
        return f"Provider: {self._active} | Model: {self.active_model}"

    # ------------------------------------------------------------------ #
    # Internal                                                              #
    # ------------------------------------------------------------------ #

    def _call_litellm(
        self,
        messages: list[dict[str, str]],
        stream: bool,
    ) -> str | Generator[str, None, None]:
        try:
            import litellm
        except ImportError:
            raise ProviderError("litellm is not installed. Run: pip install litellm")

        model = self._provider_config["model"]
        kwargs: dict[str, Any] = {"model": model, "messages": messages, "stream": stream}
        if "base_url" in self._provider_config:
            kwargs["api_base"] = self._provider_config["base_url"]

        check_api_key(self._active)

        try:
            response = litellm.completion(**kwargs)
        except Exception as e:
            raise ProviderError(f"LLM call failed ({self._active}): {e}") from e

        return stream_tokens(response) if stream else response.choices[0].message.content

    def _mock_response(self, stream: bool) -> str | Generator[str, None, None]:
        if stream:
            return (word + " " for word in MOCK_RESPONSE.split())
        return MOCK_RESPONSE

    @staticmethod
    def _load_config(config_path: Path) -> dict[str, Any]:
        if not config_path.exists():
            raise ProviderError(f"Config file not found: {config_path}")
        with open(config_path) as f:
            return yaml.safe_load(f)


if __name__ == "__main__":
    provider = Provider()
    print(provider.status())
    print()

    response = provider.chat(
        user_message="What should I focus on this week?",
        system_prompt="You are a personal advisor. The user is a software engineer.",
    )
    print("Response:", response)
