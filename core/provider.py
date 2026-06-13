import os
from pathlib import Path
from typing import Generator

import yaml

CONFIG_PATH = Path(__file__).parent.parent / "config" / "settings.yaml"

MOCK_RESPONSE = (
    "[mock provider] Context loaded successfully. "
    "Switch active_provider in config/settings.yaml to use a real LLM."
)


class ProviderError(Exception):
    pass


class Provider:
    """
    Unified LLM interface. All apps use this — never litellm or provider SDKs directly.
    Active provider and model are set in config/settings.yaml.
    API keys come from environment variables only.

    Usage:
        provider = Provider()
        response = provider.chat("What should I focus on this week?", system_prompt)
    """

    def __init__(self, config_path: str = None):
        self._config = self._load_config(config_path or CONFIG_PATH)
        self._active = self._config["active_provider"]
        self._provider_config = self._config["providers"][self._active]

    # ------------------------------------------------------------------ #
    # Public interface                                                      #
    # ------------------------------------------------------------------ #

    def chat(self, user_message: str, system_prompt: str = None, stream: bool = False):
        """
        Send a message and get a response.

        Args:
            user_message: the user's question or input
            system_prompt: context to load before the conversation (from ContextLoader)
            stream: if True, yields tokens one by one instead of returning full string

        Returns:
            str — full response (stream=False)
            Generator[str] — token stream (stream=True)
        """
        if self._active == "mock":
            return self._mock_response(stream)

        messages = self._build_messages(user_message, system_prompt)
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

    def _build_messages(self, user_message: str, system_prompt: str = None) -> list:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})
        return messages

    def _call_litellm(self, messages: list, stream: bool):
        try:
            import litellm
        except ImportError:
            raise ProviderError(
                "litellm is not installed. Run: pip install litellm"
            )

        model = self._provider_config["model"]
        kwargs = {"model": model, "messages": messages, "stream": stream}

        # ollama needs a base_url
        if "base_url" in self._provider_config:
            kwargs["api_base"] = self._provider_config["base_url"]

        # surface missing API keys early with a clear message
        self._check_api_key()

        try:
            response = litellm.completion(**kwargs)
        except Exception as e:
            raise ProviderError(f"LLM call failed ({self._active}): {e}") from e

        if stream:
            return self._stream_tokens(response)
        return response.choices[0].message.content

    def _stream_tokens(self, response) -> Generator[str, None, None]:
        for chunk in response:
            token = chunk.choices[0].delta.content
            if token:
                yield token

    def _mock_response(self, stream: bool):
        if stream:
            return self._mock_stream()
        return MOCK_RESPONSE

    def _mock_stream(self) -> Generator[str, None, None]:
        for word in MOCK_RESPONSE.split():
            yield word + " "

    def _check_api_key(self):
        key_map = {
            "claude_api": "ANTHROPIC_API_KEY",
            "openai":     "OPENAI_API_KEY",
            "gemini":     "GEMINI_API_KEY",
        }
        env_var = key_map.get(self._active)
        if env_var and not os.getenv(env_var):
            raise ProviderError(
                f"Missing API key for '{self._active}'. "
                f"Set environment variable: export {env_var}=your_key_here"
            )

    @staticmethod
    def _load_config(config_path: Path) -> dict:
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
        system_prompt="You are a personal advisor. The user is a software engineer."
    )
    print("Response:", response)
