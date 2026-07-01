"""End-to-end note workflow orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

from atomicos.diagnostics import get_logger, new_run_id
from atomicos.errors import AtomicOSError, ValidationError


logger = get_logger("workflow")


LogCallback = Callable[[str], None]


class InferenceService(Protocol):
    def synthesize(self, raw_text: str, *, run_id: str | None = None) -> str:
        """Return synthesized Markdown for raw notes."""


class PersistenceService(Protocol):
    def create_note(
        self,
        selected_folder: str,
        optional_subfolder: str,
        title: str,
        markdown: str,
        *,
        run_id: str | None = None,
    ) -> str:
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
        run_id = new_run_id()
        logger.info("run_id=%s workflow started", run_id)
        try:
            self._validate(data)
            logger.info("run_id=%s workflow validation succeeded", run_id)
            self.log(f"[INFO] Iniciando sintese para '{data.title.strip()}'...")
            self.log("[WAIT] Aguardando inferencia no Pop!_OS...")
            logger.info("run_id=%s workflow inference started", run_id)
            markdown = self.inference.synthesize(data.raw_text.strip(), run_id=run_id)
            self.log("[INFO] Persistindo nota no Vault...")
            logger.info("run_id=%s workflow persistence started", run_id)
            target_path = self.persistence.create_note(
                data.selected_folder.strip(),
                data.optional_subfolder.strip(),
                data.title.strip(),
                markdown,
                run_id=run_id,
            )
        except AtomicOSError as exc:
            logger.warning("run_id=%s workflow recoverable failure: %s", run_id, exc)
            self.log(f"[ERROR] run_id={run_id} {exc}")
            return WorkflowResult(success=False, message=str(exc), clear_editor=False)
        except Exception as exc:
            logger.exception("run_id=%s workflow unexpected failure", run_id)
            message = "Unexpected workflow failure"
            self.log(f"[ERROR] run_id={run_id} {message}")
            return WorkflowResult(success=False, message=message, clear_editor=False)

        logger.info("run_id=%s workflow succeeded target_path=%s", run_id, target_path)
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
