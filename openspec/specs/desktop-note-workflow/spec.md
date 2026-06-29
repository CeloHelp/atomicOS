## Purpose

Defines the end-to-end desktop workflow for collecting rough notes, synthesizing atomic Markdown, persisting it into Obsidian, and reporting progress to the user.

## Requirements

### Requirement: End-to-end atomic note workflow
The system SHALL provide a single user-triggered workflow that collects raw note text, target title, and destination folder, synthesizes the note, persists it to the Obsidian Vault, and reports the final result to the user.

#### Scenario: Successful note creation
- **WHEN** the user enters raw text, a target title, selects a Vault folder, and triggers synthesis
- **THEN** the system SHALL generate an atomic Markdown note, create it at the selected destination, clear the editor, re-enable the action control, and log a success message.

#### Scenario: Missing required input
- **WHEN** the user triggers synthesis without raw text, target title, or destination folder
- **THEN** the system SHALL not call the LLM or write to disk and SHALL log a validation error identifying the missing input.

### Requirement: Workflow progress logging
The system SHALL emit user-visible logs for workflow start, inference wait, persistence attempt, success, and recoverable failure states.

#### Scenario: Inference starts
- **WHEN** a valid workflow begins
- **THEN** the system SHALL append an informational log naming the target note title before sending the Ollama request.

#### Scenario: Operation fails
- **WHEN** inference, response handling, directory creation, CLI invocation, or persistence validation fails
- **THEN** the system SHALL append an error log with a concise cause and SHALL leave the user's input available for retry.

### Requirement: Clean architecture boundaries
The system SHALL separate presentation, workflow orchestration, network inference, and Vault persistence into modules with dependency injection or equivalent explicit wiring.

#### Scenario: Workflow service test with fakes
- **WHEN** the workflow is tested with fake inference and Vault services
- **THEN** the test SHALL be able to verify orchestration behavior without creating Flet UI controls, making HTTP requests, or writing to the real Vault.
