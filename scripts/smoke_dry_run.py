from __future__ import annotations

from atomicos.workflow import NoteWorkflow, WorkflowInput


class DryRunInference:
    def synthesize(self, raw_text: str) -> str:
        return f"# Dry Run\n\n{raw_text}"


class DryRunPersistence:
    def create_note(self, selected_folder: str, optional_subfolder: str, title: str, markdown: str) -> str:
        parts = [selected_folder]
        if optional_subfolder:
            parts.append(optional_subfolder)
        parts.append(title)
        return "/".join(parts)


def main() -> None:
    logs: list[str] = []
    workflow = NoteWorkflow(DryRunInference(), DryRunPersistence(), logs.append)
    result = workflow.run(
        WorkflowInput(
            raw_text="Principio da responsabilidade unica em SOLID.",
            title="Single Responsibility Principle",
            selected_folder="Conhecimento/Java/SOLID",
            optional_subfolder="Principios",
        )
    )

    for log in logs:
        print(log)
    print(f"success={result.success}")
    print(f"clear_editor={result.clear_editor}")
    print(f"target_path={result.target_path}")


if __name__ == "__main__":
    main()
