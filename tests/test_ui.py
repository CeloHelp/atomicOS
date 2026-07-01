from __future__ import annotations

from pathlib import Path

from atomicos.config import AppConfig
from atomicos.ollama import ReadinessResult
from atomicos import ui
from atomicos.ui import build_page, format_readiness_log


def test_format_readiness_log_success_message():
    assert format_readiness_log(ReadinessResult(True, "ok")).startswith("[OK]")


def test_format_readiness_log_warning_message():
    message = format_readiness_log(ReadinessResult(False, "down"))

    assert message.startswith("[WARN]")
    assert "indisponivel" in message


def test_build_page_warns_when_ai_unavailable_but_loads_vault(monkeypatch):
    class FakeOllamaClient:
        def __init__(self, config):
            self.config = config

        def check_readiness(self):
            return ReadinessResult(False, "down")

    class FakeVaultManager:
        def __init__(self, vault_root, obsidian_executable):
            self.vault_root = vault_root
            self.obsidian_executable = obsidian_executable

        def list_folders(self):
            return ["Conhecimento"]

    class FakePage:
        def __init__(self):
            self.controls = []
            self.update_count = 0

        def add(self, control):
            self.controls.append(control)

        def update(self):
            self.update_count += 1

    monkeypatch.setattr(ui, "OllamaClient", FakeOllamaClient)
    monkeypatch.setattr(ui, "VaultManager", FakeVaultManager)
    page = FakePage()

    build_page(page, AppConfig(vault_root=Path("vault")))

    text_values = _text_values(page.controls)
    assert any("[WARN]" in value for value in text_values)
    assert any("pastas carregadas" in value for value in text_values)


def _text_values(controls):
    values = []
    for control in controls:
        value = getattr(control, "value", None)
        if isinstance(value, str):
            values.append(value)
        content = getattr(control, "content", None)
        if content is not None:
            values.extend(_text_values([content]))
        child_controls = getattr(control, "controls", None)
        if child_controls:
            values.extend(_text_values(child_controls))
    return values
