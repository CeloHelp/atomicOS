"""Remote Ollama note synthesis client."""

from __future__ import annotations

import re
from typing import Any

import requests

from atomicos.config import OllamaConfig
from atomicos.errors import InferenceError


ATOMIC_NOTE_INSTRUCTION = """You are atomicOS, a local technical note synthesizer.
Convert the raw notes into one clear atomic Markdown note.
Use Portuguese when the source text is Portuguese, otherwise keep the source language.
Return only Markdown content, with a concise title, summary, key points, and practical examples when useful.
Do not wrap the response in a Markdown code fence.
""".strip()


class OllamaClient:
    """Small HTTP client for Ollama's generate endpoint."""

    def __init__(self, config: OllamaConfig, session: Any | None = None) -> None:
        self.config = config
        self.session = session or requests.Session()

    def build_prompt(self, raw_text: str) -> str:
        return f"{ATOMIC_NOTE_INSTRUCTION}\n\nRaw notes:\n{raw_text}"

    def build_payload(self, raw_text: str) -> dict[str, Any]:
        return {
            "model": self.config.model,
            "prompt": self.build_prompt(raw_text),
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_ctx": self.config.num_ctx,
            },
        }

    def synthesize(self, raw_text: str) -> str:
        url = f"{self.config.base_url.rstrip('/')}/api/generate"
        try:
            response = self.session.post(
                url,
                json=self.build_payload(raw_text),
                timeout=self.config.timeout_seconds,
            )
            response.raise_for_status()
        except requests.Timeout as exc:
            raise InferenceError("Ollama request timed out") from exc
        except requests.RequestException as exc:
            raise InferenceError(f"Ollama request failed: {exc}") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise InferenceError("Ollama returned malformed JSON") from exc

        content = payload.get("response")
        if not isinstance(content, str) or not content.strip():
            raise InferenceError("Ollama response did not contain usable content")

        return clean_markdown_response(content)


def clean_markdown_response(content: str) -> str:
    """Remove whole-response Markdown fences and reject empty cleanup results."""

    cleaned = content.strip()
    match = re.fullmatch(r"```(?:markdown|md)?\s*\n(?P<body>.*?)\n```", cleaned, re.DOTALL | re.IGNORECASE)
    if match:
        cleaned = match.group("body").strip()

    if not cleaned:
        raise InferenceError("Ollama response was empty after cleanup")

    return cleaned
