from __future__ import annotations

import logging
import subprocess
from datetime import date

import pytest

from atomicos.errors import ConfigurationError, PersistenceError
from atomicos.vault import VaultManager


def test_list_folders_returns_nested_relative_paths(tmp_path):
    (tmp_path / "Conhecimento" / "Java" / "SOLID").mkdir(parents=True)
    (tmp_path / "Conhecimento" / "Java" / "SOLID" / "Note.md").write_text("# Note")
    (tmp_path / ".obsidian").mkdir()

    folders = VaultManager(tmp_path).list_folders()

    assert folders == ["Conhecimento", "Conhecimento/Java", "Conhecimento/Java/SOLID"]


def test_list_folders_excludes_empty_directories(tmp_path):
    (tmp_path / "Conhecimento" / "Empty").mkdir(parents=True)
    (tmp_path / "Conhecimento" / "With Note").mkdir(parents=True)
    (tmp_path / "Conhecimento" / "With Note" / "Note.md").write_text("# Note")

    folders = VaultManager(tmp_path).list_folders()

    assert folders == ["Conhecimento", "Conhecimento/With Note"]


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


def test_create_note_searches_creates_and_sets_default_properties(tmp_path, caplog):
    caplog.set_level(logging.INFO)
    calls = []

    def runner(command, **kwargs):
        calls.append({"command": command, "kwargs": kwargs})
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    manager = VaultManager(tmp_path, obsidian_executable="obsidian", runner=runner)

    relative = manager.create_note("Conhecimento", "Java", "SOLID", "# SOLID")

    assert relative == "Conhecimento/Java/SOLID.md"
    assert (tmp_path / "Conhecimento" / "Java").is_dir()
    assert calls[0]["command"] == ["obsidian", "search", "query=SOLID", "path=Conhecimento"]
    assert calls[1]["command"] == ["obsidian", "create", "path=Conhecimento/Java/SOLID.md", "content=# SOLID"]
    assert calls[0]["kwargs"]["cwd"] == str(tmp_path)
    assert [call["command"][1] for call in calls[2:]] == ["property:set"] * 5
    assert calls[2]["command"] == [
        "obsidian",
        "property:set",
        "path=Conhecimento/Java/SOLID.md",
        "name=source",
        "value=atomicOS",
        "type=text",
    ]
    assert calls[5]["command"] == [
        "obsidian",
        "property:set",
        "path=Conhecimento/Java/SOLID.md",
        "name=last_action",
        "value=created",
        "type=text",
    ]
    assert calls[6]["command"][3:] == ["name=updated_at", f"value={date.today().isoformat()}", "type=date"]
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
    assert calls[1][2] == "path=Conhecimento/Java/SOLID.md"


def test_create_note_appends_when_search_returns_the_exact_target(tmp_path):
    calls = []

    def runner(command, **kwargs):
        calls.append({"command": command, "kwargs": kwargs})
        stdout = "Conhecimento/Java/SOLID.md\n" if command[1] == "search" else "ok"
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    manager = VaultManager(tmp_path, runner=runner)

    relative = manager.create_note("Conhecimento", "Java", "SOLID", "# SOLID\n\nResumo novo")

    assert relative == "Conhecimento/Java/SOLID.md"
    assert calls[0]["command"] == ["obsidian", "search", "query=SOLID", "path=Conhecimento"]
    assert calls[1]["command"] == [
        "obsidian",
        "append",
        "path=Conhecimento/Java/SOLID.md",
        "content=\n\n---\n\n# SOLID\n\nResumo novo",
    ]
    assert calls[5]["command"][3:5] == ["name=last_action", "value=appended"]


def test_create_note_creates_when_search_result_is_not_the_exact_target(tmp_path):
    calls = []

    def runner(command, **kwargs):
        calls.append(command)
        stdout = "Conhecimento/Java/SOLID - antigo.md\n" if command[1] == "search" else "ok"
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    manager = VaultManager(tmp_path, runner=runner)

    manager.create_note("Conhecimento", "Java", "SOLID", "# SOLID")

    assert calls[1][1] == "create"


def test_create_note_appends_when_target_exists_on_disk(tmp_path):
    target = tmp_path / "Conhecimento" / "Java" / "SOLID.md"
    target.parent.mkdir(parents=True)
    target.write_text("# SOLID")
    calls = []

    def runner(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    manager = VaultManager(tmp_path, runner=runner)

    manager.create_note("Conhecimento", "Java", "SOLID", "# Complemento")

    assert calls[1][1] == "append"


def test_create_note_reports_cli_failure(tmp_path, caplog):
    def runner(command, **kwargs):
        if command[1] == "search":
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        return subprocess.CompletedProcess(command, 2, stdout="x" * 600, stderr="boom")

    manager = VaultManager(tmp_path, runner=runner)

    with pytest.raises(PersistenceError, match="boom"):
        manager.create_note("Conhecimento", "", "Note", "SECRET_MARKDOWN")

    assert "obsidian cli failed" in caplog.text
    assert "<omitted>" in caplog.text
    assert "SECRET_MARKDOWN" not in caplog.text
    assert "truncated" in caplog.text


def test_create_note_removes_new_empty_directories_after_cli_failure(tmp_path):
    def runner(command, **kwargs):
        return subprocess.CompletedProcess(command, 2, stdout="", stderr="boom")

    (tmp_path / "Conhecimento").mkdir()
    manager = VaultManager(tmp_path, runner=runner)

    with pytest.raises(PersistenceError, match="boom"):
        manager.create_note("Conhecimento", "New Folder/Nested", "Note", "content")

    assert (tmp_path / "Conhecimento").is_dir()
    assert not (tmp_path / "Conhecimento" / "New Folder").exists()


def test_create_note_reports_missing_cli(tmp_path, caplog):
    def runner(command, **kwargs):
        if command[1] == "search":
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
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
