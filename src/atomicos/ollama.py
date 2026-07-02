"""Remote Ollama note synthesis client."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

import requests

from atomicos.config import OllamaConfig
from atomicos.diagnostics import Timer, get_logger
from atomicos.errors import InferenceError


logger = get_logger("ollama")


ATOMIC_NOTE_INSTRUCTION = """You are atomicOS, a local technical note synthesizer.
Convert the raw notes into one clear atomic Markdown note.
Use Portuguese when the source text is Portuguese, otherwise keep the source language.
Return only Markdown content, with a concise title, summary, key points, and practical examples when useful.
Do not wrap the response in a Markdown code fence.
Do not add explanations, prefaces, or commentary outside the final note.
""".strip()


@dataclass(frozen=True)
class ReadinessResult:
    available: bool
    message: str


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

    def check_readiness(self, timeout_seconds: float = 2.0) -> ReadinessResult:
        """Check whether Ollama is reachable without sending note content."""

        url = f"{self.config.base_url.rstrip('/')}/api/tags"
        timer = Timer.start()
        try:
            response = self.session.get(url, timeout=timeout_seconds)
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("readiness payload is not an object")
        except (requests.Timeout, requests.RequestException, ValueError) as exc:
            logger.warning(
                "ollama readiness failed base_url=%s model=%s timeout=%s duration_ms=%s error=%s",
                self.config.base_url,
                self.config.model,
                timeout_seconds,
                timer.elapsed_ms(),
                exc,
                exc_info=True,
            )
            return ReadinessResult(False, f"Ollama unavailable: {exc}")

        logger.info(
            "ollama readiness succeeded base_url=%s model=%s timeout=%s duration_ms=%s",
            self.config.base_url,
            self.config.model,
            timeout_seconds,
            timer.elapsed_ms(),
        )
        return ReadinessResult(True, "Ollama is reachable")

    def synthesize(self, raw_text: str, *, run_id: str | None = None) -> str:
        url = f"{self.config.base_url.rstrip('/')}/api/generate"
        timer = Timer.start()
        response: Any | None = None
        try:
            response = self.session.post(
                url,
                json=self.build_payload(raw_text),
                timeout=self.config.timeout_seconds,
            )
            response.raise_for_status()
        except requests.Timeout as exc:
            logger.warning(
                "run_id=%s ollama request timed out base_url=%s model=%s timeout=%s duration_ms=%s raw_input_bytes=%s",
                run_id,
                self.config.base_url,
                self.config.model,
                self.config.timeout_seconds,
                timer.elapsed_ms(),
                len(raw_text.encode("utf-8")),
                exc_info=True,
            )
            raise InferenceError("Ollama request timed out") from exc
        except requests.RequestException as exc:
            logger.warning(
                "run_id=%s ollama request failed base_url=%s model=%s timeout=%s status_code=%s duration_ms=%s raw_input_bytes=%s error=%s",
                run_id,
                self.config.base_url,
                self.config.model,
                self.config.timeout_seconds,
                _status_code(response),
                timer.elapsed_ms(),
                len(raw_text.encode("utf-8")),
                exc,
                exc_info=True,
            )
            raise InferenceError(f"Ollama request failed: {exc}") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            logger.warning(
                "run_id=%s ollama malformed json base_url=%s model=%s timeout=%s status_code=%s duration_ms=%s raw_input_bytes=%s response_bytes=%s",
                run_id,
                self.config.base_url,
                self.config.model,
                self.config.timeout_seconds,
                _status_code(response),
                timer.elapsed_ms(),
                len(raw_text.encode("utf-8")),
                _response_size(response),
                exc_info=True,
            )
            raise InferenceError("Ollama returned malformed JSON") from exc

        content = payload.get("response")
        if not isinstance(content, str) or not content.strip():
            logger.warning(
                "run_id=%s ollama unusable content base_url=%s model=%s timeout=%s status_code=%s duration_ms=%s raw_input_bytes=%s response_bytes=%s",
                run_id,
                self.config.base_url,
                self.config.model,
                self.config.timeout_seconds,
                _status_code(response),
                timer.elapsed_ms(),
                len(raw_text.encode("utf-8")),
                _response_size(response),
            )
            raise InferenceError("Ollama response did not contain usable content")

        cleaned = clean_markdown_response(content)
        logger.info(
            "run_id=%s ollama request succeeded base_url=%s model=%s timeout=%s status_code=%s duration_ms=%s raw_input_bytes=%s response_bytes=%s",
            run_id,
            self.config.base_url,
            self.config.model,
            self.config.timeout_seconds,
            _status_code(response),
            timer.elapsed_ms(),
            len(raw_text.encode("utf-8")),
            _response_size(response),
        )
        return cleaned


def clean_markdown_response(content: str) -> str:
    """Remove Markdown fences and reject empty cleanup results."""

    cleaned = content.strip()
    match = re.fullmatch(r"```(?:markdown|md)?\s*\n(?P<body>.*?)\n```", cleaned, re.DOTALL | re.IGNORECASE)
    if match:
        cleaned = match.group("body").strip()
    else:
        match = re.match(r"```(?:markdown|md)?\s*\n(?P<body>.*?)\n```", cleaned, re.DOTALL | re.IGNORECASE)
        if match:
            cleaned = match.group("body").strip()

    if not cleaned:
        raise InferenceError("Ollama response was empty after cleanup")

    return cleaned


def _status_code(response: Any | None) -> str | int:
    return getattr(response, "status_code", "unknown") if response is not None else "unknown"


def _response_size(response: Any | None) -> int:
    if response is None:
        return 0
    text = getattr(response, "text", None)
    if isinstance(text, str):
        return len(text.encode("utf-8"))
    content = getattr(response, "content", None)
    if isinstance(content, bytes):
        return len(content)
    return 0
