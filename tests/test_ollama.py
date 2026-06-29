from __future__ import annotations

import pytest
import requests

from atomicos.config import OllamaConfig
from atomicos.errors import InferenceError
from atomicos.ollama import OllamaClient, clean_markdown_response


class FakeResponse:
    def __init__(self, json_payload=None, status_error: Exception | None = None, json_error: Exception | None = None):
        self.json_payload = json_payload
        self.status_error = status_error
        self.json_error = json_error

    def raise_for_status(self):
        if self.status_error:
            raise self.status_error

    def json(self):
        if self.json_error:
            raise self.json_error
        return self.json_payload


class FakeSession:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def post(self, url, json, timeout):
        self.calls.append({"url": url, "json": json, "timeout": timeout})
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def test_build_payload_contains_model_options_and_exact_user_text():
    client = OllamaClient(OllamaConfig(base_url="http://ollama:11434"))

    payload = client.build_payload("SOLID raw notes")

    assert payload["model"] == "qwen2.5:3b"
    assert payload["stream"] is False
    assert payload["options"] == {"temperature": 0.1, "num_ctx": 4096}
    assert "SOLID raw notes" in payload["prompt"]


def test_synthesize_extracts_and_cleans_response():
    session = FakeSession(FakeResponse({"response": "```markdown\n# Note\n```"}))
    client = OllamaClient(OllamaConfig(base_url="http://ollama:11434", timeout_seconds=9), session=session)

    result = client.synthesize("raw")

    assert result == "# Note"
    assert session.calls[0]["url"] == "http://ollama:11434/api/generate"
    assert session.calls[0]["timeout"] == 9


def test_synthesize_turns_timeout_into_recoverable_error():
    client = OllamaClient(OllamaConfig(), session=FakeSession(requests.Timeout()))

    with pytest.raises(InferenceError, match="timed out"):
        client.synthesize("raw")


def test_synthesize_turns_non_success_into_recoverable_error():
    session = FakeSession(FakeResponse(status_error=requests.HTTPError("500 Server Error")))
    client = OllamaClient(OllamaConfig(), session=session)

    with pytest.raises(InferenceError, match="request failed"):
        client.synthesize("raw")


def test_synthesize_rejects_malformed_json():
    session = FakeSession(FakeResponse(json_error=ValueError("bad json")))
    client = OllamaClient(OllamaConfig(), session=session)

    with pytest.raises(InferenceError, match="malformed JSON"):
        client.synthesize("raw")


def test_synthesize_rejects_missing_response():
    client = OllamaClient(OllamaConfig(), session=FakeSession(FakeResponse({"done": True})))

    with pytest.raises(InferenceError, match="usable content"):
        client.synthesize("raw")


def test_clean_markdown_response_rejects_empty_cleanup():
    with pytest.raises(InferenceError, match="empty"):
        clean_markdown_response("   ")
