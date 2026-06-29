"""End-to-end note workflow orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

from atomicos.errors import AtomicOSError, ValidationError


LogCallback = Callable[[str], None]


class InferenceService(Protocol):
    def synthesize(self, raw_text: str) -> str:
        """Return synthesized Markdown for raw notes."""


class PersistenceService(Protocol):
    def create_note(self, selected_folder: str, optional_subfolder: str, title: str, markdown: str) -> str:
        """Persist Markdown and return the note target path."""


@dataclass(frozen=True)
class WorkflowInput:
    raw_text: str
    title: str
    selected_folder: str
    optional_subfolder: str = ""


@dataclass(frozen=True)
class WorkflowResult:
    success: bool
    message: str
    clear_editor: bool = False
    target_path: str | None = None


class NoteWorkflow:
    """Coordinates validation, inference, persistence, and progress logging."""

    def __init__(
        self,
        inference: InferenceService,
        persistence: PersistenceService,
        log: LogCallback | None = None,
    ) -> None:
        self.inference = inference
        self.persistence = persistence
        self.log = log or (lambda message: None)

    def run(self, data: WorkflowInput) -> WorkflowResult:
        try:
            self._validate(data)
            self.log(f"[INFO] Iniciando sintese para '{data.title.strip()}'...")
            self.log("[WAIT] Aguardando inferencia no Pop!_OS...")
            markdown = self.inference.synthesize(data.raw_text.strip())
            self.log("[INFO] Persistindo nota no Vault...")
            target_path = self.persistence.create_note(
                data.selected_folder.strip(),
                data.optional_subfolder.strip(),
                data.title.strip(),
                markdown,
            )
        except AtomicOSError as exc:
            self.log(f"[ERROR] {exc}")
            return WorkflowResult(success=False, message=str(exc), clear_editor=False)

        self.log("[OK] Nota injetada e sincronizada no Vault")
        return WorkflowResult(
            success=True,
            message="Note created successfully",
            clear_editor=True,
            target_path=target_path,
        )

    def _validate(self, data: WorkflowInput) -> None:
        missing = []
        if not data.raw_text.strip():
            missing.append("raw text")
        if not data.title.strip():
            missing.append("target title")
        if not data.selected_folder.strip():
            missing.append("destination folder")
        if missing:
            raise ValidationError(f"Missing required input: {', '.join(missing)}")
