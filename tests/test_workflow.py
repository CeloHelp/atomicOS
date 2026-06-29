from __future__ import annotations

import pytest

from atomicos.errors import InferenceError, PersistenceError
from atomicos.workflow import NoteWorkflow, WorkflowInput


class FakeInference:
    def __init__(self, markdown="# Note", error: Exception | None = None):
        self.markdown = markdown
        self.error = error
        self.calls = []

    def synthesize(self, raw_text: str) -> str:
        self.calls.append(raw_text)
        if self.error:
            raise self.error
        return self.markdown


class FakePersistence:
    def __init__(self, target="Conhecimento/Note", error: Exception | None = None):
        self.target = target
        self.error = error
        self.calls = []

    def create_note(self, selected_folder: str, optional_subfolder: str, title: str, markdown: str) -> str:
        self.calls.append((selected_folder, optional_subfolder, title, markdown))
        if self.error:
            raise self.error
        return self.target


def test_workflow_success_persists_note_and_signals_editor_clear():
    logs = []
    inference = FakeInference("# Clean note")
    persistence = FakePersistence("Conhecimento/Java/SOLID")
    workflow = NoteWorkflow(inference, persistence, logs.append)

    result = workflow.run(WorkflowInput(" raw ", " SOLID ", " Conhecimento ", " Java "))

    assert result.success is True
    assert result.clear_editor is True
    assert result.target_path == "Conhecimento/Java/SOLID"
    assert inference.calls == ["raw"]
    assert persistence.calls == [("Conhecimento", "Java", "SOLID", "# Clean note")]
    assert logs == [
        "[INFO] Iniciando sintese para 'SOLID'...",
        "[WAIT] Aguardando inferencia no Pop!_OS...",
        "[INFO] Persistindo nota no Vault...",
        "[OK] Nota injetada e sincronizada no Vault",
    ]


@pytest.mark.parametrize(
    "data, expected",
    [
        (WorkflowInput("", "Title", "Folder"), "raw text"),
        (WorkflowInput("Raw", "", "Folder"), "target title"),
        (WorkflowInput("Raw", "Title", ""), "destination folder"),
    ],
)
def test_workflow_validation_error_does_not_call_dependencies(data, expected):
    logs = []
    inference = FakeInference()
    persistence = FakePersistence()
    workflow = NoteWorkflow(inference, persistence, logs.append)

    result = workflow.run(data)

    assert result.success is False
    assert result.clear_editor is False
    assert expected in result.message
    assert inference.calls == []
    assert persistence.calls == []
    assert logs[-1].startswith("[ERROR]")


def test_workflow_inference_failure_preserves_input_for_retry():
    workflow = NoteWorkflow(FakeInference(error=InferenceError("ollama down")), FakePersistence())

    result = workflow.run(WorkflowInput("Raw", "Title", "Folder"))

    assert result.success is False
    assert result.clear_editor is False
    assert result.target_path is None


def test_workflow_persistence_failure_preserves_input_for_retry():
    persistence = FakePersistence(error=PersistenceError("cli failed"))
    workflow = NoteWorkflow(FakeInference("# Note"), persistence)

    result = workflow.run(WorkflowInput("Raw", "Title", "Folder"))

    assert result.success is False
    assert result.clear_editor is False
    assert persistence.calls == [("Folder", "", "Title", "# Note")]
