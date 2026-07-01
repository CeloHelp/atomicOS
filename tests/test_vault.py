from __future__ import annotations

import logging
import subprocess

import pytest

from atomicos.errors import ConfigurationError, PersistenceError
from atomicos.vault import VaultManager


def test_list_folders_returns_nested_relative_paths(tmp_path):
    (tmp_path / "Conhecimento" / "Java" / "SOLID").mkdir(parents=True)
    (tmp_path / ".obsidian").mkdir()

    folders = VaultManager(tmp_path).list_folders()

    assert folders == ["Conhecimento", "Conhecimento/Java", "Conhecimento/Java/SOLID"]


def test_list_folders_rejects_unavailable_root(tmp_path):
    manager = VaultManager(tmp_path / "missing")

    with pytest.raises(ConfigurationError, match="Vault root"):
        manager.list_folders()


def test_build_target_returns_safe_nested_destination(tmp_path):
    (tmp_path / "Conhecimento" / "Java" / "SOLID").mkdir(parents=True)
    manager = VaultManager(tmp_path)

    target = manager.build_target(
        "Conhecimento/Java/SOLID",
        "Principios",
        "Single Responsibility Principle",
    )

    assert target.relative_path == "Conhecimento/Java/SOLID/Principios/Single Responsibility Principle.md"
    assert target.absolute_parent == tmp_path.resolve() / "Conhecimento" / "Java" / "SOLID" / "Principios"


@pytest.mark.parametrize(
    ("folder", "subfolder", "title"),
    [
        ("../outside", "", "Note"),
        ("/absolute", "", "Note"),
        ("Conhecimento", "../../outside", "Note"),
        ("Conhecimento", "", "../Note"),
    ],
)
def test_build_target_rejects_unsafe_paths(tmp_path, folder, subfolder, title):
    tmp_path.mkdir(exist_ok=True)
    manager = VaultManager(tmp_path)

    with pytest.raises(PersistenceError):
        manager.build_target(folder, subfolder, title)


def test_create_note_invokes_cli_with_argument_array(tmp_path, caplog):
    caplog.set_level(logging.INFO)
    calls = []

    def runner(command, **kwargs):
        calls.append({"command": command, "kwargs": kwargs})
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    manager = VaultManager(tmp_path, obsidian_executable="obsidian", runner=runner)

    relative = manager.create_note("Conhecimento", "Java", "SOLID", "# SOLID")

    assert relative == "Conhecimento/Java/SOLID.md"
    assert (tmp_path / "Conhecimento" / "Java").is_dir()
    assert calls[0]["command"] == ["obsidian", "create", "path=Conhecimento/Java/SOLID.md", "content=# SOLID"]
    assert calls[0]["kwargs"]["cwd"] == str(tmp_path)
    assert "obsidian cli succeeded" in caplog.text
    assert "Conhecimento/Java/SOLID.md" in caplog.text
    assert "# SOLID" not in caplog.text


def test_create_note_does_not_duplicate_md_extension(tmp_path):
    calls = []

    def runner(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    manager = VaultManager(tmp_path, runner=runner)

    relative = manager.create_note("Conhecimento", "Java", "SOLID.md", "# SOLID")

    assert relative == "Conhecimento/Java/SOLID.md"
    assert calls[0][2] == "path=Conhecimento/Java/SOLID.md"


def test_create_note_reports_cli_failure(tmp_path, caplog):
    def runner(command, **kwargs):
        return subprocess.CompletedProcess(command, 2, stdout="x" * 600, stderr="boom")

    manager = VaultManager(tmp_path, runner=runner)

    with pytest.raises(PersistenceError, match="boom"):
        manager.create_note("Conhecimento", "", "Note", "SECRET_MARKDOWN")

    assert "obsidian cli failed" in caplog.text
    assert "<omitted>" in caplog.text
    assert "SECRET_MARKDOWN" not in caplog.text
    assert "truncated" in caplog.text


def test_create_note_reports_missing_cli(tmp_path, caplog):
    def runner(command, **kwargs):
        raise FileNotFoundError("obsidian")

    manager = VaultManager(tmp_path, runner=runner)

    with pytest.raises(PersistenceError, match="execute Obsidian CLI"):
        manager.create_note("Conhecimento", "", "Note", "SECRET_MARKDOWN")

    assert "obsidian cli execution failed" in caplog.text
    assert "<omitted>" in caplog.text
    assert "SECRET_MARKDOWN" not in caplog.text


def test_create_note_logs_target_directory_creation_failure(tmp_path, caplog):
    (tmp_path / "Conhecimento").write_text("not a directory")
    manager = VaultManager(tmp_path)

    with pytest.raises(PersistenceError, match="target directories"):
        manager.create_note("Conhecimento", "", "Note", "content")

    assert "vault target directory creation failed" in caplog.text
    assert "Conhecimento" in caplog.text
