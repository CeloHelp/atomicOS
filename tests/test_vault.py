from __future__ import annotations

import logging
import subprocess

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
    assert target.parent_relative_path == "Conhecimento/Java/SOLID/Principios"
    assert target.absolute_parent == tmp_path.resolve() / "Conhecimento" / "Java" / "SOLID" / "Principios"
    assert target.absolute_note == target.absolute_parent / "Single Responsibility Principle.md"


def test_build_target_does_not_duplicate_markdown_extension(tmp_path):
    (tmp_path / "Conhecimento").mkdir()
    manager = VaultManager(tmp_path)

    target = manager.build_target("Conhecimento", "", "Java - Records.md")

    assert target.relative_path == "Conhecimento/Java - Records.md"


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


def test_create_note_searches_then_creates_and_sets_properties(tmp_path, caplog):
    caplog.set_level(logging.INFO)
    calls = []

    def runner(command, **kwargs):
        calls.append({"command": command, "kwargs": kwargs})
        if command[1] == "search":
            return subprocess.CompletedProcess(command, 0, stdout="[]", stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    manager = VaultManager(tmp_path, obsidian_executable="obsidian", runner=runner)

    relative = manager.create_note("Conhecimento", "Java", "SOLID", "# SOLID")

    assert relative == "Conhecimento/Java/SOLID.md"
    assert (tmp_path / "Conhecimento" / "Java").is_dir()
    assert calls[0]["command"] == [
        "obsidian",
        "search",
        "query=SOLID",
        "limit=10",
        "format=json",
        "path=Conhecimento/Java",
    ]
    assert calls[1]["command"] == ["obsidian", "create", "path=Conhecimento/Java/SOLID.md", "content=# SOLID"]
    property_commands = [call["command"] for call in calls if call["command"][1] == "property:set"]
    assert len(property_commands) == 5
    assert ["obsidian", "property:set", "path=Conhecimento/Java/SOLID.md", "name=source", "value=atomicOS", "type=text"] in property_commands
    assert ["obsidian", "property:set", "path=Conhecimento/Java/SOLID.md", "name=area", "value=Conhecimento", "type=text"] in property_commands
    assert ["obsidian", "property:set", "path=Conhecimento/Java/SOLID.md", "name=last_action", "value=created", "type=text"] in property_commands
    assert calls[0]["kwargs"]["cwd"] == str(tmp_path)
    assert "obsidian create succeeded" in caplog.text
    assert "Conhecimento/Java/SOLID.md" in caplog.text
    assert "# SOLID" not in caplog.text


def test_create_note_appends_when_search_finds_existing_target(tmp_path):
    calls = []

    def runner(command, **kwargs):
        calls.append(command)
        if command[1] == "search":
            return subprocess.CompletedProcess(command, 0, stdout='["Conhecimento/Java/SOLID.md"]', stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    manager = VaultManager(tmp_path, runner=runner)

    relative = manager.create_note("Conhecimento", "Java", "SOLID", "# New SOLID")

    assert relative == "Conhecimento/Java/SOLID.md"
    assert calls[1][1] == "append"
    assert calls[1][2] == "path=Conhecimento/Java/SOLID.md"
    assert calls[1][3] == "content=\n\n---\n\n# New SOLID"
    assert not any(command[1] == "create" for command in calls)
    assert ["obsidian", "property:set", "path=Conhecimento/Java/SOLID.md", "name=last_action", "value=appended", "type=text"] in calls


def test_create_note_appends_when_target_file_exists_even_if_search_is_empty(tmp_path):
    (tmp_path / "Conhecimento" / "Java").mkdir(parents=True)
    (tmp_path / "Conhecimento" / "Java" / "SOLID.md").write_text("# Existing", encoding="utf-8")
    calls = []

    def runner(command, **kwargs):
        calls.append(command)
        if command[1] == "search":
            return subprocess.CompletedProcess(command, 0, stdout="[]", stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    manager = VaultManager(tmp_path, runner=runner)

    manager.create_note("Conhecimento", "Java", "SOLID", "# New SOLID")

    assert calls[1][1] == "append"
    assert not any(command[1] == "create" for command in calls)


def test_create_note_reports_cli_failure(tmp_path, caplog):
    def runner(command, **kwargs):
        if command[1] == "search":
            return subprocess.CompletedProcess(command, 0, stdout="[]", stderr="")
        return subprocess.CompletedProcess(command, 2, stdout="x" * 600, stderr="boom")

    manager = VaultManager(tmp_path, runner=runner)

    with pytest.raises(PersistenceError, match="boom"):
        manager.create_note("Conhecimento", "", "Note", "SECRET_MARKDOWN")

    assert "obsidian create failed" in caplog.text
    assert "<omitted>" in caplog.text
    assert "SECRET_MARKDOWN" not in caplog.text
    assert "truncated" in caplog.text


def test_create_note_removes_new_empty_directories_after_cli_failure(tmp_path):
    def runner(command, **kwargs):
        if command[1] == "search":
            return subprocess.CompletedProcess(command, 0, stdout="[]", stderr="")
        return subprocess.CompletedProcess(command, 2, stdout="", stderr="boom")

    (tmp_path / "Conhecimento").mkdir()
    manager = VaultManager(tmp_path, runner=runner)

    with pytest.raises(PersistenceError, match="boom"):
        manager.create_note("Conhecimento", "New Folder/Nested", "Note", "content")

    assert (tmp_path / "Conhecimento").is_dir()
    assert not (tmp_path / "Conhecimento" / "New Folder").exists()


def test_create_note_reports_missing_cli(tmp_path, caplog):
    def runner(command, **kwargs):
        raise FileNotFoundError("obsidian")

    manager = VaultManager(tmp_path, runner=runner)

    with pytest.raises(PersistenceError, match="execute Obsidian CLI"):
        manager.create_note("Conhecimento", "", "Note", "SECRET_MARKDOWN")

    assert "obsidian search execution failed" in caplog.text
    assert "SECRET_MARKDOWN" not in caplog.text


def test_create_note_logs_target_directory_creation_failure(tmp_path, caplog):
    (tmp_path / "Conhecimento").write_text("not a directory")
    manager = VaultManager(tmp_path)

    with pytest.raises(PersistenceError, match="target directories"):
        manager.create_note("Conhecimento", "", "Note", "content")

    assert "vault target directory creation failed" in caplog.text
    assert "Conhecimento" in caplog.text


def test_search_notes_parses_plain_text_output(tmp_path):
    def runner(command, **kwargs):
        return subprocess.CompletedProcess(command, 0, stdout="Conhecimento/A.md\nConhecimento/B.md\n", stderr="")

    manager = VaultManager(tmp_path, runner=runner)

    assert manager.search_notes("Java", "Conhecimento") == ["Conhecimento/A.md", "Conhecimento/B.md"]
