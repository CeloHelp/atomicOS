## ADDED Requirements

### Requirement: Vault persistence diagnostics
The system SHALL log safe diagnostic metadata for target construction, directory creation, and Obsidian CLI note creation.

#### Scenario: Obsidian CLI succeeds
- **WHEN** the Obsidian CLI creates a note successfully
- **THEN** the system SHALL log the relative target path, Vault root, return code, and execution duration without logging generated Markdown content.

#### Scenario: Obsidian CLI fails
- **WHEN** the Obsidian CLI exits with a non-zero return code or cannot be executed
- **THEN** the system SHALL log the relative target path when available, Vault root, sanitized command shape, return code when available, duration when available, and truncated stdout or stderr.

#### Scenario: Target directory creation fails
- **WHEN** the system cannot create the target note directory
- **THEN** the system SHALL log the target parent directory and exception details while returning a recoverable persistence error.
