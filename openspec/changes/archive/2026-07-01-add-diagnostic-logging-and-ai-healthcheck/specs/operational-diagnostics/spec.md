## ADDED Requirements

### Requirement: Technical diagnostic logging
The system SHALL use Python standard-library logging for technical diagnostics across startup, workflow orchestration, Ollama requests, and Vault persistence.

#### Scenario: Unexpected exception is recorded
- **WHEN** an unexpected exception occurs during startup or a synthesis execution
- **THEN** the system SHALL record the exception with stack trace using the technical logger and SHALL show a concise user-visible error or warning.

#### Scenario: Sensitive content is excluded from logs
- **WHEN** the system records diagnostic context for user notes, generated Markdown, HTTP payloads, or CLI commands
- **THEN** the system SHALL omit raw note text, full generated Markdown, secrets, and complete `--content` values from technical logs.

### Requirement: Run correlation
The system SHALL assign a unique `run_id` to every user-triggered synthesis execution and include that identifier in all technical logs for that execution.

#### Scenario: Synthesis run is correlated
- **WHEN** a user starts a synthesis run
- **THEN** workflow, Ollama, and Vault technical logs for that run SHALL include the same `run_id`.

#### Scenario: User-visible failure references run
- **WHEN** a synthesis run fails
- **THEN** the user-visible error log SHALL include enough run context to correlate the failure with technical logs.

### Requirement: Safe log detail limits
The system SHALL truncate external command output and response snippets before logging them when they may contain uncontrolled data.

#### Scenario: External command returns long output
- **WHEN** the Obsidian CLI returns stdout or stderr longer than the configured diagnostic limit
- **THEN** the system SHALL log only a truncated value and SHALL preserve the full output only in the recoverable error message if existing behavior requires it.
