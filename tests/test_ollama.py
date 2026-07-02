from __future__ import annotations

import logging

import pytest
import requests

from atomicos.config import OllamaConfig
from atomicos.errors import InferenceError
from atomicos.ollama import OllamaClient, clean_markdown_response


class FakeResponse:
    def __init__(
        self,
        json_payload=None,
        status_error: Exception | None = None,
        json_error: Exception | None = None,
        status_code: int = 200,
        text: str = "",
    ):
        self.json_payload = json_payload
        self.status_error = status_error
        self.json_error = json_error
        self.status_code = status_code
        self.text = text

    def raise_for_status(self):
        if self.status_error:
            raise self.status_error

    def json(self):
        if self.json_error:
            raise self.json_error
        return self.json_payload


class FakeSession:
    def __init__(self, result=None, get_result=None):
        self.result = result
        self.get_result = get_result if get_result is not None else result
        self.calls = []
        self.get_calls = []

    def get(self, url, timeout):
        self.get_calls.append({"url": url, "timeout": timeout})
        if isinstance(self.get_result, Exception):
            raise self.get_result
        return self.get_result

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
    session = FakeSession(FakeResponse({"response": "```markdown\n# Note\n```"}, text='{"response":"# Note"}'))
    client = OllamaClient(OllamaConfig(base_url="http://ollama:11434", timeout_seconds=9), session=session)

    result = client.synthesize("raw")

    assert result == "# Note"
    assert session.calls[0]["url"] == "http://ollama:11434/api/generate"
    assert session.calls[0]["timeout"] == 9


def test_clean_markdown_response_extracts_initial_fenced_note_and_drops_commentary():
    response = """```markdown
# WAF

Resumo sobre firewall de aplicacao web.
```

Este texto explica a nota acima."""

    assert clean_markdown_response(response) == "# WAF\n\nResumo sobre firewall de aplicacao web."


def test_readiness_success_uses_tags_endpoint_without_note_content(caplog):
    caplog.set_level(logging.INFO)
    session = FakeSession(get_result=FakeResponse({"models": []}))
    client = OllamaClient(OllamaConfig(base_url="http://ollama:11434"), session=session)

    result = client.check_readiness(timeout_seconds=1.5)

    assert result.available is True
    assert session.get_calls == [{"url": "http://ollama:11434/api/tags", "timeout": 1.5}]
    assert "readiness succeeded" in caplog.text


def test_readiness_failure_returns_recoverable_result(caplog):
    client = OllamaClient(OllamaConfig(base_url="http://ollama:11434"), session=FakeSession(get_result=requests.Timeout("down")))

    result = client.check_readiness(timeout_seconds=1)

    assert result.available is False
    assert "unavailable" in result.message
    assert "readiness failed" in caplog.text


def test_synthesize_turns_timeout_into_recoverable_error():
    client = OllamaClient(OllamaConfig(), session=FakeSession(requests.Timeout()))

    with pytest.raises(InferenceError, match="timed out"):
        client.synthesize("raw")


def test_synthesize_turns_non_success_into_recoverable_error():
    session = FakeSession(FakeResponse(status_error=requests.HTTPError("500 Server Error"), status_code=500))
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


def test_synthesize_logs_safe_metadata_without_prompt_or_generated_content(caplog):
    caplog.set_level(logging.INFO)
    raw_text = "raw secret note text"
    generated = "# Generated secret markdown"
    session = FakeSession(FakeResponse({"response": generated}, text='{"response":"redacted"}'))
    client = OllamaClient(OllamaConfig(base_url="http://ollama:11434", timeout_seconds=9), session=session)

    assert client.synthesize(raw_text, run_id="run123") == generated

    assert "run_id=run123" in caplog.text
    assert "raw_input_bytes" in caplog.text
    assert raw_text not in caplog.text
    assert generated not in caplog.text
