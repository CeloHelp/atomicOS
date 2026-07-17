"""Obsidian Vault integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path, PurePosixPath
import subprocess
from typing import Any, Callable, Sequence

from atomicos.diagnostics import Timer, get_logger, sanitize_command, truncate_value
from atomicos.errors import ConfigurationError, PersistenceError


logger = get_logger("vault")

RunCommand = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class NoteTarget:
    relative_path: str
    parent_relative_path: str
    absolute_note: Path
    absolute_parent: Path


class VaultManager:
    """Discovers Vault folders and persists notes through the Obsidian CLI."""

    SEARCH_LIMIT = 10

    def __init__(
        self,
        vault_root: Path,
        obsidian_executable: str = "obsidian",
        runner: RunCommand = subprocess.run,
    ) -> None:
        self.vault_root = vault_root.expanduser()
        self.obsidian_executable = obsidian_executable
        self.runner = runner

    def list_folders(self) -> list[str]:
        root = self._existing_root()
        folders: list[str] = []
        for path in root.rglob("*"):
            if (
                path.is_dir()
                and not _is_hidden_part(path.relative_to(root))
                and _contains_visible_markdown(path, root)
            ):
                folders.append(path.relative_to(root).as_posix())
        return sorted(folders)

    def build_target(self, selected_folder: str, optional_subfolder: str, title: str) -> NoteTarget:
        root = self._existing_root()
        parts: list[str] = []
        parts.extend(_split_relative(selected_folder))
        parts.extend(_split_relative(optional_subfolder))
        parts.append(_safe_title(title))

        relative = PurePosixPath(*parts)
        if relative.is_absolute() or any(part == ".." for part in relative.parts):
            raise PersistenceError("Target path must stay inside the Vault")

        absolute_note = (root / Path(*relative.parts)).resolve()
        try:
            absolute_note.relative_to(root.resolve())
        except ValueError as exc:
            raise PersistenceError("Target path escapes the configured Vault") from exc

        parent_relative = relative.parent.as_posix()
        if parent_relative == ".":
            parent_relative = ""

        return NoteTarget(
            relative_path=relative.as_posix(),
            parent_relative_path=parent_relative,
            absolute_note=absolute_note,
            absolute_parent=absolute_note.parent,
        )

    def create_note(
        self,
        selected_folder: str,
        optional_subfolder: str,
        title: str,
        markdown: str,
        *,
        run_id: str | None = None,
    ) -> str:
        """Search before writing, append to an existing target, otherwise create it."""

        target = self.build_target(selected_folder, optional_subfolder, title)
        logger.info(
            "run_id=%s vault target prepared vault_root=%s relative_path=%s parent=%s",
            run_id,
            self.vault_root,
            target.relative_path,
            target.absolute_parent,
        )

        created_directories = _missing_directories(root=self._existing_root(), parent=target.absolute_parent)
        try:
            target.absolute_parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logger.exception(
                "run_id=%s vault target directory creation failed vault_root=%s parent=%s relative_path=%s",
                run_id,
                self.vault_root,
                target.absolute_parent,
                target.relative_path,
            )
            raise PersistenceError(f"Could not create target directories: {exc}") from exc

        try:
            search_matches = self.search_notes(
                query=title,
                folder=target.parent_relative_path,
                run_id=run_id,
                target_path=target.relative_path,
            )

            if target.relative_path in search_matches or target.absolute_note.exists():
                self._append_note(target, markdown, run_id=run_id)
                action = "appended"
            else:
                self._create_note(target, markdown, run_id=run_id)
                action = "created"

            self._set_default_properties(
                target,
                selected_folder=selected_folder,
                action=action,
                run_id=run_id,
            )
        except PersistenceError:
            if not target.absolute_note.exists():
                _remove_empty_directories(created_directories, run_id=run_id)
            raise

        logger.info(
            "run_id=%s vault persistence completed action=%s vault_root=%s relative_path=%s",
            run_id,
            action,
            self.vault_root,
            target.relative_path,
        )
        return target.relative_path

    def search_notes(
        self,
        query: str,
        folder: str,
        *,
        run_id: str | None = None,
        target_path: str | None = None,
    ) -> list[str]:
        command = [
            self.obsidian_executable,
            "search",
            f"query={query.strip()}",
            f"limit={self.SEARCH_LIMIT}",
            "format=json",
        ]
        if folder:
            command.append(f"path={folder}")

        result = self._run_cli(
            command,
            run_id=run_id,
            target_path=target_path or folder,
            operation="obsidian search",
        )
        matches = _parse_search_paths(result.stdout)
        logger.info(
            "run_id=%s obsidian search parsed matches=%s target_path=%s",
            run_id,
            len(matches),
            target_path or folder,
        )
        return matches

    def _create_note(self, target: NoteTarget, markdown: str, *, run_id: str | None = None) -> None:
        command = [
            self.obsidian_executable,
            "create",
            f"path={target.relative_path}",
            f"content={markdown}",
        ]
        self._run_cli(command, run_id=run_id, target_path=target.relative_path, operation="obsidian create")

    def _append_note(self, target: NoteTarget, markdown: str, *, run_id: str | None = None) -> None:
        content = f"\n\n---\n\n{markdown.strip()}"
        command = [
            self.obsidian_executable,
            "append",
            f"path={target.relative_path}",
            f"content={content}",
        ]
        self._run_cli(command, run_id=run_id, target_path=target.relative_path, operation="obsidian append")

    def _set_default_properties(
        self,
        target: NoteTarget,
        *,
        selected_folder: str,
        action: str,
        run_id: str | None = None,
    ) -> None:
        metadata = [
            ("source", "atomicOS", "text"),
            ("area", _top_level_folder(selected_folder), "text"),
            ("status", "sintetizado", "text"),
            ("last_action", action, "text"),
            ("updated_at", date.today().isoformat(), "date"),
        ]
        for name, value, property_type in metadata:
            command = [
                self.obsidian_executable,
                "property:set",
                f"path={target.relative_path}",
                f"name={name}",
                f"value={value}",
                f"type={property_type}",
            ]
            self._run_cli(
                command,
                run_id=run_id,
                target_path=target.relative_path,
                operation=f"obsidian property:set {name}",
            )

    def _run_cli(
        self,
        command: Sequence[str],
        *,
        run_id: str | None,
        target_path: str | None,
        operation: str,
    ) -> subprocess.CompletedProcess[str]:
        timer = Timer.start()
        try:
            result = self.runner(
                list(command),
                cwd=str(self.vault_root),
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as exc:
            logger.exception(
                "run_id=%s %s execution failed vault_root=%s target_path=%s command=%s duration_ms=%s error=%s",
                run_id,
                operation,
                self.vault_root,
                target_path,
                sanitize_command(command),
                timer.elapsed_ms(),
                exc,
            )
            raise PersistenceError(f"Could not execute Obsidian CLI: {exc}") from exc

        duration_ms = timer.elapsed_ms()
        if result.returncode != 0:
            logger.warning(
                "run_id=%s %s failed vault_root=%s target_path=%s command=%s returncode=%s duration_ms=%s stdout=%r stderr=%r",
                run_id,
                operation,
                self.vault_root,
                target_path,
                sanitize_command(command),
                result.returncode,
                duration_ms,
                truncate_value(result.stdout),
                truncate_value(result.stderr),
            )
            cause = (result.stderr or result.stdout or "Obsidian CLI failed").strip()
            raise PersistenceError(cause)

        logger.info(
            "run_id=%s %s succeeded vault_root=%s target_path=%s returncode=%s duration_ms=%s stdout=%r stderr=%r",
            run_id,
            operation,
            self.vault_root,
            target_path,
            result.returncode,
            duration_ms,
            truncate_value(result.stdout),
            truncate_value(result.stderr),
        )
        return result

    def _existing_root(self) -> Path:
        if not self.vault_root.exists() or not self.vault_root.is_dir():
            raise ConfigurationError(f"Vault root is unavailable: {self.vault_root}")
        return self.vault_root.resolve()


def _split_relative(value: str) -> list[str]:
    if not value or not value.strip():
        return []
    normalized = value.strip().replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or any(part in ("..", "") for part in path.parts):
        raise PersistenceError("Target path contains unsafe traversal or absolute segments")
    return list(path.parts)


def _safe_title(title: str) -> str:
    stripped = title.strip()
    if not stripped:
        raise PersistenceError("Target title is required")
    if "/" in stripped or "\\" in stripped:
        raise PersistenceError("Target title must be a single path segment")
    if stripped in (".", ".."):
        raise PersistenceError("Target title is unsafe")

    forbidden = '<>:"|?*'
    safe = "".join("-" if char in forbidden else char for char in stripped).strip()
    if not safe:
        raise PersistenceError("Target title is unsafe")
    if not safe.lower().endswith(".md"):
        safe = f"{safe}.md"
    return safe


def _is_hidden_part(path: Path) -> bool:
    return any(part.startswith(".") for part in path.parts)


def _parse_search_paths(stdout: str) -> list[str]:
    value = stdout.strip()
    if not value:
        return []

    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return [line.strip() for line in value.splitlines() if line.strip()]

    paths: list[str] = []
    _collect_paths(payload, paths)
    return paths


def _collect_paths(value: Any, paths: list[str]) -> None:
    if isinstance(value, str):
        paths.append(value)
        return
    if isinstance(value, list):
        for item in value:
            _collect_paths(item, paths)
        return
    if isinstance(value, dict):
        path = value.get("path")
        if isinstance(path, str):
            paths.append(path)
        for key in ("file", "files", "results", "matches"):
            nested = value.get(key)
            if nested is not None:
                _collect_paths(nested, paths)


def _top_level_folder(value: str) -> str:
    parts = _split_relative(value)
    if not parts:
        return "uncategorized"
    return parts[0]


def _contains_visible_markdown(path: Path, root: Path) -> bool:
    for child in path.rglob("*"):
        if (
            child.is_file()
            and child.suffix.lower() == ".md"
            and not _is_hidden_part(child.relative_to(root))
        ):
            return True
    return False


def _missing_directories(root: Path, parent: Path) -> list[Path]:
    missing: list[Path] = []
    relative_parent = parent.relative_to(root)
    current = root
    for part in relative_parent.parts:
        current = current / part
        if not current.exists():
            missing.append(current)
    return missing


def _remove_empty_directories(paths: Sequence[Path], *, run_id: str | None = None) -> None:
    for path in reversed(paths):
        try:
            path.rmdir()
        except OSError:
            logger.debug("run_id=%s preserved non-empty directory %s", run_id, path)
