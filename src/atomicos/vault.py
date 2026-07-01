"""Obsidian Vault integration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import subprocess
from typing import Callable, Sequence

from atomicos.diagnostics import Timer, get_logger, sanitize_command, truncate_value
from atomicos.errors import ConfigurationError, PersistenceError


logger = get_logger("vault")


RunCommand = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class NoteTarget:
    relative_path: str
    absolute_parent: Path


class VaultManager:
    """Discovers Vault folders and creates notes through the Obsidian CLI."""

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
            if path.is_dir() and not _is_hidden_part(path.relative_to(root)):
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

        return NoteTarget(relative_path=relative.as_posix(), absolute_parent=absolute_note.parent)

    def create_note(
        self,
        selected_folder: str,
        optional_subfolder: str,
        title: str,
        markdown: str,
        *,
        run_id: str | None = None,
    ) -> str:
        target = self.build_target(selected_folder, optional_subfolder, title)
        logger.info(
            "run_id=%s vault target prepared vault_root=%s relative_path=%s parent=%s",
            run_id,
            self.vault_root,
            target.relative_path,
            target.absolute_parent,
        )
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

        command = [
            self.obsidian_executable,
            "create",
            f"path={target.relative_path}",
            f"content={markdown}",
        ]
        timer = Timer.start()
        try:
            result = self.runner(
                command,
                cwd=str(self.vault_root),
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as exc:
            logger.exception(
                "run_id=%s obsidian cli execution failed vault_root=%s relative_path=%s command=%s duration_ms=%s error=%s",
                run_id,
                self.vault_root,
                target.relative_path,
                sanitize_command(command),
                timer.elapsed_ms(),
                exc,
            )
            raise PersistenceError(f"Could not execute Obsidian CLI: {exc}") from exc

        duration_ms = timer.elapsed_ms()
        if result.returncode != 0:
            logger.warning(
                "run_id=%s obsidian cli failed vault_root=%s relative_path=%s command=%s returncode=%s duration_ms=%s stdout=%r stderr=%r",
                run_id,
                self.vault_root,
                target.relative_path,
                sanitize_command(command),
                result.returncode,
                duration_ms,
                truncate_value(result.stdout),
                truncate_value(result.stderr),
            )
            cause = (result.stderr or result.stdout or "Obsidian CLI failed").strip()
            raise PersistenceError(cause)

        logger.info(
            "run_id=%s obsidian cli succeeded vault_root=%s relative_path=%s returncode=%s duration_ms=%s stdout=%r stderr=%r",
            run_id,
            self.vault_root,
            target.relative_path,
            result.returncode,
            duration_ms,
            truncate_value(result.stdout),
            truncate_value(result.stderr),
        )
        return target.relative_path

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
