from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Protocol

from app.core.config import Settings, get_settings


class LLMProvider(Protocol):
    provider_name: str

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]: ...


class LLMProviderError(RuntimeError):
    pass


class DeterministicMockLLMProvider:
    provider_name = "deterministic_mock"

    def __init__(self, response: dict[str, Any] | None = None) -> None:
        self._response = response or {"suggestions": []}
        self.requests: list[tuple[str, str]] = []

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        self.requests.append((system_prompt, user_prompt))
        return self._response


class OpenAICompatibleProvider:
    provider_name = "openai_compatible"

    def __init__(
        self,
        base_url: str,
        api_key: str | None,
        model: str,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout_seconds = timeout_seconds

    @classmethod
    def from_settings(cls, settings: Settings) -> OpenAICompatibleProvider:
        return cls(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            timeout_seconds=settings.llm_timeout_seconds,
        )

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        request = urllib.request.Request(
            f"{self._base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers=self._headers(),
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except (TimeoutError, urllib.error.URLError, json.JSONDecodeError) as exc:
            msg = "LLM provider request failed."
            raise LLMProviderError(msg) from exc

        content = _extract_message_content(response_payload)
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            msg = "LLM provider returned non-JSON content."
            raise LLMProviderError(msg) from exc

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers


def configured_llm_provider(settings: Settings | None = None) -> LLMProvider | None:
    resolved_settings = settings or get_settings()
    provider = resolved_settings.llm_provider.strip().lower()
    if provider in {"", "disabled", "none", "off"}:
        return None
    if provider in {"openai", "openai_compatible"}:
        return OpenAICompatibleProvider.from_settings(resolved_settings)

    msg = f"Unsupported LLM provider: {resolved_settings.llm_provider}"
    raise ValueError(msg)


def _extract_message_content(response_payload: dict[str, Any]) -> str:
    try:
        content = response_payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        msg = "LLM provider response did not include message content."
        raise LLMProviderError(msg) from exc
    if not isinstance(content, str):
        msg = "LLM provider message content was not a string."
        raise LLMProviderError(msg)
    return content
